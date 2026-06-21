import inspect
from Script.api import shared
import random
from Script.api.util.functions import dumpfile
from Script.project_api.custom_vu.get_single_open_block.structs import micron_vu_40C6, SubVBInfo
from Script.project_api.functions import send_data_in_vcmd
from Script.api.cmd_seq.response import CommandResponse
from enum import IntEnum

_log = shared.logger

def issue_40C6_get_single_open_block(open_block_type:int, absolute_plane_identifier:int, dump_payload:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40C6()
    vu.b0_opcode.value = 0xC6
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d12_open_block_type.value = open_block_type
    vu.d16_absolute_plane_identifier.value = absolute_plane_identifier
    if dump_payload:
        dumpfile(filename="VU_40C6_INPUT_PARAM", data=vu.payload.copy())
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu)
    return response
class open_block_type_list(IntEnum):
    DM_NORMAL_HOST_VB = 0
    DM_NORMAL_DEFRAG_VB = 1
    PTE = 4
    Refresh_VB = 6
    DM_RPMB_HOST_VB = 7
    RPMB_DEFRAG = 8
    DM_NORMAL_SHARE_VB_1 = 9
    DM_NORMAL_WB_VB_0 = 10
    DM_RAIN_PARITY_VB = 11
    TMP_RAIN = 13
    Drive_Log = 14
    Pointer_to_Index_block = 15
    BBT = 16
    DM_NORMAL_SHARE_VB_0 = 17
    DM_EM1_DEFRAG_VB = 18
    List = 19
    LOG = 20
    Index = 21
    MAIN_ISP = 22
    TMP_ISP = 23
def get_TEMP_ISP_physical_block_information() -> SubVBInfo:
    response = issue_40C6_get_single_open_block(open_block_type = open_block_type_list.TMP_ISP, absolute_plane_identifier= 0, dump_payload= True)                   
    return SubVBInfo(response.data)
def get_MAIN_ISP_physical_block_information() -> SubVBInfo:
    response = issue_40C6_get_single_open_block(open_block_type = open_block_type_list.MAIN_ISP, absolute_plane_identifier= 0, dump_payload= True)                   
    return SubVBInfo(response.data)
def get_PT_physical_block_information() -> SubVBInfo:
    response = issue_40C6_get_single_open_block(open_block_type = open_block_type_list.Pointer_to_Index_block, absolute_plane_identifier= 0, dump_payload= True)                   
    return SubVBInfo(response.data)
def get_BBT2_physical_block_information() -> SubVBInfo:
    response = issue_40C6_get_single_open_block(open_block_type = open_block_type_list.BBT, absolute_plane_identifier= 0, dump_payload= True)                   
    return SubVBInfo(response.data)