import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd, micron_vu_40A0, micron_vu_D089
from Script.project_api.functions import send_data_out_vcmd, send_data_in_vcmd, send_no_data_vcmd
from Script.project_api.get_fw_vu.structs import GetFwVersion
from Script.project_api.set_get_temperature.structs import GetNandTemperature, SetNandTemperature
from Script.api.cmd_seq.response import CommandResponse
from Script.api import dumpfile, cmd_seq as ExecuteCMD
import struct

_log = shared.logger



def issue_40A0_get_device_safe_mode_state(keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40A0()
    vu.b0_opcode.value = 0xA0
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, payload

def issue_D089_set_safe_mode(setting_mode:int,keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D089()
    vu.b0_opcode.value = 0x89
    vu.b1_func.value = 0xD0
    vu.b12_set_mode.value = setting_mode
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response

