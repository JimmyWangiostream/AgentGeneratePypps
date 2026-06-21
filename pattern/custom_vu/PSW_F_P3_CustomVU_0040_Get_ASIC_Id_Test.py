import package_root
from Script import api
from Script.api.util.functions import dumpfile
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig, get_flash_setting
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api import read_fw_value
import time
from Script.project_api.set_string_description.structs import SerialNumberString, ProductNameString, ASICId



class Pattern(UFSTC):
    def pre_process(self) -> None:
        
        pass
    def get_ascii_str(self, raw_byte:int) -> str:
        value = raw_byte
        length = (value.bit_length() + 7) // 8
        buffer = value.to_bytes(length, "little")
        ascii_str = buffer.decode("ascii")
        return ascii_str        
    
    def step1(self) -> None:
        flash_setting = get_flash_setting()
        ce_num = flash_setting.Max_Fdevice
        logger.flow(1,"issue 40B3 to get asic id")
        response, ascid = project_api.issue_40B3_to_get_asic_id()
        logger.flow(2,"Check if ascid.nand_id_item_count.value = ce_num")
        if(ascid.nand_id_item_count.value != ce_num):
            logger.error_fp(f'vu rsp nand_id_item_count {ascid.nand_id_item_count} != device ce {ce_num}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.flow(3,"Check if ascid.controller_and_nand_type_ascii.value = 'PS8329 B68S'")
        ascii_str = self.get_ascii_str(ascid.controller_and_nand_type_ascii.value)
        expected_ascii_str = 'PS8329 B68S'
        if(expected_ascii_str != ascii_str):
            logger.error_fp(f'vu rsp controller_and_nand_type_ascii {ascid.controller_and_nand_type_ascii} != ascii_str {ascii_str}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        expected_nand_id = 0x2cd30832e8361200
        logger.flow(4,"Check if each ce ascid.die_idx.value = ce index")
        print(f'ascii str = {ascid.controller_and_nand_type_ascii}, ascid.die_idx_0.value = {ascid.die_idx_0.value}, ascid.nand_flash_id_idx0.value = {ascid.nand_flash_id_idx0.value}, \
                     ascid.die_idx_1 {ascid.die_idx_1.value}, ascid.nand_flash_id_idx1.value = {ascid.nand_flash_id_idx1.value}, ascid.die_idx_2 {ascid.die_idx_2.value}, ascid.nand_flash_id_idx2 {ascid.nand_flash_id_idx2.value},\
                        ascid.die_idx_3 {ascid.die_idx_3.value}, ascid.nand_flash_id_idx3 {ascid.nand_flash_id_idx3.value}')
        logger.flow(5,"	Check if each ce ascid.nand_flash_id_idx0.value = expected_nand_id (0x2cd30832e8361200)")
        if ce_num >= 1:
            expected_idx = 0
            if(ascid.die_idx_0.value != expected_idx):
                logger.error_fp(f'vu rsp ascid.die_idx_0 {ascid.die_idx_0.value} != expected_idx {expected_idx}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            if(ascid.nand_flash_id_idx0.value != expected_nand_id):
                logger.error_fp(f'vu rsp ascid.die_idx_0 {ascid.nand_flash_id_idx0.value} != expected_idx {expected_idx}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if ce_num >= 2:
            expected_idx = 1
            if(ascid.die_idx_1.value != expected_idx):
                logger.error_fp(f'vu rsp ascid.die_idx_1 {ascid.die_idx_1.value} != expected_idx {expected_idx}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            if(ascid.nand_flash_id_idx1.value != expected_nand_id):
                logger.error_fp(f'vu rsp ascid.die_idx_1 {ascid.nand_flash_id_idx1.value} != expected_idx {expected_idx}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if ce_num >= 4:
            expected_idx = 2
            if(ascid.die_idx_2.value != expected_idx):
                logger.error_fp(f'vu rsp ascid.die_idx_2 {ascid.die_idx_2.value} != expected_idx {expected_idx}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            if(ascid.nand_flash_id_idx2.value != expected_nand_id):
                logger.error_fp(f'vu rsp ascid.die_idx_2 {ascid.nand_flash_id_idx2.value} != expected_idx {expected_idx}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            expected_idx = 3
            if(ascid.die_idx_3.value != expected_idx):
                logger.error_fp(f'vu rsp ascid.die_idx_3 {ascid.die_idx_3.value} != expected_idx {expected_idx}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            if(ascid.nand_flash_id_idx3.value != expected_nand_id):
                logger.error_fp(f'vu rsp ascid.nand_flash_id_idx3 {ascid.nand_flash_id_idx3.value} != expected_idx {expected_idx}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL  
        print('compare 40B3 pass')             
        pass
    def post_process(self) -> None:
        pass
    
    def get_fw_configuration(self) -> project_api.GetFwConfiguration:
        #response, data_payload = project_api.issue_40C0_to_get_mConfig_data(specific_VB, 0x0)
        #response, data_payload, fw_value_by_vu = project_api.issue_4001_to_get_fw_version()
        response, data_payload, fw_configuration_by_vu = project_api.issue_408A_to_get_fw_version()
        return fw_configuration_by_vu


run = Pattern().run
if __name__ == "__main__":
    run()