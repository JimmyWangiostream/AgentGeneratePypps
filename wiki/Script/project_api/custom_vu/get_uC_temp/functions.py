import inspect
from typing import cast, List

from Script.api import shared, util, cmd_seq as ExecuteCMD

import random
from Script.api.util.functions import dumpfile
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, push_data_in_vcmd, send_no_data_vcmd
from Script.project_api.custom_vu.device_state_vu.structs import *
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.get_uC_temp.structs import micron_vu_D011

_log = shared.logger

def issue_40FD_get_uC_temp() -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xFD
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x8
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu)
    return response

def push_40FD_get_uC_temp(cmd_idx:list[int]) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xFD
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x8
    cmd_idx.append(push_data_in_vcmd(micron_vendor_cmd=vu))

def issue_D011_clear_ssr_temp_history() -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D011()
    vu.b0_opcode.value = 0x11
    vu.b1_func.value = 0xD0
    response = send_no_data_vcmd(micron_vendor_cmd=vu)
    return response    

def issue_40FD_get_uC_temp_value() -> float:
    response = issue_40FD_get_uC_temp()
    sign_bit = (response.data[4] & 0x04) >> 2
    value_bits = response.data[4] & 0x03
    dumpfile('40FD_get_nand_temp',response.data)
    VU_temp = -(int.from_bytes([response.data[3], value_bits], byteorder='little')) if sign_bit == 1 else int.from_bytes([response.data[3], value_bits], byteorder='little')
    VU_temp = VU_temp * 0.25
    return VU_temp