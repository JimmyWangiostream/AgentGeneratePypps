import inspect
from typing import cast, List
from Script.api import shared, cmd_seq as ExecuteCMD
import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_no_data_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.api.util.functions import dumpfile
from Script.project_api.custom_vu.ffu_vu.structs import *


_log = shared.logger

def issue_4077_to_report_FFU_patch_count(keep_error:bool = False) -> FFU_patch_count:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4077()
    vu.b0_opcode.value = 0x77
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return FFU_patch_count(buf)