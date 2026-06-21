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
from Script.api.ufs_api import read_fw_value
import time
from Script.project_api.set_string_description.structs import SerialNumberString, ProductNameString, ReadUid



class Pattern(UFSTC):
    def pre_process(self) -> None:
        
        pass
    def get_ascii_str(self, raw_byte:int) -> str:
        value = raw_byte
        length = (value.bit_length() + 7) // 8
        buffer = value.to_bytes(length, "little")
        ascii_str = buffer.decode("ascii")
        return ascii_str        
    
    def step1(self) -> None:
        logger.flow(1,"get health report")
        payload, health_report = project_api.get_health_report()
        print(f'health_report.flash_id_ce0 {health_report.flash_id_ce0.payload}')
        print(f'health_report.flash_id_ce1 {health_report.flash_id_ce1}')
        print(f'health_report.flash_id_ce2 {health_report.flash_id_ce2}')
        print(f'health_report.flash_id_ce3 {health_report.flash_id_ce3}')
        
        flash_setting = get_flash_setting()
        ce_num = flash_setting.Max_Fdevice
        logger.flow(1,"issue 4061 to get uid")
        response, uid = project_api.issue_4061_to_get_uid()
        if ce_num >=1:
            if health_report.flash_id_ce0.payload != uid.uid_of_physical_die0.payload:
                logger.error_fp(f'compare ce0 uid fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if uid.ce_die0.value != 0 or uid.ch_die0.value != 0 or uid.cpu_die0.value != 0:
                logger.error_fp(f'compare ce0 fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if ce_num >=2:
            if health_report.flash_id_ce1.payload != uid.uid_of_physical_die1.payload:
                logger.error_fp(f'compare ce1 uid fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if uid.ce_die1.value != 1 or uid.ch_die1.value != 0 or uid.cpu_die1.value != 0:
                logger.error_fp(f'compare ce1 fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if ce_num >=4:
            if health_report.flash_id_ce2.payload != uid.uid_of_physical_die2.payload:
                logger.error_fp(f'compare ce2 uid fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if uid.ce_die2.value != 2 or uid.ch_die2.value != 0 or uid.cpu_die2.value != 0:
                logger.error_fp(f'compare ce2 fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL    
            if health_report.flash_id_ce3.payload != uid.uid_of_physical_die3.payload:
                logger.error_fp(f'compare ce3 uid fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if uid.ce_die3.value != 3 or uid.ch_die3.value != 0 or uid.cpu_die3.value != 0:
                logger.error_fp(f'compare ce3 fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL    
        pass
    def post_process(self) -> None:
        pass
    
    def get_health_report(self) -> None:
        
        pass


run = Pattern().run
if __name__ == "__main__":
    run()