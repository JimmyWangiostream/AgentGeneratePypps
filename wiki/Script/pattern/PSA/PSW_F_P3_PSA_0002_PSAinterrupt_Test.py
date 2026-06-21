from copy import deepcopy
from enum import IntEnum
import random
import time
from typing import List, cast

import package_root
from Script import api
from Script.api.ufs_api.defines.bit_define import CHK_BIT
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.api.exception import *
from Script.lib.sdk_lib.user.exception import DLL_RESPONSE_ERROR
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.api.ufs_api.defines.constant_define import *
from Script.project_api.PSA.functions import *
from Script.api.cmd_seq.response import CommandResponse


_sdk = api.shared.sdk

class RefreshMethod(IntEnum):
    ManualForce = 1
    ManualSelective = 2

class RefreshUnit(IntEnum):
    MinimumRefresh = 0
    OneHundredPercent = 1

def check_timeout(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False

class Pattern(UFSTC):
    def config_precondition(self) -> None:
        config_descs = api.get_config_descriptors(print=True)
        self.backup_setting = deepcopy(config_descs)
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

    def sendcmd_keeperror(self, cmd_index:int) -> CommandResponse:
        try:
            ExecuteCMD.send(clear_on_success=False)
            response = ExecuteCMD.read_response(cmd_index)
        except DLL_RESPONSE_ERROR:
            response = ExecuteCMD.read_response(cmd_index)
        ExecuteCMD.clear()
        return response

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

    def HIR_when_PSA_flow_error_test(self, PSAstep:str) -> None:
        set_flag = ExecuteCMD.SetFlag().assign(idn=api.FlagIDN.REFRESH_EN, index=0, selector=0).enqueue()
        HIR_rsp = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=set_flag))
        if HIR_rsp.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Enable HIR when bPSAState is {PSAstep}')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{HIR_rsp.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        set_method = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.REFRESH_METHOD).set_attr(value=RefreshMethod.ManualForce).enqueue()
        HIR_rsp = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=set_method))
        if HIR_rsp.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set refresh method when bPSAState is {PSAstep}')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{HIR_rsp.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        set_unit = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.REFRESH_UNIT).set_attr(value=RefreshUnit.OneHundredPercent).enqueue()
        HIR_rsp = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=set_unit))
        if HIR_rsp.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set refresh method when bPSAState is {PSAstep}')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{HIR_rsp.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED

    def HID_when_PSA_flow_error_test(self, PSAstep:str) -> None:
        api.write_attribute(idn=api.AttributeIDN.DEFRAG_OPERATION, val=0x02)
        start_time = time.time()
        timeout_min = 1
        while True:
            if check_timeout(start_time, timeout_min):
                break
            read_attr_value = api.read_attribute(idn=api.AttributeIDN.HID_STATE)
            logger.info(f'bHIDState is 0x{read_attr_value:02X}')
            if read_attr_value != 0x03:
                logger.error_lb(f'Check bHIDState after trigger HID when bPSAState is {PSAstep}')
                logger.error_fp(f'bHIDState should keep 03h:in progress state within 1 min, but current value is 0x{read_attr_value}')
                raise SIGHTING_RESPONSE_UNEXPECTED

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
        self.sensitiveLU:List[int] = []
        self.non_sensitiveLU:List[int] = []
        self.sensitiveLU_start_lba:dict[int, int] = {}
        self.non_sensitiveLU_start_lba:dict[int, int] = {}
        self.support_refresh = bool(CHK_BIT(self.param.gDevice.l79_extended_ufs_features_support, 3))
        self.support_HID = bool(CHK_BIT(self.param.gDevice.l79_extended_ufs_features_support, 13))
        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        self.psa_timeout = pow(2, self.param.gDevice.b41_psa_state_timeout) * 100
        logger.info(f'PSA timeout is {self.psa_timeout}')

    def step1(self) -> None:
        logger.flow(1, 'Config multi 2 normal memory type LU / 2 EM1 LU and WriteBooster buffer 4GB')
        self.config_precondition()
        self.update_unit_desc()
        self.update_device_desc()
        test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
        for lun in range(self.param.gMaxNumberLU):
            if self.param.gUnit[lun].b3_lu_enable != api.LUNEnable.DISABLE:
                test_unit_ready.set_option(lun=lun)
                ExecuteCMD.enqueue(test_unit_ready)        
        ExecuteCMD.send()

        if self.support_refresh:
            logger.flow(2,'Set refresh method as manual force and refresh unit as 100 percent before starting PSA flow')
            api.write_attribute(idn=api.AttributeIDN.REFRESH_METHOD, val=RefreshMethod.ManualForce)
            api.write_attribute(idn=api.AttributeIDN.REFRESH_UNIT, val=RefreshUnit.OneHundredPercent)

        logger.flow(3, 'Set dPSADataSize as dPSAMaxDataSize')
        set_dPSADataSize_value = self.param.gDevice.l37_psa_max_data_size
        api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=set_dPSADataSize_value)

        logger.flow(4, 'Unmap all data and set bPSAState as pre_soldering')
        unmap = ExecuteCMD.Unmap()
        for lun in range(self.param.gMaxNumberLU):
            if self.param.gUnit[lun].b3_lu_enable != 0 and self.param.gUnit[lun].q11_logical_block_count != 0:
                unmap.assign(lun=lun, lba=0, length=self.param.gUnit[lun].q11_logical_block_count)
                ExecuteCMD.enqueue(unmap)

        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True, timeout=self.psa_timeout).enqueue()
        ExecuteCMD.send()
        self.sensitiveLU_start_lba = {k: 0 for k in self.sensitiveLU_start_lba}
        self.non_sensitiveLU_start_lba = {k: 0 for k in self.non_sensitiveLU_start_lba}

        logger.flow(5, 'Write PSA sensitive LUNs with data size = dPSADataSize / 2')
        max_chunk_size = BLOCK4K_SIZE_128M_BYTE
        for lun in self.sensitiveLU:
            datalen = set_dPSADataSize_value >> 2
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
                api.save_write_info_by_cmd(cmd=cmd, write_record=self.write_record)

            ExecuteCMD.clear()

        logger.flow(6, 'Issue HIR when bPSAState is pre_soldering and device response should be failure, issue HID and response should be success but HID does not perform')
        if self.support_refresh:
            self.HIR_when_PSA_flow_error_test(PSAstep='Pre_soldering')
        if self.support_HID:
            self.HID_when_PSA_flow_error_test(PSAstep='Pre_soldering')

        logger.flow(7, 'Issue HW reset wihtout SSU powerdown(SPOR case)')
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=False)

        logger.flow(8, 'Set bPSAState as Loading_Complete, device response should be failure because PowerCycle occur when pre_soldering state')
        write_attr = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).enqueue()
        response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=write_attr))
        if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set bPSAState as Loading_Complete with situation that PowerCycle occur when pre_soldering state')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{response.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(9, 'Set bPSAState as Off to interrupt PSA flow and check FW internal state, bPSAState shoule be off and FW internal state should be interrupt(0x01)')
        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.OFF).set_option(wait_queue_empty=True, timeout=self.psa_timeout).enqueue()
        ExecuteCMD.send()

        rsp, debug_info = api.get_debug_info()
        logger.info(f'FW internal PSA state is 0x{debug_info.payload[469]}')
        if debug_info.payload[469] != 0x01:
            logger.error_lb(f'Check FW internal state after setting bPSAState as 0x00 to interrupt PSA flow')
            logger.error_fp(f'FW internal state should be interrupt(0x01) but currernt value is 0x{debug_info.payload[469]:02X}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(10, 'Write PSA data when off(interrupt) state, device response should be failure, device response of write command should be failure')
        write_cmd = ExecuteCMD.Write10().assign(lun=self.sensitiveLU[0], lba=self.sensitiveLU_start_lba[self.sensitiveLU[0]], length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        response = self.sendcmd_keeperror(cmd_index=write_cmd)
        if response.upiu.b6_response != api.UPIUResponse.TARGET_FAILURE:
            logger.error_lb(f'Write PSA data when loading complete state')
            logger.error_fp(f'Device response should be 0x01 failure but current value is 0x{response.upiu.b6_response}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        
        logger.flow(11, 'Issue HIR when bPSAState is interrupted and device response should be failure, issue HID and response should be success but HID does not perform')
        if self.support_refresh:
            self.HIR_when_PSA_flow_error_test(PSAstep='interrupted')
        if self.support_HID:
            self.HID_when_PSA_flow_error_test(PSAstep='interrupted')

        logger.flow(12, 'Unmap all data and set bPSAState as pre_soldering')
        for lun in range(self.param.gMaxNumberLU):
            if self.param.gUnit[lun].b3_lu_enable != 0 and self.param.gUnit[lun].q11_logical_block_count != 0:
                unmap.assign(lun=lun, lba=0, length=self.param.gUnit[lun].q11_logical_block_count)
                ExecuteCMD.enqueue(unmap)

        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True,timeout=self.psa_timeout).enqueue()
        ExecuteCMD.send()
        self.sensitiveLU_start_lba = {k: 0 for k in self.sensitiveLU_start_lba}
        self.non_sensitiveLU_start_lba = {k: 0 for k in self.non_sensitiveLU_start_lba}

        logger.flow(13, 'Write PSA sensitive LUNs with data size = dPSADataSize / 2 and set bPSAState as Loading_Complete')
        max_chunk_size = BLOCK4K_SIZE_128M_BYTE
        for lun in self.sensitiveLU:
            datalen = set_dPSADataSize_value >> 2
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
                api.save_write_info_by_cmd(cmd=cmd, write_record=self.write_record)
            ExecuteCMD.clear()

        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).set_option(wait_queue_empty=True, timeout=self.psa_timeout).enqueue()
        ExecuteCMD.send()

        logger.flow(14, 'Issue HIR when bPSAState is Loading_Complete and device response should be failure, issue HID and response should be success but HID does not perform')
        if self.support_refresh:
            self.HIR_when_PSA_flow_error_test(PSAstep='Loading_Complete')            
        if self.support_HID:
            self.HID_when_PSA_flow_error_test(PSAstep='Loading_Complete')


        logger.flow(15, 'Write PSA data when loading complete state, device response should be failure, device response of write command should be failure')
        write_cmd = ExecuteCMD.Write10().assign(lun=self.sensitiveLU[0], lba=self.sensitiveLU_start_lba[self.sensitiveLU[0]], length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        response = self.sendcmd_keeperror(cmd_index=write_cmd)
        if response.upiu.b6_response != api.UPIUResponse.TARGET_FAILURE:
            logger.error_lb(f'Write PSA data when loading complete state')
            logger.error_fp(f'Device response should be 0x01 failure but current value is 0x{response.upiu.b6_response}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        
        logger.flow(16, 'Set bPSAState as Off to interrupt PSA flow and check FW internal state, bPSAState shoule be off and FW internal state should be interrupt(0x01)')
        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.OFF).set_option(wait_queue_empty=True, timeout=self.psa_timeout).enqueue()
        ExecuteCMD.send()

        rsp, debug_info = api.get_debug_info()
        logger.info(f'FW internal PSA state is 0x{debug_info.payload[469]}')
        if debug_info.payload[469] != 0x01:
            logger.error_lb(f'Check FW internal state after setting bPSAState as 0x00 to interrupt PSA flow')
            logger.error_fp(f'FW internal state should be interrupt(0x01) but currernt value is 0x{debug_info.payload[469]:02X}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(17, 'Set dPSADataSize as 0')
        api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=0)

        logger.flow(18, 'Unmap all data and set bPSAState as pre_soldering')
        for lun in range(self.param.gMaxNumberLU):
            if self.param.gUnit[lun].b3_lu_enable != 0 and self.param.gUnit[lun].q11_logical_block_count != 0:
                unmap.assign(lun=lun, lba=0, length=self.param.gUnit[lun].q11_logical_block_count)
                ExecuteCMD.enqueue(unmap)

        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True, timeout=self.psa_timeout).enqueue()
        ExecuteCMD.send()
        self.sensitiveLU_start_lba = {k: 0 for k in self.sensitiveLU_start_lba}
        self.non_sensitiveLU_start_lba = {k: 0 for k in self.non_sensitiveLU_start_lba}

        logger.flow(19, 'Write PSA sensitive LUNs, device response of write command should be failure')
        logger.info('Skip this test flow because atleast 1 PSA SLC VB allocatable')
        # write_cmd = ExecuteCMD.Write10().assign(lun=self.sensitiveLU[0], lba=self.sensitiveLU_start_lba[self.sensitiveLU[0]], length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        # response = self.sendcmd_keeperror(cmd_index=write_cmd)
        # if response.upiu.b6_response != api.UPIUResponse.TARGET_FAILURE:
        #     logger.error_lb(f'Write PSA data dPSADataSize as 0 in pre_soldering state')
        #     logger.error_fp(f'Device response should be 0x01 failure but current value is 0x{response.upiu.b6_response}')
        #     raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(20, 'Set bPSAState as Loading_Complete')
        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).set_option(wait_queue_empty=True, timeout=self.psa_timeout).enqueue()
        ExecuteCMD.send()

        logger.flow(21, 'Issue power cycle')
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=True)

        logger.flow(22, 'Read bPSAState value should be Loading_Complete')
        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        if read_attr_value != api.PSAState.LOADING_COMPLETE:
            logger.error_lb('Check bPSAState after power cycle in Loading_Complete state')
            logger.error_fp(f'bPSAState should keep Loading_Complete state but current value is 0x{read_attr_value}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(23, '1st write')
        write_cmd = ExecuteCMD.Write10().assign(lun=self.sensitiveLU[0], lba=self.sensitiveLU_start_lba[self.sensitiveLU[0]], length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        ExecuteCMD.send(clear_on_success=False)
        for cmd in ExecuteCMD._cmd_list:
            api.save_write_info_by_cmd(cmd, write_record=self.write_record)
        ExecuteCMD.clear()

        logger.flow(24, 'Read bPSAState value should be soldered')
        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        if read_attr_value != api.PSAState.SOLDERED:
            logger.error_lb('Check bPSAState after 1st write')
            logger.error_fp(f'bPSAState should change in soldered state but current value is 0x{read_attr_value}')
            raise SIGHTING_RESPONSE_UNEXPECTED        

        logger.flow(25, 'Issue VU 0x405C to PSA Post Reflow progress and VU 0x404F to get PSA migration state, Post reflow progress should be 0xFFFFFFFF percent and migration state should be 1')
        cmd_idx:List[int] = []
        push_405C_get_PSA_post_reflow_progress(cmd_idx=cmd_idx)
        push_404F_get_PSA_migration_state(cmd_idx=cmd_idx)
        ExecuteCMD.send(clear_on_success=False)
        rsp = ExecuteCMD.read_response(index=cmd_idx[0])
        reflow_progress = PSAPostReflowProgress(rsp.data)
        rsp = ExecuteCMD.read_response(index=cmd_idx[1])
        migration_state = PSAMigrationState(rsp.data)
        ExecuteCMD.clear()
        logger.info(f'Reflow progress = 0x{reflow_progress.PercentageForSLCPSAblocks.value:X}, migration state = {migration_state.IsPsaOngoing.value}, host read trim = {migration_state.HostReadWithPSATrim.value}')
        if reflow_progress.PercentageForSLCPSAblocks.value != 0xFFFFFFFF or migration_state.IsPsaOngoing.value != 0x01:
            logger.error_lb('Issue VU 0x405C to PSA Post Reflow progress and VU 0x404F to get PSA migration state')
            logger.error_fp(f'Post reflow progress should be 100 percent and migration state should be 0 but current value: Reflow progress = 0x{reflow_progress.PercentageForSLCPSAblocks.value:X}, migration state = {migration_state.IsPsaOngoing.value}')
            raise SIGHTING_RESPONSE_UNEXPECTED

    def post_process(self) -> None:
        self.VU_clear_PSA_state()
        self.re_config()
        pass


run = Pattern().run
if __name__ == "__main__":
    run()