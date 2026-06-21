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
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        pass

    def step1(self) -> None:
        logger.flow(1, 'Write TLC data up to 15 WL')
        self.lba = 0
        total_size = 15 * self.WL_block
        api.sequential_write(lun=0, start_lba=self.lba, total_size=total_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.lba += total_size
        _, self.open_vb_info = api.get_open_vb_info()        
        print_open_vb_info_cursor(self.open_vb_info.TLC_L2, "TLC_L2")
        self.VB, pca = get_PCA_VB_and_print(lun = 0, lba=0)
        pass
    
    def step2(self) -> None:
        logger.flow(2, 'read status in vu 40BF and check status = 0')
        status = project_api.check_if_current_VB_scan_in_progress_completed(VB=self.VB)
        if status != 0:
            logger.error_lb(f'check status in vu 40BF')
            logger.error_fp(f'expect status equal to 0 when LWWL = 14, but current value = {status}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
        
    def step3(self) -> None:
        logger.flow(3, 'inject UECC in WL0 and WL1 and WL3 and WL9')
        self.VB, pca = get_PCA_VB_and_print(lun=0, lba=0)
        inject_UECC(pca=pca)
        self.VB, pca = get_PCA_VB_and_print(lun=0, lba=self.WL_block+1 + api.BLOCK4K_SIZE_16K_BYTE)
        inject_UECC(pca=pca)
        self.VB, pca = get_PCA_VB_and_print(lun=0, lba=self.WL_block*3+1 + api.BLOCK4K_SIZE_16K_BYTE * 2)
        inject_UECC(pca=pca)
        self.VB, pca = get_PCA_VB_and_print(lun=0, lba=self.WL_block*9+1 + self.pageline_block*3 + + api.BLOCK4K_SIZE_16K_BYTE * 3)
        inject_UECC(pca=pca)
        pass
        
    def step4(self) -> None:
        logger.flow(4, 'Write TLC data up to 16 WL')
        total_size = 16 * self.WL_block - self.lba
        api.sequential_write(lun=0, start_lba=self.lba, total_size=total_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.lba += total_size
        _, self.open_vb_info = api.get_open_vb_info()        
        print_open_vb_info_cursor(self.open_vb_info.TLC_L2, "TLC_L2")
        pass
        
    def step5(self) -> None:
        logger.flow(5, 'SSU Sleep and Awake')
        ssu_sleep_and_active()
        logger.info('SSU Sleep and Awake completed')
        pass
        
    def step6(self) -> None:
        logger.flow(6, 'read status in vu 40BF and check status = 1 and check PageList only WL%3==0 been shown')
        status = project_api.check_if_current_VB_scan_in_progress_completed(VB=self.VB)
        if status != 1:
            logger.error_lb(f'check status in vu 40BF')
            logger.error_fp(f'expect status equal to 1 when LWWL = 15, but current value = {status}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
        PageList = project_api.get_Normal_VB_Scan_Pages(RSTriggerBy=project_api.RSTriggerBy.other)
        for page in range(3312):
            pageline, WL_type, phy_WL, SubBlock, FlushGroup, TwoWLGroup, RainGoup = get_physical_layout(pageline=page, block_type="TLC")
            if phy_WL % 3 ==0 and  page in PageList:
                PageList.remove(page)
        if PageList:
            logger.error_lb(f'check PageList in vu 40BF')
            logger.error_fp(f'expect page only scan WL%3==0, but current value = {PageList} not as expected, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
        
        self.old_error_detected_WLs = project_api.get_gc_read_scan_released_scan_pageline()
        if len(self.old_error_detected_WLs) != 2:
            logger.error_lb(f'check error_detected_WLs in vu 40BF')
            logger.error_fp(f'expect error_detected_WLs cnt equal to 2 when read scan occur, but current value = {len(self.old_error_detected_WLs)}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        if self.old_error_detected_WLs[0] != 0:
            logger.error_lb(f'check error_detected_WLs in vu 40BF')
            logger.error_fp(f'expect error_detected_WLs equal to 0 when read scan occur, but current value = {self.old_error_detected_WLs[0]}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        if self.old_error_detected_WLs[1] != 3:
            logger.error_lb(f'check error_detected_WLs in vu 40BF')
            logger.error_fp(f'expect error_detected_WLs equal to 3 when read scan occur, but current value = {self.old_error_detected_WLs[1]}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    
    def step7(self) -> None:
        logger.flow(7, 'inject UECC in WL6')
        self.VB, pca = get_PCA_VB_and_print(lun=0, lba=self.WL_block*6+1)
        inject_UECC(pca=pca)
        _, self.open_vb_info_new = api.get_open_vb_info()        
        print_open_vb_info_cursor(self.open_vb_info_new.TLC_L2, "TLC_L2")
        pass
    
    def step8(self) -> None:
        logger.flow(8, 'Write TLC data with SPOR')
        self.after_spor_lba, self.lba = self.write_data_with_SPOR(lun=0, startLBA=self.lba)
        _, self.open_vb_info_new = api.get_open_vb_info()        
        print_open_vb_info_cursor(self.open_vb_info_new.TLC_L2, "TLC_L2")
        pass
        
    def step9(self) -> None:
        self.VB, pca = get_PCA_VB_and_print(lun=0, lba=self.after_spor_lba)
        if pca.die.value == 0:
            pca.page.value -= 1
            pca.die.value = self.max_ce-1
            pca.plane.value = self.max_plane-1
        elif pca.plane.value == 0:
            pca.plane.value = self.max_plane-1
            pca.die.value -= 1
        else:
            pca.plane.value -= 1

        _, WL_type, self.SPOR_WL, SubBlock, FlushGroup, TwoWLGroup, RainGoup = get_physical_layout(pageline=pca.page.value, block_type="TLC")
        for p in range(pca.page.value - 1, -1, -1):
            _, _, self.SPOR_WL, temp_SB, _, _, _ = get_physical_layout(pageline=p, block_type="TLC")
            if p < 0 or temp_SB != SubBlock:
                break
            pca.page.value = p
        logger.flow(9, f'Inject UECC in SPOR page, WL = {self.SPOR_WL}')
        inject_UECC(pca=pca)
        _, self.open_vb_info_new = api.get_open_vb_info()        
        print_open_vb_info_cursor(self.open_vb_info_new.TLC_L2, "TLC_L2")
        pass
    
    def step10(self) -> None:
        logger.flow(10, 'Write TLC data to the last WL in VB')
        page = 3311 - self.open_vb_info_new.TLC_L2.first_empty_physical_page.value - 12
        total_size = (page * self.max_ce * self.max_plane  - 24 -2) *api.BLOCK4K_SIZE_16K_BYTE
        
        api.sequential_write(lun=0, start_lba=self.lba, total_size=total_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.lba += total_size
        _, self.open_vb_info_new = api.get_open_vb_info()        
        print_open_vb_info_cursor(self.open_vb_info_new.TLC_L2, "TLC_L2")
        pass
    
    def step11(self) -> None:
        logger.flow(11, 'read status in vu 40BF and check status = 0 and ERROR Detected pageline includes WL0, WL3, WL9')
        status = project_api.check_if_current_VB_scan_in_progress_completed(VB=self.VB)
        if status != 1:
            logger.error_lb(f'check status in vu 40BF')
            logger.error_fp(f'expect status equal to 1 after write, but current value = {status}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        new_error_detected_WLs = project_api.get_gc_read_scan_released_scan_pageline()
        if len(new_error_detected_WLs) != 3:
            logger.error_lb(f'check error_detected_WLs in vu 40BF')
            logger.error_fp(f'expect error_detected_WLs cnt equal to 3 when read scan occur, but current value = {len(new_error_detected_WLs)}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if new_error_detected_WLs[2] != 9:
            logger.error_lb(f'check error_detected_WLs in vu 40BF')
            logger.error_fp(f'expect error_detected_WLs equal to 9 when read scan occur, but current value = {new_error_detected_WLs[2]}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        APL_flag = project_api.get_APL_flag_of_VB(log_VB=self.VB)
        if APL_flag != 1:
            logger.error_lb(f'check APL_flag after SPOR occur')
            logger.error_fp(f'expect APL_flag of vb {self.VB} is 1, but current value = {APL_flag}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
            
        pass
    
    def step12(self) -> None:
        logger.flow(12, 'Write TLC data to close VB')
        total_size = self.tlc_vb_size - self.lba
        api.sequential_write(lun=0, start_lba=self.lba, total_size=total_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.lba += total_size
        _, self.open_vb_info = api.get_open_vb_info()        
        print_open_vb_info_cursor(self.open_vb_info.TLC_L2, "TLC_L2")
        pass
    
    def step14(self) -> None:
        logger.flow(13, 'read status in vu 40BF and check status = 0 and no ERROR Detected pageline')
        status = project_api.check_if_current_VB_scan_in_progress_completed(VB=self.VB)
        if status != 0:
            logger.error_lb(f'check status in vu 40BF')
            logger.error_fp(f'expect status equal to 0 when VB closed, but current value = {status}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        new_error_detected_WLs = project_api.get_gc_read_scan_released_scan_pageline()
        if len(new_error_detected_WLs) != 0:
            logger.error_lb(f'check error_detected_WLs in vu 40BF')
            logger.error_fp(f'expect error_detected_WLs cnt equal to 0 while VB is closed, but current value = {len(new_error_detected_WLs)}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def post_process(self) -> None:
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        polling_bkops_idle()
        logger.info('Post process completed')
        VB_list = [self.VB]
        check_BB_retirementafter_refresh(VB_list = VB_list, expect_reason=project_api.BBRetirementReaspnType.READBACK)
        pass
            
    def reconfig_lun(self) -> None:
        config_descs = api.get_config_descriptors(print=False)
        for index in range(4):
            config_descs[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
        for index in range(4):
            api.push_write_config(config_descs[index], index=index)
        ExecuteCMD.send()
        return
    
    def push_spor(self, delay:int) -> None:
        power_cycle = ExecuteCMD.CmdSeqPowerCycle()
        power_cycle.set_option(mode=api.PowerCycleMode.ALL_POWER_DOWN, wait_queue_empty=True, delay_time=delay)
        ExecuteCMD.enqueue(power_cycle)
        for channel in range(1,3 +1):
            power_ctrl = ExecuteCMD.CmdSeqPowerControl()
            power_ctrl.set_option(
                mode=1,
                channel=channel,
                spendtime=500,
                ramptime=100,
                wait_queue_empty=True,
                delay_time=100
            )
            ExecuteCMD.enqueue(power_ctrl)

        power_cycle = ExecuteCMD.CmdSeqPowerCycle()
        power_cycle.set_option(mode=api.PowerCycleMode.LINK_START_UP, wait_queue_empty=True, delay_time=delay)
        ExecuteCMD.enqueue(power_cycle)
        nop = ExecuteCMD.CmdSeqPushNopOutPollNopIn()
        nop.set_option(timeout=5000, wait_queue_empty=True, delay_time=100)
        ExecuteCMD.enqueue(nop)        

    
    def write_data_with_SPOR(self, lun:int, startLBA:int) -> tuple[int, int]:
        lba = startLBA
        apl_created = False
        delay = 100000
        logger.info("============= create APL ================")
        while not apl_created:
            temp_write_record = api.get_empty_write_record()
            write10 = ExecuteCMD.Write10()
            chunk_size = api.BLOCK4K_SIZE_64K_BYTE
            write10.assign(lun=lun, lba=lba, length=chunk_size, fua=0)
            write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX)
            ExecuteCMD.enqueue(write10)
            self.push_spor(delay=delay)
            ExecuteCMD.send(clear_on_success=False)
            for cmd in ExecuteCMD._cmd_list:
                api.save_write_info_by_cmd(cmd, temp_write_record)
            ExecuteCMD.clear()
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
            try:
                api.read_compare(temp_write_record, api.CompareMethod.SW_COMPARE)
                delay -= 50000
                if delay<0:
                    raise SIGHTING_RESPONSE_UNEXPECTED
            except DLL_CRC32_COMPARE_FAIL:
                ExecuteCMD.clear()
                apl_created = True
            lba+=chunk_size
            after_spor_lba = lba
        chunk_size = self.max_plane * api.BLOCK4K_SIZE_16K_BYTE * 3
        api.sequential_write(lun=lun, start_lba=lba, total_size=chunk_size, chunk_size=chunk_size, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        lba += chunk_size
        return after_spor_lba, lba

run = Pattern().run
if __name__ == "__main__":
    run()