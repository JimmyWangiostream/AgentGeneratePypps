import inspect
from typing import cast, List, Generator, Tuple, Dict, Optional

from Script.api import shared, dumpfile, cmd_seq as ExecuteCMD
import random
from Script import api
from Script.api.exception import SIGHTING_RESPONSE_UNEXPECTED
from Script.project_api.reh.structs import PAGE_TYPE
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.vth_sweep.structs import micron_vu_401D, vt_diff_format
from Script.pattern.pattern_logger import logger

_log = shared.logger

def issue_401D_to_get_vt_distribution(die:int, plane:int, block:int, page:int, isSLC:int, index_in_16k_page:int, start_dac:int, end_dac:int, vt_mode:int, keep_error:bool = False)-> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_401D()
    vu.b0_opcode.value = 0x1D
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.die.value = die
    vu.plane.value = plane
    vu.block.value = block
    vu.page.value = page
    vu.slcMode.value = isSLC
    vu.indexIn16KPage.value = index_in_16k_page
    vu.startDAC.value = start_dac
    vu.endDAC.value = end_dac
    vu.vtMode.value = vt_mode
    specific_length = (end_dac - start_dac + 1) * 4
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, specific_read_buffer_len = specific_length, keep_error= keep_error)
    return response, payload

def convert_page_to_page_order(page:int, isSLC: int)->int:
    page_order = 0
    if isSLC == 1:
        page_order = page
    else:
        physical_page_base      = [0, 1620, 1652, 3308]
        physical_page_size      = [1620, 32, 1656, 4]
        order_base              = [0, 540, 556, 1108]
        order_size              = [540, 16, 552, 3] #有些 plane 的最後一個 page 是存 bitmap parity 不會轉 LBA
        if page >= physical_page_base[3] and  page < physical_page_base[3]+physical_page_size[3]:  #SLC
            region_index = 3
            shared_page_num = 1
        elif page >= physical_page_base[1] and  page < physical_page_base[1]+physical_page_size[1]: #MLC
            region_index = 1
            shared_page_num = 2
        elif page >= physical_page_base[0] and  page < physical_page_base[0]+physical_page_size[0]: #TLC
            region_index = 0
            shared_page_num = 3
        elif page >= physical_page_base[2] and page < physical_page_base[2]+physical_page_size[2]:  #TLC
            region_index = 2
            shared_page_num = 3
        else:
            logger.error(f'unexpected value - page = {page}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        
        offset = int((page - physical_page_base[region_index])//shared_page_num)
        page_order = order_base[region_index]+offset
    return page_order