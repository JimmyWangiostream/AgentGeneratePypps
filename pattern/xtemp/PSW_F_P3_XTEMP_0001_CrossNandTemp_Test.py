from copy import deepcopy
from enum import IntEnum
import random
import time
from typing import List, Set, cast

import package_root
from Script import api
from Script.api.ufs_api.defines.bit_define import *
from Script.api.ufs_api.fw_value.functions import read_fw_value
from Script.api.util.functions import dumpfile
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.api.exception import *
from Script.lib.sdk_lib.user.exception import DLL_RESPONSE_ERROR
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.api.ufs_api.defines.constant_define import *
from Script import project_api
from Script.api.cmd_seq.response import CommandResponse

TEMP_GAP = 37
BOOKING_IN_MP = BIT9
XTEMP_BOOKING = 20
_sdk = api.shared.sdk

class VB_group_for_list(int):
    LIST_BLK = 0x01
    LIST_INDEX_BLK = 0x02
    TMP_CODE_BLK = 0x03
    CURRENT_PTE = 0x04
    LOG_TAB_BLK = 0x05
    CURRENT_L2_SLC = 0x06
    CURRENT_L2_MLC = 0x07
    CURRENT_DATA_GC_BLK_SLC = 0x09
    CURRENT_DATA_GC_BLK_MLC = 0x0A
    INCOMPLETE_BLK_SLC = 0x0B
    INCOMPLETE_BLK_MLC = 0x0C
    CURRENT_L1 = 0x0D
    PTE_POOL = 0x0E
    USED_BLK_POOL_SLC = 0x10
    USED_BLK_POOL_MLC = 0x11
    CURRENT_L3_SLC = 0x12
    CURRENT_L3_MLC = 0x13
    RAIN_SWAP_NO_OBR_SLC_L2_SLC = 0X15
    RAIN_SWAP_NO_OBR_TLC_L2_SLC = 0X16
    RAIN_SWAP_NO_OBR_TLC_L2_TLC = 0X17
    RAIN_SWAP_NO_OBR_TEMP_BLK = 0X18
    FREE_BLK_QUEUE_SLC = 0X1A
    FREE_BLK_QUEUE_MLC = 0X1B
    FREE_BLK_QUEUE_TABLE = 0X1C

class RiskyType(IntEnum):
    SAFE_GROUP = 0
    COLD_GROUP = 1
    HOT_GROUP = 2
    NA = 3

class Tnandzone(IntEnum):
    SAFE = 0
    COLD = 1
    HOT = 2

class RefreshBehavior(IntEnum):
    NA = 0
    Cold2Safe = 1
    Hot2Safe = 2

def check_timeout(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False

class Pattern(UFSTC):
    def config_precondition(self) -> None:
        config_descs = api.get_config_descriptors(print=True)
        for i in range(4): 
            for unit in range(8):
                LU_number = i * 8 + unit
                if LU_number == 0:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[i].units[unit].l4_num_alloc_units = self.total_au
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                    config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                else:
                    config_descs[i].units[unit].b0_lu_enable = 0
                    config_descs[i].units[unit].l4_num_alloc_units = 0
            config_descs[i].header.b2_conf_desc_continue = 0 if i == 3 else 1
            api.push_write_config(config_descs[i], index=i)
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

    def get_device_ec(self) -> bytearray:
        resp, DebugInfo = api.ufs_api.vendor_cmd.get_debug_info()    
        resp, buffer = api.ufs_api.vendor_cmd.read_Xmemory(sram_address = DebugInfo.VB_list_cycle_address.value)    
        return buffer

    def set_ec(self, set_ec:bytearray) -> None:
        total_VB_count = self.fw_geometry.l52_total_vb_count
        data = bytearray(b'\xFF' * 0x4000)
        del set_ec[total_VB_count*4:]
        data[:len(set_ec)] = set_ec

        api.ufs_api.vendor_cmd.access_vendor_mode()
        vuc = ExecuteCMD.VendorCmdWrite()
        vuc.assign(length=api.DATA_SIZE_16K_BYTE, cmd_index=api.VendorCmd.GET_FW_GEOMETRY, cmd_set_type=0x0F)
        vuc.upiu.u16_cdb.b2_rsvd = api.VendorCmdRuleCdb2.CMD_IN_CDB
        vuc.upiu.u16_cdb.b6_cmd2 = 4
        vuc.data = data
        vuc.enqueue()
        ExecuteCMD.send()

    def set_nand_temp(self, set_temp:int) -> None:
        temp_set = 65536 + set_temp if set_temp < 0 else set_temp
        set_nand_temp = project_api.SetNandTemperature()
        set_nand_temp.bEnableSetVuTemp.value = 1
        set_nand_temp.UC_TERMAL_SENSOR_1.value = temp_set
        set_nand_temp.NAND_TEMPERATURE_DIE_0.value = temp_set
        if self.flash_setting.Max_Fdevice >= 2:
            set_nand_temp.NAND_TEMPERATURE_DIE_1.value = temp_set
        if self.flash_setting.Max_Fdevice >= 4:
            set_nand_temp.NAND_TEMPERATURE_DIE_2.value = temp_set
            set_nand_temp.NAND_TEMPERATURE_DIE_3.value = temp_set
        set_nand_temp.Use_Delayed_fake_tmeperatures.value = 0  
        rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)
        self.get_nand_temp()
        # t_status = self.get_fw_Tstatus() # for debug
        # logger.info(f'FW_Tstatus = {t_status}')
        
    def get_fw_Tstatus(self) -> int:
        t_status = cast(int, read_fw_value('gXtempMgr.T_status'))
        return t_status

    def get_nand_temp(self) -> None:
        rsp , GetNandTemperature = project_api.issue_4021_get_nand_temperature()
        die0_temp = GetNandTemperature.temperature_of_die_0.value - TEMP_GAP
        die1_temp = GetNandTemperature.temperature_of_die_1.value - TEMP_GAP
        die2_temp = GetNandTemperature.temperature_of_die_2.value - TEMP_GAP
        die3_temp = GetNandTemperature.temperature_of_die_3.value - TEMP_GAP
        logger.info(f'{die0_temp} / {die1_temp} / {die2_temp} / {die3_temp}')      

    def get_xtemp_parameter(self) -> tuple[int,int,int,int,int]:
        rsp, mconfig = project_api.get_mConfig_data()
        XTEMP_ENABLE_PEC = mconfig.XTEMP_ENABLE_PEC.value
        XTEMP_TEMP_BUFFER = mconfig.XTEMP_TEMP_BUFFER.value
        XTEMP_TIME_DETECTION_VALUE = mconfig.XTEMP_TIME_DETECTION_VALUE.value
        XTEMP_REFRESH_T1 = mconfig.XTEMP_Refresh_T1.value if mconfig.XTEMP_Refresh_T1.value <= 127 else mconfig.XTEMP_Refresh_T1.value - 256
        XTEMP_REFRESH_T2 = mconfig.XTEMP_Refresh_T2.value if mconfig.XTEMP_Refresh_T2.value <= 127 else mconfig.XTEMP_Refresh_T2.value - 256
        logger.info(f'Xtemp enable EPC = {XTEMP_ENABLE_PEC}, temp buffer = {XTEMP_TEMP_BUFFER}, time detection = {XTEMP_TIME_DETECTION_VALUE}')
        logger.info(f'Xtemp refresh T1 = {XTEMP_REFRESH_T1}, Xtemp refresh T2 = {XTEMP_REFRESH_T2}')

        if mconfig.XTEMP_ENABLE_PEC.value != 10:
            mconfig.XTEMP_ENABLE_PEC.value = 10
            mconfig.payload[0:7] = "MCONFIG".encode("ascii")
            project_api.set_mConfig_data(mConfig=mconfig)

            rsp, mconfig = project_api.get_mConfig_data()
            XTEMP_ENABLE_PEC = mconfig.XTEMP_ENABLE_PEC.value
            XTEMP_TEMP_BUFFER = mconfig.XTEMP_TEMP_BUFFER.value
            XTEMP_TIME_DETECTION_VALUE = mconfig.XTEMP_TIME_DETECTION_VALUE.value
            XTEMP_REFRESH_T1 = mconfig.XTEMP_Refresh_T1.value if mconfig.XTEMP_Refresh_T1.value <= 127 else mconfig.XTEMP_Refresh_T1.value - 256
            XTEMP_REFRESH_T2 = mconfig.XTEMP_Refresh_T2.value if mconfig.XTEMP_Refresh_T2.value <= 127 else mconfig.XTEMP_Refresh_T2.value - 256
            logger.info(f'Xtemp enable EPC = {XTEMP_ENABLE_PEC}, temp buffer = {XTEMP_TEMP_BUFFER}, time detection = {XTEMP_TIME_DETECTION_VALUE}')
            logger.info(f'Xtemp refresh T1 = {XTEMP_REFRESH_T1}, Xtemp refresh T2 = {XTEMP_REFRESH_T2}')
        return XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2

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
        self.backup_ec_value = self.get_device_ec()
        self.flash_setting = api.get_flash_setting()
        self.SLC_VB_size = self.fw_geometry.l84_vb_size_u0 >> 3 # menas (var * 512 / 4096) to change unit from sector to blocks
        self.TLC_VB_size = self.fw_geometry.l88_vb_size_u1 >> 3 # menas (var * 512 / 4096) to change unit from sector to blocks
        logger.info(f'SLC_VB_size = {self.SLC_VB_size}, TLC_VB_size = {self.TLC_VB_size}')
        self.startLBA = 0
        self.VB_risky_type:dict[int ,int] = {}
        self.write_record = api.get_empty_write_record()

    def step1(self) -> None:
        logger.flow(1, 'Config LUN0 with total AU in normal memory type and erase purge all capacity')
        self.config_precondition()
        self.update_unit_desc()
        self.update_device_desc()

        logger.flow(2, 'Get xtemp parameter from mconfig')
        XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2 = self.get_xtemp_parameter()
        idle_wait_detect_temp = 2 * XTEMP_TIME_DETECTION_VALUE

        logger.flow(3, f'Set EC as XTEMP_ENABLE_PEC * 100 = {XTEMP_ENABLE_PEC * 100}')
        set_ec_value = XTEMP_ENABLE_PEC * 100
        value_bytes = set_ec_value.to_bytes(4, byteorder='little', signed=False)
        data = bytearray(b'\xFF' * 0x4000)
        data[:(self.fw_geometry.l52_total_vb_count * 4)] = value_bytes * self.fw_geometry.l52_total_vb_count
        self.set_ec(data)

        logger.flow(4, 'Issue HW reset to enable xtemp algo')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)

        logger.flow(5, 'Get nand temp from VU 0x4021')
        self.get_nand_temp()

        # ====== Tstatus is 'Safe' ======
        logger.flow(6, 'Sequential write 1 TLC VB size for creating used VB and get VB info for verifying risky type should be no any mark')
        api.sequential_write(lun=0, start_lba=self.startLBA, total_size=self.TLC_VB_size + (6 * BLOCK4K_SIZE_16K_BYTE), chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 0,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.startLBA += self.TLC_VB_size + (6 * BLOCK4K_SIZE_16K_BYTE)
        self.refresh_behavior_check(behavior = RefreshBehavior.NA, Tstatus = Tnandzone.SAFE, expected_new_VB_ricky_type = RiskyType.SAFE_GROUP)
        
        logger.flow(7, f'Set nand temp as XTEMP_REFRESH_T2 + 1 = {XTEMP_REFRESH_T2 + 1}')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T2 + 1)
        time.sleep(idle_wait_detect_temp)

	    # ====== Tstatus is 'Hot Risky' ======
        logger.flow(8, f'Check the VB created when Tstatus is "Safe" should keep without any risky type and no any booking user is XTEMP_BOOKING(20) with BOOKING_IN_MP(BIT9)')
        self.refresh_behavior_check(behavior = RefreshBehavior.NA, Tstatus = Tnandzone.HOT, expected_new_VB_ricky_type = RiskyType.NA)

        logger.flow(9, 'Sequential write 1 TLC VB size data and check VB risky type should mark risky type as "Hot Risky"')
        api.sequential_write(lun=0, start_lba=self.startLBA, total_size=self.TLC_VB_size, chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 0,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.startLBA += self.TLC_VB_size
        self.refresh_behavior_check(behavior = RefreshBehavior.NA, Tstatus = Tnandzone.HOT, expected_new_VB_ricky_type = RiskyType.HOT_GROUP)

        logger.flow(10, f'Set nand temp as XTEMP_REFRESH_T2 = {XTEMP_REFRESH_T2}')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T2)
        time.sleep(idle_wait_detect_temp)

        # ====== Tstatus is 'Safe' but not starting to trigger MP refresh of all Hot Risky VBs======
        logger.flow(11, 'check the VB created when Tstatus is "Hot Risky" should keep risky type as "Hot Risky" and no any booking user is XTEMP_BOOKING(20) with BOOKING_IN_MP(BIT9)')
        self.refresh_behavior_check(behavior = RefreshBehavior.NA, Tstatus = Tnandzone.SAFE, expected_new_VB_ricky_type = RiskyType.NA)

        logger.flow(12, 'Sequential write 1 TLC VB size data and check VB risky type should not mark any risky type')
        api.sequential_write(lun=0, start_lba=self.startLBA, total_size=self.TLC_VB_size, chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 0,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.startLBA += self.TLC_VB_size
        self.refresh_behavior_check(behavior = RefreshBehavior.NA, Tstatus = Tnandzone.SAFE, expected_new_VB_ricky_type = RiskyType.SAFE_GROUP)

        logger.flow(13, f'Issue VU 0xD08A to set NAND temperature as (XTEMP_Refresh_T2 - XTEMP_TEMP_BUFFER) = {XTEMP_REFRESH_T2 - XTEMP_TEMP_BUFFER} and check and no any booking user is XTEMP_BOOKING(20) with BOOKING_IN_MP(BIT9)')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T2 - XTEMP_TEMP_BUFFER)
        time.sleep(idle_wait_detect_temp)
        self.refresh_behavior_check(behavior = RefreshBehavior.NA, Tstatus = Tnandzone.SAFE, expected_new_VB_ricky_type = RiskyType.NA)

        logger.flow(14, f'Issue VU 0xD08A to set NAND temperature as (XTEMP_Refresh_T2 - XTEMP_TEMP_BUFFER - 1) = {XTEMP_REFRESH_T2 - XTEMP_TEMP_BUFFER - 1}')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T2 - XTEMP_TEMP_BUFFER - 1)
        time.sleep(idle_wait_detect_temp)

        # ====== Tstatus is 'Safe' ======
        logger.flow(15, 'Check risky type VBs should be refreshed any mark as no risky')
        self.refresh_behavior_check(behavior = RefreshBehavior.Hot2Safe, Tstatus = Tnandzone.SAFE, expected_new_VB_ricky_type = RiskyType.NA)

        logger.flow(16, 'Sequential write 1 TLC VB size data and check VB risky type should not mark any risky type')
        api.sequential_write(lun=0, start_lba=self.startLBA, total_size=self.TLC_VB_size, chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 0,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.startLBA += self.TLC_VB_size
        self.refresh_behavior_check(behavior = RefreshBehavior.NA, Tstatus = Tnandzone.SAFE, expected_new_VB_ricky_type = RiskyType.SAFE_GROUP)

        logger.flow(17, f'Set nand temp as XTEMP_REFRESH_T1 - 1 = {XTEMP_REFRESH_T1 - 1}')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T1 - 1)
        time.sleep(idle_wait_detect_temp)

        # ====== Tstatus is 'Cold Risky' ======
        logger.flow(18, f'Check the VB created when Tstatus is "Safe" should keep without any risky type and no any booking user is XTEMP_BOOKING(20) with BOOKING_IN_MP(BIT9)')
        self.refresh_behavior_check(behavior = RefreshBehavior.NA, Tstatus = Tnandzone.COLD, expected_new_VB_ricky_type = RiskyType.NA)

        logger.flow(19, 'Sequential write 1 TLC VB size data and check VB risky type should mark risky type as "Cold Risky"')
        api.sequential_write(lun=0, start_lba=self.startLBA, total_size=self.TLC_VB_size, chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 0,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.startLBA += self.TLC_VB_size
        self.refresh_behavior_check(behavior = RefreshBehavior.NA, Tstatus = Tnandzone.COLD, expected_new_VB_ricky_type = RiskyType.COLD_GROUP)

        logger.flow(20, f'Set nand temp as XTEMP_REFRESH_T1 = {XTEMP_REFRESH_T1}')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T1)
        time.sleep(idle_wait_detect_temp)

        # ====== Tstatus is 'Safe' but not starting to trigger MP refresh of all Cold Risky VBs======
        logger.flow(21, 'check the VB created when Tstatus is "Cold Risky" should keep risky type as "Cold Risky" and no any booking user is XTEMP_BOOKING(20) with BOOKING_IN_MP(BIT9)')
        self.refresh_behavior_check(behavior = RefreshBehavior.NA, Tstatus = Tnandzone.SAFE, expected_new_VB_ricky_type = RiskyType.NA)

        logger.flow(22, 'Sequential write 1 TLC VB size data and check VB risky type should not mark any risky type')
        api.sequential_write(lun=0, start_lba=self.startLBA, total_size=self.TLC_VB_size, chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 0,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.startLBA += self.TLC_VB_size
        self.refresh_behavior_check(behavior = RefreshBehavior.NA, Tstatus = Tnandzone.SAFE, expected_new_VB_ricky_type = RiskyType.SAFE_GROUP)

        logger.flow(23, f'Issue VU 0xD08A to set NAND temperature as (XTEMP_Refresh_T1 + XTEMP_TEMP_BUFFER) = {XTEMP_REFRESH_T1 + XTEMP_TEMP_BUFFER} and check and no any booking user is XTEMP_BOOKING(20) with BOOKING_IN_MP(BIT9)')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T1 + XTEMP_TEMP_BUFFER)
        time.sleep(idle_wait_detect_temp)
        self.refresh_behavior_check(behavior = RefreshBehavior.NA, Tstatus = Tnandzone.SAFE, expected_new_VB_ricky_type = RiskyType.NA)

        logger.flow(24, f'Issue VU 0xD08A to set NAND temperature as (XTEMP_Refresh_T1 + XTEMP_TEMP_BUFFER + 1) = {XTEMP_REFRESH_T1 + XTEMP_TEMP_BUFFER + 1}')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T1 + XTEMP_TEMP_BUFFER + 1)
        time.sleep(idle_wait_detect_temp)

        # ====== Tstatus is 'Safe' ======
        logger.flow(25, 'Check risky type VBs should be refreshed any mark as no risky')
        self.refresh_behavior_check(behavior = RefreshBehavior.Cold2Safe, Tstatus = Tnandzone.SAFE, expected_new_VB_ricky_type = RiskyType.NA)
        pass

    def refresh_behavior_check(self, behavior:RefreshBehavior, Tstatus:Tnandzone, expected_new_VB_ricky_type:RiskyType = RiskyType.NA) -> None:
        current_VB_risky_type:dict[int ,int] = self.get_current_used_vb_risky_type()
        xtemp_user_count, xtemp_user_vb = self.get_booking_Q()
        logger.info(f' Now vb risky type: {current_VB_risky_type}')
        logger.info(f'Self vb risky type: {self.VB_risky_type}')

        if behavior == RefreshBehavior.NA and expected_new_VB_ricky_type == RiskyType.NA:
            if (current_VB_risky_type != self.VB_risky_type) or (xtemp_user_count != 0):
                logger.error_lb('Expect no any behavior about refresh VB, VB group shall keep same value and xtemp booking user count should be 0')
                logger.error_fp(f'current vb risky type: {current_VB_risky_type}, before risky type: {self.VB_risky_type}, xtemp booking vb list: {xtemp_user_vb}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                logger.info('VB group keep same value and no xtemp booking user for refreshing')
        elif behavior == RefreshBehavior.NA: # means expected_new_VB_ricky_type != RiskyType.NA
            if xtemp_user_count != 0:
                logger.error_lb('Expect no any behavior about refresh VB')
                logger.error_fp(f'Xtemp booking user count should be 0 but current value = {xtemp_user_count}, xtemp booking vb list: {xtemp_user_vb}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if not set(self.VB_risky_type.keys()).issubset(set(current_VB_risky_type.keys())):
                logger.error_lb('Expect before used VB should keep after operation')
                logger.error_fp(f'Before used VB not in current used VB, current vb risky type: {current_VB_risky_type}, before risky type: {self.VB_risky_type}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            common_keys: Set[int] = set(self.VB_risky_type.keys()) & set(current_VB_risky_type.keys())
            logger.info(f'Common VBs : {common_keys}')
            if not all(self.VB_risky_type[k] == current_VB_risky_type[k] for k in common_keys):
                logger.error_lb('Expect before used VB should keep after operation and keep risky type')
                logger.error_fp(f'Current vb risky type: {current_VB_risky_type}, before risky type: {self.VB_risky_type}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            extra_VBs = set(current_VB_risky_type.keys()) - set(self.VB_risky_type.keys())
            if len(extra_VBs) != 1:
                logger.error_lb('Used VB count should increased by 1 after operation')
                logger.error_fp(f'Current vb risky type: {current_VB_risky_type}, before risky type: {self.VB_risky_type}, extra VBs: {list(extra_VBs)}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if current_VB_risky_type[list(extra_VBs)[0]] != expected_new_VB_ricky_type:
                logger.error_lb(f'Expect new used VB created with risky type {expected_new_VB_ricky_type}')
                logger.error_fp(f'New created VB {list(extra_VBs)[0]} with risky type is {current_VB_risky_type[list(extra_VBs)[0]]} but expected risky type is {expected_new_VB_ricky_type}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                logger.info(f'New used VB {list(extra_VBs)[0]} created with risky type {current_VB_risky_type[list(extra_VBs)[0]]}, as same as expected new VB risky type {expected_new_VB_ricky_type}')
        elif expected_new_VB_ricky_type == RiskyType.NA: # means behavior != RefreshBehavior.NA
            if current_VB_risky_type == self.VB_risky_type:
                if xtemp_user_count == 0:
                    logger.error_lb(f'Expect xtemp refresh with risky type {behavior}')
                    logger.error_fp(f'Current vb risky type: {current_VB_risky_type} is same as before risky type: {self.VB_risky_type} and xtemp booking user count is 0 means xtemp refresh does not triggered')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    current_VB_risky_type = self.polling_xtemp_refresh_done()
                    xtemp_user_count = 0
            elif xtemp_user_count != 0:
                logger.error_lb(f'Expect xtemp refresh with risky type {behavior}')
                logger.error_fp(f'Current vb risky type: {current_VB_risky_type} is different with before risky type: {self.VB_risky_type} but xtemp booking user count is {xtemp_user_count} not 0 means xtemp refresh does not done but VB changed')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            for k,v in current_VB_risky_type.items():
                if v != 0:
                    logger.error_lb(f'Expect all VB refresh to be safe group')
                    logger.error_fp(f'Current vb risky type: {current_VB_risky_type}, not all are safe group VB')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if len(current_VB_risky_type) != len(self.VB_risky_type):
                logger.error_lb(f'Expect used vb count shall keep same number')
                logger.error_fp(f'Current vb risky type: {current_VB_risky_type}, before vb risky type: {self.VB_risky_type}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            self.VB_risky_type = {
                k: v
                for k, v in self.VB_risky_type.items()
                if v == 0
            }
            if not set(self.VB_risky_type.keys()).issubset(set(current_VB_risky_type.keys())):
                logger.error_lb('Expect before safe group used VB should keep after operation')
                logger.error_fp(f'Before safe group used VB not in current used VB, current vb risky type: {current_VB_risky_type}, before vb risky type: {self.VB_risky_type}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.error_lb(f'Check behavior about refresh')
            logger.error_fp(f'Unexpected condition, behavior = {behavior}, Tstatus = {Tstatus}, expected_new_VB_ricky_type = {expected_new_VB_ricky_type}')
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION

        self.VB_risky_type = self.polling_xtemp_refresh_done() if xtemp_user_count != 0 else deepcopy(current_VB_risky_type)

    def polling_xtemp_refresh_done(self) -> dict[int ,int]:
        start_time = time.time()
        timeout_min = 1
        xtemp_user_count, xtemp_user_vb = self.get_booking_Q()
        while xtemp_user_count != 0:
            logger.info(f'xtemp booking vb list: {xtemp_user_vb}')
            if check_timeout(start_time, timeout_min):
                logger.error_lb('Polling xtemp refresh done in 1 min')
                logger.error_fp(f'Expect xtemp refresh done in 1 min but not, current xtemp booking vb list: {xtemp_user_vb}')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            xtemp_user_count, xtemp_user_vb = self.get_booking_Q()

        return self.get_current_used_vb_risky_type()

    def get_current_used_vb_risky_type(self) -> dict[int ,int]:
        rsp, vb_info = api.get_vb_info()
        current_VB_risky_type:dict[int ,int] = {}
        for vb_num in range(self.fw_geometry.l52_total_vb_count):
            four_bytes = vb_info[vb_num * 4:(vb_num + 1) * 4]
            integer_value = int.from_bytes(four_bytes, byteorder='little')
            vb_group = integer_value & 0x3F
            access_mode = (integer_value >> 6) & 0x3
            risky_type = (integer_value >> 18) & 0x3
            if vb_group == VB_group_for_list.USED_BLK_POOL_MLC:
                logger.info(f'VB {vb_num}, group = {vb_group}, access = {access_mode}, risky type = {risky_type}')
                current_VB_risky_type[vb_num] = risky_type
            if vb_group == VB_group_for_list.CURRENT_L2_MLC:
                logger.info(f'VB {vb_num}, group = {vb_group}, access = {access_mode}, risky type = {risky_type}')
        return current_VB_risky_type

    def get_booking_Q(self) -> tuple[int, list[int]]:
        rsp, bookingQ = project_api.issue_40C5_to_get_booking_queue()
        xtemp_user_vb:list[int] = []
        xtemp_user_count = 0
        logger.info(f'LogicalVBNumberInBookingQueue = {bookingQ.LogicalVBNumberInBookingQueue.value}')
        if bookingQ.LogicalVBNumberInBookingQueue.value != 0:
            for idx in range(bookingQ.LogicalVBNumberInBookingQueue.value):
                logger.info(f'VB = {bookingQ.BookingQueueVB[idx].LogicalVBNumber.value}, Booking user = 0x{bookingQ.BookingQueueVB[idx].TheBookingUser.value:04X}')
                if bookingQ.BookingQueueVB[idx].TheBookingUser.value == (XTEMP_BOOKING | BOOKING_IN_MP):
                    xtemp_user_vb.append(bookingQ.BookingQueueVB[idx].LogicalVBNumber.value)
                    xtemp_user_count += 1
        return xtemp_user_count, xtemp_user_vb

    def post_process(self) -> None:
        self.set_ec(set_ec=self.backup_ec_value)
        pass

run = Pattern().run
if __name__ == "__main__":
    run()