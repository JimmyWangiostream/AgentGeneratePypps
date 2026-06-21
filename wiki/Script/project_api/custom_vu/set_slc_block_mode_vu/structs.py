import struct
from Script.api.struct_helper import PacketComposerABC, PacketParserABC, PacketParserComposerABC, BITPacketParserComposerABC
from Script.project_api.structs import micron_vendor_cmd

class micron_vu_D098(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.VuDynamicBlkMode = self.add_field(12, 15, 'little')
        





