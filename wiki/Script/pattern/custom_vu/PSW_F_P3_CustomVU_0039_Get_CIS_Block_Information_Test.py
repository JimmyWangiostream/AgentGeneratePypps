import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from typing import cast
from Script.api import shared
from Script.api.ufs_api import *
from Script.api.cmd_seq import QueryResponse
from Script.api.ufs_api.vendor_cmd.structs import FwGeometry
from typing import Callable
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_data_in_vcmd
from typing import List

class Pattern(UFSTC):
    def pre_process(self) -> None:
        # physical_ch_cnt = read_fw_value('gUfsApiStruct.ftl->addr_rule.geometry.physical_ch_cnt')
        # physical_ch_cnt_1 = cast(int,read_fw_value('gUfsApiStruct.ftl->addr_rule.geometry.physical_ch_cnt')) + 1
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        flashsetting = api.get_flash_setting()
        self.CE = flashsetting.FLH_Quantity * (BIT0 << flashsetting.Parallel)
        self.plane_per_die = plane_per_die = flashsetting.Plane_Per_Die

        pass
    def step1(self) -> None:
  
        logger.flow(1, 'Send VU 40B9 to get cis block information ')
        data = project_api.issue_40B9_to_get_cis_block_Information() 
        
        logger.flow(2, 'Check physical_blk_number_of_cis_vb')
        
        self.fw_code_physical_address = project_api.get_FW_code_physical_address_information()
        cis_vb = self.fw_code_physical_address.CISCode1.Block.value
        self.compare_value(data.physical_blk_number_of_cis_vb.value,cis_vb, "physical_blk_number_of_cis_vb")
        
        logger.flow(3, 'Check die_number_of_the_STC_copy')
        cis_ce = self.fw_code_physical_address.CISCode1.CE.value
        self.compare_value(data.die_number_of_the_STC_copy.value,cis_ce, "die_number_of_the_STC_copy")

        logger.flow(4, 'Check physical_blk_number_of_the_STC_copy')
        
        self.compare_value(data.physical_blk_number_of_the_STC_copy.value,cis_vb, "physical_blk_number_of_the_STC_copy")

        cis1_plane = self.fw_code_physical_address.CISCode1.Plane.value
        logger.flow(5, 'Check plane_number_of_the_STC_copy')
        self.compare_value(data.plane_number_of_the_STC_copy.value,cis1_plane, "plane_number_of_the_STC_copy")
        logger.flow(6, 'Check bitmap_of_the_copies_pending_on_refresh')
        self.compare_value(data.bitmap_of_the_copies_pending_on_refresh.value,0, "bitmap_of_the_copies_pending_on_refresh")
        logger.flow(7, 'Check if_cis0_is_bad_blk')
        self.compare_value(data.if_cis0_is_bad_blk.value,0, "if_cis0_is_bad_blk")
        logger.flow(8,'Check if_cis1_is_bad_blk')
        self.compare_value(data.if_cis1_is_bad_blk.value,0, "f_cis1_is_bad_blk")
        logger.flow(9, 'Check if_cis2_is_bad_blk')
        self.compare_value(data.if_cis2_is_bad_blk.value,0xFF, "if_cis2_is_bad_blk")
        logger.flow(10, 'Check if_cis3_is_bad_blk')
        self.compare_value(data.if_cis3_is_bad_blk.value,0xFF, "if_cis3_is_bad_blk")
        erase_cnt_for_hidden_physical_block = []
        
        for idx in range(8):
            hidden_blk_ec = int.from_bytes(self.flash_setting_buffer[2284 + idx*4 : 2284 + (idx+1)*4], 'little')
            erase_cnt_for_hidden_physical_block.append(hidden_blk_ec)
            

        logger.flow(11, 'Check cis0_ec_count')
        logger.flow(11, 'Check cis1_ec_count')

        erase_cnt_for_hidden_physical_block = []
        for idx in range(8):
            hidden_blk_ec = int.from_bytes(self.flash_setting_buffer[2284 + idx*4 : 2284 + (idx+1)*4], 'little')
            erase_cnt_for_hidden_physical_block.append(hidden_blk_ec)
        
        
        hidden_info  = []
        for i in range(8):
            value = cast(int,api.read_fw_value(f"gUfsApiStruct.ftl->hidden_area.address[{i}].u16"))
            logger.info(f'idx={i}, value = {value}')
            block = value & 0x1FFF
            ce = value >> 13
            hidden_info.append((block,ce))

        
        cis0_ce = self.fw_code_physical_address.CISCode1.CE.value
        cis0_block = (self.fw_code_physical_address.CISCode1.Block.value << 3) + self.fw_code_physical_address.CISCode1.Plane.value
        cis1_ce = self.fw_code_physical_address.CISCode2.CE.value
        cis1_block = (self.fw_code_physical_address.CISCode2.Block.value << 3) + self.fw_code_physical_address.CISCode2.Plane.value
        for index, (block, ce) in enumerate(hidden_info):
                if block == cis0_block and ce == cis0_ce:
                    cis0_index = index
                    logger.info(f'cis0 match = {cis0_index}')
                if block == cis1_block and ce == cis1_ce:
                    cis1_index = index
                    logger.info(f'cis1 match = {cis1_index}')
        logger.info(f'cis0 index = {cis0_index}, cis1 index = {cis1_index}')
        self.compare_value(data.cis0_ec_count.value,erase_cnt_for_hidden_physical_block[cis0_index], "cis0_ec_count")
        self.compare_value(data.cis1_ec_count.value,erase_cnt_for_hidden_physical_block[cis1_index], "cis1_ec_count")
        
        logger.flow(12, 'Check cis2_ec_count')
        self.compare_value(data.cis2_ec_count.value,0xFFFFFFFF, "cis2_ec_count")
        logger.flow(13, 'Check cis3_ec_count')
        self.compare_value(data.cis3_ec_count.value,0xFFFFFFFF, "cis3_ec_count")


        logger.flow(14, 'Check cis_copy_used_to_load_FE_bank')
        value = cast(int,api.read_fw_value("gbyUseCode"))
        value = (value == 3)
        self.compare_value(data.cis_copy_used_to_load_FE_bank.value, value, "cis_copy_used_to_load_FE_bank")

        logger.flow(15, 'Check cis_copy_used_to_load_DM_bank')
        self.compare_value(data.cis_copy_used_to_load_DM_bank.value,value, "cis_copy_used_to_load_DM_bank")
        code_start_page = cast(int,api.read_fw_value("gUfsApiStruct.ftl->fvl[0]->fpl->code_start_page"))

        logger.flow(16, 'Check fw_image_page_start_index')
        self.compare_value(data.fw_image_page_start_index.value,code_start_page, "fw_image_page_start_index")

        logger.flow(17, 'Check fw_image_page_end_index')
        code_end_page = code_start_page + 12 -1
        self.compare_value(data.fw_image_page_end_index.value,code_end_page, "fw_image_page_end_index")

        logger.flow(18, 'Check bank_page_start_index')
        bank_start_page = code_start_page + 12
        self.compare_value(data.bank_page_start_index.value,bank_start_page, "bank_page_start_index")

        logger.flow(19, 'Check bank_page_end_index ')
        value = cast(int,api.read_fw_value("gby_code_bank_count"))
        bank_end_page = code_start_page + 12 + value 
        self.compare_value(data.bank_page_end_index.value,bank_end_page, "bank_page_end_index")
        
        pass
    def compare_value(self,value:int,expect_value:int, desc:str="") -> None:
        if value != expect_value:
            logger.error(f'Expect {desc}={expect_value}, but = {value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'{desc} val = {value}')
    def post_process(self) -> None:
        pass
    

run = Pattern().run
if __name__ == "__main__":
    run()