import struct
from Script.api.struct_helper import *
from Script.api.ufs_api.defines.enum_define import DescriptorIDN


# Define empty classes for inheritance and type hint usage
class GeometryDescriptor(PacketParserABC):
    def from_bytes(self, payload: bytearray) -> None:
        pass

########################### UFS Specs 3.1 ###########################

class GeometryDescriptor310(GeometryDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0x57
        self.b1_descriptor_idn = DescriptorIDN.GEOMETRY
        self.b2_media_technology = 0
        self.b3_rsvd = 0
        self.q4_total_raw_device_capacity = 0
        self.b12_max_number_lu = 0
        self.l13_segment_size = 0
        self.b17_allocation_unit_size = 0
        self.b18_min_addr_block_size = 0
        self.b19_optimal_read_block_size = 0
        self.b20_optimal_write_block_size = 0
        self.b21_max_in_buffer_size = 0
        self.b22_max_out_buffer_size = 0
        self.b23_rpmb_read_write_size = 0
        self.b24_dynamic_capacity_resource_policy = 0
        self.b25_data_ordering = 0
        self.b26_max_context_id_number = 0
        self.b27_sys_data_tag_unit_size = 0
        self.b28_sys_data_tag_res_size = 0
        self.b29_supported_sec_r_types = 0
        self.w30_supported_memory_types = 0
        self.l32_system_code_max_n_alloc_u = 0
        self.w36_system_code_cap_adj_fac = 0
        self.l38_non_persist_max_n_alloc_u = 0
        self.w42_non_persist_cap_adj_fac = 0
        self.l44_enhanced1_max_n_alloc_u = 0
        self.w48_enhanced1_cap_adj_fac = 0
        self.l50_enhanced2_max_n_alloc_u = 0
        self.w54_enhanced2_cap_adj_fac = 0
        self.l56_enhanced3_max_n_alloc_u = 0
        self.w60_enhanced3_cap_adj_fac = 0
        self.l62_enhanced4_max_n_alloc_u = 0
        self.w66_enhanced4_cap_adj_fac = 0
        self.l68_optimal_logical_block_size = 0
        self.b72_rsvd = 0
        self.l73_rsvd = 0
        self.w77_rsvd = 0
        self.l79_write_booster_buffer_max_n_alloc_units = 0
        self.b83_device_max_write_booster_lus = 0
        self.b84_write_booster_buffer_cap_adj_fac = 0
        self.b85_supported_write_booster_buffer_user_space_reduction_types = 0
        self.b86_supported_write_booster_buffer_types = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBQBLBBBBBBBBBBBBBHLHLHLHLHLHLHLBLHLBBBB', payload[0:87])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_media_technology = unpacked_data[2]
        self.b3_rsvd = unpacked_data[3]
        self.q4_total_raw_device_capacity = unpacked_data[4]
        self.b12_max_number_lu = unpacked_data[5]
        self.l13_segment_size = unpacked_data[6]
        self.b17_allocation_unit_size = unpacked_data[7]
        self.b18_min_addr_block_size = unpacked_data[8]
        self.b19_optimal_read_block_size = unpacked_data[9]
        self.b20_optimal_write_block_size = unpacked_data[10]
        self.b21_max_in_buffer_size = unpacked_data[11]
        self.b22_max_out_buffer_size = unpacked_data[12]
        self.b23_rpmb_read_write_size = unpacked_data[13]
        self.b24_dynamic_capacity_resource_policy = unpacked_data[14]
        self.b25_data_ordering = unpacked_data[15]
        self.b26_max_context_id_number = unpacked_data[16]
        self.b27_sys_data_tag_unit_size = unpacked_data[17]
        self.b28_sys_data_tag_res_size = unpacked_data[18]
        self.b29_supported_sec_r_types = unpacked_data[19]
        self.w30_supported_memory_types = unpacked_data[20]
        self.l32_system_code_max_n_alloc_u = unpacked_data[21]
        self.w36_system_code_cap_adj_fac = unpacked_data[22]
        self.l38_non_persist_max_n_alloc_u = unpacked_data[23]
        self.w42_non_persist_cap_adj_fac = unpacked_data[24]
        self.l44_enhanced1_max_n_alloc_u = unpacked_data[25]
        self.w48_enhanced1_cap_adj_fac = unpacked_data[26]
        self.l50_enhanced2_max_n_alloc_u = unpacked_data[27]
        self.w54_enhanced2_cap_adj_fac = unpacked_data[28]
        self.l56_enhanced3_max_n_alloc_u = unpacked_data[29]
        self.w60_enhanced3_cap_adj_fac = unpacked_data[30]
        self.l62_enhanced4_max_n_alloc_u = unpacked_data[31]
        self.w66_enhanced4_cap_adj_fac = unpacked_data[32]
        self.l68_optimal_logical_block_size = unpacked_data[33]
        self.b72_rsvd = unpacked_data[34]
        self.l73_rsvd = unpacked_data[35]
        self.w77_rsvd = unpacked_data[36]
        self.l79_write_booster_buffer_max_n_alloc_units = unpacked_data[37]
        self.b83_device_max_write_booster_lus = unpacked_data[38]
        self.b84_write_booster_buffer_cap_adj_fac = unpacked_data[39]
        self.b85_supported_write_booster_buffer_user_space_reduction_types = unpacked_data[40]
        self.b86_supported_write_booster_buffer_types = unpacked_data[41]

########################### UFS Specs 3.1 end ###########################

########################### UFS Specs 4.0 ###########################

class GeometryDescriptor400(GeometryDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0x57
        self.b1_descriptor_idn = DescriptorIDN.GEOMETRY
        self.b2_media_technology = 0
        self.b3_rsvd = 0
        self.q4_total_raw_device_capacity = 0
        self.b12_max_number_lu = 0
        self.l13_segment_size = 0
        self.b17_allocation_unit_size = 0
        self.b18_min_addr_block_size = 0
        self.b19_optimal_read_block_size = 0
        self.b20_optimal_write_block_size = 0
        self.b21_max_in_buffer_size = 0
        self.b22_max_out_buffer_size = 0
        self.b23_rpmb_read_write_size = 0
        self.b24_dynamic_capacity_resource_policy = 0
        self.b25_data_ordering = 0
        self.b26_max_context_id_number = 0
        self.b27_sys_data_tag_unit_size = 0
        self.b28_sys_data_tag_res_size = 0
        self.b29_supported_sec_r_types = 0
        self.w30_supported_memory_types = 0
        self.l32_system_code_max_n_alloc_u = 0
        self.w36_system_code_cap_adj_fac = 0
        self.l38_non_persist_max_n_alloc_u = 0
        self.w42_non_persist_cap_adj_fac = 0
        self.l44_enhanced1_max_n_alloc_u = 0
        self.w48_enhanced1_cap_adj_fac = 0
        self.l50_enhanced2_max_n_alloc_u = 0
        self.w54_enhanced2_cap_adj_fac = 0
        self.l56_enhanced3_max_n_alloc_u = 0
        self.w60_enhanced3_cap_adj_fac = 0
        self.l62_enhanced4_max_n_alloc_u = 0
        self.w66_enhanced4_cap_adj_fac = 0
        self.l68_optimal_logical_block_size = 0
        self.b72_rsvd = 0
        self.l73_rsvd = 0
        self.w77_rsvd = 0
        self.l79_write_booster_buffer_max_n_alloc_units = 0
        self.b83_device_max_write_booster_lus = 0
        self.b84_write_booster_buffer_cap_adj_fac = 0
        self.b85_supported_write_booster_buffer_user_space_reduction_types = 0
        self.b86_supported_write_booster_buffer_types = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBQBLBBBBBBBBBBBBBHLHLHLHLHLHLHLBLHLBBBB', payload[0:87])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_media_technology = unpacked_data[2]
        self.b3_rsvd = unpacked_data[3]
        self.q4_total_raw_device_capacity = unpacked_data[4]
        self.b12_max_number_lu = unpacked_data[5]
        self.l13_segment_size = unpacked_data[6]
        self.b17_allocation_unit_size = unpacked_data[7]
        self.b18_min_addr_block_size = unpacked_data[8]
        self.b19_optimal_read_block_size = unpacked_data[9]
        self.b20_optimal_write_block_size = unpacked_data[10]
        self.b21_max_in_buffer_size = unpacked_data[11]
        self.b22_max_out_buffer_size = unpacked_data[12]
        self.b23_rpmb_read_write_size = unpacked_data[13]
        self.b24_dynamic_capacity_resource_policy = unpacked_data[14]
        self.b25_data_ordering = unpacked_data[15]
        self.b26_max_context_id_number = unpacked_data[16]
        self.b27_sys_data_tag_unit_size = unpacked_data[17]
        self.b28_sys_data_tag_res_size = unpacked_data[18]
        self.b29_supported_sec_r_types = unpacked_data[19]
        self.w30_supported_memory_types = unpacked_data[20]
        self.l32_system_code_max_n_alloc_u = unpacked_data[21]
        self.w36_system_code_cap_adj_fac = unpacked_data[22]
        self.l38_non_persist_max_n_alloc_u = unpacked_data[23]
        self.w42_non_persist_cap_adj_fac = unpacked_data[24]
        self.l44_enhanced1_max_n_alloc_u = unpacked_data[25]
        self.w48_enhanced1_cap_adj_fac = unpacked_data[26]
        self.l50_enhanced2_max_n_alloc_u = unpacked_data[27]
        self.w54_enhanced2_cap_adj_fac = unpacked_data[28]
        self.l56_enhanced3_max_n_alloc_u = unpacked_data[29]
        self.w60_enhanced3_cap_adj_fac = unpacked_data[30]
        self.l62_enhanced4_max_n_alloc_u = unpacked_data[31]
        self.w66_enhanced4_cap_adj_fac = unpacked_data[32]
        self.l68_optimal_logical_block_size = unpacked_data[33]
        self.b72_rsvd = unpacked_data[34]
        self.l73_rsvd = unpacked_data[35]
        self.w77_rsvd = unpacked_data[36]
        self.l79_write_booster_buffer_max_n_alloc_units = unpacked_data[37]
        self.b83_device_max_write_booster_lus = unpacked_data[38]
        self.b84_write_booster_buffer_cap_adj_fac = unpacked_data[39]
        self.b85_supported_write_booster_buffer_user_space_reduction_types = unpacked_data[40]
        self.b86_supported_write_booster_buffer_types = unpacked_data[41]

########################### UFS Specs 4.0 end ###########################

########################### UFS Specs 4.1 ###########################

class GeometryDescriptor410(GeometryDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0x69
        self.b1_descriptor_idn = DescriptorIDN.GEOMETRY
        self.b2_media_technology = 0
        self.b3_rsvd = 0
        self.q4_total_raw_device_capacity = 0
        self.b12_max_number_lu = 0
        self.l13_segment_size = 0
        self.b17_allocation_unit_size = 0
        self.b18_min_addr_block_size = 0
        self.b19_optimal_read_block_size = 0
        self.b20_optimal_write_block_size = 0
        self.b21_max_in_buffer_size = 0
        self.b22_max_out_buffer_size = 0
        self.b23_rpmb_read_write_size = 0
        self.b24_dynamic_capacity_resource_policy = 0
        self.b25_data_ordering = 0
        self.b26_max_context_id_number = 0
        self.b27_sys_data_tag_unit_size = 0
        self.b28_sys_data_tag_res_size = 0
        self.b29_supported_sec_r_types = 0
        self.w30_supported_memory_types = 0
        self.l32_system_code_max_n_alloc_u = 0
        self.w36_system_code_cap_adj_fac = 0
        self.l38_non_persist_max_n_alloc_u = 0
        self.w42_non_persist_cap_adj_fac = 0
        self.l44_enhanced1_max_n_alloc_u = 0
        self.w48_enhanced1_cap_adj_fac = 0
        self.l50_enhanced2_max_n_alloc_u = 0
        self.w54_enhanced2_cap_adj_fac = 0
        self.l56_enhanced3_max_n_alloc_u = 0
        self.w60_enhanced3_cap_adj_fac = 0
        self.l62_enhanced4_max_n_alloc_u = 0
        self.w66_enhanced4_cap_adj_fac = 0
        self.l68_optimal_logical_block_size = 0
        self.b72_rsvd = 0
        self.l73_rsvd = 0
        self.w77_rsvd = 0
        self.l79_write_booster_buffer_max_n_alloc_units = 0
        self.b83_device_max_write_booster_lus = 0
        self.b84_write_booster_buffer_cap_adj_fac = 0
        self.b85_supported_write_booster_buffer_user_space_reduction_types = 0
        self.b86_supported_write_booster_buffer_types = 0
        self.q87_rsvd = 0
        self.q95_rsvd = 0
        self.b103_rsvd = 0
        self.b104_cap_adj_fac_representation = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBQBLBBBBBBBBBBBBBHLHLHLHLHLHLHLBLHLBBBBQQBB', payload[0:105])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_media_technology = unpacked_data[2]
        self.b3_rsvd = unpacked_data[3]
        self.q4_total_raw_device_capacity = unpacked_data[4]
        self.b12_max_number_lu = unpacked_data[5]
        self.l13_segment_size = unpacked_data[6]
        self.b17_allocation_unit_size = unpacked_data[7]
        self.b18_min_addr_block_size = unpacked_data[8]
        self.b19_optimal_read_block_size = unpacked_data[9]
        self.b20_optimal_write_block_size = unpacked_data[10]
        self.b21_max_in_buffer_size = unpacked_data[11]
        self.b22_max_out_buffer_size = unpacked_data[12]
        self.b23_rpmb_read_write_size = unpacked_data[13]
        self.b24_dynamic_capacity_resource_policy = unpacked_data[14]
        self.b25_data_ordering = unpacked_data[15]
        self.b26_max_context_id_number = unpacked_data[16]
        self.b27_sys_data_tag_unit_size = unpacked_data[17]
        self.b28_sys_data_tag_res_size = unpacked_data[18]
        self.b29_supported_sec_r_types = unpacked_data[19]
        self.w30_supported_memory_types = unpacked_data[20]
        self.l32_system_code_max_n_alloc_u = unpacked_data[21]
        self.w36_system_code_cap_adj_fac = unpacked_data[22]
        self.l38_non_persist_max_n_alloc_u = unpacked_data[23]
        self.w42_non_persist_cap_adj_fac = unpacked_data[24]
        self.l44_enhanced1_max_n_alloc_u = unpacked_data[25]
        self.w48_enhanced1_cap_adj_fac = unpacked_data[26]
        self.l50_enhanced2_max_n_alloc_u = unpacked_data[27]
        self.w54_enhanced2_cap_adj_fac = unpacked_data[28]
        self.l56_enhanced3_max_n_alloc_u = unpacked_data[29]
        self.w60_enhanced3_cap_adj_fac = unpacked_data[30]
        self.l62_enhanced4_max_n_alloc_u = unpacked_data[31]
        self.w66_enhanced4_cap_adj_fac = unpacked_data[32]
        self.l68_optimal_logical_block_size = unpacked_data[33]
        self.b72_rsvd = unpacked_data[34]
        self.l73_rsvd = unpacked_data[35]
        self.w77_rsvd = unpacked_data[36]
        self.l79_write_booster_buffer_max_n_alloc_units = unpacked_data[37]
        self.b83_device_max_write_booster_lus = unpacked_data[38]
        self.b84_write_booster_buffer_cap_adj_fac = unpacked_data[39]
        self.b85_supported_write_booster_buffer_user_space_reduction_types = unpacked_data[40]
        self.b86_supported_write_booster_buffer_types = unpacked_data[41]
        self.q87_rsvd = unpacked_data[42]
        self.q95_rsvd = unpacked_data[43]
        self.b103_rsvd = unpacked_data[44]
        self.b104_cap_adj_fac_representation = unpacked_data[45]

########################### UFS Specs 4.1 end ###########################
