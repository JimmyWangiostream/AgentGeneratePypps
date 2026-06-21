import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from typing import List, Tuple, Optional

class Plane_based_RAIN_encoding_state(BITPacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.Table_RAIN_encoding_state = self.add_field_bit(0, 0, 'little')
        self.S_CHK_RAIN_encoding_state = self.add_field_bit(1, 1, 'little')
        self.Table_RAIN_recovery_state = self.add_field_bit(4, 4, 'little')
        self.S_CHK_RAIN_recovery_state = self.add_field_bit(5, 5, 'little')

class Open_Host_VB_simple_RAIN_encoding_state(BITPacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.Open_Host_WB_simple_RAIN_encoding_state = self.add_field_bit(0, 0, 'little')
        self.Open_Host_TLC_simple_RAIN_encoding_state = self.add_field_bit(1, 1, 'little')
        self.Open_Host_EM1_simple_RAIN_encoding_state = self.add_field_bit(2, 2, 'little')
        self.Open_Host_WB_simple_RAIN_recovery_state = self.add_field_bit(4, 4, 'little')
        self.Open_Host_TLC_simple_RAIN_recovery_state = self.add_field_bit(5, 5, 'little')
        self.Open_Host_EM1_simple_RAIN_recovery_state = self.add_field_bit(6, 6, 'little')

class Open_Host_VB_Full_Block_Protection_RAIN_encoding_state(BITPacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.Open_Host_TLC_FBP_RAIN_encoding_state = self.add_field_bit(0, 0, 'little')
        self.Open_Host_WB_FBP_RAIN_encoding_state = self.add_field_bit(1, 1, 'little')
        # self.reserved = self.add_field_bit(2, 2, 'little')
        self.Open_Host_EM1_FBP_RAIN_encoding_state = self.add_field_bit(3, 3, 'little')
        self.Open_Host_TLC_FBP_RAIN_recovery_state = self.add_field_bit(4, 4, 'little')
        self.Open_Host_WB_FBP_RAIN_recovery_state = self.add_field_bit(5, 5, 'little')
        self.Open_Host_EM1_FBP_RAIN_recovery_state = self.add_field_bit(6, 6, 'little')
class Global_permanent_RAIN_enable_flag(BITPacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.Global_permanent_RAIN_encoding_enable_flag = self.add_field_bit(0, 0, 'little')
        self.Global_permanent_RAIN_recovery_enable_flag = self.add_field_bit(1, 1, 'little')


class Permanent_RAIN_enable_bitmap(BITPacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.Open_Host_WB_encoding = self.add_field_bit(0, 0, 'little')
        self.Open_Host_TLC_encoding = self.add_field_bit(1, 1, 'little')
        self.Open_Host_EM1_encoding = self.add_field_bit(2, 2, 'little')
        self.Open_Host_WB_recovery = self.add_field_bit(4, 4, 'little')
        self.Open_Host_TLC_recovery = self.add_field_bit(5, 5, 'little')
        self.Open_Host_EM1_recovery = self.add_field_bit(6, 6, 'little')
        

class current_RAIN_accumulation_count_for_each_parity(PacketParserComposerABC):
    def __init__(self, currentCE:int, payload: bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        offset = 0
        def __set_accumulation_count_list(offset:int, rain_group_cnt:int) -> tuple[int, List[List[BaseField]]]:
            byte_len = 2
            temp:List[List[BaseField]] = [[] for ce in range(currentCE)]
            for parity in range(rain_group_cnt):
                for ce in range(currentCE):
                    if ce < currentCE:
                        temp[ce].append(self.add_field(offset, offset + byte_len - 1, 'little'))
                    offset += byte_len
            return offset, temp
        
        offset, self.WB = __set_accumulation_count_list(offset=offset, rain_group_cnt=8)
        offset, self.Host_TLC = __set_accumulation_count_list(offset=offset, rain_group_cnt=24)
        offset, self.Host_EM1 = __set_accumulation_count_list(offset=offset, rain_group_cnt=8)
        offset, self.PTE = __set_accumulation_count_list(offset=offset, rain_group_cnt=1)
        offset, self.LOG = __set_accumulation_count_list(offset=offset, rain_group_cnt=1)
        offset, self.S_CHK = __set_accumulation_count_list(offset=offset, rain_group_cnt=1)
        offset, self.UECC_recovery_user = __set_accumulation_count_list(offset=offset, rain_group_cnt=1)

class RainInfo(PacketParserComposerABC):
    def __init__(self, currentCE:int, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.Plane_based_RAIN_encoding_state = Plane_based_RAIN_encoding_state(payload, 0, 0)
        self.Open_Host_VB_simple_RAIN_encoding_state = Open_Host_VB_simple_RAIN_encoding_state(payload, 4, 4)
        self.Open_Host_VB_Full_Block_Protection_RAIN_encoding_state = Open_Host_VB_Full_Block_Protection_RAIN_encoding_state(payload, 5, 5)
        self.dummy = self.add_field(8, 11, 'little')
        self.Global_permanent_RAIN_enable_flag = Global_permanent_RAIN_enable_flag(payload, 12, 12)
        self.Permanent_RAIN_enable_bitmap = Permanent_RAIN_enable_bitmap(payload, 16, 19)
        self.host_data_pageline_count_in_SLC_VB = self.add_field(20, 23, 'little')
        self.host_data_LBA_size_in_SLC_VB = self.add_field(24, 27, 'little')
        self.host_data_pageline_count_in_TLC_VB = self.add_field(28, 31, 'little')
        self.host_data_LBA_size_in_TLC_VB = self.add_field(32, 35, 'little')
        self.max_raw_pageline_count_in_in_SLC_VB = self.add_field(36, 39, 'little')
        self.max_raw_LBA_size_in_SLC_VB = self.add_field(40, 43, 'little')
        self.max_raw_pageline_count_in_in_TLC_VB = self.add_field(44, 47, 'little')
        self.max_raw_LBA_size_in_TLC_VB = self.add_field(48, 51, 'little')
        self.CE = self.add_field(52, 55, 'little')
        self.current_RAIN_accumulation_count_for_each_parity = current_RAIN_accumulation_count_for_each_parity(currentCE, payload, 56, 56+704-1)


class Table_and_S_CHK_rain_enable_disable(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.enable_table_rain_calculation_and_write = self.add_field_bit(0,0, 'little')
        self.enable_S_CHK_rain_calculation_and_write = self.add_field_bit(1,1, 'little')
        self.enable_table_rain_usage_for_table_recovery = self.add_field_bit(4,4, 'little')
        self.enable_S_CHK_rain_usage_for_table_recovery = self.add_field_bit(5,5, 'little')
        
class Host_Permanent_Rain_Enable_Disable(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.rain_write_into_last_pages_of_Write_Booster_L2_block = self.add_field_bit(0, 0, 'little')
        self.rain_write_into_last_pages_of_Host_Normal_TLC_L2_block = self.add_field_bit(1, 1, 'little')
        self.rain_write_into_last_pages_of_Host_EM1_SLC_L2_block = self.add_field_bit(2, 2, 'little')
        self.rain_usage_for_data_recovery_into_Write_Booster_L2_block = self.add_field_bit(4, 4, 'little')
        self.rain_usage_for_data_recovery_into_Host_Normal_TLC_L2_block = self.add_field_bit(5, 5, 'little')
        self.rain_usage_for_data_recovery_into_Host_EM1_SLC_L2_block = self.add_field_bit(6, 6, 'little')
        
class Host_Simple_Rain_Enable_Disable(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.parity_calculation_into_SRAM_for_Write_Booster_L2_block = self.add_field_bit(0, 0, 'little')
        self.parity_calculation_into_SRAM_for_Host_Normal_TLC_L2_block = self.add_field_bit(1, 1, 'little')
        self.parity_calculation_into_SRAM_for_Host_EM1_SLC_L2_block = self.add_field_bit(2, 2, 'little')
        self.parity_usage_for_data_recovery_into_Write_Booster_L2_block = self.add_field_bit(4, 4, 'little')
        self.parity_usage_for_data_recovery_into_Host_Normal_TLC_L2_block = self.add_field_bit(5, 5, 'little')
        self.parity_usage_for_data_recovery_into_Host_EM1_SLC_L2_block = self.add_field_bit(6, 6, 'little')

class host_full_block_protection_rain(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.rain_write_for_Host_Normal_TLC_L2_open_block = self.add_field_bit(0, 0, 'little')
        self.rain_write_for_Write_Booster_L2_open_block = self.add_field_bit(1, 1, 'little')
        self.rain_write_for_Host_EM1_SLC_L2_open_block = self.add_field_bit(3, 3, 'little')
        self.rain_usage_for_data_recovery_for_Normal_TLC_L2_open_block = self.add_field_bit(4, 4, 'little')
        self.rain_usage_for_data_recovery_for_Write_Booster_L2_open_block = self.add_field_bit(5, 5, 'little')
        self.rain_usage_for_data_recovery_for_Host_EM1_SLC_L2_open_block = self.add_field_bit(6, 6, 'little')

class micron_vu_4055(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.rain_user = self.add_field(12, 12, 'little')
        self.group = self.add_field(13, 13, 'little')

class micron_vu_D08B(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.Table_and_S_CHK_rain_enable_disable = Table_and_S_CHK_rain_enable_disable(payload, 12, 12)
        self.Host_Permanent_Rain_Enable_Disable = Host_Permanent_Rain_Enable_Disable(payload, 13, 13)
        self.Host_Simple_Rain_Enable_Disable = Host_Simple_Rain_Enable_Disable(payload, 14, 14)
        self.host_full_block_protection_rain = host_full_block_protection_rain(payload, 16, 16)
        
        # self.Table_and_S_CHK_rain_enable_disable = self.add_field(12, 12, 'little')
        # self.Host_Permanent_Rain_Enable_Disable = self.add_field(13, 13, 'little')
        # self.Host_Simple_Rain_Enable_Disable = self.add_field(14, 14, 'little')
        # self.host_full_block_protection_rain = self.add_field(16, 16, 'little')

