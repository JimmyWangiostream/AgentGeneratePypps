import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.ufs_api.defines.enum_define import QueryResponseCode
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api import shared
from Script.lib import sdk_lib as lib
import random
from Script.api.ufs_api import *
from Script.api.exception import *
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from typing import cast
from Script.project_api.custom_vu.structs import get_nand_feature_format, set_nand_feature_format
from Script.project_api.custom_vu.mdwlsv_vu.structs import MDWLSV_format
from Script.project_api.functions import print_object_info_ai

from dataclasses import is_dataclass, asdict
from typing import Any, Mapping

#_sdk = shared.sdk

class Pattern(UFSTC):
    def make_payload(self) -> bytearray:
        return bytearray([0x01, 0x02, 0x10, 0x20, 0x22, 0x23, 0x24, 0x40, 0x58, 0x7F, 0x80, 0x81, 0x83, 0x84, 0x86, 0x87, 0x90, 0x93, 0x96, 0xA0, 0xA1, 0xA2, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xAB, 0xB1, 0xB2, 0xB3, 0xB4, 0xDA, 0xE1, 0xE2, 0xE3, 0xE7])

    def pre_process(self) -> None:
        self.disableMDWLSV = 1
        self.EnableMDWLSV = 0
        self.write_record = api.get_empty_write_record()
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting = api.get_flash_setting()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestBootA = 1
        self.TestBootB = 2
        self.TestEM1Lun = 3
        self.Total_AU_Count = self.geometry_desc.q4_total_raw_device_capacity / (self.geometry_desc.l13_segment_size * self.geometry_desc.b17_allocation_unit_size);
        


    def step1(self) -> None:
        
        feature_addr_list: bytearray = self.make_payload()
        CE = 0
        ce_num = self.flash_setting.Max_Fdevice
        logger.flow(1, f'Get NAND feature address value and set the value test')  
        step = 2
        for CE in range(ce_num):
            for idx, b in enumerate(feature_addr_list):
                #logger.info(f"idx={idx:02d}  value=0x{b:02X}")
                logger.flow(step, f'VU 4022 get feature address 0x{b:02X} on CE{CE}')     
                response, data_payload = project_api.issue_4022_to_get_NAND_feature(CE,b)
                #project_api.print_array_tohex(data_payload,60, 4)
                get_nand_feature = self.assign_get_nand_feature_info(data_payload)
                print_object_info_ai(get_nand_feature)
                logger.info(f"Result = {get_nand_feature.result.value}, Die = {get_nand_feature.die.value}, P1 = {get_nand_feature.P1.value}, P2 = {get_nand_feature.P2.value}, P3 = {get_nand_feature.P3.value}, P4 = {get_nand_feature.P4.value}")
                step += 1
                logger.flow(step, f'VU 4023 set feature address 0x{b:02X} as default value')     
                if b != 0x58:
                    response, data_payload = project_api.issue_4023_to_set_NAND_feature(CE,b,get_nand_feature.P1.value,get_nand_feature.P2.value,get_nand_feature.P3.value,get_nand_feature.P4.value)
                    q_value = int.from_bytes(data_payload[:4], byteorder="little")
                    logger.info(f"Result = {q_value}")
                    step += 1
            
            logger.flow(step, f'VU 4022 CE{CE} get feature address 01 as recover value')     
            response, data_payload = project_api.issue_4022_to_get_NAND_feature(CE,0x01)
            project_api.print_array_tohex(data_payload,60, 4)
            get_nand_feature = self.assign_get_nand_feature_info(data_payload)
            print_object_info_ai(get_nand_feature)
            logger.info(f"P1 = {get_nand_feature.P1.value}, P2 = {get_nand_feature.P2.value}, P3 = {get_nand_feature.P3.value}, P4 = {get_nand_feature.P4.value}")
            feature01_P1 = get_nand_feature.P1.value
            feature01_P2 = get_nand_feature.P2.value
            feature01_P3 = get_nand_feature.P3.value
            feature01_P4 = get_nand_feature.P4.value

            testP1 = random.randint(0x1, 0xFF)
            testP2 = random.randint(0x1, 0xFF)
            testP3 = random.randint(0x1, 0xFF)
            testP4 = random.randint(0x1, 0xFF)
            logger.info(f"Set P1 = {testP1}, P2 = {testP2}, P3 = {testP3}, P4 = {testP4}")
            response, data_payload = project_api.issue_4023_to_set_NAND_feature(CE,0x01,testP1,testP2,testP3,testP4)
            project_api.print_array_tohex(data_payload,60, 4)
            set_nand_feature = self.assign_set_nand_feature_info(data_payload)
            response, data_payload = project_api.issue_4022_to_get_NAND_feature(CE,0x01)
            project_api.print_array_tohex(data_payload,60, 4)
            get_nand_feature = self.assign_get_nand_feature_info(data_payload)
            print_object_info_ai(get_nand_feature)
            logger.info(f"P1 = {get_nand_feature.P1.value}, P2 = {get_nand_feature.P2.value}, P3 = {get_nand_feature.P3.value}, P4 = {get_nand_feature.P4.value}")

            
            response, data_payload = project_api.issue_4023_to_set_NAND_feature(CE,0x01,feature01_P1,feature01_P2,feature01_P3,feature01_P4)
            
            response, data_payload = project_api.issue_4022_to_get_NAND_feature(CE,0x01)
            project_api.print_array_tohex(data_payload,60, 4)
            get_nand_feature = self.assign_get_nand_feature_info(data_payload)
            print_object_info_ai(get_nand_feature)
            feature01_P1 = get_nand_feature.P1.value
            feature01_P2 = get_nand_feature.P2.value
            feature01_P3 = get_nand_feature.P3.value
            feature01_P4 = get_nand_feature.P4.value
            logger.info(f"P1 = {get_nand_feature.P1.value}, P2 = {get_nand_feature.P2.value}, P3 = {get_nand_feature.P3.value}, P4 = {get_nand_feature.P4.value}")

        # w.data = data1 * 1
        # w.assign(lun=1, lba=1, length=1, fua=1).set_option(manual_mode=True).enqueue()
        
        # ExecuteCMD.send(clear_on_success=True)
        
        # logger.info('Step 0: config')
        
        # cfg_desc_list = api.get_config_descriptors()
        # selector = 0x00
        # length = 0xE6
        # for index in range(1):
        #     cmd = ExecuteCMD.WriteDescriptor()
        #     cmd.assign(api.DescriptorIDN.CONFIGURATION, index, selector, length)

        #     #desc = api.ConfigDescriptor310()
        #     desc = cast(api.ConfigDescriptor310, cfg_desc_list[0])
        #     #desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
        #     desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE
            
        #     cmd.set_desc(desc)
        #     ExecuteCMD.enqueue(cmd)
        #     ExecuteCMD.send()
        # response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        # project_api.print_array_tohex(data_payload,60, 4)
        # MDWLSV_info = self.assign_MDWLSV_info(data_payload)

        # logger.info('Step 1: Enable MDWLSV')
        # response = project_api.issue_C08C_to_EnDis_MDWLSV(self.EnableMDWLSV)  
        # logger.info('[data1 4KB]')
        # data1 = bytearray([0x5B] * 4096)
        # data1[0] = 0x66
        # data1[-1] = 0x77
        # logger.print_buffer(data1)
        # w = ExecuteCMD.Write10()
        # w.data = data1 * 1
        # w.assign(lun=0, lba=0, length=1, fua=1).set_option(manual_mode=True).enqueue()
        
        # ExecuteCMD.send(clear_on_success=True)

        # w.data = data1 * 64 
        # w.assign(lun=0, lba=1, length=64, fua=1).set_option(manual_mode=True).enqueue()
        
        # ExecuteCMD.send(clear_on_success=True)
        # response, data_payload = project_api.issue_4022_to_get_NAND_feature(0,0x7F)
        # project_api.print_array_tohex(data_payload,60, 4)
        # get_nand_feature = self.assign_get_nand_feature_info(data_payload)
        
        # response, data_payload = project_api.issue_4022_to_get_NAND_feature(0,0x01)
        # project_api.print_array_tohex(data_payload,60, 4)
        # get_nand_feature = self.assign_get_nand_feature_info(data_payload)
        # feature01_P1 = get_nand_feature.P1.value
        # feature01_P2 = get_nand_feature.P2.value
        # feature01_P3 = get_nand_feature.P3.value
        # feature01_P4 = get_nand_feature.P4.value

        # testP1 = random.randint(0x1, 0xFF)
        # testP2 = random.randint(0x1, 0xFF)
        # testP3 = random.randint(0x1, 0xFF)
        # testP4 = random.randint(0x1, 0xFF)
        # response, data_payload = project_api.issue_4023_to_set_NAND_feature(0,0x01,testP1,testP2,testP3,testP4)
        # project_api.print_array_tohex(data_payload,60, 4)
        # set_nand_feature = self.assign_set_nand_feature_info(data_payload)
        # response, data_payload = project_api.issue_4022_to_get_NAND_feature(0,0x01)
        # project_api.print_array_tohex(data_payload,60, 4)
        # get_nand_feature = self.assign_get_nand_feature_info(data_payload)

        
        # response, data_payload = project_api.issue_4023_to_set_NAND_feature(0,0x01,feature01_P1,feature01_P2,feature01_P3,feature01_P4)

        # w.data = data1 * 1
        # w.assign(lun=1, lba=1, length=1, fua=1).set_option(manual_mode=True).enqueue()
        
        # ExecuteCMD.send(clear_on_success=True)

        # response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        # project_api.print_array_tohex(data_payload,60, 4)
        # MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        
        # response = project_api.issue_C08C_to_EnDis_MDWLSV(self.disableMDWLSV)  
        # response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        # project_api.print_array_tohex(data_payload,60, 4)
        # MDWLSV_info = self.assign_MDWLSV_info(data_payload)

        pass

    def post_process(self) -> None:
        pass
    def assign_MDWLSV_info(self, data_payload:bytearray) -> MDWLSV_format:
        self.MDWLSV_info = MDWLSV_format()
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value=data_payload[2]            
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value=data_payload[3]        
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_offset.value=data_payload[6]          
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_SB0_offset.value=data_payload[7]      
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_offset.value=data_payload[10]        
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_SB0_offset.value=data_payload[11]    
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value=data_payload[14]    
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_SB0_offset.value=data_payload[15]
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_offset.value=data_payload[18]    
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_SB0_offset.value=data_payload[19]
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_offset.value=data_payload[22]        
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_SB0_offset.value=data_payload[23]    
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_offset.value=data_payload[26]          
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_SB0_offset.value=data_payload[27]      
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_offset.value=data_payload[30]      
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_SB0_offset.value=data_payload[31]  
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_offset.value=data_payload[34]      
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_SB0_offset.value=data_payload[35]  
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_offset.value=data_payload[38]          
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_SB0_offset.value=data_payload[39]      
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_EM1_GC_offset.value=data_payload[42]            
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_EM1_GC_SB0_offset.value=data_payload[43]        
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value=data_payload[46]    
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_SB0_offset.value=data_payload[47]
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_offset.value=data_payload[50]        
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_SB0_offset.value=data_payload[51]    
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_offset.value=data_payload[54]    
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_SB0_offset.value=data_payload[55]
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_offset.value=data_payload[58]        
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_SB0_offset.value=data_payload[59]
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value=data_payload[2+1*60]            
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value=data_payload[3+1*60]        
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_offset.value=data_payload[6+1*60]          
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_SB0_offset.value=data_payload[7+1*60]      
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_offset.value=data_payload[10+1*60]        
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_SB0_offset.value=data_payload[11+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value=data_payload[14+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_SB0_offset.value=data_payload[15+1*60]
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_offset.value=data_payload[18+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_SB0_offset.value=data_payload[19+1*60]
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_offset.value=data_payload[22+1*60]        
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_SB0_offset.value=data_payload[23+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_offset.value=data_payload[26+1*60]          
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_SB0_offset.value=data_payload[27+1*60]      
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_offset.value=data_payload[30+1*60]      
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_SB0_offset.value=data_payload[31+1*60]  
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_offset.value=data_payload[34+1*60]      
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_SB0_offset.value=data_payload[35+1*60]  
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_offset.value=data_payload[38+1*60]          
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_SB0_offset.value=data_payload[39+1*60]      
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_EM1_GC_offset.value=data_payload[42+1*60]            
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_EM1_GC_SB0_offset.value=data_payload[43+1*60]        
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value=data_payload[46+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_SB0_offset.value=data_payload[47+1*60]
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_offset.value=data_payload[50+1*60]        
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_SB0_offset.value=data_payload[51+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_offset.value=data_payload[54+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_SB0_offset.value=data_payload[55+1*60]
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_offset.value=data_payload[58+1*60]        
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_SB0_offset.value=data_payload[59+1*60]  
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value=data_payload[2+2*60]            
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value=data_payload[3+2*60]        
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_offset.value=data_payload[6+2*60]          
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_SB0_offset.value=data_payload[7+2*60]      
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_offset.value=data_payload[10+2*60]        
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_SB0_offset.value=data_payload[11+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value=data_payload[14+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_SB0_offset.value=data_payload[15+2*60]
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_offset.value=data_payload[18+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_SB0_offset.value=data_payload[19+2*60]
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_offset.value=data_payload[22+2*60]        
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_SB0_offset.value=data_payload[23+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_offset.value=data_payload[26+2*60]          
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_SB0_offset.value=data_payload[27+2*60]      
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_offset.value=data_payload[30+2*60]      
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_SB0_offset.value=data_payload[31+2*60]  
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_offset.value=data_payload[34+2*60]      
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_SB0_offset.value=data_payload[35+2*60]  
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_offset.value=data_payload[38+2*60]          
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_SB0_offset.value=data_payload[39+2*60]      
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_EM1_GC_offset.value=data_payload[42+2*60]            
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_EM1_GC_SB0_offset.value=data_payload[43+2*60]        
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value=data_payload[46+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_SB0_offset.value=data_payload[47+2*60]
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_offset.value=data_payload[50+2*60]        
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_SB0_offset.value=data_payload[51+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_offset.value=data_payload[54+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_SB0_offset.value=data_payload[55+2*60]
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_offset.value=data_payload[58+2*60]        
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_SB0_offset.value=data_payload[59+2*60]
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value=data_payload[2+3*60]            
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value=data_payload[3+3*60]        
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_offset.value=data_payload[6+3*60]          
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_SB0_offset.value=data_payload[7+3*60]      
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_offset.value=data_payload[10+3*60]        
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_SB0_offset.value=data_payload[11+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value=data_payload[14+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_SB0_offset.value=data_payload[15+3*60]
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_offset.value=data_payload[18+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_SB0_offset.value=data_payload[19+3*60]
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_offset.value=data_payload[22+3*60]        
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_SB0_offset.value=data_payload[23+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_offset.value=data_payload[26+3*60]          
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_SB0_offset.value=data_payload[27+3*60]      
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_offset.value=data_payload[30+3*60]      
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_SB0_offset.value=data_payload[31+3*60]  
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_offset.value=data_payload[34+3*60]      
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_SB0_offset.value=data_payload[35+3*60]  
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_offset.value=data_payload[38+3*60]          
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_SB0_offset.value=data_payload[39+3*60]      
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_EM1_GC_offset.value=data_payload[42+3*60]            
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_EM1_GC_SB0_offset.value=data_payload[43+3*60]        
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value=data_payload[46+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_SB0_offset.value=data_payload[47+3*60]
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_offset.value=data_payload[50+3*60]        
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_SB0_offset.value=data_payload[51+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_offset.value=data_payload[54+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_SB0_offset.value=data_payload[55+3*60]
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_offset.value=data_payload[58+3*60]        
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_SB0_offset.value=data_payload[59+3*60]
        return self.MDWLSV_info
    def assign_get_nand_feature_info(self, data_payload:bytearray) -> get_nand_feature_format:
        self.get_nand_info_format = get_nand_feature_format()
        testbytes = data_payload[0:4]
        print(type(testbytes))
        print(type(data_payload[0:4]))
        self.get_nand_info_format.result.value = int.from_bytes(data_payload[0:4], byteorder='little')
        self.get_nand_info_format.die.value = int.from_bytes(data_payload[4:8], byteorder='little')
        self.get_nand_info_format.P1.value = int.from_bytes(data_payload[8:12], byteorder='little')
        self.get_nand_info_format.P2.value = int.from_bytes(data_payload[12:16], byteorder='little')
        self.get_nand_info_format.P3.value = int.from_bytes(data_payload[16:20], byteorder='little')
        self.get_nand_info_format.P4.value = int.from_bytes(data_payload[20:24], byteorder='little')
        return self.get_nand_info_format       
    def assign_set_nand_feature_info(self, data_payload:bytearray) -> set_nand_feature_format:
        self.set_nand_info_format = set_nand_feature_format()
        testbytes = data_payload[0:4]
        print(type(testbytes))
        print(type(data_payload[0:4]))
        self.get_nand_info_format.result.value = int.from_bytes(data_payload[0:4], byteorder='little')
        return self.set_nand_info_format       
    def config_lun(self) -> None:
        _param = shared.param
        selector = 0x00
        length = 0xE6
        self.unit_desc_idxes:List[int] = []
        for index in range(4):
            cmd = ExecuteCMD.WriteDescriptor()
            cmd.assign(api.DescriptorIDN.CONFIGURATION, index, selector, length)

            desc = api.ConfigDescriptor310()
            desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            desc.header.b3_boot_enable = api.BootEnable.BOOT_DISABLE
            desc.header.b4_descr_access_en = api.DescrAccessEn.DISABLE
            desc.header.b5_init_power_mode = api.InitPowerMode.ACTIVE
            desc.header.b6_high_priority_lun = api.HighPriorityLUN.ALL_LUN_SAME_PRIORITY
            desc.header.b7_secure_removal_type = api.SecureRemovalType.BY_PHYSICAL_ERASE
            desc.header.b8_init_active_icc_level = api.InitActiveICCLevel.LVL_00
            desc.header.w9_periodic_rtc_update = 0
            desc.header.b11_hpb_control = 0
            desc.header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.DISABLE
            desc.header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
            desc.header.l18_num_shared_write_booster_buffer_alloc_units = self.geometry_desc.l79_write_booster_buffer_max_n_alloc_units
            desc.header.l18_num_shared_write_booster_buffer_alloc_units = 0x1000

            for unit_idx in range(8):
                if index == 0 and unit_idx == self.TestNormalLun:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.NORMAL
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    #desc.units[unit_idx].l4_num_alloc_units = 8092
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == self.TestBootA:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_A
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == self.TestBootB:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_B
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == self.TestEM1Lun:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                else:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.DISABLE
                    desc.units[unit_idx].l4_num_alloc_units = 0
                    desc.units[unit_idx].b9_logical_block_size = 0

            cmd.set_desc(desc)
            ExecuteCMD.enqueue(cmd)
            ExecuteCMD.send() 
           
        for lun in range(0, _param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(DescriptorIDN.UNIT, lun)
            self.unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in self.unit_desc_idxes:
            update_descriptor(DescriptorIDN.UNIT, index, cast(QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()
        #test unit ready all enable lun
        for lun in range(_param.gMaxNumberLU):
            if  _param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
        api.write_attribute(idn=api.AttributeIDN.BOOT_LUN_EN, val=api.BootLUNID.BOOT_LUN_A)
    
    def check_mdwlsv_all_zero(self,mdwlsv_info: MDWLSV_format) -> None:
        payload = mdwlsv_info.payload
        for idx, byte_val in enumerate(payload):
            if byte_val != 0:
                logger.error_lb(f'write tlc l2 and em1 , then disable MDWLSV')
                logger.error_fp(f'expect tlc 2 and EM1 l2 has same wlsv offset, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
run = Pattern().run
if __name__ == "__main__":
    run()