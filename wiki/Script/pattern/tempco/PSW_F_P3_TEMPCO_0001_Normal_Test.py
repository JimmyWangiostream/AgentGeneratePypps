import package_root
import time
import struct
from typing import cast
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig
from Script.api.ufs_api.descriptors.configuration_desc.functions import print_config, push_write_config
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.lib import sdk_lib as lib
import random
from Script.api.exception import *
#from scriptlib.fw.common import manufacture as mfg
_sdk = api.shared.sdk

timeout_min = 15
total_VB_count = 0

def check_timeout(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False

def get_device_ec() -> bytearray:
    resp, DebugInfo = api.ufs_api.vendor_cmd.get_debug_info()    
    resp, buffer = api.ufs_api.vendor_cmd.read_Xmemory(sram_address = DebugInfo.VB_list_cycle_address.value)    
    return buffer

def set_device_ec(set_EC_value: int) -> None:
    fw_geometry = api.ufs_api.vendor_cmd.get_fw_geometry()
    total_VB_count = fw_geometry.l52_total_vb_count
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

def recover_ec(backup_ec:bytearray) -> None:
    fw_geometry = api.ufs_api.vendor_cmd.get_fw_geometry()
    total_VB_count = fw_geometry.l52_total_vb_count
    data = bytearray(b'\xFF' * 0x4000)
    del backup_ec[total_VB_count*4:]
    data[:len(backup_ec)] = backup_ec

    api.ufs_api.vendor_cmd.access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdWrite()
    vuc.assign(length=api.DATA_SIZE_16K_BYTE, cmd_index=api.VendorCmd.GET_FW_GEOMETRY, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = api.VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b6_cmd2 = 4
    vuc.data = data
    vuc.enqueue()
    ExecuteCMD.send()

def two_byte_list(buf: bytearray, start_pos:int, end_pos:int ) -> list[int]:
    num_pairs = int((end_pos + 1 - start_pos) / 2)
    sliced_data = buf[start_pos:end_pos + 1]
    format_string = f'<{num_pairs}H'
    return list(struct.unpack(format_string, sliced_data))

def VCC_power_off_power_on() -> None:
    logger.info('VCC_power_off_power_on')
    _sdk.power_control(on_off_value=lib.Power_Control.POWER_OFF.value, channel_sel=lib.Power_Channel.POWER_CHANNEL_VCC.value)
    _sdk.power_control(on_off_value=lib.Power_Control.POWER_ON.value, channel_sel=lib.Power_Channel.POWER_CHANNEL_VCC.value)

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        global total_VB_count
        total_VB_count = int(api.shared.param.gGeometry.q4_total_raw_device_capacity / (api.shared.param.gGeometry.l13_segment_size * api.shared.param.gGeometry.b17_allocation_unit_size))

        logger.flow(1, 'Get XTEMP_EC threshold contains XTEMP_EC1 ~ 4 and TempCo Trim for EC1 ~ 4 Group values from pconfig')
        _, pConfig_in_vu = project_api.mconfig_vu.get_pConfig_data()
        XTEMP_EC_value = two_byte_list(pConfig_in_vu.payload.copy(), 28, 35)
        TEMPCO_TRIM_ADDR = two_byte_list(pConfig_in_vu.payload.copy(), 36, 99)
        api.util.dumpfile(filename='XTEMP_EC_value', data=XTEMP_EC_value)
        api.util.dumpfile(filename='TEMPCO_TRIM_ADDR', data=TEMPCO_TRIM_ADDR)
        TEMPCO_TRIM:list[list[int]] = []
        for ec in range(4):
            TEMPCO_TRIM.append([])
            TEMPCO_TRIM[ec] = list(pConfig_in_vu.payload[100 + (ec * 32): 132 + (ec * 32)])
            api.util.dumpfile(filename=f'EC{ec+1}_TEMPCO_TRIM', data=TEMPCO_TRIM[ec])

        logger.flow(2, 'Issue VU 0x4084 to get NAND trim values and backup ec table for recovery and verify current trim values')
        backup_ec_value = get_device_ec()
        
        default = {}
        defaultlist:list[int] =[]
        for set in range(6):
            start_pos = set * 4
            end_pos = start_pos + 4
            get_trim_addr = TEMPCO_TRIM_ADDR[start_pos:end_pos]
            _, get_trim = project_api.issue_4084_to_get_NAND_trim(target_addr=get_trim_addr)
            for addr, item in zip(get_trim_addr, get_trim.TrimValue):
                default[addr]= item.value
                defaultlist.append(item.value)
        api.util.dumpfile(filename='defaulttrimlist', data=defaultlist)

        fw_geometry = api.ufs_api.vendor_cmd.get_fw_geometry()
        logger.info(f'FW geometry d2d3 avg ec = {fw_geometry.l4180_d2d3_avg_erase_cnt}')
        mlc_avg_ec = fw_geometry.l4180_d2d3_avg_erase_cnt
        for XTEMP_EC in range(3,-1,-1):
            if mlc_avg_ec >= XTEMP_EC_value[XTEMP_EC]:
                if defaultlist != TEMPCO_TRIM[XTEMP_EC][0:24]:
                    logger.error(f'default mlc avg ec = {mlc_avg_ec}, EC{XTEMP_EC + 1}_TEMPCO_TRIM compare failure')
                    recover_ec(backup_ec=backup_ec_value)
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                break
        testcase = 1
        for power_cycle_condition in range(2):
            for SSU_condition in range(4):
                for XTEMP_EC in range(4):
                    logger.flow(3, f'Set all MLC block ec as XTEMP_EC{XTEMP_EC + 1} value = {XTEMP_EC_value[XTEMP_EC]}')
                    set_device_ec(XTEMP_EC_value[XTEMP_EC])

                    logger.flow(4, 'trigger power cycle (POR/SPOR) event')
                    if power_cycle_condition == 0:
                        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)
                    elif power_cycle_condition == 1:
                        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = False)

                    logger.flow(5, 'Get MLC average ec should be same as step3')
                    fw_geometry = api.ufs_api.vendor_cmd.get_fw_geometry()
                    logger.info(f'FW geometry d2d3 avg ec = {fw_geometry.l4180_d2d3_avg_erase_cnt}, set ec value = {XTEMP_EC_value[XTEMP_EC]}')
                    if fw_geometry.l4180_d2d3_avg_erase_cnt != XTEMP_EC_value[XTEMP_EC]:
                        logger.error(f'The FW geometry d2d3 avg ec = {fw_geometry.l4180_d2d3_avg_erase_cnt} is not same as set ec value = {XTEMP_EC_value[XTEMP_EC]}')
                        recover_ec(backup_ec=backup_ec_value)
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL

                    logger.flow(6, f'Issue VU 0x4084 to get NAND trim values, it should be same as TempCo Trim for EC{XTEMP_EC}')
                    current_trim = {}
                    currentlist:list[int] = []
                    for set in range(6):
                        start_pos = set * 4
                        end_pos = start_pos + 4
                        get_trim_addr = TEMPCO_TRIM_ADDR[start_pos:end_pos]
                        _, get_trim = project_api.issue_4084_to_get_NAND_trim(target_addr=get_trim_addr)
                        for addr, item in zip(get_trim_addr, get_trim.TrimValue):
                            current_trim[addr]= item.value
                            currentlist.append(item.value)

                    api.util.dumpfile(filename=f'TESTCASE{testcase}_CURRENT_TRIM_VALUE_WITH_XTEMP_EC{XTEMP_EC}({XTEMP_EC_value[XTEMP_EC]})_power_cycle_condition{power_cycle_condition}', data=currentlist)
                    testcase += 1
                    if currentlist != TEMPCO_TRIM[XTEMP_EC][0:24]:
                        logger.error(f'EC{XTEMP_EC + 1}_TEMPCO_TRIM compare failure')
                        recover_ec(backup_ec=backup_ec_value)
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    
                    pc = 2 if SSU_condition == 0 or SSU_condition == 1 else 3
                    pw_on_off = 'with' if SSU_condition == 1 or SSU_condition == 3 else 'without'
                    logger.flow(7, f'Issue SSU powerdown(sleep) with(out) VCC off->on, power_condition = {pc} {pw_on_off} VCC power off power on')

                    if SSU_condition == 0 or SSU_condition == 1:
                        SSU = ExecuteCMD.StartStopUnit()
                        SSU.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=pc, no_flush=0,start=0)
                        SSU.set_option(wait_queue_empty=True)
                        ExecuteCMD.enqueue(SSU)
                        ExecuteCMD.send()
                        if SSU_condition == 1:
                            VCC_power_off_power_on()
                        SSU.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=1, no_flush=0,start=0)
                        ExecuteCMD.enqueue(SSU)
                        ExecuteCMD.send()
                    elif SSU_condition == 2 or SSU_condition == 3:
                        SSU = ExecuteCMD.StartStopUnit()
                        SSU.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=pc, no_flush=0,start=0)
                        SSU.set_option(wait_queue_empty=True)
                        ExecuteCMD.enqueue(SSU)
                        ExecuteCMD.send()
                        if SSU_condition == 3:
                            VCC_power_off_power_on()
                        SSU.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=1, no_flush=0,start=0)
                        ExecuteCMD.enqueue(SSU)
                        ExecuteCMD.send()
                    
                    logger.flow(8, f'Issue VU 0x4084 to get NAND trim values after SSU operation, it should be same as TempCo Trim for EC{XTEMP_EC}')
                    current_trim = {}
                    currentlist:list[int] = []
                    for set in range(6):
                        start_pos = set * 4
                        end_pos = start_pos + 4
                        get_trim_addr = TEMPCO_TRIM_ADDR[start_pos:end_pos]
                        _, get_trim = project_api.issue_4084_to_get_NAND_trim(target_addr=get_trim_addr)
                        for addr, item in zip(get_trim_addr, get_trim.TrimValue):
                            current_trim[addr]= item.value
                            currentlist.append(item.value)

                    api.util.dumpfile(filename=f'TESTCASE{testcase}_CURRENT_TRIM_VALUE_WITH_XTEMP_EC{XTEMP_EC}({XTEMP_EC_value[XTEMP_EC]})_SSU_condition{SSU_condition}', data=currentlist)
                    testcase += 1
                    if currentlist != TEMPCO_TRIM[XTEMP_EC][0:24]:
                        logger.error(f'EC{XTEMP_EC + 1}_TEMPCO_TRIM compare failure')
                        recover_ec(backup_ec=backup_ec_value)
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(9, 'Recover ec and POR to verify NAND trim values should be default values')
        recover_ec(backup_ec=backup_ec_value)
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)
        current_trim = {}
        currentlist = []
        for set in range(6):
            start_pos = set * 4
            end_pos = start_pos + 4
            get_trim_addr = TEMPCO_TRIM_ADDR[start_pos:end_pos]
            _, get_trim = project_api.issue_4084_to_get_NAND_trim(target_addr=get_trim_addr)
            for addr, item in zip(get_trim_addr, get_trim.TrimValue):
                current_trim[addr]= item.value
                currentlist.append(item.value)

        api.util.dumpfile(filename=f'NANA_TRIM_VALUES_AFTER_DEVICE_RECOVER_EC', data=currentlist)
        if currentlist != defaultlist:
            logger.error(f'Nand trim values after recover ec is not same as default values')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()