import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
class pre_read_statistics_info(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(64), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.pre_read_enter_counter = self.add_field(0, 3, 'little')
        self.pre_read_exit_counter = self.add_field(4, 7, 'little')
        self.pre_read_exit_cause = self.add_field(8, 11, 'little')
        self.pre_read_avail_buffer_counter = self.add_field(12, 15, 'little')
        self.next_SR_command_count= self.add_field(16, 19, 'little')
        self.RR_command_count= self.add_field(20, 23, 'little')
        self.current_SR_start_lba= self.add_field(24, 27, 'little')
        self.next_SR_start_lba= self.add_field(28, 31, 'little')
        self.pre_read_start_lba= self.add_field(32, 35, 'little')
        self.pre_read_lun= self.add_field(36, 39, 'little')