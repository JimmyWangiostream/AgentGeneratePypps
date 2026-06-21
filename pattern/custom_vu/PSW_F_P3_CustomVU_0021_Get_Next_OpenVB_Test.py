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
from Script.api.exception import *
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from typing import cast
from Script.project_api.custom_vu.structs import get_nand_feature_format, set_nand_feature_format
from Script.project_api.functions import print_object_info_ai

#_sdk = shared.sdk
used_blk_pool_slc = 16
used_blk_pool_mlc = 17
current_blk_pool_mlc = 7
current_blk_pool_slc = 6
current_l1 = 13

class Pattern(UFSTC):
    def get_all_VPCT_values(self) -> list[project_api.VPCT_values]:
        response, data_payload = project_api.issue_40C0_to_get_VPCT_description(0xFFFFFFFF, 0x0)
        dumpfile('all_VPCT_values.bin', data_payload)
        output_list = []
        num_of_vb = int.from_bytes(data_payload[0 : 4], 'little')
        for i in range(num_of_vb):
            output_list.append(project_api.VPCT_values(data_payload[4*(i+1):4*(i+1)+4]))
        return output_list
    
    def pre_process(self) -> None:
        self.write_record = api.get_empty_write_record()
        self.disableMDWLSV = 1
        self.EnableMDWLSV = 0
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.last_type = 0
        self.Total_AU_Count = self.geometry_desc.q4_total_raw_device_capacity / (self.geometry_desc.l13_segment_size * self.geometry_desc.b17_allocation_unit_size);
        self.config_lun()
    
    def step1(self) -> None:
        
        logger.info('Step 0: config')
        lun = self.TestNormalLun                 # 例：普通測試 LUN
        start_lba = 0
        total_bytes = int(self.slc_vb_size * 1)   # 完整的 SLC VB size
        cfg_desc_list = api.get_config_descriptors()
        selector = 0x00
        length = 0xE6
        for index in range(1):
            cmd = ExecuteCMD.WriteDescriptor()
            cmd.assign(api.DescriptorIDN.CONFIGURATION, index, selector, length)

            #desc = api.ConfigDescriptor310()
            desc = cast(api.ConfigDescriptor310, cfg_desc_list[0])
            #desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE
            
            cmd.set_desc(desc)
            ExecuteCMD.enqueue(cmd)
            ExecuteCMD.send()
            
        #response, data_payload = project_api.issue_40DC_to_get_next_open_vb_information(0)  
        # for vbtype in range(0,17):
        #     print(vbtype)
        #     self.next_open_vb_information_before = self.get_and_print_next_open_vb_information(vbtype)
        #project_api.print_array_tohex(data_payload,60, 4)
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=4, chunk_size=4, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=4, chunk_size=4, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'dirty': {'pos': 6, 'len': 1, 'mask': 0x1}, 
            'access_mode': {'pos': 7, 'len': 1, 'mask': 0x1}, 
        }
        response, rep_data = get_vb_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data)):
            if self.fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break
            ftl_vb_list_data.update({vb : {k: ((rep_data[vb*4] >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        used_mlc_cout = 0
        
        logger.info(f'[show all vb info at begin]')
        for vb, vb_info in ftl_vb_list_data.items():
            self.last_type = vb_info['group']
            logger.info(f'[vb = {vb}, group type = {self.last_type}]')
            
        self.next_open_vb_information_before = self.get_and_print_next_open_vb_information(0)
        if self.check_next_open_vb_information(self.next_open_vb_information_before) == False:
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        self.open_vb_information_before = self.get_and_print_open_vb_information()
        last_next_log_openvb = self.next_open_vb_information_before.LOG
        last_next_tlc_openvb = self.next_open_vb_information_before.DM_NORMAL_HOST_VB
        last_next_slc_openvb = self.next_open_vb_information_before.DM_NORMAL_SHARE_VB_0

        #tlc test
        logger.flow(1, 'TLC L2 test : get next tlc open VB A , write 1 TLC L2 vb, get current tlc open VB B')
        for testidx in range(0,2):
            logger.info(f'[write 1 tlc vb size {self.tlc_vb_size}]')
            api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=int(self.tlc_vb_size*1), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            self.next_open_vb_information_after = self.get_and_print_next_open_vb_information(0)
            #first_CE0_EM1_get_nand_feature: get_nand_feature_format = get_nand_feature_format(get_nand_feature.payload.copy())        
            if self.check_next_open_vb_information(self.next_open_vb_information_after) == False:
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            self.open_vb_information_after = self.get_and_print_open_vb_information()
            response, rep_data = get_vb_info()
            dumpfile("rep_data.bin", bytearray(rep_data))
            ftl_vb_list_data = dict()

            for vb in range(len(rep_data)):

                if self.fw_geometry.l52_total_vb_count <= vb:
                    break
                if vb *4  >= len(rep_data):
                    break
                
                ftl_vb_list_data.update({vb : {k: ((rep_data[vb*4] >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
            used_mlc_cout = 0
            for vb, vb_info in ftl_vb_list_data.items():
                if vb == last_next_tlc_openvb.value:
                    self.last_type = vb_info['group']
                    logger.info(f'[group type = {self.last_type}]')
                    if self.last_type != current_blk_pool_mlc:
                        logger.info(f'[last mlc open vb {vb} did not become current mlc L2]')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                # if vb_info['group'] == used_blk_pool_mlc:
                #     used_mlc_cout += 1
                #     logger.info(f'[used mlc vb {vb}]')
                # if vb == last_next_log_openvb.value:
                #     self.last_type = vb_info['group']
                #     print('group type = %d' % (self.last_type) )
                #     break
            
            logger.flow('1-1', f'check VB A {last_next_tlc_openvb.value} equal to VB B {self.open_vb_information_after.L2_Open_logical_VB_Host_TLC_number.value}')
            if last_next_tlc_openvb.value != self.open_vb_information_after.L2_Open_logical_VB_Host_TLC_number.value:
                logger.error_lb(f'get next tlc open VB A , write 1 TLC L2 vb, get current tlc open VB B')
                logger.error_fp(f'VB A {last_next_tlc_openvb.value} expect same as VB B {self.open_vb_information_after.L2_Open_logical_VB_Host_TLC_number.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            last_next_log_openvb = self.next_open_vb_information_after.LOG
            last_next_tlc_openvb = self.next_open_vb_information_after.DM_NORMAL_HOST_VB

        #EM1 test
        logger.flow(2, 'EM1 test : get next EM1 L2 open VB A , write 1 EM1 L2 vb, get current EM1 open VB B')
        for testidx in range(0,2):
            logger.info(f'[write 1 slc vb size {self.slc_vb_size}]')
            api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=int(self.slc_vb_size*1), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            self.next_open_vb_information_after = self.get_and_print_next_open_vb_information(0)        
            if self.check_next_open_vb_information(self.next_open_vb_information_after) == False:
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            self.open_vb_information_after = self.get_and_print_open_vb_information()
            response, rep_data = get_vb_info()
            dumpfile("rep_data.bin", bytearray(rep_data))
            ftl_vb_list_data = dict()

            for vb in range(len(rep_data)):

                if self.fw_geometry.l52_total_vb_count <= vb:
                    break
                if vb *4  >= len(rep_data):
                    break
                
                ftl_vb_list_data.update({vb : {k: ((rep_data[vb*4] >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
            used_slc_cout = 0
            for vb, vb_info in ftl_vb_list_data.items():
                if vb == last_next_slc_openvb.value:
                    self.last_type = vb_info['group']
                    logger.info(f'[group type = {self.last_type}]')
                    if self.last_type != current_blk_pool_slc:
                        logger.info(f'[last slc open vb {vb} did not become current slc L2]')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                if vb_info['group'] == used_blk_pool_slc:
                    used_slc_cout += 1
                    logger.info(f'[used slc vb {vb}]')
                # if vb == last_next_log_openvb.value:
                #     self.last_type = vb_info['group']
                #     print('group type = %d' % (self.last_type) )
                #     break
            
            logger.flow('2-1', f'check VB A {last_next_slc_openvb.value} equal to VB B {self.open_vb_information_after.open_logical_VB_number_for_EM1_L2_Host.value}')
            if last_next_slc_openvb.value != self.open_vb_information_after.open_logical_VB_number_for_EM1_L2_Host.value:
                logger.error_lb(f'get next EM1 L2 open VB A , write 1 EM1 L2 vb, get current EM1 open VB B')
                logger.error_fp(f'VB A {last_next_slc_openvb.value} expect same as VB B {self.open_vb_information_after.open_logical_VB_number_for_EM1_L2_Host.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            last_next_log_openvb = self.next_open_vb_information_after.LOG
            last_next_slc_openvb = self.next_open_vb_information_after.DM_NORMAL_SHARE_VB_0
        #L1 test
        logger.flow(3, 'L1 test: get next Small Chunk L1 open VB A , write small chunk until current L1 VB change, get current Small Chunk L1 open VB B')
        self.config_lun()
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        self.show_vb_info()
        self.next_open_vb_information_before = self.get_and_print_next_open_vb_information(0)
        if (self.check_next_open_vb_information(self.next_open_vb_information_before) == False):
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        self.open_vb_information_before = self.get_and_print_open_vb_information()
        last_next_L1_openvb = self.next_open_vb_information_before.DM_NORMAL_SHARE_VB_1
        for testidx in range(0,1):
            logger.info(f'[write 1 slc vb size {self.slc_vb_size}]')
            
            test_lba = start_lba=0
            total_len = total_size=int(self.slc_vb_size*1)
            chunk_size=api.BLOCK4K_SIZE_16K_BYTE
            l1vb_after = l1vb = self.get_dedicate_vb_group(current_l1)
            start_time = time.time()
            timeout_min = 15
            while l1vb_after == l1vb:
                if self.check_timeout(start_time, timeout_min):
                    raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
                current_last_next_l1_vb = self.write_unmap_cycle(self.TestNormalLun ,start_lba , total_size, chunk_size, last_next_L1_openvb.value)
                l1vb_after = self.get_dedicate_vb_group(current_l1)
                if l1vb == l1vb_after:
                    last_next_L1_openvb.value = current_last_next_l1_vb
            if l1vb_after != last_next_L1_openvb.value and l1vb_after != current_last_next_l1_vb :
                logger.info(f'[last L1 open vb {vb} did not become current L1]')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            self.open_vb_information_after = self.get_and_print_open_vb_information()
            logger.flow('3-1', f'check VB A {last_next_L1_openvb.value} equal to VB B {self.open_vb_information_after.L1_open_VB_S_CHUNK_logical_number.value}')
            if last_next_L1_openvb.value != self.open_vb_information_after.L1_open_VB_S_CHUNK_logical_number.value:
                logger.error_lb(f'get next Small Chunk L1 open VB A , write small chunk until current L1 VB change, get current Small Chunk L1 open VB B')
                logger.error_fp(f'VB A {last_next_L1_openvb.value} expect same as VB B {self.open_vb_information_after.L1_open_VB_S_CHUNK_logical_number.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            last_next_L1_openvb.value = current_last_next_l1_vb

        #WB test
        logger.flow(4, 'WB test: get next WB open VB A , write 1 SLC VB size on normal lun, get current WB open VB B')
        self.config_lun()
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=4, chunk_size=4, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.next_open_vb_information_before = self.get_and_print_next_open_vb_information(0)
        if (self.check_next_open_vb_information(self.next_open_vb_information_before) == False):
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        self.open_vb_information_before = self.get_and_print_open_vb_information()
        last_next_wb_openvb = self.next_open_vb_information_before.DM_NORMAL_WB_VB_0
        for testidx in range(0,2):
            logger.info(f'[write 1 slc vb size {self.slc_vb_size}]')
            api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=int(self.slc_vb_size*1), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            self.next_open_vb_information_after = self.get_and_print_next_open_vb_information(0)        
            self.check_next_open_vb_information(self.next_open_vb_information_after)
            self.open_vb_information_after = self.get_and_print_open_vb_information()
            response, rep_data = get_vb_info()
            dumpfile("rep_data.bin", bytearray(rep_data))
            ftl_vb_list_data = dict()

            for vb in range(len(rep_data)):
                if self.fw_geometry.l52_total_vb_count <= vb:
                    break
                if vb *4  >= len(rep_data):
                    break                
                ftl_vb_list_data.update({vb : {k: ((rep_data[vb*4] >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
            used_mlc_cout = 0
            for vb, vb_info in ftl_vb_list_data.items():
                if vb == last_next_wb_openvb.value:
                    self.last_type = vb_info['group']
                    logger.info(f'[group type = {self.last_type}]')
                    if self.last_type != current_blk_pool_mlc:
                        logger.info(f'[last wb open vb {vb} did not become wb current L2]')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                # if vb_info['group'] == used_blk_pool_mlc:
                #     used_mlc_cout += 1
                #     logger.info(f'[used mlc vb {vb}]')
            
            logger.flow('4-1', f'check VB A {last_next_wb_openvb.value} equal to VB B {self.open_vb_information_after.open_logical_VB_number_for_Write_Booster_WB_L2.value}')
            if last_next_wb_openvb.value != self.open_vb_information_after.open_logical_VB_number_for_Write_Booster_WB_L2.value:
                logger.error_lb(f'get next WB open VB A , write 1 SLC VB size on normal lun, get current WB open VB B')
                logger.error_fp(f'VB A {last_next_wb_openvb.value} expect same as VB B {self.open_vb_information_after.open_logical_VB_number_for_Write_Booster_WB_L2.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            last_next_wb_openvb = self.next_open_vb_information_after.DM_NORMAL_WB_VB_0
        

        pass

    def post_process(self) -> None:
        pass
    
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
    def show_vb_valid_count_info(self)-> None:
        vb_valid_count_list_data_format = {
            'value': {'pos': 0, 'len': 32, 'mask': 0xffffffff}, 
        }
        response, rep_data = get_vb_valid_cnt_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
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
    def get_dedicate_vb_group(self, grouptype:int)-> int:
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'dirty': {'pos': 6, 'len': 1, 'mask': 0x1}, 
            'access_mode': {'pos': 7, 'len': 1, 'mask': 0x1}, 
        }
        response, rep_data = get_vb_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data)):
            if self.fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break
            ftl_vb_list_data.update({vb : {k: ((rep_data[vb*4] >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        
        for vb, vb_info in ftl_vb_list_data.items():
            last_type = vb_info['group']
            if last_type == grouptype:
                logger.info(f'[vb = {vb}, group type = {last_type}]')
                return vb
        return 0
    def show_vb_info(self)-> None:
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'dirty': {'pos': 6, 'len': 1, 'mask': 0x1}, 
            'access_mode': {'pos': 7, 'len': 1, 'mask': 0x1}, 
        }
        response, rep_data = get_vb_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data)):
            if self.fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break
            ftl_vb_list_data.update({vb : {k: ((rep_data[vb*4] >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        
        for vb, vb_info in ftl_vb_list_data.items():
            last_type = vb_info['group']
            logger.info(f'[vb = {vb}, group type = {last_type}]')
        return
    def check_next_open_vb_information(self, next_open_vb_information:project_api.NextOpenVBInformation) -> bool:
        if(next_open_vb_information.DM_NORMAL_HOST_VB.value != next_open_vb_information.DM_NORMAL_WB_VB_0.value != next_open_vb_information.DM_NORMAL_SHARE_VB_1.value != next_open_vb_information.DM_NORMAL_DEFRAG_VB.value):
            return False
        if(next_open_vb_information.DM_NORMAL_SHARE_VB_0.value != next_open_vb_information.DM_RPMB_HOST_VB.value != next_open_vb_information.DM_EM1_DEFRAG_VB.value):
            return False
        return True  
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
    def print_open_vb_information(self, open_vb_information:project_api.OpenVBInformation) -> None:
        print_object_info_ai(open_vb_information)
        # logger.info('================= open_vb_information =================')
        # logger.info(f'Byte[{open_vb_information.L2_Open_logical_VB_Host_TLC_number.start_offset}:{open_vb_information.L2_Open_logical_VB_Host_TLC_number.end_offset}]: L2_Open_logical_VB_Host_TLC_number = {open_vb_information.L2_Open_logical_VB_Host_TLC_number.value}')
        # logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_L2_Open_logical_VB_Host_TLC.start_offset}:{open_vb_information.first_free_physical_page_of_L2_Open_logical_VB_Host_TLC.end_offset}]: first_free_physical_page_of_L2_Open_logical_VB_Host_TLC = {open_vb_information.first_free_physical_page_of_L2_Open_logical_VB_Host_TLC.value}')
        # logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC.start_offset}:{open_vb_information.open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC.end_offset}]: open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC = {open_vb_information.open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC.value}')
        # logger.info(f'Byte[{open_vb_information.first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC.start_offset}:{open_vb_information.first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC.end_offset}]: first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC = {open_vb_information.first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC.value}')

        # logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_EM1_L2_Host.start_offset}:{open_vb_information.open_logical_VB_number_for_EM1_L2_Host.end_offset}]: open_logical_VB_number_for_EM1_L2_Host = {open_vb_information.open_logical_VB_number_for_EM1_L2_Host.value}')
        # logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_EM1_L2_Host_VB.start_offset}:{open_vb_information.first_free_physical_page_of_EM1_L2_Host_VB.end_offset}]: first_free_physical_page_of_EM1_L2_Host_VB_ = {open_vb_information.first_free_physical_page_of_EM1_L2_Host_VB.value}')
        # logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_EM1_GC.start_offset}:{open_vb_information.open_logical_VB_number_for_EM1_GC.end_offset}]: open_logical_VB_number_for_EM1_GC = {open_vb_information.open_logical_VB_number_for_EM1_GC.value}')
        # logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_EM1_GC_VB.start_offset}:{open_vb_information.first_free_physical_page_of_EM1_GC_VB.end_offset}]: first_free_physical_page_of_EM1_GC_VB = {open_vb_information.first_free_physical_page_of_EM1_GC_VB.value}')
        
        
        # logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_Write_Booster_WB_L2.start_offset}:{open_vb_information.open_logical_VB_number_for_Write_Booster_WB_L2.end_offset}]: open_logical_VB_number_for_Write_Booster_WB_L2 = {open_vb_information.open_logical_VB_number_for_Write_Booster_WB_L2.value}')
        # logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_Write_Booster_WB_L2.start_offset}:{open_vb_information.first_free_physical_page_of_Write_Booster_WB_L2.end_offset}]: first_free_physical_page_of_Write_Booster_WB_L2 = {open_vb_information.first_free_physical_page_of_Write_Booster_WB_L2.value}')
        # logger.info(f'Byte[{open_vb_information.open_Remap_VB_number_for_Write_Booster_WB_L2.start_offset}:{open_vb_information.open_Remap_VB_number_for_Write_Booster_WB_L2.end_offset}]: open_Remap_VB_number_for_Write_Booster_WB_L2 = {open_vb_information.open_Remap_VB_number_for_Write_Booster_WB_L2.value}')
        # logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_RPMB_VB.start_offset}:{open_vb_information.open_logical_VB_number_for_RPMB_VB.end_offset}]: open_logical_VB_number_for_RPMB_VB = {open_vb_information.open_logical_VB_number_for_RPMB_VB.value}')
        # logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_RPMB_VB.start_offset}:{open_vb_information.first_free_physical_page_of_RPMB_VB.end_offset}]: first_free_physical_page_of_RPMB_VB = {open_vb_information.first_free_physical_page_of_RPMB_VB.value}')
        # logger.info(f'Byte[{open_vb_information.open_Remap_VB_number_for_RPMB_VB.start_offset}:{open_vb_information.open_Remap_VB_number_for_RPMB_VB.end_offset}]: open_Remap_VB_number_for_RPMB_VB = {open_vb_information.open_Remap_VB_number_for_RPMB_VB.value}')
        
        # logger.info(f'Byte[{open_vb_information.PTE_Block_VB_number_logical.start_offset}:{open_vb_information.PTE_Block_VB_number_logical.end_offset}]: PTE_Block_VB_number_logical = {open_vb_information.PTE_Block_VB_number_logical.value}')
        # logger.info(f'Byte[{open_vb_information.PTE_block_First_free_physical_page.start_offset}:{open_vb_information.PTE_block_First_free_physical_page.end_offset}]: PTE_block_First_free_physical_page = {open_vb_information.PTE_block_First_free_physical_page.value}')
        # logger.info(f'Byte[{open_vb_information.LOG_Block_First_free_physical_page.start_offset}:{open_vb_information.LOG_Block_First_free_physical_page.end_offset}]: LOG_block_VB_number_logical = {open_vb_information.LOG_block_VB_number_logical.value}')
        # logger.info(f'Byte[{open_vb_information.List_block_First_free_physical_page.start_offset}:{open_vb_information.List_block_First_free_physical_page.end_offset}]: List_Block_VB_number_logical = {open_vb_information.List_Block_VB_number_logical.value}')
        # logger.info(f'Byte[{open_vb_information.start_physical_page_of_VB_of_TMP_RAIN_VB_SSU_VB.start_offset}:{open_vb_information.start_physical_page_of_VB_of_TMP_RAIN_VB_SSU_VB.end_offset}]: open_Logical_VB_of_TMP_RAIN_VB_SSU_VB = {open_vb_information.open_Logical_VB_of_TMP_RAIN_VB_SSU_VB.value}')
        
        return 

    def get_and_print_open_vb_information(self) -> project_api.OpenVBInformation:
        rsp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        self.print_open_vb_information(open_vb_information)
        return open_vb_information    
    def get_and_print_next_open_vb_information(self, openvbtype: int) -> project_api.NextOpenVBInformation:
        rsp, next_open_vb_information = project_api.issue_40DC_to_get_next_open_vb_information(openvbtype)
        self.print_next_open_vb_information(next_open_vb_information)
        return next_open_vb_information  
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
    
    def check_timeout(self,start_time: float, timeout_min: int) -> bool:
        current_time = time.time()
        if (current_time - start_time) >= timeout_min * 60:
            return True
        else:
            return False
    def write_unmap_cycle(self,lun: int,start_lba: int,total_bytes: int, chunk_size: int, lastvb : int) -> int:
    
        remaining = total_bytes
        cur_lba = start_lba
        loop = 0
        while remaining > 0:
            # --------------------------------------------------------------
            # 1️⃣ 連續寫入 chunk_size（若剩餘不足則寫剩下的）
            # --------------------------------------------------------------
            write_len = chunk_size
            # api.sequential_write(
            #     lun=lun,
            #     start_lba=cur_lba,
            #     total_size=write_len,
            #     chunk_size=write_len,          # 直接一次寫完
            #     fua=1,
            #     need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record,
            # )
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=lun, lba=cur_lba, length=write_len, fua=1)

            ExecuteCMD.enqueue(write10)

            # unmap = ExecuteCMD.Unmap()
            # unmap.assign(lun=lun, lba=start_lba, length=write_len)
            # ExecuteCMD.enqueue(unmap)
            loop +=1
            if (loop % 1000) == 999:
                ExecuteCMD.send(clear_on_success=True)
                self.next_open_vb_information_inner = self.get_and_print_next_open_vb_information(0) 
                if self.next_open_vb_information_inner.DM_NORMAL_SHARE_VB_1.value != lastvb:
                    logger.info(f'lastvb = {lastvb} current last openvb = {self.next_open_vb_information_inner.DM_NORMAL_SHARE_VB_1.value}')
                    lastvb = self.next_open_vb_information_inner.DM_NORMAL_SHARE_VB_1.value
                    return lastvb
            lba_increment = write_len
            cur_lba += lba_increment
            remaining -= write_len
        
        ExecuteCMD.send(clear_on_success=True)
        self.next_open_vb_information_inner = self.get_and_print_next_open_vb_information(0) 
        if self.next_open_vb_information_inner.DM_NORMAL_SHARE_VB_1.value != lastvb:
            logger.info(f'lastvb = {lastvb} current last openvb = {self.next_open_vb_information_inner.DM_NORMAL_SHARE_VB_1.value}')
            lastvb = self.next_open_vb_information_inner.DM_NORMAL_SHARE_VB_1.value
        return lastvb

run = Pattern().run
if __name__ == "__main__":
    run()