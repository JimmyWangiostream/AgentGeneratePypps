import package_root
import time
import struct
from typing import List, cast
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig
from Script.api.ufs_api.descriptors.configuration_desc.functions import print_config, push_write_config
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
#from scriptlib.fw.common import manufacture as mfg

timeout_min = 60

def check_timeout(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False

def get_device_ec() -> bytearray:
    resp, DebugInfo = api.ufs_api.vendor_cmd.get_debug_info()    
    resp, buf = api.ufs_api.vendor_cmd.read_Xmemory(sram_address = DebugInfo.VB_list_cycle_address.value)    
    return buf

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

class Pattern(UFSTC):
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
        
    def pre_process(self) -> None:
        self.param = api.shared.param
        pass

    def step1(self) -> None:

        logger.flow(1, 'Get XTEMP_EC threshold contains XTEMP_EC1 ~ 4 and TempCo Trim for EC1 ~ 4 Group values from pconfig')
        _, pConfig_in_vu = project_api.mconfig_vu.get_pConfig_data()
        XTEMP_EC_value = two_byte_list(pConfig_in_vu.payload.copy(), 28, 35)
        TEMPCO_TRIM_ADDR = two_byte_list(pConfig_in_vu.payload.copy(), 36, 99)
        api.util.dumpfile(filename='XTEMP_EC_value', data=XTEMP_EC_value)
        api.util.dumpfile(filename='TEMPCO_TRIM_ADDR', data=TEMPCO_TRIM_ADDR)
        TEMPCO_TRIM:list[list[int]] = []
        TEMPCO_TRIM.append([])
        for ec in range(4):
            TEMPCO_TRIM.append([])
            TEMPCO_TRIM[ec+1] = list(pConfig_in_vu.payload[100 + (ec * 32): 132 + (ec * 32)])
            api.util.dumpfile(filename=f'EC{ec+1}_TEMPCO_TRIM', data=TEMPCO_TRIM[ec+1])

        logger.flow(2, 'Config LUN0 as normal memory 2GB size')
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x0
        
        for i in range(4): 
            for unit in range(8):
                if (i * 8 + unit) == 0:
                    config_descs[i].units[unit].b0_lu_enable = 1
                    config_descs[i].units[unit].b3_memory_type = 0
                    config_descs[i].units[unit].l4_num_alloc_units = 0x200
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                else:
                    config_descs[i].units[unit].b0_lu_enable = 0
                    config_descs[i].units[unit].l4_num_alloc_units = 0
            if i == 3:
                config_descs[i].header.b2_conf_desc_continue = 0
            else:
                config_descs[i].header.b2_conf_desc_continue = 1
            push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        self.update_unit_desc()

        logger.flow(3, 'Issue VU 0x4084 to get NAND trim values and backup ec table for recovery and verify current trim values')
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
        TEMPCO_TRIM[0] = defaultlist

        fw_geometry = api.ufs_api.vendor_cmd.get_fw_geometry()
        logger.info(f'FW geometry d2d3 avg ec = {fw_geometry.l4180_d2d3_avg_erase_cnt}')
        mlc_avg_ec = fw_geometry.l4180_d2d3_avg_erase_cnt
        for XTEMP_EC in range(3,-1,-1):
            if mlc_avg_ec >= XTEMP_EC_value[XTEMP_EC]:
                if defaultlist != TEMPCO_TRIM[XTEMP_EC+1][0:24]:
                    logger.error(f'default mlc avg ec = {mlc_avg_ec}, EC{XTEMP_EC+1}_TEMPCO_TRIM compare failure')
                    recover_ec(backup_ec=backup_ec_value)
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                break

        testcase = 1
        for XTEMP_EC in range(4):
            logger.flow(4, f'Set all MLC block ec as XTEMP_EC{XTEMP_EC + 1} value - 1 = {XTEMP_EC_value[XTEMP_EC] - 1}')
            set_device_ec(XTEMP_EC_value[XTEMP_EC] - 1)
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)        

            logger.flow(5, f'Issue VU 0x4084 to get NAND trim values, it should be same as TempCo Trim for EC{XTEMP_EC} (0 means default)')
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

            if currentlist != TEMPCO_TRIM[XTEMP_EC][0:24] and XTEMP_EC != 0:
                logger.error(f'EC{XTEMP_EC}_TEMPCO_TRIM compare failure')
                recover_ec(backup_ec=backup_ec_value)
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            logger.flow(6, 'Get MLC average ec should be same as step3')
            fw_geometry = api.ufs_api.vendor_cmd.get_fw_geometry()
            logger.info(f'FW geometry d2d3 avg ec = {fw_geometry.l4180_d2d3_avg_erase_cnt}, set ec value = {XTEMP_EC_value[XTEMP_EC] - 1}')
            if fw_geometry.l4180_d2d3_avg_erase_cnt != XTEMP_EC_value[XTEMP_EC] - 1:
                logger.error(f'The FW geometry d2d3 avg ec = {fw_geometry.l4180_d2d3_avg_erase_cnt} is not same as set ec value = {XTEMP_EC_value[XTEMP_EC] - 1}')
                recover_ec(backup_ec=backup_ec_value)
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            logger.flow(7, f'Random write operation for trigger reach threshold = {XTEMP_EC_value[XTEMP_EC]}')
            write_record = api.get_empty_write_record()
            start_time = time.time()
            while True:
                if check_timeout(start_time, timeout_min):
                    recover_ec(backup_ec=backup_ec_value)
                    raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
                cmd_count = 200
                min_lun = 0
                max_lun = 0
                min_lba = 0
                max_lba = self.param.gLUCapacity[0]
                min_size = api.BLOCK4K_SIZE_64M_BYTE
                max_size = api.BLOCK4K_SIZE_128M_BYTE
                api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)
            
                fw_geometry = api.ufs_api.vendor_cmd.get_fw_geometry()
                logger.info(f'FW geometry d2d3 avg ec = {fw_geometry.l4180_d2d3_avg_erase_cnt}')
                if fw_geometry.l4180_d2d3_avg_erase_cnt == XTEMP_EC_value[XTEMP_EC]:
                    break

            logger.flow(8, f'Issue VU 0x4084 to get NAND trim values, it should be same as TempCo Trim for EC{XTEMP_EC+1}')
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

            api.util.dumpfile(filename=f'TESTCASE{testcase}_CURRENT_TRIM_VALUE_WITH_XTEMP_EC{XTEMP_EC+1}({XTEMP_EC_value[XTEMP_EC]})', data=currentlist)
            testcase += 1
            if currentlist != TEMPCO_TRIM[XTEMP_EC + 1][0:24]:
                logger.error(f'EC{XTEMP_EC + 1}_TEMPCO_TRIM compare failure')
                recover_ec(backup_ec=backup_ec_value)
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(9, 'Recover ec')
        recover_ec(backup_ec=backup_ec_value)
        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()