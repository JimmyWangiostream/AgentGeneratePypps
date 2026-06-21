from copy import deepcopy
from enum import IntEnum
from typing import List, cast

import package_root
from Script import api
from Script.api.exception import SIGHTING_FAIL_DATA_COMPARE_FAIL
from Script.api.ufs_api.debug_cmd.dcmd_enum import Dcmd5ResetType
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api.initial_device import init_tester_to_unit_ready
from Script.api.ufs_api.vendor_cmd.structs import FlashSetting
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.project_api.custom_vu.bad_block_information_vu.functions import issue_405E_to_get_bad_block_information
from Script.project_api.custom_vu.media_scan_vu.functions import issue_40CF_to_get_media_scan_parameters
from Script.project_api.read_disturb_vu.functions import issue_40CA_to_get_get_Read_Count_threshold_table
from Script.project_api.refresh_vu.define import VUC088Paremeter
from Script.project_api.refresh_vu.functions import issue_C088_to_start_or_stop_refresh
from Script.project_api.reh.functions import get_error_recovery_record_by_index, issue_40BA_to_get_error_recovery_statistics, issue_D019_to_en_dis_success_read_count
from Script.project_api.set_get_temperature.functions import issue_4021_get_nand_temperature

_sdk = api.shared.sdk

class READ_COUNT_STATISTICS(IntEnum):
    DISABLE = 0
    ENABLE = 1

class ERSIndex(IntEnum):
    DEFAULT_READ_PASS_COUNT = 65


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.param = api.shared.param
        self.geometry_desc = api.get_geometry_descriptor()
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        self.flash_setting = FlashSetting()
        self.flash_setting.from_bytes(self.flash_setting_buffer)
        self.fw_geometry = api.get_fw_geometry()
        self.total_au_size = int(self.geometry_desc.q4_total_raw_device_capacity / self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size)
        self.total_capacity_4K = int(self.geometry_desc.q4_total_raw_device_capacity/8)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.TestNormalLun = 1
        self.TestPSALun = 0
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.write_record = api.get_empty_write_record()
        config_descs = api.get_config_descriptors(print=True)
        self.backup_setting = deepcopy(config_descs)
        pass



    def step1(self) -> None:

        for i in range(1):
            logger.flow(1, 'Config LUN 0/1 to normal LU')
            self.LUN_configuration()

            logger.flow(2, f'Issue C088 to stop refresh execution')
            issue_C088_to_start_or_stop_refresh(bParameter0=VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)

            logger.flow(3, f'Issue 40BA VUC to get ERS')
            read_count_1st = self.get_default_read_pass_count()
            logger.info(f'1st Read default counts = {read_count_1st}')

            logger.flow(4, f'Power cycle')
            init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET, powerdown = True)

            logger.flow(5, f'Issue D019 to enable success read count')
            _ = issue_D019_to_en_dis_success_read_count(READ_COUNT_STATISTICS.ENABLE)

            lun = self.TestPSALun    
            length = self.param.gDevice.l37_psa_max_data_size
            # length = 256
            logger.flow(6, f'Set PSA state to PRE_SOLDERING')
            self.set_psa_flow(lun, length)

            logger.flow(7, f'Write PSA for max PSA data size = {length}')
            total = length
            start = 0
            while total > 0:
                chunk_size = min(total, WRITE_10_MAX_BLOCK_LEN)
                ExecuteCMD.Write10().assign(lun=lun, lba=start, length=chunk_size, fua=0).enqueue()                
                total -= chunk_size
                start += chunk_size
            ExecuteCMD.send()

            logger.flow(8, f'Issue 40BA VUC to get ERS')
            read_count_2nd = self.get_default_read_pass_count()
            logger.info(f'2nd Read default counts = {read_count_2nd}')

            logger.flow(9, f'Write PSA_STATE to LOADING_COMPLETE')
            ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.LOADING_COMPLETE).set_option(wait_queue_empty=True).enqueue()
            ExecuteCMD.send()

            logger.flow(10, f'Read PSA size for max PAS data size = {length}')
            total = length
            start = 0
            while total > 0:
                chunk_size = min(total, READ_10_MAX_BLOCK_LEN)
                ExecuteCMD.Read10().assign(lun=lun, lba=start, length=chunk_size, fua=0).enqueue()                
                total -= chunk_size
                start += chunk_size
            ExecuteCMD.send()

            logger.flow(11, f'Issue 40BA VUC to get ERS')
            read_count_3rd = self.get_default_read_pass_count()
            logger.info(f'3rd Read default counts = {read_count_3rd}')

            logger.flow(12, f'Power cycle')       
            init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET, powerdown = True)

            logger.flow(13, f'Issue D019 to enable read count')
            _ = issue_D019_to_en_dis_success_read_count(READ_COUNT_STATISTICS.ENABLE)

            logger.flow(14, f'Issue 404E to get bad block')
            _, VU_DATA_405E = issue_405E_to_get_bad_block_information()

            logger.flow(15, f'Issue 4021 to get nand temperature')
            _, GetNandTemperature = issue_4021_get_nand_temperature()

            logger.flow(16, f'Issue 40CA to get read count threshold table')
            _, rc_threshold_of_vb = issue_40CA_to_get_get_Read_Count_threshold_table()

            logger.flow(17, f'Issue 40CF to get media scan parameter')
            _, payload = issue_40CF_to_get_media_scan_parameters()

            logger.flow(18, f'Issue 40BA VUC to get ERS')
            read_count_4th = self.get_default_read_pass_count()
            logger.info(f'4th Read default counts = {read_count_4th}')

            logger.flow(19, f'Compare ERS default read pass counts before and after power cycle')
            if any(a < b for a, b in zip(read_count_4th, read_count_3rd)):
                logger.error_lb(f'Compare ERS default read pass counts before and after power cycle')
                logger.error_fp(f'Expect default read pass counts to be equal before and after power cycle (3rd: {read_count_3rd} vs 4th: {read_count_4th})')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            logger.flow(20, 'Issue C088 to start refresh')
            issue_C088_to_start_or_stop_refresh(bParameter0=VUC088Paremeter.StartRefresh)
        
        pass
    
    def post_process(self) -> None:
        logger.info('Set bPSAState as Off to interrupt PSA flow')
        api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.OFF)
        logger.info('Re-config to backup description')
        self.re_config()
        pass

    def LUN_configuration(self) -> None:
        config_desc = api.get_config_descriptors(print = True)
        lun_num_per_desc = 8
        au_size = (self.total_au_size)//2

        for index in range(int(self.max_number_lu/lun_num_per_desc)):
            config_desc[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            config_desc[index].header.b3_boot_enable = api.BootEnable.BOOT_DISABLE
            for unit in range(lun_num_per_desc):
                if index == 0 and unit == self.TestPSALun: # LUN 0
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[index].units[unit].l4_num_alloc_units = au_size
                    config_desc[index].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit == self.TestNormalLun: # LUN 1
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[index].units[unit].l4_num_alloc_units = au_size
                    config_desc[index].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                else:
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.DISABLE
                    config_desc[index].units[unit].l4_num_alloc_units = 0
                    config_desc[index].units[unit].b9_logical_block_size = 0
                
            push_write_config(config_desc[index], index=index)

        ExecuteCMD.send()

        self.update_unit_desc()
        self.update_device_desc()

        test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
        for lun in range(self.param.gMaxNumberLU):
            if self.param.gUnit[lun].b3_lu_enable != api.LUNEnable.DISABLE:
                test_unit_ready.set_option(lun=lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send()

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

    def update_device_desc(self) -> None:
        device_descriptor = ExecuteCMD.ReadDescriptor()
        device_descriptor.assign(idn=api.DescriptorIDN.DEVICE)
        index = ExecuteCMD.enqueue(device_descriptor)
        ExecuteCMD.send(clear_on_success=False)
        api.update_descriptor(idn=api.DescriptorIDN.DEVICE, index=0, response=cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

    def get_default_read_pass_count(self) -> List[int]:
        read_counts: List[int] = []
        _, ers = issue_40BA_to_get_error_recovery_statistics()
        ers_buf = bytearray(ers.payload)
        rec = get_error_recovery_record_by_index(ERSIndex.DEFAULT_READ_PASS_COUNT) 
        if rec != None:  
            offset = rec.offset
            for ce in range(self.flash_setting.Max_Fdevice):
                log = ''
                for pln in range(self.flash_setting.Plane_Per_Die):
                    count = int.from_bytes(ers_buf[offset: offset+rec.occupies], byteorder='little')
                    offset += rec.occupies
                    read_counts.append(count)
                    log+= f'plane{pln}: {count}, '
                logger.info(f'CE{ce}: {log}')
        
        return read_counts
    
    def set_psa_flow(self, lun:int, length:int) -> None:

        logger.info(f'Set PSA data size = {length}')
        api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=length)

        logger.info(f'Unmap lun{lun}')
        unmap = ExecuteCMD.Unmap()
        unmap.assign(lun=lun, lba=0, length=self.param.gUnit[lun].q11_logical_block_count)
        ExecuteCMD.enqueue(unmap)

        logger.info(f'Write PSA_STATE to PRE_SOLDERING')
        ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.send()
        pass

    def re_config(self) -> None:
        for i in range(4):
            if i == 3:
                self.backup_setting[i].header.b2_conf_desc_continue = 0
            else:
                self.backup_setting[i].header.b2_conf_desc_continue = 1
            push_write_config(self.backup_setting[i], index=i) 
        ExecuteCMD.send()





run = Pattern().run
if __name__ == "__main__":
    run()