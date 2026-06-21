import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
class triggerRPMBerase(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(1), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.triggerRPMBerase = self.add_field(0, 0, 'little')
class queryRPMBerase(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(1), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.RPMBerasestatus = self.add_field(0, 0, 'little')