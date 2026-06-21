import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from typing import Dict, List, cast, Optional
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.api.ufs_api.debug_cmd.dcmd_enum import Dcmd5ResetType
from time import sleep

ENG2_WA = True

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass
    
    def step1(self) -> None:
        logger.flow(1, 'issue D0FC to set Device state in ram')
        project_api.set_device_state(Device_state=1, only_in_ram=True)
        pass
    
    def step2(self) -> None:
        logger.flow(2, 'issue read memory to check addr 0xF8F80826 shall be 1')
        device_state = self.get_device_state_in_ram()
        if device_state != 1:
            logger.error_lb(f'check Device State after setting')
            logger.error_fp(f'expect Device State from SRAM match MicronVU setting, but SRAM value = {device_state}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        _, device_state = project_api.get_FW_states_in_RAM()
        if device_state != 1:
            logger.error_lb(f'check Device State after setting')
            logger.error_fp(f'expect Device State from VU40FC match MicronVU setting, but VU40FC value = {device_state}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
        
    def step3(self) -> None:
        logger.flow(3, 'issue VU C083 to set erase cnt and check device response fail while Device_state=1')
        VB_Num = project_api.VUC083VB_Num.CHANGE_THE_EC_ONLY_IN_RAM
        response = project_api.issue_C083_to_set_erase_read_count_parameter(Parameter0=project_api.VUC083Paremeter.SET_EC_TABLE, VB_Num=VB_Num, RC_TH_Value=0, data_payload=bytearray(api.DATA_SIZE_4K_BYTE), keep_error=True)
        if not (response.upiu.b6_response == api.UPIUResponse.TARGET_FAILURE and 
            response.upiu.b7_status == api.ScsiStatus.CHECK_CONDITION and
            response.b32_sense_data.b12_asc == 0x24 and
            response.b32_sense_data.b13_ascq == 0x0):
            logger.error_lb(f'issue_C083_to_set_erase_read_count_parameter while device_state == 1')
            logger.error_fp(f'expect response fail, but status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        pass
        
    def step4(self) -> None:
        logger.flow(4, 'power off with SSU')
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
        pass
    
    def step5(self) -> None:
        logger.flow(5, 'issue read memory to check addr 0xF8F80826 shall be 0')
        device_state = self.get_device_state_in_ram()
        if device_state != 0:
            logger.error_lb(f'check Device State after POR')
            logger.error_fp(f'expect Device State from SRAM clear after POR, but SRAM value = {device_state}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        _, device_state = project_api.get_FW_states_in_RAM()
        if device_state != 0:
            logger.error_lb(f'check Device State after POR')
            logger.error_fp(f'expect Device State from VU40FC clear after POR, but VU40FC value = {device_state}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def post_process(self) -> None:
        pass
    
    def get_device_state_in_ram(self) -> int:
        addr = 0xF8F80800
        _, payload = api.read_Xmemory(addr)
        return int(payload[38])




run = Pattern().run
if __name__ == "__main__":
    run()