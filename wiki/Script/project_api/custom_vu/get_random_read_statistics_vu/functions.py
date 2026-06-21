import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.structs import *
from Script.project_api.custom_vu.get_random_read_statistics_vu.structs import *
from typing import Tuple, Union



_log = shared.logger
def print_array_tohex(databuff : bytearray, showlen :int, bytesperline: int) -> None:
    len = databuff.__len__()
    if len >= showlen:
        len = showlen
    for index in range(0,len,bytesperline):
        if(index + bytesperline < len):
            tmpdata = databuff[index: index+bytesperline]
            print(tmpdata.hex(' ',1) )
        else:            
            tmpdata = databuff[index: len]            
            print(tmpdata.hex(' ',1) )
    return
def issue_409F_to_get_random_read_statistics() -> tuple[CommandResponse,  random_read_statistics_info]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x9F
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    print_array_tohex(payload,68, 4)
    return response, random_read_statistics_info(payload)
