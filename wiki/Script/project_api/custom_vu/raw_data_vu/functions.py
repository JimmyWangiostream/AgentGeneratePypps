import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.raw_data_vu.structs import *
from Script.project_api.functions import get_physical_layout

_log = shared.logger

def issue_4060_to_read_raw_data(Die:int, Plane:int, Block:int, Page:int, SLC_Enable:int, Ecc_Enable:int, Scrambler_Enable:int, REH_Enable:int = 1, ARC_disable:int = 0, PSA_Enable: int = 0, keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if Ecc_Enable:
        specific_read_buffer_len = 16452
    else:
        specific_read_buffer_len = 18352
    vu = micron_vu_4060()
    vu.b0_opcode.value = 0x60
    vu.b1_func.value = 0x40
    # vu.w2_transfer_length.value = specific_read_buffer_len
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.Die.value = Die
    vu.Plane.value = Plane
    vu.Block.value = Block
    vu.Page.value = Page
    vu.SLC_Enable.value = SLC_Enable
    vu.Ecc_Enable.value = Ecc_Enable
    vu.Scrambler_Enable.value = Scrambler_Enable
    vu.Data_Byte_Number.value = specific_read_buffer_len
    vu.REH_Enable.value = REH_Enable
    vu.ARC_disable.value = ARC_disable
    vu.psa_Enable.value = PSA_Enable
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, specific_read_buffer_len = specific_read_buffer_len, keep_error=keep_error)
    return response, payload

def issue_C060_to_write_raw_data(Ce:int, Plane:int, Block:int, Page:int, SLC_Enable:int, Ecc_Enable:int, datapayload:bytearray, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_C060()
    vu.b0_opcode.value = 0x60
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.Ce.value = Ce
    vu.Plane.value = Plane
    vu.Block.value = Block
    vu.Start_Page.value = Page
    if not SLC_Enable:
        pageline, WL_type, phy_WL, SubBlock, FlushGroup, TwoWLGroup, RainGoup = get_physical_layout(pageline=Page, block_type="TLC")
    if SLC_Enable:
        vu.End_Page.value = vu.Start_Page.value
        if Ecc_Enable:
            specific_read_buffer_len = (16 * 1024 + 16 * 4)
        else:
            specific_read_buffer_len = (16 * 1024 + 1968)
        vu.Data_Byte_Length.value = specific_read_buffer_len
    else:
        if WL_type == "SLC":
            vu.End_Page.value = vu.Start_Page.value
            vu.Data_Byte_Length.value = (16 * 1024 + 16 * 4)
        elif WL_type == "MLC":
            vu.End_Page.value = vu.Start_Page.value + 1
            vu.Data_Byte_Length.value = 20* 1024 * (vu.End_Page.value - vu.Start_Page.value +1)
            pass
        else:
            vu.End_Page.value = vu.Start_Page.value + 2
            vu.Data_Byte_Length.value = 20* 1024 * (vu.End_Page.value - vu.Start_Page.value +1)
        specific_read_buffer_len = vu.Data_Byte_Length.value
    vu.SLC_Enable.value = SLC_Enable
    vu.Ecc_Enable.value = Ecc_Enable
    datapayload = datapayload[:vu.Data_Byte_Length.value]
    response = send_data_out_vcmd(micron_vendor_cmd=vu, data_payload= datapayload, specific_read_buffer_len = specific_read_buffer_len, keep_error=keep_error)
    return response

def issue_D060_to_erase_specific_block(Ce:int, Plane:int, Block:int, SlcEnable:int, psaEnable:int, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D060()
    vu.b0_opcode.value = 0x60
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.Ce.value = Ce
    vu.Plane.value = Plane
    vu.Block.value = Block
    vu.SlcEnable.value = SlcEnable
    vu.psaEnable.value = psaEnable
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error = keep_error)
    return response