import math
import bitstruct
from copy import deepcopy
from typing import Optional, cast, Any, Union

from Script.api import shared
from Script.api.cmd_seq._cycle_tracker import CmdSeqFuncType, CycleTracker
from Script.api.cmd_seq import _buffer_manager as _buf_mngr
from Script.api.cmd_seq.protocols import IsEntry, IsCmdUpiuEntry, UniformTimeout, is_tester_cmd
from Script.api.ufs_api.upiu.structs import CommandUpiu
from Script.api.ufs_api.upiu.protocols import HasCommonHeader
from Script.api.cmd_seq.cmds import Read10, Read16, Read6, ReadBuffer, ReadDescriptor, Write10, Write16, Write6, WriteDescriptor, HpbRead, TaskManagement
from Script.api.cmd_seq.response import (
    CmdSeqResponse, CommandResponse, TaskMgmtResponse, QueryResponse,CmdSeqPowerCycleResponse, CmdSeqSwitchVoltageResponse,
    CmdSeqSwitchReferenceClockResponse, CmdSeqSpeedChangeResponse, CmdSeqInitialFlowResponse, CmdSeqGpioTriggerResponse,
    CmdSeqHibernateResponse, CmdSeqTestUnitReadyResponse, CmdSeqPowerControlResponse, CmdSeqReadyDeviceInitFlagResponse,
    CmdSeqPushNopOutPollNopInResponse, CmdSeqTaskMgmtDummyResponse, CmdSeqPrefetchHpbWriteBufferDummyResponse, NopInResponse,
    get_sense_data_str, get_cmd_response_byte_str, get_task_mgmt_response_byte_str, get_task_mgmt_service_response_str, get_query_response_byte_str)
from Script.api.exception import (
    PATTERN_ASSERT_EXECUTOR_AUTO_MODE_AND_MANUAL_MODE_MIX_IN_SAME_PACKAGE, PATTERN_ASSERT_EXECUTOR_CMD_LIST_IS_FULL, PATTERN_ASSERT_CMD_LIST_NOT_CLEAR, PATTERN_ASSERT_EXECUTOR_EHS_FEATURE_NOT_SUPPORT,
    PATTERN_ASSERT_EXECUTOR_EHS_PAYLOAD_LENGTH_SHALL_EQUAL_TO_TOTAL_EHS_LEN, PATTERN_ASSERT_EXECUTOR_HW_CMP_SHALL_NOT_ENABLE_WITH_HPB_READ, PATTERN_ASSERT_EXECUTOR_HW_CMP_SHALL_NOT_ENABLE_WITH_MANUAL_MODE, PATTERN_ASSERT_EXECUTOR_HW_CMP_SHALL_NOT_ENABLE_WITH_READ_BUFFER,
    PATTERN_ASSERT_EXECUTOR_MANUAL_RW_DATA_SHALL_ALIGN_4KB, PATTERN_ASSERT_EXECUTOR_PATTERN_MODE_SHALL_BE_ALL_SAME_IN_THE_PACKAGE, PATTERN_ASSERT_EXECUTOR_SHALL_SET_QD_LIMIT, PATTERN_ASSERT_EXECUTOR_UNIDENTIFIED_RESPONSE,
    PATTERN_ASSERT_EXECUTOR_NO_RESULT_INFO_BUF, PATTERN_ASSERT_EXECUTOR_RESPONSE_LENGTH_EXCEED_LIMIT, TESTER_ASSERT_MONITOR_RESP_NOT_ALIGN_WITH_RESULT_BUF, TIMEOUT_EXCEPTIONS)
from Script.api.ufs_api.defines.enum_define import CmdParamPatternMode, TimeResolution, UPIUTransactionType, SdkCmd2ndByte
from Script.api.ufs_api.defines.bit_define import BIT
from Script.api.ufs_api.debug_cmd.dcmd_enum import HostDoneQueueType
from Script.api.util.functions import dumpfile
from Script.lib.sdk_lib._hal.exception import DLL_ERROR
from Script.lib.sdk_lib.user import CmdSeqResult, CmdSeqStep
from Script.lib import sdk_lib
from Script.lib.sdk_lib.user.exception import DLL_CRC32_COMPARE_FAIL, DLL_PATTERN_2_ERROR, DLL_RESPONSE_ERROR

# [OK] 預設clear_on_success=True自動清掉
# [OK] 預設hw_cmp=False
# [OK] 預設_time_resolution=resolution_ms
# [OK] 如果設定uniform_timeout(max=0x00FFFFFFms)，將CMD Level Timeout關閉(BIT5)，否則開啟CMD Level Timeout
    # [OK] 當設定為unifrom_timeout時可選擇time_resolution = us or ms
    # [OK] 如果設定為us, 會info提示DCMD7的time resolution也變成us了
# [OK] 推進TaskManagement時_active_task_management=True
# [OK] 推進HPB時_hpb=True
# [OK] 如果開啟hw_cmp，ReadBuffer flag 或 HPB Read flag是True 或 ManualMode, raise exception(due to Tester limit)

_log = shared.logger
_sdk = shared.sdk
_cmd_list: list[IsEntry] = []
_total_payload_in_512B: int = 0
_total_ehs_in_96B: int = 0
_mark_tag: int = 0
_task_tag: int = 0
_rw_manual_mode: bool | None = None
_active_task_mgmt: bool = False
_has_hpb: bool = False
_has_read_buffer: bool = False
_is_cmd_sent: bool = False
_package_pattern_mode: CmdParamPatternMode | None = None
_cycle_tracker: CycleTracker = CycleTracker()
_qd_limit: int | None = None

def set_qd_limit(qd_limit: int) -> None:
    global _qd_limit
    _qd_limit = qd_limit

def print_bytearray(data: bytearray) -> None:
    _log.debug("                 " + ' '.join(f"{i:02}" for i in range(8)))

    for i in range(0, len(data), 8):
        row = data[i:i+8]
        label = f"(byte{i:02}~byte{i+7:02}):"
        values = ' '.join(f"{b:02X}" for b in row)
        if len(row) < 8:
            values += ' ' + ' '.join('--' for _ in range(8 - len(row)))
        _log.debug(f"{label} {values.strip()}")

def enqueue(cmd_entry: IsEntry) -> int:
    # Return index in _cmd_list
    global _cmd_list, _total_payload_in_512B, _total_ehs_in_96B, _active_task_mgmt, _has_hpb, _has_read_buffer
    _log.debug(f'enqueue {len(_cmd_list) + 1}th cmd')
    if _is_cmd_sent:
        raise PATTERN_ASSERT_CMD_LIST_NOT_CLEAR
    cmd = deepcopy(cmd_entry) # 避免修改原始命令

    payload_len_in_512B = 0
    ehs_len_in_96B = 0
    if not is_tester_cmd(cmd):
        _auto_tune_param(cast(IsCmdUpiuEntry, cmd))
        payload_len_in_512B = math.ceil(cast(IsCmdUpiuEntry, cmd).param.l46_data_length / _buf_mngr.ALIGN_SIZE_512)
        ehs_len_in_96B = math.ceil(len(cmd.ehs.to_bytes()) / _buf_mngr.ALIGN_EHS_UNIT)
        
    if _buf_mngr.early_check_if_full(entry_cnt=(len(_cmd_list) + 2),  # +2 is to save space for ending cmd
                                     total_data_cnt_in_512B=_total_payload_in_512B + payload_len_in_512B, 
                                     total_ehs_cnt_in_96B=_total_ehs_in_96B + ehs_len_in_96B):
        raise PATTERN_ASSERT_EXECUTOR_CMD_LIST_IS_FULL

    if isinstance(cmd_entry, TaskManagement):
        _active_task_mgmt = True
    if isinstance(cmd_entry, HpbRead):
        _has_hpb = True
    if isinstance(cmd_entry, ReadBuffer):
        _has_read_buffer = True

    _cmd_list.append(cmd)
    _total_payload_in_512B += payload_len_in_512B
    _total_ehs_in_96B += ehs_len_in_96B

    if is_tester_cmd(cmd):
        assert hasattr(cmd.upiu, 'b1_function_code')
        cmd.cycle_indicator = _cycle_tracker.increment_cycle(CmdSeqFuncType(cmd.upiu.b1_function_code))
    else:
        cmd.cycle_indicator = _cycle_tracker.increment_cycle(CmdSeqFuncType.CMD_UPIU, cast(HasCommonHeader, cmd.upiu).b3_tasktag)

    cmd_idx = len(_cmd_list) - 1
    return cmd_idx

def send(QD: int=-1,
         timeout: UniformTimeout | None=None,
         clear_on_success: bool=True,
         read_hw_compare: bool=False,
         skip_response_check: bool=False,
         record_timestamp: bool=True,
         record_response: bool=True) -> None:
    global _cmd_list, _is_cmd_sent

    #--------------- Force Timeout = Uniform 30s ----------------#
    timeout = UniformTimeout(30000, TimeResolution.ms) #TODO: force uniform timeout for a temp solution
    #----------------------- Sanity check -----------------------#
    if _is_cmd_sent:
        raise PATTERN_ASSERT_CMD_LIST_NOT_CLEAR
    if _rw_manual_mode and read_hw_compare:
        raise PATTERN_ASSERT_EXECUTOR_HW_CMP_SHALL_NOT_ENABLE_WITH_MANUAL_MODE
    if _has_hpb and read_hw_compare:
        raise PATTERN_ASSERT_EXECUTOR_HW_CMP_SHALL_NOT_ENABLE_WITH_HPB_READ
    if _has_read_buffer and read_hw_compare:
        raise PATTERN_ASSERT_EXECUTOR_HW_CMP_SHALL_NOT_ENABLE_WITH_READ_BUFFER
    _is_cmd_sent = True

    #----------------------- Build CMD_SEQ Buf -----------------------#
    _buf_mngr.set_data_begin_offset(len(_cmd_list) + 1) # +1 is to save space for ending cmd
    for idx, cmd in enumerate(_cmd_list):
        _log.debug('===========================================')
        _log.debug(f'[executor:send] push cmd {idx+1}th cmd, {cmd.__class__.__name__}')
        print_bytearray(cmd.compose_entry_buf())
        payload_offset, ehs_offset = _buf_mngr.push_cmd(cmd.compose_entry_buf(), cmd.data, cmd.ehs.to_bytes())
        if not is_tester_cmd(cmd):
            # write param back to cmd object in cmd_list
            cast(IsCmdUpiuEntry, cmd).param.l42_data_address_offset = payload_offset
            cast(IsCmdUpiuEntry, cmd).param.l54_ehs_data_address = ehs_offset
    cmd_seq_obj = _build_cmd_seq_buf(QD, timeout, read_hw_compare, skip_response_check, record_timestamp, record_response)

    #---------------- Send_CMD_SEQ_EHS & Send_CMD_SEQ ---------------#
    if _total_ehs_in_96B > 0:
        _log.debug(f'math.ceil(_total_ehs_in_96B * 96 / _buf_mngr.ALIGN_SIZE_512) = {math.ceil(_total_ehs_in_96B * 96 / _buf_mngr.ALIGN_SIZE_512)}')
        dumpfile('CMD_ExeCMDEhs_DumpAll.bin', _buf_mngr._ehs_buffer)
        _sdk.send_cmd_seq_ehs(_buf_mngr._ehs_buffer, math.ceil(_total_ehs_in_96B * 96 / _buf_mngr.ALIGN_SIZE_512))
    _sdk.send_cmd_seq(cmd_seq_obj)
    #---------------- CMD_SEQ_Monitor & Error Handling ---------------#
    _log.debug('[executor:send] CMD_SEQ_MONITOR')
    try:
        result_obj, info_buf = _sdk.cmd_seq_monitor(cmd_seq_obj.cmd_blk_cnt, cmd_seq_obj.data_blk_cnt)
    except DLL_ERROR as dll_e:
        _log.error(f"{dll_e.__class__.__name__}: {dll_e}")
        result_obj = dll_e.error_data.result_buf
        info_buf = dll_e.error_data.info_buf
        dumpfile('Info_ExeCMDBuff_DumpAll.bin', info_buf[:_buf_mngr._data_ptr], print_info=False)
        _printout_result_buf_fail_response(result_obj)
        if isinstance(dll_e, (DLL_RESPONSE_ERROR, DLL_CRC32_COMPARE_FAIL, TIMEOUT_EXCEPTIONS, DLL_PATTERN_2_ERROR)):
            _get_buffers_and_set_to_buf_mngr(info_buf)
        raise

    #---------------- CMD_SEQ Response Success ----------------#
    _log.debug("[executor:send] CMD SEQ response SUCCESS")
    dumpfile('Info_ExeCMDBuff_DumpAll.bin', info_buf[:_buf_mngr._data_ptr], print_info=False)
    _log.debug(f"  Group index: {result_obj.group_idx}, entry index: {result_obj.entry_idx}, total index: {result_obj.total_idx}")
    #---------------- Parsing Returned Buffer (CMD_SEQ_INFO_BUF & CMD_SEQ_EHS_BUF) ----------------#
    if clear_on_success:
        clear()
    else:
        _get_buffers_and_set_to_buf_mngr(info_buf)
        

def read_response(index: int) -> CommandResponse:
    # Note: Set CommandResponse as default type, as major pattern use cases rely on Command UPIU
    global _cmd_list
    cmd = _cmd_list[index]
    resp_entry = _buf_mngr.get_entry(cmd.cycle_indicator)
    return identify_response(resp_entry, cmd=cmd)  # type: ignore

def identify_response(entry: bytearray, cmd: IsEntry | None = None) -> CmdSeqResponse:
    # If entry length < 72B (e.g. Response pbyResultBuf-> pbyRespUPIU has 52B only), we will pad zeroes to fulfill 72B-struct mapping
    if len(entry) > _buf_mngr.ENTRY_SIZE:
        raise PATTERN_ASSERT_EXECUTOR_RESPONSE_LENGTH_EXCEED_LIMIT
    elif len(entry) < _buf_mngr.ENTRY_SIZE:  # Pad zeroes to meet standard length
        entry += bytearray(_buf_mngr.ENTRY_SIZE - len(entry))

    resp: Union[CmdSeqResponse, Any]
    if entry[0] != UPIUTransactionType.SDK_CMD:  # UPIU response

        if entry[0] == UPIUTransactionType.TM_RSP:
            resp = TaskMgmtResponse()
        elif entry[0] == UPIUTransactionType.QRY_RSP:
            resp = QueryResponse()
        elif entry[0] == UPIUTransactionType.NOP_IN:
            resp = NopInResponse()
        elif entry[0] == UPIUTransactionType.RSP:
            resp = CommandResponse()
            resp.b32_sense_data.from_bytes(entry[32:52])
        else:
            _log.error(f"Unknown UPIU response: {entry}")
            raise PATTERN_ASSERT_EXECUTOR_UNIDENTIFIED_RESPONSE

        resp.raw_data = entry
        resp.upiu.from_bytes(entry)
        resp.b53_cmd_tag = entry[53]
        resp.l54_cmd_timestamp = int.from_bytes(entry[54:58], byteorder='big')
        resp.b58_resp_tag = entry[58]
        resp.l59_resp_timestamp = int.from_bytes(entry[59:63], byteorder='big')
        if cmd is not None:
            cmd = cast(IsCmdUpiuEntry, cmd)
            resp.data = _buf_mngr.get_payload(cmd.param.l42_data_address_offset, cmd.param.l46_data_length)
            total_ehs_length = cast(HasCommonHeader, cmd.upiu).b8_total_ehs_length
            if total_ehs_length > 0: # Due to tester limit: Relied on b8_total_ehs_length, so it's not possible to do error case for this field
                resp.ehs.from_bytes(_buf_mngr.get_ehs(cmd.param.l54_ehs_data_address, total_ehs_length * 32))

    else:
        if entry[1] == SdkCmd2ndByte.PWR_CYCLE:
            resp = CmdSeqPowerCycleResponse()
            resp.raw_data = entry
            resp.b2_mode = entry[2]
            resp.l32_delay_time = int.from_bytes(entry[32:36], byteorder='big')
            resp.w36_wait_queue_empty = int.from_bytes(entry[36:38], byteorder='big')
            resp.l40_endpoint_reset_time = int.from_bytes(entry[40:44], byteorder='big')
            resp.l44_link_startup_time = int.from_bytes(entry[44:48], byteorder='big')

        elif entry[1] == SdkCmd2ndByte.SWITCH_VOLTAGE:
            resp = CmdSeqSwitchVoltageResponse()
            resp.raw_data = entry
            resp.w2_vcc = int.from_bytes(entry[2:4], byteorder='big')
            resp.w4_vccq = int.from_bytes(entry[4:6], byteorder='big')
            resp.w6_vccq2 = int.from_bytes(entry[6:8], byteorder='big')
            resp.l32_delay_time = int.from_bytes(entry[32:36], byteorder='big')
            resp.w36_wait_queue_empty = int.from_bytes(entry[36:38], byteorder='big')

        elif entry[1] == SdkCmd2ndByte.SWITCH_REF_CLK:
            resp = CmdSeqSwitchReferenceClockResponse()
            resp.raw_data = entry
            resp.b2_refclk = entry[2]
            resp.b3_divca = entry[3]
            resp.b4_divm = entry[4]
            resp.b5_locktime = entry[5]
            resp.l32_delay_time = int.from_bytes(entry[32:36], byteorder='big')
            resp.w36_wait_queue_empty = int.from_bytes(entry[36:38], byteorder='big')

        elif entry[1] == SdkCmd2ndByte.SPD_CHG:
            resp = CmdSeqSpeedChangeResponse()
            resp.raw_data = entry
            resp.b2_hs_rate = entry[2]
            resp.b3_rx_mode, resp.b3_rx_lane, resp.b3_rx_gear = bitstruct.unpack('>u3u2u3', int.to_bytes(entry[3]))
            resp.b4_tx_mode, resp.b4_tx_lane, resp.b4_tx_gear = bitstruct.unpack('>u3u2u3', int.to_bytes(entry[4]))
            resp.w5_fc0_protection_timeout = int.from_bytes(entry[5:7], byteorder='big')
            resp.w7_tc0_replay_timeout = int.from_bytes(entry[7:9], byteorder='big')
            resp.w9_afc0_req_timeout = int.from_bytes(entry[9:11], byteorder='big')
            resp.w11_fc1_protection_timeout = int.from_bytes(entry[11:13], byteorder='big')
            resp.w13_tc1_replay_timeout = int.from_bytes(entry[13:15], byteorder='big')
            resp.w15_afc1_req_timeout = int.from_bytes(entry[15:17], byteorder='big')
            resp.l32_delay_time = int.from_bytes(entry[32:36], byteorder='big')
            resp.w36_wait_queue_empty = int.from_bytes(entry[36:38], byteorder='big')

        elif entry[1] == SdkCmd2ndByte.INIT_FLOW:
            resp = CmdSeqInitialFlowResponse()
            resp.raw_data = entry
            resp.l32_delay_time = int.from_bytes(entry[32:36], byteorder='big')
            resp.w36_wait_queue_empty = int.from_bytes(entry[36:38], byteorder='big')
            resp.l40_link_startup_time = int.from_bytes(entry[40:44], byteorder='big')
            resp.l44_nop_out_time = int.from_bytes(entry[44:48], byteorder='big')
            resp.l48_init_flag_time = int.from_bytes(entry[48:52], byteorder='big')

        elif entry[1] == SdkCmd2ndByte.TRIG_GPIO:
            resp = CmdSeqGpioTriggerResponse()
            resp.raw_data = entry
            resp.b2_mode = entry[2]
            resp.b3_toggle_delay = entry[3]
            resp.l32_delay_time = int.from_bytes(entry[32:36], byteorder='big')
            resp.w36_wait_queue_empty = int.from_bytes(entry[36:38], byteorder='big')

        elif entry[1] == SdkCmd2ndByte.HIBERNATE:
            resp = CmdSeqHibernateResponse()
            resp.raw_data = entry
            _, resp.b2_hiberopt_exit, resp.b2_hiberopt_enter = bitstruct.unpack('>u6u1u1', int.to_bytes(entry[2]))
            resp.w3_loopcount = int.from_bytes(entry[3:5], byteorder='big')
            resp.l5_delayafterenter = int.from_bytes(entry[5:9], byteorder='big')
            resp.l9_delayafterexit = int.from_bytes(entry[9:13], byteorder='big')
            resp.l32_delay_time = int.from_bytes(entry[32:36], byteorder='big')
            resp.w36_wait_queue_empty = int.from_bytes(entry[36:38], byteorder='big')
            resp.l40_hiber_enter_time = int.from_bytes(entry[40:44], byteorder='big')
            resp.l44_hiber_exit_time = int.from_bytes(entry[44:48], byteorder='big')

        elif entry[1] == SdkCmd2ndByte.TEST_UNIT_READY:
            resp = CmdSeqTestUnitReadyResponse()
            resp.raw_data = entry
            resp.b2_lun = entry[2]
            resp.l3_timeout = int.from_bytes(entry[3:7], byteorder='big')
            resp.l32_delay_time = int.from_bytes(entry[32:36], byteorder='big')
            resp.w36_wait_queue_empty = int.from_bytes(entry[36:38], byteorder='big')
            resp.l40_test_unit_ready_time = int.from_bytes(entry[40:44], byteorder='big')

        elif entry[1] == SdkCmd2ndByte.PWR_CTRL:
            resp = CmdSeqPowerControlResponse()
            resp.raw_data = entry
            resp.b2_mode  = entry[2]
            resp.b3_channel = entry[3]
            resp.w4_spendtime = int.from_bytes(entry[4:6], byteorder='big')
            resp.w6_ramptime = int.from_bytes(entry[6:8], byteorder='big')
            resp.l32_delay_time = int.from_bytes(entry[32:36], byteorder='big')
            resp.w36_wait_queue_empty = int.from_bytes(entry[36:38], byteorder='big')

        elif entry[1] == SdkCmd2ndByte.RDY_DEV_INIT_FLAG:
            resp = CmdSeqReadyDeviceInitFlagResponse()
            resp.raw_data = entry
            resp.l32_delay_time = int.from_bytes(entry[32:36], byteorder='big')
            resp.w36_wait_queue_empty = int.from_bytes(entry[36:38], byteorder='big')
            resp.l40_init_flag_time = int.from_bytes(entry[40:44], byteorder='big')

        elif entry[1] == SdkCmd2ndByte.PUSH_NOP_OUT_POLL_NOP_IN:
            resp = CmdSeqPushNopOutPollNopInResponse()
            resp.raw_data = entry
            resp.l2_timeout = int.from_bytes(entry[2:6], byteorder='big')
            resp.l32_delay_time = int.from_bytes(entry[32:36], byteorder='big')
            resp.w36_wait_queue_empty = int.from_bytes(entry[36:38], byteorder='big')
            resp.l40_nop_in_time = int.from_bytes(entry[40:44], byteorder='big')

        elif entry[1] == SdkCmd2ndByte.TM_DUMMY_RSP:
            resp = CmdSeqTaskMgmtDummyResponse()
            resp.raw_data = entry
            resp.b2_abort_tag = entry[2]
            resp.l32_delay_time = int.from_bytes(entry[32:36], byteorder='big')
            resp.w36_wait_queue_empty = int.from_bytes(entry[36:38], byteorder='big')
            resp.l54_send_cmd_timestamp = int.from_bytes(entry[54:58], byteorder='big')
            resp.b58_abort_tag = entry[58]
            resp.l59_abort_timestamp = int.from_bytes(entry[59:63], byteorder='big')

        elif entry[1] == SdkCmd2ndByte.PREFETCH_HPB_WR_BUF_DUMMY_RSP:
            resp = CmdSeqPrefetchHpbWriteBufferDummyResponse()
            resp.raw_data = entry
            resp.b2_task_tag = entry[2]
            resp.b3_type = entry[3]
            resp.l32_delay_time = int.from_bytes(entry[32:36], byteorder='big')
            resp.w36_wait_queue_empty = int.from_bytes(entry[36:38], byteorder='big')
            resp.l54_send_cmd_timestamp = int.from_bytes(entry[54:58], byteorder='big')

        else:
            _log.error(f"Unknown CMD SEQ response {entry}")
            raise PATTERN_ASSERT_EXECUTOR_UNIDENTIFIED_RESPONSE

    return resp

def clear() -> None:
    global _cmd_list, _total_payload_in_512B, _rw_manual_mode, _total_ehs_in_96B, _active_task_mgmt, _is_cmd_sent, _package_pattern_mode, _has_read_buffer, _has_hpb
    _buf_mngr.reset_module()
    _cmd_list.clear()
    _total_payload_in_512B = 0
    _total_ehs_in_96B = 0
    _rw_manual_mode = None
    _active_task_mgmt = False
    _has_read_buffer = False
    _has_hpb = False
    _is_cmd_sent = False
    _package_pattern_mode = None
    _cycle_tracker.reset()
    # Clear tester SDK queue
    shared.sdk.clear_done_queue(HostDoneQueueType.ALL_DONE_QUEUE_ERR_HANDLE, 0)

def _build_cmd_seq_buf(QD: int,
         timeout: UniformTimeout | None,
         read_hw_compare: bool,
         skip_response_check: bool,
         record_timestamp: bool,
         record_response: bool) -> sdk_lib.SendCmdSeq:
    cmd_seq_obj = sdk_lib.SendCmdSeq()
    cmd_seq_obj.pby_cmd_buf = _buf_mngr._buffer
    dumpfile('CMD_ExeCMDBuff_DumpAll.bin', cmd_seq_obj.pby_cmd_buf[:_buf_mngr._data_ptr], print_info=False)

    if _qd_limit is None:
        raise PATTERN_ASSERT_EXECUTOR_SHALL_SET_QD_LIMIT
    cmd_seq_obj.qd = QD if QD != -1 else _qd_limit
    if record_timestamp:
        cmd_seq_obj.option |= BIT(0)
    if record_response:
        cmd_seq_obj.option |= BIT(1)
    if _active_task_mgmt:
        cmd_seq_obj.option |= BIT(3)
    if skip_response_check:
        cmd_seq_obj.option |= BIT(6)
    if _rw_manual_mode:
        cmd_seq_obj.option |= BIT(2)    # Enable read/write manual mode
        cmd_seq_obj.option &= ~BIT(4)   # Disable read HW compare
    if read_hw_compare:
        cmd_seq_obj.option &= ~BIT(2)   # Disable read/write manual mode
        cmd_seq_obj.option |= BIT(4)    # Enable read HW compare
        cmd_seq_obj.option &= ~BIT(7)   # Disable HPB dynamic mode
    cmd_seq_obj.cmd_blk_cnt = math.ceil(_buf_mngr._entry_ptr / _buf_mngr.ALIGN_SIZE_512)
    cmd_seq_obj.data_blk_cnt = _buf_mngr._data_ptr // _buf_mngr.ALIGN_SIZE_512
    if _total_payload_in_512B == 0:
        cmd_seq_obj.data_blk_cnt = cmd_seq_obj.cmd_blk_cnt
    assert _buf_mngr._data_ptr % _buf_mngr.ALIGN_SIZE_512 == 0, '[BUG] data ptr must align 512'
    assert _buf_mngr._ehs_ptr % _buf_mngr.ALIGN_EHS_UNIT == 0, '[BUG] ehs ptr must align 96'
    if timeout is None:
        # cmd_seq_obj.option |= BIT(5)    # Enable CMD Level Timeout #TODO: force uniform timeout for a temp solution
        pass
    else:
        _log.info(f'Uniform Timeout Resolution Set to {timeout.val}{timeout.unit.name}')
        cmd_seq_obj.ext_option |= (timeout.unit << 1)
        cmd_seq_obj.timeout = timeout.val
        if timeout.unit == TimeResolution.us:
            _log.warning('DCMD7 Time Resolution Also Changed to us.')
    _log.debug('[executor:send] SEND_CMD_SEQ Options')
    _log.debug(f'{cmd_seq_obj.qd=}, cmd_seq_obj.option={cmd_seq_obj.option:08b}, {cmd_seq_obj.cmd_blk_cnt=}, {cmd_seq_obj.data_blk_cnt=}, {cmd_seq_obj.timeout=}, cmd_seq_obj.ext_option={cmd_seq_obj.ext_option:08b}, cmd_seq_obj.fix_pattern={cmd_seq_obj.fix_pattern:x}')

    return cmd_seq_obj

def _get_buffers_and_set_to_buf_mngr(info_buf: bytearray) -> None:
    if _total_ehs_in_96B > 0:
        block_cnt = math.ceil(_total_ehs_in_96B * 96 / _buf_mngr.ALIGN_SIZE_512)
        ehs_buf = _sdk.cmd_seq_get_ehs(block_cnt)
        dumpfile('Info_ExeCMDEhs_DumpAll.bin', ehs_buf[0:_total_ehs_in_96B * 96])
        _buf_mngr._ehs_buffer = ehs_buf
    _buf_mngr._buffer = info_buf
    _buf_mngr.gen_rsp_cycle_indicator(len(_cmd_list))

def _get_mark_tag() -> int:
    global _mark_tag
    _mark_tag += 1
    return _mark_tag & 0xFFFFFFFF

def _get_task_tag() -> int:
    global _task_tag
    _task_tag += 1
    return _task_tag & 0xFF

def _auto_tune_param(cmd: IsCmdUpiuEntry) -> None:
    """
    [OK] Raise exception if both MANUAL R/W and AUTO R/W exist in the list  
    [OK] Fill CmdUpiuParam.w36_data_in_out based on Auto/Manual Mode  
    [OK] Fill CmdUpiuParam.w36_data_in_out based on whether the cmd has data in/out  
    [OK] Set CmdUpiuParam.l46_data_length based on Expected Data Length  
    [OK] Set CmdUpiuParam.l46_data_length based on R/W Descriptor w18_length  
    [OK] Increment tasktag and set upiu.b3_tasktag when pushing CMD  
    [OK] Check if expected data length is aligned to 4KB when pushing Manual W/R  
    [OK] Increment CmdUpiuParam.l38_mark_tag_or_crc32 when pushing Write  
    [Deprecated] Check if the length set in upiu matches the payload length when pushing cmd  
                  (payload may be smaller than upiu length)  
    [OK] Check if upiu.b8_total_ehs_length matches the length of the ehs bytearray  
    [OK] Raise exception if ehs.b0_length != 0 but Tester < V6  
    [OK] Raise exception if the pattern mode across the entire package is not consistent.  
    """
    global _rw_manual_mode, _package_pattern_mode
    cmd.upiu.b3_tasktag = _get_task_tag() if cmd.upiu.b3_tasktag == -1 else cmd.upiu.b3_tasktag # type: ignore[attr-defined]
    if isinstance(cmd, (Write6, Write10, Write16)) and cmd.param.w36_data_in_out == 0:
        # W CMD Auto Mode
        cmd.param.w36_crc_compare = 0
        cmd.param.l38_mark_tag_or_crc32 = _get_mark_tag() if cmd.specific_tag is None else cmd.specific_tag
        cmd.param.l46_data_length = 0
    elif isinstance(cmd, (Read6, Read10, Read16, HpbRead)) and cmd.param.w36_data_in_out == 0:
        # R CMD Auto Mode
        cmd.param.l46_data_length = 0
    elif isinstance(cmd, (Write6, Write10, Write16, Read6, Read10, Read16, HpbRead)) and cmd.param.w36_data_in_out == 1:
        # R/W Manual Mode
        cmd.param.w36_add_tag = 0
        if cmd.upiu.l12_expected_data_length % 4096 != 0:
            _log.debug(f'{cmd.upiu.l12_expected_data_length=}')
            raise PATTERN_ASSERT_EXECUTOR_MANUAL_RW_DATA_SHALL_ALIGN_4KB
        cmd.param.l46_data_length = _buf_mngr.align_up(cmd.upiu.l12_expected_data_length, _buf_mngr.ALIGN_SIZE_512)
    elif isinstance(cmd.upiu, CommandUpiu):
        # Other SCSI CMDs
        cmd.param.w36_add_tag = 0
        cmd.param.l46_data_length = _buf_mngr.align_up(cmd.upiu.l12_expected_data_length, _buf_mngr.ALIGN_SIZE_512)
    elif isinstance(cmd, (ReadDescriptor, WriteDescriptor)):
        # R/W Descriptor
        cmd.param.l46_data_length = _buf_mngr.align_up(cmd.upiu.u12_specific_fields.w18_length, _buf_mngr.ALIGN_SIZE_512)

    # R CMD w/ CRC Compare(SW Compare)
    if isinstance(cmd, (Read6, Read10, Read16)) and cmd.param.w36_crc_compare == 1:
        cmd.param.w36_add_tag = 0

    if isinstance(cmd, (Write6, Write10, Write16, Read6, Read10, Read16)):
        # Sanity check: Manual R/W & Auto R/W shall not mix in same package
        if _rw_manual_mode is None:
            _rw_manual_mode = cmd.param.w36_data_in_out == 1
        else:  # Manual mode has been assigned, all read/write cmds must align with this mode
            if _rw_manual_mode != bool(cmd.param.w36_data_in_out):
                _log.error("Cmd option Data in/out (%d) does not align with manual mode (%d)" % (cmd.param.w36_data_in_out, _rw_manual_mode))
                raise PATTERN_ASSERT_EXECUTOR_AUTO_MODE_AND_MANUAL_MODE_MIX_IN_SAME_PACKAGE
        # Sanity check: Raise exception if the pattern mode across the entire package is not consistent.
        if _package_pattern_mode is None:
            _package_pattern_mode = CmdParamPatternMode(cmd.param.w36_pattern_mode)
        else:
            if _package_pattern_mode != CmdParamPatternMode(cmd.param.w36_pattern_mode):
                _log.error(f'The pattern mode across the entire package is not consistent. Expect {CmdParamPatternMode(_package_pattern_mode).name}')
                raise PATTERN_ASSERT_EXECUTOR_PATTERN_MODE_SHALL_BE_ALL_SAME_IN_THE_PACKAGE
    
    # Sanity check: Check if current Tester supports EHS feature
    tester_version = -1 if shared.param.gHostInfo.sdk_ver1 is None else shared.param.gHostInfo.sdk_ver1
    if cmd.ehs.b0_length != 0 and tester_version < 7:
        raise PATTERN_ASSERT_EXECUTOR_EHS_FEATURE_NOT_SUPPORT
    
    # Sanity check: EHS Length is identical to bLength(32-byte units)
    if cast(HasCommonHeader, cmd.upiu).b8_total_ehs_length * 32 != len(cmd.ehs.to_bytes()):
        raise PATTERN_ASSERT_EXECUTOR_EHS_PAYLOAD_LENGTH_SHALL_EQUAL_TO_TOTAL_EHS_LEN

def _printout_result_buf_fail_response(result_obj: CmdSeqResult) -> None:
    _log.error("[executor:send] CMD_SEQ response FAIL")
    _log.error(f"  SDK errorcode: 0x{result_obj.errorcode:02X}, sub_errorcode_1: 0x{result_obj.sub_errorcode_1:02X}, sub_errorcode_2: 0x{result_obj.sub_errorcode_2:02X}")
    _log.error("CMD_SEQ result:")
    for name, value in vars(result_obj).items():
        if name == 'reserved':
            continue
        if isinstance(value, int):
            _log.error(f"{name:<20} : 0x{value:X}")
        elif isinstance(value, bytearray):
            _log.error(f"{name:<20} : 0x{value.hex()}")
        else:
            _log.error(f"{name:<20} : {value}")
    try:
        resp = identify_response(result_obj.pby_resp_upiu)
    except PATTERN_ASSERT_EXECUTOR_UNIDENTIFIED_RESPONSE:
        _log.warning('Cannot Parse Response of Fail CMD (could be due to a cmd timeout)')
        return
    if isinstance(resp, CommandResponse):
        _log.error(f"UPIU response: {get_cmd_response_byte_str(resp)}({resp.upiu.b6_response})")
        _log.error(get_sense_data_str(resp))
    elif isinstance(resp, TaskMgmtResponse):
        _log.error(f"UPIU response: {get_task_mgmt_response_byte_str(resp)}({resp.upiu.b6_response})")
        _log.error(f"Task Mgmt Service Response: {get_task_mgmt_service_response_str(resp)}(0x{resp.upiu.l12_output_parameter1:02X})")
    elif isinstance(resp, QueryResponse):
        _log.error(f"UPIU query response: {get_query_response_byte_str(resp)}(0x{resp.upiu.b6_query_response:02X})")