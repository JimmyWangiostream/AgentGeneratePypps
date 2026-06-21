import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api import shared
from Script.lib import sdk_lib as lib
import random
from Script.api.exception import *
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from typing import cast

#_sdk = shared.sdk

class Pattern(UFSTC):
    def pre_process(self) -> None:
        cfg_desc_list = api.get_config_descriptors()
        for cfg_desc in cfg_desc_list:
            cfg_desc = cast(api.ConfigDescriptor310, cfg_desc)
            logger.info("")
            self.printout_config_desc_header(cfg_desc.header)
            for unit_desc in cfg_desc.units:
                self.printout_config_desc_unit(unit_desc)
        self.region_id = 0
        self.config_region_num = 4
        self.rpmb = api.RPMB(self.region_id)
        selector = 0x00
        length = 0xE6
        #config 4 region
        if (self.config_region_num > 0):
            for index in range(1):
                cmd = ExecuteCMD.WriteDescriptor()
                cmd.assign(api.DescriptorIDN.CONFIGURATION, index, selector, length)

                #desc = api.ConfigDescriptor310()
                desc = cast(api.ConfigDescriptor310, cfg_desc_list[0])
                #desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
                desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE
                if(self.config_region_num == 1):
                    desc.header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE
                elif(self.config_region_num == 2):
                    desc.header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE | api.RPMBRegionEnable.REGION_1_ENABLE
                elif(self.config_region_num == 3):
                    desc.header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE | api.RPMBRegionEnable.REGION_1_ENABLE | api.RPMBRegionEnable.REGION_2_ENABLE
                elif(self.config_region_num == 4):
                    desc.header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE | api.RPMBRegionEnable.REGION_1_ENABLE | api.RPMBRegionEnable.REGION_2_ENABLE | api.RPMBRegionEnable.REGION_3_ENABLE
                #desc.header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE | api.RPMBRegionEnable.REGION_1_ENABLE | api.RPMBRegionEnable.REGION_2_ENABLE | api.RPMBRegionEnable.REGION_3_ENABLE
                #desc.header.b12_rpmb_region0_size = 1
                desc.header.b13_rpmb_region1_size = 1
                desc.header.b14_rpmb_region2_size = 1
                desc.header.b15_rpmb_region3_size = 1
                cmd.set_desc(desc)
                ExecuteCMD.enqueue(cmd)
                ExecuteCMD.send()
            # descrpmb = api.get_rpmb_unit_descriptor()
            # rpmb_unit_desc = cast(api.RPMBUnitDescriptor310, descrpmb)
            # logger.info(f"  {rpmb_unit_desc.b9_rpmb_region_enable=}")
            # logger.info(f"  {rpmb_unit_desc.b19_rpmb_region0_size=}")
            # logger.info(f"  {rpmb_unit_desc.b20_rpmb_region1_size=}")
            # logger.info(f"  {rpmb_unit_desc.b21_rpmb_region2_size=}")
            # logger.info(f"  {rpmb_unit_desc.b22_rpmb_region3_size=}")
            cfg_desc_list_new = api.get_config_descriptors()
            for cfg_desc in cfg_desc_list_new:
                cfg_desc = cast(api.ConfigDescriptor310, cfg_desc)
                logger.info("")
                self.printout_config_desc_header(cfg_desc.header)
                for unit_desc in cfg_desc.units:
                    self.printout_config_desc_unit(unit_desc)
        # else:
        #     for index in range(1):
        #         cmd = ExecuteCMD.WriteDescriptor()
        #         cmd.assign(api.DescriptorIDN.CONFIGURATION, index, selector, length)

        #         desc = cast(api.ConfigDescriptor310, cfg_desc_list[0])
        #         #desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
        #         desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE
        #         desc.header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE
        #         desc.header.b13_rpmb_region1_size = 0
        #         desc.header.b14_rpmb_region2_size = 0
        #         desc.header.b15_rpmb_region3_size = 0
        #         cmd.set_desc(desc)
        #         ExecuteCMD.enqueue(cmd)
        #         ExecuteCMD.send()
            
        #     cfg_desc_list_new = api.get_config_descriptors()
        #     for cfg_desc in cfg_desc_list_new:
        #         cfg_desc = cast(api.ConfigDescriptor310, cfg_desc)
        #         logger.info("")
        #         self.printout_config_desc_header(cfg_desc.header)
        #         for unit_desc in cfg_desc.units:
        #             self.printout_config_desc_unit(unit_desc)
        pass

    def printout_config_desc_header(self, header: api.ConfigDescriptorHeader) -> None:
        header = cast(api.ConfigDescriptorHeader310, header)
        logger.info(f"{header.__class__.__name__}")
        logger.info(f"  {header.b0_length=}")
        logger.info(f"  {header.b1_descriptor_idn=}")
        logger.info(f"  {header.b2_conf_desc_continue=}")
        logger.info(f"  {header.b3_boot_enable=}")
        logger.info(f"  {header.b4_descr_access_en=}")
        logger.info(f"  {header.b5_init_power_mode=}")
        logger.info(f"  {header.b6_high_priority_lun=}")
        logger.info(f"  {header.b7_secure_removal_type=}")
        logger.info(f"  {header.b8_init_active_icc_level=}")
        logger.info(f"  {header.w9_periodic_rtc_update=}")
        logger.info(f"  {header.b11_hpb_control=}")
        logger.info(f"  {header.b12_rpmb_region_enable=}")
        logger.info(f"  {header.b13_rpmb_region1_size=}")
        logger.info(f"  {header.b14_rpmb_region2_size=}")
        logger.info(f"  {header.b15_rpmb_region3_size=}")
        logger.info(f"  {header.b16_write_booster_buffer_preserve_user_space_en=}")
        logger.info(f"  {header.b17_write_booster_buffer_type=}")
        logger.info(f"  {header.l18_num_shared_write_booster_buffer_alloc_units=}")

    def printout_config_desc_unit(self, unit: api.ConfigDescriptorUnit) -> None:
        unit = cast(api.ConfigDescriptorUnit310, unit)
        logger.info(f"{unit.__class__.__name__}")
        logger.info(f"  {unit.b0_lu_enable=}")
        logger.info(f"  {unit.b1_boot_lun_id=}")
        logger.info(f"  {unit.b2_lu_write_protect=}")
        logger.info(f"  {unit.b3_memory_type=}")
        logger.info(f"  {unit.l4_num_alloc_units=}")
        logger.info(f"  {unit.b8_data_reliability=}")
        logger.info(f"  {unit.b9_logical_block_size=}")
        logger.info(f"  {unit.b10_provisioning_type=}")
        logger.info(f"  {unit.w11_context_capabilities=}")
        logger.info(f"  {unit.w16_lu_max_active_hpb_region=}")
        logger.info(f"  {unit.w18_hpb_pinned_region_start_idx=}")
        logger.info(f"  {unit.w20_num_hpb_pinned_regions=}")
        logger.info(f"  {unit.l22_lu_num_write_booster_buffer_alloc_units=}")


    def step1(self) -> None:
        logger.flow(1, 'Host issue D078 to set RPMB writecounter')
        set_writecounter = 100
        set_region = 0
        
        for index in range(self.config_region_num):
            set_region = index
            if index ==0:
                #vuc_clear_rpmb_key(RPMBRegion.REGION_0)                
                project_api.issue_D079_Clear_RPMB_Key(region=index)
                rpmb = RPMB(RPMBRegion.REGION_0)
            if index ==1:
                #vuc_clear_rpmb_key(RPMBRegion.REGION_1)   
                project_api.issue_D079_Clear_RPMB_Key(region=index)
                rpmb = RPMB(RPMBRegion.REGION_1)    
            if index ==2:
                #vuc_clear_rpmb_key(RPMBRegion.REGION_2)         
                project_api.issue_D079_Clear_RPMB_Key(region=index)          
                rpmb = RPMB(RPMBRegion.REGION_2)
            if index ==3:
                #vuc_clear_rpmb_key(RPMBRegion.REGION_3)   
                project_api.issue_D079_Clear_RPMB_Key(region=index)
                rpmb = RPMB(RPMBRegion.REGION_3)


            try:
                write_counter = rpmb.rpmb_read_counter()
            except SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
                key_is_cleared = True
                logger.info("Flow = RPMB key is cleared")
                rpmb.rpmb_key_programming()

            # project_api.issue_D078_to_set_RPMB_WriteCounter(write_counter = set_writecounter, region = set_region)
            # # #vuc_set_writecounter(RPMBRegion.REGION_0,set_writecounter)
            # write_counter = rpmb.rpmb_read_counter()
            # if write_counter != set_writecounter :
            #     raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        set_region = 0
        for index in range(self.config_region_num):
            if index ==0:
                rpmb = RPMB(RPMBRegion.REGION_0)
            if index ==1:
                rpmb = RPMB(RPMBRegion.REGION_1)    
            if index ==2:              
                rpmb = RPMB(RPMBRegion.REGION_2)
            if index ==3:
                rpmb = RPMB(RPMBRegion.REGION_3)
            set_writecounter = random.randint(1,0xFFFFFFFF)
            project_api.issue_D078_to_set_RPMB_WriteCounter(write_counter = set_writecounter, region = index)
            #vuc_set_writecounter(RPMBRegion.REGION_0,set_writecounter)
            write_counter = rpmb.rpmb_read_counter()
            if write_counter != set_writecounter :
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        #project_api.issue_D079_Clear_RPMB_Key(region=self.region_id)
        for index in range(self.config_region_num):
            set_region = index
            if index ==0:
                #vuc_clear_rpmb_key(RPMBRegion.REGION_0)
                project_api.issue_D079_Clear_RPMB_Key(region=index)
                rpmb = RPMB(RPMBRegion.REGION_0)
            if index ==1:
                #vuc_clear_rpmb_key(RPMBRegion.REGION_1)
                project_api.issue_D079_Clear_RPMB_Key(region=index)
                rpmb = RPMB(RPMBRegion.REGION_1)    
            if index ==2:
                #vuc_clear_rpmb_key(RPMBRegion.REGION_2)   
                project_api.issue_D079_Clear_RPMB_Key(region=index)             
                rpmb = RPMB(RPMBRegion.REGION_2)
            if index ==3:
                #vuc_clear_rpmb_key(RPMBRegion.REGION_3)
                project_api.issue_D079_Clear_RPMB_Key(region=index)
                rpmb = RPMB(RPMBRegion.REGION_3)


            try:
                write_counter = rpmb.rpmb_read_counter()
            except SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
                key_is_cleared = True
                logger.info("Flow = RPMB key is cleared")
                rpmb.rpmb_key_programming()
            write_counter = rpmb.rpmb_read_counter()
            if write_counter != 0:
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        
        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()