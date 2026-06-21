import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class SubVBInfo(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.amount = self.add_field(0,3, 'little')
        self.logicalvb = self.add_field(4,7, 'little')
        self.notapplicable = self.add_field(8,11, 'little')
        self.physicalblock = self.add_field(12,15, 'little')
        self.FEP = self.add_field(16,19, 'little')
        self.CE = self.add_field(20,23, 'little')
        self.plane = self.add_field(24,27, 'little')
        self.NA2 = self.add_field(28, 31, 'little')
        self.erase_cnt = self.add_field(32, 35, 'little')
        self.wb_l2_logicalvb = self.add_field(36, 39, 'little')
        self.wb_l2_block = self.add_field(40, 43, 'little')
        self.wb_l2_FEP = self.add_field(44, 47, 'little')
        self.wb_l2_erase_cnt = self.add_field(48, 51, 'little')
        self.em1_l2_logicalvb = self.add_field(52, 55, 'little')
        self.em1_l2_block = self.add_field(56, 59, 'little')
        self.em1_l2_FEP = self.add_field(60, 63, 'little')
        self.em1_l2_erase_cnt = self.add_field(64, 67, 'little')
class micron_vu_40C6(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        super().__init__(payload)
        self.d12_open_block_type = self.add_field(12, 15, 'little')
        self.d16_absolute_plane_identifier = self.add_field(16, 19, 'little')
