import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.project_api.custom_vu.device_state_vu.structs import *
from Script.api.cmd_seq.response import CommandResponse


_log = shared.logger

def set_device_state(Device_state:int, only_in_ram:bool = True, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    if only_in_ram:
        vu = micron_vu_D0FC()
        vu.b0_opcode.value = 0xFC
        vu.b1_func.value = 0xD0
        vu.bValue.value = Device_state
    else:
        vu = micron_vu_D0E2()
        vu.b0_opcode.value = 0xE2
        vu.b1_func.value = 0xD0
        vu.bDeviceState.value = Device_state
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response

def get_FW_states_in_RAM(keep_error:bool = False) -> tuple[CommandResponse, int]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40FC()
    vu.b0_opcode.value = 0xFC
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    Device_state = int(payload[0])
    return response, Device_state

def issue_40E2_to_get_device_state(keep_error:bool = False) -> tuple[CommandResponse, int, int]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40E2()
    vu.b0_opcode.value = 0xE2
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    Device_state = int(payload[0])
    NumOfRemainingStateChanges = int(payload[1])
    return response, Device_state, NumOfRemainingStateChanges