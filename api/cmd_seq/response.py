from Script.api.ufs_api.defines.enum_define import ScsiStatus, SenseKey, UPIUResponse, TaskMgmtServiceResponse, QueryResponseCode
from Script.api.ufs_api.defines.asc_ascq_define import ASC_ASCQ_MAP
from Script.api.ufs_api.upiu.protocols import IsEhs
from Script.api.ufs_api.upiu.structs import Ehs, ResponseUpiu, TaskMngmtResponseUpiu, QueryResponseUpiu, NopInUpiu, SenseData


class CmdSeqResponse:
    def __init__(self) -> None:
        self.raw_data: bytearray = bytearray()


class CommandResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.data: bytearray = bytearray()
        self.ehs: IsEhs = Ehs()
        self.upiu: ResponseUpiu = ResponseUpiu()
        self.b32_sense_data: SenseData = SenseData()
        self.b53_cmd_tag: int = 0
        self.l54_cmd_timestamp: int = 0
        self.b58_resp_tag: int = 0
        self.l59_resp_timestamp: int = 0


class NopInResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.data: bytearray = bytearray()
        self.ehs: IsEhs = Ehs()
        self.upiu: NopInUpiu = NopInUpiu()
        self.b32_sense_data: SenseData = SenseData()
        self.b53_cmd_tag: int = 0
        self.l54_cmd_timestamp: int = 0
        self.b58_resp_tag: int = 0
        self.l59_resp_timestamp: int = 0


class TaskMgmtResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.data: bytearray = bytearray()
        self.ehs: IsEhs = Ehs()
        self.upiu: TaskMngmtResponseUpiu = TaskMngmtResponseUpiu()
        self.b32_sense_data: SenseData = SenseData()
        self.b53_cmd_tag: int = 0
        self.l54_cmd_timestamp: int = 0
        self.b58_resp_tag: int = 0
        self.l59_resp_timestamp: int = 0


class QueryResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.data: bytearray = bytearray()
        self.ehs: IsEhs = Ehs()
        self.upiu: QueryResponseUpiu = QueryResponseUpiu()
        self.b32_sense_data: SenseData = SenseData()
        self.b53_cmd_tag: int = 0
        self.l54_cmd_timestamp: int = 0
        self.b58_resp_tag: int = 0
        self.l59_resp_timestamp: int = 0

############### Tester Commands ###############

class CmdSeqPowerCycleResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.b0_transaction_type = 0xFF
        self.b1_function_code = 0x01
        self.b2_mode: int = 0
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0
        self.l40_endpoint_reset_time: int = 0
        self.l44_link_startup_time: int = 0


class CmdSeqSwitchVoltageResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.b0_transaction_type = 0xFF
        self.b1_function_code = 0x02
        self.w2_vcc: int = 0
        self.w4_vccq: int = 0
        self.w6_vccq2: int = 0
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0


class CmdSeqSwitchReferenceClockResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.b0_transaction_type = 0xFF
        self.b1_function_code = 0x03
        self.b2_refclk: int = 0
        self.b3_divca: int = 0
        self.b4_divm: int = 0
        self.b5_locktime: int = 0
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0


class CmdSeqSpeedChangeResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.b0_transaction_type = 0xFF
        self.b1_function_code = 0x04
        self.b2_hs_rate: int = 0
        self.b3_rx_gear: int = 0
        self.b3_rx_lane: int = 0
        self.b3_rx_mode: int = 0
        self.b4_tx_gear: int = 0
        self.b4_tx_lane: int = 0
        self.b4_tx_mode: int = 0
        self.w5_fc0_protection_timeout: int = 0
        self.w7_tc0_replay_timeout: int = 0
        self.w9_afc0_req_timeout: int = 0
        self.w11_fc1_protection_timeout: int = 0
        self.w13_tc1_replay_timeout: int = 0
        self.w15_afc1_req_timeout: int = 0
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0


class CmdSeqInitialFlowResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.b0_transaction_type = 0xFF
        self.b1_function_code = 0x05
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0
        self.l40_link_startup_time: int = 0
        self.l44_nop_out_time: int = 0
        self.l48_init_flag_time: int = 0


class CmdSeqGpioTriggerResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.b0_transaction_type = 0xFF
        self.b1_function_code = 0x06
        self.b2_mode: int = 0
        self.b3_toggle_delay: int = 0
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0


class CmdSeqHibernateResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.b0_transaction_type = 0xFF
        self.b1_function_code = 0x07
        self.b2_hiberopt_enter: int = 0
        self.b2_hiberopt_exit: int = 0
        self.w3_loopcount: int = 0
        self.l5_delayafterenter: int = 0
        self.l9_delayafterexit: int = 0
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0
        self.l40_hiber_enter_time: int = 0
        self.l44_hiber_exit_time: int = 0


class CmdSeqTestUnitReadyResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.b0_transaction_type = 0xFF
        self.b1_function_code = 0x08
        self.b2_lun: int = 0
        self.l3_timeout: int = 0
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0
        self.l40_test_unit_ready_time: int = 0


class CmdSeqPowerControlResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.b0_transaction_type = 0xFF
        self.b1_function_code = 0x09
        self.b2_mode: int = 0
        self.b3_channel: int = 0
        self.w4_spendtime: int = 0
        self.w6_ramptime: int = 0
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0


class CmdSeqReadyDeviceInitFlagResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.b0_transaction_type = 0xFF
        self.b1_function_code = 0x0A
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0
        self.l40_init_flag_time: int = 0


class CmdSeqPushNopOutPollNopInResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.b0_transaction_type = 0xFF
        self.b1_function_code = 0x0B
        self.l2_timeout: int = 0
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0
        self.l40_nop_in_time: int = 0


class CmdSeqTaskMgmtDummyResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.b0_transaction_type = 0xFF
        self.b1_function_code = 0xFE
        self.b2_abort_tag: int = 0
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0
        self.l54_send_cmd_timestamp: int = 0
        self.b58_abort_tag: int = 0
        self.l59_abort_timestamp: int = 0


class CmdSeqPrefetchHpbWriteBufferDummyResponse(CmdSeqResponse):
    def __init__(self) -> None:
        super().__init__()
        self.b0_transaction_type = 0xFF
        self.b1_function_code = 0xFD
        self.b2_task_tag: int = 0
        self.b3_type: int = 0
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0
        self.l54_send_cmd_timestamp: int = 0

############### Tester Commands end ###############


def get_scsi_status_str(cmd_resp: CommandResponse) -> str:
    status = cmd_resp.upiu.b7_status
    if status not in ScsiStatus._value2member_map_:
        str_s = f"{status} does not found in SCSI_STATUS"
    else:
        str_s = ScsiStatus(status).name
    return str_s


def get_sense_key_str(cmd_resp: CommandResponse) -> str:
    key = cmd_resp.b32_sense_data.b2_sense_key
    if key not in SenseKey._value2member_map_:
        str_k = f"{key} does not found in SENSE_KEY"
    else:
        str_k = SenseKey(key).name
    return str_k


def get_asc_ascq_description(cmd_resp: CommandResponse) -> str:
    asc = cmd_resp.b32_sense_data.b12_asc
    ascq = cmd_resp.b32_sense_data.b13_ascq
    key = '%02Xh/%02Xh' % (asc, ascq)
    return ASC_ASCQ_MAP.get(key, f"{key} does not found in ASC/ASCQ map")


def get_sense_data_str(resp: CommandResponse) -> str:
    scsi_status = get_scsi_status_str(resp)
    sense_key = get_sense_key_str(resp)
    asc_ascq = get_asc_ascq_description(resp)
    sense_data = f"SCSI status: {scsi_status}(0x{resp.upiu.b7_status:02X}), Sense: {sense_key}(0x{resp.b32_sense_data.b2_sense_key:02X}), ASC/ASCQ: {asc_ascq}({resp.b32_sense_data.b12_asc:02X}h/{resp.b32_sense_data.b13_ascq:02X}h)"
    return sense_data


def get_cmd_response_byte_str(resp: CommandResponse) -> str:
    val = resp.upiu.b6_response
    if val not in UPIUResponse._value2member_map_:
        str_r = f"{val} does not found in {UPIUResponse.__name__}"
    else:
        str_r = UPIUResponse(val).name
    return str_r


def get_task_mgmt_response_byte_str(resp: TaskMgmtResponse) -> str:
    val = resp.upiu.b6_response
    if val not in UPIUResponse._value2member_map_:
        str_r = f"{val} does not found in {UPIUResponse.__name__}"
    else:
        str_r = UPIUResponse(val).name
    return str_r


def get_task_mgmt_service_response_str(resp: TaskMgmtResponse) -> str:
    val = resp.upiu.l12_output_parameter1
    if val not in TaskMgmtServiceResponse._value2member_map_:
        str_r = f"{val} does not found in {TaskMgmtServiceResponse.__name__}"
    else:
        str_r = TaskMgmtServiceResponse(val).name
    return str_r


def get_query_response_byte_str(resp: QueryResponse) -> str:
    val = resp.upiu.b6_query_response
    if val not in QueryResponseCode._value2member_map_:
        str_r = f"{val} does not found in {QueryResponseCode.__name__}"
    else:
        str_r = QueryResponseCode(val).name
    return str_r
