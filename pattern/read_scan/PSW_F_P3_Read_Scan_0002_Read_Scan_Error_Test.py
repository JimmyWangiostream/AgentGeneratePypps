import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.read_scan.mutual_fun import *
from typing import Any
import time
from enum import auto

class Pattern(UFSTC):
    def pre_process(self) -> None:
        leave_inhibition_mode()
        config_lun(normal_list=[0], em1_list=[1])
        _flash_setting = api.get_flash_setting()
        _fw_geometry = api.get_fw_geometry()
        self.max_ce = _flash_setting.Max_Fdevice
        self.max_plane = _flash_setting.Plane_Per_Die
        self.pageline_block = self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
        self.WL_block = self.pageline_block * 4 * 3
        self.tlc_vb_size = (_fw_geometry.l88_vb_size_u1 * 512 // 4096)
        _, self.mConfig_bkup = project_api.get_mConfig_data()
        self.mConfig_bkup.payload[0:7] = "MCONFIG".encode("ascii")
        pass

    def step1(self) -> None:
        class disable_case(IntEnum):
            disable_by_vu = auto()
            disable_PAGE_TYPE_SELECT_ALL = auto()
            disable_PAGE_TYPE_SELECT_SOME = auto()
            diable_TLC_data_block = auto()
            disable_SUBBLOCK_SELECT_0 = auto()
            disable_SUBBLOCK_SELECT_1 = auto()
            disable_SUBBLOCK_SELECT_2 = auto()
            disable_SUBBLOCK_SELECT_3 = auto()
            set_TEMP_LOW = auto()
            set_TEMP_HIGHT = auto()

        for test in disable_case:
            logger.info(f'===================== TestCase: {test.name} =====================')
            SB_offset = 0
            if test == disable_case.disable_by_vu:
                project_api.set_Enable_Disable_Read_Scan(enable=0)
            else:
                temp_mconfig = project_api.mConfig(self.mConfig_bkup.payload.copy())
                if test == disable_case.disable_PAGE_TYPE_SELECT_ALL:
                    temp_mconfig.PAGE_TYPE_SELECT.value &= ~api.BIT0
                    temp_mconfig.PAGE_TYPE_SELECT.value &= ~api.BIT1
                    temp_mconfig.PAGE_TYPE_SELECT.value &= ~api.BIT2
                elif test == disable_case.disable_PAGE_TYPE_SELECT_SOME:
                    # temp_mconfig.PAGE_TYPE_SELECT.value &= ~api.BIT0
                    temp_mconfig.PAGE_TYPE_SELECT.value &= ~api.BIT1
                    temp_mconfig.PAGE_TYPE_SELECT.value &= ~api.BIT2
                elif test == disable_case.diable_TLC_data_block:
                    temp_mconfig.TLC_data_block.value &= ~api.BIT1
                elif test == disable_case.disable_SUBBLOCK_SELECT_0:
                    temp_mconfig.SUBBLOCK_SELECT.value &= ~api.BIT0
                    SB_offset=0
                elif test == disable_case.disable_SUBBLOCK_SELECT_1:
                    temp_mconfig.SUBBLOCK_SELECT.value &= ~api.BIT1
                    SB_offset=1
                elif test == disable_case.disable_SUBBLOCK_SELECT_2:
                    temp_mconfig.SUBBLOCK_SELECT.value &= ~api.BIT2
                    SB_offset=2
                elif test == disable_case.disable_SUBBLOCK_SELECT_3:
                    temp_mconfig.SUBBLOCK_SELECT.value &= ~api.BIT3
                    SB_offset=3
                elif test == disable_case.set_TEMP_LOW:
                    temp_mconfig.TEMP_LOW.value = 254
                    temp_mconfig.TEMP_HIGH.value = 255
                elif test == disable_case.set_TEMP_HIGHT:
                    temp_mconfig.TEMP_LOW.value = 0
                    temp_mconfig.TEMP_HIGH.value = 1
                project_api.set_mConfig_data(mConfig=temp_mconfig)
                api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
            
            logger.flow(1, 'reconfig to Erase all data')
            self.reconfig_lun()
            self.write_record = api.get_empty_write_record()
        
            logger.flow(2, 'Write TLC data up to 15 WL')
            self.lba = 0
            total_size = 15 * self.WL_block
            api.sequential_write(lun=0, start_lba=self.lba, total_size=total_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            self.lba += total_size
            
            logger.flow(3, 'inject UECC in WL3')
            self.VB, pca = get_PCA_VB_and_print(lun=0, lba=self.WL_block*3+1 + SB_offset*self.pageline_block*3)

            inject_UECC(pca=pca)
            
            logger.flow(4, 'Write TLC data up to 16 WL')
            total_size = 16 * self.WL_block - self.lba
            api.sequential_write(lun=0, start_lba=self.lba, total_size=total_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            self.lba += total_size
            
            logger.flow(5, 'read status in vu 40BF and check UECC detected')
            status = project_api.check_if_current_VB_scan_in_progress_completed(VB=self.VB)
            if test in [disable_case.disable_PAGE_TYPE_SELECT_SOME,
                        disable_case.disable_SUBBLOCK_SELECT_0,
                        disable_case.disable_SUBBLOCK_SELECT_1,
                        disable_case.disable_SUBBLOCK_SELECT_2,
                        disable_case.disable_SUBBLOCK_SELECT_3,]:
                if status != 1:
                    logger.error_lb(f'check status in vu 40BF')
                    logger.error_fp(f'expect status equal to 1 when read scan enable, but current value = {status}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                error_detected_WLs = project_api.get_gc_read_scan_released_scan_pageline()
                logger.info(f'error_detected_WLs = {error_detected_WLs}')
                if len(error_detected_WLs) == 0:
                    logger.error_lb(f'check error_detected_WLs in vu 40BF')
                    logger.error_fp(f'expect error_detected_WLs not equal to 0 when read scan trigger, but current value = {len(error_detected_WLs)}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                if 3 not in error_detected_WLs:
                    logger.error_lb(f'check error_detected_WLs in vu 40BF')
                    logger.error_fp(f'expect error_detected_WLs equal to 3 when read scan {test.name}, but current value = {error_detected_WLs}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                if status != 0:
                    logger.error_lb(f'check status in vu 40BF')
                    logger.error_fp(f'expect status equal to 0 when read scan disable, but current value = {status}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                error_detected_WLs = project_api.get_gc_read_scan_released_scan_pageline()
                if len(error_detected_WLs) != 0:
                    logger.error_lb(f'check error_detected_WLs in vu 40BF')
                    logger.error_fp(f'expect error_detected_WLs equal to 0 when read scan disable, but current value = {len(error_detected_WLs)}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(6, 'recover modify')
            project_api.set_Enable_Disable_Read_Scan(enable=1)
            project_api.set_mConfig_data(mConfig=self.mConfig_bkup)
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
            pass
        pass
    
    def post_process(self) -> None:
        pass
            
    def reconfig_lun(self) -> None:
        config_descs = api.get_config_descriptors(print=False)
        for index in range(4):
            config_descs[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
        for index in range(4):
            api.push_write_config(config_descs[index], index=index)
        ExecuteCMD.send()
        return
    

run = Pattern().run
if __name__ == "__main__":
    run()