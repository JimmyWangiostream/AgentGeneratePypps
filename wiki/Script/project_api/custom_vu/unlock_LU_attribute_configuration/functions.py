import inspect
from typing import cast, List

from Script.api import shared, util, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.project_api.custom_vu.device_state_vu.structs import *
from Script.api.cmd_seq.response import CommandResponse


_log = shared.logger

def issue_D085_unlock_LU_attribute_configuration() -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x85
    vu.b1_func.value = 0xD0
    vu.d8_split_pkg_index.value = 0
    send_no_data_vcmd(micron_vendor_cmd=vu)
    pass