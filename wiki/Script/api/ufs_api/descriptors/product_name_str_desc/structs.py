import struct
from Script.api.struct_helper import *


# Define empty classes for inheritance and type hint usage
class ProductNameStringDescriptor(PacketParserABC):
    def from_bytes(self, payload: bytearray) -> None:
        pass

########################### UFS Specs 3.1 ###########################

class ProductNameStringDescriptor310(ProductNameStringDescriptor):
    _length = 16

    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        for i in range(self._length):
            setattr(self, f"w{i*2+2}_uc_{i}", 0)

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BB' + 'H' * self._length
        unpacked_data = struct.unpack(format_string, payload[0:34])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        for i in range(self._length):
            setattr(self, f"w{i*2+2}_uc_{i}", unpacked_data[i+2])

########################### UFS Specs 3.1 end ###########################

########################### UFS Specs 4.0 ###########################

class ProductNameStringDescriptor400(ProductNameStringDescriptor):
    _length = 16

    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        for i in range(self._length):
            setattr(self, f"w{i*2+2}_uc_{i}", 0)

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BB' + 'H' * self._length
        unpacked_data = struct.unpack(format_string, payload[0:34])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        for i in range(self._length):
            setattr(self, f"w{i*2+2}_uc_{i}", unpacked_data[i+2])

########################### UFS Specs 4.0 end ###########################

########################### UFS Specs 4.1 ###########################

class ProductNameStringDescriptor410(ProductNameStringDescriptor):
    _length = 16

    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        for i in range(self._length):
            setattr(self, f"w{i*2+2}_uc_{i}", 0)

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BB' + 'H' * self._length
        unpacked_data = struct.unpack(format_string, payload[0:34])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        for i in range(self._length):
            setattr(self, f"w{i*2+2}_uc_{i}", unpacked_data[i+2])

########################### UFS Specs 4.1 end ###########################
