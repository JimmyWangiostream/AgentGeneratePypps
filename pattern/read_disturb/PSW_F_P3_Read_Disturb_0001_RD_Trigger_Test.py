import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.read_disturb.mutual_fun import *
from Script.project_api.functions import print_object_info_ai

MAX_VALUE = 0xFFFFFFFF
class BlockCase(IntEnum):
    TLC_Open = 0
    TLC_Closed = 1
    SLC_Open = 2
    SLC_Closed = 3
    
class ScanCase(IntEnum):
    selection1 = 0
    selection2 = 1
    
class UpdateCase(IntEnum):
    Nromal = 0
    Boundary = 1

class Pattern(UFSTC):
    def pre_process(self) -> None:
        leave_inhibition_mode()
        self.fw_geometry = api.get_fw_geometry()
        self.write_record = api.get_empty_write_record()
        _, self.debug_info = api.get_debug_info()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.TestWBLun = 2
        config_lun(normal_list=[self.TestNormalLun, self.TestWBLun], em1_list=[self.TestEM1Lun])
        self.TestCase: Dict[BlockCase, tuple[int, int, int]] = {}
        _, self.mConfig_in_vu = project_api.get_mConfig_data()
        pass
    
    def step1(self) -> None:
        logger.flow(1, f"write data to create TLC/SLC block")
        total_size = int(self.tlc_vb_size*1.5)
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        total_size = int(self.slc_vb_size*1.5)
        api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.TestCase[BlockCase.TLC_Open] = (self.TestNormalLun, self.tlc_vb_size, 0)
        self.TestCase[BlockCase.TLC_Closed] = (self.TestNormalLun, 0, 0)
        self.TestCase[BlockCase.SLC_Open] = (self.TestEM1Lun, self.slc_vb_size, 0)
        self.TestCase[BlockCase.SLC_Closed] = (self.TestEM1Lun, 0, 0)
        pass
    
    def step2(self) -> None:
        logger.flow(2, f"Read written data and get VB address")
        self.read_cnt_of_vb_before = project_api.get_all_VB_read_count()
        self.expect_rc = copy.deepcopy(self.read_cnt_of_vb_before)
        for case , (lun, lba, _) in self.TestCase.items():
            times = random.randint(10,100)
            pca = get_PCA_and_print(lun=lun, lba=lba)
            vb = pca.virtual_block_number.value
            logger.info(f"Case {case.name}: RC of VB{vb} = {self.read_cnt_of_vb_before[vb]}, read LUN = {lun}, LBA = {lba},  {times} times")
            read_LBA_repeatedly(lun=lun, lba = lba, read_times=times)
            self.TestCase[case] = (lun, lba, vb)
            self.expect_rc[vb] += times
        pass
    
    def step3(self) -> None:
        logger.flow(3, f"get RC and check RC increase")
        self.read_cnt_of_vb_after = project_api.get_all_VB_read_count()
        for case , (lun, lba, vb) in self.TestCase.items():
            if self.expect_rc[vb] != self.read_cnt_of_vb_after[vb]:
                times = self.expect_rc[vb] - self.read_cnt_of_vb_before[vb]
                logger.error_lb(f'check {case.name} VB {vb} after read {times} times')
                logger.error_fp(f'expect read_cnt_of_vb increase {times}, but before value = {self.read_cnt_of_vb_before[vb]}, current value = {self.read_cnt_of_vb_after[vb]}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    
    def step4(self) -> None:
        for update in UpdateCase:
            for blockcase in BlockCase:
                for scancase in ScanCase:
                    logger.info(f"=========== TestCase: BlockCase {blockcase.name}, ScanCase {scancase.name}, RC_TH UpdateCase {update.name} ===========")
                    (lun, lba, target_vb) = self.TestCase[blockcase]
                    pca = get_PCA_and_print(lun=lun, lba=lba)
                    target_vb = pca.virtual_block_number.value
                    
                    logger.flow(4, f"set RC to RC_ALL_WL_SCAN + 1 or 10")
                    read_cnt_of_vb_before = project_api.get_all_VB_read_count()
                    data_payload = bytearray(4096)
                    for vb in range(self.fw_geometry.l52_total_vb_count):
                        if vb == target_vb:
                            if scancase == ScanCase.selection2:
                                RC_ALL_WL_SCAN = self.mConfig_in_vu.RC_ALL_WL_SCAN.value * 1000000
                                set_value = RC_ALL_WL_SCAN + 1
                            else:
                                set_value = 10
                            logger.info(f"Set RC of VB{vb} = {set_value}")
                            data_payload[vb*4:(vb+1)*4] = (set_value).to_bytes(4, 'little')
                        else:
                            data_payload[vb*4:(vb+1)*4] = read_cnt_of_vb_before[vb].to_bytes(4, 'little')
                    project_api.set_all_VB_read_count(data_payload=data_payload)

                    logger.flow(5, f"issue D018 to disable Read Disturb")
                    project_api.issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(flag=1)
        
                    logger.flow(6, f"Reading data leads to RC > RC_TH")
                    vb = target_vb
                    self.smart_info_before = project_api.get_read_disturb_counter()
                    response, self.health_report_before = project_api.issue_40FE_to_read_enhanced_health_report()
                    self.read_cnt_of_vb_before = project_api.get_all_VB_read_count()
                    set_RC_TH_Value = self.read_cnt_of_vb_before[vb] + 1
                    project_api.set_specific_VB_read_count_threshold(VB_Num=vb, RC_TH_Value=set_RC_TH_Value)
                    _, self.RC_TH_list_before = project_api.issue_40CA_to_get_get_Read_Count_threshold_table()
                    self.erase_cnt_of_vb_before, erase_cnt_for_hidden_physical_block, _ = project_api.get_all_VB_erase_count()
                    times = random.randint(10,100)
                    _, RC_TH_list = project_api.issue_40CA_to_get_get_Read_Count_threshold_table()
                    logger.info(f"Case {blockcase.name}: EC[{vb}] = {self.erase_cnt_of_vb_before[vb]} RC[{vb}] = {self.read_cnt_of_vb_before[vb]}, set threshold = {set_RC_TH_Value}, read LUN = {lun}, LBA = {lba}, {times} times")
                    if RC_TH_list[vb] != set_RC_TH_Value:
                        logger.error_lb(f'check RC_TH of VB {vb} after set RC_TH')
                        logger.error_fp(f'expect RC_TH of VB {vb} = {set_RC_TH_Value}, but current value = {RC_TH_list[vb]}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    read_LBA_repeatedly(lun=lun, lba = lba, read_times=times)
                    self.read_cnt_of_vb_after = project_api.get_all_VB_read_count()
                    _, self.RC_TH_list_after = project_api.issue_40CA_to_get_get_Read_Count_threshold_table()
                    self.erase_cnt_of_vb_after, erase_cnt_for_hidden_physical_block, _ = project_api.get_all_VB_erase_count()
                    
                    logger.flow(7, f"check RD trigger cnt while disable RD")
                    self.check_read_disdurb_cnt_in_smart_info(before_smart=self.smart_info_before, before_health=self.health_report_before, blk_mode=blockcase, expect_selection1_inc=0, expect_selection2_inc=0)
                    
                    
                    logger.flow(8, f"set RC_TH to near the boundary if Boundary case")
                    if update == UpdateCase.Boundary:
                        set_RC_TH_Value = MAX_VALUE - 10
                        project_api.set_specific_VB_read_count_threshold(VB_Num=vb, RC_TH_Value=set_RC_TH_Value)
                        self.read_cnt_of_vb_boundary = project_api.get_all_VB_read_count()
                        _, self.RC_TH_list_boundary = project_api.issue_40CA_to_get_get_Read_Count_threshold_table()
                        self.erase_cnt_of_vb_boundary, erase_cnt_for_hidden_physical_block, _ = project_api.get_all_VB_erase_count()
                    
                    logger.flow(9, f"issue D018 to enable Read Disturb and scan idle")
                    project_api.issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(flag=0)
                    polling_Read_Disturb_idle(vb = vb)
                    
                    logger.flow(10, f"check RD trigger counter while RC > RC_TH")
                    expect_selection1_inc = 1 if scancase == ScanCase.selection1 else None
                    expect_selection2_inc = 1 if scancase == ScanCase.selection2 else None
                    self.check_read_disdurb_cnt_in_smart_info(before_smart=self.smart_info_before, before_health=self.health_report_before, blk_mode=blockcase, expect_selection1_inc=expect_selection1_inc, expect_selection2_inc=expect_selection2_inc)

                    logger.flow(12, f"Check RC_TH after RD")
                    self.read_cnt_of_vb_end = project_api.get_all_VB_read_count()
                    _, self.RC_TH_list_end = project_api.issue_40CA_to_get_get_Read_Count_threshold_table()
                    self.erase_cnt_of_vb_end, erase_cnt_for_hidden_physical_block, _ = project_api.get_all_VB_erase_count()
                    logger.info(f"==============================================================================")
                    EC_RC_TH_name, EC_RC_TH_value = get_EC_RC_TH(mConfig=self.mConfig_in_vu, EC=self.erase_cnt_of_vb_after[vb], is_SLC=("SLC" in blockcase.name), is_open=("Open" in blockcase.name), vb = vb)
                    logger.info(f"Case {blockcase.name} before read       : RC[{vb}] = {self.read_cnt_of_vb_before[vb]}, RC_TH[{vb}] = {self.RC_TH_list_before[vb]}, EC[{vb}] = {self.erase_cnt_of_vb_before[vb]}, read times = {times}")
                    logger.info(f"Case {blockcase.name} after read        : RC[{vb}] = {self.read_cnt_of_vb_after[vb]}, RC_TH[{vb}] = {self.RC_TH_list_after[vb]}, EC[{vb}] = {self.erase_cnt_of_vb_after[vb]}")
                    if update == UpdateCase.Boundary:
                        logger.info(f"Case {blockcase.name} set RC_TH boundary: RC[{vb}] = {self.read_cnt_of_vb_boundary[vb]}, RC_TH[{vb}] = {self.RC_TH_list_boundary[vb]}, EC[{vb}] = {self.erase_cnt_of_vb_boundary[vb]}")
                        self.read_cnt_of_vb_after = self.read_cnt_of_vb_boundary
                        self.RC_TH_list_after = self.RC_TH_list_boundary
                        self.erase_cnt_of_vb_after = self.erase_cnt_of_vb_boundary
                    logger.info(f"Case {blockcase.name} after read disturb: RC[{vb}] = {self.read_cnt_of_vb_end[vb]}, RC_TH[{vb}] = {self.RC_TH_list_end[vb]}, EC[{vb}] = {self.erase_cnt_of_vb_end[vb]}")
                    logger.info(f"==============================================================================")
                    if self.RC_TH_list_end[vb] <= self.RC_TH_list_after[vb] and update != UpdateCase.Boundary:
                        logger.error_lb(f'check RC_TH of VB {vb} update after Read Disturb')
                        logger.error_fp(f'expect new_RC_TH > old_RC_TH, but before value = {self.RC_TH_list_after[vb]}, current value = {self.RC_TH_list_end[vb]}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        
                    logger.flow(13, f"isuue VU 40CB to get total Read Count and Flush RC table threshold")
                    _, infofation = project_api.issue_40CB_to_get_total_Read_Count_and_Flush_RC_table_threshold(LogicalVB=vb)
                    print_object_info_ai(infofation)
                    if infofation.TotalReadCount_RC_VB.value != self.read_cnt_of_vb_end[vb] and update != UpdateCase.Boundary:
                        logger.error_lb(f'check TotalReadCount_RC_VB in VU 40CB of VB {vb} after Read Disturb')
                        logger.error_fp(f'expect TotalReadCount_RC_VB equal to {self.read_cnt_of_vb_end[vb]}, but current value = {infofation.TotalReadCount_RC_VB.value}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    if infofation.FlushRCTableThreshold_RC_TH_VB.value != self.RC_TH_list_end[vb]:
                        logger.error_lb(f'check FlushRCTableThreshold_RC_TH_VB in VU 40CB of VB {vb} after Read Disturb')
                        logger.error_fp(f'expect FlushRCTableThreshold_RC_TH_VB equal to {self.RC_TH_list_end[vb]}, but current value = {infofation.FlushRCTableThreshold_RC_TH_VB.value}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    RBER_XX_SF4 = get_mConfig_value(mConfig=self.mConfig_in_vu, field_name="RBER_FB_SF_4")
                    if infofation.CECCThreshold_ReadDisturbScan.value != RBER_XX_SF4:
                        logger.error_lb(f'check CECCThreshold_ReadDisturbScan in VU 40CB of VB {vb} after Read Disturb')
                        logger.error_fp(f'expect CECCThreshold_ReadDisturbScan equal to {RBER_XX_SF4}, but current value = {infofation.CECCThreshold_ReadDisturbScan.value}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    if infofation.IsScanTaskIdle.value != 1:
                        logger.error_lb(f'check IsScanTaskIdle in VU 40CB of VB {vb} after Read Disturb')
                        logger.error_fp(f'expect IsScanTaskIdle equal to {1}, but current value = {infofation.IsScanTaskIdle.value}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    
                    logger.flow(14, f"read compare all data expect pass")
                    api.read_compare(write_record = self.write_record)
                    
                    logger.flow(15, f"polling bkops idle")
                    polling_bkops_idle()
                    pass
                
                    
    
    def check_read_disdurb_cnt_in_smart_info(self, before_smart:project_api.ReadDisturbSmartInfo, before_health:project_api.ReadEnhanceHealthReport, blk_mode:BlockCase, expect_selection1_inc:Optional[int] = None, expect_selection2_inc:Optional[int] = None) -> None:
        smart_info = project_api.get_read_disturb_counter()
        print_object_info_ai(smart_info)
        response, health_report = project_api.issue_40FE_to_read_enhanced_health_report()
        print_object_info_ai(health_report)
        if expect_selection1_inc != None:
            if smart_info.prdh_rand_trig_cnt.value - before_smart.prdh_rand_trig_cnt.value != expect_selection1_inc:
                logger.error_lb(f'check page selection1(RC < RC_ALL_WL_SCAN) trigger cnt')
                logger.error_fp(f'expect prdh_rand_trig_cnt increase {expect_selection1_inc}, but before value = {before_smart.prdh_rand_trig_cnt.value}, current value = {smart_info.prdh_rand_trig_cnt.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        if expect_selection2_inc != None:
            if smart_info.prdh_seq_trig_cnt.value - before_smart.prdh_seq_trig_cnt.value != expect_selection2_inc:
                logger.error_lb(f'check page selection2(RC >= RC_ALL_WL_SCAN) trigger cnt')
                logger.error_fp(f'expect page prdh_seq_trig_cnt increase {expect_selection1_inc}, but before value = {before_smart.prdh_seq_trig_cnt.value}, current value = {smart_info.prdh_seq_trig_cnt.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        if smart_info.prdh_rand_trig_cnt.value + smart_info.prdh_seq_trig_cnt.value != smart_info.prdh_scan_pass_cnt.value + smart_info.prdh_scan_fail_cnt.value + smart_info.prdh_scan_entry_skip_cnt.value:
            logger.error_lb(f'check read_disdurb_cnt_in_smart_info')
            logger.error_fp(f'prdh_rand_trig_cnt({smart_info.prdh_rand_trig_cnt.value}) + prdh_seq_trig_cnt({smart_info.prdh_seq_trig_cnt.value}) != prdh_scan_pass_cnt({smart_info.prdh_scan_pass_cnt.value}) + prdh_scan_fail_cnt({smart_info.prdh_scan_fail_cnt.value}) + prdh_scan_entry_skip_cnt({smart_info.prdh_scan_entry_skip_cnt.value}), result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        expect_inc = (expect_selection1_inc if expect_selection1_inc else 0) + (expect_selection2_inc if expect_selection2_inc else 0)
        current = health_report.vbs_scanned_by_read_disturb_counter.value
        before = before_health.vbs_scanned_by_read_disturb_counter.value
        if current - before != expect_inc:
            logger.error_lb(f'check Read Disturb trigger cnt of {blk_mode.name}')
            logger.error_fp(f'expect vbs_scanned_by_read_disturb_counter increase {expect_inc}, but before value = {before}, current value = {current}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        current = health_report.read_disturb_in_background_counter.value
        before = before_health.read_disturb_in_background_counter.value
        if current <= before and expect_inc > 0:
            logger.error_lb(f'check Read Disturb trigger cnt of {blk_mode.name}')
            logger.error_fp(f'expect read_disturb_in_background_counter increase {expect_inc}, but before value = {before}, current value = {current}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        before_smart = smart_info
        before_health = health_report

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()