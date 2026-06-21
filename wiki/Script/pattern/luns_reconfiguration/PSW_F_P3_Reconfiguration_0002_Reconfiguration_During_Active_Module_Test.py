from enum import IntEnum
import random
import time
from typing import List, cast
import package_root
from Script import api
from Script.api.cmd_seq.response import QueryResponse
from Script.api.exception import PATTERN_ASSERT_STUCK_WHILE_TIMEOUT, SIGHTING_FAIL_DATA_COMPARE_FAIL, SIGHTING_RESPONSE_UNEXPECTED, SPEC_ASSERT_RPMB_KEY_NOT_CLEARED, SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET, SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
from Script.api.ufs_api.defines.bit_define import BIT, CHK_BIT
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.defines.enum_define import DescriptorIDN, RPMBMsgType, RPMBRegion
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api.descriptors.device_health_desc.functions import DeviceHealthDescriptorUnion
from Script.api.ufs_api.descriptors.device_health_desc.structs import DeviceHealthDescriptor310
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.rpmb.structs import RPMBMsgDataFrame
from Script.api.ufs_api.vendor_cmd.functions import access_vendor_mode, vuc_clear_rpmb_key
from Script.api.ufs_api.vendor_cmd.structs import FlashSetting
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.project_api.custom_vu.erase_read_count_etc_tables_cis_tables_vu.functions import set_all_VB_erase_count
from Script.project_api.custom_vu.unlock_LU_attribute_configuration.functions import issue_D085_unlock_LU_attribute_configuration
from Script.project_api.luns_reconfiguration.structs import CONFIG_DESCRIPTOR_LOCK

_sdk = api.shared.sdk

class HID_DEFRAG_OPERATION(IntEnum):
    Disable                 = 0
    Analysis                = 1
    Analysis_And_Defrag     = 2

class HID_STATE(IntEnum):
    Idle                    = 0
    Analysis_In_Progress    = 1
    Required                = 2
    Defrag_In_Progress      = 3
    Completed               = 4
    Not_Required            = 5

class REFRESH_STATUS(IntEnum):
    Idle                        =0
    In_Progress                 =1
    Stop_By_Host                =2
    Complete_Success            =3
    Fail_Lun_Queue_Not_Empty    =4
    General_Fail                =5

class WRITE_BOOSTER_FLUSH_STATUS(IntEnum):
    Idle                        =0
    In_Progress                 =1
    Stopped                     =2
    Completed                   =3
    General_Fail                =4


class RECONFIGURATION_STATUS(IntEnum):
    SUCCESS     = 0
    FAIL        = 1

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

        logger.flow(8, f'Verify any in-progress module is cleared when PSA state is OFF')
        self.verify_active_module_is_cleared()

        #===================== bPSAState = 1 (PRE_SOLDERING) ==========================================
        logger.flow(9, f'Set bPSAState as pre_soldering')
        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.send()

        logger.flow(10, f'Check PSA state, expect PSA state is PRE_SOLDERING')
        self.check_psa_state(api.PSAState.PRE_SOLDERING)
        
        #===================== bPSAState = 2 (LOADING_COMPLETE) ==========================================
        logger.flow(11, f'Set bPSAState as LOADING_COMPLETE')
        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).set_option(timeout=self.psa_timeout).enqueue()
        ExecuteCMD.send()

        logger.flow(12, f'Check PSA state, expect PSA state is LOADING_COMPLETE')
        self.check_psa_state(api.PSAState.LOADING_COMPLETE)
        
        #===================== bPSAState = 3 (SOLDERED)  ==========================================
        logger.flow(13, f'Issue power cycle')
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=True)

        logger.flow(14, f'Write data for LUN{self.TestPSALun} with length = {BLOCK4K_SIZE_16M_BYTE}')
        write_cmd = ExecuteCMD.Write10().assign(lun = self.TestPSALun, lba=0, length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        ExecuteCMD.send()

        logger.flow(15, f'Check PSA state, expect PSA state is SOLDERED')
        self.check_psa_state(api.PSAState.SOLDERED)
        
        logger.flow(16, f'Verify any in-progress module is cleared when PSA state is SOLDERED')
        self.verify_active_module_is_cleared()

        pass
    
    def post_process(self) -> None:
        set_all_VB_erase_count(data_payload=self.erase_cnt_buffer_backup, set_in_ram=False)
        self.VU_clear_PSA_state()
        self.config_backup()
        pass

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

    def rpmb_key_programming(self) -> None:
        access_vendor_mode()
        vuc_clear_rpmb_key(RPMBRegion.REGION_0)
        try:
            write_counter = self.rpmb.rpmb_read_counter()
        except SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
            self.rpmb.rpmb_key_programming()
            write_counter = self.rpmb.rpmb_read_counter()
        pass

    def check_timeout(self, start_time: float, timeout_min: int) -> bool:
        current_time = time.time()
        if (current_time - start_time) >= timeout_min * 60:
            return True
        else:
            return False
    
    def verify_active_module_is_cleared(self)-> None:
        logger.info(f'Verify the RPMB data is kept also after LUN reconfiguration')
        self.test_RPMB()
        if self.support_HID:
            logger.info(f'Verify the HID variables are cleared after LUN reconfiguration')
            self.test_HID_flow()
        if self.support_write_booster:
            logger.info(f'Verify the WB variables are cleared after LUN reconfiguration')
            self.test_write_booster_flow()
        if self.support_refresh:
            logger.info(f'Verify the HIR variables are cleared after LUN reconfiguration')
            self.test_HIR_flow()
        pass

    def test_RPMB(self)->None:
        logger.info(f'Write RPMB Data')
        rpmb_write_buffer = self.write_rpmb(0, 4)
        rpmb_write_data:List[bytes] = []
        for lba in range(4):
            rpmb_write_data.append(bytes(rpmb_write_buffer[lba*512+228:lba*512+484]))

        normal_ratio = random.randint(30, 70)
        em1_ratio = 100 - normal_ratio
        logger.info(f'Re-config LUN as {normal_ratio}% normal and {em1_ratio}% EM1')
        self.re_config_lun(normal_ratio, em1_ratio, RECONFIGURATION_STATUS.SUCCESS.value)

        logger.info(f'Compare RMPB data')
        self.compare_rmpb_data(0, 4, rpmb_write_data)

    def test_write_booster_flow(self)->None:
        logger.info(f'Set flag idn = {api.FlagIDN.WRITEBOOSTER_EN} to enable writebooster')
        api.set_flag(idn = api.FlagIDN.WRITEBOOSTER_EN)

        logger.info(f'Erase all card')
        self.erase_all_card()

        logger.info(f'Read attribute idn= {api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS} to check flush status should not be idle')
        flush_status = api.read_attribute(api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS)
        if flush_status != WRITE_BOOSTER_FLUSH_STATUS.Idle.value:
            raise SIGHTING_RESPONSE_UNEXPECTED
        
        loop_cnt = 0
        lun  = self.TestPSALun
        while True:
            lba = random.randint(0, self.param.gUnit[lun].q11_logical_block_count - BLOCK4K_SIZE_1G_BYTE-1)

            logger.info(f'Sequence write 1G bytes from lba = {lba} on lun{lun}')
            api.sequential_write(lun=lun, start_lba=lba, total_size=BLOCK4K_SIZE_1G_BYTE, chunk_size=api.BLOCK4K_SIZE_512K_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            
            logger.info(f'Check if event status bit 5 is set to 1 by reading attribute idn = {api.AttributeIDN.EXC_EVENT_STATUS}')
            event_status = api.read_attribute(idn = api.AttributeIDN.EXC_EVENT_STATUS)
            if event_status & BIT(5) > 0:
                break

            loop_cnt +=1
            if loop_cnt >= 1000:
                logger.error_lb('Sequential write 1G until Write booster needed flush')
                logger.error_fp(f'Sequential Write over {loop_cnt} times Write booster never need flush')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            
        logger.info(f'Set flag idn = {api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN} to enable write booster buffer flush')
        api.set_flag(idn = api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)

        logger.info(f'Check if flush status is {WRITE_BOOSTER_FLUSH_STATUS.In_Progress.value} by reading attribute idn = {api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS}')
        flush_status = api.read_attribute(api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS)
        if flush_status == WRITE_BOOSTER_FLUSH_STATUS.In_Progress.value:
            normal_ratio = random.randint(30, 70)
            em1_ratio = 100 - normal_ratio
            logger.info(f'Re-config LUN as {normal_ratio}% normal and {em1_ratio}% EM1')
            self.re_config_lun(normal_ratio, em1_ratio, RECONFIGURATION_STATUS.SUCCESS.value)
        else:
            logger.error_lb('Set flag bWriteBoosterFlushEn(0Fh) as 01h and check bWriteBoosterBufferFlushStatus value')
            logger.error_fp(f'Expect that bWriteBoosterBufferFlushStatus changed into {WRITE_BOOSTER_FLUSH_STATUS.In_Progress.value}(in-progress), but current value is 0x{flush_status:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        
        logger.info(f'Check if flush status is {WRITE_BOOSTER_FLUSH_STATUS.Idle.value} by reading attribute idn = {api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS}')
        flush_status = api.read_attribute(api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS)
        if flush_status != WRITE_BOOSTER_FLUSH_STATUS.Idle.value:
                logger.error_lb('Set attribute bDefragOperation(35h) as 02h and bHIDState is 03h (defrag in progress), then re-config lun')
                logger.error_fp(f'"Expect that bHIDState changed into 00h (idle), but current value is 0x{flush_status:02X}')
                raise SIGHTING_RESPONSE_UNEXPECTED


        api.clear_flag(idn = api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)
        api.clear_flag(idn = api.FlagIDN.WRITEBOOSTER_EN)
        pass

    def test_HID_flow(self) -> None:
        for lun in [self.TestPSALun, self.TestEM1Lun] :
            chunk_size = BLOCK4K_SIZE_256M_BYTE - BLOCK4K_SIZE_1M_BYTE
            length = BLOCK4K_SIZE_1G_BYTE + BLOCK4K_SIZE_4G_BYTE
            start_time = time.time()
            timeout_min = 10
            start_lba = 0
            logger.info(f'Write data {length} bytes from {start_lba} on lun{lun}')
            self.write_data(lun, start_lba, chunk_size, length)
            while True:
                cmd_count = random.randint(10, 32)
                min_lun = lun
                max_lun = lun
                min_lba = 0
                max_lba = self.param.gLUCapacity[lun] - BLOCK4K_SIZE_32M_BYTE
                min_size = BLOCK4K_SIZE_32M_BYTE
                max_size = BLOCK4K_SIZE_32M_BYTE

                logger.info(f'Random write data on lun{lun}')
                api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

                logger.info(f'Write attribute idn = {api.AttributeIDN.DEFRAG_OPERATION} and value = {HID_DEFRAG_OPERATION.Analysis.value}')
                api.write_attribute(idn=api.AttributeIDN.DEFRAG_OPERATION, val=HID_DEFRAG_OPERATION.Analysis.value)
                
                read_attr_value = api.read_attribute(idn=api.AttributeIDN.HID_STATE)
                logger.info(f'Read bHIDState is 0x{read_attr_value:02X}')
                if read_attr_value == HID_STATE.Required.value:
                    api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                    break

                if self.check_timeout(start_time, timeout_min):
                    logger.error_lb('Set attribute bDefragOperation(35h) as 01h: HID analysis is enabled and read bHIDState after each random write flow')
                    logger.error_fp(f'"Expect that bHIDState changed into 02h: Defrag Required within 10 mins, but current value is 0x{read_attr_value:02X}')
                    raise SIGHTING_RESPONSE_UNEXPECTED

            logger.info(f'Write attribute idn = {api.AttributeIDN.DEFRAG_OPERATION} and value = {HID_DEFRAG_OPERATION.Analysis_And_Defrag.value}')    
            api.write_attribute(idn=api.AttributeIDN.DEFRAG_OPERATION, val=HID_DEFRAG_OPERATION.Analysis_And_Defrag.value)

            read_attr_value = api.read_attribute(idn=api.AttributeIDN.HID_STATE)
            logger.info(f'Read bHIDState is 0x{read_attr_value:02X}')
            
            if read_attr_value == HID_STATE.Defrag_In_Progress.value:
                normal_ratio = random.randint(30, 70)
                em1_ratio = 100 - normal_ratio
                logger.info(f'Re-config LUN as {normal_ratio}% normal and {em1_ratio}% EM1')
                self.re_config_lun(normal_ratio, em1_ratio, RECONFIGURATION_STATUS.SUCCESS.value)
        
                read_attr_value = api.read_attribute(idn=api.AttributeIDN.HID_STATE)
                hid_progress = api.read_attribute(idn=api.AttributeIDN.HID_PROGRESS_RATIO)
                logger.info(f'Read bHIDState is 0x{read_attr_value:02X}')
                if read_attr_value != HID_STATE.Idle.value or hid_progress != 0:  
                    logger.error_lb('Set attribute bDefragOperation(35h) as 02h and bHIDState is 03h (defrag in progress), then re-config lun')
                    logger.error_fp(f'Expect that bHIDState and bHIDProgressRatio are changed into 00h , but the current bHIDState is 0x{read_attr_value:02X} and bHIDProgressRatio is {hid_progress}')
                    raise SIGHTING_RESPONSE_UNEXPECTED
            else:
                logger.error_lb('Set attribute bDefragOperation(35h) as 02h and check bHIDState value')
                logger.error_fp(f'Expect that bHIDState changed into {HID_STATE.Defrag_In_Progress.value}(in-progress), but current value is 0x{read_attr_value:02X}')
                raise SIGHTING_RESPONSE_UNEXPECTED
        
        logger.info(f'Write attribute idn = {api.AttributeIDN.DEFRAG_OPERATION} and value = {HID_DEFRAG_OPERATION.Disable.value}')        
        api.write_attribute(idn=api.AttributeIDN.DEFRAG_OPERATION, val=HID_DEFRAG_OPERATION.Disable.value)
        pass
        
    def test_HIR_flow(self)-> None:
        refreshunit = 1; #REFRESH_WHOLE_DEVICE
        logger.info(f'Set attribute idn = {api.AttributeIDN.REFRESH_UNIT} to be {refreshunit}')
        api.write_attribute(idn = api.AttributeIDN.REFRESH_UNIT, val=refreshunit)
        refreshmethod = 1 #REFRESH_MANUAL_FORCE
        logger.info(f'Set attribute idn = {api.AttributeIDN.REFRESH_METHOD} to be {refreshmethod}')
        api.write_attribute(idn = api.AttributeIDN.REFRESH_METHOD, val=refreshmethod)

        logger.info(f'Write all enable LUN')
        api.sequential_write(lun=self.TestPSALun, start_lba=0, total_size=BLOCK4K_SIZE_4G_BYTE, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=BLOCK4K_SIZE_4G_BYTE, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        cmd_count = random.randint(10, 32)
        min_lun = self.TestPSALun
        max_lun = self.TestEM1Lun
        min_lba = 0
        max_lba = BLOCK4K_SIZE_4G_BYTE - BLOCK4K_SIZE_4M_BYTE
        min_size = BLOCK4K_SIZE_4M_BYTE
        max_size = BLOCK4K_SIZE_4M_BYTE
        logger.info(f'Random write all enable LUN')
        api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        logger.info(f'Random erase all enable LUN')
        api.random_erase(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                    write_record=self.write_record)
     
        logger.info(f'Set flag idn = {api.FlagIDN.REFRESH_EN} to enable refresh')
        api.set_flag(idn=api.FlagIDN.REFRESH_EN)

        refresh_progress_1st = self.pattern_get_health_descriptor().l41_refresh_progress
        logger.info(f'Read 1st refresh progress is 0x{refresh_progress_1st:02X}')
        start_time = time.time()
        timeout_min = 20
        while True:
            refresh_progress_2nd = self.pattern_get_health_descriptor().l41_refresh_progress
            logger.info(f'Read 2nd refresh progress is 0x{refresh_progress_2nd:02X}')
            if refresh_progress_1st > 0 and  refresh_progress_2nd == 0:
                normal_ratio = random.randint(30, 70)
                em1_ratio = 100 - normal_ratio
                logger.info(f'Re-config LUN as {normal_ratio}% normal and {em1_ratio}% EM1')
                self.re_config_lun(normal_ratio, em1_ratio, RECONFIGURATION_STATUS.SUCCESS.value)

                refresh_status = api.read_attribute(idn=api.AttributeIDN.REFRESH_STATUS)
                refresh_progress = self.pattern_get_health_descriptor().l41_refresh_progress
                logger.info(f'Read refresh status is 0x{refresh_status:02X} and progress is {refresh_progress}')

                if refresh_status != REFRESH_STATUS.Idle.value or refresh_progress != 0:
                    logger.error_lb('Set Flag REFRESH_EN(07h) as 01h and refresh progress is bigger than zero (in progress), then re-config lun')
                    logger.error_fp(f'Expect that refresh status changed into 00h (idle) and progress is 00h, but current status is 0x{refresh_status:02X} and progress is {refresh_progress}')
                    raise SIGHTING_RESPONSE_UNEXPECTED
                
                break
            if self.check_timeout(start_time, timeout_min):
                logger.error_lb('Set Flag REFRESH_EN(07h) as 01h and polling refresh progress')
                logger.error_fp(f'Expect that refresh progress changed into 00h within 10 mins, but current value is {refresh_progress_2nd}')
                raise SIGHTING_RESPONSE_UNEXPECTED
            
            refresh_progress_1st = refresh_progress_2nd

        api.clear_flag(idn=api.FlagIDN.REFRESH_EN)
        pass

    def write_rpmb(self, start_lba:int, data_len:int)-> bytearray:       
        key_is_cleared = False
        try:
            write_counter = self.rpmb.rpmb_read_counter()
        except SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
            key_is_cleared = True
            logger.info("Flow = RPMB key is cleared")
            self.rpmb.rpmb_key_programming()
            
        self.rpmb.rpmb_write_data(start_lba, data_len)
        rpmb_data = self.get_rpmb_write_data(start_lba, data_len)

        if key_is_cleared:
            logger.error("RPMB key is cleared")
            raise SPEC_ASSERT_RPMB_KEY_NOT_CLEARED
        
        return  rpmb_data   

    def compare_rmpb_data(self, start_lba:int, data_len:int, write_data:List[bytes])-> None:
        resp = self.rpmb.rpmb_read_data(start_lba, data_len)
        for lba in range(data_len):
            read_data = bytes(resp.data[lba*512+228:lba*512+484])
            if read_data != write_data[lba]:
                logger.error_lb(f'Write and compare RPMB data')
                logger.error_fp(f'Comparison expected to pass, but verification failed')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def write_data(self, lun:int, lba:int, chunk_size: int, length:int) -> None:
        logger.flow(4, 'Write PSA sensitive LUNs with data size = dPSADataSize / 2')
        total_len = length
        start = lba
        while total_len > 0:
            chunk_size = int(min(chunk_size, total_len))
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=lun, lba=start, length=chunk_size, fua=0)
            write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
            total_len -= chunk_size
            start += chunk_size
            ExecuteCMD.enqueue(write10)

        ExecuteCMD.send(clear_on_success=False)
        for cmd in ExecuteCMD._cmd_list:
            api.save_write_info_by_cmd(cmd=cmd, write_record=self.write_record)

        ExecuteCMD.clear()

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

    def re_config_lun(self, normal_ratio:int, em1_ratio:int, result: int) ->None:
        normal_au_size = (self.total_au_size * normal_ratio) // 100
        em1_au_size = self.total_au_size - normal_au_size
        em1_au_size = em1_au_size if em1_au_size < self.geometry_desc.l44_enhanced1_max_n_alloc_u else self.geometry_desc.l44_enhanced1_max_n_alloc_u

        config_desc = api.get_config_descriptors()
        for unit in range(8):
            if unit == self.TestPSALun :
                config_desc[0].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                config_desc[0].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                config_desc[0].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                config_desc[0].units[unit].b3_memory_type = api.MemoryType.NORMAL
                config_desc[0].units[unit].l4_num_alloc_units = normal_au_size
                config_desc[0].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                config_desc[0].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                config_desc[0].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE 
            elif unit == self.TestEM1Lun:
                config_desc[0].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                config_desc[0].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                config_desc[0].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                config_desc[0].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                config_desc[0].units[unit].l4_num_alloc_units = em1_au_size
                config_desc[0].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                config_desc[0].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                config_desc[0].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE 
            else:
                config_desc[0].units[unit].b0_lu_enable = 0
                config_desc[0].units[unit].l4_num_alloc_units = 0
        
        config_desc[0].header.b2_conf_desc_continue = 0
        push_write_config(config_desc[0], index=0)


        if result == RECONFIGURATION_STATUS.FAIL.value:
            try:
                ExecuteCMD.send(clear_on_success=False, skip_response_check= True)
            except:
                response = cast(api.QueryResponse, ExecuteCMD.read_response(0))
                logger.info(f'response = {response.upiu.b6_query_response}')
            ExecuteCMD.clear()
            if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE and response.upiu.b6_query_response != api.QueryResponseCode.PARAM_ALREADY_WRITTEN:
                logger.error_lb('Write LUN configuration')
                logger.error_fp(f'Expect the write LUN configuration response to be {api.QueryResponseCode.GENERAL_FAILURE} or {api.QueryResponseCode.PARAM_ALREADY_WRITTEN}, but received {response.upiu.b6_query_response}')
                raise SIGHTING_RESPONSE_UNEXPECTED
        else:
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

    def config_backup(self) -> None:
        for i in range(4):
            if i == 3:
                self.backup_setting[i].header.b2_conf_desc_continue = 0
            else:
                self.backup_setting[i].header.b2_conf_desc_continue = 1
            push_write_config(self.backup_setting[i], index=i) 
        ExecuteCMD.send()
        pass
    
    def erase_all_card(self)->None:
        for lun in [self.TestPSALun, self.TestEM1Lun]:
            start_lba = 0
            data_len = 65535
            continue_push_unmap = True
            while continue_push_unmap:
                start_lba = min(start_lba, self.param.gLUCapacity[lun])
                if (start_lba + data_len) > self.param.gLUCapacity[lun]:
                    data_len = self.param.gLUCapacity[lun] - start_lba
                    continue_push_unmap = False
                logger.info(f'unmap, start_lba = {start_lba}, data_len = {data_len}')
                unmap = ExecuteCMD.Unmap()
                unmap.assign(lun=lun, lba=start_lba, length=data_len)
                ExecuteCMD.enqueue(unmap)      
                start_lba += data_len
            ExecuteCMD.send()
        idn = api.FlagIDN.PURGE_EN
        set_flag = ExecuteCMD.SetFlag().assign(idn).enqueue()
        ExecuteCMD.send(clear_on_success=True)
        timeout_min = 30
        start_time = time.time()
        polling_cnt = 0
        while True:
            if self.check_timeout(start_time, timeout_min):
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            purge_status = api.read_attribute(idn=api.AttributeIDN.PURGE_STATUS)
            polling_cnt += 1
            logger.info(f'purge status = {purge_status}, polling count = {polling_cnt}')
            if purge_status == 0x03:
                logger.info(f'purge status = {purge_status}, complete')
                break
        pass      

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

    def check_psa_state(self, state:int) -> None:
        psa_state = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{psa_state:02X}')
        if psa_state != state:
            logger.error_lb('Check bPSAState after power cycle in OFF state')
            logger.error_fp(f'bPSAState should be 0x{state:02X} but current value is 0x{psa_state:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        pass

    def get_rpmb_write_data(self, start_lba:int, data_len:int) -> bytearray:
        rpmb_data_frame = RPMBMsgDataFrame()

        rpmb_data_frame.key_mac = self.rpmb.key

        logger.info("Flow-a = Write data Request (Security Protocol Out) ")

        rpmb_data_frame.write_counter = self.rpmb.write_counter
        rpmb_data_frame.address = start_lba
        rpmb_data_frame.block_count = data_len
        rpmb_data_frame.req_rsp_type = RPMBMsgType.DATA_WRITE_REQ
        
        rpmb_data_buffer = bytearray(rpmb_data_frame.block_count * 512)   # 用來放 rpmb data
        rpmb_data_buffer = self.rpmb.gen_mac_for_write_rpmb_data(rpmb_data_frame)

        return rpmb_data_buffer

    def pattern_get_health_descriptor(self) -> DeviceHealthDescriptorUnion:
        idn = DescriptorIDN.DEVICE_HEALTH
        index = 0x00
        selector = 0x00
        cmd = ExecuteCMD.ReadDescriptor()
        cmd.assign(idn, index, selector)
        cmd_index = ExecuteCMD.enqueue(cmd)

        ExecuteCMD.send(clear_on_success=False)
        resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
        ExecuteCMD.clear()

        desc = DeviceHealthDescriptor310()
        desc.from_bytes(resp.data)
        return desc

run = Pattern().run
if __name__ == "__main__":
    run()