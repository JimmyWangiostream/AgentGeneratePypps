from ._sdk_base import _SDKLibProtocol
from .. import _hal
from . import log_callback as logger
from .exception import *
from . import constant as const
from . import _error_code as err
from enum import IntEnum

class SendCmdSeq:
    def __init__(self):
        self.pby_cmd_buf = bytearray()
        self.qd = 0
        self.option = 0
        self.cmd_blk_cnt = 0
        self.data_blk_cnt = 0
        self.timeout = 0
        self.ext_option = 0
        self.fix_pattern = 0x5A5A5A5A5A5A5A5A


class CmdSeqResult:
    def __init__(self):
        self.step = 0
        self.errorcode = 0
        self.sub_errorcode_1 = 0
        self.sub_errorcode_2 = 0
        self.group_idx = 0
        self.entry_idx = 0
        self.error_tag = 0
        self.expect_crc32 = 0
        self.real_crc32 = 0
        self.total_exe_time = 0
        self.reserved = 0
        self.pby_resp_upiu = bytearray(52)
        self.resp_error_cnt = 0
        self.fail_lba = 0
        self.fail_sector = 0
        self.fail_cnt = 0
        self.fail_data_hh = 0
        self.fail_data_hl = 0
        self.fail_data_lh = 0
        self.fail_data_ll = 0
        self.expect_data_hh = 0
        self.expect_data_hl = 0
        self.expect_data_lh = 0
        self.expect_data_ll = 0
        self.total_idx = 0
        self.reserved = bytearray(393)
    
    def set_val(self, result_buf: bytearray):
        self.step = result_buf[0]
        self.errorcode = result_buf[1]
        self.sub_errorcode_1 = result_buf[2]
        self.sub_errorcode_2 = result_buf[3]
        self.group_idx = int.from_bytes(result_buf[4:6], byteorder='big')
        self.entry_idx = result_buf[6]
        self.error_tag = result_buf[7]
        self.expect_crc32 = int.from_bytes(result_buf[8:12], byteorder='big')
        self.real_crc32 = int.from_bytes(result_buf[12:16], byteorder='big')
        self.total_exe_time = int.from_bytes(result_buf[16:20], byteorder='big')
        self.reserved = result_buf[20]
        self.pby_resp_upiu = result_buf[21:73]
        self.resp_error_cnt = int.from_bytes(result_buf[73:77], byteorder='little')
        self.fail_lba = int.from_bytes(result_buf[77:81], byteorder='big')
        self.fail_sector = result_buf[81]
        self.fail_cnt = result_buf[82]
        self.fail_data_hh = int.from_bytes(result_buf[83:87], byteorder='big')
        self.fail_data_hl = int.from_bytes(result_buf[87:91], byteorder='big')
        self.fail_data_lh = int.from_bytes(result_buf[91:95], byteorder='big')
        self.fail_data_ll = int.from_bytes(result_buf[95:99], byteorder='big')
        self.expect_data_hh = int.from_bytes(result_buf[99:103], byteorder='big')
        self.expect_data_hl = int.from_bytes(result_buf[103:107], byteorder='big')
        self.expect_data_lh = int.from_bytes(result_buf[107:111], byteorder='big')
        self.expect_data_ll = int.from_bytes(result_buf[111:115], byteorder='big')
        self.total_idx = int.from_bytes(result_buf[115:119], byteorder='little')
        self.reserved = result_buf[119:]

class CmdSeqStep(IntEnum): # for result buf, index 0 use
    FINISHED = 1,
    EXECUTE = 2,
    STATUS = 3

class _SDKLibCmdSeqMixin(_SDKLibProtocol):
    def send_cmd_seq(self, cmd: SendCmdSeq):
        assert len(cmd.pby_cmd_buf) % const.DATA_SIZE_8K_BYTE == 0, "Command buffer must be aligned to 8K Byte"
        _hal.send_cmd_seq(self._dll, cmd.pby_cmd_buf, cmd.qd, cmd.option, 
                          cmd.cmd_blk_cnt, cmd.data_blk_cnt, cmd.timeout, 
                          cmd.ext_option, cmd.fix_pattern)

    def send_cmd_seq_ehs(self, data_buf: bytearray, data_block_cnt: int):
        assert len(data_buf) <= const.DATA_SIZE_512K_BYTE, "Buffer size exceeds 512KB"
        _hal.cmd_seq_send_ehs(self._dll, data_buf, data_block_cnt)

    def cmd_seq_get_ehs(self, data_block_cnt: int) -> bytearray:
        return _hal.cmd_seq_get_ehs(self._dll, data_block_cnt)
    
    def cmd_seq_monitor(self, block_cnt: int, data_block_cnt: int, polling_time: int = 0) -> tuple[CmdSeqResult, bytearray]:
        result = CmdSeqResult()
        try:
            result_buf, info_buf = _hal.cmd_seq_monitor(self._dll, block_cnt, data_block_cnt, polling_time)
            result.set_val(result_buf)
        except DLL_ERROR as e:
            # convert bytearray to object
            result.set_val(e.error_data.result_buf)
            e.error_data.result_buf = result

            fun_str = "cmd_seq_monitor"
            error_code = result.errorcode
            sub_errorcode_1 = result.sub_errorcode_1
            sub_errorcode_2 = result.sub_errorcode_2
            if error_code == 0xFF: # ref CMD SEQ Feature Error Code
                if sub_errorcode_1 == 0x01:
                    _hal.handle_error_code(sub_errorcode_2, err.pwr_cycle_codes, fun_str, e.error_data)
                elif sub_errorcode_1 == 0x02:
                    _hal.handle_error_code(sub_errorcode_2, err.switch_vltage_codes, fun_str, e.error_data)
                elif sub_errorcode_1 == 0x03:
                    _hal.handle_error_code(sub_errorcode_2, err.switch_ref_clk_codes, fun_str, e.error_data)
                elif sub_errorcode_1 == 0x04:
                    _hal.handle_error_code(sub_errorcode_2, err.spd_change_codes, fun_str, e.error_data)
                elif sub_errorcode_1 == 0x05:
                    _hal.handle_error_code(sub_errorcode_2, err.init_flow_codes, fun_str, e.error_data)
                elif sub_errorcode_1 == 0x06:
                    _hal.handle_error_code(0x00, err.triiger_gpio, fun_str, e.error_data)
                elif sub_errorcode_1 == 0x07:
                    _hal.handle_error_code(sub_errorcode_2, err.hiber_codes, fun_str, e.error_data)
                elif sub_errorcode_1 == 0x08:
                    _hal.handle_error_code(sub_errorcode_2, err.test_unit_rdy_codes, fun_str, e.error_data)
                elif sub_errorcode_1 == 0x09:
                    _hal.handle_error_code(0x00, err.pwr_ctrl_codes, fun_str, e.error_data)
                elif sub_errorcode_1 == 0x0A:
                    _hal.handle_error_code(sub_errorcode_2, err.rdy_dev_init_flag_codes, fun_str, e.error_data)
                elif sub_errorcode_1 == 0x0B:
                    _hal.handle_error_code(sub_errorcode_2, err.nop_out_nop_in_codes, fun_str, e.error_data)
                else:
                    _hal.handle_error_code(error_code, err.major_error_codes, fun_str, e.error_data)
            elif error_code == 0x88:
                _hal.handle_error_code(sub_errorcode_1, err.excep_error_code_ref, fun_str, e.error_data)
            else:  # ref Major Error Code
                _hal.handle_error_code(error_code, err.major_error_codes, fun_str, e.error_data)

        return result, info_buf