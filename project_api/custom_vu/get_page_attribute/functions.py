import inspect
from Script.api import shared
import random
from Script.project_api.functions import send_data_in_vcmd
from Script.project_api.custom_vu.get_page_attribute.structs import micron_vu_4010
from Script.api.cmd_seq.response import CommandResponse

_log = shared.logger

def issue_4010_get_page_attribute(page_index:int, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4010()
    vu.b0_opcode.value = 0x10
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d12_page_index.value = page_index
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response
