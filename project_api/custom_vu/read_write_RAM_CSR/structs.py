import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class micron_vu_C0F0(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        super().__init__(payload)
        self.d12_ramStartAddress = self.add_field(12, 15, 'little')
        self.d16_byteCount = self.add_field(16, 19, 'little')

class micron_vu_4027(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        super().__init__(payload)
        self.d12_ramStartAddress = self.add_field(12, 15, 'little')
        self.d16_byteCount = self.add_field(16, 19, 'little')