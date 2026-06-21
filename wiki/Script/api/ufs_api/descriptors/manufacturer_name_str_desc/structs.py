import struct
from Script.api.struct_helper import *


# Define empty classes for inheritance and type hint usage
class ManufacturerNameStringDescriptor(PacketParserABC):
    def from_bytes(self, payload: bytearray) -> None:
        pass

########################### UFS Specs 3.1 ###########################

class ManufacturerNameStringDescriptor310(ManufacturerNameStringDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.w2_uc_0 = 0
        self.w4_uc_1 = 0
        self.w6_uc_2 = 0
        self.w8_uc_3 = 0
        self.w10_uc_4 = 0
        self.w12_uc_5 = 0
        self.w14_uc_6 = 0
        self.w16_uc_7 = 0
        
    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBHHHHHHHH', payload[0:18])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.w2_uc_0 = unpacked_data[2]
        self.w4_uc_1 = unpacked_data[3]
        self.w6_uc_2 = unpacked_data[4]
        self.w8_uc_3 = unpacked_data[5]
        self.w10_uc_4 = unpacked_data[6]
        self.w12_uc_5 = unpacked_data[7]
        self.w14_uc_6 = unpacked_data[8]
        self.w16_uc_7 = unpacked_data[9]

########################### UFS Specs 3.1 end ###########################

########################### UFS Specs 4.0 ###########################

class ManufacturerNameStringDescriptor400(ManufacturerNameStringDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.w2_uc_0 = 0
        self.w4_uc_1 = 0
        self.w6_uc_2 = 0
        self.w8_uc_3 = 0
        self.w10_uc_4 = 0
        self.w12_uc_5 = 0
        self.w14_uc_6 = 0
        self.w16_uc_7 = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBHHHHHHHH', payload[0:18])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.w2_uc_0 = unpacked_data[2]
        self.w4_uc_1 = unpacked_data[3]
        self.w6_uc_2 = unpacked_data[4]
        self.w8_uc_3 = unpacked_data[5]
        self.w10_uc_4 = unpacked_data[6]
        self.w12_uc_5 = unpacked_data[7]
        self.w14_uc_6 = unpacked_data[8]
        self.w16_uc_7 = unpacked_data[9]

########################### UFS Specs 4.0 end ###########################

########################### UFS Specs 4.1 ###########################

class ManufacturerNameStringDescriptor410(ManufacturerNameStringDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.w2_uc_0 = 0
        self.w4_uc_1 = 0
        self.w6_uc_2 = 0
        self.w8_uc_3 = 0
        self.w10_uc_4 = 0
        self.w12_uc_5 = 0
        self.w14_uc_6 = 0
        self.w16_uc_7 = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBHHHHHHHH', payload[0:18])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.w2_uc_0 = unpacked_data[2]
        self.w4_uc_1 = unpacked_data[3]
        self.w6_uc_2 = unpacked_data[4]
        self.w8_uc_3 = unpacked_data[5]
        self.w10_uc_4 = unpacked_data[6]
        self.w12_uc_5 = unpacked_data[7]
        self.w14_uc_6 = unpacked_data[8]
        self.w16_uc_7 = unpacked_data[9]

########################### UFS Specs 4.1 end ###########################
