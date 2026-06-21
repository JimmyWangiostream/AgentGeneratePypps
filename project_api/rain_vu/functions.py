import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.rain_vu.structs import *
from Script.project_api.rain_vu.define import *
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd



_log = shared.logger

def issue_4055_to_get_rain_parity(rain_user:int, group:int, keep_error:bool = False) -> tuple[CommandResponse, List[bytearray], bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4055()
    vu.b0_opcode.value = 0x55
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x5000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.rain_user.value = rain_user
    vu.group.value = group
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    fw_spare_list:List[bytearray] = []
    parity = bytearray(0x4000)
    offset = 0
    for idx in range(4):
        fw_spare = payload[offset:offset+16]
        offset += len(fw_spare)
        fw_spare_list.append(fw_spare)
        parity[idx*0x1000:(idx+1)*0x1000] = payload[offset:offset+0x1000]
        offset+=0x1000
    return response, fw_spare_list, parity

def issue_4054_to_get_rain_info(currentCE:int, keep_error:bool = False) -> tuple[CommandResponse, RainInfo]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x54
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, RainInfo(currentCE, payload)

def issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain:int, Host_Permanent_Rain:int, Host_Simple_Rain:int, host_full_block_protection_rain:int, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D08B()
    vu.b0_opcode.value = 0x8B
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    if Table_and_S_CHK_rain & RainVB.S_CHK:
        vu.Table_and_S_CHK_rain_enable_disable.enable_S_CHK_rain_calculation_and_write.value = 1
        if Table_and_S_CHK_rain & RainVB.S_CHK_recovery:
            vu.Table_and_S_CHK_rain_enable_disable.enable_S_CHK_rain_usage_for_table_recovery.value = 1
    if Table_and_S_CHK_rain & RainVB.Table:
        vu.Table_and_S_CHK_rain_enable_disable.enable_table_rain_calculation_and_write.value = 1
        if Table_and_S_CHK_rain & RainVB.Table_recovery:
            vu.Table_and_S_CHK_rain_enable_disable.enable_table_rain_usage_for_table_recovery.value = 1
    if Host_Permanent_Rain & RainVB.EM1:
        vu.Host_Permanent_Rain_Enable_Disable.rain_write_into_last_pages_of_Host_EM1_SLC_L2_block.value = 1
        if Host_Permanent_Rain & RainVB.EM1_recovery:
            vu.Host_Permanent_Rain_Enable_Disable.rain_usage_for_data_recovery_into_Host_EM1_SLC_L2_block.value = 1
    if Host_Permanent_Rain & RainVB.TLC:
        vu.Host_Permanent_Rain_Enable_Disable.rain_write_into_last_pages_of_Host_Normal_TLC_L2_block.value = 1
        if Host_Permanent_Rain & RainVB.TLC_recovery:
            vu.Host_Permanent_Rain_Enable_Disable.rain_usage_for_data_recovery_into_Host_Normal_TLC_L2_block.value = 1
    if Host_Permanent_Rain & RainVB.WB:
        vu.Host_Permanent_Rain_Enable_Disable.rain_write_into_last_pages_of_Write_Booster_L2_block.value = 1
        if Host_Permanent_Rain & RainVB.WB_recovery:
            vu.Host_Permanent_Rain_Enable_Disable.rain_usage_for_data_recovery_into_Write_Booster_L2_block.value = 1
    if Host_Simple_Rain & RainVB.EM1:
        vu.Host_Simple_Rain_Enable_Disable.parity_calculation_into_SRAM_for_Host_EM1_SLC_L2_block.value = 1
        if Host_Simple_Rain & RainVB.EM1_recovery:
            vu.Host_Simple_Rain_Enable_Disable.parity_usage_for_data_recovery_into_Host_EM1_SLC_L2_block.value = 1
    if Host_Simple_Rain & RainVB.TLC:
        vu.Host_Simple_Rain_Enable_Disable.parity_calculation_into_SRAM_for_Host_Normal_TLC_L2_block.value = 1
        if Host_Simple_Rain & RainVB.TLC_recovery:
            vu.Host_Simple_Rain_Enable_Disable.parity_usage_for_data_recovery_into_Host_Normal_TLC_L2_block.value = 1
    if Host_Simple_Rain & RainVB.WB:
        vu.Host_Simple_Rain_Enable_Disable.parity_calculation_into_SRAM_for_Write_Booster_L2_block.value = 1
        if Host_Simple_Rain & RainVB.WB_recovery:
            vu.Host_Simple_Rain_Enable_Disable.parity_usage_for_data_recovery_into_Write_Booster_L2_block.value = 1
    if host_full_block_protection_rain & RainVB.EM1:
        vu.host_full_block_protection_rain.rain_write_for_Host_EM1_SLC_L2_open_block.value = 1
        if host_full_block_protection_rain & RainVB.EM1_recovery:
            vu.host_full_block_protection_rain.rain_usage_for_data_recovery_for_Host_EM1_SLC_L2_open_block.value = 1
    if host_full_block_protection_rain & RainVB.TLC:
        vu.host_full_block_protection_rain.rain_write_for_Host_Normal_TLC_L2_open_block.value = 1
        if host_full_block_protection_rain & RainVB.TLC_recovery:
            vu.host_full_block_protection_rain.rain_usage_for_data_recovery_for_Normal_TLC_L2_open_block.value = 1
    if host_full_block_protection_rain & RainVB.WB:
        vu.host_full_block_protection_rain.rain_write_for_Write_Booster_L2_open_block.value = 1
        if host_full_block_protection_rain & RainVB.WB_recovery:
            vu.host_full_block_protection_rain.rain_usage_for_data_recovery_for_Write_Booster_L2_open_block.value = 1
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response