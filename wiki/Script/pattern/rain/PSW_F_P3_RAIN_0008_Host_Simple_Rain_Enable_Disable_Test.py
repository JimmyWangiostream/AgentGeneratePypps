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
        _, rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
        print_rain_info(rain_info=rain_info)
        
        pass

    def step1(self) -> None:
        for testMode in [TestMode.TEST_TLC, TestMode.TEST_SLC, TestMode.TEST_WB]:
            reconfig_to_erase_all_lun(write_record=self.write_record)
            polling_bkops_idle()
            project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.DisableEnqueueInRefreshBQ)
            SLC_en = testMode != TestMode.TEST_TLC
            Table_and_S_CHK_rain = cast(int, project_api.RainVB.ALL)
            Host_Permanent_Rain = cast(int, project_api.RainVB.ALL)
            Host_Simple_Rain = cast(int, project_api.RainVB.ALL)
            host_full_block_protection_rain = cast(int, project_api.RainVB.ALL)
            
            lun, mode_str = get_general_parameter(testMode)            
            Rain_in_SRAM, data_recovery = get_rain_enable_disable_parameter(testMode)            
            rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode)
            logger.info(f'============ Test {mode_str} VB ============')
            if rain_user == project_api.RainUser.WB_RAIN:
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            
            prog_unit = 3 if testMode == TestMode.TEST_TLC else 1
            
            logger.flow(1, f'write {mode_str} data')
            lba = 0
            total_len = self.max_plane * api.BLOCK4K_SIZE_16K_BYTE * prog_unit
            api.sequential_write(lun=lun, start_lba=lba, total_size=total_len, chunk_size=total_len, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            cursor = get_specific_open_vb_cursor(testMode, print_info=True)
            lba += total_len
            last_lba = lba -1
                            
            logger.flow(2, f'Inject UECC on the written page')
            pca = get_PCA_and_print(lun=lun, lba=last_lba//2)
            inject_UECC(pca=pca, SLC_enable=SLC_en)
            
            logger.flow(3, f'issue VU D08B BYTE 14 Host Simple Rain Disable BIT4/5/6')
            Host_Simple_Rain &= ~cast(int, data_recovery)
            project_api.issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain, Host_Permanent_Rain, Host_Simple_Rain, host_full_block_protection_rain)
            _, rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
            print_rain_info(rain_info=rain_info)
            
            logger.flow(4, f'read status expect UECC')
            dire_read_payload = direct_read_raw_data_and_check_status(pca=pca, SLC_enable=SLC_en, expect_status= project_api.ReadStatus.UECC, REH_Enable=True)
            
            logger.flow(5, f'issue VU D08B BYTE 14 Host Simple Rain Enable BIT4/5/6')
            Host_Simple_Rain |= cast(int, data_recovery)
            project_api.issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain, Host_Permanent_Rain, Host_Simple_Rain, host_full_block_protection_rain)
            _, rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
            print_rain_info(rain_info=rain_info)
            
            logger.flow(6, f'read compare expect pass')
            read_compare_rain_result(write_record=self.write_record, expect_error=False)

            logger.flow(7, f'issue VU 4055 to get parity of each VB type')
            _, fw_spare_list, old_get_parity = project_api.issue_4055_to_get_rain_parity(rain_user=rain_user, group=prog_unit-1)
            _, fw_spare_list, get_recover_parity = project_api.issue_4055_to_get_rain_parity(rain_user=project_api.RainUser.RECOVER_USER, group=0)
            if get_recover_parity != old_get_parity:
                logger.error_lb(f'issue VU4055: parity from {rain_user.name} differs from RECOVER_USER')
                logger.error_fp(f'expect parity from {rain_user.name} == recover_parity from RECOVER_USER, but {rain_user.name} parity = {format_bytearray(old_get_parity[0:8])}, RECOVER_USER parity = {format_bytearray(get_recover_parity[0:8])}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(8, f'issue VU D08B BYTE 14 Host Simple Rain Disable BIT0/1/2')
            Host_Simple_Rain &= ~cast(int, Rain_in_SRAM)
            project_api.issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain, Host_Permanent_Rain, Host_Simple_Rain, host_full_block_protection_rain)
            _, rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
            print_rain_info(rain_info=rain_info)
            
            logger.flow(9, f'Continue writing data until exceeding next same rain group')
            total_len = rain_goup_cnt * self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
            api.sequential_write(lun=lun, start_lba=lba, total_size=total_len, chunk_size=total_len, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            cursor = get_specific_open_vb_cursor(testMode, print_info=True)
            lba += total_len
            
            logger.flow(10, f'issue VU 4055 to check if parity has not changed')
            _, fw_spare_list, new_get_parity = project_api.issue_4055_to_get_rain_parity(rain_user=rain_user, group=prog_unit-1)
            if new_get_parity[0:8] != old_get_parity[0:8]:
                dumpfile("new_get_parity.txt", new_get_parity)
                dumpfile("old_get_parity.txt", old_get_parity)
                logger.error_lb(f'issue VU4055 to get parity')
                logger.error_fp(f'expect parity not change after disable rain, but new_get_parity = {format_bytearray(new_get_parity[0:8])}, old_get_parity = {format_bytearray(old_get_parity[0:8])}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            old_get_parity = new_get_parity
            
            logger.flow(11, f'issue VU D08B BYTE 14 Host Simple Rain Enable BIT0/1/2')
            Host_Simple_Rain |= cast(int, Rain_in_SRAM)
            project_api.issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain, Host_Permanent_Rain, Host_Simple_Rain, host_full_block_protection_rain)
            _, rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
            print_rain_info(rain_info=rain_info)
            
            logger.flow(12, f'Continue writing data until exceed next same rain group')
            total_len = rain_goup_cnt * self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
            api.sequential_write(lun=lun, start_lba=lba, total_size=total_len, chunk_size=total_len, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            cursor = get_specific_open_vb_cursor(testMode, print_info=True)
            
            logger.flow(13, f'issue VU 4055 to check if the parity calculation is correct')
            _, fw_spare_list, new_get_parity = project_api.issue_4055_to_get_rain_parity(rain_user=rain_user, group=prog_unit-1)
            if new_get_parity[0:8] == old_get_parity[0:8]:
                dumpfile("new_get_parity.txt", new_get_parity)
                dumpfile("old_get_parity.txt", old_get_parity)
                logger.error_lb(f'issue VU4055 to get parity')
                logger.error_fp(f'expect parity change after enable rain, but new_get_parity = {format_bytearray(new_get_parity[0:8])}, old_get_parity = {format_bytearray(old_get_parity[0:8])}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.EnableEnqueueInRefreshBQ)
            polling_bkops_idle()
        pass
    
    def post_process(self) -> None:
        pass
    

run = Pattern().run
if __name__ == "__main__":
    run()