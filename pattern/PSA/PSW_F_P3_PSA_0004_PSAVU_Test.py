from copy import deepcopy
from enum import IntEnum
import random
import time
from typing import List, cast

import package_root
from Script import api
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.api.exception import *
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.api.ufs_api.defines.constant_define import *
from Script import project_api

_sdk = api.shared.sdk

class trimtype(IntEnum):
    POR = 0
    PSA = 1
    SLx = 2

class VB_group_for_list(int):
    CURRENT_L2_MLC = 0x07
    USED_BLK_POOL_MLC = 0x11

def check_timeout(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False

class Pattern(UFSTC):
    def config_precondition(self) -> None:
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.b17_write_booster_buffer_type = 1
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x400
        for i in range(4): 
            for unit in range(8):
                LU_number = i * 8 + unit
                if LU_number == 0 or LU_number == 1:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[i].units[unit].l4_num_alloc_units = self.total_au // 4
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD if LU_number == 0 else api.ProvisioningType.THIN_PROVISIONING_ERASE
                    self.sensitiveLU.append(LU_number) if LU_number not in self.sensitiveLU else None
                    self.sensitiveLU_start_lba[LU_number] = 0
                elif LU_number == 2 or LU_number == 3:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[i].units[unit].l4_num_alloc_units = self.total_au // 4
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD if LU_number == 2 else api.ProvisioningType.THIN_PROVISIONING_ERASE
                    self.non_sensitiveLU.append(LU_number) if LU_number not in self.non_sensitiveLU else None
                    self.non_sensitiveLU_start_lba[LU_number] = 0
                else:
                    config_descs[i].units[unit].b0_lu_enable = 0
                    config_descs[i].units[unit].l4_num_alloc_units = 0
            if i == 3:
                config_descs[i].header.b2_conf_desc_continue = 0
            else:
                config_descs[i].header.b2_conf_desc_continue = 1
            api.push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        
    def re_config(self) -> None:
        for i in range(4):
            if i == 3:
                self.backup_setting[i].header.b2_conf_desc_continue = 0
            else:
                self.backup_setting[i].header.b2_conf_desc_continue = 1
            api.push_write_config(self.backup_setting[i], index=i)
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

    def write_non_sensitive_LU(self, write_size:int) -> None:
        max_chunk_size = BLOCK4K_SIZE_128M_BYTE
        for lun in self.non_sensitiveLU:
            datalen = write_size >> 1
            while datalen > 0:
                chunk_size = min(max_chunk_size, datalen)
                write10 = ExecuteCMD.Write10()
                write10.assign(lun=lun, lba=self.non_sensitiveLU_start_lba[lun], length=chunk_size, fua=0)
                write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
                datalen -= chunk_size
                self.non_sensitiveLU_start_lba[lun] += chunk_size
                ExecuteCMD.enqueue(write10)
            
            ExecuteCMD.send()

    def check_PSA_post_reflow_progress_by405C(self, expected_progress_value:int) -> None:
        reflow_progress = project_api.issue_405C_get_PSA_post_reflow_progress()
        logger.info(f'Percentage For SLC PSA blocks = {reflow_progress.PercentageForSLCPSAblocks.value}, Percentage For SLC PSA blocks2 = {reflow_progress.PercentageForSLCPSAblocks2.value}, Zero constant = {reflow_progress.ZeroConstant.value}')
        if reflow_progress.PercentageForSLCPSAblocks.value != reflow_progress.PercentageForSLCPSAblocks2.value or reflow_progress.PercentageForSLCPSAblocks.value != expected_progress_value:
            logger.error(f'Issue VU 0x405C to check PSA reflow percentage should be {expected_progress_value} but not')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if reflow_progress.ZeroConstant.value != 0:
            logger.error(f'The output of VU 0x405C offset 8:11 should be 0 but current value is {reflow_progress.ZeroConstant.value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def check_PSA_migration_state(self, expected_state:int, expected_read_trim:int) -> None:
        migration_state = project_api.issue_404F_get_PSA_migration_state()
        logger.info(f'Migration state = {migration_state.IsPsaOngoing.value}, Host read trim = {migration_state.HostReadWithPSATrim.value}')
        if migration_state.IsPsaOngoing.value != expected_state:
            logger.error(f'Issue VU 0x404F to check PSA migration state value should be {expected_state} but current value is {migration_state.IsPsaOngoing.value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if migration_state.HostReadWithPSATrim.value != expected_read_trim:
            logger.error(f'Issue VU 0x404F to check host read trim should be {expected_read_trim} but current value is {migration_state.HostReadWithPSATrim.value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def check_PSA_remain_buffer_size(self, expected_remain_size:int) -> None:
        PSA_buffer = project_api.issue_4050_check_PSA_buffer_size()
        logger.info(f'PSA remain buffer size = {PSA_buffer.RemainPSABufferSize.value}')
        if PSA_buffer.RemainPSABufferSize.value != expected_remain_size:
            logger.error(f'Issue VU 0x4050 to check PSA remain buffer size value should be {expected_remain_size} but current value is {PSA_buffer.RemainPSABufferSize.value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

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

    def verify_health_report_PSA_relative_field(self, expected_state:int=0xFFFF, expected_offcnt:int=0XFFFF, expected_PSAsize:int=0xFFFF, expected_progress:int=0xFFFF) -> int:
        rsp, HR = project_api.issue_40FE_to_read_enhanced_health_report() 
        state = HR.psastate.value
        offcnt = HR.psa_off_counter.value
        PSAsize = HR.psa_data_size.value
        progress = HR.psa_refresh_percentage_progress.value
        logger.info(f'Health report field state = {state}, offcnt = {offcnt}, PSAsize = {PSAsize}, progress = {progress}')
        if state != expected_state and expected_state != 0xFFFF:
            logger.error_lb(f'Check PSA state of health report during PSA flow')
            logger.error_fp(f'Expected PSA state is {expected_state} but current PSA state in health report is {state}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if offcnt != expected_offcnt and expected_offcnt != 0xFFFF:
            logger.error_lb(f'Check PSA offcount of health report during PSA flow')
            logger.error_fp(f'Expected PSA offcount is {expected_offcnt} but current PSA offcount in health report is {offcnt}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if PSAsize != expected_PSAsize and expected_PSAsize != 0xFFFF:
            logger.error_lb(f'Check PSA size of health report during PSA flow')
            logger.error_fp(f'Expected PSA size is {expected_PSAsize} but current PSA size in health report is {PSAsize}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if expected_progress != 0xFFFF:
            if progress > 100:
                logger.error_lb(f'Check PSA refresh progress of health report during PSA flow')
                logger.error_fp(f'Expected PSA refresh progress between 0 and 100, but current PSA refresh progress in health report is {progress}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL                
            if (expected_progress == 0 or expected_progress == 100) and progress != expected_progress:
                logger.error_lb(f'Check PSA refresh progress of health report during PSA flow')
                logger.error_fp(f'Expected PSA refresh progress is {expected_progress} but current PSA refresh progress in health report is {progress}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if expected_progress > 0 and progress < expected_progress:                
                logger.error_lb(f'Check PSA refresh progress of health report during PSA flow')
                logger.error_fp(f'Expected PSA refresh progress is {expected_progress} or larger than that, but current PSA refresh progress in health report is {progress}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        return offcnt

    def check_vb_mlc_trim(self, expected_trim:int) -> None:
        logger.info('Check mlc vb trim type')
        rsp, vb_info = api.get_vb_info()
        for vb_num in range(self.fw_geometry.l52_total_vb_count):
            four_bytes = vb_info[vb_num * 4:(vb_num + 1) * 4]
            integer_value = int.from_bytes(four_bytes, byteorder='little')
            vb_group = integer_value & 0x3F
            access_mode = (integer_value >> 6) & 0x3
            vb_trim = (integer_value >> 16) & 0x3
            # logger.info(f'VB {vb_num}, group = {vb_group}, access = {access_mode}, trim type = {vb_trim}') # for debug
            if vb_group == VB_group_for_list.USED_BLK_POOL_MLC or vb_group == VB_group_for_list.CURRENT_L2_MLC:
                if vb_trim != expected_trim:
                    logger.error_lb(f'Check vb trim should be {expected_trim} in PSA flow testing')
                    logger.error_fp(f'VB {vb_num}, group = {vb_group}, access = {access_mode}, trim type = {vb_trim}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def get_hwsetting_inhibition_time(self) -> int: 
        self.hw_setting = api.HwSetting.get_instance()
        self.hw_setting.update_from_device()
        value = self.hw_setting.get_local_val(api.HwSettingField.INHIBITION_TIME)
        return value
    
    def check_post_reflow_state_during_inhibit_phase(self) -> None:
        while True:
            pass_time_sec = time.time() - self.inhibit_start_time
            if pass_time_sec >= self.inhibition_time_sec * 0.9:
                break
            else:
                time.sleep(2)
                cmd_idx:List[int] = []
                project_api.push_405C_get_PSA_post_reflow_progress(cmd_idx=cmd_idx)
                project_api.push_404F_get_PSA_migration_state(cmd_idx=cmd_idx)
                ExecuteCMD.send(clear_on_success=False)
                rsp = ExecuteCMD.read_response(index=cmd_idx[0])
                reflow_progress = project_api.PSAPostReflowProgress(rsp.data)
                rsp = ExecuteCMD.read_response(index=cmd_idx[1])
                migration_state = project_api.PSAMigrationState(rsp.data)
                ExecuteCMD.clear()
                logger.info(f'pass time = {pass_time_sec}, current state = {migration_state.IsPsaOngoing.value} and progress = {reflow_progress.PercentageForSLCPSAblocks.value}')
                if reflow_progress.PercentageForSLCPSAblocks.value != 0 or migration_state.IsPsaOngoing.value != 0:
                    logger.error_lb('Check post reflow migration state and progress after 1st write')
                    logger.error_fp(f'Shoule keep The migration state 0(means refresh does not completed) and progress 0(means idle during inhibit phase), current state = {migration_state.IsPsaOngoing.value} and progress = {reflow_progress.PercentageForSLCPSAblocks.value}, pass time = {pass_time_sec}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    
    def pre_process(self) -> None:
        logger.info(api.CommonPath.root)
        logger.info(api.CommonPath.development_report)
        logger.info(api.CommonPath.ini)
        logger.info(api.CommonPath.mp_tool)
        logger.info(api.CommonPath.tcsp)
        logger.info(api.CommonPath.report)
        self.param = api.shared.param
        self.total_au = int(self.param.gGeometry.q4_total_raw_device_capacity / (self.param.gGeometry.l13_segment_size * self.param.gGeometry.b17_allocation_unit_size))
        self.write_record = api.get_empty_write_record()
        self.fw_geometry = api.get_fw_geometry()
        self.backup_setting = api.get_config_descriptors()
        self.SLC_VB_size = self.fw_geometry.l84_vb_size_u0 >> 3 # menas (var * 512 / 4096) to change unit from sector to blocks
        self.sensitiveLU:List[int] = []
        self.non_sensitiveLU:List[int] = []
        self.sensitiveLU_start_lba:dict[int, int] = {}
        self.non_sensitiveLU_start_lba:dict[int, int] = {}
        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        self.PSAoffcount_when_pattern_start =  self.verify_health_report_PSA_relative_field()
        self.psa_timeout = pow(2, self.param.gDevice.b41_psa_state_timeout) * 100
        logger.info(f'PSA timeout is {self.psa_timeout}')
        self.inhibition_time_sec = self.get_hwsetting_inhibition_time()
        logger.info(f'Inhibition time = {self.inhibition_time_sec}(sec)')

    def step1(self) -> None:
        for interrupt_PSA_test in range(2):
            logger.flow(1, 'Config multi 2 normal memory type LU / 2 EM1 LU and WriteBooster buffer 4GB')
            self.config_precondition()
            self.update_unit_desc()
            self.update_device_desc()
            test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
            for lun in range(self.param.gMaxNumberLU):
                if self.param.gUnit[lun].b3_lu_enable != api.LUNEnable.DISABLE:
                    test_unit_ready.set_option(lun=lun)
                    ExecuteCMD.enqueue(test_unit_ready)

            logger.flow(2, 'Set dPSADataSize as 16GB and issue VU 0x4050 get remain PSA buffer size')
            set_dPSADataSize_value = BLOCK4K_SIZE_16G_BYTE
            api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=set_dPSADataSize_value)
            self.check_PSA_remain_buffer_size(expected_remain_size=0)

            logger.flow(3, 'Issue VU 0x404F to get PSA migration state and host read trim')
            self.check_PSA_migration_state(expected_state=0,expected_read_trim=0)
            self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.OFF, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_PSAsize=0, expected_progress=0)

            logger.flow(4, 'Write 8GB data in normal memory type and issue VU 0x4050 get remain PSA buffer size')
            max_chunk_size = BLOCK4K_SIZE_128M_BYTE
            for lun in self.sensitiveLU:
                datalen = BLOCK4K_SIZE_4G_BYTE
                while datalen > 0:
                    chunk_size = min(max_chunk_size, datalen)
                    write10 = ExecuteCMD.Write10()
                    write10.assign(lun=lun, lba=self.sensitiveLU_start_lba[lun], length=chunk_size, fua=0)
                    write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
                    datalen -= chunk_size
                    self.sensitiveLU_start_lba[lun] += chunk_size
                    ExecuteCMD.enqueue(write10)

                ExecuteCMD.send(clear_on_success=False)
                for cmd in ExecuteCMD._cmd_list:
                    api.save_write_info_by_cmd(cmd, write_record=self.write_record)

                ExecuteCMD.clear()

            self.check_PSA_remain_buffer_size(expected_remain_size=0)
            self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.OFF, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_PSAsize=0, expected_progress=0)

            logger.flow(5, 'Unmap all data')
            unmap = ExecuteCMD.Unmap()
            for lun in self.sensitiveLU:
                unmap.assign(lun=lun, lba=0, length=self.param.gUnit[lun].q11_logical_block_count)
                ExecuteCMD.enqueue(unmap)

            ExecuteCMD.send()
            self.sensitiveLU_start_lba.clear()
            for lun in self.sensitiveLU:
                self.sensitiveLU_start_lba[lun] = 0
                self.write_record[lun].clear()

            logger.flow(6, 'Set bPSAState as pre_soldering to start PSA flow and issue VU 0x4050 get remain PSA buffer size')
            ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True, timeout=self.psa_timeout).enqueue()
            ExecuteCMD.send()
            self.check_PSA_remain_buffer_size(expected_remain_size=set_dPSADataSize_value)

            logger.flow(7, 'Issue VU 0x405C to get PSA Post Reflow progress and the value should be 0')
            self.check_PSA_post_reflow_progress_by405C(expected_progress_value=0x0)

            logger.flow(8, 'Issue VU 0x404F to get PSA migration state and host read trim')
            self.check_PSA_migration_state(expected_state=0,expected_read_trim=0)
            self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.PRE_SOLDERING, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_PSAsize=0, expected_progress=0)

            logger.flow(9, 'Write 14.5GB data in normal memory type / EM1 LU and issue VU 0x4050 get remain PSA buffer size')
            write_size = BLOCK4K_SIZE_10G_BYTE + BLOCK4K_SIZE_4G_BYTE + BLOCK4K_SIZE_512M_BYTE
            for lun in self.sensitiveLU:
                datalen = write_size >> 1
                while datalen > 0:
                    chunk_size = min(max_chunk_size, datalen)
                    write10 = ExecuteCMD.Write10()
                    write10.assign(lun=lun, lba=self.sensitiveLU_start_lba[lun], length=chunk_size, fua=0)
                    write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
                    datalen -= chunk_size
                    self.sensitiveLU_start_lba[lun] += chunk_size
                    ExecuteCMD.enqueue(write10)

                ExecuteCMD.send(clear_on_success=False)
                for cmd in ExecuteCMD._cmd_list:
                    api.save_write_info_by_cmd(cmd, write_record=self.write_record)

                ExecuteCMD.clear()

            self.write_non_sensitive_LU(write_size=write_size)
            self.check_PSA_remain_buffer_size(expected_remain_size=set_dPSADataSize_value - write_size)
            self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.PRE_SOLDERING, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_PSAsize=self.sensitiveLU_start_lba[0]+self.sensitiveLU_start_lba[1], expected_progress=0)

            logger.flow(10, 'Read normal memory LU data and Issue VU 0x404F to get PSA migration state and host read trim')
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=self.sensitiveLU[0], lba=0, length=BLOCK4K_SIZE_16M_BYTE)
            ExecuteCMD.enqueue(read10)
            ExecuteCMD.send()
            self.check_PSA_migration_state(expected_state=0,expected_read_trim=1)

            logger.flow(11, 'Read EM1 LU data and Issue VU 0x404F to get PSA migration state and host read trim')
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=self.non_sensitiveLU[0], lba=0, length=BLOCK4K_SIZE_16M_BYTE)
            ExecuteCMD.enqueue(read10)
            ExecuteCMD.send()   
            self.check_PSA_migration_state(expected_state=0,expected_read_trim=0)

            logger.flow(12, 'Set dPSADataSize as 17GB and issue VU 0x4050 get remain PSA buffer size')
            set_dPSADataSize_value = BLOCK4K_SIZE_16G_BYTE + BLOCK4K_SIZE_1G_BYTE
            api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=set_dPSADataSize_value)
            self.check_PSA_remain_buffer_size(expected_remain_size=set_dPSADataSize_value - write_size)
            self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.PRE_SOLDERING, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_PSAsize=self.sensitiveLU_start_lba[0]+self.sensitiveLU_start_lba[1], expected_progress=0)

            logger.flow(13, 'Write more 0.5GB data in normal memory LU and issue VU 0x4050 get remain PSA buffer size')
            write_more_size = BLOCK4K_SIZE_512M_BYTE
            for lun in self.sensitiveLU:
                datalen = write_more_size >> 1
                while datalen > 0:
                    chunk_size = min(max_chunk_size, datalen)
                    write10 = ExecuteCMD.Write10()
                    write10.assign(lun=lun, lba=self.sensitiveLU_start_lba[lun], length=chunk_size, fua=0)
                    write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
                    datalen -= chunk_size
                    self.sensitiveLU_start_lba[lun] += chunk_size
                    ExecuteCMD.enqueue(write10)

                ExecuteCMD.send(clear_on_success=False)
                for cmd in ExecuteCMD._cmd_list:
                    api.save_write_info_by_cmd(cmd, write_record=self.write_record)

                ExecuteCMD.clear()
            self.check_PSA_remain_buffer_size(expected_remain_size=set_dPSADataSize_value - write_size - write_more_size)
            self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.PRE_SOLDERING, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_PSAsize=self.sensitiveLU_start_lba[0]+self.sensitiveLU_start_lba[1], expected_progress=0)

            logger.flow(14, 'Write more data over dPSADataSize until fill allocated VBs and issue VU 0x4050 get remain PSA buffer size')
            PSA_SLC_VB_allocable = (set_dPSADataSize_value // self.SLC_VB_size) + 1 if set_dPSADataSize_value % self.SLC_VB_size == 0 else (set_dPSADataSize_value // self.SLC_VB_size) + 2
            PSA_data_limit = PSA_SLC_VB_allocable * self.SLC_VB_size
            logger.info(f'dPSADataSize = {set_dPSADataSize_value}, SLC VB size = {self.SLC_VB_size}, expected PSA VB allocable = {PSA_SLC_VB_allocable}, data length limit = {PSA_data_limit}')
            for lun in self.sensitiveLU:
                datalen = (PSA_data_limit >> 1) - self.sensitiveLU_start_lba[lun]
                datalen = datalen + 1 if PSA_data_limit % 2 != 0 and lun == 1 else datalen
                while datalen > 0:
                    chunk_size = min(max_chunk_size, datalen)
                    write10 = ExecuteCMD.Write10()
                    write10.assign(lun=lun, lba=self.sensitiveLU_start_lba[lun], length=chunk_size, fua=0)
                    write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
                    datalen -= chunk_size
                    self.sensitiveLU_start_lba[lun] += chunk_size
                    ExecuteCMD.enqueue(write10)

                ExecuteCMD.send(clear_on_success=False)
                for cmd in ExecuteCMD._cmd_list:
                    api.save_write_info_by_cmd(cmd, write_record=self.write_record)

                ExecuteCMD.clear()

            self.check_PSA_remain_buffer_size(expected_remain_size=0)
            self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.PRE_SOLDERING, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_PSAsize=self.sensitiveLU_start_lba[0]+self.sensitiveLU_start_lba[1], expected_progress=0)

            logger.flow(15, 'Set dPSADataSize as 14GB and issue VU 0x4050 get remain PSA buffer size')
            api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=BLOCK4K_SIZE_10G_BYTE + BLOCK4K_SIZE_4G_BYTE)
            self.check_PSA_remain_buffer_size(expected_remain_size=0)
            self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.PRE_SOLDERING, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_PSAsize=self.sensitiveLU_start_lba[0]+self.sensitiveLU_start_lba[1], expected_progress=0)

            logger.flow(16, 'Set dPSADataSize as dPSAMaxDataSize, write for fill dPSADataSize and issue VU 0x4050 get remain PSA buffer size')
            set_dPSADataSize_value = self.param.gDevice.l37_psa_max_data_size
            api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=set_dPSADataSize_value)
            expected_remain_size = set_dPSADataSize_value
            for key in self.sensitiveLU_start_lba:
                expected_remain_size -= self.sensitiveLU_start_lba[key]
            logger.info(f'Expected PSA remain buffer size is {expected_remain_size}')
            self.check_PSA_remain_buffer_size(expected_remain_size=expected_remain_size)

            for lun in self.sensitiveLU:
                datalen = (set_dPSADataSize_value >> 1) - self.sensitiveLU_start_lba[lun] - (interrupt_PSA_test * 10) # for remain PSA buffer size is not 0 test
                datalen = datalen + 1 if set_dPSADataSize_value % 2 != 0 and lun == 1 else datalen
                while datalen > 0:
                    random_chunk_size = random.randint(BLOCK4K_SIZE_4K_BYTE, WRITE_10_MAX_BLOCK_LEN)
                    chunk_size = min(random_chunk_size, datalen)
                    write10 = ExecuteCMD.Write10()
                    write10.assign(lun=lun, lba=self.sensitiveLU_start_lba[lun], length=chunk_size, fua=0)
                    write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
                    datalen -= chunk_size
                    self.sensitiveLU_start_lba[lun] += chunk_size
                    ExecuteCMD.enqueue(write10)

                ExecuteCMD.send(clear_on_success=False)
                for cmd in ExecuteCMD._cmd_list:
                    api.save_write_info_by_cmd(cmd, write_record=self.write_record)

                ExecuteCMD.clear()
                expected_remain_size = set_dPSADataSize_value
                for key in self.sensitiveLU_start_lba:
                    expected_remain_size -= self.sensitiveLU_start_lba[key]
                logger.info(f'Expected PSA remain buffer size is {expected_remain_size}')
                self.check_PSA_remain_buffer_size(expected_remain_size=expected_remain_size)
            self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.PRE_SOLDERING, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_PSAsize=self.sensitiveLU_start_lba[0]+self.sensitiveLU_start_lba[1], expected_progress=0)
            self.check_vb_mlc_trim(expected_trim = trimtype.PSA)

            logger.flow(17, 'Set bPSAState as loading_complete')
            ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).set_option(wait_queue_empty=True, timeout=self.psa_timeout).enqueue()
            ExecuteCMD.send()
            self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.LOADING_COMPLETE, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_PSAsize=self.sensitiveLU_start_lba[0]+self.sensitiveLU_start_lba[1], expected_progress=0)              

            logger.flow(18, 'Issue VU 0x4050 get remain PSA buffer size should keep')
            self.check_PSA_remain_buffer_size(expected_remain_size=expected_remain_size)

            logger.flow(19, 'Read normal memory LU data and Issue VU 0x404F to get PSA migration state and host read trim')
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=self.sensitiveLU[0], lba=0, length=BLOCK4K_SIZE_16M_BYTE)
            ExecuteCMD.enqueue(read10)
            ExecuteCMD.send()
            self.check_PSA_migration_state(expected_state=0,expected_read_trim=1)

            logger.flow(20, 'Read EM1 LU data and Issue VU 0x404F to get PSA migration state and host read trim')
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=self.non_sensitiveLU[0], lba=0, length=BLOCK4K_SIZE_16M_BYTE)
            ExecuteCMD.enqueue(read10)
            ExecuteCMD.send()        
            self.check_PSA_migration_state(expected_state=0,expected_read_trim=0)

            logger.flow(21, 'Issue VU 0x405C to get PSA Post Reflow progress and the value should be 0')
            self.check_PSA_post_reflow_progress_by405C(expected_progress_value=0x0)
            self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.LOADING_COMPLETE, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_PSAsize=self.sensitiveLU_start_lba[0]+self.sensitiveLU_start_lba[1], expected_progress=0)              

            logger.flow(22, 'Issue power cycle')
            api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=True)
            self.inhibit_start_time = time.time()

            logger.flow(23, 'Read normal memory LU data and Issue VU 0x404F to get PSA migration state and host read trim')
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=self.sensitiveLU[0], lba=BLOCK4K_SIZE_16M_BYTE, length=BLOCK4K_SIZE_16M_BYTE)
            ExecuteCMD.enqueue(read10)
            ExecuteCMD.send()
            self.check_PSA_migration_state(expected_state=0,expected_read_trim=1)

            logger.flow(24, 'Read EM1 LU data and Issue VU 0x404F to get PSA migration state and host read trim')
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=self.non_sensitiveLU[0], lba=BLOCK4K_SIZE_16M_BYTE, length=BLOCK4K_SIZE_16M_BYTE)
            ExecuteCMD.enqueue(read10)
            ExecuteCMD.send()              
            self.check_PSA_migration_state(expected_state=0,expected_read_trim=0)

            logger.flow(25, 'Issue VU 0x405C to get PSA Post Reflow progress and the value should be 0')
            self.check_PSA_post_reflow_progress_by405C(expected_progress_value=0x0)
            self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.LOADING_COMPLETE, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_PSAsize=self.sensitiveLU_start_lba[0]+self.sensitiveLU_start_lba[1], expected_progress=0)

            if interrupt_PSA_test == 1:
                logger.flow(26, 'PSA interrupt test has been do')
            else:
                logger.flow(26, 'Set bPSAState as off(00h) to interrupt PSA flow and issue VU 0x4050 get remain PSA buffer size should be 0, restart PSA flow from step1')
                ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.OFF).set_option(wait_queue_empty=True,timeout=self.psa_timeout).enqueue()
                ExecuteCMD.send()
                self.check_PSA_remain_buffer_size(expected_remain_size=0)

        logger.flow(27, '1st write and check post reflow state ')
        ExecuteCMD.Write10().assign(lun=self.sensitiveLU[0], lba=self.sensitiveLU_start_lba[self.sensitiveLU[0]], length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        ExecuteCMD.send(clear_on_success=False)
        for cmd in ExecuteCMD._cmd_list:
            api.save_write_info_by_cmd(cmd, write_record=self.write_record)
        ExecuteCMD.clear()
        self.check_post_reflow_state_during_inhibit_phase()

        logger.flow(28, 'Issue VU 0x4050 get remain PSA buffer size should be 0 after 1st write')
        self.check_PSA_remain_buffer_size(expected_remain_size=0)
        self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.SOLDERED, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_PSAsize=self.sensitiveLU_start_lba[0]+self.sensitiveLU_start_lba[1])

        logger.flow(29, 'Polling VU 0x405C to PSA Post Reflow progress and VU 0x404F to get PSA migration state and host read trim')
        start_time = time.time()
        timeout_min = 15
        Power_case_test_done = False
        before_loop_progress = 0
        while True:
            time.sleep(2)
            cmd_idx:List[int] = []
            project_api.push_405C_get_PSA_post_reflow_progress(cmd_idx=cmd_idx)
            project_api.push_404F_get_PSA_migration_state(cmd_idx=cmd_idx)
            ExecuteCMD.send(clear_on_success=False)
            rsp = ExecuteCMD.read_response(index=cmd_idx[0])
            reflow_progress = project_api.PSAPostReflowProgress(rsp.data)
            rsp = ExecuteCMD.read_response(index=cmd_idx[1])
            migration_state = project_api.PSAMigrationState(rsp.data)
            ExecuteCMD.clear()
            logger.info(f'Reflow progress = {reflow_progress.PercentageForSLCPSAblocks.value}, migration state = {migration_state.IsPsaOngoing.value}, host read trim = {migration_state.HostReadWithPSATrim.value}')
            if migration_state.HostReadWithPSATrim.value == 1:
                logger.error(f'Host read trim should be 0 when device soldered but current value is {migration_state.HostReadWithPSATrim.value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if reflow_progress.PercentageForSLCPSAblocks.value != reflow_progress.PercentageForSLCPSAblocks2.value:
                logger.error(f'PercentageForSLCPSAblocks[0:3] = {reflow_progress.PercentageForSLCPSAblocks.value}, PercentageForSLCPSAblocks2[4:7] = {reflow_progress.PercentageForSLCPSAblocks2.value} mismatch')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if reflow_progress.ZeroConstant.value != 0:
                logger.error(f'The output of VU 0x405C offset 8:11 should be 0 but current value is {reflow_progress.ZeroConstant.value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if reflow_progress.PercentageForSLCPSAblocks.value == 100 and migration_state.IsPsaOngoing.value == 0x01:
                self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.SOLDERED, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_progress = reflow_progress.PercentageForSLCPSAblocks.value, expected_PSAsize=self.sensitiveLU_start_lba[0]+self.sensitiveLU_start_lba[1])
                break
            elif reflow_progress.PercentageForSLCPSAblocks.value >= 100 or migration_state.IsPsaOngoing.value != 0x00:
                logger.error_lb('Check migration state and post reflow progress')
                logger.error_fp(f'Migration state should be 0x01 and reflow progress should below 100 but current progress = {reflow_progress.ZeroConstant.value} and state = {migration_state.IsPsaOngoing.value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            if reflow_progress.PercentageForSLCPSAblocks.value >= 50 and Power_case_test_done == False:
                self.verify_health_report_PSA_relative_field(expected_state=api.PSAState.SOLDERED, expected_offcnt=self.PSAoffcount_when_pattern_start + interrupt_PSA_test, expected_progress = reflow_progress.PercentageForSLCPSAblocks.value, expected_PSAsize=self.sensitiveLU_start_lba[0]+self.sensitiveLU_start_lba[1])
                api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET)
                Power_case_test_done = True
            if before_loop_progress > reflow_progress.PercentageForSLCPSAblocks.value:
                logger.error(f'Before loop progress = {before_loop_progress}, current loop progress = {reflow_progress.ZeroConstant.value}, it should not decrease during data relocation')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                before_loop_progress = reflow_progress.PercentageForSLCPSAblocks.value

            if check_timeout(start_time, timeout_min):
                logger.error(f'Expect reflow progress = 100 percent and migration state = 0 within {timeout_min}min, but current value: Reflow progress = {reflow_progress.PercentageForSLCPSAblocks.value}, migration state = {migration_state.IsPsaOngoing.value}')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
        self.check_vb_mlc_trim(expected_trim = trimtype.POR)

    def post_process(self) -> None:
        api.read_compare(write_record=self.write_record)
        self.VU_clear_PSA_state()
        self.re_config()
        pass


run = Pattern().run
if __name__ == "__main__":
    run()