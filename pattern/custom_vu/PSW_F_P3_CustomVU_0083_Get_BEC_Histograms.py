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
from Script.project_api.custom_vu.media_scan_vu.structs import *
from Script.project_api.custom_vu.lba_convert_vu import issue_4051_to_get_physical_address
from Script.project_api.custom_vu.raw_data_vu.functions import issue_4060_to_read_raw_data
from Script.pattern.apl_system_rebuild.mutual_fun import *
from Script.project_api.reh.functions import issue_409E_to_get_error_bit_numbers

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.write_record = api.get_empty_write_record()
        self.flash_setting = api.get_flash_setting()
        self._fw_geometry = api.get_fw_geometry()
        self.max_ce = self.flash_setting.Max_Fdevice
        self.max_plane = self.flash_setting.Plane_Per_Die
        pageline_block = self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
        self.WL_block = pageline_block * 4 * 3
        self.tlc_vb_size = (self._fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.slc_vb_size = (self._fw_geometry.l84_vb_size_u0 * 512 // 4096)
        
        pass

    def step1(self) -> None:
        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)
        pass

    def step2(self) -> None:

        flipbit_list = [x for x in range(0, 384, 4)]

        for flipbit in flipbit_list:

            logger.flow(2, 'config lun and write tlc ce page' )
            self.config_lun()
            tlc_ce_page = self.flash_setting.Plane_Per_Die * 4 * 3
            api.sequential_write(lun=0, start_lba=0, total_size=int(tlc_ce_page), chunk_size=tlc_ce_page, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

            logger.flow(3, f'inject flipbit = {flipbit} on tlc block' )
            error_bits_from_vu409E = self.flipbit_on_TLC(flipbit_set=flipbit)
            
            logger.flow(4, 'vu4026 reset bec historgrams, check bec historgrams is reseted')
            resp, payload = project_api.issue_4026_to_get_BEC_histograms_information(reset_enable=1)
            if not all(all(x == 0 for x in l) for l in [payload.tlc_histogram_die0, payload.tlc_histogram_die1, payload.tlc_histogram_die2, payload.tlc_histogram_die3]):
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(5, 'vu4028 trigger media scan with tlc blk')
            temppca = PCA()
            self.tlc_pca = api.lba_to_pba(lun=0, lba=0)
            temppca.from_bytes(bytearray(self.tlc_pca.payload))            
            parm = micron_vu_4028_param()
            parm.d16_die = temppca.b5_ce
            parm.d20_plane = temppca.b6_plane
            parm.d24_block = (temppca.b11_block_h<<8) | (temppca.b10_block_l)
            parm.d28_page = temppca.l12_fpage>>5
            parm.b40_slc_mode = 0
            parm.b41_bfea_bin = 0
            parm.b42_page_attr = 3 #Must align with page: 0--SLC   1--MLC_LP  2--MLC_UP 3--TLC_LP 4--TLC_UP   5--TLC_XP
            parm.b43_is_blank_page = 0 #1： is blank page   0：is not blank page
            parm.b44_is_partial_block = 1 #0: is full block  1: is partial block
            parm.b45_is_em1_vb = 0 #0 is not EM1   1: is EM1
            resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(parm)
            if payload.media_scan_status.value == 0xFF:
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            logger.flow(6, 'get vu4026 bec historgrams')
            resp, payload_new = project_api.issue_4026_to_get_BEC_histograms_information(reset_enable=0)

            logger.flow(7, 'check bec historgrams expected')
            if flipbit <= 0x08:
                bin0_bec_cnt = int.from_bytes(bytes(payload_new.tlc_histogram_die0[0:3]), byteorder='little')
                bin1_bec_cnt = int.from_bytes(bytes(payload_new.tlc_histogram_die0[4:7]), byteorder='little')
                bin2_bec_cnt = int.from_bytes(bytes(payload_new.tlc_histogram_die0[8:11]), byteorder='little')
                if bin0_bec_cnt+bin1_bec_cnt+bin2_bec_cnt != 0x04:
                    logger.error(f'bin0_bec_cnt={bin0_bec_cnt}, bin1_bec_cnt={bin1_bec_cnt}, bin2_bec_cnt={bin2_bec_cnt}, expected total=4')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                for bin_num in range(3, 95):
                    bin_num_offset = bin_num*4
                    bec_cnt = int.from_bytes(bytes(payload_new.tlc_histogram_die0[bin_num_offset:bin_num_offset+3]), byteorder='little')
                    if bec_cnt != 0x00:
                        logger.error(f'bin_num={bin_num}, bec_cnt_result={bec_cnt}, expected total=0')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    
            elif payload.bec.value >= 320:
                bin_x = 80
                bin80_bec_cnt = int.from_bytes(bytes(payload_new.tlc_histogram_die0[320:323]), byteorder='little')
                if bin80_bec_cnt != 0x04:
                    logger.error(f'bin80_bec_cnt={bin80_bec_cnt}, expected=4')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

                for bin_num in range(2, 95):
                    if bin_num==bin_x:
                        continue
                    bec_cnt = int.from_bytes(bytes(payload_new.tlc_histogram_die0[bin_num*4:bin_num*4+3]), byteorder='little')
                    if bec_cnt != 0x00:
                        logger.error(f'bin_num={bin_num}, bec_cnt_result={bec_cnt}, expected total=0')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL                
            else:
                bin0_bec_cnt = int.from_bytes(bytes(payload_new.tlc_histogram_die0[0:3]), byteorder='little')
                bin1_bec_cnt = int.from_bytes(bytes(payload_new.tlc_histogram_die0[4:7]), byteorder='little')
                if bin0_bec_cnt+bin1_bec_cnt != 0x03:
                    logger.error(f'bin0_bec_cnt={bin0_bec_cnt}, bin1_bec_cnt={bin1_bec_cnt}, expected total=3')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                expect_bin = error_bits_from_vu409E[0] // 4
                previous_previous_bin = expect_bin-2
                previous_bin =  expect_bin-1
                next_bin =  expect_bin+1

                expect_bin_bec = int.from_bytes(bytes(payload_new.tlc_histogram_die0[expect_bin*4:expect_bin*4+3]), byteorder='little')
                previous_previous_bin_bec = int.from_bytes(bytes(payload_new.tlc_histogram_die0[previous_previous_bin*4:previous_previous_bin*4+3]), byteorder='little')
                previous_bin_bec = int.from_bytes(bytes(payload_new.tlc_histogram_die0[previous_bin*4:previous_bin*4+3]), byteorder='little')
                next_bin_bec = int.from_bytes(bytes(payload_new.tlc_histogram_die0[next_bin*4:next_bin*4+3]), byteorder='little')
                if expect_bin_bec+previous_bin_bec+next_bin_bec+previous_previous_bin_bec != 0x01:
                    logger.error(f'expect_bin_bec={expect_bin_bec}, previous_bin_bec={previous_bin_bec}, next_bin_bec={next_bin_bec}, previous_previous_bin_bec={previous_previous_bin_bec}, expected total=1')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                bin_x = previous_bin if previous_bin_bec == 0x1 else (expect_bin if expect_bin_bec == 0x01 else (next_bin if next_bin_bec == 0x01 else previous_previous_bin))

                for bin_num in range(2, 95):
                    if bin_num==bin_x:
                        continue
                    bec_cnt = int.from_bytes(bytes(payload_new.tlc_histogram_die0[bin_num*4:bin_num*4+3]), byteorder='little')
                    if bec_cnt != 0x00:
                        logger.error(f'bin_num={bin_num}, bec_cnt_result={bec_cnt}, expected total=0')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
        pass

    def post_process(self) -> None:
        pass

    def flipbit_on_TLC(self, flipbit_set:int=0)->list[int]:

        logger.flow(3, f'GET Open vb information by VU 0x40C1 as table2')
        get_open_vb = get_and_print_open_vb_information()
        testlba = 0
        isTLC = 0
        _,micron_pca = issue_4051_to_get_physical_address(0, testlba)
        _, raw_data = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isTLC, Ecc_Enable=1, Scrambler_Enable=1)
        dumpfile(f"direct_read_data_idx3.bin", raw_data)
        logger.flow(13, f'Issue 409E VUC with ECC information = 1 to get error bit numbers')
        _, output_409E = issue_409E_to_get_error_bit_numbers()
        error_bits_409E = [output_409E.errorBitNumber1.value, output_409E.errorBitNumber2.value, output_409E.errorBitNumber3.value, output_409E.errorBitNumber4.value]
        logger.info(f'409E error bits ={error_bits_409E}')
        project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x00)
        isTLC = 0
        _, raw_dataLP = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isTLC, Ecc_Enable=0, Scrambler_Enable=0)
        raw_dataLP_1 = copy.deepcopy(raw_dataLP)
        dumpfile(f"pageLP.bin", raw_dataLP)
        #LP_fwrite = rebuild_payload_mv(raw_data)
        LP_fwrite = raw_dataLP
        _, raw_dataUP = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value+1, SLC_Enable=isTLC, Ecc_Enable=0, Scrambler_Enable=0)
        raw_dataUP_1 = copy.deepcopy(raw_dataUP)
        dumpfile(f"pageUP.bin", raw_dataUP)        
        #UP_fwrite = rebuild_payload_mv(raw_data)
        UP_fwrite = raw_dataUP
        _, raw_data_XP = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value+2, SLC_Enable=isTLC, Ecc_Enable=0, Scrambler_Enable=0)
        raw_data_XP_1 = copy.deepcopy(raw_data_XP)
        dumpfile(f"pageXP.bin", raw_data_XP)
        #XP_fwrite = rebuild_payload_mv(raw_data)
        XP_fwrite = raw_data_XP
        raw_data_flip = LP_fwrite #ecc on
        
        diffcount = count_diff_bytes(raw_dataLP, raw_data_flip)
        logger.info(f'LP different count ={diffcount}')
        #flipped = flip_bits(raw_data_flip)                # 直接使用預設 start_bit=0, count=500
        flipbit = flipbit_set
        flipped = flip_bits_one_per_byte(raw_data_flip, total_bits=flipbit, block_index=0) 
        diffcount = count_diff_bytes(raw_dataLP_1, raw_data_flip)
        logger.info(f'LP different count ={diffcount} after flip bits {flipbit}')
        print_bit_positions(flipped, title=f"{flipbit} bits position")
        logger.info(f"Flip first {flipbit} bits – done")
        logger.info(f"raw_data_flip = {len(raw_data_flip)}") 
        write_payload = build_write_payload(raw_data_flip, UP_fwrite, XP_fwrite)
        print(len(write_payload))
        #erase
        die = 1 << micron_pca.die.value
        plane = 1 << micron_pca.plane.value
        #rsp, payload = issue_40F6_to_erase_in_direct_nand_mode(die, plane, micron_pca.virtual_block_number.value, micron_pca.virtual_block_number.value+1,slc_enable=0)   
        logger.flow(3, 'issue D060 to erase original data')
        #project_api.issue_D060_to_erase_specific_block(Ce=die,Plane=plane,Block=micron_pca.virtual_block_number.value,SlcEnable=0,psaEnable=0)
        project_api.issue_D060_to_erase_specific_block(Ce=micron_pca.die.value,Plane=micron_pca.plane.value,Block=micron_pca.virtual_block_number.value,SlcEnable=0,psaEnable=0)
            
        #write raw data
        dumpfile(f"FLIP_Write.bin", write_payload)
        _ = project_api.issue_C060_to_write_raw_data(Ce=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isTLC,Ecc_Enable=0, datapayload=write_payload)
        
        #read raw data
        _, raw_data_1 = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isTLC, Ecc_Enable=1, Scrambler_Enable=1)
        raw_data_11 = copy.deepcopy(raw_data_1)
        diffcount = count_diff_bytes(raw_dataLP, raw_data_11)
        logger.info(f'LP different count ={diffcount}')
        dumpfile(f"FW_FLOW_READ.bin", raw_data_11)
        logger.flow(13, f'Issue 409E VUC with ECC information = 1 to get error bit numbers')
        _, output_409E = issue_409E_to_get_error_bit_numbers()
        error_bits_409E = [output_409E.errorBitNumber1.value, output_409E.errorBitNumber2.value, output_409E.errorBitNumber3.value, output_409E.errorBitNumber4.value]
        logger.info(f'409E error bits ={error_bits_409E}')
        logger.info(f'flipbit_set={flipbit_set}, vu409E get 1st 4k err bit={error_bits_409E[0]}')

        _, raw_dataLP_after = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isTLC, Ecc_Enable=0, Scrambler_Enable=0)
        raw_dataLP_after_1 = copy.deepcopy(raw_dataLP_after)
        dumpfile(f"pageLP_after.bin", raw_dataLP_after_1)
        diffcount = count_diff_bytes(raw_dataLP_1, raw_dataLP_after_1)
        logger.info(f'LP different count ={diffcount}')
        
        return error_bits_409E
    
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