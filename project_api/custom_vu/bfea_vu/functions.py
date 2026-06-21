import inspect
from typing import cast, List

from Script.api import shared, util, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd, micron_vu_40B1, micron_vu_4067
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.project_api.custom_vu.bfea_vu.structs import *
from Script.api.cmd_seq.response import CommandResponse
from Script.api import dumpfile, cmd_seq as ExecuteCMD

_log = shared.logger
def issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(flag:int) -> None:
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x18
    vu.b1_func.value = 0xD0
    vu.d12_reserved.value = flag
    send_no_data_vcmd(micron_vendor_cmd=vu)


def issue_404A_Get_Bfea_Bin_Offset() -> Bin_Offset_404A:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0x4A
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu)
    dumpfile('404A_vu_output.bin',buf)
    return Bin_Offset_404A(buf)

def issue_40B1_Get_Best_Bfea_Scan(vb:int, ce: int) -> bytearray:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40B1()
    vu.b0_opcode.value = 0xB1
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.l12_vb.value = vb
    vu.l16_die.value = ce
    dumpfile('40B1_vu_input.bin',bytearray(vu.payload))
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu)
    dumpfile('40B1_vu_output.bin',buf)
    return buf


def issue_4067_Single_Read_With_Bin_Option(ce:int, vb: int, bin:int, plane:int , page:int) -> bytearray:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4067()
    vu.b0_opcode.value = 0x67
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.l12_ce.value = ce
    vu.l16_plane.value = plane
    vu.l20_vb.value = vb
    vu.l24_page.value = page
    vu.l29_bin.value = bin
    dumpfile('4067_vu_input.bin',bytearray(vu.payload))
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu)
    dumpfile('4067_vu_output.bin',buf)
    return buf

def issue_D04A_Set_Bin_Offset(N:int, EC_interval:int, SLC_L1:int, MLC_L1:int, MLC_L2:int, MLC_L3:int, TLC_L1:int, TLC_L2:int, TLC_L3:int, TLC_L4:int, TLC_L5:int, TLC_L6:int, TLC_L7:int) -> bytearray:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D04A()
    vu.b0_opcode.value = 0x4A
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0#0x80
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.N.value = N
    vu.EC_Interval.value = EC_interval
    vu.SLC_L1.value = SLC_L1
    vu.MLC_L1.value = MLC_L1
    vu.MLC_L2.value = MLC_L2
    vu.MLC_L3.value = MLC_L3
    vu.TLC_L1.value = TLC_L1
    vu.TLC_L2.value = TLC_L2
    vu.TLC_L3.value = TLC_L3
    vu.TLC_L4.value = TLC_L4
    vu.TLC_L5.value = TLC_L5
    vu.TLC_L6.value = TLC_L6
    vu.TLC_L7.value = TLC_L7
    dumpfile('D04A_input.bin',bytearray(vu.payload))
    response, buf = send_data_in_vcmd(micron_vendor_cmd=vu)
    return buf