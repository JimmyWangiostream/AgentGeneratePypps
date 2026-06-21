import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
class micron_vu_D048(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(52)
        super().__init__(payload)
        self.FW_CIS0 = self.add_field(12, 15, 'little')
        self.FW_CIS1 = self.add_field(16, 19, 'little')
        self.FW_CIS2 = self.add_field(20, 23, 'little')
        self.FW_CIS3 = self.add_field(24, 27, 'little')
        self.BBM_Table_EC = self.add_field(28, 31, 'little')
        self.ISP_Block_EC = self.add_field(32, 35, 'little')
        self.Pointer_Block_EC = self.add_field(36, 39, 'little')
class BB_retirement_reason(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.Type = self.add_field_bit(4,7, 'little')
        self.BlkType = self.add_field_bit(0,3, 'little')


class PBA_format(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.blockNum = self.add_field(0,2, 'little')
        self.CePlane = self.add_field(3,3, 'little')

class BB_info(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(4096), start_offset: int = AUTO_OFFSET, end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload=payload, start_offset=start_offset, end_offset=end_offset)
        self.status = self.add_field(0, 3, 'little')
        self.replaced_physical_block = self.add_field(4, 7, 'little')
        self.later_VB_count = self.add_field(8, 11, 'little')
        self.later_VB_max_count = self.add_field(12, 15, 'little')
        self.later_program_fail_VB_max_count = self.add_field(16, 19, 'little')
        self.later_erase_fail_VB_max_count = self.add_field(44, 47, 'little')
        self.early_pool_physical_VB_count = self.add_field(64, 67, 'little')
        self.reserved = self.add_field(68, 4095, 'little')
