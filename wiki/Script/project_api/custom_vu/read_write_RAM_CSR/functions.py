import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, push_data_in_vcmd
from Script.project_api.custom_vu.read_write_RAM_CSR.structs import micron_vu_4027, micron_vu_C0F0
from Script.api.cmd_seq.response import CommandResponse

_log = shared.logger

def issue_4027_read_SRAM_CSR_data(start_address:int, count_of_byte:int = 4, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4027()
    vu.b0_opcode.value = 0x27
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x80
    vu.d12_ramStartAddress.value = start_address
    vu.d16_byteCount.value = count_of_byte
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response

def push_4027_read_SRAM_CSR_data(cmd_idx:list[int], start_address:int, count_of_byte:int = 4) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4027()
    vu.b0_opcode.value = 0x27
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x80
    vu.d12_ramStartAddress.value = start_address
    vu.d16_byteCount.value = count_of_byte
    cmd_idx.append(push_data_in_vcmd(micron_vendor_cmd=vu))

def issue_C0F0_write_RAM_CSR(write_data:bytearray, start_address:int, count_of_byte:int = 4, keep_error:bool = True) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_C0F0()
    vu.b0_opcode.value = 0xF0
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 0x1000
    vu.d12_ramStartAddress.value = start_address
    vu.d16_byteCount.value = count_of_byte
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload= write_data, keep_error=keep_error)
    return response