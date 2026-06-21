import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD
from Script.project_api.custom_vu.get_info_about_TLC_defrag_operation_vu import VU_40C2_struct
import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse


_log = shared.logger

def issue_40C2_to_get_info_about_TLC_defrag_operation() -> VU_40C2_struct:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xC2
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)  #can this that big?
    #vu.b44_vu_length.value = 12
    
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu)
    return VU_40C2_struct(payload[0:176])