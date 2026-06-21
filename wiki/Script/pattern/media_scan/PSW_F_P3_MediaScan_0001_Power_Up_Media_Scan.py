import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from typing import List, cast, Optional
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.pattern.refresh.mutual_fun import *
from Script.project_api.custom_vu.media_scan_vu.structs import *
from Script.pattern.apl_system_rebuild.mutual_fun import inject_UECC
from Script.project_api.vth_sweep.functions import convert_page_to_page_order

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.write_record = api.get_empty_write_record()
        self.flash_setting = api.get_flash_setting()
        self.fw_geometry = api.get_fw_geometry()
        self.geometry_desc = api.get_geometry_descriptor()
        self.max_ce = self.flash_setting.Max_Fdevice
        self.max_plane = self.flash_setting.Plane_Per_Die
        pageline_block = self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
        self.TLC_WL_block = pageline_block * 4 * 3
        self.SLC_WL_block = pageline_block * 4
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.Total_AU_Count = self.geometry_desc.q4_total_raw_device_capacity / (self.geometry_desc.l13_segment_size * self.geometry_desc.b17_allocation_unit_size)
        pass

    def step1(self) -> None:

#=================================================================================================
        #TLC L2
#=================================================================================================
        
        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(2, 'configure lun and write tlc vb one wl size')
        self.config_lun()
        self.write_record = api.get_empty_write_record()
        write_size=self.TLC_WL_block
        api.sequential_write(lun=0, start_lba=0, total_size=write_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        _, open_vb_info = api.get_open_vb_info()
        old_tlc_l2_vb=open_vb_info.TLC_L2.logical_vb.value
        empty_ce=open_vb_info.TLC_L2.first_empty_CE.value
        empty_plane=open_vb_info.TLC_L2.first_empty_plane.value
        empty_page=open_vb_info.TLC_L2.first_empty_physical_page.value

        logger.flow(3, 'inject empty page UECC')
        pca = PCA()
        pca.b4_mode = 2
        pca.b5_ce = empty_ce
        pca.b6_plane = empty_plane
        pca.b11_block_h = (old_tlc_l2_vb >> 8) & 0xFF
        pca.b10_block_l = old_tlc_l2_vb & 0xFF
        for inject_page in range(empty_page, empty_page+12,3):
            logger.info(f'inject empty page{inject_page} UECC')
            pca.l12_fpage = convert_page_to_page_order(page=inject_page, isSLC=0)<<5
            inject_UECC(pca=pca)

        logger.flow(4, 'execute power up media scan')
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)

        logger.flow(5, f'check tlc l2 vb is change')
        _, open_vb_info = api.get_open_vb_info()
        new_tlc_l2_vb=open_vb_info.TLC_L2.logical_vb.value
        if new_tlc_l2_vb == old_tlc_l2_vb:
            logger.info('tlc l2 vb should change')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(6, f'Read Compare data')
        api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)

#=================================================================================================
        #SLC L2
#=================================================================================================
        
        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(2, 'configure lun and write slc vb one wl size')
        self.config_lun()
        self.write_record = api.get_empty_write_record()
        write_size=self.SLC_WL_block
        api.sequential_write(lun=1, start_lba=0, total_size=write_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        _, open_vb_info = api.get_open_vb_info()
        old_slc_l2_vb=open_vb_info.SLC_L2.logical_vb.value
        empty_ce=open_vb_info.SLC_L2.first_empty_CE.value
        empty_plane=open_vb_info.SLC_L2.first_empty_plane.value
        empty_page=open_vb_info.SLC_L2.first_empty_physical_page.value

        logger.flow(3, 'inject empty page UECC')
        pca = PCA()
        pca.b4_mode = 1
        pca.b5_ce = empty_ce
        pca.b6_plane = empty_plane    
        pca.b11_block_h = (old_slc_l2_vb >> 8) & 0xFF
        pca.b10_block_l = old_slc_l2_vb & 0xFF
        for inject_page in range(empty_page, empty_page+4):
            logger.info(f'inject empty page{inject_page} UECC')
            pca.l12_fpage = convert_page_to_page_order(page=inject_page, isSLC=1)<<5
            inject_UECC(pca=pca)

        logger.flow(4, 'execute power up media scan')
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)

        logger.flow(5, f'check slc l2 vb is change')
        _, open_vb_info = api.get_open_vb_info()
        new_slc_l2_vb=open_vb_info.SLC_L2.logical_vb.value
        if new_slc_l2_vb == old_slc_l2_vb:
            logger.info('slc l2 vb should change')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(6, f'Read Compare data')
        api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)
        
#=================================================================================================
        #TLC L1
#=================================================================================================
        
        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(2, 'configure lun and write tlc l1 vb')
        self.config_lun()
        self.write_record = api.get_empty_write_record()
        write_size = BLOCK4K_SIZE_16K_BYTE
        api.sequential_write(lun=0, start_lba=0, total_size=write_size, chunk_size=BLOCK4K_SIZE_16K_BYTE, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        _, open_vb_info = api.get_open_vb_info()
        old_l1_vb=open_vb_info.TLC_L1.logical_vb.value
        empty_ce=open_vb_info.TLC_L1.first_empty_CE.value
        empty_plane=open_vb_info.TLC_L1.first_empty_plane.value
        empty_page=open_vb_info.TLC_L1.first_empty_physical_page.value

        logger.flow(3, 'inject l1 blk empty page UECC')
        pca = PCA()
        pca.b4_mode = 2
        pca.b5_ce = empty_ce
        pca.b6_plane = empty_plane    
        pca.b11_block_h = (old_l1_vb >> 8) & 0xFF
        pca.b10_block_l = old_l1_vb & 0xFF
        empty_page+=3
        for inject_page in range(empty_page, empty_page+12,3):
            logger.info(f'inject empty page{inject_page} UECC')
            pca.l12_fpage = convert_page_to_page_order(page=inject_page, isSLC=0)<<5
            inject_UECC(pca=pca)

        logger.flow(4, 'execute power up media scan')
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)

        logger.flow(5, f'check tlc l1 vb is change')
        _, open_vb_info = api.get_open_vb_info()
        new_l1_vb=open_vb_info.TLC_L1.logical_vb.value
        empty_ce=open_vb_info.TLC_L1.first_empty_CE.value
        empty_plane=open_vb_info.TLC_L1.first_empty_plane.value
        empty_page=open_vb_info.TLC_L1.first_empty_physical_page.value
        if new_l1_vb == old_l1_vb:
            logger.info('tlc l1 vb should change')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(12, f'Read Compare data')
        api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)
        
#=================================================================================================
        #LOG
#=================================================================================================
        
        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)
        
        logger.flow(2, 'configure lun and write tlc vb 12M')
        self.config_lun()
        self.write_record = api.get_empty_write_record()
        api.sequential_write(lun=0, start_lba=0, total_size=BLOCK4K_SIZE_12M_BYTE, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        _, open_vb_info = api.get_open_vb_info()
        old_log_vb=open_vb_info.LOG.logical_vb.value
        empty_ce=open_vb_info.LOG.first_empty_CE.value
        empty_plane=open_vb_info.LOG.first_empty_plane.value
        empty_page=open_vb_info.LOG.first_empty_physical_page.value

        logger.flow(3, 'inject log blk empty page UECC')
        pca = PCA()
        pca.b4_mode = 1
        pca.b5_ce = empty_ce
        pca.b6_plane = empty_plane    
        pca.b11_block_h = (old_log_vb >> 8) & 0xFF
        pca.b10_block_l = old_log_vb & 0xFF
        for inject_page in range(empty_page, empty_page+4):
            logger.info(f'inject empty page{inject_page} UECC')
            pca.l12_fpage = convert_page_to_page_order(page=inject_page, isSLC=1)<<5
            inject_UECC(pca=pca)

        logger.flow(4, 'execute power up media scan')
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)

        logger.flow(5, f'check log vb is refresh')
        _, open_vb_info = api.get_open_vb_info()
        new_log_vb=open_vb_info.LOG.logical_vb.value
        if new_log_vb == old_log_vb:
            logger.error('log vb is not change')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
#=================================================================================================
        #PTE
#=================================================================================================

        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        #4096 node才會flush pte
        logger.flow(2, 'configure lun and write tlc vb 4096 size')
        self.config_lun()
        self.write_record = api.get_empty_write_record()      
        api.sequential_write(lun=0, start_lba=0, total_size=4096, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        _, open_vb_info = api.get_open_vb_info()
        old_pte_vb=open_vb_info.PTE.logical_vb.value
        empty_ce=open_vb_info.PTE.first_empty_CE.value
        empty_plane=open_vb_info.PTE.first_empty_plane.value
        empty_page=open_vb_info.PTE.first_empty_physical_page.value

        logger.flow(3, 'inject pte blk empty page UECC')
        pca = PCA()
        pca.b4_mode = 1
        pca.b5_ce = empty_ce
        pca.b6_plane = empty_plane    
        pca.b11_block_h = (old_pte_vb >> 8) & 0xFF
        pca.b10_block_l = old_pte_vb & 0xFF
        for inject_page in range(empty_page, empty_page+4):
            logger.info(f'inject empty page{inject_page} UECC')
            pca.l12_fpage = convert_page_to_page_order(page=inject_page, isSLC=1)<<5
            inject_UECC(pca=pca)

        logger.flow(4, 'execute power up media scan')
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
        
        logger.flow(5, f'check pte vb is refresh')
        _, open_vb_info = api.get_open_vb_info()
        new_pte_vb=open_vb_info.PTE.logical_vb.value
        if new_pte_vb == old_pte_vb:
            logger.error('pte vb is not change')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        pass

    def post_process(self) -> None:
        pass

    def config_lun(self) -> None:
        selector = 0x00
        length = 0xE6
        Total_AU_Count = shared.param.gGeometry.q4_total_raw_device_capacity // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
        EM1_total_AU = min(shared.param.gGeometry.l44_enhanced1_max_n_alloc_u, Total_AU_Count//2)
        normal_total_AU = Total_AU_Count//2
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
            desc.header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE
            desc.header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.DISABLE
            desc.header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
            desc.header.l18_num_shared_write_booster_buffer_alloc_units = shared.param.gGeometry.l79_write_booster_buffer_max_n_alloc_units if index==0 else 0
            
            for unit_idx in range(8):
                lun = index * 8 + unit_idx
                if lun ==0:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.NORMAL
                    desc.units[unit_idx].l4_num_alloc_units = normal_total_AU
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif lun==1:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = EM1_total_AU
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
        unit_desc_idxes:List[int] = []
        for lun in range(0, shared.param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

        for lun in range(shared.param.gMaxNumberLU):
            if shared.param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send()
        return
    
run = Pattern().run
if __name__ == "__main__":
    run()