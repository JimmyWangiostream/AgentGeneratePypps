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
        for testMode in [TestMode.TEST_PTE, TestMode.TEST_L1]:
            SLC_en = testMode != TestMode.TEST_TLC
            Table_and_S_CHK_rain = cast(int, project_api.RainVB.ALL)
            Host_Permanent_Rain = cast(int, project_api.RainVB.ALL)
            Host_Simple_Rain = cast(int, project_api.RainVB.ALL)
            host_full_block_protection_rain = cast(int, project_api.RainVB.ALL)
            
            lun, mode_str = get_general_parameter(testMode)            
            Rain_in_last_valid_page, data_recovery = get_rain_enable_disable_parameter(testMode)       
            rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode)
            logger.info(f'============ Test {mode_str} VB ============')
            logger.flow(1, f'write {mode_str} data more than 1 pageline')
            last_lba, cursor = write_data_more_than_N_pageline(pageline_cnt=1, lun=lun, testMode=testMode, write_record=self.write_record)
            
            logger.flow(2, f'Inject UECC on the written page')
            invalid_plane_list = get_invalid_plane_list()
            while True:
                ce_plane = random.randint(0, self.max_ce*self.max_plane-1)
                if invalid_plane_list[cursor.physical_vb.value] != ce_plane:
                    break
            pca = project_api.physical_address_info()
            pca.die.value = ce_plane // self.max_plane
            pca.plane.value = ce_plane % self.max_plane
            pca.physical_block_number_w_BBT.value = cursor.physical_vb.value
            pca.page.value = cursor.first_empty_physical_page.value - 1
            inject_UECC(pca=pca, SLC_enable=SLC_en)          
            
            logger.flow(3, f'issue VU D08B BYTE 12 Table and S_CHK (L1) rain Disable BIT4/5')
            Table_and_S_CHK_rain &= ~cast(int, data_recovery)
            project_api.issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain, Host_Permanent_Rain, Host_Simple_Rain, host_full_block_protection_rain)
            _, rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
            print_rain_info(rain_info=rain_info)
            
            logger.flow(4, f'read status expect UECC')
            dire_read_payload = direct_read_raw_data_and_check_status(pca=pca, SLC_enable=SLC_en, expect_status= project_api.ReadStatus.UECC, REH_Enable=True)
            
            logger.flow(5, f'issue VU D08B BYTE 12 Table and S_CHK (L1) rain Enable BIT4/5')
            Table_and_S_CHK_rain |= cast(int, data_recovery)
            project_api.issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain, Host_Permanent_Rain, Host_Simple_Rain, host_full_block_protection_rain)
            _, rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
            print_rain_info(rain_info=rain_info)
            
            logger.flow(6, f'read compare expect pass')
            read_compare_rain_result(write_record=self.write_record, expect_error=False)
            
            logger.flow(7, f'issue VU D08B BYTE 12 Table and S_CHK (L1) rain Disable BIT0/1')
            Table_and_S_CHK_rain &= ~cast(int, Rain_in_last_valid_page)
            project_api.issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain, Host_Permanent_Rain, Host_Simple_Rain, host_full_block_protection_rain)
            _, rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
            print_rain_info(rain_info=rain_info)
            
            logger.flow(8, f'direct read last valid page not parity')
            pageline_cnt = cursor.first_empty_physical_page.value+2
            last_lba, cursor = write_data_more_than_N_pageline(pageline_cnt=pageline_cnt, lun=lun, testMode=testMode, write_record=self.write_record)
            vb = cursor.logical_vb.value
            pageline = cursor.first_empty_physical_page.value-1
            invalid_plane_list = get_invalid_plane_list()
            max_ce_plane = self.max_plane * self.max_ce - 1
            if invalid_plane_list[vb] == max_ce_plane:
                max_ce_plane -= 1
            direc_read_pca = PCA()
            direc_read_pca.l0_op = 0
            direc_read_pca.b4_mode = 2 if testMode == TestMode.TEST_TLC else 1
            direc_read_pca.b5_ce = max_ce_plane//self.max_plane
            direc_read_pca.b6_plane = max_ce_plane%self.max_plane
            direc_read_pca.b11_block_h = (vb>>8) & 0xFF
            direc_read_pca.b10_block_l = vb & 0xFF
            direc_read_pca.l12_fpage = pageline<<5
            dire_read_payload = api.direct_read(pca=direc_read_pca, block_count=4, include_FW_spare=True)
            if testMode == TestMode.TEST_L1:
                FW_spare_mark = dire_read_payload[0x4004]
                if FW_spare_mark != 0x83:
                    dumpfile(f"direct_read_data.bin", dire_read_payload)
                    logger.error_lb(f'check last valid page after disable rand encode')
                    logger.error_fp(f'expect last valid page not parity, but FW spare mark = {FW_spare_mark} not 0x83(DUMMY), result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                FW_spare_mark = int.from_bytes(dire_read_payload[0x4000:0x4004], 'little')
                if FW_spare_mark != 0x44494152:
                    dumpfile(f"direct_read_data.bin", dire_read_payload)
                    logger.error_lb(f'check last valid page after disable rand encode')
                    logger.error_fp(f'expect last valid page not parity, but FW spare mark = {FW_spare_mark} not 0x44494152(FW Mark), result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            x=0
        pass
    
    def post_process(self) -> None:
        pass
    

run = Pattern().run
if __name__ == "__main__":
    run()