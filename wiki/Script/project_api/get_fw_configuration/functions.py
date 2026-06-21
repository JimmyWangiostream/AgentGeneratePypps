import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.project_api.get_fw_configuration.structs import GetFwConfiguration
from Script.project_api.vpct_vu import micron_vu_408A
from Script.api.cmd_seq.response import CommandResponse



_log = shared.logger

def issue_408A_to_get_fw_version(keep_error:bool = False) -> tuple[CommandResponse, bytearray, GetFwConfiguration]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    #vu = micron_vendor_cmd()
    vu = micron_vu_408A()
    vu.b0_opcode.value = 0x8A
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d8_split_pkg_index.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    fw_configuration = GetFwConfiguration(payload[0:128])
    return response, payload, fw_configuration

