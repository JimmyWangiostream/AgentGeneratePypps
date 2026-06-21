import inspect
from typing import cast, List
from Script.api import shared, cmd_seq as ExecuteCMD
import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_no_data_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.api.util.functions import dumpfile
from Script.project_api.custom_vu.VDET_vu.structs import *


_log = shared.logger

def issue_D074_to_disable_VDET(keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x74
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response

def issue_40B8_to_get_VDET_information(keep_error:bool = False) -> tuple[CommandResponse, VDET_Information]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xB8
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x10
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    _VDET_Information = VDET_Information(payload)
    dumpfile('40B8.bin', payload)
    return response, _VDET_Information
