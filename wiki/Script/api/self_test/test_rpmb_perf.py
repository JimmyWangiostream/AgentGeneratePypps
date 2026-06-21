from Script.api import ExecuteCMD
from Script.api.ufs_api.debug_cmd.dcmd_enum import Dcmd5ResetType
from .base import ApiTestBase
from Script import api

_log = api.shared.logger

class TestRPMBPerformance(ApiTestBase):
    def setUp(self) -> None:
        ExecuteCMD.clear()
    def test_rpmb_performance(self):
        rpmb_perf = api.RpmbPerformanceClass(api.enum_define.RPMBRegion.REGION_0)
        rpmb_perf_var = api.RpmbPerformanceVar()
        
        _log.info("Device Init!")
        api.ufs_api.init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)
        
        _log.info("pattern start!")

        #clear write counter to do

        #read device write counter and do key programing
        rpmb_perf.rpmb_init()

        #Seq Write
        rpmb_perf_var.mode = api.RpmbPerformanceMode.SEQUENTIAL.value
        rpmb_perf_var.direction = api.RpmbPerformanceDirection.WRITE.value
        rpmb_perf_var.chunk_size_in_rpmb_block = 1
        rpmb_perf_var.test_size_in_kbyte = 12
        rpmb_perf_var.start_lba = 0
        rpmb_perf_var.end_lba = 65535
        rpmb_perf_var.allow_lba_overlap = 0
        rpmb_perf_var.lba_allign_cs = 1
        rpmb_perf_var.latency = 0
        rpmb_perf_var.rpmb_region = 1
        rpmb_perf_var.rpmb_region_enable = 1
        rpmb_perf_var.write_count_enable = 0

        perf_value = rpmb_perf.executer(rpmb_perf_var)

        #Seq. Read
        rpmb_perf_var.direction = api.RpmbPerformanceDirection.READ.value
        perf_value = rpmb_perf.executer(rpmb_perf_var)

        #Rand. Write
        rpmb_perf_var.test_size_in_kbyte = 12
        rpmb_perf_var.mode = api.RpmbPerformanceMode.RANDOM.value
        rpmb_perf_var.direction = api.RpmbPerformanceDirection.WRITE.value
        rpmb_perf_var.allow_lba_overlap = 1
        perf_value = rpmb_perf.executer(rpmb_perf_var)

        #Rand. Read
        rpmb_perf_var.direction = api.RpmbPerformanceDirection.READ.value
        perf_value = rpmb_perf.executer(rpmb_perf_var)


        _log.info("pattern end!")