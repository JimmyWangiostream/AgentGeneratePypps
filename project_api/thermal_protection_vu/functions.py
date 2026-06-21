import inspect
from typing import cast, List

from Script.api import shared, dumpfile, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.thermal_protection_vu.structs import *
from Script.project_api.thermal_protection_vu.define import *
from Script.project_api.functions import send_data_out_vcmd, send_data_in_vcmd, send_no_data_vcmd
from Script.api.cmd_seq.response import CommandResponse

_log = shared.logger


def issue_40FA_read_thermal_stuck_threshold(keep_error:bool = False) -> tuple[CommandResponse, ReadThermalStuckThreshold]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xFA
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, ReadThermalStuckThreshold(payload)

def issue_D0F1_write_thermal_stuck_threshold(SetThreshold:WriteThermalStuckThreshold, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D0F1()
    vu.b0_opcode.value = 0xF1
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    
    vu.threshold_count.value = SetThreshold.threshold_count.value
    vu.low_thermal_protection_threshold.value = SetThreshold.low_thermal_protection_threshold.value
    vu.high_thermal_protection_threshold.value = SetThreshold.high_thermal_protection_threshold.value

    dumpfile("write_TP_threshold.bin", vu.payload)
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response

def issue_D0F3_disable_thermal_stuck(enable:ThermalProtectionType, mode:HardThermalProtectionType, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D0F3()
    vu.b0_opcode.value = 0xF3
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    
    vu.thermal_protection_type.value = enable
    vu.hard_thermal_protection_type.value = mode

    dumpfile("disable_TP.bin", vu.payload)
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response
