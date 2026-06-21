import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from typing import List

class micron_vu_C088(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.bParameter0 = self.add_field(12, 12, 'little')
        
class micron_vu_C087(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.bParameter0 = self.add_field(12, 12, 'little')
        self.bParameter1 = self.add_field(13, 14, 'little')
        self.bParameter2 = self.add_field(15, 15, 'little')
        
class micron_vu_40C5(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        
        
class BookingQueueUnit(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.CorrectedBits = self.add_field(0, 3, 'little')
        self.LogicalVBNumber = self.add_field(4, 7, 'little')
        self.TheBookingUser = self.add_field(8, 11, 'little')
        
class BookingQueue(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        ALL_VB = (len(payload)-4)//12
        self.LogicalVBNumberInBookingQueue = self.add_field(0, 3, 'little')
        self.BookingQueueVB:List[BookingQueueUnit] = []
        offset = 4
        for vb in range(ALL_VB):
            self.BookingQueueVB.append(BookingQueueUnit(payload, offset+vb*12, offset+(vb+1)*12-1))
        