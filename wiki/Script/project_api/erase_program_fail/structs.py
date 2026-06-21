import struct
from Script.api.struct_helper import *


class PhysicalAddressInformation(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(112), start_offset: int = AUTO_OFFSET, end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload=payload, start_offset=start_offset, end_offset=end_offset)
        self.BlockInfoList_0_die = self.add_field(0, 0, 'little')
        self.BlockInfoList_0_plane = self.add_field(1, 1, 'little')
        self.BlockInfoList_0_block = self.add_field(2, 3, 'little')
        self.BlockInfoList_0_page = self.add_field(4, 5, 'little')
        self.BlockInfoList_0_tg_bitmap = self.add_field(6, 6, 'little')
        self.BlockInfoList_1_die = self.add_field(7, 7, 'little')
        self.BlockInfoList_1_plane = self.add_field(8, 8, 'little')
        self.BlockInfoList_1_block = self.add_field(9, 10, 'little')
        self.BlockInfoList_1_page = self.add_field(11, 12, 'little')
        self.BlockInfoList_1_tg_bitmap = self.add_field(13, 13, 'little')
        self.BlockInfoList_2_die = self.add_field(14, 14, 'little')
        self.BlockInfoList_2_plane = self.add_field(15, 15, 'little')
        self.BlockInfoList_2_block = self.add_field(16, 17, 'little')
        self.BlockInfoList_2_page = self.add_field(18, 19, 'little')
        self.BlockInfoList_2_tg_bitmap = self.add_field(20, 20, 'little')
        self.BlockInfoList_3_die = self.add_field(21, 21, 'little')
        self.BlockInfoList_3_plane = self.add_field(22, 22, 'little')
        self.BlockInfoList_3_block = self.add_field(23, 24, 'little')
        self.BlockInfoList_3_page = self.add_field(25, 26, 'little')
        self.BlockInfoList_3_tg_bitmap = self.add_field(27, 27, 'little')
        self.reserved = self.add_field(28, 111, 'little')


class BEFailStatus(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(4096), start_offset: int = AUTO_OFFSET, end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload=payload, start_offset=start_offset, end_offset=end_offset)
        self.fail_type = self.add_field(0, 3, 'little')
        self.fail_times = self.add_field(4, 7, 'little')
        self.time_0_die = self.add_field(8, 11, 'little')
        self.time_0_plane = self.add_field(12, 15, 'little')
        self.time_0_block = self.add_field(16, 19, 'little')
        self.time_0_page = self.add_field(20, 23, 'little')
        self.time_0_tg_bitmap = self.add_field(24, 27, 'little')
        self.reserved = self.add_field(28, 4095, 'little')
