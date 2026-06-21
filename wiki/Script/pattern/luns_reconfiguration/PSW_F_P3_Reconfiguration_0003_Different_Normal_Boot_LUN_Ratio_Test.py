from enum import IntEnum
import random
import time
from typing import List, cast
import re
import package_root
from Script import api
from Script import project_api
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api.ffu import codesign_ffu_bin
from Script.api.ufs_api.rw_functions import read_compare
from Script.api.ufs_api.vendor_cmd.structs import FlashSetting
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.lib.sdk_lib.user.exception import DLL_RESPONSE_ERROR
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.api.exception import *
from Script.api.ufs_api.defines.enum_define import *
from Script.api.ufs_api.defines.constant_define import *

_sdk = api.shared.sdk

class EVENT(IntEnum):
    WRITE = 0
    UNMAP = 1
    # FFU = 2
    # PURGE = 3
    READ_COMPARE = 2
    EVENT_CNT = 3
    
class TestCase:
    def __init__(self, name:str, em1_ratio:float, normal_ratio:float, boot_ratio:float):
        self.name = name
        self.em1 = em1_ratio
        self.normal = normal_ratio
        self.boot = boot_ratio

    def __eq__(self, other:object) -> bool:
        if not isinstance(other, TestCase):
            return False
        return (self.em1, self.normal, self.boot) == (other.em1, other.normal, other.boot)
    
    # 關鍵：根據數值產生雜湊值，這樣物件才能被放進 set 中
    def __hash__(self) -> int:
        return hash((self.em1, self.normal, self.boot))

    def __repr__(self) -> str:
        return f'Test Case{self.name} as EM1: {self.em1}%, Normal: {self.normal}%, Boot: {self.boot}%,'

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.param = api.shared.param
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        self.flash_setting = FlashSetting()
        self.flash_setting.from_bytes(self.flash_setting_buffer)
        self.hw_setting = api.HwSetting.get_instance()
        self.hw_setting.update_from_device()
        self.hw_setting.backup()
        _, self.debug_info = api.get_debug_info()
        self.au_size = self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size * 512
        self.total_au_size = int(self.geometry_desc.q4_total_raw_device_capacity / self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size)
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.backup_setting = api.get_config_descriptors(print=False)
        self.TestBootLun = 1
        self.TestNormalLun = 2
        self.TestEM1Lun = 0
        pass

    def step1(self) -> None:
        self.hw_setting.set_to_device(api.HwSettingField.FFU_FEATURE, api.FFUFeature.FFU_SAMVE_SVN_BACKWARD_EN)

        test_cases = self.generate_test_cases()
        logger.info(f'Total test case count = {len(test_cases)}')
        for i, case in enumerate(test_cases):
            self.write_record = api.get_empty_write_record()
            lun_list: List[int] = []
            logger.flow(1, f'Config case {i}: {case}')
            self.config_lun(em1_ratio = case.em1, normal_ratio = case.normal, boot_ratio = case.boot)
            logger.flow(2, f'Random issue SCSI Command with all QD commands')
            self.random_scsi_test([self.TestEM1Lun, self.TestBootLun, self.TestNormalLun])
        pass
    
    def post_process(self) -> None:
        self.hw_setting.recover()
        pass

    def generate_test_cases(self)-> List[TestCase]:
        case_list: List[TestCase]= []

        candidates = [
            TestCase(f"1-1", 100, 0, 0),
            TestCase(f"2-1", 99, 0, 1),
            TestCase(f"3-1", 98, 0, 2),
            TestCase(f"3-1", 98, 1, 1),
        ]
        for case in candidates:
                case_list.append(case)

        for p in reversed(range(90, 98)):
            rem = 100 - p
            candidates = [
                TestCase(f"{rem}-1", p, 0, rem),
                TestCase(f"{rem}-2", p, rem * 0.25, rem * 0.75),
                TestCase(f"{rem}-3", p, rem * 0.5, rem * 0.5),
                TestCase(f"{rem}-4", p, rem * 0.75, rem * 0.25),
            ]

            for case in candidates:
                case_list.append(case)

        for p in random.sample(range(10, 90), 5):
            rem = 100 - p
            candidates = [
                TestCase(f"{rem}-1", p, 0, rem),
                TestCase(f"{rem}-2", p, rem * 0.25, rem * 0.75),
                TestCase(f"{rem}-3", p, rem * 0.5, rem * 0.5),
                TestCase(f"{rem}-4", p, rem * 0.75, rem * 0.25),
            ]
            for case in candidates:
                case_list.append(case)

        for p in reversed(range(0, 10)):
            rem = 100 - p
            candidates = [
                TestCase(f"{rem}-1", p, 0, rem),
                TestCase(f"{rem}-2", p, rem * 0.25, rem * 0.75),
                TestCase(f"{rem}-3", p, rem * 0.5, rem * 0.5),
                TestCase(f"{rem}-4", p, rem * 0.75, rem * 0.25),
            ]
            for case in candidates:
                case_list.append(case)

        return case_list
        # return sorted(list(case_set), key=sort_key)
    
    def config_lun(self, em1_ratio:float, normal_ratio:float, boot_ratio:float) -> None:
        normal_au_size = int(self.total_au_size * normal_ratio//100)
        em1_au_size = int(self.total_au_size * em1_ratio//100)
        em1_au_size = em1_au_size if em1_au_size < self.geometry_desc.l44_enhanced1_max_n_alloc_u else self.geometry_desc.l44_enhanced1_max_n_alloc_u
        boot_au_size = self.total_au_size - normal_au_size - em1_au_size

        config_desc = api.get_config_descriptors(print=True)
        config_desc[0].header.b3_boot_enable = api.BootEnable.BOOT_ENABLE
        config_desc[0].header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE
        config_desc[0].header.b17_write_booster_buffer_type = 1
        config_desc[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
        config_desc[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x400 #4G
        for i in range(4): 
            for unit in range(8):
                LU_number = i * 8 + unit
                if LU_number == self.TestEM1Lun:
                    config_desc[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[i].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[i].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_desc[i].units[unit].l4_num_alloc_units = em1_au_size
                    config_desc[i].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[i].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE 
                elif LU_number == self.TestNormalLun:
                    config_desc[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[i].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[i].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[i].units[unit].l4_num_alloc_units = normal_au_size
                    config_desc[i].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[i].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif LU_number == self.TestBootLun:
                    config_desc[i].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[i].units[unit].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_A
                    config_desc[i].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[i].units[unit].l4_num_alloc_units = boot_au_size
                    config_desc[i].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[i].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                else:
                    config_desc[i].units[unit].b0_lu_enable = 0
                    config_desc[i].units[unit].l4_num_alloc_units = 0

            config_desc[i].header.b2_conf_desc_continue = 0 if i==3 else 1
            push_write_config(config_desc[i], index=i)


        ExecuteCMD.send()

        self.update_unit_desc()
        self.update_device_desc()

        test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
        for lun in range(self.param.gMaxNumberLU):
            if self.param.gUnit[lun].b3_lu_enable != api.LUNEnable.DISABLE:
                test_unit_ready.set_option(lun=lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send()
        api.write_attribute(idn=api.AttributeIDN.BOOT_LUN_EN, val=api.BootLUNID.BOOT_LUN_A)

        logger.info(f'Configuration AU Size: em1:{em1_au_size}, normal:{normal_au_size}, boot:{boot_au_size}')
        logger.info(f'Logical block count: em1:{self.param.gUnit[self.TestEM1Lun].q11_logical_block_count}, normal:{self.param.gUnit[self.TestNormalLun].q11_logical_block_count}, boot:{self.param.gUnit[self.TestBootLun].q11_logical_block_count}')
        pass

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
        pass

    def update_device_desc(self) -> None:
        device_descriptor = ExecuteCMD.ReadDescriptor()
        device_descriptor.assign(idn=api.DescriptorIDN.DEVICE)
        index = ExecuteCMD.enqueue(device_descriptor)
        ExecuteCMD.send(clear_on_success=False)
        api.update_descriptor(idn=api.DescriptorIDN.DEVICE, index=0, response=cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()
        pass

    def check_timeout(self,start_time: float, timeout_sec: int) -> bool:
        current_time = time.time()
        if (current_time - start_time) >= timeout_sec:
            return True
        else:
            return False
    
    def random_scsi_test(self, enable_lun_list:list[int]) -> None:
        event_sequence = [i for i in range(EVENT.EVENT_CNT)]
        random.shuffle(event_sequence)

        for event in event_sequence:
            if event == EVENT.WRITE:
                for lun in enable_lun_list:
                    block_counts = self.param.gUnit[lun].q11_logical_block_count
                    logger.info(f'LUN{lun} total block counts = {block_counts}')
                    if block_counts > 0:
                        logger.info(f'Random WRITE test for LUN{lun}')
                        cmd_count = 200
                        min_lun = lun
                        max_lun = lun
                        min_lba = 0
                        max_lba =  block_counts - BLOCK4K_SIZE_128K_BYTE
                        min_size = BLOCK4K_SIZE_4K_BYTE
                        max_size = BLOCK4K_SIZE_128K_BYTE
                        api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                        
                        logger.info(f'Issue WRITE 4K size for LUN{lun} and LBA{block_counts-1}, expect response should success')
                        ExecuteCMD.Write10().assign(lun=lun, lba=block_counts-1, length=1, fua=0).enqueue()
                        ExecuteCMD.send(clear_on_success=False)
                        for cmd in ExecuteCMD._cmd_list:
                            api.save_write_info_by_cmd(cmd, self.write_record)
                        ExecuteCMD.clear()

                        logger.info(f'Issue WRITE 4K size for LUN{lun} and LBA{block_counts}, expect response should out of range fail')
                        write10 = ExecuteCMD.Write10().assign(lun=lun, lba=block_counts, length=1, fua=0).enqueue()
                        try:
                            ExecuteCMD.send(clear_on_success=False, skip_response_check=True)
                        except DLL_RESPONSE_ERROR:
                            logger.info(f'Write10 response Fail')
                        rsp = ExecuteCMD.read_response(write10)
                        if rsp.upiu.b6_response != UPIUResponse.TARGET_FAILURE or rsp.upiu.b7_status != ScsiStatus.CHECK_CONDITION or \
                            rsp.b32_sense_data.b2_sense_key != SenseKey.ILLEGAL_REQUEST or rsp.b32_sense_data.b12_asc != 0x21:
                            logger.error_lb(f'Host write out of range LBA{block_counts} on LUN{lun}')
                            logger.error_fp(f'Expect the write response to be {api.QueryResponseCode.GENERAL_FAILURE} and asc = LOGICAL_BLOCK_ADDRESS_OUT_OF_RANGE(21h), but Current response = {api.get_cmd_response_byte_str(rsp)}, status = {api.get_scsi_status_str(rsp)}, sense_key = {api.get_sense_key_str(rsp)}, asc = {api.get_asc_ascq_description(rsp)}')
                            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
                        ExecuteCMD.clear()

            elif event == EVENT.UNMAP:
                for lun in enable_lun_list:
                    block_counts = self.param.gUnit[lun].q11_logical_block_count
                    logger.info(f'LUN{lun} total block counts = {block_counts}')
                    if block_counts > 0:
                        logger.info(f'Random UNMAP test for LUN{lun}')
                        cmd_count = 200
                        min_lun = lun
                        max_lun = lun
                        min_lba = 0
                        max_lba = block_counts - BLOCK4K_SIZE_128K_BYTE
                        min_size = BLOCK4K_SIZE_4K_BYTE
                        max_size = BLOCK4K_SIZE_128K_BYTE
                        api.random_erase(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                                    write_record=self.write_record)
                        
                        logger.info(f'Issue WRITE 4K size for LUN{lun} and LBA {block_counts-1}, expect response should success')
                        ExecuteCMD.Unmap().assign(lun=lun, lba=block_counts-1, length=1).enqueue()
                        ExecuteCMD.send(clear_on_success=False)
                        for cmd in ExecuteCMD._cmd_list:
                            api.save_write_info_by_cmd(cmd, self.write_record)
                        ExecuteCMD.clear()

                        logger.info(f'Issue WRITE 4K size for LUN{lun} and LBA{block_counts}, expect response should out of range fail')
                        unmap = ExecuteCMD.Unmap().assign(lun=lun, lba=block_counts, length=1).enqueue()
                        try:
                            ExecuteCMD.send(clear_on_success=False, skip_response_check=True)
                        except DLL_RESPONSE_ERROR:
                            logger.info(f'Unmap response Fail')
                        rsp = ExecuteCMD.read_response(unmap)
                        if rsp.upiu.b6_response != UPIUResponse.TARGET_FAILURE or rsp.upiu.b7_status != ScsiStatus.CHECK_CONDITION or \
                            rsp.b32_sense_data.b2_sense_key != SenseKey.ILLEGAL_REQUEST or rsp.b32_sense_data.b12_asc != 0x21:
                            logger.error_lb(f'Host unmap out of range LBA{block_counts} on LUN{lun}')
                            logger.error_fp(f'Expect the unmap response to be {api.QueryResponseCode.GENERAL_FAILURE} and asc = LOGICAL_BLOCK_ADDRESS_OUT_OF_RANGE(21h), but Current response = {api.get_cmd_response_byte_str(rsp)}, status = {api.get_scsi_status_str(rsp)}, sense_key = {api.get_sense_key_str(rsp)}, asc = {api.get_asc_ascq_description(rsp)}')
                            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
                        ExecuteCMD.clear()


            # elif event == EVENT.FFU:
            #     logger.info(f'FFU update test')
            #     current_bin = api.search_ffu_bin(api.api.FFUBinType.FW_HW_BIN, api.api.FFUSvnType.CURRENT_SVN_BIN, True)
            #     temp_bin = current_bin.copy()
            #     temp_bin = codesign_ffu_bin(ffu_bin=temp_bin, ffu_bin_type=api.FFUBinType.FW_HW_BIN, include_mconfig=True)
            #     api.send_ffu_write_buffer(len(temp_bin), 0, temp_bin)
            #     api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET)
            #     ffu_status = api.read_attribute(idn=api.AttributeIDN.DEVICE_FFU_STATUS)
            #     if ffu_status != api.FFUStatus.SUCCESSFUL_MICROCODE_UPDATE:
            #         raise api.SIGHTING_FFU_STATUS_UNEXPECTED
                
            # elif event == EVENT.PURGE:
            #     logger.info(f'Purge test')
            #     api.set_flag(idn=FlagIDN.PURGE_EN)
            #     purge_timeout = 30 
                
            #     start_time = time.time()
            #     while True:
            #         if self.check_timeout(start_time, purge_timeout):
            #             raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            #         val = api.read_attribute(idn=AttributeIDN.PURGE_STATUS)
            #         if val == PurgeStatus.PURGE_STS_COMPLETE_SUCCESS:
            #             break
            #         time.sleep(1)

            elif event == EVENT.READ_COMPARE:
                logger.info(f'Read compare test')
                read_compare(self.write_record, api.CompareMethod.HW_COMPARE)

run = Pattern().run
if __name__ == "__main__":
    run()