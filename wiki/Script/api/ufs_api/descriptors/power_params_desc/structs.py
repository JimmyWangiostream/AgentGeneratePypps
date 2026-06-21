import struct
from Script.api.struct_helper import *


# Define empty classes for inheritance and type hint usage
class PowerParametersDescriptor(PacketParserABC):
    def from_bytes(self, payload: bytearray) -> None:
        pass

########################### UFS Specs 3.1 ###########################

class PowerParametersDescriptor310(PowerParametersDescriptor):
    _length = 16

    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        for i in range(self._length):
            setattr(self, f"w{i*2+2}_active_icc_levels_vcc_{i}", 0)
        for i in range(self._length):
            setattr(self, f"w{i*2+34}_active_icc_levels_vccq_{i}", 0)
        for i in range(self._length):
            setattr(self, f"w{i*2+66}_active_icc_levels_vccq2_{i}", 0)
        
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BB' + 'H' * self._length * 3
        unpacked_data = struct.unpack(format_string, payload[0:98])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        for i in range(self._length):
            setattr(self, f"w{i*2+2}_active_icc_levels_vcc_{i}", unpacked_data[i+2])
        for i in range(self._length):
            setattr(self, f"w{i*2+34}_active_icc_levels_vccq_{i}", unpacked_data[i+18])
        for i in range(self._length):
            setattr(self, f"w{i*2+66}_active_icc_levels_vccq2_{i}", unpacked_data[i+34])

########################### UFS Specs 3.1 end ###########################

########################### UFS Specs 4.0 ###########################

class PowerParametersDescriptor400(PowerParametersDescriptor):
    _length = 16

    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        for i in range(self._length):
            setattr(self, f"w{i * 2 + 2}_active_icc_levels_vcc_{i}", 0)
        for i in range(self._length):
            setattr(self, f"w{i * 2 + 34}_active_icc_levels_vccq_{i}", 0)
        for i in range(self._length):
            setattr(self, f"w{i * 2 + 66}_active_icc_levels_vccq2_{i}", 0)

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BB' + 'H' * self._length * 3
        unpacked_data = struct.unpack(format_string, payload[0:98])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        for i in range(self._length):
            setattr(self, f"w{i * 2 + 2}_active_icc_levels_vcc_{i}", unpacked_data[i + 2])
        for i in range(self._length):
            setattr(self, f"w{i * 2 + 34}_active_icc_levels_vccq_{i}", unpacked_data[i + 18])
        for i in range(self._length):
            setattr(self, f"w{i * 2 + 66}_active_icc_levels_vccq2_{i}", unpacked_data[i + 34])

########################### UFS Specs 4.0 end ###########################

########################### UFS Specs 4.1 ###########################

class PowerParametersDescriptor410(PowerParametersDescriptor):
    _length = 16

    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_descriptor_idn = 0
        for i in range(self._length):
            setattr(self, f"w{i * 2 + 2}_active_icc_levels_vcc_{i}", 0)
        for i in range(self._length):
            setattr(self, f"w{i * 2 + 34}_active_icc_levels_vccq_{i}", 0)
        for i in range(self._length):
            setattr(self, f"w{i * 2 + 66}_active_icc_levels_vccq2_{i}", 0)

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BB' + 'H' * self._length * 3
        unpacked_data = struct.unpack(format_string, payload[0:98])
        self.b0_length = unpacked_data[0]
        self.b1_descriptor_idn = unpacked_data[1]
        for i in range(self._length):
            setattr(self, f"w{i * 2 + 2}_active_icc_levels_vcc_{i}", unpacked_data[i + 2])
        for i in range(self._length):
            setattr(self, f"w{i * 2 + 34}_active_icc_levels_vccq_{i}", unpacked_data[i + 18])
        for i in range(self._length):
            setattr(self, f"w{i * 2 + 66}_active_icc_levels_vccq2_{i}", unpacked_data[i + 34])

########################### UFS Specs 4.1 end ###########################
