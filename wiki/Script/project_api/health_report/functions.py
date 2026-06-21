import inspect
from typing import cast, List
from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd, micron_vu_40FE
from Script.project_api.functions import push_data_in_vcmd, send_data_out_vcmd, send_data_in_vcmd, send_no_data_vcmd
from Script.project_api.get_fw_vu.structs import GetFwVersion
from Script.project_api.set_get_temperature.structs import GetNandTemperature, SetNandTemperature
from Script.api.cmd_seq.response import CommandResponse
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.project_api.health_report.structs import *
import struct

_log = shared.logger



def issue_40FE_to_read_enhanced_health_report(keep_error:bool = False) -> tuple[CommandResponse, ReadEnhanceHealthReport]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40FE()
    vu.b0_opcode.value = 0xFE
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    health_report = ReadEnhanceHealthReport(payload)
    return response, health_report

def push_40FE_to_read_enhanced_health_report(cmd_idx:list[int]) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40FE()
    vu.b0_opcode.value = 0xFE
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    cmd_idx.append(push_data_in_vcmd(micron_vendor_cmd=vu))