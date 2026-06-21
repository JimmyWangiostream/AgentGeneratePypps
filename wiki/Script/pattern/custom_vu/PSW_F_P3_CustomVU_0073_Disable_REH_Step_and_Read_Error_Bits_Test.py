from enum import IntEnum

import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.exception import SIGHTING_RESPONSE_UNEXPECTED, SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
from Script.api.ufs_api.defines.constant_define import DATA_SIZE_20K_BYTE
from Script.lib.sdk_lib.user.constant import DATA_SIZE_16K_BYTE
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
import random
from typing import Tuple, TypeAlias, List, Dict, cast
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api.vendor_cmd.structs import PCA, FlashSetting
from Script.project_api.custom_vu.lba_convert_vu import physical_address_info
from Script.project_api.custom_vu.lba_convert_vu import issue_4051_to_get_physical_address
from Script.project_api.custom_vu.lba_convert_vu.functions import issue_4052_to_get_logical_address
from Script.project_api.refresh_vu.define import VUC088Paremeter
from Script.project_api.refresh_vu.functions import issue_C088_to_start_or_stop_refresh
from Script.project_api.reh.functions import create_read_last_ref_table, get_page_range_by_type, issue_4014_to_get_ecc_result_for_all_step, issue_40F9_to_get_rr_number_and_error_bits, issue_D014_to_alloc_release_codeword_buffer_to_save_REH_info, issue_D014_to_en_dis_read_recovery_module, issue_D014_to_set_last_table_content, issue_D014_to_set_read_recovery_module, \
    get_error_number_info_record_by_steps, \
    iter_reh_steps, rr_number_and_error_bits, set_read_last_table
from Script.project_api.reh.structs import NAND_MODE, BLOCK_PAGE_TYPE, PAGE_TYPE_MAP, READ_LAST_TABLE, PAGE_TYPE
from Script.project_api.custom_vu.raw_data_vu.functions import issue_4060_to_read_raw_data, issue_C060_to_write_raw_data
from Script.project_api.sticky_read.functions import issue_4066_force_current_read_last_as_sticky_read, issue_4066_get_sticky_read_status_and_offset, issue_4066_to_dis_en_sticky_read
from Script.project_api.sticky_read.structs import STICKY_READ_OUTPUT_STATUS, STICKY_READ_STATUS

_sdk = api.shared.sdk

class STICKY_READ_SETTING(IntEnum):
    DISABLE = 0
    ENABLE = 1

ReadLastTableDict = Dict[READ_LAST_TABLE, List[int]]
READ_LAST_TABLE_TYPE= Dict[PAGE_TYPE, ReadLastTableDict]   # die0、die1…的最外層型別

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.param = api.shared.param
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        self.flash_setting = FlashSetting()
        self.flash_setting.from_bytes(self.flash_setting_buffer)
        self.total_au_size = int(self.geometry_desc.q4_total_raw_device_capacity / self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size)
        self.total_capacity_4K = int(self.geometry_desc.q4_total_raw_device_capacity/8)
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.write_record = api.get_empty_write_record()
        self.read_last_ref_table: Dict[int, READ_LAST_TABLE_TYPE] = create_read_last_ref_table(self.flash_setting.Max_Fdevice)
        pass

    def step1(self) -> None:
        logger.flow(1, 'Config normal LU and EM1 LU')
        self.lun_configuration()

        logger.flow(2, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
        issue_C088_to_start_or_stop_refresh(bParameter0=VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)

        logger.flow(3, f'Sequential write LUN0 and LUN1 with 1VB size')
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=self.tlc_vb_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=self.slc_vb_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        planeBitMap = (1 << self.flash_setting.Plane_Per_Die) - 1

        logger.flow(4, f'Issue D014 op2 VUC to set read last table')
        set_read_last_table(maxDie=self.flash_setting.Max_Fdevice, read_last_table=self.read_last_ref_table)

        logger.flow(5, f'Issue 4066 VUC to enable sticky read feature')
        self.set_sticky_read_en_dis(STICKY_READ_SETTING.ENABLE)

        logger.flow(6, f'Issue D014 option 7 VUC to allocate codeword buffer')
        _ = issue_D014_to_alloc_release_codeword_buffer_to_save_REH_info(0x0)  

        for lun in [self.TestNormalLun, self.TestEM1Lun]:
        # for lun in [self.TestNormalLun]:

            length = self.slc_vb_size if lun == self.TestEM1Lun else self.tlc_vb_size
            isSLC = 1 if lun == self.TestEM1Lun else 0

            lba = random.randint(lun, length-1)

            logger.flow(7, f'Issue 4051 VUC to get PBA from LUN{lun} and LBA = ({lba})')
            _,pca = issue_4051_to_get_physical_address(lun, lba)

            die = pca.die.value
            page = pca.page.value
            block = pca.virtual_block_number.value
            plane = pca.plane.value
            table_index= random.choice([READ_LAST_TABLE.LAST_TABLE_1,READ_LAST_TABLE.LAST_TABLE_2])

            logger.flow(8, f'Issue vu 4066 to force read last as sticky read')
            for page_type in PAGE_TYPE:
                arc = random.randint(0, 2)
                self.force_read_last_as_sticky_read(die, page_type, arc, table_index)

            if lun == self.TestNormalLun:
                block_page_range = [ BLOCK_PAGE_TYPE.TLC_BLOCK_TLC_PAGE, BLOCK_PAGE_TYPE.TLC_BLOCK_SLC_PAGE, BLOCK_PAGE_TYPE.TLC_BLOCK_MLC_PAGE]
                # block_page_range = [BLOCK_PAGE_TYPE.TLC_BLOCK_TLC_PAGE]
            else: 
                block_page_range = [BLOCK_PAGE_TYPE.SLC_BLOCK_SLC_PAGE]

            for block_type in block_page_range:
                reh_steps: List[Tuple[int, int]] = list(iter_reh_steps(type=BLOCK_PAGE_TYPE(block_type)))
                disable_reh_steps: List[Tuple[int, int]] = self.filter_disable_reh_steps(reh_steps)
                for page_type in PAGE_TYPE_MAP.get(BLOCK_PAGE_TYPE(block_type), []):
                    page = get_page_range_by_type(page_type)

                    logger.info(f'Select {page_type.label} page = {page}')
                    
                    # logger.flow(9, f'Issue 4014 option 2 VUC to get result for all plane on die {die}')
                    # _, payload = issue_4014_to_get_ecc_result_for_all_step(die = die)
                    # dumpfile("4014_opt2_0.bin", payload)

                    if page_type in [PAGE_TYPE.PAGE_SLC_LP, PAGE_TYPE.PAGE_POR_DSLC, PAGE_TYPE.PAGE_POR_SSLC]:
                        nand_type = 0
                    elif page_type in [PAGE_TYPE.PAGE_MLC_LP, PAGE_TYPE.PAGE_MLC_UP]:
                        nand_type = 1
                    else:
                        nand_type = 2

                    for cb, cs in disable_reh_steps:
                        if(cb <= 2):
                            disBigMap = 0xFFFFFFFF
                            disSmallMap = 0xFFFFFFFF & ~(1 << cs)
                        else:
                            disBigMap = 0xFFFFFFFF & ~(1 <<cb)
                            disSmallMap = 0xFFFFFFFF
                        logger.flow(10, f'Issue D014 op1 with page_type = {nand_type}, big step bit map: {disBigMap:#10X}, small step bit map: {disSmallMap:#10X}')
                        issue_D014_to_en_dis_read_recovery_module(pageType=nand_type, bigStepBitMap=disBigMap, smallStepBitMap=disSmallMap)

                        for b, s in reh_steps:
                            logger.flow(11, f'Issue D014 op0 with big step: {b}, small step: {s} to make and recover UECC on {block_type.label}')
                            _ = issue_D014_to_set_read_recovery_module(
                                die = die, 
                                bigIndex=b, 
                                smallIndex=s, 
                                nandMode=isSLC, 
                                isSpeciBlock=0, 
                                block=0, 
                                isPSA=0)

                            logger.flow(11, f'Issue 4052 VUC to get LBA form PBA')
                            _, la = issue_4052_to_get_logical_address(pca.die.value, pca.plane.value, pca.virtual_block_number.value, page, pca.offset.value)
                            logger.info(f'page = {page}, offset = {pca.offset.value}, lun = {la.lun.value}, lba = {la.lba.value}')
                        
                            if not (la.lun.value == lun and la.lba.value >= 0 and la.lba.value < length):
                                raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

                            logger.flow(12, f'Issue host read 4K size from LUN{la.lun.value} LBA = {la.lba.value}')
                            ExecuteCMD.Read10().assign(lun = la.lun.value, lba=la.lba.value, length=1, fua=0).enqueue()
                            ExecuteCMD.send()

                            logger.flow(13, f'Issue 40F9 VUC get rr number')
                            _, rr_number_raw_data, _ = issue_40F9_to_get_rr_number_and_error_bits(1<<die, planeBitMap, block, page, page, isSLC, 0, 0, 0)
                            rr_number_step = rr_number_and_error_bits(rr_number_raw_data[0: len(rr_number_and_error_bits().payload)])
                            logger.info(f'{b} - {s} VU 40F9 response big step = {rr_number_step.bigStep.value} and small step = {rr_number_step.smallStep.value} max error bits = {rr_number_step.maxErrorBits.value} on page = {page} , page type =  {page_type.label}')

                            
                            logger.flow(14, f'Issue 4014 option 2 VUC to get result for all plane on die {die}')
                            _, payload = issue_4014_to_get_ecc_result_for_all_step(die = die)
                            dumpfile("4014_opt2_1.bin", payload)

                            logger.flow(15, f'Verify 4014 option 2 output data')
                            self.check_error_number_info(b, s, cb, cs, isSLC, plane, payload)
                            

        logger.flow(16, f'Issue D014 option 7 VUC to release codeword buffer')
        _ = issue_D014_to_alloc_release_codeword_buffer_to_save_REH_info(0x1)  

        pass
    
    def post_process(self) -> None:
        pass

    def lun_configuration(self) -> None:
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

    def write_raw_data_for_all_plane(self, die:int, block:int, page:int, isSLC:int, block_type:BLOCK_PAGE_TYPE)->None:
        if isSLC or block_type == BLOCK_PAGE_TYPE.TLC_BLOCK_SLC_PAGE.value:
            write_data = bytearray((16 * 1024 + 16 * 4))
        elif block_type == BLOCK_PAGE_TYPE.TLC_BLOCK_MLC_PAGE.value:
            write_data = bytearray(DATA_SIZE_20K_BYTE*2)  
        else:
            write_data = bytearray(DATA_SIZE_20K_BYTE*3)     
        for i in range(len(write_data)):
            write_data[i] = 0xAA

        for plane in range(self.flash_setting.Plane_Per_Die):
            _ = issue_C060_to_write_raw_data(Ce=die, Plane=plane, Block=block, Page=page, SLC_Enable=isSLC, Ecc_Enable=1, datapayload=write_data)
        
        pass
    # b/s = gen error big/small step,  cb/cs = mask big/small step
    def check_error_number_info(self, b:int, s:int, cb:int, cs:int, isSLC:int, plane:int, payload: bytearray)->None:
        error_number : List[int] = []
        rec = get_error_number_info_record_by_steps(b,s, isSLC)
        if rec :
            start = rec.index*self.flash_setting.Plane_Per_Die*2
            offset = 0
            for p in range(self.flash_setting.Plane_Per_Die):
                error_number.append(int.from_bytes(payload[start+offset:start+offset+2], 'little'))
                offset +=2

            logger.info(f'Issue D014 option2 to mask {cb}-{cs} then issue 4014 option 2 to get ecc number {b}-{s} {rec.name} = {error_number}')
            if (cb <= 2 and b == cb and s == cs) or (cb > 2 and b == cb):
                if not (len(error_number) > 0 and all(v == 0 for v in error_number)):
                    logger.error_lb(f'Issue 4014 option 2 VUC to get error number information')
                    logger.error_fp(f'{b} - {s} {rec.name} disabled , Expected all error bit = 0  but current = {error_number}')
                    raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
            else:
                if not (len(error_number) > 0 and all(v >0 and v < 0x3FFF for v in error_number)):
                    logger.error_lb(f'Issue 4014 option 2 VUC to get error number information')
                    logger.error_fp(f'{b} - {s} {rec.name} :Expected non-zero and non-0x3FFF on all planes, but current = {error_number}')
                    raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

    def set_sticky_read_en_dis(self, setting:STICKY_READ_SETTING) -> None:
        _, result = issue_4066_to_dis_en_sticky_read(STICKY_READ_SETTING.ENABLE)
        if result == STICKY_READ_STATUS.FAILED:
            logger.error_lb(f'Host issue vu 4066 to enable sticky read feature')
            logger.error_fp(f'Expect the result value is success, but failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def force_read_last_as_sticky_read(self, die:int, page_type:int, arc:int, table_index:int) -> None:
        _, sr = issue_4066_force_current_read_last_as_sticky_read(die, page_type, 0, table_index, arc)
        if sr.result.value == STICKY_READ_STATUS.FAILED:
            logger.error_lb(f'Host issue vu 4066 to force read last as sticky read')
            logger.error_fp(f'Expect the status value is success, but failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def filter_disable_reh_steps(self, steps: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        seen_over_2 = set()          # 用來記錄已出現過的 big step (>2)
        filtered: List[Tuple[int, int]] = []

        for big, small in steps:
            if big > 2:
                # 只要這個 big step 第一次出現就加入，之後直接略過
                if big not in seen_over_2:
                    filtered.append((big, small))
                    seen_over_2.add(big)
            else:
                # big <= 2 → 不需要去重，直接加入
                filtered.append((big, small))

        return filtered

run = Pattern().run
if __name__ == "__main__":
    run()