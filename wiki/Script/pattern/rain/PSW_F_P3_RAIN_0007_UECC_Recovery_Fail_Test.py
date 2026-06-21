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
        
        self.hw_setting = api.HwSetting.get_instance()
        self.hw_setting.update_from_device()
        self.fw_debug_mode_bkup = self.hw_setting.get_local_val(api.HwSettingField.FW_DEBUG_MODE)
        self.hw_setting.set_local_val(api.HwSettingField.FW_DEBUG_MODE, 0)
        self.hw_setting.set_to_device()
        pass

    def step1(self) -> None:
        for testMode in [TestMode.TEST_TLC, TestMode.TEST_SLC, TestMode.TEST_WB, TestMode.TEST_PTE]:
            for closed_vb in [False, True]:
                response, self.health_report_before = project_api.issue_40FE_to_read_enhanced_health_report()
                lun, mode_str = get_general_parameter(testMode)            
                rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode)
                logger.info(f'============ Test {mode_str} {"closed" if closed_vb else "open"} VB ============')
                logger.flow(1, f'Write until {mode_str} VB has enough data')
                if rain_user == project_api.RainUser.WB_RAIN:
                    api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                else:
                    api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                
                if closed_vb:
                    if testMode == TestMode.TEST_PTE:
                        continue
                    cursor = get_specific_open_vb_cursor(testMode)
                    last_lba, vb = create_closed_vb(testMode=testMode, lun=lun, write_record=self.write_record)
                else:
                    last_lba, cursor = write_data_more_than_N_pageline(pageline_cnt=3, lun=lun, testMode=testMode, write_record=self.write_record)
                
                logger.flow(2, f'inject 2 UECC in same rain group')
                if testMode == TestMode.TEST_PTE:
                    uecc_pca = self.inject_2_UECC_by_open_vb_info(cursor=cursor, testMode = testMode)
                else:
                    uecc_pca = self.inject_2_UECC_by_lun(lun=lun)

                logger.flow(3, f'issue C088 to stop refresh')
                project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
                
                logger.flow(4, f'direct read and check read status is UECC')
                for idx,(pca, SLC_en) in enumerate(uecc_pca):
                    dire_read_payload = direct_read_raw_data_and_check_status(pca=pca, SLC_enable=SLC_en, expect_status= project_api.ReadStatus.UECC, REH_Enable= testMode in [TestMode.TEST_PTE])
                    pass
                
                if testMode not in [TestMode.TEST_PTE]:
                    logger.flow(5, 'Host Read the injected error LBAs')
                    lba = 0
                    cmd_queue = []
                    while last_lba:
                        length = min(last_lba, api.READ_10_MAX_BLOCK_LEN)
                        read10 = ExecuteCMD.Read10()
                        read10.assign(lun=lun, lba=lba, length=length)
                        cmd = ExecuteCMD.enqueue(read10)
                        cmd_queue.append(cmd)
                        logger.info(f'push: read LUN{lun}, lba = {lba}, length = {length}')
                        last_lba -= length
                        lba += length
                    try:
                        ExecuteCMD.send(clear_on_success=False)
                        response = ExecuteCMD.read_response(cmd_queue[-1])
                    except DLL_RESPONSE_ERROR:
                        for cmd_index in cmd_queue:
                            response = ExecuteCMD.read_response(cmd_index)
                            logger.warning(f"lun = {response.upiu.b2_lun}, task_tag = {hex(response.upiu.b3_tasktag)},  response = {get_cmd_response_byte_str(response)}, status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}")
                            if response.upiu.b6_response != UPIUResponse.TARGET_SUCCESS:
                                break
                    ExecuteCMD.clear()
                    if response.upiu.b6_response != api.UPIUResponse.TARGET_FAILURE or response.upiu.b7_status != api.ScsiStatus.CHECK_CONDITION or response.b32_sense_data.b2_sense_key != api.SenseKey.MEDIUM_ERROR:
                        logger.error_lb(f'check read resp after read uecc area')
                        logger.error_fp(f'expect response fail, but status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}')
                        raise SIGHTING_RESPONSE_UNEXPECTED
                    
                    logger.flow(6, 'check refresh booking queue after UECC decode fail')
                    VB_list = [pca.virtual_block_number.value]
                    check_UECC_refresh_booking_Q(VB_list=VB_list)
                
                    logger.flow(8, f"check RAIN counter in health report")
                    d1_open_raind_recovery_fail_count = None
                    d3_open_raind_recovery_fail_count = None
                    d1_closed_raind_recovery_fail_count = None
                    d3_closed_raind_recovery_fail_count = None
                    if testMode== TestMode.TEST_TLC:
                        if closed_vb:
                            d3_closed_raind_recovery_fail_count = True
                        else:
                            d3_open_raind_recovery_fail_count = True
                    else:
                        if closed_vb:
                            d1_closed_raind_recovery_fail_count = True
                        else:
                            d1_open_raind_recovery_fail_count = True
                    check_RAIN_cnt_in_heatlth_report(self.health_report_before,
                                                        d1_closed_raind_recovery_fail_count = d1_closed_raind_recovery_fail_count,
                                                        d1_open_raind_recovery_fail_count = d1_open_raind_recovery_fail_count,
                                                        d3_closed_raind_recovery_fail_count=d3_closed_raind_recovery_fail_count,
                                                        d3_open_raind_recovery_fail_count=d3_open_raind_recovery_fail_count
                                                    )
                
                logger.flow(7, 'POR')
                api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
                
                if testMode not in [TestMode.TEST_PTE]:
                    logger.flow(8, f'reconfig to clear all data')
                    reconfig_to_erase_all_lun(write_record=self.write_record)
                pass

    def post_process(self) -> None:
        self.hw_setting.update_from_device()
        self.hw_setting.set_local_val(api.HwSettingField.FW_DEBUG_MODE, self.fw_debug_mode_bkup)
        self.hw_setting.set_to_device()
        pass

    def inject_2_UECC_by_lun(self, lun:int) -> List[tuple[project_api.physical_address_info, bool]]:
        SLC_en = lun != self.TestNormalLun
        uecc_pca:List[tuple[project_api.physical_address_info, bool]] = []
        invalid_plane_list = get_invalid_plane_list()
        pca = get_PCA_and_print(lun=lun, lba=0)
        uecc_pca.append((copy.deepcopy(pca), SLC_en))
        pca = get_PCA_and_print(lun=lun, lba=api.BLOCK4K_SIZE_16K_BYTE)
        uecc_pca.append((copy.deepcopy(pca), SLC_en))
        for pca, SLC_en  in uecc_pca:
            inject_UECC(pca=pca, SLC_enable=SLC_en)
        return uecc_pca
    
    def inject_2_UECC_by_open_vb_info(self, cursor:api.OpenVBInfoUnit, testMode:TestMode) -> List[tuple[project_api.physical_address_info, bool]]:
        SLC_en = testMode != TestMode.TEST_TLC
        uecc_pca:List[tuple[project_api.physical_address_info, bool]] = []
        invalid_plane_list = get_invalid_plane_list()
        block = cursor.logical_vb.value
        ce_plane = self.max_plane * cursor.first_empty_CE.value + cursor.first_empty_plane.value - 1
        pageline = cursor.first_empty_physical_page.value
        if invalid_plane_list[block] == ce_plane:
            ce_plane -= 1
        if ce_plane < 0:
            ce_plane += self.max_plane*self.max_ce
            pageline -= 1

        pca = project_api.physical_address_info()
        pca.die.value = ce_plane // self.max_plane
        pca.plane.value = ce_plane % self.max_plane
        pca.physical_block_number_w_BBT.value = block
        pca.page.value = pageline

        uecc_pca.append((copy.deepcopy(pca), SLC_en))
        
        ce_plane -= 1
        if invalid_plane_list[block] == ce_plane:
            ce_plane -= 1
        if ce_plane < 0:
            ce_plane += self.max_plane*self.max_ce
            pageline -= 1

        pca.die.value = ce_plane // self.max_plane
        pca.plane.value = ce_plane % self.max_plane
        uecc_pca.append((copy.deepcopy(pca), SLC_en))
        for pca, SLC_en  in uecc_pca:
            inject_UECC(pca=pca, SLC_enable=SLC_en)
        return uecc_pca


run = Pattern().run
if __name__ == "__main__":
    run()