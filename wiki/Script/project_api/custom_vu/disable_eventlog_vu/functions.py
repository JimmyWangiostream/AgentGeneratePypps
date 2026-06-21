import inspect
import time
from Script.api import shared
import random
from Script.project_api.custom_vu.read_log.structs import *
from Script.project_api.functions import send_no_data_vcmd
from Script.api.cmd_seq.response import CommandResponse
from typing import List

_log = shared.logger

def issue_D08F_to_disable_some_event_log(eventlog:List[int]) -> None: 
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x8F
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 4096 #don't care
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)  #don't care
    for i, logid in enumerate(eventlog):
        vu.payload[12+i*2] = logid & 0xFF
        vu.payload[12+i*2 + 1] = (logid >> 8) & 0xFF
    send_no_data_vcmd(micron_vendor_cmd=vu)
    return 