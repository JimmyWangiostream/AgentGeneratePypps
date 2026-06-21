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
from Script.project_api.functions import get_physical_layout
import time
max_plane = 0

def erase_all_lun(write_record: List[List[api.WriteRecordNode]]) -> None:
    for lun in range(shared.param.gMaxNumberLU):
        if not shared.param.gUnit[lun].b3_lu_enable:
            continue
        capacity = shared.param.gLUCapacity[lun]
        lba = 0
        while capacity > 0:
            length = min(ERASE_MAX_BLOCK_LEN, capacity)
            unmap = ExecuteCMD.Unmap()
            unmap.assign(lun=lun, lba=lba, length=length)
            ExecuteCMD.enqueue(unmap)
            capacity -= length
            lba += length            
    ExecuteCMD.send(clear_on_success=False)
    for cmd in ExecuteCMD._cmd_list:
        api.save_write_info_by_cmd(cmd, write_record)   
    ExecuteCMD.clear()
    f = ExecuteCMD.FormatUnit()
    f.assign(lun=api.WellKnownLUN.UFS_DEVICE, longlist=0, cmplist=0)
    ExecuteCMD.enqueue(f)
    ExecuteCMD.send()

def get_PCA_VB_and_print(lun: int, lba: int) -> tuple[int, project_api.physical_address_info]:
    global max_plane
    if max_plane == 0:
        _flash_setting = api.get_flash_setting()
        max_plane = _flash_setting.Plane_Per_Die
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
    return vb, out_pca

def push_ssu() -> None:
    ssu = ExecuteCMD.StartStopUnit()
    ssu.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0)
    ssu.set_option(wait_queue_empty=True)
    ExecuteCMD.enqueue(ssu)
    ssu.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0)
    ssu.set_option(wait_queue_empty=True)
    ExecuteCMD.enqueue(ssu)
    return

def ssu_sleep_and_active() -> None:
    push_ssu()
    ExecuteCMD.send(clear_on_success=True)
    pass

def print_open_vb_info_cursor(cursor:api.OpenVBInfoUnit, cursor_name:str) -> None:
    logger.info(f"===== {cursor_name} =====")
    logger.info(f"logical_vb: {cursor.logical_vb.value}")
    logger.info(f"physical_vb: {cursor.physical_vb.value}")
    logger.info(f"first_empty_CE: {cursor.first_empty_CE.value}")
    logger.info(f"first_empty_plane: {cursor.first_empty_plane.value}")
    logger.info(f"first_empty_physical_page: {cursor.first_empty_physical_page.value}")
    logger.info(f"first_empty_node: {cursor.first_empty_node.value}")
    
def inject_UECC(pca:project_api.physical_address_info, SLC_enable:bool = False) -> None:
    vb = pca.virtual_block_number.value
    Die = pca.die.value
    Plane = pca.plane.value
    Block = pca.physical_block_number_w_BBT.value
    Page = pca.page.value
    logger.info(f'Inject UECC: PhyBlock = {Block}, CE = {Die}, Plane = {Plane}, Page = {Page}, SLC_enable = {SLC_enable}')
    if SLC_enable:
        dire_write_payload = bytearray(DATA_SIZE_16K_BYTE)
    else:
        dire_write_payload = bytearray(DATA_SIZE_20K_BYTE*3)
    for i in range(len(dire_write_payload)):
        dire_write_payload[i] = 0xAA
    _ = project_api.issue_C060_to_write_raw_data(Ce=Die,Block=Block,Plane=Plane, Page=Page,SLC_Enable=SLC_enable,Ecc_Enable=1, datapayload=dire_write_payload)
    return

def config_lun(normal_list:List[int], em1_list:List[int]) -> None:
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

def polling_bkops_idle() -> None:
    while 1:
        bkops_status = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
        if bkops_status == 0:
            break
        time.sleep(1)
        
def check_BB_retirementafter_refresh(VB_list:List[int] = [], expect_reason:project_api.BBRetirementReaspnType = project_api.BBRetirementReaspnType.DUMMY) -> None:
    _, bbt_data = project_api.issue_405E_to_get_bad_block_information()
    total_BB_count = int.from_bytes(bbt_data[0:4], 'little')
    if total_BB_count == 0:
        logger.error_lb(f'check total_BB_count of VU')
        logger.error_fp(f'expect total_BB_count from BB Table not equal to 0 after UECC, but total_BB_count value = {total_BB_count}, result Fail!')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    start = 4
    for idx in range(total_BB_count):
        BB_retirement_reason = project_api.BB_retirement_reason(bbt_data[start + idx*8: start + idx*8 +4])
        PBA = project_api.PBA_format(bbt_data[start + 4 + idx*8: start + 4 + idx*8 +4])
        vb = PBA.blockNum.value
        BlkType = project_api.BBRetirementReaspnBlkType(BB_retirement_reason.BlkType.value)
        Reason = project_api.BBRetirementReaspnType(BB_retirement_reason.Type.value)
        # if BB_retirement_reason.BlkType.value != 0 or BB_retirement_reason.Type.value != 0:
        logger.info(f'idx = {idx}, Block : {vb},  BlkType = {BlkType} ({BlkType.name}), Reason = {Reason} ({Reason.name})')
        if vb in VB_list:
            if expect_reason != Reason:
                logger.error_lb(f'check vb {vb} BBRetirementReaspn after refresh')
                logger.error_fp(f'expect VB {vb} is {expect_reason.name},  but current is {Reason.name}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            VB_list.remove(vb)
        pass  
    if VB_list:
        logger.error_lb(f'check all vb BBRetirementReaspn in BBT')
        logger.error_fp(f'expect VBs {VB_list} is updated, but not found in 405E, result Fail!')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    return