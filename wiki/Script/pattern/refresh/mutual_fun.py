import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from typing import Dict, List, cast, Optional
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.vendor_cmd.functions import *
from enum import Enum, IntEnum
import time
from Script.project_api.functions import print_object_info_ai

    
    
    
    
def get_VB_group(show:bool = False) -> Dict[int, Dict[str, int]]:
    fw_geometry = api.get_fw_geometry()
    vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'access_mode': {'pos': 6, 'len': 2, 'mask': 0x3}, 
            'dirty': {'pos': 8, 'len': 1, 'mask': 0x1}, 
            'partition': {'pos': 9, 'len': 2, 'mask': 0x3}, 
            'cursor_idx': {'pos': 11, 'len': 1, 'mask': 0x1}, 
            'pte_tbl_mark': {'pos': 12, 'len': 1, 'mask': 0x1}, 
            'host_w_mark': {'pos': 13, 'len': 2, 'mask': 0x3}, 
            'src_uecc': {'pos': 15, 'len': 1, 'mask': 0x1}, 
            'vb_trim': {'pos': 16, 'len': 2, 'mask': 0x3}, 
            'risky_type': {'pos': 18, 'len': 2, 'mask': 0x3}, 
            'rsv': {'pos': 20, 'len': 12, 'mask': 0xFFF}, 
        }
    response, rep_data = api.get_vb_info()
    dumpfile("rep_data.bin", bytearray(rep_data))
    ftl_vb_list_data = dict()

    for vb in range(len(rep_data)):
        if fw_geometry.l52_total_vb_count <= vb:
            break
        if vb *4  >= len(rep_data):
            break

        ftl_vb_list_data.update({vb : {k: (((rep_data[vb*4]|rep_data[vb*4+1]<<8) >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
    if show:
        for vb, info in ftl_vb_list_data.items():
            group = info['group']
            access_mode = info['access_mode']
            partition = info['partition']
            logger.info(f'VB {vb} grouptype = {group} ({project_api.VB_GROUP(group).name}), access_mode = {access_mode}, partition = {partition}')
    return ftl_vb_list_data


def config_lun() -> tuple[int,int]:
    Total_AU_Count = shared.param.gGeometry.q4_total_raw_device_capacity // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
    config_descs = api.get_config_descriptors(print=False)
    for table in range(4):
        for unit in range(8):
            config_descs[table].header.b2_conf_desc_continue = 1
            config_descs[table].units[unit].b0_lu_enable = 0
            config_descs[table].units[unit].b1_boot_lun_id = 0
            config_descs[table].units[unit].l4_num_alloc_units = 0
            config_descs[table].units[unit].b9_logical_block_size = 0xc
            config_descs[table].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
            if (table * 8 + unit) == 0:
                config_descs[table].units[unit].b0_lu_enable = 1
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                config_descs[table].units[unit].l4_num_alloc_units = min(shared.param.gGeometry.l44_enhanced1_max_n_alloc_u, Total_AU_Count//2)
            elif (table * 8 + unit) == 1:
                config_descs[0].units[unit].b0_lu_enable = 1
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[0].units[unit].b3_memory_type = api.MemoryType.NORMAL
                config_descs[0].units[unit].l4_num_alloc_units = Total_AU_Count//2
    
    config_descs[3].header.b2_conf_desc_continue = 0
    config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.ENABLE
    config_descs[0].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
    config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0
    for i in range(4):
        api.push_write_config(config_descs[i], index=i)
    ExecuteCMD.send()
    ExecuteCMD.clear()

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
    ExecuteCMD.send(clear_on_success=False)
    ExecuteCMD.clear()

    slc_lun = 0
    tlc_lun = 1
    return (slc_lun, tlc_lun)

def get_PCA_and_print(lun: int, lba: int, rpmb_region: int = 0) -> PCA:
    _pca = lba_to_pba(lun, lba, rpmb_region)
    pca = PCA()
    pca.from_bytes(bytearray(_pca.payload))
    logger.info(f'Lun{lun}, LBA = {lba}: Block = {(pca.b11_block_h<<8) | (pca.b10_block_l)}, mode = {pca.b4_mode}, CE = {pca.b5_ce}, Plane = {pca.b6_plane}, fPage = {pca.l12_fpage}(pageline = {pca.l12_fpage>>5}), lmu = {pca.b20_lmu}, format = {pca.b7_format}')
    return pca

def print_open_vb_info_cursor(cursor:api.OpenVBInfoUnit, cursor_name:str) -> None:
    logger.info(f"===== {cursor_name} =====")
    logger.info(f"logical_vb: {cursor.logical_vb.value}")
    logger.info(f"physical_vb: {cursor.physical_vb.value}")
    logger.info(f"first_empty_CE: {cursor.first_empty_CE.value}")
    logger.info(f"first_empty_plane: {cursor.first_empty_plane.value}")
    logger.info(f"first_empty_physical_page: {cursor.first_empty_physical_page.value}")
    logger.info(f"first_empty_node: {cursor.first_empty_node.value}")

def polling_bkops(expect_value:int, timeout:int) -> int:
    start_time = time.time()
    while True:
        value_from_attribute = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
        if value_from_attribute == expect_value:
            break
        if (time.time() - start_time) > timeout:
            logger.error('timeout!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    return value_from_attribute

def trigger_ReadDisturb_refresh(write_record:List[List[api.WriteRecordNode]],
                                tlc_lun:int = 0) -> List[int]:
    sorted_vb_dict = get_sorted_VB_list()
    vb_list = sorted_vb_dict[project_api.VBListNum.CURRENT_L2_TLC]
    read_cnt_of_vb_before = project_api.get_all_VB_read_count()
    data_payload = bytearray(4096)
    for vb in range(len(read_cnt_of_vb_before)):
        if vb in vb_list:
            set_value = 0xFFFFFFFF-1
            logger.info(f"Set RC of VB {vb} = 0x{set_value:X}")
            data_payload[vb*4:(vb+1)*4] = (set_value).to_bytes(4, 'little')
        else:
            data_payload[vb*4:(vb+1)*4] = read_cnt_of_vb_before[vb].to_bytes(4, 'little')
    project_api.set_all_VB_read_count(data_payload=data_payload)
    api.read_compare(write_record)
    return vb_list
    
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

def get_HP_MP_LP_list(vb_list:List[int], max_cnt:int = 0) -> Dict[project_api.VUC087Paremeter, List[int]]:
    vb_random = vb_list[:]
    random.shuffle(vb_random)
    if max_cnt:
        vb_random = vb_random[:max_cnt]
    HP_list = [vb_random.pop()] if vb_random else []
    MP_list = [vb_random.pop()] if vb_random else []
    LP_list = [vb_random.pop()] if vb_random else []
    for vb in vb_random:
        r = random.randint(0, 2)
        if r == 0:
            HP_list.append(vb)
        elif r == 1:
            MP_list.append(vb)
        else:
            LP_list.append(vb)
    temp = {}
    if HP_list:
        temp[project_api.VUC087Paremeter.HighPriority] =  HP_list
    if MP_list:
        temp[project_api.VUC087Paremeter.MediumPriority] =  MP_list
    if LP_list:
        temp[project_api.VUC087Paremeter.LowPriority] =  LP_list
    return temp

def check_booking_queue(PriorityDict:Dict[project_api.VUC087Paremeter, List[int]]) -> project_api.BookingQueue:
    _, booking_q = project_api.issue_40C5_to_get_booking_queue()
    PriorityDict_temp = copy.deepcopy(PriorityDict)
    if PriorityDict_temp:
        if booking_q.LogicalVBNumberInBookingQueue.value == 0:
            logger.error_lb(f'check LogicalVBNumberInBookingQueue after bkops idle')
            logger.error_fp(f'expect LogicalVBNumberInBookingQueue is not 0, but current value = {booking_q.LogicalVBNumberInBookingQueue.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        for priority, vb_list in PriorityDict_temp.items():
            logger.info(f'check if {priority.name} has vb {vb_list}')
        for idx, VBs in enumerate(booking_q.BookingQueueVB):
            vb = VBs.LogicalVBNumber.value
            Priority_bit = project_api.BookingUser(VBs.TheBookingUser.value & 0x700)
            if Priority_bit == project_api.BookingUser.BOOKING_IN_HP:
                Priority = project_api.VUC087Paremeter.HighPriority
            elif Priority_bit == project_api.BookingUser.BOOKING_IN_MP:
                Priority = project_api.VUC087Paremeter.MediumPriority
            else:
                Priority = project_api.VUC087Paremeter.LowPriority
            logger.info(f'BookingQ[{idx}]: VB {vb}, TheBookingUser: {project_api.BookingUser(VBs.TheBookingUser.value & project_api.BookingUser.MAX_BOOKING_USER_COUNT-1).name} ({Priority.name})')
            if vb not in PriorityDict_temp[Priority]:
                logger.error_lb(f'check vb {vb} after Booking')
                logger.error_fp(f'VB {vb} is {Priority_bit.name},  but not in {Priority.name} {PriorityDict_temp[Priority]}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                PriorityDict_temp[Priority].remove(vb)
        for priority, vb_list in PriorityDict_temp.items():
            for vb in vb_list:
                logger.error_lb(f'check vb {vb} after Booking')
                logger.error_fp(f'VB {vb} is not in booking_q, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    else:
        logger.info(f'check if LogicalVBNumberInBookingQueue is 0')
        if booking_q.LogicalVBNumberInBookingQueue.value != 0:
            logger.error_lb(f'check LogicalVBNumberInBookingQueue after bkops idle')
            logger.error_fp(f'expect LogicalVBNumberInBookingQueue is 0, but current value = {booking_q.LogicalVBNumberInBookingQueue.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    return booking_q

def check_vb_release(PriorityDict:Dict[project_api.VUC087Paremeter, List[int]]) -> Dict[project_api.VBListNum, List[int]]:
    sorted_vb_dict = get_sorted_VB_list()
    for Priority, vb_list in PriorityDict.items():
        for vb in vb_list:
            if vb not in sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_TLC]:
                current_group = project_api.VBListNum.OTHER
                for group, l in sorted_vb_dict.items():
                    if vb in l:
                        current_group = group                            
                        break
                logger.error_lb(f'check VB {vb} after bkops idle')
                logger.error_fp(f'expect VB {vb} is in FREE_BLK_QUEUE_TLC, but current in the {current_group.name}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    return sorted_vb_dict

def check_booking_user_in_queue(VB_list:List[int], expect_user:project_api.BookingUser, expect_priority:project_api.VUC087Paremeter) -> None:
    logger.info(f"issue VU 40C5 to check the refresh booking queue")
    _, booking_q = project_api.issue_40C5_to_get_booking_queue()
    if booking_q.LogicalVBNumberInBookingQueue.value == 0:
        logger.error_lb(f'check LogicalVBNumberInBookingQueue after RAIN decode')
        logger.error_fp(f'expect LogicalVBNumberInBookingQueue is not 0, but current value = {booking_q.LogicalVBNumberInBookingQueue.value}, result Fail!')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    for idx, VBs in enumerate(booking_q.BookingQueueVB):
        vb = VBs.LogicalVBNumber.value
        Priority_bit = project_api.BookingUser(VBs.TheBookingUser.value & 0x700)
        if Priority_bit == project_api.BookingUser.BOOKING_IN_HP:
            Priority = project_api.VUC087Paremeter.HighPriority
        elif Priority_bit == project_api.BookingUser.BOOKING_IN_MP:
            Priority = project_api.VUC087Paremeter.MediumPriority
        else:
            Priority = project_api.VUC087Paremeter.LowPriority
        TheBookingUser = project_api.BookingUser(VBs.TheBookingUser.value & project_api.BookingUser.MAX_BOOKING_USER_COUNT-1)
        logger.info(f'BookingQ[{idx}]: VB {vb}, TheBookingUser: {TheBookingUser.name} ({Priority.name})')
        if vb in VB_list:
            if expect_user != TheBookingUser or expect_priority != Priority:
                logger.error_lb(f'check vb {vb} after Booking')
                logger.error_fp(f'expect VB {vb} is {expect_user.name} ({expect_priority.name}),  but current is {TheBookingUser.name} ({Priority.name}), result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            VB_list.remove(vb)
        pass     
    if VB_list:
        logger.error_lb(f'check all vb book in refresh booking queue')
        logger.error_fp(f'expect VBs {VB_list} is booked, but not found in 40C5, result Fail!')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    pass


# ══════════════════════════════════════════════════════════════
# Trigger functions — each sets up FW conditions for a specific
# refresh type to be naturally detected and booked by the FW.
# Returns: list of VBs that should appear in the booking queue.
# ══════════════════════════════════════════════════════════════

def trigger_UECC_refresh(write_record: List[List[api.WriteRecordNode]],
                         tlc_lun: int = 0) -> List[int]:
    """Trigger Read UECC refresh by injecting UECC and reading.
       FW naturally books EH_BOOKSIGNALUECC_BOOKING_0."""
    from Script.pattern.rain.mutual_fun import get_PCA_and_print, inject_UECC
    pca = get_PCA_and_print(lun=tlc_lun, lba=0)
    inject_UECC(pca=pca, SLC_enable=False)
    api.read_compare(write_record)
    return [pca.virtual_block_number.value]


def trigger_wear_leveling_lowgap_refresh(write_record: List[List[api.WriteRecordNode]] | None = None) -> List[int]:
    """Trigger Static WL LowGap refresh by manipulating erase count.
       FW naturally books SWL_REFRESH_LOW_GAP."""
    import copy
    fw_geometry = api.get_fw_geometry()
    _, debug_info = api.get_debug_info()
    _, erase_cnt_buffer_backup = api.read_Xmemory(sram_address=debug_info.VB_list_cycle_address.value)
    _, wl_info = project_api.issue_4098_to_get_wear_leveling_information()
    sorted_vb_dict = get_sorted_VB_list()

    for type_ in [project_api.VBListNum.CURRENT_L2_TLC, project_api.VBListNum.CURRENT_L2_EM1, project_api.VBListNum.PTE_POOL]:
        if type_ in sorted_vb_dict:
            break

    target_vb = sorted_vb_dict[type_][0]

    # Parameters per pool type
    gEC_for_Static_pool = 0
    gEC_for_dynamic_pool = 0
    gEC_for_static_ICS_pool = 0
    gEC_of_Static_pool_for_open = 0
    gEC_of_dynamic_pool_for_open = 0

    if type_ == project_api.VBListNum.CURRENT_L2_TLC:
        gEC_of_dynamic_pool_for_open = wl_info.EC_Threshold_of_dynamic_pool.value + 1
        target_free_vb = sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_TLC][0]
        set_ec = wl_info.EC_gap_delta_Threshold_TH1_of_dynamic_pool.value + 1
        set_version = wl_info.globalVersion_of_dynamic_pool.value + 1
    elif type_ == project_api.VBListNum.CURRENT_L2_EM1:
        gEC_of_Static_pool_for_open = wl_info.EC_Threshold_of_static_pool.value + 1
        target_free_vb = sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_EM1][0]
        set_ec = wl_info.EC_gap_delta_Threshold_TH1_of_static_pool.value + 1
        set_version = wl_info.globalVersion_of_static_pool.value + 1
    else:  # PTE_POOL
        gEC_for_static_ICS_pool = wl_info.EC_Threshold_of_ICS_pool.value + 1
        target_free_vb = sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_TABLE][0]
        set_ec = wl_info.EC_gap_delta_Threshold_TH1_of_ICS_pool.value + 1
        set_version = 0

    set_erase_cnt_payload = copy.deepcopy(erase_cnt_buffer_backup)[0:api.DATA_SIZE_4K_BYTE]
    set_version_dict: Dict[int, int] = {}
    for vb in range(fw_geometry.l52_total_vb_count):
        set_version_dict[vb] = 0

    set_erase_cnt_payload[target_vb * 4 : (target_vb+1)*4] = (0).to_bytes(4, 'little')
    set_erase_cnt_payload[target_free_vb * 4 : (target_free_vb+1)*4] = (set_ec).to_bytes(4, 'little')
    set_version_dict[target_vb] = set_version

    api.set_ftl_version(set_VB_version=set_version_dict)
    project_api.issue_C072_to_set_static_wear_leveling_EC_gap_threshold(
        gEC_for_Static_pool,
        gEC_for_dynamic_pool,
        gEC_for_static_ICS_pool,
        gEC_of_Static_pool_for_open,
        gEC_of_dynamic_pool_for_open,
        wl_info.EC_gap_delta_Threshold_TH1_of_static_pool.value,
        wl_info.EC_gap_delta_Threshold_TH1_of_dynamic_pool.value,
        wl_info.EC_gap_delta_Threshold_TH1_of_ICS_pool.value,
        wl_info.EC_gap_delta_Threshold_TH2_of_static_pool.value,
        wl_info.EC_gap_delta_Threshold_TH2_of_dynamic_pool.value,
        wl_info.EC_gap_delta_Threshold_TH2_of_ICS_pool.value)
    project_api.set_all_VB_erase_count(data_payload=set_erase_cnt_payload, set_in_ram=True)

    return [target_vb]


def trigger_wear_leveling_highgap_refresh(write_record: List[List[api.WriteRecordNode]] | None = None) -> List[int]:
    """Trigger Static WL HighGap refresh (larger EC gap).
       FW naturally books SWL_REFRESH_HIGH_GAP."""
    import copy
    fw_geometry = api.get_fw_geometry()
    _, debug_info = api.get_debug_info()
    _, erase_cnt_buffer_backup = api.read_Xmemory(sram_address=debug_info.VB_list_cycle_address.value)
    _, wl_info = project_api.issue_4098_to_get_wear_leveling_information()
    sorted_vb_dict = get_sorted_VB_list()

    for type_ in [project_api.VBListNum.CURRENT_L2_TLC, project_api.VBListNum.CURRENT_L2_EM1, project_api.VBListNum.PTE_POOL]:
        if type_ in sorted_vb_dict:
            break

    target_vb = sorted_vb_dict[type_][0]

    gEC_for_Static_pool = 0
    gEC_for_dynamic_pool = 0
    gEC_for_static_ICS_pool = 0
    gEC_of_Static_pool_for_open = 0
    gEC_of_dynamic_pool_for_open = 0

    if type_ == project_api.VBListNum.CURRENT_L2_TLC:
        gEC_of_dynamic_pool_for_open = wl_info.EC_Threshold_of_dynamic_pool.value + 1
        target_free_vb = sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_TLC][0]
        set_ec = wl_info.EC_gap_delta_Threshold_TH2_of_dynamic_pool.value + 1
        set_version = wl_info.globalVersion_of_dynamic_pool.value + 2
    elif type_ == project_api.VBListNum.CURRENT_L2_EM1:
        gEC_of_Static_pool_for_open = wl_info.EC_Threshold_of_static_pool.value + 1
        target_free_vb = sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_EM1][0]
        set_ec = wl_info.EC_gap_delta_Threshold_TH2_of_static_pool.value + 1
        set_version = wl_info.globalVersion_of_static_pool.value + 2
    else:  # PTE_POOL
        gEC_for_static_ICS_pool = wl_info.EC_Threshold_of_ICS_pool.value + 1
        target_free_vb = sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_TABLE][0]
        set_ec = wl_info.EC_gap_delta_Threshold_TH2_of_ICS_pool.value + 1
        set_version = 0

    set_erase_cnt_payload = copy.deepcopy(erase_cnt_buffer_backup)[0:api.DATA_SIZE_4K_BYTE]
    set_version_dict: Dict[int, int] = {}
    for vb in range(fw_geometry.l52_total_vb_count):
        set_version_dict[vb] = 0

    set_erase_cnt_payload[target_vb * 4 : (target_vb+1)*4] = (0).to_bytes(4, 'little')
    set_erase_cnt_payload[target_free_vb * 4 : (target_free_vb+1)*4] = (set_ec).to_bytes(4, 'little')
    set_version_dict[target_vb] = set_version

    api.set_ftl_version(set_VB_version=set_version_dict)
    project_api.issue_C072_to_set_static_wear_leveling_EC_gap_threshold(
        gEC_for_Static_pool,
        gEC_for_dynamic_pool,
        gEC_for_static_ICS_pool,
        gEC_of_Static_pool_for_open,
        gEC_of_dynamic_pool_for_open,
        wl_info.EC_gap_delta_Threshold_TH1_of_static_pool.value,
        wl_info.EC_gap_delta_Threshold_TH1_of_dynamic_pool.value,
        wl_info.EC_gap_delta_Threshold_TH1_of_ICS_pool.value,
        wl_info.EC_gap_delta_Threshold_TH2_of_static_pool.value,
        wl_info.EC_gap_delta_Threshold_TH2_of_dynamic_pool.value,
        wl_info.EC_gap_delta_Threshold_TH2_of_ICS_pool.value)
    project_api.set_all_VB_erase_count(data_payload=set_erase_cnt_payload, set_in_ram=True)

    return [target_vb]


# ── Shell / placeholder trigger functions ──

def trigger_mediascan_refresh(write_record: List[List[api.WriteRecordNode]]) -> List[int]:
    """Trigger MediaScan refresh.
       FW naturally books MEDIA_SCAN_BOOKING_0/1."""
    from Script.project_api.custom_vu.media_scan_vu.structs import micron_vu_C085_param_with_data

    project_api.issue_C08B_to_enable_diable_media_scan(True)

    param = micron_vu_C085_param_with_data()
    param.last_scan_spend_time = 0x1000000
    project_api.issue_C085_to_set_media_scan_parameters(param)

    api.read_compare(write_record)

    return get_sorted_VB_list().get(project_api.VBListNum.CURRENT_L2_TLC, [])


def trigger_hir_refresh(write_record: List[List[api.WriteRecordNode]],
                        tlc_lun: int = 0) -> List[int]:
    """Trigger Host Initiated Refresh (HIR).
       FW naturally books HOST_INITIATED_REFRESH."""
    api.write_attribute(idn=api.AttributeIDN.REFRESH_UNIT, val=0)
    api.write_attribute(idn=api.AttributeIDN.REFRESH_METHOD, val=1)

    fw_geometry = api.get_fw_geometry()
    tlc_vb_size = (fw_geometry.l88_vb_size_u1 * 512 // 4096)
    api.sequential_write(lun=tlc_lun, start_lba=0, total_size=tlc_vb_size * 2,
                         chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua=0,
                         need_compare=False, compare_method=api.CompareMethod.HW_COMPARE,
                         write_record=write_record)

    return get_sorted_VB_list().get(project_api.VBListNum.CURRENT_L2_TLC, [])


def trigger_xtemp_refresh(write_record: List[List[api.WriteRecordNode]],
                          tlc_lun: int = 0) -> List[int]:
    """Trigger XTemp refresh by setting temperature outside T1~T2 range.
       FW naturally books XTEMP_BOOKING."""
    from Script.pattern.hir.mutual_fun import (
        get_xtemp_parameter, set_nand_temp, set_ec, Tnand_in_T1_T2_range
    )
    fw_geometry = api.get_fw_geometry()
    flash_setting = api.get_flash_setting()
    CE = flash_setting.FLH_Quantity * (1 << flash_setting.Parallel)

    # 1. Get XTemp config
    (XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER,
     XTEMP_TIME_DETECTION_VALUE,
     XTEMP_REFRESH_T1, XTEMP_REFRESH_T2) = get_xtemp_parameter()
    idle_wait = XTEMP_TIME_DETECTION_VALUE
    logger.info(f"XTemp T1={XTEMP_REFRESH_T1} T2={XTEMP_REFRESH_T2} "
                f"detect={idle_wait}s EC_enable={XTEMP_ENABLE_PEC}")

    # 2. Set EC high on all VBs to enable XTemp detection
    set_ec_value = XTEMP_ENABLE_PEC * 100
    value_bytes = set_ec_value.to_bytes(4, 'little')
    data = bytearray(b'\xFF' * 0x4000)
    data[:(fw_geometry.l52_total_vb_count * 4)] = value_bytes * fw_geometry.l52_total_vb_count
    set_ec(fw_geometry.l52_total_vb_count, data)

    # 3. HW reset to enable XTemp algo
    api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=True)

    # 4. Ensure Tnand is within safe range first
    if not Tnand_in_T1_T2_range(CE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2):
        set_temp = (XTEMP_REFRESH_T2 - XTEMP_REFRESH_T1) // 2
        set_nand_temp(CE, set_temp=set_temp)
        time.sleep(idle_wait)

    # 5. Write some data
    tlc_vb_size = (fw_geometry.l88_vb_size_u1 * 512 // 4096)
    api.sequential_write(lun=0, start_lba=0, total_size=tlc_vb_size,
                         chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua=0,
                         need_compare=False, compare_method=api.CompareMethod.HW_COMPARE,
                         write_record=write_record)

    # 6. Set temperature outside range → triggers XTemp booking
    set_nand_temp(CE, set_temp=XTEMP_REFRESH_T2 + 1)
    time.sleep(idle_wait)

    # 7. Back to safe range
    set_nand_temp(CE, set_temp=XTEMP_REFRESH_T1 - 1)
    time.sleep(idle_wait)

    return get_sorted_VB_list().get(project_api.VBListNum.CURRENT_L2_TLC, [])


def trigger_psa_refresh(write_record: List[List[api.WriteRecordNode]],
                        tlc_lun: int = 0) -> List[int]:
    """Trigger PSA refresh.
       FW naturally books PSA_BOOKING."""
    dev_desc = api.get_device_descriptor()
    api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=dev_desc.l37_psa_max_data_size)
    api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.PRE_SOLDERING)
    logger.info(f"PSA State = {api.read_attribute(idn=api.AttributeIDN.PSA_STATE)}")
    api.sequential_write(lun=0, start_lba=0, total_size=api.BLOCK4K_SIZE_128M_BYTE,
                         chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua=1,
                         need_compare=False, compare_method=api.CompareMethod.HW_COMPARE,
                         write_record=write_record)
    api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.LOADING_COMPLETE)
    logger.info(f"PSA State = {api.read_attribute(idn=api.AttributeIDN.PSA_STATE)}")
    api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET)
    api.random_write(cmd_count=1, min_lun=0, max_lun=0, min_lba=1, max_lba=1,
                     min_size=api.BLOCK4K_SIZE_4K_BYTE, max_size=api.BLOCK4K_SIZE_4K_BYTE,
                     need_compare=False, compare_method=api.CompareMethod.HW_COMPARE,
                     write_record=write_record)
    return get_sorted_VB_list().get(project_api.VBListNum.CURRENT_L2_TLC, [])




def trigger_bfea_refresh(write_record: List[List[api.WriteRecordNode]]) -> List[int]:
    """Trigger BFEA scan refresh.
       FW naturally books BFEA_SCAN_BOOKING."""
    fw_geometry = api.get_fw_geometry()
    flash_setting = api.get_flash_setting()
    ce_num = flash_setting.Max_Fdevice
    tlc_vb_size = (fw_geometry.l88_vb_size_u1 * 512 // 4096)

    # 1. Write data to create VB
    api.sequential_write(lun=0, start_lba=0, total_size=tlc_vb_size * 3,
                         chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua=1,
                         need_compare=False, compare_method=api.CompareMethod.HW_COMPARE,
                         write_record=write_record)

    # 2. Get target VB from PCA
    from Script.pattern.rain.mutual_fun import get_PCA_and_print
    pca_info = get_PCA_and_print(lun=0, lba=0)
    vb = pca_info.virtual_block_number.value


    # 5. Wait for timer + scan completion
    import time
    logger.info(f"  waiting {setting_timer_minutes} min for BFEA trigger...")
    time.sleep(setting_timer_minutes * 60)
    _polling_bfea_idle()

    return get_sorted_VB_list().get(project_api.VBListNum.CURRENT_L2_TLC, [])


# ══════════════════════════════════════════════════════════════
# Verify helpers
# ══════════════════════════════════════════════════════════════

def verify_refresh_event_logs(vb_list: List[int], expect_user: int,
                               log_ids: tuple[int, ...] = (0x3006, 0x3051)) -> None:
    """Check event logs after refresh completes.

    Single-pass scan. Pass log_ids=(0x3006,) or (0x3051,) to check only one type.
    """
    from Script.project_api.custom_vu.read_log.functions import _get_event_log_count, _read_event_log_by_index

    count = _get_event_log_count(project_api.EventLogPriority.LowPriority)
    if count == 0:
        logger.warning("  No event logs found in NAND after timeout")
        return

    if count > 50:
        logger.warning(f"  Large event log count={count}, scanning anyway "
                       f"but may be slow")

    need_3006 = 0x3006 in log_ids
    need_3051 = 0x3051 in log_ids
    found_3006 = False
    found_3051 = False

    for idx in range(count):
        try:
            buf = _read_event_log_by_index(idx, project_api.EventLogPriority.LowPriority)
        except Exception:
            continue

        # Check log_id at SPECIFIC_LOG_INFO_OFFSET
        log_id = int.from_bytes(buf[project_api.SPECIFIC_LOG_INFO_OFFSET:
                                    project_api.SPECIFIC_LOG_INFO_OFFSET + 4], 'little')

        if log_id == 0x3006 and need_3006 and not found_3006:
            found_3006 = True
            ev = project_api.BookRefEventLog(buf, project_api.SPECIFIC_LOG_INFO_OFFSET)
            print_object_info_ai(ev)
            errors: list[str] = []
            if ev.log_id.value != 0x3006:
                errors.append(f"log_id: expected=0x3006, actual=0x{ev.log_id.value:04X}")
            if ev.blockType.value not in (0, 1):
                errors.append(f"blockType: expected 0(SLC) or 1(TLC), actual={ev.blockType.value}")
            if ev.rdLogVB.value not in vb_list:
                errors.append(f"rdLogVB: expected in {vb_list}, actual={ev.rdLogVB.value}")
            if ev.user.value != expect_user and ev.user.value != 0:
                errors.append(f"user: expected={expect_user}({project_api.BookingUser(expect_user).name}), actual={ev.user.value}")
            # if ev.firstFreePP.value == 0:
            #     errors.append(f"firstFreePP: expected >0, actual=0")
            # if ev.rcCount.value == 0:
            #     errors.append(f"rcCount: expected >0, actual=0")
            # if ev.ecCount.value == 0:
            #     errors.append(f\"ecCount: expected >0, actual=0\")
            if errors:
                logger.error_lb(f'BookRefEventLog[{idx}] field validation FAIL')
                for e in errors:
                    logger.error_lb(f'  {e}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            logger.info(f"  BookRefEventLog[{idx}] — OK")

        elif log_id == 0x3051 and need_3051 and not found_3051:
            found_3051 = True
            ev2 = project_api.RefStartEventLog(buf, project_api.SPECIFIC_LOG_INFO_OFFSET)
            print_object_info_ai(ev2)
            errors = []
            if ev2.log_id.value != 0x3051:
                errors.append(f"log_id: expected=0x3051, actual=0x{ev2.log_id.value:04X}")
            if ev2.timestamp.value == 0:
                errors.append(f"timestamp: expected non-zero (refresh started), actual=0")
            if ev2.srcLogicVB.value not in vb_list:
                errors.append(f"srcLogicVB: expected in {vb_list}, actual={ev2.srcLogicVB.value}")
            if ev2.srcPhysicalVB.value == 0xFFFF or ev2.srcPhysicalVB.value == 0:
                errors.append(f"srcPhysicalVB: expected valid physical VB, actual={ev2.srcPhysicalVB.value}")
            if ev2.temperature.value > 125:
                errors.append(f"temperature: expected [-40,125], actual={ev2.temperature.value}")
            if ev2.isOppositeRisky.value not in (0, 1):
                errors.append(f"isOppositeRisky: expected 0 or 1, actual={ev2.isOppositeRisky.value}")
            if errors:
                logger.error_lb(f'RefStartEventLog[{idx}] field validation FAIL')
                for e in errors:
                    logger.error_lb(f'  {e}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            logger.info(f"  RefStartEventLog[{idx}] — OK")

        # Early exit once all requested log IDs are found
        if (not need_3006 or found_3006) and (not need_3051 or found_3051):
            break

    # Summary
    missing = []
    if need_3006 and not found_3006:
        missing.append("0x3006(BookRefEventLog)")
    if need_3051 and not found_3051:
        missing.append("0x3051(RefStartEventLog)")
    if missing:
        logger.error_lb(f"Expected event log(s) not found: {', '.join(missing)}")
        logger.error_fp(f"refresh may not have generated expected event logs")
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    logger.info(f"  All expected event logs verified — OK")
    
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