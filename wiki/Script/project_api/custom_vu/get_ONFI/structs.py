import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class ONFI_frequency(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(2), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset = start_offset, end_offset = end_offset)
        self.ONFI_frequency = self.add_field(0, 1, 'little')
        