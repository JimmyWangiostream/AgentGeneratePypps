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
import copy

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.TestNormalLun, self.TestEM1Lun, self.TestWBLun, self.flash_setting, self.fw_geometry = rain_pattern_precondition()
        self.max_ce, self.max_plane, self.max_pageline = get_geometry_parameter()
        self.write_record = api.get_empty_write_record()
        pass

    def step1(self) -> None:
        for testMode in [TestMode.TEST_TLC, TestMode.TEST_SLC, TestMode.TEST_WB, TestMode.TEST_PTE]:
            SLC_en = testMode != TestMode.TEST_TLC
            lun, mode_str = get_general_parameter(testMode)            
            rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode)
            logger.info(f'============ Test {mode_str} VB ============')
            logger.flow(1, f'Erase all data')
            reconfig_to_erase_all_lun(write_record=self.write_record)
            max_ce_plane = self.max_plane * self.max_ce - 1
            
            logger.flow(2, f'Write until {mode_str} VB has enough data')
            if rain_user == project_api.RainUser.WB_RAIN:
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                
            if testMode == TestMode.TEST_PTE:
                last_lba, cursor = write_data_more_than_N_pageline(pageline_cnt=1, lun=lun, testMode=testMode, write_record=self.write_record)
                pageline = cursor.first_empty_physical_page.value - 1
                vb = cursor.logical_vb.value
                invalid_plane_list = get_invalid_plane_list()
                if invalid_plane_list[vb] == max_ce_plane:
                    max_ce_plane -= 1
                pca = project_api.physical_address_info()
                pca.die.value = 0
                pca.plane.value = 1 if invalid_plane_list[vb] == 0 else 0
                pca.physical_block_number_w_BBT.value = vb
                pca.page.value = pageline
            else:
                last_lba, vb = create_closed_vb(testMode=testMode, lun=lun, write_record=self.write_record)
                pca = get_PCA_and_print(lun=lun, lba=last_lba)
            sorted_vb_dict = get_sorted_VB_list()
            
            logger.flow(3, f'inject UECC in last valid page')
            LVP_pca = copy.deepcopy(pca)
            LVP_pca.die.value = max_ce_plane//self.max_plane
            LVP_pca.plane.value = max_ce_plane%self.max_plane
            if testMode != TestMode.TEST_PTE:
                if testMode == TestMode.TEST_TLC:
                    last_pageline = 3311
                else:
                    last_pageline = 1103
                LVP_pca.page.value = last_pageline
            inject_UECC(pca=LVP_pca, SLC_enable=SLC_en)
            
            logger.flow(4, f'inject UECC in host block')
            inject_UECC(pca=pca, SLC_enable=SLC_en)

            logger.flow(5, f'read status expect UECC')
            dire_read_payload = direct_read_raw_data_and_check_status(pca=pca, SLC_enable=SLC_en, expect_status= project_api.ReadStatus.UECC, REH_Enable=True)
            pass

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()