import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class PSAMigrationState(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.IsPsaOngoing = self.add_field(0,3, 'little')
        self.HostReadWithPSATrim = self.add_field(4,7, 'little')

class PSABufferSize(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.RemainPSABufferSize = self.add_field(0,3, 'little')

class PSAPostReflowProgress(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.PercentageForSLCPSAblocks = self.add_field(0,3, 'little')
        self.PercentageForSLCPSAblocks2 = self.add_field(4,7, 'little')
        self.ZeroConstant = self.add_field(8,11, 'little') 