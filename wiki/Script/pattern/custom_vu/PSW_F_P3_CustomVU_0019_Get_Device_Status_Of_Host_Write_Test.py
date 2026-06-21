import package_root
import time
import copy
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

TLC_Max_PEC = 3000
timeout_min = 15

class Access_Mode(int):
    ACCESS_MODE_SLC = 0
    ACCESS_MODE_MLC = 1

def check_timeout(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False

def verify_device_status_of_host_write(expected_value: int) -> None:
    response = project_api.issue_4064_get_device_status_of_host_write()
    device_status = int.from_bytes([response.data[0], response.data[3]], byteorder='little')
    logger.info(f'Device status of host write = {device_status}, expected value = {expected_value}')
    if device_status != expected_value:
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL

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

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        config_descs = api.get_config_descriptors(print=True)
        backup_config_setting = copy.deepcopy(config_descs)
        _param = api.shared.param
        total_au = int(_param.gGeometry.q4_total_raw_device_capacity / (_param.gGeometry.l13_segment_size * _param.gGeometry.b17_allocation_unit_size))
        write_record = api.get_empty_write_record()

        
        #====================VC1====================#
        logger.flow(1, 'Host issue VU 0x4064 to get device status of host write after device init, the value should be 2:sustain')
        verify_device_status_of_host_write(0x2)
        
        #====================VC2====================#        
        logger.flow(2, 'Config with WB partition')
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.b2_conf_desc_continue = 0
        config_descs[0].header.b17_write_booster_buffer_type = 1
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x400
        push_write_config(config_descs[0], index=0)
        ExecuteCMD.send()
        
        logger.flow(3, 'Host issue VU 0x4064 to get device status of host write before WB enabled, the value should be 2:sustain')
        verify_device_status_of_host_write(0x2)

        logger.flow(4, 'Enable WB buffer')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)

        logger.flow(5, 'Host issue VU 0x4064 to get device status of host write after WB enabled, the value should be 1:burst')
        verify_device_status_of_host_write(0x1)
        
        #====================VC3====================#
        logger.flow(6, 'Write for fill WB buffer')
        start_time = time.time()
        startLBA = 0
        total_size = api.BLOCK4K_SIZE_1G_BYTE
        while True:
            if check_timeout(start_time, timeout_min):
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT

            api.sequential_write(lun=0, start_lba=startLBA, total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua=0, need_compare=False, compare_method=0, write_record=write_record)
            startLBA += total_size

            ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
            logger.info(f'Available WB size = {ava_WB_size}')
            if ava_WB_size == 0x0:
                break

            if startLBA + total_size > _param.gLUCapacity[0]:
                logger.error(f'Next loop start LBA = {startLBA} with total size = {total_size}, it will be over LU capacity = {_param.gLUCapacity[0]} out of range')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        api.sequential_write(lun=0, start_lba=startLBA, total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua=0, need_compare=False, compare_method=0, write_record=write_record)    
        logger.flow(7, 'Host issue VU 0x4064 to get device status of host write after available WB size is 0x0, the value should be 2:sustain')
        verify_device_status_of_host_write(0x2)
        
        logger.info('Disable WB buffer')
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)

        #====================VC4====================#
        logger.flow(8, 'Config without WB partition')
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.b2_conf_desc_continue = 0
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x0
        push_write_config(config_descs[0], index=0)
        ExecuteCMD.send()
        
        logger.flow(9, 'Get PE_COUNT_THRESHOLD from HW setting for recovery')
        hw_setting = api.HwSetting.get_instance()

        PE_COUNT_THRESHOLD_LSB = hw_setting.get_local_val(field = api.HwSettingField.PE_COUNT_THRESHOLD_LSB)
        PE_COUNT_THRESHOLD_MSB = hw_setting.get_local_val(field = api.HwSettingField.PE_COUNT_THRESHOLD_MSB)
        PE_count_threshold = (PE_COUNT_THRESHOLD_MSB << 8) | PE_COUNT_THRESHOLD_LSB
        logger.info(f'PE_count_threshold = {PE_count_threshold}')

        logger.flow(10, f'Set device EC as PE_count_threshold {PE_count_threshold}')
        backup_ec_value = get_device_ec()
        set_device_ec(set_EC_value = PE_count_threshold)

        logger.flow(11, 'Config with WB partition and check bWriteBoosterbufferLifeTimeEst should be 0xB')
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.b2_conf_desc_continue = 0
        config_descs[0].header.b17_write_booster_buffer_type = 1
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x400
        push_write_config(config_descs[0], index=0)
        ExecuteCMD.send()

        WB_lifetime = api.read_attribute(idn=api.AttributeIDN.WRITEBOOSTER_BUFFER_LIFETIME_EST)
        logger.info(f'WB_lifetime = {WB_lifetime}')
        
        if WB_lifetime != 0xB:
            logger.error(f'WB_lifetime = {WB_lifetime}, expected value is 0xB')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.info('Enable WB buffer')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)

        logger.flow(12, 'Host issue VU 0x4064 to get device status of host write with WB lifetime exceeded, the value should be 2:sustain')
        verify_device_status_of_host_write(0x2)
        
        logger.flow(13, 'Recover ec as backup value')
        recover_ec(backup_ec=backup_ec_value)
        
        #====================VC5====================#
        logger.flow(14, 'Config LUN0 as normal memory and LUN1 as enhanced memory type1 without WB')
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x0
        
        for i in range(4): 
            for unit in range(8):
                if (i * 8 + unit) == 0:
                    config_descs[i].units[unit].b0_lu_enable = 1
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[i].units[unit].l4_num_alloc_units = int(total_au / 2)
                    config_descs[i].units[unit].b9_logical_block_size = 0xc
                elif (i * 8 + unit) == 1:
                    config_descs[i].units[unit].b0_lu_enable = 1
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[i].units[unit].l4_num_alloc_units = int(total_au / 2)
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

        self.unit_desc_idxes:List[int] = []
        for lun in range(0, _param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
            self.unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in self.unit_desc_idxes:
            api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

        logger.flow(15, 'Issue write cmd to LUN1: enhanced memory type1')
        cmd_count = 32
        min_lun = 1
        max_lun = 1
        min_lba = 0
        max_lba = _param.gLUCapacity[1]
        min_size = api.BLOCK4K_SIZE_64M_BYTE
        max_size = api.BLOCK4K_SIZE_128M_BYTE    
        api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)

        logger.flow(16, 'Issue VU 0x4064 to get device status of host write after write cmd to LUN1, the value should be 1:burst')
        verify_device_status_of_host_write(0x1)

        logger.flow(17, 'Issue write cmd to LUN0: normal memory')
        cmd_count = 32
        min_lun = 0
        max_lun = 0
        min_lba = 0
        max_lba = _param.gLUCapacity[0]
        min_size = api.BLOCK4K_SIZE_64M_BYTE
        max_size = api.BLOCK4K_SIZE_128M_BYTE    
        api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)

        logger.flow(18, 'Issue VU 0x4064 to get device status of host write after write cmd to LUN0, the value should be 2:sustain')
        verify_device_status_of_host_write(0x2)

        #====================VC6====================#
        
        logger.flow(19, 'Config default setting')
        for i in range(4):
            backup_config_setting[i].header.b2_conf_desc_continue = 0 if i == 3 else 1
            push_write_config(backup_config_setting[i], index=i)
        ExecuteCMD.send()

        logger.flow(20, 'Random write 5 loop')
        write_record = api.get_empty_write_record()
        for loop in range(5):
            cmd_count = random.randint(10, 32)
            min_lun = 0
            max_lun = 0
            min_lba = 0
            max_lba = _param.gLUCapacity[0]
            min_size = api.BLOCK4K_SIZE_64M_BYTE
            max_size = api.BLOCK4K_SIZE_128M_BYTE     
            api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)        
        
        logger.flow(21, 'Set TLC GC threshold as 10')
        slc_gc_threshold, mlc_gc_threhold = api.ufs_api.vendor_cmd.get_gc_threshold()
        logger.info(f'default mlc_gc_threhold = {mlc_gc_threhold}')
        api.ufs_api.vendor_cmd.set_gc_threshold(Access_Mode.ACCESS_MODE_MLC, 10)

        logger.flow(22, 'Check BKOPS status should be 0x2')
        BKOPSstatus = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
        logger.info(f'BKOPS status = {BKOPSstatus}')
        if BKOPSstatus != 0x2:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(23, 'Host issue VU 0x4064 to get device status of host write after trigger foreground GC, the value should be 3:dirty')
        verify_device_status_of_host_write(0x3)
        
        logger.flow(24, 'Recover mlc gc threshold')
        api.ufs_api.vendor_cmd.set_gc_threshold(Access_Mode.ACCESS_MODE_MLC, mlc_gc_threhold)
        
        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()