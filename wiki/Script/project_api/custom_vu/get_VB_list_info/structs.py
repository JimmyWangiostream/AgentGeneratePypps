import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from Script.api.util.functions import dumpfile

class GetBlkList(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(324), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        dumpfile("GetBlkList.bin", payload)
        self.head_vb_in_list_blk = self.add_field(0, 3, 'little')
        self.tail_vb_in_list_blk = self.add_field(4, 7, 'little')
        self.blk_cnt_in_list_blk = self.add_field(8, 11, 'little')
        self.head_vb_in_index_blk = self.add_field(12, 15, 'little')
        self.tail_vb_in_index_blk = self.add_field(16, 19, 'little')
        self.blk_cnt_in_index_blk = self.add_field(20, 23, 'little')
        self.head_vb_in_tmp_code_blk = self.add_field(24, 27, 'little')
        self.tail_vb_in_tmp_code_blk = self.add_field(28, 31, 'little')
        self.blk_cnt_in_tmp_code_blk = self.add_field(32, 35, 'little')
        self.head_vb_in_current_pte_blk = self.add_field(36, 39, 'little')
        self.tail_vb_in_current_pte_blk = self.add_field(40, 43, 'little')
        self.blk_cnt_in_current_pte_blk = self.add_field(44, 47, 'little')
        self.head_vb_in_log_tab_blk = self.add_field(48, 51, 'little')
        self.tail_vb_in_log_tab_blk = self.add_field(52, 55, 'little')
        self.blk_cnt_vb_in_log_tab_blk = self.add_field(56, 59, 'little')
        self.head_vb_in_current_l2_em1_blk = self.add_field(60, 63, 'little')
        self.tail_vb_in_current_l2_em1_blk = self.add_field(64, 67, 'little')
        self.blk_cnt_in_current_l2_em1_blk = self.add_field(68, 71, 'little')                                   
        self.head_vb_in_current_l2_tlc = self.add_field(72, 75, 'little')
        self.tail_vb_in_current_l2_tlc = self.add_field(76, 79, 'little')
        self.blk_cnt_in_current_l2_tlc = self.add_field(80, 83, 'little')  
        self.head_vb_in_current_l2_tlc_valid_wb = self.add_field(84, 87, 'little')
        self.tail_vb_in_current_l2_tlc_valid_wb = self.add_field(88, 91, 'little')
        self.blk_cnt_in_current_l2_tlc_valid_wb = self.add_field(92, 95, 'little')  
        self.head_vb_in_gc_target_em1 = self.add_field(96, 99, 'little')
        self.tail_vb_in_gc_target_em1 = self.add_field(100, 103, 'little')
        self.blk_cnt_in_gc_target_em1 = self.add_field(104, 107, 'little')  
        self.head_vb_in_gc_target_tlc = self.add_field(108, 111, 'little')
        self.tail_vb_in_gc_target_tlc = self.add_field(112, 115, 'little')
        self.blk_cnt_in_gc_target_tlc = self.add_field(116, 119, 'little') 

        self.head_incomplete_blk_em1 = self.add_field(120, 123, 'little')
        self.tail_incomplete_blk_em1 = self.add_field(124, 127, 'little')
        self.blk_cnt_incomplete_blk_em1 = self.add_field(128, 131, 'little')


        self.head_incomplete_blk_tlc = self.add_field(132, 135, 'little')
        self.tail_incomplete_blk_tlc = self.add_field(136, 139, 'little')
        self.blk_cnt_incomplete_blk_tlc = self.add_field(140, 143, 'little')


        self.head_vb_in_current_l1 = self.add_field(144, 147, 'little')
        self.tail_vb_in_current_l1 = self.add_field(148, 151, 'little')
        self.blk_cnt_vb_in_current_l1 = self.add_field(152, 155, 'little')



        self.head_vb_in_pte_pool = self.add_field(156, 159, 'little')
        self.tail_vb_in_pte_pool = self.add_field(160, 163, 'little')
        self.blk_cnt_vb_in_pte_pool = self.add_field(164, 167, 'little')



        self.head_used_blk_pool_em1 = self.add_field(168, 171, 'little')
        self.tail_used_blk_pool_em1 = self.add_field(172, 175, 'little')
        self.blk_cnt_used_blk_pool_em1 = self.add_field(176, 179, 'little')



        self.head_used_blk_pool_tlc = self.add_field(180, 183, 'little')
        self.tail_used_blk_pool_tlc = self.add_field(184, 187, 'little')
        self.blk_cnt_used_blk_pool_tlc = self.add_field(188, 191, 'little')




        self.head_used_blk_pool_tlc_wb = self.add_field(192, 195, 'little')
        self.tail_used_blk_pool_tlc_wb = self.add_field(196, 199, 'little')
        self.blk_cnt_used_blk_pool_tlc_wb = self.add_field(200, 203, 'little')



        self.head_current_l3_em1 = self.add_field(204, 207, 'little')
        self.tail_current_l3_em1 = self.add_field(208, 211, 'little')
        self.blk_cnt_current_l3_em1 = self.add_field(212, 215, 'little')


        self.head_current_l3_tlc = self.add_field(216, 219, 'little')
        self.tail_current_l3_tlc = self.add_field(220, 223, 'little')
        self.blk_cnt_current_l3_tlc = self.add_field(224, 227, 'little')



        self.head_current_l3_tlc_wb = self.add_field(228, 231, 'little')
        self.tail_current_l3_tlc_wb = self.add_field(232, 235, 'little')
        self.blk_cnt_current_l3_tlc_wb = self.add_field(236, 239, 'little')



        self.head_rain_swap_em1 = self.add_field(240, 243, 'little')
        self.tail_rain_swap_em1 = self.add_field(244, 247, 'little')
        self.blk_cnt_rain_swap_em1 = self.add_field(248, 251, 'little')



        self.head_rain_swap_wb = self.add_field(252, 255, 'little')
        self.tail_rain_swap_wb = self.add_field(256, 259, 'little')
        self.blk_cnt_rain_swap_wb = self.add_field(260, 263, 'little')



        self.head_rain_swap_tlc = self.add_field(264, 267, 'little')
        self.tail_rain_swap_tlc = self.add_field(268, 271, 'little')
        self.blk_cnt_rain_swap_tlc = self.add_field(272, 275, 'little')


        self.head_rain_temp_rain = self.add_field(276, 279, 'little')
        self.tail_rain_temp_rain = self.add_field(280, 283, 'little')
        self.blk_cnt_rain_temp_rain = self.add_field(284, 287, 'little')


        self.head_free_blk_queue_em1 = self.add_field(288, 291, 'little')
        self.tail_free_blk_queue_em1 = self.add_field(292, 295, 'little')
        self.blk_cnt_free_blk_queue_em1 = self.add_field(296, 299, 'little')


        self.head_free_blk_queue_tlc = self.add_field(300, 303, 'little')
        self.tail_free_blk_queue_tlc = self.add_field(304, 307, 'little')
        self.blk_cnt_free_blk_queue_tlc = self.add_field(308, 311, 'little')


        

        self.head_free_blk_queue_table = self.add_field(312, 315, 'little')
        self.tail_free_blk_queue_table = self.add_field(316, 319, 'little')
        self.blk_cnt_free_blk_queue_table = self.add_field(320, 323, 'little')


class MmesgEventLogBlockInformation(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(324), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        dumpfile("MmesgEventLogBlockInformation.bin", payload)
        self.amount_double_word_of_product_output = self.add_field(0, 3, 'little') #Mmesg data payload size(4BYTE based)
        self.event_log_pb_cnt = self.add_field(4, 7, 'little') # max num = ce * 6(plane)
        self.event_log_nand_physical_block_0_location_ce0 = self.add_field(8, 11, 'little')
        self.event_log_nand_physical_block_1_location_ce0 = self.add_field(12,15, 'little')
        self.event_log_nand_physical_block_2_location_ce0 = self.add_field(16, 19, 'little')
        self.event_log_nand_physical_block_3_location_ce0 = self.add_field(20, 23, 'little')
        self.event_log_nand_physical_block_4_location_ce0 = self.add_field(24, 27, 'little')
        self.event_log_nand_physical_block_5_location_ce0 = self.add_field(28, 31, 'little')

        self.event_log_nand_physical_block_0_location_ce1 = self.add_field(32, 35, 'little')
        self.event_log_nand_physical_block_1_location_ce1 = self.add_field(36, 39, 'little')
        self.event_log_nand_physical_block_2_location_ce1 = self.add_field(40, 43, 'little')
        self.event_log_nand_physical_block_3_location_ce1 = self.add_field(44, 47, 'little')
        self.event_log_nand_physical_block_4_location_ce1 = self.add_field(48, 51, 'little')
        self.event_log_nand_physical_block_5_location_ce1 = self.add_field(52, 55, 'little')
        

        self.event_log_nand_physical_block_0_location_ce2 = self.add_field(56, 59, 'little')
        self.event_log_nand_physical_block_1_location_ce2 = self.add_field(60, 63, 'little')
        self.event_log_nand_physical_block_2_location_ce2 = self.add_field(64, 67, 'little')
        self.event_log_nand_physical_block_3_location_ce2 = self.add_field(68, 71, 'little')
        self.event_log_nand_physical_block_4_location_ce2 = self.add_field(72, 75, 'little')
        self.event_log_nand_physical_block_5_location_ce2 = self.add_field(76, 79, 'little')


        self.event_log_nand_physical_block_0_location_ce3 = self.add_field(80, 83, 'little')
        self.event_log_nand_physical_block_1_location_ce3 = self.add_field(84, 87, 'little')
        self.event_log_nand_physical_block_2_location_ce3 = self.add_field(88, 91, 'little')
        self.event_log_nand_physical_block_3_location_ce3 = self.add_field(92, 95, 'little')
        self.event_log_nand_physical_block_4_location_ce3 = self.add_field(96, 99, 'little')
        self.event_log_nand_physical_block_5_location_ce3 = self.add_field(100, 103, 'little')

        self.mmseg_log_pb_cnt = self.add_field(104, 107, 'little') # max num = ce * 6(plane)
        self.event_log_nand_physical_block_0_location_ce0 = self.add_field(108, 111, 'little')
    