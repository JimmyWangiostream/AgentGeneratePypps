from typing import List
from Script.api import shared
from Script.api.cmd_seq.protocols import IsCmdUpiuEntry
from Script.api.exception import PATTERN_ASSERT_NOT_IMPLEMENTED, PATTERN_ASSERT_UNEXPECTED_CONDITION
from Script.api.ufs_api.defines import CmdParamPatternMode
from Script.api.ufs_api.upiu import structs
from Script.api.ufs_api.upiu.protocols import IsUpiu
from Script.api.ufs_api.upiu.upiu import BaseUnmap, BaseWrite10, BaseWrite16, BaseWrite6
from Script.api.util.write_record.crc import crc32_1byte
from Script.api.util.write_record.structs import WriteRecordNode
from Script.api.util.functions import dumpfile

_log = shared.logger

def get_empty_write_record() -> List[List[WriteRecordNode]]:
    return [[] for _ in range(32)]

def binary_search(write_record: List[WriteRecordNode], start_lba: int, end_lba: int) -> int:
    mid = 0
    left = 0
    right = len(write_record) - 1

    _start_lba = 0
    _end_lba = 0
    _cover_node = 0

    while left <= right:
        mid = (left + right) // 2
        _start_lba = write_record[mid].start_lba
        _end_lba = write_record[mid].end_lba

        # New    |-------|        |-------|
        # Old  |------|              |-------|
        if _start_lba <= start_lba and _end_lba >= start_lba:  # 如果 start 在範圍內
            return mid
        elif _start_lba <= end_lba and _end_lba >= end_lba:  # 如果 end 在範圍內
            _cover_node = mid  # 先找到End不能直接return, 有可能start也在前面的node有overlay, 要以start為主再往後掃, 所以先keep
            right = mid - 1;  # 繼續往左小的LBA找
        # New  |----------|
        # Old    |------|
        elif start_lba <= _start_lba and end_lba >= _end_lba:  # New start, end 含蓋 Old Start End
            _cover_node = mid  # 因為這個node被含蓋，有可能在其它node是只有start或是end, 或是沒有。如果沒有在其它node，則return 此node
            right = mid - 1;	# 繼續往左小的LBA找
        elif _start_lba > start_lba:
            right = mid - 1
        elif _start_lba < start_lba:
            left = mid + 1

    if _cover_node != 0:  # while裡沒有return lMid表示都不到，即return cover node，如果沒有cover node則return leaf
        return _cover_node
    else:
        return mid

def save_write_info(start_lba: int, block_count: int, data_pattern_mode: CmdParamPatternMode, add_tag: int, mark_tag: int, write_record: List[WriteRecordNode]) -> None:
    _log.info("function - save_write_info()")
    
    insert = False
    new_start = start_lba
    new_end = start_lba + block_count - 1

    if len(write_record) == 0:
        write_node = WriteRecordNode()
        write_node.start_lba = new_start
        write_node.end_lba = new_end
        write_node.data_pattern_mode = data_pattern_mode
        write_node.add_tag = add_tag 
        write_node.mark_tag = mark_tag
        write_record.append(write_node)
        return
    
    start_index = binary_search(write_record, new_start, new_end)
    current_node: WriteRecordNode | None = write_record[start_index]
 
    while current_node != None:
        old_start = current_node.start_lba
        old_end = current_node.end_lba
        old_data_pattern_mode = current_node.data_pattern_mode
        old_add_tag = current_node.add_tag
        old_mark_tag = current_node.mark_tag

        if new_start <= old_start and new_end >= old_end:  # Case1. 新資料完全覆蓋舊資料，則最早那筆完全無效，設StartLBA = -1
            # //New  |-----|     |--------|     |--------|
			# //Old  |-----|       |----|          |-----|
			# //==>  |-----|     |--------|     |--------|
            if insert:
                write_record.pop(start_index)
                if start_index >= len(write_record):
                    break
                else:
                    current_node = write_record[start_index]
                    continue
            else:
                current_node.start_lba = new_start
                current_node.end_lba = new_end
                current_node.add_tag = add_tag
                current_node.mark_tag = mark_tag
                current_node.data_pattern_mode = data_pattern_mode                
                insert = True

        elif old_start <= new_start and old_end > new_end:  # Case2. 如果舊資料含蓋新資料，則將舊資料覆蓋，並且切成2段
            # //New  |----|	        |------|          
			# //Old  |------|     |-----------| 
			# //==>  |----|-|     |-|------|--|
            current_node.start_lba = new_end + 1  # 將舊資料的start改成新資料end往右左一筆，才不會重覆
            if not insert:
                new_node = WriteRecordNode()
                new_node.start_lba = new_start
                new_node.end_lba = new_end
                new_node.data_pattern_mode = data_pattern_mode
                new_node.add_tag = add_tag
                new_node.mark_tag = mark_tag
                write_record.insert(start_index, new_node)
                if old_start != new_start:
                    new_node = WriteRecordNode()
                    new_node.start_lba = old_start
                    new_node.end_lba = new_start - 1
                    new_node.data_pattern_mode = old_data_pattern_mode
                    new_node.add_tag = old_add_tag
                    new_node.mark_tag = old_mark_tag                    
                    write_record.insert(start_index, new_node)
            break  # 新資料在此node舊資料內，所以不可能蓋到其它舊資料，即break不再往下找

        elif new_start >= old_start and new_start <= old_end:  # Case3. 新資料的Start在舊資料的範圍內
            # //New     |----|	       |------|        
			# //Old  |----|       |-----------|       
			# //==>  |--|----|    |----|------|
            current_node.end_lba = new_start - 1  # 將舊資料的End改成新資料Start往左一筆，才不會重覆
            if not insert:
                new_node = WriteRecordNode()
                new_node.start_lba = new_start
                new_node.end_lba = new_end
                new_node.data_pattern_mode = data_pattern_mode
                new_node.add_tag = add_tag
                new_node.mark_tag = mark_tag                
                write_record.insert(start_index + 1, new_node)
                start_index += 1    # python 跟 C 不一樣，這裡插入後又會被拿出來，所以要多跳一格
                insert = True

        elif new_end >= old_start and new_end <= old_end:  # Case4. 新資料的End在舊資料的範圍內
            # //New  |----|	      
			# //Old     |----| 
			# //==>  |----|--|
            current_node.start_lba = new_end + 1  # 將舊資料的start改成新資料end往右左一筆，才不會重覆
            if not insert:
                new_node = WriteRecordNode()
                new_node.start_lba = new_start
                new_node.end_lba = new_end
                new_node.data_pattern_mode = data_pattern_mode
                new_node.add_tag = add_tag
                new_node.mark_tag = mark_tag                
                write_record.insert(start_index, new_node)
                insert = True
            break  # 新資料的End在此node舊資料內，所以不可能蓋到其它舊資料，即break不再往下找

        else:  # 找不到資料
            # //New  |----|	                      |----|
			# //Old          |----|       |----|  
            if not insert:
                new_node = WriteRecordNode()
                new_node.start_lba = new_start
                new_node.end_lba = new_end
                new_node.data_pattern_mode = data_pattern_mode
                new_node.add_tag = add_tag
                new_node.mark_tag = mark_tag
                if new_end < old_start:
                    write_record.insert(start_index, new_node)
                else:
                    write_record.insert(start_index + 1, new_node)

            break  # 沒重覆，不可能蓋到其它舊資料，即break不再往下找

        start_index += 1

        if start_index < len(write_record):
            current_node = write_record[start_index]
        else:
            current_node = None
     
def save_write_info_by_cmd(cmd: IsUpiu, write_record: List[List[WriteRecordNode]]) -> None:
    if not isinstance(cmd, (BaseWrite6, BaseWrite10, BaseWrite16, BaseUnmap)):
        _log.warning(f'Skip UPIU {type(cmd)}. Not related to write_record.')
        return
    
    if isinstance(cmd, IsCmdUpiuEntry):
        add_tag = cmd.param.w36_add_tag
        mark_tag = cmd.param.l38_mark_tag_or_crc32
        pattern_mode = cmd.param.w36_pattern_mode
    #elif:
    #   place holder for normal send
    else:
        _log.error(f'Invalid cmd object: {type(cmd)}')

    lun = cmd.upiu.b2_lun
    cdb = cmd.upiu.u16_cdb
    if isinstance(cdb, structs.CdbWrite6):
        lba = (cdb.b1_lba_h << 16) + cdb.w2_lba_l
        data_len = cdb.b4_transfer_length
        _log.info(f"write lun={lun}, startlba=0x{lba:X}, endlba=0x{(lba + data_len - 1):X}, len=0x{data_len:X}, add_tag={bool(add_tag)}, mark_tag=0x{mark_tag:X}")
        save_write_info(lba, data_len, pattern_mode, add_tag, mark_tag, write_record[lun])
    elif isinstance(cdb, structs.CdbWrite10):
        lba = cdb.l2_lba
        data_len = cdb.w7_transfer_length
        _log.info(f"write lun={lun}, startlba=0x{lba:X}, endlba=0x{(lba + data_len - 1):X}, len=0x{data_len:X}, add_tag={bool(add_tag)}, mark_tag=0x{mark_tag:X}")
        save_write_info(lba, data_len, pattern_mode, add_tag, mark_tag, write_record[lun])
    elif isinstance(cdb, structs.CdbWrite16):
        lba = (cdb.l2_lba_h << 32) + cdb.l6_lba_l
        data_len = cdb.l10_transfer_length
        _log.info(f"write lun={lun}, startlba=0x{lba:X}, endlba=0x{(lba + data_len - 1):X}, len=0x{data_len:X}, add_tag={bool(add_tag)}, mark_tag=0x{mark_tag:X}")
        save_write_info(lba, data_len, pattern_mode, add_tag, mark_tag, write_record[lun])
    elif isinstance(cmd, BaseUnmap):
        for desc in cmd._block_descriptors:
            lba = (desc.l0_lba_h << 32) + desc.l4_lba_l
            data_len = desc.l8_number_of_logical_blocks
            _log.info(f"unmap lun={lun}, startlba=0x{lba:X}, endlba=0x{(lba + data_len - 1):X}, len=0x{data_len:X}")
            save_write_info(lba, data_len, data_pattern_mode=CmdParamPatternMode.PTN_ERASE, add_tag=0, mark_tag=0, write_record=write_record[lun])
    else:
        _log.error('unexpected condition.')
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION

def gen_data_pattern(chunk_size: int, data_pattern_mode: int, lba: int, add_tag: int, loop_count: int) -> bytearray:
        
    i = 0
    tmp_buffer = bytearray(chunk_size)
    
    lba_4k = 0
    lba_mark = 0
   
    lba_mark = lba * (chunk_size // 512)
    # lba_4k = lba * (64 * (chunk_size // 512)) 
    lba_4k = lba * (64 * (chunk_size // 512)) & 0xFFFFFFFF

    # print(f"lba={lba}") 
    # print(f"lba_4k=0x{lba_4k:x}") 

    if data_pattern_mode == CmdParamPatternMode.HW_INCREASE:
        for i in range(0, chunk_size // 4, 2):
            if add_tag == 1:
                if (i % 128) == 0:
                    tmp_buffer[(i+1)*4:(i+2)*4] = lba_mark.to_bytes(4, byteorder='big')
                    lba_mark += 1
                else:
                    tmp_buffer[(i+1)*4:(i+2)*4] = lba_4k.to_bytes(4, byteorder='big')
                tmp_buffer[i*4: (i+1)*4] = loop_count.to_bytes(4, byteorder='big')
            else:
                tmp_buffer[(i+1)*4:(i+2)*4] = lba_4k.to_bytes(4, byteorder='big')
                tmp_buffer[i*4: (i+1)*4] = (0).to_bytes(4, byteorder='big')
            lba_4k += 1

    elif data_pattern_mode == CmdParamPatternMode.HW_FIX:
        
        # 2808 HW_FIX
        fix_data = 0x5A5A5A5A
        
        for i in range(0, chunk_size // 4):
            if add_tag == 1:
                if (i % 128) == 0:
                    tmp_buffer[i*4:(i+1)*4] = loop_count.to_bytes(4, byteorder='big')
                elif (i % 128) == 1:
                    tmp_buffer[i*4:(i+1)*4] = lba_mark.to_bytes(4, byteorder='big')
                    lba_mark += 1
                else:
                    tmp_buffer[i*4:(i+1)*4] = fix_data.to_bytes(4, byteorder='big')
            else:
                tmp_buffer[i*4:(i+1)*4] = fix_data.to_bytes(4, byteorder='big')

        # 2807 tester HW_FIX
        # for i in range(0, chunk_size // 4, 2):
        #     if (i % 128) == 0 and i != 0:
        #         lba_4k += (512 // 8)

        #     if add_tag == 1:
        #         if (i % 128) == 0:
        #             tmp_buffer[(i+1)*4:(i+2)*4] = lba_mark.to_bytes(4, byteorder='big')
        #             lba_mark += 1
        #         else:
        #             tmp_buffer[(i+1)*4:(i+2)*4] = lba_4k.to_bytes(4, byteorder='big')

        #         tmp_buffer[i*4:(i+1)*4] = loop_count.to_bytes(4, byteorder='big')
        #     else:
        #         tmp_buffer[i*4:(i+1)*4] = (0).to_bytes(4, byteorder='big')
        #         tmp_buffer[(i+1)*4:(i+2)*4] = lba_4k.to_bytes(4, byteorder='big')
    elif data_pattern_mode == CmdParamPatternMode.PTN_ERASE:
        tmp_buffer = bytearray([0] * chunk_size)

    else:
        _log.error('Pattern mode {data_pattern_mode} is not implemented.')
        raise PATTERN_ASSERT_NOT_IMPLEMENTED

    return tmp_buffer

def gen_data_buffer_for_crc32(write_node: WriteRecordNode, write_crc: int) -> int:
    _log.info("function - gen_data_buffer_for_crc32()")

    start_lba = write_node.start_lba
    data_len = write_node.end_lba - write_node.start_lba + 1
    data_pattern_mode = write_node.data_pattern_mode
    add_tag = write_node.add_tag
    loop_count = write_node.mark_tag
    chunk_size = 4096
    # chunk_size = 512

    data_buffer = bytearray(4096)  # 4KB 的 bytearray
    
    for j in range(data_len):
        data_buffer = gen_data_pattern(chunk_size, data_pattern_mode, start_lba + j, add_tag, loop_count)

        # dumpfile("data_buffer.bin", data_buffer)

        write_crc = crc32_1byte(data_buffer, chunk_size, write_crc)

        # for k in range(chunk_size // 512):
            # write_crc = crc32_1byte(data_buffer[512*k:512*(k+1)], 512, write_crc)

    # print(f'write_crc=0x{write_crc:x}')

    return write_crc


def find_record_to_gen_data_crc(lun: int, start_lba: int, data_len: int, write_record: List[WriteRecordNode]) -> int:

    write_crc = 0
    finish = False

    end_lba = start_lba + data_len - 1
    record_node = WriteRecordNode()

    start_index = binary_search(write_record, start_lba, end_lba)
    
    while (start_index < len(write_record)):
        current_node = write_record[start_index]

        if current_node.end_lba < start_lba:
            _log.info(f"no write record found!, node info => start_lba={current_node.start_lba}, end_lba={current_node.end_lba}, read info => lun={lun}, startlba={start_lba}, endlba={start_lba + data_len - 1}, len={data_len}")
    
        if current_node.start_lba <= start_lba and current_node.end_lba >= start_lba:
            record_node.start_lba = start_lba

            if end_lba < current_node.end_lba:
                record_node.end_lba = end_lba
            else:
                record_node.end_lba = current_node.end_lba

            record_node.data_pattern_mode = current_node.data_pattern_mode
            record_node.add_tag = current_node.add_tag
            record_node.mark_tag = current_node.mark_tag
            
            write_crc = gen_data_buffer_for_crc32(record_node, write_crc)

            if current_node.end_lba < end_lba:
                start_lba = current_node.end_lba + 1
                finish = False
            else:
                finish = True
                break

            start_index += 1
        else:
            _log.info(f"LBA {start_lba} out of <write_record> range, the record range from LBA {current_node.start_lba} to LBA {current_node.end_lba}")
            write_crc = -1        
            return write_crc

    if finish == False:
        _log.info(f"LBA {start_lba} out of <write_record> range, the record range from LBA {current_node.start_lba} to LBA {current_node.end_lba}")
        write_crc = -1     

    return write_crc


# def test_crc32() -> None:
#     _param = shared.param

#     # pby_write_data_buf = bytearray([0xA5] * 4096)

#     file_path = r'D:\Source Code\Git\PyPPS V3\results\data_buffer.bin'
#     with open(file_path, 'rb') as file:
#         pby_write_data_buf = file.read()

#     dw_size = 4096

#     for i in range(1):
#         # Assuming Software_CRC_16bytes_prefetch is defined elsewhere
#         # write_crc_16b = software_crc_16bytes_prefetch(pby_write_data_buf, dw_size, i)
#         write_crc_1b = crc32_1byte(pby_write_data_buf, dw_size, 0)
        
#         print(f"0x{write_crc_1b:x}")  # 輸出 '0xff'
#         # print(f"0x{write_crc_16b:x}")  # 輸出 '0xff'
  