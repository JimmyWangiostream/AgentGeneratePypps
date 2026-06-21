from copy import deepcopy
from enum import IntEnum
import random
import time
from typing import Any, List, Set, cast

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
from Script.project_api.functions import print_object_info_ai

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
    def config_precondition(self, WB_partition:bool) -> None:
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.b17_write_booster_buffer_type = 1 if WB_partition else 0
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 1 if WB_partition else 0
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x1000 if WB_partition else 0
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

        if mconfig.XTEMP_ENABLE_PEC.value < 2 or mconfig.XTEMP_ENABLE_PEC.value > 10:
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

    def get_specific_vb_group(self, string:str) -> Any:
        rsp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        print_object_info_ai(open_vb_information)
        value_before = None
        for name, field in open_vb_information.__dict__.items():
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value"):
                if name == string:
                    value_before = field.value
                    break
        return value_before  
    
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
        logger.flow(1, 'Config LUN0 with total AU in normal memory type and WB partition')
        self.config_precondition(WB_partition = True)
        self.update_unit_desc()
        self.update_device_desc()

        logger.flow(2, 'Get mconfig for parameters: XTEMP_ENABLE_PEC, NXTEMP_Refresh_T1, NXTEMP_Refresh_T2, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE; if XTEMP_ENABLE_PEC not between 2 and 10, set it to 10')
        XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2 = self.get_xtemp_parameter()
        idle_wait_detect_temp = XTEMP_TIME_DETECTION_VALUE

        logger.flow(3, f'Set all VB EC as (XTEMP_ENABLE_PEC * 100) = {XTEMP_ENABLE_PEC * 100} (enable XTEMP condition)')
        set_ec_value = XTEMP_ENABLE_PEC * 100
        value_bytes = set_ec_value.to_bytes(4, byteorder='little', signed=False)
        data = bytearray(b'\xFF' * 0x4000)
        data[:(self.fw_geometry.l52_total_vb_count * 4)] = value_bytes * self.fw_geometry.l52_total_vb_count
        self.set_ec(data)

        logger.flow(4, 'HW reset to enable XTEMP algorithm')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)

        logger.flow(5, f'Issue VU 0xD08A to set NAND temperature to XTEMP_Refresh_T2 + 1 = {XTEMP_REFRESH_T2 + 1}, changing Tstatus to "Hot Risky"')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T2 + 1)
        time.sleep(idle_wait_detect_temp)

        logger.flow(6, 'Enable WB and sequential write for filling WB buffer')
        api.set_flag(idn = api.FlagIDN.WRITEBOOSTER_EN)
        available_WB_size = 0xA
        start_time = time.time()
        timeout_min = 5
        while available_WB_size != 0x0:
            if check_timeout(start_time = start_time, timeout_min = timeout_min):
                logger.error_lb('Sequential write data for filling WB buffer size')
                logger.error_fp(f'Flow timeout 5 min, current available WB size = 0x{available_WB_size:X}, write cumulative data size = {self.startLBA}')
                raise SPEC_ASSERT_UFS_RSP_OP_SHALL_WRITE_ATTRIBUTE
            if self.startLBA + self.TLC_VB_size > self.param.gLUCapacity[0]:
                logger.error_lb('Sequential write data for filling WB buffer size')
                logger.error_fp(f'Current available WB size = 0x{available_WB_size:X}, write cumulative data size = {self.startLBA} will reach LUN0 capacity({self.param.gLUCapacity[0]})')
                raise SPEC_ASSERT_UFS_RSP_OP_SHALL_WRITE_ATTRIBUTE
            api.sequential_write(lun=0, start_lba=self.startLBA, total_size=self.TLC_VB_size, chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 0,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            self.startLBA += self.TLC_VB_size
            available_WB_size = api.read_attribute(idn = api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)

        logger.flow(7, 'Enable WB buffer flush')
        api.set_flag(idn = api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)

        logger.flow(8, 'Issue VU 0x40C1 to get open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC and polling until the risky type of VB is "Hot risky"')
        Open_GC_TLC_VB = self.get_specific_vb_group("open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC")
        risky_type = 0
        group_type = 0
        start_time = time.time()
        timeout_min = 1
        if Open_GC_TLC_VB != 0xFFFFFFFF:
            group_type, risky_type = self.get_vb_group_and_risky_type(vb = Open_GC_TLC_VB, print_risky_type = RiskyType.HOT_GROUP)
        while Open_GC_TLC_VB == 0xFFFFFFFF or risky_type != RiskyType.HOT_GROUP:
            if check_timeout(start_time = start_time, timeout_min = timeout_min):
                logger.error_lb('Enable WB flush and polling Open_GC_TLC_VB')
                logger.error_fp(f'Flow timeout {timeout_min} min, expect Open_GC_TLC_VB should be valid and risky type should be "Hot group", current Open_GC_TLC_VB = {Open_GC_TLC_VB}, group = {group_type}, risky = {risky_type}')
                raise SPEC_ASSERT_UFS_RSP_OP_SHALL_WRITE_ATTRIBUTE
            Open_GC_TLC_VB = self.get_specific_vb_group("open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC")
            if Open_GC_TLC_VB != 0xFFFFFFFF:
                group_type, risky_type = self.get_vb_group_and_risky_type(vb = Open_GC_TLC_VB, print_risky_type = RiskyType.HOT_GROUP)

        logger.flow(9, 'Issue VU 0xD08A to set NAND temperature as (XTEMP_Refresh_T2 - XTEMP_TEMP_BUFFER - 1)')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T2 - XTEMP_TEMP_BUFFER - 1)
        time.sleep(idle_wait_detect_temp)

        logger.flow(10, 'Check VB with hot risky type should be refreshed; mark as no risky. VU 0x40C5 checks that VB with hot risky type must be booking user XTEMP_BOOKING(20)')
        xtemp_user_count, xtemp_user_vb = self.get_booking_Q()
        if xtemp_user_count == 1:
            if xtemp_user_vb[0] != Open_GC_TLC_VB:
                logger.error_lb('Expect Open_GC_TLC_VB should pushed in refresh bookingQ after Tstatus set to safe zone')
                logger.error_fp(f'Open_GC_TLC_VB is {Open_GC_TLC_VB}, xtemp booking vb is {xtemp_user_vb[0]} mismatch')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            group_type, risky_type = self.get_vb_group_and_risky_type(vb = Open_GC_TLC_VB, print_risky_type = RiskyType.HOT_GROUP)
            if group_type == VB_group_for_list.CURRENT_DATA_GC_BLK_MLC and risky_type == RiskyType.HOT_GROUP:
                logger.error_lb('Expect Open_GC_TLC_VB should pushed in refresh bookingQ or finished refresh after Tstatus set to safe zone')
                logger.error_fp(f'The original Open_GC_TLC_VB {Open_GC_TLC_VB} keep group({group_type}) and risky type({risky_type}), it does not refresh or pushed in bookingQ')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                start_time = time.time()
                timeout_min = 5
                while group_type != VB_group_for_list.FREE_BLK_QUEUE_MLC:
                    if (time.time() - start_time) > (timeout_min * 60):
                        logger.error_lb(f'Polling the original Open_GC_TLC_VB {Open_GC_TLC_VB} refresh as free blk')
                        logger.error_fp(f'Flow timeout {timeout_min} min, expect original Open_GC_TLC_VB {Open_GC_TLC_VB} should refresh as free blk but current VB group is {group_type}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL                
                    time.sleep(1)
                    group_type, risky_type = self.get_vb_group_and_risky_type(vb = Open_GC_TLC_VB)
                    logger.info(f'Polling the original Open_GC_TLC_VB {Open_GC_TLC_VB} refresh as free blk, current VB group = {group_type}, risky type = {risky_type}')

        logger.flow(11, 'Enable WB buffer flush and polling flush complete')
        available_WB_size = 0x0
        flush_status = 0x0
        start_time = time.time()
        timeout_min = 5
        while available_WB_size != 0xA or flush_status == api.WriteBoosterBufferFlushStatus.IN_PROGRESS:
            if (time.time() - start_time) > (timeout_min * 60):
                logger.error_lb('Enable WB flush and polling flush status')
                logger.error_fp(f'Flow timeout 5 min, current available WB size = 0x{available_WB_size:X}, flush status = 0x{flush_status}')
                raise SPEC_ASSERT_UFS_RSP_OP_SHALL_WRITE_ATTRIBUTE
            available_WB_size = api.read_attribute(idn = api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
            flush_status = api.read_attribute(idn = api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS)

        logger.flow(12, 'Disable WB flush')
        api.clear_flag(idn = api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)

        logger.flow(13, 'Issue VU 0xD08A to set NAND temperature as (XTEMP_Refresh_T1 - 1) for changing Tstatus into "Cold Risky"')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T1 - 1)
        time.sleep(idle_wait_detect_temp)

        logger.flow(14, 'Sequential write for filling WB buffer')
        available_WB_size = 0xA
        start_time = time.time()
        timeout_min = 5
        while available_WB_size != 0x0:
            if check_timeout(start_time = start_time, timeout_min = timeout_min):
                logger.error_lb('Sequential write data for filling WB buffer size')
                logger.error_fp(f'Flow timeout 5 min, current available WB size = 0x{available_WB_size:X}, write cumulative data size = {self.startLBA}')
                raise SPEC_ASSERT_UFS_RSP_OP_SHALL_WRITE_ATTRIBUTE
            if self.startLBA + self.TLC_VB_size > self.param.gLUCapacity[0]:
                logger.error_lb('Sequential write data for filling WB buffer size')
                logger.error_fp(f'Current available WB size = 0x{available_WB_size:X}, write cumulative data size = {self.startLBA} will reach LUN0 capacity({self.param.gLUCapacity[0]})')
                raise SPEC_ASSERT_UFS_RSP_OP_SHALL_WRITE_ATTRIBUTE
            api.sequential_write(lun=0, start_lba=self.startLBA, total_size=self.TLC_VB_size, chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 0,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            self.startLBA += self.TLC_VB_size
            available_WB_size = api.read_attribute(idn = api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)

        logger.flow(15, 'Enable WB buffer flush')
        api.set_flag(idn = api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)

        logger.flow(16, 'Issue VU 0x40C1 to get open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC and polling until the risky type of VB is "Cold risky"')
        Open_GC_TLC_VB = self.get_specific_vb_group("open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC")
        risky_type = 0
        group_type = 0
        start_time = time.time()
        timeout_min = 1
        if Open_GC_TLC_VB != 0xFFFFFFFF:
            group_type, risky_type = self.get_vb_group_and_risky_type(vb = Open_GC_TLC_VB, print_risky_type = RiskyType.COLD_GROUP)
        while Open_GC_TLC_VB == 0xFFFFFFFF or risky_type != RiskyType.COLD_GROUP:
            if check_timeout(start_time = start_time, timeout_min = timeout_min):
                logger.error_lb('Enable WB flush and polling Open_GC_TLC_VB')
                logger.error_fp(f'Flow timeout {timeout_min} min, expect Open_GC_TLC_VB should be valid and risky type should be "Cold group", current Open_GC_TLC_VB = {Open_GC_TLC_VB}, group = {group_type}, risky = {risky_type}')
                raise SPEC_ASSERT_UFS_RSP_OP_SHALL_WRITE_ATTRIBUTE
            Open_GC_TLC_VB = self.get_specific_vb_group("open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC")
            if Open_GC_TLC_VB != 0xFFFFFFFF:
                group_type, risky_type = self.get_vb_group_and_risky_type(vb = Open_GC_TLC_VB, print_risky_type = RiskyType.COLD_GROUP)

        logger.flow(17, 'Issue VU 0xD08A to set NAND temperature as (XTEMP_Refresh_T1 + XTEMP_TEMP_BUFFER + 1)')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T1 + XTEMP_TEMP_BUFFER + 1)
        time.sleep(idle_wait_detect_temp)

        logger.flow(18, 'Check VB with cold risky type should be refreshed; mark as no risky. VU 0x40C5 checks that VB with cold risky type must be booking user XTEMP_BOOKING(20)')
        xtemp_user_count, xtemp_user_vb = self.get_booking_Q()
        if xtemp_user_count == 1:
            if xtemp_user_vb[0] != Open_GC_TLC_VB:
                logger.error_lb('Expect Open_GC_TLC_VB should pushed in refresh bookingQ after Tstatus set to safe zone')
                logger.error_fp(f'Open_GC_TLC_VB is {Open_GC_TLC_VB}, xtemp booking vb is {xtemp_user_vb[0]} mismatch')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            group_type, risky_type = self.get_vb_group_and_risky_type(vb = Open_GC_TLC_VB, print_risky_type = RiskyType.COLD_GROUP)
            if group_type == VB_group_for_list.CURRENT_DATA_GC_BLK_MLC and risky_type == RiskyType.COLD_GROUP:
                logger.error_lb('Expect Open_GC_TLC_VB should pushed in refresh bookingQ or finished refresh after Tstatus set to safe zone')
                logger.error_fp(f'The original Open_GC_TLC_VB {Open_GC_TLC_VB} keep group({group_type}) and risky type({risky_type}), it does not refresh or pushed in bookingQ')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                start_time = time.time()
                timeout_min = 5
                while group_type != VB_group_for_list.FREE_BLK_QUEUE_MLC:
                    if (time.time() - start_time) > (timeout_min * 60):
                        logger.error_lb(f'Polling the original Open_GC_TLC_VB {Open_GC_TLC_VB} refresh as free blk')
                        logger.error_fp(f'Flow timeout {timeout_min} min, expect original Open_GC_TLC_VB {Open_GC_TLC_VB} should refresh as free blk but current VB group is {group_type}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL                
                    time.sleep(1)
                    group_type, risky_type = self.get_vb_group_and_risky_type(vb = Open_GC_TLC_VB)
                    logger.info(f'Polling the original Open_GC_TLC_VB {Open_GC_TLC_VB} refresh as free blk, current VB group = {group_type}, risky type = {risky_type}')

        logger.flow(19, 'Config LUN0 with total AU in normal memory type without WB partition')
        self.config_precondition(WB_partition = False)
        self.update_unit_desc()
        self.update_device_desc()
        self.startLBA = 0

        logger.flow(20, 'HW reset to reset Tstatus')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)

        logger.flow(21, 'Issue VU 0xD08A to set NAND temperature as XTEMP_Refresh_T2 + 1 for changing Tstatus into "Hot Risky"')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T2 + 1)
        time.sleep(idle_wait_detect_temp)

        logger.flow(22, 'Sequential write 5 TLC VB size data and check that VBs risky type is marked as "Hot group"')
        api.sequential_write(lun=0, start_lba=self.startLBA, total_size=5 * self.TLC_VB_size + (6 * BLOCK4K_SIZE_16K_BYTE), chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 0,
                                need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.startLBA += 5 * self.TLC_VB_size + (6 * BLOCK4K_SIZE_16K_BYTE)
        Hot_VB_list = self.get_specific_risky_VB(risky_type_str = 'Hot')
        Hot_VB_count = len(Hot_VB_list)
        VB_list = deepcopy(Hot_VB_list)

        logger.flow(23, 'Issue VU 0xD08A to set NAND temperature as XTEMP_Refresh_T1 - 1 for changing Tstatus into "Cold Risky"')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T1 - 1)
        time.sleep(idle_wait_detect_temp)

        logger.flow(24, 'Check the VB created when Tstatus is "Hot Risky" should change risky type to "Cold group"; VU 0x40C5 verifies that VB with hot risky type must be booking user XTEMP_BOOKING(20)')
        risky_VB_cnt = len(VB_list)
        before_VB_inQ = 0
        while risky_VB_cnt != 0:
            xtemp_user_count, xtemp_user_vb = self.get_booking_Q()
            if xtemp_user_count != 1:
                logger.error_lb('Created VB when Tstatus is "Hot Risky" and set Tstatus as "Cold Risky"')
                logger.error_fp(f'Device should start to refresh hot group VBs but booking user XTEMP_BOOKING(20) count is 0 in bookingQ')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            elif xtemp_user_vb[0] != before_VB_inQ:
                if xtemp_user_vb[0] != VB_list[0]:
                    logger.error_lb('Expect booking user XTEMP_BOOKING(20) VB should be min of risky VBs')
                    logger.error_fp(f'XTEMP_BOOKING(20) VB = {xtemp_user_vb[0]}, least risky VB list = {VB_list}, refresh order = {Hot_VB_list}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    VB_list.remove(xtemp_user_vb[0])
                    risky_VB_cnt = len(VB_list)
                before_VB_inQ = xtemp_user_vb[0]
                time.sleep(idle_wait_detect_temp)

        self.polling_xtemp_refresh_done()
        Cold_VB_list = self.get_specific_risky_VB(risky_type_str = 'Cold')
        Cold_VB_count = len(Cold_VB_list)
        if Hot_VB_count != Cold_VB_count:
            logger.error_lb('Hot group VBs should refreshed and mark as Cold group after set Tstatus as "Cold Risky"')
            logger.error_fp(f'Hot group VBs = {Hot_VB_list}, Cold group VBs after set Tstatus to "Cold Risky" = {Cold_VB_list}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        VB_list = deepcopy(Cold_VB_list)

        logger.flow(25, 'Sequential write 5 TLC VB size data and check that VBs risky type is marked as "Cold group"')
        api.sequential_write(lun=0, start_lba=self.startLBA, total_size=5 * self.TLC_VB_size, chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 0,
                                need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.startLBA += 5 * self.TLC_VB_size
        Cold_VB_list = self.get_specific_risky_VB(risky_type_str = 'Cold')
        Cold_VB_count = len(Cold_VB_list)
        for VB_num in Cold_VB_list:
            if VB_num not in VB_list:
                VB_list.append(VB_num)

        logger.flow(26, 'Issue VU 0xD08A to set NAND temperature as XTEMP_Refresh_T2 + 1 for changing Tstatus into "Hot Risky"')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T2 + 1)
        time.sleep(idle_wait_detect_temp)

        logger.flow(27, 'Check the VB created when Tstatus is "Cold Risky" should change risky type to "Hot group"; VU 0x40C5 verifies that VB with cold risky type must be booking user XTEMP_BOOKING(20)')
        risky_VB_cnt = len(VB_list)
        before_VB_inQ = 0
        while risky_VB_cnt != 0:
            xtemp_user_count, xtemp_user_vb = self.get_booking_Q()
            if xtemp_user_count != 1:
                logger.error_lb('Created VB when Tstatus is "Cold Risky" and set Tstatus as "Safe zone"')
                logger.error_fp(f'Device should start to refresh hot group VBs but booking user XTEMP_BOOKING(20) count is 0 in bookingQ')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            elif xtemp_user_vb[0] != before_VB_inQ:
                if xtemp_user_vb[0] != VB_list[0]:
                    logger.error_lb('Expect booking user XTEMP_BOOKING(20) VB should be min of risky VBs')
                    logger.error_fp(f'XTEMP_BOOKING(20) VB = {xtemp_user_vb[0]}, least risky VB list = {VB_list}, refresh order = {Cold_VB_list}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    VB_list.remove(xtemp_user_vb[0])
                    risky_VB_cnt = len(VB_list)
                before_VB_inQ = xtemp_user_vb[0]
                time.sleep(idle_wait_detect_temp)

        self.polling_xtemp_refresh_done()
        Hot_VB_list = self.get_specific_risky_VB(risky_type_str = 'Hot')
        Hot_VB_count = len(Hot_VB_list)
        if Hot_VB_count != Cold_VB_count:
            logger.error_lb('Cold group VBs should refreshed and mark as Hot group after set Tstatus as "Hot Risky"')
            logger.error_fp(f'Hot group VBs = {Hot_VB_list}, Cold group VBs after set Tstatus to "Cold Risky" = {Cold_VB_list}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def polling_xtemp_refresh_done(self) -> None:
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

    def get_vb_group_and_risky_type(self, vb:int, print_risky_type:int = 0xFF) -> tuple[int, int]:
        rsp, vb_info = api.get_vb_info()
        ret_risky_of_vb:int = 0
        ret_group_of_vb:int = 0
        for vb_num in range(self.fw_geometry.l52_total_vb_count):
            four_bytes = vb_info[vb_num * 4:(vb_num + 1) * 4]
            integer_value = int.from_bytes(four_bytes, byteorder='little')
            vb_group = integer_value & 0x3F
            access_mode = (integer_value >> 6) & 0x3
            risky_type = (integer_value >> 18) & 0x3
            if vb_num == vb or risky_type == print_risky_type:
                logger.info(f'VB {vb_num}, group = {vb_group}, access = {access_mode}, risky type = {risky_type}')
                if vb_num == vb:
                    ret_risky_of_vb = risky_type
                    ret_group_of_vb = vb_group
        return ret_group_of_vb, ret_risky_of_vb

    def get_specific_risky_VB(self, risky_type_str:str) -> list[int]:
        status_uc = risky_type_str.upper()
        if status_uc not in {"HOT", "COLD"}:
            logger.error_lb(f'Set xtemp environment with risky Tstatus')
            logger.error_fp(f'Input parameter Tstatus = "{risky_type_str}" is unexpected')
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION

        if status_uc == "HOT":
            expect_risky_type = RiskyType.HOT_GROUP
        else:
            expect_risky_type = RiskyType.COLD_GROUP

        rsp, vb_info = api.get_vb_info()
        ret_risky_of_vb:list[int] = []
        for vb_num in range(self.fw_geometry.l52_total_vb_count):
            four_bytes = vb_info[vb_num * 4:(vb_num + 1) * 4]
            integer_value = int.from_bytes(four_bytes, byteorder='little')
            vb_group = integer_value & 0x3F
            access_mode = (integer_value >> 6) & 0x3
            risky_type = (integer_value >> 18) & 0x3
            if risky_type == expect_risky_type:
                logger.info(f'VB {vb_num}, group = {vb_group}, access = {access_mode}, risky type = {risky_type}')
                ret_risky_of_vb.append(vb_num)
        return ret_risky_of_vb

    def list_all_vb_group(self) -> None:
        rsp, vb_info = api.get_vb_info()
        for vb_num in range(self.fw_geometry.l52_total_vb_count):
            four_bytes = vb_info[vb_num * 4:(vb_num + 1) * 4]
            integer_value = int.from_bytes(four_bytes, byteorder='little')
            vb_group = integer_value & 0x3F
            access_mode = (integer_value >> 6) & 0x3
            risky_type = (integer_value >> 18) & 0x3
            logger.info(f'VB {vb_num}, group = {vb_group}, access = {access_mode}, risky type = {risky_type}')

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