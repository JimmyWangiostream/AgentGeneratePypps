import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from typing import List, Tuple, Optional

class micron_vu_40BF(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.sub_Operation = self.add_field(12, 15, 'little')
        self.input_data = self.add_field(16, 19, 'little')