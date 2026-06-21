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
    PTE = 0
    LOG = 1
    SWAP = 2

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
        self.trigger_flow()
        #self.not_trigger_flow()
        
        pass
        
    def post_process(self) -> None:
        open_card()
        pass
    def not_trigger_flow(self) ->None:
        open_card()
        project_api.issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(0)
        logger.flow(16, 'Configuration')
        slc_lun, tlc_lun = config_lun(slc_au=self.total_au//2, tlc_au=self.total_au//2)

        lun = tlc_lun
        total_len = self.TLC_VB_4K_SIZE
        
        logger.flow(17, 'Send VU 4071 to get SGS value')
        
        data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
        next_gen_threshold_cnt = next_trigger_rc = data_4071.sgs_read_count_threshold.value

        lun = tlc_lun
        total_len = self.TLC_VB_4K_SIZE
        logger.info(f'current read cnt TLC ={data_4071.curr_read_count_TLC.value}, current read cnt SLC = {data_4071.curr_read_count_SLC.value}')
        logger.flow(18, f'Write all card')
        data_len =  self._param.gLUCapacity[slc_lun]
        write_data(lun=slc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=data_len,write_record=self.write_record) 
        _, open_vb_info = api.get_open_vb_info()

        data_len =  self._param.gLUCapacity[tlc_lun]
        write_data(lun=tlc_lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=data_len, write_record=self.write_record)
        logger.flow(19, f'get open vb info')
        _, open_vb_info = api.get_open_vb_info()
        print_open_vb_information_phison(open_vb_info)
        pca, vb_number = self.get_current_open_vb(TestCases.SWAP, open_vb_info)

        logger.flow(20, f'Send VU C071 to adjust read count = next trigger rc - 1 = {next_trigger_rc-1}')
        param = project_api.C071_param()
        param.sgs_scan_dynamic_read_count.value = data_4071.curr_read_count_TLC.value 
        param.sgs_scan_static_read_count.value = next_trigger_rc - 1
        project_api.issue_C071_to_set_SGD_scan_parameters(param)
        data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)

        logger.flow(21, 'spor to read swap vb')
        init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)
    
        logger.flow(22, 'Check slc read count not increase')
        data_4071_after_read = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
        compare_value(data_4071_after_read.curr_read_count_SLC.value, data_4071.curr_read_count_SLC.value, desc="curr_read_count_SLC")
        
    def trigger_flow(self)->None:
        
        for case in [TestCases.PTE, TestCases.LOG]:   
            
            open_card()
            project_api.issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(0)
            logger.flow(1, f'Case = {case.name}')
            logger.flow(1, 'Configuration')
            slc_lun, tlc_lun = config_lun(slc_au=0, tlc_au=self.total_au)
            lun = tlc_lun
            
            logger.flow(2, 'Send VU 4071 to get SGS value')
            
            data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)

            next_gen_threshold_cnt = next_trigger_rc = data_4071.sgs_read_count_threshold.value
            logger.info(f'inital slc read count = {data_4071.curr_read_count_SLC.value}')
            logger.flow(3, 'Test trigger SGM in all RC level')
            first_time = True
            rc_level = 0
            last_event_cnt = 0
            flagged = True
            loop = 0
            lun = tlc_lun
            logger.info(f'current read count = {data_4071.curr_read_count_SLC.value}, next trigger SGM read count = {data_4071.remain_read_count_trigger_sgs_SLC.value}')
        
            logger.flow(4, f'Write all card')
            write_data(lun=lun,start_lba=0,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=self._param.gLUCapacity[lun], write_record=self.write_record)

            stop_event_value = 0
            
            while (stop_event_value < 1):  
                if rc_level == 0 and first_time:
                    logger.info(f'current rc range,  rc < RC_THRESHOLD')
                elif rc_level == 0:
                    logger.info(f'current rc range,  RC_THRESHOLD < rc < RC_THRESHOLD_{rc_level}')
                else:
                    logger.info(f'current rc range,  RC_THRESHOLD_{rc_level-1} < rc < RC_THRESHOLD_{rc_level}')

                
                data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
                logger.info(f'current read cnt TLC ={data_4071.curr_read_count_TLC.value}, current read cnt SLC = {data_4071.curr_read_count_SLC.value}')
                
                logger.flow(6, f'Send VU C071 to adjust read count = next trigger rc - 1 = {next_trigger_rc-1}')
                param = project_api.C071_param()
                param.sgs_scan_dynamic_read_count.value = data_4071.curr_read_count_TLC.value  
                param.sgs_scan_static_read_count.value = next_trigger_rc - 1
                project_api.issue_C071_to_set_SGD_scan_parameters(param)

                logger.flow(7, f'read {case.name} vb to flag vb')
                if case == TestCases.PTE:
                    read_data(lun=lun,start_lba=0,len=1,total_len=1)
                    _, vu_pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=0)
                    vb_number = vu_pca.PPT_virtual_block_number.value
                    logger.info(f'pte vb number = {vb_number}')
                    
                elif case == TestCases.LOG:
                    logger.flow(5, f'Get {case.name} open vb')
                    _, open_vb_info = api.get_open_vb_info()
                    pca, vb_number = self.get_current_open_vb(case, open_vb_info)
                    logger.info(f'log vb number = {vb_number}')
                    ssu = ExecuteCMD.StartStopUnit()
                    ssu.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0)
                    ssu.set_option(wait_queue_empty=True)
                    ExecuteCMD.enqueue(ssu)
                    ssu.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0)
                    ssu.set_option(wait_queue_empty=True)
                    ExecuteCMD.enqueue(ssu)
                    ExecuteCMD.send(clear_on_success=True)
               
                logger.flow(8, 'Send 4071 to check sgs value')
                data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
  
                current_read_count = data_4071.curr_read_count_SLC.value
                logger.info(f'current read cnt TLC ={data_4071.curr_read_count_TLC.value}, current read cnt SLC = {data_4071.curr_read_count_SLC.value}')
                
                if current_read_count >= next_gen_threshold_cnt:
                    flagged = False
                else:
                    flagged = True

                if (rc_level == 0 and first_time == True) or flagged == False: 
                    compare_value(data_4071.sgs_scan_flagged_physical_vb_cnt.value, 0,desc="sgs_scan_flagged_physical_vb_cnt")
                    compare_value(data_4071.sgs_scan_flagged_physical_vbNumb[vb_number].value, 0, desc=f"sgs_scan_flagged_physical_vbNumb[{vb_number}]")
                    for i in range(len(data_4071.sgs_scan_flagged_physical_vbNumb)):
                        if data_4071.sgs_scan_flagged_physical_vbNumb[i].value != 0:
                            logger.info(f'vbNum = {i} be flagged, non flagged case')
                            check_vb_in_which_group(i)
                    pass
                else:
                    compare_value(data_4071.sgs_scan_flagged_physical_vb_cnt.value, 1,desc="sgs_scan_flagged_physical_vb_cnt")
                    for i in range(len(data_4071.sgs_scan_flagged_physical_vbNumb)):
                        if data_4071.sgs_scan_flagged_physical_vbNumb[i].value != 0:
                            logger.info(f'vbNum = {i} be flagged')
                            vb_group_name = check_vb_in_which_group(i)
                            flag_vb_number = i
                    
                    if case == TestCases.PTE:
                        if vb_group_name == "LOG_TAB_BLK" or vb_group_name == "PTE_POOL":
                            vb_number = flag_vb_number
                    else:
                        compare_value(data_4071.sgs_scan_flagged_physical_vbNumb[vb_number].value, 1, desc=f"sgs_scan_flagged_physical_vbNumb[{vb_number}]")
                
                if current_read_count >= next_gen_threshold_cnt:

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
                loop = random.randint(0,12) 
                D017_param = choose_D017_param(vb_number, loop, self.CE, self.PLANE_PER_DIE)
                
                project_api.issue_D017_to_create_SGM_fail(D017_param)

                is_bad_blk_before = check_vb_in_BBT(vb_number,None)

                logger.flow(10, 'Erase to trigger SGM')
                self.random_write_check_system_vb_erase(lun,case,vb_number)
               
                logger.flow(11, 'Send 4071 to check event cnt increase')
                data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
                event_cnt = data_4071.sgs_scan_event_cnt_SLC[rc_level].value
                if (rc_level == 0 and first_time == True):
                    compare_value(event_cnt,last_event_cnt,desc=f"sgs_scan_event_cnt_{rc_level}_SLC")
                elif flagged == False:
                    event_cnt = data_4071.sgs_scan_event_cnt_SLC[rc_level+1].value
                    compare_value(event_cnt, last_event_cnt, desc=f"sgs_scan_event_cnt_{rc_level+1}_SLC")
                else:
                    event_cnt = data_4071.sgs_scan_event_cnt_SLC[rc_level+1].value
                    compare_value(event_cnt, last_event_cnt + 1, desc=f"sgs_scan_event_cnt_{rc_level+1}_SLC")
                                 
                last_event_cnt = event_cnt

                logger.flow(12, 'Send 4071 to check flagged physical vb cnt / flagged physical vbNumb = 0 after trigger SGM')
                compare_value(data_4071.sgs_scan_flagged_physical_vb_cnt.value, 0,desc="sgs_scan_flagged_physical_vb_cnt")
                compare_value(data_4071.sgs_scan_flagged_physical_vbNumb[vb_number].value, 0, desc=f"sgs_scan_flagged_physical_vbNumb[{vb_number}]")

                logger.flow(13, f'Send VU 405E to check vb={vb_number} not in retirement bitmap')
                
                is_retirement_case = check_is_retirement_case(D017_param)
                logger.info(f'is retirement case = {is_retirement_case}')

                is_bad_blk = check_vb_in_BBT(vb_number, D017_param)
                if (rc_level == 0 and first_time == True) or (flagged == False):
                    if is_bad_blk == True and is_bad_blk_before == False:
                        logger.error(f'Expect vb={vb_number} not be retired, but not')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    if is_retirement_case == True:
                        logger.flow(2, f'Send VU 0x405E to check vb={vb_number} is in retirement bitmap')
                        if is_bad_blk == False:
                            logger.error(f'Expect vb={vb_number} be retired, but not')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    else:
                        if is_bad_blk == True and is_bad_blk_before == False:
                            logger.error(f'Expect vb={vb_number} not be retired, but not')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                if event_cnt == 1 and rc_level < 4:
                    logger.flow(2, f'Send VU C071 to adjust read count = {data_4071.sgs_read_count_threshold_list[rc_level].value} (RC_THRESHOLD_{rc_level})')
                    next_trigger_rc = data_4071.sgs_read_count_threshold_list[rc_level].value
                    rc_level += 1
                    param = project_api.C071_param()
                    param.sgs_scan_dynamic_read_count.value = data_4071.curr_read_count_TLC.value
                    param.sgs_scan_static_read_count.value = next_trigger_rc
                    param.sgs_scan_static_event_cnt[rc_level].value = last_event_cnt
                    project_api.issue_C071_to_set_SGD_scan_parameters(param)

                    logger.flow(2, 'Send VU 4071 to get SGS value')
                    data_4071 = project_api.issue_4071_to_get_SGD_scan_parameter(isSGS=1)
                    remain = data_4071.remain_read_count_trigger_sgs_SLC.value
                    current_read_count = data_4071.curr_read_count_SLC.value
                    next_trigger_rc = remain
                    next_gen_threshold_cnt = current_read_count + data_4071.sgs_scan_window_list[rc_level].value
                    logger.info(f'current rc({current_read_count}), next gen threshold cnt({next_gen_threshold_cnt}), gen new remain value = {remain}')
                    
                    last_event_cnt = 0

                stop_event_value = data_4071.sgs_scan_event_cnt_SLC[1].value

                first_time = False
            
        pass
    def get_current_open_vb(self, case:TestCases, open_vb_info:OpenVBInfo) -> tuple[PCA, int]:
        pca = PCA()
        if case == TestCases.SWAP:
            vb_number = open_vb_info.SWAP.logical_vb.value
            
        elif case == TestCases.PTE:
            vb_number = open_vb_info.PTE.logical_vb.value
            
        elif case == TestCases.LOG:
            vb_number = open_vb_info.LOG.logical_vb.value
            
        logger.info(f'vb number = {vb_number}')
        return (pca, vb_number)

    def random_write_check_system_vb_erase(self,lun:int,case:TestCases, vb_number:int) -> None:
        gc_trigger = False

        start_time = time.time()
        timeout_min = 120

        while(gc_trigger == False):
            if check_timeout(start_time, timeout_min):
                logger.error(f'Cannot create system vb GC in {timeout_min} min')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            total_write_len = api.WRITE_10_MAX_BLOCK_LEN
            startlba = random.randint(0, self._param.gLUCapacity[lun]-1-total_write_len)

            write_data(lun=lun,start_lba=startlba,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_write_len)
            gc_trigger = check_vb_in_specific_pool(vb_number,"FREE_BLK_QUEUE_TABLE")
            if gc_trigger == True:
                logger.info('vb number gc to free block')

        start_time = time.time()
        while(True):
            if check_timeout(start_time, timeout_min):
                logger.error(f'Cannot reuse system vb in {timeout_min} min')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            total_write_len = api.WRITE_10_MAX_BLOCK_LEN
            startlba = random.randint(0, self._param.gLUCapacity[lun]-1-total_write_len)

            write_data(lun=lun,start_lba=startlba,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_write_len)
            if not check_vb_in_specific_pool(vb_number,"FREE_BLK_QUEUE_TABLE"):
                logger.info('random write -> vb goto free table group -> write -> check vb not in free table queue')
                break
    pass
run = Pattern().run 
if __name__ == "__main__":
    run()