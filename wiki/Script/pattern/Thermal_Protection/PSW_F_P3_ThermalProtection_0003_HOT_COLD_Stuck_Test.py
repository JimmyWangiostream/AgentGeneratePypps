import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.project_api.thermal_protection_vu.structs import *
from Script.project_api.thermal_protection_vu.define import *
from Script.pattern.Thermal_Protection import *

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.TestNormalLun = 0
        self.TestLBA       = 0
        self.TestSize      = DATA_SIZE_4K_BYTE
        self.ExpectedCRC   = 0
        self.RestOption    = [api.Dcmd5ResetType.HW_RESET, api.Dcmd5ResetType.RESET_N]
        
        _, StuckThreshold = project_api.issue_40FA_read_thermal_stuck_threshold()
        logger.info(f"{StuckThreshold.threshold_for_low_thermal_stuck_area.value=}")
        logger.info(f"{StuckThreshold.threshold_for_high_thermal_stuck_area.value=}")
        self.TpThreshold = [{"low": 180, "high": StuckThreshold.threshold_for_high_thermal_stuck_area.value}, 
                            {"low": StuckThreshold.threshold_for_low_thermal_stuck_area.value, "high": 80}]

        f = ExecuteCMD.FormatUnit()
        f.assign(lun=api.WellKnownLUN.UFS_DEVICE, longlist=0, cmplist=0)
        ExecuteCMD.enqueue(f)
        ExecuteCMD.send(clear_on_success=True)

    def step1(self) -> None:
        for reset_mode in self.RestOption:
            for thres in self.TpThreshold:
                tp_threshold = WriteThermalStuckThreshold()
                
                logger.flow(1, "Send VU D0F3 to switch to HOT_COLD mode")
                project_api.issue_D0F3_disable_thermal_stuck(ThermalProtectionType.TP_ENABLE, HardThermalProtectionType.TP_HARD_HOT_COLD)
                
                logger.flow(2, f"Send VU D0F1 to modify HIGH/LOW threshold, LOW={thres['low']-80}C, HIGH={thres['high']-80}C")  # UFS temperature = real + 80
                tp_threshold.low_thermal_protection_threshold.value = thres['low']
                tp_threshold.high_thermal_protection_threshold.value = thres['high']
                project_api.issue_D0F1_write_thermal_stuck_threshold(tp_threshold)

                logger.flow(3, 'Write 4k data should no response')
                try:
                    write10 = ExecuteCMD.Write10()
                    write10.assign(lun=self.TestNormalLun, lba=self.TestLBA, length=self.TestSize, fua=1)
                    ExecuteCMD.enqueue(write10)
                    ExecuteCMD.send(clear_on_success=False)

                    logger.error_fp("FW should stuck")
                    raise PATTERN_ASSERT_UNEXPECTED_CONDITION
                
                except api.TIMEOUT_EXCEPTIONS:
                    ExecuteCMD.clear()
                    logger.info("Write timeout is expected")

                    logger.info("Check assert code via DME Get")
                    assert_code = api.get_fw_assert_number()
                    if assert_code == 0x0:
                        logger.error_fp(f'Should record assert code')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                logger.flow(4, f"Reset device to recover: [{reset_mode.name}]")
                if reset_mode == api.Dcmd5ResetType.HW_RESET:
                    api.init_tester_to_unit_ready(reset_mode, powerdown=False)
                else:
                    manual_rst_n()
                
                logger.flow(5, "Read data should not be written")
                read10 = ExecuteCMD.Read10()
                read10.assign(lun=self.TestNormalLun, lba=self.TestLBA + self.TestSize, length=self.TestSize)
                read10.set_sw_cmp(crc32=self.ExpectedCRC)
                ExecuteCMD.enqueue(read10)
                ExecuteCMD.send(clear_on_success=True)

                # logger.flow(6, "Send VU 4080 to get TP assert code")  
            
    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()