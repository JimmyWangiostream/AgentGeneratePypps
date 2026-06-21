import inspect
from typing import cast, List

from Script.api import shared, dumpfile, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.erase_read_count_etc_tables_cis_tables_vu.define import *
from Script.project_api.custom_vu.erase_read_count_etc_tables_cis_tables_vu.structs import *

_log = shared.logger

def issue_4097_to_get_erase_read_count_etc_tables_cis_tables(Parameter0:int, keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4097()
    vu.b0_opcode.value = 0x97
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.Parameter0.value = Parameter0
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    dumpfile('vu4097.bin', payload)
    return response, payload

def issue_C083_to_set_erase_read_count_parameter(Parameter0:int, VB_Num:int, RC_TH_Value:int, data_payload:bytearray, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_C083()
    vu.b0_opcode.value = 0x83
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.Parameter0.value = Parameter0
    vu.VB_Num.value = VB_Num
    vu.RC_TH_Value.value = RC_TH_Value
    response= send_data_out_vcmd(micron_vendor_cmd=vu, data_payload = data_payload, keep_error=keep_error)
    return response

def get_all_VB_erase_count() -> tuple[List[int], List[int], List[int]]:
    rsp, data_payload = issue_4097_to_get_erase_read_count_etc_tables_cis_tables(Parameter0=VU4097Paremeter.GET_EC_TABLE)
    erase_cnt_of_vb = []
    erase_cnt_for_hidden_physical_block = []
    physical_block_type = []
    for i in range(512+8):
        if i < 512:
            erase_cnt_of_vb.append(int.from_bytes(data_payload[4*i:4*(i+1)], 'little'))
        else:
            erase_cnt_for_hidden_physical_block.append(int.from_bytes(data_payload[4*i:4*(i+1)], 'little'))
    for i in range(8):
        physical_block_type.append(int.from_bytes(data_payload[2080+i:2080+i+1], 'little'))
    return erase_cnt_of_vb, erase_cnt_for_hidden_physical_block, physical_block_type

def get_all_VB_read_count() -> List[int]:
    rsp, data_payload = issue_4097_to_get_erase_read_count_etc_tables_cis_tables(Parameter0=VU4097Paremeter.GET_RC_TABLE)
    read_count_of_vb = []
    for i in range(512):
        read_count_of_vb.append(int.from_bytes(data_payload[4*i:4*(i+1)], 'little'))
    return read_count_of_vb

def get_VB_to_PB_mapping() -> List[int]:
    rsp, data_payload = issue_4097_to_get_erase_read_count_etc_tables_cis_tables(Parameter0=VU4097Paremeter.GET_L2P_VB_TABLE)
    physical_block_index_of_vb = []
    for i in range(512):
        physical_block_index_of_vb.append(int.from_bytes(data_payload[2*i:2*(i+1)], 'little'))
    return physical_block_index_of_vb

def get_FW_code_physical_address_information() -> FWCodePhysicalAddressInfomation:
    rsp, data_payload = issue_4097_to_get_erase_read_count_etc_tables_cis_tables(Parameter0=VU4097Paremeter.GET_CIS_VB_TABLE)
    return FWCodePhysicalAddressInfomation(data_payload)

# def get_system_sub_vb_versions() -> SystemSubVBVersions:
#     rsp, data_payload = issue_4097_to_get_erase_read_count_etc_tables_cis_tables(Parameter0=VU4097Paremeter.GET_SYSTEM_ALL_SUB_VB_VERSIONS)
#     return SystemSubVBVersions(data_payload)

def get_BBT_physical_block_information() -> BBTSubVBInfo:
    rsp, data_payload = issue_4097_to_get_erase_read_count_etc_tables_cis_tables(Parameter0=VU4097Paremeter.GET_BBT_SUB_VB_INFO)
    return BBTSubVBInfo(data_payload)

def get_all_VB_type() -> List[VBTypeInfo]:
    rsp, data_payload = issue_4097_to_get_erase_read_count_etc_tables_cis_tables(Parameter0=VU4097Paremeter.GET_EC_TABLE_RAW)
    all_vb_type = []
    total_super_vb = int.from_bytes(data_payload[0:4], 'little')
    for i in range(total_super_vb):
        all_vb_type.append(VBTypeInfo(data_payload, 4+4*i, 4+4*(i+1)-1))
    return all_vb_type

def get_ics_bad_block() -> ICSBadBlock:
    rsp, data_payload = issue_4097_to_get_erase_read_count_etc_tables_cis_tables(Parameter0=VU4097Paremeter.ICS_BAD_BLOCK)
    return ICSBadBlock(data_payload)


def get_supr_blocks() -> List[int]:
    rsp, data_payload = issue_4097_to_get_erase_read_count_etc_tables_cis_tables(Parameter0=VU4097Paremeter.RESERVED)
    output_list = []
    num_of_vb = int.from_bytes(data_payload[0 : 4], 'little')
    for i in range(num_of_vb):
        output_list.append(int.from_bytes(data_payload[4*(i+1):4*(i+1)+4]))
    return output_list

def set_all_VB_erase_count(data_payload:bytearray, set_in_ram:bool = False) -> CommandResponse:
    VB_Num = VUC083VB_Num.CHANGE_THE_EC_ONLY_IN_RAM if set_in_ram else VUC083VB_Num.FLUSH_THE_EC_CHANGE_IN_SYSTEM_TABLE
    rsp = issue_C083_to_set_erase_read_count_parameter(Parameter0=VUC083Paremeter.SET_EC_TABLE, VB_Num=VB_Num, RC_TH_Value=0, data_payload=data_payload)
    return rsp

def set_all_VB_read_count(data_payload:bytearray) -> CommandResponse:
    rsp = issue_C083_to_set_erase_read_count_parameter(Parameter0=VUC083Paremeter.SET_RC_TABLE, VB_Num=0, RC_TH_Value=0, data_payload=data_payload)
    return rsp

def set_specific_VB_read_count_threshold(VB_Num:int, RC_TH_Value:int) -> CommandResponse:
    data_payload = bytearray(4096)
    rsp = issue_C083_to_set_erase_read_count_parameter(Parameter0=VUC083Paremeter.SET_RC_THRESHOLD_VALUE, VB_Num=VB_Num, RC_TH_Value=RC_TH_Value, data_payload=data_payload)
    return rsp