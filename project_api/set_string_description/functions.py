import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd, micron_vu_D088
from Script.project_api.functions import send_data_out_vcmd, send_data_in_vcmd, send_no_data_vcmd
from Script.project_api.get_fw_vu.structs import GetFwVersion
from Script.project_api.set_string_description.structs import SerialNumberString, ProductNameString, ASICId, ReadUid, HealthReportForNandId, AllManufacturingSetting, WWYY, ManufactureDate, GetTemperature
from Script.api.cmd_seq.response import CommandResponse
from Script.api import dumpfile, cmd_seq as ExecuteCMD


_log = shared.logger



def issue_D088_enable_disable_auto_standby(if_auto_standby_enable:int, keep_error:bool = False) -> CommandResponse:
    vu = micron_vu_D088()
    vu.b0_opcode.value = 0x88
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.b12_if_auto_standby_enable.value = if_auto_standby_enable
    dumpfile("enable_disable_auto_standby.bin", vu.payload)
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response

def issue_C04A_to_set_serial_number_string(SerialNumberString:SerialNumberString, keep_error:bool = False) -> CommandResponse:
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x4A
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    payload = bytearray(128)
    payload = bytearray(SerialNumberString.payload)
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload= payload, keep_error=keep_error)
    return response


def issue_C04B_to_set_serial_product_string(ProductNameString:ProductNameString, keep_error:bool = False) -> CommandResponse:
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x4B
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 0x20
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    payload = bytearray(32)
    payload = bytearray(ProductNameString.payload)
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload= payload, keep_error=keep_error)
    return response

def issue_C04F_to_set_wwyy(WWYY:WWYY, keep_error:bool = False) -> CommandResponse:
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x4F
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    payload = bytearray(128)
    payload = bytearray(WWYY.payload)
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload= payload, keep_error=keep_error)
    return response

def issue_C04E_to_set_manufacture_date(ManufactureDate:ManufactureDate, keep_error:bool = False) -> CommandResponse:
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x4E
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    payload = bytearray(128)
    payload = bytearray(ManufactureDate.payload)
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload= payload, keep_error=keep_error)
    return response


def issue_40B3_to_get_asic_id(keep_error:bool = False) -> tuple[CommandResponse, ASICId]:
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xB3
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    ascid = ASICId(payload[0:4096])
    return response, ascid

def issue_4040_to_get_all_manufacturing_setting(keep_error:bool = False) -> tuple[CommandResponse, AllManufacturingSetting]:
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x40
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    ascid = AllManufacturingSetting(payload[0:4096])
    return response, ascid


def issue_4061_to_get_uid(keep_error:bool = False) -> tuple[CommandResponse, ReadUid]:
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x61
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    uid = ReadUid(payload[0:4096])
    return response, uid

def get_health_report(keep_error:bool = False) -> tuple[bytearray, HealthReportForNandId]:
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xBB
    vu.b1_func.value = 0x42
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    health_report = HealthReportForNandId(payload[0:4096])
    return payload, health_report

def get_smart_info(keep_error:bool = False) -> bytearray:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xFF
    vu.b1_func.value = 0x42
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return payload
