from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def printout_geometry_desc(self, geometry_desc: api.GeometryDescriptor) -> None:
        geometry_desc = cast(api.GeometryDescriptor410, geometry_desc)
        logger.info(f"{geometry_desc.__class__.__name__}")
        logger.info(f"  {geometry_desc.b0_length=}")
        logger.info(f"  {geometry_desc.b1_descriptor_idn=}")
        logger.info(f"  {geometry_desc.b2_media_technology=}")
        logger.info(f"  {geometry_desc.q4_total_raw_device_capacity=}")
        logger.info(f"  {geometry_desc.b12_max_number_lu=}")
        logger.info(f"  {geometry_desc.l13_segment_size=}")
        logger.info(f"  {geometry_desc.b17_allocation_unit_size=}")
        logger.info(f"  {geometry_desc.b18_min_addr_block_size=}")
        logger.info(f"  {geometry_desc.b19_optimal_read_block_size=}")
        logger.info(f"  {geometry_desc.b20_optimal_write_block_size=}")
        logger.info(f"  {geometry_desc.b21_max_in_buffer_size=}")
        logger.info(f"  {geometry_desc.b22_max_out_buffer_size=}")
        logger.info(f"  {geometry_desc.b23_rpmb_read_write_size=}")
        logger.info(f"  {geometry_desc.b24_dynamic_capacity_resource_policy=}")
        logger.info(f"  {geometry_desc.b25_data_ordering=}")
        logger.info(f"  {geometry_desc.b26_max_context_id_number=}")
        logger.info(f"  {geometry_desc.b27_sys_data_tag_unit_size=}")
        logger.info(f"  {geometry_desc.b28_sys_data_tag_res_size=}")
        logger.info(f"  {geometry_desc.b29_supported_sec_r_types=}")
        logger.info(f"  {geometry_desc.w30_supported_memory_types=}")
        logger.info(f"  {geometry_desc.l32_system_code_max_n_alloc_u=}")
        logger.info(f"  {geometry_desc.w36_system_code_cap_adj_fac=}")
        logger.info(f"  {geometry_desc.l38_non_persist_max_n_alloc_u=}")
        logger.info(f"  {geometry_desc.w42_non_persist_cap_adj_fac=}")
        logger.info(f"  {geometry_desc.l44_enhanced1_max_n_alloc_u=}")
        logger.info(f"  {geometry_desc.w48_enhanced1_cap_adj_fac=}")
        logger.info(f"  {geometry_desc.l50_enhanced2_max_n_alloc_u=}")
        logger.info(f"  {geometry_desc.w54_enhanced2_cap_adj_fac=}")
        logger.info(f"  {geometry_desc.l56_enhanced3_max_n_alloc_u=}")
        logger.info(f"  {geometry_desc.w60_enhanced3_cap_adj_fac=}")
        logger.info(f"  {geometry_desc.l62_enhanced4_max_n_alloc_u=}")
        logger.info(f"  {geometry_desc.w66_enhanced4_cap_adj_fac=}")
        logger.info(f"  {geometry_desc.l68_optimal_logical_block_size=}")
        logger.info(f"  {geometry_desc.l79_write_booster_buffer_max_n_alloc_units=}")
        logger.info(f"  {geometry_desc.b83_device_max_write_booster_lus=}")
        logger.info(f"  {geometry_desc.b84_write_booster_buffer_cap_adj_fac=}")
        logger.info(f"  {geometry_desc.b85_supported_write_booster_buffer_user_space_reduction_types=}")
        logger.info(f"  {geometry_desc.b86_supported_write_booster_buffer_types=}")

    def step1(self) -> None:
        logger.info("Get Geometry Descriptor")
        desc = api.get_geometry_descriptor()
        self.printout_geometry_desc(desc)

    def step2(self) -> None:
        lun_amount = api.get_max_number_of_lun()
        logger.info(f"Get Max number of lun = {lun_amount}")

        desc = cast(api.GeometryDescriptor410, api.get_geometry_descriptor())
        out_of_order_type = api.SupportedOutOfOrderDataTransfer(desc.b25_data_ordering)
        logger.info(f"Get Out-of-order type: {out_of_order_type.value} ({out_of_order_type.name})")

        support_memory_types = []
        if desc.w30_supported_memory_types & api.SupportedMemoryType.NORMAL:
            support_memory_types.append(api.SupportedMemoryType.NORMAL.name)
        if desc.w30_supported_memory_types & api.SupportedMemoryType.SYSTEM_CODE:
            support_memory_types.append(api.SupportedMemoryType.SYSTEM_CODE.name)
        if desc.w30_supported_memory_types & api.SupportedMemoryType.NON_PERSISTENT:
            support_memory_types.append(api.SupportedMemoryType.NON_PERSISTENT.name)
        if desc.w30_supported_memory_types & api.SupportedMemoryType.ENHANCED_1:
            support_memory_types.append(api.SupportedMemoryType.ENHANCED_1.name)
        if desc.w30_supported_memory_types & api.SupportedMemoryType.ENHANCED_2:
            support_memory_types.append(api.SupportedMemoryType.ENHANCED_2.name)
        if desc.w30_supported_memory_types & api.SupportedMemoryType.ENHANCED_3:
            support_memory_types.append(api.SupportedMemoryType.ENHANCED_3.name)
        if desc.w30_supported_memory_types & api.SupportedMemoryType.ENHANCED_4:
            support_memory_types.append(api.SupportedMemoryType.ENHANCED_4.name)
        if desc.w30_supported_memory_types & api.SupportedMemoryType.RPMB:
            support_memory_types.append(api.SupportedMemoryType.RPMB.name)
        logger.info(f"Support memory types: {', '.join(support_memory_types)}")

    def post_process(self) -> None:
        pass

run = Pattern().run
if __name__ == "__main__":
    run()