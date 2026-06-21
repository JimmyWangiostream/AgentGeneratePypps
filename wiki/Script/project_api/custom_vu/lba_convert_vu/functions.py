import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.project_api.custom_vu.lba_convert_vu.structs import \
    micron_vu_4051, \
    micron_vu_4052, \
    micron_vu_40D4, \
    micron_vu_40C9, \
    ftl_lba, Logical_VB, \
    physical_address_info, logical_address_info
from Script.api.cmd_seq.response import CommandResponse
from Script.pattern.pattern_logger import logger

_log = shared.logger

def issue_4051_to_get_physical_address(luID: int, lba: int, keep_error:bool = False) -> tuple[CommandResponse, physical_address_info]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore

    vu = micron_vu_4051()
    vu.b0_opcode.value = 0x51
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.luID.value = luID
    vu.lba.value =  lba
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    logger.print_buffer(payload[:84])
    _physical_address_info = physical_address_info(payload[0:len(physical_address_info().payload)])
    return response, _physical_address_info

def issue_4052_to_get_logical_address(die: int, plane: int, block:int, page:int, vp: int, keep_error:bool = False) -> tuple[CommandResponse, logical_address_info]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4052()
    vu.b0_opcode.value = 0x52
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.didId.value = die
    vu.planeId.value = plane
    vu.logBlockId.value = block
    vu.pageId.value = page
    vu.virtualPageId.value = vp
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    _logical_address_info = logical_address_info(payload)
    return response, _logical_address_info

def issue_40D4_to_get_FTL_LBA(lunID: int, lba:int, keep_error: bool = False) -> tuple[CommandResponse, ftl_lba]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40D4()
    vu.b0_opcode.value = 0xD4
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.lunId.value = lunID
    vu.hostLba.value = lba
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    _lba = ftl_lba(payload)

    return response, _lba

def issue_40C9_to_get_logical_vb(physical_block: int, plane:int, keep_error:bool = False) -> tuple[CommandResponse, Logical_VB]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40C9()
    vu.b0_opcode.value = 0xC9
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.phyBlock.value = physical_block
    vu.planeId.value = plane
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    _logical_vb = Logical_VB(payload[0:len(Logical_VB().payload)])
    return response, _logical_vb
