import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.read_scan_vu.structs import *
from Script.project_api.read_scan_vu.define import *
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd

_log = shared.logger

def issue_40BF_to_get_read_scan_info(sub_Operation:ReadScanVBInfoSubOperation, input_data:int, keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40BF()
    vu.b0_opcode.value = 0xBF
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x4000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.sub_Operation.value = sub_Operation
    vu.input_data.value = input_data
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, payload

def set_Enable_Disable_Read_Scan(enable:int) -> int:
    response, payload = issue_40BF_to_get_read_scan_info(sub_Operation=ReadScanVBInfoSubOperation.Enable_Disable_Read_Scan, input_data=enable)
    status = int.from_bytes(payload[0:4], 'little')
    return status

def get_Normal_VB_Scan_Pages(RSTriggerBy:RSTriggerBy) -> List[int]:
    response, payload = issue_40BF_to_get_read_scan_info(sub_Operation=ReadScanVBInfoSubOperation.Get_Normal_VB_Scan_Pages, input_data=RSTriggerBy)
    Normal_VB_Page_List_Length = int.from_bytes(payload[0:4], 'little')
    PageList:List[int] = []
    for i in range(Normal_VB_Page_List_Length):
        PageList.append(int.from_bytes(payload[4+i*4:4+(i+1)*4], 'little'))
    return PageList

def get_APL_flag_of_VB(log_VB:int) -> int:
    response, payload = issue_40BF_to_get_read_scan_info(sub_Operation=ReadScanVBInfoSubOperation.Get_APL_flag_of_VB, input_data=log_VB)
    APL_flag = int.from_bytes(payload[0:4], 'little')
    return APL_flag

def get_setting_refresh_stop_page() -> int:
    response, payload = issue_40BF_to_get_read_scan_info(sub_Operation=ReadScanVBInfoSubOperation.set_refresh_stop_page, input_data=0)
    value = int.from_bytes(payload[0:4], 'little')
    return value

def get_gc_read_scan_released_scan_pageline() -> List[int]:
    response, payload = issue_40BF_to_get_read_scan_info(sub_Operation=ReadScanVBInfoSubOperation.get_gc_read_scan_released_scan_or_UECC_pageline, input_data=1)
    gc_read_scan_released_scan_pageline = int.from_bytes(payload[0:4], 'little')
    WLs:List[int] = []
    for i in range(gc_read_scan_released_scan_pageline):
        WLs.append(int.from_bytes(payload[4+i*4:4+(i+1)*4], 'little'))
    return WLs

def get_Normal_lock_list_VBs_number() -> List[int]:
    response, payload = issue_40BF_to_get_read_scan_info(sub_Operation=ReadScanVBInfoSubOperation.get_Normal_lock_list_VBs_number, input_data=1)
    lock_list_tatal_VB_count = int.from_bytes(payload[0:4], 'little')
    VB_number:List[int] = []
    for i in range(lock_list_tatal_VB_count):
        VB_number.append(int.from_bytes(payload[4+i*4:4+(i+1)*4], 'little'))
    return VB_number

def check_if_source_VB_could_be_recovered_by_GC_source_recovery(VB:int) -> int:
    response, payload = issue_40BF_to_get_read_scan_info(sub_Operation=ReadScanVBInfoSubOperation.check_if_source_VB_could_be_recovered_by_GC_source_recovery, input_data=VB)
    status = int.from_bytes(payload[0:4], 'little')
    return status

def check_if_current_VB_scan_in_progress_completed(VB:int) -> int:
    response, payload = issue_40BF_to_get_read_scan_info(sub_Operation=ReadScanVBInfoSubOperation.check_if_current_VB_scan_in_progress_completed, input_data=VB)
    status = int.from_bytes(payload[0:4], 'little')
    return status

