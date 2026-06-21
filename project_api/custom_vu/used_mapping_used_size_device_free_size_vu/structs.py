import struct
from Script.api.struct_helper import PacketComposerABC, PacketParserABC, PacketParserComposerABC, BITPacketParserComposerABC
from Script.project_api.structs import micron_vendor_cmd

class micron_vu_40A8(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.mode = self.add_field(12, 15, 'little')
        self.lunid = self.add_field(16, 19, 'little')
        self.startlba = self.add_field(20, 23, 'little')
        self.length = self.add_field(24, 27, 'little')





