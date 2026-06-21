import struct
from enum import IntEnum
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class STICKY_READ_SETTING(IntEnum):
    DISABLE = 0
    ENABLE = 1

class STICKY_READ_STATUS(IntEnum):
    SUCCESS = 0
    FAILED = 1

class STICKY_READ_OUTPUT_STATUS(IntEnum):
    STICKY_READ_NOT_ENTERED     = 0xF0
    STICKY_READ_ENTERED         = 0xF1
    INVALID_VALUE               = 0x55


class micron_vu_4066(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.option0 = self.add_field(12, 12, 'little')
        self.option1 = self.add_field(13, 13, 'little')
        self.die = self.add_field(14, 14, 'little')
        self.pageType = self.add_field(15, 15, 'little')
        self.isPSA = self.add_field(16, 16, 'little')
        self.readLast = self.add_field(17, 17, 'little')
        self.arc = self.add_field(18, 18, 'little')


class sticky_read_status(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(11), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.result= self.add_field(0, 3, 'little')
        self.stickyReadStatus = self.add_field(4, 7, 'little')
        self.offset1 = self.add_field(8, 8, 'little')
        self.offset2 = self.add_field(9, 9, 'little')
        self.offset3 = self.add_field(10, 10, 'little')