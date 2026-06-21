import struct
from Script.api.struct_helper import *


# Define empty classes for inheritance and type hint usage
class RPMBUnitDescriptor(PacketParserABC):
    def from_bytes(self, payload: bytearray) -> None:
        pass

########################### UFS Specs 3.1 ###########################

class RPMBUnitDescriptor310(RPMBUnitDescriptor):
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
        self.b9_rpmb_region_enable = 0
        self.b10_logical_block_size = 0
        self.q11_logical_block_count = 0
        self.b19_rpmb_region0_size = 0
        self.b20_rpmb_region1_size = 0
        self.b21_rpmb_region2_size = 0
        self.b22_rpmb_region3_size = 0
        self.b23_provisioning_type = 0
        self.q24_phy_mem_resource_count = 0
        self.b32_rsvd = 0
        self.w33_rsvd = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBBBBBBBBQBBBBBQBH', payload[0:35])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_unit_index = unpacked_data[2]
        self.b3_lu_enable = unpacked_data[3]
        self.b4_boot_lun_id = unpacked_data[4]
        self.b5_lu_write_protect = unpacked_data[5]
        self.b6_lu_queue_depth = unpacked_data[6]
        self.b7_psa_sensitive = unpacked_data[7]
        self.b8_memory_type = unpacked_data[8]
        self.b9_rpmb_region_enable = unpacked_data[9]
        self.b10_logical_block_size = unpacked_data[10]
        self.q11_logical_block_count = unpacked_data[11]
        self.b19_rpmb_region0_size = unpacked_data[12]
        self.b20_rpmb_region1_size = unpacked_data[13]
        self.b21_rpmb_region2_size = unpacked_data[14]
        self.b22_rpmb_region3_size = unpacked_data[15]
        self.b23_provisioning_type = unpacked_data[16]
        self.q24_phy_mem_resource_count = unpacked_data[17]
        self.b32_rsvd = unpacked_data[18]
        self.w33_rsvd = unpacked_data[19]

########################### UFS Specs 3.1 end ###########################

########################### UFS Specs 4.0 ###########################

class RPMBUnitDescriptor400(RPMBUnitDescriptor):
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
        self.b9_rpmb_region_enable = 0
        self.b10_logical_block_size = 0
        self.q11_logical_block_count = 0
        self.b19_rpmb_region0_size = 0
        self.b20_rpmb_region1_size = 0
        self.b21_rpmb_region2_size = 0
        self.b22_rpmb_region3_size = 0
        self.b23_provisioning_type = 0
        self.q24_phy_mem_resource_count = 0
        self.b32_rsvd = 0
        self.w33_rsvd = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBBBBBBBBQBBBBBQBH', payload[0:35])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_unit_index = unpacked_data[2]
        self.b3_lu_enable = unpacked_data[3]
        self.b4_boot_lun_id = unpacked_data[4]
        self.b5_lu_write_protect = unpacked_data[5]
        self.b6_lu_queue_depth = unpacked_data[6]
        self.b7_psa_sensitive = unpacked_data[7]
        self.b8_memory_type = unpacked_data[8]
        self.b9_rpmb_region_enable = unpacked_data[9]
        self.b10_logical_block_size = unpacked_data[10]
        self.q11_logical_block_count = unpacked_data[11]
        self.b19_rpmb_region0_size = unpacked_data[12]
        self.b20_rpmb_region1_size = unpacked_data[13]
        self.b21_rpmb_region2_size = unpacked_data[14]
        self.b22_rpmb_region3_size = unpacked_data[15]
        self.b23_provisioning_type = unpacked_data[16]
        self.q24_phy_mem_resource_count = unpacked_data[17]
        self.b32_rsvd = unpacked_data[18]
        self.w33_rsvd = unpacked_data[19]

########################### UFS Specs 4.0 end ###########################

########################### UFS Specs 4.1 ###########################

class RPMBUnitDescriptor410(RPMBUnitDescriptor):
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
        self.b9_rpmb_region_enable = 0
        self.b10_logical_block_size = 0
        self.q11_logical_block_count = 0
        self.b19_rpmb_region0_size = 0
        self.b20_rpmb_region1_size = 0
        self.b21_rpmb_region2_size = 0
        self.b22_rpmb_region3_size = 0
        self.b23_provisioning_type = 0
        self.q24_phy_mem_resource_count = 0
        self.b32_rsvd = 0
        self.w33_rsvd = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBBBBBBBBQBBBBBQBH', payload[0:35])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_unit_index = unpacked_data[2]
        self.b3_lu_enable = unpacked_data[3]
        self.b4_boot_lun_id = unpacked_data[4]
        self.b5_lu_write_protect = unpacked_data[5]
        self.b6_lu_queue_depth = unpacked_data[6]
        self.b7_psa_sensitive = unpacked_data[7]
        self.b8_memory_type = unpacked_data[8]
        self.b9_rpmb_region_enable = unpacked_data[9]
        self.b10_logical_block_size = unpacked_data[10]
        self.q11_logical_block_count = unpacked_data[11]
        self.b19_rpmb_region0_size = unpacked_data[12]
        self.b20_rpmb_region1_size = unpacked_data[13]
        self.b21_rpmb_region2_size = unpacked_data[14]
        self.b22_rpmb_region3_size = unpacked_data[15]
        self.b23_provisioning_type = unpacked_data[16]
        self.q24_phy_mem_resource_count = unpacked_data[17]
        self.b32_rsvd = unpacked_data[18]
        self.w33_rsvd = unpacked_data[19]

########################### UFS Specs 4.1 end ###########################
