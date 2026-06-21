import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd, micron_vu_D08A
from Script.project_api.functions import send_data_out_vcmd, send_data_in_vcmd, send_no_data_vcmd
from Script.project_api.get_fw_vu.structs import GetFwVersion
from Script.project_api.set_get_temperature.structs import GetNandTemperature, SetNandTemperature
from Script.api.cmd_seq.response import CommandResponse
from Script.api import dumpfile, cmd_seq as ExecuteCMD
import struct

_log = shared.logger


def issue_4021_get_nand_temperature(keep_error:bool = False) -> tuple[CommandResponse, GetNandTemperature]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x21
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    dumpfile("get_temp_vu.bin", vu.payload)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    get_temp = GetNandTemperature(payload[0:4096])
    return response, get_temp

def issue_D08A_set_vu_temperature(SetNandTemperature:SetNandTemperature, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D08A()
    vu.b0_opcode.value = 0x8A
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.b12_enable_set_vu_temp.value = SetNandTemperature.bEnableSetVuTemp.value
    vu.b13_enable_ffu_set_vu_temp.value = SetNandTemperature.bEnableFFUSetVuTemp.value
    vu.w14_UC_TERMAL_SENSOR_1.value = SetNandTemperature.UC_TERMAL_SENSOR_1.value
    vu.w16_UC_TERMAL_SENSOR_2.value = SetNandTemperature.UC_TERMAL_SENSOR_2.value
    vu.w18_UC_TERMAL_SENSOR_3.value = SetNandTemperature.UC_TERMAL_SENSOR_3.value
    vu.w20_NAND_TEMPERATURE_DIE_0.value = SetNandTemperature.NAND_TEMPERATURE_DIE_0.value
    vu.w22_NAND_TEMPERATURE_DIE_1.value = SetNandTemperature.NAND_TEMPERATURE_DIE_1.value
    vu.w24_NAND_TEMPERATURE_DIE_2.value = SetNandTemperature.NAND_TEMPERATURE_DIE_2.value
    vu.w26_NAND_TEMPERATURE_DIE_3.value = SetNandTemperature.NAND_TEMPERATURE_DIE_3.value
    vu.w28_NAND_TEMPERATURE_DIE_4.value = SetNandTemperature.NAND_TEMPERATURE_DIE_4.value
    vu.w30_NAND_TEMPERATURE_DIE_5.value = SetNandTemperature.NAND_TEMPERATURE_DIE_5.value
    vu.w32_NAND_TEMPERATURE_DIE_6.value = SetNandTemperature.NAND_TEMPERATURE_DIE_6.value
    vu.w34_NAND_TEMPERATURE_DIE_7.value = SetNandTemperature.NAND_TEMPERATURE_DIE_7.value
    vu.b36_FFU_VU_TEMPER.value = SetNandTemperature.FFU_VU_TEMPER.value
    vu.b37_Use_Delayed_Fake_Temperatures.value = SetNandTemperature.Use_Delayed_fake_tmeperatures.value
    dumpfile("set_temperature.bin", vu.payload)
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response


def issue_40FD_get_uC_temp_123(keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xFD
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x8
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    dumpfile("get_uctemp_vu.bin", vu.payload)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, payload

def issue_40FD_get_uC_temp() -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    data_len = 44
    buffer_data = bytearray(data_len)
    buffer_data[0] = 0xFD   # Opcode
    buffer_data[1] = 0x40   # Function
    buffer_data[3] = 0x08
    cmd_w_buf = ExecuteCMD.WriteBuffer()
    cmd_w_buf.assign(lun=0, mode=0xE1, buffer_id=0, buffer_offset=0, length=data_len, vendor=True)
    cmd_w_buf.set_option(wait_queue_empty=True)
    cmd_w_buf.data = buffer_data
    ExecuteCMD.enqueue(cmd_w_buf)
    ExecuteCMD.send()

    read_buffer = ExecuteCMD.ReadBuffer()
    read_buffer.assign(lun=0, mode=0xC1, buffer_id=0, buffer_offset=0, length=0x08, vendor=True)
    read_buffer.set_option(wait_queue_empty=True)
    cmd_index = ExecuteCMD.enqueue(read_buffer)
    ExecuteCMD.send(timeout=None, clear_on_success=False)
    response = ExecuteCMD.read_response(cmd_index)
    return response
