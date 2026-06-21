from copy import deepcopy

import package_root
import time
import struct
from typing import List, cast
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.api.ufs_api.descriptors.configuration_desc.functions import print_config, push_write_config
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
#from scriptlib.fw.common import manufacture as mfg

timeout_min = 15
_param = api.shared.param

class VB_group_for_list(api.Enum):
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

def check_timeout(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False

def calculate_by_vb_list() -> bytearray:
    resp, vb_info = api.ufs_api.vendor_cmd.get_vb_info()
    fw_geometry = api.ufs_api.vendor_cmd.get_fw_geometry()
    total_VB_count = fw_geometry.l52_total_vb_count
    vb_group_counts: dict[int, dict[int, int]] = {i: {0: 0, 1: 0} for i in range(64)}
    vb_group_indices: dict[int, dict[int, list[int]]] = {i: {0: [], 1: []} for i in range(64)}

    for i in range(total_VB_count):
        four_bytes = vb_info[i * 4:(i + 1) * 4]
        integer_value = int.from_bytes(four_bytes, byteorder='little')
        vb_group = integer_value & 0x3F
        access_mode = (integer_value >> 6) & 0x3
        logger.info(f'VB {i}, group = {vb_group}, access = {access_mode}')
        
        if vb_group in [member.value for member in VB_group_for_list]:
            vb_group_counts[vb_group][access_mode] += 1
            vb_group_indices[vb_group][access_mode].append(i)

    result_list: list[int] = []
    for vb_group in range(64):
        if vb_group in [member.value for member in VB_group_for_list]:
            if vb_group == 0x07 or vb_group == 0x11 or vb_group == 0x13:
                if vb_group_counts[vb_group][1] > 0:
                    result_list.append(vb_group_counts[vb_group][1])
                    result_list.extend(vb_group_indices[vb_group][1])
                    logger.info(f'VB group = {vb_group}, access = 1 count = {vb_group_counts[vb_group][1]}')
                else:
                    result_list.append(0)
                    logger.info(f'VB group = {vb_group}, access = 1 count = 0')
            
                if vb_group_counts[vb_group][0] > 0:
                    result_list.append(vb_group_counts[vb_group][0])
                    result_list.extend(vb_group_indices[vb_group][0])
                    logger.info(f'VB group = {vb_group}, access = 0 count = {vb_group_counts[vb_group][0]}')
                else:
                    result_list.append(0)
                    logger.info(f'VB group = {vb_group}, access = 0 count = 0')
            elif vb_group == 0x1B:
                result_list.append(vb_group_counts[vb_group][1]+ vb_group_counts[vb_group][0])
                if vb_group_counts[vb_group][1] > 0:
                    result_list.extend(vb_group_indices[vb_group][1])
                if vb_group_counts[vb_group][0] > 0:
                    result_list.extend(vb_group_indices[vb_group][0])
                logger.info(f'VB group = {vb_group}, access = n, count = {vb_group_counts[vb_group][1]+ vb_group_counts[vb_group][0]}')
            elif vb_group_counts[vb_group][1] > 0:
                result_list.append(vb_group_counts[vb_group][1])
                result_list.extend(vb_group_indices[vb_group][1])
                logger.info(f'VB group = {vb_group}, access = 1 count = {vb_group_counts[vb_group][1]}')
            elif vb_group_counts[vb_group][0] > 0:
                result_list.append(vb_group_counts[vb_group][0])
                result_list.extend(vb_group_indices[vb_group][0])
                logger.info(f'VB group = {vb_group}, access = 0 count = {vb_group_counts[vb_group][0]}')
            else: 
                result_list.append(0)
                logger.info(f'VB group = {vb_group}, access = n, count = 0')

    result_bytearray = bytearray()
    for value in result_list:
        result_bytearray.extend(value.to_bytes(2, byteorder='little'))

    sorted_bytearray = sort_vb_info(result_bytearray)
    return sorted_bytearray

def sort_vb_info(vb_info: bytearray) -> bytearray:
    result_bytearray = bytearray()
    index = 0
    
    while index < len(vb_info):
        count = int.from_bytes(vb_info[index:index+2], byteorder='little')
        index += 2
        
        info_list = []
        for _ in range(count):
            info = int.from_bytes(vb_info[index:index+2], byteorder='little')
            info_list.append(info)
            index += 2
        info_list.sort()
        
        result_bytearray.extend(count.to_bytes(2, byteorder='little'))
        for info in info_list:
            result_bytearray.extend(info.to_bytes(2, byteorder='little'))
    
    return result_bytearray

def get_sorted_VB_list_from_VU_406D() -> bytearray:
    resp = project_api.custom_vu.issue_406D_get_VB_list_info()
    api.util.dumpfile(filename = 'VB_list_info_fromVU', data = resp.data)
    sorted_vb_list = sort_vb_info(resp.data)
    api.util.dumpfile(filename = 'VB_list_info_fromVU_sorted', data=sorted_vb_list)
    return sorted_vb_list

class Pattern(UFSTC):
    def config_precondition(self) -> None:
        config_descs = api.get_config_descriptors(print=True)
        self.backup_setting = deepcopy(config_descs)
        config_descs[0].header.b17_write_booster_buffer_type = 1
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x400
        for i in range(4): 
            for unit in range(8):
                config_descs[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                if (i * 8 + unit) == 0:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[i].units[unit].l4_num_alloc_units = self.total_au >> 1
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                elif (i * 8 + unit) == 1:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[i].units[unit].l4_num_alloc_units = self.total_au >> 1
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                else:
                    config_descs[i].units[unit].b0_lu_enable = api.LUNEnable.DISABLE
                    config_descs[i].units[unit].l4_num_alloc_units = 0
            config_descs[i].header.b2_conf_desc_continue = 0 if i == 3 else 1
            push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()

    def re_config(self) -> None:
        for i in range(4):
            self.backup_setting[i].header.b2_conf_desc_continue = 0 if i == 3 else 1
            api.push_write_config(self.backup_setting[i], index=i) 
        ExecuteCMD.send()

    def update_unit_desc(self) -> None:
        unit_desc_idxes:List[int] = []
        for lun in range(_param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

    def pre_process(self) -> None:
        self.total_au = int(_param.gGeometry.q4_total_raw_device_capacity / (_param.gGeometry.l13_segment_size * _param.gGeometry.b17_allocation_unit_size))
        pass

    def step1(self) -> None:
        logger.flow(1, 'Modify HW setting to for suspend disabled')
        self.hw_setting = api.HwSetting.get_instance()
        self.power_saving_ctrl_backup = self.hw_setting.get_local_val(api.HwSettingField.POWER_SAVING_CTRL_ENABLE)
        self.hw_setting.set_to_device(field = api.HwSettingField.POWER_SAVING_CTRL_ENABLE, val= 0x3A)

        logger.flow(2, 'Host Issue VU 0x406D to get VB list')
        sorted_vb_list_from_VU = get_sorted_VB_list_from_VU_406D()

        logger.flow(3, 'Dump vb info and calculate with data for verification')
        data_from_vb_info = bytearray(b'\x00' * 0x1000)
        buf = calculate_by_vb_list()
        data_from_vb_info[:len(buf)] = buf
        api.util.dumpfile(filename = 'Calculate_by_vb_info', data = data_from_vb_info)

        if sorted_vb_list_from_VU != data_from_vb_info:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(4, 'Config multi LU and WB')
        self.config_precondition()
        self.update_unit_desc()

        logger.flow(5, 'Host Issue VU 0x406D to get VB list after config multi LU and WB')
        sorted_vb_list_from_VU = get_sorted_VB_list_from_VU_406D()

        logger.flow(6, 'Dump vb info and calculate with data for verification')
        data_from_vb_info = bytearray(b'\x00' * 0x1000)
        buf = calculate_by_vb_list()
        data_from_vb_info[:len(buf)] = buf
        api.util.dumpfile(filename = 'Calculate_by_vb_info', data = data_from_vb_info)

        if sorted_vb_list_from_VU != data_from_vb_info:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(7, 'Enable WB and random write for filling WB buffer')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        write_record = api.get_empty_write_record()
        start_time = time.time()
        while True:
            if check_timeout(start_time, timeout_min):
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            cmd_count = random.randint(10, 32)
            min_lun = 0
            max_lun = 1
            min_lba = 0
            max_lba = _param.gLUCapacity[0]
            min_size = api.BLOCK4K_SIZE_64M_BYTE
            max_size = api.BLOCK4K_SIZE_128M_BYTE
            api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)
            
            ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
            logger.info(f'Available WB size = {ava_WB_size}')
            if ava_WB_size == 0x0:
                break

        logger.flow(8, 'Host Issue VU 0x406D to get VB list after write for filling WB buffer')
        sorted_vb_list_from_VU = get_sorted_VB_list_from_VU_406D()

        logger.flow(9, 'Dump vb info and calculate with data for verification')
        data_from_vb_info = bytearray(b'\x00' * 0x1000)
        buf = calculate_by_vb_list()
        data_from_vb_info[:len(buf)] = buf
        api.util.dumpfile(filename = 'Calculate_by_vb_info', data = data_from_vb_info)

        if sorted_vb_list_from_VU != data_from_vb_info:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(10, 'Enable WB flush and polling available WB size = 0xA and WB flush status = 03h:completed')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)
        start_time = time.time()
        while True:
            if check_timeout(start_time, timeout_min):
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            WB_flush_status = api.read_attribute(idn=api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS)
            ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
            logger.info(f'WB flush status = {WB_flush_status}, Available WB size = {ava_WB_size}')
            if ava_WB_size == 0xA and WB_flush_status == api.WriteBoosterBufferFlushStatus.COMPLETED:
                break

        logger.flow(11, 'Idle 30s for device stablize')
        time.sleep(30)

        logger.flow(12, 'Host Issue VU 0x406D to get VB list after WB buffer flush completed')
        sorted_vb_list_from_VU = get_sorted_VB_list_from_VU_406D()

        logger.flow(13, 'Dump vb info and calculate with data for verification')
        data_from_vb_info = bytearray(b'\x00' * 0x1000)
        buf = calculate_by_vb_list()
        data_from_vb_info[:len(buf)] = buf
        api.util.dumpfile(filename = 'Calculate_by_vb_info', data = data_from_vb_info)

        if sorted_vb_list_from_VU != data_from_vb_info:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        pass

    def post_process(self) -> None:
        self.hw_setting.set_to_device(field = api.HwSettingField.POWER_SAVING_CTRL_ENABLE, val=self.power_saving_ctrl_backup)
        self.re_config()
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()