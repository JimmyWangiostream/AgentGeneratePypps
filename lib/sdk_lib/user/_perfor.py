from ._sdk_base import _SDKLibProtocol
from .. import _hal
from .exception import *
from . import constant as const
from ._error_code import major_error_codes, excep_error_code_ref

class PerformanceArg:
    def __init__(self):
        self.qd = 0
        self.lun = 0
        self.mode = 0 # no use
        self.direction = 0
        self.block_size = 0
        self.chunk_size = 0
        self.total_lba_cnt = 0
        self.lba_sector_cnt = 0
        self.latency_start_addr = 0
        self.op_timeout = 0
        self.attribute = 0
        self.cmd_timeout = 0
        self.pattern_mode = 0
        self.pattern_tag = 0
        self.seed_h = 0
        self.seed_l = 0
        self.by_4k_gen = 0
        self.group_no = 0
        self.sample_rate_gap_time = 0
        self.total_execute_time = 0

class EnPerformanceArg:
    def __init__(self):
        self.en_mode = 0
        self.main_mode = 0
        self.main_qd = 0
        self.main_chunk_size_kb = 0
        self.main_cnt = 0
        self.minor_mode = 0
        self.minor_qd = 0
        self.minor_op = 0
        self.minor_chunl_size_kb = 0
        self.minor_cnt = 0
        self.seq_start_lba = 0
        self.seq_end_lba = 0
        self.block_size = 0
        self.latency_start_addr = 0
        self.op_timeout = 0
        self.delat_t_ms = 0
        self.measure_purge = 0
        self.lba_sector_cnt = 0
        self.task_entry = 0
        self.stop_cnt = 0
        self.cmd_timeout = 0
        self.sample_rate_gap_time = 0
        self.total_execute_time = 0
        self.main_flag = 0
        self.minor_flag = 0

class HpbEnPerformanceArg(EnPerformanceArg): pass

class HpbPerformanceArg:
    def __init__(self):
        self.qd = 0
        self.lun = 0
        self.mode = 0
        self.direction = 0
        self.block_size = 0
        self.chunk_size = 0
        self.total_lba_cnt = 0
        self.lba_sector_cnt = 0
        self.latency_start_addr = 0
        self.op_timeout = 0
        self.attribute = 0
        self.cmd_timeout = 0
        self.reserved = bytearray(15)
        self.sample_rate_gap_time = 0
        self.total_execute_time = 0

class RpmbPerformanceArg:
    def __init__(self):
        self.mode = 0
        self.direction = 0
        self.block_size = 0
        self.rpmb_chunk_size = 0
        self.rpmb_write_cnt = 0
        self.total_lba_cnt = 0
        self.lba_sector_cnt = 0
        self.op_timeout = 0
        self.rpmb_region = 0
        self.rpmb_region_enable = 0
        self.rpmb_write_cnt_enable = 0
        self.cmd_timeout = 0
        self.latency_start_addr = 0

class AdvRpmbPerformanceArg(RpmbPerformanceArg): pass

class GenericEhsPerformanceArg(PerformanceArg):
    def __init__(self):
        super().__init__()
        self.ehs_trig_lba_seq_idx = 0
        self.ehs_trig_lba_seq_step = 0

class _SDKLibPerformanceMixin(_SDKLibProtocol):
    def _handle_error(self, result_buf: bytearray, fun_str: str):
        error_code = result_buf[0]
        sub_error_code = result_buf[1]
        resp_error = result_buf[2]

        # special case: OOR
        if error_code == 0x8A & sub_error_code == 0x02 & resp_error == 0x05:
            raise OOR_ISSUE(f"[{fun_str}]: OOR Issue Occurred, Dump SDRAM Data")
        
        if error_code == const.SDK_EXCEPTION:
            _hal.handle_error_code(sub_error_code, excep_error_code_ref, fun_str, result_buf)
        elif error_code == const.SDK_RESPONSE_ERROR:
            _hal.handle_error_code(error_code, {
                error_code: (DLL_RESPONSE_ERROR, f"Rsp Error: {resp_error}"),
            }, fun_str, result_buf)
        elif error_code == const.SDK_PATTERN_2_ERROR:
            pass #record Task Tag of compare error CMD. <v6.31.18>
        else:
            _hal.handle_error_code(error_code, major_error_codes, fun_str, result_buf)

    def performance(self, arg: PerformanceArg, pby_addr_buf: bytearray) -> tuple[bytearray, bytearray]:
        assert len(pby_addr_buf) % 8192 == 0, "Data buffer size must be 8196 bytes alignment" 
        
        arg_buf = bytearray(512)
        arg_buf[0] = arg.qd
        arg_buf[1] = arg.lun
        arg_buf[2] = arg.mode
        arg_buf[3] = arg.direction
        arg_buf[4] = arg.block_size
        arg_buf[5] = arg.chunk_size
        arg_buf[6:10] = arg.total_lba_cnt.to_bytes(4, byteorder='big')
        arg_buf[10:14] = arg.lba_sector_cnt.to_bytes(4, byteorder='big')
        arg_buf[14:18] = arg.latency_start_addr.to_bytes(4, byteorder='big')
        arg_buf[18:22] = arg.op_timeout.to_bytes(4, byteorder='big')
        arg_buf[22] = arg.attribute
        arg_buf[23:27] = arg.cmd_timeout.to_bytes(4, byteorder='big')
        arg_buf[27] = arg.pattern_mode
        arg_buf[28:32] = arg.pattern_tag.to_bytes(4, byteorder='big')
        arg_buf[32:36] = arg.seed_h.to_bytes(4, byteorder='big')
        arg_buf[36:40] = arg.seed_l.to_bytes(4, byteorder='big')
        arg_buf[40] = arg.by_4k_gen
        arg_buf[41] = arg.group_no
        arg_buf[42:46] = arg.sample_rate_gap_time.to_bytes(4, byteorder='big')
        arg_buf[46:50] = arg.total_execute_time.to_bytes(4, byteorder='big')

        pby_result_buf = bytearray()
        try:
            pby_result_buf, pby_info_buf = _hal.performance(self._dll, arg_buf, pby_addr_buf)
        except DLL_ERROR as e:
            self._handle_error(e.result_buf, "performance")
        return (pby_result_buf, pby_info_buf)

    def en_performance(self, arg: EnPerformanceArg, pby_addr_buf: bytearray) -> tuple[bytearray, bytearray]:
        assert len(pby_addr_buf) % 8196 == 0, "Data buffer size must be 8196 bytes alignment"

        arg_buf = bytearray(512)
        arg_buf[0] = arg.en_mode
        arg_buf[1] = arg.main_mode
        arg_buf[2] = arg.main_qd
        arg_buf[3:7] = arg.main_chunk_size_kb.to_bytes(4, byteorder='little')
        arg_buf[7:11] = arg.main_cnt.to_bytes(4, byteorder='little')
        arg_buf[11] = arg.minor_mode
        arg_buf[12] = arg.minor_qd
        arg_buf[13] = arg.minor_op
        arg_buf[14:18] = arg.minor_chunl_size_kb.to_bytes(4, byteorder='little')
        arg_buf[18:22] = arg.minor_cnt.to_bytes(4, byteorder='little')
        arg_buf[22:26] = arg.seq_start_lba.to_bytes(4, byteorder='little')
        arg_buf[26:30] = arg.seq_end_lba.to_bytes(4, byteorder='little')
        arg_buf[31] = arg.block_size
        arg_buf[32:37] = arg.latency_start_addr.to_bytes(4, byteorder='little')
        arg_buf[36:40] = arg.op_timeout.to_bytes(4, byteorder='little')
        arg_buf[40:42] = arg.delat_t_ms.to_bytes(2, byteorder='little')
        arg_buf[42] = arg.measure_purge
        arg_buf[43:45] = arg.lba_sector_cnt.to_bytes(2, byteorder='little')
        arg_buf[45:49] = arg.task_entry.to_bytes(4, byteorder='little')
        arg_buf[49] = arg.stop_cnt
        arg_buf[50:54] = arg.cmd_timeout.to_bytes(4, byteorder='little')
        arg_buf[54:58] = arg.sample_rate_gap_time.to_bytes(4, byteorder='little')
        arg_buf[58:62] = arg.total_execute_time.to_bytes(4, byteorder='little')
        arg_buf[62] = arg.main_flag
        arg_buf[63] = arg.minor_flag

        try:
            pby_result_buf, pby_info_buf = _hal.en_performance(self._dll, arg_buf, pby_addr_buf)
        except DLL_ERROR as e:
            self._handle_error(e.result_buf, "en_performance")

        return (arg_buf, pby_addr_buf)
    
    def hpb_read_performance(self, arg: HpbPerformanceArg, pby_addr_buf: bytearray) -> tuple[bytearray, bytearray]:
        assert len(pby_addr_buf) % 8196 == 0, "Data buffer size must be 8196 bytes alignment"

        arg_buf = bytearray(512)
        arg_buf[0] = arg.qd
        arg_buf[1] = arg.lun
        arg_buf[2] = arg.mode
        arg_buf[3] = arg.direction
        arg_buf[4] = arg.block_size
        arg_buf[5] = arg.chunk_size
        arg_buf[6:10] = arg.total_lba_cnt.to_bytes(4, byteorder='little')
        arg_buf[10:14] = arg.lba_sector_cnt.to_bytes(4, byteorder='little')
        arg_buf[14:18] = arg.latency_start_addr.to_bytes(4, byteorder='little')
        arg_buf[18:22] = arg.op_timeout.to_bytes(4, byteorder='little')
        arg_buf[22] = arg.attribute
        arg_buf[23:27] = arg.cmd_timeout.to_bytes(4, byteorder='little')
        arg_buf[27:42] = arg.reserved
        arg_buf[42:46] = arg.sample_rate_gap_time.to_bytes(4, byteorder='little')
        arg_buf[46:50] = arg.total_execute_time.to_bytes(4, byteorder='little')

        try:
            pby_result_buf, pby_info_buf = _hal.hpb_read_performance(self._dll, arg_buf, pby_addr_buf)
        except DLL_ERROR as e:
            self._handle_error(e.result_buf, "hpb_read_performance")
        
        return (pby_result_buf, pby_info_buf)

    def hpb_en_performance(self, arg: HpbEnPerformanceArg, pby_addr_buf: bytearray) -> tuple[bytearray, bytearray]:
        assert len(pby_addr_buf) % 8196 == 0, "Data buffer size must be 8196 bytes alignment"

        arg_buf = bytearray(512)
        arg_buf[0] = arg.en_mode
        arg_buf[1] = arg.main_mode
        arg_buf[2] = arg.main_qd
        arg_buf[3:7] = arg.main_chunk_size_kb.to_bytes(4, byteorder='little')
        arg_buf[7:11] = arg.main_cnt.to_bytes(4, byteorder='little')
        arg_buf[11] = arg.minor_mode
        arg_buf[12] = arg.minor_qd
        arg_buf[13] = arg.minor_op
        arg_buf[14:18] = arg.minor_chunl_size_kb.to_bytes(4, byteorder='little')
        arg_buf[18:22] = arg.minor_cnt.to_bytes(4, byteorder='little')
        arg_buf[22:26] = arg.seq_start_lba.to_bytes(4, byteorder='little')
        arg_buf[26:30] = arg.seq_end_lba.to_bytes(4, byteorder='little')
        arg_buf[31] = arg.block_size
        arg_buf[32:37] = arg.latency_start_addr.to_bytes(4, byteorder='little')
        arg_buf[36:40] = arg.op_timeout.to_bytes(4, byteorder='little')
        arg_buf[40:42] = arg.delat_t_ms.to_bytes(2, byteorder='little')
        arg_buf[42] = arg.measure_purge
        arg_buf[43:45] = arg.lba_sector_cnt.to_bytes(2, byteorder='little')
        arg_buf[45:49] = arg.task_entry.to_bytes(4, byteorder='little')
        arg_buf[49] = arg.stop_cnt
        arg_buf[50:54] = arg.cmd_timeout.to_bytes(4, byteorder='little')

        try:
            pby_result_buf, pby_info_buf = _hal.hpb_read_performance(self._dll, arg_buf, pby_addr_buf)
        except DLL_ERROR as e:
            self._handle_error(e.result_buf, "hpb_read_performance")
        
        return (pby_result_buf, pby_info_buf)
    
    def rpmb_performance(self, arg: RpmbPerformanceArg, pby_addr_buf: bytearray) -> tuple[bytearray, bytearray]:
        assert len(pby_addr_buf) % 8192 == 0, "Data buffer size must be 8192 bytes alignment"

        arg_buf = bytearray(512)
        arg_buf[0] = arg.mode
        arg_buf[1] = arg.direction
        arg_buf[2] = arg.block_size
        arg_buf[3] = arg.rpmb_chunk_size
        arg_buf[4:8] = arg.rpmb_write_cnt.to_bytes(4, byteorder='little')
        arg_buf[8:12] = arg.total_lba_cnt.to_bytes(4, byteorder='big')
        arg_buf[12:16] = arg.lba_sector_cnt.to_bytes(4, byteorder='big')
        arg_buf[16:20] = arg.op_timeout.to_bytes(4, byteorder='big')
        arg_buf[20] = arg.rpmb_region
        arg_buf[21] = arg.rpmb_region_enable
        arg_buf[22] = arg.rpmb_write_cnt_enable
        arg_buf[23:27] = arg.cmd_timeout.to_bytes(4, byteorder='little')
        arg_buf[27:31] = arg.latency_start_addr.to_bytes(4, byteorder='little')

        try:
            pby_result_buf, pby_info_buf = _hal.rpmb_performance(self._dll, arg_buf, pby_addr_buf)
        except DLL_ERROR as e:
            self._handle_error(e.result_buf, "rpmb_performance")
        
        return (pby_result_buf, pby_info_buf)

    def adv_rpmb_performance(self, arg: AdvRpmbPerformanceArg, pby_addr_buf: bytearray) -> tuple[bytearray, bytearray]:
        assert len(pby_addr_buf) % 8192 == 0, "Data buffer size must be 8192 bytes alignment"
        
        arg_buf = bytearray(32)
        arg_buf[0] = arg.mode
        arg_buf[1] = arg.direction
        arg_buf[2] = arg.block_size
        arg_buf[3] = arg.rpmb_chunk_size
        arg_buf[4:8] = arg.rpmb_write_cnt.to_bytes(4, byteorder='little')
        arg_buf[8:12] = arg.total_lba_cnt.to_bytes(4, byteorder='big')
        arg_buf[12:16] = arg.lba_sector_cnt.to_bytes(4, byteorder='big')
        arg_buf[16:20] = arg.op_timeout.to_bytes(4, byteorder='big')
        arg_buf[20] = arg.rpmb_region
        arg_buf[21] = arg.rpmb_region_enable
        arg_buf[22] = arg.rpmb_write_cnt_enable
        arg_buf[23:27] = arg.cmd_timeout.to_bytes(4, byteorder='little')
        arg_buf[27:31] = arg.latency_start_addr.to_bytes(4, byteorder='little')

        try:
            pby_result_buf, pby_info_buf = _hal.adv_rpmb_performance(self._dll, arg_buf, pby_addr_buf)
        except DLL_ERROR as e:
            self._handle_error(e.result_buf, "rpmb_performance")
        
        return (pby_result_buf, pby_info_buf)

    def generic_ehs_performance(self, arg: GenericEhsPerformanceArg, pby_addr_buf: bytearray) -> tuple[bytearray, bytearray, bytearray]:
        assert len(pby_addr_buf) % 8196 == 0, "Data buffer size must be 8196 bytes alignment" 
        
        arg_buf = bytearray(512)
        arg_buf[0] = arg.qd
        arg_buf[1] = arg.lun
        arg_buf[2] = arg.mode
        arg_buf[3] = arg.direction
        arg_buf[4] = arg.block_size
        arg_buf[5] = arg.chunk_size
        arg_buf[6:10] = arg.total_lba_cnt.to_bytes(4, byteorder='little')
        arg_buf[10:14] = arg.lba_sector_cnt.to_bytes(4, byteorder='little')
        arg_buf[14:18] = arg.latency_start_addr.to_bytes(4, byteorder='little')
        arg_buf[18:22] = arg.op_timeout.to_bytes(4, byteorder='little')
        arg_buf[22] = arg.attribute
        arg_buf[23:27] = arg.cmd_timeout.to_bytes(4, byteorder='little')
        arg_buf[27] = arg.pattern_mode
        arg_buf[28:32] = arg.pattern_tag.to_bytes(32, byteorder='little')
        arg_buf[32:36] = arg.seed_h.to_bytes(4, byteorder='little')
        arg_buf[36:40] = arg.seed_l.to_bytes(4, byteorder='little')
        arg_buf[40] = arg.by_4k_gen
        arg_buf[41] = arg.group_no
        arg_buf[42:46] = arg.ehs_trig_lba_seq_idx.to_bytes(4, byteorder='little')
        arg_buf[46:50] = arg.ehs_trig_lba_seq_step.to_bytes(4, byteorder='little')
        try:
            pby_result_buf, pby_info_buf, pby_ehs_info_buf  = _hal.generic_ehs_performance(self._dll, arg_buf, pby_addr_buf)
        except DLL_ERROR as e:
            self._handle_error(e.result_buf, "generic_ehs_performance")
        
        return (pby_result_buf, pby_info_buf, pby_ehs_info_buf)