from Script.api import shared
from Script.lib import sdk_lib as lib
_sdk = shared.sdk
_log = shared.logger

from Script import api

def dll_init():
    _log.debug('dll_init')
    _sdk.dll_initial()

def get_dll_version():
    _log.debug('get_dll_version')
    dll_ver = _sdk.get_dll_version()
    _log.debug(f"DLL Version:v = {dll_ver.v}")
    _log.debug(f"DLL Version:main_ver = {dll_ver.main_ver}")
    _log.debug(f"DLL Version:minor_ver = {dll_ver.minor_ver}")
    _log.debug(f"DLL Version:year = {dll_ver.year}")
    _log.debug(f"DLL Version:month = {dll_ver.month}")
    _log.debug(f"DLL Version:date = {dll_ver.date}")

def get_host_info():
    _log.debug('get_host_info')
    host_info = _sdk.get_host_info()
    assert host_info.debuginfo is not None
    assert host_info.errorbitmap is not None
    assert host_info.usb_int_evt_0 is not None
    assert host_info.usb_int_evt_1 is not None
    _log.debug(f"crc32: {host_info.crc32}")
    _log.debug(f"queue_status: {host_info.queue_status}")
    _log.debug(f"linkstartuptime: {host_info.linkstartuptime}")
    _log.debug(f"powerchangerety: {host_info.powerchangerety}")
    _log.debug(f"tx_lane0_state: {host_info.tx_lane0_state}")
    _log.debug(f"tx_lane1_state: {host_info.tx_lane1_state}")
    _log.debug(f"rx_lane0_state: {host_info.rx_lane1_state}")
    _log.debug(f"rx_lane1_state: {host_info.rx_lane1_state}")
    _log.debug(f"debuginfo[0]: {host_info.debuginfo[0]}")
    _log.debug(f"debuginfo[1]: {host_info.debuginfo[1]}")
    _log.debug(f"debuginfo[2]: {host_info.debuginfo[2]}")
    _log.debug(f"debuginfo[3]: {host_info.debuginfo[3]}")
    _log.debug(f"debuginfo[4]: {host_info.debuginfo[4]}")
    _log.debug(f"debuginfo[5]: {host_info.debuginfo[5]}")
    _log.debug(f"debuginfo[6]: {host_info.debuginfo[6]}")
    _log.debug(f"errorbitmap[0]: {host_info.errorbitmap[0]}")
    _log.debug(f"errorbitmap[1]: {host_info.errorbitmap[1]}")
    _log.debug(f"errorbitmap[2]: {host_info.errorbitmap[2]}")
    _log.debug(f"errorbitmap[3]: {host_info.errorbitmap[3]}")
    _log.debug(f"errorbitmap[4]: {host_info.errorbitmap[4]}")
    _log.debug(f"send_rst_n_key: {host_info.send_rst_n_key}")
    _log.debug(f"send_rst_n_highd: {host_info.send_rst_n_highd}")
    _log.debug(f"send_rst_n_lowd: {host_info.send_rst_n_lowd}")
    _log.debug(f"boardversion1: {host_info.boardversion1}")
    _log.debug(f"boardversion2: {host_info.boardversion2}")
    _log.debug(f"phisondeviceflag: {host_info.phisondeviceflag}")
    _log.debug(f"powerchange_resultcode: {host_info.powerchange_resultcode}")
    _log.debug(f"layererror: {host_info.layererror}")
    _log.debug(f"send_rst_n_key_status: {host_info.send_rst_n_key_status}")
    _log.debug(f"link_start_up_send_count: {host_info.link_start_up_send_count}")
    _log.debug(f"rstn_send_key_count: {host_info.rstn_send_key_count}")
    _log.debug(f"pcs_check_status: {host_info.pcs_check_status}")
    _log.debug(f"monitor_total_size: {host_info.monitor_total_size}")
    _log.debug(f"monitor_node_size: {host_info.monitor_node_size}")
    _log.debug(f"sdk_ver1: {host_info.sdk_ver1}")
    _log.debug(f"sdk_ver2: {host_info.sdk_ver2}")
    _log.debug(f"sdk_minor: {host_info.sdk_minor}")
    _log.debug(f"line_reset: {host_info.line_reset}")
    _log.debug(f"usb_timeout: {host_info.usb_timeout}")
    _log.debug(f"test_tx_count: {host_info.test_tx_count}")
    _log.debug(f"dme_value: {host_info.dme_value}")
    _log.debug(f"adapt_state: {host_info.adapt_state}")
    _log.debug(f"usb_error_code: {host_info.usb_error_code}")
    _log.debug(f"usb_int_evt_0[0]: {host_info.usb_int_evt_0[0]}")
    _log.debug(f"usb_int_evt_0[1]: {host_info.usb_int_evt_0[1]}")
    _log.debug(f"usb_int_evt_0[2]: {host_info.usb_int_evt_0[2]}")
    _log.debug(f"usb_int_evt_0[3]: {host_info.usb_int_evt_0[3]}")
    _log.debug(f"usb_int_evt_1[0]: {host_info.usb_int_evt_1[0]}")
    _log.debug(f"usb_int_evt_1[1]: {host_info.usb_int_evt_1[1]}")
    _log.debug(f"usb_int_evt_1[2]: {host_info.usb_int_evt_1[2]}")
    _log.debug(f"usb_int_evt_1[3]: {host_info.usb_int_evt_1[3]}")
    _log.debug(f"usb_err_count_0: {host_info.usb_err_count_0}")
    _log.debug(f"usb_err_count_1: {host_info.usb_err_count_1}")
    _log.debug(f"usb_err_count_2: {host_info.usb_err_count_2}")
    _log.debug(f"usb_err_count_3: {host_info.usb_err_count_3}")
    _log.debug(f"ps2808_type: {host_info.usb_int_evt_1}")
    _log.debug(f"support_hpb_size: {host_info.usb_err_count_0}")
    _log.debug(f"dll_enable: {host_info.usb_err_count_1}")
    _log.debug(f"bulkout_ep_offset: {host_info.usb_err_count_2}")
    _log.debug(f"bulin_ep_offset: {host_info.bulin_ep_offset}")
    _log.debug(f"line_reset_count: {host_info.line_reset_count}")
    _log.debug(f"scsi_retry_count: {host_info.scsi_retry_count}")
    _log.debug(f"usb_hw_err_count_0: {host_info.usb_hw_err_count_0}")
    _log.debug(f"usb_hw_err_count_1: {host_info.usb_hw_err_count_1}")
    _log.debug(f"usb_hw_err_count_2: {host_info.usb_hw_err_count_2}")
    _log.debug(f"serial_number: {host_info.serial_number}")
    _log.debug(f"tester_usb_timeout: {host_info.tester_usb_timeout}")
    _log.debug(f"builddate_unix_timestamp: {host_info.builddate_unix_timestamp}")
    _log.debug(f"commit_hash: {host_info.commit_hash}")
    _log.debug(f"customer_sdk_ver1: {host_info.customer_sdk_ver1}")
    _log.debug(f"customer_sdk_ver2: {host_info.customer_sdk_ver2}")
    _log.debug(f"customer_sdk_minor: {host_info.customer_sdk_minor}")
    _log.debug(f"customer_sdk_minor2: {host_info.customer_sdk_minor2}")
    _log.debug(f"dll_ver1: {host_info.dll_ver1}")
    _log.debug(f"dll_ver2: {host_info.dll_ver2}")
    _log.debug(f"usb_speed: {host_info.usb_speed}")
    _log.debug(f"dcmd23_flag: {host_info.dcmd23_flag}")
    _log.debug(f"dme_req_time_start: {host_info.dme_req_time_start}")
    _log.debug(f"dme_req_time_end: {host_info.dme_req_time_end}")
    _log.debug(f"powermode_time_start: {host_info.powermode_time_start}")
    _log.debug(f"powermode_time_end: {host_info.powermode_time_end}")
    _log.debug(f"hibernate_time_start: {host_info.hibernate_time_start}")
    _log.debug(f"hibernate_time_end: {host_info.hibernate_time_end}")
    _log.debug(f"dme_timeout_occur: {host_info.dme_timeout_occur}")
    _log.debug(f"minimum_detect_busy_time: {host_info.minimum_detect_busy_time}")
    _log.debug(f"hyper_ram_error: {host_info.hyper_ram_error}")
    _log.debug(f"usb_err_st_0: {host_info.usb_err_st_0}")
    _log.debug(f"usb_err_st_1: {host_info.usb_err_st_1}")
    _log.debug(f"usb_err_st_2: {host_info.usb_err_st_2}")
    _log.debug(f"tester_hw_din_limit: {host_info.tester_hw_din_limit}")
    _log.debug(f"reserved: {host_info.reserved}")
    _log.debug(f"scsi_0x79_error_code: {host_info.scsi_0x79_error_code}")
    _log.debug(f"script_sdk_parameter_error: {host_info.script_sdk_parameter_error}")
    return host_info

VCC_STD_UFS3X = 2.5
VCCQ_STD = 1.3
VCCQ2 = 1.8
def host_init(rest_type = 0, vcc = VCC_STD_UFS3X, vccq = VCCQ_STD, vccq2 = VCCQ2):
    _log.debug('host_init')
    _sdk.host_initial(rest_type)
    
    _log.debug(f"switch vcc val = {vcc}")
    try:
        _sdk.switch_voltage_value(vcc, lib.PowerChannel.VCC.value)
    except lib.exception.DLL_ERROR as e:
        vcc_voltage = _sdk.measure_voltage(lib.VoltageChannel.VCC.value)
        _log.debug(f"Target VCC = {vcc:.2f}, Measure VCC =  = {vcc_voltage:.2f}")
        raise e
    
    _log.debug(f"switch vccq val = {vccq}")
    try:
        _sdk.switch_voltage_value(vccq, lib.PowerChannel.VCCQ.value)
    except lib.exception.DLL_ERROR as e:
        vccq_voltage = _sdk.measure_voltage(lib.VoltageChannel.VCCQ.value)
        _log.debug(f"Target VCC = {vccq:.2f}, Measure VCC =  = {vccq_voltage:.2f}")
        raise e
    
    _log.debug(f"switch vccq2 val = {vccq2}")
    try:
        _sdk.switch_voltage_value(vccq2, lib.PowerChannel.VCCQ2.value)
    except lib.exception.DLL_ERROR as e:
        vccq2_voltage = _sdk.measure_voltage(lib.VoltageChannel.VCCQ2.value)
        _log.debug(f"Target VCC = {vccq2:.2f}, Measure VCC =  = {vccq2_voltage:.2f}")
        raise e

    _log.debug("power on all channel")
    _sdk.power_control(lib.Power_Control.POWER_ON.value, lib.Power_Channel.POWER_CHANNEL_ALL.value)

def init_device_to_default():
    get_dll_version()
    host_info = get_host_info()
    if(host_info.dll_enable == False):
        _log.warning('DLL is not enabled, init')
        dll_init()
    host_init(lib.HostInit.TESTER_POWER_OFF.value)
