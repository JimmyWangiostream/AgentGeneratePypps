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
from Script.project_api.block_budget.structs import GetCSICSInfoDescription, GetBoundaryBlocksForHiddenTableStaticDynamicPool, VBCount
import inspect
from typing import cast

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.test_4087()
        pass
    def get_all_vb_cnt(self) -> VBCount:
        offset = 2560
        rsp_data = project_api.get_block_read_count_table()
        return VBCount(rsp_data[offset:offset+36])    
    def test_4087(self) -> None:
        flash_setting = get_flash_setting()
        ce_num = flash_setting.Max_Fdevice
        logger.flow(1,"get 4087 data")
        rsp , get_cs_ics_info_description = project_api.issue_4087_get_ics_cs_info_description()
        logger.flow(2,"get 4004 data")
        rsp, get_boundary_blocks= project_api.issue_4004_get_boundaryblocks_for_hiddentable_static_dynamicpool()
        logger.flow(2,"get fw value for compare")
        dumpfile('get_boundary_blocks.bin', get_boundary_blocks.payload)
        total_vb = read_fw_value('gUfsApiStruct.ftl->addr_rule.geometry.total_vb')
        print(f'total_vb = {total_vb}')   
        lc_per_page = read_fw_value('gUfsApiStruct.ftl->addr_rule.geometry.lc_per_page')
        print(f'lc_per_page = {lc_per_page}')   
        bbtmax_revoke_cnt = read_fw_value('gUfsApiStruct.ftl->bbt.max_revoke_cnt')
        print(f'bbtmax_revoke_cnt = {bbtmax_revoke_cnt}')# 25
        revoke_cnt = read_fw_value('gUfsApiStruct.ftl->bbt.revoke_cnt')
        print(f'bbtmax_revoke_cnt = {revoke_cnt}')#       

        compare_value = get_cs_ics_info_description.number_of_ics_table.value
        expected_value = get_boundary_blocks.ics_bound_ce0plane0.value - get_boundary_blocks.spare_bound_ce0plane0.value
        if compare_value != expected_value:
            logger.error_fp(f'compare_value = {compare_value} != {expected_value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        compare_value = get_cs_ics_info_description.max_number_of_cs.value
        expected_value = int(total_vb) - get_cs_ics_info_description.number_of_ics_table.value  # type: ignore
        if compare_value != expected_value:
            logger.error_fp(f'compare_value = {compare_value} != {expected_value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL        
        
        bad_blk_cnt = 0
        for ce in range(ce_num):
            for plane in range (6): 
                plane_num = plane#ce * plane + plane
                read_fw_value_string = 'gUfsApiStruct.ftl->bbt.bbt_info_ce['+ str(ce) +'].bbt_info[' + str(plane_num) + '].bad_blk_cnt'
                tmp_cnt = read_fw_value(read_fw_value_string)
                logger.info(f'{read_fw_value_string} = {tmp_cnt}')
                bad_blk_cnt = bad_blk_cnt + int(tmp_cnt)  # type: ignore
        
        logger.info(f'bad_blk_cnt = {bad_blk_cnt}')
        compare_value = get_cs_ics_info_description.number_of_early_bb_at_t0.value
        expected_value = bad_blk_cnt
        if compare_value != expected_value:
            logger.error_fp(f'compare_value = {compare_value} != {expected_value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL        
        total_vb = read_fw_value('gUfsApiStruct.ftl->addr_rule.geometry.total_vb')
        logger.info(f'total_vb = {total_vb}')   
        hidden_blk_cnt = 0
        for ce in range(ce_num):
            for plane in range (6): 
                plane_num = plane#ce * plane + plane
                read_fw_value_string = 'gUfsApiStruct.ftl->bbt.bbt_info_ce['+ str(ce) +'].bbt_info[' + str(plane_num) + '].hidden_bound'
                # hidden_bound  -> compare_value = 0xFFFF
                hidden_blk_cnt += cast(int ,read_fw_value(read_fw_value_string))        
        logger.info(f'hidden_blk_cnt = {hidden_blk_cnt}')   
        ics_blk = 0
        ics_blk = get_boundary_blocks.ics_bound_ce0plane0.value - get_boundary_blocks.spare_bound_ce0plane0.value
        logger.info(f'ics_blk = {ics_blk}')  
        compare_value = get_cs_ics_info_description.remianing_cs_at_run_time.value # all vb - ics - hidden

        expected_value = cast(int,total_vb) - ics_blk - (get_boundary_blocks.spare_bound_ce0plane0.value + 1) - cast(int, revoke_cnt) #get_boundary_blocks.dynamic_bound0_ce0plane0.value
        if compare_value != expected_value:
            logger.error_fp(f'compare_value = {compare_value} != {expected_value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL         
        pass
    def step1(self) -> None:              
        pass
    def post_process(self) -> None:
        pass
    



run = Pattern().run
if __name__ == "__main__":
    run()