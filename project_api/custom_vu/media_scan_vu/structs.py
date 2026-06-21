import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from typing import List

class micron_vu_4026(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.d12_reset_enable = self.add_field(12, 15, 'little')

class micron_vu_4028_param():
    def __init__(self) -> None:
        self.d16_die = 0
        self.d20_plane = 0
        self.d24_block = 0
        self.d28_page = 0
        self.b40_slc_mode = 0
        self.b41_bfea_bin = 0
        self.b42_page_attr = 0
        self.b43_is_blank_page = 0
        self.b44_is_partial_block = 0
        self.b45_is_em1_vb = 0

class micron_vu_4028(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(46)
        super().__init__(payload)
        self.d16_die = self.add_field(16, 19, 'little')
        self.d20_plane = self.add_field(20, 23, 'little')
        self.d24_block = self.add_field(24, 27, 'little')
        self.d28_page = self.add_field(28, 31, 'little')
        self.b40_slc_mode = self.add_field(40, 40, 'little')
        self.b41_bfea_bin = self.add_field(41, 41, 'little')
        self.b42_page_attr = self.add_field(42, 42, 'little')
        self.b43_is_blank_page = self.add_field(43, 43, 'little')
        self.b44_is_partial_block = self.add_field(44, 44, 'little')
        self.b45_is_em1_vb = self.add_field(45, 45, 'little')
        self.parameter_length = 46

class micron_vu_402F_param_with_data():
    def __init__(self)-> None:
        self.b12_is_partial_block = 0
        self.w13_pe_cycle = 0
        self.b15_is_em1 = 0

class micron_vu_402F(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.b12_is_partial_block = self.add_field(12, 12, 'little')
        self.w13_pe_cycle = self.add_field(13, 14, 'little')
        self.b15_is_em1 = self.add_field(15, 15, 'little')

class micron_vu_C085_param_with_data():
    def __init__(self)-> None:
        self.last_full_scan_group_spend_time = 0xFFFFFFFF
        self.set_open_blk_freq_in_secs = 0xFFFFFFFF
        self.set_media_scan_bin_low = 0xFF
        self.set_media_scan_bin_high = 0xFF
        self.set_scale_factor_reduce_scan_time = 0xFF
        self.last_scan_spend_time = 0xFFFFFFFF

class micron_vu_C08B(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.b12_media_scan_enable = self.add_field(12, 12, 'little')

class micron_vu_D08E_param():
    def __init__(self)-> None:
        self.b12_th_cnt = 9
        self.w14_bec_valley_th_slc = 450
        self.w16_valley_center_ecth_slc = 400
        self.w18_valley_diffec_th_slc = 450
        self.b20_valley_ofs_th_slc = 31
        self.b21_xtemp_th_delta_slc = 80
        self.b22_is_partial_block = 0
        self.b23_is_em1 = 0
        self.w24_pe_cycle = 0

class micron_vu_D08E(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.b12_th_cnt = self.add_field(12, 12, 'little')
        self.w14_bec_valley_th_slc = self.add_field(14, 15, 'little')
        self.w16_valley_center_ecth_slc = self.add_field(16, 17, 'little')
        self.w18_valley_diffec_th_slc = self.add_field(18, 19, 'little')
        self.b20_valley_ofs_th_slc = self.add_field(20, 20, 'little')
        self.b21_xtemp_th_delta_slc = self.add_field(21, 21, 'little')
        self.b22_is_partial_block = self.add_field(22, 22, 'little')
        self.b23_is_em1 = self.add_field(23, 23, 'little')
        self.w24_pe_cycle = self.add_field(24, 25, 'little')
    
#---------------------data in struct---------------------
class get_bec_histogram_struct(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.tlc_histogram_die0 = bytearray()
        self.tlc_histogram_die1 = bytearray()
        self.tlc_histogram_die2 = bytearray()
        self.tlc_histogram_die3 = bytearray()
        self.tlc_histogram_die0 = payload[0:383]
        self.tlc_histogram_die1 = payload[384:767]
        self.tlc_histogram_die2 = payload[768:1151]
        self.tlc_histogram_die3 = payload[1152:1535]

class get_media_scan_status_struct(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.media_scan_status = self.add_field(0, 0, 'little')
        self.bec = self.add_field(1, 2, 'little')
        self.diff_ec = self.add_field(3, 4, 'little')
        self.center_ec = self.add_field(5, 6, 'little')
        self.arc_offset = self.add_field(7, 7, 'little')

class get_media_scan_param_struct(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.scanned_blocks=[]
        self.scan_ins_num = self.add_field(0, 3, 'little')
        self.elapsed_time = self.add_field(4, 7, 'little')
        self.long_power_off_flag = self.add_field(8, 11, 'little')
        self.is_ongoing = self.add_field(12, 15, 'little')
        self.cur_scan_vb = self.add_field(16, 19, 'little')
        self.scan_status = self.add_field(20, 23, 'little')
        self.media_scan_open_freq_in_sec = self.add_field(24, 27, 'little')
        self.media_scan_status = self.add_field(28, 31, 'little')
        self.cur_scan_page = self.add_field(32, 35, 'little')
        self.finish_group_num = self.add_field(36, 39, 'little')
        self.scan_group = self.add_field(40, 43, 'little')
        self.pon_scan = self.add_field(44, 47, 'little')
        self.scan_cnt = self.add_field(48, 51, 'little')
        start_off = 52
        for i in range(self.scan_cnt.value):
            vb = self.add_field(start_off, start_off+3, 'little')
            self.scanned_blocks.append(vb.value)
            start_off+=4

        self.media_scan_percentage = self.add_field(start_off , start_off+3, 'little')

class set_media_scan_param_struct(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)        
        self.last_full_scan_group_spend_time = self.add_field(0, 3, 'little')
        self.set_open_blk_freq_in_secs = self.add_field(4, 7, 'little')
        self.set_media_scan_bin_low = self.add_field(8, 8, 'little')
        self.set_media_scan_bin_high = self.add_field(9, 9, 'little')
        self.set_scale_factor_reduce_scan_time = self.add_field(11, 11, 'little')
        self.last_scan_spend_time = self.add_field(12, 15, 'little')

class get_media_scan_thresholds_struct(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.Evt1_Mask = self.add_field(0, 3, 'little')
        self.Evt_Mask = self.add_field(4, 7, 'little')
        self.diff_ec = self.add_field(3, 4, 'little')
        self.center_ec = self.add_field(5, 6, 'little')
        self.arc_offset = self.add_field(7, 7, 'little')        