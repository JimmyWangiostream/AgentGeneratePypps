import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.wear_leveling.mutual_fun import *
from Script.project_api.functions import print_object_info_ai

class Trigger_Case(IntEnum):
    is_cold = 0
    is_prior_round = 1
    is_MAX_VALUE = 2
class GC_pool(IntEnum):
    Static = 1
    Dynamic = 2

class ThresholdCase(IntEnum):
    TH1 = 0
    TH2 = 1
class Pattern(UFSTC):
    def pre_process(self) -> None:
        leave_inhibition_mode()
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.TestWBLun = 2
        self.config_lun(normal_list=[self.TestNormalLun, self.TestWBLun], em1_list=[self.TestEM1Lun])
        self.fw_geometry = api.get_fw_geometry()
        self.write_record = api.get_empty_write_record()
        _, self.debug_info = api.get_debug_info()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        _, self.erase_cnt_buffer_backup = api.read_Xmemory(sram_address=self.debug_info.VB_list_cycle_address.value)
        self.MAX_VALUE = {GC_pool.Static: 0x7FFF, GC_pool.Dynamic: 0x7FFF}
        pass
    
    def step1(self) -> None:        
        for GC_case in [
            project_api.VBListNum.USED_BLK_POOL_EM1,
            project_api.VBListNum.USED_BLK_POOL_TLC,
            project_api.VBListNum.USED_BLK_POOL_TLC_WB,
        ]:
            for trigger_case in Trigger_Case:
                for threshold_case in ThresholdCase:
                    set_erase_cnt_payload = bytearray(api.DATA_SIZE_4K_BYTE)
                    project_api.set_all_VB_erase_count(data_payload=set_erase_cnt_payload, set_in_ram=True)
                    logger.info(f'=========== Test GC {GC_case.name}, trigger_case {trigger_case.name}, threshold case {threshold_case.name} ===========')
                    api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                    logger.flow(1, f'Config lun')
                    self.config_lun(normal_list=[self.TestNormalLun, self.TestWBLun], em1_list=[self.TestEM1Lun])
                    
                    logger.flow(2, f'write to create VB')
                    lba = 0
                    chunk_size = api.BLOCK4K_SIZE_128M_BYTE
                    new_group = GC_case
                    if GC_case == project_api.VBListNum.USED_BLK_POOL_EM1:
                        pool = GC_pool.Static
                        free_group = project_api.VBListNum.FREE_BLK_QUEUE_EM1
                        lun = self.TestEM1Lun
                        vbsize = self.slc_vb_size
                    else:
                        pool = GC_pool.Dynamic
                        free_group = project_api.VBListNum.FREE_BLK_QUEUE_TLC
                        if GC_case == project_api.VBListNum.USED_BLK_POOL_TLC:
                            lun = self.TestNormalLun
                            vbsize = self.tlc_vb_size
                        elif GC_case == project_api.VBListNum.USED_BLK_POOL_TLC_WB:
                            new_group = project_api.VBListNum.USED_BLK_POOL_TLC
                            lun = self.TestWBLun
                            vbsize = self.slc_vb_size
                            api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                    total_size = vbsize * 3
                    api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunk_size, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                    lba += total_size
                    # api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                        
                    logger.flow(3, f'issue 4098 to get WL information')
                    self.VB_dict:Dict[project_api.VBListNum, List[int]] = {}
                    _, self.wear_leveling_A = project_api.issue_4098_to_get_wear_leveling_information()
                    print_object_info_ai(self.wear_leveling_A)
                    for vb in range(self.fw_geometry.l52_total_vb_count):
                        EC_data = self.wear_leveling_A.EC_data_of_VBs[vb]
                        VER_data = self.wear_leveling_A.VER_data_of_VBs[vb]
                        logger.info(f'wear_leveling_A VB: {vb}, EC = {EC_data.EC.value} VBListNum = {EC_data.VBListNum.value} ({project_api.VBListNum(EC_data.VBListNum.value).name}), OpenType = {EC_data.OpenVBType.value} ({project_api.OpenVBType(EC_data.OpenVBType.value).name}), Version = {VER_data.version.value}, force_bit = {VER_data.force_bit.value}, IsDfgSrc = {EC_data.IsDfgSrc.value}')
                    for vb in range(self.fw_geometry.l52_total_vb_count):
                        VBList = self.wear_leveling_A.EC_data_of_VBs[vb].VBListNum.value
                        if VBList not in self.VB_dict:
                            self.VB_dict[project_api.VBListNum(VBList)] = []
                        self.VB_dict[project_api.VBListNum(VBList)].append(vb)
                        
                    # gEC_for_Static_pool = self.wear_leveling_A.Global_Erase_Counter_of_static_pool.value
                    # gEC_for_dynamic_pool = self.wear_leveling_A.Global_Erase_Counter_of_dynamic_pool.value
                    # gEC_for_static_ICS_pool = self.wear_leveling_A.Global_Erase_Counter_of_ICS_pool.value
                    # gEC_of_Static_pool_for_open = self.wear_leveling_A.Global_Erase_Counter_of_static_pool_for_open_block.value
                    # gEC_of_dynamic_pool_for_open = self.wear_leveling_A.Global_Erase_Counter_of_dynamic_pool_for_open_block.value
                    gEC_for_Static_pool = 0
                    gEC_for_dynamic_pool = 0
                    gEC_for_static_ICS_pool = 0
                    gEC_of_Static_pool_for_open = 0
                    gEC_of_dynamic_pool_for_open = 0
                    gEC_gap_delta_TH1_static = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_static_pool.value
                    gEC_gap_delta_TH1_dynamic = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_dynamic_pool.value
                    gEC_gap_delta_TH1_ICS = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_ICS_pool.value
                    gEC_gap_delta_TH2_static = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_static_pool.value
                    gEC_gap_delta_TH2_dynamic = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_dynamic_pool.value
                    gEC_gap_delta_TH2_ICS = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_ICS_pool.value
                    if pool == GC_pool.Static:
                        gEC_for_Static_pool = self.wear_leveling_A.EC_Threshold_of_static_pool.value + 1
                        if threshold_case == ThresholdCase.TH1:
                            set_ec = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_static_pool.value + 1
                        else:
                            set_ec = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_static_pool.value + 1
                    else:
                        gEC_for_dynamic_pool = self.wear_leveling_A.EC_Threshold_of_dynamic_pool.value + 1
                        if threshold_case == ThresholdCase.TH1:
                            set_ec = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_dynamic_pool.value + 1
                        else:
                            set_ec = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_dynamic_pool.value + 1
                    
                    logger.flow(5, f'issue C083 to set {GC_case.name} EC = 0 and issue C072 to set static_wear_leveling global EC')
                    set_version_dict:Dict[int, int] = {}
                    for vb in range(self.fw_geometry.l52_total_vb_count):
                        set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (set_ec+1).to_bytes(4, 'little')
                        set_version_dict[vb] = 0
                    for ListNum, vb_list in self.VB_dict.items():
                        if ListNum == GC_case:
                            vb = vb_list[0]
                            set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (0).to_bytes(4, 'little')
                            if pool == GC_pool.Static:
                                set_version_dict[vb] = self.wear_leveling_A.globalVersion_of_static_pool.value+1
                            else:
                                set_version_dict[vb] = self.wear_leveling_A.globalVersion_of_dynamic_pool.value+1
                            source_vb = vb
                            temp = self.VB_dict[free_group].copy()
                            random.shuffle(temp)
                            vb = temp[0]
                            set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (set_ec).to_bytes(4, 'little')
                            target_vb = vb
                            break

                    if trigger_case == Trigger_Case.is_cold:
                        if pool == GC_pool.Static:
                            slc_partition_current_vb_version = self.wear_leveling_A.globalVersion_of_static_pool.value + self.wear_leveling_A.Version_delta_Threshold_of_static_pool.value + 1
                            api.set_ftl_version(slc_partition_current_vb_version = slc_partition_current_vb_version)
                        else:
                            mlc_partition_current_vb_version = self.wear_leveling_A.globalVersion_of_dynamic_pool.value + self.wear_leveling_A.Version_delta_Threshold_of_dynamic_pool.value + 1
                            api.set_ftl_version(mlc_partition_current_vb_version = mlc_partition_current_vb_version)
                    elif trigger_case == Trigger_Case.is_MAX_VALUE:
                        partition_current_vb_version = self.MAX_VALUE[pool]
                        if pool == GC_pool.Static:
                            api.set_ftl_version(slc_partition_current_vb_version = partition_current_vb_version)
                        else:
                            api.set_ftl_version(mlc_partition_current_vb_version = partition_current_vb_version)
                    else:
                        api.set_ftl_version(set_VB_version=set_version_dict)
                    
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
                    project_api.set_all_VB_erase_count(data_payload=set_erase_cnt_payload, set_in_ram=True)

                    _, self.wear_leveling_C = project_api.issue_4098_to_get_wear_leveling_information()
                    print_object_info_ai(self.wear_leveling_C)
                    logger.info(f'Source VB = {source_vb}, Target VB = {target_vb}')
                    for vb in range(self.fw_geometry.l52_total_vb_count):
                        EC_data = self.wear_leveling_C.EC_data_of_VBs[vb]
                        VER_data = self.wear_leveling_C.VER_data_of_VBs[vb]
                        logger.info(f'wear_leveling_C VB: {vb}, EC = {EC_data.EC.value} VBListNum = {EC_data.VBListNum.value} ({project_api.VBListNum(EC_data.VBListNum.value).name}), OpenType = {EC_data.OpenVBType.value} ({project_api.OpenVBType(EC_data.OpenVBType.value).name}), Version = {VER_data.version.value}, force_bit = {VER_data.force_bit.value}, IsDfgSrc = {EC_data.IsDfgSrc.value}')

                    if trigger_case == Trigger_Case.is_MAX_VALUE:
                        if pool == GC_pool.Static:
                            if self.wear_leveling_C.globalVersion_of_static_pool.value != 0:
                                logger.error_lb(f'check globalVersion_of_static_pool after setting to {self.MAX_VALUE[pool]} (MAX_VALUE)')
                                logger.error_fp(f'expect globalVersion_of_static_pool = 0, but current value = {self.wear_leveling_C.globalVersion_of_static_pool.value}, result Fail!')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        else:
                            if self.wear_leveling_C.globalVersion_of_dynamic_pool.value != 0:
                                logger.error_lb(f'check globalVersion_of_dynamic_pool after setting to {self.MAX_VALUE[pool]} (MAX_VALUE)')
                                logger.error_fp(f'expect globalVersion_of_dynamic_pool = 0, but current value = {self.wear_leveling_C.globalVersion_of_dynamic_pool.value}, result Fail!')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                            
                    logger.flow(8, f'polling BKOPS idle')
                    polling_bkops_idle()
                    
                    logger.flow(9, f'issue 4098 to get WL information and check counter')
                    _, self.wear_leveling_D = project_api.issue_4098_to_get_wear_leveling_information()
                    for vb in range(self.fw_geometry.l52_total_vb_count):
                        EC_data = self.wear_leveling_D.EC_data_of_VBs[vb]
                        VER_data = self.wear_leveling_D.VER_data_of_VBs[vb]
                        logger.info(f'wear_leveling_D VB: {vb}, EC = {EC_data.EC.value} VBListNum = {EC_data.VBListNum.value} ({project_api.VBListNum(EC_data.VBListNum.value).name}), OpenType = {EC_data.OpenVBType.value} ({project_api.OpenVBType(EC_data.OpenVBType.value).name}), Version = {VER_data.version.value}, force_bit = {VER_data.force_bit.value}, IsDfgSrc = {EC_data.IsDfgSrc.value}')
                    print_object_info_ai(self.wear_leveling_D)
                    if self.wear_leveling_D.VER_data_of_VBs[source_vb].force_bit.value != 1:
                        logger.error_lb(f'check force_bit after pick WL GC')
                        logger.error_fp(f'expect force_bit of source_vb {source_vb} = 1, but current value = {self.wear_leveling_D.VER_data_of_VBs[source_vb].force_bit.value}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL

                    print_WL_different(self.wear_leveling_A, self.wear_leveling_D)
                    if pool == GC_pool.Static:
                        check_WL_value_change(self.wear_leveling_A, self.wear_leveling_D, 'totalSWLGCTriggerCount_of_static_pool', 1)
                        old_done = self.wear_leveling_A.totalSWLGCMissCount_of_static_pool.value + self.wear_leveling_A.totalSWLGCDoneCount_of_static_pool.value
                        new_done = self.wear_leveling_D.totalSWLGCMissCount_of_static_pool.value + self.wear_leveling_D.totalSWLGCDoneCount_of_static_pool.value
                        if old_done != new_done -1:
                            logger.error_lb(f'check Done/Miss Count after refresh')
                            logger.error_fp(f'expect totalSWLGCMissCount_of_static_pool + totalSWLGCDoneCount_of_static_pool increase, but current value = {new_done}, before value = {old_done}, result Fail!')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        if threshold_case == ThresholdCase.TH1:
                            check_WL_value_change(self.wear_leveling_A, self.wear_leveling_D, 'totalSWLBGGCTriggerCount_of_static_pool', 1)
                        else:
                            check_WL_value_change(self.wear_leveling_A, self.wear_leveling_D, 'totalSWLFGGCTriggerCount_of_static_pool', 1)
                    else:
                        check_WL_value_change(self.wear_leveling_A, self.wear_leveling_D, 'totalSWLGCTriggerCount_of_dynamic_pool', 1)
                        old_done = self.wear_leveling_A.totalSWLGCMissCount_of_dynamic_pool.value + self.wear_leveling_A.totalSWLGCDoneCount_of_dynamic_pool.value
                        new_done = self.wear_leveling_D.totalSWLGCMissCount_of_dynamic_pool.value + self.wear_leveling_D.totalSWLGCDoneCount_of_dynamic_pool.value
                        if old_done != new_done -1:
                            logger.error_lb(f'check Done/Miss Count after refresh')
                            logger.error_fp(f'expect totalSWLGCMissCount_of_dynamic_pool + totalSWLGCDoneCount_of_dynamic_pool increase, but current value = {new_done}, before value = {old_done}, result Fail!')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        if threshold_case == ThresholdCase.TH1:
                            check_WL_value_change(self.wear_leveling_A, self.wear_leveling_D, 'totalSWLBGGCTriggerCount_of_dynamic_pool', 1)
                        else:
                            check_WL_value_change(self.wear_leveling_A, self.wear_leveling_D, 'totalSWLFGGCTriggerCount_of_dynamic_pool', 1)
                    
                    for vb in range(self.fw_geometry.l52_total_vb_count):
                        EC_data_before = self.wear_leveling_A.EC_data_of_VBs[vb]
                        EC_data_after = self.wear_leveling_D.EC_data_of_VBs[vb]
                        if EC_data_before.VBListNum.value != EC_data_after.VBListNum.value or \
                            EC_data_before.OpenVBType.value != EC_data_after.OpenVBType.value:
                            logger.info(f'Before: VB: {vb}, EC = {EC_data_before.EC.value} VBListNum = {EC_data_before.VBListNum.value} ({project_api.VBListNum(EC_data_before.VBListNum.value).name}), OpenType = {EC_data_before.OpenVBType.value} ({project_api.OpenVBType(EC_data_before.OpenVBType.value).name}), IsDfgSrc = {EC_data_before.IsDfgSrc.value}')
                            logger.info(f'After:  VB: {vb}, EC = {EC_data_after.EC.value} VBListNum = {EC_data_after.VBListNum.value} ({project_api.VBListNum(EC_data_after.VBListNum.value).name}), OpenType = {EC_data_after.OpenVBType.value} ({project_api.OpenVBType(EC_data_after.OpenVBType.value).name}), IsDfgSrc = {EC_data_after.IsDfgSrc.value}')
                            logger.info(f'==================================')
                        if vb == source_vb:
                            if EC_data_after.VBListNum.value != free_group or EC_data_before.VBListNum.value != GC_case:
                                logger.error_lb(f'check VB {vb} group change after refresh')
                                logger.error_fp(f'expect VB {vb}, EC = {EC_data_after.EC.value} from {GC_case.name} to {free_group.name}, but current is {project_api.VBListNum(EC_data_before.VBListNum.value).name} to {project_api.VBListNum(EC_data_after.VBListNum.value).name}, result Fail!')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                            if EC_data_after.IsDfgSrc.value != 1:
                                logger.error_lb(f'check VB {vb} group change after refresh')
                                logger.error_fp(f'expect VB {vb}, IsDfgSrc = 1, but current value is {EC_data_after.IsDfgSrc.value}, result Fail!')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                        if vb == target_vb:
                            if EC_data_after.VBListNum.value != new_group or EC_data_before.VBListNum.value != free_group:
                                logger.error_lb(f'check VB {vb} group change after refresh')
                                logger.error_fp(f'expect VB {vb}, EC = {EC_data_after.EC.value} from {free_group.name} to {new_group.name}, but current is {project_api.VBListNum(EC_data_before.VBListNum.value).name} to {project_api.VBListNum(EC_data_after.VBListNum.value).name}, result Fail!')
                                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    pass
        pass
    
    
        
    def config_lun(self, normal_list:List[int], em1_list:List[int]) -> None:
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
    
    def post_process(self) -> None:
        project_api.set_all_VB_erase_count(data_payload=self.erase_cnt_buffer_backup, set_in_ram=False)
        pass

run = Pattern().run
if __name__ == "__main__":
    run()