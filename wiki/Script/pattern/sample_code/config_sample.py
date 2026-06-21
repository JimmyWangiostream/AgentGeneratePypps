from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger


class Pattern(UFSTC):
    def pre_process(self) -> None:
        logger.info(api.CommonPath.root)
        logger.info(api.CommonPath.development_report)
        logger.info(api.CommonPath.ini)
        logger.info(api.CommonPath.mp_tool)
        logger.info(api.CommonPath.tcsp)
        logger.info(api.CommonPath.report)
        pass

    def printout_config_desc_header(self, header: api.ConfigDescriptorHeader) -> None:
        header = cast(api.ConfigDescriptorHeader410, header)
        logger.info(f"{header.__class__.__name__}")
        logger.info(f"  {header.b0_length=}")
        logger.info(f"  {header.b1_descriptor_idn=}")
        logger.info(f"  {header.b2_conf_desc_continue=}")
        logger.info(f"  {header.b3_boot_enable=}")
        logger.info(f"  {header.b4_descr_access_en=}")
        logger.info(f"  {header.b5_init_power_mode=}")
        logger.info(f"  {header.b6_high_priority_lun=}")
        logger.info(f"  {header.b7_secure_removal_type=}")
        logger.info(f"  {header.b8_init_active_icc_level=}")
        logger.info(f"  {header.w9_periodic_rtc_update=}")
        logger.info(f"  {header.b11_hpb_control=}")
        logger.info(f"  {header.b12_rpmb_region_enable=}")
        logger.info(f"  {header.b13_rpmb_region1_size=}")
        logger.info(f"  {header.b14_rpmb_region2_size=}")
        logger.info(f"  {header.b15_rpmb_region3_size=}")
        logger.info(f"  {header.b16_write_booster_buffer_preserve_user_space_en=}")
        logger.info(f"  {header.b17_write_booster_buffer_type=}")
        logger.info(f"  {header.l18_num_shared_write_booster_buffer_alloc_units=}")

    def printout_config_desc_unit(self, unit: api.ConfigDescriptorUnit) -> None:
        unit = cast(api.ConfigDescriptorUnit410, unit)
        logger.info(f"{unit.__class__.__name__}")
        logger.info(f"  {unit.b0_lu_enable=}")
        logger.info(f"  {unit.b1_boot_lun_id=}")
        logger.info(f"  {unit.b2_lu_write_protect=}")
        logger.info(f"  {unit.b3_memory_type=}")
        logger.info(f"  {unit.l4_num_alloc_units=}")
        logger.info(f"  {unit.b8_data_reliability=}")
        logger.info(f"  {unit.b9_logical_block_size=}")
        logger.info(f"  {unit.b10_provisioning_type=}")
        logger.info(f"  {unit.w11_context_capabilities=}")
        logger.info(f"  {unit.w16_lu_max_active_hpb_region=}")
        logger.info(f"  {unit.w18_hpb_pinned_region_start_idx=}")
        logger.info(f"  {unit.w20_num_hpb_pinned_regions=}")
        logger.info(f"  {unit.l22_lu_num_write_booster_buffer_alloc_units=}")

    def step1(self) -> None:
        logger.info("Set Configuration Descriptors")
        selector = 0x00
        length = 0xE6
        for index in range(4):
            cmd = ExecuteCMD.WriteDescriptor()
            cmd.assign(api.DescriptorIDN.CONFIGURATION, index, selector, length)

            desc = api.ConfigDescriptor410()
            desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            desc.header.b3_boot_enable = api.BootEnable.BOOT_ENABLE
            desc.header.b4_descr_access_en = api.DescrAccessEn.DISABLE
            desc.header.b5_init_power_mode = api.InitPowerMode.ACTIVE
            desc.header.b6_high_priority_lun = api.HighPriorityLUN.ALL_LUN_SAME_PRIORITY
            desc.header.b7_secure_removal_type = api.SecureRemovalType.BY_PHYSICAL_ERASE
            desc.header.b8_init_active_icc_level = api.InitActiveICCLevel.LVL_00
            desc.header.w9_periodic_rtc_update = 0
            desc.header.b11_hpb_control = 0
            desc.header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE | api.RPMBRegionEnable.REGION_1_ENABLE | api.RPMBRegionEnable.REGION_2_ENABLE | api.RPMBRegionEnable.REGION_3_ENABLE
            desc.header.b13_rpmb_region1_size = 8
            desc.header.b14_rpmb_region2_size = 8
            desc.header.b15_rpmb_region3_size = 8
            desc.header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.DISABLE
            desc.header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.DEDICATED
            desc.header.l18_num_shared_write_booster_buffer_alloc_units = 0

            for unit_idx in range(8):
                if index == 0 and unit_idx == 0:  # LUN 0
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.NORMAL
                    desc.units[unit_idx].l4_num_alloc_units = 60016
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == 1:  # LUN 1
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_A
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = 100
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == 2:  # LUN 2
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_B
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = 100
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == 3:  # LUN 3
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.NORMAL
                    desc.units[unit_idx].l4_num_alloc_units = 200
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

    def step2(self) -> None:
        logger.info("Get Configuration Descriptors")
        cfg_desc_list = api.get_config_descriptors()
        for cfg_desc in cfg_desc_list:
            cfg_desc = cast(api.ConfigDescriptor410, cfg_desc)
            logger.info("")
            self.printout_config_desc_header(cfg_desc.header)
            for unit_desc in cfg_desc.units:
                self.printout_config_desc_unit(unit_desc)

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()