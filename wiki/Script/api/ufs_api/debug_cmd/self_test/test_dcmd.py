from Script import api
from Script.api.self_test.base import ApiTestBase
from Script.api import shared

_log = shared.logger

class TestDcmd5(ApiTestBase):
    def dcmd5_init(self) -> None:
        _log.debug("Excute Dcmd5")

        arg = api.Set_Dcmd5_Arg()
        arg.ssu_powerdown = 0
        arg.reset_type = api.Dcmd5ResetType.HW_RESET
        arg.read_boot_data = 0
        arg.spd_change_af_init = 0
        arg.spd_change_af_link = 0
        arg.ssu_active_af_init = 2
        arg.read_data = 0

        data = api.Set_Dcmd5_Data()
        data.boot_lba = 0
        data.ref_clk = 0
        data.mode = 1
        data.gear = 4
        data.lane = 2
        data.hs_rate = 27 # follow by c code
        dcmd5 = api.Dcmd5(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=False, 
                  speed_change=api.Dcmd5SpeedChange(api.SpeedChangeTiming.AFTER_INIT, 
                            api.SpdChgPowerMode.SLOW, 
                            api.SpdChgGear.GEAR_1, 
                            api.SpdChgLane.LANE_2, 
                            api.SpdChgHsRate.RATE_B, 
                            api.RefClk.MHZ_26_0),
                    ssu_active=api.Dcmd5SsuActive.EXIT_SLEEP,
                    read_boot=None,
                    read_data=None)
        dcmd5.set_debug_cmd5()
        rsp = dcmd5.get_debug_cmd5()

        _log.debug(f"status: {rsp.status}")
        _log.debug(f"device_init_flag: {rsp.device_init_flag}")
        _log.debug(f"ssu_error_code: {rsp.ssu_error_code}")
        _log.debug(f"generic_error_code: {rsp.generic_error_code}")
        _log.debug(f"boot_error_code: {rsp.boot_error_code}")
        _log.debug(f"boot_data_crc: {rsp.boot_data_crc}")
        _log.debug(f"read_data_crc: {rsp.read_data_crc}")
        _log.debug(f"device_init_flag: {rsp.device_init_flag}")
        _log.debug(f"dcmd5_total_time: {rsp.dcmd5_total_time}")
        _log.debug(f"ssu_power_down_total_time: {rsp.ssu_power_down_total_time}")
        _log.debug(f"link_startup_total_time: {rsp.link_startup_total_time}")
        _log.debug(f"power_change_time_after_link: {rsp.power_change_time_after_link}")
        _log.debug(f"nop_out_total_time: {rsp.nop_out_total_time}")
        _log.debug(f"boot_data_read_total_time: {rsp.boot_data_read_total_time}")
        _log.debug(f"device_ready_time: {rsp.device_ready_time}")
        _log.debug(f"power_change_time_after_init: {rsp.power_change_time_after_init}")
        _log.debug(f"ssu_active_total_time: {rsp.ssu_active_total_time}")
        _log.debug(f"read_data_total_time: {rsp.read_data_total_time}")
        _log.debug(f"nop_out_time_after_initial: {rsp.nop_out_time_after_initial}")
        _log.debug(f"time_stamp_start: {rsp.time_stamp_start}")
        _log.debug(f"time_stamp_end: {rsp.time_stamp_end}")
