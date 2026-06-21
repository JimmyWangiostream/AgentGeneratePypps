from Script import api
import datetime
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from typing import List, cast, Optional
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from time import sleep
from Script.project_api.custom_vu.media_scan_vu.structs import *
from Script.pattern.apl_system_rebuild.mutual_fun import *

RESET_COMMANDS: Final[Mapping[int, str]] = {
    0:      "hw_reset",      # Hardware Reset
    1:       "reset_n",       # Reset‑N
    2:  "endpoint_rst",  # Endpoint Reset
    3:    "unipro_rst",    # UniPro Reset
}

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.write_record = api.get_empty_write_record()
        self.flash_setting = api.get_flash_setting()
        self._fw_geometry = api.get_fw_geometry()
        self.max_ce = self.flash_setting.Max_Fdevice
        self.max_plane = self.flash_setting.Plane_Per_Die
        pageline_block = self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
        self.TLC_WL_block = pageline_block * 4 * 3
        self.SLC_WL_block = pageline_block * 4
        self.tlc_vb_size = (self._fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.slc_vb_size = (self._fw_geometry.l84_vb_size_u0 * 512 // 4096)
        pass

    def step1(self) -> None:
        
#=================================================================================================
        #vuD018 verify media scan not triggered -> media scan should trigger after reset
#=================================================================================================

        for reset_type in range (api.Dcmd5ResetType.HW_RESET,api.Dcmd5ResetType.RESET_N+1):

            logger.flow(1, 'vuD018 disable DM_Bg_Task_In_Bank')
            project_api.issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(flag=True)

            logger.flow(2, 'configure lun and write slc tlc one vb size')
            self.config_lun_and_write_slc_tlc_partition()

            logger.flow(3, 'vuC085 set last scan spend time = 0x1000000 to trigger next scan group')
            param = micron_vu_C085_param_with_data()
            param.last_scan_spend_time = 0x1000000
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)

            logger.flow(4, 'vu40CF get current scan vb/page/scangroup')
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            old_scan_vb = payload.cur_scan_vb.value
            old_scan_page = payload.cur_scan_page.value
            old_scan_group = payload.scan_group.value
            logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

            logger.flow(5, 'idle trigger media scan and check media scan is not triggered within 60 seconds')
            start_time = datetime.datetime.now()
            while 1:
                resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
                new_scan_vb = payload.cur_scan_vb.value
                new_scan_page = payload.cur_scan_page.value
                new_scan_group = payload.scan_group.value
                logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
                if new_scan_vb != old_scan_vb or new_scan_page != old_scan_page or new_scan_group != old_scan_group:
                    logger.info('media scan should not trigger')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                time.sleep(1)
                diff_time = datetime.datetime.now() - start_time
                if diff_time.seconds > 60:
                    logger.info('[PASS] test over 1 min not trigger scan')
                    break

            logger.flow(6, f'power reset, reset event = {RESET_COMMANDS.get(reset_type)}')
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(reset_type))

            logger.flow(7, 'vu40CF get current scan vb/page/scangroup')
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            old_scan_vb = payload.cur_scan_vb.value
            old_scan_page = payload.cur_scan_page.value
            old_scan_group = payload.scan_group.value
            logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

            logger.flow(8, 'vuC085 set last scan spend time = 0x2000000 to trigger next scan group')
            param = micron_vu_C085_param_with_data()
            param.last_scan_spend_time = 0x2000000
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)

            logger.flow(9, 'delay 1s')
            time.sleep(1)

            logger.flow(10, 'vu40CF get current scan vb/page/scangroup')
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            
            logger.flow(11, 'check media scan is triggered')
            if new_scan_vb == old_scan_vb and new_scan_page == old_scan_page:
                logger.error('media scan should trigger')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
#=================================================================================================
        #vuD018 set enable, media scan should triggered 
#================================================================================================= 

        logger.flow(1, 'vuD018 disable DM_Bg_Task_In_Bank')
        project_api.issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(flag=True)

        logger.flow(2, 'configure lun and write slc tlc one vb size')
        self.config_lun_and_write_slc_tlc_partition()

        logger.flow(3, 'vuC085 set last scan spend time = 0x1000000 to trigger next scan group')
        param = micron_vu_C085_param_with_data()
        param.last_scan_spend_time = 0x1000000
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        logger.flow(4, 'vu40CF get current scan vb/page/scangroup')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value
        logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

        logger.flow(5, 'idle trigger media scan and check media scan is not triggered within 60 seconds')
        start_time = datetime.datetime.now()
        while 1:
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            if new_scan_vb != old_scan_vb or new_scan_page != old_scan_page or new_scan_group != old_scan_group:
                logger.info('media scan should not trigger')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            time.sleep(1)
            diff_time = datetime.datetime.now() - start_time
            if diff_time.seconds > 60:
                logger.info('[PASS] test over 1 min not trigger scan')
                break

        logger.flow(6, 'vu40CF get current scan vb/page/scangroup')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value
        logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

        logger.flow(7, 'vuC085 set last scan spend time = 0x2000000 to trigger next scan group')
        param = micron_vu_C085_param_with_data()
        param.last_scan_spend_time = 0x8000000
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        logger.flow(8, 'vuD018 enable DM_Bg_Task_In_Bank')
        project_api.issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(flag=False)            

        logger.flow(9, 'delay 1s')
        time.sleep(1)

        logger.flow(10, 'vu40CF get current scan vb/page/scangroup')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        new_scan_vb = payload.cur_scan_vb.value
        new_scan_page = payload.cur_scan_page.value
        new_scan_group = payload.scan_group.value
        logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
        
        logger.flow(11, 'check media scan is triggered')
        if new_scan_vb == old_scan_vb and new_scan_page == old_scan_page:
            logger.info('media scan should trigger')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

#=================================================================================================
        #verify disable media scan case
#=================================================================================================
        
        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(2, 'configure lun and write slc tlc one vb size')
        self.config_lun_and_write_slc_tlc_partition()

        logger.flow(3, 'vu40CF get current scan vb/page/scangroup')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value
        logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')        

        logger.flow(4, 'vuC085 set last scan spend time = 0x1000000 to trigger next scan group')
        param = micron_vu_C085_param_with_data()
        param.last_scan_spend_time = 0x1000000
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        logger.flow(5, 'idle trigger media scan and check media scan is not triggered within 60 seconds')
        start_time = datetime.datetime.now()
        while 1:
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            if new_scan_vb != old_scan_vb or new_scan_page != old_scan_page or new_scan_group != old_scan_group:
                logger.info('media scan should not trigger')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            time.sleep(1)
            diff_time = datetime.datetime.now() - start_time
            if diff_time.seconds > 60:
                logger.info('[PASS] test over 1 min not trigger scan')
                break

#=================================================================================================
        #verify enable media scan case
#=================================================================================================        
        
        logger.flow(1, 'configure lun and write slc tlc one vb size')
        self.config_lun_and_write_slc_tlc_partition()

        logger.flow(2, 'vu40CF get current scan vb/page/scangroup')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value
        logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

        logger.flow(3, 'vuC085 set last scan spend time = 0x1000000 to trigger next scan group')
        param = micron_vu_C085_param_with_data()
        param.last_scan_spend_time = 0x1000000
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        logger.flow(4, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(5, 'delay 1s')
        time.sleep(1)

        logger.flow(6, 'vu40CF get current scan vb/page/scangroup')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        new_scan_vb = payload.cur_scan_vb.value
        new_scan_page = payload.cur_scan_page.value
        new_scan_group = payload.scan_group.value
        logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')

        logger.flow(7, 'check media scan is triggered')
        if new_scan_vb == old_scan_vb and new_scan_page == old_scan_page:
            logger.info('media scan should trigger')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

#=================================================================================================
        #verify reset to enable media scan after reset mode
#=================================================================================================        
        
        for reset_type in range (api.Dcmd5ResetType.HW_RESET,api.Dcmd5ResetType.UNIPRO_RESET+1):

            logger.flow(1, 'vuC08B disable media scan')
            response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

            logger.flow(2, 'vu40CF check media scan is disable')
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            if payload.scan_status.value == 0x01:
                logger.info('media scan should disable')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            logger.flow(3, f'[reset mode] reset event = {RESET_COMMANDS.get(reset_type)}')
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(reset_type))
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()

            logger.flow(4, 'check media scan enable/disable expected')
            if reset_type == api.Dcmd5ResetType.HW_RESET or reset_type == api.Dcmd5ResetType.RESET_N:
                if payload.scan_status.value == 0x00:
                    logger.info('power loss, media scan should enable')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
            elif reset_type == api.Dcmd5ResetType.ENDPOINT_RESET or reset_type == api.Dcmd5ResetType.UNIPRO_RESET:
                if payload.scan_status.value == 0x01:
                    logger.info('sw reset, media scan should disable')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)
        
#=================================================================================================
        #掃描過程中被中斷，FW Keep掃描的頁面，下次啟動時從keep頁面繼續掃描
#================================================================================================= 
        
        logger.flow(1, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(2, 'configure lun and write slc tlc one vb size')
        self.config_lun_and_write_slc_tlc_partition()

        logger.flow(3, 'vuC085 set last scan spend time = 0x1000000 to trigger next scan group')
        param = micron_vu_C085_param_with_data()
        param.last_scan_spend_time = 0x1000000
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        logger.flow(4, 'idle trigger media scan finish')
        old_vb_seq_scan_map=[]
        while 1:
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            scan_vb = payload.cur_scan_vb.value
            scan_page = payload.cur_scan_page.value
            scan_group = payload.scan_group.value
            logger.info(f'scan_vb={scan_vb}, scan_page={scan_page}, scan_group={scan_group}')
            if scan_vb == 0xFFFFFFFF and scan_page == 0xFFFFFFFF:
                break
            if scan_vb not in old_vb_seq_scan_map:
                old_vb_seq_scan_map.append(scan_vb)

        logger.flow(5, 'vuC085 set last scan spend time = 0x2000000 to trigger next scan group')
        param = micron_vu_C085_param_with_data()
        param.last_scan_spend_time = 0x2000000
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        logger.flow(6, 'idle 1s')
        time.sleep(1)

        logger.flow(7, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(8, 'vu40CF get current scan vb/page/scangroup')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value
        logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

        logger.flow(9, 'idle 1s')
        time.sleep(1)

        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        new_scan_vb = payload.cur_scan_vb.value
        new_scan_page = payload.cur_scan_page.value
        new_scan_group = payload.scan_group.value
        logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
        if new_scan_vb != old_scan_vb or new_scan_page != old_scan_page or new_scan_group != old_scan_group:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(10, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)
        
        logger.flow(11, 'check continue scanning from the last scanned page position. ')
        while 1:
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            scan_vb = payload.cur_scan_vb.value
            scan_page = payload.cur_scan_page.value
            scan_group = payload.scan_group.value
            logger.info(f'scan_vb={scan_vb}, scan_page={scan_page}, scan_group={scan_group}')
            if scan_vb == old_scan_vb:
                if scan_page > old_scan_page:
                    break
            else:
                find_cur_index = old_vb_seq_scan_map.index(old_scan_vb)
                if old_vb_seq_scan_map[find_cur_index+1] != scan_vb:
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    break

        pass


    def post_process(self) -> None:
        pass
    

    def config_lun_and_write_slc_tlc_partition(self)->None:

        self.config_lun()

        api.sequential_write(lun=0, start_lba=0, total_size=self.tlc_vb_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        self.tlc_pca = api.lba_to_pba(lun=0, lba=0)

        api.sequential_write(lun=1, start_lba=0, total_size=self.slc_vb_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        self.slc_pca = api.lba_to_pba(lun=1, lba=0)

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