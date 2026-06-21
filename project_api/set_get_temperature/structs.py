import struct
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.struct_helper import *        
        
class GetNandTemperature(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(4096), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        dumpfile("get_nand_temperature.bin", payload)
        self.die_count_of_system = self.add_field(0, 3, 'little')
        self.temperature_of_die_0 = self.add_field(4, 4, 'little')
        self.die_0 = self.add_field(5, 5, 'little')
        self.temperature_of_die_1 = self.add_field(6, 6, 'little')
        self.die_1 = self.add_field(7, 7, 'little')
        self.temperature_of_die_2 = self.add_field(8, 8, 'little')
        self.die_2 = self.add_field(9, 9, 'little')
        self.temperature_of_die_3 = self.add_field(10, 10, 'little')
        self.die_3 = self.add_field(11, 11, 'little')                     

class SetNandTemperature(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(37), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        dumpfile("set_nand_temperature.bin", payload)
        self.bEnableSetVuTemp = self.add_field(0, 0, 'little')
        self.bEnableFFUSetVuTemp = self.add_field(1, 1, 'little')
        self.UC_TERMAL_SENSOR_1 = self.add_field(2, 3, 'little')
        self.UC_TERMAL_SENSOR_2 = self.add_field(4, 5, 'little')
        self.UC_TERMAL_SENSOR_3 = self.add_field(6, 7, 'little')
        self.NAND_TEMPERATURE_DIE_0 = self.add_field(8, 9, 'little')
        self.NAND_TEMPERATURE_DIE_1 = self.add_field(10, 11, 'little')                  
        self.NAND_TEMPERATURE_DIE_2 = self.add_field(12, 13, 'little')                  
        self.NAND_TEMPERATURE_DIE_3 = self.add_field(14, 15, 'little')                  
        self.NAND_TEMPERATURE_DIE_4 = self.add_field(16, 17, 'little')                  
        self.NAND_TEMPERATURE_DIE_5 = self.add_field(18, 19, 'little')                  
        self.NAND_TEMPERATURE_DIE_6 = self.add_field(20, 21, 'little')                  
        self.NAND_TEMPERATURE_DIE_7 = self.add_field(22, 23, 'little')                  
        self.FFU_VU_TEMPER = self.add_field(24, 24, 'little')                  
        self.Use_Delayed_fake_tmeperatures = self.add_field(25, 25, 'little')                  
        