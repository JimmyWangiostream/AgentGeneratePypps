import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.exception import SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
import random
from typing import TypeAlias, List, Dict, cast
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api.vendor_cmd.structs import PCA, FlashSetting
from Script.api.ufs_api.descriptors.configuration_desc.structs import ConfigDescriptor310, ConfigDescriptor400, ConfigDescriptor410
from Script.project_api.custom_vu.lba_convert_vu import physical_address_info
from Script.project_api.custom_vu.lba_convert_vu import issue_4051_to_get_physical_address
from Script.project_api.reh.functions import issue_D014_to_set_read_recovery_module, \
    issue_40F9_to_get_rr_number_and_error_bits, \
    issue_D014_to_set_last_table_content, \
    issue_409E_to_get_ECC_information, \
    issue_409E_to_get_error_bit_numbers, \
    issue_40BB_to_get_error_bit_numbers_and_read_retry_step, \
    create_read_last_ref_table ,\
    get_page_type_by_physical_page ,\
    iter_reh_steps, set_read_last_table
from Script.project_api.sticky_read.functions import issue_4066_get_sticky_read_status_and_offset, \
    issue_4066_to_dis_en_sticky_read, \
    issue_4066_force_current_read_last_as_sticky_read
from Script.project_api.reh.structs import NAND_MODE, BLOCK_PAGE_TYPE, READ_LAST_TABLE, PAGE_TYPE
from Script.project_api.sticky_read.structs import STICKY_READ_STATUS, STICKY_READ_SETTING
from Script.project_api.custom_vu.raw_data_vu.functions import issue_4060_to_read_raw_data


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
        self.write_record = api.get_empty_write_record()
        self.read_last_ref_table: Dict[int, READ_LAST_TABLE_TYPE] = create_read_last_ref_table(self.flash_setting.Max_Fdevice)
        pass

    def step1(self) -> None:
        logger.flow(1, 'Config LUN0 to normal LU and LUN1 to EM1 LU')
        self.set_LUN_configuration()

        logger.flow(2, f'Sequential write LUN0 and LUN1')
        api.sequential_write(lun=0, start_lba=0, total_size=self.tlc_vb_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.sequential_write(lun=1, start_lba=0, total_size=self.slc_vb_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        logger.flow(3, f'Issue 409E VUC with ECC information = 0 to get cw size and max error num')
        _, cw_size, max_error_num = issue_409E_to_get_ECC_information()
        if cw_size != 4096 or max_error_num != 320:
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        
        logger.flow(4, f'Issue D014 op2 VUC to set read last table')
        set_read_last_table(maxDie=self.flash_setting.Max_Fdevice, read_last_table=self.read_last_ref_table)

        for lun in range(2):
            length = self.tlc_vb_size if lun == 0 else self.slc_vb_size
            isSLC = 0 if lun ==0 else 1
                
            lba = random.randint(0, length-1)
            logger.flow(5, f'Random select LBA={lba} on LUN{lun}')

            logger.flow(6, f'Issue 4051 VUC to get PBA from LBA={lba})')
            _,pca = issue_4051_to_get_physical_address(lun, lba)

            page_type, block_type = get_page_type_by_physical_page(pca.page.value, pca.virtual_block_number.value, isSLC)

            logger.flow(6, f'Issue 4066 VUC to force current read last as sticky read)')
            table_index = READ_LAST_TABLE(random.randint(READ_LAST_TABLE.LAST_TABLE_1, READ_LAST_TABLE.LAST_TABLE_2))
            _, sr = issue_4066_force_current_read_last_as_sticky_read(pca.die.value, page_type, 0, table_index, 0)
            if sr.result.value == STICKY_READ_STATUS.FAILED:
                logger.error_lb(f'Host issue vu 4066 to force read last as sticky read')
                logger.error_fp(f'Expect the status value is success, but failed')
                raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

            logger.flow(6, f'Issue 4066 VUC to enable sticky read feature')
            self.set_sticky_read_en_dis(STICKY_READ_SETTING.ENABLE)
            
            for b, s in iter_reh_steps(type = BLOCK_PAGE_TYPE(block_type)):
                logger.flow(7, f'Issue D014 VUC op0 with big step: {b}, small step: {s} to make recovery ECC')
                if b > 2:
                    break

                _ = issue_D014_to_set_read_recovery_module(
                    die = pca.die.value, 
                    bigIndex=b, 
                    smallIndex=s, 
                    nandMode=isSLC, 
                    isSpeciBlock=1, 
                    block=pca.virtual_block_number.value, 
                    isPSA=0)
                
                logger.flow(8, f'Host read LUN{lun} LBA = {lba}')
                self.read_data(lun, lba, 1)

                logger.flow(9, f'Issue 40BB VUC to get error bit number and read retry step')
                _, output_40BB = issue_40BB_to_get_error_bit_numbers_and_read_retry_step(pca.die.value)

                logger.flow(10, f'Check 40BB output, result !=0 and errorBits != 0x3FFF and big/small step is equal to D014 big/small step')
                if b == 0 and s != 0 and lun == 0:
                    if not (output_40BB.reReadResult.value == 0 and output_40BB.reReadErrorBits.value != 0x3FFF and \
                        output_40BB.reReadBigStep.value == b  and output_40BB.reReadSmallStep.value == s and \
                        output_40BB.readLastResult.value == 1 and output_40BB.readLastErrorBits.value == 0x3FFF):
                        logger.error_lb(f'Issue 40BB to check Re-Read step result')
                        logger.error_fp(f'Expected re-read : result = 0, error bits != 0x3FFF, big step = {b}, small step = {s}, and\
                                        read last: result = 1 , read last error bits == 0x3FFF, but current\
                                        re-read: result ={output_40BB.reReadResult.value}, Error Bit = {output_40BB.reReadErrorBits.value:#06x}, big step = {output_40BB.reReadBigStep.value}, small step = {output_40BB.reReadSmallStep.value}, and\
                                        read last: result ={output_40BB.readLastResult.value}, Error Bit = {output_40BB.readLastErrorBits.value:#06x}')
                        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
                    
                elif b == 1 and lun == 0:
                    if not (output_40BB.readLastResult.value == 0 and output_40BB.readLastErrorBits.value != 0x3FFF and \
                        output_40BB.readLastBigStep.value == b  and output_40BB.readLastSmallStep.value == s and \
                        output_40BB.reReadResult.value == 1 and output_40BB.reReadErrorBits.value == 0x3FFF):
                        logger.error_lb(f'Issue 40BB to check Read last step result')
                        logger.error_fp(f'Expected re-read : result = 1, error bits == 0x3FFF,  and\
                                        read last: result = 0 , read last error bits != 0x3FFF, big step = {b}, small step = {s}, but current\
                                        re-read: result ={output_40BB.reReadResult.value}, Error Bit = {output_40BB.reReadErrorBits.value:#06x} and\
                                        read last: result ={output_40BB.readLastResult.value}, Error Bit = {output_40BB.readLastErrorBits.value:#06x}, big step = {output_40BB.readLastBigStep.value}, small step = {output_40BB.readLastSmallStep.value}')
                elif b >= 2:
                    if not (output_40BB.readLastResult.value == 1 and output_40BB.readLastErrorBits.value == 0x3FFF and 
                            output_40BB.reReadResult.value == 1 and output_40BB.reReadErrorBits.value == 0x3FFF) :
                        logger.error_lb(f'Issue 40BB to check Read last step result')
                        logger.error_fp(f'Expected re-read : result = 1, error bits == 0x3FFF,  and\
                                        read last: result = 1 , read last error bits = 0x3FFF, but current\
                                        re-read: result ={output_40BB.reReadResult.value}, Error Bit = {output_40BB.reReadErrorBits.value} and\
                                        read last: result ={output_40BB.readLastResult.value}, Error Bit = {output_40BB.readLastErrorBits.value}')
                        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

            
            for b, s in iter_reh_steps(type = BLOCK_PAGE_TYPE(block_type)):
                logger.flow(11, f'Issue D014 VUC op0 with big step: {b}, small step: {s} to make recovery ECC')
                _ = issue_D014_to_set_read_recovery_module(
                    die = pca.die.value, 
                    bigIndex=b, 
                    smallIndex=s, 
                    nandMode=isSLC, 
                    isSpeciBlock=1, 
                    block=pca.virtual_block_number.value, 
                    isPSA=0)
                                
                logger.flow(12, f'Issue 4060 VUC to get raw data')
                _, raw_data = issue_4060_to_read_raw_data(Die=pca.die.value, Plane=pca.plane.value, Block=pca.virtual_block_number.value, Page=pca.page.value, SLC_Enable=isSLC, Ecc_Enable=1, Scrambler_Enable=1)

                logger.flow(13, f'Issue 409E VUC with ECC information = 1 to get error bit numbers')
                _, output_409E = issue_409E_to_get_error_bit_numbers()
                error_bits_409E = [output_409E.errorBitNumber1.value, output_409E.errorBitNumber2.value, output_409E.errorBitNumber3.value, output_409E.errorBitNumber4.value]
                logger.info(f'409E error bits ={error_bits_409E}')

                logger.flow(14, f'Issue 40BB VUC to get error bit number and read retry step')
                _, output_40BB = issue_40BB_to_get_error_bit_numbers_and_read_retry_step(pca.die.value)
                error_bits_40BB = [output_40BB.errorBitNumber1.value, output_40BB.errorBitNumber2.value, output_40BB.errorBitNumber3.value, output_40BB.errorBitNumber4.value]
                logger.info(f'40BB error bits = {output_40BB}')


                logger.flow(15, f'Compare error bit numbers between output 409E and 40BB')
                if error_bits_409E != error_bits_40BB:
                    logger.error_lb(f'Compare the error bit obtained from 409E VU and 40BB VU')
                    logger.error_fp(f'Expected data to match, but a mismatch occurred.')
                    raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
            
            logger.flow(6, f'Issue 4066 VUC to enable sticky read feature')
            self.set_sticky_read_en_dis(STICKY_READ_SETTING.DISABLE)
            
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
                if index == 0 and unit == 0: # LUN 0
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[index].units[unit].l4_num_alloc_units = au_size
                    config_desc[index].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index ==0 and unit == 1: #LUN 1
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
            w.assign(lun = lun, lba=lba, length=size, fua=1).enqueue()
            offset += size
            lba = start+offset
        ExecuteCMD.send()
        pass
    
    def set_sticky_read_en_dis(self, setting:STICKY_READ_SETTING) -> None:
        _, result = issue_4066_to_dis_en_sticky_read(STICKY_READ_SETTING.ENABLE)
        if result == STICKY_READ_STATUS.FAILED:
            logger.error_lb(f'Host issue vu 4066 to enable sticky read feature')
            logger.error_fp(f'Expect the result value is success, but failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    
    
run = Pattern().run
if __name__ == "__main__":
    run()