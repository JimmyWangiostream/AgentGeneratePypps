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

match_dict:Dict[project_api.VB_GROUP, Dict[str, list[project_api.VBListNum] | list[project_api.OpenVBType]]] = {
    project_api.VB_GROUP.HIDDEN_BLK_USE : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.LIST_BLK : {"VBList":[project_api.VBListNum.LIST_BLK], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.LIST_INDEX_BLK : {"VBList":[project_api.VBListNum.INDEX_BLK], "OpenType":[project_api.OpenVBType.OTHER, project_api.OpenVBType.INDEX_BLK]},
    project_api.VB_GROUP.TMP_CODE_BLK : {"VBList":[project_api.VBListNum.TMP_CODE_BLK], "OpenType":[project_api.OpenVBType.OTHER, project_api.OpenVBType.TEMP_CODE_BLK]},
    project_api.VB_GROUP.CURRENT_PTE : {"VBList":[project_api.VBListNum.CURRENT_PTE], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.LOG_TAB_BLK : {"VBList":[project_api.VBListNum.LOG_TAB_BLK], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.CURRENT_L2_SLC : {"VBList":[project_api.VBListNum.CURRENT_L2_EM1], "OpenType":[project_api.OpenVBType.OTHER, project_api.OpenVBType.EM1_L2_BLK]},
    project_api.VB_GROUP.CURRENT_L2_MLC : {"VBList":[project_api.VBListNum.CURRENT_L2_TLC, project_api.VBListNum.CURRENT_L2_TLC_WB], "OpenType":[project_api.OpenVBType.OTHER, project_api.OpenVBType.L2_OPEN_LOGICAL_VB, project_api.OpenVBType.WRITE_BOOSTER_L2]},
    project_api.VB_GROUP.FREEZE_L2_BLK : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.CURRENT_DATA_GC_BLK_SLC : {"VBList":[project_api.VBListNum.DATA_GC_TARGET_BLK_EM1], "OpenType":[project_api.OpenVBType.OTHER, project_api.OpenVBType.EM1_GC]},
    project_api.VB_GROUP.CURRENT_DATA_GC_BLK_MLC : {"VBList":[project_api.VBListNum.DATA_GC_TARGET_BLK_TLC], "OpenType":[project_api.OpenVBType.OTHER, project_api.OpenVBType.NORMAL_DEFRAG_VB]},
    project_api.VB_GROUP.INCOMPLETE_BLK_SLC : {"VBList":[project_api.VBListNum.INCOMPLETE_BLK_EM1], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.INCOMPLETE_BLK_MLC : {"VBList":[project_api.VBListNum.INCOMPLETE_BLK_TLC], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.CURRENT_L1 : {"VBList":[project_api.VBListNum.CURRENT_L1], "OpenType":[project_api.OpenVBType.OTHER, project_api.OpenVBType.L1_OPEN_VB]},
    project_api.VB_GROUP.PTE_POOL : {"VBList":[project_api.VBListNum.PTE_POOL], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.STATIC_SLC_USED_BLK : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.USED_BLK_POOL_SLC : {"VBList":[project_api.VBListNum.USED_BLK_POOL_EM1], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.USED_BLK_POOL_MLC : {"VBList":[project_api.VBListNum.USED_BLK_POOL_TLC, project_api.VBListNum.USED_BLK_POOL_TLC_WB], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.CURRENT_L3_SLC : {"VBList":[project_api.VBListNum.CURRENT_L3_EM1], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.CURRENT_L3_MLC : {"VBList":[project_api.VBListNum.CURRENT_L3_TLC], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.REFRESH_LINE : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.RAIN_SWAP_NO_OBR_SLC_L2_SLC : {"VBList":[project_api.VBListNum.RAIN_SWAP_EM1], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_SLC : {"VBList":[project_api.VBListNum.RAIN_SWAP_WB], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_TLC : {"VBList":[project_api.VBListNum.RAIN_SWAP_TLC], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.RAIN_SWAP_NO_OBR_BLK : {"VBList":[project_api.VBListNum.RAIN_SWAP_TEMP_RAIN], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.RAIN_SWAP_TLC_CURSOR_BLK : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.FREE_BLK_QUEUE_SLC : {"VBList":[project_api.VBListNum.FREE_BLK_QUEUE_EM1], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.FREE_BLK_QUEUE_MLC : {"VBList":[project_api.VBListNum.FREE_BLK_QUEUE_TLC], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.FREE_BLK_QUEUE_TABLE : {"VBList":[project_api.VBListNum.FREE_BLK_QUEUE_TABLE], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.TMP_ERASE_BLK_SLC : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.TMP_ERASE_BLK_MLC : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.TMP_ERASE_BLK_TABLE : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.TMP_USED_BLK_SLC : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.TMP_USED_BLK_MLC : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.TMP_USED_BLK_TABLE : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.TMP_REMOVE_BLK_SLC : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.TMP_REMOVE_BLK_MLC : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.TMP_REMOVE_BLK_TABLE : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.REFERENCE_QUEUE_SLC : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.REFERENCE_QUEUE_MLC : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.REVOKE_BLK : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.REMAP_DATA_GC_BLK_SLC : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.REMAP_DATA_GC_BLK_MLC : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.RPMB_COLLECT_BLK : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.PRE_ERASE_BLK : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.TMP_PRE_ERASE : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.PURGE_WAIT_ERASE_SLC : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.PURGE_WAIT_ERASE_MLC : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.DRVLOG_BLK : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.CONSTRAINT_QUEUE : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.TMP_FORCE_PTE_GC_TARGET : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.RESERVED_VB_GROUP0 : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.RESERVED_VB_GROUP1 : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.RESERVED_VB_GROUP2 : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.RESERVED_VB_GROUP3 : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.SELF_PE_ERASE_BLK : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
    project_api.VB_GROUP.CONFIG_NUM_LIST_GROUP : {"VBList":[project_api.VBListNum.OTHER], "OpenType":[project_api.OpenVBType.OTHER]},
}


def get_PCA_and_print(lun: int, lba: int, rpmb_region: int = 0) -> PCA:
    _pca = lba_to_pba(lun, lba, rpmb_region)
    pca = PCA()
    pca.from_bytes(bytearray(_pca.payload))
    logger.info(f'Lun{lun}, LBA = {lba}: Block = {(pca.b11_block_h<<8) | (pca.b10_block_l)}, mode = {pca.b4_mode}, CE = {pca.b5_ce}, Plane = {pca.b6_plane}, fPage = {pca.l12_fpage}(pageline = {pca.l12_fpage>>5}), lmu = {pca.b20_lmu}, format = {pca.b7_format}')
    return pca

def config_lun(SLC_Ratio:float = 0.5) -> tuple[int,int]:
    TLC_Ratio = 1-SLC_Ratio
    Total_AU_Count = shared.param.gGeometry.q4_total_raw_device_capacity // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
    config_descs = api.get_config_descriptors(print=True)
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
                config_descs[table].units[unit].l4_num_alloc_units = min(shared.param.gGeometry.l44_enhanced1_max_n_alloc_u, int(Total_AU_Count * SLC_Ratio))
            elif (table * 8 + unit) == 1:
                config_descs[0].units[unit].b0_lu_enable = 1
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[0].units[unit].b3_memory_type = api.MemoryType.NORMAL
                config_descs[0].units[unit].l4_num_alloc_units = int(Total_AU_Count * TLC_Ratio)
    
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
        
def print_WL_different(raw_value: Any, expect_value: Any) -> None:
    raw_fields = [
        (name, field) for name, field in raw_value.__dict__.items()
        if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
    ]
    raw_fields.sort(key=lambda kv: kv[1].start_offset)
    expect_fields = [
        (name, field) for name, field in expect_value.__dict__.items()
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
    
def check_WL_value_change(before: project_api.WearLevelingInformation, after: project_api.WearLevelingInformation, string:str, modify_value:int) -> None:
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
    if value_before + modify_value != value:
        logger.error_lb(f'check {string}')
        logger.error_fp(f'expect {string} equel to {value_before + modify_value}, but current value = {value}, result Fail!')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    
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