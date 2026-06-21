import struct
from Script.api.struct_helper import *


# Define empty classes for inheritance and type hint usage
class DeviceHealthDescriptor(PacketParserABC):
    def from_bytes(self, payload: bytearray) -> None:
        pass

########################### UFS Specs 3.1 ###########################

class DeviceHealthDescriptor310(DeviceHealthDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.b2_pre_eol_info = 0
        self.b3_device_life_time_est_a = 0
        self.b4_device_life_time_est_b = 0
        self.q5_vendor_prop_info_1 = 0
        self.q13_vendor_prop_info_2 = 0
        self.q21_vendor_prop_info_3 = 0
        self.q29_vendor_prop_info_4 = 0
        self.l37_refresh_total_count = 0
        self.l41_refresh_progress = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBBQQQQLL', payload[0:45])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_pre_eol_info = unpacked_data[2]
        self.b3_device_life_time_est_a = unpacked_data[3]
        self.b4_device_life_time_est_b = unpacked_data[4]
        self.q5_vendor_prop_info_1 = unpacked_data[5]
        self.q13_vendor_prop_info_2 = unpacked_data[6]
        self.q21_vendor_prop_info_3 = unpacked_data[7]
        self.q29_vendor_prop_info_4 = unpacked_data[8]
        self.l37_refresh_total_count = unpacked_data[9]
        self.l41_refresh_progress = unpacked_data[10]

########################### UFS Specs 3.1 end ###########################

########################### UFS Specs 4.0 ###########################

class DeviceHealthDescriptor400(DeviceHealthDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.b2_pre_eol_info = 0
        self.b3_device_life_time_est_a = 0
        self.b4_device_life_time_est_b = 0
        self.q5_vendor_prop_info_1 = 0
        self.q13_vendor_prop_info_2 = 0
        self.q21_vendor_prop_info_3 = 0
        self.q29_vendor_prop_info_4 = 0
        self.l37_refresh_total_count = 0
        self.l41_refresh_progress = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBBQQQQLL', payload[0:45])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_pre_eol_info = unpacked_data[2]
        self.b3_device_life_time_est_a = unpacked_data[3]
        self.b4_device_life_time_est_b = unpacked_data[4]
        self.q5_vendor_prop_info_1 = unpacked_data[5]
        self.q13_vendor_prop_info_2 = unpacked_data[6]
        self.q21_vendor_prop_info_3 = unpacked_data[7]
        self.q29_vendor_prop_info_4 = unpacked_data[8]
        self.l37_refresh_total_count = unpacked_data[9]
        self.l41_refresh_progress = unpacked_data[10]

########################### UFS Specs 4.0 end ###########################

########################### UFS Specs 4.1 ###########################

class DeviceHealthDescriptor410(DeviceHealthDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.b2_pre_eol_info = 0
        self.b3_device_life_time_est_a = 0
        self.b4_device_life_time_est_b = 0
        self.q5_vendor_prop_info_1 = 0
        self.q13_vendor_prop_info_2 = 0
        self.q21_vendor_prop_info_3 = 0
        self.q29_vendor_prop_info_4 = 0
        self.l37_refresh_total_count = 0
        self.l41_refresh_progress = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBBBBQQQQLL', payload[0:45])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.b2_pre_eol_info = unpacked_data[2]
        self.b3_device_life_time_est_a = unpacked_data[3]
        self.b4_device_life_time_est_b = unpacked_data[4]
        self.q5_vendor_prop_info_1 = unpacked_data[5]
        self.q13_vendor_prop_info_2 = unpacked_data[6]
        self.q21_vendor_prop_info_3 = unpacked_data[7]
        self.q29_vendor_prop_info_4 = unpacked_data[8]
        self.l37_refresh_total_count = unpacked_data[9]
        self.l41_refresh_progress = unpacked_data[10]

########################### UFS Specs 4.1 end ###########################
