import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.project_api.custom_vu.efus_vu.structs import *
from Script.api.cmd_seq.response import CommandResponse


_log = shared.logger



def issue_D0F4_to_set_eFuse(eFuse_addr:int, eFuse_value:int, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D0F4()
    vu.b0_opcode.value = 0xF4
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0x1000 
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.eFuse_addr.value = eFuse_addr
    vu.eFuse_value.value = eFuse_value
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response

def issue_40F4_to_get_eFus() -> VU_40F4_struct:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xF4
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096 
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)  #don't care
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu)
    return VU_40F4_struct(payload)
