import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script import api
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.project_api.mconfig_vu.structs import mConfig, pConfig
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.structs import micron_vu_D078, micron_vu_D079, micron_vu_C08C, micron_vu_4022, micron_vu_4023, micron_vu_D0FE

from Script.project_api.custom_vu.mdwlsv_vu.structs import MDWLSV_format

_log = shared.logger

def issue_D078_to_set_RPMB_WriteCounter(write_counter:int, region:int) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D078()
    vu.b0_opcode.value = 0x78
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d12_writecounter.value = write_counter
    vu.d16_region.value = region
    send_no_data_vcmd(micron_vendor_cmd=vu)
    pass

def issue_D079_Clear_RPMB_Key(region:int) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D079()
    vu.b0_opcode.value = 0x79
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d12_region.value = region
    send_no_data_vcmd(micron_vendor_cmd=vu)
    pass

def issue_D083_clean_up_write_once() -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x83
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d8_split_pkg_index.value = 0
    send_no_data_vcmd(micron_vendor_cmd=vu)
    pass
    pass

def issue_4022_to_get_NAND_feature(die : int, feature: int) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4022()
    vu.b0_opcode.value = 0x22
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d12_ce.value = 0
    vu.d16_die.value = die
    vu.d20_feature_address.value = feature
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    return response, payload

def issue_4023_to_set_NAND_feature(die : int, feature: int, P1: int, P2: int, P3: int, P4: int) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4023()
    vu.b0_opcode.value = 0x23
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d12_ce.value = 0
    vu.d16_die.value = die
    vu.d20_feature_address.value = feature
    vu.d24_P1.value = P1
    vu.d28_P2.value = P2
    vu.d32_P3.value = P3
    vu.d36_P4.value = P4
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    return response, payload


def print_array_tohex(databuff : bytearray, showlen :int, bytesperline: int) -> None:
    len = databuff.__len__()
    if len >= showlen:
        len = showlen
    for index in range(0,len,bytesperline):
        if(index + bytesperline < len):
            tmpdata = databuff[index: index+bytesperline]
            print(tmpdata.hex(' ',1) )
        else:            
            tmpdata = databuff[index: len]            
            print(tmpdata.hex(' ',1) )
    return

def issue_40DB_to_get_bkops_status() -> int:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xDB
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)  
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu)
    return payload[0]


def issue_D0FE_set_FW_production_mode() -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D0FE()
    vu.b0_opcode.value = 0xFE
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = random.randint(0x1, 0xFFFF)
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    send_no_data_vcmd(micron_vendor_cmd=vu)    