import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class micron_vu_40C0(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.vbNum = self.add_field(12, 15, 'little')
        self.tableVBDataCheck = self.add_field(20, 23, 'little')

class VPCT_values(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.VPCT_IS_TLC = self.add_field_bit(31,31, 'little')
        # self.Reserved = self.add_field_bit(30,30, 'little')
        self.VPCT_IS_RPMB_EM1_GC_SRC = self.add_field_bit(29,29, 'little')
        self.VPCT_IS_OPEN = self.add_field_bit(28,28, 'little')
        self.VPCT_IS_GC_SRC = self.add_field_bit(27,27, 'little')
        self.VPCT_IS_PARTIAL_BLOCK = self.add_field_bit(26,26, 'little')
        # self.Reserved = self.add_field_bit(25,25, 'little')
        self.VPCT_NEED_UNMAP_PPTR = self.add_field_bit(24,24, 'little')
        # self.Reserved = self.add_field_bit(23,23, 'little')
        # self.Reserved = self.add_field_bit(22,22, 'little')
        # self.Reserved = self.add_field_bit(21,21, 'little')
        # self.Reserved = self.add_field_bit(20,20, 'little')
        self.VPC = self.add_field_bit(0,20, 'little')

class VBINFO_values(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.VBINFO_BIT_RSV = self.add_field_bit(0,0, 'little')
        self.VBINFO_BIT_PMNTRAINEN = self.add_field_bit(1,1, 'little')
        self.VBINFO_BIT_IS_APL = self.add_field_bit(2,2, 'little')
        self.VBINFO_BIT_PSA = self.add_field_bit(3,3, 'little')
        self.VBINFO_NOT_RSCAN = self.add_field_bit(4,4, 'little')
        self.VBINFO_BIT_EM1_NORMAL = self.add_field_bit(5,5, 'little')
        self.VBINFO_BIT_RPMB = self.add_field_bit(6,6, 'little')
        self.VBINFO_BIT_GC_FG_QUEUE = self.add_field_bit(7,7, 'little')
        self.VBINFO_BIT_GC_BG_QUEUE = self.add_field_bit(8,8, 'little')
        self.VBINFO_TEMP_FULL_BLK_PROTECTION_RAIN = self.add_field_bit(9,9, 'little')
        self.VBINFO_TEMP_SWAP_BLK_PROTECTION_RAIN = self.add_field_bit(10,10, 'little')
        self.VBINFO_CLOSE_BLK_PARTIAL_STATIC = self.add_field_bit(11,11, 'little')
        self.VBINFO_BIT_GC_SOURCE = self.add_field_bit(12,12, 'little')
        self.VBINFO_BIT_GC_DEST = self.add_field_bit(13,13, 'little')
        self.VBINFO_BIT_COLD_RISKY = self.add_field_bit(14,14, 'little')
        self.VBINFO_BIT_HOT_RISKY = self.add_field_bit(15,15, 'little')



