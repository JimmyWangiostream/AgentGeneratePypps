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
from Script.project_api.functions import get_physical_layout


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.TestNormalLun, self.TestEM1Lun, self.TestWBLun, self.flash_setting, self.fw_geometry = rain_pattern_precondition()
        self.max_ce, self.max_plane, self.max_pageline = get_geometry_parameter()
        self.write_record = api.get_empty_write_record()
        invalid_plane_list = get_invalid_plane_list()
        
        pass

    def step1(self) -> None:
        for testMode in [TestMode.TEST_TLC, TestMode.TEST_SLC, TestMode.TEST_WB]:
            SLC_en = testMode != TestMode.TEST_TLC
            lun, mode_str = get_general_parameter(testMode)            
            rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode)
            logger.info(f'============ Test {mode_str} VB ============')
            logger.flow(1, f'Erase all data')
            reconfig_to_erase_all_lun(write_record=self.write_record)

            logger.flow(2, f'Write until {mode_str} VB has enough data')
            if rain_user == project_api.RainUser.WB_RAIN:
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            
            last_lba, cursor = write_data_more_than_N_pageline(pageline_cnt=rain_goup_cnt*3, lun=lun, testMode=testMode, write_record=self.write_record)
            lba = 0
            first_pca = get_PCA_and_print(lun=lun, lba=lba)
            first_lba = lba
            lba += rain_goup_cnt * self.max_ce* self.max_plane * api.BLOCK4K_SIZE_16K_BYTE + api.BLOCK4K_SIZE_16K_BYTE
            second_lba = lba
            second_pca = get_PCA_and_print(lun=lun, lba=lba)
            lba += rain_goup_cnt * self.max_ce* self.max_plane * api.BLOCK4K_SIZE_16K_BYTE + api.BLOCK4K_SIZE_16K_BYTE
            third_pca = get_PCA_and_print(lun=lun, lba=lba)
            third_lba = lba

            second_pageline = second_pca.page.value

            logger.flow(3, f'inject UECC in SWAP block')
            self.inject_UECC_in_swap(second_pageline, testMode)

            logger.flow(4, f'SPOR')
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
            
            logger.flow(5, f'inject UECC in host block')
            for pca in [first_pca, second_pca, third_pca]:
                inject_UECC(pca=pca, SLC_enable=SLC_en)

            logger.flow(6, f'direct read and check read status is UECC')
            read10 = ExecuteCMD.Read10()
            length = second_lba - first_lba
            read10.assign(lun=lun, lba=first_lba, length=length, fua=0)
            write_crc = api.find_record_to_gen_data_crc(lun, first_lba, length, self.write_record[lun])
            if write_crc != -1:
                read10.set_sw_cmp(crc32=write_crc)
            ExecuteCMD.enqueue(read10)
            ExecuteCMD.send(timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
            dire_read_payload = direct_read_raw_data_and_check_status(pca=second_pca, SLC_enable=SLC_en, expect_status= project_api.ReadStatus.UECC, REH_Enable=True)
            dire_read_payload = direct_read_raw_data_and_check_status(pca=third_pca, SLC_enable=SLC_en, expect_status= project_api.ReadStatus.UECC, REH_Enable=True)
            pass

    def post_process(self) -> None:
        pass
    
    def inject_UECC_in_swap(self, host_pageline:int, testMode:TestMode) -> None:
        swap_vb, pageline, _ = get_specific_RAIN_SWAP_vb(testMode=testMode)
        invalid_plane_list = get_invalid_plane_list()
        temp = host_pageline
        
        for pageline in range(1104):
            for ce in range(self.max_ce):
                for plane in range(self.max_plane):
                    ce_plane = ce * self.max_plane + plane
                    if ce_plane == invalid_plane_list[swap_vb]:
                        logger.info(f'skip ce{ce} plane{plane} due to invalid_plane')
                        continue
                    if temp == 0:
                        swap_pca = project_api.physical_address_info()
                        swap_pca.die.value = ce
                        swap_pca.plane.value = plane
                        swap_pca.physical_block_number_w_BBT.value = swap_vb
                        swap_pca.page.value = pageline
                        inject_UECC(pca=swap_pca, SLC_enable=True)
                        return
                    temp-=1
        return


run = Pattern().run
if __name__ == "__main__":
    run()