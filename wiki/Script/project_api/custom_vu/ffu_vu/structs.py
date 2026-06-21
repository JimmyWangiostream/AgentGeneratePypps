import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from Script.api.util.functions import dumpfile

class micron_vu_4077(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        super().__init__(payload)


class FFU_patch_count(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(4), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.patch_Trial_Count = self.add_field(0,1)
        self.patch_Success_Count = self.add_field(2,3)
