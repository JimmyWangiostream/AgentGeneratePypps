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

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.TestNormalLun = 0
        self.TestLBA       = 0
        self.TestSize      = DATA_SIZE_4K_BYTE
        self.ExpectedCRC   = 0

        _, StuckThreshold = project_api.issue_40FA_read_thermal_stuck_threshold()
        logger.info(f"{StuckThreshold.threshold_for_low_thermal_stuck_area.value=}")
        logger.info(f"{StuckThreshold.threshold_for_high_thermal_stuck_area.value=}")
        self.TpThreshold = [{"low": 180, "high": StuckThreshold.threshold_for_high_thermal_stuck_area.value},  # for cold stuck
                            {"low": StuckThreshold.threshold_for_low_thermal_stuck_area.value, "high": 80}]    # for hot stuck
        
        f = ExecuteCMD.FormatUnit()
        f.assign(lun=api.WellKnownLUN.UFS_DEVICE, longlist=0, cmplist=0)
        ExecuteCMD.enqueue(f)
        ExecuteCMD.send(clear_on_success=True)

    def step1(self) -> None:
        tp_threshold = WriteThermalStuckThreshold()

        logger.flow(1, "Send VU D0F3 to disable Hard TP")
        project_api.issue_D0F3_disable_thermal_stuck(ThermalProtectionType.TP_DISABLE, HardThermalProtectionType.TP_HARD_HOT_COLD)
            
        for thres in self.TpThreshold:        
            logger.flow(2, f"Send VU D0F1 to modify HIGH/LOW threshold, LOW={thres['low']}, HIGH={thres['high']}")  # UFS temperature = real + 80
            tp_threshold.low_thermal_protection_threshold.value = thres['low']
            tp_threshold.high_thermal_protection_threshold.value = thres['high']
            project_api.issue_D0F1_write_thermal_stuck_threshold(tp_threshold)

            logger.flow(3, "Write 4k data and read compare written data")
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=self.TestNormalLun, lba=self.TestLBA, length=self.TestSize, fua=1)
            ExecuteCMD.enqueue(write10)
            ExecuteCMD.send(clear_on_success=False)

            write_record = api.get_empty_write_record()
            for cmd in ExecuteCMD._cmd_list:
                api.save_write_info_by_cmd(cmd, write_record)
            ExecuteCMD.clear()

            api.read_compare(write_record, api.CompareMethod.HW_COMPARE)

        logger.flow(4, "Send VU D0F1 to restore HIGH/LOW threshold")
        tp_threshold.low_thermal_protection_threshold.value = self.TpThreshold[1]['low']
        tp_threshold.high_thermal_protection_threshold.value = self.TpThreshold[0]['high']
        project_api.issue_D0F1_write_thermal_stuck_threshold(tp_threshold)
        
        logger.flow(5, "Send VU D0F3 to enable Hard TP")
        project_api.issue_D0F3_disable_thermal_stuck(ThermalProtectionType.TP_ENABLE, HardThermalProtectionType.TP_HARD_HOT_ONLY)
        
        logger.flow(6, "Send VU D0FC to set shipping mode")
        project_api.set_device_state(Device_state=1, only_in_ram=True)

        logger.flow(7, "Send VU D0F3 to disable Hard TP expect no effect")
        project_api.issue_D0F3_disable_thermal_stuck(ThermalProtectionType.TP_DISABLE, HardThermalProtectionType.TP_HARD_HOT_ONLY)

        logger.flow(8, "Send VU D0F1 to modify TD_TOOLOW_AREA_ENTER = 100C")
        tp_threshold.low_thermal_protection_threshold.value = self.TpThreshold[0]['low']
        tp_threshold.high_thermal_protection_threshold.value = self.TpThreshold[0]['high']
        project_api.issue_D0F1_write_thermal_stuck_threshold(tp_threshold)

        logger.flow(9, "Write 4k data and read compare written data")
        write10 = ExecuteCMD.Write10()
        write10.assign(lun=self.TestNormalLun, lba=self.TestLBA, length=self.TestSize, fua=1)
        ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=False)

        write_record = api.get_empty_write_record()
        for cmd in ExecuteCMD._cmd_list:
            api.save_write_info_by_cmd(cmd, write_record)
        ExecuteCMD.clear()

        api.read_compare(write_record, api.CompareMethod.HW_COMPARE)
        
        logger.flow(10, 'Send VU 0xD0F1 to modify TD_SUPER_HIGH_AREA_ENTER = 0C')            
        tp_threshold.low_thermal_protection_threshold.value = self.TpThreshold[1]['low']
        tp_threshold.high_thermal_protection_threshold.value = self.TpThreshold[1]['high']
        project_api.issue_D0F1_write_thermal_stuck_threshold(tp_threshold)

        logger.flow(11, 'Write 4k data should no response')
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
            
            logger.info("Check assert via DME Get")
            assert_code = api.get_fw_assert_number()
            if assert_code == 0x0:
                logger.error_fp(f'Should record assert code')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(12, f"Power cycle to recover device")
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
        
        logger.flow(13, "Read data should not be written")
        read10 = ExecuteCMD.Read10()
        read10.assign(lun=self.TestNormalLun, lba=self.TestLBA + self.TestSize, length=self.TestSize)
        read10.set_sw_cmp(crc32=self.ExpectedCRC)
        ExecuteCMD.enqueue(read10)
        ExecuteCMD.send(clear_on_success=True)

        # logger.flow(14, "Send VU 4080 to get TP assert code")


    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()