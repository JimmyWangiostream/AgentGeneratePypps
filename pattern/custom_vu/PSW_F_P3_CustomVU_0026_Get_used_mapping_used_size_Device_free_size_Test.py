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
import math
from typing import List, Dict

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = shared.param
        pass
    def step1(self) -> None:
        
        logger.flow(1, 'Precondition SLC & MLC Partition')
        for wb_case in range(2):
            
            for case in range(1, 3):
                
                if case == 1:
                    normal_ratio = 100
                    em1_ratio = 0
                
                elif case == 2:
                    normal_ratio = 50
                    em1_ratio = 50
                
                elif case == 3:
                    normal_ratio = 0
                    em1_ratio = 100
                logger.info(f'case = {case}, TLC ratio = {normal_ratio}, SLC ratio = {em1_ratio}')
                normal_lun_list, em1_lun_list = self.config_lun(normal_ratio, em1_ratio, wb_case)
                if wb_case == 1:
                    logger.flow(1-1, 'Set writebooster enable')
                    api.set_flag(api.FlagIDN.WRITEBOOSTER_EN)

                total_normal_mb , total_normal_node = self.calc_total_normal_mb(normal_lun_list)

                logger.flow(2, 'Send VU 40A8 Test with mode = 1')
                total_enable_lun = normal_lun_list + em1_lun_list
                lun = total_enable_lun[0]
                data_free_size = project_api.issue_40A8_to_get_used_mapping_used_size_device_free_size(mode = 1, lun=lun)
                logger.flow(3, 'Compare data free size')
                self.compare_value(data_free_size, total_normal_mb, desc="data_free_size")
                
                logger.flow(4, 'Send VU 40A8 Test with mode = 2')
                mapping_size_of_device = project_api.issue_40A8_to_get_used_mapping_used_size_device_free_size(mode = 2, lun=lun)
                logger.flow(5, 'Compare mapping size of device')
                self.compare_value(mapping_size_of_device, 0, desc="mapping_size_of_device")

                logger.flow(6, 'Random write config lun')
                total_valid_node = 0
                total_valid_mb = 0
                write_list : List[tuple[int,int]] = []
                max_write_len = 0
                max_write_lun = 0
                for lun in normal_lun_list:
                    data_len = api.WRITE_10_MAX_BLOCK_LEN
                    total_len = random.randint(1, min(BLOCK4K_SIZE_1G_BYTE, self._param.gLUCapacity[lun]) )
                    start_lba = 0
                    self.write_data(lun=lun,start_lba=start_lba,len=data_len,total_len=total_len)
                    write_list.append((lun, total_len))
                    if max_write_len < total_len:
                        max_write_len = total_len
                        max_write_lun = lun
                    total_valid_node +=  total_len

                total_valid_mb = total_valid_node * DATA_SIZE_4K_BYTE // (1024*1024)
                if (total_valid_node % 4096) !=0:
                    overwrite_len = total_valid_node % 4096
                    overwrite_len = 4096
                    self.write_data(lun=max_write_lun,start_lba=start_lba,len=overwrite_len,total_len=overwrite_len)     
                
                for lun in em1_lun_list:
                    data_len = random.randint(api.BLOCK4K_SIZE_128K_BYTE, api.BLOCK4K_SIZE_512K_BYTE)
                    total_len = random.randint(1,  min(BLOCK4K_SIZE_1G_BYTE, self._param.gLUCapacity[lun]))
                    start_lba = random.randint(0, self._param.gLUCapacity[lun] - total_len)
                    self.write_data(lun=lun,start_lba=0,len=data_len,total_len=total_len)
                
                logger.info(f'total valid node = {total_valid_node}, total valid mb ={total_valid_mb}')

                logger.flow(7, 'Send VU 40A8 Test with mode = 1')
                data_free_size = project_api.issue_40A8_to_get_used_mapping_used_size_device_free_size(mode = 1, lun=lun)
                logger.flow(8, 'Compare data free size')
                
                expect_value = (total_normal_node - total_valid_node)* DATA_SIZE_4K_BYTE // (1024*1024)
                self.compare_value(data_free_size, expect_value, desc="data_free_size")
                
                logger.flow(9, 'Send VU 40A8 Test with mode = 2')
                mapping_size_of_device = project_api.issue_40A8_to_get_used_mapping_used_size_device_free_size(mode = 2, lun=lun)
                logger.flow(10, 'Compare mapping size of device')
                expect_value = total_valid_node
                self.compare_value(mapping_size_of_device, expect_value, desc="mapping_size_of_device")

                logger.flow(11, 'random unmap config lun')
                total_invalid_node = 0
                total_invalid_mb = 0
                for lun, write_len in write_list:
                    data_len = random.randint(api.BLOCK4K_SIZE_128K_BYTE, api.BLOCK4K_SIZE_512K_BYTE)
                    total_len = min(write_len, data_len)
                    start_lba = 0
                    self.unmap_data(lun=lun,start_lba=start_lba,len=data_len,total_len=total_len)
                    total_invalid_node += total_len
                total_invalid_mb = total_invalid_node * DATA_SIZE_4K_BYTE // (1024*1024)


                for lun in em1_lun_list:
                    data_len = random.randint(api.BLOCK4K_SIZE_128K_BYTE, api.BLOCK4K_SIZE_512K_BYTE)
                    total_len = random.randint(0, min(BLOCK4K_SIZE_1G_BYTE, self._param.gLUCapacity[lun]))
                    start_lba = random.randint(0, self._param.gLUCapacity[lun] - total_len)
                    self.unmap_data(lun=lun,start_lba=start_lba,len=data_len,total_len=total_len)
                
                
                logger.info(f'total invalid node = {total_invalid_node}, total invalid mb = {total_invalid_mb}')

                logger.flow(12, 'Send VU 40A8 Test with mode = 1')
                data_free_size = project_api.issue_40A8_to_get_used_mapping_used_size_device_free_size(mode = 1, lun=lun)
                logger.flow(13, 'Compare data free size')
                expect_value = (total_normal_node - total_valid_node + total_invalid_node)* DATA_SIZE_4K_BYTE // (1024*1024)
                self.compare_value(data_free_size, expect_value, desc="data_free_size")
                
                logger.flow(14, 'Send VU 40A8 Test with mode = 2')
                mapping_size_of_device = project_api.issue_40A8_to_get_used_mapping_used_size_device_free_size(mode = 2, lun=lun)
                logger.flow(15, 'Compare mapping size of device')
                expect_value = total_valid_node - total_invalid_node
                self.compare_value(mapping_size_of_device, expect_value, desc="mapping_size_of_device")
                
    def unmap_data(self,lun:int, start_lba:int, len:int, total_len:int) -> None:
        while total_len > 0:
            len = min(total_len, len)
            unmap = ExecuteCMD.Unmap()
            unmap.assign(lun=lun, lba=start_lba, length=len)
            ExecuteCMD.enqueue(unmap)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
    def write_data(self, lun:int, start_lba:int, len:int, total_len:int, write_record:List[List[WriteRecordNode]]=[]) -> None:
        while total_len > 0:
            len = min(total_len, len)
            write10 = ExecuteCMD.Write10()
            logger.info(f'start lba = {start_lba}, len = {len}')
            write10.assign(lun=lun, lba=start_lba, length=len, fua=0)
            ExecuteCMD.enqueue(write10)
            start_lba += len
            total_len -= len
        ExecuteCMD.send(timeout=api.UniformTimeout(val=30000, unit=api.TimeResolution.ms), clear_on_success=False)
        ExecuteCMD.clear()
        
    def compare_value(self,value:int,expect_value:int, desc:str="") -> None:
        if value != expect_value:
            logger.error(f'Expect {desc}={expect_value}, but = {value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'{desc} val = {value}')
    def calc_total_normal_mb(self, normal_lun_list:list[int]) -> tuple[int,int]:
        total_normal_mb_cnt = 0
        for lun in normal_lun_list:
            total_normal_mb_cnt += self._param.gLUCapacity[lun]
        total_normal_mb = total_normal_mb_cnt * DATA_SIZE_4K_BYTE // (1024*1024) 
        my_total_normal_mb = total_normal_mb_cnt * DATA_SIZE_4K_BYTE // (1024*1024)
        return (total_normal_mb, total_normal_mb_cnt)
    def random_distribute(self,config_au:int,lun_list:list[int]) -> Dict[int,int]:
        base_au = config_au // len(lun_list)
        extra_au = config_au % len(lun_list)
        lun_au_map = {i:base_au for i in lun_list}
        for i in random.sample(lun_list, extra_au):
            lun_au_map[i] += 1
        return lun_au_map    
    
    def config_lun(self, normal_ratio:int, em1_ratio:int, wb_case:int) -> tuple[list[int], list[int]]:
        max_lun_cnt = self._param.gMaxNumberLU 
        normal_lun_count = 0
        em1_lun_count = 0
        total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        
        #get each config au
        config_normal_au = (total_au * normal_ratio) // 100
        config_em1_au = total_au - config_normal_au

        #dispatch each lun cnt
        if normal_ratio > 0 and em1_ratio > 0:
            normal_lun_count = random.randint(1, max_lun_cnt -1)
            em1_lun_count = random.randint(1, max_lun_cnt - normal_lun_count)
        elif normal_ratio > 0:
            normal_lun_count = random.randint(1, max_lun_cnt)
        else:
            em1_lun_count = random.randint(1, max_lun_cnt)
        
        #get choosen lun list
        all_luns = list(range(max_lun_cnt))
        #for test
        normal_luns_list = random.sample(all_luns, normal_lun_count)
        # #for test
        # if len(normal_luns_list) >0 and  0 not in normal_luns_list:
        #     normal_luns_list[0] = 0
        remaining = [i for i in all_luns if i not in normal_luns_list]
        em1_luns_list = random.sample(remaining, em1_lun_count)
        #for test
        # if len(em1_luns_list) >0 and len(normal_luns_list) == 0 and 0 not in em1_luns_list:
        #     em1_luns_list[0] = 0
        
        if len(normal_luns_list) > 0:
            normal_lun_au_map = self.random_distribute(config_normal_au, normal_luns_list)
        if len(em1_luns_list) > 0:
            em1_lun_au_map = self.random_distribute(config_em1_au, em1_luns_list)
        
        config_descs = api.get_config_descriptors(print=False)
        for table in range(4):
            for unit in range(8):
                config_descs[table].header.b2_conf_desc_continue = 1
                config_descs[table].units[unit].b0_lu_enable = 0
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].l4_num_alloc_units = 0
                config_descs[table].units[unit].b9_logical_block_size = 0xc
                config_descs[table].units[unit].b10_provisioning_type = ProvisioningType.THIN_PROVISIONING_ERASE
                if (table * 8 + unit) in normal_luns_list:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b3_memory_type = MemoryType.NORMAL
                    config_descs[table].units[unit].l4_num_alloc_units = normal_lun_au_map[table * 8 + unit]
                elif (table * 8 + unit) in em1_luns_list:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b3_memory_type = MemoryType.ENHANCED_1
                    config_descs[table].units[unit].l4_num_alloc_units =em1_lun_au_map[table * 8 + unit]
        if wb_case == 1:
            config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
            config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = min(self._param.gGeometry.l79_write_booster_buffer_max_n_alloc_units, config_normal_au)
        else:
            config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0
        
        config_descs[3].header.b2_conf_desc_continue = 0

        for table in range(4):
            api.push_write_config(config_descs[table], index=table)

        ExecuteCMD.send()
        ExecuteCMD.clear()
        config_descs = api.get_config_descriptors(print=True)

        #update descriptor to get new capacity
        unit_desc_idxes:List[int] = []
        for lun in range(0, self._param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            update_descriptor(DescriptorIDN.UNIT, index, cast(QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

        #test unit ready all enable lun
        for lun in range(self._param.gMaxNumberLU):
            if self._param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

        return (normal_luns_list, em1_luns_list)
    def post_process(self) -> None:
        pass
    

run = Pattern().run
if __name__ == "__main__":
    run()