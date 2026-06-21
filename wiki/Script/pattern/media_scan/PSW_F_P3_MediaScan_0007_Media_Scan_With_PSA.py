import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.ufs_api.defines.bit_define import CHK_BIT
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api.exception import *
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.project_api.custom_vu.erase_read_count_etc_tables_cis_tables_vu.functions import set_all_VB_erase_count
from Script.project_api.custom_vu.media_scan_vu.structs import *
from Script.pattern.apl_system_rebuild.mutual_fun import *
from Script.project_api.custom_vu.unlock_LU_attribute_configuration.functions import issue_D085_unlock_LU_attribute_configuration
from Script.project_api.luns_reconfiguration.structs import CONFIG_DESCRIPTOR_LOCK

class Pattern(UFSTC):

    def pre_process(self) -> None:
        self.param = api.shared.param
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        self.flash_setting = FlashSetting()
        self.flash_setting.from_bytes(self.flash_setting_buffer)
        _, self.debug_info = api.get_debug_info()
        self.au_size = self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size * 512
        self.total_au_size = int(self.geometry_desc.q4_total_raw_device_capacity / self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size)
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.psa_timeout = pow(2, self.param.gDevice.b41_psa_state_timeout) * 100
        self.TestPSALun = 0
        self.TestEM1Lun = 1
        self.backup_setting = api.get_config_descriptors(print=False)
        self.write_record = api.get_empty_write_record()
        self.support_refresh = bool(CHK_BIT(self.param.gDevice.l79_extended_ufs_features_support, 3))
        self.support_write_booster = bool(CHK_BIT(self.param.gDevice.l79_extended_ufs_features_support, 8))
        self.support_HID = bool(CHK_BIT(self.param.gDevice.l79_extended_ufs_features_support, 13))
        self.rpmb = RPMB(RPMBRegion.REGION_0)
        pass

    def step1(self) -> None:
        
        _, self.erase_cnt_buffer_backup = api.read_Xmemory(sram_address=self.debug_info.VB_list_cycle_address.value)

        logger.flow(1, f'Config LUN{self.TestPSALun} as normal LU and LUN{self.TestEM1Lun} as EM1 LU')
        self.config_lun()

        logger.flow(2, f'Program RPMB Key')
        self.rpmb_key_programming()

        logger.flow(3, f'Send VUC D085 to reset config descriptor lock to be {CONFIG_DESCRIPTOR_LOCK.UNLOCK.value}')
        self.set_config_descriptor_lock(CONFIG_DESCRIPTOR_LOCK.UNLOCK.value)

        logger.flow(4, f'Send VUC C083 to set EC count to be 1')
        self.set_EC_count(1)

        #===================== bPSAState = 0 (PSA off) ==========================================
        max_psa_size = self.param.gDevice.l37_psa_max_data_size
        logger.flow(5, f'Set dPSADataSize as dPSAMaxDataSize value {max_psa_size}')
        api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=max_psa_size)

        logger.flow(6, f'Issue Unmap command for PSA LUN')
        unmap = ExecuteCMD.Unmap()
        unmap.assign(lun=self.TestPSALun, lba=0, length=self.param.gUnit[self.TestPSALun].q11_logical_block_count)
        ExecuteCMD.enqueue(unmap)
        ExecuteCMD.send()

        logger.flow(7, f'Check PSA state, expect PSA state is idle')
        self.check_psa_state(api.PSAState.OFF)
   
        logger.flow(8, 'vu40CF get current scan info')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value

        logger.flow(9, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(10, 'trigger media scan')
        spend_time_set = 0x1000000
        new_scan_vb, new_scan_page, new_scan_group = self.execute_media_scan_and_get_cur_scan_info(spend_time_set)
        logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')

        logger.flow(11, 'check media scan should triggerd in psa-off state')
        if new_scan_vb == old_scan_vb and new_scan_page == old_scan_page and new_scan_group == old_scan_group:
            logger.error('media scan should triggered')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        old_scan_vb = new_scan_vb
        old_scan_page = new_scan_page
        old_scan_group = new_scan_group
        #===================== bPSAState = 1 (PRE_SOLDERING) ==========================================
        logger.flow(12, f'Set bPSAState as pre_soldering')
        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.send()

        logger.flow(13, f'Check PSA state, expect PSA state is PRE_SOLDERING')
        self.check_psa_state(api.PSAState.PRE_SOLDERING)

        logger.flow(14, 'trigger media scan')
        spend_time_set+=0x100
        new_scan_vb, new_scan_page, new_scan_group = self.execute_media_scan_and_get_cur_scan_info(spend_time_set)
        logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')

        logger.flow(15, 'check media scan should not triggerd in psa-presoldering state')
        if new_scan_vb != old_scan_vb or new_scan_page != old_scan_page or new_scan_group != old_scan_group:
            logger.error('media scan should not triggered')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        old_scan_vb = new_scan_vb
        old_scan_page = new_scan_page
        old_scan_group = new_scan_group
        #===================== bPSAState = 1 (PRE_SOLDERING) interrupt psa case ==========================================

        logger.flow(16, 'Set bPSAState as Off to interrupt PSA flow')
        api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.OFF)
        
        logger.flow(17, f'Check PSA state, expect PSA state is off')
        self.check_psa_state(api.PSAState.OFF)

        logger.flow(18, 'trigger media scan')
        spend_time_set+=0x100
        new_scan_vb, new_scan_page, new_scan_group = self.execute_media_scan_and_get_cur_scan_info(spend_time_set)
        logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')

        logger.flow(19, 'check media scan should not triggerd in psa-presoldering state interrupt')
        if new_scan_vb != old_scan_vb or new_scan_page != old_scan_page or new_scan_group != old_scan_group:
            logger.error('media scan should not triggered')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL       
        
        old_scan_vb = new_scan_vb
        old_scan_page = new_scan_page
        old_scan_group = new_scan_group
        #===================== bPSAState = 2 (LOADING_COMPLETE) ==========================================
        logger.flow(20, f'Set bPSAState as pre_soldering')
        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.send()

        logger.flow(21, f'Check PSA state, expect PSA state is PRE_SOLDERING')
        self.check_psa_state(api.PSAState.PRE_SOLDERING)

        logger.flow(22, f'Create PSA block')
        write_cmd = ExecuteCMD.Write10().assign(lun = self.TestPSALun, lba=0, length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        ExecuteCMD.send()
        pca=get_PCA_and_print(lun=self.TestPSALun, lba=0)
        psa_vb = pca.b11_block_h<<8 | pca.b10_block_l
        logger.info('psa vb=%d', psa_vb)
   
        logger.flow(23, f'Set bPSAState as LOADING_COMPLETE')
        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).set_option(timeout=self.psa_timeout).enqueue()
        ExecuteCMD.send()

        logger.flow(24, f'Check PSA state, expect PSA state is LOADING_COMPLETE')
        self.check_psa_state(api.PSAState.LOADING_COMPLETE)

        logger.flow(25, 'trigger media scan')
        new_scan_vb, new_scan_page, new_scan_group = self.execute_media_scan_and_get_cur_scan_info(spend_time_set)
        logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')

        logger.flow(26, 'check media scan should not triggerd in loading complete state')
        logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')        
        if new_scan_vb != old_scan_vb or new_scan_page != old_scan_page or new_scan_group != old_scan_group:
            logger.error('media scan should not triggered')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        #===================== bPSAState = 3 (SOLDERED)  ==========================================
        logger.flow(27, f'Issue power cycle')
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=True)

        logger.flow(28, f'1st write')
        write_cmd = ExecuteCMD.Write10().assign(lun = self.TestPSALun, lba=0, length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        ExecuteCMD.send()

        logger.flow(29, f'Check PSA state, expect PSA state is SOLDERED')
        self.check_psa_state(api.PSAState.SOLDERED)

        logger.flow(30, 'vu40CF get current scan info')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value

        logger.flow(31, 'trigger media scan')
        new_scan_vb, new_scan_page, new_scan_group = self.execute_media_scan_and_get_cur_scan_info(spend_time_set)
        logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')

        logger.flow(32, 'check media scan should triggerd in soldered state')
        if new_scan_vb == old_scan_vb and new_scan_page == old_scan_page and new_scan_group == old_scan_group:
            logger.error('media scan should triggered')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(33, 'check psa vb not scanned by media scan')
        for vb in payload.scanned_blocks:
            logger.info('scanned blocks=%d', vb)
            if vb == psa_vb:
                logger.error('psa vb should not scanned by media scan')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        pass
    
    def post_process(self) -> None:
        self.VU_clear_PSA_state()
        self.config_backup()
        pass

    def execute_media_scan_and_get_cur_scan_info(self, spend_time_set:int) -> tuple[int, int, int]:
        
        param = micron_vu_C085_param_with_data()
        param.last_scan_spend_time = spend_time_set
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)
        
        time.sleep(5)

        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        scan_vb = payload.cur_scan_vb.value
        scan_page = payload.cur_scan_page.value
        scan_group = payload.scan_group.value

        return scan_vb, scan_page, scan_group

    def set_payload_with_value(self, value:int) -> bytearray:
        field_offset = 4
        payload = bytearray(DATA_SIZE_4K_BYTE)
        bytes_val = value.to_bytes(field_offset, 'little')
        for i in range(self.fw_geometry.l52_total_vb_count):
            payload[i * field_offset : (i+1)*field_offset] = bytes_val
        return payload
        
    def set_EC_count(self, value:int)-> None:
        payload = self.set_payload_with_value(value)
        set_all_VB_erase_count(data_payload=payload, set_in_ram=True)

    def get_target_vb_list(self, group:int)-> List[int]:
        retval = 0
        vb_list = []
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'access_mode': {'pos': 6, 'len': 2, 'mask': 0x3}, 
            'dirty': {'pos': 8, 'len': 1, 'mask': 0x1}, 
        }
        response, rep_data = get_vb_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data)):
            if self.fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break

            ftl_vb_list_data.update({vb : {k: (((rep_data[vb*4]|rep_data[vb*4+1]<<8) >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        used_mlc_cout = 0
        map_vb_cnt = {} # type: ignore
        logger.info(f'[show all vb info at begin]')
        for vb, vb_info in ftl_vb_list_data.items():
            last_type = vb_info['group']
            dirtybit = vb_info['dirty']
            if last_type in map_vb_cnt:
                map_vb_cnt[last_type] += 1
            else:
                map_vb_cnt[last_type] = 1
            logger.info(f'[vb = {vb}, group type = {last_type}, dirtybit = {dirtybit}]')
            if last_type == group:
                vb_list.append(vb)
        for k,v in map_vb_cnt.items():
            logger.info(f'group type = {k}, cnt = {v}]')
        logger.info(f'get target vb list of vb {group} cnt = {len(vb_list)}')
        return vb_list
    
    def set_config_descriptor_lock(self, isLock:int)-> None:
        logger.info('Issue VU 0xD085 to Unlock LU Attribute Configuration-Description')
        issue_D085_unlock_LU_attribute_configuration()
        logger.info(f'Write attribute idn = {api.AttributeIDN.CONFIG_DESCR_LOCK} and value = {isLock}')
        api.write_attribute(idn = api.AttributeIDN.CONFIG_DESCR_LOCK, val = isLock)

        bConfigDescrLock = api.read_attribute(idn=api.AttributeIDN.CONFIG_DESCR_LOCK)
        logger.info(f'attribute 0Bh(bConfigDescrLock) value = {bConfigDescrLock}')
        if bConfigDescrLock != isLock:
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def rpmb_key_programming(self) -> None:
        access_vendor_mode()
        vuc_clear_rpmb_key(RPMBRegion.REGION_0)
        try:
            write_counter = self.rpmb.rpmb_read_counter()
        except SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
            self.rpmb.rpmb_key_programming()
            write_counter = self.rpmb.rpmb_read_counter()
        pass

    def update_unit_desc(self) -> None:
        unit_desc_idxes:List[int] = []
        for lun in range(self.param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()
        pass

    def update_device_desc(self) -> None:
        device_descriptor = ExecuteCMD.ReadDescriptor()
        device_descriptor.assign(idn=api.DescriptorIDN.DEVICE)
        index = ExecuteCMD.enqueue(device_descriptor)
        ExecuteCMD.send(clear_on_success=False)
        api.update_descriptor(idn=api.DescriptorIDN.DEVICE, index=0, response=cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()
        pass

    def config_lun(self) -> None:
        normal_au_size = self.total_au_size//2
        em1_au_size = self.total_au_size//2
        em1_au_size = em1_au_size if em1_au_size < self.geometry_desc.l44_enhanced1_max_n_alloc_u else self.geometry_desc.l44_enhanced1_max_n_alloc_u

        config_desc = api.get_config_descriptors(print=True)
        config_desc[0].header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE
        config_desc[0].header.b17_write_booster_buffer_type = 1
        config_desc[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
        config_desc[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x400 #4G
        for i in range(4): 
            for unit in range(8):
                LU_number = i * 8 + unit
                if LU_number == self.TestPSALun:
                    config_desc[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[i].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[i].units[unit].l4_num_alloc_units = normal_au_size
                    config_desc[i].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[i].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE 
                elif LU_number == self.TestEM1Lun:
                    config_desc[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[i].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[i].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_desc[i].units[unit].l4_num_alloc_units = em1_au_size
                    config_desc[i].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[i].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                else:
                    config_desc[i].units[unit].b0_lu_enable = 0
                    config_desc[i].units[unit].l4_num_alloc_units = 0

            config_desc[i].header.b2_conf_desc_continue = 0 if i==3 else 1
            push_write_config(config_desc[i], index=i)


        ExecuteCMD.send()

        self.update_unit_desc()
        self.update_device_desc()

        test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
        for lun in range(self.param.gMaxNumberLU):
            if self.param.gUnit[lun].b3_lu_enable != api.LUNEnable.DISABLE:
                test_unit_ready.set_option(lun=lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send()

        pass
    
    def check_psa_state(self, state:int) -> None:
        psa_state = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{psa_state:02X}')
        if psa_state != state:
            logger.error_lb('Check bPSAState after power cycle in OFF state')
            logger.error_fp(f'bPSAState should be 0x{state:02X} but current value is 0x{psa_state:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        pass

    def VU_clear_PSA_state(self) -> None:
        api.access_vendor_mode()
        vuc = ExecuteCMD.VendorCmdWrite()
        vuc.assign(length=api.DATA_SIZE_4K_BYTE, cmd_index=api.VendorCmd.WRITE_PARAMETER, cmd_set_type=0x0F)
        vuc.upiu.u16_cdb.b2_rsvd = api.VendorCmdRuleCdb2.CMD_IN_DOUT
        data = bytearray(b'\x00' * 0x1000)
        data[0] = 0x04
        data[4] = 0x01
        data[8] = 0x44
        data[12] = 0x41
        data[14] = 0x01
        data[16] = 0x15
        data[21] = 0x02
        data[24] = 0x01
        data[28] = 0x46
        data[32] = 0x53
        vuc.data = data
        vuc.enqueue()
        ExecuteCMD.send()
        pass
    
    def config_backup(self) -> None:
        for i in range(4):
            if i == 3:
                self.backup_setting[i].header.b2_conf_desc_continue = 0
            else:
                self.backup_setting[i].header.b2_conf_desc_continue = 1
            push_write_config(self.backup_setting[i], index=i) 
        ExecuteCMD.send()
        pass    

run = Pattern().run
if __name__ == "__main__":
    run()