import package_root
from typing import cast
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from typing import TypeAlias, cast, List
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api.vendor_cmd.functions import lba_to_pba
from Script.api.ufs_api.vendor_cmd.structs import L2P_PCA, PCA
from Script.api.ufs_api.descriptors.configuration_desc.structs import ConfigDescriptor, ConfigDescriptor310, ConfigDescriptor400, ConfigDescriptor410
from enum import Enum, auto
from Script.project_api.custom_vu.lba_convert_vu import ftl_lba,issue_40D4_to_get_FTL_LBA

ENG2_WA = True

ConfigDescriptorUnion: TypeAlias = ConfigDescriptor310 | ConfigDescriptor400 | ConfigDescriptor410

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.geometry_desc = api.get_geometry_descriptor()
        self.au_size = self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size * 512
        self.boot_au_size = int(api.DATA_SIZE_16M_BYTE/self.au_size)
        self.total_au_size = self.geometry_desc.q4_total_raw_device_capacity / (self.geometry_desc.l13_segment_size * self.geometry_desc.b17_allocation_unit_size)
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.normal_au_size = int((self.total_au_size-2*self.boot_au_size) / self.max_number_lu)
        self.normal_4K_size = int(self.normal_au_size*self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size / 8)
        pass

    def step1(self) -> None:
        default_write_size = api.BLOCK4K_SIZE_4M_BYTE
        logger.flow(1, 'Config LUN 0~3 Enable')
        self.config_LUN_enable()
        for lun in range(0, 4):
            lun_capacity = api.get_unit_descriptor(lun).q11_logical_block_count
            length = default_write_size if lun_capacity > default_write_size else lun_capacity
            lba = 0
            logger.flow(2, f'Sequence write , lun ={lun}  lba = {lba}, total size = {length}')
            self.write_data(lun, 0, length)
            logger.flow(3, f'Random select LBA on LUN: {lun}')
            lba = random.randint(0, length)
            logger.info(f'Select LUN = {lun}, LBA = {lba}')
            logger.flow(4, 'Issue phison VU L2P with selected LBA to get PBA')
            phison_pca = lba_to_pba(lun, lba)
            logger.flow(5, 'Issue Micron VU 40D4 with selected LBA to get PBA')
            _,ftl_lba = issue_40D4_to_get_FTL_LBA(lun, lba)
            logger.flow(6, 'Compare FTL LBA from micron VU 40D4 with LCA from phison VU L2P ')
            if(ftl_lba.lba.value != phison_pca.l112_lca.value):
                logger.error_lb(f'Issue 40D4 to get FTL LBA')
                logger.error_fp(f'Expected LBA = {phison_pca.l112_lca.value}, but LBA = {ftl_lba.lba.value}')
                raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def post_process(self) -> None:
        pass

    def config_LUN_enable(self) -> None:
        config_desc = api.get_config_descriptors(print = True)
        lun_num_per_desc = 8

        for index in range(int(self.max_number_lu/lun_num_per_desc)):
            config_desc[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            config_desc[index].header.b3_boot_enable = api.BootEnable.BOOT_ENABLE
            for unit in range(lun_num_per_desc):
                config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.DISABLE
                config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                config_desc[index].units[unit].l4_num_alloc_units = self.normal_au_size
                config_desc[index].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                if index == 0 and unit == 0:  # LUN 0
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[index].units[unit].l4_num_alloc_units = self.normal_au_size
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                elif index == 0 and unit == 1: # LUN 1
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_A
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_desc[index].units[unit].l4_num_alloc_units = self.boot_au_size 
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                elif index == 0 and unit == 2: # LUN 2
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_B
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_desc[index].units[unit].l4_num_alloc_units = self.boot_au_size
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                elif index == 0 and unit == 3: # LUN 3
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_desc[index].units[unit].l4_num_alloc_units = self.normal_au_size
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                else:
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.DISABLE
            
            push_write_config(config_desc[index], index=index)

        for lun in range (0, 4):
            ExecuteCMD.RequestSense().assign(lun = lun, length = 18).enqueue()
        ExecuteCMD.send()
        pass
    
    def write_data(self, lun: int, lba: int, length:int ) -> None:
        logger.info(f'Sequence write data {length} size')
        start = lba
        offset = 0
        while offset < length:
            size = 0xffff
            if(offset + size > length):
                size = length - offset
            w = ExecuteCMD.Write10()
            w.assign(lun = lun, lba=lba, length=size, fua=1).enqueue()
            offset += size
            lba = start+offset
        ExecuteCMD.send()
        pass

run = Pattern().run
if __name__ == "__main__":
    run()