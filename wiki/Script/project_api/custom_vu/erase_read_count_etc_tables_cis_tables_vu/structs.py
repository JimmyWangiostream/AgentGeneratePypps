import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class micron_vu_C083(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.Parameter0 = self.add_field(12, 15, 'little')
        self.VB_Num = self.add_field(16, 19, 'little')
        self.RC_TH_Value = self.add_field(20, 23, 'little')
class micron_vu_4097(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.Parameter0 = self.add_field(12, 12, 'little')

class CISCode(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.Channel = self.add_field(0,0, 'little')
        self.CE = self.add_field(1,1, 'little')
        self.Plane = self.add_field(2,2, 'little')
        self.Block = self.add_field(4,5, 'little')
        self.Page = self.add_field(6,7, 'little')

class TempCodePhysicalAddr(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.node_offset_4K = self.add_field_bit(0,1, 'little')
        self.plane = self.add_field_bit(2,4, 'little')
        self.LMU = self.add_field_bit(2,4, 'little')
        self.page = self.add_field_bit(7,17, 'little')
        self.DIE = self.add_field_bit(18,19, 'little')
        self.block = self.add_field_bit(20,28, 'little')
        self.reserve = self.add_field_bit(29,31, 'little')


class FWCodePhysicalAddressInfomation(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.CISCode1 = CISCode(payload, 0, 7)
        self.CISCode2 = CISCode(payload, 8, 15)
        self.TempCodeValidPlaneBitmap = self.add_field(16,19, 'little')
        self.TempCodePhysicalAddress:list[PhysicalAddress] = []
        temp_code_physical_addr_offset = 20
        for i in range(12):
            self.TempCodePhysicalAddress.append(PhysicalAddress(payload, temp_code_physical_addr_offset + 4*(i), temp_code_physical_addr_offset + 4*(i+1)-1))

class PhysicalAddress(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.offset_4K_node = self.add_field_bit(0,1, 'little')
        self.plane = self.add_field_bit(2,4, 'little')
        self.LMU = self.add_field_bit(5,6, 'little')
        self.page = self.add_field_bit(7,17, 'little')
        self.CE = self.add_field_bit(18,19, 'little')
        self.block = self.add_field_bit(20,28, 'little')

class SystemSubVBVersions(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.FTLSubVBVersion = self.add_field(0,3, 'little')
        self.FESubVBVersion = self.add_field(4,7, 'little')
        self.FTLSubVBCount = self.add_field(8,11, 'little')
        self.FESubVBCount = self.add_field(12,15, 'little')

class BBTSubVBInfo(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.Sub_VB_version = self.add_field(0,3, 'little')
        self.First_empty_page = self.add_field(4,7, 'little')
        self.Seq = self.add_field(8,11, 'little')
        self.BBT_block_count = self.add_field(12,15, 'little')
        self.Block = self.add_field(16,19, 'little')
        self.CE = self.add_field(20,23, 'little')
        self.plane = self.add_field(24,27, 'little')

class VBTypeInfo(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.VB_index = self.add_field_bit(0,9, 'little')
        self.VB_IS_RAIN_SWAP = self.add_field_bit(10,10, 'little')
        self.VB_IS_PTE = self.add_field_bit(11,11, 'little')
        self.VB_IS_CODE = self.add_field_bit(12,12, 'little')
        self.VB_IS_TABLE_REFRESH = self.add_field_bit(13,13, 'little')
        self.VB_IS_BBT = self.add_field_bit(14,14, 'little')
        self.VB_IS_Pointer = self.add_field_bit(15,15, 'little')
        self.VB_type = self.add_field_bit(20,24, 'little')
        

class ICSBadBlockPair(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.VB_index = self.add_field(0,3, 'little')
        self.invalid_VB_plane = self.add_field(4,7, 'little')



class ICSBadBlock(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.Number_of_super_block = self.add_field(0,3, 'little')
        self.ICSBadBlocks:list[ICSBadBlockPair] = []
        start_offset = 4
        for i in range(511):
            self.ICSBadBlocks.append(ICSBadBlockPair(payload, start_offset + 8*(i), start_offset + 8*(i+1)-1))