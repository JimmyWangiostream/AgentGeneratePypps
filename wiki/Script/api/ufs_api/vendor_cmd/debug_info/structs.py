from Script.api.struct_helper import *



class BBTInfo(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.hidden_bound = self.add_field(0, 1, 'big')
        self.remap_cnt = self.add_field(2, 3, 'big')
        self.bad_blk_cnt = self.add_field(4, 5, 'big')
        self.orphan_cnt = self.add_field(6, 7, 'big')
        self.orphan_cnt_slc = self.add_field(8, 9, 'big')
        self.run_tume_bad = self.add_field(10, 11, 'big')

class DebugInfo(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.pivot = self.add_field(0, 1, 'big')
        self.user_ceil = self.add_field(2, 3, 'big')
        self.user_floor = self.add_field(4, 5, 'big')
        self.max_revoke_cnt = self.add_field(6, 7, 'big')
        self.revoke_cnt = self.add_field(8, 9, 'big')
        self.last_vb = self.add_field(10, 11, 'big')
        self.status = self.add_field(12, 13, 'big')
        self.last_slc_pool_vb = self.add_field(14, 15, 'big')
        self.bbt_info = []
        start_offset = 16
        for i in range(32):
            self.bbt_info.append(BBTInfo(payload, start_offset + i*12, start_offset + (i+1)*12 -1))
        self.ehn_data_vb_cnt = self.add_field(400, 401, 'big')
        self.last_slc_pool_vb2 = self.add_field(402, 403, 'big')

        self.l1_flush_thres = self.add_field(470, 471, 'big')
        self.node_of_prog_data_0_last_prog_done_pca = self.add_field(472, 475, 'big')
        self.node_of_prog_data_1_last_prog_done_pca = self.add_field(476, 479, 'big')
        self.node_of_l1_prog_data_last_prog_done_pca = self.add_field(480, 483, 'big')
        self.prog_data_0_last_prog_done_pca = self.add_field(484, 487, 'big')
        self.prog_data_1_last_prog_done_pca = self.add_field(488, 491, 'big')
        self.l1_prog_data_last_prog_done_pca = self.add_field(492, 495, 'big')
        self.MLC_data_gc_threshold = self.add_field(496, 497, 'big')
        self.MLC_used_VB = self.add_field(498, 499, 'big')
        self.VB_list_node_address = self.add_field(512, 515, 'big')
        self.VB_list_cycle_address = self.add_field(516, 519, 'big')
        self.VB_list_group_data_address = self.add_field(520, 523, 'big')
        self.VB_list_misc_address = self.add_field(524, 527, 'big')
        self.VB_list_write_protect_address = self.add_field(528, 531, 'big')
        self.VB_list_remap_address = self.add_field(532, 535, 'big')
        self.Valid_count_table_address = self.add_field(536, 539, 'big')
        self.Write_buffer_address = self.add_field(540, 543, 'big')
        self.Copy_buffer_address = self.add_field(544, 547, 'big')
        self.Read_buffer_address = self.add_field(548, 551, 'big')
        self.PMD_cache_buffer_address = self.add_field(552, 555, 'big')
        self.PCS_register_address = self.add_field(556, 559, 'big')
        self.PMA_1_register_address = self.add_field(560, 563, 'big')
        self.PMA_0_register_address = self.add_field(564, 567, 'big')
        self.Split_info_register_address = self.add_field(568, 571, 'big')
        self.VB_list_node_length = self.add_field(572, 573, 'big')
        self.VB_list_cycle_length = self.add_field(574, 575, 'big')
        self.VB_list_group_data_length = self.add_field(576, 577, 'big')
        self.VB_list_misc_length = self.add_field(578, 579, 'big')
        self.VB_list_write_protect_length = self.add_field(580, 581, 'big')
        self.VB_list_remap_length = self.add_field(582, 583, 'big')
        self.Valid_count_table_length = self.add_field(584, 585, 'big')
        self.Write_buffer_length = self.add_field(586, 587, 'big')
        self.Copy_buffer_length = self.add_field(588, 589, 'big')
        self.Read_buffer_length = self.add_field(590, 591, 'big')
        self.PMD_cache_buffer_length = self.add_field(592, 593, 'big')
        self.PCS_register_length = self.add_field(594, 595, 'big')
        self.PMA_1_register_length = self.add_field(596, 597, 'big')
        self.PMA_0_register_length = self.add_field(598, 599, 'big')
        self.Split_info_register_length = self.add_field(600, 601, 'big')

















