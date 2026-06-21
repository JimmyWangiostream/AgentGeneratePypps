import struct
from Script.api.struct_helper import *


# Define empty classes for inheritance and type hint usage
class UnitDescriptor(PacketParserABC):
    def from_bytes(self, payload: bytearray) -> None:
        pass

########################### UFS Specs 3.1 ###########################

class UnitDescriptor310(UnitDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.b2_unit_index = 0
        self.b3_lu_enable = 0
        self.b4_boot_lun_id = 0
        self.b5_lu_write_protect = 0
        self.b6_lu_queue_depth = 0
        self.b7_psa_sensitive = 0
        self.b8_memory_type = 0
        self.b9_data_reliability = 0
        self.b10_logical_block_size = 0
        self.q11_logical_block_count = 0
        self.l19_erase_block_size = 0
        self.b23_provisioning_type = 0
        self.q24_phy_mem_resource_count = 0
        self.w32_context_capabilities = 0
        self.b34_large_unit_granularity_m1 = 0
        self.w35_lu_max_active_hpb_regions = 0
        self.w37_hpb_pinned_region_start_idx = 0
        self.w39_num_hpb_pinned_regions = 0
        self.l41_lu_num_write_booster_buffer_alloc_units = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBBBBBBBBQLBQHBHHHL', payload[0:45])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_unit_index = unpacked_data[2]
        self.b3_lu_enable = unpacked_data[3]
        self.b4_boot_lun_id = unpacked_data[4]
        self.b5_lu_write_protect = unpacked_data[5]
        self.b6_lu_queue_depth = unpacked_data[6]
        self.b7_psa_sensitive = unpacked_data[7]
        self.b8_memory_type = unpacked_data[8]
        self.b9_data_reliability = unpacked_data[9]
        self.b10_logical_block_size = unpacked_data[10]
        self.q11_logical_block_count = unpacked_data[11]
        self.l19_erase_block_size = unpacked_data[12]
        self.b23_provisioning_type = unpacked_data[13]
        self.q24_phy_mem_resource_count = unpacked_data[14]
        self.w32_context_capabilities = unpacked_data[15]
        self.b34_large_unit_granularity_m1 = unpacked_data[16]
        self.w35_lu_max_active_hpb_regions = unpacked_data[17]
        self.w37_hpb_pinned_region_start_idx = unpacked_data[18]
        self.w39_num_hpb_pinned_regions = unpacked_data[19]
        self.l41_lu_num_write_booster_buffer_alloc_units = unpacked_data[20]

########################### UFS Specs 3.1 end ###########################

########################### UFS Specs 4.0 ###########################

class UnitDescriptor400(UnitDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.b2_unit_index = 0
        self.b3_lu_enable = 0
        self.b4_boot_lun_id = 0
        self.b5_lu_write_protect = 0
        self.b6_lu_queue_depth = 0
        self.b7_psa_sensitive = 0
        self.b8_memory_type = 0
        self.b9_data_reliability = 0
        self.b10_logical_block_size = 0
        self.q11_logical_block_count = 0
        self.l19_erase_block_size = 0
        self.b23_provisioning_type = 0
        self.q24_phy_mem_resource_count = 0
        self.w32_context_capabilities = 0
        self.b34_large_unit_granularity_m1 = 0
        self.w35_lu_max_active_hpb_regions = 0
        self.w37_hpb_pinned_region_start_idx = 0
        self.w39_num_hpb_pinned_regions = 0
        self.l41_lu_num_write_booster_buffer_alloc_units = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBBBBBBBBQLBQHBHHHL', payload[0:45])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_unit_index = unpacked_data[2]
        self.b3_lu_enable = unpacked_data[3]
        self.b4_boot_lun_id = unpacked_data[4]
        self.b5_lu_write_protect = unpacked_data[5]
        self.b6_lu_queue_depth = unpacked_data[6]
        self.b7_psa_sensitive = unpacked_data[7]
        self.b8_memory_type = unpacked_data[8]
        self.b9_data_reliability = unpacked_data[9]
        self.b10_logical_block_size = unpacked_data[10]
        self.q11_logical_block_count = unpacked_data[11]
        self.l19_erase_block_size = unpacked_data[12]
        self.b23_provisioning_type = unpacked_data[13]
        self.q24_phy_mem_resource_count = unpacked_data[14]
        self.w32_context_capabilities = unpacked_data[15]
        self.b34_large_unit_granularity_m1 = unpacked_data[16]
        self.w35_lu_max_active_hpb_regions = unpacked_data[17]
        self.w37_hpb_pinned_region_start_idx = unpacked_data[18]
        self.w39_num_hpb_pinned_regions = unpacked_data[19]
        self.l41_lu_num_write_booster_buffer_alloc_units = unpacked_data[20]

########################### UFS Specs 4.0 end ###########################

########################### UFS Specs 4.1 ###########################

class UnitDescriptor410(UnitDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.b2_unit_index = 0
        self.b3_lu_enable = 0
        self.b4_boot_lun_id = 0
        self.b5_lu_write_protect = 0
        self.b6_lu_queue_depth = 0
        self.b7_psa_sensitive = 0
        self.b8_memory_type = 0
        self.b9_data_reliability = 0
        self.b10_logical_block_size = 0
        self.q11_logical_block_count = 0
        self.l19_erase_block_size = 0
        self.b23_provisioning_type = 0
        self.q24_phy_mem_resource_count = 0
        self.w32_context_capabilities = 0
        self.b34_large_unit_granularity_m1 = 0
        self.w35_lu_max_active_hpb_regions = 0
        self.w37_hpb_pinned_region_start_idx = 0
        self.w39_num_hpb_pinned_regions = 0
        self.l41_lu_num_write_booster_buffer_alloc_units = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBBBBBBBBQLBQHBHHHL', payload[0:45])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_unit_index = unpacked_data[2]
        self.b3_lu_enable = unpacked_data[3]
        self.b4_boot_lun_id = unpacked_data[4]
        self.b5_lu_write_protect = unpacked_data[5]
        self.b6_lu_queue_depth = unpacked_data[6]
        self.b7_psa_sensitive = unpacked_data[7]
        self.b8_memory_type = unpacked_data[8]
        self.b9_data_reliability = unpacked_data[9]
        self.b10_logical_block_size = unpacked_data[10]
        self.q11_logical_block_count = unpacked_data[11]
        self.l19_erase_block_size = unpacked_data[12]
        self.b23_provisioning_type = unpacked_data[13]
        self.q24_phy_mem_resource_count = unpacked_data[14]
        self.w32_context_capabilities = unpacked_data[15]
        self.b34_large_unit_granularity_m1 = unpacked_data[16]
        self.w35_lu_max_active_hpb_regions = unpacked_data[17]
        self.w37_hpb_pinned_region_start_idx = unpacked_data[18]
        self.w39_num_hpb_pinned_regions = unpacked_data[19]
        self.l41_lu_num_write_booster_buffer_alloc_units = unpacked_data[20]

########################### UFS Specs 4.1 end ###########################
