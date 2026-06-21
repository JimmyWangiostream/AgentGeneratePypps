from copy import deepcopy

import package_root
from Script.api.exception import SIGHTING_RESPONSE_UNEXPECTED, SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
from Script.api.ufs_api.vendor_cmd.structs import FlashSetting
from Script.lib import sdk_lib as lib
from time import sleep
from typing import Tuple, List, Dict, cast
from Script import api
from Script.api import shared, dumpfile,  cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
import random
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from enum import IntEnum
from Script.project_api.custom_vu.lba_convert_vu import \
    issue_4051_to_get_physical_address, \
    issue_4052_to_get_logical_address
from Script.project_api.refresh_vu.define import VUC088Paremeter
from Script.project_api.refresh_vu.functions import issue_C088_to_start_or_stop_refresh
from Script.project_api.reh.functions import \
    get_page_range_by_type, \
    issue_D014_to_set_read_recovery_module, \
    issue_D014_to_set_last_table_content, \
    issue_40F9_to_get_rr_number_and_error_bits, \
    issue_4014_to_get_read_recovery_info_read_last, \
    issue_40BA_to_get_error_recovery_statistics, \
    issue_D019_to_en_dis_success_read_count, \
    get_error_recovery_record_by_index, \
    create_read_last_ref_table, \
    ERROR_RECOVERY_STATISTICS_RECORD, \
    iter_reh_steps, \
    set_read_last_table
from Script.project_api.reh.structs import \
    READ_LAST_TABLE, PAGE_TYPE, BLOCK_PAGE_TYPE, \
    PAGE_TYPE_MAP, error_recovery_statistics
from Script.project_api.sticky_read.functions import \
    issue_4066_get_sticky_read_status_and_offset, \
    issue_4066_to_dis_en_sticky_read, \
    issue_4066_force_current_read_last_as_sticky_read
from Script.project_api.sticky_read.structs import STICKY_READ_OUTPUT_STATUS

class STICKY_READ_STATUS(IntEnum):
    SUCCESS = 0
    FAILED = 1

class STICKY_READ_SETTING(IntEnum):
    DISABLE = 0
    ENABLE = 1

class ERSIndex(IntEnum):
    DEFAULT_READ_PASS_COUNT = 65
    STICKY_READ_PASS_COUNT  = 66

class ReadCountTest(IntEnum):
    DEFAULT_READ_PASS_CASE = 0
    STICKY_READ_PASS_CASE = 1

ReadLastTableDict = Dict[READ_LAST_TABLE, List[int]]
READ_LAST_TABLE_TYPE= Dict[PAGE_TYPE, ReadLastTableDict]   # die0、die1…的最外層型別

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
        self.TestNormalLun = 0
        self.write_record = api.get_empty_write_record()
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.read_last_ref_table: Dict[int, READ_LAST_TABLE_TYPE] = create_read_last_ref_table(self.flash_setting.Max_Fdevice)
        self.page_type_lun_lba_map: Dict[PAGE_TYPE, Tuple[int, int]] = {}
        self.block_page_range = [
            BLOCK_PAGE_TYPE.TLC_BLOCK_SLC_PAGE,
            BLOCK_PAGE_TYPE.TLC_BLOCK_MLC_PAGE,
            BLOCK_PAGE_TYPE.TLC_BLOCK_TLC_PAGE
        ]
        pass

    def step1(self) -> None:
        logger.flow(1, 'Config LUN 0 to normal LU')
        self.LUN_configuration()

        logger.flow(1, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
        issue_C088_to_start_or_stop_refresh(bParameter0=VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)

        lun = self.TestNormalLun
        length = self.tlc_vb_size
        lba = random.randint(0, length-1)

        logger.flow(2, f'Sequential write LUN0 with 1VB size')
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=length, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        logger.flow(3, f'Issue 4051 VUC to get PBA from LBA({lba})')
        _,pca = issue_4051_to_get_physical_address(lun, lba)

        die = pca.die.value
        plane = pca.plane.value
        page = pca.page.value
        block = pca.virtual_block_number.value
        offset = pca.offset.value

        for case in [ReadCountTest.DEFAULT_READ_PASS_CASE.value, ReadCountTest.STICKY_READ_PASS_CASE.value]:
        # for case in [ReadCountTest.STICKY_READ_PASS_CASE.value]:
            
            read_count_index = ERSIndex.DEFAULT_READ_PASS_COUNT.value
            sticky_count_index = ERSIndex.STICKY_READ_PASS_COUNT.value 
            logger.info(f'loop case {case}')

            logger.flow(4, f'Issue D019 to enable success read count')
            _ = issue_D019_to_en_dis_success_read_count(STICKY_READ_SETTING.ENABLE)

            if case == ReadCountTest.STICKY_READ_PASS_CASE.value:
                logger.flow(5, f'Enable sticky read and force read last as sticky read offset')
                self.set_sticky_read_precondition(die)
                
                # logger.flow(6, f'Generate read fail to enter sticky read flow')
                # # self.gen_read_fail(die, block, plane, page, offset)

            logger.flow(7, f'Issue 40BA VUC to get ERS')
            _, ers_bk = issue_40BA_to_get_error_recovery_statistics()

            for block_type in self.block_page_range:
                for page_type in PAGE_TYPE_MAP.get(BLOCK_PAGE_TYPE(block_type), []):
                    page = get_page_range_by_type(page_type)

                    _, ers_bk = issue_40BA_to_get_error_recovery_statistics()

                    logger.flow(8, f'Issue 4052 VUC to get logical address with page = {page}, page type = {page_type.label}')
                    _, la = issue_4052_to_get_logical_address(die, plane, block, page, offset)
                    if not (la.lun.value == self.TestNormalLun and  la.lba.value >= 0 and la.lba.value < length):
                        logger.error_lb(f'Issue 4052 VUC to convert die{die}, plane{plane}, block{block}, page{page}, offset{offset} to LBA ')
                        logger.error_fp(f'Expect LUN and LBA value not equal to 0xFFFFFFFF, but converted LUN = {la.lun.value} and LBA = {la.lba.value}')
                        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
                    
                    self.page_type_lun_lba_map[page_type] = (la.lun.value, la.lba.value)

                    logger.flow(9, f'Issue host read 4K size from LUN{la.lun.value}, LBA:{la.lba.value}')
                    ExecuteCMD.Read10().assign(lun = la.lun.value, lba=la.lba.value, length=1, fua=0).enqueue()
                    ExecuteCMD.send()

                    logger.flow(10, f'Issue 40BA VUC get EHS')
                    _, ers = issue_40BA_to_get_error_recovery_statistics()

                    logger.flow(11, f'Compare EHS entry value')
                    read_count_diff = self.compare_ers_entry(die, plane, read_count_index, ers_bk, ers)
                    sticky_count_diff = self.compare_ers_entry(die, plane, sticky_count_index, ers_bk, ers)
                    logger.info(f'page type = {page_type.label}, page = {page}, 65 read count diff = {read_count_diff}, 66 sticky count diff = {sticky_count_diff}')
                    if case == ReadCountTest.DEFAULT_READ_PASS_CASE.value:
                        if not (read_count_diff > 0 and sticky_count_diff == 0):
                            logger.error_lb(f'Issue D019 VUC to ENABLE read count, then issue 40BA VUC to retrieve and compare EHS entry values')
                            logger.error_fp(f'EHS index {read_count_diff} is expected to increase and index {sticky_count_diff} is expected to remain unchanged , but the comparison failed')
                            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
                    else:
                        if not (sticky_count_diff > 0 and sticky_count_diff == read_count_diff):
                            logger.error_lb(f'Issue D019 VUC to ENABLE read count, then issue 40BA VUC to retrieve and compare EHS entry values')
                            logger.error_fp(f'EHS index {read_count_diff} and {sticky_count_diff} is expected to increase, but the comparison failed')
                            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

                    ers_bk = ers

            logger.flow(12, f'Issue D019 to disable success read count')
            _ = issue_D019_to_en_dis_success_read_count(STICKY_READ_SETTING.DISABLE)

            for block_type in self.block_page_range:
                for page_type in PAGE_TYPE_MAP.get(BLOCK_PAGE_TYPE(block_type), []):
                    lun, lba = self.page_type_lun_lba_map[page_type]
                    logger.flow(13, f'Issue host read 4K size from LUN{lun}, LBA:{lba}')
                    ExecuteCMD.Read10().assign(lun = lun, lba=lba, length=1, fua=0).enqueue()
                    ExecuteCMD.send()

            logger.flow(14, f'Issue 40BA VUC get EHS')
            _, ers = issue_40BA_to_get_error_recovery_statistics()

            logger.flow(15, f'Compare EHS entry value')
            read_count_diff = self.compare_ers_entry(die, plane, read_count_index, ers_bk, ers)
            sticky_count_diff = self.compare_ers_entry(die, plane, sticky_count_index, ers_bk, ers)
            if not (read_count_diff == 0 and sticky_count_diff == 0):
                logger.error_lb(f'Issue D019 VUC to DISABLE read count, then issue 40BA VUC to retrieve and compare EHS entry values')
                logger.error_fp(f'Expect EHS {read_count_index} and {sticky_count_index} to remain unchanged, but the comparison failed')
                raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        
            logger.flow(16, f'Issue D019 to enable success read count')
            _ = issue_D019_to_en_dis_success_read_count(STICKY_READ_SETTING.ENABLE)

            logger.flow(17, f'Power cycle')
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET)

            logger.flow(18, f'Issue 40BA VUC to get ERS')
            _, ers_bk = issue_40BA_to_get_error_recovery_statistics()

            if case == ReadCountTest.STICKY_READ_PASS_CASE.value:
                logger.flow(19, f'Enable sticky read and force read last as sticky read offset')
                self.set_sticky_read_precondition(die)

                # logger.flow(20, f'Generate read fail to enter sticky read flow')
                # self.gen_read_fail(die, block, plane, page, offset)

            for block_type in self.block_page_range:
                for page_type in PAGE_TYPE_MAP.get(BLOCK_PAGE_TYPE(block_type), []):
                    page = get_page_range_by_type(page_type)
                    
                    logger.flow(21, f'Issue 4052 VUC to get logical address with page = {page}, page type = {page_type.label}')
                    _, la = issue_4052_to_get_logical_address(die, plane, block, page, offset)
                    if not (la.lun.value == self.TestNormalLun and  la.lba.value >= 0 and la.lba.value < length):
                        logger.error_lb(f'Issue 4052 VUC to convert die{die}, plane{plane}, block{block}, page{page}, offset{offset} to LBA ')
                        logger.error_fp(f'Expect LUN and LBA value not equal to 0xFFFFFFFF, but converted LUN = {la.lun.value} and LBA = {la.lba.value}')
                        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

                    logger.flow(22, f'Issue host read 4K size from LUN{la.lun.value}, LBA:{la.lba.value}')
                    ExecuteCMD.Read10().assign(lun = la.lun.value, lba=la.lba.value, length=1, fua=0).enqueue()
                    ExecuteCMD.send()

            logger.flow(23, f'Issue 40BA VUC get EHS')
            _, ers = issue_40BA_to_get_error_recovery_statistics()

            logger.flow(24, f'Compare EHS entry value')
            read_count_diff = self.compare_ers_entry(die, plane, read_count_index, ers_bk, ers)
            sticky_count_diff = self.compare_ers_entry(die, plane, sticky_count_index, ers_bk, ers)
            if not (read_count_diff == 0 and sticky_count_diff == 0):
                logger.error_lb(f'Device power cycle,  then issue 40BA VUC to retrieve and compare EHS entry values')
                logger.error_fp(f'Expect EHS {read_count_index} and {sticky_count_index} to remain unchanged, but the comparison failed')
                raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

        pass

    def post_process(self) -> None:
        pass

    def LUN_configuration(self) -> None:
        config_desc = api.get_config_descriptors(print = True)
        lun_num_per_desc = 8
        au_size = (self.total_au_size)//3
        for index in range(int(self.max_number_lu/lun_num_per_desc)):
            config_desc[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            config_desc[index].header.b3_boot_enable = api.BootEnable.BOOT_DISABLE
            for unit in range(lun_num_per_desc):
                config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.DISABLE
                config_desc[index].units[unit].l4_num_alloc_units = 0
                config_desc[index].units[unit].b9_logical_block_size = 0
                if index == 0 and unit == self.TestNormalLun: # LUN 0
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[index].units[unit].l4_num_alloc_units = au_size
                    config_desc[index].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
            
            push_write_config(config_desc[index], index=index)

        ExecuteCMD.send()

        self.update_unit_desc()

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
        pass

    def set_sticky_read_precondition(self, die:int) -> None:
        logger.info(f'Issue D014 op2 VUC to set read last table')
        set_read_last_table(maxDie=self.flash_setting.Max_Fdevice, read_last_table=self.read_last_ref_table)       
        
        logger.info(f'Issue 4066 VUC to force read last as sticky read')
        table_index = random.choice([READ_LAST_TABLE.LAST_TABLE_1, READ_LAST_TABLE.LAST_TABLE_2])
        for page_type in PAGE_TYPE:
            arc = random.randint(0, 2)
            self.force_read_last_as_sticky_read(die, page_type, arc, table_index)

        logger.info(f'Issue 4066 VUC to enable sticky read feature')
        self.set_sticky_read_en_dis(STICKY_READ_SETTING.ENABLE)
    
    def force_read_last_as_sticky_read(self, die:int, page_type:int, arc:int, table_index:int) -> None:
        _, sr = issue_4066_force_current_read_last_as_sticky_read(die, page_type, 0, table_index, arc)
        if sr.result.value == STICKY_READ_STATUS.FAILED:
            logger.error_lb(f'Host issue vu 4066 to force read last as sticky read')
            logger.error_fp(f'Expect the status value is success, but failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def gen_read_fail(self, die:int, block:int, plane:int, page:int, offset:int) -> None:
        _ = issue_D014_to_set_read_recovery_module(
                    die = die, 
                    bigIndex=0, 
                    smallIndex=0, 
                    nandMode=0, 
                    isSpeciBlock=1, 
                    block=block, 
                    isPSA=0)
        logger.info(f'Issue 40F6 VUC get rr number')
        issue_40F9_to_get_rr_number_and_error_bits(1<<die, 1<<plane, block, page, page, 0, 0, 0, 0)

        for block_type in self.block_page_range:    
            for page_type in PAGE_TYPE_MAP.get(BLOCK_PAGE_TYPE(block_type), []):
                logger.info(f'Issue 4066 VUC get sticky read status')
                self.check_sticky_read_status(die, page_type)


    def set_sticky_read_en_dis(self, setting:int) -> None:
        _, result = issue_4066_to_dis_en_sticky_read(setting)
        if result == STICKY_READ_STATUS.FAILED:
            logger.error_lb(f'Host issue vu 4066 to enable sticky read feature')
            logger.error_fp(f'Expect the result value is success, but failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def get_ers_value(self, die:int, plane:int, rec:ERROR_RECOVERY_STATISTICS_RECORD, payload: bytearray)->int:
        start = rec.offset+die*self.flash_setting.Plane_Per_Die*rec.occupies+plane*rec.occupies
        val = int.from_bytes(payload[start: start+rec.occupies], byteorder='little')
        return val

    def compare_ers_entry(self, die:int, plane:int, ers_inx:int, org_ers:error_recovery_statistics, cur_ers:error_recovery_statistics)-> int:
        ret = 0
        rec = get_error_recovery_record_by_index(ers_inx)   
        if rec != None:    
            cur = self.get_ers_value(die = die, plane = plane, rec = rec, payload = bytearray(cur_ers.payload))
            org = self.get_ers_value(die = die, plane = plane, rec = rec, payload = bytearray(org_ers.payload))
            ret = cur - org
            logger.info(f'{rec.name} entry: original value = {org}, current value = {cur}')      
        return ret

    def check_sticky_read_status(self, die:int, type:PAGE_TYPE)-> bool:
        ret = False
        _, _sr = issue_4066_get_sticky_read_status_and_offset(die, type, 0)
        logger.info(f'Issue 4066 VUC get sticky read result = {_sr.result.value} and status = {_sr.stickyReadStatus.value}')
        if _sr.result.value == STICKY_READ_STATUS.SUCCESS and \
            _sr.stickyReadStatus.value == STICKY_READ_OUTPUT_STATUS.STICKY_READ_ENTERED:
            ret = True
        return ret

run = Pattern().run
if __name__ == "__main__":
    run()