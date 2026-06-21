import struct
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.struct_helper import *


class SerialNumberString(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(128), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.size_of_descriptor = self.add_field(0, 0, 'big') # > 64  will rsp fail
        self.string_type_identifier = self.add_field(1, 1, 'big') # 5
        self.unicode_string_chracter = self.add_field(2, 127, 'big')

class ProductNameString(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(128), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.unicode_string_chracter = self.add_field(0, 31, 'big')
        self.reserved = self.add_field(32, 127, 'big')

class WWYY(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(128), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.wwyy = self.add_field(0, 1, 'big')
        self.reserved = self.add_field(2, 127, 'big')

class ManufactureDate(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(128), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.manufacturedate = self.add_field(0, 1, 'big')
        self.reserved = self.add_field(2, 127, 'big')


class ASICId(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(4096), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        dumpfile("ascid.bin", payload)
        self.controller_and_nand_type_ascii = self.add_field(0, 15, 'little')
        self.nand_id_item_count = self.add_field(16, 31, 'little')
        self.die_idx_0 = self.add_field(32, 32, 'little')        
        self.nand_flash_id_idx0 = self.add_field(33, 40, 'big')
        self.die_idx_1 = self.add_field(48, 48, 'little')        
        self.nand_flash_id_idx1 = self.add_field(49, 56, 'big')
        self.die_idx_2 = self.add_field(64, 64, 'little')        
        self.nand_flash_id_idx2 = self.add_field(65, 72, 'big')
        self.die_idx_3 = self.add_field(80, 80, 'little')        
        self.nand_flash_id_idx3 = self.add_field(81, 88, 'big')
        self.reserved = self.add_field(96, 4095, 'little')

class AllManufacturingSetting(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(4096), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        dumpfile("all_manufacturing_setting.bin", payload)
        self.manufacturer_name = self.add_field(0, 15, 'little')
        self.product_name_string = self.add_field(16, 47, 'little')
        self.oem_id = self.add_field(48, 109, 'little')        
        self.reserved0 = self.add_field(110, 111, 'big')
        self.product_revision_level = self.add_field(112, 119, 'little')        
        self.reserved1 = self.add_field(120, 127, 'big')
        self.serial_number_string = self.add_field(128, 189, 'little')        
        self.reserved2 = self.add_field(190, 191, 'big')
        self.manufacturer_date = self.add_field(192, 193, 'big')        
        self.reserved3 = self.add_field(194, 207, 'big')
        self.manufacturer_id = self.add_field(208, 209, 'big')        

class GetTemperature(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(4096), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        dumpfile("get_temperature.bin", payload)
        self.die_count = self.add_field(0, 3, 'little')
        self.temp_val_die0 = self.add_field(4, 4, 'little')
        self.die_0 = self.add_field(5, 5, 'little')
        self.content_die1 = self.add_field(6, 7, 'little')
        self.content_die2 = self.add_field(8, 9, 'little')
        self.content_die3 = self.add_field(10, 11, 'little')
        
class ReadUid(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(4096), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        dumpfile("readuid.bin", payload)
        self.die_count_of_system = self.add_field(0, 3, 'little')
        self.uid_of_physical_die0 = self.add_field(4, 19, 'little')
        self.ch_die0 = self.add_field(20, 21, 'little')        
        self.ce_die0 = self.add_field(22, 22, 'little')
        self.cpu_die0 = self.add_field(23, 23, 'little')
        self.uid_of_physical_die1 = self.add_field(24, 39, 'little') #self.add_field(24, 43, 'little')
        self.ch_die1 = self.add_field(40, 41, 'little')
        self.ce_die1 = self.add_field(42, 42, 'little')
        self.cpu_die1 = self.add_field(43, 43, 'little')
        self.uid_of_physical_die2 = self.add_field(44, 59, 'little') #self.add_field(44, 63, 'little')        
        self.ch_die2 = self.add_field(60, 61, 'little')
        self.ce_die2 = self.add_field(62, 62, 'little')
        self.cpu_die2 = self.add_field(63, 63, 'little')
        self.uid_of_physical_die3 = self.add_field(64, 79, 'little')
        self.ch_die3 = self.add_field(80, 81, 'little')
        self.ce_die3 = self.add_field(82, 82, 'little')
        self.cpu_die3 = self.add_field(83, 83, 'little')
        self.reserved = self.add_field(84, 4095, 'little')        

class HealthReportForNandId(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(4096), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        dumpfile("health report.bin", payload)
        self.flash_id_ce0 = self.add_field(268, 283, 'little')
        self.flash_id_ce1 = self.add_field(284, 299, 'little')
        self.flash_id_ce2 = self.add_field(300, 315, 'little')
        self.flash_id_ce3 = self.add_field(316, 331, 'little')