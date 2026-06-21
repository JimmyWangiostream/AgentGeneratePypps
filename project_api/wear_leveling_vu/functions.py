import inspect
from typing import cast, List

from Script.api import shared, dumpfile, cmd_seq as ExecuteCMD

import random
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.wear_leveling_vu.define import *
from Script.project_api.wear_leveling_vu.structs import *

_log = shared.logger

def issue_C072_to_set_static_wear_leveling_EC_gap_threshold(gEC_for_Static_pool:int, 
                                                            gEC_for_dynamic_pool:int, 
                                                            gEC_for_static_ICS_pool:int, 
                                                            gEC_of_Static_pool_for_open:int, 
                                                            gEC_of_dynamic_pool_for_open:int, 
                                                            gEC_gap_delta_TH1_static:int, 
                                                            gEC_gap_delta_TH1_dynamic:int, 
                                                            gEC_gap_delta_TH1_ICS:int, 
                                                            gEC_gap_delta_TH2_static:int, 
                                                            gEC_gap_delta_TH2_dynamic:int, 
                                                            gEC_gap_delta_TH2_ICS:int, 
                                                            keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_C072()
    vu.b0_opcode.value = 0x72
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    data_payload = bytearray(0x1000)
    data_payload[0:4] = gEC_for_Static_pool.to_bytes(4, 'little')
    data_payload[4:8] = gEC_for_dynamic_pool.to_bytes(4, 'little')
    data_payload[8:12] = gEC_for_static_ICS_pool.to_bytes(4, 'little')
    data_payload[12:16] = gEC_of_Static_pool_for_open.to_bytes(4, 'little')
    data_payload[16:20] = gEC_of_dynamic_pool_for_open.to_bytes(4, 'little')
    data_payload[20:24] = gEC_gap_delta_TH1_static.to_bytes(4, 'little')
    data_payload[24:28] = gEC_gap_delta_TH1_dynamic.to_bytes(4, 'little')
    data_payload[28:32] = gEC_gap_delta_TH1_ICS.to_bytes(4, 'little')
    data_payload[32:36] = gEC_gap_delta_TH2_static.to_bytes(4, 'little')
    data_payload[36:40] = gEC_gap_delta_TH2_dynamic.to_bytes(4, 'little')
    data_payload[40:44] = gEC_gap_delta_TH2_ICS.to_bytes(4, 'little')
    response= send_data_out_vcmd(micron_vendor_cmd=vu, data_payload = data_payload, keep_error=keep_error)
    return response

def issue_4098_to_get_wear_leveling_information(keep_error:bool = False) -> tuple[CommandResponse, WearLevelingInformation]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4098()
    vu.b0_opcode.value = 0x98
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x3000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.bParameter0.value = 0x0
    vu.bParameter1.value = 0x0
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, WearLevelingInformation(payload)

def issue_4098_to_enable_disable_wear_leveling(enable:bool, keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4098()
    vu.b0_opcode.value = 0x98
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x3000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.bParameter0.value = 0x1
    vu.bParameter1.value = int(enable)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, payload
