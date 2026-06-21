import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.structs import *
from Script.project_api.custom_vu.do_power_loss_analysing_vu.structs import *
from Script.project_api.structs import micron_vu_409D
from typing import Tuple, Union



_log = shared.logger
# def print_array_tohex(databuff : bytearray, showlen :int, bytesperline: int) -> None:
#     len = databuff.__len__()
#     if len >= showlen:
#         len = showlen
#     for index in range(0,len,bytesperline):
#         if(index + bytesperline < len):
#             tmpdata = databuff[index: index+bytesperline]
#             print(tmpdata.hex(' ',1) )
#         else:            
#             tmpdata = databuff[index: len]            
#             print(tmpdata.hex(' ',1) )
#     return
def issue_409D_to_do_power_loss_analysing(opcode:int, die: int, plane: int, block: int, slcmode: int, startpage: int, stoppage: int, param_idx: int =0, param_val: int = 0) -> tuple[CommandResponse,  Union[APL_Blank_Check,APL_Powerloss_Check,APL_LWP_Check,APL_Get_Parameter]]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_409D()
    vu.b0_opcode.value = 0x9D
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    #print_array_tohex(payload,68, 4)
    vu.d12_die.value = die
    vu.d16_plane.value = plane
    vu.d20_block.value = block
    vu.b24_slcmode.value = slcmode
    vu.w25_startpage.value = startpage
    vu.w27_stoppage.value = stoppage
    vu.b29_opcode.value = opcode
    if opcode == 1 or opcode == 2:
        vu.b30_parameter_index.value = param_idx
    if opcode == 1:
        vu.w30_parameter_value.value = param_val
    #response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, specific_read_buffer_len=4096, keep_error=False)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    if opcode == 3:
        return response, APL_Blank_Check(payload)
    elif opcode == 4:
        return response, APL_Powerloss_Check(payload)
    elif opcode == 0:
        return response, APL_LWP_Check(payload)
    elif opcode == 2:
        return response, APL_Get_Parameter(payload)
    else:
        return response, APL_Get_Parameter(payload)

