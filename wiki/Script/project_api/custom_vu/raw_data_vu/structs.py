import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class micron_vu_4060(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(52)
        super().__init__(payload)
        self.Die = self.add_field(12, 15, 'little')
        self.Plane = self.add_field(16, 19, 'little')
        self.Block = self.add_field(20, 23, 'little')
        self.Page = self.add_field(24, 27, 'little')
        self.Data_Byte_Number = self.add_field(28, 31, 'little')
        self.SLC_Enable = self.add_field(32, 32, 'little')
        self.Ecc_Enable = self.add_field(33, 33, 'little')
        self.Scrambler_Enable = self.add_field(34, 34, 'little')
        self.REH_Enable = self.add_field(35, 35, 'little')
        self.ARC_disable = self.add_field(36, 36, 'little')
        self.psa_Enable = self.add_field(37, 37, 'little')
        self.FW_Block = self.add_field(38, 38, 'little')
        self.Bin = self.add_field(39, 39, 'little')
        self.isBadBlock = self.add_field(40, 40, 'little')
        self.SeedEcBit_Enable = self.add_field(41, 41, 'little')
        self.cfRead_Enable = self.add_field(43, 43, 'little')
        self.reserved = self.add_field(44, 44, 'little')
        self.offsetType = self.add_field(45, 45, 'little')
        self.Prefix_Offset_Lower_Page = self.add_field(46, 47, 'little')
        self.Prefix_Offset_Upper_Page = self.add_field(48, 49, 'little')
        self.Prefix_Offset_Extra_Page = self.add_field(50, 51, 'little')
        self.parameter_length = 52

class micron_vu_C060(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(52)
        super().__init__(payload)
        self.Ce = self.add_field(12, 15, 'little')
        self.Plane = self.add_field(16, 19, 'little')
        self.Block = self.add_field(20, 23, 'little')
        self.Start_Page = self.add_field(24, 25, 'little')
        self.End_Page = self.add_field(26, 27, 'little')
        self.Data_Byte_Length = self.add_field(28, 31, 'little')
        self.SLC_Enable = self.add_field(32, 32, 'little')
        self.Ecc_Enable = self.add_field(33, 33, 'little')
        self.isHost = self.add_field(34, 34, 'little')
        self.reserved = self.add_field(35, 35, 'little')
        self.FW_Block = self.add_field(36, 39, 'little')
        self.SeedEcBit_Enable = self.add_field(40, 40, 'little')
        self.reserved = self.add_field(41, 43, 'little')
        self.psaEnable = self.add_field(44, 44, 'little')
        self.parameter_length = 52
        
class micron_vu_D060(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(52)
        super().__init__(payload)
        self.Ce = self.add_field(12, 15, 'little')
        self.Plane = self.add_field(16, 19, 'little')
        self.Block = self.add_field(20, 23, 'little')
        self.SlcEnable = self.add_field(24, 27, 'little')
        self.psaEnable = self.add_field(28, 28, 'little')
