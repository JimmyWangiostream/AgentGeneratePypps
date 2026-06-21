import package_root
import time
import struct
from typing import cast
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.api.ufs_api.descriptors.configuration_desc.functions import print_config, push_write_config
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *

def expected_page_attribute(page_index: int) -> tuple[int,list[int]]:
    if 0 <= page_index <= 1619:
        group_start = (page_index // 3) * 3
        group_indices = [group_start + i for i in range(3)]
        return page_index % 3 + 3, group_indices  # TLC_lower (3), TLC_upper (4), TLC_extra (5)
    elif  1652 <= page_index <= 3307:
        group_start = ((page_index - 1652) // 3) * 3 + 1652
        group_indices = [group_start + i for i in range(3)]
        return (page_index + 1) % 3 + 3, group_indices  # TLC_lower (3), TLC_upper (4), TLC_extra (5)
    elif 1620 <= page_index <= 1651:
        group_indices = [0, 0, 0]
        return (page_index - 1620) % 2 + 1, group_indices  # MLC_lower (1), MLC_upper (2)    
    elif 3308 <= page_index <= 3311:
        group_indices = [0, 0, 0]
        return 0, group_indices  # SLC    
    else:
        return 7, [0, 0, 0]



class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:

        for page_index in range(3313):
            logger.flow(1, f'Host issue VU 0x4010 to get page attribute with page index = {page_index}')
            resp = project_api.issue_4010_get_page_attribute(page_index=page_index, keep_error=True)

            if page_index <= 3311:
                if resp.upiu.b6_response != api.UPIUResponse.TARGET_SUCCESS:
                    logger.error(f'Fail to get page attribute with page index = {page_index}')
                    raise SIGHTING_RESPONSE_UNEXPECTED
                else:
                    page_attribute = int.from_bytes(resp.data[0:3], byteorder='little')
                    TLC_lower = int.from_bytes(resp.data[4:7], byteorder='little')
                    TLC_upper = int.from_bytes(resp.data[8:11], byteorder='little')
                    TLC_extra = int.from_bytes(resp.data[12:15], byteorder='little')
                    TLC_page_list = [TLC_lower, TLC_upper, TLC_extra]
                    logger.info(f'Page index = {page_index}, page attribute = {page_attribute}, lower/upper/extra = {TLC_page_list}')

                    sw_page_attribute, sw_TLC_page_list = expected_page_attribute(page_index=page_index)
                    if page_attribute != sw_page_attribute or TLC_page_list != sw_TLC_page_list:
                        logger.error(f'Expected page attribute = {sw_page_attribute}, lower/upper/extra = {sw_TLC_page_list}, data mismatch')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    else:
                        logger.info(f'Expected page attribute = {sw_page_attribute}, lower/upper/extra = {sw_TLC_page_list}, data match')

            else:
                if resp.upiu.b6_response != api.UPIUResponse.TARGET_FAILURE or resp.upiu.b7_status != api.ScsiStatus.CHECK_CONDITION or resp.b32_sense_data.b2_sense_key != api.SenseKey.ILLEGAL_REQUEST or resp.b32_sense_data.b12_asc != 0x1A or resp.b32_sense_data.b13_ascq != 0x00:
                    logger.error(f'Get page attribute with page index = {page_index}, response should be target failaure with status = CEHCK_CONDITION, sense_key = ILLEGAL_REQUEST, asc = PARAMETER_LIST_LENGTH_ERROR')
                    logger.error(f'Current reponse = {api.get_cmd_response_byte_str(resp)}, status = {api.get_scsi_status_str(resp)}, sense_key = {api.get_sense_key_str(resp)}, asc = {api.get_asc_ascq_description(resp)}')
                    raise SIGHTING_RESPONSE_UNEXPECTED
                else:
                    logger.info(f'Get page index = {page_index} and response as expection')

            ExecuteCMD.clear() 

        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()