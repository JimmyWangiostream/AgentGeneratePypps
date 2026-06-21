import struct
from Script.api.struct_helper import *
from Script.api.ufs_api.defines.bit_define import CHK_BIT


# Define empty classes for inheritance and type hint usage
class DeviceDescriptor(PacketParserABC):
    def from_bytes(self, payload: bytearray) -> None:
        pass
class UFSFeaturesSupport(PacketParserABC):
    def from_bytes(self, payload: bytearray) -> None:
        pass
class ExtendedUFSFeaturesSupport(PacketParserABC):
    def from_bytes(self, payload: bytearray) -> None:
        pass
class ExtendedWriteBoosterSupport(PacketParserABC):
    def from_bytes(self, payload: bytearray) -> None:
        pass

########################### UFS Specs 3.1 ###########################

class DeviceDescriptor310(DeviceDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.b2_device = 0
        self.b3_device_class = 0
        self.b4_device_subclass = 0
        self.b5_protocol = 0
        self.b6_number_lu = 0
        self.b7_number_wlu = 0
        self.b8_boot_enable = 0
        self.b9_descr_access_en = 0
        self.b10_init_power_mode = 0
        self.b11_high_priority_lun = 0
        self.b12_secure_removal_type = 0
        self.b13_security_lu = 0
        self.b14_background_ops_term_lat = 0
        self.b15_init_active_icc_level = 0
        self.w16_spec_version = 0
        self.w18_manufacturer_date = 0
        self.b20_manufacturer_name = 0
        self.b21_product_name = 0
        self.b22_serial_number = 0
        self.b23_oem_id = 0
        self.w24_manufacturer_id = 0
        self.b26_ud0_base_offset = 0
        self.b27_ud_config_p_length = 0
        self.b28_device_rtt_cap = 0
        self.w29_periodic_rtc_update = 0
        self.b31_ufs_features_support = 0
        self.b32_ffu_timeout = 0
        self.b33_queue_depth = 0
        self.w34_device_version = 0
        self.b36_num_secure_wp_area = 0
        self.l37_psa_max_data_size = 0
        self.b41_psa_state_timeout = 0
        self.b42_product_revision_level = 0
        self.b43_rsvd = 0
        self.l44_rsvd = 0
        self.l48_rsvd = 0   # For Unified Memory Extension Standard
        self.l52_rsvd = 0
        self.l56_rsvd = 0
        self.l60_rsvd = 0
        self.b64_rsvd = 0   # For Host Performance Booster Extension Standard
        self.w65_rsvd = 0
        self.l67_rsvd = 0
        self.l71_rsvd = 0
        self.l75_rsvd = 0
        self.l79_extended_ufs_features_support = 0
        self.b83_write_booster_buffer_preserve_user_space_en = 0
        self.b84_write_booster_buffer_type = 0
        self.l85_num_shared_write_booster_buffer_alloc_units = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBBBBBBBBBBBBBHHBBBBHBBBHBBBHBLBBBLLLLLBHLLLLBBL', payload[0:89])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_device = unpacked_data[2]
        self.b3_device_class = unpacked_data[3]
        self.b4_device_subclass = unpacked_data[4]
        self.b5_protocol = unpacked_data[5]
        self.b6_number_lu = unpacked_data[6]
        self.b7_number_wlu = unpacked_data[7]
        self.b8_boot_enable = unpacked_data[8]
        self.b9_descr_access_en = unpacked_data[9]
        self.b10_init_power_mode = unpacked_data[10]
        self.b11_high_priority_lun = unpacked_data[11]
        self.b12_secure_removal_type = unpacked_data[12]
        self.b13_security_lu = unpacked_data[13]
        self.b14_background_ops_term_lat = unpacked_data[14]
        self.b15_init_active_icc_level = unpacked_data[15]
        self.w16_spec_version = unpacked_data[16]
        self.w18_manufacturer_date = unpacked_data[17]
        self.b20_manufacturer_name = unpacked_data[18]
        self.b21_product_name = unpacked_data[19]
        self.b22_serial_number = unpacked_data[20]
        self.b23_oem_id = unpacked_data[21]
        self.w24_manufacturer_id = unpacked_data[22]
        self.b26_ud0_base_offset = unpacked_data[23]
        self.b27_ud_config_p_length = unpacked_data[24]
        self.b28_device_rtt_cap = unpacked_data[25]
        self.w29_periodic_rtc_update = unpacked_data[26]
        self.b31_ufs_features_support = unpacked_data[27]
        self.b32_ffu_timeout = unpacked_data[28]
        self.b33_queue_depth = unpacked_data[29]
        self.w34_device_version = unpacked_data[30]
        self.b36_num_secure_wp_area = unpacked_data[31]
        self.l37_psa_max_data_size = unpacked_data[32]
        self.b41_psa_state_timeout = unpacked_data[33]
        self.b42_product_revision_level = unpacked_data[34]
        self.b43_rsvd = unpacked_data[35]
        self.l44_rsvd = unpacked_data[36]
        self.l48_rsvd = unpacked_data[37]
        self.l52_rsvd = unpacked_data[38]
        self.l56_rsvd = unpacked_data[39]
        self.l60_rsvd = unpacked_data[40]
        self.b64_rsvd = unpacked_data[41]
        self.w65_rsvd = unpacked_data[42]
        self.l67_rsvd = unpacked_data[43]
        self.l71_rsvd = unpacked_data[44]
        self.l75_rsvd = unpacked_data[45]
        self.l79_extended_ufs_features_support = unpacked_data[46]
        self.b83_write_booster_buffer_preserve_user_space_en = unpacked_data[47]
        self.b84_write_booster_buffer_type = unpacked_data[48]
        self.l85_num_shared_write_booster_buffer_alloc_units = unpacked_data[49]

class UFSFeaturesSupport310(UFSFeaturesSupport):
    def __init__(self) -> None:
        self.u0_ffu = 0
        self.u1_psa = 0
        self.u2_device_life_span = 0
        self.u3_refresh_op = 0
        self.u4_too_high_temp = 0
        self.u5_too_low_temp = 0
        self.u6_extended_temp = 0
        self.u7_rsvd = 0

    def from_bytes(self, payload: bytearray | int) -> None:
        if isinstance(payload, bytearray):
            unpacked_data = struct.unpack("B", payload)[0]
        else:
            unpacked_data = payload

        self.u0_ffu = CHK_BIT(unpacked_data, 0)
        self.u1_psa = CHK_BIT(unpacked_data, 1)
        self.u2_device_life_span = CHK_BIT(unpacked_data, 2)
        self.u3_refresh_op = CHK_BIT(unpacked_data, 3)
        self.u4_too_high_temp = CHK_BIT(unpacked_data, 4)
        self.u5_too_low_temp = CHK_BIT(unpacked_data, 5)
        self.u6_extended_temp = CHK_BIT(unpacked_data, 6)
        self.u7_rsvd = CHK_BIT(unpacked_data, 7)

class ExtendedUFSFeaturesSupport310(ExtendedUFSFeaturesSupport):
    def __init__(self) -> None:
        self.u0_ffu = 0
        self.u1_psa = 0
        self.u2_device_life_span = 0
        self.u3_refresh_op = 0
        self.u4_too_high_temp = 0
        self.u5_too_low_temp = 0
        self.u6_extended_temp = 0
        self.u7_rsvd = 0
        self.u8_write_booster = 0
        self.u9_performance_throttling = 0
        self.q10_rsvd = 0
        self.q18_rsvd = 0
        self.l26_rsvd = 0
        self.w30_rsvd = 0

    def from_bytes(self, payload: bytearray | int) -> None:
        if isinstance(payload, bytearray):
            unpacked_data = struct.unpack("B", payload)[0]
        else:
            unpacked_data = payload

        self.u0_ffu = CHK_BIT(unpacked_data, 0)
        self.u1_psa = CHK_BIT(unpacked_data, 1)
        self.u2_device_life_span = CHK_BIT(unpacked_data, 2)
        self.u3_refresh_op = CHK_BIT(unpacked_data, 3)
        self.u4_too_high_temp = CHK_BIT(unpacked_data, 4)
        self.u5_too_low_temp = CHK_BIT(unpacked_data, 5)
        self.u6_extended_temp = CHK_BIT(unpacked_data, 6)
        self.u7_rsvd = CHK_BIT(unpacked_data, 7)
        self.u8_write_booster = CHK_BIT(unpacked_data, 8)
        self.u9_performance_throttling = CHK_BIT(unpacked_data, 9)

########################### UFS Specs 3.1 end ###########################

########################### UFS Specs 4.0 ###########################

class DeviceDescriptor400(DeviceDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.b2_device = 0
        self.b3_device_class = 0
        self.b4_device_subclass = 0
        self.b5_protocol = 0
        self.b6_number_lu = 0
        self.b7_number_wlu = 0
        self.b8_boot_enable = 0
        self.b9_descr_access_en = 0
        self.b10_init_power_mode = 0
        self.b11_high_priority_lun = 0
        self.b12_secure_removal_type = 0
        self.b13_security_lu = 0
        self.b14_background_ops_term_lat = 0
        self.b15_init_active_icc_level = 0
        self.w16_spec_version = 0
        self.w18_manufacturer_date = 0
        self.b20_manufacturer_name = 0
        self.b21_product_name = 0
        self.b22_serial_number = 0
        self.b23_oem_id = 0
        self.w24_manufacturer_id = 0
        self.b26_ud0_base_offset = 0
        self.b27_ud_config_p_length = 0
        self.b28_device_rtt_cap = 0
        self.w29_periodic_rtc_update = 0
        self.b31_ufs_features_support = 0
        self.b32_ffu_timeout = 0
        self.b33_queue_depth = 0
        self.w34_device_version = 0
        self.b36_num_secure_wp_area = 0
        self.l37_psa_max_data_size = 0
        self.b41_psa_state_timeout = 0
        self.b42_product_revision_level = 0
        self.b43_rsvd = 0
        self.l44_rsvd = 0
        self.l48_rsvd = 0   # For Unified Memory Extension Standard
        self.l52_rsvd = 0
        self.l56_rsvd = 0
        self.l60_rsvd = 0
        self.b64_rsvd = 0   # For Host Performance Booster Extension Standard
        self.w65_rsvd = 0
        self.l67_rsvd = 0
        self.l71_rsvd = 0
        self.l75_rsvd = 0
        self.l79_extended_ufs_features_support = 0
        self.b83_write_booster_buffer_preserve_user_space_en = 0
        self.b84_write_booster_buffer_type = 0
        self.l85_num_shared_write_booster_buffer_alloc_units = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBBBBBBBBBBBBBHHBBBBHBBBHBBBHBLBBBLLLLLBHLLLLBBL', payload[0:89])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_device = unpacked_data[2]
        self.b3_device_class = unpacked_data[3]
        self.b4_device_subclass = unpacked_data[4]
        self.b5_protocol = unpacked_data[5]
        self.b6_number_lu = unpacked_data[6]
        self.b7_number_wlu = unpacked_data[7]
        self.b8_boot_enable = unpacked_data[8]
        self.b9_descr_access_en = unpacked_data[9]
        self.b10_init_power_mode = unpacked_data[10]
        self.b11_high_priority_lun = unpacked_data[11]
        self.b12_secure_removal_type = unpacked_data[12]
        self.b13_security_lu = unpacked_data[13]
        self.b14_background_ops_term_lat = unpacked_data[14]
        self.b15_init_active_icc_level = unpacked_data[15]
        self.w16_spec_version = unpacked_data[16]
        self.w18_manufacturer_date = unpacked_data[17]
        self.b20_manufacturer_name = unpacked_data[18]
        self.b21_product_name = unpacked_data[19]
        self.b22_serial_number = unpacked_data[20]
        self.b23_oem_id = unpacked_data[21]
        self.w24_manufacturer_id = unpacked_data[22]
        self.b26_ud0_base_offset = unpacked_data[23]
        self.b27_ud_config_p_length = unpacked_data[24]
        self.b28_device_rtt_cap = unpacked_data[25]
        self.w29_periodic_rtc_update = unpacked_data[26]
        self.b31_ufs_features_support = unpacked_data[27]
        self.b32_ffu_timeout = unpacked_data[28]
        self.b33_queue_depth = unpacked_data[29]
        self.w34_device_version = unpacked_data[30]
        self.b36_num_secure_wp_area = unpacked_data[31]
        self.l37_psa_max_data_size = unpacked_data[32]
        self.b41_psa_state_timeout = unpacked_data[33]
        self.b42_product_revision_level = unpacked_data[34]
        self.b43_rsvd = unpacked_data[35]
        self.l44_rsvd = unpacked_data[36]
        self.l48_rsvd = unpacked_data[37]
        self.l52_rsvd = unpacked_data[38]
        self.l56_rsvd = unpacked_data[39]
        self.l60_rsvd = unpacked_data[40]
        self.b64_rsvd = unpacked_data[41]
        self.w65_rsvd = unpacked_data[42]
        self.l67_rsvd = unpacked_data[43]
        self.l71_rsvd = unpacked_data[44]
        self.l75_rsvd = unpacked_data[45]
        self.l79_extended_ufs_features_support = unpacked_data[46]
        self.b83_write_booster_buffer_preserve_user_space_en = unpacked_data[47]
        self.b84_write_booster_buffer_type = unpacked_data[48]
        self.l85_num_shared_write_booster_buffer_alloc_units = unpacked_data[49]

class UFSFeaturesSupport400(UFSFeaturesSupport):
    def __init__(self) -> None:
        self.u0_ffu = 0
        self.u1_psa = 0
        self.u2_device_life_span = 0
        self.u3_refresh_op = 0
        self.u4_too_high_temp = 0
        self.u5_too_low_temp = 0
        self.u6_extended_temp = 0
        self.u7_rsvd = 0

    def from_bytes(self, payload: bytearray | int) -> None:
        if isinstance(payload, bytearray):
            unpacked_data = struct.unpack("B", payload)[0]
        else:
            unpacked_data = payload

        self.u0_ffu = CHK_BIT(unpacked_data, 0)
        self.u1_psa = CHK_BIT(unpacked_data, 1)
        self.u2_device_life_span = CHK_BIT(unpacked_data, 2)
        self.u3_refresh_op = CHK_BIT(unpacked_data, 3)
        self.u4_too_high_temp = CHK_BIT(unpacked_data, 4)
        self.u5_too_low_temp = CHK_BIT(unpacked_data, 5)
        self.u6_extended_temp = CHK_BIT(unpacked_data, 6)
        self.u7_rsvd = CHK_BIT(unpacked_data, 7)

class ExtendedUFSFeaturesSupport400(ExtendedUFSFeaturesSupport):
    def __init__(self) -> None:
        self.u0_ffu = 0
        self.u1_psa = 0
        self.u2_device_life_span = 0
        self.u3_refresh_op = 0
        self.u4_too_high_temp = 0
        self.u5_too_low_temp = 0
        self.u6_extended_temp = 0
        self.u7_rsvd = 0
        self.u8_write_booster = 0
        self.u9_performance_throttling = 0
        self.u10_adv_rpmb = 0
        self.u11_rsvd = 0
        self.u12_rsvd = 0
        self.u13_rsvd = 0
        self.u14_barrier = 0
        self.u15_clear_error_history_functionality = 0
        self.u16_ext_iid = 0
        self.u17_rsvd = 0
        self.u18_rsvd = 0

    def from_bytes(self, payload: bytearray | int) -> None:
        if isinstance(payload, bytearray):
            unpacked_data = struct.unpack("B", payload)[0]
        else:
            unpacked_data = payload

        self.u0_ffu = CHK_BIT(unpacked_data, 0)
        self.u1_psa = CHK_BIT(unpacked_data, 1)
        self.u2_device_life_span = CHK_BIT(unpacked_data, 2)
        self.u3_refresh_op = CHK_BIT(unpacked_data, 3)
        self.u4_too_high_temp = CHK_BIT(unpacked_data, 4)
        self.u5_too_low_temp = CHK_BIT(unpacked_data, 5)
        self.u6_extended_temp = CHK_BIT(unpacked_data, 6)
        self.u7_rsvd = CHK_BIT(unpacked_data, 7)
        self.u8_write_booster = CHK_BIT(unpacked_data, 8)
        self.u9_performance_throttling = CHK_BIT(unpacked_data, 9)
        self.u10_adv_rpmb = CHK_BIT(unpacked_data, 10)
        self.u11_rsvd = CHK_BIT(unpacked_data, 11)
        self.u12_rsvd = CHK_BIT(unpacked_data, 12)
        self.u13_rsvd = CHK_BIT(unpacked_data, 13)
        self.u14_barrier = CHK_BIT(unpacked_data, 14)
        self.u15_clear_error_history_functionality = CHK_BIT(unpacked_data, 15)
        self.u16_ext_iid = CHK_BIT(unpacked_data, 16)
        self.u17_rsvd = CHK_BIT(unpacked_data, 17)
        self.u18_rsvd = CHK_BIT(unpacked_data, 18)

########################### UFS Specs 4.0 end ###########################

########################### UFS Specs 4.1 ###########################

class DeviceDescriptor410(DeviceDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.b2_device = 0
        self.b3_device_class = 0
        self.b4_device_subclass = 0
        self.b5_protocol = 0
        self.b6_number_lu = 0
        self.b7_number_wlu = 0
        self.b8_boot_enable = 0
        self.b9_descr_access_en = 0
        self.b10_init_power_mode = 0
        self.b11_high_priority_lun = 0
        self.b12_secure_removal_type = 0
        self.b13_security_lu = 0
        self.b14_background_ops_term_lat = 0
        self.b15_init_active_icc_level = 0
        self.w16_spec_version = 0
        self.w18_manufacturer_date = 0
        self.b20_manufacturer_name = 0
        self.b21_product_name = 0
        self.b22_serial_number = 0
        self.b23_oem_id = 0
        self.w24_manufacturer_id = 0
        self.b26_ud0_base_offset = 0
        self.b27_ud_config_p_length = 0
        self.b28_device_rtt_cap = 0
        self.w29_periodic_rtc_update = 0
        self.b31_ufs_features_support = 0
        self.b32_ffu_timeout = 0
        self.b33_queue_depth = 0
        self.w34_device_version = 0
        self.b36_num_secure_wp_area = 0
        self.l37_psa_max_data_size = 0
        self.b41_psa_state_timeout = 0
        self.b42_product_revision_level = 0
        self.b43_rsvd = 0
        self.l44_rsvd = 0
        self.l48_rsvd = 0   # For Unified Memory Extension Standard
        self.l52_rsvd = 0
        self.l56_rsvd = 0
        self.l60_rsvd = 0
        self.b64_rsvd = 0   # For Host Performance Booster Extension Standard
        self.w65_rsvd = 0
        self.l67_rsvd = 0
        self.l71_rsvd = 0
        self.w75_rsvd = 0
        self.w77_extended_write_booster_support = 0
        self.l79_extended_ufs_features_support = 0
        self.b83_write_booster_buffer_preserve_user_space_en = 0
        self.b84_write_booster_buffer_type = 0
        self.l85_num_shared_write_booster_buffer_alloc_units = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBBBBBBBBBBBBBHHBBBBHBBBHBBBHBLBBBLLLLLBHLLHHLBBL', payload[0:89])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_device = unpacked_data[2]
        self.b3_device_class = unpacked_data[3]
        self.b4_device_subclass = unpacked_data[4]
        self.b5_protocol = unpacked_data[5]
        self.b6_number_lu = unpacked_data[6]
        self.b7_number_wlu = unpacked_data[7]
        self.b8_boot_enable = unpacked_data[8]
        self.b9_descr_access_en = unpacked_data[9]
        self.b10_init_power_mode = unpacked_data[10]
        self.b11_high_priority_lun = unpacked_data[11]
        self.b12_secure_removal_type = unpacked_data[12]
        self.b13_security_lu = unpacked_data[13]
        self.b14_background_ops_term_lat = unpacked_data[14]
        self.b15_init_active_icc_level = unpacked_data[15]
        self.w16_spec_version = unpacked_data[16]
        self.w18_manufacturer_date = unpacked_data[17]
        self.b20_manufacturer_name = unpacked_data[18]
        self.b21_product_name = unpacked_data[19]
        self.b22_serial_number = unpacked_data[20]
        self.b23_oem_id = unpacked_data[21]
        self.w24_manufacturer_id = unpacked_data[22]
        self.b26_ud0_base_offset = unpacked_data[23]
        self.b27_ud_config_p_length = unpacked_data[24]
        self.b28_device_rtt_cap = unpacked_data[25]
        self.w29_periodic_rtc_update = unpacked_data[26]
        self.b31_ufs_features_support = unpacked_data[27]
        self.b32_ffu_timeout = unpacked_data[28]
        self.b33_queue_depth = unpacked_data[29]
        self.w34_device_version = unpacked_data[30]
        self.b36_num_secure_wp_area = unpacked_data[31]
        self.l37_psa_max_data_size = unpacked_data[32]
        self.b41_psa_state_timeout = unpacked_data[33]
        self.b42_product_revision_level = unpacked_data[34]
        self.b43_rsvd = unpacked_data[35]
        self.l44_rsvd = unpacked_data[36]
        self.l48_rsvd = unpacked_data[37]
        self.l52_rsvd = unpacked_data[38]
        self.l56_rsvd = unpacked_data[39]
        self.l60_rsvd = unpacked_data[40]
        self.b64_rsvd = unpacked_data[41]
        self.w65_rsvd = unpacked_data[42]
        self.l67_rsvd = unpacked_data[43]
        self.l71_rsvd = unpacked_data[44]
        self.w75_rsvd = unpacked_data[45]
        self.w77_extended_write_booster_support = unpacked_data[46]
        self.l79_extended_ufs_features_support = unpacked_data[47]
        self.b83_write_booster_buffer_preserve_user_space_en = unpacked_data[48]
        self.b84_write_booster_buffer_type = unpacked_data[49]
        self.l85_num_shared_write_booster_buffer_alloc_units = unpacked_data[50]

class ExtendedWriteBoosterSupport410(ExtendedWriteBoosterSupport):
    def __init__(self) -> None:
        self.u0_write_booster_buffer_resize = 0
        self.u1_fifo_partial_flush_mode = 0
        self.u2_pinned_partial_flush_mode = 0

    def from_bytes(self, payload: bytearray | int) -> None:
        if isinstance(payload, bytearray):
            unpacked_data = struct.unpack("B", payload)[0]
        else:
            unpacked_data = payload

        self.u0_write_booster_buffer_resize = CHK_BIT(unpacked_data, 0)
        self.u1_fifo_partial_flush_mode = CHK_BIT(unpacked_data, 1)
        self.u2_pinned_partial_flush_mode = CHK_BIT(unpacked_data, 2)

class UFSFeaturesSupport410(UFSFeaturesSupport):
    def __init__(self) -> None:
        self.u0_ffu = 0
        self.u1_psa = 0
        self.u2_device_life_span = 0
        self.u3_refresh_op = 0
        self.u4_too_high_temp = 0
        self.u5_too_low_temp = 0
        self.u6_extended_temp = 0
        self.u7_rsvd = 0

    def from_bytes(self, payload: bytearray | int) -> None:
        if isinstance(payload, bytearray):
            unpacked_data = struct.unpack("B", payload)[0]
        else:
            unpacked_data = payload

        self.u0_ffu = CHK_BIT(unpacked_data, 0)
        self.u1_psa = CHK_BIT(unpacked_data, 1)
        self.u2_device_life_span = CHK_BIT(unpacked_data, 2)
        self.u3_refresh_op = CHK_BIT(unpacked_data, 3)
        self.u4_too_high_temp = CHK_BIT(unpacked_data, 4)
        self.u5_too_low_temp = CHK_BIT(unpacked_data, 5)
        self.u6_extended_temp = CHK_BIT(unpacked_data, 6)
        self.u7_rsvd = CHK_BIT(unpacked_data, 7)

class ExtendedUFSFeaturesSupport410(ExtendedUFSFeaturesSupport):
    def __init__(self) -> None:
        self.u0_ffu = 0
        self.u1_psa = 0
        self.u2_device_life_span = 0
        self.u3_refresh_op = 0
        self.u4_too_high_temp = 0
        self.u5_too_low_temp = 0
        self.u6_extended_temp = 0
        self.u7_rsvd = 0
        self.u8_write_booster = 0
        self.u9_performance_throttling = 0
        self.u10_adv_rpmb = 0
        self.u11_rsvd = 0
        self.u12_device_level_exception_warning = 0
        self.u13_hid = 0
        self.u14_barrier = 0
        self.u15_clear_error_history_functionality = 0
        self.u16_ext_iid = 0
        self.u17_rsvd = 0
        self.u18_fast_recovery_mode = 0
        self.u19_rpmb_authenticated_vendor_cmd = 0
        self.u20_rsvd = 0

    def from_bytes(self, payload: bytearray | int) -> None:
        if isinstance(payload, bytearray):
            unpacked_data = struct.unpack("B", payload)[0]
        else:
            unpacked_data = payload

        self.u0_ffu = CHK_BIT(unpacked_data, 0)
        self.u1_psa = CHK_BIT(unpacked_data, 1)
        self.u2_device_life_span = CHK_BIT(unpacked_data, 2)
        self.u3_refresh_op = CHK_BIT(unpacked_data, 3)
        self.u4_too_high_temp = CHK_BIT(unpacked_data, 4)
        self.u5_too_low_temp = CHK_BIT(unpacked_data, 5)
        self.u6_extended_temp = CHK_BIT(unpacked_data, 6)
        self.u7_rsvd = CHK_BIT(unpacked_data, 7)
        self.u8_write_booster = CHK_BIT(unpacked_data, 8)
        self.u9_performance_throttling = CHK_BIT(unpacked_data, 9)
        self.u10_adv_rpmb = CHK_BIT(unpacked_data, 10)
        self.u11_rsvd = CHK_BIT(unpacked_data, 11)
        self.u12_device_level_exception_warning = CHK_BIT(unpacked_data, 12)
        self.u13_hid = CHK_BIT(unpacked_data, 13)
        self.u14_barrier = CHK_BIT(unpacked_data, 14)
        self.u15_clear_error_history_functionality = CHK_BIT(unpacked_data, 15)
        self.u16_ext_iid = CHK_BIT(unpacked_data, 16)
        self.u17_rsvd = CHK_BIT(unpacked_data, 17)
        self.u18_fast_recovery_mode = CHK_BIT(unpacked_data, 18)
        self.u19_rpmb_authenticated_vendor_cmd = CHK_BIT(unpacked_data, 19)

########################### UFS Specs 4.1 end ###########################
