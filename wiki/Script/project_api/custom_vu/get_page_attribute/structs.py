import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class micron_vu_4010(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        super().__init__(payload)
        self.d12_page_index = self.add_field(12, 15, 'little')