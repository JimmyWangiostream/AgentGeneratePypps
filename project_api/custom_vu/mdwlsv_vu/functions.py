import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.open_vb_information_vu.structs import *
from Script.project_api.structs import micron_vu_D078, micron_vu_D079, micron_vu_C08C, micron_vu_4022, micron_vu_4023



_log = shared.logger
def issue_C08C_to_EnDis_MDWLSV(value : int) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_C08C()
    vu.b0_opcode.value = 0x8C
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.b12_isMDWLSV_Disable.value = value
    payload = bytearray(4096)
    
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload= payload)
    return response

def issue_4029_to_get_MDWLSV_offset_information() -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x29
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    return response, payload
