import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from typing import List
default_page = 2000 # 4000page could record
class APL_Blank_Check_LSB(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(1), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.blank_result = self.add_field_bit(0,3, 'little')
class APL_Blank_Check_MSB(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(1), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.blank_result = self.add_field_bit(4,7, 'little')
class APL_Blank_Check(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(default_page), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        #self.pagelist:list[Union[APL_Blank_Check_LSB, APL_Blank_Check_MSB]] = []
        self.pagelist: List[Union[APL_Blank_Check_LSB, APL_Blank_Check_MSB]] = []
        for i in range(default_page):
            self.pagelist.append(APL_Blank_Check_LSB(payload, i, i))
            self.pagelist.append(APL_Blank_Check_MSB(payload, i, i))
        # for i in range(default_page):
        #     field_LSB: APL_Blank_Check_LSB = APL_Blank_Check_LSB(payload, i, i)
        #     self.pagelist.append(field_LSB)
        #     field_MSB: APL_Blank_Check_MSB = APL_Blank_Check_MSB(payload, i, i)
        #     self.pagelist.append(field_MSB)
    # def __getitem__(self, idx: int):
    #     """直接返回內部的 pagelist 元素。"""
    #     return self.pagelist[idx]
    # def __len__(self) -> int:
    #     """支援 len(self) → 數量"""
    #     return len(self.pagelist)
class APL_Powerloss_Check(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(default_page), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.pagelist:list[Union[APL_Blank_Check_LSB, APL_Blank_Check_MSB]] = []
        for i in range(default_page):
            self.pagelist.append(APL_Blank_Check_LSB(payload, i, i))
            self.pagelist.append(APL_Blank_Check_MSB(payload, i, i))
class APL_Get_Parameter(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(68), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.appoint_param_value = self.add_field(0, 1, 'little')
class APL_LWP_Check(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(68), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.LWP = self.add_field(0, 1, 'little')
        self.LWP_status = self.add_field(2, 3, 'little')
        self.last_reliable_page = self.add_field(4, 5, 'little')
        self.fep_status = self.add_field(6, 7, 'little')