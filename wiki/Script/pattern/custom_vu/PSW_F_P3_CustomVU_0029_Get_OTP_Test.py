import package_root
import time
import struct
from typing import cast
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.api.util import dumpfile
from Script.api.ufs_api.descriptors.configuration_desc.functions import print_config, push_write_config
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import *
#from scriptlib.fw.common import manufacture as mfg

timeout_min = 15
def parse_die_data(byte_data: bytearray) -> dict[str, list[int]]:
    dies:dict[str, list[int]] = {}
    dies = {
        "die0": [],
        "die1": [],
        "die2": [],
        "die3": []
    }
    
    current_die = None
    die_count = 0
    before_value = 0
    for i in range(0, len(byte_data), 2):
        value = (byte_data[i + 1] << 8) | byte_data[i]
        if value == before_value:
            continue
        else:
            before_value = value

        if value == 0xFFF0:
            current_die = f"die{die_count}"
            die_count += 1
        elif value == 0xFFF1:
            current_die = f"die{die_count}"
            die_count += 1
        elif value == 0xFFF2:
            current_die = f"die{die_count}"
            die_count += 1
        elif value == 0xFFF3:
            current_die = f"die{die_count}"
            die_count += 1
        elif value == 0xFFFF:
            break
        elif current_die is not None:
            dies[current_die].append(value)

    for die, data in dies.items():
        hex_data = [f'0x{value:04X}' for value in data]
        logger.info(f'{die}: {hex_data}')

    return dies

def format_direct_read_bbt(byte_data: bytearray) -> dict[str, list[int]]:
    dies:dict[str, list[int]] = {}
    dies = {
        "die0": [],
        "die1": [],
        "die2": [],
        "die3": []
    }

    for i in range(4 * api.DATA_SIZE_4K_BYTE):
        ce = i // api.DATA_SIZE_4K_BYTE
        current_die = f"die{ce}"
        vb = (i - (ce * api.DATA_SIZE_4K_BYTE)) // 3
        plane = ((i - (ce * api.DATA_SIZE_4K_BYTE)) % 3) * 2
        if byte_data[i] & 0xF == 0x04:
            #logger.info(f'ce = {ce}, vb = {vb}, plane = {plane}')
            value = (vb << 3) | plane
            dies[current_die].append(value)
        if (byte_data[i] >> 4) & 0xF == 0x04:
            plane += 1
            #logger.info(f'ce = {ce}, vb = {vb}, plane = {plane}')
            value = (vb << 3) | plane
            dies[current_die].append(value)
            
    for die, data in dies.items():
        hex_data = [f'0x{value:04X}' for value in data]
        logger.info(f'{die}: {hex_data}')
    return dies

def check_timeout(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False
    

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        self.flash_setting = FlashSetting()
        self.flash_setting.from_bytes(self.flash_setting_buffer)
        pass

    def step1(self) -> None:
        otp:list[bytearray] = []
        logger.flow(1, f'Host Issue VU 0x40BC to get OTP with page index = 0~3 (full/top/bottom)')
        for page_index in range(3):
            resp = project_api.issue_40BC_get_OTP(OTP_page_index=page_index)
            otp.append(bytearray(0))
            otp[page_index] = resp.data
            dumpfile(f'OTP_page_index{page_index}', otp[page_index])
        
        logger.flow(2, f'Verify OTP between page index = 0~3 (full/top/bottom)')
        if otp[1] != otp[2]:
            logger.error('Top deck BB page mismatch with bottom deck BB page')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info('Top deck BB page is same as bottom deck BB page')

        logger.info('Full BB page info of dies:')
        otp_dict0 = parse_die_data(byte_data=otp[0])
        logger.info('Top deck BB page info of dies:')
        otp_dict1 = parse_die_data(byte_data=otp[1])
        if otp_dict0 != otp_dict1:
            logger.error('Full BB page data mismatch with top deck BB page')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info('Full BB page data is same as top deck BB page')

        logger.flow(3, 'Get BBT info from VU 0x4097')
        self.bbt_sub_vb_info = project_api.get_BBT_physical_block_information()
        direc_read_pca = PCA()
        direc_read_pca.b10_block_l = self.bbt_sub_vb_info.Block.value
        direc_read_pca.b5_ce = self.bbt_sub_vb_info.CE.value
        direc_read_pca.b6_plane = self.bbt_sub_vb_info.plane.value

        logger.flow(4, 'Direct read BBT')
        direct_read_bbt_data = api.direct_read(pca=direc_read_pca, block_count=(4 * api.BLOCK4K_SIZE_4K_BYTE), include_FW_spare=True)
        dumpfile(f'Direct_read_bbt_data', direct_read_bbt_data)

        logger.flow(5, 'Format direct read data and check early bad blocks compare with OTP info')
        logger.info('Direct read bbt and format of dies:')
        direct_read_bbt_dict = format_direct_read_bbt(byte_data = direct_read_bbt_data)
        if otp_dict0 != direct_read_bbt_dict:
            logger.error('Full BB page data mismatch with direct read bbt')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info('Full BB page data is same as direct read bbt, test result = pass')
        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()