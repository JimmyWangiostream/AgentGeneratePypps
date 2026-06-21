from copy import deepcopy
import random
import package_root
from Script import api
from typing import List, cast
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api

_sdk = api.shared.sdk

class Pattern(UFSTC):
    def config_LUN0_with_total_AU(self) -> None:
        config_descs = api.get_config_descriptors(print=True)
        self.backup_setting = deepcopy(config_descs)
        for i in range(4): 
            for unit in range(8):
                config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.DISABLE
                config_descs[i].units[unit].l4_num_alloc_units = 0
                config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                LU_number = i * 8 + unit
                if LU_number == 0:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[i].units[unit].l4_num_alloc_units = self.total_au
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
            config_descs[i].header.b2_conf_desc_continue = 0 if i == 3 else 1
            push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()

    def config_precondition(self) -> None:
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.b3_boot_enable = 1
        config_descs[0].header.b4_descr_access_en = 1
        config_descs[0].header.b5_init_power_mode = 1
        config_descs[0].header.b6_high_priority_lun = 0x5
        config_descs[0].header.b7_secure_removal_type = 0
        config_descs[0].header.b8_init_active_icc_level = 0
        config_descs[0].header.w9_periodic_rtc_update = 0
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 0
        config_descs[0].header.b17_write_booster_buffer_type = 1        
        
        for i in range(4): 
            for unit in range(8):
                LU_number = i * 8 + unit
                if LU_number == 0:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_descs[i].units[unit].b2_lu_write_protect = 0
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[i].units[unit].l4_num_alloc_units = 0x389B
                    config_descs[i].units[unit].b8_data_reliability = 0
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                    config_descs[i].units[unit].w11_context_capabilities = 0
                elif LU_number == 1:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_A
                    config_descs[i].units[unit].b2_lu_write_protect = 0
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[i].units[unit].l4_num_alloc_units = 0x3
                    config_descs[i].units[unit].b8_data_reliability = 0
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                    config_descs[i].units[unit].w11_context_capabilities = 0
                elif LU_number == 2:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_B
                    config_descs[i].units[unit].b2_lu_write_protect = 0
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[i].units[unit].l4_num_alloc_units = 0x3
                    config_descs[i].units[unit].b8_data_reliability = 0
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                    config_descs[i].units[unit].w11_context_capabilities = 0
                elif LU_number == 3:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_descs[i].units[unit].b2_lu_write_protect = 0
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[i].units[unit].l4_num_alloc_units = 0x1
                    config_descs[i].units[unit].b8_data_reliability = 0
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                    config_descs[i].units[unit].w11_context_capabilities = 0
                elif LU_number == 4:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_descs[i].units[unit].b2_lu_write_protect = 0
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[i].units[unit].l4_num_alloc_units = 0x182
                    config_descs[i].units[unit].b8_data_reliability = 0
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                    config_descs[i].units[unit].w11_context_capabilities = 0
                elif LU_number == 5:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_descs[i].units[unit].b2_lu_write_protect = 0
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[i].units[unit].l4_num_alloc_units = 0x2
                    config_descs[i].units[unit].b8_data_reliability = 0
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                    config_descs[i].units[unit].w11_context_capabilities = 0
                elif LU_number == 6:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_descs[i].units[unit].b2_lu_write_protect = 0
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[i].units[unit].l4_num_alloc_units = 0x3201
                    config_descs[i].units[unit].b8_data_reliability = 0
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                    config_descs[i].units[unit].w11_context_capabilities = 0
                elif LU_number == 7:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_descs[i].units[unit].b2_lu_write_protect = 0
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[i].units[unit].l4_num_alloc_units = 0xB0B
                    config_descs[i].units[unit].b8_data_reliability = 0
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                    config_descs[i].units[unit].w11_context_capabilities = 0
                else:
                    config_descs[i].units[unit].b0_lu_enable = 0
                    config_descs[i].units[unit].l4_num_alloc_units = 0
            config_descs[i].header.b2_conf_desc_continue = 0 if i == 3 else 1
            push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()

    def re_config(self) -> None:
        for i in range(4):
            if i == 3:
                self.backup_setting[i].header.b2_conf_desc_continue = 0
            else:
                self.backup_setting[i].header.b2_conf_desc_continue = 1
            push_write_config(self.backup_setting[i], index=i) 
        ExecuteCMD.send()

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

    def update_device_desc(self) -> None:
        device_descriptor = ExecuteCMD.ReadDescriptor()
        device_descriptor.assign(idn=api.DescriptorIDN.DEVICE)
        index = ExecuteCMD.enqueue(device_descriptor)
        ExecuteCMD.send(clear_on_success=False)
        api.update_descriptor(idn=api.DescriptorIDN.DEVICE, index=0, response=cast(api.QueryResponse, ExecuteCMD.read_response(index)))
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

    def pre_process(self) -> None:
        logger.info(api.CommonPath.root)
        logger.info(api.CommonPath.development_report)
        logger.info(api.CommonPath.ini)
        logger.info(api.CommonPath.mp_tool)
        logger.info(api.CommonPath.tcsp)
        logger.info(api.CommonPath.report)
        self.param = api.shared.param
        self.total_au = int(self.param.gGeometry.q4_total_raw_device_capacity / (self.param.gGeometry.l13_segment_size * self.param.gGeometry.b17_allocation_unit_size))
        self.write_record_PSA_data = api.get_empty_write_record()
        self.write_record_Boot_data = api.get_empty_write_record()
        self.non_sensitiveLU_write_start_lba = 0
        self.fw_geometry = api.get_fw_geometry()
        self.SLC_VB_size = self.fw_geometry.l84_vb_size_u0 >> 3 # menas (var * 512 / 4096) to change unit from sector to blocks
        self.flash_setting = api.get_flash_setting()
        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        self.psa_timeout = pow(2, self.param.gDevice.b41_psa_state_timeout) * 100
        logger.info(f'PSA timeout is {self.psa_timeout}')

    def step1(self) -> None:
        logger.flow(1, 'Verify qTotalRawDeviceCapacity of geometry descriptor')
        if self.flash_setting.Max_Fdevice == 1:
            expected_totalraw_byte = 127984992256
        elif self.flash_setting.Max_Fdevice == 2:
            expected_totalraw_byte = 255944818688
        elif self.flash_setting.Max_Fdevice == 4:
            expected_totalraw_byte = 511864471552
        logger.info(f'qTotalRawDeviceCapacity is {self.param.gGeometry.q4_total_raw_device_capacity}(512byte unit) and expected value is {expected_totalraw_byte}(byte unit), CE = {self.flash_setting.Max_Fdevice}')
        totalrawcapa_of_geometry_descriptor_byte = self.param.gGeometry.q4_total_raw_device_capacity * 512
        if totalrawcapa_of_geometry_descriptor_byte != expected_totalraw_byte:
            logger.error_lb('Check the qTotalRawDeviceCapacity of geometry descriptor shall as expected value')
            logger.error_fp(f'qTotalRawDeviceCapacity is {self.param.gGeometry.q4_total_raw_device_capacity}(512byte unit) and expected value is {expected_totalraw_byte}(byte unit), CE = {self.flash_setting.Max_Fdevice}')
            raise SIGHTING_FAIL_WRONG_CE_NUMBER_VALUE

        logger.flow(2, 'Config LUN0 with total AU and normal memory type')
        self.config_LUN0_with_total_AU()
        self.update_unit_desc()
        self.update_device_desc()
        test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
        for lun in range(self.param.gMaxNumberLU):
            if self.param.gUnit[lun].b3_lu_enable != api.LUNEnable.DISABLE:
                test_unit_ready.set_option(lun=lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send()

        logger.flow(3, 'Verify dPSAMaxDataSize of device descriptor')
        if self.flash_setting.Max_Fdevice == 1:
            max_SLC_pre_programming_capacity = 42661662720
        elif self.flash_setting.Max_Fdevice == 2:
            max_SLC_pre_programming_capacity = 85314936832
        elif self.flash_setting.Max_Fdevice == 4:
            max_SLC_pre_programming_capacity = 170621489152
        logger.info(f'dPSAMaxDataSize is {self.param.gDevice.l37_psa_max_data_size}(4Kbyte unit) and expected value is {max_SLC_pre_programming_capacity}(byte unit), CE = {self.flash_setting.Max_Fdevice}')
        dPSAMaxDataSize_of_device_descriptor_byte = self.param.gDevice.l37_psa_max_data_size * DATA_SIZE_4K_BYTE
        if dPSAMaxDataSize_of_device_descriptor_byte != max_SLC_pre_programming_capacity:
            logger.error_lb('Check the dPSAMaxDataSize of device descriptor shall as max SLC Pre-programming Capacity')
            logger.error_fp(f'dPSAMaxDataSize is {self.param.gDevice.l37_psa_max_data_size}(4Kbyte unit) and expected max SLC Pre-programming Capacity is {max_SLC_pre_programming_capacity}(byte unit), CE = {self.flash_setting.Max_Fdevice}')
            raise SIGHTING_FAIL_WRONG_CE_NUMBER_VALUE

        logger.flow(4, 'Config CP25_PreProgramming_Configuration condition, set bBootLunEn as 1 and bConfigDescrLock as 1')
        self.config_precondition()
        api.write_attribute(idn=api.AttributeIDN.BOOT_LUN_EN, val=1)
        api.write_attribute(idn=api.AttributeIDN.CONFIG_DESCR_LOCK, val=1)
        self.update_unit_desc()
        self.update_device_desc()

        logger.flow(5, 'Set dPSADataSize as 0x100000')
        set_dPSADataSize_value = 0x100000
        logger.info(f'Value of dPSAMaxDataSize is {self.param.gDevice.l37_psa_max_data_size} and set value as {set_dPSADataSize_value}')
        api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=set_dPSADataSize_value)
                 
        logger.flow(6, 'Set bPSAState as pre_soldering')
        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(timeout=self.psa_timeout).enqueue()
        ExecuteCMD.send()        

        logger.flow(7, 'Pre-load data to LUN0 with size < 0x400000KB')
        max_chunk_size = BLOCK4K_SIZE_64M_BYTE
        startLBA = 0
        datalen = (0x400000 // 4) - 1
        while datalen > 0:
            chunk_size = min(max_chunk_size, datalen)
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=0, lba=startLBA, length=chunk_size, fua=0)
            write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
            datalen -= chunk_size
            startLBA += chunk_size
            ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=False)
        for cmd in ExecuteCMD._cmd_list:
            api.save_write_info_by_cmd(cmd, write_record=self.write_record_PSA_data)
        ExecuteCMD.clear()

        logger.flow(8, 'Set bPSAState as Loading_Complete')
        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).set_option(timeout=self.psa_timeout).enqueue()
        ExecuteCMD.send()

        logger.flow(9, 'Verify preloaded data shall pass')
        api.read_compare(write_record=self.write_record_PSA_data)

        logger.flow(10, 'Program boot data to LUN1(BootA)')
        max_chunk_size = BLOCK4K_SIZE_16K_BYTE
        startLBA = 0
        datalen = self.param.gLUCapacity[1]
        while datalen > 0:
            chunk_size = min(max_chunk_size, datalen)
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=1, lba=startLBA, length=chunk_size, fua=0)
            write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
            datalen -= chunk_size
            startLBA += chunk_size
            ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=False)
        for cmd in ExecuteCMD._cmd_list:
            api.save_write_info_by_cmd(cmd, write_record=self.write_record_Boot_data)
        ExecuteCMD.clear()

        logger.flow(11, 'Program boot data to LUN2(BootB)')
        max_chunk_size = BLOCK4K_SIZE_16K_BYTE
        startLBA = 0
        datalen = self.param.gLUCapacity[2]
        while datalen > 0:
            chunk_size = min(max_chunk_size, datalen)
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=2, lba=startLBA, length=chunk_size, fua=0)
            write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
            datalen -= chunk_size
            startLBA += chunk_size
            ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=False)
        for cmd in ExecuteCMD._cmd_list:
            api.save_write_info_by_cmd(cmd, write_record=self.write_record_Boot_data)
        ExecuteCMD.clear()

        logger.flow(12, 'Verify boot data shall pass')
        api.read_compare(write_record=self.write_record_Boot_data)

        logger.flow(13, 'Issue power cycle')
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=True)

        logger.flow(14, '1st write with valid LBA/length and check bPSAState should be soldered')
        write_cmd = ExecuteCMD.Write10().assign(lun=0, lba=0x100000-1, length=BLOCK4K_SIZE_4K_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        ExecuteCMD.send(clear_on_success=False)
        for cmd in ExecuteCMD._cmd_list:
            api.save_write_info_by_cmd(cmd, write_record=self.write_record_PSA_data)
        ExecuteCMD.clear()

        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        if read_attr_value != api.PSAState.SOLDERED:
            logger.error_lb('Check bPSAState after 1st write')
            logger.error_fp(f'bPSAState should change in soldered state but current value is 0x{read_attr_value}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(15, 'Compare all data should pass')
        api.read_compare(write_record=self.write_record_PSA_data)
        api.read_compare(write_record=self.write_record_Boot_data)


    def post_process(self) -> None:
        self.VU_clear_PSA_state()
        project_api.issue_D085_unlock_LU_attribute_configuration()
        self.re_config()
        pass


run = Pattern().run
if __name__ == "__main__":
    run()