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

from typing import TypeAlias, cast

class TestCases(IntEnum):
    TLC_L2 = 0
    WB_L2 = 1
    SLC_L2 = 2

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = shared.param
        self.total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.fw_geometry = api.get_fw_geometry()
        self.TLC_VB_4K_SIZE = (self.fw_geometry.l88_vb_size_u1 * 512) // api.DATA_SIZE_4K_BYTE
        self.SLC_VB_4K_SIZE = (self.fw_geometry.l84_vb_size_u0 * 512) // api.DATA_SIZE_4K_BYTE
        self.write_record = api.get_empty_write_record()
        
        flashsetting = api.get_flash_setting()
        self.CE = flashsetting.FLH_Quantity * (BIT0 << flashsetting.Parallel)
        self.PLANE_PER_DIE = flashsetting.Plane_Per_Die
        
        pass
    def step1(self) -> None:
    
        logger.flow(1, 'Issue 4056 get mConfig data')
        mConfig_size = 437
        _,  payload= project_api.issue_4056_to_get_mConfig_data(get_option=0, keep_error=False)
        self.mconfig_data = mConfig(payload, 4, 4+mConfig_size-1)
        
        logger.info(f'mconfig.SGS_TOUCHUP_ERASE_SWITCH = {self.mconfig_data.SGS_TOUCHUP_ERASE_SWITCH.value}')
        logger.info(f'mconfig.SGSSCAN_RC_TH = {self.mconfig_data.SGSSCAN_RC_TH.value}')
        logger.info(f'mconfig.SGSSCAN_RC_0 = {self.mconfig_data.SGSSCAN_RC_0.value}')
        logger.info(f'mconfig.SGSSCAN_RC_1 = {self.mconfig_data.SGSSCAN_RC_1.value}')
        logger.info(f'mconfig.SGSSCAN_RC_2 = {self.mconfig_data.SGSSCAN_RC_2.value}')
        logger.info(f'mconfig.SGSSCAN_RC_3 = {self.mconfig_data.SGSSCAN_RC_3.value}')

        logger.info(f'mconfig.SGSSCAN_W_0 = {self.mconfig_data.SGSSCAN_W_0.value}')
        logger.info(f'mconfig.SGSSCAN_W_1 = {self.mconfig_data.SGSSCAN_W_1.value}')
        logger.info(f'mconfig.SGSSCAN_W_2 = {self.mconfig_data.SGSSCAN_W_2.value}')
        logger.info(f'mconfig.SGSSCAN_W_3 = {self.mconfig_data.SGSSCAN_W_3.value}')
        logger.info(f'mconfig.SGSSCAN_W_4 = {self.mconfig_data.SGSSCAN_W_4.value}')

        data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
        logger.flow(2, 'Issue 4071 check default value')
        compare_value(data_4071.sgs_read_count_threshold.value, self.mconfig_data.SGSSCAN_RC_TH.value * 1000000000 * self.CE, desc="sgs_read_count_threshold")
        compare_value(data_4071.sgs_read_count_threshold_list[0].value, self.mconfig_data.SGSSCAN_RC_0.value * 1000000000* self.CE,desc="sgs_read_count_threshold_0")
        compare_value(data_4071.sgs_read_count_threshold_list[1].value, self.mconfig_data.SGSSCAN_RC_1.value * 1000000000* self.CE, desc="sgs_read_count_threshold_1")
        compare_value(data_4071.sgs_read_count_threshold_list[2].value, self.mconfig_data.SGSSCAN_RC_2.value * 1000000000* self.CE, desc="sgs_read_count_threshold_2")
        compare_value(data_4071.sgs_read_count_threshold_list[3].value, self.mconfig_data.SGSSCAN_RC_3.value * 1000000000* self.CE, desc="sgs_read_count_threshold_3")
        compare_value(data_4071.sgs_scan_window_list[0].value, self.mconfig_data.SGSSCAN_W_0.value* 1000000* self.CE, desc="sgs_scan_window_0")
        compare_value(data_4071.sgs_scan_window_list[1].value, self.mconfig_data.SGSSCAN_W_1.value * 1000000* self.CE, desc="sgs_scan_window_1")
        compare_value(data_4071.sgs_scan_window_list[2].value, self.mconfig_data.SGSSCAN_W_2.value * 1000000* self.CE, desc="sgs_scan_window_2")
        compare_value(data_4071.sgs_scan_window_list[3].value, self.mconfig_data.SGSSCAN_W_3.value * 1000000* self.CE, desc="sgs_scan_window_3")
        for i in range(len(data_4071.sgs_scan_event_cnt_TLC)):
            compare_value(data_4071.sgs_scan_event_cnt_TLC[i].value, 0, desc=f"sgs_scan_event_cnt_{i}_TLC")
        for i in range(len(data_4071.sgs_scan_event_cnt_SLC)):
            compare_value(data_4071.sgs_scan_event_cnt_SLC[i].value, 0, desc=f"sgs_scan_event_cnt_{i}_SLC")
        pass
    def step2(self) -> None:
        open_card()  
        logger.flow(1, 'Test VU 404B to_erase_with_SGM_enabled')
        group_list = ["FREE_BLK_QUEUE_MLC"]
        free_block = choose_free_block(group_list)
        #region
        #free_block = choose_free_block('FREE_BLK_QUEUE_MLC')
        # param = project_api.D017_param()
        # param.scan_type.value = 1
        # param.block.value = free_block
        # param.die.value = 0
        # param.plane.value = 5
        # param.error_inject_enable.value = 1
        # param.first_low_vt_scan.value = 0
        # param.touch_up.value =1
        # param.low_vt_re_scan.value = 1
        # param.high_vt_scan.value = 0
        # param.switch.value = 1
        # param.index.value = 0
        # print_param(param)
        # case=5
        # param = choose_D017_param(free_block, case, self.CE, 6)
        # project_api.issue_D017_to_create_SGM_fail(param)
        # logger.flow("3", f'Send 404B to vb={param.block.value} force trigger SGM')
        # result = project_api.issue_404B_to_erase_with_SGM_enabled(param.block.value,enable_retirement=1)
        #endregion

        param = project_api.D017_param()
        param.block.value = free_block
        for case in range(13):
            param.first_low_vt_scan.value = random.randint(0,1)
            param.low_vt_re_scan.value = random.randint(0,1)
            param.high_vt_scan.value = random.randint(0,1)
            param.switch.value = random.randint(0,3)
            param = choose_D017_param(param.block.value, case, self.CE, self.PLANE_PER_DIE)
            for enable_retirement in [0, 1]:
                for error_inject_error in [0, 1]:
                    param.error_inject_enable.value = error_inject_error
                    param.block.value = param.block.value
                    logger.flow("2", 'Send D017 with param')
                    print_param(param)
                    project_api.issue_D017_to_create_SGM_fail(param)
                    logger.flow("3", f'Send 404B to vb={param.block.value} force trigger SGM')
                    result = project_api.issue_404B_to_erase_with_SGM_enabled(param.block.value,enable_retirement=enable_retirement)
                    logger.flow("4", 'Check is retirement case or not')
                    is_retirement_case = check_is_retirement_case(param)
                    logger.info(f'is retirement case = {is_retirement_case}')
                    if error_inject_error == 1:
                        if is_retirement_case == True:
                            compare_value(result, expect_value=0)
                            if enable_retirement == 0:
                                is_bad_blk = check_vb_in_BBT(param.block.value, param)
                                if is_bad_blk != False:
                                    logger.error('enable retirement = 0, fail case cannot retire')
                                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                            else:
                                is_bad_blk = check_vb_in_BBT(param.block.value, param)
                                if is_bad_blk != True:
                                    logger.error('enable retirement = 1,  fail case  should retire')
                                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                            param.block.value = choose_free_block(group_list)
                        else:
                            compare_value(result, expect_value=1)
                            is_bad_blk = check_vb_in_BBT(param.block.value, param)
                            if is_bad_blk != False:
                                logger.error('Not fail case, cannot retire')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                    else:
                        compare_value(result, expect_value=1)
                        is_bad_blk = check_vb_in_BBT(param.block.value, param)
                        if is_bad_blk != False:
                            logger.error('Not fail case, cannot retire')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    
                                   
                 
    def step3(self) -> None:
        
        for case in TestCases: 
            open_card()
            project_api.issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(0)
            logger.flow(3, f'Case = {case.name}')
            logger.flow(3, 'Configuration')
            data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
            if case == TestCases.TLC_L2:
                slc_lun, tlc_lun = config_lun(slc_au=0, tlc_au=self.total_au)
            elif case == TestCases.WB_L2:
                max_wb_size = self._param.gGeometry.l79_write_booster_buffer_max_n_alloc_units
                slc_lun, tlc_lun = config_lun(slc_au=0, tlc_au=self.total_au, wb_au=max_wb_size)
            else:
                slc_lun, tlc_lun = config_lun(slc_au=self.total_au, tlc_au=0)

            self.write_record = api.get_empty_write_record()
            param = project_api.C071_param()
            param.sgs_scan_dynamic_read_count.value = 0
            param.sgs_scan_static_read_count.value = 0
            project_api.issue_C071_to_set_SGD_scan_parameters(param)

            if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                lun = tlc_lun
                total_len = self.TLC_VB_4K_SIZE
            else:
                lun = slc_lun
                total_len = self.SLC_VB_4K_SIZE
            
            logger.flow(4, 'Get free vb')
            if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                group_list = ["FREE_BLK_QUEUE_MLC"]
            else:
                group_list = ["FREE_BLK_QUEUE_SLC", "FREE_BLK_QUEUE_TABLE"]
            free_block = choose_free_block(group_list)

            logger.flow(5, f'Send 404B to vb={free_block} force trigger SGM')
            result = project_api.issue_404B_to_erase_with_SGM_enabled(free_block,enable_retirement=1)
            compare_value(result, 1, desc="404B result")  

            logger.flow(6, 'Send VU 4071 to get SGS value')
            data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
            if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                compare_value(data_4071.sgs_scan_event_cnt_TLC[0].value, 1, desc="sgs_scan_event_cnt_0_TLC")
            else:
                compare_value(data_4071.sgs_scan_event_cnt_SLC[0].value, 1, desc="sgs_scan_event_cnt_0_SLC")
                
            next_gen_threshold_cnt = next_trigger_rc = data_4071.sgs_read_count_threshold.value

            logger.flow(7, 'Test trigger SGM in all RC level')
            first_time = True
            rc_level = 0
            last_event_cnt = 0
            flagged = True
            stop_event_value = 0
           
            while (stop_event_value < 3):  
                if rc_level == 0 and first_time:
                    logger.info(f'current rc range,  rc < RC_THRESHOLD')
                elif rc_level == 0:
                    logger.info(f'current rc range,  RC_THRESHOLD < rc < RC_THRESHOLD_{rc_level}')
                else:
                    logger.info(f'current rc range,  RC_THRESHOLD_{rc_level-1} < rc < RC_THRESHOLD_{rc_level}')
                
                if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                    lun = tlc_lun
                    total_len = self.TLC_VB_4K_SIZE
                    logger.info(f'current read count = {data_4071.curr_read_count_TLC.value}, next trigger SGM read count = {data_4071.remain_read_count_trigger_sgs_TLC.value}')
                
                else:
                    lun = slc_lun
                    total_len = self.SLC_VB_4K_SIZE
                    logger.info(f'current read count = {data_4071.curr_read_count_SLC.value}, next trigger SGM read count = {data_4071.remain_read_count_trigger_sgs_SLC.value}')

                logger.flow(8, f'Write 1 {case.name} VB')
                if case == TestCases.WB_L2:
                    api.set_flag(api.FlagIDN.WRITEBOOSTER_EN)
                else:
                    api.clear_flag(api.FlagIDN.WRITEBOOSTER_EN)

                write_data(lun=lun,start_lba=0,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len, write_record=self.write_record)

                logger.flow(9, 'Send VUC = l2p(0x88) to get pca')
                pca = api.lba_to_pba(lun,lba=0)
                vb_number = pca.w10_block.value

                logger.flow(10, f'Send VU C071 to adjust read count = next trigger rc - 1 = {next_trigger_rc-1}')
                param = project_api.C071_param()
                if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                    param.sgs_scan_dynamic_read_count.value = next_trigger_rc - 1
                    param.sgs_scan_static_read_count.value = data_4071.curr_read_count_SLC.value
                else:
                    param.sgs_scan_dynamic_read_count.value = data_4071.curr_read_count_TLC.value
                    param.sgs_scan_static_read_count.value = next_trigger_rc - 1

                if not first_time:
                    if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                        param.sgs_scan_dynamic_event_cnt[rc_level+1].value = last_event_cnt
                    else:
                        param.sgs_scan_static_event_cnt[rc_level+1].value = last_event_cnt
                project_api.issue_C071_to_set_SGD_scan_parameters(param)
                
                logger.flow(11, 'Read len = 1 to flag vb')
                read_data(lun=lun,start_lba=0,len=1,total_len=1)

                logger.flow(12, 'Send 4071 to check sgs value')
                data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
                
                if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                    current_read_count = data_4071.curr_read_count_TLC.value
                else:
                    current_read_count = data_4071.curr_read_count_SLC.value
                logger.info(f'current read cnt TLC ={data_4071.curr_read_count_TLC.value}, current read cnt SLC = {data_4071.curr_read_count_SLC.value}')

                if current_read_count >= next_gen_threshold_cnt:
                    flagged = False
                else:
                    flagged = True

                if (rc_level == 0 and first_time == True) or flagged == False: #first time
                    if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                        compare_value(data_4071.sgs_scan_flagged_physical_vb_cnt.value, 0,desc="sgs_scan_flagged_physical_vb_cnt")
                        compare_value(data_4071.sgs_scan_flagged_physical_vbNumb[vb_number].value, 0, desc=f"sgs_scan_flagged_physical_vbNumb[{vb_number}]")
                    else:
                        logger.info(f'scan_flagged_physical_vb_cnt = {data_4071.sgs_scan_flagged_physical_vb_cnt.value}')
                        for i in range(len(data_4071.sgs_scan_flagged_physical_vbNumb)):
                            if data_4071.sgs_scan_flagged_physical_vbNumb[i].value != 0:
                                logger.info(f'vbNum = {i} be flagged')
                                if not check_vb_in(i, VBPolicy.LOG_PTE):
                                    logger.error(f'When read count not reach threshold, flagged VB must belong to the LOG_TAB_BLK, CURRENT_PTE, or PTE_POOL group')
                                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                    pass
                else:
                    if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                        compare_value(data_4071.sgs_scan_flagged_physical_vb_cnt.value, 1,desc="sgs_scan_flagged_physical_vb_cnt")
                        for i in range(len(data_4071.sgs_scan_flagged_physical_vbNumb)):
                            if data_4071.sgs_scan_flagged_physical_vbNumb[i].value != 0:
                                logger.info(f'vbNum = {i} be flagged')
                        compare_value(data_4071.sgs_scan_flagged_physical_vbNumb[vb_number].value, 1, desc=f"sgs_scan_flagged_physical_vbNumb[{vb_number}]")
                    else:
                        logger.info(f'scan_flagged_physical_vb_cnt = {data_4071.sgs_scan_flagged_physical_vb_cnt.value}')
                        if data_4071.sgs_scan_flagged_physical_vb_cnt.value < 1:
                            logger.error('When the RC threshold is reached, at least one VB must be flagged')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL  
                        for i in range(len(data_4071.sgs_scan_flagged_physical_vbNumb)):
                            if data_4071.sgs_scan_flagged_physical_vbNumb[i].value != 0:
                                logger.info(f'vbNum = {i} be flagged')
                                if not check_vb_in(i, VBPolicy.LOG_PTE_SLC):
                                    logger.error(f'When read count not reach threshold, flagged VB must belong to the LOG_TAB_BLK, CURRENT_PTE, PTE_POOL, or USED_BLK_POOL_SLC group')
                                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                physical_cnt_before_erase = data_4071.sgs_scan_flagged_physical_vb_cnt.value
                
                if current_read_count >= next_gen_threshold_cnt:

                    if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                        remain = data_4071.remain_read_count_trigger_sgs_TLC.value
                    else:
                        remain = data_4071.remain_read_count_trigger_sgs_SLC.value
                    logger.info(f'current rc({current_read_count}) >= next gen threshold cnt({next_gen_threshold_cnt}), gen new remain value = {remain}')
                    
                    interval = remain - current_read_count
                    if interval < 1 or interval > data_4071.sgs_scan_window_list[rc_level].value:
                        logger.error(f"Expect interval should >= 1 and <= sgs_scan_window_{rc_level}={data_4071.sgs_scan_window_list[rc_level].value}, but = {interval}")
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    
                    next_gen_threshold_cnt = current_read_count + data_4071.sgs_scan_window_list[rc_level].value
                    next_trigger_rc = remain
                else:
                    next_trigger_rc = next_gen_threshold_cnt    

                logger.info(f'next gen threshold cnt = {next_gen_threshold_cnt}, next trigger rc = {next_trigger_rc}, interval = {interval}')

                
                is_bad_blk_before = check_vb_in_BBT(vb_number)

                logger.flow(13, 'Erase to trigger SGM')
                unmap_data(lun=lun,start_lba=0,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len, write_record=self.write_record)  
                purge_operation()

                logger.flow(14, 'Send 4071 to check event cnt increase')
                data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)

                if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                    if (rc_level == 0 and first_time == True):
                        event_cnt = data_4071.sgs_scan_event_cnt_TLC[rc_level].value
                        compare_value(event_cnt,last_event_cnt,desc=f"sgs_scan_event_cnt_{rc_level}_TLC")
                    elif flagged == False:
                        event_cnt = data_4071.sgs_scan_event_cnt_TLC[rc_level+1].value
                        compare_value(event_cnt, last_event_cnt, desc=f"sgs_scan_event_cnt_{rc_level+1}_TLC") 
                    else:
                        event_cnt = data_4071.sgs_scan_event_cnt_TLC[rc_level+1].value
                        compare_value(event_cnt, last_event_cnt + 1, desc=f"sgs_scan_event_cnt_{rc_level+1}_TLC")   
                else:
                    
                    physical_cnt_after_erase = data_4071.sgs_scan_flagged_physical_vb_cnt.value
                    diff = physical_cnt_before_erase - physical_cnt_after_erase 
                    event_cnt = data_4071.sgs_scan_event_cnt_SLC[rc_level+1].value
                    logger.info(f'sgs_scan_event_cnt_{rc_level+1}_SLC val = {event_cnt}')
                    if(event_cnt - last_event_cnt) != diff:
                        logger.info(f'event cnt before erase = {last_event_cnt}, event cnt after erase = {event_cnt}')
                        logger.info(f'scan_flagged_physical_vb_cnt before erase = {physical_cnt_before_erase}, scan_flagged_physical_vb_cnt after erase = {physical_cnt_after_erase }')
                        logger.error(f'After VB erase, scan_flagged_physical_vb_cnt must equal the delta of the event count') 
                        logger.error(f'event cnt - last event cnt = {event_cnt - last_event_cnt}, scan_flagged_physical_vb_cnt - last scan_flagged_physical_vb_cnt = {diff}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL  
                last_event_cnt = event_cnt
                logger.info(f'scan_flagged_physical_vb_cnt = {data_4071.sgs_scan_flagged_physical_vb_cnt.value}')

                logger.flow(15, 'Send 4071 to check flagged physical vb cnt / flagged physical vbNumb = 0 after trigger SGM')
                if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                    compare_value(data_4071.sgs_scan_flagged_physical_vb_cnt.value, 0,desc="sgs_scan_flagged_physical_vb_cnt")
                    compare_value(data_4071.sgs_scan_flagged_physical_vbNumb[vb_number].value, 0, desc=f"sgs_scan_flagged_physical_vbNumb[{vb_number}]")
                else:
                    for i in range(len(data_4071.sgs_scan_flagged_physical_vbNumb)):
                        if data_4071.sgs_scan_flagged_physical_vbNumb[i].value != 0:
                            logger.info(f'vbNum = {i} be flagged')
                            if not check_vb_in(i, VBPolicy.LOG_PTE):
                                logger.error(f'When read count not reach threshold, flagged VB must belong to the LOG_TAB_BLK, CURRENT_PTE, PTE_POOL group')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

                logger.flow(16, f'Send VU = 405E to check vb={vb_number} not in retirement bitmap')
                param_D017 = project_api.D017_param()
                is_bad_blk = check_vb_in_BBT(vb_number)
                if is_bad_blk == True and is_bad_blk_before == False:
                    logger.error(f'Expect vb={vb_number} not be retired, but not')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                if event_cnt == 1 and rc_level < 4:
                    logger.flow(17, f'Send VU C071 to adjust read count = {data_4071.sgs_read_count_threshold_list[rc_level].value} (RC_THRESHOLD_{rc_level})')
                    next_trigger_rc = data_4071.sgs_read_count_threshold_list[rc_level].value
                    rc_level += 1
                    param = project_api.C071_param()
                    if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                        param.sgs_scan_dynamic_read_count.value = next_trigger_rc
                        param.sgs_scan_static_read_count.value = data_4071.curr_read_count_SLC.value
                        param.sgs_scan_dynamic_event_cnt[rc_level].value = last_event_cnt
                    else:
                        param.sgs_scan_dynamic_read_count.value = data_4071.curr_read_count_TLC.value
                        param.sgs_scan_static_read_count.value = next_trigger_rc
                        param.sgs_scan_static_event_cnt[rc_level].value = last_event_cnt
   
                    project_api.issue_C071_to_set_SGD_scan_parameters(param)

                    logger.info('Send VU 4071 to get SGS value')
                    data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
                    if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                        remain = data_4071.remain_read_count_trigger_sgs_TLC.value
                        current_read_count = data_4071.curr_read_count_TLC.value
                    else:
                        remain = data_4071.remain_read_count_trigger_sgs_SLC.value
                        current_read_count = data_4071.curr_read_count_SLC.value
                    
                    next_trigger_rc = remain
                    next_gen_threshold_cnt = current_read_count + data_4071.sgs_scan_window_list[rc_level].value
                    logger.info(f'next gen threshold cnt = {next_gen_threshold_cnt}, next trigger rc = {next_trigger_rc}, current rc = {current_read_count}')
                    last_event_cnt = 0

                if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                    stop_event_value = data_4071.sgs_scan_event_cnt_TLC[5].value
                else:
                    stop_event_value = data_4071.sgs_scan_event_cnt_SLC[5].value

                first_time = False
                
            logger.flow(19, 'read compare erase success')
            read_compare(self.write_record)
        pass
        
    def step4(self) -> None:
        open_card()        
        EVENT_LOG_COMPARERS = {
            0x0026: compare_eventlog_0x0026,
            0x6009: compare_eventlog_0x6009,
            0x6008: compare_eventlog_0x6008,
        }
        for test_case in range(2):
            if test_case == 0:
                logger.flow(21, 'VU 0xD0F8 disable eventlog test (disable single event log)')
                disable_logs = [0x6008]
            else:
                logger.flow(21, 'VU 0xD0F8 disable eventlog test (disable multiple event log)')
                disable_logs = [0x6008, 0x0026]

            for reset_type_value in range(Dcmd5ResetType.HW_RESET, Dcmd5ResetType.UNIPRO_RESET+1):
                
                reset_type = Dcmd5ResetType(reset_type_value)

                logger.flow(22, f'Send 4080 to get current eventlog id=0x6008/0x6009/0x0026')
                
                output_before_list = []
                for event_id in disable_logs:
                    output_before_list.append(project_api.issue_find_event_log_by_id(event_id, EventLogPriority.LowPriority)) 

                logger.flow(23, 'VU 0xD0F8 disable eventlog id = 0x6008/0x6009/0x0026')
                project_api.issue_D08F_to_disable_some_event_log(disable_logs)
            
                logger.flow(24, 'trigger 0x6008/0x6009/0x0026 event (touchup occurred + scan done + retirement)')
                param = self.force_trigger_sgm(case=1)

                logger.flow(25, f'Send 4080 to check not flush eventlog id=0x6008/0x6009/0x0026')
                output_after_list = []
                for event_id in disable_logs:
                    output_after_list.append(project_api.issue_find_event_log_by_id(event_id, EventLogPriority.LowPriority)) 

                for i, event_id in enumerate(disable_logs):
                    if len(output_after_list[i]) != len(output_before_list[i]):
                        logger.error_lb(f'issue D08F to disable eventlog id={hex(disable_logs[i])} -> trigger sgm touchup + retirement check not flush eventlog')
                        logger.error_fp(f'Expect D08F disable {hex(disable_logs[i])}, but not')
                        raise SIGHTING_RESPONSE_UNEXPECTED
                
                logger.flow(26, f'H8 Enter/Exit')
                self.enter_exit_h8()

                logger.flow(27, 'trigger 0x6008/0x6009/0x0026 event (touchup occurred + scan done + retirement)')
                param = self.force_trigger_sgm(case=1)

                output_after_list = []
                for event_id in disable_logs:
                    output_after_list.append(project_api.issue_find_event_log_by_id(event_id, EventLogPriority.LowPriority)) 

                for i, event_id in enumerate(disable_logs):
                    if len(output_after_list[i]) != len(output_before_list[i]):
                        logger.error_lb(f'issue D08F to disable eventlog id={hex(disable_logs[i])} -> trigger sgm touchup + retirement check not flush eventlog')
                        logger.error_fp(f'Expect D08F disable {hex(disable_logs[i])}, but not')
                        raise SIGHTING_RESPONSE_UNEXPECTED
                
                logger.flow(28, f'do reset, reset type = {reset_type.name}')
                init_tester_to_unit_ready(reset_type)

                logger.flow(29, 'trigger 0x6008/0x6009/0x0026 event (touchup occurred + scan done + retirement)')
                param = self.force_trigger_sgm(case=1)
                
                logger.flow(30, f'Send 4080 to check flush eventlog id=0x6008/0x6009/0x0026')
                output_after_list = []
                for event_id in disable_logs:
                    output_after_list.append(project_api.issue_find_event_log_by_id(event_id, EventLogPriority.LowPriority)) 

                for i, event_id in enumerate(disable_logs):
                    if len(output_after_list[i]) != (len(output_before_list[i]) + 1):
                        logger.error_lb(f'reset = {reset_type.name} to re-enable eventlog id={hex(disable_logs[i])} -> trigger sgm touchup + retirement check flush eventlog')
                        logger.error_fp(f'reset = {reset_type.name} to re-enable eventlog id={hex(disable_logs[i])}, but not')
                        raise SIGHTING_RESPONSE_UNEXPECTED
                
                for i, event_id in enumerate(disable_logs):
                    logger.flow(31, f'check eventlog id={hex(disable_logs[i])}')
                    newest_log = output_after_list[i][-1] 
                    if event_id in EVENT_LOG_COMPARERS:
                        comparer_func = EVENT_LOG_COMPARERS[event_id]
                        comparer_func(newest_log, param)
                    else:
                        logger.error_lb(f'pls check the input event log')
                        logger.error_fp(f'eventlog id ={hex(disable_logs[i])}, not defined')
                        raise SIGHTING_RESPONSE_UNEXPECTED
        pass
             
    def force_trigger_sgm(self, case:int)-> project_api.D017_param:
        group_list = ["FREE_BLK_QUEUE_MLC"]
        free_block = choose_free_block(group_list)
        
        logger.flow(2, 'Send D017 with param')
        param = choose_D017_param(free_block, case, self.CE, self.PLANE_PER_DIE)
        project_api.issue_D017_to_create_SGM_fail(param)

        logger.flow(3, f'Send 404B to vb={param.block.value} force trigger SGM')
        result = project_api.issue_404B_to_erase_with_SGM_enabled(param.block.value,enable_retirement=1)
        
        return param
    def enter_exit_h8(self) -> None:
        f = ExecuteCMD.CmdSeqHibernate() 
        f.set_option(
            hibernate_enter=1,
            hibernate_exit=1,
            loopcount=10,
            delayafterenter=500,
            delayafterexit=1000,
            wait_queue_empty=True,
            delay_time=100
        )
        
        ExecuteCMD.enqueue(f)
        ExecuteCMD.send(clear_on_success=True)
        ExecuteCMD.clear()

    def post_process(self) -> None:
        
        pass
    

run = Pattern().run
if __name__ == "__main__":
    run()