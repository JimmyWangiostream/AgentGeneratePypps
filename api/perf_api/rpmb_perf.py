from Script.api import shared
from Script.lib import sdk_lib as lib
from enum import Enum
import random
import struct
import hashlib
import hmac
from Script import api

_sdk = shared.sdk
_log = shared.logger

BLOCK_SIZE_256B = 0x08

RPMB_MAX_TASKENTRY_WO_LATENCY = 0xF8000

class RpmbPerformanceMode(Enum):
    SEQUENTIAL = 0
    RANDOM = 1

class RpmbPerformanceDirection(Enum):
    READ = 0
    WRITE = 1

class RpmbMsgType(Enum):
    RPMB_KEY_PROGRAM_REQ = 0x0001
    RPMB_WRITE_COUNTER_READ_REQ = 0x0002
    RPMB_DATA_WRITE_REQ = 0x0003
    RPMB_DATA_READ_REQ = 0x0004
    RPMB_RESULT_READ_REQ = 0x0005
    RPMB_SECURE_W_PROTECT_CONFIG_BLOCK_REQ = 0x0006
    RPMB_SECURE_R_PROTECT_CONFIG_BLOCK_REQ = 0x0007
    RPMB_PURGE_ENABLE_REQ = 0x0008
    RPMB_PURGE_STATUS_READ_REQ = 0x0009

    RPMB_KEY_PROGRAM_RSP = 0x0100
    RPMB_WRITE_COUNTER_READ_RSP = 0x0200
    RPMB_DATA_WRITE_RSP = 0x0300
    RPMB_DATA_READ_RSP = 0x0400
    RPMB_SECURE_W_PROTECT_CONFIG_BLOCK_RSP = 0x0600
    RPMB_SECURE_R_PROTECT_CONFIG_BLOCK_RSP = 0x0700
    RPMB_PURGE_ENABLE_RSP = 0x0800
    PRMB_PURGE_STATUS_READ_RSP = 0x0900

class _RpmbMSGDataFrame():
    def __init__(self):
        self.stuff = bytearray(196)
        self.mac_key = bytearray(32)
        self.data = bytearray(256)
        self.Nonce = bytearray(16)
        self.write_counter = 0
        self.address = 0
        self.block_count = 0
        self.result = 0
        self.reqrestype = 0

class RpmbPerformanceVar():
    def __init__(self):
        self.mode = 0
        self.direction = 0
        self.chunk_size_in_rpmb_block = 0
        self.test_size_in_kbyte = 0
        self.start_lba = 0
        self.end_lba = 0
        self.allow_lba_overlap = 0
        self.lba_allign_cs = 0
        self.latency = 0
        self.rpmb_region = 0
        self.rpmb_region_enable = 0
        self.write_count_enable = 0
        

class RpmbPerformanceClass():
    def __init__(self, region_id: int):
        #Buffer for rpmbperformance api
        self.lba_entry_buffer = None
        self.result_buffer = None
        self.info_buffer = None
        self.key = bytearray([0x78, 0x56, 0x34, 0x12] * 8)
        self.rpmb = api.RPMB(region_id)

        #Variable for rpmbperformance api
        self.rpmbperf_arg = lib.RpmbPerformanceArg()
        self.rpmb_msg_data_frame = _RpmbMSGDataFrame()
        self.total_test_size_kbyte = 0
        self.test_mode = 0
        self.chunk_in_block = 0
        self.write_counter = 0

    # @property
    # def get_write_counter(self) -> int:
    #     return self.write_counter

    def rpmb_init(self):
        _log.info("Function - rpmb_init")
        try:
            self.write_counter = self.rpmb.rpmb_read_counter()
        except (api.SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET) as e:            
            self.rpmb.rpmb_key_programming()
            try:
                self.write_counter = self.rpmb.rpmb_read_counter()
            except Exception as e:
                raise Exception(f"Failed to read RPMB counter after programming key: {e}")
        except Exception as e:
            raise Exception(f"Failed to read RPMB counter: {e}")

    def _clear_rpmb_write_cnt_key(self):
        pass

    def rpmb_reset(self):
        _log.info("Function - rpmb_reset")
        self._clear_rpmb_write_cnt_key()
        self.write_counter = 0
        self.rpmb.rpmb_key_programming()

    def _get_performance_result(self):
        _log.info("Function - _get_performance_result")

        total_execute_time = int.from_bytes(self.result_buffer[4:8], byteorder='big', signed=False) #unit: us
        _log.info("Total Time Spend   : %g ms (%f s)", total_execute_time / 1000.0, total_execute_time / 1000.0 / 1000.0)
        test_size_in_mbyte = self.total_test_size_kbyte * self.rpmbperf_arg.rpmb_region / 1024 #region for what?
        total_execute_time_in_sec = total_execute_time / (1000 * 1000)
        performance_mbyte_per_second = test_size_in_mbyte / total_execute_time_in_sec
        performance_io_per_second = (performance_mbyte_per_second * 1024 * 1024) / (self.chunk_in_block * 256)

        if self.test_mode == RpmbPerformanceMode.SEQUENTIAL.value:
            _log.info("Performance        : %g MB/s", performance_mbyte_per_second)
            return performance_mbyte_per_second
        else:
            _log.info("IOPS               : %g", performance_io_per_second)
            return performance_io_per_second

    def _prepare_lba_buffer(self, lba_buffer_size, rpmb_perf_var: RpmbPerformanceVar, lba_entry_cnt):
        _log.info("Function - _prepare_lba_buffer")
        lba_buffer = bytearray(lba_buffer_size * [0xff])
        lba_entry_size = 64 #64B per entry
        mac_entry_size = 32 #32B per mac entry
        lba_buffer_current_offset = 0
        lba_current_offset = 0

        if rpmb_perf_var.direction == RpmbPerformanceDirection.WRITE.value:
            self.rpmb_msg_data_frame.reqrestype = RpmbMsgType.RPMB_DATA_WRITE_REQ.value
            for i in range(256):
                self.rpmb_msg_data_frame.data[i] = 0xAA
            self.rpmb_msg_data_frame.write_counter = self.write_counter
            self.rpmb_msg_data_frame.block_count = rpmb_perf_var.chunk_size_in_rpmb_block

        if self.test_mode == RpmbPerformanceMode.SEQUENTIAL.value:
            lba_current_offset = rpmb_perf_var.start_lba
            for i in range(0, lba_entry_cnt):
                lba_buffer_current_offset = i * lba_entry_size

                if rpmb_perf_var.direction == RpmbPerformanceDirection.WRITE.value:
                    self.rpmb_msg_data_frame.address = lba_current_offset

                    self._gen_rpmb_mac()

                    #mac_key change big endian to lba_buffer
                    self.rpmb_msg_data_frame.mac_key = self._swap_endian_every_4_bytes(self.rpmb_msg_data_frame.mac_key)
                    lba_buffer[lba_buffer_current_offset : lba_buffer_current_offset + mac_entry_size] = self.rpmb_msg_data_frame.mac_key
                    self.rpmb_msg_data_frame.write_counter += 1
                
                lba_buffer[lba_buffer_current_offset + mac_entry_size : lba_buffer_current_offset + mac_entry_size + 2] = struct.pack(r">H", lba_current_offset)
                lba_current_offset += rpmb_perf_var.chunk_size_in_rpmb_block

        elif self.test_mode == RpmbPerformanceMode.RANDOM.value:
            lba_current_offset = 0
            if rpmb_perf_var.lba_allign_cs:
                lba_cnt = ((rpmb_perf_var.end_lba + 1) - rpmb_perf_var.start_lba) // rpmb_perf_var.chunk_size_in_rpmb_block
                total_lba = [0] * lba_cnt
                for i in range(0, lba_cnt):
                    total_lba[i] = rpmb_perf_var.start_lba + i * rpmb_perf_var.chunk_size_in_rpmb_block
            else:
                lba_cnt = (rpmb_perf_var.end_lba + 1 - rpmb_perf_var.chunk_size_in_rpmb_block) - rpmb_perf_var.start_lba
                total_lba = [0] * lba_cnt
                for i in range(0, lba_cnt):
                    total_lba[i] = rpmb_perf_var.start_lba + i

            for i in range(0, lba_entry_cnt):
                lba_buffer_current_offset = i * lba_entry_size
                RandLBAIdx = random.randint(0, lba_cnt - 1)

                lba_current_offset = total_lba[RandLBAIdx]

                if rpmb_perf_var.direction == RpmbPerformanceDirection.WRITE.value:
                    self.rpmb_msg_data_frame.address = lba_current_offset

                    self._gen_rpmb_mac()

                    #mac_key change big endian to lba_buffer
                    self.rpmb_msg_data_frame.mac_key = self._swap_endian_every_4_bytes(self.rpmb_msg_data_frame.mac_key)
                    lba_buffer[lba_buffer_current_offset : lba_buffer_current_offset + mac_entry_size] = self.rpmb_msg_data_frame.mac_key
                    self.rpmb_msg_data_frame.write_counter += 1

                lba_buffer[lba_buffer_current_offset + mac_entry_size : lba_buffer_current_offset + mac_entry_size + 2] = struct.pack(r">H", lba_current_offset)

                if rpmb_perf_var.allow_lba_overlap == 0:
                    total_lba[RandLBAIdx] = total_lba[lba_cnt - 1]
                    lba_cnt -= 1

                    if (lba_cnt == 0) and (i < lba_entry_cnt - 1): #total lba count is not enough for lba entry count when not allow lba overlap
                        raise 'LBA Entry Cnt Exceed LBA_Cnt, check test_size_in_kbyte/chunk_size_in_rpmb_block'
        
        self.lba_entry_buffer = lba_buffer

    def _error_handle(self, rpmb_perf_var: RpmbPerformanceVar):
        if rpmb_perf_var.mode == RpmbPerformanceMode.SEQUENTIAL.value:
            if rpmb_perf_var.test_size_in_kbyte * 1024 > (rpmb_perf_var.end_lba + 1 - rpmb_perf_var.start_lba) * 256:
                raise 'not support LBA size > LBA range'
        
    def _load_normal_mode_arg(self):
        self.rpmbperf_arg.mode = 0 #not used
        self.rpmbperf_arg.direction = 0 #0:read, 1:write
        self.rpmbperf_arg.block_size = BLOCK_SIZE_256B #follow spec, 0x08 = 256B (should be a fixed value)
        self.rpmbperf_arg.rpmb_chunk_size = 0 #uint = 256B
        self.rpmbperf_arg.rpmb_write_cnt = 0
        self.rpmbperf_arg.total_lba_cnt = 0
        self.rpmbperf_arg.lba_sector_cnt = 0
        self.rpmbperf_arg.op_timeout = 0
        self.rpmbperf_arg.rpmb_region = 0
        self.rpmbperf_arg.rpmb_region_enable = 0 #bit0 - Region 0, bit1 - Region 1, bit2 - Region 2, bit3 - Region 3
        self.rpmbperf_arg.rpmb_write_cnt_enable = 0
        self.rpmbperf_arg.cmd_timeout = 0
        self.rpmbperf_arg.latency_start_addr = 0

    def _load_latency_mode_arg(self):
        pass

    def executer(self, rpmb_perf_var: RpmbPerformanceVar):
        _log.info("=================Function - rpmb_performance executer=================")
        self._error_handle(rpmb_perf_var)
        
        self.test_mode = rpmb_perf_var.mode
        self.total_test_size_kbyte = rpmb_perf_var.test_size_in_kbyte
        self.chunk_in_block = rpmb_perf_var.chunk_size_in_rpmb_block
        
        if rpmb_perf_var.latency == 0:
            self._load_normal_mode_arg()
        elif rpmb_perf_var.latency == 1:
            self._load_latency_mode_arg()
            raise 'not support latency'
        
        task_entry = (rpmb_perf_var.test_size_in_kbyte * 1024) // (rpmb_perf_var.chunk_size_in_rpmb_block * 256)
        self.rpmbperf_arg.total_lba_cnt = task_entry
        entry_page_size = 8 #512B per page, one lba entry is 64B

        if rpmb_perf_var.latency == 0:
            if task_entry > RPMB_MAX_TASKENTRY_WO_LATENCY: #Max 1015808 taskEntry due to SDRAM size 62MB
                raise 'Exceed MAX_TASK_ENTRY, SDK cant handle'

        #Caculate total sector count
        sector_size_in_8KB = (8 * 1024) // 512 
        sector_cnt = task_entry // entry_page_size

        if (task_entry % entry_page_size): #how many sectors were occuipied by task_entry
            sector_cnt += 1

        if (sector_cnt % sector_size_in_8KB): #fill sector to align 8KB
            sector_cnt = sector_cnt + (sector_size_in_8KB - (sector_cnt % sector_size_in_8KB)) #Align 8KB

        ### using user setting
        self.rpmbperf_arg.direction = rpmb_perf_var.direction
        self.rpmbperf_arg.rpmb_chunk_size = rpmb_perf_var.chunk_size_in_rpmb_block
        self.rpmbperf_arg.rpmb_write_cnt = self.write_counter
        self.rpmbperf_arg.lba_sector_cnt = sector_cnt
        self.rpmbperf_arg.rpmb_region = rpmb_perf_var.rpmb_region
        self.rpmbperf_arg.rpmb_region_enable = rpmb_perf_var.rpmb_region_enable
        self.rpmbperf_arg.rpmb_write_cnt_enable = rpmb_perf_var.write_count_enable
        ###
        
        lba_buffer_size = sector_cnt * 512
        self._prepare_lba_buffer(lba_buffer_size, rpmb_perf_var, task_entry)

        _log.info("Queue Depth        : 1")
        _log.info("LUN                : %d", api.ufs_api.defines.WellKnownLUN.RPMB)
        _log.info("Test Mode          : RPMB %s %s", "SEQUENTIAL" if rpmb_perf_var.mode == RpmbPerformanceMode.SEQUENTIAL.value else "RANDOM", "READ" if rpmb_perf_var.direction == RpmbPerformanceDirection.READ.value else "WRITE")
        _log.info("Chunk Block(256B)  : %d", rpmb_perf_var.chunk_size_in_rpmb_block)
        _log.info("Total Test Size    : %d KB", rpmb_perf_var.test_size_in_kbyte)
        _log.info("LBA Range          : %u ~ %u", rpmb_perf_var.start_lba, rpmb_perf_var.end_lba)
        _log.info("RPMB Write Count   : %d", self.write_counter)
        _log.info("Task Entry         : %d", task_entry)
        _log.info("Allow Overlap      : %s", "YES" if rpmb_perf_var.allow_lba_overlap else "NO")
        _log.info("Align Chunk size   : %s", "YES" if rpmb_perf_var.lba_allign_cs else "NO")
        _log.info("Record Latency     : %s", "YES" if rpmb_perf_var.latency else "NO")

        _log.info("Function - _sdk.rpmb_performance")
        self.result_buffer, self.info_buffer = _sdk.rpmb_performance(self.rpmbperf_arg, self.lba_entry_buffer)

        if(rpmb_perf_var.direction == RpmbPerformanceDirection.WRITE.value):
            self.write_counter += self.total_test_size_kbyte * 1024 // (self.chunk_in_block * 256)

        return self._get_performance_result()

    def _gen_rpmb_mac(self):
        block_cnt = self.rpmb_msg_data_frame.block_count
        key = self.key
        mac_buffer = bytearray((block_cnt * 284) * [0xff])

        self.rpmb_msg_data_frame.mac_key = bytearray(32)

        for i in range(0, block_cnt):
            mac_buffer_current_offset = i * 284
            mac_buffer[mac_buffer_current_offset : mac_buffer_current_offset + 256] = self.rpmb_msg_data_frame.data
            mac_buffer[mac_buffer_current_offset + 256 : mac_buffer_current_offset + 272] = self.rpmb_msg_data_frame.Nonce
            mac_buffer[mac_buffer_current_offset + 272 : mac_buffer_current_offset + 276] = self.rpmb_msg_data_frame.write_counter.to_bytes(4, byteorder="big")
            mac_buffer[mac_buffer_current_offset + 276 : mac_buffer_current_offset + 278] = self.rpmb_msg_data_frame.address.to_bytes(2, byteorder='big')
            mac_buffer[mac_buffer_current_offset + 278 : mac_buffer_current_offset + 280] = self.rpmb_msg_data_frame.block_count.to_bytes(2, byteorder='big')
            mac_buffer[mac_buffer_current_offset + 280 : mac_buffer_current_offset + 282] = self.rpmb_msg_data_frame.result.to_bytes(2, byteorder='little')
            mac_buffer[mac_buffer_current_offset + 282 : mac_buffer_current_offset + 284] = self.rpmb_msg_data_frame.reqrestype.to_bytes(2, byteorder='big')

            if i == block_cnt - 1:
                self.rpmb_msg_data_frame.mac_key = api.hmac_sha256(key, mac_buffer)
    
    def _swap_endian_every_4_bytes(self, byte_array):
        chunks = [byte_array[i:i+4] for i in range(0, len(byte_array), 4)]

        swapped_chunks = []
        for chunk in chunks:
            unpacked = struct.unpack('<L', chunk)[0]
            packed = struct.pack('>L', unpacked)
            swapped_chunks.append(packed)

        result = b''.join(swapped_chunks)
        return result