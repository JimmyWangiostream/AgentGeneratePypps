import inspect
from typing import cast, List, Generator, Tuple
from Script.api import shared, dumpfile, cmd_seq as ExecuteCMD
import random
from Script import api
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.project_api.mconfig_vu.structs import mConfig, pConfig
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.sticky_read.structs import micron_vu_4066, sticky_read_status

_log = shared.logger

def issue_4066_to_dis_en_sticky_read(isEnable:int, keep_error:bool = False)-> tuple[CommandResponse, int]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4066()
    vu.b0_opcode.value = 0x66
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option0.value = 0
    vu.option1.value = isEnable
    vu.die.value = 0
    vu.pageType.value = 0
    vu.isPSA.value = 0
    vu.readLast.value = 0
    vu.arc.value = 0
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    dumpfile('VU4066.bin', payload)
    _sticky_read_status = sticky_read_status(payload[0:len(sticky_read_status().payload)])
    return response, _sticky_read_status.stickyReadStatus.value

def issue_4066_force_current_read_last_as_sticky_read(die:int, pageType:int, isPSA:int, readLast:int, arc:int,  keep_error:bool = False)-> tuple[CommandResponse, sticky_read_status]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4066()
    vu.b0_opcode.value = 0x66
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option0.value = 2
    vu.option1.value = 0
    vu.die.value = die
    vu.pageType.value = pageType
    vu.isPSA.value = isPSA
    vu.readLast.value = readLast
    vu.arc.value = arc
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    dumpfile('VU4066.bin', payload)
    _sticky_read_status = sticky_read_status(payload[0:len(sticky_read_status().payload)])
    return response, _sticky_read_status

def issue_4066_get_sticky_read_status_and_offset(die:int, pagetype:int, isPSA:int, keep_error:bool = False) -> tuple[CommandResponse, sticky_read_status]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4066()
    vu.b0_opcode.value = 0x66
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option0.value = 1
    vu.option1.value = 0
    vu.die.value = die
    vu.pageType.value = pagetype
    vu.isPSA.value = isPSA
    vu.readLast.value = 0
    vu.arc.value = 0
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    dumpfile('VU4066.bin', payload)
    _sticky_read_status = sticky_read_status(payload[0:len(sticky_read_status().payload)])
    return response, _sticky_read_status