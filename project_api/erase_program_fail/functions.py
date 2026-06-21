import inspect

from Script.api import shared

import random
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.structs import micron_vendor_cmd, micron_vu_4013, micron_vu_C012
from Script.project_api.erase_program_fail.structs import PhysicalAddressInformation, BEFailStatus

_log = shared.logger


def issue_4013_to_get_BE_fail_status(force_clear: int = 1) -> tuple[CommandResponse, BEFailStatus]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4013()
    vu.b0_opcode.value = 0x13
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d8_split_pkg_index.value = 0x00
    vu.d12_force_clear.value = force_clear
    vu.d16_reserved.value = 0x00
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    return response, BEFailStatus(payload)


def issue_C012_to_create_program_erase_fail(PhysicalAddressInformation:PhysicalAddressInformation, fail_type: int, block_info_list_count: int = 1, skip_uecc: int = 1) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_C012()
    vu.b0_opcode.value = 0x12
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 112
    vu.d12_fail_type.value = fail_type
    vu.d16_block_info_list_count.value = block_info_list_count
    vu.d20_fail_times.value = 1
    vu.d24_enable_safe_mode_for_bb.value = 1
    vu.d28_skip_uecc.value = skip_uecc
    vu.d32_reserved.value = 0x00
    payload = bytearray(112)
    payload = bytearray(PhysicalAddressInformation.payload)
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload=payload)
    return response


def issue_C0BC_to_write_BB_information(payload: bytearray) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xBC
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 0x4000
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload=payload)

    return response
