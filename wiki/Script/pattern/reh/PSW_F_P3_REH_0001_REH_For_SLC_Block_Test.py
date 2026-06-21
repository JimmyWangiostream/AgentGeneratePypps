import copy
import package_root
from typing import cast, TypeAlias, List, Dict
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.exception import SIGHTING_FAIL_DATA_COMPARE_FAIL, SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH, SIGHTING_RESPONSE_UNEXPECTED
from Script.api.ufs_api.defines.bit_define import BIT10
from Script.api.ufs_api.vendor_cmd.structs import FlashSetting
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.project_api.custom_vu.lba_convert_vu import physical_address_info, logical_address_info
from Script.project_api.custom_vu.lba_convert_vu import issue_4051_to_get_physical_address, issue_4052_to_get_logical_address
from Script.project_api.custom_vu.raw_data_vu.functions import issue_4060_to_read_raw_data, issue_C060_to_write_raw_data, issue_D060_to_erase_specific_block
from Script.project_api.refresh_vu.define import VUC088Paremeter
from Script.project_api.refresh_vu.functions import issue_C088_to_start_or_stop_refresh
from Script.project_api.reh.functions import \
    READ_LAST_TABLE_TYPE, \
    create_read_last_ref_table, \
    get_page_range_by_type, \
    issue_409E_to_get_error_bit_numbers, \
    issue_40BA_to_get_error_recovery_statistics, \
    issue_D014_to_set_nand_temperature, \
    issue_D014_to_set_read_recovery_module, \
    issue_D014_to_set_last_table_content, \
    issue_40F9_to_get_rr_number_and_error_bits ,\
    get_error_recovery_record_by_steps, \
    iter_reh_steps, \
    set_read_last_table
    
from Script.project_api.reh.structs import \
    BLOCK_PAGE_TYPE ,\
    PAGE_TYPE_MAP ,\
    PAGE_TYPE, \
    NAND_MODE, \
    READ_LAST_TABLE, \
    ERROR_RECOVERY_STATISTICS_RECORD, \
    rr_number_and_error_bits
from Script.project_api.sticky_read.functions import issue_4066_force_current_read_last_as_sticky_read
from Script.project_api.sticky_read.structs import STICKY_READ_STATUS


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.param = api.shared.param
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        self.flash_setting = FlashSetting()
        self.flash_setting.from_bytes(self.flash_setting_buffer)
        self.au_size = self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size * 512
        self.total_au_size = int(self.geometry_desc.q4_total_raw_device_capacity / self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size)
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.TestPSALun = 0
        self.TestEM1Lun = 1
        self.write_record = api.get_empty_write_record()
        self.read_last_ref_table: Dict[int, READ_LAST_TABLE_TYPE] = create_read_last_ref_table(self.flash_setting.Max_Fdevice)
        self.error_ERS_Message: List[str] = []
        pass

    def step1(self) -> None:
        logger.flow(1, f'Config LUN{self.TestPSALun} to normal and LUN{self.TestEM1Lun} to EM1')
        self.set_LUN_configuration()

        logger.flow(2, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
        issue_C088_to_start_or_stop_refresh(bParameter0=VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)

        logger.flow(2, f'Issue D014 op2 VUC to set read last table')
        set_read_last_table(maxDie=self.flash_setting.Max_Fdevice, read_last_table=self.read_last_ref_table)

        logger.flow(3, f'Issue vu 4066 to force read last as sticky read')
        for die in range(self.flash_setting.Max_Fdevice):
            for page_type in PAGE_TYPE:
                arc = random.randint(0, 2)
                self.force_read_last_as_sticky_read(die, page_type, arc, READ_LAST_TABLE.LAST_TABLE_1)

        for lun in [self.TestEM1Lun, self.TestPSALun]:
        # for lun in [self.TestEM1Lun]:
            length = self.slc_vb_size

            self.pre_condition_flow(lun, length)
        
            temp = (random.randint(-37, 125) & 0xFF)
            logger.flow(4, f'Issue D014 op8 VUC to set NAND temperature enable, temperature = {temp}')
            issue_D014_to_set_nand_temperature(isEnable =1, temperature = temp)

            logger.flow(5, f'Issue 40BA VUC to get backup ERS value')
            _, bk_ers = issue_40BA_to_get_error_recovery_statistics()

            isSLC = NAND_MODE.SLC_BLOCK.value
            isPSA = 1 if lun == self.TestPSALun else 0

            error_count = 150

            for b, s in iter_reh_steps(BLOCK_PAGE_TYPE.SLC_BLOCK_SLC_PAGE):
                if b >= 9: 
                    continue

                logger.flow(7, f'Host write 1VB data size for LUN {lun}')
                api.sequential_write(lun=lun, start_lba=0, total_size=length, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                
                lba = random.randint(0, length-1)

                logger.flow(7, f'Issue 4051 VUC to get PBA from LBA({lba})')
                _,pca = issue_4051_to_get_physical_address(lun, lba)
                page = pca.page.value

                logger.flow(8, f'Flip {error_count} error bit count in SLC page {page}')
                self.flipbit_on_SLC_single_page(pca.die.value, pca.plane.value, pca.physical_block_number_w_BBT.value, pca.page.value, error_count, isPSA)

                logger.flow(9, f'Issue D014 VUC to make and recover UECC on SLC block\'s SLC page with big step: {b}, small step: {s}')
                _ = issue_D014_to_set_read_recovery_module(
                    die = pca.die.value, 
                    bigIndex=b, 
                    smallIndex=s, 
                    nandMode= NAND_MODE.SLC_BLOCK.value, 
                    isSpeciBlock=1, 
                    block=pca.virtual_block_number.value, 
                    isPSA=isPSA)
                

                logger.flow(10, f'Issue host read 4K size from LBA')
                self.read_data(lun, lba, 1)
                
                logger.flow(11, f'Issue 40F9 VUC to get error step in REH')
                _, rr_number_raw_data, count = issue_40F9_to_get_rr_number_and_error_bits(1<<pca.die.value, 1<<pca.plane.value, pca.virtual_block_number.value, page, page, isSLC, 0, 0, 0)
                rr_number_step = rr_number_and_error_bits(rr_number_raw_data[0: len(rr_number_and_error_bits().payload)])
            
                logger.flow(12, f'Compare big step and small step')
                if not (rr_number_step.bigStep.value == b and rr_number_step.smallStep.value == s and rr_number_step.maxErrorBits.value > 0):
                    logger.error_lb(f'Host issue vu 40F9 to get rr number and error bit')
                    logger.error_fp(f'Expect big step = {b}, small step = {s} and max error bit > 0,' 
                                    f'but 40F9 big step = {rr_number_step.bigStep.value} and small step = {rr_number_step.smallStep.value},'
                                    f'max error bit = {rr_number_step.maxErrorBits.value},'
                                    f'page = {page}, page type =  {page_type.label}'
                    )
                    raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
            
                logger.flow(13, f'Issue 40BA VUC to get current ERS value')
                _, ers = issue_40BA_to_get_error_recovery_statistics()

                logger.flow(14, f'Compare ERS value with backup ERS')
                rec = get_error_recovery_record_by_steps(b, s, isSLC, isPSA)
                if rec != None:
                    val = self.get_ers_value(die = pca.die.value, plane = pca.plane.value, rec = rec, payload = bytearray(ers.payload))
                    org_val = self.get_ers_value(die = pca.die.value, plane = pca.plane.value, rec = rec, payload = bytearray(bk_ers.payload))
                    logger.info(f'D014 op0 {b}-{s} ERS {rec.name} backup value= {org_val}, current value = {val}')
                    if(val <= org_val):
                        self.error_ERS_Message.append(f'Expect current value = {val} is greater than original value = {org_val} in ERS {rec.name} {b}-{s} for LUN{lun}')

                bk_ers = ers

            # logger.flow(15, f'Issue read command to compare data') 
            # api.read_compare(self.write_record, api.CompareMethod.HW_COMPARE)

            if(lun == self.TestPSALun):
                logger.flow(16, 'Set bPSAState as Off to interrupt PSA flow and check FW internal state, bPSAState should be off and FW internal state should be interrupt(0x01)')
                api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.OFF)
                self.set_LUN_configuration()
        
            logger.flow(17, f'Issue D014 op8 VUC to set NAND temperature disable, temperature = {temp}')
            issue_D014_to_set_nand_temperature(isEnable =0, temperature = temp)

        logger.flow(18, 'Issue C088 to start refrseh')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        
        if self.error_ERS_Message:
            for err in self.error_ERS_Message:
                logger.error(err)
            logger.error_lb(f'Host issue vu 40BA to get error recovery statistic')
            logger.error_fp(f'Expect all the current values in ERS are greater than original values, but verification failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        
        pass

    def post_process(self) -> None:
        pass

    def set_LUN_configuration(self) -> None:
        config_desc = api.get_config_descriptors(print = True)
        lun_num_per_desc = 8
        au_size = (self.total_au_size)//2

        for index in range(int(self.max_number_lu/lun_num_per_desc)):
            config_desc[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            config_desc[index].header.b3_boot_enable = api.BootEnable.BOOT_DISABLE
            for unit in range(lun_num_per_desc):
                config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.DISABLE
                config_desc[index].units[unit].l4_num_alloc_units = 0
                config_desc[index].units[unit].b9_logical_block_size = 0
                if index == 0 and unit == self.TestPSALun: # LUN 0
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[index].units[unit].l4_num_alloc_units = au_size
                    config_desc[index].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit == self.TestEM1Lun: # LUN 1
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_desc[index].units[unit].l4_num_alloc_units = au_size if au_size < self.geometry_desc.l44_enhanced1_max_n_alloc_u else self.geometry_desc.l44_enhanced1_max_n_alloc_u
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

    def read_data(self, lun:int, lba:int, length:int) -> None:
        logger.info(f'Sequence read data LUN:{lun}, LBA:{lba}, length:{length}')
        start = lba
        offset = 0
        while offset < length:
            size = 0xffff
            if(offset + size > length):
                size = length - offset
            w = ExecuteCMD.Read10()
            w.assign(lun = lun, lba=lba, length=size, fua=0).enqueue()
            offset += size
            lba = start+offset
        ExecuteCMD.send()

    def get_ers_value(self, die:int, plane:int, rec:ERROR_RECOVERY_STATISTICS_RECORD, payload: bytearray)->int:
        start = rec.offset+die*self.flash_setting.Plane_Per_Die*rec.occupies+plane*rec.occupies
        val = int.from_bytes(payload[start: start+rec.occupies], byteorder='little')
        return val
    
    def force_read_last_as_sticky_read(self, die:int, page_type:int, arc:int, table_index:int) -> None:
        _, sr = issue_4066_force_current_read_last_as_sticky_read(die, page_type, 0, table_index, arc)
        if sr.result.value == STICKY_READ_STATUS.FAILED:
            logger.error_lb(f'Host issue vu 4066 to force read last as sticky read')
            logger.error_fp(f'Expect the status value is success, but failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def pre_condition_flow(self, lun: int, length:int)->None:
        if lun == self.TestEM1Lun:
            api.sequential_write(lun=lun, start_lba=0, total_size=length, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        elif lun == self.TestPSALun:
            set_dPSADataSize_value = self.param.gDevice.l37_psa_max_data_size
            api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=set_dPSADataSize_value)

            unmap = ExecuteCMD.Unmap()
            unmap.assign(lun=self.TestPSALun, lba=0, length=self.param.gUnit[self.TestPSALun].q11_logical_block_count)
            ExecuteCMD.enqueue(unmap)

            ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True).enqueue()
            ExecuteCMD.send()

            api.sequential_write(lun=lun, start_lba=0, total_size=length, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        pass

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

    def check_if_trigger_reh_refresh(self, refresh_vb:int) -> None:
        BOOKING_IN_HP = BIT10
        REH_BOOKING = 6
        rsp, bookingQ = project_api.issue_40C5_to_get_booking_queue()
        reh_user_count = 0
        logger.info(f'LogicalVBNumberInBookingQueue = {bookingQ.LogicalVBNumberInBookingQueue.value}')
        if bookingQ.LogicalVBNumberInBookingQueue.value != 0:
            for idx in range(bookingQ.LogicalVBNumberInBookingQueue.value):
                logger.info(f'VB = {bookingQ.BookingQueueVB[idx].LogicalVBNumber.value}, Booking user = 0x{bookingQ.BookingQueueVB[idx].TheBookingUser.value:04X}')
                if bookingQ.BookingQueueVB[idx].TheBookingUser.value == (REH_BOOKING | BOOKING_IN_HP) and bookingQ.BookingQueueVB[idx].LogicalVBNumber.value == refresh_vb:
                    reh_user_count += 1
        if reh_user_count == 0:
            logger.error_lb(f'Expect REH refresh vb in progress, booking Q should contain booking user EH_BOOKSIGNALUECC_BOOKING_0(6) with BOOKING_IN_HP(BIT10)')
            logger.error_fp(f'Booking Q does not contain booking user EH_BOOKSIGNALUECC_BOOKING_0(6) with BOOKING_IN_HP(BIT10)')
            # raise SIGHTING_FAIL_DATA_COMPARE_FAIL


run = Pattern().run
if __name__ == "__main__":
    run()