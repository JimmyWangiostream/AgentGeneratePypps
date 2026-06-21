import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
class setRPMBpassword(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(1), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.setRPMBpassword_status = self.add_field(0, 0, 'little')
class clearRPMBpassword(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(1), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.clearRPMBpassword_status = self.add_field(0, 0, 'little')
class queryRPMBpassword(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(1), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.queryRPMBpassword_status = self.add_field(0, 0, 'little')