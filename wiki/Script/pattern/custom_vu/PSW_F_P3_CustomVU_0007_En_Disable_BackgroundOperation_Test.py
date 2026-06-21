from enum import IntEnum

import package_root
import time
from typing import Dict, List, cast
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.ufs_api.descriptors.configuration_desc.functions import print_config, push_write_config
from Script.lib.sdk_lib.user.exception import G_TIMEOUT_ALL
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.project_api.functions import print_object_info_ai

class Access_Mode(int):
    ACCESS_MODE_SLC = 0
    ACCESS_MODE_MLC = 1

class VB_group(int):
    USED_BLK_POOL_MLC = 0x11
    FREE_BLK_QUEUE_MLC = 0X1B
class Trigger_Case(IntEnum):
    is_cold = 0
    is_prior_round = 1
    is_MAX_VALUE = 2
class GC_pool(IntEnum):
    Static = 1
    Dynamic = 2
class ThresholdCase(IntEnum):
    TH1 = 0
    TH2 = 1

def check_timeout(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = api.shared.param
        self._fw_geometry = api.get_fw_geometry()
        self.MAX_VALUE = {GC_pool.Static: 0x7FFF, GC_pool.Dynamic: 0x7FFF}
        self.write_record = api.get_empty_write_record()
        pass

    def get_vb_group_list(self, tlc_used_VB_list:list[int], tlc_free_VB_list:list[int]) -> None:
        resp, vb_info = api.ufs_api.vendor_cmd.get_vb_info()
        total_VB_count = self._fw_geometry.l52_total_vb_count
        for i in range(total_VB_count):
            four_bytes = vb_info[i * 4:(i + 1) * 4]
            integer_value = int.from_bytes(four_bytes, byteorder='little')
            vb_group = integer_value & 0x3F
            logger.info(f'VB {i}, group = {vb_group}')
            if vb_group == VB_group.USED_BLK_POOL_MLC:
                tlc_used_VB_list.append(i)
            elif vb_group == VB_group.FREE_BLK_QUEUE_MLC:
                tlc_free_VB_list.append(i)
        logger.info(f'tlc used vb: {tlc_used_VB_list}')
        logger.info(f'tlc free vb: {tlc_free_VB_list}')

    def get_device_ec(self) -> bytearray:
        resp, DebugInfo = api.ufs_api.vendor_cmd.get_debug_info()    
        resp, buffer = api.ufs_api.vendor_cmd.read_Xmemory(sram_address = DebugInfo.VB_list_cycle_address.value)    
        return buffer
    
    def set_ec(self, set_ec:bytearray) -> None:
        total_VB_count = self._fw_geometry.l52_total_vb_count
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

    def leave_inhibition_mode(self) -> None:
        enablelun = 0
        for lunidx in range(0, self._param.gMaxNumberLU):
            if self._param.gUnit[lunidx].b3_lu_enable:
                enablelun = lunidx
                break
        for _ in range(1000+1):
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=enablelun, lba=0, length=1, fua=1)
            ExecuteCMD.enqueue(read10)
        ExecuteCMD.send(timeout=api.UniformTimeout(val=read10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
        pass

    def trigger_WL_GC(self) -> None:
        logger.flow(20, f'HW reset for device pre-condition')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)
        self.leave_inhibition_mode()
        trigger_case = Trigger_Case.is_cold
        threshold_case = ThresholdCase.TH1
        GC_case = project_api.VBListNum.USED_BLK_POOL_TLC

        set_erase_cnt_payload = bytearray(api.DATA_SIZE_4K_BYTE)
        project_api.set_all_VB_erase_count(data_payload=set_erase_cnt_payload, set_in_ram=True)
        logger.info(f'=========== Test GC: USED_BLK_POOL_TLC, trigger_case: is_cold, threshold case: TH1 ===========')
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        logger.flow(21, f'Config device without WB')
        self.config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x0
        for i in range(4):
            self.config_descs[i].header.b2_conf_desc_continue = 1 if i != 3 else 0
            push_write_config(self.config_descs[i], index=i)
        ExecuteCMD.send()
        
        logger.flow(22, f'write to create used VB')
        lba = 0
        chunk_size = api.BLOCK4K_SIZE_128M_BYTE
        new_group = GC_case
        pool = GC_pool.Dynamic
        free_group = project_api.VBListNum.FREE_BLK_QUEUE_TLC
        lun = 0
        vbsize = self._fw_geometry.l88_vb_size_u1 >> 3
        total_size = vbsize * 10
        api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunk_size, fua = 0,
            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        lba += total_size
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            
        logger.flow(23, f'issue 4098 to get WL information')
        self.VB_dict:Dict[project_api.VBListNum, List[int]] = {}
        _, self.wear_leveling_A = project_api.issue_4098_to_get_wear_leveling_information()
        print_object_info_ai(self.wear_leveling_A)
        for vb in range(self._fw_geometry.l52_total_vb_count):
            EC_data = self.wear_leveling_A.EC_data_of_VBs[vb]
            VER_data = self.wear_leveling_A.VER_data_of_VBs[vb]
            logger.info(f'wear_leveling_A VB: {vb}, EC = {EC_data.EC.value} VBListNum = {EC_data.VBListNum.value} ({project_api.VBListNum(EC_data.VBListNum.value).name}), OpenType = {EC_data.OpenVBType.value} ({project_api.OpenVBType(EC_data.OpenVBType.value).name}), Version = {VER_data.version.value}, force_bit = {VER_data.force_bit.value}, IsDfgSrc = {EC_data.IsDfgSrc.value}')
        for vb in range(self._fw_geometry.l52_total_vb_count):
            VBList = self.wear_leveling_A.EC_data_of_VBs[vb].VBListNum.value
            if VBList not in self.VB_dict:
                self.VB_dict[project_api.VBListNum(VBList)] = []
            self.VB_dict[project_api.VBListNum(VBList)].append(vb)
            
        gEC_for_Static_pool = 0
        gEC_for_dynamic_pool = 0
        gEC_for_static_ICS_pool = 0
        gEC_of_Static_pool_for_open = 0
        gEC_of_dynamic_pool_for_open = 0
        gEC_gap_delta_TH1_static = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_static_pool.value
        gEC_gap_delta_TH1_dynamic = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_dynamic_pool.value
        gEC_gap_delta_TH1_ICS = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_ICS_pool.value
        gEC_gap_delta_TH2_static = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_static_pool.value
        gEC_gap_delta_TH2_dynamic = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_dynamic_pool.value
        gEC_gap_delta_TH2_ICS = self.wear_leveling_A.EC_gap_delta_Threshold_TH2_of_ICS_pool.value
        gEC_for_dynamic_pool = self.wear_leveling_A.EC_Threshold_of_dynamic_pool.value + 1
        set_ec = self.wear_leveling_A.EC_gap_delta_Threshold_TH1_of_dynamic_pool.value + 1
        
        logger.flow(24, f'issue C083 to set USED_BLK_POOL_TLC EC = 0 and issue C072 to set static_wear_leveling global EC')
        set_version_dict:Dict[int, int] = {}
        for vb in range(self._fw_geometry.l52_total_vb_count):
            set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (set_ec+1).to_bytes(4, 'little')
            set_version_dict[vb] = 0
        for ListNum, vb_list in self.VB_dict.items():
            if ListNum == GC_case:
                vb = vb_list[0]
                set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (0).to_bytes(4, 'little')
                set_version_dict[vb] = self.wear_leveling_A.globalVersion_of_dynamic_pool.value+1
                source_vb = vb
                temp = self.VB_dict[free_group].copy()
                random.shuffle(temp)
                vb = temp[0]
                set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (set_ec).to_bytes(4, 'little')
                target_vb = vb
                break

        mlc_partition_current_vb_version = self.wear_leveling_A.globalVersion_of_dynamic_pool.value + self.wear_leveling_A.Version_delta_Threshold_of_dynamic_pool.value + 1
        api.set_ftl_version(mlc_partition_current_vb_version = mlc_partition_current_vb_version)
        
        project_api.issue_C072_to_set_static_wear_leveling_EC_gap_threshold(gEC_for_Static_pool, 
                                                                gEC_for_dynamic_pool, 
                                                                gEC_for_static_ICS_pool, 
                                                                gEC_of_Static_pool_for_open, 
                                                                gEC_of_dynamic_pool_for_open,
                                                                gEC_gap_delta_TH1_static,
                                                                gEC_gap_delta_TH1_dynamic,
                                                                gEC_gap_delta_TH1_ICS,
                                                                gEC_gap_delta_TH2_static,
                                                                gEC_gap_delta_TH2_dynamic,
                                                                gEC_gap_delta_TH2_ICS)
        project_api.set_all_VB_erase_count(data_payload=set_erase_cnt_payload, set_in_ram=True)

        _, self.wear_leveling_C = project_api.issue_4098_to_get_wear_leveling_information()
        print_object_info_ai(self.wear_leveling_C)
        logger.info(f'Source VB = {source_vb}, Target VB = {target_vb}')
        for vb in range(self._fw_geometry.l52_total_vb_count):
            EC_data = self.wear_leveling_C.EC_data_of_VBs[vb]
            VER_data = self.wear_leveling_C.VER_data_of_VBs[vb]
            logger.info(f'wear_leveling_C VB: {vb}, EC = {EC_data.EC.value} VBListNum = {EC_data.VBListNum.value} ({project_api.VBListNum(EC_data.VBListNum.value).name}), OpenType = {EC_data.OpenVBType.value} ({project_api.OpenVBType(EC_data.OpenVBType.value).name}), Version = {VER_data.version.value}, force_bit = {VER_data.force_bit.value}, IsDfgSrc = {EC_data.IsDfgSrc.value}')

        logger.flow(25, 'Check BKOPS status should not be 0')
        BKOPS_status_backup = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
        logger.info(f'BKOPS status = {BKOPS_status_backup}')
        if BKOPS_status_backup == 0x0:
                logger.error_lb('Check BKOPS status should not be 0 when WL GC triggered and disable foreground GC')
                logger.error_fp(f'Expect BKOPS status should not be 0 but current value is {BKOPS_status_backup}')
                logger.info('Recover ec')
                self.set_ec(set_ec=self.backup_ec_value)
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def step1(self) -> None:
        #====================normal case====================#
        logger.flow(1, 'Config WB partition')
        self.config_descs = api.get_config_descriptors(print=True)
        self.config_descs[0].header.b2_conf_desc_continue = 1
        self.config_descs[0].header.b17_write_booster_buffer_type = 1
        self.config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
        self.config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x1000

        for i in range(4):
            self.config_descs[i].header.b2_conf_desc_continue = 1 if i != 3 else 0
            push_write_config(self.config_descs[i], index=i)
        ExecuteCMD.send()

        logger.flow(2, 'Enable WB buffer')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)

        logger.flow(3, 'Write for fill WB buffer')
        start_time = time.time()
        timeout_min = 15
        while True:
            ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
            logger.info(f'Available WB size = {ava_WB_size}')
            if ava_WB_size == 0x0:
                break

            if check_timeout(start_time, timeout_min):
                logger.error_lb('Random write for filling WB buffer')
                logger.error_fp(f'Expect available WB size change into 0x0 within {timeout_min}min but current value is 0x{ava_WB_size:02X}')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            cmd_count = random.randint(10, 32)
            min_lun = 0
            max_lun = 0
            min_lba = 0
            max_lba = self._param.gLUCapacity[0]
            min_size = api.BLOCK4K_SIZE_64M_BYTE
            max_size = api.BLOCK4K_SIZE_128M_BYTE
            api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        logger.flow(4, 'Enable WB buffer flush')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)

        logger.flow(5, 'Polling flush status until completed successfully and available WB size should be 0xA, record spending time')
        polling_cnt = 0
        start_time = time.time()
        while True:
            WB_flush_status = api.read_attribute(idn=api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS)
            ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
            polling_cnt += 1
            logger.info(f'WB flush status = {WB_flush_status}, Available WB size = {ava_WB_size}, polling count = {polling_cnt}')
            if WB_flush_status == api.WriteBoosterBufferFlushStatus.COMPLETED:
                break
            
            if check_timeout(start_time, timeout_min):
                logger.error_lb('Enable WB flush when available WB size = 0x0 and polling WB flush status')
                logger.error_fp(f'Expect WB flush status change into 0x3(completed) within {timeout_min}min but current value is 0x{WB_flush_status:02X}')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT

        if ava_WB_size != 0xA:
            logger.error_lb('Check available WB size when WB flush completed')
            logger.error_fp(f'Expect available WB size should be 0xA but current value is 0x{ava_WB_size:02X}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        #====================disable background operation====================#
        logger.flow(6, 'Disable WB buffer flush')
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)

        logger.flow(7, 'Write for fill WB buffer')
        start_time = time.time()
        while True:
            if check_timeout(start_time, timeout_min):
                logger.error_lb('Random write for filling WB buffer')
                logger.error_fp(f'Expect available WB size change into 0x0 within {timeout_min}min but current value is 0x{ava_WB_size:02X}')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            cmd_count = random.randint(10, 32)
            min_lun = 0
            max_lun = 0
            min_lba = 0
            max_lba = self._param.gLUCapacity[0]
            min_size = api.BLOCK4K_SIZE_64M_BYTE
            max_size = api.BLOCK4K_SIZE_128M_BYTE
            api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            
            ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
            logger.info(f'Available WB size = {ava_WB_size}')
            if ava_WB_size == 0:
                break        

        logger.flow(8, 'Enable WB buffer flush')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)
        
        logger.flow(9, 'Host issue VU 0xD0FD with value 0x00-disable all the background operations')
        project_api.issue_D0FD_disable_all_the_background_operations()

        logger.flow(10, 'Polling flush status and available WB size, expect flush status should be in progress and available WB size keep value does not descreased within polling times')
        WB_flush_status_backup = api.read_attribute(idn=api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS)
        ava_WB_size_backup = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
        logger.info(f'WB flush status(backup) = {WB_flush_status_backup}, Available WB size(backup) = {ava_WB_size_backup}, polling count = {polling_cnt}')
        start_time = time.time()
        while True:
            WB_flush_status = api.read_attribute(idn=api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS)
            ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
            polling_cnt -= 1
            logger.info(f'WB flush status = {WB_flush_status}, Available WB size = {ava_WB_size}, polling count = {polling_cnt}')
            if WB_flush_status_backup != WB_flush_status or ava_WB_size_backup != ava_WB_size:
                logger.error_lb('Enable WB flush when available WB size = 0x0 and polling WB flush status with all the background operations disabled')
                logger.error_fp(f'Expect available WB size keep 0x{ava_WB_size_backup:02X} and WB flush status keep 0x{WB_flush_status_backup:02X}, but current available WB size = 0x{ava_WB_size:02X} and WB flush status = 0x{WB_flush_status:02X}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if polling_cnt == 0:
                break

        #====================enable background operation====================#
        logger.flow(11, 'Host issue VU 0xD0FD with value 0x01-enable all the background operations')
        project_api.issue_D0FD_enable_all_the_background_operations()

        logger.flow(12, 'Polling flush status until completed successfully and available WB size should be 0xA')
        start_time = time.time()
        while True:
            if check_timeout(start_time, timeout_min):
                logger.error_lb('Enable all the background operation and polling WB flush status')
                logger.error_fp(f'Expect WB flush status change into 0x3(completed) within {timeout_min}min but current value is 0x{WB_flush_status:02X}')                
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            WB_flush_status = api.read_attribute(idn=api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS)
            ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
            logger.info(f'WB flush status = {WB_flush_status}, Available WB size = {ava_WB_size}')
            if WB_flush_status == api.WriteBoosterBufferFlushStatus.COMPLETED:
                break

        if ava_WB_size != 0xA:
            logger.error_lb('Check available WB size when WB flush completed')
            logger.error_fp(f'Expect available WB size should be 0xA but current value is 0x{ava_WB_size:02X}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        #====================VU disable background operation with powercycle reset====================#
        logger.flow(13, 'Host issue VU 0xD0FD with value 0x00-disable all the background operations')
        project_api.issue_D0FD_disable_all_the_background_operations()

        logger.flow(14, 'HW reset')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)

        logger.flow(15, 'Enable WB buffer')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)

        logger.flow(16, 'Write for fill WB buffer')
        start_time = time.time()
        while True:
            if check_timeout(start_time, timeout_min):
                logger.error_lb('Random write for filling WB buffer')
                logger.error_fp(f'Expect available WB size change into 0x0 within {timeout_min}min but current value is 0x{ava_WB_size:02X}')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            cmd_count = random.randint(10, 32)
            min_lun = 0
            max_lun = 0
            min_lba = 0
            max_lba = self._param.gLUCapacity[0]
            min_size = api.BLOCK4K_SIZE_64M_BYTE
            max_size = api.BLOCK4K_SIZE_128M_BYTE
            api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            
            ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
            logger.info(f'Available WB size = {ava_WB_size}')
            if ava_WB_size == 0:
                break              

        logger.flow(17, 'Enable WB buffer flush')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)

        logger.flow(18, 'Polling flush status until completed successfully and available WB size should be 0xA')
        start_time = time.time()
        while True:
            if check_timeout(start_time, timeout_min):
                logger.error_lb('Enable WB flush when available WB size = 0x0 and polling WB flush status')
                logger.error_fp(f'Expect WB flush status change into 0x3(completed) within {timeout_min}min but current value is 0x{WB_flush_status:02X}')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            WB_flush_status = api.read_attribute(idn=api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS)
            ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
            logger.info(f'WB flush status = {WB_flush_status}, Available WB size = {ava_WB_size}')
            if WB_flush_status == api.WriteBoosterBufferFlushStatus.COMPLETED:
                break

        if ava_WB_size != 0xA:
            logger.error_lb('Check available WB size when WB flush completed')
            logger.error_fp(f'Expect available WB size should be 0xA but current value is 0x{ava_WB_size:02X}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        #====================VU disable foreground operation====================#
        logger.flow(19, 'Get current vb erase count table and backup')
        self.backup_ec_value = self.get_device_ec()
        dumpfile(filename='backup_ec_value', data=self.backup_ec_value)

        for disable_FG_GC_case in range(2):
            self.trigger_WL_GC()

            logger.flow(26, 'Host issue VU 0xD0FD with value 0x02-disable all the foreground operations')
            project_api.issue_D0FD_disable_all_the_foreground_operations()

            logger.flow(27, 'Check BKOPS status should not be 0 and polling BKOPS status 1 min should keep value')
            BKOPS_status_backup = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
            logger.info(f'BKOPS status = {BKOPS_status_backup}')
            if BKOPS_status_backup == 0x0:
                logger.error_lb('Check BKOPS status should not be 0 when WL GC triggered and disable foreground GC')
                logger.error_fp(f'Expect BKOPS status should not be 0 but current value is {BKOPS_status_backup}')
                logger.info('Recover ec')
                self.set_ec(set_ec=self.backup_ec_value)
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            start_time = time.time()
            while True:
                if check_timeout(start_time, 1):
                    break
                BKOPS_status = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
                logger.info(f'BKOPS status = {BKOPS_status}')
                if BKOPS_status != BKOPS_status_backup:
                    logger.error_lb('Check BKOPS should keep value when foreground GC disabled')
                    logger.error_fp(f'Expect BKOPS status should be {BKOPS_status_backup} but current value is {BKOPS_status}')
                    logger.info('Recover ec')
                    self.set_ec(set_ec=self.backup_ec_value)
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            if disable_FG_GC_case == 0:
                logger.flow(28, 'Host issue VU 0xD0FD with value 0x03-enable all the foreground operations')
                project_api.issue_D0FD_enable_all_the_foreground_operations()
            else:
                logger.flow(28, 'HW reset to reset foreground operations as enabled')
                api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = False)

            logger.flow(29, 'Polling BKOPS status should change into 0 within 1 min')
            start_time = time.time()
            while True:
                if check_timeout(start_time, 1):
                    logger.error_lb('Check BKOPS should change into 0 when foreground GC enabled')
                    logger.error_fp(f'Expect BKOPS status should be 0 within 1 min but current value is {BKOPS_status}')
                    logger.info('Recover ec')
                    self.set_ec(set_ec=self.backup_ec_value)
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                BKOPS_status = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
                logger.info(f'BKOPS status = {BKOPS_status}')
                if BKOPS_status == 0:
                    break

            logger.flow(30, 'Recover ec and HW reset')
            self.set_ec(set_ec=self.backup_ec_value)
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)

        #====================VU disable BG trim====================#

        logger.flow(31, 'Random write some data')
        cmd_count = 100
        min_lun = 0
        max_lun = 0
        min_lba = 0
        max_lba = self._param.gLUCapacity[0]
        min_size = api.BLOCK4K_SIZE_64M_BYTE
        max_size = api.BLOCK4K_SIZE_128M_BYTE
        api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        logger.flow(32, 'disable BG trim')
        project_api.issue_D0FD_disable_BG_trim()

        try:
            logger.flow(33, 'Format unit and expected timeout occur, device shall stuck')
            ExecuteCMD.FormatUnit().assign(lun=0).enqueue()
            ExecuteCMD.send()
            logger.error_lb('Issue format unit after VU disable BG trim')
            logger.error_fp('Expected timeout occur, device shall stuck but response is success')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        except G_TIMEOUT_ALL:
            ExecuteCMD.clear()

        logger.flow(34, 'HW reset to reset foreground operations as enabled')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = False)

        logger.flow(35, 'Format unit and device response shall be success')
        ExecuteCMD.FormatUnit().assign(lun=0).enqueue()
        ExecuteCMD.send()

        logger.flow(36, 'Random write some data')
        cmd_count = 100
        min_lun = 0
        max_lun = 0
        min_lba = 0
        max_lba = self._param.gLUCapacity[0]
        min_size = api.BLOCK4K_SIZE_64M_BYTE
        max_size = api.BLOCK4K_SIZE_128M_BYTE
        api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        logger.flow(37, 'disable BG trim')
        project_api.issue_D0FD_disable_BG_trim()

        logger.flow(38, 'enable BG trim')
        project_api.issue_D0FD_enable_BG_trim()

        logger.flow(39, 'Format unit and device response shall be success')
        ExecuteCMD.FormatUnit().assign(lun=0).enqueue()
        ExecuteCMD.send()

        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()