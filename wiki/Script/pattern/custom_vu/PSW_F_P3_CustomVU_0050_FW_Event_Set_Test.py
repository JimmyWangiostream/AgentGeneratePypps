import package_root
from Script import api
from Script.api.util.functions import dumpfile
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
import inspect
from Script.api import (shared, ExecuteCMD,
                        Dcmd5ResetType,
                        PATTERN_ASSERT_BUFFER_MANAGER_FAIL_CYCLE_INDICATOR_NOT_FOUND,
                        SfReadDescriptor, TaskManagementFunction, ConfigDescriptor410, ConfigDescriptorHeader410, ConfigDescriptorUnit410, MemoryType, ProvisioningType)
from Script.api.ufs_api import WellKnownLUN, init_tester_to_unit_ready


class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass
     
    def test_D0FB(self) -> None:
        logger.flow(1,"D0F8 0 test, expetced POWER_ON_WB_EN no change after HW RESET")
        set_flag = ExecuteCMD.SetFlag().assign(idn=api.FlagIDN.POWER_ON_WB_EN).enqueue()
        ExecuteCMD.send(clear_on_success=True)    
        rsp = project_api.issue_D0FB_set_fw_state_in_ram(0)
        init_tester_to_unit_ready(Dcmd5ResetType.RESET_N)
        read_flag = ExecuteCMD.ReadFlag().assign(idn=api.FlagIDN.POWER_ON_WB_EN).enqueue()
        ExecuteCMD.send(clear_on_success=False)
        rsp = cast(api.QueryResponse, ExecuteCMD.read_response(read_flag))# type: ignore
        idn, index, selector, val = api.parse_read_attr_rsp(rsp)# type: ignore
        logger.info(f'{idn=},{index=},{selector=},{val=}')        
        ExecuteCMD.clear()
        if val != 1:
            logger.error_fp(f'value reset after hw reset')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL            
        logger.flow(2,"D0F8 1 test, expetced POWER_ON_WB_EN change after HW RESET")
        rsp = project_api.issue_D0FB_set_fw_state_in_ram(1)
        init_tester_to_unit_ready(Dcmd5ResetType.RESET_N)
        read_flag = ExecuteCMD.ReadFlag().assign(idn=api.FlagIDN.POWER_ON_WB_EN).enqueue()
        ExecuteCMD.send(clear_on_success=False)
        rsp = cast(api.QueryResponse, ExecuteCMD.read_response(read_flag))# type: ignore
        idn, index, selector, val = api.parse_read_attr_rsp(rsp)# type: ignore
        logger.info(f'{idn=},{index=},{selector=},{val=}')        
        ExecuteCMD.clear()
        if val != 0:
            logger.error_fp(f'value not reset after hw reset')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL            
        logger.flow(3,"D0F8 2 test, expetced SCSI cmd TO, after ISR")
        try:
            rsp = project_api.issue_D0FB_set_fw_state_in_ram(2)
        except api.TIMEOUT_EXCEPTIONS:
            cmd_to_trigger = True
            ExecuteCMD.clear()

        cmd_to_trigger = False
        try:
            read_flag = ExecuteCMD.ReadFlag().assign(idn=api.FlagIDN.POWER_ON_WB_EN).enqueue()
            ExecuteCMD.send(clear_on_success=False)        
        except api.TIMEOUT_EXCEPTIONS:
            cmd_to_trigger = True
            ExecuteCMD.clear()

        if not cmd_to_trigger:
            logger.error_fp(f'ISR FAIL')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL     
        pass
        logger.flow(4,"init flow with HW RESET")
        init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)
    def step1(self) -> None:
        self.test_D0FB()                 
        pass
    def post_process(self) -> None:
        pass
    



run = Pattern().run
if __name__ == "__main__":
    run()