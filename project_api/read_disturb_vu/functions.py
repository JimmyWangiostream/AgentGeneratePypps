import inspect
from typing import cast, List

from Script.api import shared, dumpfile, cmd_seq as ExecuteCMD

import random
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.read_disturb_vu.define import *
from Script.project_api.read_disturb_vu.structs import *
from Script.project_api.set_string_description.functions import get_smart_info

_log = shared.logger

def issue_40CC_to_trigger_Read_Disturb_scan(LogicalVB:int, keep_error:bool = False) -> tuple[CommandResponse, ReadDisturbTriggerInfo]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40CC()
    vu.b0_opcode.value = 0xCC
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.LogicalVB.value = LogicalVB
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, ReadDisturbTriggerInfo(payload)

def issue_40CB_to_get_total_Read_Count_and_Flush_RC_table_threshold(LogicalVB:int, keep_error:bool = False) -> tuple[CommandResponse, ReadDisturbRC]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40CB()
    vu.b0_opcode.value = 0xCB
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.LogicalVB.value = LogicalVB
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, ReadDisturbRC(payload)

def issue_40CA_to_get_get_Read_Count_threshold_table(keep_error:bool = False) -> tuple[CommandResponse, List[int]]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40CA()
    vu.b0_opcode.value = 0xCA
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    number_of_super_blocks = int.from_bytes(payload[0:4], 'little')
    RC_thresholds = []
    for i in range(number_of_super_blocks):
        RC_thresholds.append(int.from_bytes(payload[4+i*4:4+(i+1)*4], 'little'))
    return response, RC_thresholds

def issue_408C_to_get_EC_RC_threshold_table(wBlockType:int, keep_error:bool = False) -> tuple[CommandResponse, List[ReadThresholdSet]]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_408C()
    vu.b0_opcode.value = 0x8C
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.wBlockType.value = wBlockType
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    number_of_RC_sets = int.from_bytes(payload[0:4], 'little')
    Read_TH_sets = []
    for i in range(number_of_RC_sets):
        Read_TH_sets.append(ReadThresholdSet(payload, 4+i*8, 4+(i+1)*8))
    return response, Read_TH_sets

def get_read_disturb_counter() -> ReadDisturbSmartInfo:
    payload_get = get_smart_info()
    return ReadDisturbSmartInfo(payload_get)
