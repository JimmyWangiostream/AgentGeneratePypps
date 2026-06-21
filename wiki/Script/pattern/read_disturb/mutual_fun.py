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
import time
from Script.project_api.functions import print_object_info_ai


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

def read_LBA_repeatedly(lun:int, lba:int, read_times:int) -> None:
    for _ in range(read_times):
        read10 = ExecuteCMD.Read10()
        read10.assign(lun=lun, lba=lba, length=1, fua=1)
        ExecuteCMD.enqueue(read10)
    ExecuteCMD.send(timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
    return
    
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

def get_group_dict(vb_list_data:Dict[int, Dict[str, int]]) -> Dict[project_api.VB_GROUP, List[int]]:
    VB_dict:Dict[project_api.VB_GROUP, List[int]] = {}
    for vb, info in vb_list_data.items():
        group = info['group']
        if project_api.VB_GROUP(group) not in VB_dict:
            VB_dict[project_api.VB_GROUP(group)] = []
        VB_dict[project_api.VB_GROUP(group)].append(vb)
    return VB_dict

def polling_bkops_idle() -> None:
    while 1:
        bkops_status = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
        if bkops_status == 0:
            break
        time.sleep(1)
        
def polling_Read_Disturb_idle(vb:int) -> None:
    start_time = time.time()
    timeout_min = 1
    while 1:
        _, infofation = project_api.issue_40CB_to_get_total_Read_Count_and_Flush_RC_table_threshold(LogicalVB=vb)
        if infofation.IsScanTaskIdle.value == 1:
            break
        current_time = time.time()
        if (current_time - start_time) >= timeout_min * 60:
                logger.error_lb('Polling Read Disturb done in 1 min')
                logger.error_fp(f'Expect Read Disturb done in 1 min but not, current IsScanTaskIdle =  {infofation.IsScanTaskIdle.value}')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
        time.sleep(1)
        
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

def get_PCA_and_print(lun: int, lba: int) -> project_api.physical_address_info:
    _, pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=lba)
    vb = pca.virtual_block_number.value
    Die = pca.die.value
    Plane = pca.plane.value
    Block = pca.physical_block_number_w_BBT.value
    Page = pca.page.value
    logger.info(f'Lun{lun}, LBA = {lba}: VB = {vb}, PhyBlock = {Block}, CE = {Die}, Plane = {Plane}, Page = {Page}')
    return pca
    
def get_mConfig_value(mConfig:project_api.mConfig, field_name:str) ->int:
    fields = [
        (name, field) for name, field in mConfig.__dict__.items()
        if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
    ]
    for name, field in fields:
        if name == field_name:
            return int(field.value)
    logger.error_lb(f'get {field_name} in mConfig')
    logger.error_fp(f'there is no field name equal to {field_name}')
    raise PATTERN_ASSERT_UNEXPECTED_CONDITION

def get_EC_RC_TH(mConfig:project_api.mConfig, EC:int, is_SLC:bool, is_open:bool, vb:int) -> tuple[str, int]:
    XLC = "SLC" if is_SLC else "TLC"
    FP = "P" if is_open else "F"
    group = 0
    while group <= 4:
        EC_field = f"{XLC}_EC_{group}"
        upper_value = get_mConfig_value(mConfig=mConfig, field_name=EC_field) * 100
        if EC <= upper_value:
            expect_field = f"{XLC}_EC_RC_TH_{FP}B{group}"
            EC_RC_TH = get_mConfig_value(mConfig=mConfig, field_name=expect_field) * 1000
            logger.info(f'get {expect_field} = {EC_RC_TH} due to EC[{vb}] = {EC} < {upper_value} ({EC_field})')
            return expect_field, EC_RC_TH
        group += 1
    max_value = get_mConfig_value(mConfig=mConfig, field_name=f"{XLC}_EC_4") * 1000
    logger.error_lb(f'check RC of vb {vb} after creation')
    logger.error_fp(f'EC[{vb}] should never overcome {XLC}_EC_4 = {max_value}, but current value = {EC}, result Fail!')
    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

def get_SF(mConfig:project_api.mConfig, BER:int, vb:int) -> tuple[str, int, bool]:
    group = 0
    need_refresh = False
    while group <= 4:
        RBER_FB_SF_field = f"RBER_FB_SF_{group}"
        upper_value = get_mConfig_value(mConfig=mConfig, field_name=RBER_FB_SF_field)
        if BER < upper_value:
            expect_field = f"SF_{group}"
            SF = get_mConfig_value(mConfig=mConfig, field_name=expect_field)
            logger.info(f'get {expect_field} = {SF} due to BER of VB{vb} = {BER} < {upper_value} ({RBER_FB_SF_field})')
            return expect_field, SF, need_refresh
        group += 1
    need_refresh = True
    logger.info(f'VB{vb} need to be refreshed due to BER of VB{vb} = {BER} >= {upper_value} ({RBER_FB_SF_field})')
    return "", 0, need_refresh

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