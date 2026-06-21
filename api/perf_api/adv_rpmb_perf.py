from Script.api import shared
from Script.api.ufs_api.upiu.structs import AdvRpmbMetaInfo
from Script.lib import sdk_lib as lib
from enum import Enum
import random
import struct
import hashlib
import hmac
from Script import api

_sdk = shared.sdk

BLOCK_SIZE_4KB = 0X1000

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

class _Advanced_RPMB_Meta_Information():
    def __init__(self):
        self.message_type = bytearray(16)
        self.nonce = bytearray(32)
        self.write_counter = bytearray(32)
        self.addressOfLUN = bytearray(16)
        self.block_count = bytearray(16)
        self.result = bytearray(16)

class _AdvRpmbMSGDataFrame():
    def __init__(self):
        self.ehs_header = 0
        self.adv_meta_info = _Advanced_RPMB_Meta_Information()
        self.mac_key = bytearray(64)

class AdvRpmbPerformanceVar():
    def __init__(self):
        self.mode = 0 #0: Seq , 1: Ran
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

class AdvanceRpmbPerformanceClass():
    def __init__(self):
        #Buffer for rpmbperformance api
        self.lba_entry_buffer = None
        self.result_buffer = None
        self.info_buffer = None
        self.key = bytearray([0x78, 0x56, 0x34, 0x12] * 8)
        self.adv_rpmb = None
        self.region_id = None

        #Variable for rpmbperformance api
        self.adv_rpmbperf_arg = lib.AdvRpmbPerformanceArg()
        self.adv_rpmb_msg_data_frame = _AdvRpmbMSGDataFrame()
        self.adv_meta_info = AdvRpmbMetaInfo()
        self.total_test_size_kbyte = 0
        self.test_mode = 0
        self.chunk_in_block = 0

    def adv_rpmb_init(self, region_id): 
        self.region_id = region_id
        self.adv_rpmb = api.AdvRPMB(self.region_id)
        try:
            self.adv_meta_info.l18_write_counter = self.adv_rpmb.adv_rpmb_read_counter()
        except (api.SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET) as e:            
            self.adv_rpmb.adv_rpmb_key_programming()
            try:
                self.adv_meta_info.l18_write_counter = self.adv_rpmb.adv_rpmb_read_counter()
            except Exception as e:
                print(f"Failed to read Advance RPMB counter after programming key: {e}")
        except Exception as e:
            print(f"Failed to read Advance RPMB counter: {e}")
            
    def _get_performance_result(self):
        total_execute_time = int.from_bytes(self.result_buffer[4:8], byteorder='big', signed=False) #unit: us
        test_size_in_mbyte = self.total_test_size_kbyte * self.adv_rpmbperf_arg.rpmb_region / 1024 #region for what?
        total_execute_time_in_sec = total_execute_time / (1000 * 1000)
        performance_mbyte_per_second = test_size_in_mbyte / total_execute_time_in_sec
        performance_io_per_second = (performance_mbyte_per_second * 1024 * 1024) / (self.chunk_in_block * 4 * 1024)

        if self.test_mode == RpmbPerformanceMode.SEQUENTIAL.value:
            return performance_mbyte_per_second
        else:
            return performance_io_per_second


    def _prepare_lba_buffer(self, lba_buffer_size, rpmb_perf_var: AdvRpmbPerformanceVar, lba_entry_cnt):
        lba_buffer = bytearray(lba_buffer_size * [0xff])
        lba_entry_size = 64 #64B per entry
        mac_entry_size = 32 #32B per mac entry
        lba_buffer_current_offset = 0
        lba_current_offset = 0
        transfer_data_size = rpmb_perf_var.chunk_size_in_rpmb_block * 4096
        data_container = []
        

        if rpmb_perf_var.direction == RpmbPerformanceDirection.WRITE.value:
            for i in range(transfer_data_size):
                data_container.append(0xAA)

        if self.test_mode == RpmbPerformanceMode.SEQUENTIAL.value:
            lba_current_offset = rpmb_perf_var.start_lba
            for i in range(0, lba_entry_cnt):
                lba_buffer_current_offset = i * lba_entry_size
                
                if rpmb_perf_var.direction == RpmbPerformanceDirection.WRITE.value:
                    self.adv_meta_info.w22_address_lun=  lba_current_offset

                    mac = self._gen_rpmb_mac(data_container) #set mac to meta info

                    #mac_key change big endian to lba_buffer
                    lba_buffer[lba_buffer_current_offset : lba_buffer_current_offset + mac_entry_size] = mac #self._swap_endian_every_4_bytes(mac)
                    self.adv_meta_info.l18_write_counter += 1
                
                lba_buffer[lba_buffer_current_offset + mac_entry_size : lba_buffer_current_offset + mac_entry_size + 2] = struct.pack(r">H", lba_current_offset)
                lba_current_offset += rpmb_perf_var.chunk_size_in_rpmb_block

        elif self.test_mode == RpmbPerformanceMode.RANDOM.value:
            lba_current_offset = 0
            # Arrange LBA pool
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

            #pick up form LBA pool and prepare lba buffer for performance api
            for i in range(0, lba_entry_cnt):
                lba_buffer_current_offset = i * lba_entry_size
                RandLBAIdx = random.randint(0, lba_cnt - 1)

                lba_current_offset = total_lba[RandLBAIdx]
                lba_buffer[lba_buffer_current_offset + mac_entry_size : lba_buffer_current_offset + mac_entry_size + 2] = struct.pack(r">H", lba_current_offset)

                if rpmb_perf_var.allow_lba_overlap == 0:
                    total_lba[RandLBAIdx] = total_lba[lba_cnt - 1]
                    lba_cnt -= 1

                    if (lba_cnt == 0) and (i < lba_entry_cnt - 1): #need to improve
                        raise 'LBA Entry Cnt Exceed LBA_Cnt when allow lba overlap'

                if rpmb_perf_var.direction == RpmbPerformanceDirection.WRITE.value:
                    self.adv_meta_info.w22_address_lun =  lba_current_offset

                    mac = self._gen_rpmb_mac(data_container)

                    #mac_key change big endian to lba_buffer
                    lba_buffer[lba_buffer_current_offset : lba_buffer_current_offset + mac_entry_size] = mac
                    self.adv_meta_info.l18_write_counter += 1
                
                lba_buffer[lba_buffer_current_offset + mac_entry_size : lba_buffer_current_offset + mac_entry_size + 2] = struct.pack(r">H", lba_current_offset)
                lba_current_offset += rpmb_perf_var.chunk_size_in_rpmb_block

        self.lba_entry_buffer = lba_buffer

    def _error_handle(self, rpmb_perf_var: AdvRpmbPerformanceVar):
        pass
        
    def _load_normal_mode_arg(self):
        self.adv_rpmbperf_arg.mode = 0 #not used
        self.adv_rpmbperf_arg.direction = 0 #0:read, 1:write
        self.adv_rpmbperf_arg.block_size = 0XC #4KB
        self.adv_rpmbperf_arg.rpmb_chunk_size = 0 #uint = 4KB
        self.adv_rpmbperf_arg.rpmb_write_cnt = 0
        self.adv_rpmbperf_arg.total_lba_cnt = 0
        self.adv_rpmbperf_arg.lba_sector_cnt = 0
        self.adv_rpmbperf_arg.op_timeout = 0
        self.adv_rpmbperf_arg.rpmb_region = 0
        self.adv_rpmbperf_arg.rpmb_region_enable = 0 #bit0 - Region 0, bit1 - Region 1, bit2 - Region 2, bit3 - Region 3
        self.adv_rpmbperf_arg.rpmb_write_cnt_enable = 0
        self.adv_rpmbperf_arg.cmd_timeout = 0
        self.adv_rpmbperf_arg.latency_start_addr = 0

    def _load_latency_mode_arg(self):
        raise "Advance Not Support Latency Mode now"

    def executer(self, rpmb_perf_var: AdvRpmbPerformanceVar):   
        self._error_handle(rpmb_perf_var)
        
        self.test_mode = rpmb_perf_var.mode
        self.total_test_size_kbyte = rpmb_perf_var.test_size_in_kbyte
        self.chunk_in_block = rpmb_perf_var.chunk_size_in_rpmb_block
        
        if rpmb_perf_var.latency == 0:
            self._load_normal_mode_arg()
        elif rpmb_perf_var.latency == 1:
            self._load_latency_mode_arg()
            raise 'not support latency'
        
        task_entry = (rpmb_perf_var.test_size_in_kbyte) // (rpmb_perf_var.chunk_size_in_rpmb_block * 4) #adv rpmb block is 4KB
        self.adv_rpmbperf_arg.total_lba_cnt = task_entry
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
        self.adv_rpmbperf_arg.direction = rpmb_perf_var.direction
        self.adv_rpmbperf_arg.block_size = 0XC #4KB, can be changed by user
        self.adv_rpmbperf_arg.rpmb_chunk_size = rpmb_perf_var.chunk_size_in_rpmb_block
        self.adv_rpmbperf_arg.rpmb_write_cnt = self.adv_meta_info.l18_write_counter
        self.adv_rpmbperf_arg.lba_sector_cnt = sector_cnt
        self.adv_rpmbperf_arg.rpmb_region = rpmb_perf_var.rpmb_region
        self.adv_rpmbperf_arg.rpmb_region_enable = rpmb_perf_var.rpmb_region_enable
        self.adv_rpmbperf_arg.rpmb_write_cnt_enable = rpmb_perf_var.write_count_enable
        ###
        
        lba_buffer_size = sector_cnt * 512
        self._prepare_lba_buffer(lba_buffer_size, rpmb_perf_var, task_entry)
        self.result_buffer, self.info_buffer = _sdk.adv_rpmb_performance(self.adv_rpmbperf_arg, self.lba_entry_buffer)

        return self._get_performance_result()
    
    def random_nonce(self):
        return bytearray(random.getrandbits(8) for i in range(16))

    def _gen_rpmb_mac(self, write_buf:bytearray):
        ehs = bytearray(64)     
        ehs[0] = 0x02   # bLength
        ehs[1] = 0x01   # bEHSType
        ehs[5] = RpmbMsgType.RPMB_DATA_WRITE_REQ
        nonce = bytearray([0x00] * 16)
        ehs[6:22] = nonce
        ehs[22:26] = struct.pack(r'>L', self.adv_meta_info.l18_write_counter)
        ehs[26:28] = struct.pack(r'>H', self.adv_meta_info.w22_address_lun)
        ehs[28:30] = struct.pack(r'>H', self.chunk_in_block)
       
        '''filename = "ehs.bin"
        with open(filename, "wb") as file:
            file.write(ehs[4:32])
        file.close()'''

        hmac_input = bytearray()
        hmac_input.extend(write_buf)
        hmac_input.extend(ehs[4:32])
        hmac_input.extend(bytearray(4))

        '''filename = "hmac.bin"
        with open(filename, "wb") as file:
            file.write(hmac_input)
        file.close()'''

        __key_val =  bytearray([0x12, 0x34, 0x56, 0x78] * 8)

        '''filename = "key.bin"
        with open(filename, "wb") as file:
            file.write(__key_val)
        file.close()'''

        result = api.hmac_sha256(__key_val, hmac_input)

        '''filename = "result.bin"
        with open(filename, "wb") as file:
            file.write(result)
        file.close()'''

        return result
    
    def _swap_endian_every_4_bytes(self, byte_array):
        chunks = [byte_array[i:i+4] for i in range(0, len(byte_array), 4)]

        swapped_chunks = []
        for chunk in chunks:
            unpacked = struct.unpack('<L', chunk)[0]
            packed = struct.pack('>L', unpacked)
            swapped_chunks.append(packed)

        result = b''.join(swapped_chunks)
        return result