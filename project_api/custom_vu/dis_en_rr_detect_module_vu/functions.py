import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.open_vb_information_vu.structs import *
from Script.project_api.structs import micron_vu_C0F4



_log = shared.logger
def issue_C0F4_to_EnDis_RR_detect(rrd_enable : int, fw_acces_ptn_en : int) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_C0F4()
    vu.b0_opcode.value = 0xF4
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.b12_rrd_enable.value = rrd_enable
    vu.b13_fw_access_pattern_enable.value = fw_acces_ptn_en
    vu.b14_die_balance_enable.value = 0
    payload = bytearray(4096)
    
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload= payload)
    return response