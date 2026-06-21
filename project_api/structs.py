from abc import ABC, abstractmethod
import struct
import bitstruct
from Script.api.struct_helper import *
import copy

class micron_vendor_cmd(PacketParserComposerABC):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload, start_offset = AUTO_OFFSET, end_offset = AUTO_OFFSET)
        self.b0_opcode = self.add_field(0, 0, 'big')
        self.b1_func = self.add_field(1, 1, 'big')
        self.w2_transfer_length = self.add_field(2, 3, 'big')
        self.d4_random_stamp = self.add_field(4, 7, 'big')
        self.d8_split_pkg_index = self.add_field(8, 11, 'big')
        self.d12_reserved = self.add_field(12, 43, 'little')
        # self.b44_vu_length = self.add_field(44, 44, 'little')
        self.parameter_length = 44

class micron_vu_D078(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.d12_writecounter = self.add_field(12, 15, 'little')
        self.d16_region = self.add_field(16, 16, 'little')

class micron_vu_D079(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.d12_region = self.add_field(12, 12, 'little')
        
class micron_vu_C08C(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.b12_isMDWLSV_Disable = self.add_field(12, 12, 'little')

class micron_vu_4022(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.d12_ce = self.add_field(12, 15, 'little')
        self.d16_die = self.add_field(16, 19, 'little')
        self.d20_feature_address = self.add_field(20, 23, 'little')

class micron_vu_4023(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.d12_ce = self.add_field(12, 15, 'little')
        self.d16_die = self.add_field(16, 19, 'little')
        self.d20_feature_address = self.add_field(20, 23, 'little')
        self.d24_P1 = self.add_field(24, 27, 'little')
        self.d28_P2 = self.add_field(28, 31, 'little')
        self.d32_P3 = self.add_field(32, 35, 'little')
        self.d36_P4 = self.add_field(36, 39, 'little')

class micron_vu_40DC(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.d12_openvbtype = self.add_field(12, 12, 'little')

class micron_vu_40DD(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.w12_vbnum = self.add_field(12, 13, 'little')
        self.w14_die = self.add_field(14, 15, 'little')
        self.w16_plane = self.add_field(16, 17, 'little')
        self.w18_page = self.add_field(18, 19, 'little')
        self.w20_vpindex = self.add_field(20, 21, 'little')

class micron_vu_4048(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.l12_password = self.add_field(12, 19, 'little')
        self.b20_wpara0 = self.add_field(20, 20, 'little')
        
class micron_vu_4047(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.l12_password = self.add_field(12, 19, 'little')
        self.b20_wpara0 = self.add_field(20, 20, 'little')
        
class micron_vu_40B1(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.l12_vb = self.add_field(12, 15, 'little')
        self.l16_die = self.add_field(16, 17, 'little')

class micron_vu_D0FB(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.d12_option = self.add_field(12, 12, 'little')

class micron_vu_4067(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.l12_ce = self.add_field(12, 15, 'little')
        self.l16_plane = self.add_field(16, 19, 'little')
        self.l20_vb = self.add_field(20, 23, 'little')
        self.l24_page = self.add_field(24, 27, 'little')
        self.l29_bin = self.add_field(29, 29, 'little')

class micron_vu_40F6(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.l12_die = self.add_field(12, 15, 'little')
        self.l16_plane = self.add_field(16, 19, 'little')
        self.l16_start_blk = self.add_field(20, 23, 'little')
        self.l20_end_blk = self.add_field(24, 27, 'little')

class micron_vu_40F5(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.sub_opcode = self.add_field(12, 15, 'little')
        self.logical_vb = self.add_field(16, 19, 'little')

class micron_vu_4099(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.l12_param0 = self.add_field(12, 12, 'little')


class micron_vu_D08A(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.b12_enable_set_vu_temp = self.add_field(12, 12, 'little')
        self.b13_enable_ffu_set_vu_temp = self.add_field(13, 13, 'little')
        self.w14_UC_TERMAL_SENSOR_1 = self.add_field(14, 15, 'little')
        self.w16_UC_TERMAL_SENSOR_2 = self.add_field(16, 17, 'little')
        self.w18_UC_TERMAL_SENSOR_3 = self.add_field(18, 19, 'little')
        self.w20_NAND_TEMPERATURE_DIE_0 = self.add_field(20, 21, 'little')
        self.w22_NAND_TEMPERATURE_DIE_1 = self.add_field(22, 23, 'little')
        self.w24_NAND_TEMPERATURE_DIE_2 = self.add_field(24, 25, 'little')
        self.w26_NAND_TEMPERATURE_DIE_3 = self.add_field(26, 27, 'little')
        self.w28_NAND_TEMPERATURE_DIE_4 = self.add_field(28, 29, 'little')
        self.w30_NAND_TEMPERATURE_DIE_5 = self.add_field(30, 31, 'little')
        self.w32_NAND_TEMPERATURE_DIE_6 = self.add_field(32, 33, 'little')
        self.w34_NAND_TEMPERATURE_DIE_7 = self.add_field(34, 35, 'little')
        self.b36_FFU_VU_TEMPER = self.add_field(36, 36, 'little')
        self.b37_Use_Delayed_Fake_Temperatures = self.add_field(37, 37, 'little')
    
        
class micron_vu_D088(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.b12_if_auto_standby_enable = self.add_field(12, 12, 'little')

class micron_vu_D0B0(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.l12_enable_disable = self.add_field(12, 12, 'little')

class micron_vu_D017(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.die = self.add_field(12,12,'little')
        self.plane = self.add_field(13,13,'little')
        self.block = self.add_field(14,15,'little')
        self.error_inject_enable = self.add_field(16,16,'little')
        self.scan_type = self.add_field(17,17,'little')
        self.first_low_vt_scan = self.add_field(18,18,'little')
        self.touch_up = self.add_field(19,19,'little')
        self.low_vt_re_scan = self.add_field(20,20,'little')
        self.high_vt_scan = self.add_field(21,21,'little')
        self.switch = self.add_field(22,22,'little')
        self.index = self.add_field(23,23,'little')

class micron_vu_4071(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.isSGS = self.add_field(12, 12, 'little')

class micron_vu_C071(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.isSGS = self.add_field(12, 12, 'little')

class micron_vu_404B(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.input_vb = self.add_field(12, 15, 'little')
        self.enable_retirement = self.add_field(20, 23, 'little')
        self.b12_if_auto_standby_enable = self.add_field(12, 12, 'little')

class micron_vu_409D(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.d12_die = self.add_field(12, 15, 'little')
        self.d16_plane = self.add_field(16, 19, 'little')
        self.d20_block = self.add_field(20, 23, 'little')
        self.b24_slcmode = self.add_field(24, 24, 'little')
        self.w25_startpage = self.add_field(25, 26, 'little')
        self.w27_stoppage = self.add_field(27, 28, 'little')
        self.d25_reserved = self.add_field(25, 28, 'little')
        self.b29_opcode = self.add_field(29, 29, 'little')
        self.b30_parameter_index = self.add_field(30, 30, 'little')
        self.w30_parameter_value = self.add_field(31, 32, 'little')
        self.b33_reserved = self.add_field(33, 33, 'little')


class micron_vu_40FE(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.d12_ce = self.add_field(12, 15, 'little')
        self.d16_die = self.add_field(16, 19, 'little')

class micron_vu_40C7(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.d12_pb = self.add_field(12, 15, 'little')
        self.d16_plane = self.add_field(16, 19, 'little')
        self.d20_reserved = self.add_field(20, 43, 'little')
        self.parameter_length = 44

class micron_vu_40D6(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.d12_ce = self.add_field(12, 15, 'little')
        self.d16_plane = self.add_field(16, 19, 'little')
        self.d20_next_n = self.add_field(20, 23, 'little')
        self.d24_pool_type = self.add_field(24, 27, 'little')
        self.d28_is_cis = self.add_field(28, 31, 'little')
        self.d32_pf_on_open_data = self.add_field(32, 35, 'little')
        self.d36_reserved = self.add_field(36, 43, 'little')
        self.parameter_length = 44

class micron_vu_40F6_1(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.d12_die = self.add_field(12, 15, 'little')
        self.d16_plane = self.add_field(16, 19, 'little')
        self.d20_start_block = self.add_field(20, 23, 'little')
        self.d24_end_block = self.add_field(24, 27, 'little')
        self.d28_slc_enable = self.add_field(28, 31, 'little')
        self.d32_psa_trim_enable = self.add_field(32, 35, 'little')
        self.d36_reserved = self.add_field(36, 43, 'little')
        self.parameter_length = 44

class micron_vu_40F7(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(48)) -> None:
        super().__init__(payload)
        self.d12_die = self.add_field(12, 15, 'little')
        self.d16_plane = self.add_field(16, 19, 'little')
        self.d20_start_block = self.add_field(20, 23, 'little')
        self.d24_end_block = self.add_field(24, 27, 'little')
        self.d28_start_page = self.add_field(28, 31, 'little')
        self.d32_end_page = self.add_field(32, 35, 'little')
        self.d36_slc_enable = self.add_field(36, 39, 'little')
        self.d40_pattern = self.add_field(40, 43, 'little')
        self.d44_psa_enable = self.add_field(44, 47, 'little')
        self.parameter_length = 48

class micron_vu_40F8(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(48)) -> None:
        super().__init__(payload)
        self.w12_die = self.add_field(12, 13, 'little')
        self.w14_psa_trim = self.add_field(14, 15, 'little')
        self.d16_plane = self.add_field(16, 19, 'little')
        self.d20_start_block = self.add_field(20, 23, 'little')
        self.d24_end_block = self.add_field(24, 27, 'little')
        self.d28_start_page = self.add_field(28, 31, 'little')
        self.d32_end_page = self.add_field(32, 35, 'little')
        self.d36_data_byte_number = self.add_field(36, 39, 'little')
        self.d40_slc_enable = self.add_field(40, 43, 'little')
        self.b44_read_stress = self.add_field(44, 44, 'little')
        self.b45_block_type = self.add_field(45, 45, 'little')
        self.b46_seedecbit_enable = self.add_field(46, 46, 'little')
        self.d47_reserved = self.add_field(47, 47, 'little')
        self.parameter_length = 48

class micron_vu_4013(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.d12_force_clear = self.add_field(12, 15, 'little')
        self.d16_reserved = self.add_field(16, 43, 'little')
        self.parameter_length = 44

class micron_vu_C012(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.d12_fail_type = self.add_field(12, 15, 'little')
        self.d16_block_info_list_count = self.add_field(16, 19, 'little')
        self.d20_fail_times = self.add_field(20, 23, 'little')
        self.d24_enable_safe_mode_for_bb = self.add_field(24, 27, 'little')
        self.d28_skip_uecc = self.add_field(28, 31, 'little')
        self.d32_reserved = self.add_field(32, 43, 'little')
        self.parameter_length = 44

class micron_vu_40A0(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.parameter_length = 44

class micron_vu_D089(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.b12_set_mode = self.add_field(12, 12, 'little')        

class micron_vu_C0F4(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.b12_rrd_enable = self.add_field(12, 12, 'little')
        self.b13_fw_access_pattern_enable = self.add_field(13, 13, 'little')
        self.b14_die_balance_enable = self.add_field(14, 14, 'little')

class micron_vu_D0FE(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)

class VbListFmt(BITPacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.group = self.add_field_bit(0, 5, 'little')
        self.access_mode = self.add_field_bit(6, 7, 'little')
        self.dirty = self.add_field_bit(8, 8, 'little')
        self.partition = self.add_field_bit(9, 10, 'little')
        self.cursor_idx = self.add_field_bit(11, 11, 'little')
        self.pte_tbl_mark = self.add_field_bit(12, 12, 'little')
        self.host_w_mark = self.add_field_bit(13, 14, 'little')
        self.src_uecc = self.add_field_bit(15, 15, 'little')
        self.vb_trim = self.add_field_bit(16, 17, 'little')
        self.risky_type = self.add_field_bit(18, 19, 'little')
        self.xtemp_gc_mark = self.add_field_bit(20, 20, 'little')
        self.rsv = self.add_field_bit(21, 31, 'little')