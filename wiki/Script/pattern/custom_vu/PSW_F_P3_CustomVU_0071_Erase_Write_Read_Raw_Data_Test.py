import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from typing import List, cast, Optional
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from time import sleep
import math
from Script.project_api.functions import get_physical_layout
from Script.project_api.functions import print_object_info_ai


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.write_record = api.get_empty_write_record()
        _, self.debug_info = api.get_debug_info()
        self.config_lun()
        _flash_setting = api.get_flash_setting()
        _fw_geometry = api.get_fw_geometry()
        self.max_ce = _flash_setting.Max_Fdevice
        self.max_plane = _flash_setting.Plane_Per_Die
        pageline_block = self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
        self.WL_block = pageline_block * 4 * 3
        self.tlc_vb_size = (_fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.slc_vb_size = (_fw_geometry.l84_vb_size_u0 * 512 // 4096)
        
        pass

    def step1(self) -> None:
        logger.flow(1, 'write data to create TLC/SLC block')
        api.sequential_write(lun=0, start_lba=0, total_size=self.tlc_vb_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        lba = random.randint(0, self.tlc_vb_size)
        _, self.tlc_pca = project_api.issue_4051_to_get_physical_address(luID=0, lba=lba)
        api.sequential_write(lun=1, start_lba=0, total_size=self.slc_vb_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        lba = random.randint(0, self.slc_vb_size)
        _, self.slc_pca = project_api.issue_4051_to_get_physical_address(luID=1, lba=lba)
        pass

    def step2(self) -> None:
        for pca in [self.tlc_pca, self.slc_pca]:
            VB = pca.virtual_block_number.value
            Die = pca.die.value
            Plane = pca.plane.value
            Block = pca.physical_block_number_w_BBT.value
            Page = pca.page.value
            resp, BB_info = project_api.issue_40C7_to_get_bad_block_info(Block, Die*self.max_plane+Plane)
            if BB_info.replaced_physical_block.value != 0xFFFFFFFF:
                RemapPB = BB_info.replaced_physical_block.value
            else:
                RemapPB = Block
            
            SlcEnable = 1 if pca == self.slc_pca else 0
            _, WL_type, phy_WL, SubBlock, FlushGroup, TwoWLGroup, RainGoup = get_physical_layout(pageline=Page, block_type="SLC" if SlcEnable else "TLC")
            for p in range(Page - 1, -1, -1):
                _, _, _, temp_SB, _, _, _ = get_physical_layout(pageline=p, block_type="SLC" if SlcEnable else "TLC")
                if p < 0 or temp_SB != SubBlock:
                    break
                Page = p
            logger.info(f'VB = {VB}, PhyBlock = {Block}, RemapPB = {RemapPB}, CE = {Die}, Plane = {Plane}, Page = {Page}')

            logger.flow(2, 'issue 4060 to check original data')
            _,dire_read_payload = project_api.issue_4060_to_read_raw_data(Die=Die, Plane=Plane, Block=RemapPB, Page=Page, SLC_Enable=SlcEnable,Ecc_Enable=1, Scrambler_Enable=1, REH_Enable=0)
            dumpfile(filename=f"01_read_PhyBlock_{RemapPB}.bin", data=dire_read_payload)
            if dire_read_payload[0x4000:0x4004] != b'\x00\x00\x00\x00':
                logger.error_lb(f'check data after write')
                logger.error_fp(f'expect read_status of PhyBlock = {RemapPB} is 0(Normal), but current payload[4000:4003] = (0x{int.from_bytes(dire_read_payload[0x4000:0x4004],"little"):X}), result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(3, 'issue D060 to erase original data')
            project_api.issue_D060_to_erase_specific_block(Ce=Die,Plane=Plane,Block=RemapPB,SlcEnable=SlcEnable,psaEnable=0)
            
            logger.flow(4, 'issue 4060 to check data after erase')
            _,dire_read_payload = project_api.issue_4060_to_read_raw_data(Die=Die, Plane=Plane, Block=RemapPB, Page=Page, SLC_Enable=SlcEnable,Ecc_Enable=1, Scrambler_Enable=1, REH_Enable=0)
            dumpfile(filename=f"02_read_PhyBlock_{RemapPB}.bin", data=dire_read_payload)
            if dire_read_payload[0x4000:0x4004] != b'\x01\x01\x01\x01':
                logger.error_lb(f'check data after D060')
                logger.error_fp(f'expect read_status of PhyBlock = {RemapPB} is 1(Empty), but current payload[4000:4003] = (0x{int.from_bytes(dire_read_payload[0x4000:0x4004],"little"):X}), result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if SlcEnable:
                dire_write_payload = bytearray(DATA_SIZE_16K_BYTE)
            else:
                dire_write_payload = bytearray(DATA_SIZE_20K_BYTE*3)
            for i in range(len(dire_write_payload)):
                dire_write_payload[i] = 0xAA

            logger.flow(5, 'issue C060 to write raw data')
            project_api.issue_C060_to_write_raw_data(Ce=Die,Block=Block,Plane=Plane, Page=Page,SLC_Enable=SlcEnable,Ecc_Enable=1, datapayload=dire_write_payload)
            
            logger.flow(6, 'issue 4060 to check data after write')
            write_page = 1 if SlcEnable else 3 
            for i in range(write_page):
                _,dire_read_payload = project_api.issue_4060_to_read_raw_data(Die=Die, Plane=Plane, Block=RemapPB, Page=Page, SLC_Enable=SlcEnable,Ecc_Enable=1, Scrambler_Enable=1, REH_Enable=0)
                dumpfile(filename=f"03_read_PhyBlock_{RemapPB}_{i}.bin", data=dire_read_payload)
                if dire_read_payload[0x4000:0x4004] != b'\x00\x00\x00\x00':
                    logger.error_lb(f'check data after C060')
                    logger.error_fp(f'expect read_status of PhyBlock = {RemapPB} is 0(Normal), but current payload[4000:4003] = (0x{int.from_bytes(dire_read_payload[0x4000:0x4004],"little"):X}), result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                if dire_read_payload[0x0000:0x4000] != dire_write_payload[i*0x4000:(i+1)*0x4000]:
                    logger.error_lb(f'check data after C060 write all 0xAA data')
                    logger.error_fp(f'expect data is all 0xAA, but current data not correct, result Fail!')
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