import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class micron_vu_40BC(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        super().__init__(payload)
        self.b12_bIndex = self.add_field(12, 12, 'little')