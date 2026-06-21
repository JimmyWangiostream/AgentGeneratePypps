from copy import deepcopy
from enum import IntEnum
import random
import time
import package_root
from Script import api
from typing import List, cast
from Script.api.cmd_seq.response import CommandResponse
from Script.api.exception import *
from Script.api.ufs_api.defines.bit_define import CHK_BIT
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api import cmd_seq as ExecuteCMD
from Script.api.ufs_api import vendor_cmd
from Script.lib.sdk_lib.user.exception import DLL_RESPONSE_ERROR
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.api.ufs_api.rpmb.rpmb import RPMB

_sdk = api.shared.sdk
class trimtype(IntEnum):
    POR = 0
    PSA = 1
    SLx = 2

class RefreshMethod(IntEnum):
    ManualForce = 1
    ManualSelective = 2

class RefreshUnit(IntEnum):
    MinimumRefresh = 0
    OneHundredPercent = 1

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
                elif LU_number == 2 or LU_number == 3:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[i].units[unit].l4_num_alloc_units = self.total_au // 4
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD if LU_number == 2 else api.ProvisioningType.THIN_PROVISIONING_ERASE
                else:
                    config_descs[i].units[unit].b0_lu_enable = 0
                    config_descs[i].units[unit].l4_num_alloc_units = 0
            if i == 3:
                config_descs[i].header.b2_conf_desc_continue = 0
            else:
                config_descs[i].header.b2_conf_desc_continue = 1
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

    def sendcmd_keeperror(self, cmd_index:int) -> CommandResponse:
        try:
            ExecuteCMD.send(clear_on_success=False)
            response = ExecuteCMD.read_response(cmd_index)
        except DLL_RESPONSE_ERROR:
            response = ExecuteCMD.read_response(cmd_index)
        ExecuteCMD.clear()
        return response
    
    def write_non_sensitive_LU(self) -> None:        
        write10 = ExecuteCMD.Write10()
        write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX)
        for lun in self.non_sensitiveLU:
            write10.assign(lun=lun, lba=self.non_sensitiveLU_write_start_lba, length=api.BLOCK4K_SIZE_64M_BYTE, fua=0)
            ExecuteCMD.enqueue(write10)

        ExecuteCMD.send(clear_on_success=False)
        for cmd in ExecuteCMD._cmd_list:
            api.save_write_info_by_cmd(cmd, write_record=self.write_record)

        ExecuteCMD.clear()
        self.non_sensitiveLU_write_start_lba += api.BLOCK4K_SIZE_64M_BYTE

    def RPMB_write_data(self) -> None:
        vendor_cmd.access_vendor_mode()
        vendor_cmd.vuc_clear_rpmb_key(api.RPMBRegion.REGION_0)
        rpmb = RPMB(api.RPMBRegion.REGION_0)
        try:
            write_counter = rpmb.rpmb_read_counter()
        except SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
            logger.info("Flow = RPMB key is cleared")
            rpmb.rpmb_key_programming()
        rpmb.rpmb_write_data(start_lba=0, data_len=4)

    def Set_bPSAState_when_soldered_test(self) -> None:
        test_state:List[api.PSAState] = [api.PSAState.OFF, api.PSAState.PRE_SOLDERING, api.PSAState.LOADING_COMPLETE, api.PSAState.SOLDERED, cast(api.PSAState, 0xFF)]
        for state in test_state:
            logger.info(f'Write bPSA state as 0x{state:02X}')
            write_attr = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(state).enqueue()
            response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=write_attr))
            if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
                logger.error_lb(f'Set bPSAState with value = {state} in soldered state')
                logger.error_fp(f'Expect the response should be 0xFF general failure, but current value is 0x{response.upiu.b6_query_response:02X}')
                raise SIGHTING_RESPONSE_UNEXPECTED
            
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
        self.non_sensitiveLU_write_start_lba = 0
        self.fw_geometry = api.get_fw_geometry()
        self.SLC_VB_size = self.fw_geometry.l84_vb_size_u0 >> 3 # menas (var * 512 / 4096) to change unit from sector to blocks
        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        self.psa_timeout = pow(2, self.param.gDevice.b41_psa_state_timeout) * 100
        logger.info(f'PSA timeout is {self.psa_timeout}')
        self.support_refresh = bool(CHK_BIT(self.param.gDevice.l79_extended_ufs_features_support, 3))
        if  self.support_refresh:
            logger.info('Set refresh method as manual force and refresh unit as 100 percent before starting PSA flow')
            api.write_attribute(idn=api.AttributeIDN.REFRESH_METHOD, val=RefreshMethod.ManualForce)
            api.write_attribute(idn=api.AttributeIDN.REFRESH_UNIT, val=RefreshUnit.OneHundredPercent)

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

        logger.flow(2, 'Check unit descriptor bPSASensitive should be 01h only with normal memory LU')
        self.sensitiveLU:List[int] = []
        self.non_sensitiveLU:List[int] = []
        self.sensitiveLU_start_lba:dict[int, int] = {}
        for lun in range(self.param.gMaxNumberLU):
            unit_desc = self.param.gUnit[lun]
            if unit_desc.b3_lu_enable != api.LUNEnable.DISABLE:
                logger.info(f'Enabled LUN{lun} memory type = 0x{unit_desc.b8_memory_type:02X}, PSAsensitive = 0x{unit_desc.b7_psa_sensitive:02X}')
                if unit_desc.b7_psa_sensitive == 1:
                    self.sensitiveLU.append(lun)
                    self.sensitiveLU_start_lba[lun] = 0
                elif unit_desc.b7_psa_sensitive == 0:
                    self.non_sensitiveLU.append(lun)
                if (unit_desc.b7_psa_sensitive == 1 and unit_desc.b8_memory_type == api.MemoryType.ENHANCED_1) or (unit_desc.b7_psa_sensitive == 0 and unit_desc.b8_memory_type == api.MemoryType.NORMAL):
                    logger.error_lb(f'Check unit descriptor bPSASensitive')
                    logger.error_fp(f'bPSASensitive should be 1 with normal memory LU and only with normal memory LU')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(3, 'Write data in LUNs PSA sensitive to fill LU capacity')
        max_chunk_size = BLOCK4K_SIZE_128M_BYTE
        for lun in self.sensitiveLU:
            datalen = self.param.gLUCapacity[lun]
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

        logger.flow(4, 'Set dPSADataSize as dPSAMaxDataSize + 1 and device response should be failure')
        set_dPSADataSize_value = self.param.gDevice.l37_psa_max_data_size + 1
        logger.info(f'Value of dPSAMaxDataSize is {self.param.gDevice.l37_psa_max_data_size} and set value as {set_dPSADataSize_value}')
        write_attr = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_DATA_SIZE, index=0, selector=0).set_attr(set_dPSADataSize_value).enqueue()
        response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=write_attr))
        if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set dPSADataSize as dPSAMaxDataSize + 1')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{response.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(5, f'Set dPSADataSize as dPSAMaxDataSize value {self.param.gDevice.l37_psa_max_data_size}')
        api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=self.param.gDevice.l37_psa_max_data_size)

        logger.flow(6, 'Set bPSAState as Loading_Complete and device response should be failure when bPSAState is not pre_soldering')
        write_attr = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).enqueue()
        response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=write_attr))
        if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set bPSAState as Loading_Complete when bPSAState is not pre_soldering')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{response.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(7, 'Set bPSAState as pre_soldering and device response should be failure cause by data are not unmapped yet')
        write_attr = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).enqueue()
        response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=write_attr))
        if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set bPSAState as pre_soldering when device data are not unmapped yet')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{response.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(8, 'Set dPSADataSize as 16GB')
        set_dPSADataSize_value = BLOCK4K_SIZE_16G_BYTE
        api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=api.BLOCK4K_SIZE_16G_BYTE)

        logger.flow(9, 'Write data in EM1 LUNs successfully completed in PSA flow')
        self.write_non_sensitive_LU()
         
        logger.flow(10, 'Send command sequence contain unmapping PSA sensitive LUNs and setting bPSAState as pre_soldering')
        unmap = ExecuteCMD.Unmap()
        for lun in self.sensitiveLU:
            unmap.assign(lun=lun, lba=0, length=self.param.gUnit[lun].q11_logical_block_count)
            ExecuteCMD.enqueue(unmap)

        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True,timeout=self.psa_timeout).enqueue()
        ExecuteCMD.send()
        self.sensitiveLU_start_lba.clear()
        for lun in self.sensitiveLU:
            self.sensitiveLU_start_lba[lun] = 0
            self.write_record[lun].clear()

        logger.flow(11, 'Write data in EM1 LUNs successfully completed in PSA flow')
        self.write_non_sensitive_LU()

        logger.flow(12, 'Set bPSAState as pre_soldering again, the response should be failure')
        write_attr = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).enqueue()
        response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=write_attr))
        if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set bPSAState as pre_soldering when pre_soldering state already set')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{response.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        
        logger.flow(13, 'Enable WriteBooster buffer')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
        logger.info(f'Available WB size is 0x{ava_WB_size:02X}')

        logger.flow(14, 'Write PSA sensitive LUNs with data size 8GB')
        max_chunk_size = BLOCK4K_SIZE_128M_BYTE
        for lun in self.sensitiveLU:
            datalen = BLOCK4K_SIZE_4G_BYTE
            while datalen > 0:
                chunk_size = min(max_chunk_size, datalen)
                write10 = ExecuteCMD.Write10()
                write10.assign(lun=lun, lba=self.sensitiveLU_start_lba[lun], length=chunk_size, fua=1)
                write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
                datalen -= chunk_size
                self.sensitiveLU_start_lba[lun] += chunk_size
                ExecuteCMD.enqueue(write10)

            ExecuteCMD.send(clear_on_success=False)
            for cmd in ExecuteCMD._cmd_list:
                api.save_write_info_by_cmd(cmd, write_record=self.write_record)

            ExecuteCMD.clear()

        logger.flow(15, 'Check available WB size should keep 0xA')
        ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
        logger.info(f'Available WB size is 0x{ava_WB_size:02X}')

        if ava_WB_size != 0xA:
            logger.error_lb('Check available WB size after write PSA sensitive LUNs in pre_soldering stage')
            logger.error_fp(f'The value of available WB size should keep 0xA but current value is 0x{ava_WB_size:02X}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

        logger.flow(16, 'Write PSA sensitive LUNs with data size for filling Max PSA SLC VB allocable') # over dPSADataSize and smaller than Max PSA SLC VB allocable size
        PSA_SLC_VB_allocable = (set_dPSADataSize_value // self.SLC_VB_size) + 1 if set_dPSADataSize_value % self.SLC_VB_size == 0 else (set_dPSADataSize_value // self.SLC_VB_size) + 2
        PSA_data_limit = PSA_SLC_VB_allocable * self.SLC_VB_size
        logger.info(f'dPSADataSize = {set_dPSADataSize_value}, SLC VB size = {self.SLC_VB_size}, expected PSA VB allocable = {PSA_SLC_VB_allocable}, data length limit = {PSA_data_limit}')

        max_chunk_size = BLOCK4K_SIZE_128M_BYTE
        for lun in self.sensitiveLU:
            datalen = (PSA_data_limit >> 1) - self.sensitiveLU_start_lba[lun]
            while datalen > 0:
                chunk_size = min(max_chunk_size, datalen)
                write10 = ExecuteCMD.Write10()
                write10.assign(lun=lun, lba=self.sensitiveLU_start_lba[lun], length=chunk_size, fua=1)
                write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
                datalen -= chunk_size
                self.sensitiveLU_start_lba[lun] += chunk_size
                ExecuteCMD.enqueue(write10)

            ExecuteCMD.send(clear_on_success=False)
            for cmd in ExecuteCMD._cmd_list:
                api.save_write_info_by_cmd(cmd, write_record=self.write_record)

            ExecuteCMD.clear()

        logger.flow(17, 'Set bPSAState as Loading_Complete and device response should be failure because PSA written data size is over dPSADataSize')
        write_attr = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).enqueue()
        response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=write_attr))
        if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set bPSAState as Loading_Complete with PSA written data size is over dPSADataSize')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{response.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(18, 'Write PSA sensitive LUNs with data size for overing Max PSA SLC VB allocable')
        write_cmd = ExecuteCMD.Write10().assign(lun=self.sensitiveLU[0], lba=self.sensitiveLU_start_lba[self.sensitiveLU[0]], length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        response = self.sendcmd_keeperror(cmd_index=write_cmd)
        if response.upiu.b6_response != api.UPIUResponse.TARGET_FAILURE:
            logger.error_lb(f'Write PSA sensitive LUNs with data size for overing Max PSA SLC VB allocable')
            logger.error_fp(f'Device response should be 0x01 failure but current value is 0x{response.upiu.b6_response}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(19, 'Set dPSADataSize as dPSAMaxDataSize')
        set_dPSADataSize_value = self.param.gDevice.l37_psa_max_data_size
        api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=set_dPSADataSize_value)

        logger.flow(20, 'Write PSA sensitive LUNs with data size for filling NEW dPSADataSize with random chunk size between 4K and Write10 max size')
        for lun in self.sensitiveLU:
            datalen = (set_dPSADataSize_value >> 1) - self.sensitiveLU_start_lba[lun]
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

        self.check_vb_mlc_trim(expected_trim = trimtype.PSA)

        logger.flow(21, 'Write more PSA data to over dPSADataSize when dPSADataSize set as dPSAMaxDataSize')
        write_cmd = ExecuteCMD.Write10().assign(lun=self.sensitiveLU[0], lba=self.sensitiveLU_start_lba[self.sensitiveLU[0]], length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        response = self.sendcmd_keeperror(cmd_index=write_cmd)
        if response.upiu.b6_response != api.UPIUResponse.TARGET_FAILURE:            
            logger.error_lb(f'Write more PSA data to over dPSADataSize when dPSADataSize set as dPSAMaxDataSize')
            logger.error_fp(f'Device response should be 0x01 failure but current value is 0x{response.upiu.b6_response}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(22, 'Set bPSAState as Loading_Complete')
        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).set_option(timeout=self.psa_timeout).enqueue()
        ExecuteCMD.send()

        logger.flow(23, 'Compare all data should pass')
        api.read_compare(write_record=self.write_record)

        logger.flow(24, 'Set bPSAState as Loading_Complete again and device response should be failure')
        write_attr = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).enqueue()
        response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=write_attr))
        if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set bPSAState as Loading_Complete when Loading_Complete state already set')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{response.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(25, 'Set bPSAState as pre_soldering and device response should be failure when state is not off')
        write_attr = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).enqueue()
        response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=write_attr))
        if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set bPSAState as pre_soldering when state is not off')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{response.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(26, 'Write data in EM1 LUNs successfully completed in PSA flow')
        self.write_non_sensitive_LU()

        logger.flow(27, 'Issue power cycle')
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=True)

        logger.flow(28, 'Check bPSAState should be Loading_Complete and FW internal state should be Post_reflow(0x02)')
        rsp, debug_info = vendor_cmd.get_debug_info()
        logger.info(f'FW internal PSA state is 0x{debug_info.payload[469]}')
        if debug_info.payload[469] != 0x02:
            logger.error_lb(f'Check FW internal state after power cycle at loading complete state')
            logger.error_fp(f'FW internal state should be Post_reflow(0x02) but currernt value is 0x{debug_info.payload[469]:02X}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        if read_attr_value != api.PSAState.LOADING_COMPLETE:
            logger.error_lb('Check bPSAState after power cycle in Loading_Complete state')
            logger.error_fp(f'bPSAState should keep Loading_Complete state but current value is 0x{read_attr_value}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(29, 'Issue RPMB write and check bPSAState')
        self.RPMB_write_data()

        logger.flow(30, 'Set bPSAState as pre_soldering and device response should be failure when state is not off')
        write_attr = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).enqueue()
        response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=write_attr))
        if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set bPSAState as pre_soldering when state is not off')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{response.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        
        logger.flow(31, 'Set bPSAState as Loading_Complete and device response should be failure when state is not pre_soldering')
        write_attr = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).enqueue()
        response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=write_attr))
        if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set bPSAState as Loading_Complete when bPSAState is not pre_soldering')
            logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{response.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(32, '1st write with LBA out of range and check bPSAState should keep Loading_Complete')
        write_cmd = ExecuteCMD.Write10().assign(lun=self.sensitiveLU[0], lba=self.param.gUnit[self.sensitiveLU[0]].q11_logical_block_count, length=BLOCK4K_SIZE_4K_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        response = self.sendcmd_keeperror(cmd_index=write_cmd)
        if response.upiu.b6_response != api.UPIUResponse.TARGET_FAILURE:
            raise SIGHTING_RESPONSE_UNEXPECTED

        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        if read_attr_value != api.PSAState.LOADING_COMPLETE:
            logger.error_lb('Check bPSAState after 1st write with out of range condition in Loading_Complete state')
            logger.error_fp(f'bPSAState should keep Loading_Complete state but current value is 0x{read_attr_value}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(33, '1st write with valid LBA/length and check bPSAState should be soldered')
        write_cmd = ExecuteCMD.Write10().assign(lun=self.sensitiveLU[0], lba=self.sensitiveLU_start_lba[self.sensitiveLU[0]], length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        ExecuteCMD.send(clear_on_success=False)
        for cmd in ExecuteCMD._cmd_list:
            api.save_write_info_by_cmd(cmd, write_record=self.write_record)
        ExecuteCMD.clear()

        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        if read_attr_value != api.PSAState.SOLDERED:
            logger.error_lb('Check bPSAState after 1st write')
            logger.error_fp(f'bPSAState should change in soldered state but current value is 0x{read_attr_value}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        
        if self.support_refresh:
            logger.info('Insert HIR(trigger refresh) event')
            ExecuteCMD.SetFlag().assign(idn=api.FlagIDN.REFRESH_EN, index=0, selector=0).enqueue()
            ExecuteCMD.send()
            start_time = time.time()
            timeout_min = 60
            refresh_status = api.read_attribute(idn = api.AttributeIDN.REFRESH_STATUS)
            while refresh_status != 0x03:
                if check_timeout(start_time, timeout_min):
                    logger.error(f'Expect refresh status should be 03h within {timeout_min} min')
                    raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
                time.sleep(2)
                refresh_status = api.read_attribute(idn = api.AttributeIDN.REFRESH_STATUS)
            self.check_vb_mlc_trim(expected_trim = trimtype.POR)

        logger.flow(34, 'Set bPSAState as off/pre_soldering/loading_complete when bPSAState is soldered, device response should be failure')
        self.Set_bPSAState_when_soldered_test()

        logger.flow(35, 'HW RESET')
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=True)

        logger.flow(36, 'Compare all data should pass')
        api.read_compare(write_record=self.write_record)

        logger.flow(37, 'Check bPSAState should keep soldered')
        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        if read_attr_value != api.PSAState.SOLDERED:
            logger.error_lb('Check bPSAState after 1st write')
            logger.error_fp(f'bPSAState should change in soldered state but current value is 0x{read_attr_value}')
            raise SIGHTING_RESPONSE_UNEXPECTED        

        logger.flow(38, 'Set bPSAState as off/pre_soldering/loading_complete when bPSAState is soldered, device response should be failure')
        self.Set_bPSAState_when_soldered_test()
        pass

    def post_process(self) -> None:
        self.VU_clear_PSA_state()
        self.re_config()
        pass


run = Pattern().run
if __name__ == "__main__":
    run()