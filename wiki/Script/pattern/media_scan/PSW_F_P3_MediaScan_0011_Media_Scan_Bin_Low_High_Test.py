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
from Script.pattern.refresh.mutual_fun import get_VB_group
from Script.project_api.custom_vu.media_scan_vu.structs import *
from Script.project_api.custom_vu.lba_convert_vu import issue_4051_to_get_physical_address
from Script.pattern.apl_system_rebuild.mutual_fun import *

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
        #Open TLC vb bin < BIN_LOW should skip scan
#=================================================================================================
        
        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(2, 'config lun and write tlc 2000 pageline size')
        self.config_lun()
        pageline_block = self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
        write_size = pageline_block*2000
        api.sequential_write(lun=0, start_lba=0, total_size=write_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        _,micron_pca = issue_4051_to_get_physical_address(0, write_size-1)
        logger.info(f'die={micron_pca.die.value}, Plane={micron_pca.plane.value}, Block={micron_pca.virtual_block_number.value}, Page={micron_pca.page.value}')        

        logger.flow(3, 'check write vb is current l2 mlc vb')
        temppca = PCA()
        temppca.from_bytes(bytearray(api.lba_to_pba(lun=0, lba=write_size-1).payload))
        logger.info(f'Block = {(temppca.b11_block_h<<8) | (temppca.b10_block_l)}, mode = {temppca.b4_mode}, CE = {temppca.b5_ce}, Plane = {temppca.b6_plane}, fPage = {temppca.l12_fpage}(pageline = {temppca.l12_fpage>>5}), lmu = {temppca.b20_lmu}, format = {temppca.b7_format}')
        cur_l2_vb=(temppca.b11_block_h<<8) | (temppca.b10_block_l)
        ftl_vb_list_data_before = get_VB_group()
        if project_api.VB_GROUP(ftl_vb_list_data_before[cur_l2_vb]["group"]) != project_api.VB_GROUP.CURRENT_L2_MLC:        
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(4, 'set media scan BIN_LOW=10')
        set_mconfig_bin_low = 10
        param = micron_vu_C085_param_with_data()
        param.set_media_scan_bin_low = set_mconfig_bin_low
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        logger.flow(5,'Issue 40B0 VUC to BFEA Scan (set BFEA table), set bf scan bin=9')
        set_bf_bin=9
        for ce in range(self.max_ce):
            rsp = project_api.issue_40B0_Bfea_Scan(2, cur_l2_vb, ce, set_bf_bin)

        logger.flow(6,'Issue 40B0 VUC to BFEA Scan (get BFEA table)')
        for ce in range(self.max_ce):
            buf = project_api.issue_40B0_Bfea_Scan(3, cur_l2_vb, ce, 0)
            logger.info('Host get Byte[0-3]output of this vendor cmd  should be 0(Bin index)')
            output = int.from_bytes(buf[0:4], byteorder='little')
            dumpfile('bfea_scan_vb_rsp.bin',buf)
            if output != set_bf_bin:
                logger.error_fp(f'output = {output} != expected_value {set_bf_bin}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(7, f'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_group = payload.scan_group.value
        
        logger.flow(8, f'Trigger media scan')
        spend_time_set = 0x1000000
        while 1:
            
            param = micron_vu_C085_param_with_data()
            param.set_media_scan_bin_low = set_mconfig_bin_low
            param.last_scan_spend_time = spend_time_set
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)
            
            time.sleep(5)

            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            if new_scan_vb == 0xFFFFFFFF and new_scan_page == 0xFFFFFFFF:
                logger.flow(9, f'check open tlc vb should skip scan')
                for scanned_vb in payload.scanned_blocks:
                    logger.info('scanned blocks=%d', scanned_vb)
                    if scanned_vb == cur_l2_vb:
                        logger.error('open tlc blk should skip scan')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if new_scan_group == old_scan_group:
                logger.info('scan all group, test done')
                break
            spend_time_set+=0x100

#=================================================================================================
        #Close TLC vb bin < BIN_LOW should skip scan
#=================================================================================================

        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(2, 'config lun and write tlc one vb size')
        self.config_lun()
        api.sequential_write(lun=0, start_lba=0, total_size=self.tlc_vb_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        logger.flow(3, 'check write vb is mlc used pool vb')
        temppca = PCA()
        temppca.from_bytes(bytearray(api.lba_to_pba(lun=0, lba=0).payload))
        logger.info(f'Block = {(temppca.b11_block_h<<8) | (temppca.b10_block_l)}, mode = {temppca.b4_mode}, CE = {temppca.b5_ce}, Plane = {temppca.b6_plane}, fPage = {temppca.l12_fpage}(pageline = {temppca.l12_fpage>>5}), lmu = {temppca.b20_lmu}, format = {temppca.b7_format}')
        used_vb=(temppca.b11_block_h<<8) | (temppca.b10_block_l)
        ftl_vb_list_data_before = get_VB_group()
        if project_api.VB_GROUP(ftl_vb_list_data_before[used_vb]["group"]) != project_api.VB_GROUP.USED_BLK_POOL_MLC:        
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(4, 'set media scan BIN_LOW=10')
        set_mconfig_bin_low = 10
        param = micron_vu_C085_param_with_data()
        param.set_media_scan_bin_low = set_mconfig_bin_low
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        logger.flow(5,'Issue 40B0 VUC to BFEA Scan (set BFEA table)')
        set_bf_bin=9
        for ce in range(self.max_ce):
            rsp = project_api.issue_40B0_Bfea_Scan(2, used_vb, ce, set_bf_bin)

        logger.flow(6,'Issue 40B0 VUC to BFEA Scan (get BFEA table)')
        for ce in range(self.max_ce):
            buf = project_api.issue_40B0_Bfea_Scan(3, used_vb, ce, 0)
            logger.info('Host get Byte[0-3]output of this vendor cmd  should be 0(Bin index)')
            output = int.from_bytes(buf[0:4], byteorder='little')
            dumpfile('bfea_scan_vb_rsp.bin',buf)
            if output != set_bf_bin:
                logger.error_fp(f'output = {output} != expected_value {set_bf_bin}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(7, f'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(8, f'idle trigger media scan next group finish')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_group = payload.scan_group.value
        spend_time_set = 0x1000000
        param = micron_vu_C085_param_with_data()
        param.set_media_scan_bin_low = set_mconfig_bin_low
        param.last_scan_spend_time = spend_time_set
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        time.sleep(5)

        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        new_scan_vb = payload.cur_scan_vb.value
        new_scan_page = payload.cur_scan_page.value
        new_scan_group = payload.scan_group.value
        logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
        if old_scan_group == 22:
            if new_scan_vb != 0xFFFFFFFF or new_scan_page != 0xFFFFFFFF or new_scan_group != 0:
                logger.error(f'scan group unexpected, new_scan_group={new_scan_group}, expected scan group=0')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        elif new_scan_vb != 0xFFFFFFFF or new_scan_page != 0xFFFFFFFF or new_scan_group != old_scan_group+1:
            logger.error(f'scan group unexpected, new_scan_group={new_scan_group}, old_scan_group={old_scan_group}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(9, f'check used tlc vb should skip scanned')
        for scan_vb in payload.scanned_blocks:
            logger.info('scanned blocks=%d', scan_vb)
            if scan_vb == used_vb:
                logger.error(f'used_vb={used_vb} should skip scan')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
#=================================================================================================
        #Close TLC vb bin > BIN_HIGH should booking refreshQ
#=================================================================================================

        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(2, 'config lun and write tlc one vb size')
        self.config_lun()
        api.sequential_write(lun=0, start_lba=0, total_size=self.tlc_vb_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        logger.flow(3, 'check write vb is mlc used pool vb')
        temppca = PCA()
        temppca.from_bytes(bytearray(api.lba_to_pba(lun=0, lba=0).payload))
        logger.info(f'Block = {(temppca.b11_block_h<<8) | (temppca.b10_block_l)}, mode = {temppca.b4_mode}, CE = {temppca.b5_ce}, Plane = {temppca.b6_plane}, fPage = {temppca.l12_fpage}(pageline = {temppca.l12_fpage>>5}), lmu = {temppca.b20_lmu}, format = {temppca.b7_format}')
        used_vb=(temppca.b11_block_h<<8) | (temppca.b10_block_l)
        ftl_vb_list_data_before = get_VB_group()
        if project_api.VB_GROUP(ftl_vb_list_data_before[used_vb]["group"]) != project_api.VB_GROUP.USED_BLK_POOL_MLC:        
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(4, 'set media scan BIN_LOW=8, BIN_HIGH=10')
        set_mconfig_bin_low = 8
        set_mconfig_bin_high = 10
        param = micron_vu_C085_param_with_data()
        param.set_media_scan_bin_low = set_mconfig_bin_low
        param.set_media_scan_bin_high = set_mconfig_bin_high
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        logger.flow(5,'Issue 40B0 VUC to BFEA Scan (set BFEA table), set bf scan bin=11')
        set_bf_bin=11
        for ce in range(self.max_ce):
            rsp = project_api.issue_40B0_Bfea_Scan(2, used_vb, ce, set_bf_bin)

        logger.flow(6,'Issue 40B0 VUC to BFEA Scan (get BFEA table)')
        for ce in range(self.max_ce):
            buf = project_api.issue_40B0_Bfea_Scan(3, used_vb, ce, 0)
            logger.info('Host get Byte[0-3]output of this vendor cmd  should be 0(Bin index)')
            output = int.from_bytes(buf[0:4], byteorder='little')
            dumpfile('bfea_scan_vb_rsp.bin',buf)
            if output != set_bf_bin:
                logger.error_fp(f'output = {output} != expected_value {set_bf_bin}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(7, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)         
        
        logger.flow(8, f'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(9, 'check close tlc vb should booking refreshQ')
        spend_time_set = 0x1000000
        param = micron_vu_C085_param_with_data()
        param.set_media_scan_bin_low = set_mconfig_bin_low
        param.set_media_scan_bin_high = set_mconfig_bin_high
        param.last_scan_spend_time = spend_time_set
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        time.sleep(5)

        logger.info('issue 40C5 to check if the Booking Queue is correct')
        _, booking_q_before = project_api.issue_40C5_to_get_booking_queue()
        if booking_q_before.LogicalVBNumberInBookingQueue.value != 0:
            for idx, vb in enumerate(booking_q_before.BookingQueueVB):
                logger.info(f'BookingQ[{idx}]: VB {vb.LogicalVBNumber.value}')
                if vb.LogicalVBNumber.value != used_vb:
                    logger.error(f'BookingQ_VB not vb{used_vb}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.error(f'used_vb={used_vb} should booking refreshQ')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
#=================================================================================================
        #Close TLC vb bin < BIN_HIGH and > BIN_LOW should be scanned
#=================================================================================================            
        
        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(2, 'config lun and write tlc one vb size')
        self.config_lun()
        api.sequential_write(lun=0, start_lba=0, total_size=self.tlc_vb_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        logger.flow(3, 'check write vb is mlc used pool vb')
        temppca = PCA()
        temppca.from_bytes(bytearray(api.lba_to_pba(lun=0, lba=0).payload))
        logger.info(f'Block = {(temppca.b11_block_h<<8) | (temppca.b10_block_l)}, mode = {temppca.b4_mode}, CE = {temppca.b5_ce}, Plane = {temppca.b6_plane}, fPage = {temppca.l12_fpage}(pageline = {temppca.l12_fpage>>5}), lmu = {temppca.b20_lmu}, format = {temppca.b7_format}')
        used_vb=(temppca.b11_block_h<<8) | (temppca.b10_block_l)
        ftl_vb_list_data_before = get_VB_group()
        if project_api.VB_GROUP(ftl_vb_list_data_before[used_vb]["group"]) != project_api.VB_GROUP.USED_BLK_POOL_MLC:        
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(4, 'set media scan BIN_LOW=8, BIN_HIGH=10')
        set_mconfig_bin_low = 8
        set_mconfig_bin_high = 10
        param = micron_vu_C085_param_with_data()
        param.set_media_scan_bin_low = set_mconfig_bin_low
        param.set_media_scan_bin_high = set_mconfig_bin_high
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        logger.flow(5,'Issue 40B0 VUC to BFEA Scan (set BFEA table), set bf scan bin=9')
        set_bf_bin=9
        for ce in range(self.max_ce):
            rsp = project_api.issue_40B0_Bfea_Scan(2, used_vb, ce, set_bf_bin)

        logger.flow(6,'Issue 40B0 VUC to BFEA Scan (get BFEA table)')
        for ce in range(self.max_ce):
            buf = project_api.issue_40B0_Bfea_Scan(3, used_vb, ce, 0)
            logger.info('Host get Byte[0-3]output of this vendor cmd  should be 0(Bin index)')
            output = int.from_bytes(buf[0:4], byteorder='little')
            dumpfile('bfea_scan_vb_rsp.bin',buf)
            if output != set_bf_bin:
                logger.error_fp(f'output = {output} != expected_value {set_bf_bin}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(7, f'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(8, 'check close tlc vb should be scanned')
        spend_time_set = 0x1000000
        param = micron_vu_C085_param_with_data()
        param.set_media_scan_bin_low = set_mconfig_bin_low
        param.set_media_scan_bin_high = set_mconfig_bin_high
        param.last_scan_spend_time = spend_time_set
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        time.sleep(5)

        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        if used_vb not in payload.scanned_blocks:
            logger.info(payload.scanned_blocks)
            logger.error(f'used_vb={used_vb} should be scanned')
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