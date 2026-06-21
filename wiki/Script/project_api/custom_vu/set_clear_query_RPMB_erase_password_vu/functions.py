import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.structs import *
from Script.project_api.custom_vu.set_clear_query_RPMB_erase_password_vu.structs import *
from Script.project_api.structs import micron_vu_4047
from typing import Tuple, Union
from Script.project_api.functions import print_object_info_ai



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
def issue_4047_to_set_clear_query_RPMB_erase_password(password : int, para0:int) -> tuple[CommandResponse,  Union[setRPMBpassword, clearRPMBpassword, queryRPMBpassword]]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4047()
    vu.b0_opcode.value = 0x47
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.l12_password.value = password
    vu.b20_wpara0.value = para0
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    print_array_tohex(payload,68, 4)
    if para0 == 0:
        print_object_info_ai(setRPMBpassword(payload))
        return response, setRPMBpassword(payload)
    elif para0 == 1:
        print_object_info_ai(clearRPMBpassword(payload))
        return response, clearRPMBpassword(payload)
    else:
        print_object_info_ai(queryRPMBpassword(payload))
        return response, queryRPMBpassword(payload)
