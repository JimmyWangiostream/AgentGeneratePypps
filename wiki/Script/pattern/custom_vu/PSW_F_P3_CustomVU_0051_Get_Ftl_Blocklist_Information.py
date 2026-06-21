import package_root
from Script import api
from Script.api.util.functions import dumpfile
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig, get_flash_setting
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api import read_fw_value, vendor_cmd
import time
from Script.project_api.block_budget.structs import GetCSICSInfoDescription, GetBoundaryBlocksForHiddenTableStaticDynamicPool, VBCount
from Script.project_api.custom_vu.get_VB_list_info.structs import GetBlkList, MmesgEventLogBlockInformation
from Script.project_api.custom_vu.get_VB_list_info.functions import issue_4099_to_get_ftl_blk_list,issue_4099_to_get_ftl_blk_list_mmmesg
import inspect
from typing import Any
from Script.api.ufs_api.vendor_cmd.structs import PCA
from typing import Literal
class BlockInfo:
    blk_cnt: int                 
    blk_head: int              
    blk_tail: int             
    
def print_object_info_ai(object: Any) -> None:
        logger.info(f'================= [{object.__class__.__name__}]=================')
        fields = [
            (name, field) for name, field in object.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        fields.sort(key=lambda kv: kv[1].start_offset)
        for name, field in fields:
            logger.info(
                f'Byte[{field.start_offset}:{field.end_offset}]: {name} = {field.value}'
            )



def get_vb_list(vb_info: bytearray) -> list[BlockInfo]:
    result_list :list[BlockInfo] = []
    index = 0
    
    while index < len(vb_info):
        blk_info = BlockInfo()
        count = int.from_bytes(vb_info[index:index+2], byteorder='little')
        index += 2
        is_all_zero = not any(vb_info[index:])
        if is_all_zero:
            logger.info(f'index {index} = all zero')
            return result_list
        else:
            blk_info.blk_cnt = count
            if count == 0:
                blk_info.blk_head = 0
                blk_info.blk_tail = 0
                result_list.append(blk_info)
            else:

                for _ in range(count):
                    info = int.from_bytes(vb_info[index:index+2], byteorder='little')
                    if _ == 0:
                        blk_info.blk_head = info
                    if _ == (count-1):
                        blk_info.blk_tail = info
                        result_list.append(blk_info)
                    index += 2
    
    return result_list

def get_bit_from_byte(byte: int, bit_index: int) -> int:
    """
    Get a specific bit from a byte.

    :param byte: 1-byte integer (0~255)
    :param bit_index: bit position (0~7), bit0 = LSB
    :return: 0 or 1
    """
    if not 0 <= byte <= 0xFF:
        raise ValueError("byte must be in range 0~255")
    if not 0 <= bit_index <= 7:
        raise ValueError("bit_index must be in range 0~7")

    return (byte >> bit_index) & 0x1

def get_bits(val:int, start:int, end:int) -> int: 
    """取 bit[start:end]（包含 start，不包含 end）"""
    width = end - start
    mask = (1 << width) - 1
    return (val >> start) & mask

class MmesgBlkLocation:
    def __init__(self, data:int | bytearray | bytes, byteorder: Literal["little", "big"] = "little") -> None:
        self.raw: int
        if isinstance(data, (bytes, bytearray)):
            if len(data) != 4:
                raise ValueError("data must be 4 bytes")
            self.raw = int.from_bytes(data, byteorder)
        elif isinstance(data, int):
            self.raw = data & 0xFFFFFFFF
        else:
            raise TypeError("data must be bytes or int")

        self.block_number_of_physical_blk = (self.raw >> 0) & 0x7FF            # bit[0:10]
        self.die_number_of_physical_blk = (self.raw >> 11) & 0x7                     # bit[11:13]
        self.plane_number_of_physical_blk = (self.raw >> 14) & 0x7  # bit[14:16]
        self.pb_status = (self.raw >> 17) & 0x3    # bit[17:18]


    def __repr__(self) -> str:
        return (
            f"MmesgBlkLocation("
            f"block_number_of_physical_blk={self.block_number_of_physical_blk}, "
            f"pb_status={self.pb_status}, "
            f"plane_number_of_physical_blk={self.plane_number_of_physical_blk}, "
            f"die_number_of_physical_blk={self.die_number_of_physical_blk})"
        )



class Pattern(UFSTC):
    def pre_process(self) -> None:
        #self.test_4099_param0_1()
        self.test_4099()
        pass
    def get_sorted_VB_list_from_VU_406D(self) -> list[BlockInfo]:
        resp = project_api.issue_406D_get_VB_list_info()
        dumpfile("4060_raw_data", resp.data)
        vb_list = get_vb_list(resp.data)
        return vb_list
    def test_pb_info(self,pb_location:int) -> None:
        mmesg_location = MmesgBlkLocation(pb_location)
        pca = PCA()
        logger.info(f'issue direct read')
        pca.b10_block_l = mmesg_location.block_number_of_physical_blk 
        pca.b11_block_h = mmesg_location.block_number_of_physical_blk >> 8
        pca.b38_plane = mmesg_location.plane_number_of_physical_blk
        pca.b5_ce = mmesg_location.die_number_of_physical_blk
        pca.l12_fpage = 0
        dumpfile("first_pca.bin", pca.to_bytes)
        payload = vendor_cmd.direct_read(pca, 4,include_FW_spare = True)
        read_status_page0 = payload[128 + 4* DATA_SIZE_4K_BYTE]
        dumpfile("first_pb_diread_read.bin", payload)
        pca.l12_fpage = 1103
        dumpfile("last_pca.bin", pca.to_bytes)
        payload = vendor_cmd.direct_read(pca, 4,include_FW_spare = True)
        read_status_last_page = payload[128 + 4* DATA_SIZE_4K_BYTE]
        dumpfile("last_pb_diread_read.bin", payload)
        if mmesg_location.pb_status == 0: # close
            if read_status_page0 != 0 or read_status_last_page != 0:
                logger.error_fp(f'mmesg_location.pb_status = {mmesg_location.pb_status} (close), \
                read_status_page0({read_status_page0}) and read_status_last_page({read_status_last_page}) should be 0') 
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL    
                pass
        if mmesg_location.pb_status == 1: # open
            if read_status_page0 != 0 or get_bit_from_byte(read_status_last_page, 4) != 1:
                logger.error_fp(f'mmesg_location.pb_status = {mmesg_location.pb_status} (close), \
                read_status_page0({read_status_page0}) should be 0 and read_status_last_page({read_status_last_page}) bit 4 should be 1') 
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                pass   
        if mmesg_location.pb_status == 2: # invalid
            if get_bit_from_byte(read_status_page0, 4) != 1 or get_bit_from_byte(read_status_last_page, 4) != 1:
                logger.error_fp(f'mmesg_location.pb_status = {mmesg_location.pb_status} (close), \
                read_status_page0({read_status_page0}) bit 4 should be 1and read_status_last_page({read_status_last_page}) bit 4 should be 1')                 
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL    
                pass
        pass
    def test_4099_param0_1(self) -> None:
        logger.flow(4,"get 4099 with parm0 = 1")
        rsp, mmseg_info = issue_4099_to_get_ftl_blk_list_mmmesg(1) 
        mmseg_cnt = mmseg_info.amount_double_word_of_product_output.value - mmseg_info.event_log_pb_cnt.value - 3
                    
        offset_of_mmseg = 8 + 4 * (mmseg_info.event_log_pb_cnt.value + 1)
        logger.info(f'Check mmseg')
        logger.info(f'offset_of_mmseg = {offset_of_mmseg}')
        for i in range(mmseg_cnt):
            logger.info(f'check {i}st pb of mmseg log')
            pb_info = int.from_bytes(mmseg_info.payload[offset_of_mmseg + 4*i: offset_of_mmseg + 4 * i + 4], byteorder='little')
            self.test_pb_info(pb_info)

        for i in range(mmseg_info.event_log_pb_cnt.value):
            logger.info(f'check {i}st pb of event log')
            pb_info = int.from_bytes(mmseg_info.payload[8 + 4*i: 8 + 4 * i + 4], byteorder='little')
            self.test_pb_info(pb_info)            



    def test_4099(self) -> None:
        logger.flow(1,"get 406D")
        vb_info_list = self.get_sorted_VB_list_from_VU_406D()
        logger.flow(2,"get 4099")
        rsp, blk_info = issue_4099_to_get_ftl_blk_list(0)
        
        dumpfile("4099_blk_info", blk_info.payload)
        offset_increase_4099 = 12
        offset_4099 = 0
        logger.flow(3,"compare 406D and 4099")
        for vb_info in vb_info_list:
            logger.info(f'vb_info = {vb_info.blk_cnt}, {vb_info.blk_head}, {vb_info.blk_tail}')
            blk_head = int.from_bytes(blk_info.payload[offset_4099:offset_4099+4], byteorder='little')
            blk_tail = int.from_bytes(blk_info.payload[offset_4099+4:offset_4099+8], byteorder='little')
            blk_cnt = int.from_bytes(blk_info.payload[offset_4099+8:offset_4099+12], byteorder='little')
            if vb_info.blk_cnt > 0:
                if (vb_info.blk_cnt != blk_cnt) or (vb_info.blk_head != blk_head) or (vb_info.blk_tail != blk_tail):
                    logger.error_fp(f'vb_info.blk_cnt{vb_info.blk_cnt} != blk_cnt{blk_cnt} or vb_info.blk_head{vb_info.blk_head} != blk_head{blk_head}\
                                    or vb_info.blk_tail{vb_info.blk_tail} != blk_tail{blk_tail}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                if ((blk_cnt != 0) and ((blk_cnt != 0xFFFFFFFF))) or (blk_head != 0xFFFFFFFF) or (blk_tail != 0xFFFFFFFF):
                    logger.error_fp(f'blk_cnt{blk_cnt} != 0 or 0xFFFFFFFF != blk_head{blk_head}\
                                        or 0xFFFFFFFF != blk_tail{blk_tail}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            offset_4099 += offset_increase_4099
        compare_list = blk_info.payload[offset_4099:]
        is_all_ff = all(b == 0xff for b in compare_list)
        if not is_all_ff:
            logger.error_fp(f'expected all 0xff, offset_4099 = {offset_4099}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL            
        pass
    def step1(self) -> None:              
        pass
    def post_process(self) -> None:
        pass
    



run = Pattern().run
if __name__ == "__main__":
    run()