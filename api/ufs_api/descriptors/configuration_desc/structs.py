import struct
from Script.api.struct_helper import *
from Script.api.ufs_api.defines.enum_define import DescriptorIDN


# Define empty classes for inheritance and type hint usage
class ConfigDescriptorHeader(PacketComposerABC, PacketParserABC):
    def to_bytes(self) -> bytearray:
        return bytearray()
    def from_bytes(self, payload: bytearray) -> None:
        pass

class ConfigDescriptorUnit(PacketComposerABC, PacketParserABC):
    def to_bytes(self) -> bytearray:
        return bytearray()
    def from_bytes(self, payload: bytearray) -> None:
        pass

class ConfigDescriptor(PacketComposerABC, PacketParserABC):
    def to_bytes(self) -> bytearray:
        return bytearray()
    def from_bytes(self, payload: bytearray) -> None:
        pass

########################### UFS Specs 3.1 ###########################

class ConfigDescriptorHeader310(ConfigDescriptorHeader):
    def __init__(self) -> None:
        self.b0_length = 0xE6
        self.b1_descriptor_idn = DescriptorIDN.CONFIGURATION
        self.b2_conf_desc_continue = 0
        self.b3_boot_enable = 0
        self.b4_descr_access_en = 0
        self.b5_init_power_mode = 0
        self.b6_high_priority_lun = 0
        self.b7_secure_removal_type = 0
        self.b8_init_active_icc_level = 0
        self.w9_periodic_rtc_update = 0
        self.b11_hpb_control = 0
        self.b12_rpmb_region_enable = 0
        self.b13_rpmb_region1_size = 0
        self.b14_rpmb_region2_size = 0
        self.b15_rpmb_region3_size = 0
        self.b16_write_booster_buffer_preserve_user_space_en = 0
        self.b17_write_booster_buffer_type = 0
        self.l18_num_shared_write_booster_buffer_alloc_units = 0

    def to_bytes(self) -> bytearray:
        buf = bytearray(22)
        struct.pack_into(
            '>BBBBBBBBBHBBBBBBBL', buf, 0,
            self.b0_length,
            self.b1_descriptor_idn,
            self.b2_conf_desc_continue,
            self.b3_boot_enable,
            self.b4_descr_access_en,
            self.b5_init_power_mode,
            self.b6_high_priority_lun,
            self.b7_secure_removal_type,
            self.b8_init_active_icc_level,
            self.w9_periodic_rtc_update,
            self.b11_hpb_control,
            self.b12_rpmb_region_enable,
            self.b13_rpmb_region1_size,
            self.b14_rpmb_region2_size,
            self.b15_rpmb_region3_size,
            self.b16_write_booster_buffer_preserve_user_space_en,
            self.b17_write_booster_buffer_type,
            self.l18_num_shared_write_booster_buffer_alloc_units
        )
        return buf

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBBBBBBHBBBBBBBL'
        unpacked_data = struct.unpack(format_string, payload[0:22])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_conf_desc_continue = unpacked_data[2]
        self.b3_boot_enable = unpacked_data[3]
        self.b4_descr_access_en = unpacked_data[4]
        self.b5_init_power_mode = unpacked_data[5]
        self.b6_high_priority_lun = unpacked_data[6]
        self.b7_secure_removal_type = unpacked_data[7]
        self.b8_init_active_icc_level = unpacked_data[8]
        self.w9_periodic_rtc_update = unpacked_data[9]
        self.b11_hpb_control = unpacked_data[10]
        self.b12_rpmb_region_enable = unpacked_data[11]
        self.b13_rpmb_region1_size = unpacked_data[12]
        self.b14_rpmb_region2_size = unpacked_data[13]
        self.b15_rpmb_region3_size = unpacked_data[14]
        self.b16_write_booster_buffer_preserve_user_space_en = unpacked_data[15]
        self.b17_write_booster_buffer_type = unpacked_data[16]
        self.l18_num_shared_write_booster_buffer_alloc_units = unpacked_data[17]

class ConfigDescriptorUnit310(ConfigDescriptorUnit):
    def __init__(self) -> None:
        self.b0_lu_enable = 0
        self.b1_boot_lun_id = 0
        self.b2_lu_write_protect = 0
        self.b3_memory_type = 0
        self.l4_num_alloc_units = 0
        self.b8_data_reliability = 0
        self.b9_logical_block_size = 0
        self.b10_provisioning_type = 0
        self.w11_context_capabilities = 0
        self.b13_rsvd = 0
        self.w14_rsvd = 0
        self.w16_lu_max_active_hpb_region = 0
        self.w18_hpb_pinned_region_start_idx = 0
        self.w20_num_hpb_pinned_regions = 0
        self.l22_lu_num_write_booster_buffer_alloc_units = 0

    def to_bytes(self) -> bytearray:
        buf = bytearray(26)
        struct.pack_into(
            '>BBBBLBBBHBHHHHL', buf, 0,
            self.b0_lu_enable,
            self.b1_boot_lun_id,
            self.b2_lu_write_protect,
            self.b3_memory_type,
            self.l4_num_alloc_units,
            self.b8_data_reliability,
            self.b9_logical_block_size,
            self.b10_provisioning_type,
            self.w11_context_capabilities,
            self.b13_rsvd,
            self.w14_rsvd,
            self.w16_lu_max_active_hpb_region,
            self.w18_hpb_pinned_region_start_idx,
            self.w20_num_hpb_pinned_regions,
            self.l22_lu_num_write_booster_buffer_alloc_units
        )
        return buf

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBLBBBHBHHHHL'
        unpacked_data = struct.unpack(format_string, payload[0:26])
        self.b0_lu_enable = unpacked_data[0]
        self.b1_boot_lun_id = unpacked_data[1]
        self.b2_lu_write_protect = unpacked_data[2]
        self.b3_memory_type = unpacked_data[3]
        self.l4_num_alloc_units = unpacked_data[4]
        self.b8_data_reliability = unpacked_data[5]
        self.b9_logical_block_size = unpacked_data[6]
        self.b10_provisioning_type = unpacked_data[7]
        self.w11_context_capabilities = unpacked_data[8]
        self.b13_rsvd = unpacked_data[9]
        self.w14_rsvd = unpacked_data[10]
        self.w16_lu_max_active_hpb_region = unpacked_data[11]
        self.w18_hpb_pinned_region_start_idx = unpacked_data[12]
        self.w20_num_hpb_pinned_regions = unpacked_data[13]
        self.l22_lu_num_write_booster_buffer_alloc_units = unpacked_data[14]

class ConfigDescriptor310(ConfigDescriptor):
    def __init__(self) -> None:
        self.header = ConfigDescriptorHeader310()
        self.units = [ConfigDescriptorUnit310() for _ in range(8)]

    def to_bytes(self) -> bytearray:
        buf = self.header.to_bytes()
        for cfg_desc_unit in self.units:
            buf += cfg_desc_unit.to_bytes()
        return buf

    def from_bytes(self, payload: bytearray) -> None:
        self.header.from_bytes(payload[0:22])
        offset = 22  # config descriptor header length
        for cfg_desc_unit in self.units:
            cfg_desc_unit.from_bytes(payload[offset:offset+26])
            offset += 26  # config unit descriptor length

########################### UFS Specs 3.1 end ###########################

########################### UFS Specs 4.0 ###########################

class ConfigDescriptorHeader400(ConfigDescriptorHeader):
    def __init__(self) -> None:
        self.b0_length = 0xE6
        self.b1_descriptor_idn = DescriptorIDN.CONFIGURATION
        self.b2_conf_desc_continue = 0
        self.b3_boot_enable = 0
        self.b4_descr_access_en = 0
        self.b5_init_power_mode = 0
        self.b6_high_priority_lun = 0
        self.b7_secure_removal_type = 0
        self.b8_init_active_icc_level = 0
        self.w9_periodic_rtc_update = 0
        self.b11_hpb_control = 0
        self.b12_rpmb_region_enable = 0
        self.b13_rpmb_region1_size = 0
        self.b14_rpmb_region2_size = 0
        self.b15_rpmb_region3_size = 0
        self.b16_write_booster_buffer_preserve_user_space_en = 0
        self.b17_write_booster_buffer_type = 0
        self.l18_num_shared_write_booster_buffer_alloc_units = 0

    def to_bytes(self) -> bytearray:
        buf = bytearray(22)
        struct.pack_into(
            '>BBBBBBBBBHBBBBBBBL', buf, 0,
            self.b0_length,
            self.b1_descriptor_idn,
            self.b2_conf_desc_continue,
            self.b3_boot_enable,
            self.b4_descr_access_en,
            self.b5_init_power_mode,
            self.b6_high_priority_lun,
            self.b7_secure_removal_type,
            self.b8_init_active_icc_level,
            self.w9_periodic_rtc_update,
            self.b11_hpb_control,
            self.b12_rpmb_region_enable,
            self.b13_rpmb_region1_size,
            self.b14_rpmb_region2_size,
            self.b15_rpmb_region3_size,
            self.b16_write_booster_buffer_preserve_user_space_en,
            self.b17_write_booster_buffer_type,
            self.l18_num_shared_write_booster_buffer_alloc_units
        )
        return buf

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBBBBBBHBBBBBBBL'
        unpacked_data = struct.unpack(format_string, payload[0:22])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_conf_desc_continue = unpacked_data[2]
        self.b3_boot_enable = unpacked_data[3]
        self.b4_descr_access_en = unpacked_data[4]
        self.b5_init_power_mode = unpacked_data[5]
        self.b6_high_priority_lun = unpacked_data[6]
        self.b7_secure_removal_type = unpacked_data[7]
        self.b8_init_active_icc_level = unpacked_data[8]
        self.w9_periodic_rtc_update = unpacked_data[9]
        self.b11_hpb_control = unpacked_data[10]
        self.b12_rpmb_region_enable = unpacked_data[11]
        self.b13_rpmb_region1_size = unpacked_data[12]
        self.b14_rpmb_region2_size = unpacked_data[13]
        self.b15_rpmb_region3_size = unpacked_data[14]
        self.b16_write_booster_buffer_preserve_user_space_en = unpacked_data[15]
        self.b17_write_booster_buffer_type = unpacked_data[16]
        self.l18_num_shared_write_booster_buffer_alloc_units = unpacked_data[17]

class ConfigDescriptorUnit400(ConfigDescriptorUnit):
    def __init__(self) -> None:
        self.b0_lu_enable = 0
        self.b1_boot_lun_id = 0
        self.b2_lu_write_protect = 0
        self.b3_memory_type = 0
        self.l4_num_alloc_units = 0
        self.b8_data_reliability = 0
        self.b9_logical_block_size = 0
        self.b10_provisioning_type = 0
        self.w11_context_capabilities = 0
        self.b13_rsvd = 0
        self.w14_rsvd = 0
        self.w16_lu_max_active_hpb_region = 0
        self.w18_hpb_pinned_region_start_idx = 0
        self.w20_num_hpb_pinned_regions = 0
        self.l22_lu_num_write_booster_buffer_alloc_units = 0

    def to_bytes(self) -> bytearray:
        buf = bytearray(26)
        struct.pack_into(
            '>BBBBLBBBHBHHHHL', buf, 0,
            self.b0_lu_enable,
            self.b1_boot_lun_id,
            self.b2_lu_write_protect,
            self.b3_memory_type,
            self.l4_num_alloc_units,
            self.b8_data_reliability,
            self.b9_logical_block_size,
            self.b10_provisioning_type,
            self.w11_context_capabilities,
            self.b13_rsvd,
            self.w14_rsvd,
            self.w16_lu_max_active_hpb_region,
            self.w18_hpb_pinned_region_start_idx,
            self.w20_num_hpb_pinned_regions,
            self.l22_lu_num_write_booster_buffer_alloc_units
        )
        return buf

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBLBBBHBHHHHL'
        unpacked_data = struct.unpack(format_string, payload[0:26])
        self.b0_lu_enable = unpacked_data[0]
        self.b1_boot_lun_id = unpacked_data[1]
        self.b2_lu_write_protect = unpacked_data[2]
        self.b3_memory_type = unpacked_data[3]
        self.l4_num_alloc_units = unpacked_data[4]
        self.b8_data_reliability = unpacked_data[5]
        self.b9_logical_block_size = unpacked_data[6]
        self.b10_provisioning_type = unpacked_data[7]
        self.w11_context_capabilities = unpacked_data[8]
        self.b13_rsvd = unpacked_data[9]
        self.w14_rsvd = unpacked_data[10]
        self.w16_lu_max_active_hpb_region = unpacked_data[11]
        self.w18_hpb_pinned_region_start_idx = unpacked_data[12]
        self.w20_num_hpb_pinned_regions = unpacked_data[13]
        self.l22_lu_num_write_booster_buffer_alloc_units = unpacked_data[14]

class ConfigDescriptor400(ConfigDescriptor):
    def __init__(self) -> None:
        self.header = ConfigDescriptorHeader400()
        self.units = [ConfigDescriptorUnit400() for _ in range(8)]

    def to_bytes(self) -> bytearray:
        buf = self.header.to_bytes()
        for cfg_desc_unit in self.units:
            buf += cfg_desc_unit.to_bytes()
        return buf

    def from_bytes(self, payload: bytearray) -> None:
        self.header.from_bytes(payload[0:22])
        offset = 22  # config descriptor header length
        for cfg_desc_unit in self.units:
            cfg_desc_unit.from_bytes(payload[offset:offset+26])
            offset += 26  # config unit descriptor length

########################### UFS Specs 4.0 end ###########################

########################### UFS Specs 4.1 ###########################

class ConfigDescriptorHeader410(ConfigDescriptorHeader):
    def __init__(self) -> None:
        self.b0_length = 0xE6
        self.b1_descriptor_idn = DescriptorIDN.CONFIGURATION
        self.b2_conf_desc_continue = 0
        self.b3_boot_enable = 0
        self.b4_descr_access_en = 0
        self.b5_init_power_mode = 0
        self.b6_high_priority_lun = 0
        self.b7_secure_removal_type = 0
        self.b8_init_active_icc_level = 0
        self.w9_periodic_rtc_update = 0
        self.b11_hpb_control = 0
        self.b12_rpmb_region_enable = 0
        self.b13_rpmb_region1_size = 0
        self.b14_rpmb_region2_size = 0
        self.b15_rpmb_region3_size = 0
        self.b16_write_booster_buffer_preserve_user_space_en = 0
        self.b17_write_booster_buffer_type = 0
        self.l18_num_shared_write_booster_buffer_alloc_units = 0

    def to_bytes(self) -> bytearray:
        buf = bytearray(22)
        struct.pack_into(
            '>BBBBBBBBBHBBBBBBBL', buf, 0,
            self.b0_length,
            self.b1_descriptor_idn,
            self.b2_conf_desc_continue,
            self.b3_boot_enable,
            self.b4_descr_access_en,
            self.b5_init_power_mode,
            self.b6_high_priority_lun,
            self.b7_secure_removal_type,
            self.b8_init_active_icc_level,
            self.w9_periodic_rtc_update,
            self.b11_hpb_control,
            self.b12_rpmb_region_enable,
            self.b13_rpmb_region1_size,
            self.b14_rpmb_region2_size,
            self.b15_rpmb_region3_size,
            self.b16_write_booster_buffer_preserve_user_space_en,
            self.b17_write_booster_buffer_type,
            self.l18_num_shared_write_booster_buffer_alloc_units
        )
        return buf

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBBBBBBHBBBBBBBL'
        unpacked_data = struct.unpack(format_string, payload[0:22])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_conf_desc_continue = unpacked_data[2]
        self.b3_boot_enable = unpacked_data[3]
        self.b4_descr_access_en = unpacked_data[4]
        self.b5_init_power_mode = unpacked_data[5]
        self.b6_high_priority_lun = unpacked_data[6]
        self.b7_secure_removal_type = unpacked_data[7]
        self.b8_init_active_icc_level = unpacked_data[8]
        self.w9_periodic_rtc_update = unpacked_data[9]
        self.b11_hpb_control = unpacked_data[10]
        self.b12_rpmb_region_enable = unpacked_data[11]
        self.b13_rpmb_region1_size = unpacked_data[12]
        self.b14_rpmb_region2_size = unpacked_data[13]
        self.b15_rpmb_region3_size = unpacked_data[14]
        self.b16_write_booster_buffer_preserve_user_space_en = unpacked_data[15]
        self.b17_write_booster_buffer_type = unpacked_data[16]
        self.l18_num_shared_write_booster_buffer_alloc_units = unpacked_data[17]

class ConfigDescriptorUnit410(ConfigDescriptorUnit):
    def __init__(self) -> None:
        self.b0_lu_enable = 0
        self.b1_boot_lun_id = 0
        self.b2_lu_write_protect = 0
        self.b3_memory_type = 0
        self.l4_num_alloc_units = 0
        self.b8_data_reliability = 0
        self.b9_logical_block_size = 0
        self.b10_provisioning_type = 0
        self.w11_context_capabilities = 0
        self.b13_rsvd = 0
        self.w14_rsvd = 0
        self.w16_lu_max_active_hpb_region = 0
        self.w18_hpb_pinned_region_start_idx = 0
        self.w20_num_hpb_pinned_regions = 0
        self.l22_lu_num_write_booster_buffer_alloc_units = 0

    def to_bytes(self) -> bytearray:
        buf = bytearray(26)
        struct.pack_into(
            '>BBBBLBBBHBHHHHL', buf, 0,
            self.b0_lu_enable,
            self.b1_boot_lun_id,
            self.b2_lu_write_protect,
            self.b3_memory_type,
            self.l4_num_alloc_units,
            self.b8_data_reliability,
            self.b9_logical_block_size,
            self.b10_provisioning_type,
            self.w11_context_capabilities,
            self.b13_rsvd,
            self.w14_rsvd,
            self.w16_lu_max_active_hpb_region,
            self.w18_hpb_pinned_region_start_idx,
            self.w20_num_hpb_pinned_regions,
            self.l22_lu_num_write_booster_buffer_alloc_units
        )
        return buf

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBLBBBHBHHHHL'
        unpacked_data = struct.unpack(format_string, payload[0:26])
        self.b0_lu_enable = unpacked_data[0]
        self.b1_boot_lun_id = unpacked_data[1]
        self.b2_lu_write_protect = unpacked_data[2]
        self.b3_memory_type = unpacked_data[3]
        self.l4_num_alloc_units = unpacked_data[4]
        self.b8_data_reliability = unpacked_data[5]
        self.b9_logical_block_size = unpacked_data[6]
        self.b10_provisioning_type = unpacked_data[7]
        self.w11_context_capabilities = unpacked_data[8]
        self.b13_rsvd = unpacked_data[9]
        self.w14_rsvd = unpacked_data[10]
        self.w16_lu_max_active_hpb_region = unpacked_data[11]
        self.w18_hpb_pinned_region_start_idx = unpacked_data[12]
        self.w20_num_hpb_pinned_regions = unpacked_data[13]
        self.l22_lu_num_write_booster_buffer_alloc_units = unpacked_data[14]

class ConfigDescriptor410(ConfigDescriptor):
    def __init__(self) -> None:
        self.header = ConfigDescriptorHeader410()
        self.units = [ConfigDescriptorUnit410() for _ in range(8)]

    def to_bytes(self) -> bytearray:
        buf = self.header.to_bytes()
        for cfg_desc_unit in self.units:
            buf += cfg_desc_unit.to_bytes()
        return buf

    def from_bytes(self, payload: bytearray) -> None:
        self.header.from_bytes(payload[0:22])
        offset = 22  # config descriptor header length
        for cfg_desc_unit in self.units:
            cfg_desc_unit.from_bytes(payload[offset:offset+26])
            offset += 26  # config unit descriptor length

########################### UFS Specs 4.1 end ###########################
