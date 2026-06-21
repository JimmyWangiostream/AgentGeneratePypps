import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD
from Script.project_api.custom_vu.get_params_of_ftl_status_vu.structs import VU_40C3_struct
import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse


_log = shared.logger

def issue_40C3_to_get_params_of_ftl_status() -> VU_40C3_struct:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xC3
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 6144
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)  
    #vu.b44_vu_length.value = 12
    
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu)
    return VU_40C3_struct(payload[0:6144])