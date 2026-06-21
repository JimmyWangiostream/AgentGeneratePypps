import struct
from Script.api.struct_helper import *


# Define empty classes for inheritance and type hint usage
class OEMIDStringDescriptor(PacketParserABC):
    def from_bytes(self, payload: bytearray) -> None:
        pass

########################### UFS Specs 3.1 ###########################

class OEMIDStringDescriptor310(OEMIDStringDescriptor):
    _length = 126

    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        for i in range(self._length):  # From w2_uc_0 to w252_uc_125
            setattr(self, f"w{i*2+2}_uc_{i}", 0)
        
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BB' + 'H' * self._length
        unpacked_data = struct.unpack(format_string, payload[0:254])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        for i in range(self._length):
            setattr(self, f"w{i*2+2}_uc_{i}", unpacked_data[i+2])

########################### UFS Specs 3.1 end ###########################

########################### UFS Specs 4.0 ###########################

class OEMIDStringDescriptor400(OEMIDStringDescriptor):
    _length = 126

    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        for i in range(self._length):  # From w2_uc_0 to w252_uc_125
            setattr(self, f"w{i*2+2}_uc_{i}", 0)

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BB' + 'H' * self._length
        unpacked_data = struct.unpack(format_string, payload[0:254])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        for i in range(self._length):
            setattr(self, f"w{i*2+2}_uc_{i}", unpacked_data[i+2])

########################### UFS Specs 4.0 end ###########################

########################### UFS Specs 4.1 ###########################

class OEMIDStringDescriptor410(OEMIDStringDescriptor):
    _length = 126

    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        for i in range(self._length):  # From w2_uc_0 to w252_uc_125
            setattr(self, f"w{i*2+2}_uc_{i}", 0)

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BB' + 'H' * self._length
        unpacked_data = struct.unpack(format_string, payload[0:254])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        for i in range(self._length):
            setattr(self, f"w{i*2+2}_uc_{i}", unpacked_data[i+2])

########################### UFS Specs 4.1 end ###########################
