import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from typing import Dict, List, cast, Optional, Any
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.vendor_cmd.functions import *
from enum import Enum, IntEnum
from Script.project_api.functions import get_physical_layout, print_object_info_ai
import math
import time
from Script.api.ufs_api.defines import CmdParamPatternMode, CompareMethod
from Script.api.ufs_api import *
from time import sleep
def trigger_read_disturb(lun:int, lba:int) -> None:
    def read_LBA_repeatedly(lun:int, lba:int, read_times:int) -> None:
        for _ in range(read_times):
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=lun, lba=lba, length=1, fua=1)
            ExecuteCMD.enqueue(read10)
        ExecuteCMD.send(timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
        return
    _,pca = project_api.issue_4051_to_get_physical_address(lun, lba)
    read_cnt_of_vb_before = project_api.get_all_VB_read_count()
    vb = pca.virtual_block_number.value
    set_RC_TH_Value = read_cnt_of_vb_before[vb] + 1
    project_api.set_specific_VB_read_count_threshold(VB_Num=vb, RC_TH_Value=set_RC_TH_Value)
    times = random.randint(10,100)
    read_LBA_repeatedly(lun=lun, lba = lba, read_times=times)
    polling_bkops_idle()
    pass

def trigger_wear_leveling(fw_geometry:api.FwGeometry, debug_info:api.DebugInfo) -> None:
    _, erase_cnt_buffer_backup = api.read_Xmemory(sram_address=debug_info.VB_list_cycle_address.value)
    _, wear_leveling_A = project_api.issue_4098_to_get_wear_leveling_information()
    sorted_VB_list_dict = get_sorted_VB_list()
    gEC_for_Static_pool = 0
    gEC_for_dynamic_pool = 0
    gEC_for_static_ICS_pool = 0
    gEC_of_Static_pool_for_open = 0
    gEC_of_dynamic_pool_for_open = 0
    gEC_gap_delta_TH1_static = wear_leveling_A.EC_gap_delta_Threshold_TH1_of_static_pool.value
    gEC_gap_delta_TH1_dynamic = wear_leveling_A.EC_gap_delta_Threshold_TH1_of_dynamic_pool.value
    gEC_gap_delta_TH1_ICS = wear_leveling_A.EC_gap_delta_Threshold_TH1_of_ICS_pool.value
    gEC_gap_delta_TH2_static = wear_leveling_A.EC_gap_delta_Threshold_TH2_of_static_pool.value
    gEC_gap_delta_TH2_dynamic = wear_leveling_A.EC_gap_delta_Threshold_TH2_of_dynamic_pool.value
    gEC_gap_delta_TH2_ICS = wear_leveling_A.EC_gap_delta_Threshold_TH2_of_ICS_pool.value
    set_erase_cnt_payload = copy.deepcopy(erase_cnt_buffer_backup)[0:api.DATA_SIZE_4K_BYTE]
    set_version_dict:Dict[int, int] = {}
    for vb in range(fw_geometry.l52_total_vb_count):
        set_version_dict[vb] = 0
    for type in [project_api.VBListNum.CURRENT_L2_TLC, project_api.VBListNum.CURRENT_L2_EM1, project_api.VBListNum.PTE_POOL]:
        if type in sorted_VB_list_dict:
            break

    target_vb = sorted_VB_list_dict[type][0]
    if type == project_api.VBListNum.CURRENT_L2_TLC:
        gEC_of_dynamic_pool_for_open = wear_leveling_A.EC_Threshold_of_dynamic_pool.value + 1
        target_free_vb = sorted_VB_list_dict[project_api.VBListNum.FREE_BLK_QUEUE_TLC][0]
        set_ec = wear_leveling_A.EC_gap_delta_Threshold_TH1_of_dynamic_pool.value + 1
        set_version = wear_leveling_A.globalVersion_of_dynamic_pool.value+1
    elif type == project_api.VBListNum.CURRENT_L2_EM1:
        gEC_of_Static_pool_for_open = wear_leveling_A.EC_Threshold_of_static_pool.value + 1
        target_free_vb = sorted_VB_list_dict[project_api.VBListNum.FREE_BLK_QUEUE_EM1][0]
        set_ec = wear_leveling_A.EC_gap_delta_Threshold_TH1_of_static_pool.value + 1  
        set_version = wear_leveling_A.globalVersion_of_static_pool.value+1
    elif type == project_api.VBListNum.PTE_POOL:
        gEC_for_static_ICS_pool = wear_leveling_A.EC_Threshold_of_ICS_pool.value + 1
        target_free_vb = sorted_VB_list_dict[project_api.VBListNum.FREE_BLK_QUEUE_TABLE][0]
        set_ec = wear_leveling_A.EC_gap_delta_Threshold_TH1_of_ICS_pool.value + 1
        set_version = 0
    set_erase_cnt_payload[target_vb * 4 : (target_vb+1)*4] = (0).to_bytes(4, 'little')
    set_erase_cnt_payload[target_free_vb * 4 : (target_free_vb+1)*4] = (set_ec).to_bytes(4, 'little')
    set_version_dict[target_vb] = set_version
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
    polling_bkops_idle()
    project_api.set_all_VB_erase_count(data_payload=erase_cnt_buffer_backup, set_in_ram=False)
    pass
def trigger_read_scan_UECC(lun:int, lba:int, SLC_enable:bool) -> None:
    pca = get_PCA_and_print(lun=lun, lba=lba)
    inject_UECC(pca=pca, SLC_enable=SLC_enable)
    read10 = ExecuteCMD.Read10()
    read10.assign(lun=lun, lba=lba, length=1, fua=1)
    ExecuteCMD.enqueue(read10)
    ExecuteCMD.send(timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
    polling_bkops_idle()
    pass

def leave_inhibition_mode() -> None:
    enablelun = 0
    for lunidx in range(0, shared.param.gMaxNumberLU):
        if shared.param.gUnit[lunidx].b3_lu_enable:
            enablelun = lunidx
            break
    for _ in range(1000+1):
        read10 = ExecuteCMD.Read10()
        read10.assign(lun=enablelun, lba=0, length=1, fua=1)
        ExecuteCMD.enqueue(read10)
    ExecuteCMD.send(timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
    pass

def trigger_refresh() -> None:
    sorted_vb_dict = get_sorted_VB_list()
    vb_list = []
    vb_list += [vb for vb in sorted_vb_dict.get(project_api.VBListNum.CURRENT_L2_TLC, [])]
    vb_list += [vb for vb in sorted_vb_dict.get(project_api.VBListNum.CURRENT_L2_EM1, [])]
    vb_list += [vb for vb in sorted_vb_dict.get(project_api.VBListNum.CURRENT_L1, [])]
    vb_list = vb_list[:5]
    project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.MediumPriority)
    polling_bkops_idle()
    pass

    

# bfea section
def check_timeout(start_time: float, timeout_min: int, timeout_sec:int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60 + timeout_sec:
        return True
    else:
        return False

def write_data(lun:int, start_lba:int, total_size: int, chunk_size:int) -> None:
    chunk_size = 65535
    lba = start_lba
    total_len = total_size
    while(total_len):
        write10 = ExecuteCMD.Write10()
        chunk_size = min(int(chunk_size),int(total_len))
        write10.assign(lun=lun, lba=lba, length=chunk_size, fua=0)
        write10.set_option(pattern_mode=CmdParamPatternMode.HW_FIX)
        ExecuteCMD.enqueue(write10)
        total_len -= chunk_size     
        lba += chunk_size
    ExecuteCMD.send(clear_on_success=True)

def polling_bfea_idle()-> None:
    timeout_min = 0
    timeout_sec = 2000
    start_time = time.time()   
    logger.info(f'polling_bfea_idle')  
    while True:
        if check_timeout(start_time, timeout_min, timeout_sec):
            raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
        payload = project_api.issue_40B0_Bfea_Scan(5,0,0,0)
        output = int.from_bytes(payload[0:4], byteorder='little')      
        if output != 1:
            logger.info(f'output = {output}, continue polling')
            time.sleep(1)
        else:
            logger.info(f'output = {output}, already idle')
            break  

def set_bfea_scan_make_offset_all_128()->None:
    # logger.info('Issue 40B1 VUC to get best BFEA bin')
    # logger.info(f'test_vb = {test_vb}, test_ce = {test_ce}')
    for setting_N in range(15, -1, -1):
        logger.info(f'set bin {setting_N} offset to 128')
        for setting_EC_Interval in range(1,5):
            setting_SLC_L1 = 128
            setting_MLC_L1 = 128
            setting_MLC_L2 = 128
            setting_MLC_L3 = 128
            setting_TLC_L1 = 128
            setting_TLC_L2 = 128
            setting_TLC_L3 = 128
            setting_TLC_L4 = 128
            setting_TLC_L5 = 128
            setting_TLC_L6 = 128
            setting_TLC_L7 = 128                     
            project_api.issue_D04A_Set_Bin_Offset(setting_N, setting_EC_Interval, setting_SLC_L1, setting_MLC_L1, setting_MLC_L2, setting_MLC_L3, setting_TLC_L1, setting_TLC_L2, setting_TLC_L3, setting_TLC_L4, setting_TLC_L5, setting_TLC_L6, setting_TLC_L7)
def trigger_bfea_refresh_and_check_if_trigger(tlc_vb_size:int, ce_num:int) -> bool:
    project_api.issue_D088_enable_disable_auto_standby(0)    
    logger.flow(1,f'4056 get mconfig data')
    _, mConfig_in_vu = project_api.get_mConfig_data()
    FB_SCAN_WL_MIN = mConfig_in_vu.FB_SCAN_WL_MIN.value
    PB_SCAN_PAGE = mConfig_in_vu.PB_SCAN_PAGE.value
    FB_SCAN_WL_MAX = mConfig_in_vu.FB_SCAN_WL_MAX.value
    PB_SCAN_ENABLE_PAGE_GAP = mConfig_in_vu.PB_SCAN_ENABLE_PAGE_GAP.value
    logger.info(f'FB_SCAN_WL_MIN = {FB_SCAN_WL_MIN}, PB_SCAN_PAGE = {PB_SCAN_PAGE}, FB_SCAN_WL_MAX = {FB_SCAN_WL_MAX}, PB_SCAN_ENABLE_PAGE_GAP = {PB_SCAN_ENABLE_PAGE_GAP}')
    write_data_size4k = (PB_SCAN_PAGE + PB_SCAN_ENABLE_PAGE_GAP) *  6 * ce_num * 4
    logger.flow(3,f'write {write_data_size4k} 4k')
    write_data(0, 0, write_data_size4k, 65535)    
    backup_bin_404A = project_api.issue_404A_Get_Bfea_Bin_Offset()
    set_bfea_scan_make_offset_all_128()   

    pca = api.lba_to_pba(0, 0)
    vb = pca.w10_block.value
    ce = pca.b5_ce.value
    test_vb = vb
    test_ce = ce  
    logger.flow(5,'backup trigger count')
    bu_bfea_regular_scan_group_trig_count_0 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_trig_count[0]'))
    bu_bfea_regular_scan_group_done_count_0 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_done_count[0]'))
    bu_bfea_regular_scan_group_trig_count_1 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_trig_count[1]'))
    bu_bfea_regular_scan_group_done_count_1 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_done_count[1]'))
    bu_bfea_regular_scan_group_trig_count_2 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_trig_count[2]'))
    bu_bfea_regular_scan_group_done_count_2 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_done_count[2]'))
    logger.info(f'bfea_regular_scan_group_trig_count_0 = {bu_bfea_regular_scan_group_trig_count_0}')               
    logger.info(f'bfea_regular_scan_group_trig_count_1 = {bu_bfea_regular_scan_group_trig_count_1}')               
    logger.info(f'bfea_regular_scan_group_trig_count_2 = {bu_bfea_regular_scan_group_trig_count_2}')               
    logger.info(f'bfea_regular_scan_group_done_count_0 = {bu_bfea_regular_scan_group_done_count_0}')               
    logger.info(f'bfea_regular_scan_group_done_count_1 = {bu_bfea_regular_scan_group_done_count_1}')               
    logger.info(f'bfea_regular_scan_group_done_count_2 = {bu_bfea_regular_scan_group_done_count_2}')      
    logger.flow(6,'Issue 40B0 bfea scan')
    min_bin = 0xFFFFFFFF
    for ce in range(ce_num):
        logger.info(f'40B0 option = 3, vb = {test_vb}, ce = {ce}')
        payload = project_api.issue_40B0_Bfea_Scan(3, test_vb, ce, 0)
        output = int.from_bytes(payload[0:4], byteorder='little')  
        logger.info(f'result = {output}')
        if min_bin > output:
            min_bin = output
    min_bin_val = min_bin  
    logger.flow(7,f'Get min bin from vb {test_vb} from all ce = {min_bin_val}')
    setting_timer_minutes = 1
    if min_bin_val <= 1:
        grp = 0
    elif min_bin_val <= 8:
        grp = 1
    elif min_bin_val <= 15:
        grp = 2
    grp = grp            
    logger.info(f'grp = {grp}')
    time_gap_min = 20
    logger.info(f'40B0 opcode = 9, grp = {grp}, timer minute = {time_gap_min - setting_timer_minutes}')
    project_api.issue_40B0_Bfea_Scan(9, grp, (20  - setting_timer_minutes) * 60, 0) # will be 20 * 60 - 1*60 = 19 * 60 (sec)         
    logger.flow(9,f'idle {setting_timer_minutes} min')
    sleep(setting_timer_minutes * 60)

    polling_bfea_idle()
    #cur_bfea_change_bin_ce_blk_cnt = read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_change_bin_ce_blk_cnt')
    cur_bfea_regular_scan_group_trig_count_0 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_trig_count[0]'))
    cur_bfea_regular_scan_group_done_count_0 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_done_count[0]'))
    cur_bfea_regular_scan_group_trig_count_1 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_trig_count[1]'))
    cur_bfea_regular_scan_group_done_count_1 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_done_count[1]'))
    cur_bfea_regular_scan_group_trig_count_2 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_trig_count[2]'))
    cur_bfea_regular_scan_group_done_count_2 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_done_count[2]'))     
    logger.info(f'bfea_regular_scan_group_trig_count_0 = {cur_bfea_regular_scan_group_trig_count_0}')               
    logger.info(f'bfea_regular_scan_group_trig_count_1 = {cur_bfea_regular_scan_group_trig_count_1}')               
    logger.info(f'bfea_regular_scan_group_trig_count_2 = {cur_bfea_regular_scan_group_trig_count_2}')               
    logger.info(f'bfea_regular_scan_group_done_count_0 = {cur_bfea_regular_scan_group_done_count_0}')               
    logger.info(f'bfea_regular_scan_group_done_count_1 = {cur_bfea_regular_scan_group_done_count_1}')               
    logger.info(f'bfea_regular_scan_group_done_count_2 = {cur_bfea_regular_scan_group_done_count_2}') 
    logger.info(f'grp = {grp}, min_bin_val = {min_bin_val}')   

    if grp == 0:
        if(int(cur_bfea_regular_scan_group_trig_count_0) != (int(bu_bfea_regular_scan_group_trig_count_0) + 1)):
            logger.error_fp(f'cur_bfea_regular_scan_group_trig_count_0 = {cur_bfea_regular_scan_group_trig_count_0} != bu_bfea_regular_scan_group_trig_count_0({bu_bfea_regular_scan_group_trig_count_0}) + 1 ')

        if(int(cur_bfea_regular_scan_group_done_count_0) != (int(bu_bfea_regular_scan_group_done_count_0) + 1)):
            logger.error_fp(f'cur_bfea_regular_scan_group_done_count_0 = {cur_bfea_regular_scan_group_done_count_0} != bu_bfea_regular_scan_group_done_count_0({bu_bfea_regular_scan_group_done_count_0}) + 1 ')
                    
    if grp == 1:
        if(int(cur_bfea_regular_scan_group_trig_count_1) != (int(bu_bfea_regular_scan_group_trig_count_1) + 1)):
            logger.error_fp(f'cur_bfea_regular_scan_group_trig_count_1 = {cur_bfea_regular_scan_group_trig_count_1} != bu_bfea_regular_scan_group_trig_count_1({bu_bfea_regular_scan_group_trig_count_1}) + 1 ')
  
        if(int(cur_bfea_regular_scan_group_done_count_1) != (int(bu_bfea_regular_scan_group_done_count_1) + 1)):
            logger.error_fp(f'cur_bfea_regular_scan_group_done_count_1 = {cur_bfea_regular_scan_group_done_count_1} != bu_bfea_regular_scan_group_done_count_0({bu_bfea_regular_scan_group_done_count_1}) + 1 ')            
    if grp == 2:
        if(int(cur_bfea_regular_scan_group_trig_count_2) != (int(bu_bfea_regular_scan_group_trig_count_2) + 1)):
            logger.error_fp(f'cur_bfea_regular_scan_group_trig_count_2 = {cur_bfea_regular_scan_group_trig_count_2} != bu_bfea_regular_scan_group_trig_count_1({bu_bfea_regular_scan_group_trig_count_2}) + 1 ')
 
        if(int(cur_bfea_regular_scan_group_done_count_2) != (int(bu_bfea_regular_scan_group_done_count_2) + 1)):
            logger.error_fp(f'cur_bfea_regular_scan_group_done_count_2 = {cur_bfea_regular_scan_group_done_count_2} != bu_bfea_regular_scan_group_done_count_0({bu_bfea_regular_scan_group_done_count_2}) + 1 ')

    rsp, bookingQ = project_api.issue_40C5_to_get_booking_queue()
    output = int.from_bytes(bookingQ.payload[12:16], byteorder='little')  
    logger.info(f'output = {output}')
    expect_val = 0
    bit_position = 18
    mask = 1 << bit_position
    bfea_booking = (output & mask) >> bit_position
    expect_val = 18
    logger.info(f'bfea_booking({bfea_booking})')
    result = True
    if bfea_booking != expect_val:
        logger.info(f'bfea_booking({bfea_booking}) != expect_val ({expect_val})')
        result = False
    else:
        logger.info(f'bfea_booking({bfea_booking}) = expect_val ({expect_val})')
        result = True
    for backup_N in range(16):
        logger.info(f'set bin {backup_N} offset recover')        
        for setting_EC_Interval in range(1,5):
            setting_SLC_L1 = backup_bin_404A.payload[backup_N*11]
            setting_MLC_L1 = backup_bin_404A.payload[backup_N*11 + 1]
            setting_MLC_L2 = backup_bin_404A.payload[backup_N*11 + 2]
            setting_MLC_L3 = backup_bin_404A.payload[backup_N*11 + 3]
            setting_TLC_L1 = backup_bin_404A.payload[backup_N*11 + 4]
            setting_TLC_L2 = backup_bin_404A.payload[backup_N*11 + 5]
            setting_TLC_L3 = backup_bin_404A.payload[backup_N*11 + 6]
            setting_TLC_L4 = backup_bin_404A.payload[backup_N*11 + 7]
            setting_TLC_L5 = backup_bin_404A.payload[backup_N*11 + 8]
            setting_TLC_L6 = backup_bin_404A.payload[backup_N*11 + 9]
            setting_TLC_L7 = backup_bin_404A.payload[backup_N*11 + 10]
            project_api.issue_D04A_Set_Bin_Offset(backup_N, setting_EC_Interval , setting_SLC_L1, setting_MLC_L1, setting_MLC_L2, setting_MLC_L3, setting_TLC_L1, setting_TLC_L2, setting_TLC_L3, setting_TLC_L4, setting_TLC_L5, setting_TLC_L6, setting_TLC_L7)       


    return result  



def trigger_bfea_and_check_if_trigger(tlc_vb_size:int, ce_num:int) -> bool:
    project_api.issue_D088_enable_disable_auto_standby(0)    
    logger.flow(3,'write 3 TLC VB')
    write_data(0, 0, 3*tlc_vb_size, 65535)
    logger.flow(4,'Host issue L2P with written range to get CE/VB')
    pca = api.lba_to_pba(0, 0)
    vb = pca.w10_block.value
    ce = pca.b5_ce.value
    test_vb = vb
    test_ce = ce      
    logger.flow(5,'backup trigger count')
    bu_bfea_regular_scan_group_trig_count_0 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_trig_count[0]'))
    bu_bfea_regular_scan_group_done_count_0 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_done_count[0]'))
    bu_bfea_regular_scan_group_trig_count_1 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_trig_count[1]'))
    bu_bfea_regular_scan_group_done_count_1 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_done_count[1]'))
    bu_bfea_regular_scan_group_trig_count_2 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_trig_count[2]'))
    bu_bfea_regular_scan_group_done_count_2 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_done_count[2]'))
    logger.info(f'bfea_regular_scan_group_trig_count_0 = {bu_bfea_regular_scan_group_trig_count_0}')               
    logger.info(f'bfea_regular_scan_group_trig_count_1 = {bu_bfea_regular_scan_group_trig_count_1}')               
    logger.info(f'bfea_regular_scan_group_trig_count_2 = {bu_bfea_regular_scan_group_trig_count_2}')               
    logger.info(f'bfea_regular_scan_group_done_count_0 = {bu_bfea_regular_scan_group_done_count_0}')               
    logger.info(f'bfea_regular_scan_group_done_count_1 = {bu_bfea_regular_scan_group_done_count_1}')               
    logger.info(f'bfea_regular_scan_group_done_count_2 = {bu_bfea_regular_scan_group_done_count_2}')  
    logger.flow(6,'Issue 40B0 bfea scan')
    min_bin = 0xFFFFFFFF
    for ce in range(ce_num):
        logger.info(f'40B0 option = 3, vb = {test_vb}, ce = {test_ce}')
        payload = project_api.issue_40B0_Bfea_Scan(3, test_vb, ce, 0)
        output = int.from_bytes(payload[0:4], byteorder='little')  
        logger.info(f'result = {output}')
        if min_bin > output:
            min_bin = output
    min_bin_val = min_bin  
    logger.flow(7,f'Get min bin from vb {test_vb} from all ce = {min_bin_val}')   
    logger.flow(8,'Issue 40B0 VUC to BFEA Scan to set timer')
    setting_timer_minutes = 1
    if min_bin_val <= 1:
        grp = 0
    elif min_bin_val <= 8:
        grp = 1
    elif min_bin_val <= 15:
        grp = 2
    grp = grp            
    logger.info(f'grp = {grp}')
    time_gap_min = 20
    logger.info(f'40B0 opcode = 9, grp = {grp}, timer minute = {time_gap_min - setting_timer_minutes}')
    project_api.issue_40B0_Bfea_Scan(9, grp, (20  - setting_timer_minutes) * 60, 0) # will be 20 * 60 - 1*60 = 19 * 60 (sec)       
    logger.flow(9,f'idle {setting_timer_minutes} min')
    sleep(setting_timer_minutes * 60)
    polling_bfea_idle()
    #cur_bfea_change_bin_ce_blk_cnt = read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_change_bin_ce_blk_cnt')
    cur_bfea_regular_scan_group_trig_count_0 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_trig_count[0]'))
    cur_bfea_regular_scan_group_done_count_0 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_done_count[0]'))
    cur_bfea_regular_scan_group_trig_count_1 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_trig_count[1]'))
    cur_bfea_regular_scan_group_done_count_1 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_done_count[1]'))
    cur_bfea_regular_scan_group_trig_count_2 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_trig_count[2]'))
    cur_bfea_regular_scan_group_done_count_2 = cast(int,read_fw_value('gUfsApiStruct.ftl->split_info->smart_info_2.bfea_regular_scan_group_done_count[2]'))     
    logger.info(f'bfea_regular_scan_group_trig_count_0 = {cur_bfea_regular_scan_group_trig_count_0}')               
    logger.info(f'bfea_regular_scan_group_trig_count_1 = {cur_bfea_regular_scan_group_trig_count_1}')               
    logger.info(f'bfea_regular_scan_group_trig_count_2 = {cur_bfea_regular_scan_group_trig_count_2}')               
    logger.info(f'bfea_regular_scan_group_done_count_0 = {cur_bfea_regular_scan_group_done_count_0}')               
    logger.info(f'bfea_regular_scan_group_done_count_1 = {cur_bfea_regular_scan_group_done_count_1}')               
    logger.info(f'bfea_regular_scan_group_done_count_2 = {cur_bfea_regular_scan_group_done_count_2}') 
    if grp == 0:
        if(int(cur_bfea_regular_scan_group_trig_count_0) != (int(bu_bfea_regular_scan_group_trig_count_0) + 1)):
            logger.error_fp(f'cur_bfea_regular_scan_group_trig_count_0 = {cur_bfea_regular_scan_group_trig_count_0} != bu_bfea_regular_scan_group_trig_count_0({bu_bfea_regular_scan_group_trig_count_0}) + 1 ')
            return False  
        if(int(cur_bfea_regular_scan_group_done_count_0) != (int(bu_bfea_regular_scan_group_done_count_0) + 1)):
            logger.error_fp(f'cur_bfea_regular_scan_group_done_count_0 = {cur_bfea_regular_scan_group_done_count_0} != bu_bfea_regular_scan_group_done_count_0({bu_bfea_regular_scan_group_done_count_0}) + 1 ')
            return False             
    if grp == 1:
        if(int(cur_bfea_regular_scan_group_trig_count_1) != (int(bu_bfea_regular_scan_group_trig_count_1) + 1)):
            logger.error_fp(f'cur_bfea_regular_scan_group_trig_count_1 = {cur_bfea_regular_scan_group_trig_count_1} != bu_bfea_regular_scan_group_trig_count_1({bu_bfea_regular_scan_group_trig_count_1}) + 1 ')
            return False  
        if(int(cur_bfea_regular_scan_group_done_count_1) != (int(bu_bfea_regular_scan_group_done_count_1) + 1)):
            logger.error_fp(f'cur_bfea_regular_scan_group_done_count_1 = {cur_bfea_regular_scan_group_done_count_1} != bu_bfea_regular_scan_group_done_count_0({bu_bfea_regular_scan_group_done_count_1}) + 1 ')
            return False                  
    if grp == 2:
        if(int(cur_bfea_regular_scan_group_trig_count_2) != (int(bu_bfea_regular_scan_group_trig_count_2) + 1)):
            logger.error_fp(f'cur_bfea_regular_scan_group_trig_count_2 = {cur_bfea_regular_scan_group_trig_count_2} != bu_bfea_regular_scan_group_trig_count_1({bu_bfea_regular_scan_group_trig_count_2}) + 1 ')
            return False   
        if(int(cur_bfea_regular_scan_group_done_count_2) != (int(bu_bfea_regular_scan_group_done_count_2) + 1)):
            logger.error_fp(f'cur_bfea_regular_scan_group_done_count_2 = {cur_bfea_regular_scan_group_done_count_2} != bu_bfea_regular_scan_group_done_count_0({bu_bfea_regular_scan_group_done_count_2}) + 1 ')
            return False   
    return True  


# def trigger_urgent_GC(lun:int) -> None:
#     slc_threshold, tlc_threshold = api.get_gc_threshold()
#     logger.info(f'tlc threshold = {tlc_threshold}')
#     logger.flow(56-2, 'Disable bkops')
#     project_api.issue_D0FD_en_disable_BKOPS(bValue=2)
#     project_api.issue_D0FD_en_disable_BKOPS(bValue=0)
#     logger.flow("57-2", 'Write until tlc gc threshold')
#     write_until_threshold(lun,'USED_BLK_POOL_MLC', tlc_threshold, loop=loop)
#     project_api.issue_D0FD_en_disable_BKOPS(bValue=3)
#     project_api.issue_D0FD_en_disable_BKOPS(bValue=1)
    
#     pca = get_PCA_and_print(lun=lun, lba=lba)
#     inject_UECC(pca=pca, SLC_enable=SLC_enable)
#     read10 = ExecuteCMD.Read10()
#     read10.assign(lun=lun, lba=lba, length=1, fua=1)
#     ExecuteCMD.enqueue(read10)
#     ExecuteCMD.send(timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))


def check_if_read_disturb_triggered(health_report_before:project_api.ReadEnhanceHealthReport) -> bool:
    response, health_report = project_api.issue_40FE_to_read_enhanced_health_report()
    print_struct_different(health_report_before, health_report)
    total_modify = 0
    total_modify += get_struct_value_difference(health_report_before, health_report, 'read_disturb_refresh_start_count_em1')
    total_modify += get_struct_value_difference(health_report_before, health_report, 'read_disturb_refresh_start_count_normal_tlc')
    total_modify += get_struct_value_difference(health_report_before, health_report, 'read_disturb_refresh_start_count_normal_slc')
    total_modify += get_struct_value_difference(health_report_before, health_report, 'read_disturb_refresh_start_count_table')
    return total_modify > 0

def check_if_wear_leveling_triggered(wear_leveling_before:project_api.WearLevelingInformation) -> bool:
    _, wear_leveling_after = project_api.issue_4098_to_get_wear_leveling_information()
    print_struct_different(wear_leveling_before, wear_leveling_after)
    total_modify = 0
    total_modify += get_struct_value_difference(wear_leveling_before, wear_leveling_after, 'totalSWLTriggerCount_of_ICS_pool')
    total_modify += get_struct_value_difference(wear_leveling_before, wear_leveling_after, 'totalSWLTriggerCount_of_static_pool')
    total_modify += get_struct_value_difference(wear_leveling_before, wear_leveling_after, 'totalSWLTriggerCount_of_dynamic_pool')
    return total_modify > 0

def check_if_read_scan_UECC_triggered(bbt_list_before:List[tuple[project_api.PBA_format, project_api.BB_retirement_reason]]) -> bool:
    bbt_list_after = get_bbt_list()
    A_set = {
        (bytes(a.payload.copy()), bytes(b.payload.copy()))
        for a, b in bbt_list_before
    }

    delta = [
        (x, y)
        for x, y in bbt_list_after
        if (bytes(x.payload.copy()), bytes(y.payload.copy())) not in A_set
    ]

    for pba, retirement_reason in delta:
        if retirement_reason.Type.value == project_api.BBRetirementReaspnType.READ_SCAN_UECC:
            return True
    return False

def get_read_back_node() -> int:
    return int(cast(int, api.read_fw_value('gUfsApiStruct.ftl->split_info->data_gc.target.rb_verify.current.node')))

def check_if_Read_Back_triggered(before_node:int) -> bool:
    current_node = get_read_back_node()
    return current_node > before_node



def config_lun(normal_list:List[int] = [], em1_list:List[int] = []) -> None:
    selector = 0x00
    length = 0xE6
    Total_AU_Count = shared.param.gGeometry.q4_total_raw_device_capacity // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
    EM1_total_AU = min(shared.param.gGeometry.l44_enhanced1_max_n_alloc_u, Total_AU_Count//(len(normal_list) + len(em1_list)) * len(em1_list))
    normal_total_AU = Total_AU_Count//(len(normal_list) + len(em1_list)) * len(normal_list)
    for index in range(4):
        cmd = ExecuteCMD.WriteDescriptor()
        cmd.assign(api.DescriptorIDN.CONFIGURATION, index, selector, length)

        desc = api.ConfigDescriptor310()
        desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
        desc.header.b3_boot_enable = api.BootEnable.BOOT_DISABLE
        desc.header.b4_descr_access_en = api.DescrAccessEn.DISABLE
        desc.header.b5_init_power_mode = api.InitPowerMode.ACTIVE
        desc.header.b6_high_priority_lun = api.HighPriorityLUN.ALL_LUN_SAME_PRIORITY
        desc.header.b7_secure_removal_type = api.SecureRemovalType.BY_PHYSICAL_ERASE
        desc.header.b8_init_active_icc_level = api.InitActiveICCLevel.LVL_00
        desc.header.w9_periodic_rtc_update = 0
        desc.header.b11_hpb_control = 0
        desc.header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE
        desc.header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.DISABLE
        desc.header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
        desc.header.l18_num_shared_write_booster_buffer_alloc_units = shared.param.gGeometry.l79_write_booster_buffer_max_n_alloc_units if index==0 else 0

        
        for unit_idx in range(8):
            lun = index * 8 + unit_idx
            if lun in normal_list:
                desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                desc.units[unit_idx].b3_memory_type = api.MemoryType.NORMAL
                desc.units[unit_idx].l4_num_alloc_units = (normal_total_AU) // len(normal_list)
                desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
            elif lun in em1_list:
                desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                desc.units[unit_idx].l4_num_alloc_units = (EM1_total_AU) // len(em1_list)
                desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
            else:
                desc.units[unit_idx].b0_lu_enable = api.LUNEnable.DISABLE
                desc.units[unit_idx].l4_num_alloc_units = 0
                desc.units[unit_idx].b9_logical_block_size = 0

        cmd.set_desc(desc)
        ExecuteCMD.enqueue(cmd)
        ExecuteCMD.send()
    unit_desc_idxes:List[int] = []
    for lun in range(0, shared.param.gMaxNumberLU):
        unit_descriptor = ExecuteCMD.ReadDescriptor()
        unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
        unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

    ExecuteCMD.send(clear_on_success=False)
    for index in unit_desc_idxes:
        api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
    ExecuteCMD.clear()

    for lun in range(shared.param.gMaxNumberLU):
        if shared.param.gUnit[lun].b3_lu_enable:
            test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
            test_unit_ready.set_option(lun)
            ExecuteCMD.enqueue(test_unit_ready)
    ExecuteCMD.send()
    return

def get_sorted_VB_list() -> Dict[project_api.VBListNum, List[int]]:
    resp = project_api.custom_vu.issue_406D_get_VB_list_info()
    sorted_VB_list_dict:Dict[project_api.VBListNum, List[int]] = {}
    offset = 0
    VB_list = 0
    while offset < len(resp.data):
        vb_count = int.from_bytes(resp.data[offset:offset+2], byteorder='little')
        offset +=2
        for i in range(vb_count):
            vb = int.from_bytes(resp.data[offset:offset+2], byteorder='little')
            if project_api.VBListNum(VB_list) not in sorted_VB_list_dict:
                sorted_VB_list_dict[project_api.VBListNum(VB_list)] = []
            sorted_VB_list_dict[project_api.VBListNum(VB_list)].append(vb)
            offset +=2
        VB_list+=1
    return sorted_VB_list_dict

def polling_bkops_idle() -> None:
    while 1:
        bkops_status = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
        if bkops_status == 0:
            break
        time.sleep(1)
        
def print_struct_different(before_value: Any, after_value: Any) -> None:
    raw_fields = [
        (name, field) for name, field in before_value.__dict__.items()
        if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
    ]
    raw_fields.sort(key=lambda kv: kv[1].start_offset)
    expect_fields = [
        (name, field) for name, field in after_value.__dict__.items()
        if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
    ]
    expect_fields.sort(key=lambda kv: kv[1].start_offset)
    
    for (name0, raw), (name1, expect) in zip(
                                raw_fields,
                                expect_fields,
                            ):
        if hasattr(raw, "value") and hasattr(expect, "value") and name0 == name1:
            if raw.value != expect.value:
                logger.info(f'{name0}: {raw.value} (0x{raw.value:X}) -> {expect.value} (0x{expect.value:X})')
        pass
    
def get_struct_value_difference(before: Any, after: Any, string:str) -> int:
    value = None
    value_before = None
    for name, field in before.__dict__.items():
        if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value"):
            if name == string:
                value_before = field.value
                break
    for name, field in after.__dict__.items():
        if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value"):
            if name == string:
                value = field.value
    if value is None or value_before is None:
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION
    return int(value - value_before)

def get_bbt_list() -> List[tuple[project_api.PBA_format, project_api.BB_retirement_reason]]:
    bb_list : List[tuple[project_api.PBA_format, project_api.BB_retirement_reason]] = []
    _, VU_DATA = project_api.issue_405E_to_get_bad_block_information()
    total_BB_count = int.from_bytes(VU_DATA[0:4], 'little')
    start = 4
    for idx in range(total_BB_count):
        pba = project_api.PBA_format(VU_DATA[start + 4 + idx*8 : start + 4 + idx*8 +4])
        BB_retirement_reason = project_api.BB_retirement_reason(VU_DATA[start + idx*8 : start + idx*8 +4])
        BlkType = project_api.BBRetirementReaspnBlkType(BB_retirement_reason.BlkType.value)
        Type = project_api.BBRetirementReaspnType(BB_retirement_reason.Type.value)
        logger.info(f'idx = {idx},PBA: Blocl = {pba.blockNum.value}, CePlane = {pba.CePlane.value}; BB_retirement_reason: BlkType = {BlkType} ({BlkType.name}), Type = {Type} ({Type.name})')
        bb_list.append((pba, BB_retirement_reason))
    return bb_list

def get_PCA_and_print(lun: int, lba: int) -> project_api.physical_address_info:
    max_plane = 6
    _, pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=lba)
    vb = pca.virtual_block_number.value
    Die = pca.die.value
    Plane = pca.plane.value
    Block = pca.physical_block_number_w_BBT.value
    Page = pca.page.value
    _, BB_info = project_api.issue_40C7_to_get_bad_block_info(Block, Die*max_plane+Plane)
    if BB_info.replaced_physical_block.value != 0xFFFFFFFF:
        RemapPB = BB_info.replaced_physical_block.value
    else:
        RemapPB = Block
    logger.info(f'Lun{lun}, LBA = {lba}: VB = {vb}, PhyBlock = {Block}, RemapPB = {RemapPB}, CE = {Die}, Plane = {Plane}, Page = {Page}')
    out_pca = copy.deepcopy(pca)
    out_pca.physical_block_number_w_BBT.value = RemapPB
    return out_pca

def inject_UECC(pca:project_api.physical_address_info, SLC_enable:bool) -> None:
    vb = pca.virtual_block_number.value
    Die = pca.die.value
    Plane = pca.plane.value
    Block = pca.physical_block_number_w_BBT.value
    Page = pca.page.value
    _, WL_type, phy_WL, SubBlock, FlushGroup, TwoWLGroup, RainGoup = get_physical_layout(pageline=Page, block_type="SLC" if SLC_enable else "TLC")
    for p in range(Page - 1, -1, -1):
        _, temp_WL_type, _, temp_SB, _, _, _ = get_physical_layout(pageline=p, block_type="SLC" if SLC_enable else "TLC")
        if temp_SB < 0 or temp_SB != SubBlock:
            break
        Page = p
        WL_type = temp_WL_type

    logger.info(f'Inject UECC: PhyBlock = {Block}, CE = {Die}, Plane = {Plane}, Page = {Page} (WL_type={WL_type}), SLC_enable = {SLC_enable}')
    if SLC_enable:
        dire_write_payload = bytearray(DATA_SIZE_16K_BYTE)
    else:
        dire_write_payload = bytearray(DATA_SIZE_20K_BYTE*3)
    for i in range(len(dire_write_payload)):
        dire_write_payload[i] = 0xAA
    _ = project_api.issue_C060_to_write_raw_data(Ce=Die,Block=Block,Plane=Plane, Page=Page,SLC_Enable=SLC_enable,Ecc_Enable=1, datapayload=dire_write_payload)
    return

