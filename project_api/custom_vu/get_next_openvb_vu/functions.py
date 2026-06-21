import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.structs import *
from Script.project_api.custom_vu.get_next_openvb_vu.structs import *
from Script.project_api.structs import micron_vu_D078, micron_vu_D079, micron_vu_C08C, micron_vu_4022, micron_vu_4023, micron_vu_40DC



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
def issue_40DC_to_get_next_open_vb_information(openvbtype : int) -> tuple[CommandResponse, NextOpenVBInformation]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40DC()
    vu.b0_opcode.value = 0xDC
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d12_openvbtype.value = openvbtype
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    
    print_array_tohex(payload,68, 4)
    return response, NextOpenVBInformation(payload)
