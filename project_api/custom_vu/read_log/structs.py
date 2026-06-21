import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class micron_vu_4080(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.para_0 = self.add_field(12, 15, 'little')
        self.para_1 = self.add_field(16, 19, 'little')
        self.para_2 = self.add_field(20, 23, 'little')
        self.para_3 = self.add_field(24, 27, 'little')
        self.para_4 = self.add_field(28, 31, 'little')


class micron_vu_4082(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)

