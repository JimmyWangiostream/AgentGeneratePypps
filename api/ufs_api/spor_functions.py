
import random
from typing import List, cast
from Script.lib.sdk_lib.user.exception import DLL_POWER_CYCLE
from Script.api import shared
import Script.api.cmd_seq as ExecuteCMD
from Script.api.cmd_seq.protocols import IsCmdUpiuEntry
from Script.api.exception import PATTERN_ASSERT_STUCK_WHILE_TIMEOUT, PATTERN_ASSERT_UFS_WRONG_PARAMETER_CMD_CNT_CHECK_ERROR, PATTERN_ASSERT_UFS_WRONG_PARAMETER_LBA_SIZE_CHECK_ERROR, PATTERN_ASSERT_UFS_WRONG_PARAMETER_LUN_CHECK_ERROR
from Script.api.ufs_api.defines import CmdParamPatternMode, CompareMethod
from Script.api.ufs_api.upiu import structs
from Script.api.util.write_record.functions import find_record_to_gen_data_crc, gen_data_buffer_for_crc32, save_write_info, save_write_info_by_cmd
from Script.api.util.write_record.structs import WriteRecordNode

from Script.api.ufs_api.debug_cmd.dcmd7 import *

_log = shared.logger
_sdk = shared.sdk

def random_write_spor(cmd_count: int, min_lun: int, max_lun: int, min_lba: int, max_lba: int, min_size: int, max_size: int, need_compare: bool, 
                  compare_method: int, write_record: List[List[WriteRecordNode]]) -> None:
    _log.info("function - random_write()")
    
    _param = shared.param
        
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

            write10 = ExecuteCMD.Write10()
            write10.assign(lun=lun, lba=start_lba, length=data_len, fua=0)

            ExecuteCMD.enqueue(write10)

        dcmd7_arg = api.set_dcmd7_arg()
        dcmd7_arg.activate = api.Dcmd7Activate.EN
        dcmd7_arg.detect_type = api.Dcmd7DetectType.BUSY_TIME_DETECT
        dcmd7_arg.reset_type = api.Dcmd7ResetType.HW_RESET        
        dcmd7_arg.detect_time = 10

        # dcmd7_arg.gap_time = 500
        # dcmd7_arg.response_detect_count = 600
        # dcmd7_arg.response_detect_delay_time = 700

        api.set_debug_cmd7(dcmd7_arg, 0)

        try:
            ExecuteCMD.send()
        except DLL_POWER_CYCLE as e:
            _sdk.clear_done_queue(api.HostDoneQueueType.ALL_DONE_QUEUE_ERR_HANDLE, 0)

        dcmd7_arg.activate = api.Dcmd7Activate.DIS
        api.set_debug_cmd7(dcmd7_arg, 0)

        dcmd7_rsp = api.get_debug_cmd7()
        
        if dcmd7_rsp.status == api.Dcmd7Status.PASS:
            if dcmd7_rsp.interrupt_status == api.Dcmd7InterruptStatus.SUCCESS:
                _log.info("SPOR Interrupt Success, SOPR Occur!")
            else:
                _log.info("SPOR Interrupt Fail!")

        if (need_compare):
            pass
         