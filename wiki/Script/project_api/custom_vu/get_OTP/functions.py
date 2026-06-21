import inspect
from Script.api import shared
import random
from Script.project_api.functions import send_data_in_vcmd
from Script.project_api.custom_vu.get_OTP import micron_vu_40BC
from Script.api.cmd_seq.response import CommandResponse


_log = shared.logger

def issue_40BC_get_OTP(OTP_page_index:int) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40BC()
    vu.b0_opcode.value = 0xBC
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.b12_bIndex.value = OTP_page_index
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu)
    return response
