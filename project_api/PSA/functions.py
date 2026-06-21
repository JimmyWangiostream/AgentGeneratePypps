import inspect
from Script.api import shared
import random
from Script.project_api.PSA.structs import *
from Script.project_api.functions import send_data_in_vcmd, push_data_in_vcmd
from Script.project_api.structs import micron_vendor_cmd

from Script.api.cmd_seq.response import CommandResponse

_log = shared.logger

def issue_405C_get_PSA_post_reflow_progress() -> PSAPostReflowProgress:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x5C
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu)
    return PSAPostReflowProgress(buf)

def push_405C_get_PSA_post_reflow_progress(cmd_idx:list[int]) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x5C
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    cmd_idx.append(push_data_in_vcmd(micron_vendor_cmd=vu))

def issue_4050_check_PSA_buffer_size() -> PSABufferSize:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x50
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu)
    return PSABufferSize(buf)

def push_4050_check_PSA_buffer_size(cmd_idx:list[int]) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x50
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    cmd_idx.append(push_data_in_vcmd(micron_vendor_cmd=vu))

def issue_404F_get_PSA_migration_state() -> PSAMigrationState:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x4F
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu)
    return PSAMigrationState(buf)

def push_404F_get_PSA_migration_state(cmd_idx:list[int]) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x4F
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    cmd_idx.append(push_data_in_vcmd(micron_vendor_cmd=vu))