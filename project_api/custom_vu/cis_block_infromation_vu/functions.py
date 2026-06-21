import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.cis_block_infromation_vu.structs import VU_40B9_struct

_log = shared.logger

def issue_40B9_to_get_cis_block_Information() -> VU_40B9_struct:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xB9
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096 
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)  #don't care
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu)
    return VU_40B9_struct(payload[0:48])
