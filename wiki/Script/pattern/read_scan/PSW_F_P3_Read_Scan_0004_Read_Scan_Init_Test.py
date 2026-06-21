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
from Script.project_api.functions import get_physical_layout

class Pattern(UFSTC):
    def pre_process(self) -> None:
        leave_inhibition_mode()
        config_lun(normal_list=[0], em1_list=[1])
        self.write_record = api.get_empty_write_record()
        _flash_setting = api.get_flash_setting()
        _fw_geometry = api.get_fw_geometry()
        self.max_ce = _flash_setting.Max_Fdevice
        self.max_plane = _flash_setting.Plane_Per_Die
        self.pageline_block = self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
        self.WL_block = self.pageline_block * 4 * 3
        self.tlc_vb_size = (_fw_geometry.l88_vb_size_u1 * 512 // 4096)
        _, self.mConfig = project_api.get_mConfig_data()
        self.mConfig.payload[0:7] = "MCONFIG".encode("ascii")
        logger.info('Pre-process completed')
        pass
    
    def check_read_scan_trigger(self,vb:int,  expected_WL:List[int] = []) -> List[int]:
        status = project_api.check_if_current_VB_scan_in_progress_completed(VB=vb)
        if status != 1:
            logger.error_lb(f'check status in vu 40BF')
            logger.error_fp(f'expect status equal to 1 after init completed, but current value = {status}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        error_detected_WLs = project_api.get_gc_read_scan_released_scan_pageline()
        if len(error_detected_WLs) == 0:
            logger.error_lb(f'check error_detected_WLs in vu 40BF')
            logger.error_fp(f'expect error_detected_WLs not equal to 0 when read scan trigger, but current value = {len(error_detected_WLs)}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if expected_WL:
            result = all(item in error_detected_WLs for item in expected_WL)
            if not result:
                logger.error_lb(f'check error_detected_WLs in vu 40BF')
                logger.error_fp(f'expect error_detected_WLs include {expected_WL}, but current value = {error_detected_WLs}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        return error_detected_WLs
    
    def read_scan_en_disable(self, enable:bool) -> None:
        temp_mconfig = project_api.mConfig(self.mConfig.payload.copy())
        if enable:
            temp_mconfig.TLC_data_block.value |= api.BIT1
        else:
            temp_mconfig.TLC_data_block.value &= ~api.BIT1
        project_api.set_mConfig_data(mConfig=temp_mconfig)
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
        _, mConfig = project_api.get_mConfig_data()
        logger.info(f"mConfig.TLC_data_block.value = {mConfig.TLC_data_block.value}")
        
    def get_pca_and_check_not_remap(self, lun:int, lba:int) -> tuple[int, project_api.physical_address_info]:
        vb, pca = get_PCA_VB_and_print(lun=lun, lba=lba)
        while vb != pca.physical_block_number_w_BBT.value:
            lba += api.BLOCK4K_SIZE_16K_BYTE
            vb, pca = get_PCA_VB_and_print(lun=lun, lba=lba)
        return vb, pca
        

    def step1(self) -> None:
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        logger.flow(1, 'set mConfig to disable read scan')
        self.read_scan_en_disable(enable=False)
        
        logger.flow(2, 'write data up to WL15')
        lba = 0
        chunk_size = self.WL_block * self.mConfig.READ_SCAN_SAFE_AREA.value * 2
        total_size = chunk_size
        api.sequential_write(lun=0, start_lba=lba, total_size=total_size, chunk_size=chunk_size, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        lba += total_size
        
        logger.flow(3, 'rand inject UECC on 0~7 WL')
        randWL = random.randint(0, self.mConfig.READ_SCAN_SAFE_AREA.value) // 3 * 3
        vb, pca = self.get_pca_and_check_not_remap(lun=0, lba=self.WL_block * randWL)
        inject_UECC(pca=pca)
        _, WL_type, phy_WL, SubBlock, FlushGroup, TwoWLGroup, RainGoup = get_physical_layout(pageline=pca.page.value, block_type="TLC")
        
        logger.flow(4, 'set mConfig to enable read scan and POR')
        self.read_scan_en_disable(enable=True)
        
        logger.flow(5, 'issue 40BF to check status == 1 and detected UECC WL')
        error_detected_WLs = self.check_read_scan_trigger(vb=vb, expected_WL=[phy_WL])

        logger.flow(6, 'set mConfig to disable read scan')
        self.read_scan_en_disable(enable=False)
        
        logger.flow(7, 'write data up to WL23')
        chunk_size = self.WL_block * self.mConfig.READ_SCAN_SAFE_AREA.value
        total_size = chunk_size
        api.sequential_write(lun=0, start_lba=lba, total_size=total_size, chunk_size=chunk_size, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        lba += total_size
        
        logger.flow(8, 'rand inject UECC on 8~15 WL')
        randWL = random.randint(self.mConfig.READ_SCAN_SAFE_AREA.value, self.mConfig.READ_SCAN_SAFE_AREA.value*2) // 3 * 3
        vb, pca = self.get_pca_and_check_not_remap(lun=0, lba=self.WL_block * randWL)
        inject_UECC(pca=pca)
        _, WL_type, phy_WL, SubBlock, FlushGroup, TwoWLGroup, RainGoup = get_physical_layout(pageline=pca.page.value, block_type="TLC")
        
        logger.flow(9, 'set mConfig to enable read scan and POR')
        self.read_scan_en_disable(enable=True)
        
        logger.flow(10, 'issue 40BF to check status == 1 and detected UECC WL')
        error_detected_WLs = self.check_read_scan_trigger(vb=vb, expected_WL=error_detected_WLs + [phy_WL])
        
        logger.flow(11, 'write data up to WL31')
        chunk_size = self.WL_block * self.mConfig.READ_SCAN_SAFE_AREA.value
        total_size = chunk_size
        api.sequential_write(lun=0, start_lba=lba, total_size=total_size, chunk_size=chunk_size, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        lba += total_size
        
        logger.flow(12, 'rand inject UECC on 16~23 WL')
        randWL = random.randint(self.mConfig.READ_SCAN_SAFE_AREA.value*2, self.mConfig.READ_SCAN_SAFE_AREA.value*3) // 3 * 3
        vb, pca = self.get_pca_and_check_not_remap(lun=0, lba=self.WL_block * randWL)
        inject_UECC(pca=pca)
        _, WL_type, phy_WL, SubBlock, FlushGroup, TwoWLGroup, RainGoup = get_physical_layout(pageline=pca.page.value, block_type="TLC")
        
        logger.flow(13, 'POR')
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
        
        logger.flow(14, 'issue 40BF to check status == 0')
        status = project_api.check_if_current_VB_scan_in_progress_completed(VB=vb)
        if status != 0:
            logger.error_lb(f'check status in vu 40BF')
            logger.error_fp(f'expect status equal to 0 after init completed but CompleteSlice = Slice, but current value = {status}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    

    def post_process(self) -> None:
        logger.info('Post process completed')
        pass
            
    def reconfig_lun(self) -> None:
        config_descs = api.get_config_descriptors(print=False)
        for index in range(4):
            config_descs[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
        for index in range(4):
            api.push_write_config(config_descs[index], index=index)
        ExecuteCMD.send()
        logger.info('LUN reconfiguration completed')
        return

run = Pattern().run

if __name__ == "__main__":
    run()