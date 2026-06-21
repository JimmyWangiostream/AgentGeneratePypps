import package_root
import time
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

from dataclasses import is_dataclass, asdict
from typing import Any, Mapping

#_sdk = shared.sdk

class Pattern(UFSTC):
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
        

    def check_timeout(self,start_time: float, timeout_min: int) -> bool:
        current_time = time.time()
        if (current_time - start_time) >= timeout_min * 60:
            return True
        else:
            return False
    def step1(self) -> None:

        logger.flow('1-0', 'disable Media Scan') 
        hw_setting = api.HwSetting.get_instance()
        hw_setting.update_from_device()
        medium_scan_setting_bk = hw_setting.get_local_val(api.HwSettingField.MEDIUM_SCAN_TRIGGER_TIME)
        hw_setting.set_to_device(field = api.HwSettingField.MEDIUM_SCAN_TRIGGER_TIME, val= 0x80)

        check_tlcl2 = False
        check_em1 =False
        logger.flow(1, 'VU C08C disable and enable MDWLSV')     
        response = project_api.issue_C08C_to_EnDis_MDWLSV(self.disableMDWLSV)  
        response = project_api.issue_C08C_to_EnDis_MDWLSV(self.EnableMDWLSV)  
        logger.flow('1-1', 'VU 0x4029 get MDWLSV Offset')
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,60, 4)
        MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        logger.flow('1-2', 'check table reset')
        self.check_mdwlsv_all_zero(MDWLSV_info)
        for i in range(2):
            logger.flow(2, 'config lun and WB')
            self.config_lun()
            wlsv_default = 0
            write10 = ExecuteCMD.Write10()
            cur_lba = 0
            tlc_ce_page = self.flash_setting.Plane_Per_Die * 4 * 3
            logger.info(f'tlc_ce_page = {tlc_ce_page}')
            write_len = 1
            logger.flow(3, 'write 1 tlc CE page size on normal LUN')
            write10.assign(lun=self.TestNormalLun, lba=cur_lba, length=tlc_ce_page, fua=1)
            ExecuteCMD.enqueue(write10)
            ExecuteCMD.send(clear_on_success=True)
            logger.flow(4, 'VU 0x4029 get MDWLSV Offset')
            response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
            project_api.print_array_tohex(data_payload,60, 4)
            MDWLSV_info = self.assign_MDWLSV_info(data_payload)
            response, data_payload = project_api.issue_4022_to_get_NAND_feature(0,0x7F)
            project_api.print_array_tohex(data_payload,60, 4)
            get_nand_feature = self.assign_get_nand_feature_info(data_payload)
            logger.flow(5, f'VU 0x4022 get nand feature address 0x7F P3 = {get_nand_feature.P3.value}')
            rsp, previos_payload = get_previous_info()
            project_api.print_array_tohex(previos_payload,60, 4)
            if previos_payload[0] == 1:
                check_tlcl2 = True
            else:
                check_tlcl2 = False
            logger.flow(6, f'Check last program module is TLC L2, result is {check_tlcl2}')
            logger.flow(7, 'Write 1 lba size on EM1 LUN')
            write10.assign(lun=self.TestEM1Lun, lba=cur_lba, length=write_len, fua=1)
            ExecuteCMD.enqueue(write10)
            ExecuteCMD.send(clear_on_success=True)
            
            
            logger.flow(8, 'VU 0x4029 get MDWLSV Offset')
            response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
            project_api.print_array_tohex(data_payload,60, 4)
            MDWLSV_info = self.assign_MDWLSV_info(data_payload)
            tlc_l2_offset = MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value
            logger.info(f'Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset = {MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value}')
            if check_tlcl2 == True:
                logger.flow(9, 'Check CE0 MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset should equal to P3 of step5')
                if MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value == wlsv_default or MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value != get_nand_feature.P3.value:
                    logger.error_lb(f'write tlc l2 , then write em1 l2')
                    logger.error_fp(f'expect tlc l2 has wlsv offset, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            response, data_payload = project_api.issue_4022_to_get_NAND_feature(0,0x7F)
            project_api.print_array_tohex(data_payload,60, 4)
            get_nand_feature = self.assign_get_nand_feature_info(data_payload)
            logger.flow(10, f'VU 0x4022 get nand feature address 0x7F P3 = {get_nand_feature.P3.value}')
            
            rsp, previos_payload = get_previous_info()
            project_api.print_array_tohex(previos_payload,60, 4)
            if previos_payload[0] == 4:
                check_em1 = True
            else:
                check_em1 = False
            logger.flow(11, f'Check last program module is EM1, result is {check_em1}')
            #_, open_vb_info = get_open_vb_info()
            logger.flow(12, 'Write 1 lba size on normal LUN (L1)')
            write10.assign(lun=self.TestNormalLun, lba=cur_lba, length=write_len, fua=1)
            ExecuteCMD.enqueue(write10)
            ExecuteCMD.send(clear_on_success=True)
            logger.flow(13, 'VU 0x4029 get MDWLSV Offset')
            response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
            project_api.print_array_tohex(data_payload,60, 4)
            MDWLSV_info = self.assign_MDWLSV_info(data_payload)
            EM1_offset = MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value
            logger.info(f'Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset = {MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value}')
            if check_em1 == True:
                logger.flow(14, 'Check CE0 MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset should equal to P3 of step10')
                if MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value == wlsv_default or get_nand_feature.P3.value != MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value:
                    logger.error_lb(f'write EM1 l2 , then write L1')
                    logger.error_fp(f'expect EM1 l2 has wlsv offset, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(15, 'VU C08C disable MDWLSV')
            response = project_api.issue_C08C_to_EnDis_MDWLSV(self.disableMDWLSV)  
            
            logger.flow(16, 'VU 0x4029 get MDWLSV Offset')
            response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
            project_api.print_array_tohex(data_payload,60, 4)
            MDWLSV_info = self.assign_MDWLSV_info(data_payload)
            if MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value != EM1_offset or MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value != tlc_l2_offset:
                logger.error_lb(f'write tlc l2 and em1 , then disable MDWLSV')
                logger.error_fp(f'expect tlc 2 and EM1 l2 has same wlsv offset, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            logger.flow(17, 'VU C08C enable MDWLSV')
            response = project_api.issue_C08C_to_EnDis_MDWLSV(self.EnableMDWLSV)  
            logger.flow(18, 'VU 0x4029 get MDWLSV Offset')
            response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
            project_api.print_array_tohex(data_payload,60, 4)
            MDWLSV_info = self.assign_MDWLSV_info(data_payload)
            logger.flow('18-1', 'Check table reset')
            self.check_mdwlsv_all_zero(MDWLSV_info)
        write_record = api.get_empty_write_record()
        _param = api.shared.param
        start_time = time.time()
        timeout_min = 10
        disable_status = False
        
        logger.flow('19', 'random write read + random enable or disable MDWLSV  should not timeout occur')
        while True:
            if self.check_timeout(start_time, timeout_min):
                break
            testlun = random.randint(0, 3)
            cmd_count = random.randint(10, 32)
            min_lun = 0
            max_lun = 0
            min_lba = 0
            max_lba = _param.gLUCapacity[testlun]
            min_size = api.BLOCK4K_SIZE_64M_BYTE
            max_size = api.BLOCK4K_SIZE_128M_BYTE
            api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        need_compare=True, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)
            if random.randint(1, 10) > 3:
                logger.flow('19-1', 'VU C08C enable MDWLSV')
                response = project_api.issue_C08C_to_EnDis_MDWLSV(self.EnableMDWLSV)  
                if disable_status == True:
                    logger.flow('19-2', 'VU 0x4029 get MDWLSV Offset check table after disable and enable MDWLSV')
                    response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
                    project_api.print_array_tohex(data_payload,60, 4)
                    MDWLSV_info = self.assign_MDWLSV_info(data_payload)
                    self.check_mdwlsv_all_zero(MDWLSV_info)
                disable_status = False
            if random.randint(1, 10) > 6:
                logger.flow('19-3', 'VU C08C disable MDWLSV')
                response = project_api.issue_C08C_to_EnDis_MDWLSV(self.disableMDWLSV) 
                disable_status = True
        hw_setting.set_to_device(field = api.HwSettingField.MEDIUM_SCAN_TRIGGER_TIME, val= medium_scan_setting_bk)
        
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
        self.print_object_info_ai(self.MDWLSV_info)
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
            #desc.header.l18_num_shared_write_booster_buffer_alloc_units = 0x1000

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
    def print_object_info_ai(self, object: Any) -> None:
        logger.info(f'================= [{object.__class__.__name__}]=================')
        fields = [
            (name, field) for name, field in object.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        fields.sort(key=lambda kv: kv[1].start_offset)
        for name, field in fields:
            logger.info(
                f'Byte[{field.start_offset}:{field.end_offset}]: {name} = {field.value}'
            )
run = Pattern().run
if __name__ == "__main__":
    run()