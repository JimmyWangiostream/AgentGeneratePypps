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
        self.flash_setting = api.get_flash_setting()
        self.CE = self.flash_setting.FLH_Quantity * (BIT0 << self.flash_setting.Parallel)
        self.default_dict = {  
            0x150: 0x3,
            0x350: 0x1,
            0x050: 0x4,
            0x250: 0x1,
        } #NEED TO GET DEAFULT FIRST
        # 2026-05-16 11:43:31 - INFO - addr: 336 , value: 0
        # 2026-05-16 11:43:31 - INFO - addr: 848 , value: 0
        # 2026-05-16 11:43:31 - INFO - addr: 80 , value: 226
        # 2026-05-16 11:43:31 - INFO - addr: 592 , value: 254
        #ask fw

        self.force_crack_dict = {  
            0x150: 0x0,
            0x350: 0x0,
            0x050: 0xFF,
            0x250: 0xFF,
        }
        pass
    def check_all_die_nand_status(self,expect_result:int)-> None:
        data = project_api.issue_40E6_to_check_nand_die_crack()
        for ce in range(self.CE):
            logger.info(f'die = {ce}, result = {data[ce]}')
            if data[ce] != expect_result:
                logger.error_lb(f'Check die = {ce} =result')
                logger.error_fp(f'Expect die = {ce} result = {expect_result}, but = {data[ce]}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
    def step1(self) -> None:
        #get default value need to ask fw the parameters I used is correct or not.
        _, self.get_trim = project_api.issue_4084_to_get_NAND_trim(target_addr=list(self.force_crack_dict.keys()))
        for addr, item in zip(self.force_crack_dict.keys(), self.get_trim.TrimValue):
            logger.info(f"addr: {addr} , value: {item.value}")

        logger.flow(1, 'Issue VU 40E6 and check value = 0 (no crack).')
        self.check_all_die_nand_status(expect_result = 0)

        logger.flow(2, 'power cycle')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = False)
        
        for addr, value in self.force_crack_dict.items():
            logger.flow(3, 'Set trim to create crack.')
            logger.info(f"addr: {hex(addr)} , set value: {value}")
            set_crack_dict = {addr : value}
            print(set_crack_dict)
            #project_api.issue_C084_to_set_NAND_trim(set_dict=set_crack_dict)

            logger.flow(4, 'Issue VU 40E6 and check value = 1 (crack).')
            self.check_all_die_nand_status(expect_result = 1)

            logger.flow(5, 'power cycle')
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = False)
            
            #fw said hardware reset will clear. and after i send 40E6 fw will do hardware reset , so is this step required?
            logger.flow(5, 'Issue C084 to recover the trim value') 
            set_default_dict = {addr :self.default_dict[addr]}
            logger.info(f"addr: {hex(addr)} , set value: {self.default_dict[addr]}")
            print(set_default_dict)
            #project_api.issue_C084_to_set_NAND_trim(set_dict=set_default_dict)

            logger.flow(6, 'Issue VU 40E6 and check value = 0 (no crack).')
            self.check_all_die_nand_status(expect_result = 0)

            logger.flow(7, 'power cycle')
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = False)

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
