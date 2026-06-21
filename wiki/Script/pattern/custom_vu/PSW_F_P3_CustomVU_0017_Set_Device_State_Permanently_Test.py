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

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.modify_cnt = 0
        _, self.efuse_data_from_xmemory = api.read_Xmemory(sram_address=0xF8F80800)
        self.modify_limit = 8
        pass
    
    def step1(self) -> None:
        set_value = 1
        logger.flow(1, f'issue D0E2 to set Device state = {set_value}, modify_cnt = {self.modify_cnt+1}')
        self.set_device_state_in_different_method(Device_state=set_value, direct_set_efuse=False)
        pass
    
    def step2(self) -> None:
        logger.flow(2, 'power off with SSU')
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
        pass
    
    def step3(self) -> None:
        expect_value = (1 << self.modify_cnt) - 1
        logger.flow(3, f'issue read memory to check addr 0xF8F80826 shall be {expect_value}')
        _, device_state, NumOfRemainingStateChanges = project_api.issue_40E2_to_get_device_state()
        if device_state != expect_value:
            logger.error_lb(f'check Device State after setting')
            logger.error_fp(f'expect Device State from SRAM match MicronVU setting, but SRAM value = {device_state}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if self.modify_limit - self.modify_cnt != NumOfRemainingStateChanges:
            logger.error_lb(f'check NumOfRemainingStateChanges after setting')
            logger.error_fp(f'expect NumOfRemainingStateChanges = {self.modify_limit - self.modify_cnt}, but current value = {NumOfRemainingStateChanges}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def step4(self) -> None:
        logger.flow(4, 'issue VU C083 to set erase cnt and check device response fail while Device_state=1')
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

    def step5(self) -> None:
        logger.flow(5, 'issue D0E2 to set Device state multiple times')
        for i in range(6):
            set_value = i % 2
            logger.info(f'issue D0E2 to set Device state = {set_value}, modify_cnt = {self.modify_cnt+1}')
            self.set_device_state_in_different_method(Device_state=set_value, direct_set_efuse=i<3)
            logger.info('power off with SSU')
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
            expect_value = (1 << (self.modify_cnt)) - 1
            logger.info(f'issue read memory to check addr 0xF8F80826 shall be {expect_value}')
            _, device_state, NumOfRemainingStateChanges = project_api.issue_40E2_to_get_device_state()
            if device_state != expect_value:
                logger.error_lb(f'check Device State after setting')
                logger.error_fp(f'expect Device State from 40E2 is {expect_value}, but SRAM value = {device_state}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if self.modify_limit - self.modify_cnt != NumOfRemainingStateChanges:
                logger.error_lb(f'check NumOfRemainingStateChanges after setting')
                logger.error_fp(f'expect NumOfRemainingStateChanges = {self.modify_limit - self.modify_cnt}, but current value = {NumOfRemainingStateChanges}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            pass
        pass

    def step6(self) -> None:
        set_value = 0
        logger.flow(6, f'issue D0E2 to set Device state = {set_value}, modify_cnt = {self.modify_cnt+1}, expect fail')
        response = project_api.set_device_state(Device_state=set_value, only_in_ram=False, keep_error=True)
        if not (response.upiu.b6_response == api.UPIUResponse.TARGET_FAILURE and 
            response.upiu.b7_status == api.ScsiStatus.CHECK_CONDITION):
            logger.error_lb(f'issue D0E2 to set Device stat after 7 times')
            logger.error_fp(f'expect response fail, but status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        pass
    
    def step7(self) -> None:
        _, device_state, NumOfRemainingStateChanges = project_api.issue_40E2_to_get_device_state()
        if device_state != 2:
            logger.error_lb(f'check Device State after setting 8 times')
            logger.error_fp(f'expect Device State is 2 (Failure Analysis (FA) state), but current value = {device_state}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if NumOfRemainingStateChanges != 0:
            logger.error_lb(f'check NumOfRemainingStateChanges after setting 8 times')
            logger.error_fp(f'expect NumOfRemainingStateChanges = {0}, but current value = {NumOfRemainingStateChanges}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def set_device_state_in_different_method(self, Device_state:int, direct_set_efuse:bool) -> None:
        self.modify_cnt += 1
        if direct_set_efuse:
            original = self.efuse_data_from_xmemory[0x24:0x28]
            set_addr = 0xF8F80800 + 0x24
            expect_value = (1 << self.modify_cnt) - 1
            original[2] = expect_value
            set_value = int.from_bytes(original, 'little')
            project_api.issue_D0F4_to_set_eFuse(eFuse_addr=set_addr, eFuse_value=set_value)
            pass
        else:
            response = project_api.set_device_state(Device_state=Device_state, only_in_ram=False, keep_error=True)
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