import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_no_data_vcmd
from Script.project_api.custom_vu.set_slc_block_mode_vu import micron_vu_D098
from Script.api.cmd_seq.response import CommandResponse
from Script.api.exception import *
from Script.lib.sdk_lib.user.exception import DLL_RESPONSE_ERROR
from Script.api.ufs_api.defines import UPIUResponse
from Script.api.cmd_seq.response import CommandResponse

_log = shared.logger


def issue_D098_to_set_slc_block_mode(mode:int) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D098()
    vu.b0_opcode.value = 0x98
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0 
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)  #don't care
    vu.VuDynamicBlkMode.value = mode
    send_no_data_vcmd(vu)
    return