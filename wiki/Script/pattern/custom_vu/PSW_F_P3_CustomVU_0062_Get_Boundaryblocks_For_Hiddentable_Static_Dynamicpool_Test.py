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
        self.test_4004()
        pass
    def get_all_vb_cnt(self) -> VBCount:
        offset = 2560
        rsp_data = project_api.get_block_read_count_table()
        return VBCount(rsp_data[offset:offset+36])    
    def test_4004(self)->None:
        flash_setting = get_flash_setting()
        ce_num = flash_setting.Max_Fdevice
        rsp , get_cs_ics_info_description = project_api.issue_4087_get_ics_cs_info_description()
        dumpfile('get_cs_ics_info_description.bin', get_cs_ics_info_description.payload)
        rsp, get_boundary_blocks= project_api.issue_4004_get_boundaryblocks_for_hiddentable_static_dynamicpool()
        dumpfile('get_boundary_blocks.bin', get_boundary_blocks.payload)
        total_vb = read_fw_value('gUfsApiStruct.ftl->addr_rule.geometry.total_vb')
        print(f'total_vb = {total_vb}')   
        lc_per_page = read_fw_value('gUfsApiStruct.ftl->addr_rule.geometry.lc_per_page')
        print(f'lc_per_page = {lc_per_page}')   
        bbtmax_revoke_cnt = read_fw_value('gUfsApiStruct.ftl->bbt.max_revoke_cnt')
        print(f'bbtmax_revoke_cnt = {bbtmax_revoke_cnt}')# 25
        #debug
        hidden_bound = 0
        for ce in range(ce_num):
            for plane in range (6): 
                plane_num = plane#ce * plane + plane
                read_fw_value_string = 'gUfsApiStruct.ftl->bbt.bbt_info_ce['+ str(ce) +'].bbt_info[' + str(plane_num) + '].hidden_bound'
                # hidden_bound  -> compare_value = 0xFFFF
                tmp_cnt = cast(int ,read_fw_value(read_fw_value_string))

                logger.info(f'{read_fw_value_string} = {tmp_cnt}')
                compare_value = int.from_bytes(get_boundary_blocks.payload[2*plane_num:2*plane_num+2], 'little') 
                # ENG3, cause start from 0
                compare_value += 1
                if tmp_cnt == 0:
                    tmp_cnt = 0xFFFF + 1
                # ENG3 E
                if compare_value != tmp_cnt:
                    logger.error_fp(f'compare_value = {compare_value} != {tmp_cnt}')
                    #continue
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                    pass

        spare_bound = read_fw_value('gUfsApiStruct.ftl->bbt.pivot') #5 = ICS START 可以使用( as table), but實際上hidden + spare = 0~4, 因此show 4 (不含)
        #
        spare_bound_from_vu = 0
        logger.info(f'spare_bound = {spare_bound}')
        start_offset = 48 * 1
        for ce in range(ce_num):
            for plane_num in range (6): 
                compare_value = int.from_bytes(get_boundary_blocks.payload[start_offset+2*plane_num:start_offset+2*plane_num+2], 'little') 
                # ENG3 , cause start from 0
                spare_bound_from_vu = compare_value
                compare_value += 1  
                # ENG3 E              
                if compare_value != spare_bound:
                    logger.error_fp(f'compare_value = {compare_value} != {spare_bound}')
                    #continue
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                    pass

        ics_bound = read_fw_value('gUfsApiStruct.ftl->bbt.last_bbs_vb')  #  = ics vb 個數  = last_bbs_vb - spare_bound
        logger.info(f'ics_bound = {ics_bound}')
        start_offset = 48 * 2
        for ce in range(ce_num):
            for plane_num in range (6): 
                compare_value = int.from_bytes(get_boundary_blocks.payload[start_offset+2*plane_num:start_offset+2*plane_num+2], 'little') 
                if compare_value != ics_bound:
                    logger.error_fp(f'compare_value = {compare_value} != {ics_bound}')
                    #continue
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                    pass


        table_bound = read_fw_value('gUfsApiStruct.ftl->bbt.last_tbl_pool_vb') 
        logger.info(f'table_bound = {table_bound}')        
        start_offset = 48 * 3
        for ce in range(ce_num):
            for plane_num in range (6): 
                compare_value = int.from_bytes(get_boundary_blocks.payload[start_offset+2*plane_num:start_offset+2*plane_num+2], 'little') 
                if compare_value != table_bound:
                    logger.error_fp(f'compare_value = {compare_value} != {table_bound}')
                    #continue
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                    pass
                
        last_slc_pool_vb = read_fw_value('gUfsApiStruct.ftl->bbt.last_slc_pool_vb')
        print(f'last_slc_pool_vb = {last_slc_pool_vb}')
        logger.info(f'last_slc_pool_vb = {last_slc_pool_vb}')        
        start_offset = 48 * 4
        for ce in range(ce_num):
            for plane_num in range (6): 
                compare_value = int.from_bytes(get_boundary_blocks.payload[start_offset+2*plane_num:start_offset+2*plane_num+2], 'little') 
                if compare_value != last_slc_pool_vb:
                    logger.error_fp(f'compare_value = {compare_value} != {last_slc_pool_vb}')
                    #continue
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                    pass
                
        dynamic_bound0 = read_fw_value('gUfsApiStruct.ftl->bbt.user_floor') # 451 = table + data
        logger.info(f'dynamic_bound0 = {dynamic_bound0}')        
        start_offset = 48 * 5
        for ce in range(ce_num):
            for plane_num in range (6): 
                # 461 - spare
                compare_value = int.from_bytes(get_boundary_blocks.payload[start_offset+2*plane_num:start_offset+2*plane_num+2], 'little') 
                if (compare_value - spare_bound_from_vu) != dynamic_bound0:
                    logger.error_fp(f'compare_value = {(compare_value - spare_bound_from_vu)} != {dynamic_bound0}')
                    #continue
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                    pass
        dynamic_bound = read_fw_value('gUfsApiStruct.ftl->bbt.user_ceil')
        logger.info(f'dynamic_bound = {dynamic_bound}')        
        start_offset = 48 * 6
        for ce in range(ce_num):
            for plane_num in range (6): 
                compare_value = int.from_bytes(get_boundary_blocks.payload[start_offset+2*plane_num:start_offset+2*plane_num+2], 'little') 
                if (compare_value - spare_bound_from_vu) != dynamic_bound:
                    logger.error_fp(f'compare_value = {(compare_value - spare_bound_from_vu)} != {dynamic_bound}')
                    #continue
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
                    pass

        bad_blk_cnt = 0
        for ce in range(ce_num):
            for plane in range (6): 
                plane_num = plane#ce * plane + plane
                read_fw_value_string = 'gUfsApiStruct.ftl->bbt.bbt_info_ce['+ str(ce) +'].bbt_info[' + str(plane_num) + '].bad_blk_cnt'
                tmp_cnt = cast(int,read_fw_value(read_fw_value_string))
                logger.info(f'{read_fw_value_string} = {tmp_cnt}')
                bad_blk_cnt = bad_blk_cnt + int(tmp_cnt)
      
        logger.info(f'bad_blk_cnt = {bad_blk_cnt}')
        pass
    def step1(self) -> None:              
        pass
    def post_process(self) -> None:
        pass
    



run = Pattern().run
if __name__ == "__main__":
    run()