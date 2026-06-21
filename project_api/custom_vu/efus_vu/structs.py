import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
        

class micron_vu_D0F4(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.eFuse_addr = self.add_field(12, 15, 'little')
        self.eFuse_value = self.add_field(16, 19, 'little')

class VU_40F4_struct(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(4096), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.efuse = []
        for i in range(64):
            self.efuse.append(self.add_field(i*4,i*4+3,'little'))
        

