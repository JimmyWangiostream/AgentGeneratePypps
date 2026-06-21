import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.media_scan_vu.structs import *

_log = shared.logger
def issue_4026_to_get_BEC_histograms_information(reset_enable:int, keep_error:bool = False) -> tuple[CommandResponse, get_bec_histogram_struct]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4026()
    vu.b0_opcode.value = 0x26
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = 0
    vu.d8_split_pkg_index.value = 0
    vu.d12_reset_enable.value = reset_enable
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, get_bec_histogram_struct(payload)

def issue_4028_to_get_media_scan_without_dm(param:micron_vu_4028_param, keep_error:bool = False) -> tuple[CommandResponse, get_media_scan_status_struct]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4028()
    vu.b0_opcode.value = 0x28
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = 0
    vu.d8_split_pkg_index.value = 0
    vu.d16_die.value = param.d16_die
    vu.d20_plane.value = param.d20_plane
    vu.d24_block.value = param.d24_block
    vu.d28_page.value = param.d28_page
    vu.b40_slc_mode.value = param.b40_slc_mode
    vu.b41_bfea_bin.value = param.b41_bfea_bin
    vu.b42_page_attr.value = param.b42_page_attr
    vu.b43_is_blank_page.value = param.b43_is_blank_page
    vu.b44_is_partial_block.value = param.b44_is_partial_block
    vu.b45_is_em1_vb.value = param.b45_is_em1_vb
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, get_media_scan_status_struct(payload)

def issue_402C_to_get_media_scan_vhc_informance(keep_error:bool = False) -> tuple[CommandResponse, get_media_scan_status_struct]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x2C
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d8_split_pkg_index.value = 0
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, get_media_scan_status_struct(payload)

def issue_402F_to_get_media_scan_thresholds(param:micron_vu_402F_param_with_data, keep_error:bool = False) -> tuple[CommandResponse, get_media_scan_thresholds_struct]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_402F()
    vu.b0_opcode.value = 0x2F
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = 0
    vu.d8_split_pkg_index.value = 0
    vu.b12_is_partial_block.value = param.b12_is_partial_block
    vu.w13_pe_cycle.value = param.w13_pe_cycle
    vu.b15_is_em1.value = param.b15_is_em1
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, get_media_scan_thresholds_struct(payload)

def issue_40CF_to_get_media_scan_parameters(keep_error:bool = False) -> tuple[CommandResponse, get_media_scan_param_struct]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xCF
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)
    vu.d8_split_pkg_index.value = 0
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, get_media_scan_param_struct(payload)

def issue_C085_to_set_media_scan_parameters(param:micron_vu_C085_param_with_data, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x85
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)
    set_param = set_media_scan_param_struct(bytearray(16))
    set_param.last_full_scan_group_spend_time.value = param.last_full_scan_group_spend_time
    set_param.set_open_blk_freq_in_secs.value = param.set_open_blk_freq_in_secs
    set_param.set_media_scan_bin_low.value = param.set_media_scan_bin_low
    set_param.set_media_scan_bin_high.value = param.set_media_scan_bin_high
    set_param.set_scale_factor_reduce_scan_time.value = param.set_scale_factor_reduce_scan_time
    set_param.last_scan_spend_time.value = param.last_scan_spend_time
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload= bytearray(set_param.payload), keep_error=keep_error)
    return response

def issue_C08B_to_enable_diable_media_scan(enable_media_scan: bool = False, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_C08B()
    vu.b0_opcode.value = 0x8B
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)
    vu.d8_split_pkg_index.value = 0
    vu.b12_media_scan_enable.value = enable_media_scan
    dummy_data = bytearray(4096)
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload=dummy_data, keep_error=keep_error)
    return response

def issue_D08E_to_change_media_scan_thresholds(param:micron_vu_D08E_param, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D08E()
    vu.b0_opcode.value = 0x8E
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0
    vu.d4_random_stamp.value = 0
    vu.d8_split_pkg_index.value = 0
    vu.b12_th_cnt.value = param.b12_th_cnt
    vu.w14_bec_valley_th_slc.value = param.w14_bec_valley_th_slc
    vu.w16_valley_center_ecth_slc.value = param.w16_valley_center_ecth_slc
    vu.w18_valley_diffec_th_slc.value = param.w18_valley_diffec_th_slc
    vu.b20_valley_ofs_th_slc.value = param.b20_valley_ofs_th_slc
    vu.b21_xtemp_th_delta_slc.value = param.b21_xtemp_th_delta_slc
    vu.b22_is_partial_block.value = param.b22_is_partial_block
    vu.b23_is_em1.value = param.b23_is_em1
    vu.w24_pe_cycle.value = param.w24_pe_cycle
    data_buf = bytearray(0)
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload=data_buf, keep_error=keep_error)
    return response