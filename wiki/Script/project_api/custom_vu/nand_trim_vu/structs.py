import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from typing import cast, List


class micron_vu_4084(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.GetTrimItemCnt = self.add_field(12, 15, 'little')
        self.die:List[BaseField] = []
        self.TA_LSB:List[BaseField] = []
        self.TA_MSB:List[BaseField] = []
        self.die.append(self.add_field(16, 17, 'little'))
        self.TA_LSB.append(self.add_field(18, 18, 'little'))
        self.TA_MSB.append(self.add_field(19, 19, 'little'))
        self.die.append(self.add_field(20, 21, 'little'))
        self.TA_LSB.append(self.add_field(22, 22, 'little'))
        self.TA_MSB.append(self.add_field(23, 23, 'little'))
        self.die.append(self.add_field(24, 25, 'little'))
        self.TA_LSB.append(self.add_field(26, 26, 'little'))
        self.TA_MSB.append(self.add_field(27, 27, 'little'))
        self.die.append(self.add_field(28, 29, 'little'))
        self.TA_LSB.append(self.add_field(30, 30, 'little'))
        self.TA_MSB.append(self.add_field(31, 31, 'little'))
        
class get_trim_struct(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.GetTrimItemCnt = self.add_field(0,3, 'little')
        self.TrimValue:List[BaseField] = []
        self.rsv:List[BaseField] = []
        self.dieIndex:List[BaseField] = []
        self.TrimValue.append(self.add_field(4, 4, 'little'))
        self.rsv.append(self.add_field(5, 5, 'little'))
        self.dieIndex.append(self.add_field(6, 7, 'little'))
        self.TrimValue.append(self.add_field(8, 8, 'little'))
        self.rsv.append(self.add_field(9, 9, 'little'))
        self.dieIndex.append(self.add_field(10, 11, 'little'))
        self.TrimValue.append(self.add_field(12, 12, 'little'))
        self.rsv.append(self.add_field(13, 13, 'little'))
        self.dieIndex.append(self.add_field(14, 15, 'little'))
        self.TrimValue.append(self.add_field(16, 16, 'little'))
        self.rsv.append(self.add_field(17, 17, 'little'))
        self.dieIndex.append(self.add_field(18, 19, 'little'))

class set_trim_struct(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.ItemCount = self.add_field(0,3, 'little')
        self.ItemIndexValue:List[BaseField] = []
        self.SetTrimRegisterValue:List[BaseField] = []
        self.Reserved:List[BaseField] = []
        self.DieIndex:List[BaseField] = []
        self.TA_LSB:List[BaseField] = []
        self.TA_MSB:List[BaseField] = []
        
        self.ItemIndexValue.append(self.add_field(4, 4, 'little'))
        self.SetTrimRegisterValue.append(self.add_field(5, 5, 'little'))
        self.Reserved.append(self.add_field(6, 7, 'little'))
        self.DieIndex.append(self.add_field(8, 9, 'little'))
        self.TA_LSB.append(self.add_field(10, 10, 'little'))
        self.TA_MSB.append(self.add_field(11, 11, 'little'))
        self.ItemIndexValue.append(self.add_field(12, 12, 'little'))
        self.SetTrimRegisterValue.append(self.add_field(13, 13, 'little'))
        self.Reserved.append(self.add_field(14, 15, 'little'))
        self.DieIndex.append(self.add_field(16, 17, 'little'))
        self.TA_LSB.append(self.add_field(18, 18, 'little'))
        self.TA_MSB.append(self.add_field(19, 19, 'little'))
        self.ItemIndexValue.append(self.add_field(20, 20, 'little'))
        self.SetTrimRegisterValue.append(self.add_field(21, 21, 'little'))
        self.Reserved.append(self.add_field(22, 23, 'little'))
        self.DieIndex.append(self.add_field(24, 25, 'little'))
        self.TA_LSB.append(self.add_field(26, 26, 'little'))
        self.TA_MSB.append(self.add_field(27, 27, 'little'))
        self.ItemIndexValue.append(self.add_field(28, 28, 'little'))
        self.SetTrimRegisterValue.append(self.add_field(29, 29, 'little'))
        self.Reserved.append(self.add_field(30, 31, 'little'))
        self.DieIndex.append(self.add_field(32, 33, 'little'))
        self.TA_LSB.append(self.add_field(34, 34, 'little'))
        self.TA_MSB.append(self.add_field(35, 35, 'little'))