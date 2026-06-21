import inspect
from typing import cast, List

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.custom_vu.structs import *
from Script.project_api.custom_vu.get_defrag_source_vp_info_vu.structs import *
from Script.project_api.structs import micron_vu_40DD



_log = shared.logger
def print_array_tohex(databuff : bytearray, showlen :int, bytesperline: int) -> None:
    len = databuff.__len__()
    if len >= showlen:
        len = showlen
    for index in range(0,len,bytesperline):
        if(index + bytesperline < len):
            tmpdata = databuff[index: index+bytesperline]
            print(tmpdata.hex(' ',1) )
        else:            
            tmpdata = databuff[index: len]            
            print(tmpdata.hex(' ',1) )
    return
def issue_40DD_to_get_defrag_source_vp_information(vbnum : int, die:int, plane:int, page:int, vpindex:int) -> tuple[CommandResponse, SoucevpInformation]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40DD()
    vu.b0_opcode.value = 0xDD
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.w12_vbnum.value = vbnum
    vu.w14_die.value = die
    vu.w16_plane.value = plane
    vu.w18_page.value = page
    vu.w20_vpindex.value = vpindex

    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=False)
    
    print_array_tohex(payload,68, 4)
    return response, SoucevpInformation(payload)
