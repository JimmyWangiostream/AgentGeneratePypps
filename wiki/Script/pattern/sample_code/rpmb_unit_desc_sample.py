from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def printout_rpmb_unit_desc(self, rpmb_unit_desc: api.RPMBUnitDescriptor) -> None:
        rpmb_unit_desc = cast(api.RPMBUnitDescriptor410, rpmb_unit_desc)
        logger.info(f"{rpmb_unit_desc.__class__.__name__}")
        logger.info(f"  {rpmb_unit_desc.b0_length=}")
        logger.info(f"  {rpmb_unit_desc.b1_descriptor_idn=}")
        logger.info(f"  {rpmb_unit_desc.b2_unit_index=}")
        logger.info(f"  {rpmb_unit_desc.b3_lu_enable=}")
        logger.info(f"  {rpmb_unit_desc.b4_boot_lun_id=}")
        logger.info(f"  {rpmb_unit_desc.b5_lu_write_protect=}")
        logger.info(f"  {rpmb_unit_desc.b6_lu_queue_depth=}")
        logger.info(f"  {rpmb_unit_desc.b7_psa_sensitive=}")
        logger.info(f"  {rpmb_unit_desc.b8_memory_type=}")
        region_en_str = 'region0'
        if api.CHK_BIT(rpmb_unit_desc.b9_rpmb_region_enable, 1):
            region_en_str += ', region1'
        if api.CHK_BIT(rpmb_unit_desc.b9_rpmb_region_enable, 2):
            region_en_str += ', region2'
        if api.CHK_BIT(rpmb_unit_desc.b9_rpmb_region_enable, 3):
            region_en_str += ', region3'
        if api.CHK_BIT(rpmb_unit_desc.b9_rpmb_region_enable, 4):
            region_en_str += ', AdvRPMB'
        if api.CHK_BIT(rpmb_unit_desc.b9_rpmb_region_enable, 5):
            region_en_str += ', RPMBPurge'
        logger.info(f"  {rpmb_unit_desc.b9_rpmb_region_enable=} ({region_en_str})")
        logger.info(f"  {rpmb_unit_desc.b10_logical_block_size=}")
        logger.info(f"  {rpmb_unit_desc.q11_logical_block_count=}")
        logger.info(f"  {rpmb_unit_desc.b19_rpmb_region0_size=}")
        logger.info(f"  {rpmb_unit_desc.b20_rpmb_region1_size=}")
        logger.info(f"  {rpmb_unit_desc.b21_rpmb_region2_size=}")
        logger.info(f"  {rpmb_unit_desc.b22_rpmb_region3_size=}")
        logger.info(f"  {rpmb_unit_desc.b23_provisioning_type=}")
        logger.info(f"  {rpmb_unit_desc.q24_phy_mem_resource_count=}")

    def step1(self) -> None:
        logger.info("Get RPMB Unit Descriptor")
        desc = api.get_rpmb_unit_descriptor()
        self.printout_rpmb_unit_desc(desc)

    def post_process(self) -> None:
        pass

run = Pattern().run
if __name__ == "__main__":
    run()