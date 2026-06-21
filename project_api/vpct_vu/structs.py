import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd


class micron_vu_4001(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.vbNum = self.add_field(12, 15, 'big')
        self.VPCT = self.add_field(16, 19, 'big')
        self.tableVBDataCheck = self.add_field(20, 23, 'big')


class micron_vu_408A(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.vbNum = self.add_field(12, 15, 'big')
        self.VPCT = self.add_field(16, 19, 'big')
        self.tableVBDataCheck = self.add_field(20, 23, 'big')






