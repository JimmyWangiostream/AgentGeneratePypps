from enum import IntEnum
from typing import List, cast

import package_root
from copy import deepcopy
import random
from Script import api
from Script.api.ufs_api.defines.constant_define import BLOCK4K_SIZE_16M_BYTE, DATA_SIZE_4K_BYTE
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.api.ufs_api.vendor_cmd.structs import FlashSetting
from Script.pattern.pattern_logger import logger
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.exception import *
from Script.project_api.custom_vu.erase_read_count_etc_tables_cis_tables_vu.functions import get_all_VB_erase_count, set_all_VB_erase_count
from Script.project_api.custom_vu.unlock_LU_attribute_configuration.functions import issue_D085_unlock_LU_attribute_configuration
from Script.project_api.health_report.functions import issue_40FE_to_read_enhanced_health_report
from Script.project_api.luns_reconfiguration.structs import CONFIG_DESCRIPTOR_LOCK

_sdk = api.shared.sdk

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
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.psa_timeout = pow(2, self.param.gDevice.b41_psa_state_timeout) * 100
        self.TestPSALun = 0
        self.TestEM1Lun = 1
        self.backup_setting = api.get_config_descriptors(print=False)
        self.write_record = api.get_empty_write_record()
        pass


    def step1(self) -> None:
        _, self.erase_cnt_buffer_backup = api.read_Xmemory(sram_address=self.debug_info.VB_list_cycle_address.value)

        logger.flow(1, f'Config LUN{self.TestPSALun} as normal LU and LUN{self.TestEM1Lun} as EM1 LU')
        self.config_lun()

        logger.flow(2, f'Validate all LUN reconfiguration test cases')
        self.lun_reconfiguration_test(api.PSAState.OFF)
        
        for loop in range(3):    
            #===================== bPSAState = 0 (PSA off) ==========================================
            logger.flow(3, f'Set dPSADataSize as dPSAMaxDataSize value {self.param.gDevice.l37_psa_max_data_size}')
            max_psa_size = self.param.gDevice.l37_psa_max_data_size
            api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=max_psa_size)

            logger.flow(4, f'Issue Unmap command for PSA LUN')
            for i in range(8):
                if self.param.gUnit[i].b3_lu_enable == api.LUNEnable.ENABLE and self.param.gUnit[i].b8_memory_type == api.MemoryType.NORMAL:
                    unmap = ExecuteCMD.Unmap()
                    unmap.assign(lun=i, lba=0, length=self.param.gUnit[i].q11_logical_block_count)
                    ExecuteCMD.enqueue(unmap)
            ExecuteCMD.send()

            logger.flow(5, f'Validate all LUN reconfiguration test cases')
            self.lun_reconfiguration_test(api.PSAState.OFF)

            logger.flow(6, f'Check PSA state, expect PSA state is OFF')
            self.check_PSA_state(api.PSAState.OFF)
            #===================== bPSAState = 1 (PRE-SOLDERING) ==========================================
            logger.flow(7, f'Set bPSAState as pre_soldering')
            ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True).enqueue()
            ExecuteCMD.send()

            logger.flow(8, f'Validate all LUN reconfiguration test cases')
            self.lun_reconfiguration_test(api.PSAState.PRE_SOLDERING)

            logger.flow(9, f'Check PSA state, expect PSA state is PRE_SOLDERING')
            self.check_PSA_state(api.PSAState.PRE_SOLDERING)
            
            if loop == 0:
                logger.flow(10, 'Set bPSAState as Off to interrupt PSA flow')
                api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.OFF)
                continue
            #===================== bPSAState = 2 (loading complete) ==========================================
            logger.flow(11, f'Set bPSAState as Loading_Complete')
            ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).set_option(timeout=self.psa_timeout).enqueue()
            ExecuteCMD.send()

            logger.flow(12, f'Validate all LUN reconfiguration test cases')
            self.lun_reconfiguration_test(api.PSAState.LOADING_COMPLETE)

            logger.flow(13, f'Check PSA state, expect PSA state is LOADING_COMPLETE')
            self.check_PSA_state(api.PSAState.LOADING_COMPLETE)
            
            if loop == 1:
                logger.flow(14, 'Set bPSAState as Off to interrupt PSA flow')
                api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.OFF)
                continue

        #===================== bPSAState = 3 (soldered)  ==========================================
        logger.flow(15, f'Issue power cycle')
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=True)

        logger.flow(16, f'Write data for LUN{self.TestPSALun} with length = {BLOCK4K_SIZE_16M_BYTE}')
        write_cmd = ExecuteCMD.Write10().assign(lun = self.TestPSALun, lba=0, length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        ExecuteCMD.send()

        logger.flow(17, f'Validate all LUN reconfiguration test cases')
        self.lun_reconfiguration_test(api.PSAState.SOLDERED)

        logger.flow(18, f'Check PSA state, expect PSA state is SOLDERED')
        self.check_PSA_state(api.PSAState.SOLDERED)
        pass
    
    def post_process(self) -> None:
        set_all_VB_erase_count(data_payload=self.erase_cnt_buffer_backup, set_in_ram=False)
        self.VU_clear_PSA_state()
        self.config_backup()
        pass

    def config_lun(self) -> None:
        normal_au_size = self.total_au_size//2
        em1_au_size = self.total_au_size//2
        em1_au_size = em1_au_size if em1_au_size < self.geometry_desc.l44_enhanced1_max_n_alloc_u else self.geometry_desc.l44_enhanced1_max_n_alloc_u

        config_desc = api.get_config_descriptors(print=True)
        config_desc[0].header.b17_write_booster_buffer_type = 1
        config_desc[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
        config_desc[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x400
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

    def re_config_lun(self, normal_ratio:int, em1_ratio:int, result: int, test_case : int) ->None:
        normal_lun_count = random.randint(1, 7)
        em1_lun_count = 8 - normal_lun_count
        normal_au_size = (self.total_au_size * normal_ratio) // 100
        em1_au_size = self.total_au_size - normal_au_size
        em1_au_size = em1_au_size if em1_au_size < self.geometry_desc.l44_enhanced1_max_n_alloc_u else self.geometry_desc.l44_enhanced1_max_n_alloc_u

        config_desc = api.get_config_descriptors()
        for unit in range(8):
            if unit < normal_lun_count:
                config_desc[0].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                config_desc[0].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                config_desc[0].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                config_desc[0].units[unit].b3_memory_type = api.MemoryType.NORMAL
                config_desc[0].units[unit].l4_num_alloc_units = normal_au_size//normal_lun_count
                config_desc[0].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                config_desc[0].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                config_desc[0].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE 
            else:
                config_desc[0].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                config_desc[0].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                config_desc[0].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                config_desc[0].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                config_desc[0].units[unit].l4_num_alloc_units = em1_au_size//em1_lun_count
                config_desc[0].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                config_desc[0].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                config_desc[0].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE 
        
        config_desc[0].header.b2_conf_desc_continue = 0
        push_write_config(config_desc[0], index=0)


        if result == RECONFIGURATION_STATUS.FAIL.value:
            try:
                ExecuteCMD.send(clear_on_success=False, skip_response_check= True)
            except:
                response = cast(api.QueryResponse, ExecuteCMD.read_response(0))
                logger.info(f'response = {response.upiu.b6_query_response}')
            ExecuteCMD.clear()
            if test_case != 2 and response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE: 
                logger.error_lb('Write LUN configuration')
                logger.error_fp(f'Expect the write LUN configuration response to be {api.QueryResponseCode.GENERAL_FAILURE}, but received {response.upiu.b6_query_response}')
                raise SIGHTING_RESPONSE_UNEXPECTED
            elif test_case == 2 and response.upiu.b6_query_response != api.QueryResponseCode.PARAM_ALREADY_WRITTEN:
                logger.error_lb('Write LUN configuration')
                logger.error_fp(f'Expect the write LUN configuration response to be {api.QueryResponseCode.PARAM_ALREADY_WRITTEN}, but received {response.upiu.b6_query_response}')
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

    def set_config_descriptor_lock(self, isLock:int)-> None:
        logger.info('Issue VU 0xD085 to Unlock LU Attribute Configuration-Description')
        issue_D085_unlock_LU_attribute_configuration()
        logger.info(f'Write attribute idn = {api.AttributeIDN.CONFIG_DESCR_LOCK} and value = {isLock}')
        api.write_attribute(idn = api.AttributeIDN.CONFIG_DESCR_LOCK, val = isLock)

        bConfigDescrLock = api.read_attribute(idn=api.AttributeIDN.CONFIG_DESCR_LOCK)
        logger.info(f'attribute 0Bh(bConfigDescrLock) value = {bConfigDescrLock}')
        if bConfigDescrLock != isLock:
            logger.error_lb('Issue VU D085 to Unlock LU Attribute configuration description and write attribute 0Bh(bConfigDescrLock)')
            logger.error_fp(f'Write attribute 0Bh(bConfigDescrLock) is {isLock}, but read attribute is {bConfigDescrLock}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def lun_reconfiguration_test(self, PSA_state:api.PSAState) -> None:
        for case in range(4):
            if case == 0:
                logger.info(f'Verify the reconfiguration flow for PSA state = {PSA_state} when bConfigDescrLock is set to 0x0(unlock) and PEC <= 30')
                ec = random.randint(0, 30)
                self.set_EC_count(ec)
                logger.info(f'Set EC count = {ec}')
            elif case == 1:
                logger.info(f'Verify the reconfiguration flow for PSA state = {PSA_state} when bConfigDescrLock is set to 0x0(unlock) and PEC > 30')
                ec = random.randint(31, 100)
                self.set_EC_count(ec)
                logger.info(f'Set EC count = {ec}')
            elif case == 2:
                logger.info(f'Verify the reconfiguration flow for PSA state = {PSA_state} when bConfigDescrLock is set to 0x1(lock)')
                ec = random.randint(0, 30)
                self.set_EC_count(ec)
                logger.info(f'Set EC count = {ec}')
            elif case == 3:
                logger.info(f'Verify that bConfigDescrLock can be restored form 0x1 to 0x0 via D085 VU in PSA state = {PSA_state}')

            bConfigDescrLock = CONFIG_DESCRIPTOR_LOCK.LOCK.value if case == 2 else CONFIG_DESCRIPTOR_LOCK.UNLOCK.value
           
            logger.info(f'Write attribute 0Bh(bConfigDescrLock) with value {bConfigDescrLock} expect response is success')
            self.set_config_descriptor_lock(bConfigDescrLock)

            if bConfigDescrLock == CONFIG_DESCRIPTOR_LOCK.LOCK.value:
                result = RECONFIGURATION_STATUS.FAIL.value
            else:
                if PSA_state == api.PSAState.OFF:
                    result = RECONFIGURATION_STATUS.SUCCESS.value
                elif PSA_state == api.PSAState.SOLDERED:
                    result = RECONFIGURATION_STATUS.FAIL.value if case == 1 else RECONFIGURATION_STATUS.SUCCESS.value
                else:
                    result = RECONFIGURATION_STATUS.FAIL.value

            erase_cnt_of_vb, _, _ = get_all_VB_erase_count()
            max_ec = max(erase_cnt_of_vb[0:self.fw_geometry.l52_total_vb_count])
            logger.info(f'Get max erase count =  {max_ec}')

            normal_ratio = random.randint(10, 90)
            em1_ratio = 100 - normal_ratio
            logger.info(f'Reconfig LUN with normal ratio {normal_ratio} and em1 ratio {em1_ratio}')
            self.re_config_lun(normal_ratio, em1_ratio, result, case)

            logger.info(f'Check warning byte in health report')
            _, report = issue_40FE_to_read_enhanced_health_report() 

            if case == 1 and max_ec > 30 and PSA_state == api.PSAState.OFF:
                if report.lun_reconfig_ec_warning.value != 1:
                    logger.error_lb('Check the warning byte shall be mapped at 140h offset of the Health Report')
                    logger.error_fp(f'Expect the warning byte shall be 1, but current is {report.lun_reconfig_ec_warning.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                if report.lun_reconfig_ec_warning.value != 0:
                    logger.error_lb('Check the warning byte shall be mapped at 140h offset of the Health Report')
                    logger.error_fp(f'Expect the warning byte shall be 0, but current is {report.lun_reconfig_ec_warning.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

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

    def config_backup(self) -> None:
        for i in range(4):
            if i == 3:
                self.backup_setting[i].header.b2_conf_desc_continue = 0
            else:
                self.backup_setting[i].header.b2_conf_desc_continue = 1
            push_write_config(self.backup_setting[i], index=i) 
        ExecuteCMD.send()

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

    def check_PSA_state(self, state:int) -> None:
        psa_state = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{psa_state:02X}')
        if psa_state != state:
            logger.error_lb('Read PSA State to check value')
            logger.error_fp(f'Expect the bPSAState should be 0x{state:02X},  but current value is 0x{psa_state:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        pass
run = Pattern().run
if __name__ == "__main__":
    run()