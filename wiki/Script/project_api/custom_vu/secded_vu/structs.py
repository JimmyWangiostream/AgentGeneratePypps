import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from Script.api.util.functions import dumpfile

class micron_vu_40BD(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(52)
        super().__init__(payload)
        self.opCode = self.add_field(12, 15, 'little')