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
        logger.flow(1, f'Write TLC data 3 pages')
        lba = 0
        total_len = self.max_plane * api.BLOCK4K_SIZE_16K_BYTE * 3
        api.sequential_write(lun=self.TestNormalLun, start_lba=lba, total_size=total_len, chunk_size=total_len, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.last_lba = total_len -1
        pass
        
    def step2(self) -> None:
        logger.flow(2, f'Write SLC data to create Temp RAIN VB')
        api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=api.BLOCK4K_SIZE_4K_BYTE, chunk_size=api.BLOCK4K_SIZE_4K_BYTE, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)

    def step3(self) -> None:
        logger.flow(3, f'inject UECC in TMP RAIN VB and SPOR')
        cursor = get_specific_open_vb_cursor(testMode=TestMode.TEST_TMP_RAIN)
        self.inject_UECC_in_Temp_Rain_VB(cursor=cursor)
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
        pass
        
    def step4(self) -> None:
        logger.flow(4, f'Write TLC 4KB')
        api.sequential_write(lun=self.TestNormalLun, start_lba=self.last_lba +1, total_size=api.BLOCK4K_SIZE_4K_BYTE, chunk_size=api.BLOCK4K_SIZE_4K_BYTE, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
        pass

    def step5(self) -> None:
        logger.flow(5, f'inject UECC in host block')
        self.pca = get_PCA_and_print(lun=self.TestNormalLun, lba=0)            
        inject_UECC(pca=self.pca, SLC_enable=False)         

    def step6(self) -> None:
        logger.flow(6, f'direct read and check read status is UECC')
        dire_read_payload = direct_read_raw_data_and_check_status(pca=self.pca, SLC_enable=False, expect_status= project_api.ReadStatus.UECC, REH_Enable=True)
        pass

    def post_process(self) -> None:
        pass
    
    def inject_UECC_in_Temp_Rain_VB(self, cursor:api.OpenVBInfoUnit) -> None:
        block = cursor.logical_vb.value
        pageline = cursor.first_empty_physical_page.value
        invalid_plane_list = get_invalid_plane_list()
        max_ce_plane = self.max_plane * cursor.first_empty_CE.value + cursor.first_empty_plane.value
        for ce in range(self.max_ce):
            for plane in range(self.max_plane):
                ce_plane = self.max_plane * ce + plane
                if invalid_plane_list[block] == ce_plane:
                    continue
                if ce_plane >= max_ce_plane:
                    break
                pca = project_api.physical_address_info()
                pca.die.value = ce
                pca.plane.value = plane
                pca.physical_block_number_w_BBT.value = block
                pca.page.value = pageline
                inject_UECC(pca=pca, SLC_enable=True)
            

run = Pattern().run
if __name__ == "__main__":
    run()