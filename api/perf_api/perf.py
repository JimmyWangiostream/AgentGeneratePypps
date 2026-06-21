from Script.api import shared

from Script.lib import sdk_lib as lib
from enum import Enum
import random
import struct

_sdk = shared.sdk

SEQUENTIAL = 0
RANDOM = 1

class PerformanceMode(Enum):
    SEQUENTIAL = 0
    RANDOM = 1


class PerformanceClass():
    def __init__(self):
        #Buffer for performance api
        self.lba_entry_buffer = None
        self.result_buffer = None
        self.info_buffer = None

        #Variable for performance api
        self.perf_arg = lib.PerformanceArg()
        self.total_test_size_kbyte = 0
        self.test_mode = 0
        self.chunk_in_block = 0


    def get_performance_result(self):
        total_execute_time = int.from_bytes(self.result_buffer[4:8], byteorder='big', signed=False) #unit: us
        test_size_in_mbyte = self.total_test_size_kbyte / 1024
        total_execute_time_in_sec = total_execute_time / (1000 * 1000)
        performance_mbyte_per_second = test_size_in_mbyte / total_execute_time_in_sec
        performance_kilo_io_per_second = (performance_mbyte_per_second * 1024) / (self.chunk_in_block * 4)

        if self.test_mode == PerformanceMode.SEQUENTIAL.value:
            return performance_mbyte_per_second
        else:
            return performance_kilo_io_per_second

    def _prepare_lba_buffer(self,lba_buffer_size = 0, test_mode = 0, start_lba = 0, end_lba = 0, chunk_in_block = 0, lba_entry_cnt = 0, allow_lba_overlap = 0):
        lba_buffer = bytearray(0xff for _ in range(lba_buffer_size))
        lba_entry_size = 4 #4B per entry
        lba_buffer_current_offset = 0
        lba_buufer_next_offset = lba_buffer_current_offset + lba_entry_size
        target_lba = start_lba

        if test_mode == PerformanceMode.SEQUENTIAL.value: # Prepare LBA buffer for sequential access
            for i in range(0, lba_entry_cnt):
                lba_buffer[lba_buffer_current_offset : lba_buufer_next_offset] = struct.pack(r">L", target_lba)
                lba_buffer_current_offset = lba_buufer_next_offset
                lba_buufer_next_offset += lba_entry_size
                target_lba += chunk_in_block

        elif test_mode == PerformanceMode.RANDOM.value:
            if allow_lba_overlap:
                for i in range(0, lba_entry_cnt):
                    # 生成一個在 start_lba 和 end_lba 之間的隨機 LBA
                    target_lba = random.randint(start_lba, end_lba - chunk_in_block + 1)
                    lba_buffer[lba_buffer_offset:lba_buffer_offset + lba_entry_size] = struct.pack(">L", target_lba)
                    lba_buffer_offset += lba_entry_size
            else:
                # 使用集合來確保 LBA 是唯一的
                unique_lbas = set()
                while len(unique_lbas) < lba_entry_cnt:
                    target_lba = random.randint(start_lba, end_lba - chunk_in_block + 1)
                    unique_lbas.add(target_lba) #if there is same lba in uunique_lbAs, target lba will not be added.

                for target_lba in unique_lbas:
                    lba_buffer[lba_buffer_current_offset:lba_buffer_current_offset + lba_entry_size] = struct.pack(">L", target_lba)
                    lba_buffer_current_offset += lba_entry_size
        
        self.lba_entry_buffer = lba_buffer

    def _error_handle(self, check_test_size = 0, check_chunk_size = 0):
        #if (check_test_size > 0x1000000):
            #raise 'Exceed MAX_TASK_ENTRY, SDK cant handle'
        
        #if(check_chunk_size % 4 != 0):
            #raise ValueError("chunk size can't be supported")
        pass

    def _load_normal_mode_arg(self):
        self.perf_arg.qd = 32
        self.perf_arg.lun = 0
        self.perf_arg.mode = 0 #not used
        self.perf_arg.direction = 0 #0:read, 1:write, 5:read16, 6:write16
        self.perf_arg.block_size = 0xC #follow spec, 0XC = 4KB (should be a fixed value)
        self.perf_arg.chunk_size = 0x12 #0x12 , 1 * 2 ^2 = 4KB
        self.perf_arg.total_lba_cnt = 0 #struct.pack(r">L", 1) #same as lba entry
        self.perf_arg.lba_sector_cnt = 16 #struct.pack(r">L", 10) # (PerfVarPtr->dwTaskEntry / dwEntryPerPage, 16 == 512B * 16
        self.perf_arg.latency_start_addr = 0 #struct.pack(r">L", 0)
        self.perf_arg.op_timeout =  0 #struct.pack(r">L", 0) #timeout setting for each operation, 0 means no timeou execution 
        self.perf_arg.attribute = 0
        self.perf_arg.cmd_timeout = 0 #struct.pack(r">L", 0)
        self.perf_arg.pattern_mode = 0 #0:increase 1:Decrease 2:Fix 3:Random , should be parameter
            #bit[5] - 1 : Enable AddTag , 0 : Disable AddTag,
            #bit[6] - 1 : Enable HW compare , 0 : Disable HW compare  when Direction is Read
            #bit[7] - 1 : Enable Get Fail data (performance will drop) , 0 : Disable Get Fail data
        self.perf_arg.pattern_tag = 0 #struct.pack(r">L", 0) #if pattern_mode bit[5] is 1, this value will be used as pattern tag
        self.perf_arg.seed_h = 0 #struct.pack(r">L", 0) #if pattern_mode = 2, this value will be used as seed for fix mode
        self.perf_arg.seed_l = 0 #struct.pack(r">L", 0) #if pattern_mode = 2, this value will be used as seed for fix mode
        
        self.perf_arg.by_4k_gen = 0 #seems no used
        self.perf_arg.group_no = 0 #upiu contex id, should be parameter
        self.perf_arg.sample_rate_gap_time = 0 #struct.pack(r">L", 0)
        self.perf_arg.total_execute_time = 0 #struct.pack(r">L", 0)

    def _load_latency_mode_arg(self):
        pass

    def executer(self, assign_qd=32, assign_lun=0, assign_direction=1, assign_chunk_size_in_kbyte= 4, assign_test_size_in_kbyte = 0, enable_latency_mode = 0, test_mode = 0, allow_lba_overlap = 0, assign_start_lba = 0, assign_end_lba = 0):
        
        #self._error_handle(assign_test_size_in_kbyte, assign_chunk_size_in_kbyte)
        
        self.test_mode = test_mode

        if enable_latency_mode == 0:
            self._load_normal_mode_arg()
        elif enable_latency_mode == 1:
            self._load_latency_mode_arg()

        self.total_test_size_kbyte = assign_test_size_in_kbyte

        ### chunk size covert into low 4bit and high 4bit (sdk rule)
        chunk_size_low4bit = 0
        chunk_size_high4bit = assign_chunk_size_in_kbyte 
        while (chunk_size_high4bit % 2 == 0):
            chunk_size_high4bit //= 2
            chunk_size_low4bit += 1
            if (chunk_size_low4bit == 15):
                break

        if (chunk_size_low4bit > 15):
            raise ValueError("dwChunkSize_low4bit exceeds the maximum value of 15")
        ###
        task_entry = assign_test_size_in_kbyte // assign_chunk_size_in_kbyte
        self.perf_arg.total_lba_cnt = task_entry
        entry_page_size = 128 #512B per page, one lba entry is 4B

        #Caculate total sector count
        sector_size_in_8KB = (8 * 1024) // 512 
        sector_cnt = task_entry // entry_page_size

        if (task_entry % entry_page_size): #how many sectors were occuipied by task_entry
            sector_cnt += 1

        if (sector_cnt % sector_size_in_8KB): #fill sector to align 8KB
            sector_cnt = sector_cnt + (sector_size_in_8KB - (sector_cnt % sector_size_in_8KB)) #Align 8KB 

        ### using user setting
        self.perf_arg.qd = assign_qd
        self.perf_arg.lun = assign_lun
        self.perf_arg.direction = assign_direction
        self.perf_arg.chunk_size = (chunk_size_high4bit << 4) + (chunk_size_low4bit & 0xF) #follow sdk rule
        self.perf_arg.lba_sector_cnt = sector_cnt
        ###

        #create lba buffer
        #self.chunk_in_block = (assign_chunk_size_in_kbyte * 1024) >> self.perf_arg.block_size 
        self.chunk_in_block = assign_chunk_size_in_kbyte // 4 
        lba_buffer_size = sector_cnt * 512
        self._prepare_lba_buffer(lba_buffer_size, test_mode, assign_start_lba, assign_end_lba, self.chunk_in_block, task_entry, allow_lba_overlap)
        self.result_buffer, self.info_buffer = _sdk.performance(self.perf_arg, self.lba_entry_buffer)
    
    def do_exception(self):
        raise Exception("Test Exception")
