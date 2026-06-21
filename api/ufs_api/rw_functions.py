
import random
from typing import List, cast
from Script.api import shared
import Script.api.cmd_seq as ExecuteCMD
from Script.api.cmd_seq.protocols import IsCmdUpiuEntry
from Script.api.exception import *
from Script.api.ufs_api.defines import CmdParamPatternMode, CompareMethod
from Script.api.ufs_api.upiu import structs
from Script.api.util.write_record.functions import find_record_to_gen_data_crc, gen_data_buffer_for_crc32, save_write_info, save_write_info_by_cmd
from Script.api.util.write_record.structs import WriteRecordNode
from Script import api

_log = shared.logger

def write_all_lun(write_record: List[List[WriteRecordNode]]) -> None:
    _param = shared.param
    
    max_chunk_size = 65535

    for lun in range(0, _param.gMaxNumberLU):
        if _param.gUnit[lun].b3_lu_enable:
            count = 0
            lba = 0            
            datalen = _param.gLUCapacity[lun]

            while datalen > 0:
                chunk_size = min(max_chunk_size, datalen)

                write10 = ExecuteCMD.Write10()
                write10.assign(lun=lun, lba=lba, length=chunk_size, fua=0)
                write10.set_option(pattern_mode=CmdParamPatternMode.HW_FIX)

                datalen -= chunk_size
                lba += chunk_size

                ExecuteCMD.enqueue(write10)

            ExecuteCMD.send(clear_on_success=False, timeout=api.UniformTimeout(val=write10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
            for cmd in ExecuteCMD._cmd_list:
                save_write_info_by_cmd(cmd, write_record)
            ExecuteCMD.clear()
 
def read_compare(write_record: List[List[WriteRecordNode]], compare_method: int = CompareMethod.HW_COMPARE) -> None:
    _log.info("function - read_compare()")
    
    for lun in range(len(write_record)):
        if len(write_record[lun]) > 0:
            if compare_method == CompareMethod.HW_COMPARE:
                for node in range(len(write_record[lun])):
                    write_node = write_record[lun][node]

                    if write_node.data_pattern_mode == CmdParamPatternMode.PTN_ERASE:
                        pass
                    else:
                        lba = write_node.start_lba
                        data_len = write_node.end_lba - write_node.start_lba + 1
                        mark_tag = write_node.mark_tag
                        data_pattern_mode: CmdParamPatternMode = write_node.data_pattern_mode

                        read10 = ExecuteCMD.Read10()
                        read10.assign(lun=lun, lba=lba, length=data_len)
                        read10.set_hw_cmp(mark_tag=mark_tag, pattern_mode=data_pattern_mode)
                        ExecuteCMD.enqueue(read10)

                if len(ExecuteCMD._cmd_list) > 0:
                    ExecuteCMD.send(read_hw_compare=True, timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))


                for node in range(len(write_record[lun])):
                    write_node = write_record[lun][node]

                    if write_node.data_pattern_mode == CmdParamPatternMode.PTN_ERASE:                        
                        lba = write_node.start_lba
                        data_len = write_node.end_lba - write_node.start_lba + 1

                        write_crc = 0

                        read10 = ExecuteCMD.Read10()
                        read10.assign(lun=lun, lba=lba, length=data_len)
                        read10.set_sw_cmp(crc32=write_crc)
                        ExecuteCMD.enqueue(read10)

                if len(ExecuteCMD._cmd_list) > 0:
                    ExecuteCMD.send(timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))


            elif compare_method == CompareMethod.SW_COMPARE:
                for node in range(len(write_record[lun])):
                    write_node = write_record[lun][node]
                    
                    lba = write_node.start_lba
                    data_len = write_node.end_lba - write_node.start_lba + 1

                    write_crc = gen_data_buffer_for_crc32(write_node, 0)

                    read10 = ExecuteCMD.Read10()
                    read10.assign(lun=lun, lba=lba, length=data_len)
                    read10.set_sw_cmp(crc32=write_crc)
                    ExecuteCMD.enqueue(read10)

                if len(ExecuteCMD._cmd_list) > 0:
                    ExecuteCMD.send(timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
            
def random_write(cmd_count: int, min_lun: int, max_lun: int, min_lba: int, max_lba: int, min_size: int, max_size: int, need_compare: bool, 
                  compare_method: int, write_record: List[List[WriteRecordNode]], fua:int = 0) -> None:
    _log.info("function - random_write()")
    
    _param = shared.param
        
    if max_lba < min_lba:
        raise PATTERN_ASSERT_UFS_WRONG_PARAMETER_LBA_SIZE_CHECK_ERROR
    elif (max_lun > _param.gMaxNumberLU-1) or (max_lun < min_lun):
        raise PATTERN_ASSERT_UFS_WRONG_PARAMETER_LUN_CHECK_ERROR
    elif (cmd_count < 1) or (cmd_count > 256):
        raise PATTERN_ASSERT_UFS_WRONG_PARAMETER_CMD_CNT_CHECK_ERROR
    elif max_size > api.WRITE_10_MAX_BLOCK_LEN:
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION
    else:

        _max_lba = max_lba    # 只有外面傳進來的 max_lba 有機會會被改掉，所以另外定一個參數，下一個loop才不會有問題

        for _ in range(1, cmd_count + 1):

            random_lun_count = 0

            if min_lun == max_lun:
                lun = min_lun
            else:
                while True:
                    lun = random.randint(min_lun, max_lun)
                    
                    random_lun_count += 1
                    if random_lun_count > 100:                        
                        raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT                         
                    
                    if _param.gUnit[lun].b3_lu_enable:
                        break
            
            if max_lba >= _param.gLUCapacity[lun]:
                _max_lba = _param.gLUCapacity[lun]

            if min_size != max_size:
                data_len = random.randint(min_size, max_size)
            else:
                data_len = min_size

            if data_len >= _param.gLUCapacity[lun]:
                data_len = _param.gLUCapacity[lun]

            if (_max_lba - data_len) < min_lba:
                start_lba = min_lba
            else:
                start_lba = random.randint(min_lba, _max_lba - data_len)

            if (start_lba + data_len) > _param.gLUCapacity[lun]:
                start_lba = _param.gLUCapacity[lun] - data_len

            write10 = ExecuteCMD.Write10()
            write10.assign(lun=lun, lba=start_lba, length=data_len, fua=fua)

            ExecuteCMD.enqueue(write10)
            
        ExecuteCMD.send(clear_on_success=False, timeout=api.UniformTimeout(val=write10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
        for cmd in ExecuteCMD._cmd_list:
            save_write_info_by_cmd(cmd, write_record)
        ExecuteCMD.clear()

        if (need_compare):
            read_compare(write_record, compare_method)

def random_read(cmd_count: int, min_lun: int, max_lun: int, min_lba: int, max_lba: int, min_size: int, max_size: int, need_compare: bool, write_record: List[List[WriteRecordNode]]) -> None:
    _log.info("function - random_read()")
    
    _param = shared.param

    write_crc = 0

    if max_lba < min_lba:
        raise PATTERN_ASSERT_UFS_WRONG_PARAMETER_LBA_SIZE_CHECK_ERROR
    elif (max_lun > _param.gMaxNumberLU-1) or (max_lun < min_lun):
        raise PATTERN_ASSERT_UFS_WRONG_PARAMETER_LUN_CHECK_ERROR
    elif (cmd_count < 1) or (cmd_count > 256):
        raise PATTERN_ASSERT_UFS_WRONG_PARAMETER_CMD_CNT_CHECK_ERROR
    else:
        _max_lba = 0    # 只有外面傳進來的 max_lba 有機會會被改掉，所以另外定一個參數，下一個loop才不會有問題

        for _ in range(1, cmd_count + 1):
            
            random_lun_count = 0

            if min_lun == max_lun:
                lun = min_lun
            else:
                while True:
                    lun = random.randint(min_lun, max_lun)
                    
                    random_lun_count += 1
                    if random_lun_count > 100:                        
                        raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
                    
                    if _param.gUnit[lun].b3_lu_enable:
                        break
            
            if max_lba >= _param.gLUCapacity[lun]:
                _max_lba = _param.gLUCapacity[lun]

            if min_size != max_size:
                data_len = random.randint(min_size, max_size)
            else:
                data_len = min_size

            if data_len >= _param.gLUCapacity[lun]:
                data_len = _param.gLUCapacity[lun]

            if (_max_lba - data_len) < min_lba:
                start_lba = min_lba
            else:
                start_lba = random.randint(min_lba, _max_lba - data_len)

            if (start_lba + data_len) > _param.gLUCapacity[lun]:
                start_lba = _param.gLUCapacity[lun] - data_len

            read10 = ExecuteCMD.Read10()
            read10.assign(lun=lun, lba=start_lba, length=data_len, fua=0)
            # write10.assign(lun=0, lba=0, length=3, fua=0)

            if (need_compare):
                write_crc = find_record_to_gen_data_crc(lun, start_lba, data_len, write_record[lun])

                if write_crc != -1:   # -1 表示找不到 write record，表示 read 的地方沒有寫過，就無法 compare
                    read10.set_sw_cmp(crc32=write_crc)

            ExecuteCMD.enqueue(read10)

        ExecuteCMD.send(timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))

def random_erase(cmd_count: int, min_lun: int, max_lun: int, min_lba: int, max_lba: int, min_size: int, max_size: int, write_record: List[List[WriteRecordNode]]) -> None:
    _log.info("function - random_erase()")
    
    _param = shared.param

    write_crc = 0

    if max_lba < min_lba:
        raise PATTERN_ASSERT_UFS_WRONG_PARAMETER_LBA_SIZE_CHECK_ERROR
    elif (max_lun > _param.gMaxNumberLU-1) or (max_lun < min_lun):
        raise PATTERN_ASSERT_UFS_WRONG_PARAMETER_LUN_CHECK_ERROR
    elif (cmd_count < 1) or (cmd_count > 256):
        raise PATTERN_ASSERT_UFS_WRONG_PARAMETER_CMD_CNT_CHECK_ERROR
    else:
        _max_lba = 0    # 只有外面傳進來的 max_lba 有機會會被改掉，所以另外定一個參數，下一個loop才不會有問題

        for _ in range(1, cmd_count + 1):
            
            random_lun_count = 0

            if min_lun == max_lun:
                lun = min_lun
            else:
                while True:
                    lun = random.randint(min_lun, max_lun)
                    
                    random_lun_count += 1
                    if random_lun_count > 100:                        
                        raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
                    
                    if _param.gUnit[lun].b3_lu_enable:
                        break
            
            if max_lba >= _param.gLUCapacity[lun]:
                _max_lba = _param.gLUCapacity[lun]

            if min_size != max_size:
                data_len = random.randint(min_size, max_size)
            else:
                data_len = min_size

            if data_len >= _param.gLUCapacity[lun]:
                data_len = _param.gLUCapacity[lun]

            if (_max_lba - data_len) < min_lba:
                start_lba = min_lba
            else:
                start_lba = random.randint(min_lba, _max_lba - data_len)

            if (start_lba + data_len) > _param.gLUCapacity[lun]:
                start_lba = _param.gLUCapacity[lun] - data_len

            unmap = ExecuteCMD.Unmap()
            unmap.assign(lun=lun, lba=start_lba, length=data_len)
            ExecuteCMD.enqueue(unmap)

        ExecuteCMD.send(clear_on_success=False, timeout=api.UniformTimeout(val=unmap.param.l50_timeout//1000, unit=api.TimeResolution.ms))
        for cmd in ExecuteCMD._cmd_list:
            save_write_info_by_cmd(cmd, write_record)   
        ExecuteCMD.clear()     

            
def sequential_write(lun: int, start_lba: int, total_size: int, chunk_size: int, fua:int, need_compare: bool, 
                     compare_method: int, write_record: List[List[WriteRecordNode]]) -> None:
    _log.info("function - sequential_write()")
    
    _param = shared.param
        
    if (lun > _param.gMaxNumberLU-1):
        raise PATTERN_ASSERT_UFS_WRONG_PARAMETER_LUN_CHECK_ERROR
    lba = start_lba           
    datalen = total_size

    while datalen > 0:
        chunk_size = min(chunk_size, datalen)

        write10 = ExecuteCMD.Write10()
        write10.assign(lun=lun, lba=lba, length=chunk_size, fua=fua)
        write10.set_option(pattern_mode=CmdParamPatternMode.HW_FIX)

        datalen -= chunk_size
        lba += chunk_size
        ExecuteCMD.enqueue(write10)
        
    ExecuteCMD.send(clear_on_success=False, timeout=api.UniformTimeout(val=write10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
    for cmd in ExecuteCMD._cmd_list:
        save_write_info_by_cmd(cmd, write_record)
    ExecuteCMD.clear()
    if (need_compare):
        read_compare(write_record, compare_method)