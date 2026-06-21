from copy import deepcopy
from enum import IntEnum
import time
import random
import package_root
from Script import api
from typing import List, cast
from Script.api.cmd_seq.response import CommandResponse
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api import cmd_seq as ExecuteCMD
from Script.api.ufs_api.fw_value.functions import read_fw_value
from Script.lib.sdk_lib.user.exception import DLL_RESPONSE_ERROR
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api

_sdk = api.shared.sdk
class RefreshMethod(IntEnum):
    ManualForce = 1
    ManualSelective = 2

class RefreshUnit(IntEnum):
    MinimumRefresh = 0
    OneHundredPercent = 1

class trimtype(IntEnum):
    POR = 0
    PSA = 1
    SLx = 2

class VB_group_for_list(int):
    CURRENT_L2_MLC = 0x07
    USED_BLK_POOL_MLC = 0x11

class Pattern(UFSTC):
    def config_LUN0_with_total_AU(self, memory_type:api.MemoryType) -> None:
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
                    config_descs[i].units[unit].b3_memory_type = memory_type
                    config_descs[i].units[unit].l4_num_alloc_units = self.total_au
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
            config_descs[i].header.b2_conf_desc_continue = 0 if i == 3 else 1
            push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()

    def re_config(self) -> None:
        for i in range(4):
            self.backup_setting[i].header.b2_conf_desc_continue = 0 if i == 3 else 1
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

    def sendcmd_keeperror(self, cmd_index:int) -> CommandResponse:
        try:
            ExecuteCMD.send(clear_on_success=False)
            response = ExecuteCMD.read_response(cmd_index)
        except DLL_RESPONSE_ERROR:
            response = ExecuteCMD.read_response(cmd_index)
        ExecuteCMD.clear()
        return response

    def set_inhibition_time(self, expected_inhibition_time_sec:int) -> None:
        hw_setting = api.HwSetting.get_instance()
        hw_setting.update_from_device()
        hw_setting.set_local_val(api.HwSettingField.INHIBITION_TIME, expected_inhibition_time_sec)
        hw_setting.set_to_device()
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=True)
        hw_setting.update_from_device()
        current_inhibition_time = hw_setting.get_local_val(api.HwSettingField.INHIBITION_TIME)
        if current_inhibition_time != expected_inhibition_time_sec:
            logger.error_lb(f'Modify HW setting about inhibition time with value = {expected_inhibition_time_sec}')
            logger.error_fp(f'Expect inhibition time should be {expected_inhibition_time_sec} after set hw setting but current value is {current_inhibition_time}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def check_post_reflow_state_during_inhibit_phase(self, polling_time_sec:int) -> None:
        while True:
            time.sleep(2)
            pass_time_sec = time.time() - self.inhibit_start_time
            if pass_time_sec >= polling_time_sec:
                break
            else:
                cmd_idx:List[int] = []
                project_api.push_405C_get_PSA_post_reflow_progress(cmd_idx=cmd_idx)
                project_api.push_404F_get_PSA_migration_state(cmd_idx=cmd_idx)
                ExecuteCMD.send(clear_on_success=False)
                rsp = ExecuteCMD.read_response(index=cmd_idx[0])
                self.reflow_progress = project_api.PSAPostReflowProgress(rsp.data)
                rsp = ExecuteCMD.read_response(index=cmd_idx[1])
                self.migration_state = project_api.PSAMigrationState(rsp.data)
                ExecuteCMD.clear()
                logger.info(f'pass time = {pass_time_sec}, current state = {self.migration_state.IsPsaOngoing.value} and progress = {self.reflow_progress.PercentageForSLCPSAblocks.value}')
                if self.reflow_progress.PercentageForSLCPSAblocks.value != 0 or self.migration_state.IsPsaOngoing.value != 0:
                    logger.error_lb('Check post reflow migration state and progress after 1st write')
                    logger.error_fp(f'Should keep The migration state 0(means refresh does not completed) and progress 0(means idle during inhibit phase), current state = {self.migration_state.IsPsaOngoing.value} and progress = {self.reflow_progress.PercentageForSLCPSAblocks.value}, pass time = {pass_time_sec}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def check_vb_mlc_trim(self, expected_trim:int) -> None:
        logger.info('Check mlc vb trim type')
        rsp, vb_info = api.get_vb_info()
        for vb_num in range(self.fw_geometry.l52_total_vb_count):
            four_bytes = vb_info[vb_num * 4:(vb_num + 1) * 4]
            integer_value = int.from_bytes(four_bytes, byteorder='little')
            vb_group = integer_value & 0x3F
            access_mode = (integer_value >> 6) & 0x3
            vb_trim = (integer_value >> 16) & 0x3
            # logger.info(f'VB {vb_num}, group = {vb_group}, access = {access_mode}, trim type = {vb_trim}')
            if vb_group == VB_group_for_list.USED_BLK_POOL_MLC or vb_group == VB_group_for_list.CURRENT_L2_MLC:
                if vb_trim != expected_trim:
                    logger.error_lb(f'Check vb trim should be {expected_trim} in PSA flow testing')
                    logger.error_fp(f'VB {vb_num}, group = {vb_group}, access = {access_mode}, trim type = {vb_trim}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def check_during_inhibition_time_and_inhibit_lock(self) -> None:
        inhibit_lock = self.get_inhibit_lock()
        pass_time = time.time() - self.inhibit_start_time
        logger.info(f'pass time = {pass_time}, current state = {self.migration_state.IsPsaOngoing.value} and progress = {self.reflow_progress.PercentageForSLCPSAblocks.value}')
        if pass_time > (self.setting_inhibition_time * 0.9):
            logger.error_lb(f'Issue HIR and polling PSA refresh progress should complete during inhibition phase')
            logger.error_fp(f'HIR to refresh PSA VB does not complete during inhibition time {self.setting_inhibition_time} sec, pass time {pass_time}')
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        elif inhibit_lock != 1:
            logger.error_lb(f'Issue HIR and polling PSA refresh progress should complete during inhibition phase')
            logger.error_fp(f'inhibit_lock shall keep 1 during inhibition time {self.setting_inhibition_time} sec, pass time {pass_time}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
    def get_inhibit_lock(self) -> int:
        return cast(int,read_fw_value('gInhibitMgr.lock'))

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
        self.SLC_VB_size = self.fw_geometry.l84_vb_size_u0 >> 3 # menas (var * 512 / 4096) to change unit from sector to blocks
        self.setting_inhibition_time = 240
        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        self.psa_timeout = pow(2, self.param.gDevice.b41_psa_state_timeout) * 100
        logger.info(f'PSA timeout is {self.psa_timeout}')

    def step1(self) -> None:
        logger.flow(1, 'Config LUN0 with total AU and enhanced memory type1 and check dPSAMaxDataSize should be 0')
        self.config_LUN0_with_total_AU(memory_type=api.MemoryType.ENHANCED_1)
        self.update_unit_desc()
        self.update_device_desc()
        test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
        for lun in range(self.param.gMaxNumberLU):
            if self.param.gUnit[lun].b3_lu_enable != api.LUNEnable.DISABLE:
                test_unit_ready.set_option(lun=lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send()
        if self.param.gDevice.l37_psa_max_data_size != 0:
            logger.error_lb('Config LUN0 with total AU and enhanced memory type1')
            logger.error_fp(f'Expect value of dPSAMaxDataSize should be 0 but current value is {self.param.gDevice.l37_psa_max_data_size}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(2, 'Unmap all data')
        for lun in range(self.param.gMaxNumberLU):
            if self.param.gUnit[lun].b3_lu_enable != api.LUNEnable.DISABLE:
                ExecuteCMD.Unmap().assign(lun=lun, lba=0, length=self.param.gUnit[lun].q11_logical_block_count).enqueue()
        ExecuteCMD.send()

        logger.flow(3, 'Set bPSAState as pre_soldering, expect query response will be failure')
        write_attr = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).enqueue()
        response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=write_attr))
        if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set bPSAState as pre_soldering when device is FULL EM1')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{response.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(4, 'Config LUN0 with total AU and normal memory')
        self.config_LUN0_with_total_AU(memory_type=api.MemoryType.NORMAL)
        self.update_unit_desc()
        self.update_device_desc()
        test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
        for lun in range(self.param.gMaxNumberLU):
            if self.param.gUnit[lun].b3_lu_enable != api.LUNEnable.DISABLE:
                test_unit_ready.set_option(lun=lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send()

        logger.flow(5, f'Set inhibition time in hw setting with value {self.setting_inhibition_time} (means {self.setting_inhibition_time} second, it may should multiple of 30)')
        self.set_inhibition_time(expected_inhibition_time_sec=self.setting_inhibition_time)

        logger.flow(6, 'Set bRefreshMethod as 01h: Manual_Force and bRefreshUnit as 00h: Minimum capability')
        api.write_attribute(idn=api.AttributeIDN.REFRESH_METHOD, val=RefreshMethod.ManualForce)
        api.write_attribute(idn=api.AttributeIDN.REFRESH_UNIT, val=RefreshUnit.MinimumRefresh)

        logger.flow(7, f'Set dPSADataSize as dPSAMaxDataSize = {self.param.gDevice.l37_psa_max_data_size}')
        api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=self.param.gDevice.l37_psa_max_data_size)

        logger.flow(8, 'Unmap all data')
        for lun in range(self.param.gMaxNumberLU):
            if self.param.gUnit[lun].b3_lu_enable != api.LUNEnable.DISABLE:
                ExecuteCMD.Unmap().assign(lun=lun, lba=0, length=self.param.gUnit[lun].q11_logical_block_count).enqueue()
        ExecuteCMD.send()

        logger.flow(9, 'Set bPSAState as pre_soldering')
        api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.PRE_SOLDERING)

        logger.flow(10, 'Write 2 SLC VB size data in normal memory LU')
        api.sequential_write(lun=0, start_lba=0, total_size=2 * self.SLC_VB_size, chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 0,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        logger.flow(11, 'Set bPSAState as loading_complete')
        api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.LOADING_COMPLETE)

        logger.flow(12, 'Issue power cycle')
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=True)
        self.inhibit_start_time = time.time()

        logger.flow(13, '1st write')
        api.sequential_write(lun=0, start_lba=2 * self.SLC_VB_size, total_size=api.BLOCK4K_SIZE_4K_BYTE, chunk_size=api.BLOCK4K_SIZE_4K_BYTE, fua = 0,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        logger.flow(14, 'Issue VU 0x405C to get PSA post reflow progress percentage and VU 0x404F to get PSA migration state during inhibition time first 40 seconds')
        self.check_post_reflow_state_during_inhibit_phase(polling_time_sec=40)

        while self.reflow_progress.PercentageForSLCPSAblocks.value != 100:
            self.check_during_inhibition_time_and_inhibit_lock()
            logger.flow(15, 'Set fRefreshEnable to trigger HIR and polling refresh complete')
            start_time = time.time()
            timeout_min = 1
            api.set_flag(idn=api.FlagIDN.REFRESH_EN)
            refresh_status = api.read_attribute(idn = api.AttributeIDN.REFRESH_STATUS)
            while refresh_status != 0x03:
                if (time.time() - start_time) > timeout_min * 60:
                    logger.error(f'Expect refresh status should be 03h(completed successfully) within {timeout_min} min')
                    raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
                time.sleep(2)
                refresh_status = api.read_attribute(idn = api.AttributeIDN.REFRESH_STATUS)
            
            logger.flow(16, 'Issue VU 0x405C to get PSA post reflow progress percentge and VU 0x404F to get PSA migration state, if progress is not 100 after inhibition time, judge testing failure, else go back to flow-14')
            cmd_idx:List[int] = []
            project_api.push_405C_get_PSA_post_reflow_progress(cmd_idx=cmd_idx)
            project_api.push_404F_get_PSA_migration_state(cmd_idx=cmd_idx)
            ExecuteCMD.send(clear_on_success=False)
            rsp = ExecuteCMD.read_response(index=cmd_idx[0])
            self.reflow_progress = project_api.PSAPostReflowProgress(rsp.data)
            rsp = ExecuteCMD.read_response(index=cmd_idx[1])
            self.migration_state = project_api.PSAMigrationState(rsp.data)
            ExecuteCMD.clear()
            logger.info(f'Migration state = {self.migration_state.IsPsaOngoing.value} and reflow progress = {self.reflow_progress.PercentageForSLCPSAblocks.value}')
        
        logger.flow(17, 'Check all PSA VB should be refreshed as POR VB during inhibition time')
        self.check_during_inhibition_time_and_inhibit_lock()
        self.check_vb_mlc_trim(expected_trim = trimtype.POR)
        self.check_during_inhibition_time_and_inhibit_lock()

    def post_process(self) -> None:
        self.VU_clear_PSA_state()
        self.re_config()
        pass


run = Pattern().run
if __name__ == "__main__":
    run()