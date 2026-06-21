import package_root
from Script import api
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from typing import cast
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig, get_flash_setting
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api import read_fw_value
import time
from Script.project_api.block_budget.structs import GetCSICSInfoDescription, GetBoundaryBlocksForHiddenTableStaticDynamicPool, VBCount
from Script.project_api.mconfig_vu.structs import mConfig
import inspect
from Script.api import (shared, ExecuteCMD,
                        Dcmd5ResetType,
                        PATTERN_ASSERT_BUFFER_MANAGER_FAIL_CYCLE_INDICATOR_NOT_FOUND,
                        SfReadDescriptor, TaskManagementFunction, ConfigDescriptor410, ConfigDescriptorHeader410, ConfigDescriptorUnit410, MemoryType, ProvisioningType)
from Script.api.ufs_api import WellKnownLUN, init_tester_to_unit_ready
import Script.project_api.functions

# from Script.project_api.functions import issue_4022_to_get_NAND_feature

from Script.project_api.set_get_temperature.structs import GetNandTemperature, SetNandTemperature

class Pattern(UFSTC):
    def pre_process(self) -> None:     
        logger.flow(1,f'get hw setting, check if value are the same(temp)')
        hw_setting = api.HwSetting.get_instance()
        hw_setting.update_from_device()          
        lt_ce0, ct_ce0,  ht_ce0 = self.get_hwsetting_FA23_P1()
        # if lt_ce0!=ct_ce0 or ct_ce0 != ht_ce0:
        #     logger.error_fp(f'temperature ct lt ht compare fail')
        #     raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        nand_feature_tmp = self.get_fw_nand_feature()
        if (lt_ce0 << 1) != nand_feature_tmp:
            logger.error_fp(f'temperature ct compare hwsetting fail')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(2,f'modify hw setting, make sure all temp are different')
        expected_lt_ce0 = lt_ce0 + 1
        expected_ct_ce0 = ct_ce0 + 2
        expected_ht_ce0 = ht_ce0 + 3
        logger.info(f'expected_lt_ce0 = {expected_lt_ce0}, CT_CE0_TX_VREF = {expected_ct_ce0}, expected_ct_ce0 = {expected_ht_ce0}')

        hw_setting.set_local_val(api.HwSettingField.LT_CE0_TX_VREF, expected_lt_ce0)
        hw_setting.set_local_val(api.HwSettingField.CT_CE0_TX_VREF, expected_ct_ce0)
        hw_setting.set_local_val(api.HwSettingField.HT_CE0_TX_VREF, expected_ht_ce0)                  
        hw_setting.set_to_device()
        
        logger.flow(3,f'common temp data training test')
        nand_feature_tmp = self.get_fw_nand_feature()
        if (expected_ct_ce0 << 1) != nand_feature_tmp:
            logger.error_fp(f'temperature ct compare namnd temp ({(expected_ct_ce0 << 1)}) != get_fw_nand_feature ({nand_feature_tmp})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL            
        logger.flow(4,f'low temp data training test')
        setting_val = -11
        self.set_temp(setting_val) # 0 = -37
        nand_feature_tmp = self.get_fw_nand_feature()
        if (expected_lt_ce0 << 1) != nand_feature_tmp:
            logger.error_fp(f'temperature lt compare namnd temp ({(expected_lt_ce0 << 1)}) != get_fw_nand_feature ({nand_feature_tmp})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL   
            
        logger.flow(5,f'high temp data training test')
        setting_val = 100
        self.set_temp(setting_val)
        nand_feature_tmp = self.get_fw_nand_feature()
        if (expected_ht_ce0 << 1) != nand_feature_tmp:
            logger.error_fp(f'temperature ht compare namnd temp ({(expected_ht_ce0 << 1)}) != get_fw_nand_feature ({nand_feature_tmp})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL      
        
        logger.flow(6,f'recover hw setting')
        expected_lt_ce0 = lt_ce0 
        expected_ct_ce0 = ct_ce0 
        expected_ht_ce0 = ht_ce0
        logger.info(f'expected_lt_ce0 = {expected_lt_ce0}, CT_CE0_TX_VREF = {expected_ct_ce0}, expected_ct_ce0 = {expected_ht_ce0}')
        hw_setting.set_local_val(api.HwSettingField.LT_CE0_TX_VREF, expected_lt_ce0)
        hw_setting.set_local_val(api.HwSettingField.CT_CE0_TX_VREF, expected_ct_ce0)
        hw_setting.set_local_val(api.HwSettingField.HT_CE0_TX_VREF, expected_ht_ce0)

        hw_setting.set_to_device()
                
        logger.flow(7,f'recover temp')
        self.recover_temp()
        pass
    def set_temp(self, temp: int) -> None:
        set_nand_temp = SetNandTemperature()
        set_nand_temp.bEnableSetVuTemp.value = 1
        tmp = temp.to_bytes(2,byteorder='little',signed=True)
        #tmp = list(tmp)
        set_nand_temp.UC_TERMAL_SENSOR_1.payload = tmp
        rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)
        VU_temp = project_api.issue_40FD_get_uC_temp_value()
        logger.info(f'temp = {VU_temp}')
        ExecuteCMD.clear()
        #dumpbin('40FD_get_nand_temp',data_temp)        
    def recover_temp(self) -> None:
        set_nand_temp = SetNandTemperature()
        set_nand_temp.bEnableSetVuTemp.value = 0
        rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)

    def get_hwsetting_FA23_P1(self) -> list[int]:

        hw_setting = api.HwSetting.get_instance()
        hw_setting.update_from_device()        
        lt_ce = hw_setting.get_local_val(api.HwSettingField.LT_CE0_TX_VREF)
        ct_ce = hw_setting.get_local_val(api.HwSettingField.CT_CE0_TX_VREF)
        ht_ce = hw_setting.get_local_val(api.HwSettingField.HT_CE0_TX_VREF)                           
        return [lt_ce, ct_ce,  ht_ce]

    def get_fw_nand_feature(self) -> int:
        response, data_payload = project_api.issue_4022_to_get_NAND_feature(0,0x23)
        #rsp, payload = issue_4022_to_get_NAND_feature(die = 0, feature=0x4023)
        number = data_payload[8]
        #dumpbin('4022_data_trianing',data_payload)
        logger.info(f'4022_data_training_temp = {number}')
        return number
    
    def post_process(self) -> None:
        pass
    



run = Pattern().run
if __name__ == "__main__":
    run()