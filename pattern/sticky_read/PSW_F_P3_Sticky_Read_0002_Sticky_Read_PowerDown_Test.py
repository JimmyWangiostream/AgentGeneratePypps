import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api import Dcmd5ResetType
from Script.api.exception import SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
from Script.api.ufs_api.defines.constant_define import DATA_SIZE_4K_BYTE
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from typing import TypeAlias, List, Dict, cast
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api.vendor_cmd.structs import PCA, FlashSetting
from Script.api.ufs_api.descriptors.configuration_desc.structs import ConfigDescriptor310, ConfigDescriptor400, ConfigDescriptor410
from enum import IntEnum
from Script.api.ufs_api import init_tester_to_unit_ready
from Script.project_api.custom_vu.lba_convert_vu import physical_address_info
from Script.project_api.custom_vu.lba_convert_vu import issue_4051_to_get_physical_address
from Script.project_api.reh.functions import create_read_last_ref_table, issue_40F9_to_get_rr_number_and_error_bits, issue_D014_to_set_last_table_content, issue_D014_to_set_read_recovery_module, iter_reh_steps, set_read_last_table
from Script.project_api.reh.structs import BLOCK_PAGE_TYPE, ERROR_RECOVERY_STATISTICS_RECORD, NAND_MODE, PAGE_TYPE, READ_LAST_TABLE
from Script.project_api.sticky_read.functions import issue_4066_force_current_read_last_as_sticky_read, issue_4066_get_sticky_read_status_and_offset, issue_4066_to_dis_en_sticky_read
from Script.project_api.sticky_read.structs import STICKY_READ_OUTPUT_STATUS


class STICKY_READ_SETTING(IntEnum):
    DISABLE = 0
    ENABLE = 1

class STICKY_READ_STATUS(IntEnum):
    SUCCESS = 0
    FAILED = 1


ReadLastTableDict = Dict[READ_LAST_TABLE, List[int]]
READ_LAST_TABLE_TYPE= Dict[PAGE_TYPE, ReadLastTableDict]   # die0、die1…的最外層型別

ENG2_WA = True

ConfigDescriptorUnion: TypeAlias = ConfigDescriptor310 | ConfigDescriptor400 | ConfigDescriptor410

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.param = api.shared.param
        self.write_record = api.get_empty_write_record()
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        self.flash_setting = FlashSetting()
        self.flash_setting.from_bytes(self.flash_setting_buffer)
        self.total_au_size = int(self.geometry_desc.q4_total_raw_device_capacity / self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size)
        self.total_capacity_4K = int(self.geometry_desc.q4_total_raw_device_capacity/8)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.read_last_ref_table: Dict[int, READ_LAST_TABLE_TYPE] = create_read_last_ref_table(self.flash_setting.Max_Fdevice)
        pass

    def step1(self) -> None:
        logger.flow(1, 'Config LUN0 to normal LU and LUN1 to EM1 LU')
        self.set_LUN_configuration()

        logger.flow(2, f'Sequential write 1 vb size')
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=self.tlc_vb_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=self.slc_vb_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        for lun in [self.TestNormalLun, self.TestEM1Lun]:
            length = self.slc_vb_size if lun == self.TestEM1Lun else self.tlc_vb_size
            isSLC = 1 if lun == self.TestEM1Lun else 0
            block_type = BLOCK_PAGE_TYPE.SLC_BLOCK_SLC_PAGE if lun == self.TestEM1Lun else BLOCK_PAGE_TYPE.TLC_BLOCK_TLC_PAGE

            logger.flow(3, f'Issue D014 op2 VUC to set read last table')
            set_read_last_table(maxDie=self.flash_setting.Max_Fdevice, read_last_table=self.read_last_ref_table)

            logger.flow(4, f'Random select LBA in LUN{lun}')
            lba = random.randint(lun, length-1)

            logger.flow(5, f'Issue 4051 VUC to get PBA from LBA({lba})')
            _,pca = issue_4051_to_get_physical_address(lun, lba)

            die = pca.die.value
            page = pca.page.value
            plane = pca.plane.value
            block = pca.virtual_block_number.value
            page_type = self.get_page_type_by_page_number(page, block_type)
            table_index = READ_LAST_TABLE(random.randint(READ_LAST_TABLE.LAST_TABLE_1, READ_LAST_TABLE.LAST_TABLE_2))
            logger.info(f'Select LBA = {lba} in LUN{lun}, page = {page}, page type = {page_type.label}')

            logger.flow(6, f'Issue 4066 VUC to disable sticky read feature')
            self.set_sticky_read_en_dis(STICKY_READ_SETTING.DISABLE)

            logger.flow(7, f'Issue D014 to generate read fail and issue 4066 to check sticky read not entered')
            self.generate_fail_and_check_sticky_read(lun, lba, die, block, plane, page, isSLC, block_type, page_type, table_index, STICKY_READ_OUTPUT_STATUS.STICKY_READ_NOT_ENTERED)

            logger.flow(8, f'Issue 4066 VUC to enable sticky read feature')
            self.set_sticky_read_en_dis(STICKY_READ_SETTING.ENABLE)

            logger.flow(9, f'Issue 4066 VUC to force read last as sticky read')
            arc = random.randint(0, 2)
            self.force_read_last_as_sticky_read(die, page_type, arc, table_index)

            logger.flow(10, f'Issue D014 to generate read fail and issue 4066 to check sticky read entered')
            self.generate_fail_and_check_sticky_read(lun, lba, die, block, plane, page,isSLC, block_type, page_type, table_index, STICKY_READ_OUTPUT_STATUS.STICKY_READ_ENTERED)

            logger.flow(11, f'Issue 4066 VUC to disable sticky read feature')
            self.set_sticky_read_en_dis(STICKY_READ_SETTING.DISABLE)

            logger.flow(12, f'Power down')
            init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)

            logger.flow(13, f'Issue D014 op2 VUC to set read last table')
            set_read_last_table(maxDie=self.flash_setting.Max_Fdevice, read_last_table=self.read_last_ref_table)

            logger.flow(14, f'Issue 4066 VUC to force read last as sticky read')
            arc = random.randint(0, 2)
            self.force_read_last_as_sticky_read(die, page_type, arc, table_index)

            logger.flow(15, f'Issue D014 to generate read fail and issue 4066 to check sticky read entered')
            self.generate_fail_and_check_sticky_read(lun, lba, die, block, plane, page, isSLC, block_type, page_type, table_index, STICKY_READ_OUTPUT_STATUS.STICKY_READ_ENTERED)

        pass

    def post_process(self) -> None:
        pass

    def set_LUN_configuration(self) -> None:
        config_desc = api.get_config_descriptors(print = True)
        lun_num_per_desc = 8
        au_size = int(self.total_au_size/2)
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
                elif index ==0 and unit == self.TestEM1Lun :# LUN1
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_desc[index].units[unit].l4_num_alloc_units = au_size if au_size < self.geometry_desc.l44_enhanced1_max_n_alloc_u else self.geometry_desc.l44_enhanced1_max_n_alloc_u
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

    def read_data(self, lun:int, lba:int, length:int) -> None:
        logger.info(f'Sequence read data LUN:{lun}, LBA:{lba}, length:{length}')
        start = lba
        offset = 0
        while offset < length:
            size = 0xffff
            if(offset + size > length):
                size = length - offset
            w = ExecuteCMD.Read10()
            w.assign(lun = lun, lba=lba, length=size, fua=1).enqueue()
            offset += size
            lba = start+offset
        ExecuteCMD.send()
        pass

    def get_direct_read_data(self, physical_address: physical_address_info) ->tuple[bytearray, bytearray]:
        pca = PCA()
        pca.b4_mode = NAND_MODE.SLC_BLOCK.value
        pca.b5_ce = physical_address.die.value
        pca.b6_plane = physical_address.plane.value
        pca.b11_block_h = (physical_address.virtual_block_number.value>>8) & 0xFF
        pca.b10_block_l = physical_address.virtual_block_number.value & 0xFF
        pca.l12_fpage = int(physical_address.page.value * 32 + physical_address.offset.value * 8)
        payload = api.direct_read(pca=pca, block_count=4, include_FW_spare=True)
        spare = payload[4 * DATA_SIZE_4K_BYTE:4 * DATA_SIZE_4K_BYTE + DATA_SIZE_4K_BYTE]
        data = payload[:4 * DATA_SIZE_4K_BYTE]
        return data, spare
    
    def set_sticky_read_en_dis(self, setting:STICKY_READ_SETTING) -> None:
        _, result = issue_4066_to_dis_en_sticky_read(setting)
        if result == STICKY_READ_STATUS.FAILED:
            logger.error_lb(f'Host issue vu 4066 to enable sticky read feature')
            logger.error_fp(f'Expect the result value is success, but failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def _to_signed_byte(self, val: int) -> int:
        """將 0‑255 的 byte 轉成有號 byte（-128 ~ 127）。"""
        return val - 256 if val > 127 else val              
    
    def get_page_type_by_page_number(self, page:int, block_type:int) -> PAGE_TYPE:
        page_type : PAGE_TYPE = PAGE_TYPE.PAGE_SLC_LP
        if(block_type == BLOCK_PAGE_TYPE.SLC_BLOCK_SLC_PAGE):
            page_type = PAGE_TYPE.PAGE_POR_SSLC
        else:
            if page >= 3308:
                page_type = PAGE_TYPE.PAGE_SLC_LP
            elif page >= 1620 and page <= 1651:
                if (page-1620) % 2 == 0:
                    page_type = PAGE_TYPE.PAGE_MLC_LP
                else:
                    page_type = PAGE_TYPE.PAGE_MLC_UP
            else:
                if page % 3 == 0:
                    page_type = PAGE_TYPE.PAGE_TLC_LP
                elif page % 3 == 1:
                    page_type = PAGE_TYPE.PAGE_TLC_UP
                else:
                    page_type = PAGE_TYPE.PAGE_TLC_XP
        return page_type
    
    def check_sticky_read_status(self, die:int, type:PAGE_TYPE, table: READ_LAST_TABLE, check_status:STICKY_READ_OUTPUT_STATUS)-> None:
        _, _sr = issue_4066_get_sticky_read_status_and_offset(die, type, 0)
        if not (
            _sr.result.value == STICKY_READ_STATUS.SUCCESS and 
            _sr.stickyReadStatus.value == check_status
        ):
            logger.error_lb(f'Host issue vu 4066 to get sticky read status')
            logger.error_fp(f'Expect the result value is success(0) and status = {check_status}, but current result = {_sr.result.value} and status = {_sr.stickyReadStatus.value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        offsets = [_sr.offset1.value, _sr.offset2.value, _sr.offset3.value]
        refs = self.read_last_ref_table[die][type][table]

        if not ((check_status == STICKY_READ_OUTPUT_STATUS.STICKY_READ_ENTERED and offsets == refs) or \
                (check_status == STICKY_READ_OUTPUT_STATUS.STICKY_READ_NOT_ENTERED and offsets != refs)): 
            logger.error_lb(f'Host issue vu 4066 to get sticky read status')
            logger.error_fp(f'Read last offset compare fail, expect offset is {refs}, but current offset is {offsets}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def force_read_last_as_sticky_read(self, die:int, page_type:int, arc:int, table_index:int) -> None:
        _, sr = issue_4066_force_current_read_last_as_sticky_read(die, page_type, 0, table_index, arc)
        if sr.result.value == STICKY_READ_STATUS.FAILED:
            logger.error_lb(f'Host issue vu 4066 to force read last as sticky read')
            logger.error_fp(f'Expect the status value is success, but failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def generate_fail_and_check_sticky_read(self, lun:int, lba:int ,die:int, block:int, plane:int, page:int, isSLC: int, block_type: BLOCK_PAGE_TYPE, page_type:PAGE_TYPE, table_index:READ_LAST_TABLE, read_status:STICKY_READ_OUTPUT_STATUS)->None:
        for b, s in iter_reh_steps(type =block_type):
            if b > 1:
                break
            logger.info(f'Issue D014 VUC with big step: {b}, small step: {s} to make and recover UECC on {block_type.label}' )
            _ = issue_D014_to_set_read_recovery_module(
                die = die, 
                bigIndex=b, 
                smallIndex=s, 
                nandMode=isSLC, 
                isSpeciBlock=1, 
                block=block, 
                isPSA=0)
            
            logger.info(f'Sequence read data lba = {lba} in lun{lun}')
            # _, rr_number_raw_data, _ = issue_40F9_to_get_rr_number_and_error_bits(1<<die, 1<<plane, block, page, page, isSLC, 0, 0, 0)
            self.read_data(lun, lba, 1)

            logger.info(f'Issue 4066 VUC to check sticky read status: {read_status}')
            self.check_sticky_read_status(die, page_type, table_index, read_status)


run = Pattern().run
if __name__ == "__main__":
    run()