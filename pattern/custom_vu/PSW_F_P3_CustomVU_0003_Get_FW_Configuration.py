import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig, get_flash_setting
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api import read_fw_value
import time
from typing import cast

class Pattern(UFSTC):
    def pre_process(self) -> None:
        
        pass
    def get_later_bad_cnt(self) -> None:
        rsp_data = project_api.get_bad_block_erase_cnt_table()
        sub_bytes = rsp_data[2:4]
        self.latter_bad_cnt = int.from_bytes(sub_bytes, byteorder='big')
        logger.info(f'latter_bad_cnt = {self.latter_bad_cnt}')

    def step1(self) -> None:

        total_fvl = cast(int,read_fw_value('gUfsApiStruct.ftl->total_fvl'))
        print(f'total_fvl = {total_fvl}')   
        physical_ch_cnt = cast(int,read_fw_value('gUfsApiStruct.ftl->addr_rule.geometry.physical_ch_cnt'))
        print(f'physical_ch_cnt = {physical_ch_cnt}')   
        block_per_plane = cast(int,read_fw_value('gUfsApiStruct.ftl->addr_rule.geometry.block_per_plane'))
        print(f'block_per_plane = {block_per_plane}')      
        physical_plane_per_vb = cast(int,read_fw_value('gUfsApiStruct.ftl->addr_rule.physical_planes_per_vb'))
        print(f'physical_plane_per_vb = {physical_plane_per_vb}')   
        d2_page_per_block = cast(int,read_fw_value('gUfsApiStruct.ftl->addr_rule.geometry.d2_page_per_block'))
        print(f'd2_page_per_block = {d2_page_per_block}')       
        d1_page_per_block = cast(int,read_fw_value('gUfsApiStruct.ftl->addr_rule.geometry.d1_page_per_block'))
        print(f'd1_page_per_block = {d1_page_per_block}')       
        total_vb = cast(int,read_fw_value('gUfsApiStruct.ftl->addr_rule.geometry.total_vb'))
        print(f'total_vb = {total_vb}')   
        lc_per_page = cast(int,read_fw_value('gUfsApiStruct.ftl->addr_rule.geometry.lc_per_page'))
        print(f'lc_per_page = {lc_per_page}')   
        bbtmax_revoke_cnt = cast(int,read_fw_value('gUfsApiStruct.ftl->bbt.max_revoke_cnt'))
        print(f'bbtmax_revoke_cnt = {bbtmax_revoke_cnt}')   
        last_tbl_pool_vb = cast(int,read_fw_value('gUfsApiStruct.ftl->bbt.last_tbl_pool_vb'))
        print(f'last_tbl_pool_vb = {last_tbl_pool_vb}')   
        last_slc_pool_vb = cast(int,read_fw_value('gUfsApiStruct.ftl->bbt.last_slc_pool_vb'))
        print(f'last_slc_pool_vb = {last_slc_pool_vb}')   
        head_size = cast(int,read_fw_value('gUfsApiStruct.ftl->vb_list.list[0].head.size'))
        print(f'head_size = {head_size}')   


        logger.info(f'total_fvl = {total_fvl}')   
        logger.info(f'physical_ch_cnt = {physical_ch_cnt}')  
        logger.info(f'block_per_plane = {block_per_plane}')     
        logger.info(f'physical_plane_per_vb = {physical_plane_per_vb}')       
        logger.info(f'd2_page_per_block = {d2_page_per_block}')      
        logger.info(f'd1_page_per_block = {d1_page_per_block}')   
        logger.info(f'total_vb = {total_vb}')            
        logger.info(f'lc_per_page = {lc_per_page}')       
        logger.info(f'bbtmax_revoke_cnt = {bbtmax_revoke_cnt}')    
        logger.info(f'last_tbl_pool_vb = {last_tbl_pool_vb}')   
        logger.info(f'last_slc_pool_vb = {last_slc_pool_vb}')       
        logger.info(f'head_size = {head_size}')  

        fw_configuration = self.get_fw_configuration()
        dumpfile('fw_configuration.bin', fw_configuration.payload)
        
        logger.info(f'fw_configuration.TotalFieldCounts.value = {fw_configuration.TotalFieldCounts.value}')   
        logger.info(f'fw_configuration.NumberOfTotalDie.value = {fw_configuration.NumberOfTotalDie.value}')   #
        logger.info(f'fw_configuration.NumberOfChannels.value = {fw_configuration.NumberOfChannels.value}') #
        logger.info(f'fw_configuration.NumberOfBlocksPerPlane.value = {fw_configuration.NumberOfBlocksPerPlane.value}') #
        logger.info(f'fw_configuration.NumberOfPhysicalBlocks.value = {fw_configuration.NumberOfPhysicalBlocks.value}') #
        
        logger.info(f'fw_configuration.NumberOfPagesPerTlcBlock.value = {fw_configuration.NumberOfPagesPerTlcBlock.value}') #
        logger.info(f'fw_configuration.NumberOfPagesPerSlcBlock.value = {fw_configuration.NumberOfPagesPerSlcBlock.value}') #
        logger.info(f'fw_configuration.SizeOfPhysicalPage.value = {fw_configuration.SizeOfPhysicalPage.value}') #
        logger.info(f'fw_configuration.SizeOfPhysicalAddressUnit.value = {fw_configuration.SizeOfPhysicalAddressUnit.value}') #
        logger.info(f'fw_configuration.NumberOfBlocksInSuperlock.value = {fw_configuration.NumberOfBlocksInSuperlock.value}')#
        logger.info(f'fw_configuration.CountOfAllSuperlocks.value = {fw_configuration.CountOfAllSuperlocks.value}') #
        logger.info(f'fw_configuration.VPCountPerPhysicalPage.value = {fw_configuration.VPCountPerPhysicalPage.value}')#
        logger.info(f'fw_configuration.MetadataSpareSizePerKB.value = {fw_configuration.MetadataSpareSizePerKB.value}') #
        logger.info(f'fw_configuration.ECCSpareSizePerKB.value = {fw_configuration.ECCSpareSizePerKB.value}') #
        logger.info(f'fw_configuration.DMMaximumReplacedBlockCountForBBRemapPerPlane.value = {fw_configuration.DMMaximumReplacedBlockCountForBBRemapPerPlane.value}')
        logger.info(f'fw_configuration.FirstLogicalVBNumberForHostData.value = {fw_configuration.FirstLogicalVBNumberForHostData.value}')
        logger.info(f'fw_configuration.TheFirstLogVBOfStaticPool.value = {fw_configuration.TheFirstLogVBOfStaticPool.value}')
        logger.info(f'fw_configuration.TheFirstLogVBOfDynamicPool.value = {fw_configuration.TheFirstLogVBOfDynamicPool.value}')
        logger.info(f'fw_configuration.TheFirstLogVBOfTableVB.value = {fw_configuration.TheFirstLogVBOfTableVB.value}')
        logger.info(f'fw_configuration.MaxEarlyBBCountPerPlane.value = {fw_configuration.MaxEarlyBBCountPerPlane.value}')
        self.get_later_bad_cnt()
        flash_setting = get_flash_setting()
        ce_num = flash_setting.Max_Fdevice
        if fw_configuration.NumberOfTotalDie.value != ce_num:
            logger.error_fp(f'data compare fail, fw_configuration.NumberOfTotalDie.value({fw_configuration.NumberOfTotalDie.value}) != ce_num({ce_num})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL   
        if fw_configuration.NumberOfChannels.value != physical_ch_cnt:                                                                                         
            logger.error_fp(f'data compare fail, fw_configuration.NumberOfChannels.value({fw_configuration.NumberOfChannels.value}) != physical_ch_cnt({physical_ch_cnt})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL     

        if fw_configuration.NumberOfBlocksPerPlane.value != block_per_plane:
            logger.error_fp(f'data compare fail, fw_configuration.NumberOfBlocksPerPlane.value({fw_configuration.NumberOfBlocksPerPlane.value}) != block_per_plane({block_per_plane})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL                
        
        if fw_configuration.NumberOfPagesPerTlcBlock.value != d2_page_per_block:
            logger.error_fp(f'data compare fail, fw_configuration.NumberOfPagesPerTlcBlock.value({fw_configuration.NumberOfPagesPerTlcBlock.value}) != d2_page_per_block({d2_page_per_block})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL 

        if fw_configuration.NumberOfPagesPerSlcBlock.value != d1_page_per_block:
            logger.error_fp(f'data compare fail, fw_configuration.NumberOfPagesPerSlcBlock.value({fw_configuration.NumberOfPagesPerSlcBlock.value}) != d1_page_per_block({d1_page_per_block})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL    
        if fw_configuration.SizeOfPhysicalPage.value != 18352:
            logger.error_fp(f'data compare fail, fw_configuration.SizeOfPhysicalPage.value({fw_configuration.SizeOfPhysicalPage.value}) != 18352')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL                          
        if fw_configuration.SizeOfPhysicalAddressUnit.value != 16384:
            logger.error_fp(f'data compare fail, fw_configuration.SizeOfPhysicalAddressUnit.value({fw_configuration.SizeOfPhysicalPage.value}) != 16384')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL           
        if fw_configuration.NumberOfBlocksInSuperlock.value != physical_plane_per_vb:
            logger.error_fp(f'data compare fail, fw_configuration.NumberOfBlocksInSuperlock.value({fw_configuration.NumberOfBlocksInSuperlock.value}) != physical_plane_per_vb({physical_plane_per_vb})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL                                   
        if fw_configuration.CountOfAllSuperlocks.value != total_vb:
            logger.error_fp(f'data compare fail, fw_configuration.CountOfAllSuperlocks.value({fw_configuration.CountOfAllSuperlocks.value}) != total_vb({total_vb})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL 
        if fw_configuration.VPCountPerPhysicalPage.value != lc_per_page:
            logger.error_fp(f'data compare fail, fw_configuration.VPCountPerPhysicalPage.value({fw_configuration.VPCountPerPhysicalPage.value}) != lc_per_page({lc_per_page})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL                                                   
        if fw_configuration.MetadataSpareSizePerKB.value != 16:
            logger.error_fp(f'data compare fail, fw_configuration.MetadataSpareSizePerKB.value({fw_configuration.MetadataSpareSizePerKB.value}) != 16')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL                 
        if fw_configuration.ECCSpareSizePerKB.value != 456:
            logger.error_fp(f'data compare fail, fw_configuration.ECCSpareSizePerKB.value({fw_configuration.ECCSpareSizePerKB.value}) != 456')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL            
        if fw_configuration.DMMaximumReplacedBlockCountForBBRemapPerPlane.value != bbtmax_revoke_cnt:
            logger.error_fp(f'data compare fail, fw_configuration.DMMaximumReplacedBlockCountForBBRemapPerPlane.value({fw_configuration.DMMaximumReplacedBlockCountForBBRemapPerPlane.value}) != bbtmax_revoke_cnt({bbtmax_revoke_cnt})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL         
        if fw_configuration.FirstLogicalVBNumberForHostData.value != (last_tbl_pool_vb + 1):
            logger.error_fp(f'data compare fail, fw_configuration.FirstLogicalVBNumberForHostData.value({fw_configuration.FirstLogicalVBNumberForHostData.value}) != last_tbl_pool_vb + 1({last_tbl_pool_vb + 1} )')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL   
        


        if fw_configuration.TheFirstLogVBOfStaticPool.value != (last_tbl_pool_vb + 1):
            logger.error_fp(f'data compare fail, fw_configuration.TheFirstLogVBOfStaticPool.value({fw_configuration.TheFirstLogVBOfStaticPool.value}) != last_tbl_pool_vb + 1({last_tbl_pool_vb + 1} )')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL         
        

        if fw_configuration.TheFirstLogVBOfDynamicPool.value != (last_slc_pool_vb + 1):
            logger.error_fp(f'data compare fail, fw_configuration.TheFirstLogVBOfDynamicPool.value({fw_configuration.TheFirstLogVBOfDynamicPool.value}) != last_slc_pool_vb + 1({last_slc_pool_vb + 1})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL   
        if fw_configuration.TheFirstLogVBOfTableVB.value != head_size:
            logger.error_fp(f'data compare fail, fw_configuration.TheFirstLogVBOfTableVB.value({fw_configuration.TheFirstLogVBOfTableVB.value}) != head_size({head_size})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL   

        if fw_configuration.MaxGBBCount.value != self.latter_bad_cnt:
            logger.error_fp(f'data compare fail, fw_configuration.MaxGBBCount.value({fw_configuration.MaxGBBCount.value}) != latter_bad_cnt({self.latter_bad_cnt})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL                                         
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