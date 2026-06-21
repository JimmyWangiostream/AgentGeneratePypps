import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_no_data_vcmd
from Script.project_api.custom_vu.invalid_table_cache_vu import micron_vu_D08C
from Script.api.cmd_seq.response import CommandResponse


_log = shared.logger

def issue_D08C_to_invalid_table_cache(rainEnable:int, keep_error:bool = False) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D08C()
    vu.b0_opcode.value = 0x8C
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.rainEnable.value = rainEnable
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return 
