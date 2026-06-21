import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig
from Script.api.ufs_api.defines.constant_define import *
from typing import cast
from Script.api.ufs_api import *
import time

ENG2_WA = True
 
class Pattern(UFSTC):
    def pre_process(self) -> None:
       
        pass
    def set_inhibition_time_test(self,sec:int) -> None:
        logger.flow(1, 'get hw setting of inhibition time')
        self.hw_setting.set_local_val(api.HwSettingField.INHIBITION_TIME, sec)                  
        self.hw_setting.set_to_device()  
        self.power_cycle()        
        self.inhibition_time_sec = self.get_hwsetting_inhibition_time()
        logger.info(f'inhibition_time_sec = {self.inhibition_time_sec}')
        self.power_cycle()
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))
        if self.inhibination_enable != 1:
            logger.error_fp(f'inhibination_enable({self.inhibination_enable}) != 1')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL             
        time.sleep(self.inhibition_time_sec)
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))
        time.sleep(0.01)
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))        
        if self.inhibination_enable != 0:
            logger.error_fp(f'inhibination_enable({self.inhibination_enable}) != 0')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
    def step1(self) -> None:   
        self.default_inhibition_time_test()
        self.zero_sec_inhibition_time_test()
        test_inhibition_time_list = [180, 150, 90, 60, 30, 210, 240, 255, self.backup_inhibition_time_sec]
        for test_inhibition_time in test_inhibition_time_list:
            self.set_inhibition_time_test(test_inhibition_time)
        pass
    def zero_sec_inhibition_time_test(self)->None:
        self.hw_setting.set_local_val(api.HwSettingField.INHIBITION_TIME, 0)                  
        self.hw_setting.set_to_device()  
        self.power_cycle()
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))
        if self.inhibination_enable != 0:
            logger.error_fp(f'inhibination_enable({self.inhibination_enable}) != 0')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL           
    def default_inhibition_time_test(self) -> None:
        logger.flow(1, 'get hw setting of inhibition time')
        self.inhibition_time_sec = self.get_hwsetting_inhibition_time()
        self.backup_inhibition_time_sec = self.inhibition_time_sec
        logger.info(f'inhibition_time_sec = {self.inhibition_time_sec}')
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))
        self.power_cycle()
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))
        if self.inhibination_enable != 1:
            logger.error_fp(f'inhibination_enable({self.inhibination_enable}) != 1')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'idle = {self.inhibition_time_sec} sec')             
        time.sleep(self.inhibition_time_sec)
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))
        time.sleep(0.01)
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))
        if self.inhibination_enable != 0:
            logger.error_fp(f'inhibination_enable({self.inhibination_enable}) != 0')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL        
    def power_cycle(self)->None:
       if random.randint(0,1):
            init_tester_to_unit_ready(resetmode = Dcmd5ResetType.HW_RESET, powerdown = False)
       else:
           init_tester_to_unit_ready(resetmode = Dcmd5ResetType.HW_RESET, powerdown = True)
       access_vendor_mode()
    def get_hwsetting_inhibition_time(self) -> int:
 
        self.hw_setting = api.HwSetting.get_instance()
        self.hw_setting.update_from_device()        
        # check
        value = self.hw_setting.get_local_val(api.HwSettingField.INHIBITION_TIME)
        return value
    def post_process(self) -> None:
        pass
   
 
run = Pattern().run
if __name__ == "__main__":
    run()