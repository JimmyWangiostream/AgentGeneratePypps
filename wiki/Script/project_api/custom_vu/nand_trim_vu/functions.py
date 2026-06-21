import inspect
from typing import cast, List, Dict

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.nand_trim_vu.structs import *
from Script.api.exception import *
from Script.api.util.functions import dumpfile

_log = shared.logger

def issue_4084_to_get_NAND_trim(target_addr:List[int], keep_error:bool = False) -> tuple[CommandResponse, get_trim_struct]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4084()
    vu.b0_opcode.value = 0x84
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.GetTrimItemCnt.value = len(target_addr)
    if len(target_addr):
        for item in range(len(target_addr)):
            vu.die[item].value = 0
            vu.TA_MSB[item].value = target_addr[item] >> 8
            vu.TA_LSB[item].value = target_addr[item] & 0xFF
    else:
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, get_trim_struct(payload)

def issue_C084_to_set_NAND_trim(set_dict:Dict[int, int], keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x84
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    set_trim = set_trim_struct(bytearray(4096))
    set_trim.ItemCount.value = len(set_dict)
    for idx, (addr, value) in enumerate(set_dict.items()):
        set_trim.ItemIndexValue[idx].value = idx
        set_trim.TA_MSB[idx].value = addr >> 8
        set_trim.TA_LSB[idx].value = addr & 0xFF
        set_trim.SetTrimRegisterValue[idx].value = value
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload= bytearray(set_trim.payload), keep_error=keep_error)
    return response