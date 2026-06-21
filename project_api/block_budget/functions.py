import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD
from Script.api.ufs_api.defines.enum_define import VendorCmdRuleCdb2, VendorCmd, VendorCmdRuleCdb3
import random
from Script.project_api.structs import micron_vendor_cmd, micron_vu_D0FB
from Script.project_api.functions import send_data_out_vcmd, send_data_in_vcmd, send_no_data_vcmd
from Script.project_api.get_fw_vu.structs import GetFwVersion
from Script.project_api.block_budget.structs import GetCSICSInfoDescription, GetBoundaryBlocksForHiddenTableStaticDynamicPool, VBCount
from Script.api.cmd_seq.response import CommandResponse
from Script.api import dumpfile, cmd_seq as ExecuteCMD


_log = shared.logger


def issue_4087_get_ics_cs_info_description(keep_error:bool = False) -> tuple[CommandResponse, GetCSICSInfoDescription]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x87
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    dumpfile("get_temp_vu.bin", vu.payload)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    get_temp = GetCSICSInfoDescription(payload[0:4096])
    return response, get_temp

def issue_4004_get_boundaryblocks_for_hiddentable_static_dynamicpool(keep_error:bool = False) -> tuple[CommandResponse, GetBoundaryBlocksForHiddenTableStaticDynamicPool]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x04
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    dumpfile("set_temperature.bin", vu.payload)
    response , payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    getpayload = GetBoundaryBlocksForHiddenTableStaticDynamicPool(payload)
    return response, getpayload

def get_block_read_count_table() -> bytearray:
    vuc = ExecuteCMD.VendorCmdRead() 
    vuc.assign(length=8192, cmd_index=VendorCmd.GET_BLOCK_READ_CNT)
    vuc.upiu.u16_cdb.b3_rsvd = VendorCmdRuleCdb3.CMD_OTHER
    cmd_index = ExecuteCMD.enqueue(vuc)
    ExecuteCMD.send(clear_on_success=False)
    response = ExecuteCMD.read_response(cmd_index)
    ExecuteCMD.clear()
    return response.data

def get_bad_block_erase_cnt_table() -> bytearray:
    vuc = ExecuteCMD.VendorCmdRead() 
    vuc.assign(length=4096, cmd_index=VendorCmd.GET_BADBLK_EEASECNT_TABLE)
    vuc.upiu.u16_cdb.b3_rsvd = VendorCmdRuleCdb3.CMD_ATTRIBUTE
    cmd_index = ExecuteCMD.enqueue(vuc)
    ExecuteCMD.send(clear_on_success=False)
    response = ExecuteCMD.read_response(cmd_index)
    ExecuteCMD.clear()
    return response.data



def issue_D0FB_set_fw_state_in_ram(option:int,keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D0FB()
    vu.b0_opcode.value = 0xFB
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d12_option.value = option
    dumpfile("issue_D0FB_set_fw_state_in_ram.bin", vu.payload)
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response    

