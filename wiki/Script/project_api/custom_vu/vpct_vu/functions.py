import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.project_api.custom_vu.vpct_vu import micron_vu_40C0
from Script.api.cmd_seq.response import CommandResponse


_log = shared.logger

def issue_40C0_to_get_VPCT_description(vbNum:int, tableVBDataCheck:int = 0, keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40C0()
    vu.b0_opcode.value = 0xC0
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x2000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.vbNum.value = vbNum
    vu.tableVBDataCheck.value = tableVBDataCheck
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, payload
