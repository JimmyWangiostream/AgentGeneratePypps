from abc import ABC, abstractmethod
import struct
from typing import List
from Script.api.struct_helper import *
from Script.api.ufs_api.defines.constant_define import DATA_SIZE_4K_BYTE

class FboDescriptor(PacketParserABC):
    def __init__(self) -> None:
        self.b0_length = 0
        self.w1_fbo_version = 0
        self.l3_fbo_recommended_lba_range_size = 0
        self.l7_fbo_max_lba_range_size = 0
        self.l11_fbo_min_lba_range_size = 0
        self.b15_fbo_max_lba_range_count = 0
        self.w16_fbo_lba_range_alignment = 0


    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BHLLLBH'
        unpacked_data = struct.unpack(format_string, payload[0:18])
        self.b0_length =  unpacked_data[0]
        self.w1_fbo_version =  unpacked_data[1]
        self.l3_fbo_recommended_lba_range_size =  unpacked_data[2]
        self.l7_fbo_max_lba_range_size =  unpacked_data[3]
        self.l11_fbo_min_lba_range_size =  unpacked_data[4]
        self.b15_fbo_max_lba_range_count =  unpacked_data[5]
        self.w16_fbo_lba_range_alignment =  unpacked_data[6]
class FboWriteBufferEntry0101():
    def __init__(self, start_lba : int, length : int) -> None:
        self.start_lba = start_lba
        self.length = length
        self.reserved = 0
class FboReadBufferEntry0101():
    def __init__(self, start_lba : int, length : int, regression_level : int) -> None:
        self.start_lba = start_lba
        self.length = length
        self.regression_level = regression_level
class FboWriteBufferStruct0101(PacketComposerABC):
    def __init__(self, fbo_type : int = 0, fbo_version : int = 0,car : int = 0, write_buffer_entry_list : List[FboWriteBufferEntry0101] = [] ) -> None:
        self.fbo_type = fbo_type
        self.fbo_version = fbo_version
        self.car = car
        self.fbo_write_buffer_entry_list = write_buffer_entry_list
    def to_bytes(self) -> bytearray:
        cmd_data = bytearray([0x0] * DATA_SIZE_4K_BYTE)
        cmd_data[0] = self.fbo_type #fbo type
        cmd_data[4] = self.fbo_version # version
        cmd_data[5] = len(self.fbo_write_buffer_entry_list) # number of fbo wb entries
        cmd_data[6] = self.car # car
        index = 0
        for entry in self.fbo_write_buffer_entry_list:
            cmd_data[12 + index * 8 : 16 + index * 8 ] = struct.pack('>L', entry.start_lba)
            cmd_data[16 + index * 8 : 19 + index * 8 ] = struct.pack('>L', entry.length)[1:]
            cmd_data[19 + index * 8] = entry.reserved
            index += 1
        return cmd_data

class FboReadBufferStruct0101(PacketParserABC):
    def __init__(self) -> None:
        self.fbo_type = 0
        self.fbo_version = 0
        self.number_of_fbo_read_buffer_entries = 0
        self.car = 0
        self.all_ranges_regression_level = 0
    def from_bytes(self, resp_data: bytearray) -> None:
        self.fbo_type = resp_data[0]
        self.fbo_version = resp_data[4]
        self.number_of_fbo_read_buffer_entries = resp_data[5]
        self.car = resp_data[6]
        self.all_ranges_regression_level = resp_data[7]
        fbo_read_buffer_entry_list = []
        for i in range(0, self.number_of_fbo_read_buffer_entries):
            start_lba = int.from_bytes(resp_data[12 + i * 8 : 16 + i *8], byteorder = 'big')
            length = int.from_bytes(resp_data[16 + i * 8 : 19 + i * 8], byteorder = 'big')
            regression_level = resp_data[19 + i * 8]
            fbo_read_buffer_entry_list.append(FboReadBufferEntry0101(start_lba = start_lba, length = length, regression_level = regression_level))
        self.fbo_read_buffer_entry_list = fbo_read_buffer_entry_list
