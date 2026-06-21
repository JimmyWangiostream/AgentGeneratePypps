from .base import ApiTestBase
from Script.api import shared
from Script.lib import sdk_lib as lib

_sdk = shared.sdk

class TestPerformance(ApiTestBase):
    def test_seq_rw_ran_rw(self) -> None:
        perf_arg = lib.PerformanceArg()
        perf_arg.qd = 32
        perf_arg.lun = 0
        perf_arg.direction = 1 # write10
        perf_arg.block_size = 12 # ref pGlobalParam->gUnit[PerfVarPtr->byLUN].b10_LogicalBlockSize from c/c++
        perf_arg.chunk_size = 25 # 2*(2^5)
        perf_arg.total_lba_cnt = 0 # (DWORD)(PerfVarPtr->dwTestSizeKByte / dwChunkInKByte)
        perf_arg.lba_sector_cnt = 0 #(DWORD)(PerfVarPtr->dwTaskEntry / dwEntryPerPage);
        perf_arg.latency_start_addr = 0
        perf_arg.op_timeout = 0
        perf_arg.attribute = 0
        perf_arg.cmd_timeout = 0
        perf_arg.pattern_mode = 0
        perf_arg.pattern_tag = 0
        perf_arg.seed_h = 0
        perf_arg.seed_l = 0
        perf_arg.by_4k_gen = 0
        perf_arg.group_no = 0
        perf_arg.sample_rate_gap_time = 0
        perf_arg.total_execute_time = 0
        