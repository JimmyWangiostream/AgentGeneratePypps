import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_out_vcmd, send_data_in_vcmd
from Script.project_api.custom_vu.used_mapping_used_size_device_free_size_vu import micron_vu_40A8
from Script.api.cmd_seq.response import CommandResponse
from Script.api.exception import *
from Script.lib.sdk_lib.user.exception import DLL_RESPONSE_ERROR
from Script.api.ufs_api.defines import UPIUResponse
from Script.api.cmd_seq.response import CommandResponse, get_cmd_response_byte_str

_log = shared.logger

def issue_40A8_to_get_used_mapping_used_size_device_free_size(mode:int, lun:int) -> int:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40A8()
    vu.b0_opcode.value = 0xA8
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x4000
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)  #don't care
    vu.mode.value = mode
    response, payload = send_data_in_vcmd(vu)
    value = int.from_bytes(payload[0:4],'little')
    return value