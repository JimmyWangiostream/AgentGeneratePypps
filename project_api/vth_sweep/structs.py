from __future__ import annotations   # <‑‑ 必須放在所有 import 之前
import struct
from typing import List, Dict, Final
from enum import Enum, IntEnum
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class micron_vu_401D(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.die = self.add_field(12, 15, 'little')
        self.plane = self.add_field(16, 19, 'little')
        self.block = self.add_field(20, 23, 'little')
        self.page = self.add_field(24, 27, 'little')
        self.slcMode = self.add_field(28, 31, 'little')
        self.indexIn16KPage = self.add_field(32, 35, 'little')
        self.startDAC = self.add_field(36, 37, 'little')
        self.endDAC = self.add_field(38, 39, 'little')
        self.vtMode = self.add_field(40, 40, 'little')

class VTPhysicalInformation(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.die = self.add_field_bit(0,2, 'little')
        self.vtPlane = self.add_field_bit(3,5, 'little')
        self.vtData = self.add_field_bit(6,6, 'little')
        self.errType = self.add_field_bit(7,10, 'little')
        self.multiPlane = self.add_field_bit(11,13, 'little')
        self.slcMode = self.add_field_bit(14,15, 'little')

class VTDumpInformation(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.vtBufIndex = self.add_field_bit(0,1, 'little')
        self.vtOffset = self.add_field_bit(2,9, 'little')
        self.vb = self.add_field_bit(10,19, 'little')
        self.page = self.add_field_bit(20,31, 'little')

class VTEraseCountInformation(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.ec = self.add_field_bit(0,19, 'little')
        self.ec_remainder = self.add_field_bit(20,23, 'little')
        self.validFlag = self.add_field_bit(24,31, 'little')


class vt_diff_format(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.magicNum = self.add_field(0, 3, 'little')
        self.pbInfo = VTPhysicalInformation(self.__payload, self.start_offset + 4, self.start_offset + 6)  # 第4,5 byte，即索引4到5
        self.block = self.add_field(6, 7, 'little')
        self.vtInfo = VTDumpInformation(self.__payload, self.start_offset + 8, self.start_offset + 12)
        self.ecInfo = VTEraseCountInformation(self.__payload, self.start_offset + 12, self.start_offset + 16)
        self.vtBufAddr = self.add_field(16, 19, 'little')
        self.pageAttribute = self.add_field(20, 21, 'little')
        self.isDynamicSLC = self.add_field(22, 22, 'little')
        self.rdBaseTrim = [self.add_field(23, 23, 'little'), self.add_field(24, 24, 'little'), self.add_field(25, 25, 'little')]
        self.tailFlag = self.add_field(26, 29, 'little')