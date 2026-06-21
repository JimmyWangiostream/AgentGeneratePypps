import time

import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD, shared
from Script.api.exception import PATTERN_ASSERT_STUCK_WHILE_TIMEOUT, SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET, SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
from Script.api.ufs_api.defines.constant_define import BLOCK256B_SIZE_4K_BYTE
from Script.api.ufs_api.defines.enum_define import RPMBRegion
from Script.api.ufs_api.vendor_cmd.functions import get_vb_info
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
import random
from typing import TypeAlias, List, Dict
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api.vendor_cmd.structs import PCA
from Script.api.ufs_api.descriptors.configuration_desc.structs import ConfigDescriptor310, ConfigDescriptor400, ConfigDescriptor410
from Script.project_api.outgoing_slx.structs import TRIM_STATE, VB_GROUP_TYPE

ConfigDescriptorUnion: TypeAlias = ConfigDescriptor310 | ConfigDescriptor400 | ConfigDescriptor410
_param = shared.param

class Pattern(UFSTC):
    def pre_process(self) -> None:

        api.MP().execute()
        api.first_init_to_max_hs_gear(link_startup_mode=_param.current_speed.link_startup_mode, ref_clk=_param.current_speed.refclk)
    
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.au_size = self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size * 512
        self.total_au_size = self.geometry_desc.q4_total_raw_device_capacity // (self.geometry_desc.l13_segment_size * self.geometry_desc.b17_allocation_unit_size)
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.TestWBLun = 3
        self.rpmb = RPMB(RPMBRegion.REGION_0)
        self.slx_trim_set : set[int] = set()
        self.por_trim_set : set[int] = set()
        self.write_record = api.get_empty_write_record()
        pass

    def step1(self) -> None:

        logger.flow(1, 'Verify all free VB by erasing with SLx trim')
        self.get_vb_trim_set()
        if not(self.check_include_set({VB_GROUP_TYPE.FREE_BLK_QUEUE_SLC, VB_GROUP_TYPE.FREE_BLK_QUEUE_MLC}, self.slx_trim_set) and \
            self.check_exclude_set({VB_GROUP_TYPE.FREE_BLK_QUEUE_MLC}, self.por_trim_set) and \
            self.check_include_set({VB_GROUP_TYPE.LIST_BLK, VB_GROUP_TYPE.LIST_INDEX_BLK, VB_GROUP_TYPE.TMP_CODE_BLK, VB_GROUP_TYPE.LOG_TAB_BLK}, self.por_trim_set)):
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        self.clear_all_set()

        logger.flow(2, 'RPMB Write Data')
        logger.info('RPMB key progrmming')
        self.rpmb_key_programming()
        logger.info('RPMB write data')
        self.rpmb.rpmb_write_data(0, BLOCK256B_SIZE_4K_BYTE)
        logger.flow(3, 'Verify EM1 open VB by erasing with POR trim')
        self.get_vb_trim_set()
        if not(self.check_include_set({VB_GROUP_TYPE.FREE_BLK_QUEUE_SLC, VB_GROUP_TYPE.FREE_BLK_QUEUE_MLC}, self.slx_trim_set) and \
                self.check_exclude_set({VB_GROUP_TYPE.FREE_BLK_QUEUE_MLC}, self.por_trim_set) and \
                self.check_include_set({VB_GROUP_TYPE.CURRENT_L2_SLC}, self.por_trim_set)):
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        self.clear_all_set()

        logger.flow(4, 'LUN Configuration')
        self.set_LUN_configuration()
        logger.flow(5, 'Verify open VB (L1, L2, WB) by erasing with POR trim')
        self.get_vb_trim_set()
        if not(self.check_include_set({VB_GROUP_TYPE.FREE_BLK_QUEUE_SLC, VB_GROUP_TYPE.FREE_BLK_QUEUE_MLC}, self.slx_trim_set) and \
                self.check_include_set({VB_GROUP_TYPE.CURRENT_L2_MLC, VB_GROUP_TYPE.CURRENT_L1}, self.por_trim_set)):
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        self.clear_all_set()

        logger.flow(6, 'Purge All')
        self.purge_all()
        logger.flow(7, 'Verify all free VB by erasing with POR trim')
        self.get_vb_trim_set()
        if not(self.check_exclude_set({VB_GROUP_TYPE.FREE_BLK_QUEUE_SLC, VB_GROUP_TYPE.FREE_BLK_QUEUE_MLC}, self.slx_trim_set) and \
                self.check_include_set({VB_GROUP_TYPE.FREE_BLK_QUEUE_SLC, VB_GROUP_TYPE.FREE_BLK_QUEUE_MLC, VB_GROUP_TYPE.CURRENT_L2_MLC, VB_GROUP_TYPE.CURRENT_L1}, self.por_trim_set)):
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        self.clear_all_set()

        logger.flow(8, 'RPMB Write Data')
        logger.info('RPMB key progrmming')
        self.rpmb_key_programming()
        logger.info('RPMB write data')
        self.rpmb.rpmb_write_data(0, BLOCK256B_SIZE_4K_BYTE)
        logger.flow(9, 'Verify EM1 open VB by erasing with POR trim')
        self.get_vb_trim_set()
        if not(self.check_exclude_set({VB_GROUP_TYPE.FREE_BLK_QUEUE_SLC, VB_GROUP_TYPE.FREE_BLK_QUEUE_MLC}, self.slx_trim_set) and \
                self.check_include_set({VB_GROUP_TYPE.FREE_BLK_QUEUE_SLC, VB_GROUP_TYPE.FREE_BLK_QUEUE_MLC, VB_GROUP_TYPE.CURRENT_L2_SLC}, self.por_trim_set)):
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        self.clear_all_set()
        
        logger.flow(10, 'Get EM1 open VB index')
        RPMB_write_SLC_vb_index = self.get_vb_index(VB_GROUP_TYPE.CURRENT_L2_SLC)
        logger.info(f'EM1 open vb index : {RPMB_write_SLC_vb_index}') 

        logger.flow(11, f'Sequential write EM1 LUN{self.TestEM1Lun}')
        api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size= api.BLOCK4K_SIZE_1M_BYTE, chunk_size=api.BLOCK4K_SIZE_1M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        logger.flow(12, 'Verify EM1 VB already opened due to RPMB write')
        self.get_vb_trim_set()
        if not(self.check_exclude_set({VB_GROUP_TYPE.FREE_BLK_QUEUE_SLC, VB_GROUP_TYPE.FREE_BLK_QUEUE_MLC}, self.slx_trim_set) and \
                self.check_include_set({VB_GROUP_TYPE.FREE_BLK_QUEUE_SLC, VB_GROUP_TYPE.FREE_BLK_QUEUE_MLC, VB_GROUP_TYPE.CURRENT_L2_MLC, VB_GROUP_TYPE.CURRENT_L1,  VB_GROUP_TYPE.CURRENT_L2_SLC, VB_GROUP_TYPE.RAIN_SWAP_NO_OBR_SLC_L2_SLC}, self.por_trim_set)):
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        self.clear_all_set()
        logger.flow(13, 'Get EM1 open VB index')
        EM1_LUN_write_SLC_vb_index = self.get_vb_index(VB_GROUP_TYPE.CURRENT_L2_SLC)
        logger.info(f'EM1 open vb index : {EM1_LUN_write_SLC_vb_index}') 

        logger.flow(14, f'Check if the RPMB-written VB index equals the EM1 LUN VB index.') 
        if not RPMB_write_SLC_vb_index == EM1_LUN_write_SLC_vb_index:
            logger.error_lb(f'Check if the RPMB-written VB index equals the EM1 LUN VB index.')
            logger.error_fp(f'Expect the RPMB-written VB index {RPMB_write_SLC_vb_index} is equal to EM1 LUN VB index {EM1_LUN_write_SLC_vb_index}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def post_process(self) -> None:
        pass

    def get_vb_trim_set(self)->None:
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'dirty': {'pos': 6, 'len': 1, 'mask': 0x1}, 
            'access_mode': {'pos': 8, 'len': 1, 'mask': 0x1}, 
            'vb_trim':{'pos':16, 'len':2, 'mask': 0x3}
        }
        total_VB_count = self.fw_geometry.l52_total_vb_count
        _, vb_info_data = get_vb_info()
        dumpfile("vb_info.bin", bytearray(vb_info_data))

        vb_info_list = dict()

        for id in range(total_VB_count):
            if id *4  >= len(vb_info_data):
                break
            integer_value = int.from_bytes(vb_info_data[id*4: ((id+1)*4)], byteorder='little')
            vb_info_list.update({id : {k: ((integer_value >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})

        for vb_idx, vb_info in vb_info_list.items():
            vb_trim = vb_info['vb_trim']
            if(vb_trim == TRIM_STATE.SLx_TRIM):
                self.slx_trim_set.add(vb_info['group'])
            elif vb_trim == TRIM_STATE.POR_TRIM:
                self.por_trim_set.add(vb_info['group'])
            
        logger.info(f'SLx Trim group : {sorted(self.slx_trim_set)}')
        logger.info(f'POR Trim group : {sorted(self.por_trim_set)}')
        pass

    def get_vb_index(self, vb_group: int)-> list[int]:
        vb_list : list[int] = []
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'dirty': {'pos': 6, 'len': 1, 'mask': 0x1}, 
            'access_mode': {'pos': 8, 'len': 1, 'mask': 0x1}, 
            'vb_trim':{'pos':16, 'len':2, 'mask': 0x3}
        }
        total_VB_count = self.fw_geometry.l52_total_vb_count
        _, vb_info_data = get_vb_info()
        dumpfile("vb_info.bin", bytearray(vb_info_data))

        vb_info_list = dict()

        for id in range(total_VB_count):
            if id *4  >= len(vb_info_data):
                break
            integer_value = int.from_bytes(vb_info_data[id*4: ((id+1)*4)], byteorder='little')
            vb_info_list.update({id : {k: ((integer_value >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        
        for vb_idx, vb_info in vb_info_list.items():
            group = vb_info['group']
            if(group == vb_group):
                vb_list.append(vb_idx)

        logger.info(f'VB Group {vb_group} : {vb_list}')        
        return vb_list

    def set_LUN_configuration(self) -> None:
        selector = 0x00
        length = 0xE6
        config_desc = api.get_config_descriptors(print = True)
        lun_num_per_desc = 8
        EM1_total_AU = min(shared.param.gGeometry.l44_enhanced1_max_n_alloc_u, self.total_au_size//3)
        normal_total_AU = self.total_au_size//3 * 2
        for index in range(int(self.max_number_lu/lun_num_per_desc)):
            cmd = ExecuteCMD.WriteDescriptor()
            cmd.assign(api.DescriptorIDN.CONFIGURATION, index, selector, length)

            config_desc[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            config_desc[index].header.b3_boot_enable = api.BootEnable.BOOT_DISABLE
            # config_desc[index].header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE
            config_desc[index].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.DISABLE
            config_desc[index].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
            config_desc[index].header.l18_num_shared_write_booster_buffer_alloc_units = self.geometry_desc.l79_write_booster_buffer_max_n_alloc_units if index==0 else 0
            for unit in range(lun_num_per_desc):
                if index == 0 and unit == self.TestNormalLun: # LUN 0
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[index].units[unit].l4_num_alloc_units = 8192 #(normal_total_AU)//2
                    config_desc[index].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index ==0 and unit == self.TestEM1Lun: #LUN 1
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id =  api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_desc[index].units[unit].l4_num_alloc_units = 2000 #(EM1_total_AU)
                    config_desc[index].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit == self.TestWBLun:
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[index].units[unit].l4_num_alloc_units = 8192 #(normal_total_AU)//2
                    config_desc[index].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                else:
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.DISABLE
                    config_desc[index].units[unit].l4_num_alloc_units = 0
                    config_desc[index].units[unit].b9_logical_block_size = 0
                
            cmd.set_desc(config_desc[index])
            ExecuteCMD.enqueue(cmd)
            # push_write_config(config_desc[index], index=index)

        ExecuteCMD.RequestSense().assign(lun = self.TestNormalLun, length = 18).enqueue()
        ExecuteCMD.RequestSense().assign(lun = self.TestEM1Lun, length = 18).enqueue()
        ExecuteCMD.RequestSense().assign(lun = self.TestWBLun, length = 18).enqueue()
        ExecuteCMD.send()
        pass

    def purge_all(self)->None:
        idn = api.FlagIDN.PURGE_EN
        logger.flow(8, 'Host issue set flag idn = %d' % idn)
        set_flag = ExecuteCMD.SetFlag().assign(idn).enqueue()
        ExecuteCMD.send(clear_on_success=True)
        timeout_min = 10
        start_time = time.time()
        polling_cnt = 0
        while True:
            if self.check_timeout(start_time, timeout_min):
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            purge_status = api.read_attribute(idn=api.AttributeIDN.PURGE_STATUS)
            polling_cnt += 1
            logger.info(f'purge status = {purge_status}, polling count = {polling_cnt}')
            if purge_status is 0x03:
                logger.info(f'purge status = {purge_status}, complete')
                break

    def check_timeout(self, start_time: float, timeout_min: int) -> bool:
        current_time = time.time()
        if (current_time - start_time) >= timeout_min * 60:
            return True
        else:
            return False

    def rpmb_key_programming(self) -> None:
        try:
            write_counter = self.rpmb.rpmb_read_counter()
        except SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
            self.rpmb.rpmb_key_programming()
            write_counter = self.rpmb.rpmb_read_counter()

    def check_include_set(self, subset:set[int], totalSet:set[int]) -> bool:
        if subset.issubset(totalSet):
            return True
        else:
            return False
        
    def check_exclude_set(self, subset:set[int], totalSet:set[int]) -> bool:
        if totalSet.isdisjoint(subset):
            return True
        else:
            return False
        
    def clear_all_set(self)-> None:
        self.slx_trim_set.clear()
        self.por_trim_set.clear()

run = Pattern().run
if __name__ == "__main__":
    run()