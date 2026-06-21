import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.project_api.mconfig_vu.structs import *
from Script.api.cmd_seq.response import CommandResponse



_log = shared.logger

def issue_4056_to_get_mConfig_data(get_option:int, keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4056()
    vu.b0_opcode.value = 0x56
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option.value = get_option
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, payload

def issue_C056_to_set_mConfig_data(set_option:int, payload:bytearray, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_C056()
    vu.b0_opcode.value = 0x56
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option.value = set_option
    # payload = bytearray(4096)
    # payload[0:len(mConfig.payload)] = mConfig.payload
    # payload[1024:1024+len(pConfig.payload)] = pConfig.payload
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload= payload, keep_error=keep_error)
    return response


def get_mConfig_data(keep_error:bool = False) -> tuple[CommandResponse, mConfig]:
    rsp, payload = issue_4056_to_get_mConfig_data(get_option=0, keep_error=keep_error)
    mConfig_size = int.from_bytes(payload[0:4], 'little')
    payload = payload[4:4+mConfig_size]
    _mConfig = mConfig(payload, 0, mConfig_size-1)
    return rsp, _mConfig

def get_pConfig_data(keep_error:bool = False) -> tuple[CommandResponse, pConfig]:
    rsp, payload = issue_4056_to_get_mConfig_data(get_option=1, keep_error=keep_error)
    pConfig_size = int.from_bytes(payload[0:4], 'little')
    payload = payload[4:4+pConfig_size]
    _pConfig = pConfig(payload, 0, pConfig_size-1)
    return rsp, _pConfig

def get_HW_page_config_data(keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    rsp, payload = issue_4056_to_get_mConfig_data(get_option=2, keep_error=keep_error)
    return rsp, payload

def set_mConfig_data(mConfig:mConfig, keep_error:bool = False) -> CommandResponse:
    return issue_C056_to_set_mConfig_data(set_option=0, payload=bytearray(mConfig.payload), keep_error=keep_error)
    
def set_pConfig_data(pConfig:pConfig, keep_error:bool = False) -> CommandResponse:
    return issue_C056_to_set_mConfig_data(set_option=1, payload=bytearray(pConfig.payload), keep_error=keep_error)

def set_HW_page_config_data(data_payload:bytearray, keep_error:bool = False) -> CommandResponse:
    return issue_C056_to_set_mConfig_data(set_option=2, payload=data_payload, keep_error=keep_error)