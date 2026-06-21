import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.wear_leveling.mutual_fun import *
from Script.project_api.functions import print_object_info_ai

class Trigger_Case(IntEnum):
    is_cold = 0
    is_prior_round = 1

class ConfigCase(IntEnum):
    EM1_larger_than_30 = 0
    EM1_less_than_30 = 1
class Refresh_pool(IntEnum):
    ICS = 0
    Static = 1
    Dynamic = 2

class ThresholdCase(IntEnum):
    TH1 = 0
    TH2 = 1

class Pattern(UFSTC):
    def pre_process(self) -> None:
        leave_inhibition_mode()
        self.fw_geometry = api.get_fw_geometry()
        self.write_record = api.get_empty_write_record()
        _, self.debug_info = api.get_debug_info()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        _, self.erase_cnt_buffer_backup = api.read_Xmemory(sram_address=self.debug_info.VB_list_cycle_address.value)
        pass
    
    def step1(self) -> None:        
        for refresh_case in [
            project_api.VBListNum.INDEX_BLK,
            project_api.VBListNum.TMP_CODE_BLK,
            project_api.VBListNum.CURRENT_L1,
            project_api.VBListNum.CURRENT_L2_EM1,
            project_api.VBListNum.CURRENT_L2_TLC,
            project_api.VBListNum.CURRENT_L2_TLC_WB,
        ]:
            for trigger_case in Trigger_Case:
                for threshold_case in ThresholdCase:
                    for config_case in ConfigCase:
                        logger.info(f'=========== Test Refresh {refresh_case.name}, config {config_case.name}, trigger_case {trigger_case.name}, threshold case {threshold_case.name} ===========')
                        logger.flow(1, f'Config lun')
                        if config_case == ConfigCase.EM1_larger_than_30:
                            self.slc_lun, self.tlc_lun = config_lun(SLC_Ratio=0.5)
                        else:
                            self.slc_lun, self.tlc_lun = config_lun(SLC_Ratio=0.25)
                        if refresh_case in [project_api.VBListNum.INDEX_BLK, project_api.VBListNum.TMP_CODE_BLK,]:
                            pool = Refresh_pool.ICS
                        elif refresh_case in [project_api.VBListNum.CURRENT_L2_EM1] or (refresh_case == project_api.VBListNum.CURRENT_L1 and config_case == ConfigCase.EM1_larger_than_30):
                            pool = Refresh_pool.Static
                        else:
                            pool = Refresh_pool.Dynamic
                        
                        logger.flow(2, f'write to create VB')
                        if refresh_case == project_api.VBListNum.CURRENT_L1:
                            api.sequential_write(lun=self.tlc_lun, start_lba=0, total_size=api.BLOCK4K_SIZE_16K_BYTE, chunk_size=api.BLOCK4K_SIZE_16K_BYTE, fua = 1,
                                need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                        elif refresh_case == project_api.VBListNum.CURRENT_L2_EM1:
                            api.sequential_write(lun=self.slc_lun, start_lba=0, total_size=api.BLOCK4K_SIZE_128M_BYTE, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                                need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                        elif refresh_case == project_api.VBListNum.CURRENT_L2_TLC:
                            api.sequential_write(lun=self.tlc_lun, start_lba=0, total_size=api.BLOCK4K_SIZE_128M_BYTE, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                                need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                        elif refresh_case == project_api.VBListNum.CURRENT_L2_TLC_WB:
                            api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                            api.sequential_write(lun=self.slc_lun, start_lba=0, total_size=api.BLOCK4K_SIZE_128M_BYTE, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                                need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                            api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                            
                        logger.flow(3, f'issue 4098 to get WL information')
                        self.VB_dict:Dict[project_api.VBListNum, List[int]] = {}
                        _, self.wear_leveling_A = project_api.issue_4098_to_get_wear_leveling_information()
                        for bq in range(self.fw_geometry.l52_total_vb_count):
                            VBList = self.wear_leveling_A.EC_data_of_VBs[bq].VBListNum.value
                            if VBList not in self.VB_dict:
                                self.VB_dict[project_api.VBListNum(VBList)] = []
                            self.VB_dict[project_api.VBListNum(VBList)].append(bq)
                            
                        logger.flow(4, f'issue C088 to StopRefreshRefreshCanStillBeEnqueue')
                        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
                        # gEC_for_Static_pool = self.wear_leveling_A.Global_Erase_Counter_of_static_pool.value
                        # gEC_for_dynamic_pool = self.wear_leveling_A.Global_Erase_Counter_of_dynamic_pool.value
                        # gEC_for_static_ICS_pool = self.wear_leveling_A.Global_Erase_Counter_of_ICS_pool.value
                        # gEC_of_Static_pool_for_open = self.wear_leveling_A.Global_Erase_Counter_of_static_pool_for_open_block.value
                        # gEC_of_dynamic_pool_for_open = self.wear_leveling_A.Global_Erase_Counter_of_dynamic_pool_for_open_block.value
                        gEC_for_Static_pool = 0
                        gEC_for_dynamic_pool = 0
                        gEC_for_static_ICS_pool = 0
                        gEC_of_Static_pool_for_open = 0
                        gEC_of_dynamic_pool_for_open = 0
                        gEC_gap_delta_TH1_static = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_static_pool.value
                        gEC_gap_delta_TH1_dynamic = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_dynamic_pool.value
                        gEC_gap_delta_TH1_ICS = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_ICS_pool.value
                        gEC_gap_delta_TH2_static = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_static_pool.value
                        gEC_gap_delta_TH2_dynamic = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_dynamic_pool.value
                        gEC_gap_delta_TH2_ICS = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_ICS_pool.value
                        set_erase_cnt_payload = bytearray(api.DATA_SIZE_4K_BYTE)
                        if pool == Refresh_pool.ICS:
                            gEC_for_static_ICS_pool = self.wear_leveling_A.EC_Threshold_of_ICS_pool.value + 1
                            if threshold_case == ThresholdCase.TH1:
                                set_ec = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_ICS_pool.value + 1  
                            else:
                                set_ec = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_ICS_pool.value + 1  
                        elif pool == Refresh_pool.Static:
                            gEC_of_Static_pool_for_open = self.wear_leveling_A.EC_Threshold_of_static_pool.value + 1
                            if threshold_case == ThresholdCase.TH1:
                                set_ec = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_static_pool.value + 1  
                            else:
                                set_ec = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_static_pool.value + 1  
                        else:
                            gEC_of_dynamic_pool_for_open = self.wear_leveling_A.EC_Threshold_of_dynamic_pool.value + 1
                            if threshold_case == ThresholdCase.TH1:
                                set_ec = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_dynamic_pool.value + 1  
                            else:
                                set_ec = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_dynamic_pool.value + 1  
                            
                        set_version_dict:Dict[int, int] = {}
                        for bq in range(self.fw_geometry.l52_total_vb_count):
                            set_erase_cnt_payload[bq * 4 : (bq+1)*4] = (set_ec).to_bytes(4, 'little')
                            set_version_dict[bq] = 0
                        for ListNum, vb_list in self.VB_dict.items():
                            if ListNum == refresh_case:
                                bq = vb_list[0]
                                set_erase_cnt_payload[bq * 4 : (bq+1)*4] = (0).to_bytes(4, 'little')
                                if pool == Refresh_pool.Static:
                                    set_version_dict[bq] = self.wear_leveling_A.globalVersion_of_static_pool.value+1
                                else:
                                    set_version_dict[bq] = self.wear_leveling_A.globalVersion_of_dynamic_pool.value+1
                                break
                        
                        logger.flow(5, f'issue C083 to set {refresh_case.name} EC = 0 and issue C072 to set static_wear_leveling global EC')
                        if pool != Refresh_pool.ICS:
                            if trigger_case == Trigger_Case.is_cold:
                                if pool == Refresh_pool.Static:
                                    slc_partition_current_vb_version = self.wear_leveling_A.globalVersion_of_static_pool.value + self.wear_leveling_A.Version_delta_Threshold_of_static_pool.value + 1
                                    api.set_ftl_version(slc_partition_current_vb_version = slc_partition_current_vb_version)
                                else:
                                    mlc_partition_current_vb_version = self.wear_leveling_A.globalVersion_of_dynamic_pool.value + self.wear_leveling_A.Version_delta_Threshold_of_dynamic_pool.value + 1
                                    api.set_ftl_version(mlc_partition_current_vb_version = mlc_partition_current_vb_version)
                            else:
                                api.set_ftl_version(set_VB_version=set_version_dict)
                        project_api.set_all_VB_erase_count(data_payload=set_erase_cnt_payload, set_in_ram=True)
                        project_api.issue_C072_to_set_static_wear_leveling_EC_gap_threshold(gEC_for_Static_pool, 
                                                                            gEC_for_dynamic_pool, 
                                                                            gEC_for_static_ICS_pool, 
                                                                            gEC_of_Static_pool_for_open, 
                                                                            gEC_of_dynamic_pool_for_open,
                                                                            gEC_gap_delta_TH1_static,
                                                                            gEC_gap_delta_TH1_dynamic,
                                                                            gEC_gap_delta_TH1_ICS,
                                                                            gEC_gap_delta_TH2_static,
                                                                            gEC_gap_delta_TH2_dynamic,
                                                                            gEC_gap_delta_TH2_ICS)
                        
                        logger.flow(6, f'issue 4098 to get WL information and check counter')
                        _, self.wear_leveling_B = project_api.issue_4098_to_get_wear_leveling_information()
                        for vb in range(self.fw_geometry.l52_total_vb_count):
                            EC_data = self.wear_leveling_B.EC_data_of_VBs[vb]
                            VER_data = self.wear_leveling_B.VER_data_of_VBs[vb]
                            logger.info(f'wear_leveling_B VB: {vb}, EC = {EC_data.EC.value} VBListNum = {EC_data.VBListNum.value} ({project_api.VBListNum(EC_data.VBListNum.value).name}), OpenType = {EC_data.OpenVBType.value} ({project_api.OpenVBType(EC_data.OpenVBType.value).name}), Version = {VER_data.version.value}, force_bit = {VER_data.force_bit.value}, IsDfgSrc = {EC_data.IsDfgSrc.value}')

                        print_object_info_ai(self.wear_leveling_B)
                        print_WL_different(self.wear_leveling_A, self.wear_leveling_B)
                        if pool == Refresh_pool.ICS:
                            check_WL_value_change(self.wear_leveling_A, self.wear_leveling_B, 'totalSWLJudgeCount_of_ICS_pool', 1)
                            check_WL_value_change(self.wear_leveling_A, self.wear_leveling_B, 'totalSWLJudgePassCount_of_ICS_pool', 1)
                            check_WL_value_change(self.wear_leveling_A, self.wear_leveling_B, 'totalSWLRefreshBookCount_of_ICS_pool', 1)
                        elif pool == Refresh_pool.Static:
                            check_WL_value_change(self.wear_leveling_A, self.wear_leveling_B, 'totalSWLJudgeCount_of_static_pool', 1)
                            check_WL_value_change(self.wear_leveling_A, self.wear_leveling_B, 'totalSWLJudgePassCount_of_static_pool', 1)
                            check_WL_value_change(self.wear_leveling_A, self.wear_leveling_B, 'totalSWLRefreshBookCount_of_static_pool', 1)
                        else:
                            check_WL_value_change(self.wear_leveling_A, self.wear_leveling_B, 'totalSWLJudgeCount_of_dynamic_pool', 1)
                            check_WL_value_change(self.wear_leveling_A, self.wear_leveling_B, 'totalSWLJudgePassCount_of_dynamic_pool', 1)
                            check_WL_value_change(self.wear_leveling_A, self.wear_leveling_B, 'totalSWLRefreshBookCount_of_dynamic_pool', 1)

                        logger.flow(7, f'issue 40C5 to check Booking Queue')
                        find = False
                        enqueue_VB = 0
                        if threshold_case == ThresholdCase.TH1:
                            Priority = project_api.BookingUser.BOOKING_IN_LP
                            BookingUser = project_api.BookingUser.SWL_REFRESH_LOW_GAP
                        else:
                            Priority = project_api.BookingUser.BOOKING_IN_MP
                            BookingUser = project_api.BookingUser.SWL_REFRESH_HIGH_GAP
                        _, self.booking_q_before = project_api.issue_40C5_to_get_booking_queue()
                        for idx, bq in enumerate(self.booking_q_before.BookingQueueVB):
                            VBList = self.wear_leveling_B.EC_data_of_VBs[bq.LogicalVBNumber.value].VBListNum.value
                            logger.info(f'BookingQ[{idx}]: VB {bq.LogicalVBNumber.value}, VBListNum = {VBList} ({project_api.VBListNum(VBList).name}), TheBookingUser: {project_api.BookingUser(bq.TheBookingUser.value & project_api.BookingUser.MAX_BOOKING_USER_COUNT-1).name} ({project_api.BookingUser(bq.TheBookingUser.value & 0x700).name})')
                            if VBList == refresh_case:
                                find = True
                                enqueue_VB = bq.LogicalVBNumber.value
                                if (bq.TheBookingUser.value & Priority != Priority) or \
                                    (bq.TheBookingUser.value & BookingUser != BookingUser):
                                    logger.error_lb(f'check BookingQueueVB after sWL refresh')
                                    logger.error_fp(f'expect BookingQueueVB[{idx}] is {Priority.name} and {BookingUser.name}, but current value = {bq.value}, result Fail!')
                                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        if not find:
                            logger.error_lb(f'check Booking Queue')
                            logger.error_fp(f'expect {project_api.VBListNum(VBList).name} should enqueue, result Fail!')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        
                        logger.flow(8, f'issue C088 to StartRefresh and polling BKOPS idle')
                        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
                        polling_bkops_idle()
                        
                        logger.flow(9, f'issue 4098 to get WL information and check counter')
                        _, self.wear_leveling_C = project_api.issue_4098_to_get_wear_leveling_information()
                        print_object_info_ai(self.wear_leveling_C)

                        print_WL_different(self.wear_leveling_B, self.wear_leveling_C)
                        if pool == Refresh_pool.ICS:
                            check_WL_value_change(self.wear_leveling_B, self.wear_leveling_C, 'totalSWLTriggerCount_of_ICS_pool', 1)
                            old_done = self.wear_leveling_B.totalSWLRefreshMissCount_of_ICS_pool.value + self.wear_leveling_B.totalSWLRefreshDoneCount_of_ICS_pool.value
                            new_done = self.wear_leveling_C.totalSWLRefreshMissCount_of_ICS_pool.value + self.wear_leveling_C.totalSWLRefreshDoneCount_of_ICS_pool.value
                            if old_done != new_done -1:
                                logger.error_lb(f'check Done/Miss Count after refresh')
                                logger.error_fp(f'expect totalSWLRefreshMissCount_of_ICS_pool + totalSWLRefreshDoneCount_of_ICS_pool increase, but current value = {new_done}, before value = {old_done}, result Fail!')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                            expect_VBListNum = project_api.VBListNum.FREE_BLK_QUEUE_TABLE
                        elif pool == Refresh_pool.Static:
                            check_WL_value_change(self.wear_leveling_B, self.wear_leveling_C, 'totalSWLTriggerCount_of_static_pool', 1)
                            old_done = self.wear_leveling_B.totalSWLRefreshMissCount_of_static_pool.value + self.wear_leveling_B.totalSWLRefreshDoneCount_of_static_pool.value
                            new_done = self.wear_leveling_C.totalSWLRefreshMissCount_of_static_pool.value + self.wear_leveling_C.totalSWLRefreshDoneCount_of_static_pool.value
                            if old_done != new_done -1:
                                logger.error_lb(f'check Done/Miss Count after refresh')
                                logger.error_fp(f'expect totalSWLRefreshMissCount_of_static_pool + totalSWLRefreshDoneCount_of_static_pool increase, but current value = {new_done}, before value = {old_done}, result Fail!')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                            expect_VBListNum = project_api.VBListNum.FREE_BLK_QUEUE_EM1
                        else:
                            check_WL_value_change(self.wear_leveling_B, self.wear_leveling_C, 'totalSWLTriggerCount_of_dynamic_pool', 1)
                            old_done = self.wear_leveling_B.totalSWLRefreshMissCount_of_dynamic_pool.value + self.wear_leveling_B.totalSWLRefreshDoneCount_of_dynamic_pool.value
                            new_done = self.wear_leveling_C.totalSWLRefreshMissCount_of_dynamic_pool.value + self.wear_leveling_C.totalSWLRefreshDoneCount_of_dynamic_pool.value
                            if old_done != new_done -1:
                                logger.error_lb(f'check Done/Miss Count after refresh')
                                logger.error_fp(f'expect totalSWLRefreshMissCount_of_dynamic_pool + totalSWLRefreshDoneCount_of_dynamic_pool increase, but current value = {new_done}, before value = {old_done}, result Fail!')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                            expect_VBListNum = project_api.VBListNum.FREE_BLK_QUEUE_TLC
                        
                        for bq in range(self.fw_geometry.l52_total_vb_count):
                            EC_data_before = self.wear_leveling_B.EC_data_of_VBs[bq]
                            EC_data_after = self.wear_leveling_C.EC_data_of_VBs[bq]
                            if EC_data_before.VBListNum.value != EC_data_after.VBListNum.value or \
                                EC_data_before.OpenVBType.value != EC_data_after.OpenVBType.value:
                                logger.info(f'Before: VB: {bq}, EC = {EC_data_before.EC.value} VBListNum = {EC_data_before.VBListNum.value} ({project_api.VBListNum(EC_data_before.VBListNum.value).name}), OpenType = {EC_data_before.OpenVBType.value} ({project_api.OpenVBType(EC_data_before.OpenVBType.value).name})')
                                logger.info(f'After:  VB: {bq}, EC = {EC_data_after.EC.value} VBListNum = {EC_data_after.VBListNum.value} ({project_api.VBListNum(EC_data_after.VBListNum.value).name}), OpenType = {EC_data_after.OpenVBType.value} ({project_api.OpenVBType(EC_data_after.OpenVBType.value).name})')
                                logger.info(f'==================================')
                            if EC_data_before.VBListNum.value == refresh_case:
                                if EC_data_after.VBListNum.value != expect_VBListNum:
                                    logger.error_lb(f'check VB {bq} group change after refresh')
                                    logger.error_fp(f'expect VB {bq} from {refresh_case.name} to {expect_VBListNum.name}, but current is {refresh_case.name} to {project_api.VBListNum(EC_data_after.VBListNum.value).name}, result Fail!')
                                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                            if EC_data_after.VBListNum.value == refresh_case:
                                if EC_data_before.VBListNum.value != expect_VBListNum:
                                    logger.error_lb(f'check VB {bq} group change after refresh')
                                    logger.error_fp(f'expect VB {bq} from {expect_VBListNum.name} to {refresh_case.name}, but current is {project_api.VBListNum(EC_data_before.VBListNum.value).name} to {refresh_case.name}, result Fail!')
                                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        if refresh_case != project_api.VBListNum.CURRENT_L1:
                            break
        pass
    
    def post_process(self) -> None:
        project_api.set_all_VB_erase_count(data_payload=self.erase_cnt_buffer_backup, set_in_ram=False)
        pass

run = Pattern().run
if __name__ == "__main__":
    run()