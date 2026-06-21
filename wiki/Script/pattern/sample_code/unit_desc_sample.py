from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def printout_unit_desc(self, unit_desc: api.UnitDescriptor) -> None:
        unit_desc = cast(api.UnitDescriptor410, unit_desc)
        logger.info(f"{unit_desc.__class__.__name__}")
        logger.info(f"  {unit_desc.b0_length=}")
        logger.info(f"  {unit_desc.b1_descriptor_idn=}")
        logger.info(f"  {unit_desc.b2_unit_index=}")
        logger.info(f"  {unit_desc.b3_lu_enable=} ({api.LUNEnable(unit_desc.b3_lu_enable).name})")
        logger.info(f"  {unit_desc.b4_boot_lun_id=} ({api.BootLUNID(unit_desc.b4_boot_lun_id).name})")
        logger.info(f"  {unit_desc.b5_lu_write_protect=} ({api.LUNWriteProtect(unit_desc.b5_lu_write_protect).name})")
        logger.info(f"  {unit_desc.b6_lu_queue_depth=}")
        logger.info(f"  {unit_desc.b7_psa_sensitive=}")
        logger.info(f"  {unit_desc.b8_memory_type=} ({api.MemoryType(unit_desc.b8_memory_type).name})")
        logger.info(f"  {unit_desc.b9_data_reliability=} ({api.DataReliability(unit_desc.b9_data_reliability).name})")
        logger.info(f"  {unit_desc.b10_logical_block_size=}")
        logger.info(f"  {unit_desc.q11_logical_block_count=}")
        logger.info(f"  {unit_desc.l19_erase_block_size=}")
        logger.info(f"  {unit_desc.b23_provisioning_type=} ({api.ProvisioningType(unit_desc.b23_provisioning_type).name})")
        logger.info(f"  {unit_desc.q24_phy_mem_resource_count=}")
        logger.info(f"  {unit_desc.w32_context_capabilities=}")
        logger.info(f"  {unit_desc.b34_large_unit_granularity_m1=}")
        logger.info(f"  {unit_desc.w35_lu_max_active_hpb_regions=}")
        logger.info(f"  {unit_desc.w37_hpb_pinned_region_start_idx=}")
        logger.info(f"  {unit_desc.w39_num_hpb_pinned_regions=}")
        logger.info(f"  {unit_desc.l41_lu_num_write_booster_buffer_alloc_units=}")

    def step1(self) -> None:
        desc_list = []
        for unit_idx in range(32):
            logger.info(f"Get Unit Descriptor [{unit_idx}]")
            desc_list.append(api.get_unit_descriptor(unit_idx))
        for desc in desc_list:
            self.printout_unit_desc(desc)

    def post_process(self) -> None:
        pass

run = Pattern().run
if __name__ == "__main__":
    run()