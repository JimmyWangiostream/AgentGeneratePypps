import package_root
from Script import api
from Script.api.util.functions import dumpfile
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api import  cmd_seq as ExecuteCMD
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig, get_flash_setting
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api import read_fw_value
import time
from Script.project_api.set_get_temperature.structs import GetNandTemperature, SetNandTemperature
import inspect
from Script.lib.sdk_lib.user.exception import  DLL_RESPONSE_ERROR
from typing import Optional, cast, Any, Union

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.test_4021()
        pass
    def compare_data_show_log(self,variable1_name:str,variable1_val:int, variable2_name:str,variable2_val:int,increase_val:int = 0, compare_method:str = "=")->None:
        if compare_method == "=":
            if(variable1_val != (variable2_val + increase_val)):
                logger.error_fp(f'compare fail {variable1_name}({variable1_val}) != {variable2_name}({variable2_val}) + {increase_val}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL    
            if increase_val == 0:
                if(variable1_val != (variable2_val)):
                    logger.error_fp(f'compare fail  {variable1_name}({variable1_val}) != {variable2_name}({variable2_val})')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
             
    def test_4021(self) -> None:
        logger.flow(1,"issue 4021 to get each nand temperature")
        rsp , GetNandTemperature = project_api.issue_4021_get_nand_temperature()
        # normal temperature case
        flash_setting = get_flash_setting()
        ce_num = flash_setting.Max_Fdevice

        # self.compare_data_show_log("tempereture_from_fw_ce0",cast(int, (tempereture_from_fw_ce0)), "GetNandTemperature.temperature_of_die_0.value",GetNandTemperature.temperature_of_die_0.value)

        # if ce_num >= 2:
        #     tempereture_from_fw_ce1 = read_fw_value('gUfsApiStruct.ftl->temp.temporary_ts[1]')
        #     self.compare_data_show_log("tempereture_from_fw_ce1",cast(int, (tempereture_from_fw_ce1)), "GetNandTemperature.temperature_of_die_1.value",GetNandTemperature.temperature_of_die_1.value)
        # if ce_num >= 4:
        #     tempereture_from_fw_ce2 = read_fw_value('gUfsApiStruct.ftl->temp.temporary_ts[2]')
        #     self.compare_data_show_log("tempereture_from_fw_ce2",cast(int, (tempereture_from_fw_ce2)), "GetNandTemperature.temperature_of_die_2.value",GetNandTemperature.temperature_of_die_2.value)
        #     #     logger.error_fp(f'temperature ce2 compare fail')
        #     #     raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #     tempereture_from_fw_ce3 = read_fw_value('gUfsApiStruct.ftl->temp.temporary_ts[3]')
        #     self.compare_data_show_log("tempereture_from_fw_ce3",cast(int, (tempereture_from_fw_ce3)), "GetNandTemperature.temperature_of_die_3.value",GetNandTemperature.temperature_of_die_3.value)
        #     #     logger.error_fp(f'temperature ce3 compare fail')
        #     #     raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
        #vu set temperature case
        logger.flow(3,"issue D08A to set temperature , with Use_Delayed_fake_tmeperatures = 0, bEnableSetVuTemp = 1, tempeprature = 20")
        temp_gap = 37
        temp_set = 20
        set_nand_temp = SetNandTemperature()
        set_nand_temp.bEnableSetVuTemp.value = 1
        set_nand_temp.NAND_TEMPERATURE_DIE_0.value = temp_set
        if ce_num >= 2:
            set_nand_temp.NAND_TEMPERATURE_DIE_1.value = temp_set
        if ce_num >= 4:
            set_nand_temp.NAND_TEMPERATURE_DIE_2.value = temp_set
            set_nand_temp.NAND_TEMPERATURE_DIE_3.value = temp_set
        set_nand_temp.Use_Delayed_fake_tmeperatures.value = 0  
        rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)
        logger.flow(4,"issue 4021 to get each nand temperature, expected nand temperature = 20 + 37(value offset)")
        rsp , GetNandTemperature = project_api.issue_4021_get_nand_temperature()
        self.compare_data_show_log("temp_set + temp_gap", temp_set + temp_gap, "GetNandTemperature.temperature_of_die_0.value", GetNandTemperature.temperature_of_die_0.value)

        if ce_num >= 2:
            self.compare_data_show_log("temp_set + temp_gap", temp_set + temp_gap, "GetNandTemperature.temperature_of_die_1.value", GetNandTemperature.temperature_of_die_1.value)            
            if (temp_set + temp_gap)!= GetNandTemperature.temperature_of_die_1.value:
                logger.error_fp(f'temperature ce1 compare fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if ce_num >= 4:
            self.compare_data_show_log("temp_set + temp_gap", temp_set + temp_gap, "GetNandTemperature.temperature_of_die_2.value", GetNandTemperature.temperature_of_die_2.value) 
            self.compare_data_show_log("temp_set + temp_gap", temp_set + temp_gap, "GetNandTemperature.temperature_of_die_3.value", GetNandTemperature.temperature_of_die_3.value)  
        # error case
        logger.flow(5,"issue 4021 to error case largger than threshold")
        temp_set = 126
        set_nand_temp = SetNandTemperature()
        set_nand_temp.bEnableSetVuTemp.value = 1
        set_nand_temp.NAND_TEMPERATURE_DIE_0.value = temp_set
        if ce_num >= 2:
            set_nand_temp.NAND_TEMPERATURE_DIE_1.value = temp_set
        if ce_num >= 4:
            set_nand_temp.NAND_TEMPERATURE_DIE_2.value = temp_set
            set_nand_temp.NAND_TEMPERATURE_DIE_3.value = temp_set
        set_nand_temp.Use_Delayed_fake_tmeperatures.value = 0  

        rsp_fail = False
        try:            
            rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)    
        except DLL_RESPONSE_ERROR:
            rsp_fail = True
            logger.info('send command error')   
        ExecuteCMD.clear()                           
        if not rsp_fail:
            logger.error_fp(f'D08A with error case set temp ({temp_set}), shall fail')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(5,"issue 4021 to error case smaller than threshold")
        temp = -38
        temp_set = temp.to_bytes(2,byteorder='little',signed=True)
        set_nand_temp = SetNandTemperature()
        set_nand_temp.bEnableSetVuTemp.value = 1
        set_nand_temp.NAND_TEMPERATURE_DIE_0.payload = temp_set
        if ce_num >= 2:
            set_nand_temp.NAND_TEMPERATURE_DIE_1.payload = temp_set
        if ce_num >= 4:
            set_nand_temp.NAND_TEMPERATURE_DIE_2.payload = temp_set
            set_nand_temp.NAND_TEMPERATURE_DIE_3.payload = temp_set
        set_nand_temp.Use_Delayed_fake_tmeperatures.value = 0  

        rsp_fail = False
        try:            
            rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)    
        except DLL_RESPONSE_ERROR:
            rsp_fail = True
            logger.info('send command error')  
        ExecuteCMD.clear()                
        if not rsp_fail:
            logger.error_fp(f'D08A with error case set temp ({temp}), shall fail')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL        
        # recover

        logger.flow(5,"issue D08A to set temperature , with bEnableSetVuTemp = 0")
        set_nand_temp.bEnableSetVuTemp.value = 0
        set_nand_temp.Use_Delayed_fake_tmeperatures.value = 0  
        rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)
        logger.flow(6,"issue 4021 to get each nand temperature")
        rsp , GetNandTemperature = project_api.issue_4021_get_nand_temperature()
        pass
    def step1(self) -> None:              
        pass
    def post_process(self) -> None:
        pass
    



run = Pattern().run
if __name__ == "__main__":
    run()