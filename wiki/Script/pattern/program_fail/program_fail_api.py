from Script import api
from Script.api.ufs_api.vendor_cmd.functions import *
from typing import Dict, List, cast


def calculate_bbt(payload: bytearray) -> List[Dict[str, int]]:
    bbt_map = []
    bbt_cnt = int.from_bytes(payload[0:4], byteorder='little')

    for index in range(0, bbt_cnt, 1):
        BB_info = payload[(index * 8) + 8:(index * 8) + 16]
        BB_Block = int.from_bytes(BB_info[0:3], byteorder='little')
        BB_CE_Plane = int.from_bytes(BB_info[3:4], byteorder='little') >> 3
        BB_CE = BB_CE_Plane // 6
        BB_Plane = BB_CE_Plane % 6

        bbt_map.append({'Block': BB_Block, 'CE': BB_CE, 'Plane': BB_Plane})

    return bbt_map

def config_lun(normal_list: List[int], em1_list: List[int]) -> None:
    selector = 0x00
    length = 0xE6
    Total_AU_Count = shared.param.gGeometry.q4_total_raw_device_capacity // (
                shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
    EM1_total_AU = min(shared.param.gGeometry.l44_enhanced1_max_n_alloc_u,
                        Total_AU_Count // (len(normal_list) + len(em1_list)) * len(em1_list))
    normal_total_AU = Total_AU_Count // (len(normal_list) + len(em1_list)) * len(normal_list)
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
        desc.header.l18_num_shared_write_booster_buffer_alloc_units = shared.param.gGeometry.l79_write_booster_buffer_max_n_alloc_units if index == 0 else 0

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
    unit_desc_idxes: List[int] = []
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
