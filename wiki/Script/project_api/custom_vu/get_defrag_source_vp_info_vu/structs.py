import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
class SoucevpInformation(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(68), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.is_successful = self.add_field(0, 3, 'little')
        self.vbprotect = self.add_field(4, 7, 'little')
        self.vbnum = self.add_field(8, 11, 'little')
        self.die = self.add_field(12, 15, 'little')
        self.plane = self.add_field(16, 19, 'little')
        self.page = self.add_field(20, 23, 'little')
        self.vpindex = self.add_field(24, 27, 'little')
        self.physicalvb_of_logicvb_acquired_byL2PVBT = self.add_field(28, 31, 'little')
        self.block_of_sourcevp_acquired_byBBT = self.add_field(32, 35, 'little')