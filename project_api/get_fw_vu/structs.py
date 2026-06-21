import struct
from Script.api.struct_helper import *

class GetFwVersion(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(22), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.FwVersion = self.add_field(0, 1, 'big')
        self.CompileVersion = self.add_field(2, 5, 'big')
        self.ControllerNand = self.add_field(6, 21, 'big')
        