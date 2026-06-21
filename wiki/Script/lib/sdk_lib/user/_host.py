from ._sdk_base import _SDKLibProtocol
from .. import _hal
from enum import Enum

class HostReg(Enum):
    HOST_BRA_REG = 4
    HOST_RNG_REG = 8
    HOST_UFS_REG = 16
    HOST_DME_REG = 17
    HOST_RNG2_REG = 19
    HOST_MPHY_REG = 20

class HostInfo: # check big endian with sdk team
    def __init__(self, info_buf=None):
        self.crc32 = None
        self.queue_status = None
        self.linkstartuptime = None
        self.powerchangerety = None
        self.tx_lane0_state = None
        self.tx_lane1_state = None
        self.rx_lane0_state = None
        self.rx_lane1_state = None
        self.debuginfo = None
        self.errorbitmap = None
        self.send_rst_n_key = None
        self.send_rst_n_highd = None
        self.send_rst_n_lowd = None
        self.boardversion1 = None
        self.boardversion2 = None
        self.phisondeviceflag = None
        self.powerchange_resultcode = None
        self.layererror = None
        self.send_rst_n_key_status = None
        self.link_start_up_send_count = None
        self.rstn_send_key_count = None
        self.pcs_check_status = None
        self.monitor_total_size = None
        self.monitor_node_size = None
        self.sdk_ver1 = None
        self.sdk_ver2 = None
        self.sdk_minor = None
        self.line_reset = None
        self.usb_timeout = None
        self.test_tx_count = None
        self.dme_value = None
        self.adapt_state = None
        self.usb_error_code = None
        self.usb_int_evt_0 = None
        self.usb_int_evt_1 = None
        self.usb_err_count_0 = None
        self.usb_err_count_1 = None
        self.usb_err_count_2 = None
        self.usb_err_count_3 = None
        self.ps2808_type = None
        self.support_hpb_size = None
        self.dll_enable = None
        self.bulkout_ep_offset = None
        self.bulin_ep_offset = None
        self.line_reset_count = None
        self.scsi_retry_count = None
        self.usb_hw_err_count_0 = None
        self.usb_hw_err_count_1 = None
        self.usb_hw_err_count_2 = None
        self.serial_number = None
        self.tester_usb_timeout = None
        self.builddate_unix_timestamp = None
        self.commit_hash = None
        self.customer_sdk_ver1 = None
        self.customer_sdk_ver2 = None
        self.customer_sdk_minor = None
        self.customer_sdk_minor2 = None
        self.dll_ver1 = None
        self.dll_ver2 = None
        self.usb_speed = None
        self.dcmd23_flag = None
        self.dme_req_time_start = None
        self.dme_req_time_end = None
        self.powermode_time_start = None
        self.powermode_time_end = None
        self.hibernate_time_start = None
        self.hibernate_time_end = None
        self.dme_timeout_occur = None
        self.minimum_detect_busy_time = None
        self.hyper_ram_error = None
        self.usb_err_st_0 = None
        self.usb_err_st_1 = None
        self.usb_err_st_2 = None
        self.tester_hw_din_limit = None
        self.reserved = None
        self.scsi_0x79_error_code = None
        self.script_sdk_parameter_error = None

        if info_buf is not None:
            self.set_host_info(info_buf)

    def set_host_info(self, info_buf: bytearray):
        self.crc32 = int.from_bytes(info_buf[0:4], byteorder='big') # big endian
        self.queue_status = info_buf[4]
        self.linkstartuptime = int.from_bytes(info_buf[5:9], byteorder='big') # big endian
        self.powerchangerety = info_buf[9]
        self.tx_lane0_state = info_buf[10]
        self.tx_lane1_state = info_buf[11]
        self.rx_lane0_state = info_buf[12]
        self.rx_lane1_state = info_buf[13]
        self.debuginfo = info_buf[14:21]
        self.errorbitmap = info_buf[21:26]
        self.send_rst_n_key = info_buf[26]
        self.send_rst_n_highd = info_buf[27]
        self.send_rst_n_lowd = info_buf[28]
        self.boardversion1 = info_buf[29]
        self.boardversion2 = info_buf[30]
        self.phisondeviceflag = info_buf[31]
        self.powerchange_resultcode = info_buf[32]
        self.layererror = info_buf[33]
        self.send_rst_n_key_status = info_buf[34]
        self.link_start_up_send_count = info_buf[35]
        self.rstn_send_key_count = info_buf[36]
        self.pcs_check_status = info_buf[37]
        self.monitor_total_size = int.from_bytes(info_buf[38:40], byteorder='big') # big endian
        self.monitor_node_size = info_buf[40]
        self.sdk_ver1 = info_buf[41]
        self.sdk_ver2 = info_buf[42]
        self.sdk_minor = info_buf[43]
        self.line_reset = info_buf[44]
        self.usb_timeout = info_buf[45]
        self.test_tx_count = int.from_bytes(info_buf[46:50], byteorder='big') # big endians
        self.dme_value = info_buf[50]
        self.adapt_state = info_buf[51]
        self.usb_error_code = info_buf[52]
        self.usb_int_evt_0 = info_buf[53:57]
        self.usb_int_evt_1 = info_buf[57:61]
        self.usb_err_count_0 = int.from_bytes(info_buf[61:65], byteorder='big') # big endian
        self.usb_err_count_1 = int.from_bytes(info_buf[65:69], byteorder='big') # big endian
        self.usb_err_count_2 = int.from_bytes(info_buf[69:73], byteorder='big') # big endian
        self.usb_err_count_3 = int.from_bytes(info_buf[73:77], byteorder='big') # big endian
        self.ps2808_type = info_buf[77]
        self.support_hpb_size = int.from_bytes(info_buf[78:80], byteorder='big') # big endian
        self.dll_enable = info_buf[80]
        self.bulkout_ep_offset = info_buf[81]
        self.bulin_ep_offset = info_buf[82]
        self.line_reset_count = int.from_bytes(info_buf[83:85], byteorder='big') # big endian
        self.scsi_retry_count = info_buf[85]
        self.usb_hw_err_count_0 = info_buf[86]
        self.usb_hw_err_count_1 = info_buf[87]
        self.usb_hw_err_count_2 = info_buf[88]
        self.serial_number = info_buf[89:101]
        self.tester_usb_timeout = int.from_bytes(info_buf[101:105], byteorder='big') # big endian
        self.builddate_unix_timestamp = int.from_bytes(info_buf[105:109], byteorder='little')
        self.commit_hash = int.from_bytes(info_buf[109:113], byteorder='little')
        self.customer_sdk_ver1 = info_buf[113]
        self.customer_sdk_ver2 = info_buf[114]
        self.customer_sdk_minor = info_buf[115]
        self.customer_sdk_minor2 = info_buf[116]
        self.dll_ver1 = info_buf[117]
        self.dll_ver2 = info_buf[118]
        self.usb_speed = info_buf[119]
        self.dcmd23_flag = info_buf[120]
        self.dme_req_time_start = int.from_bytes(info_buf[121:129], byteorder='little')
        self.dme_req_time_end = int.from_bytes(info_buf[129:137], byteorder='little')
        self.powermode_time_start = int.from_bytes(info_buf[137:145], byteorder='little')
        self.powermode_time_end = int.from_bytes(info_buf[145:153], byteorder='little')
        self.hibernate_time_start = int.from_bytes(info_buf[153:161], byteorder='little')
        self.hibernate_time_end = int.from_bytes(info_buf[161:169], byteorder='little')
        self.dme_timeout_occur = info_buf[169]
        self.minimum_detect_busy_time = info_buf[170]
        self.hyper_ram_error = info_buf[171]
        self.usb_err_st_0 = int.from_bytes(info_buf[172:176], byteorder='little')
        self.usb_err_st_1 = int.from_bytes(info_buf[176:180], byteorder='little')
        self.usb_err_st_2 = int.from_bytes(info_buf[180:184], byteorder='little')
        self.tester_hw_din_limit = info_buf[184]
        self.reserved = info_buf[184:512]
        self.scsi_0x79_error_code = info_buf[512]
        self.script_sdk_parameter_error = info_buf[513]

class _SDKLibHostMixin(_SDKLibProtocol):
    def get_host_info(self) -> HostInfo:
        info_buf = _hal.get_host_info(self._dll)
        return HostInfo(info_buf)
    
    def get_host_reg(self, reg_idx: int) -> bytearray:
        return _hal.get_host_reg(self._dll, reg_idx)