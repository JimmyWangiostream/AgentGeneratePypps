import package_root
import time
from Script import api
from typing import cast
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.ufs_api.defines.enum_define import QueryResponseCode
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
from Script.project_api.custom_vu.structs import get_nand_feature_format, set_nand_feature_format
from Script.project_api.custom_vu.set_clear_query_RPMB_erase_password_vu.structs import queryRPMBpassword, clearRPMBpassword, setRPMBpassword
from Script.project_api.custom_vu.trigger_RPMB_erase_status_vu.structs import triggerRPMBerase, queryRPMBerase
from typing import Any, Tuple, Union, cast, List
from Script.project_api.functions import print_object_info_ai


CHUNK_SIZE: int = 4 * 1024  # 4 KB

#_sdk = shared.sdk

def check_timeout(start_time: float, timeout_min: int, timeout_sec:int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60 + timeout_sec:
        return True
    else:
        return False

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.EnableMDWLSV = 0
        self.write_record = api.get_empty_write_record()
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.Total_AU_Count = self.geometry_desc.q4_total_raw_device_capacity / (self.geometry_desc.l13_segment_size * self.geometry_desc.b17_allocation_unit_size);
        

    def step1(self) -> None:
        
        logger.flow(1, 'config lun and WB')
        self.config_lun()
        _param = api.shared.param
        password = random.randint(0x1, 0xFFFFFFFFFFFFFFFF)
        logger.info(f'pattern use password: {hex(password)}')
        #password = 0x1122334455667788
        set_cmd = 0
        clear_cmd = 1
        query_cmd = 2
        logger.flow(2, 'query RPMB password status')
        rsp, querypasswordstatus_ = project_api.issue_4047_to_set_clear_query_RPMB_erase_password(password,query_cmd)
        payload = querypasswordstatus_.payload
        cast(bytes, payload)
        result:int = payload[0]
        logger.info(f'status ={result}')
        if result == 0: # password is not set
            logger.flow(3, 'clear RPMB password expect result = 1')
            rsp, clearpasswordstatus = project_api.issue_4047_to_set_clear_query_RPMB_erase_password(password,clear_cmd)
            payload = clearpasswordstatus.payload
            cast(bytes, payload)
            result = payload[0]
            logger.info(f'status ={result}')
            if result != 1:
                logger.error_lb(f'erase password when password exist')
                logger.error_fp(f'expect result = 1, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            rsp, querypasswordstatus_ = project_api.issue_4047_to_set_clear_query_RPMB_erase_password(password,query_cmd)
            payload = querypasswordstatus_.payload
            cast(bytes, payload)
            result = payload[0]
            logger.info(f'status ={result}')
            if result != 0:
                logger.error_lb(f'query password status after password erase')
                logger.error_fp(f'expect result = 0, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            logger.flow(4, f'set RPMB password {hex(password)}')
            rsp, setpasswordstatus = project_api.issue_4047_to_set_clear_query_RPMB_erase_password(password,set_cmd)
        else:
            logger.flow(3, 'clear RPMB password expect result = 0')
            rsp, clearpasswordstatus = project_api.issue_4047_to_set_clear_query_RPMB_erase_password(password,clear_cmd)
            payload = clearpasswordstatus.payload
            cast(bytes, payload)
            result = payload[0]
            logger.info(f'status ={result}')
            if result != 0:
                logger.error_lb(f'erase password when password exist')
                logger.error_fp(f'expect result = 0, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(3, 'clear RPMB password expect result = 0')
            rsp, querypasswordstatus_ = project_api.issue_4047_to_set_clear_query_RPMB_erase_password(password,query_cmd)
            payload = querypasswordstatus_.payload
            cast(bytes, payload)
            result = payload[0]
            logger.info(f'status ={result}')
            if result != 0:
                logger.error_lb(f'query password status after password erase')
                logger.error_fp(f'expect result = 0, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            logger.flow(4, f'set RPMB password {hex(password)}')
            rsp, setpasswordstatus = project_api.issue_4047_to_set_clear_query_RPMB_erase_password(password,set_cmd)
        payload = setpasswordstatus.payload
        cast(bytes, payload)
        result = payload[0]
        logger.info(f'status ={result}')
        if result != 0:
            logger.error_lb(f'set password after password erased')
            logger.error_fp(f'expect result = 0, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.flow(5, f'query RPMB password status expect result = 1')
        rsp, querypasswordstatus_ = project_api.issue_4047_to_set_clear_query_RPMB_erase_password(password,query_cmd)
        payload = querypasswordstatus_.payload
        cast(bytes, payload)
        result = payload[0]
        logger.info(f'status ={result}')
        if result != 1:
            logger.error_lb(f'query password status after password set')
            logger.error_fp(f'expect result = 1, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(6, f'write RPMB region0')
        rpmb = self.write_rpmb()
        rpmb = self.read_rpmb_should_not_0(rpmb)

        # logger.flow(8-0, 'show vb info after write rpmb')
        # self.show_vb_info(0xFF)
        # self.show_vb_valid_count_info()

        logger.flow(7, f'trigger RPMB erase expect status = 0 ')
        rsp, triggerrpmberase = project_api.issue_4048_to_trigger_RPMB_erase_status(password,0)
        logger.flow(8, f'query RPMB erase status and polling untill status = 1 ')
        rsp, rpmberasestatus = project_api.issue_4048_to_trigger_RPMB_erase_status(password,1)
        payload = triggerrpmberase.payload
        cast(bytes, payload)
        result= payload[0]
        logger.info(f'trigger RPMB erase status ={result}')
        if result != 0:
            logger.error_lb(f'trigger RPMB erase after password set')
            logger.error_fp(f'expect result = 0, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        payload = rpmberasestatus.payload
        cast(bytes, payload)
        result = payload[0]
        logger.info(f'query RPMB erase status ={result}')
        while result != 1:
            rsp, rpmberasestatus = project_api.issue_4048_to_trigger_RPMB_erase_status(password,1)
            payload = rpmberasestatus.payload
            cast(bytes, payload)
            result = payload[0]
            logger.info(f'query RPMB erase status ={result}')
            if result != 2 and result != 1 :
                logger.error_lb(f'polling RPMB erase complete after trigger erase')
                logger.error_fp(f'expect result = 1 or 2, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.flow(9, f'RPMB data should unmap, read as 0')
        rpmb = self.read_rpmb_should_0(rpmb)

        wrongpassword = password - 1
        logger.flow(10, f'clear RPMB password:{hex(password)} with input wrong password:{hex(wrongpassword)} expect result = 2')
        rsp, clearpasswordstatus = project_api.issue_4047_to_set_clear_query_RPMB_erase_password(wrongpassword,clear_cmd)
        payload = clearpasswordstatus.payload
        cast(bytes, payload)
        result = payload[0]
        logger.info(f'status ={result}')
        if result != 2:
            logger.error_lb(f'erase password when password exist and input wrong password')
            logger.error_fp(f'expect result = 2, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        # logger.flow(11, f'trigger RPMB erase with wrong password:{hex(wrongpassword)} expect status = 2 ')
        # rsp, triggerrpmberase = project_api.issue_4048_to_trigger_RPMB_erase_status(wrongpassword,0)
        # payload = triggerrpmberase.payload
        # cast(bytes, payload)
        # result= payload[0]
        # logger.info(f'trigger RPMB erase status ={result}')
        # if result != 2:
        #     logger.error_lb(f'trigger RPMB erase with wrong password after password set')
        #     logger.error_fp(f'expect result = 2, result Fail!')
        #     raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(11, f'clear RPMB password:{hex(password)} expect result = 0')
        rsp, clearpasswordstatus = project_api.issue_4047_to_set_clear_query_RPMB_erase_password(password,clear_cmd)
        payload = clearpasswordstatus.payload
        cast(bytes, payload)
        result = payload[0]
        logger.info(f'status ={result}')
        if result != 0:
            logger.error_lb(f'erase password when password exist and input wrong password')
            logger.error_fp(f'expect result = 0, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        # logger.flow(13, f'trigger RPMB erase with password:{hex(password)} after clear password expect status = 1 ')
        # rsp, triggerrpmberase = project_api.issue_4048_to_trigger_RPMB_erase_status(password,0)
        # payload = triggerrpmberase.payload
        # cast(bytes, payload)
        # result= payload[0]
        # logger.info(f'trigger RPMB erase status ={result}')
        # if result != 1:
        #     logger.error_lb(f'trigger RPMB erase after password clear')
        #     logger.error_fp(f'expect result = 1, result Fail!')
        #     raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        # logger.flow(8-0, 'show vb info before purge')
        # self.show_vb_info(0xFF)
        # self.show_vb_valid_count_info()
        # idn = api.FlagIDN.PURGE_EN
        # logger.flow(8, 'Host issue set flag idn = %d' % idn)
        # set_flag = ExecuteCMD.SetFlag().assign(idn).enqueue()
        # ExecuteCMD.send(clear_on_success=True)
        # timeout_min = 0
        # timeout_sec = 2000
        # start_time = time.time()
        # polling_cnt = 0
        # while True:
        #     if check_timeout(start_time, timeout_min, timeout_sec):
        #         raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
        #     purge_status = api.read_attribute(idn=api.AttributeIDN.PURGE_STATUS)
        #     polling_cnt += 1
        #     logger.info(f'purge status = {purge_status}, polling count = {polling_cnt}')
        #     if purge_status is 0x03:
        #         logger.info(f'purge status = {purge_status}, complete')
        #         break
        
        # logger.flow(8-1, 'show vb info after purge')
        # self.show_vb_info(0xFF)
        # self.show_vb_valid_count_info()
        pass

    def post_process(self) -> None:
        pass
    def print_next_open_vb_information(self, next_open_vb_information:project_api.NextOpenVBInformation) -> None:
        logger.info('================= Next_open_vb_information =================')
        logger.info(f'amountofvalidvb={hex(next_open_vb_information.amountofvalidvb.value)}')
        logger.info(f'DM_NORMAL_HOST_VB={hex(next_open_vb_information.DM_NORMAL_HOST_VB.value)}')
        logger.info(f'DM_NORMAL_WB_VB_0={hex(next_open_vb_information.DM_NORMAL_WB_VB_0.value)}')
        logger.info(f'DM_NORMAL_SHARE_VB_1={hex(next_open_vb_information.DM_NORMAL_SHARE_VB_1.value)}')
        logger.info(f'DM_NORMAL_SHARE_VB_0={hex(next_open_vb_information.DM_NORMAL_SHARE_VB_0.value)}')
        logger.info(f'DM_RPMB_HOST_VB={hex(next_open_vb_information.DM_RPMB_HOST_VB.value)}')
        logger.info(f'DM_NORMAL_DEFRAG_VB={hex(next_open_vb_information.DM_NORMAL_DEFRAG_VB.value)}')
        logger.info(f'DM_EM1_DEFRAG_VB={hex(next_open_vb_information.DM_EM1_DEFRAG_VB.value)}')
        logger.info(f'List={hex(next_open_vb_information.List.value)}')
        logger.info(f'PTE={hex(next_open_vb_information.PTE.value)}')
        logger.info(f'LOG={hex(next_open_vb_information.LOG.value)}')
        logger.info(f'Index={hex(next_open_vb_information.Index.value)}')
        logger.info(f'DM_RAIN_PARITY_VB={hex(next_open_vb_information.DM_RAIN_PARITY_VB.value)}')
        logger.info(f'TMP_RAIN={hex(next_open_vb_information.TMP_RAIN.value)}')
        logger.info(f'Drive_Log={hex(next_open_vb_information.Drive_Log.value)}')
        logger.info(f'Pointer={hex(next_open_vb_information.Pointer.value)}')
        logger.info(f'BBT={hex(next_open_vb_information.BBT.value)}')

        return   
    def get_and_print_next_open_vb_information(self, openvbtype: int) -> project_api.NextOpenVBInformation:
        rsp, next_open_vb_information = project_api.issue_40DC_to_get_next_open_vb_information(openvbtype)
        self.print_next_open_vb_information(next_open_vb_information)
        return next_open_vb_information  
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
    def print_open_vb_information(self, open_vb_information:project_api.OpenVBInformation) -> None:
        logger.info('================= open_vb_information =================')
        logger.info(f'Byte[{open_vb_information.L2_Open_logical_VB_Host_TLC_number.start_offset}:{open_vb_information.L2_Open_logical_VB_Host_TLC_number.end_offset}]: L2_Open_logical_VB_Host_TLC_number = {open_vb_information.L2_Open_logical_VB_Host_TLC_number.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_L2_Open_logical_VB_Host_TLC.start_offset}:{open_vb_information.first_free_physical_page_of_L2_Open_logical_VB_Host_TLC.end_offset}]: first_free_physical_page_of_L2_Open_logical_VB_Host_TLC = {open_vb_information.first_free_physical_page_of_L2_Open_logical_VB_Host_TLC.value}')
        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC.start_offset}:{open_vb_information.open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC.end_offset}]: open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC = {open_vb_information.open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC.start_offset}:{open_vb_information.first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC.end_offset}]: first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC = {open_vb_information.first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC.value}')

        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_EM1_L2_Host.start_offset}:{open_vb_information.open_logical_VB_number_for_EM1_L2_Host.end_offset}]: open_logical_VB_number_for_EM1_L2_Host = {open_vb_information.open_logical_VB_number_for_EM1_L2_Host.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_EM1_L2_Host_VB.start_offset}:{open_vb_information.first_free_physical_page_of_EM1_L2_Host_VB.end_offset}]: first_free_physical_page_of_EM1_L2_Host_VB_ = {open_vb_information.first_free_physical_page_of_EM1_L2_Host_VB.value}')
        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_EM1_GC.start_offset}:{open_vb_information.open_logical_VB_number_for_EM1_GC.end_offset}]: open_logical_VB_number_for_EM1_GC = {open_vb_information.open_logical_VB_number_for_EM1_GC.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_EM1_GC_VB.start_offset}:{open_vb_information.first_free_physical_page_of_EM1_GC_VB.end_offset}]: first_free_physical_page_of_EM1_GC_VB = {open_vb_information.first_free_physical_page_of_EM1_GC_VB.value}')
        
        
        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_Write_Booster_WB_L2.start_offset}:{open_vb_information.open_logical_VB_number_for_Write_Booster_WB_L2.end_offset}]: open_logical_VB_number_for_Write_Booster_WB_L2 = {open_vb_information.open_logical_VB_number_for_Write_Booster_WB_L2.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_Write_Booster_WB_L2.start_offset}:{open_vb_information.first_free_physical_page_of_Write_Booster_WB_L2.end_offset}]: first_free_physical_page_of_Write_Booster_WB_L2 = {open_vb_information.first_free_physical_page_of_Write_Booster_WB_L2.value}')
        logger.info(f'Byte[{open_vb_information.open_Remap_VB_number_for_Write_Booster_WB_L2.start_offset}:{open_vb_information.open_Remap_VB_number_for_Write_Booster_WB_L2.end_offset}]: open_Remap_VB_number_for_Write_Booster_WB_L2 = {open_vb_information.open_Remap_VB_number_for_Write_Booster_WB_L2.value}')
        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_RPMB_VB.start_offset}:{open_vb_information.open_logical_VB_number_for_RPMB_VB.end_offset}]: open_logical_VB_number_for_RPMB_VB = {open_vb_information.open_logical_VB_number_for_RPMB_VB.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_RPMB_VB.start_offset}:{open_vb_information.first_free_physical_page_of_RPMB_VB.end_offset}]: first_free_physical_page_of_RPMB_VB = {open_vb_information.first_free_physical_page_of_RPMB_VB.value}')
        logger.info(f'Byte[{open_vb_information.open_Remap_VB_number_for_RPMB_VB.start_offset}:{open_vb_information.open_Remap_VB_number_for_RPMB_VB.end_offset}]: open_Remap_VB_number_for_RPMB_VB = {open_vb_information.open_Remap_VB_number_for_RPMB_VB.value}')
        
        logger.info(f'Byte[{open_vb_information.PTE_Block_VB_number_logical.start_offset}:{open_vb_information.PTE_Block_VB_number_logical.end_offset}]: PTE_Block_VB_number_logical = {open_vb_information.PTE_Block_VB_number_logical.value}')
        logger.info(f'Byte[{open_vb_information.PTE_block_First_free_physical_page.start_offset}:{open_vb_information.PTE_block_First_free_physical_page.end_offset}]: PTE_block_First_free_physical_page = {open_vb_information.PTE_block_First_free_physical_page.value}')
        return 

    def get_and_print_open_vb_information(self) -> project_api.OpenVBInformation:
        rsp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        self.print_open_vb_information(open_vb_information)
        return open_vb_information    
    def show_vb_info(self, group:int)-> int:
        retval = 0
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'access_mode': {'pos': 6, 'len': 2, 'mask': 0x3}, 
            'dirty': {'pos': 8, 'len': 1, 'mask': 0x1}, 
        }
        response, rep_data = get_vb_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data)):
            if self.fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break

            ftl_vb_list_data.update({vb : {k: (((rep_data[vb*4]|rep_data[vb*4+1]<<8) >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        used_mlc_cout = 0
        
        logger.info(f'[show all vb info at begin]')
        for vb, vb_info in ftl_vb_list_data.items():
            last_type = vb_info['group']
            dirtybit = vb_info['dirty']
            logger.info(f'[vb = {vb}, group type = {last_type}, dirtybit = {dirtybit}]')
            if last_type == group:
                return vb
        return retval
    
    def compare_first_4k_bytes(self,payload_a: bytes, payload_b: bytes) -> bool:
        """回傳兩個 `bytes` 變數前 4 KB 是否相同。"""
        a_head: bytes = payload_a[:CHUNK_SIZE]
        b_head: bytes = payload_b[:CHUNK_SIZE]
        return a_head == b_head 
    
    def config_lun(self) -> None:
        selector = 0x00
        length = 0xE6
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
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /2)
                    #desc.units[unit_idx].l4_num_alloc_units = 8092
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == self.TestEM1Lun:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /2)
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
    def write_rpmb(self)-> RPMB:
        access_vendor_mode()
        vuc_clear_rpmb_key(RPMBRegion.REGION_0)            
        rpmb = RPMB(RPMBRegion.REGION_0)
        key_is_cleared = False

        for i in range(1):
            key_is_cleared = False                
            #project_api.issue_D079_Clear_RPMB_Key(region=0)

            rpmb = RPMB(RPMBRegion.REGION_0)
            try:
                write_counter = rpmb.rpmb_read_counter()
            except SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
                key_is_cleared = True
                logger.info("Flow = RPMB key is cleared")
                rpmb.rpmb_key_programming()
                
            rpmb.rpmb_write_data(0, 4)
            rpmb.rpmb_read_data(0, 2)
        if not key_is_cleared:
            logger.error("RPMB key is not cleared")
            raise SPEC_ASSERT_RPMB_KEY_NOT_CLEARED
        return rpmb
    
    def read_rpmb_should_not_0(self,rpmb:RPMB)-> RPMB:
        #vuc_clear_rpmb_key(RPMBRegion.REGION_0)            
        resp = rpmb.rpmb_read_data(0, 4)
        chunks: List[bytes] = []
        for lba in range(4):
            chunks.append(bytes(resp.data[lba*512+228:lba*512+484]))
        data_payload = bytearray()
        for chunk in chunks:
            data_payload.extend(chunk)
        if all(b == 0 for b in data_payload):
            logger.error("RPMB data should not cleared")
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        return rpmb
    def read_rpmb_should_0(self,rpmb:RPMB)-> RPMB:
        #vuc_clear_rpmb_key(RPMBRegion.REGION_0)            
        resp = rpmb.rpmb_read_data(0, 4)
        data_payload = resp.data[228:484]
        if not all(b == 0 for b in data_payload):
            logger.error("RPMB data is not cleared")
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        return rpmb
    def show_vb_valid_count_info(self)-> None:
        vb_valid_count_list_data_format = {
            'value': {'pos': 0, 'len': 32, 'mask': 0xffffffff}, 
        }
        response, rep_data = get_vb_valid_cnt_info()
        dumpfile("rep_valid_data.bin", bytearray(rep_data))
        ftl_vb_valid_count_list_data = dict()

        for vb in range(len(rep_data)):
            if self.fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break
            ftl_vb_valid_count_list_data.update({vb : {k: (((rep_data[vb*4] | rep_data[vb*4 +1] << 8 | rep_data[vb*4 +2] << 16 | rep_data[vb*4 +3] << 24) >> v['pos']) & v['mask']) for k, v in vb_valid_count_list_data_format.items()}})
        
        for vb, vb_info in ftl_vb_valid_count_list_data.items():
            validcnt = vb_info['value']
            logger.info(f'[vb = {vb}, valid count = {validcnt}]')
            if validcnt != 0:
                logger.info(f'[has node vb = {vb}, valid count = {validcnt}]')
        return
run = Pattern().run
if __name__ == "__main__":
    run()