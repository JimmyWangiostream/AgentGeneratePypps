from copy import deepcopy
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
from Script import project_api
from Script.api.cmd_seq.response import CommandResponse


_sdk = api.shared.sdk

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
                    self.enabledLU.append(LU_number) if LU_number not in self.enabledLU else None
                elif LU_number == 2 or LU_number == 3:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[i].units[unit].l4_num_alloc_units = self.total_au // 4
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD if LU_number == 2 else api.ProvisioningType.THIN_PROVISIONING_ERASE
                    self.non_sensitiveLU.append(LU_number) if LU_number not in self.non_sensitiveLU else None
                    self.non_sensitiveLU_start_lba[LU_number] = 0
                    self.enabledLU.append(LU_number) if LU_number not in self.enabledLU else None
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

    def sendcmd_keeperror(self, cmd_index:int) -> CommandResponse:
        try:
            ExecuteCMD.send(clear_on_success=False)
            response = ExecuteCMD.read_response(cmd_index)
        except DLL_RESPONSE_ERROR:
            response = ExecuteCMD.read_response(cmd_index)
        ExecuteCMD.clear()
        return response

    def set_device_ec(self, set_EC_value: int) -> None:
        total_VB_count = self.fw_geometry.l52_total_vb_count
        value_bytes = set_EC_value.to_bytes(4, byteorder='little', signed=False)
        data = bytearray(b'\xFF' * 0x4000)
        data[:(total_VB_count * 4)] = value_bytes * total_VB_count

        api.ufs_api.vendor_cmd.access_vendor_mode()
        vuc = ExecuteCMD.VendorCmdWrite()
        vuc.assign(length=api.DATA_SIZE_16K_BYTE, cmd_index=api.VendorCmd.GET_FW_GEOMETRY, cmd_set_type=0x0F)
        vuc.upiu.u16_cdb.b2_rsvd = api.VendorCmdRuleCdb2.CMD_IN_CDB
        vuc.upiu.u16_cdb.b6_cmd2 = 4
        vuc.data = data
        vuc.enqueue()
        ExecuteCMD.send()

    def issue_SSU_powerdown_active(self) -> None:        
        SSU = ExecuteCMD.StartStopUnit()
        SSU.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=3, no_flush=0,start=0)
        SSU.set_option(wait_queue_empty=True)
        ExecuteCMD.enqueue(SSU)
        ExecuteCMD.send()
        self.VCC_power_off_power_on()
        SSU.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=1, no_flush=0,start=0)
        ExecuteCMD.enqueue(SSU)
        ExecuteCMD.send()

    def VCC_power_off_power_on(self) -> None:
        logger.info('VCC_power_off_power_on')
        _sdk.power_control(on_off_value=lib.Power_Control.POWER_OFF.value, channel_sel=lib.Power_Channel.POWER_CHANNEL_VCC.value)
        _sdk.power_control(on_off_value=lib.Power_Control.POWER_ON.value, channel_sel=lib.Power_Channel.POWER_CHANNEL_VCC.value)

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

    def get_hwsetting_inhibition_time(self) -> int: 
        self.hw_setting = api.HwSetting.get_instance()
        self.hw_setting.update_from_device()
        value = self.hw_setting.get_local_val(api.HwSettingField.INHIBITION_TIME)
        return value

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
        self.enabledLU:List[int] = []
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
        self.inhibition_time_sec = self.get_hwsetting_inhibition_time()
        self.inhibition_time_min = (self.inhibition_time_sec // 60) if self.inhibition_time_sec % 60 == 0 else (self.inhibition_time_sec // 60) + 1
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
            ExecuteCMD.send()

            # logger.flow(2, 'Set all blocks erase count as 15 (over threshold of generating event log 10)')
            # self.set_device_ec(set_EC_value=15)
            # Skip flow because eventlog does not implement yet

            logger.flow(3, 'Get PSA_SLC_Temperature_low_th and PSA_SLC_Temperature_high_th from mconfig')
            rsp, mconfig = project_api.get_mConfig_data()
            logger.info(f'PSA_SLC_Temperature_low_th = {mconfig.PSA_SLC_Temperature_low_th.value - 80}, PSA_SLC_Temperature_low_th = {mconfig.PSA_SLC_Temperature_high_th.value - 80}')

            # logger.flow(4, 'Set Tnand by VU 0xD08A lower than PSA_SLC_Temperature_low_th')
            # Skip flow because eventlog does not implement yet

            logger.flow(5, 'Set dPSADataSize as 16GB')
            set_dPSADataSize_value = BLOCK4K_SIZE_16G_BYTE
            api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=set_dPSADataSize_value)

            logger.flow(6, 'Unmap PSA sensitive LUN data and set bPSAState as pre_soldering')
            unmap = ExecuteCMD.Unmap()
            for lun in self.sensitiveLU:
                if self.param.gUnit[lun].b3_lu_enable != 0 and self.param.gUnit[lun].q11_logical_block_count != 0:
                    unmap.assign(lun=lun, lba=0, length=self.param.gUnit[lun].q11_logical_block_count)
                    ExecuteCMD.enqueue(unmap)

            ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True, timeout=self.psa_timeout).enqueue()
            ExecuteCMD.send()
            self.sensitiveLU_start_lba = {k: 0 for k in self.sensitiveLU_start_lba}
            self.non_sensitiveLU_start_lba = {k: 0 for k in self.non_sensitiveLU_start_lba}

            # logger.flow(7, 'Check event log should contain "Average PEC of Dynamic pool > 10 PEC"')
            # Skip flow because eventlog does not implement yet

            logger.flow(8, 'Write PSA sensitive LUNs with data size 15GB')
            max_chunk_size = BLOCK4K_SIZE_128M_BYTE
            for lun in self.sensitiveLU:
                datalen = (15 * BLOCK4K_SIZE_1G_BYTE) // len(self.sensitiveLU)
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

            # logger.flow(9, 'Check event log should contain "Write PSA sensitive data when Tnand outside allowed range"') # It does not implement yet
            # Skip flow because eventlog does not implement yet

            logger.flow(10, 'Set dPSADataSize as 8GB')
            set_dPSADataSize_value = BLOCK4K_SIZE_8G_BYTE
            api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=set_dPSADataSize_value)

            logger.flow(11, 'Write PSA sensitive LUNs for condition is dPSADataSize descreased in pre_soldering state')
            write_cmd = ExecuteCMD.Write10().assign(lun=self.sensitiveLU[0], lba=self.sensitiveLU_start_lba[self.sensitiveLU[0]], length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
            response = self.sendcmd_keeperror(cmd_index=write_cmd)
            if response.upiu.b6_response != api.UPIUResponse.TARGET_FAILURE:
                logger.error_lb(f'Write PSA sensitive LUNs for condition is dPSADataSize descreased in pre_soldering state')
                logger.error_fp(f'Device response should be 0x01 failure but current value is 0x{response.upiu.b6_response}')
                raise SIGHTING_RESPONSE_UNEXPECTED

            logger.flow(12, 'Set bPSAState as Loading_Complete, device response should be failure because PSA written data over dPSADataSize')
            write_attr = ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).enqueue()
            response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=write_attr))
            if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
                logger.error_lb(f'Set bPSAState as Loading_Complete for condition is dPSADataSize descreased in pre_soldering state')
                logger.error_fp(f'Device response should be 0xFF failure but current value is 0x{response.upiu.b6_query_response:02X}')
                raise SIGHTING_RESPONSE_UNEXPECTED

            logger.flow(13, 'Set bPSAState as Off to interrupt PSA flow and check FW internal state, bPSAState shoule be off and FW internal state should be interrupt(0x01)')
            ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.OFF).set_option(wait_queue_empty=True, timeout=self.psa_timeout).enqueue()
            ExecuteCMD.send()

            rsp, debug_info = api.get_debug_info()
            logger.info(f'FW internal PSA state is 0x{debug_info.payload[469]}')
            if debug_info.payload[469] != 0x01:
                logger.error_lb(f'Check FW internal state after setting bPSAState as 0x00 to interrupt PSA flow')
                logger.error_fp(f'FW internal state should be interrupt(0x01) but currernt value is 0x{debug_info.payload[469]:02X}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            logger.flow(14, 'Config multi 2 normal memory type LU / 2 EM1 LU and WriteBooster buffer 4GB')
            self.config_precondition()
            self.update_unit_desc()
            self.update_device_desc()
            test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
            for lun in range(self.param.gMaxNumberLU):
                if self.param.gUnit[lun].b3_lu_enable != api.LUNEnable.DISABLE:
                    test_unit_ready.set_option(lun=lun)
                    ExecuteCMD.enqueue(test_unit_ready)        
            ExecuteCMD.send()

            for lun in range(self.param.gMaxNumberLU):
                self.write_record[lun].clear()

            logger.flow(15, 'Set dPSADataSize as dPSAMaxDataSize')
            set_dPSADataSize_value = self.param.gDevice.l37_psa_max_data_size
            api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=set_dPSADataSize_value)

            logger.flow(16, 'Random write for trigger BKOPS')
            start_time = time.time()
            timeout_min = 30
            while True:
                datalen = BLOCK4K_SIZE_10G_BYTE                
                while datalen > 0:
                    lun = random.choice(self.enabledLU)
                    random_chunk_size = random.randint(BLOCK4K_SIZE_4K_BYTE, WRITE_10_MAX_BLOCK_LEN)
                    chunk_size = min(random_chunk_size, datalen)
                    startLBA = random.randint(0, self.param.gLUCapacity[lun] - random_chunk_size)
                    write10 = ExecuteCMD.Write10()
                    write10.assign(lun=lun, lba=startLBA, length=chunk_size, fua=0)
                    write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
                    datalen -= chunk_size
                    ExecuteCMD.enqueue(write10)
                ExecuteCMD.send(clear_on_success=False)
                for cmd in ExecuteCMD._cmd_list:
                    api.save_write_info_by_cmd(cmd=cmd, write_record=self.write_record)
                ExecuteCMD.clear()

                BKOPS_status = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
                logger.info(f'BKOPS status = {BKOPS_status}')
                if BKOPS_status != 0x00:
                    break
                
                if check_timeout(start_time, timeout_min):
                    logger.error(f'Random write for trigger BKOPS {timeout_min}min, but current BKOPS status = {BKOPS_status}')
                    raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT

            logger.flow(17, 'Unmap PSA sensitive LUN data and set bPSAState as pre_soldering')
            unmap = ExecuteCMD.Unmap()
            for lun in self.sensitiveLU:
                if self.param.gUnit[lun].b3_lu_enable != 0 and self.param.gUnit[lun].q11_logical_block_count != 0:
                    unmap.assign(lun=lun, lba=0, length=self.param.gUnit[lun].q11_logical_block_count)
                    ExecuteCMD.enqueue(unmap)

            ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True,timeout=self.psa_timeout).enqueue()
            ExecuteCMD.send()
            self.sensitiveLU_start_lba = {k: 0 for k in self.sensitiveLU_start_lba}
            self.non_sensitiveLU_start_lba = {k: 0 for k in self.non_sensitiveLU_start_lba}

            for lun in self.sensitiveLU:
                self.write_record[lun].clear()

            logger.flow(18, 'Write PSA sensitive LUNs with data size = dPSADataSize / 2')
            max_chunk_size = BLOCK4K_SIZE_128M_BYTE
            data_size = set_dPSADataSize_value >> 1
            for lun in self.sensitiveLU:
                datalen = data_size // len(self.sensitiveLU)
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

            logger.flow(19, 'SSU powerdown with vcc off -> SSU active')
            self.issue_SSU_powerdown_active()

            logger.flow(20, 'Write PSA sensitive LUNs with data size = dPSADataSize / 2')
            max_chunk_size = BLOCK4K_SIZE_128M_BYTE
            data_size = set_dPSADataSize_value >> 1
            for lun in self.sensitiveLU:
                datalen = data_size // len(self.sensitiveLU)
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

            if interrupt_PSA_test == 1:
                logger.flow(21, 'PSA interrupt test has been do, set bPSAState as Loading_complete')
                ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).set_option(wait_queue_empty=True, timeout=self.psa_timeout).enqueue()
                ExecuteCMD.send()
            else:
                logger.flow(21, 'Set bPSAState as Off and issue SSU powerdown -> active and HW reset without SSU powerdown')
                ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.OFF).set_option(wait_queue_empty=True, timeout=self.psa_timeout).enqueue()
                ExecuteCMD.send()
                self.issue_SSU_powerdown_active()
                api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=False)

        logger.flow(22, 'SSU powerdown with vcc off -> SSU active')
        self.issue_SSU_powerdown_active()

        logger.flow(23, 'Read bPSAState value should be Loading_Complete and FW internal state should not be post_reflow(0x02)')
        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        if read_attr_value != api.PSAState.LOADING_COMPLETE:
            logger.error_lb('Check bPSAState after SSU powerdown -> active in Loading_Complete state')
            logger.error_fp(f'bPSAState should keep Loading_Complete state but current value is 0x{read_attr_value}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        
        rsp, debug_info = api.get_debug_info()
        logger.info(f'FW internal PSA state is 0x{debug_info.payload[469]}')
        if debug_info.payload[469] == 0x02:
            logger.error_lb(f'Check FW internal state after SSU powerdown -> active in loading_complete state')
            logger.error_fp(f'FW internal state should not be post_reflow(0x02) but currernt value is 0x{debug_info.payload[469]:02X}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(24, 'Issue power cycle')
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=True)
        
        logger.flow(25, 'SSU powerdown with vcc off -> SSU active')
        self.issue_SSU_powerdown_active()

        logger.flow(26, 'Read bPSAState value should be Loading_Complete')
        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        if read_attr_value != api.PSAState.LOADING_COMPLETE:
            logger.error_lb('Check bPSAState after SSU powerdown -> active in Loading_Complete state')
            logger.error_fp(f'bPSAState should keep Loading_Complete state but current value is 0x{read_attr_value}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        logger.flow(27, '1st write')
        write_cmd = ExecuteCMD.Write10().assign(lun=self.sensitiveLU[0], lba=self.sensitiveLU_start_lba[self.sensitiveLU[0]], length=BLOCK4K_SIZE_16M_BYTE,fua=0).set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX).enqueue()
        ExecuteCMD.send(clear_on_success=False)
        for cmd in ExecuteCMD._cmd_list:
            api.save_write_info_by_cmd(cmd, write_record=self.write_record)
        ExecuteCMD.clear()

        logger.flow(28, 'Read bPSAState value should be soldered and FW internal state should be post_reflow(0x02)')
        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        if read_attr_value != api.PSAState.SOLDERED:
            logger.error_lb('Check bPSAState after 1st write')
            logger.error_fp(f'bPSAState should change in soldered state but current value is 0x{read_attr_value}')
            raise SIGHTING_RESPONSE_UNEXPECTED    

        rsp, debug_info = api.get_debug_info()
        logger.info(f'FW internal PSA state is 0x{debug_info.payload[469]}')
        if debug_info.payload[469] != 0x02:
            logger.error_lb(f'Check FW internal state when bPSAState change in soldered')
            logger.error_fp(f'FW internal state should be post_reflow(0x02) but currernt value is 0x{debug_info.payload[469]:02X}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(29, 'Issue VU 0x405C to PSA Post Reflow progress and VU 0x404F to get PSA migration state, Post reflow progress should be 100 percent and migration state should be 0')
        start_time = time.time()
        timeout_min = 15 + self.inhibition_time_min
        SSU_case_test_done = False
        rand_write_case_test_done = False
        before_loop_progress = 0
        while True:
            time.sleep(2)
            VU_idx:List[int] = []
            project_api.push_405C_get_PSA_post_reflow_progress(cmd_idx=VU_idx)
            ExecuteCMD.send(clear_on_success=False)
            rsp = ExecuteCMD.read_response(index=VU_idx[0])
            reflow_progress = project_api.PSAPostReflowProgress(rsp.data)
            ExecuteCMD.clear()

            logger.info(f'Reflow progress = {reflow_progress.PercentageForSLCPSAblocks.value}')
            if reflow_progress.PercentageForSLCPSAblocks.value == 100:
                break
            elif reflow_progress.PercentageForSLCPSAblocks.value >= 30 and SSU_case_test_done == False:
                self.issue_SSU_powerdown_active()
                SSU_case_test_done = True
            elif reflow_progress.PercentageForSLCPSAblocks.value >= 60 and rand_write_case_test_done == False:
                datalen = BLOCK4K_SIZE_2G_BYTE                
                while datalen > 0:
                    lun = random.choice(self.enabledLU)
                    random_chunk_size = random.randint(BLOCK4K_SIZE_4K_BYTE, BLOCK4K_SIZE_32M_BYTE)
                    chunk_size = min(random_chunk_size, datalen)
                    startLBA = random.randint(0, self.param.gLUCapacity[lun] - random_chunk_size)
                    write10 = ExecuteCMD.Write10()
                    write10.assign(lun=lun, lba=startLBA, length=chunk_size, fua=0)
                    write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout= 30 * 1000 * 1000)
                    datalen -= chunk_size
                    ExecuteCMD.enqueue(write10)
                ExecuteCMD.send(clear_on_success=False)
                for cmd in ExecuteCMD._cmd_list:
                    api.save_write_info_by_cmd(cmd=cmd, write_record=self.write_record)
                ExecuteCMD.clear()
                rand_write_case_test_done = True

            if before_loop_progress > reflow_progress.PercentageForSLCPSAblocks.value:
                logger.error(f'Before loop progress = {before_loop_progress}, current loop progress = {reflow_progress.ZeroConstant.value}, it should not decrease during data relocation')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                before_loop_progress = reflow_progress.PercentageForSLCPSAblocks.value

            if check_timeout(start_time, timeout_min):
                logger.error(f'Expect reflow progress = 100 percent within {timeout_min}min, but current value: Reflow progress = {reflow_progress.PercentageForSLCPSAblocks.value}')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT

        logger.flow(30, 'Read bPSAState value should be soldered and FW internal state should be relocate_complete(0x03) after reflow progress 100 percent')
        read_attr_value = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
        logger.info(f'bPSAState is 0x{read_attr_value:02X}')
        if read_attr_value != api.PSAState.SOLDERED:
            logger.error_lb('Check bPSAState after 1st write')
            logger.error_fp(f'bPSAState should change in soldered state but current value is 0x{read_attr_value}')
            raise SIGHTING_RESPONSE_UNEXPECTED    

        rsp, debug_info = api.get_debug_info()
        logger.info(f'FW internal PSA state is 0x{debug_info.payload[469]}')
        if debug_info.payload[469] != 0x03:
            logger.error_lb(f'Check FW internal state when bPSAState change in soldered')
            logger.error_fp(f'FW internal state should be relocate_complete(0x03) but currernt value is 0x{debug_info.payload[469]:02X}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(31, 'Compare all data should pass')
        api.read_compare(write_record=self.write_record)


    def post_process(self) -> None:
        self.VU_clear_PSA_state()
        self.re_config()
        pass


run = Pattern().run
if __name__ == "__main__":
    run()