from ._sdk_base import _SDKLibProtocol
from .. import _hal
from . import log_callback as logger
from .exception import *
from ._error_code import major_error_codes
from enum import Enum, auto

class GetDevResp:
    def __init__(self):
        self.ufs_header = bytearray(3)  # UFS header[3]
        self.response_status = 0  # Response status
        self.error_type = 0  # Error Type
        self.timeout_error = 0  # Timeout Error
        self.actual_payload_length = 0  # Actual payload length (Segment length error)
        self.task_tag_pattern_gen_read_compare_error = 0  # Task Tag when Pattern Gen read compare error
        self.lba_pattern_gen_read_compare_error = 0  # LBA when Pattern Gen read compare error
        self.upiu_header = bytearray(16) # UPIU header[16]
        self.sense_data = bytearray(20)  # Sense data[20]
        self.timer_enable_type = 0  # Timer Enable Type (Max, Total Busy, …)
        self.timer_resolution = 0  # Timer Resolution (us)
        self.timer_threshold = 0  # Timer Threshold (refer Timer resolution)
        self.maximum_busy_time = 0  # Maximum Busy Time (Assign by FW )
        self.command_total_busy_time = 0  # Command Total Busy Time
        self.total_time_between_command_and_responding = 0  # Total time between command and responding
        self.time_until_fw_clear_done_queue = 0  # Time of command until FW clear done queue
        self.busy_detect_value = 0  # Busy detect value
        self.total_busy_detect_value = 0  # Total busy detect value
        self.lba_pattern_gen_write = 0  # LBA of Pattern Gen (Write)
        self.lba_pattern_gen2_read = 0  # LBA of Pattern Gen2 (Read)
        self.crc32_check_sum_high_byte = 0  # CRC32 Check Sum High Byte
        self.crc32_check_sum_low_byte = 0  # CRC32 Check Sum Low Byte
        self.tx_task_tag = 0  # Tx Task Tag
        self.rx_task_tag = 0  # Rx Task Tag
        self.error_bit_map = 0  # ErrorBitMap (DME Reg.[0x54 ~ 0x57])
        self.unipro_state = 0  # Unipro State
        self.cmd_start_time = 0  # Cmd Start Time
        self.cmd_end_time = 0  # Cmd End Time
        self.dme_line_reset = 0  # DME Line Reset (DME Reg.[0x58])
        self.dme_layer_err_code_ehs = 0  # DME Layer ERR Code
        self.ehs = 0 # ehs, only for v6

class DataInOutXferStrcut:
    def __init__(self):
        self.lun = 0
        self.task_tag = 0
        self.data_seq_len = 0
        self.buffer_offser = 0
        self.data_cnt = 0
        self.seg_cnt = 0
        self.rw = 0
        self.databuf = bytearray()
        self.iid = 0

class UPIU_Def(Enum):
    UPIU_NOP_OUT = 0    #xx00 0000
    UPIU_NOP_IN = 0x20  #xx10 0000
    UPIU_CMD = 0x01     #xx00 0001
    UPIU_RSP = 0x21,    #xx10 0001
    UPIU_DOUT = 0x02    #xx00 0010
    UPIU_DIN = 0x22     #xx10 0010
    UPIU_TSK = 0x04,    #xx00 0100
    UPIU_TSK_RSP = 0x24 #xx10 0100
    UPIU_QRY = 0x16     #xx01 0110
    UPIU_QRY_RSP = 0x36 #xx11 0110
    UPIU_RTT = 0x31     #xx11 0001
    UPIU_REJECT = 0x3F  #xx11 1111
    UPIU_RSVD = 0x1F   
    DCMD = 0xFF         # for show report msg

class CmdHeader:
    def __init__(self):
        self.tran_type = 0
        self.flag = 0
        self.lun = 0
        self.task_tag = 0
        self.iid_cmd_type = 0
        self.que_tsk = 0
        self.sts = 0
        self.ehs_len = 0
        self.dev_info = 0
        self.dat_seg_len = 0

class CmdTrans:
    def __init__(self):
        self.i12_sf0 = 0
        self.i16_sf1 = 0
        self.i20_sf2 = 0
        self.i24_sf3 = 0
        self.i28_sf4 = 0

class SendCmdStruct:
    def __init__(self):
        self.header = CmdHeader()
        self.tran = CmdTrans()
        self.payload = bytearray(1024)
        self.payload_len = 0
        self.timeout = 0
        self.action = 0
        self.pattern_mode = 0
        self.pattern_tag = 0
        self.seed_h = 0
        self.seed_l = 0
        self.by4k_gen = 0

class _SDKLibCmdTransMixin(_SDKLibProtocol):
    def send_cmd(self, cmd: SendCmdStruct):
        c_cmd_header = _hal.CCmdHeader()
        c_cmd_header.b0_Tran_Type = cmd.header.tran_type
        c_cmd_header.b1_Flag = cmd.header.flag
        c_cmd_header.b2_Lun = cmd.header.lun
        c_cmd_header.b3_Task_Tag = cmd.header.task_tag
        c_cmd_header.b4_IID_CMD_Type = cmd.header.iid_cmd_type
        c_cmd_header.b5_Que_Tsk = cmd.header.que_tsk
        c_cmd_header.b6_Sts = cmd.header.sts
        c_cmd_header.b7_EHS_Len = cmd.header.ehs_len

        c_cmd_trans = _hal.CCmdTran()
        c_cmd_trans.l12_SF0 = cmd.tran.i12_sf0
        c_cmd_trans.l16_SF1 = cmd.tran.i16_sf1
        c_cmd_trans.l20_SF2 = cmd.tran.i20_sf2
        c_cmd_trans.l24_SF3 = cmd.tran.i24_sf3
        c_cmd_trans.l28_SF4 = cmd.tran.i28_sf4
        
        _hal.send_cmd(self._dll, c_cmd_header, c_cmd_trans, 
                      cmd.payload, cmd.payload_len, cmd.timeout, cmd.action, cmd.pattern_mode,
                      cmd.pattern_tag, cmd.seed_h, cmd.seed_l, cmd.by4k_gen)

    def data_payload_xfer(self, action: int, data_buf: bytearray):
        data_len = len(data_buf)
        assert data_len % 512 == 0, "Data buffer size must be 512 bytes alignment"
        _hal.data_payload_xfer(self._dll, action, data_buf, data_len)

    def data_in_out_xfer(self, data: DataInOutXferStrcut):
        assert data.data_cnt % 512 == 0, "Data buffer size must be 512 bytes alignment"
        _hal.data_in_out_xfer(self._dll, data.lun, data.task_tag, data.data_seq_len, 
                              data.buffer_offser, data.data_cnt, data.seg_cnt, data.rw, 
                              data.databuf, data.iid)

    def get_dev_resp(self):
        def convert_to_int(buf, start, end):
            return int.from_bytes(buf[start:end], byteorder='little')
        
        try:
            resp_buf = _hal.get_dev_resp(self.dll)
            dev_rsp = GetDevResp()
            dev_rsp.ufs_header = resp_buf[0:3]
            dev_rsp.response_status = convert_to_int(resp_buf, 3, 4)
            dev_rsp.error_type = convert_to_int(resp_buf, 4, 5)
            dev_rsp.timeout_error = convert_to_int(resp_buf, 5, 6)
            dev_rsp.actual_payload_length = convert_to_int(resp_buf, 6, 8)
            dev_rsp.task_tag_pattern_gen_read_compare_error = convert_to_int(resp_buf, 8, 9)
            dev_rsp.lba_pattern_gen_read_compare_error = convert_to_int(resp_buf, 9, 13)
            dev_rsp.upiu_header = resp_buf[13:29]
            dev_rsp.sense_data = resp_buf[29:49]
            dev_rsp.timer_enable_type = convert_to_int(resp_buf, 49, 50)
            dev_rsp.timer_resolution = convert_to_int(resp_buf, 50, 52)
            dev_rsp.maximum_busy_time = convert_to_int(resp_buf, 52, 56)
            dev_rsp.command_total_busy_time = convert_to_int(resp_buf, 56, 60)
            dev_rsp.total_time_between_command_and_responding = convert_to_int(resp_buf, 60, 64)
            dev_rsp.time_until_fw_clear_done_queue = convert_to_int(resp_buf, 64, 68)
            dev_rsp.busy_detect_value = convert_to_int(resp_buf, 68, 72)
            dev_rsp.total_busy_detect_value = convert_to_int(resp_buf, 72, 76)
            dev_rsp.lba_pattern_gen_write = convert_to_int(resp_buf, 76, 80)
            dev_rsp.lba_pattern_gen2_read = convert_to_int(resp_buf, 80, 84)
            dev_rsp.crc32_check_sum_high_byte = convert_to_int(resp_buf, 84, 88)
            dev_rsp.crc32_check_sum_low_byte = convert_to_int(resp_buf, 88, 92)
            dev_rsp.tx_task_tag = convert_to_int(resp_buf, 92, 93)
            dev_rsp.rx_task_tag = convert_to_int(resp_buf, 93, 94)
            dev_rsp.error_bit_map = convert_to_int(resp_buf, 94, 98)
            dev_rsp.unipro_state = convert_to_int(resp_buf, 98, 99)
            dev_rsp.cmd_start_time = convert_to_int(resp_buf, 99, 103)
            dev_rsp.cmd_end_time = convert_to_int(resp_buf, 103, 107)
            dev_rsp.dme_line_reset = convert_to_int(resp_buf, 107, 108)
            dev_rsp.dme_layer_err_code_ehs = convert_to_int(resp_buf, 108, 109)
            dev_rsp.ehs = resp_buf[109:255]
        except DLL_ERROR as e:
            rsp_status = convert_to_int(resp_buf, 3, 4)
            _hal.handle_error_code(rsp_status, major_error_codes , "dme_set")
        return dev_rsp


