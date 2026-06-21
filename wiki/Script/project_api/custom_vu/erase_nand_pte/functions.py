import inspect
from typing import cast, List, Dict

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd, micron_vu_40F6, micron_vu_40F5
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.nand_trim_vu.structs import *
from Script.api.exception import *
from Script.api.util.functions import dumpfile

_log = shared.logger

def issue_40F6_to_erase_in_direct_nand_mode(die : int, plane: int, start_blk:int, end_blk:int, slc_enable:int = 0,psa_trim_enable:int = 0) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40F6()
    vu.b0_opcode.value = 0xF6
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.l12_die.value = die
    vu.l16_plane.value = plane
    vu.l16_start_blk.value = start_blk
    vu.l20_end_blk.value = end_blk

    dumpfile("get_40F6_vu.bin", vu.payload)

    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu)
    return response, payload

def issue_40F5_to_PTE_Recovery(sub_opcode : int, logical_vb: int) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40F5()
    vu.b0_opcode.value = 0xF5
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.sub_opcode.value = sub_opcode
    vu.logical_vb.value = logical_vb

    dumpfile("issue_40F5_to_PTE_Recovery.bin", vu.payload)

    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu)
    return response, payload