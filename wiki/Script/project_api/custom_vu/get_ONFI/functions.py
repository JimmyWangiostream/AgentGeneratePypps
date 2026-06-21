import inspect
from typing import cast, List
from Script.api import shared, util, cmd_seq as ExecuteCMD
from Script.project_api.custom_vu.get_ONFI.structs import *

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.project_api.custom_vu.device_state_vu.structs import *
from Script.api.cmd_seq.response import CommandResponse


_log = shared.logger

def issue_4073_get_ONFI_speed(keep_error:bool = False) -> tuple[CommandResponse, ONFI_frequency]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x73
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    _ONFI_frequency = ONFI_frequency(payload)
    return response, _ONFI_frequency
