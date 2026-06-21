import package_root
from Script import api
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig, get_flash_setting
from Script.api.ufs_api.defines.constant_define import *
import time

class Pattern(UFSTC):
    def pre_process(self) -> None:
        
        pass

    def step1(self) -> None:
        logger.flow(1, 'Get flash setting Vendor_Minor_Code')
        flash_setting = get_flash_setting()
        fw_version_minor_code = flash_setting.Vendor_Minor_Code
        fw_version_minor_code2 = flash_setting.Vendor_Minor_Code2
        length = (flash_setting.Reserved_508_1023.bit_length() + 7 ) // 8
        buffer = flash_setting.Reserved_508_1023.to_bytes(length, "big")
        year_in_fw = buffer[0]
        month_in_fw = buffer[1]
        day_in_fw = buffer[2]
        logger.flow(2, f'Get flash setting Vendor_Minor_Code = {fw_version_minor_code}, Vendor_Minor_Code2 = {fw_version_minor_code2}, year = {year_in_fw}, month = {month_in_fw}, day = {day_in_fw}')
        logger.flow(3, 'Get fw version from 4001 vu ')
        fw_value_by_vu = self.get_fw_value()
        logger.flow(4, f'compare fw vesion')
        fw_ver_byte0_vu = fw_value_by_vu.FwVersion.payload[0]
        fw_ver_byte1_vu = fw_value_by_vu.FwVersion.payload[1]
        if (fw_ver_byte0_vu != fw_version_minor_code):
            logger.error_fp(f'data compare fail, fw_ver_byte0({fw_ver_byte0_vu}) != fw_version_minor_code({fw_version_minor_code})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if (fw_ver_byte1_vu != fw_version_minor_code2):
            logger.error_fp(f'data compare fail, fw_ver_byte1({fw_ver_byte1_vu}) != fw_version_minor_code2({fw_version_minor_code2})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL            
        logger.flow(5, f'compare fw vesion')   
        hex_year_msb = format(int(fw_value_by_vu.CompileVersion.payload[0]),"x")
        hex_year_lsb = format(int(fw_value_by_vu.CompileVersion.payload[1]),"x")
        concat_hex = hex_year_msb + hex_year_lsb
        year_in_vu = int(concat_hex, 16)
        

        month_in_vu = fw_value_by_vu.CompileVersion.payload[2]
        day_in_vu = fw_value_by_vu.CompileVersion.payload[3]
        first2_in_year = self.get_year_first_2()
        year_in_flash_setting = first2_in_year * 100 + year_in_fw

        if(year_in_flash_setting != year_in_vu):
            logger.error_fp(f'data compare fail, year_in_flash_setting({year_in_flash_setting}) != year_in_vu({year_in_vu})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL            
        if(month_in_fw != month_in_vu):
            logger.error_fp(f'data compare fail, month_in_fw({month_in_fw}) != month_in_vu({month_in_vu})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
        if(day_in_fw != day_in_vu):
            logger.error_fp(f'data compare fail, day_in_fw({day_in_fw}) != day_in_vu({day_in_vu})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL                             
        logger.flow(6, f'compare controlnand')            
        value = fw_value_by_vu.ControllerNand.value
        length = (value.bit_length() + 7) // 8
        buffer = value.to_bytes(length, "big")
        controllernand_vu = buffer.decode("ascii")
        if not (controllernand_vu.startswith("PS8329 B68S")):
            logger.error_fp(f'data compare fail, please check dump file')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def get_year_first_2(self) -> int:
        t = time.strftime("%Y-%m-%d %H:%M:%S")
        first_two = t[:2]
        return int(first_two)

    def post_process(self) -> None:
        pass
    
    def get_fw_value(self) -> project_api.GetFwVersion:
        #response, data_payload = project_api.issue_40C0_to_get_mConfig_data(specific_VB, 0x0)
        response, data_payload, fw_value_by_vu = project_api.issue_4001_to_get_fw_version()
        return fw_value_by_vu


run = Pattern().run
if __name__ == "__main__":
    run()