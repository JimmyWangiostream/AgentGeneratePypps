from .base import ApiTestBase
from Script.api import shared

_sdk = shared.sdk
_param = shared.param

#pass
# class TestGetHostInfo(ApiTestBase):
#     def test_get_host_info(self):
#         host_info = _sdk.get_host_info()
#         print(f"crc32: {host_info.crc32}")
#         print(f"queue_status: {host_info.queue_status}")
#         print(f"linkstartuptime: {host_info.linkstartuptime}")
#         print(f"powerchangerety: {host_info.powerchangerety}")
#         print(f"tx_lane0_state: {host_info.tx_lane0_state}")
#         print(f"tx_lane1_state: {host_info.tx_lane1_state}")
#         print(f"rx_lane0_state: {host_info.rx_lane1_state}")
#         print(f"rx_lane1_state: {host_info.rx_lane1_state}")
#         print(f"debuginfo[0]: {host_info.debuginfo[0]}")
#         print(f"debuginfo[1]: {host_info.debuginfo[1]}")
#         print(f"debuginfo[2]: {host_info.debuginfo[2]}")
#         print(f"debuginfo[3]: {host_info.debuginfo[3]}")
#         print(f"debuginfo[4]: {host_info.debuginfo[4]}")
#         print(f"debuginfo[5]: {host_info.debuginfo[5]}")
#         print(f"debuginfo[6]: {host_info.debuginfo[6]}")
#         print(f"errorbitmap[0]: {host_info.errorbitmap[0]}")
#         print(f"errorbitmap[1]: {host_info.errorbitmap[1]}")
#         print(f"errorbitmap[2]: {host_info.errorbitmap[2]}")
#         print(f"errorbitmap[3]: {host_info.errorbitmap[3]}")
#         print(f"errorbitmap[4]: {host_info.errorbitmap[4]}")
#         print(f"send_rst_n_key: {host_info.send_rst_n_key}")
#         print(f"send_rst_n_highd: {host_info.send_rst_n_highd}")
#         print(f"send_rst_n_lowd: {host_info.send_rst_n_lowd}")
#         print(f"boardversion1: {host_info.boardversion1}")
#         print(f"boardversion2: {host_info.boardversion2}")
#         print(f"phisondeviceflag: {host_info.phisondeviceflag}")
#         print(f"powerchange_resultcode: {host_info.powerchange_resultcode}")
#         print(f"layererror: {host_info.layererror}")
#         print(f"send_rst_n_key_status: {host_info.send_rst_n_key_status}")
#         print(f"link_start_up_send_count: {host_info.link_start_up_send_count}")
#         print(f"rstn_send_key_count: {host_info.rstn_send_key_count}")
#         print(f"pcs_check_status: {host_info.pcs_check_status}")
#         print(f"monitor_total_size: {host_info.monitor_total_size}")
#         print(f"monitor_node_size: {host_info.monitor_node_size}")
#         print(f"sdk_ver1: {host_info.sdk_ver1}")
#         print(f"sdk_ver2: {host_info.sdk_ver2}")
#         print(f"sdk_minor: {host_info.sdk_minor}")
#         print(f"line_reset: {host_info.line_reset}")
#         print(f"usb_timeout: {host_info.usb_timeout}")
#         print(f"test_tx_count: {host_info.test_tx_count}")
#         print(f"dme_value: {host_info.dme_value}")
#         print(f"adapt_state: {host_info.adapt_state}")
#         print(f"usb_error_code: {host_info.usb_error_code}")
#         print(f"usb_int_evt_0[0]: {host_info.usb_int_evt_0[0]}")
#         print(f"usb_int_evt_0[1]: {host_info.usb_int_evt_0[1]}")
#         print(f"usb_int_evt_0[2]: {host_info.usb_int_evt_0[2]}")
#         print(f"usb_int_evt_0[3]: {host_info.usb_int_evt_0[3]}")
#         print(f"usb_int_evt_1[0]: {host_info.usb_int_evt_1[0]}")
#         print(f"usb_int_evt_1[1]: {host_info.usb_int_evt_1[1]}")
#         print(f"usb_int_evt_1[2]: {host_info.usb_int_evt_1[2]}")
#         print(f"usb_int_evt_1[3]: {host_info.usb_int_evt_1[3]}")
#         print(f"usb_err_count_0: {host_info.usb_err_count_0}")
#         print(f"usb_err_count_1: {host_info.usb_err_count_1}")
#         print(f"usb_err_count_2: {host_info.usb_err_count_2}")
#         print(f"usb_err_count_3: {host_info.usb_err_count_3}")
#         print(f"ps2808_type: {host_info.usb_int_evt_1}")
#         print(f"support_hpb_size: {host_info.usb_err_count_0}")
#         print(f"dll_enable: {host_info.usb_err_count_1}")
#         print(f"bulkout_ep_offset: {host_info.usb_err_count_2}")
#         print(f"bulin_ep_offset: {host_info.bulin_ep_offset}")
#         print(f"line_reset_count: {host_info.line_reset_count}")
#         print(f"scsi_retry_count: {host_info.scsi_retry_count}")
#         print(f"usb_hw_err_count_0: {host_info.usb_hw_err_count_0}")
#         print(f"usb_hw_err_count_1: {host_info.usb_hw_err_count_1}")
#         print(f"usb_hw_err_count_2: {host_info.usb_hw_err_count_2}")
#         print(f"serial_number: {host_info.serial_number}")
#         print(f"tester_usb_timeout: {host_info.tester_usb_timeout}")
#         print(f"builddate_unix_timestamp: {host_info.builddate_unix_timestamp}")
#         print(f"commit_hash: {host_info.commit_hash}")
#         print(f"customer_sdk_ver1: {host_info.customer_sdk_ver1}")
#         print(f"customer_sdk_ver2: {host_info.customer_sdk_ver2}")
#         print(f"customer_sdk_minor: {host_info.customer_sdk_minor}")
#         print(f"customer_sdk_minor2: {host_info.customer_sdk_minor2}")
#         print(f"dll_ver1: {host_info.dll_ver1}")
#         print(f"dll_ver2: {host_info.dll_ver2}")
#         print(f"usb_speed: {host_info.usb_speed}")
#         print(f"dcmd23_flag: {host_info.dcmd23_flag}")
#         print(f"dme_req_time_start: {host_info.dme_req_time_start}")
#         print(f"dme_req_time_end: {host_info.dme_req_time_end}")
#         print(f"powermode_time_start: {host_info.powermode_time_start}")
#         print(f"powermode_time_end: {host_info.powermode_time_end}")
#         print(f"hibernate_time_start: {host_info.hibernate_time_start}")
#         print(f"hibernate_time_end: {host_info.hibernate_time_end}")
#         print(f"dme_timeout_occur: {host_info.dme_timeout_occur}")
#         print(f"minimum_detect_busy_time: {host_info.minimum_detect_busy_time}")
#         print(f"hyper_ram_error: {host_info.hyper_ram_error}")
#         print(f"usb_err_st_0: {host_info.usb_err_st_0}")
#         print(f"usb_err_st_1: {host_info.usb_err_st_1}")
#         print(f"usb_err_st_2: {host_info.usb_err_st_2}")
#         print(f"tester_hw_din_limit: {host_info.tester_hw_din_limit}")
#         print(f"reserved: {host_info.reserved}")
#         print(f"scsi_0x79_error_code: {host_info.scsi_0x79_error_code}")
#         print(f"script_sdk_parameter_error: {host_info.script_sdk_parameter_error}")


#fail
# class TestGetHostReg(ApiTestBase):
#     def test_get_host_bra_reg(self):
#         host_bra_reg = _sdk.get_host_reg(lib.HostReg.HOST_BRA_REG.value)

#         file_path = 'HOST_BRA_REG.bin'
#         with open(file_path, 'wb') as file:
#             file.write(host_bra_reg)

#     def test_get_host_rng_reg(self):

#         host_rng_reg = _sdk.get_host_reg(lib.HostReg.HOST_RNG_REG.value)
#         file_path = 'HOST_RNG_REG.bin'
#         with open(file_path, 'wb') as file:
#             file.write(host_rng_reg)
        
#     def test_get_host_ufs_reg(self):
#         host_ufs_reg = _sdk.get_host_reg(lib.HostReg.HOST_UFS_REG.value)
#         file_path = 'HOST_UFS_REG.bin'
#         with open(file_path, 'wb') as file:
#             file.write(host_ufs_reg)

#     def test_get_host_dme_reg(self):
#         host_dme_reg = _sdk.get_host_reg(lib.HostReg.HOST_DME_REG.value)

#         file_path = 'HOST_DME_REG.bin'
#         with open(file_path, 'wb') as file:
#             file.write(host_dme_reg)

#     def test_get_host_rng2_reg(self):
#         host_rng2_reg = _sdk.get_host_reg(lib.HostReg.HOST_RNG2_REG.value)

#         file_path = 'HOST_RNG2_REG.bin'
#         with open(file_path, 'wb') as file:
#             file.write(host_rng2_reg)

#     #fail，sdk issue
#     def test_get_host_mphy_reg(self):
#         host_mphy_reg = _sdk.get_host_reg(lib.HostReg.HOST_MPHY_REG.value)
#         file_path = 'HOST_MPHY_REG.bin'
#         with open(file_path, 'wb') as file:
#             file.write(host_mphy_reg)