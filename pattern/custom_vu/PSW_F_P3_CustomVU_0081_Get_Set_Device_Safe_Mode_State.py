import package_root
from Script import api
from Script.pattern.pattern_template import UFSTC
from Script import project_api
from Script.project_api.erase_program_fail.structs import PhysicalAddressInformation
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.pattern.sgm.mutual_fun import open_card
import random
from Script.lib.sdk_lib.user.exception import G_TIMEOUT_ALL
from Script.api.ufs_api import *

_param = shared.param
class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        # D089-Set Device Reach Safe Mode
        rsp , payload = project_api.issue_40A0_get_device_safe_mode_state()
        expected_val = 255
        logger.flow(1, f'issue 40A0 expected Val in payload[0] = {expected_val}')
        if payload[0] != expected_val:
            logger.error_fp(f'40A0 palyload[0] = {payload[0]} != {expected_val}')
        
        setting_mode = random.randint(3, 255)
        logger.flow(2, f'issue D089 set safe mode {setting_mode}, expected illegal rsp')
        
        rsp_fail = False
        try:
            rsp = project_api.issue_D089_set_safe_mode(setting_mode)
        except DLL_RESPONSE_ERROR:
            rsp_fail = True
            logger.info('send command error')
            ExecuteCMD.clear()
        if not rsp_fail:
            logger.error_fp(f'D089 with setting mode = {setting_mode} shall be fail, but rsp pass')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        rsp , payload = project_api.issue_40A0_get_device_safe_mode_state()
        expected_val = 0
        logger.flow(1, f'issue 40A0 expected Val in payload[0] = {expected_val}')
        if payload[0] != expected_val:
            logger.error_fp(f'40A0 palyload[0] = {payload[0]} != {expected_val}')        

        setting_mode = 0
        logger.flow(2, f'issue D089 set safe mode {setting_mode}')
        rsp = project_api.issue_D089_set_safe_mode(setting_mode)
        
        rsp , payload = project_api.issue_40A0_get_device_safe_mode_state()
        expected_val = 0
        logger.flow(3, f'issue 40A0 expected Val in payload[0] = {expected_val}')
        if payload[0] != expected_val:
            logger.error_fp(f'40A0 palyload[0] = {payload[0]} != {expected_val}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        setting_mode = 1
        logger.flow(4, f'issue D089 set safe mode {setting_mode}')
        rsp = project_api.issue_D089_set_safe_mode(setting_mode)
        rsp_to = False
        # shall response
        try:
            rsp , payload = project_api.issue_40A0_get_device_safe_mode_state()
        except G_TIMEOUT_ALL:
            rsp_to = True
            logger.info('send command TO')
            ExecuteCMD.clear()   
        assert_num = api.get_fw_assert_number()
        if not rsp_to:
            logger.error_fp(f'D089 with setting mode = {setting_mode} shall be TO, but not')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL  
        logger.flow(5, 'MP')
        api.MP().execute()
        api.first_init_to_max_hs_gear(link_startup_mode=_param.current_speed.link_startup_mode, ref_clk=_param.current_speed.refclk)                
        expected_val = 0
        logger.flow(5, f'issue 40A0 expected Val in payload[0] = {expected_val}')
        if payload[0] != expected_val:
            logger.error_fp(f'40A0 palyload[0] = {payload[0]} != {expected_val}')  
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL      
        pass        

        setting_mode = 2
        logger.flow(6, f'issue D089 set safe mode {setting_mode}')
        try:
            rsp = project_api.issue_D089_set_safe_mode(setting_mode)
            rsp_to = False
        except G_TIMEOUT_ALL:
            rsp_to = True
            logger.info('send command TO')
            ExecuteCMD.clear()      
        assert_num = api.get_fw_assert_number()
        if not rsp_to:
            logger.error_fp(f'D089 with setting mode = {setting_mode} shall be TO, but not')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL          
        logger.flow(7, 'MP')            
        api.MP().execute()
        api.first_init_to_max_hs_gear(link_startup_mode=_param.current_speed.link_startup_mode, ref_clk=_param.current_speed.refclk)
    def post_process(self) -> None:
        
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
