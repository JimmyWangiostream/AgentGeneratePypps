import copy
from enum import IntEnum

import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.cmd_seq.response import get_asc_ascq_description, get_scsi_status_str, get_sense_key_str
from Script.api.exception import SIGHTING_RESPONSE_UNEXPECTED, SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
from Script.api.ufs_api.defines.constant_define import DATA_SIZE_20K_BYTE
from Script.api.ufs_api.defines.enum_define import ScsiStatus, UPIUResponse
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
from Script.project_api.reh.functions import create_read_last_ref_table, get_page_range_by_type, issue_4014_to_get_ecc_result_for_all_step, issue_4014_to_get_REH_tracing_info, issue_4014_to_get_sure_ARC_data, issue_409E_to_get_error_bit_numbers, issue_40F9_to_get_rr_number_and_error_bits, issue_D014_to_en_dis_read_recovery_module, issue_D014_to_set_last_table_content, issue_D014_to_set_read_recovery_module, \
    get_error_number_info_record_by_steps, \
    issue_D014_to_alloc_release_codeword_buffer_to_save_REH_info, iter_reh_steps, rr_number_and_error_bits, set_read_last_table
from Script.project_api.reh.structs import NAND_MODE, BLOCK_PAGE_TYPE, PAGE_TYPE_MAP, READ_LAST_TABLE, PAGE_TYPE
from Script.project_api.custom_vu.raw_data_vu.functions import issue_4060_to_read_raw_data, issue_C060_to_write_raw_data, issue_D060_to_erase_specific_block
from Script.project_api.sticky_read.functions import issue_4066_force_current_read_last_as_sticky_read, issue_4066_get_sticky_read_status_and_offset, issue_4066_to_dis_en_sticky_read
from Script.project_api.sticky_read.structs import STICKY_READ_OUTPUT_STATUS, STICKY_READ_STATUS

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
        
        logger.flow(4, f'Issue D014 option 7 VUC to release codeword buffer (action = 1), expect resp fail')
        response = issue_D014_to_alloc_release_codeword_buffer_to_save_REH_info(0x1, keep_error= True)
        if not (response.upiu.b6_response == UPIUResponse.TARGET_FAILURE and response.upiu.b7_status == ScsiStatus.CHECK_CONDITION):
            logger.error_lb(f'Issue D014 option 7 VUC to release codeword buffer')
            logger.error_fp(f'Expect response fail, but status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        

        logger.flow(5, f'Issue D014 op2 VUC to set read last table')
        set_read_last_table(maxDie=self.flash_setting.Max_Fdevice, read_last_table=self.read_last_ref_table)

        for lun in [self.TestNormalLun, self.TestEM1Lun]:
        # for lun in [self.TestNormalLun]:

            length = self.slc_vb_size if lun == self.TestEM1Lun else self.tlc_vb_size
            isSLC = 1 if lun == self.TestEM1Lun else 0

            lba = random.randint(lun, length-1)

            logger.flow(6, f'Issue 4051 VUC to get PBA from LUN{lun} and LBA = ({lba})')
            _,pca = issue_4051_to_get_physical_address(lun, lba)

            die = pca.die.value
            page = pca.page.value
            block = pca.virtual_block_number.value
            plane = pca.plane.value

            if lun == self.TestNormalLun:
                block_page_range = [ BLOCK_PAGE_TYPE.TLC_BLOCK_TLC_PAGE, BLOCK_PAGE_TYPE.TLC_BLOCK_MLC_PAGE, BLOCK_PAGE_TYPE.TLC_BLOCK_SLC_PAGE]
                # block_page_range = [BLOCK_PAGE_TYPE.TLC_BLOCK_TLC_PAGE]
            else: 
                block_page_range = [BLOCK_PAGE_TYPE.SLC_BLOCK_SLC_PAGE]

            for block_type in block_page_range:
                for page_type in PAGE_TYPE_MAP.get(BLOCK_PAGE_TYPE(block_type), []):
                    _,pca = issue_4051_to_get_physical_address(lun, lba)
                    die = pca.die.value
                    page = pca.page.value
                    block = pca.virtual_block_number.value
                    plane = pca.plane.value
                    page = get_page_range_by_type(page_type)
                    logger.info(f'Verify block = {block_type.label}, page_type = {page_type.label}, page = {page}')
                    reh_steps: List[Tuple[int, int]] = list(iter_reh_steps(type=BLOCK_PAGE_TYPE(block_type)))

                    logger.flow(7, f'Issue D014 option 7 VUC to allocate codeword buffer')
                    _ = issue_D014_to_alloc_release_codeword_buffer_to_save_REH_info(0x0)

                    # check empty
                    logger.flow(8, f'Issue 4014 op1 VUC to get REH tracing information in M_RAM')
                    _, reh_tracing = issue_4014_to_get_REH_tracing_info(die)

                    logger.flow(9, f'Verify REH tracing data to be empty')
                    if not all( d == 0 for d in reh_tracing): 
                        logger.error_lb(f'Issue 4014 op1 VUC to get REH tracing data')
                        logger.error_fp(f'Expected REH tracing data to be empty, but it failed verification.')
                        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
                    
                    logger.flow(10, f'Issue 4014 op5 VUC to get SURE ARC data')
                    _, arc_data = issue_4014_to_get_sure_ARC_data(die)

                    logger.flow(11, f'Verify SURE ARC data to be empty')
                    if not all( d == 0 for d in arc_data): 
                        logger.error_lb(f'Issue 4014 op5 VUC to get SURE ARC data')
                        logger.error_fp(f'Expected SURE ARC data to be empty, but it failed verification.')
                        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

                    logger.info(f'Select {page_type.label} page = {page}')
                    logger.flow(12, f'Issue 4052 VUC to get LBA form PBA')
                    _, la = issue_4052_to_get_logical_address(pca.die.value, pca.plane.value, pca.virtual_block_number.value, page, pca.offset.value)
                    logger.info(f'page = {page}, offset = {pca.offset.value}, lun = {la.lun.value}, lba = {la.lba.value}')
                    
                    
                    if not (la.lun.value == lun and la.lba.value >= 0 and la.lba.value < length):
                        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
                    
                    
                    logger.flow(12, f'Generate read fail for all REH step')
                    self.gen_read_fail(die, block, page, la.lun.value, la.lba.value, isSLC, length, reh_steps)

                    logger.flow(13, f'Issue 4014 op1 VUC to get REH tracing information in M_RAM')
                    _, reh_tracing = issue_4014_to_get_REH_tracing_info(die)

                    logger.flow(14, f'Verify REH Tracing data to be non-empty')
                    if all( d == 0 for d in reh_tracing): 
                        logger.error_lb(f'Issue 4014 op1 VUC to get REH Tracing data')
                        logger.error_fp(f'Expected REH tracing data to be non-empty, but it failed verification.')
                        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
                    
                    logger.flow(15, f'Issue 4014 op5 VUC to get SURE ARC data')
                    _, arc_data = issue_4014_to_get_sure_ARC_data(die)

                    logger.flow(16, f'Verify SURE ARC data to be non-empty')
                    if all( d == 0 for d in arc_data):
                        logger.error_lb(f'Issue 4014 op5 VUC to get SURE ARC data')
                        logger.error_fp(f'Expected SURE ARC data to be non-empty, but it failed verification.')
                        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
                    

                    logger.flow(17, f'Issue D014 option 7 VUC to release codeword buffer')
                    _ = issue_D014_to_alloc_release_codeword_buffer_to_save_REH_info(0x1)  

                    logger.flow(18, f'Issue 4014 op1 VUC to get REH tracing information in M_RAM')
                    _, reh_tracing = issue_4014_to_get_REH_tracing_info(die)

                    logger.flow(19, f'Verify REH tracing data to be empty')
                    if not all( d == 0 for d in reh_tracing): 
                        logger.error_lb(f'Issue 4014 op1 VUC to get REH tracing data')
                        logger.error_fp(f'Expected REH tracing data to be empty, but it failed verification.')
                        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
                    
                    logger.flow(20, f'Issue 4014 op5 VUC to get SURE ARC data')
                    _, arc_data = issue_4014_to_get_sure_ARC_data(die)

                    logger.flow(21, f'Verify SURE ARC data to be empty')
                    if not all( d == 0 for d in arc_data): 
                        logger.error_lb(f'Issue 4014 op5 VUC to get SURE ARC data')
                        logger.error_fp(f'Expected SURE ARC data to be empty, but it failed verification.')
                        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
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

    def check_error_number_info(self, b:int, s:int, cb:int, cs:int, isSLC:int, payload: bytearray)->None:
        error_number : List[int] = []
        rec = get_error_number_info_record_by_steps(b,s, isSLC)
        if rec :
            start = rec.index*self.flash_setting.Plane_Per_Die*2
            offset = 0
            for plane in range(self.flash_setting.Plane_Per_Die):
                error_number.append(int.from_bytes(payload[start+offset:start+offset+2], 'little'))
                offset +=2

            logger.info(f'Issue 4014 option 2 {rec.name} = {error_number}')
            if b == cb and s == cs:
                if not (len(error_number) > 0 and all(v == 0 for v in error_number)):
                    logger.error_lb(f'Issue 4014 option 2 VUC to get error number information')
                    logger.error_fp(f'{b} - {s} {rec.name} disabled , Expected all error bit = 0  but current = {error_number}')
                    # raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
            else:
                if not (len(error_number) > 0 and all(v >0 and v < 0x3FFF for v in error_number)):
                    logger.error_lb(f'Issue 4014 option 2 VUC to get error number information')
                    logger.error_fp(f'{b} - {s} {rec.name} :Expected non-zero and non-0x3FFF across all planes, but current data = {error_number}')
                    # raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH


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
    
    def gen_read_fail(self, die:int, block:int, page:int, lun:int, lba:int, isSLC:int, length:int, reh_steps:List[Tuple[int, int]]) -> None:
        for b, s in reh_steps:
            _,pca = issue_4051_to_get_physical_address(lun, lba)
            block = pca.virtual_block_number.value

            if lun == self.TestEM1Lun:
                error_count = 150
                api.sequential_write(lun=lun, start_lba=0, total_size=length, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                logger.info(f'Flip {error_count} error bit count in SLC page {page}')
                self.flipbit_on_SLC_single_page(pca.die.value, pca.plane.value, pca.physical_block_number_w_BBT.value, pca.page.value, error_count, 0)

            logger.info(f'Issue D014 VUC with big step: {b}, small step: {s} to make and recover UECC')
            _ = issue_D014_to_set_read_recovery_module(
                die = die, 
                bigIndex=b, 
                smallIndex=s, 
                nandMode=isSLC, 
                isSpeciBlock=0, 
                block=0, 
                isPSA=0)
            
            # planeBitMap = (1 << self.flash_setting.Plane_Per_Die) - 1
            # _, rr_number_raw_data, _ = issue_40F9_to_get_rr_number_and_error_bits(1<<die, planeBitMap, block, page, page, isSLC, 0, 0, 0)

            logger.info(f'Issue host read 4K size from LUN{lun} LBA = {lba}')
            ExecuteCMD.Read10().assign(lun = lun, lba=lba, length=1, fua=0).enqueue()
            ExecuteCMD.send()

    def flip_bits_one_per_byte(
        self, 
        raw: bytearray,
        *,
        total_bits: int = 500,
        block_index: int = 0,
        seed: int | None = None,
    ) -> List[int]:
        """
        在 *raw* 中的第 ``block_index`` 個 4 KB 區塊內，隨機翻轉 ``total_bits`` 個位元。
        - 每個 byte 只會翻 1 個 bit（使用 ``random.sample`` 產生不重複的 byte 索引）。
        - ``block_index = 0`` → 位元組 0  ~ 4095（原本行為）。
        - ``block_index = 1`` → 位元組 4096 ~ 8191（第 2 個 4 KB）。
        - 以此類推...

        參數
        ----------
        raw : bytearray
            會被原位元 (in‑place) 修改的緩衝區。
        total_bits : int, default 500
            要翻轉的位元數目。必須 ≤ 本區塊可用的 byte 數（每個 byte 最多 1 個 bit）。
        block_index : int, default 0
            想要操作的 4 KB 區塊編號，從 0 開始計算。
        seed : int | None
            若提供，會以此 seed 建立 ``random.Random``，讓測試可重現。

        回傳
        -------
        List[int]
            所有被翻轉的全域 bit 索引（0‑based），方便列印或除錯。
        """
        if total_bits < 0:
            raise ValueError("total_bits 必須為非負整數")
        if block_index < 0:
            raise ValueError("block_index 必須為非負整數")

        # 1️⃣ 计算本区块的起始 / 结束 byte
        block_start = block_index * 4096                     # 第 N 個 4 KB 的起點
        if block_start >= len(raw):
            raise ValueError(
                f"指定的 block_index ({block_index}) 超出 raw 的長度 "
                f"(len={len(raw)} bytes)。"
            )
        # 本区块实际可用的 byte 数（若 raw 在此处就截断了）
        max_bytes = min(4096, len(raw) - block_start)

        if total_bits > max_bytes:
            raise ValueError(
                f"欲翻轉的位元數 ({total_bits}) 大於本 4 KB 區塊可用的 byte 數 "
                f"({max_bytes})。每個 byte 只能翻 1 個 bit。"
            )

        # 2️⃣ 隨機抽樣不重複的 byte 索引（相對於整個 raw 的絕對位置）
        rng = random.Random(seed)
        byte_indices = rng.sample(
            range(block_start, block_start + max_bytes), total_bits
        )

        # 3️⃣ 為每個選中的 byte 隨機挑一個 bit (0~7) 並翻轉
        flipped_bit_positions: List[int] = []
        for b_idx in byte_indices:
            bit_off = rng.randint(0, 7)                 # 0~7 之間的整數
            global_bit_idx = b_idx * 8 + bit_off        # 全域 bit 索引
            flipped_bit_positions.append(global_bit_idx)

            # XOR 使該位元翻轉
            raw[b_idx] ^= 1 << bit_off

        # 4️⃣ 返回排序好的 bit 索引（方便列印）
        flipped_bit_positions.sort()
        return flipped_bit_positions
    
    def print_bit_positions(self, indices: List[int], *, title: str = "") -> None:
        if title:
            logger.info("\n=== " + title + " ===")
        logger.info(f"{'bit_idx':>8}  {'byte_idx':>8}  {'bit_in_byte':>11}")
        logger.info("-" * 30)
        for idx in sorted(indices):
            byte_idx = idx // 8
            bit_in_byte = idx % 8          # LSB 為 0
            logger.info(f"{idx:8d}  {byte_idx:8d}  {bit_in_byte:11d}")

    def count_diff_bytes(self, a: bytearray, b: bytearray) -> int:
       
        #先比較共同長度的部分
        diff = sum(x != y for x, y in zip(a, b))

        #再把長度差額加進去（多出的部份必定不同）
        diff += abs(len(a) - len(b))
        return diff
    
    def flipbit_on_SLC(self, die:int, plane:int, block:int, page:int, flipBitCount: int, isPSA:int = 0) -> None:
        isSLC = 1
        total_page = 1103
        raw_list: List[bytearray] = []
        for p in range(total_page+1):
            logger.info(f'VU 4060 read raw data on page {p} with ECC off')
            _, raw_data = issue_4060_to_read_raw_data(Die=die, Plane=plane, Block=block, Page=p, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=isPSA)
            if p == page:
                    flip_data = copy.deepcopy(raw_data)
                    flipped = self.flip_bits_one_per_byte(flip_data, total_bits=flipBitCount, block_index=0) 
                    diffcount = self.count_diff_bytes(raw_data, flip_data)
                    logger.info(f'LP different count ={diffcount} after flip bits {flipBitCount}')
                    self.print_bit_positions(flipped, title=f"{flipBitCount} bits position")
                    raw_list.append(flip_data)
            else:
                raw_list.append(raw_data)

        #erase
        logger.flow(3, 'issue D060 to erase original data')
        issue_D060_to_erase_specific_block(Ce=die,Plane=plane,Block=block,SlcEnable=isSLC, psaEnable = isPSA)
            
        #write raw data
        for p in range(total_page+1):
            payload = raw_list[p]
            _ = issue_C060_to_write_raw_data(Ce=die, Plane=plane, Block=block, Page=p, SLC_Enable=isSLC,Ecc_Enable=0, datapayload=payload)
        
        #read raw data
        _, raw_data_1 = issue_4060_to_read_raw_data(Die=die, Plane=plane, Block=block, Page=page, SLC_Enable=isSLC, Ecc_Enable=1, Scrambler_Enable=1, PSA_Enable=isPSA)
        raw_data_11 = copy.deepcopy(raw_data_1)
        # diffcount = self.count_diff_bytes(raw_dataLP, raw_data_11)
        diffcount = self.count_diff_bytes(raw_data, raw_data_1)
        logger.info(f'LP different count ={diffcount}')
        dumpfile(f"FW_FLOW_READ.bin", raw_data_1)

        logger.flow(13, f'Issue 409E VUC with ECC information = 1 to get error bit numbers')
        _, output_409E = issue_409E_to_get_error_bit_numbers()
        error_bits_409E = [output_409E.errorBitNumber1.value, output_409E.errorBitNumber2.value, output_409E.errorBitNumber3.value, output_409E.errorBitNumber4.value]
        logger.info(f'409E error bits ={error_bits_409E}')

        _, raw_data_after_flip = issue_4060_to_read_raw_data(Die=die, Plane=plane, Block=block, Page=page, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=isPSA)
        dumpfile(f"pageLP_after.bin", raw_data_after_flip)
        diffcount = self.count_diff_bytes(raw_data, raw_data_after_flip)
        logger.info(f'LP different count ={diffcount}')

        pass

    def flipbit_on_SLC_single_page(self, die:int, plane:int, block:int, page:int, flipBitCount: int, isPSA:int = 0) -> None:
        isSLC = 1
        _, raw_data = issue_4060_to_read_raw_data(Die=die, Plane=plane, Block=block, Page=page, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=isPSA)
        dumpfile("read_raw_data.bin", raw_data)
        flip_data = copy.deepcopy(raw_data)

        flipbit = flipBitCount
        flipped = self.flip_bits_one_per_byte(flip_data, total_bits=flipbit, block_index=0) 
        diffcount = self.count_diff_bytes(raw_data, flip_data)
        logger.info(f'LP different count ={diffcount} after flip bits {flipbit}')
        
        self.print_bit_positions(flipped, title=f"{flipbit} bits position")
        logger.info(f"Flip first {flipbit} bits – done")
        logger.info(f"raw_data_flip = {len(flip_data)}") 
        write_payload = flip_data 
        #erase
        logger.flow(3, 'issue D060 to erase original data')
        issue_D060_to_erase_specific_block(Ce=die,Plane=plane,Block=block,SlcEnable=isSLC, psaEnable = isPSA)
            
        #write raw data
        dumpfile(f"write_raw_data.bin", write_payload)
        _ = issue_C060_to_write_raw_data(Ce=die, Plane=plane, Block=block, Page=page, SLC_Enable=isSLC,Ecc_Enable=0, datapayload=write_payload)
        
        #read raw data
        _, raw_data_1 = issue_4060_to_read_raw_data(Die=die, Plane=plane, Block=block, Page=page, SLC_Enable=isSLC, Ecc_Enable=1, Scrambler_Enable=1, PSA_Enable=isPSA)
        raw_data_11 = copy.deepcopy(raw_data_1)
        # diffcount = self.count_diff_bytes(raw_dataLP, raw_data_11)
        diffcount = self.count_diff_bytes(raw_data, raw_data_1)
        logger.info(f'LP different count ={diffcount}')
        dumpfile(f"FW_FLOW_READ.bin", raw_data_1)

        logger.flow(13, f'Issue 409E VUC with ECC information = 1 to get error bit numbers')
        _, output_409E = issue_409E_to_get_error_bit_numbers()
        error_bits_409E = [output_409E.errorBitNumber1.value, output_409E.errorBitNumber2.value, output_409E.errorBitNumber3.value, output_409E.errorBitNumber4.value]
        logger.info(f'409E error bits ={error_bits_409E}')

        _, raw_data_after_flip = issue_4060_to_read_raw_data(Die=die, Plane=plane, Block=block, Page=page, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=isPSA)
        dumpfile(f"pageLP_after.bin", raw_data_after_flip)
        diffcount = self.count_diff_bytes(raw_data, raw_data_after_flip)
        logger.info(f'LP different count ={diffcount}')

        pass

run = Pattern().run
if __name__ == "__main__":
    run()