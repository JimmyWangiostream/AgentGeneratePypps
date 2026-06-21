import inspect
from typing import cast, List

from Script.api import shared, util, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd, micron_vu_4099
from Script.project_api.custom_vu.get_VB_list_info.structs import GetBlkList, MmesgEventLogBlockInformation
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.project_api.custom_vu.device_state_vu.structs import *
from Script.api.cmd_seq.response import CommandResponse
from Script.api.util.functions import dumpfile

_log = shared.logger

def issue_406D_get_VB_list_info() -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x6D
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu)
    return response

def issue_406D_get_VB_list_info_return_list() -> List[List[int]]:
    resp = issue_406D_get_VB_list_info()
    retlist:List[List[int]] = []
    index = 0    
    while index < len(resp.data):
        count = int.from_bytes(resp.data[index:index+2], byteorder='little')
        index += 2
        
        info_list:List[int] = []
        for _ in range(count):
            info = int.from_bytes(resp.data[index:index+2], byteorder='little')
            info_list.append(info)
            index += 2
        retlist.append(info_list)
    return retlist

def issue_4099_to_get_ftl_blk_list(param0: int) -> tuple[CommandResponse, GetBlkList]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4099()
    vu.b0_opcode.value = 0x99
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.l12_param0.value=param0
    dumpfile("get_4099_vu.bin", vu.payload)
    
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu)

    get_blk_list = GetBlkList(payload)
    return response, get_blk_list


def issue_4099_to_get_ftl_blk_list_mmmesg(param0: int) -> tuple[CommandResponse, MmesgEventLogBlockInformation]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4099()
    vu.b0_opcode.value = 0x99
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.l12_param0.value=param0
    dumpfile("get_4099_vu.bin", vu.payload)
    
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu)

    get_blk_list = MmesgEventLogBlockInformation(payload)
    return response, get_blk_list
