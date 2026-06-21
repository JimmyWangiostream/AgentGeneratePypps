import inspect
from typing import cast, List

from Script.api import shared, util, cmd_seq as ExecuteCMD

import random
from Script.project_api.custom_vu.secded_vu.structs import *
from Script.project_api.custom_vu.secded_vu.define import *
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.api.util.functions import dumpfile

_log = shared.logger

def issue_40BD_to_inject_SER_SECDED_event(opCode: ErrorInjection, keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40BD()
    vu.b0_opcode.value = 0xBD
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.opCode.value=opCode
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, payload
