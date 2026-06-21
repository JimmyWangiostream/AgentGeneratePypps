import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.rain.mutual_fun import *

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.TestNormalLun, self.TestEM1Lun, self.TestWBLun, self.flash_setting, self.fw_geometry = rain_pattern_precondition()
        self.max_ce, self.max_plane, self.max_pageline = get_geometry_parameter()
        self.write_record = api.get_empty_write_record()
        pass

    def step1(self) -> None:
        for testMode in [TestMode.TEST_TLC, TestMode.TEST_SLC, TestMode.TEST_WB, TestMode.TEST_L1, TestMode.TEST_LOG, TestMode.TEST_PTE]:
            SLC_en = testMode != TestMode.TEST_TLC
            lun, mode_str = get_general_parameter(testMode)            
            logger.info(f'============ Test {mode_str} VB ============')
            reconfig_to_erase_all_lun(self.write_record)
            logger.flow(1, f'Write {mode_str} data')
            if testMode == TestMode.TEST_WB:
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                
            if testMode == TestMode.TEST_LOG:
                self.ssu_sleep_and_active()
                cursor = get_specific_open_vb_cursor(testMode)
            else:
                last_lba, cursor = write_data_more_than_N_page(page_cnt=2, lun=lun, testMode=testMode, write_record=self.write_record)
            rsp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
            project_api.print_object_info_ai(open_vb_information)
            invalid_plane_list = get_invalid_plane_list()
            pageline = cursor.first_empty_physical_page.value
            block = cursor.logical_vb.value
            pca = project_api.physical_address_info()
            pca.die.value = 0
            pca.plane.value = 1 if invalid_plane_list[block] == 0 else 0
            pca.physical_block_number_w_BBT.value = block
            pca.page.value = pageline
                
            logger.flow(2, f'inject UECC')
            inject_UECC(pca=pca, SLC_enable=SLC_en)
            
            logger.flow(3, f'SPOR to trigger parity rebuild')
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
            
            logger.flow(4, f'direct read and check if UECC')
            dire_read_payload = direct_read_raw_data_and_check_status(pca=pca, SLC_enable=SLC_en, expect_status= project_api.ReadStatus.UECC, REH_Enable=True)
            pass

    def post_process(self) -> None:
        pass
    
    def ssu_sleep_and_active(self) -> None:
        ssu = ExecuteCMD.StartStopUnit()
        ssu.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0)
        ssu.set_option(wait_queue_empty=True)
        ExecuteCMD.enqueue(ssu)
        ssu.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0)
        ssu.set_option(wait_queue_empty=True)
        ExecuteCMD.enqueue(ssu)
        ExecuteCMD.send(clear_on_success=True)
        pass


run = Pattern().run
if __name__ == "__main__":
    run()