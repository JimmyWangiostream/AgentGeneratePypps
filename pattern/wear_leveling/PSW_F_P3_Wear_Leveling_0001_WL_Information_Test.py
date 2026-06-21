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

class ConfigCase(IntEnum):
    EM1_larger_than_30 = 0
    EM1_less_than_30 = 1

class Pattern(UFSTC):
    def pre_process(self) -> None:
        leave_inhibition_mode()
        self.fw_geometry = api.get_fw_geometry()
        self.write_record = api.get_empty_write_record()
        _, self.debug_info = api.get_debug_info()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.TestWBLun = 2
        self.config_lun(normal_list=[self.TestNormalLun, self.TestWBLun], em1_list=[self.TestEM1Lun])
        response, self.health_report_before = project_api.issue_40FE_to_read_enhanced_health_report()
        _, self.erase_cnt_buffer_backup = api.read_Xmemory(sram_address=self.debug_info.VB_list_cycle_address.value)
        pass
    
    
    def step1(self) -> None:
        logger.flow(1, 'create TLC/SLC/WB VB')
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.TestWBLun = 2
        self.config_lun(normal_list=[self.TestNormalLun, self.TestWBLun], em1_list=[self.TestEM1Lun])
        total_size = int(self.tlc_vb_size * 1.5)
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        total_size = int(self.slc_vb_size * 1.5)
        api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        total_size = int(self.slc_vb_size * 1.5)
        api.sequential_write(lun=self.TestWBLun, start_lba=0, total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        pass
    
    def step2(self) -> None:
        logger.flow(2, f'issue 4098 to get WL information and check fix value')
        _, self.wear_leveling_A = project_api.issue_4098_to_get_wear_leveling_information()
        print_object_info_ai(self.wear_leveling_A)
        self.check_format_value(self.wear_leveling_A, "data_size", api.DATA_SIZE_12K_BYTE - 4)
        self.check_format_value(self.wear_leveling_A, "size_in_byte_of_following_data", 304)
        self.check_format_value(self.wear_leveling_A, "SWLEnable", 1)
        self.check_format_value(self.wear_leveling_A, "Version_delta_Threshold_of_static_pool", 500)
        self.check_format_value(self.wear_leveling_A, "Version_delta_Threshold_of_dynamic_pool", 500)

        self.ftl_vb_list_data_before = get_VB_group()
        self.VB_dict:Dict[project_api.VBListNum, List[int]] = {}
        for vb, info in self.ftl_vb_list_data_before.items():
            group = info['group']
            VBList = self.wear_leveling_A.EC_data_of_VBs[vb].VBListNum.value
            if VBList not in self.VB_dict:
                self.VB_dict[project_api.VBListNum(VBList)] = []
            self.VB_dict[project_api.VBListNum(VBList)].append(vb)
            
            OpenType = self.wear_leveling_A.EC_data_of_VBs[vb].OpenVBType.value
            if project_api.VBListNum(VBList) not in match_dict[project_api.VB_GROUP(group)]['VBList']:
                logger.error_lb(f'check VB List Num of VU4098')
                logger.error_fp(f'VB {vb} in grouptype = {group} ({project_api.VB_GROUP(group).name}) : VBListNum = {VBList} ({project_api.VBListNum(VBList).name}) not as expected, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if project_api.OpenVBType(OpenType) not in match_dict[project_api.VB_GROUP(group)]['OpenType']:
                logger.error_lb(f'check Open VB Type of VU4098')
                logger.error_fp(f'VB {vb} in grouptype = {group} ({project_api.VB_GROUP(group).name}) : OpenVBType = {OpenType} ({project_api.OpenVBType(OpenType).name}) not as expected, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        polling_bkops_idle()
        pass
    
    def step3(self) -> None:
        logger.flow(3, f'issue C083 to set EC and set version of vb')
        response, data_payload, self.fw_configuration_by_vu = project_api.issue_408A_to_get_fw_version()
        logger.info(f'first LogVB of static pool = {self.fw_configuration_by_vu.TheFirstLogVBOfStaticPool.value}, first LogVB og dynamic pool = {self.fw_configuration_by_vu.TheFirstLogVBOfDynamicPool.value}, first LogVB of table pool = {self.fw_configuration_by_vu.TheFirstLogVBOfTableVB.value}')
        set_erase_cnt_payload = bytearray(api.DATA_SIZE_4K_BYTE)
        self.set_version_dict:Dict[int, int] = {}
        self.set_ec_dict:Dict[int, int] = {}
        for vb in range(self.fw_geometry.l52_total_vb_count):
            self.set_ec_dict[vb] = 0xFFFFFFFF
            self.set_version_dict[vb] = 0xFFFFFFFF
            if vb >= self.fw_configuration_by_vu.TheFirstLogVBOfTableVB.value:
                rand_ec = random.randint(0,300)
                set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (rand_ec).to_bytes(4, 'little')
                self.set_ec_dict[vb] = rand_ec
            if vb >= self.fw_configuration_by_vu.TheFirstLogVBOfStaticPool.value:
                rand_version = random.randint(0,300)
                self.set_version_dict[vb] = rand_version
        for hidden_vb in range(8):
            rand_ec = random.randint(0,150)
            set_erase_cnt_payload[512*4 + hidden_vb * 4 : 512*4 + (hidden_vb+1)*4] = (rand_ec).to_bytes(4, 'little')
        self.slc_partition_current_vb_version = random.randint(0,300)
        self.mlc_partition_current_vb_version = random.randint(0,300)
        api.set_ftl_version(slc_partition_current_vb_version = self.slc_partition_current_vb_version, mlc_partition_current_vb_version = self.mlc_partition_current_vb_version, set_VB_version=self.set_version_dict)
        project_api.set_all_VB_erase_count(data_payload=set_erase_cnt_payload, set_in_ram=True)
        pass

    def step4(self) -> None:
        logger.flow(4, f'issue 4098 to get WL information and check modified value')
        _, self.wear_leveling_B = project_api.issue_4098_to_get_wear_leveling_information()
        print_object_info_ai(self.wear_leveling_B)
        print_WL_different(self.wear_leveling_A, self.wear_leveling_B)
        self.check_format_value(self.wear_leveling_B, "globalVersion_of_static_pool", self.slc_partition_current_vb_version)
        self.check_format_value(self.wear_leveling_B, "globalVersion_of_dynamic_pool", self.mlc_partition_current_vb_version)
        version_of_openVB_list_dict:Dict[int, int] = {}
        for (vb, version), (vb_, ec) in zip(self.set_version_dict.items(), self.set_ec_dict.items()):
            vu_EC = self.wear_leveling_B.EC_data_of_VBs[vb].EC.value
            vu_version = self.wear_leveling_B.VER_data_of_VBs[vb].version.value
            EC_open_type = self.wear_leveling_B.EC_data_of_VBs[vb].OpenVBType.value
            VER_open_type = self.wear_leveling_B.VER_data_of_VBs[vb].open_type.value
            if self.wear_leveling_B.EC_data_of_VBs[vb].VBListNum.value == project_api.VBListNum.OTHER:
                continue
            if ec != 0xFFFFFFFF and ec != vu_EC:
                logger.error_lb(f'check EC_data_of_VBs of VU4098')
                logger.error_fp(f'expect EC_data_of_VBs of vb{vb} equal to {ec}, but current value = {vu_EC}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if version != 0xFFFFFFFF and version != vu_version:
                logger.error_lb(f'check VER_data_of_VBs of VU4098')
                logger.error_fp(f'expect VER_data_of_VBs of vb{vb} equal to {version}, but current value = {vu_version}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if EC_open_type != VER_open_type:
                logger.error_lb(f'check OpenType of VU4098')
                logger.error_fp(f'expect open_type in VER_data_of_VBs equal to EC_data_of_VBs of vb{vb}, but VER_data_of_VBs value = {VER_open_type}, EC_data_of_VBs value = {EC_open_type}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if EC_open_type != project_api.OpenVBType.OTHER:
                version_of_openVB_list_dict[EC_open_type] = vu_version
        temp = self.wear_leveling_B.version_of_open_VBs
        for opentype, version in enumerate(temp):
            except_value = version_of_openVB_list_dict.get(opentype, 0)
            if version.value != except_value:
                logger.error_lb(f'check version_of_open_VBs of VU4098')
                logger.error_fp(f'expect version_of_open_VBs of opentype{opentype} equal to {except_value}, but current value = {version.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
        self.slc_partition_current_vb_version = self.wear_leveling_B.boundaryVersion_of_static_pool.value +1
        self.mlc_partition_current_vb_version = self.wear_leveling_B.boundaryVersion_of_dynamic_pool.value +1
        api.set_ftl_version(slc_partition_current_vb_version = self.slc_partition_current_vb_version, mlc_partition_current_vb_version = self.mlc_partition_current_vb_version)
        _, self.wear_leveling_C = project_api.issue_4098_to_get_wear_leveling_information()
        print_object_info_ai(self.wear_leveling_C)
        print_WL_different(self.wear_leveling_B, self.wear_leveling_C)
        self.check_format_value(self.wear_leveling_C, "globalVersion_of_static_pool", 0)
        self.check_format_value(self.wear_leveling_C, "globalVersion_of_dynamic_pool", 0)
        pass
    
    def step5(self) -> None:
        logger.flow(5, f'issue C072 to set global WL value')
        gEC_for_Static_pool = self.wear_leveling_C.Global_Erase_Counter_of_static_pool.value +1
        gEC_for_dynamic_pool = self.wear_leveling_C.Global_Erase_Counter_of_dynamic_pool.value +1
        gEC_for_static_ICS_pool = self.wear_leveling_C.Global_Erase_Counter_of_ICS_pool.value +1
        gEC_of_Static_pool_for_open = self.wear_leveling_C.Global_Erase_Counter_of_static_pool_for_open_block.value +1
        gEC_of_dynamic_pool_for_open = self.wear_leveling_C.Global_Erase_Counter_of_dynamic_pool_for_open_block.value +1
        gEC_gap_delta_TH1_static = self.wear_leveling_C.EC_gap_delta_Threshold_TH1_of_static_pool.value +1
        gEC_gap_delta_TH1_dynamic = self.wear_leveling_C.EC_gap_delta_Threshold_TH1_of_dynamic_pool.value +1
        gEC_gap_delta_TH1_ICS = self.wear_leveling_C.EC_gap_delta_Threshold_TH1_of_ICS_pool.value +1
        gEC_gap_delta_TH2_static = self.wear_leveling_C.EC_gap_delta_Threshold_TH2_of_static_pool.value +1
        gEC_gap_delta_TH2_dynamic = self.wear_leveling_C.EC_gap_delta_Threshold_TH2_of_dynamic_pool.value +1
        gEC_gap_delta_TH2_ICS = self.wear_leveling_C.EC_gap_delta_Threshold_TH2_of_ICS_pool.value +1
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
        
        logger.flow(6, f'issue 4098 to get WL information and check modified value')
        _, self.wear_leveling_D = project_api.issue_4098_to_get_wear_leveling_information()
        print_object_info_ai(self.wear_leveling_D)
        print_WL_different(self.wear_leveling_C, self.wear_leveling_D)
        self.check_format_value(self.wear_leveling_D, "Global_Erase_Counter_of_static_pool", gEC_for_Static_pool)
        self.check_format_value(self.wear_leveling_D, "Global_Erase_Counter_of_dynamic_pool", gEC_for_dynamic_pool)
        self.check_format_value(self.wear_leveling_D, "Global_Erase_Counter_of_ICS_pool", gEC_for_static_ICS_pool)
        self.check_format_value(self.wear_leveling_D, "Global_Erase_Counter_of_static_pool_for_open_block", gEC_of_Static_pool_for_open)
        self.check_format_value(self.wear_leveling_D, "Global_Erase_Counter_of_dynamic_pool_for_open_block", gEC_of_dynamic_pool_for_open)
        self.check_format_value(self.wear_leveling_D, "EC_gap_delta_Threshold_TH1_of_static_pool", gEC_gap_delta_TH1_static)
        self.check_format_value(self.wear_leveling_D, "EC_gap_delta_Threshold_TH1_of_dynamic_pool", gEC_gap_delta_TH1_dynamic)
        self.check_format_value(self.wear_leveling_D, "EC_gap_delta_Threshold_TH1_of_ICS_pool", gEC_gap_delta_TH1_ICS)
        self.check_format_value(self.wear_leveling_D, "EC_gap_delta_Threshold_TH2_of_static_pool", gEC_gap_delta_TH2_static)
        self.check_format_value(self.wear_leveling_D, "EC_gap_delta_Threshold_TH2_of_dynamic_pool", gEC_gap_delta_TH2_dynamic)
        self.check_format_value(self.wear_leveling_D, "EC_gap_delta_Threshold_TH2_of_ICS_pool", gEC_gap_delta_TH2_ICS)
        pass
    
    def step6(self) -> None:
        logger.flow(6, f'check health report infomation')
        EC_record:Dict[int, List[int]] = {}
        ftl_vb_list = get_VB_group()
        _, wear_leveling = project_api.issue_4098_to_get_wear_leveling_information()
        response, self.health_report_after = project_api.issue_40FE_to_read_enhanced_health_report()
        print_object_info_ai(self.health_report_after)
        for vb, info in ftl_vb_list.items():
            vu_EC = wear_leveling.EC_data_of_VBs[vb].EC.value
            group = project_api.VB_GROUP(info['group'])
            partition = info['partition']
            if vu_EC == 0xFFFFF:
                continue
            if partition not in EC_record:
                EC_record[partition] = []
            EC_record[partition].append(vu_EC)
        for partition, ec_list in EC_record.items():
            max_value = max(ec_list)
            avg_value = sum(ec_list)//len(ec_list)
            min_value = min(ec_list)
            exhausted_life = avg_value * 100 // (3000 if partition == 2 else 100000)
            logger.info(f"partition:{partition}, max = {max_value}, avg = {avg_value}, min = {min_value}, exhausted_life = {exhausted_life}")
            if partition == 0: # table
                self.check_format_value(wear_leveling, "max_erase_counter_0_for_ICS_pool", max_value)
                self.check_format_value(self.health_report_after, "exhausted_life_for_slc_table_only", exhausted_life)
                self.check_format_value(self.health_report_after, "min_block_erase_count_for_slc_table", min_value)
                self.check_format_value(self.health_report_after, "max_block_erase_count_for_slc_table", max_value)
                self.check_format_value(self.health_report_after, "average_block_erase_count_for_slc_table", avg_value)
            elif partition == 1: # SLC
                self.check_format_value(wear_leveling, "max_erase_counter_0_for_Static_pool", max_value)
                self.check_format_value(self.health_report_after, "exhausted_life_for_em1", exhausted_life)
                self.check_format_value(self.health_report_after, "min_block_erase_count_for_em1", min_value)
                self.check_format_value(self.health_report_after, "max_block_erase_count_for_em1", max_value)
                self.check_format_value(self.health_report_after, "average_block_erase_count_for_em1", avg_value)
            else: # TLC
                self.check_format_value(wear_leveling, "max_erase_counter_0_for_Dynamic_pool", max_value)
                self.check_format_value(self.health_report_after, "exhausted_life_for_tlc", exhausted_life)
                self.check_format_value(self.health_report_after, "min_block_erase_count_for_tlc", min_value)
                self.check_format_value(self.health_report_after, "max_block_erase_count_for_tlc", max_value)
                self.check_format_value(self.health_report_after, "average_block_erase_count_for_tlc", avg_value)
        erase_cnt_of_vb, erase_cnt_for_hidden_physical_block, _ = project_api.get_all_VB_erase_count()
        ec_hidden_pool = sum(erase_cnt_for_hidden_physical_block)
        self.check_format_value(self.health_report_after, "ec_hidden_pool", ec_hidden_pool)
        
        data = project_api.issue_40B9_to_get_cis_block_Information()
        fw_blocks_max_ec = max(data.cis0_ec_count.value, data.cis1_ec_count.value)
        self.check_format_value(self.health_report_after, "fw_blocks_max_ec", fw_blocks_max_ec)
        bbt = project_api.get_BBT2_physical_block_information()
        pointer = project_api.get_PT_physical_block_information()
        self.check_format_value(self.health_report_after, "bbt_blocks_max_ec", bbt.erase_cnt.value)
        self.check_format_value(self.health_report_after, "pointer_blocks_max_ec", pointer.erase_cnt.value)
        pass

    def post_process(self) -> None:
        project_api.set_all_VB_erase_count(data_payload=self.erase_cnt_buffer_backup, set_in_ram=False)
        pass
    
    def check_format_value(self, before: Any, string:str, modify_value:int) -> None:
        value_before = None
        for name, field in before.__dict__.items():
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value"):
                if name == string:
                    value_before = field.value
                    break
        if value_before  != modify_value:
            logger.error_lb(f'check {string}')
            logger.error_fp(f'expect {string} equel to {modify_value}, but current value = {value_before}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
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


run = Pattern().run
if __name__ == "__main__":
    run()