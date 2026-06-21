import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.structs import micron_vu_40C7, micron_vu_40D6, micron_vu_40F6_1, micron_vu_40F7, micron_vu_40F8
from Script.project_api.custom_vu.bad_block_information_vu.structs import *


_log = shared.logger

def issue_D048_to_set_FW_BBT_and_system_block_EC(FW_CIS0:int = 0xFFFFFFFF, FW_CIS1:int = 0xFFFFFFFF, BBM_Table_EC:int = 0xFFFFFFFF, ISP_Block_EC:int = 0xFFFFFFFF, Pointer_Block_EC:int = 0xFFFFFFFF, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D048()
    vu.b0_opcode.value = 0x48
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.FW_CIS0.value = FW_CIS0
    vu.FW_CIS1.value = FW_CIS1
    vu.BBM_Table_EC.value = BBM_Table_EC
    vu.ISP_Block_EC.value = ISP_Block_EC
    vu.Pointer_Block_EC.value = Pointer_Block_EC
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response


def issue_405E_to_get_bad_block_information(keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x5E
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, payload


def issue_40C7_to_get_bad_block_info(pb: int, plane: int) -> tuple[CommandResponse, BB_info]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40C7()
    vu.b0_opcode.value = 0xC7
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d12_pb.value = pb
    vu.d16_plane.value = plane
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    return response, BB_info(payload)


def issue_40C8_to_get_bad_blocks_count() -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xC8
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    return response, payload


def issue_40D6_to_get_predicted_next_n_replacement_block(ce: int, plane: int, next_n: int, pool_type: int, is_CIS: int, pf_on_open_data: int) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40D6()
    vu.b0_opcode.value = 0xD6
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d12_ce.value = ce
    vu.d16_plane.value = plane
    vu.d20_next_n.value = next_n
    vu.d24_pool_type.value = pool_type
    vu.d28_is_cis.value = is_CIS
    vu.d32_pf_on_open_data.value = pf_on_open_data

    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    return response, payload


def issue_40F6_to_erase_in_direct_nand_mode_1(die: int, plane: int, start_block: int, end_block: int, slc_enable: int) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40F6_1()
    vu.b0_opcode.value = 0xF6
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d12_die.value = die
    vu.d16_plane.value = plane
    vu.d20_start_block.value = start_block
    vu.d24_end_block.value = end_block
    vu.d28_slc_enable.value = slc_enable
    vu.d32_psa_trim_enable.value = 0
    vu.d36_reserved.value = 0
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    return response, payload


def issue_40F7_to_write_raw_data_in_direct_nand_mode(die: int, plane: int, start_block: int, end_block: int, start_page: int, end_page: int, slc_enable: int, pattern: int) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40F7()
    vu.b0_opcode.value = 0xF7
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d12_die.value = die
    vu.d16_plane.value = plane
    vu.d20_start_block.value = start_block
    vu.d24_end_block.value = end_block
    vu.d28_start_page.value = start_page
    vu.d32_end_page.value = end_page
    vu.d36_slc_enable.value = slc_enable
    vu.d40_pattern.value = pattern
    vu.d44_psa_enable.value = 0
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    return response, payload


def issue_40F8_to_read_in_direct_nand_mode(die: int, plane: int, start_block: int, end_block: int, start_page: int, end_page: int, slc_enable: int) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40F8()
    vu.b0_opcode.value = 0xF8
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0xC120
    vu.w12_die.value = die
    vu.w14_psa_trim.value = 0
    vu.d16_plane.value = plane
    vu.d20_start_block.value = start_block
    vu.d24_end_block.value = end_block
    vu.d28_start_page.value = start_page
    vu.d32_end_page.value = end_page
    vu.d36_data_byte_number.value = 16384
    vu.d40_slc_enable.value = slc_enable
    vu.b44_read_stress.value = 1
    vu.b45_block_type.value = 0
    vu.b46_seedecbit_enable.value = 0
    vu.d47_reserved.value = 0
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    return response, payload
