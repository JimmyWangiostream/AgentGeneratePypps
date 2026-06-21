import inspect
from typing import cast, List
from Script.api import shared, cmd_seq as ExecuteCMD
import random
from Script.project_api.structs import micron_vendor_cmd, micron_vu_D0B0
from Script.project_api.functions import send_no_data_vcmd
from Script.api.cmd_seq.response import CommandResponse

_log = shared.logger

def issue_D0B0_to_switch_abort_task_assert(enable:int) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D0B0()
    vu.b0_opcode.value = 0xB0
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0x4000
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)  #don't care
    vu.l12_enable_disable.value = enable
    response = send_no_data_vcmd(micron_vendor_cmd=vu)
    return 