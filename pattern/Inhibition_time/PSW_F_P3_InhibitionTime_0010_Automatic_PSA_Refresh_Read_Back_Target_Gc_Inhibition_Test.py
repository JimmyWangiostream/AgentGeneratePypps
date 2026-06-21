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

    def step1(self) -> None:
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock')) # for ARM load in cache
        logger.flow(1, 'get hw setting of inhibition time')
        self.inhibition_time_sec = self.get_hwsetting_inhibition_time()
        self.backup_inhibition_time_sec = self.inhibition_time_sec
        logger.flow(2, 'power cycle + init')
        self.power_cycle()
        logger.flow(3, 'check if gInhibitMgr.lock = 1')
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))
        if self.inhibination_enable != 1:
            logger.error_fp(f'inhibination_enable({self.inhibination_enable}) != 1')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL           
        logger.flow(4, 'Automatic PSA Refresh + Read back target GC (BG only) ')        
        # need feature owner describe details 

        logger.flow(5, 'check if gc trigger , if  triggered determine fail')
        # need feature owner describe details 

        logger.flow(6, f'idle for inhibition time {self.inhibition_time_sec} sec')
        time.sleep(self.inhibition_time_sec)

        logger.flow(7, f'check if  gInhibitMgr.lock = 0')
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))
        time.sleep(0.01)
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))            
        if self.inhibination_enable != 0:
            logger.error_fp(f'inhibination_enable({self.inhibination_enable}) != 0')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL   
        logger.flow(8, 'Automatic PSA Refresh + Read back target GC (BG only) ')        
        # need feature owner describe details 

        logger.flow(9, 'check if gc trigger , if  not triggered determine fail')
        # need feature owner describe details 
                     
    def power_cycle(self)->None:
       if random.randint(0,1):
            init_tester_to_unit_ready(resetmode = Dcmd5ResetType.HW_RESET, powerdown = False)
       else:
           init_tester_to_unit_ready(resetmode = Dcmd5ResetType.HW_RESET, powerdown = True)
       access_vendor_mode()
    def get_hwsetting_inhibition_time(self) -> int:
 
        self.hw_setting = api.HwSetting.get_instance()
        self.hw_setting.update_from_device()        
        value = self.hw_setting.get_local_val(api.HwSettingField.INHIBITION_TIME)
        return value
    def post_process(self) -> None:
        pass
   
 
run = Pattern().run
if __name__ == "__main__":
    run()