import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.sgm.mutual_fun import *
from typing import Dict, List, Any
import copy
ENG2_WA = True
class TestCases(IntEnum):
    TLC_L2 = 0
    WB_L2 = 1
    SLC_L2 = 2
    ALLTYPE = 3
class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.hw_setting = api.HwSetting.get_instance()
        self.hw_setting.update_from_device()
        self._param = shared.param
        self.total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.fw_geometry = api.get_fw_geometry()
        self.TLC_VB_4K_SIZE = (self.fw_geometry.l88_vb_size_u1 * 512) // api.DATA_SIZE_4K_BYTE
        self.SLC_VB_4K_SIZE = (self.fw_geometry.l84_vb_size_u0 * 512) // api.DATA_SIZE_4K_BYTE
        flashsetting = api.get_flash_setting()
        self.write_record = api.get_empty_write_record()
        self.CE = flashsetting.FLH_Quantity * (BIT0 << flashsetting.Parallel)
        self.PLANE_PER_DIE = flashsetting.Plane_Per_Die
        self.wb_au = self._param.gGeometry.l79_write_booster_buffer_max_n_alloc_units
        self.wb_total_len = self.wb_au *  (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size) // DATA_SIZE_4K_BYTE
        pass
       
    def step1(self) -> None:

        for case in TestCases:  
            open_card()
            project_api.issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(0)
            logger.flow(13, f'Case = {case.name}')
            
            logger.flow(1, 'Config')
            if case == TestCases.TLC_L2:
                slc_lun, tlc_lun = config_lun(slc_au=0, tlc_au=self.total_au)
            elif case == TestCases.WB_L2:
                slc_lun, tlc_lun = config_lun(slc_au=0, tlc_au=self.total_au,wb_au=self.wb_au)
            elif case == TestCases.SLC_L2:
                slc_lun, tlc_lun = config_lun(slc_au=self.total_au, tlc_au=0)
            elif case == TestCases.ALLTYPE:
                slc_lun, tlc_lun = config_lun(slc_au=self.total_au//2, tlc_au=self.total_au//2, wb_au=self.wb_au)
            
            if case == TestCases.WB_L2 or case == TestCases.ALLTYPE:
                logger.flow(2, 'Enable writebooster')
                api.set_flag(api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(api.FlagIDN.WRITEBOOSTER_EN)

            logger.flow(3, 'Send VU 4071 to get SGS value')
            data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)

            logger.flow(4, 'Test trigger SGM in all RC level')
            first_time = True
            rc_level = 0
            last_event_cnt = 0
            flagged = True
            loop = 0
            total_len = 0
            last_event_tlc_cnt = 0
            last_event_slc_cnt = 0
            vb_num = 3
            stop_event_value = 0
            revoke_vb_list :List[int] = []
            
            if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                next_gen_threshold_cnt = next_trigger_rc = data_4071.sgs_read_count_threshold.value
            elif case == TestCases.SLC_L2:
                next_gen_threshold_cnt = next_trigger_rc = data_4071.sgs_read_count_threshold.value
            elif case == TestCases.ALLTYPE:
                next_gen_slc_threshold_cnt = next_trigger_slc_rc = data_4071.sgs_read_count_threshold.value 
                next_gen_tlc_threshold_cnt = next_trigger_tlc_rc = data_4071.sgs_read_count_threshold.value 
            
            while (stop_event_value < 1): 
                if rc_level == 0 and first_time:
                    logger.info(f'current rc range,  rc < RC_THRESHOLD')
                elif rc_level == 0:
                    logger.info(f'current rc range,  RC_THRESHOLD < rc < RC_THRESHOLD_{rc_level}')
                else:
                    logger.info(f'current rc range,  RC_THRESHOLD_{rc_level-1} < rc < RC_THRESHOLD_{rc_level}')
                
                if case == TestCases.TLC_L2:
                    #lun = tlc_lun
                    total_len = self.TLC_VB_4K_SIZE * vb_num
                elif case == TestCases.WB_L2 or case == TestCases.SLC_L2: 
                    #lun = tlc_lun
                    total_len = self.SLC_VB_4K_SIZE * vb_num
  
                logger.flow(5, f'Write {case.name} VB')
                write_list:list[Dict[str,Any]] = []
                write_list = self.write_vb_by_case(case, tlc_lun,slc_lun,vb_num, total_len)
                
                logger.flow(6, 'Send 4051_to_get_physical_address')
                vb_start_lbas = self.get_all_vb_list(write_list)

                logger.flow(7, 'Flag all vb')
                tlc_vb_list = []
                for vb_number, (lun, start_lba, vb_type) in vb_start_lbas.items():  #one vb read 1 time and set to next trigger gc
                    if vb_type == "TLC":
                        tlc_vb_list.append(vb_number)
                    param = project_api.C071_param()
                    if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                        logger.flow("7-1", f'Send VU C071 to adjust read count = next trigger rc - 1 = {next_trigger_rc-1}')
                        param.sgs_scan_dynamic_read_count.value = next_trigger_rc - 1
                        param.sgs_scan_static_read_count.value = data_4071.curr_read_count_SLC.value
                        param.sgs_scan_dynamic_event_cnt[rc_level+1].value = last_event_cnt
                    elif case == TestCases.SLC_L2:
                        logger.flow("7-1", f'Send VU C071 to adjust read count = next trigger rc - 1 = {next_trigger_rc-1}')
                        param.sgs_scan_dynamic_read_count.value = data_4071.curr_read_count_TLC.value
                        param.sgs_scan_static_read_count.value = next_trigger_rc - 1
                        param.sgs_scan_static_event_cnt[rc_level+1].value = last_event_cnt
                    elif case == TestCases.ALLTYPE:
                        logger.flow("7-1", f'Send VU C071 to adjust read count = next trigger tlc rc - 1 = {next_trigger_tlc_rc - 1}, next trigger slc rc - 1 = {next_trigger_slc_rc - 1}')
                        if vb_type == "TLC":
                            param.sgs_scan_dynamic_read_count.value = next_trigger_tlc_rc - 1
                            param.sgs_scan_static_read_count.value = data_4071.curr_read_count_SLC.value
                        else:
                            param.sgs_scan_dynamic_read_count.value = data_4071.curr_read_count_TLC.value
                            param.sgs_scan_static_read_count.value = next_trigger_slc_rc - 1
                        param.sgs_scan_dynamic_event_cnt[rc_level+1].value = last_event_tlc_cnt
                        param.sgs_scan_static_event_cnt[rc_level+1].value = last_event_slc_cnt
                     
                    project_api.issue_C071_to_set_SGD_scan_parameters(param)

                    logger.flow("7-2", 'read len = 1 to flag vb')
                    read_data(lun=lun,start_lba=start_lba,len=1,total_len=1)

                    logger.flow("7-3", 'Send 4071 to check sgs value')
                    data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
                    
                    if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                        current_read_count = data_4071.curr_read_count_TLC.value
                        remain = data_4071.remain_read_count_trigger_sgs_TLC.value
                    elif case == TestCases.SLC_L2:
                        current_read_count = data_4071.curr_read_count_SLC.value
                        remain = data_4071.remain_read_count_trigger_sgs_SLC.value
                    else:
                        current_tlc_read_count = data_4071.curr_read_count_TLC.value
                        current_slc_read_count = data_4071.curr_read_count_SLC.value
                        remain_tlc = data_4071.remain_read_count_trigger_sgs_TLC.value
                        remain_slc = data_4071.remain_read_count_trigger_sgs_SLC.value
                    logger.info(f'current read cnt TLC ={data_4071.curr_read_count_TLC.value}, current read cnt SLC = {data_4071.curr_read_count_SLC.value}')


                    if case == TestCases.TLC_L2 or case == TestCases.WB_L2 or case == TestCases.SLC_L2:
                        next_gen_threshold_cnt = current_read_count + data_4071.sgs_scan_window_list[rc_level].value
                        next_trigger_rc = remain
                        logger.info(f'current rc({current_read_count}), gen new remain value = {remain}')

                    else:
                        if vb_type == "TLC":
                            next_gen_tlc_threshold_cnt = current_tlc_read_count + data_4071.sgs_scan_window_list[rc_level].value
                            next_trigger_tlc_rc = remain_tlc
                        else:
                            next_gen_slc_threshold_cnt = current_slc_read_count + data_4071.sgs_scan_window_list[rc_level].value
                            next_trigger_slc_rc = remain_slc
                        logger.info(f'current tlc rc({current_tlc_read_count}) , gen new remain tlc value = {remain_tlc}')
                        logger.info(f'current slc rc({current_slc_read_count}) , gen new remain slc value = {remain_slc}')
                    
                    param = project_api.C071_param()
                    if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                        logger.flow("7-4", f'Send VU C071 to adjust read count = next trigger rc - 1 = {next_trigger_rc-1}')
                        param.sgs_scan_dynamic_read_count.value = next_trigger_rc - 1
                        param.sgs_scan_static_read_count.value = data_4071.curr_read_count_SLC.value
                        param.sgs_scan_dynamic_event_cnt[rc_level+1].value = last_event_cnt
                    elif case == TestCases.SLC_L2:
                        logger.flow("7-4", f'Send VU C071 to adjust read count = next trigger rc - 1 = {next_trigger_rc-1}')
                        param.sgs_scan_dynamic_read_count.value = data_4071.curr_read_count_TLC.value
                        param.sgs_scan_static_read_count.value = next_trigger_rc - 1
                        param.sgs_scan_static_event_cnt[rc_level+1].value = last_event_cnt
                    else:
                        if vb_type == "TLC":
                            logger.flow("7-4", f'Send VU C071 to adjust read count = next trigger rc - 1 = {next_trigger_tlc_rc-1}')
                            param.sgs_scan_dynamic_read_count.value = next_trigger_tlc_rc - 1
                            param.sgs_scan_static_read_count.value = data_4071.curr_read_count_SLC.value
                        else:
                            logger.flow("7-4", f'Send VU C071 to adjust read count = next trigger rc - 1 = {next_trigger_slc_rc-1}')
                            param.sgs_scan_dynamic_read_count.value = data_4071.curr_read_count_TLC.value
                            param.sgs_scan_static_read_count.value = next_trigger_slc_rc - 1
                        param.sgs_scan_dynamic_event_cnt[rc_level+1].value = last_event_tlc_cnt
                        param.sgs_scan_static_event_cnt[rc_level+1].value = last_event_slc_cnt
                    project_api.issue_C071_to_set_SGD_scan_parameters(param)

                    logger.flow("7-5", 'read len = 1 to flag vb')
                    read_data(lun=lun,start_lba=start_lba,len=1,total_len=1)

                    logger.flow("7-6", 'Send 4071 to check sgs value')
                    data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
                    if case == TestCases.TLC_L2 or case == TestCases.WB_L2 or case == TestCases.SLC_L2:
                        next_trigger_rc = next_gen_threshold_cnt
                    else:
                        if vb_type == "TLC":
                            next_trigger_tlc_rc = next_gen_tlc_threshold_cnt
                        else:
                            next_trigger_slc_rc = next_gen_slc_threshold_cnt

                logger.flow(8, 'Send 4071 to check sgs value')
                total_vb_cnt = len(vb_start_lbas)
                if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                    compare_value(data_4071.sgs_scan_flagged_physical_vb_cnt.value, total_vb_cnt + len(revoke_vb_list),desc="sgs_scan_flagged_physical_vb_cnt")
                    for i in range(len(data_4071.sgs_scan_flagged_physical_vbNumb)):
                        if data_4071.sgs_scan_flagged_physical_vbNumb[i].value != 0:
                            logger.info(f'vbNum = {i} be flagged')
                    for vb_number, _ in vb_start_lbas.items():
                        compare_value(data_4071.sgs_scan_flagged_physical_vbNumb[vb_number].value, 1, desc=f"sgs_scan_flagged_physical_vbNumb[{vb_number}]")
                
                elif case == TestCases.SLC_L2:
                    logger.info(f'scan_flagged_physical_vb_cnt = {data_4071.sgs_scan_flagged_physical_vb_cnt.value}')
                    if data_4071.sgs_scan_flagged_physical_vb_cnt.value < 1:
                        logger.error('When the RC threshold is reached, at least one VB must be flagged')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL  
                    for i in range(len(data_4071.sgs_scan_flagged_physical_vbNumb)):
                        if data_4071.sgs_scan_flagged_physical_vbNumb[i].value != 0:
                            logger.info(f'vbNum = {i} be flagged')
                            if not check_vb_in(i, VBPolicy.LOG_PTE_SLC_RVK):
                                logger.error(f'When read count not reach threshold, flagged VB must belong to the LOG_TAB_BLK, CURRENT_PTE, PTE_POOL, or USED_BLK_POOL_SLC group')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                elif case == TestCases.ALLTYPE:
                    logger.info(f'scan_flagged_physical_vb_cnt = {data_4071.sgs_scan_flagged_physical_vb_cnt.value}')
                    if data_4071.sgs_scan_flagged_physical_vb_cnt.value < (7 - len(revoke_vb_list)): #6 tlc + at least 1 slc
                        logger.error('When the RC threshold is reached, at least 6(TLC) + 1(SLC) VB must be flagged')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        
                    for i in range(len(data_4071.sgs_scan_flagged_physical_vbNumb)):
                        if i in tlc_vb_list:
                            compare_value(data_4071.sgs_scan_flagged_physical_vbNumb[i].value, 1, desc=f"sgs_scan_flagged_physical_vbNumb[{i}]")
                        else:
                            if data_4071.sgs_scan_flagged_physical_vbNumb[i].value != 0:
                                logger.info(f'vbNum = {i} be flagged')
                                if not check_vb_in(i, VBPolicy.LOG_PTE_SLC_RVK):
                                    logger.error(f'When read count not reach threshold, flagged VB must belong to the LOG_TAB_BLK, CURRENT_PTE, PTE_POOL, or USED_BLK_POOL_SLC group')
                                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                physical_cnt_before_erase = data_4071.sgs_scan_flagged_physical_vb_cnt.value
                vb_flagged = []
                vb_flagged = data_4071.sgs_scan_flagged_physical_vbNumb   #test not use deepcopy will work or not

                logger.flow(9, 'Send VU D017 to create fail')
                param_list = []
                is_bad_blk_before_list = []
                fail_idx = 6 if case == TestCases.ALLTYPE else 0
                for idx,(vb_number, (lun, start_lba, vb_type)) in enumerate(vb_start_lbas.items()):
                    if idx == fail_idx:
                        case_d017 = random.randint(0,10)
                        D017_param = choose_D017_param(vb_number, case_d017, self.CE, self.PLANE_PER_DIE)
                        project_api.issue_D017_to_create_SGM_fail(D017_param)
                    else:
                        case_d017 = random.randint(11,12)
                        D017_param = choose_D017_param(vb_number, case_d017, self.CE, self.PLANE_PER_DIE)
                        
                    is_bad_blk_before_list.append(check_vb_in_BBT(vb_number))    
                    param_list.append(copy.deepcopy(D017_param))

                
                logger.flow(10, 'Erase to trigger SGM')
                if case == TestCases.TLC_L2: 
                    total_len = self.TLC_VB_4K_SIZE
                    for vb, (lun,lba, vb_type) in vb_start_lbas.items():
                        unmap_data(lun=lun,start_lba=lba,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len,write_record=self.write_record)  
                elif case == TestCases.WB_L2 or case == TestCases.SLC_L2:
                    total_len = self.SLC_VB_4K_SIZE
                    for vb, (lun,lba, vb_type) in vb_start_lbas.items():
                        unmap_data(lun=lun,start_lba=lba,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len, write_record=self.write_record)
                else:
                    for vb, (lun,lba, vb_type) in vb_start_lbas.items():
                        total_len = self.SLC_VB_4K_SIZE if vb_type == "SLC" else self.TLC_VB_4K_SIZE
                        unmap_data(lun=lun,start_lba=lba,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len, write_record=self.write_record)
                purge_operation()


                current_revoke_vb_list :List[int] = []
                logger.flow(11, 'Send 4071 to check event cnt increase')
                data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)

                
                if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                    event_cnt = data_4071.sgs_scan_event_cnt_TLC[rc_level+1].value
                    for vb_number, (lun, start_lba, vb_type) in vb_start_lbas.items():
                        vb_group = check_vb_in_which_group(vb_number)
                        if vb_group == "REVOKE_BLK":
                            current_revoke_vb_list.append(vb_number)
                    revoke_vb_list += current_revoke_vb_list
                    compare_value(event_cnt, last_event_cnt + total_vb_cnt - len(current_revoke_vb_list),desc=f"sgs_scan_event_cnt_{rc_level+1}_TLC")
                    #compare_value(event_cnt, last_event_cnt + total_vb_cnt, desc=f"sgs_scan_event_cnt_{rc_level+1}_TLC")
                    
                    last_event_cnt = event_cnt
                        
                elif case == TestCases.SLC_L2:
                    physical_cnt_after_erase = data_4071.sgs_scan_flagged_physical_vb_cnt.value
                    diff = physical_cnt_before_erase - physical_cnt_after_erase 
                    event_cnt = data_4071.sgs_scan_event_cnt_SLC[rc_level+1].value
                    if(event_cnt - last_event_cnt) != diff:
                        logger.info(f'event cnt before erase = {last_event_cnt}, event cnt after erase = {event_cnt}')
                        logger.info(f'scan_flagged_physical_vb_cnt before erase = {physical_cnt_before_erase}, scan_flagged_physical_vb_cnt after erase = {physical_cnt_after_erase }')
                        logger.error(f'After VB erase, scan_flagged_physical_vb_cnt must equal the delta of the event count') 
                        logger.error(f'event cnt - last event cnt = {event_cnt - last_event_cnt}, scan_flagged_physical_vb_cnt - last scan_flagged_physical_vb_cnt = {diff}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    last_event_cnt = event_cnt
                else:
                    event_cnt = data_4071.sgs_scan_event_cnt_TLC[rc_level+1].value
                    for vb_number, (lun, start_lba, vb_type) in vb_start_lbas.items():
                        vb_group = check_vb_in_which_group(vb_number)
                        if vb_group == "REVOKE_BLK":
                            current_revoke_vb_list.append(vb_number)
                    revoke_vb_list += current_revoke_vb_list
                    compare_value(event_cnt, last_event_tlc_cnt + vb_num * 2 - len(current_revoke_vb_list), desc=f"sgs_scan_event_cnt_{rc_level+1}_TLC")
                    last_event_tlc_cnt = event_cnt
                    for i in range(len(data_4071.sgs_scan_flagged_physical_vbNumb)):
                        if data_4071.sgs_scan_flagged_physical_vbNumb[i].value != 0:
                            logger.info(f'vbNum = {i} be flagged')
                    physical_cnt_after_erase = data_4071.sgs_scan_flagged_physical_vb_cnt.value
                    diff = physical_cnt_before_erase - physical_cnt_after_erase - 6 + len(revoke_vb_list)
                    event_cnt = data_4071.sgs_scan_event_cnt_SLC[rc_level+1].value
                    if(event_cnt - last_event_slc_cnt) != diff:
                        logger.info(f'event cnt before erase = {last_event_slc_cnt}, event cnt after erase = {event_cnt}')
                        logger.info(f'scan_flagged_physical_vb_cnt before erase = {physical_cnt_before_erase}, scan_flagged_physical_vb_cnt after erase = {physical_cnt_after_erase }')
                        logger.error(f'After VB erase, scan_flagged_physical_vb_cnt must equal the delta of the event count') 
                        logger.error(f'event cnt - last event cnt = {event_cnt - last_event_slc_cnt}, scan_flagged_physical_vb_cnt - last scan_flagged_physical_vb_cnt - 6 (TLC) = {diff}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    last_event_slc_cnt = event_cnt
                logger.info(f'scan_flagged_physical_vb_cnt = {data_4071.sgs_scan_flagged_physical_vb_cnt.value}')
                logger.info(f'sgs_scan_event_cnt_{rc_level+1}_SLC = {data_4071.sgs_scan_event_cnt_SLC[rc_level+1].value}')
                
                
                logger.flow(2, 'Send 4071 to check flagged physical vb cnt / flagged physical vbNumb = 0 after trigger SGM')
                if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                    compare_value(data_4071.sgs_scan_flagged_physical_vb_cnt.value, len(revoke_vb_list),desc="sgs_scan_flagged_physical_vb_cnt")
                    for vb_number, (lun,lba,vb_type) in vb_start_lbas.items():
                        if vb_number in current_revoke_vb_list:
                            compare_value(data_4071.sgs_scan_flagged_physical_vbNumb[vb_number].value, 1, desc=f"sgs_scan_flagged_physical_vbNumb[{vb_number}]")
                        else:
                            compare_value(data_4071.sgs_scan_flagged_physical_vbNumb[vb_number].value, 0, desc=f"sgs_scan_flagged_physical_vbNumb[{vb_number}]")
                elif case == TestCases.SLC_L2:
                    for i in range(len(data_4071.sgs_scan_flagged_physical_vbNumb)):
                        if data_4071.sgs_scan_flagged_physical_vbNumb[i].value != 0:
                            logger.info(f'vbNum = {i} be flagged')
                            if not check_vb_in(i, VBPolicy.LOG_PTE_RVK):
                                logger.error(f'When read count not reach threshold, flagged VB must belong to the LOG_TAB_BLK, CURRENT_PTE, PTE_POOL group')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    for i in range(len(data_4071.sgs_scan_flagged_physical_vbNumb)):
                        if i in tlc_vb_list:
                            if vb_number in current_revoke_vb_list:
                                compare_value(data_4071.sgs_scan_flagged_physical_vbNumb[i].value, 1, desc=f"sgs_scan_flagged_physical_vbNumb[{i}]")
                            else:
                                compare_value(data_4071.sgs_scan_flagged_physical_vbNumb[i].value, 0, desc=f"sgs_scan_flagged_physical_vbNumb[{i}]")
                        else:
                            if data_4071.sgs_scan_flagged_physical_vbNumb[i].value != 0:
                                logger.info(f'vbNum = {i} be flagged')
                                if not check_vb_in(i, VBPolicy.LOG_PTE_RVK):
                                    logger.error(f'When read count not reach threshold, flagged VB must belong to the LOG_TAB_BLK, CURRENT_PTE, PTE_POOL group')
                                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL


                logger.flow(2, f'Send VUC = 0x405E check vb in retirement bitmap or not')
                for idx,(vb_number, (lun, start_lba, vb_type)) in enumerate(vb_start_lbas.items()):
                    is_retirement_case = check_is_retirement_case(param_list[idx])
                    logger.info(f'is retirement case = {is_retirement_case}')
                    is_bad_blk = check_vb_in_BBT(vb_number, param_list[idx])
                    if vb_flagged[vb_number].value == 1:
                        if is_retirement_case == True:
                                logger.flow(2, f'Send VUC = 0x405E check vb={vb_number} is in retirement bitmap')
                                if is_bad_blk == False:
                                    logger.error(f'Expect vb={vb_number} be retired, but not')
                                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                                else:
                                    logger.info(f'vb={vb_number} in retirement bitmap')
                        else:
                            if is_bad_blk == True and is_bad_blk_before_list[idx] == False:
                                logger.error(f'Expect vb={vb_number} not be retired, but not')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                            else:
                                logger.info(f'vb={vb_number} not in retirement bitmap')
                        
                if event_cnt >= 1 and rc_level < 4:
                    logger.info(f'next trigger rc = {data_4071.sgs_read_count_threshold_list[rc_level].value}')
                    next_trigger_rc = data_4071.sgs_read_count_threshold_list[rc_level].value
                    next_trigger_tlc_rc = data_4071.sgs_read_count_threshold_list[rc_level].value
                    next_trigger_slc_rc = data_4071.sgs_read_count_threshold_list[rc_level].value
                    rc_level += 1

                    last_event_cnt = 0

                if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                    stop_event_value = data_4071.sgs_scan_event_cnt_TLC[5].value
                else:
                    stop_event_value = data_4071.sgs_scan_event_cnt_SLC[5].value

                first_time = False
                if flagged == True:
                    loop += 1
            pass
    def write_vb_by_case(self, case:TestCases, tlc_lun:int, slc_lun:int, vb_num:int, total_len:int=0) -> list[Dict[str,Any]]:
        write_list :list[Dict[str,Any]] = []
        if case == TestCases.TLC_L2:
            write_data(lun=tlc_lun,start_lba=0,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len, write_record=self.write_record)
            write_list.append({'lun':tlc_lun,'start_lba':0, 'vb_size':self.TLC_VB_4K_SIZE, 'total_len':total_len, 'vb_type':"TLC"})
        elif case == TestCases.WB_L2:
            write_data(lun=tlc_lun,start_lba=0,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len, write_record=self.write_record)
            write_list.append({'lun':tlc_lun,'start_lba':0, 'vb_size':self.SLC_VB_4K_SIZE, 'total_len':total_len, 'vb_type':"TLC"})
        elif case == case == TestCases.SLC_L2:
            write_data(lun=slc_lun,start_lba=0,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len, write_record=self.write_record)
            write_list.append({'lun':slc_lun,'start_lba':0, 'vb_size':self.SLC_VB_4K_SIZE, 'total_len':total_len, 'vb_type':"SLC"})
        elif case == TestCases.ALLTYPE:
            logger.flow(2, 'Enable writebooster')
            api.clear_flag(api.FlagIDN.WRITEBOOSTER_EN)
            start_lba = 0
            total_len = self.TLC_VB_4K_SIZE * vb_num
            write_data(lun=tlc_lun,start_lba=0,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len, write_record=self.write_record)  #TLC_L2
            write_list.append({'lun':tlc_lun,'start_lba':start_lba, 'vb_size':self.TLC_VB_4K_SIZE, 'total_len':total_len, 'vb_type':"TLC"})
            api.set_flag(api.FlagIDN.WRITEBOOSTER_EN)
            start_lba = total_len
            total_len = self.SLC_VB_4K_SIZE * vb_num
            write_data(lun=tlc_lun,start_lba=start_lba,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len, write_record=self.write_record)  #WB_L2
            write_list.append({'lun':tlc_lun,'start_lba':start_lba, 'vb_size':self.SLC_VB_4K_SIZE, 'total_len':total_len, 'vb_type':"TLC"})
            total_len = self.SLC_VB_4K_SIZE * vb_num
            write_data(lun=slc_lun,start_lba=0,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len, write_record=self.write_record)#SLC_L2
            write_list.append({'lun':slc_lun,'start_lba':0, 'vb_size':self.SLC_VB_4K_SIZE, 'total_len':total_len, 'vb_type':"SLC"})
        return write_list
    
    def get_all_vb_list(self, write_list:list[Dict[str,Any]]) -> Dict[int,tuple[int,int,str]]:
        vb_start_lba_list:Dict[int,tuple[int,int,str]] = {}
        for d in write_list:
            for lba in range(d['start_lba'], d['start_lba']+d['total_len'], d['vb_size']):
                _, pca = project_api.issue_4051_to_get_physical_address(luID=d['lun'], lba=lba)
                vb_number = pca.virtual_block_number.value
                vb_start_lba_list[vb_number] = (d['lun'],lba, d['vb_type'])
            
        return vb_start_lba_list
    def post_process(self) -> None:
        open_card()
        pass
run = Pattern().run 

if __name__ == "__main__":
    run()