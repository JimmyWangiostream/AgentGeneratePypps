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

class TestCases(IntEnum):
    SLC_L2 = 0
    TLC_L2 = 1
    WB_L2 = 2
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
        pass

    def step1(self) -> None:
        self.error_flow()
        pass
    def post_process(self) -> None:
        open_card()
        pass
       
    def error_flow(self)->None:

        for case in TestCases:  
            open_card()    
            project_api.issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(0)
            logger.flow(1, f'Case = {case.name}')
            logger.flow(1, 'Configuration')
            if case == TestCases.TLC_L2:
                slc_lun, tlc_lun = config_lun(slc_au=0, tlc_au=self.total_au)
            elif case == TestCases.WB_L2:
                max_wb_size = self._param.gGeometry.l79_write_booster_buffer_max_n_alloc_units
                slc_lun, tlc_lun = config_lun(slc_au=0, tlc_au=self.total_au, wb_au=max_wb_size)
            else:
                slc_lun, tlc_lun = config_lun(slc_au=self.total_au, tlc_au=0)
            
            self.write_record = api.get_empty_write_record()
            
            data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)

            logger.flow(2, 'Test trigger SGM in all RC level')
            first_time = True
            rc_level = 0
            last_event_cnt = 0
            flagged = True
            loop = 0
            stop_event_value = 0
            re_config_times = 0
            next_gen_threshold_cnt = next_trigger_rc = data_4071.sgs_read_count_threshold.value
            
            while (stop_event_value < 1):  #do SGM until event 5 trigger 5 times
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

                logger.flow(3, f'Write 1 {case.name} VB')
                if case == TestCases.WB_L2:
                    api.set_flag(api.FlagIDN.WRITEBOOSTER_EN)
                else:
                    api.clear_flag(api.FlagIDN.WRITEBOOSTER_EN)

                write_data(lun=lun,start_lba=0,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len, write_record=self.write_record)

                logger.flow(4, 'Send VUC = l2p(0x88) to get pca')
                pca = api.lba_to_pba(lun,lba=0)
                vb_number = pca.w10_block.value

                logger.flow(5, f'Send VU C071 to adjust read count = next trigger rc - 1 = {next_trigger_rc-1}')
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

                logger.flow(6, 'read len = 1 to flag vb')
                read_data(lun=lun,start_lba=0,len=1,total_len=1)

                logger.flow(7, 'Send 4071 to check sgs value')
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
                vb_flagged = []
                vb_flagged = data_4071.sgs_scan_flagged_physical_vbNumb   
                
                logger.flow(8, 'power cycle and send VU 4071 to check sgs value')
                reset_type = random.choice([Dcmd5ResetType.HW_RESET, Dcmd5ResetType.RESET_N])
                init_tester_to_unit_ready(reset_type)
                project_api.issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(0)
                
                data_4071_after_reset = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
                event_cnt = data_4071_after_reset.sgs_scan_event_cnt_TLC[rc_level+1].value
                compare_value(event_cnt, 0, desc=f"sgs_scan_event_cnt_{rc_level+1}_TLC")
                event_cnt = data_4071_after_reset.sgs_scan_event_cnt_SLC[rc_level+1].value
                compare_value(event_cnt, 0, desc=f"sgs_scan_event_cnt_{rc_level+1}_SLC")

                compare_value(data_4071_after_reset.sgs_scan_flagged_physical_vb_cnt.value, data_4071.sgs_scan_flagged_physical_vb_cnt.value,"sgs_scan_flagged_physical_vb_cnt")
                compare_value(data_4071_after_reset.sgs_scan_flagged_physical_vbNumb[vb_number].value, data_4071.sgs_scan_flagged_physical_vbNumb[vb_number].value, desc=f"sgs_scan_flagged_physical_vbNumb[{vb_number}]")
                if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                    if data_4071_after_reset.remain_read_count_trigger_sgs_TLC.value == 0x1999999999999999:
                        logger.error_lb(f'power cycle and send VU 4071 to check sgs value')
                        logger.error_fp(f'Expect remain_read_count_trigger_sqs_TLC({data_4071_after_reset.remain_read_count_trigger_sgs_TLC.value}) shall not reset after por')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    if data_4071_after_reset.remain_read_count_trigger_sgs_SLC.value == 0x1999999999999999:
                        logger.error_lb(f'power cycle and send VU 4071 to check sgs value')
                        logger.error_fp(f'Expect remain_read_count_trigger_sqs_SLC({data_4071_after_reset.remain_read_count_trigger_sgs_SLC.value}) shall not reset after por')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                if data_4071_after_reset.curr_read_count_SLC.value < data_4071.curr_read_count_SLC.value:
                    logger.error_lb(f'power cycle and send VU 4071 to check sgs value')
                    logger.error_fp(f'Expect current slc read count({data_4071_after_reset.curr_read_count_SLC.value}) >= before power cycle current slc read count({data_4071.curr_read_count_SLC.value}), but not')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                if data_4071_after_reset.curr_read_count_TLC.value < data_4071.curr_read_count_TLC.value:
                    logger.error_lb(f'power cycle and send VU 4071 to check sgs value')
                    logger.error_fp(f'Expect current tlc read count({data_4071_after_reset.curr_read_count_TLC.value}) >= before power cycle current tlc read count({data_4071.curr_read_count_TLC.value}), but not')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
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
                logger.flow(9, 'Send VU D017 to create fail')
                D017_param = choose_D017_param(vb_number,loop,self.CE, self.PLANE_PER_DIE)
                project_api.issue_D017_to_create_SGM_fail(D017_param)

                is_bad_blk_before = check_vb_in_BBT(vb_number)
                logger.flow(10, 'Erase to trigger SGM')
                unmap_data(lun=lun,start_lba=0,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len, write_record=self.write_record)  
                purge_operation()

                logger.flow(11, 'Send 4071 to check event cnt increase')
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
                    if(event_cnt - last_event_cnt) != diff:
                        logger.info(f'event cnt before erase = {last_event_cnt}, event cnt after erase = {event_cnt}')
                        logger.info(f'scan_flagged_physical_vb_cnt before erase = {physical_cnt_before_erase}, scan_flagged_physical_vb_cnt after erase = {physical_cnt_after_erase }')
                        logger.error(f'After VB erase, scan_flagged_physical_vb_cnt must equal the delta of the event count') 
                        logger.error(f'event cnt - last event cnt = {event_cnt - last_event_cnt}, scan_flagged_physical_vb_cnt - last scan_flagged_physical_vb_cnt = {diff}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL  
                last_event_cnt = event_cnt
                logger.info(f'scan_flagged_physical_vb_cnt = {data_4071.sgs_scan_flagged_physical_vb_cnt.value}')

                logger.flow(12, 'Send 4071 to check flagged physical vb cnt / flagged physical vbNumb = 0 after trigger SGM')
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

                logger.flow(13, f'Send VU = 405E to check vb={vb_number} not in retirement bitmap')
                
                is_retirement_case = check_is_retirement_case(D017_param)
                logger.info(f'is retirement case = {is_retirement_case}')
                is_bad_blk = check_vb_in_BBT(vb_number, D017_param)
                if (rc_level == 0 and first_time == True):
                    if is_bad_blk == True and is_bad_blk_before == False:
                        logger.error(f'Expect vb={vb_number} not be retired, but not')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                elif flagged == False:
                    if is_bad_blk == True and is_bad_blk_before == False:
                        logger.error(f'Expect vb={vb_number} not be retired, but not')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:  
                    if vb_flagged[vb_number].value == 1:
                        if is_retirement_case == True:
                                logger.flow(2, f'Send VUC = 0x405E check vb={vb_number} is in retirement bitmap')
                                if is_bad_blk == False:
                                    logger.error(f'Expect vb={vb_number} be retired, but not')
                                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        else:
                            if is_bad_blk == True and is_bad_blk_before == False:
                                logger.error(f'Expect vb={vb_number} not be retired, but not')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        
                logger.flow(14, 'Re-config and send 4071 get sgs param')
                if re_config_times < 5:
                    re_config_times += 1
                    if case == TestCases.TLC_L2:
                        slc_lun, tlc_lun = config_lun(slc_au=0, tlc_au=self.total_au)
                    elif case == TestCases.WB_L2:
                        max_wb_size = self._param.gGeometry.l79_write_booster_buffer_max_n_alloc_units
                        slc_lun, tlc_lun = config_lun(slc_au=0, tlc_au=self.total_au, wb_au=max_wb_size)
                    else:
                        slc_lun, tlc_lun = config_lun(slc_au=self.total_au, tlc_au=0)
                    self.write_record = api.get_empty_write_record()
                    data_4071_after_config = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)

                    if case == TestCases.TLC_L2 or case == TestCases.WB_L2:
                        
                        if data_4071_after_config.remain_read_count_trigger_sgs_TLC.value > next_gen_threshold_cnt:
                            next_gen_threshold_cnt += data_4071.sgs_scan_window_list[rc_level].value
                            next_trigger_rc = next_gen_threshold_cnt
                        else:
                            next_trigger_rc = data_4071_after_config.remain_read_count_trigger_sgs_TLC.value
                        if data_4071_after_config.remain_read_count_trigger_sgs_TLC.value == 0x1999999999999999:
                            logger.error(f'remain_read_count_trigger_sgs_TLC = {data_4071_after_config.remain_read_count_trigger_sgs_TLC.value} should not reset tlc remain')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        if data_4071_after_config.curr_read_count_TLC.value == 0:
                            logger.error(f'curr_read_count_TLC = {data_4071_after_config.curr_read_count_TLC.value} should not reset  tlc read count')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    else:
                        
                        if data_4071_after_config.remain_read_count_trigger_sgs_SLC.value > next_gen_threshold_cnt:
                            next_gen_threshold_cnt += data_4071.sgs_scan_window_list[rc_level].value
                            next_trigger_rc = next_gen_threshold_cnt
                        else:
                            next_trigger_rc = data_4071_after_config.remain_read_count_trigger_sgs_SLC.value
                        if data_4071_after_config.remain_read_count_trigger_sgs_SLC.value == 0x1999999999999999:
                            logger.error(f'remain_read_count_trigger_sgs_SLC = {data_4071_after_config.remain_read_count_trigger_sgs_SLC.value} should not reset slc remain')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        if data_4071_after_config.curr_read_count_SLC.value == 0:
                            logger.error(f'curr_read_count_SLC = {data_4071_after_config.curr_read_count_SLC.value} should not reset slc read count')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                if event_cnt == 1 and rc_level < 4:
                    logger.flow(15, f'Send VU C071 to adjust read count = {data_4071.sgs_read_count_threshold_list[rc_level].value} (RC_THRESHOLD_{rc_level})')
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
                if flagged == True:
                    loop += 1
            logger.flow(16, 'read compare erase success')
            read_compare(self.write_record)
        pass
        
run = Pattern().run 
if __name__ == "__main__":
    run()