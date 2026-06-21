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
from Script.api.ufs_api.vendor_cmd.functions import lba_to_pba, load_PMD_data, load_PTE_data, direct_read
from Script.api.ufs_api.vendor_cmd.structs import L2P_PCA, PCA
from Script.api.ufs_api.descriptors.configuration_desc.structs import ConfigDescriptor, ConfigDescriptor310, ConfigDescriptor400, ConfigDescriptor410
from enum import Enum, auto
from Script.project_api.custom_vu.lba_convert_vu import physical_address_info, logical_address_info
from Script.project_api.custom_vu.lba_convert_vu import issue_4051_to_get_physical_address, issue_4052_to_get_logical_address


class PPT(Enum):
    PTE = 0
    PMD = auto()  # 1

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
        default_write_size = api.BLOCK4K_SIZE_16M_BYTE
        logger.flow(1, 'Config all LUN')
        self.config_all_LUN_enable()
        for lun in range(0, self.max_number_lu):
            lun_capacity = api.get_unit_descriptor(lun).q11_logical_block_count
            length = default_write_size if lun_capacity > default_write_size else lun_capacity
            lba = random.randint(0, lun_capacity - length)
            
            logger.flow(2, f'Sequence write , lun ={lun}  lba = {lba}, total size = {length}')
            self.write_data(lun, lba, length)
            
            logger.flow(3, f'Random select LBA on LUN: {lun}')
            lba = random.randint(lba, lba+length)
            logger.info(f'Select LUN = {lun}, LBA = {lba}')     

            logger.flow(4, 'Issue phison L2P VU with selected LBA to get PBA')
            phison_pca = lba_to_pba(lun, lba)
            
            logger.flow(5, 'Issue Micron VU 4051 with selected LBA to get PBA')
            _,micron_pca = issue_4051_to_get_physical_address(lun, lba)
            
            logger.flow(6, 'Compare PBA host info')
            self.compare_pca_info(phison_pca, micron_pca)

            # 寫不滿 4096 LBA, PTE 會沒有 update, 因此 vb number 會是 0xFFFFFFFF
            if micron_pca.PPT_virtual_block_number.value != 0xFFFFFFFF:
                logger.flow(7, 'Compare PTE data')
                pte_data = load_PTE_data(int(phison_pca.l112_lca.value/1024))
                pte_pca = self.get_direct_pca_info(micron_pca, PPT.PTE)
                direct_read_data = direct_read(pte_pca, 1)
                if pte_data != direct_read_data :
                    logger.error_lb(f'Host issue phison VU 0x91 to read PTE data')
                    logger.error_fp(f'Expect PTE data compare success, but failed')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if micron_pca.PPT2_virtual_block_number.value != 0xFFFFFFFF:
                logger.flow(8, 'Compare PMD data')
                pmd_data = load_PMD_data(lun, lba)
                pmd_pca = self.get_direct_pca_info(micron_pca, PPT.PMD)
                direct_read_data = direct_read(pmd_pca, 1)
                if pmd_data != direct_read_data :
                    logger.error_lb(f'Host issue phison VU 0x92 to read PMD data')
                    logger.error_fp(f'Expect PMD data compare success, but failed')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            logger.flow(9, 'Get LBA form PCA through Micron VU 4052')
            _, micorn_lba = issue_4052_to_get_logical_address(micron_pca.die.value, micron_pca.plane.value, micron_pca.physical_block_number_w_BBT.value, micron_pca.page.value, micron_pca.offset.value)
            
            logger.flow(10, 'Compare LBA Info')
            self.compare_lba_info(lun, lba, micorn_lba)
        pass

    def post_process(self) -> None:
        pass

    def config_all_LUN_enable(self) -> None:
        config_desc = api.get_config_descriptors(print = True)
        lun_num_per_desc = 8

        for index in range(int(self.max_number_lu/lun_num_per_desc)):
            config_desc[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            config_desc[index].header.b3_boot_enable = api.BootEnable.BOOT_ENABLE
            for unit in range(lun_num_per_desc):
                config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                config_desc[index].units[unit].l4_num_alloc_units = self.normal_au_size
                config_desc[index].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                if index == 0 and unit == 1: # LUN 1
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_A
                    config_desc[index].units[unit].l4_num_alloc_units = self.boot_au_size
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                elif index == 0 and unit == 2: # LUN 2
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_B
                    config_desc[index].units[unit].l4_num_alloc_units = self.boot_au_size
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                elif index == 0 and unit == 3: # LUN 3
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
            
            push_write_config(config_desc[index], index=index)

        for lun in range (0, self.max_number_lu):
            ExecuteCMD.RequestSense().assign(lun = lun, length = 18).enqueue()
        ExecuteCMD.send()
       
        pass

    def compare_pca_info(self, phison_pca: L2P_PCA, micron_pca: physical_address_info) -> None:
        phison_ppage = self.wl_page_2_physical_page(phison_pca.b4_mode.value, phison_pca.w46_page.value, phison_pca.b20_lmu.value)
        phison_offset = int((phison_pca.l12_fpage.value - phison_pca.w46_page.value *32) /8)
        if not (phison_pca.b5_ce.value == micron_pca.die.value and \
                phison_pca.b6_plane.value == micron_pca.plane.value and \
                phison_pca.w10_block.value == micron_pca.virtual_block_number.value and \
                phison_pca.w10_block.value == micron_pca.physical_block_number_wo_BBT.value and \
                phison_ppage == micron_pca.page.value and \
                phison_offset == micron_pca.offset.value) :
            logger.error_lb(f'Compare pca info consistency between phison and micron')
            logger.error_fp(f'Expect ce = {phison_pca.b5_ce.value}, plane = {phison_pca.b6_plane.value}, block = {phison_pca.w10_block.value}, page = {phison_ppage}, offset = {phison_offset},'
                            f'but ce = {micron_pca.die.value}, plane = {micron_pca.plane.value}, virtual block = {micron_pca.virtual_block_number.value}, pysical block = {micron_pca.physical_block_number_wo_BBT.value},'
                            f'page = {phison_ppage}, offset = {phison_offset}'
            )
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def write_data(self, lun: int, lba: int, length:int ) -> None:
        logger.info(f'Sequence write data LUN:{lun}, LBA:{lba}, length:{length}')
        # logger.print_buffer(data)
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

    def compare_lba_info(self, lun: int, lba: int, micron_lba: logical_address_info) -> None:
        if not (micron_lba.lun.value == lun and micron_lba.lba.value == lba) :
            logger.error_lb(f'Compare LUN and LBA consistency between phison and micron')
            logger.error_fp(f'Expect lun = {lun} and lba = {lba}, but lun = {micron_lba.lun.value}, lba = {micron_lba.lba.value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    
    def wl_page_2_physical_page(self, access_mode:int, wl_page:int, lmu:int) -> int:
        ppage = 0
        if access_mode == 1:
            ppage = wl_page
        elif access_mode == 2:
            logical_page_base = [0, 1620, 1652, 3308]
            page_base         = [0, 540, 556, 1108]

            if wl_page < 540:
                region_index = 0
                shared_page_num = 3
            elif wl_page < 556:
                region_index = 1
                shared_page_num = 2
            elif wl_page < 1108:
                region_index = 2
                shared_page_num = 3
            elif wl_page < 1112:
                region_index = 3
                shared_page_num = 1
            else:
                logger.error(f'unexpected value - wl page ={wl_page}')
                raise SIGHTING_RESPONSE_UNEXPECTED


            if shared_page_num < lmu:
                print(f'unexpected value - lmu = {lmu}')
                raise SIGHTING_RESPONSE_UNEXPECTED

            ppage  = logical_page_base[region_index]
            ppage += (wl_page - page_base[region_index]) * shared_page_num + lmu

        else:
            print(f'unexpected value - access mode = {access_mode}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        
        return ppage
    
    def get_direct_pca_info(self, physical_address: physical_address_info, type: PPT) -> PCA:
        pca = PCA()
        pca.b4_mode = 1
        if type == PPT.PTE:
            pca.b5_ce = physical_address.PPT_die.value
            pca.b6_plane = physical_address.PPT_plane.value
            pca.b11_block_h = (physical_address.PPT_virtual_block_number.value>>8) & 0xFF
            pca.b10_block_l = physical_address.PPT_virtual_block_number.value & 0xFF
            pca.l12_fpage = int(physical_address.PPT_page.value * 32 + physical_address.PPT_offset.value * 8)
        else:
            pca.b5_ce = physical_address.PPT2_die.value
            pca.b6_plane = physical_address.PPT2_plane.value
            pca.b11_block_h = (physical_address.PPT2_virtual_block_number.value>>8) & 0xFF
            pca.b10_block_l = physical_address.PPT2_virtual_block_number.value & 0xFF
            pca.l12_fpage = int(physical_address.PPT2_page.value * 32 + physical_address.PPT2_offset.value * 8) 
        pca.to_bytes()

        return pca


run = Pattern().run
if __name__ == "__main__":
    run()