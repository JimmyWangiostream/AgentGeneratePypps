import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from typing import Dict, List, cast, Optional
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from time import sleep
from typing import Any

ENG2_WA = True

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.fw_geometry = api.get_fw_geometry()
        _, self.debug_info = api.get_debug_info()
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        self.flash_setting = FlashSetting()
        self.flash_setting.from_bytes(self.flash_setting_buffer)
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.TestWBLun = 2
        self.write_record = api.get_empty_write_record()
        self.cis_block_bkup = project_api.issue_40B9_to_get_cis_block_Information()
        self.bbt_bkup = project_api.get_BBT2_physical_block_information()
        self.pointer_bkup = project_api.get_PT_physical_block_information()
        pass
    
    def step1(self) -> None:
        logger.flow(1, 'get original system block ec')
        FW_CIS0, FW_CIS1, BBM_Table_EC, ISP_Block_EC, Pointer_Block_EC = self.get_and_print_system_block_ec()

        logger.flow(2, 'issue D048 to set system block ec')
        set_FW_CIS0 = random.randint(1,255)
        set_FW_CIS1 = random.randint(1,255)
        set_BBM_Table_EC = random.randint(1,255)
        set_ISP_Block_EC = 0xFFFFFFFF
        set_Pointer_Block_EC = random.randint(1,255)
        logger.info(f'set FW_CIS0 = {set_FW_CIS0}')
        logger.info(f'set FW_CIS1 = {set_FW_CIS1}')
        logger.info(f'set BBM_Table_EC = {set_BBM_Table_EC}')
        logger.info(f'set ISP_Block_EC = {set_ISP_Block_EC}')
        logger.info(f'set Pointer_Block_EC = {set_Pointer_Block_EC}')
        project_api.issue_D048_to_set_FW_BBT_and_system_block_EC(set_FW_CIS0, set_FW_CIS1, set_BBM_Table_EC, set_ISP_Block_EC, set_Pointer_Block_EC)

        logger.flow(3, 'get current system block ec and check value')
        FW_CIS0, FW_CIS1, BBM_Table_EC, ISP_Block_EC, Pointer_Block_EC = self.get_and_print_system_block_ec()
        
        if FW_CIS0 != set_FW_CIS0:
            logger.error_lb(f'check FW_CIS0 after setting')
            logger.error_fp(f'expect FW_CIS0 value = {set_FW_CIS0}, current value = {FW_CIS0}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if FW_CIS1 != set_FW_CIS1:
            logger.error_lb(f'check FW_CIS1 after setting')
            logger.error_fp(f'expect FW_CIS1 value = {set_FW_CIS1}, current value = {FW_CIS1}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if BBM_Table_EC != set_BBM_Table_EC:
            logger.error_lb(f'check BBM_Table_EC after setting')
            logger.error_fp(f'expect BBM_Table_EC value = {set_BBM_Table_EC}, current value = {BBM_Table_EC}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if ISP_Block_EC != set_ISP_Block_EC:
            logger.error_lb(f'check ISP_Block_EC after setting')
            logger.error_fp(f'expect ISP_Block_EC value = {set_ISP_Block_EC}, current value = {ISP_Block_EC}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if Pointer_Block_EC != set_Pointer_Block_EC:
            logger.error_lb(f'check Pointer_Block_EC after setting')
            logger.error_fp(f'expect Pointer_Block_EC value = {set_Pointer_Block_EC}, current value = {Pointer_Block_EC}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(4, 'recover to original system block ec')
        self.recover_ec_setting()
        pass
    
    def get_and_print_system_block_ec(self) -> tuple[int, int, int, int, int]:
        cis_block = project_api.issue_40B9_to_get_cis_block_Information()
        bbt = project_api.get_BBT2_physical_block_information()
        pointer = project_api.get_PT_physical_block_information()
        
        FW_CIS0 = cis_block.cis0_ec_count.value
        FW_CIS1 = cis_block.cis1_ec_count.value
        BBM_Table_EC = bbt.erase_cnt.value
        ISP_Block_EC = 0xFFFFFFFF
        Pointer_Block_EC = pointer.erase_cnt.value
        logger.info(f'FW_CIS0 = {FW_CIS0}')
        logger.info(f'FW_CIS1 = {FW_CIS1}')
        logger.info(f'BBM_Table_EC = {BBM_Table_EC}')
        logger.info(f'ISP_Block_EC = {ISP_Block_EC}')
        logger.info(f'Pointer_Block_EC = {Pointer_Block_EC}')
        return FW_CIS0, FW_CIS1, BBM_Table_EC, ISP_Block_EC, Pointer_Block_EC
    
    def recover_ec_setting(self) -> None:
        FW_CIS0 = self.cis_block_bkup.cis0_ec_count.value
        FW_CIS1 = self.cis_block_bkup.cis1_ec_count.value
        BBM_Table_EC = self.bbt_bkup.erase_cnt.value
        ISP_Block_EC = 0xFFFFFFFF
        Pointer_Block_EC = self.pointer_bkup.erase_cnt.value        
        project_api.issue_D048_to_set_FW_BBT_and_system_block_EC(FW_CIS0, FW_CIS1, BBM_Table_EC, ISP_Block_EC, Pointer_Block_EC)

    def post_process(self) -> None:
        pass
    

run = Pattern().run
if __name__ == "__main__":
    run()