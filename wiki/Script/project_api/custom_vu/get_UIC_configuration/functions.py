import inspect
from typing import cast, List

from Script.api import shared, util, cmd_seq as ExecuteCMD
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd
from Script.project_api.custom_vu.device_state_vu.structs import *
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.get_UIC_configuration.structs import *


_log = shared.logger

def issue_4049_get_UIC_configuration() -> UICconfigdata:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x49
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu)
    return UICconfigdata(buf)
