import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from Script.api.util.functions import dumpfile
 

class VDET_Information(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(4), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        dumpfile("VDET_Information.bin", payload)
        super().__init__(payload, start_offset = start_offset, end_offset = end_offset)
        self.VccDropCnt = self.add_field(0, 1, 'little')
        self.VccqDropCnt = self.add_field(2, 3, 'little')


