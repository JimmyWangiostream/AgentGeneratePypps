import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd


class micron_vu_4051(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.luID = self.add_field(12, 15, 'little')
        self.lba = self.add_field(16, 19, 'little')

class physical_address_info(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(116), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.die = self.add_field(0, 3, 'little')
        self.plane = self.add_field(4, 7, 'little')
        self.virtual_block_number = self.add_field(8, 11, 'little')
        self.page = self.add_field(12, 15, 'little')
        self.offset = self.add_field(16, 19, 'little')
        self.physical_block_number_wo_BBT = self.add_field(20, 23, 'little')
        self.physical_block_number_w_BBT = self.add_field(24, 27, 'little')
        self.PPT_die = self.add_field(28, 31, 'little')
        self.PPT_plane = self.add_field(32, 35, 'little')
        self.PPT_virtual_block_number = self.add_field(36, 39, 'little')
        self.PPT_page = self.add_field(40, 43, 'little')
        self.PPT_offset = self.add_field(44, 47, 'little')
        self.PPT_physical_block_number_wo_BBT = self.add_field(48, 51, 'little')
        self.PPT_physical_block_number_w_BBT = self.add_field(52, 55, 'little')
        self.PPT2_die = self.add_field(56, 59, 'little')
        self.PPT2_plane = self.add_field(60, 63, 'little')
        self.PPT2_virtual_block_number = self.add_field(64, 67, 'little')
        self.PPT2_page = self.add_field(68, 71, 'little')
        self.PPT2_offset = self.add_field(72, 75, 'little')
        self.PPT2_physical_block_number_wo_BBT = self.add_field(76, 79, 'little')
        self.PPT2_physical_block_number_w_BBT = self.add_field(80, 83, 'little')

class micron_vu_4052(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.didId = self.add_field(12, 15, 'little')
        self.planeId = self.add_field(16, 19, 'little')
        self.logBlockId = self.add_field(20, 23, 'little')
        self.pageId = self.add_field(24, 27, 'little')
        self.virtualPageId = self.add_field(28, 31, 'little')

class logical_address_info(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(8), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.lun = self.add_field(0, 3, 'little')
        self.lba = self.add_field(4, 7, 'little')
       
class micron_vu_40D4(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.lunId = self.add_field(12, 15, 'little')
        self.hostLba = self.add_field(16, 19, 'little')


class ftl_lba(PacketParserComposerABC):
    def __init__(self, payload: bytearray= bytearray(4), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.lba = self.add_field(0, 3, 'little')

class micron_vu_40C9(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.phyBlock = self.add_field(12, 15, 'little')
        self.planeId = self.add_field(16, 19, 'little')

class Logical_VB(PacketParserComposerABC):
    def __init__(self, payload: bytearray= bytearray(4), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.logical_vb = self.add_field(0, 3, 'little')