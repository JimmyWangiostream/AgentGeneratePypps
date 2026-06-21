import struct
from Script.api.struct_helper import *


# Define empty classes for inheritance and type hint usage
class InterconnectDescriptor(PacketParserABC):
    def from_bytes(self, payload: bytearray) -> None:
        pass

########################### UFS Specs 3.1 ###########################

class InterconnectDescriptor310(InterconnectDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.w2_bcd_unipro_version = 0
        self.w4_bcd_mphy_version = 0
        
    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBHH', payload[0:6])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.w2_bcd_unipro_version = unpacked_data[2]
        self.w4_bcd_mphy_version = unpacked_data[3]

########################### UFS Specs 3.1 end ###########################

########################### UFS Specs 4.0 ###########################

class InterconnectDescriptor400(InterconnectDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.w2_bcd_unipro_version = 0
        self.w4_bcd_mphy_version = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBHH', payload[0:6])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.w2_bcd_unipro_version = unpacked_data[2]
        self.w4_bcd_mphy_version = unpacked_data[3]

########################### UFS Specs 4.0 end ###########################

########################### UFS Specs 4.1 ###########################

class InterconnectDescriptor410(InterconnectDescriptor):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        self.w2_bcd_unipro_version = 0
        self.w4_bcd_mphy_version = 0

    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBHH', payload[0:6])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        self.w2_bcd_unipro_version = unpacked_data[2]
        self.w4_bcd_mphy_version = unpacked_data[3]

########################### UFS Specs 4.0 end ###########################
