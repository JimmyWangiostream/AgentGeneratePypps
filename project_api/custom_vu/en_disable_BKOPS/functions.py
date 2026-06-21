import inspect
from Script.api import shared
from Script.project_api.functions import send_no_data_vcmd
from Script.project_api.custom_vu.en_disable_BKOPS.structs import micron_vu_D0FD

_log = shared.logger

def issue_D0FD_en_disable_BKOPS(bValue:int) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D0FD()
    vu.b0_opcode.value = 0xFD
    vu.b1_func.value = 0xD0
    vu.b12_bValue.value = bValue
    send_no_data_vcmd(micron_vendor_cmd=vu)
    pass

def issue_D0FD_disable_all_the_background_operations() -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D0FD()
    vu.b0_opcode.value = 0xFD
    vu.b1_func.value = 0xD0
    vu.b12_bValue.value = 0x00
    send_no_data_vcmd(micron_vendor_cmd=vu)
    pass


def issue_D0FD_enable_all_the_background_operations() -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D0FD()
    vu.b0_opcode.value = 0xFD
    vu.b1_func.value = 0xD0
    vu.b12_bValue.value = 0x01
    send_no_data_vcmd(micron_vendor_cmd=vu)
    pass

def issue_D0FD_disable_all_the_foreground_operations() -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D0FD()
    vu.b0_opcode.value = 0xFD
    vu.b1_func.value = 0xD0
    vu.b12_bValue.value = 0x02
    send_no_data_vcmd(micron_vendor_cmd=vu)
    pass

def issue_D0FD_enable_all_the_foreground_operations() -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D0FD()
    vu.b0_opcode.value = 0xFD
    vu.b1_func.value = 0xD0
    vu.b12_bValue.value = 0x03
    send_no_data_vcmd(micron_vendor_cmd=vu)
    pass

def issue_D0FD_disable_BG_trim() -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D0FD()
    vu.b0_opcode.value = 0xFD
    vu.b1_func.value = 0xD0
    vu.b12_bValue.value = 0x04
    send_no_data_vcmd(micron_vendor_cmd=vu)
    pass

def issue_D0FD_enable_BG_trim() -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D0FD()
    vu.b0_opcode.value = 0xFD
    vu.b1_func.value = 0xD0
    vu.b12_bValue.value = 0x05
    send_no_data_vcmd(micron_vendor_cmd=vu)
    pass