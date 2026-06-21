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
        self.RestOption    = [api.Dcmd5ResetType.HW_RESET]

        f = ExecuteCMD.FormatUnit()
        f.assign(lun=api.WellKnownLUN.UFS_DEVICE, longlist=0, cmplist=0)
        ExecuteCMD.enqueue(f)
        ExecuteCMD.send(clear_on_success=True)

    def step1(self) -> None:
        _, StuckThreshold = project_api.issue_40FA_read_thermal_stuck_threshold()
        logger.info(f"{StuckThreshold.threshold_for_low_thermal_stuck_area.value=}")
        logger.info(f"{StuckThreshold.threshold_for_high_thermal_stuck_area.value=}")
        
        for reset_mode in self.RestOption:
            tp_threshold = WriteThermalStuckThreshold()

            logger.flow(1, "Send VU D0F3 to switch to HOT_COLD mode")
            project_api.issue_D0F3_disable_thermal_stuck(ThermalProtectionType.TP_ENABLE, HardThermalProtectionType.TP_HARD_HOT_COLD)

            logger.flow(2, "Send VU D0FC to set shipping mode")
            project_api.set_device_state(Device_state=1, only_in_ram=True)
            
            logger.flow(3, "Send VU D0F3 to switch to HOT_ONLY mode")
            project_api.issue_D0F3_disable_thermal_stuck(ThermalProtectionType.TP_ENABLE, HardThermalProtectionType.TP_HARD_HOT_ONLY)
            
            logger.flow(4, "Send VU D0F1 to modify TD_TOOLOW_AREA_ENTER = 100C")  # UFS temperature = real + 80
            tp_threshold.low_thermal_protection_threshold.value = 180
            tp_threshold.high_thermal_protection_threshold.value = StuckThreshold.threshold_for_high_thermal_stuck_area.value
            project_api.issue_D0F1_write_thermal_stuck_threshold(tp_threshold)

            logger.flow(5, "Write 4k data and read compare written data")
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=self.TestNormalLun, lba=self.TestLBA, length=self.TestSize, fua=1)
            ExecuteCMD.enqueue(write10)
            ExecuteCMD.send(clear_on_success=False)

            write_record = api.get_empty_write_record()
            for cmd in ExecuteCMD._cmd_list:
                api.save_write_info_by_cmd(cmd, write_record)
            ExecuteCMD.clear()

            api.read_compare(write_record, api.CompareMethod.HW_COMPARE)

            logger.flow(6, 'Send VU 0xD0F1 to modify TD_SUPER_HIGH_AREA_ENTER = 0C')  # UFS temperature = real + 80            
            tp_threshold.low_thermal_protection_threshold.value = StuckThreshold.threshold_for_low_thermal_stuck_area.value
            tp_threshold.high_thermal_protection_threshold.value = 80
            project_api.issue_D0F1_write_thermal_stuck_threshold(tp_threshold)

            logger.flow(7, 'Write 4k data should no response')
            try:
                write10 = ExecuteCMD.Write10()
                write10.assign(lun=self.TestNormalLun, lba=self.TestLBA + self.TestSize, length=self.TestSize, fua=1)
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
            
            logger.flow(8, f"Reset device to recover: [{reset_mode.name}]")
            if reset_mode == api.Dcmd5ResetType.HW_RESET:
                api.init_tester_to_unit_ready(reset_mode, powerdown=False)
            else:
                manual_rst_n()
            
            logger.flow(9, "Read data should not be written")
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=self.TestNormalLun, lba=self.TestLBA + self.TestSize, length=self.TestSize)
            read10.set_sw_cmp(crc32=self.ExpectedCRC)
            ExecuteCMD.enqueue(read10)
            ExecuteCMD.send(clear_on_success=True)

            # logger.flow(10, "Send VU 4080 to get TP assert code")


    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()