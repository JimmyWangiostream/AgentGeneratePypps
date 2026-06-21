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
        self._param = shared.param
        pass

    def step1(self) -> None:
        for testMode in [TestMode.TEST_TLC, TestMode.TEST_SLC, TestMode.TEST_WB]:
            SLC_en = testMode != TestMode.TEST_TLC
            Table_and_S_CHK_rain = cast(int, project_api.RainVB.ALL)
            Host_Permanent_Rain = cast(int, project_api.RainVB.ALL)
            Host_Simple_Rain = cast(int, project_api.RainVB.ALL)
            host_full_block_protection_rain = cast(int, project_api.RainVB.ALL)
            
            lun, mode_str = get_general_parameter(testMode)            
            Rain_in_last_valid_page, data_recovery = get_rain_enable_disable_parameter(testMode)    
            rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode)
            logger.info(f'============ Test {mode_str} VB ============')
            
            logger.flow(1, f'issue VU D08B BYTE 13 Host Permanent Rain Disable BIT0/1/2')
            Host_Permanent_Rain &= ~cast(int, Rain_in_last_valid_page)
            project_api.issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain, Host_Permanent_Rain, Host_Simple_Rain, host_full_block_protection_rain)
            _, rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
            print_rain_info(rain_info=rain_info)
            
            if rain_user == project_api.RainUser.WB_RAIN:
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                
            if testMode == TestMode.TEST_TLC:
                last_pageline = 1111
            else:
                last_pageline = 1103
                
            logger.flow(2, f'write {mode_str} data 1 VB')
            last_lba, vb = create_closed_vb(testMode=testMode, lun=lun, write_record=self.write_record)
            
            logger.flow(3, f'direct read last valid page not parity')
            max_ce_plane = self.max_plane * self.max_ce - 1
            direc_read_pca = PCA()
            direc_read_pca.b4_mode = 2 if testMode == TestMode.TEST_TLC else 1
            direc_read_pca.b5_ce = max_ce_plane//self.max_plane
            direc_read_pca.b6_plane = max_ce_plane%self.max_plane
            direc_read_pca.b11_block_h = (vb>>8) & 0xFF
            direc_read_pca.b10_block_l = vb & 0xFF
            direc_read_pca.l12_fpage = last_pageline<<5
            dire_read_payload = api.direct_read(pca=direc_read_pca, block_count=4, include_FW_spare=True)
            FW_spare_mark = dire_read_payload[0x4004]
            if FW_spare_mark != 0x83:
                dumpfile(f"direct_read_data.bin", dire_read_payload)
                logger.error_lb(f'check last valid page after disable rand encode')
                logger.error_fp(f'expect last valid page no parity (DUMMY 0x83), but FW spare mark = {FW_spare_mark}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(4, f'POR')
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
            Host_Permanent_Rain = cast(int, project_api.RainVB.ALL)
            if rain_user == project_api.RainUser.WB_RAIN:
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                
            logger.flow(5, f'write {mode_str} data 1 VB')
            last_lba, vb = create_closed_vb(testMode=testMode, lun=lun, write_record=self.write_record)
            
            logger.flow(6, f'Inject UECC on the written page')
            pca = get_PCA_and_print(lun=lun, lba=api.BLOCK4K_SIZE_16K_BYTE)
            inject_UECC(pca=pca, SLC_enable=SLC_en)
            
            logger.flow(7, f'POR')
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
            
            logger.flow(8, f'issue VU D08B BYTE 13 Host Permanent Rain Disable BIT4/5/6')
            Host_Permanent_Rain &= ~cast(int, data_recovery)
            project_api.issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain, Host_Permanent_Rain, Host_Simple_Rain, host_full_block_protection_rain)
            _, rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
            print_rain_info(rain_info=rain_info)
            
            logger.flow(9, f'read status expect UECC')
            dire_read_payload = direct_read_raw_data_and_check_status(pca=pca, SLC_enable=SLC_en, expect_status= project_api.ReadStatus.UECC, REH_Enable=True)
            
            logger.flow(10, f'issue VU D08B BYTE 13 Host Permanent Rain Enable BIT4/5/6')
            Host_Permanent_Rain |= cast(int, data_recovery)
            project_api.issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain, Host_Permanent_Rain, Host_Simple_Rain, host_full_block_protection_rain)
            _, rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
            print_rain_info(rain_info=rain_info)
            
            logger.flow(11, f'read compare expect pass')
            read_compare_rain_result(write_record=self.write_record, expect_error=False)
        pass
    
    def post_process(self) -> None:
        pass
    

run = Pattern().run
if __name__ == "__main__":
    run()