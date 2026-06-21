import package_root
from Script import api
from Script.pattern.pattern_template import UFSTC
from Script import project_api
from Script.project_api.erase_program_fail.structs import PhysicalAddressInformation
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.api.ufs_api import *

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        logger.flow(1, 'Issue VU D011 to get open VB information, extract the L2 VB from the result.')
        response, self.health_report = project_api.issue_40FE_to_read_enhanced_health_report() 
        resp = project_api.issue_D011_clear_ssr_temp_history()
        response, self.health_report = project_api.issue_40FE_to_read_enhanced_health_report()

        if self.health_report.temperature_profile_t_37.value != 0:
            logger.error('health_report temperature_profile_t_37 != 0')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if self.health_report.temperature_profile_37_t_25.value != 0:
            logger.error('health_report temperature_profile_37_t_25 != 0')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL        
        if self.health_report.temperature_profile_25_t_0.value != 0:
            logger.error('health_report temperature_profile_25_t_0 != 0')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL   
        if self.health_report.temperature_profile_0_t_95.value != 0:
            logger.error('health_report temperature_profile_0_t_95 != 0')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL  
        if self.health_report.temperature_profile_95_t_115.value != 0:
            logger.error('health_report temperature_profile_95_t_115 != 0')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
        if self.health_report.temperature_profile_t_115.value != 0:
            logger.error('health_report temperature_profile_t_115 != 0')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.flow(2, f'power cycle')
        init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)          
        response, self.health_report = project_api.issue_40FE_to_read_enhanced_health_report()
        all_zero_temperature = True
        if (self.health_report.temperature_profile_t_37.value != 0) or (self.health_report.temperature_profile_37_t_25.value != 0)\
            or (self.health_report.temperature_profile_25_t_0.value != 0) or (self.health_report.temperature_profile_0_t_95.value != 0)\
            or (self.health_report.temperature_profile_95_t_115.value != 0) or (self.health_report.temperature_profile_t_115.value != 0):
            all_zero_temperature = False
        if all_zero_temperature:
            logger.error('all temperature = 0, after power cycle')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
