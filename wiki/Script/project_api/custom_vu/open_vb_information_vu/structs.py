import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class OpenVBInformation(PacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET, end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload=payload, start_offset=start_offset, end_offset=end_offset)

        self.L2_Open_logical_VB_Host_TLC_number = self.add_field(0, 3, 'little')
        self.first_free_physical_page_of_L2_Open_logical_VB_Host_TLC = self.add_field(4, 7, 'little')
        self.open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC = self.add_field(8, 11, 'little')
        self.first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC = self.add_field(12, 15, 'little')
        self.open_Remap_VB_number_for_L2_Open_logical_VB_Host_TLC = self.add_field(16, 19, 'little')
        self.open_Remap_VB_number_for_GC_Open_VB_TLC = self.add_field(20, 23, 'little')
        self.open_logical_VB_number_for_EM1_L2_Host = self.add_field(24, 27, 'little')
        self.first_free_physical_page_of_EM1_L2_Host_VB = self.add_field(28, 31, 'little')
        self.open_logical_VB_number_for_EM1_GC = self.add_field(32, 35, 'little')
        self.first_free_physical_page_of_EM1_GC_VB = self.add_field(36, 39, 'little')
        self.open_Remap_VB_number_for_EM1_L2_Host = self.add_field(40, 43, 'little')
        self.open_Remap_VB_number_for_EM1_GC = self.add_field(44, 47, 'little')
        self.open_Logical_VB_of_TMP_RAIN_VB_SSU_VB = self.add_field(48, 51, 'little')
        self.open_Remap_VB_of_TMP_RAIN_VB_SSU_VB = self.add_field(52, 55, 'little')
        self.start_physical_page_of_VB_of_TMP_RAIN_VB_SSU_VB = self.add_field(56, 59, 'little')

        self.reserved_60_63 = self.add_field(60, 63, 'little')
        self.reserved_64_67 = self.add_field(64, 67, 'little')
        self.reserved_68_71 = self.add_field(68, 71, 'little')
        self.reserved_72_75 = self.add_field(72, 75, 'little')
        self.reserved_76_79 = self.add_field(76, 79, 'little')
        self.reserved_80_83 = self.add_field(80, 83, 'little')
        self.reserved_84_87 = self.add_field(84, 87, 'little')

        self.open_logical_VB_number_for_Write_Booster_WB_L2 = self.add_field(88, 91, 'little')
        self.first_free_physical_page_of_Write_Booster_WB_L2 = self.add_field(92, 95, 'little')
        self.open_Remap_VB_number_for_Write_Booster_WB_L2 = self.add_field(96, 99, 'little')
        self.open_logical_VB_number_for_RPMB_VB = self.add_field(100, 103, 'little')
        self.first_free_physical_page_of_RPMB_VB = self.add_field(104, 107, 'little')
        self.open_Remap_VB_number_for_RPMB_VB = self.add_field(108, 111, 'little')

        self.high_priority_event_log_location = self.add_field(112, 115, 'little')
        self.first_free_physical_page_for_high_priority_event_log = self.add_field(116, 119, 'little')
        self.mmesg_log_location = self.add_field(120, 123, 'little')
        self.first_free_physical_page_and_offset_for_mmesg_log = self.add_field(124, 127, 'little')

        self.reserved_128_235 = self.add_field(128, 235, 'little')
        self.reserved_236_239 = self.add_field(236, 239, 'little')
        self.reserved_240_243 = self.add_field(240, 243, 'little')
        self.reserved_244_247 = self.add_field(244, 247, 'little')
        self.reserved_248_251 = self.add_field(248, 251, 'little')
        self.reserved_252_255 = self.add_field(252, 255, 'little')

        self.open_logical_VB_number_for_SWAP_RAIN_TLC = self.add_field(256, 259, 'little')
        self.first_free_physical_page_of_SWAP_RAIN_TLC = self.add_field(260, 263, 'little')
        self.open_Remap_VB_number_for_TLC_SWAP_RAIN = self.add_field(264, 267, 'little')
        self.start_physical_page_of_parity_storage_VB_for_SWAP_RAIN_TLC = self.add_field(268, 271, 'little')
        self.is_physical_page_unrecovered_for_SWAP_RAIN_TLC = self.add_field(272, 275, 'little')

        self.open_logical_VB_number_for_SWAP_RAIN_WB = self.add_field(276, 279, 'little')
        self.first_free_physical_page_of_SWAP_RAIN_WB = self.add_field(280, 283, 'little')
        self.open_Remap_VB_number_for_SWAP_RAIN_WB = self.add_field(284, 287, 'little')
        self.start_physical_page_of_parity_storage_of_SWAP_RAIN_WB = self.add_field(288, 291, 'little')
        self.is_physical_page_unrecovered_SWAP_RAIN_WB = self.add_field(292, 295, 'little')

        self.open_logical_VB_number_for_SWAP_RAIN_EM1 = self.add_field(296, 299, 'little')
        self.first_free_physical_page_of_SWAP_RAIN_EM1 = self.add_field(300, 303, 'little')
        self.open_Remap_VB_number_for_SWAP_RAIN_EM1 = self.add_field(304, 307, 'little')
        self.start_physical_page_of_parity_storage_VB_for_SWAP_RAIN_EM1 = self.add_field(308, 311, 'little')
        self.is_physical_page_unrecovered_for_SWAP_RAIN_EM1 = self.add_field(312, 315, 'little')

        self.List_Block_VB_number_logical = self.add_field(316, 319, 'little')
        self.List_Block_VB_number_Remap = self.add_field(320, 323, 'little')
        self.List_block_First_free_physical_page = self.add_field(324, 327, 'little')

        self.PTE_Block_VB_number_logical = self.add_field(328, 331, 'little')
        self.PTE_Block_VB_number_Remap = self.add_field(332, 335, 'little')
        self.PTE_block_First_free_physical_page = self.add_field(336, 339, 'little')

        self.INDEX_VB_number_logical = self.add_field(340, 343, 'little')
        self.INDEX_VB_number_Remap = self.add_field(344, 347, 'little')
        self.INDEX_block_First_free_physical_page = self.add_field(348, 351, 'little')

        self.LOG_block_VB_number_logical = self.add_field(352, 355, 'little')
        self.LOG_Block_VB_number_Remap = self.add_field(356, 359, 'little')
        self.LOG_Block_First_free_physical_page = self.add_field(360, 363, 'little')

        self.L1_open_VB_S_CHUNK_logical_number = self.add_field(364, 367, 'little')
        self.L1_open_VB_S_CHUNK_VB_number_Remap = self.add_field(368, 371, 'little')
        self.L1_open_VB_S_CHUNK_first_free_physical_page = self.add_field(372, 375, 'little')
        self.L1_openVB_first_free_physical_page = self.add_field(376, 379, 'little')

        self.low_priority_event_log_location = self.add_field(380, 383, 'little')
        self.first_free_physical_page_for_low_priority_event_log = self.add_field(384, 387, 'little')




