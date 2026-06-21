import random
from typing import Dict, List, cast
import package_root
from Script import api, project_api
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api.vendor_cmd.structs import FlashSetting
from Script.lib import sdk_lib as lib
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.project_api.custom_vu.lba_convert_vu.functions import issue_4052_to_get_logical_address
from Script.project_api.custom_vu.raw_data_vu.functions import issue_4060_to_read_raw_data
from Script.project_api.reh.functions import get_page_range_by_type
from Script.project_api.reh.structs import PAGE_TYPE
from Script.project_api.vth_sweep.functions import convert_page_to_page_order, issue_401D_to_get_vt_distribution

_sdk = api.shared.sdk


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
        self.hw_setting = api.HwSetting.get_instance()
        self.hw_setting.update_from_device()
        self.hw_setting.backup()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.write_record = api.get_empty_write_record()
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.set_trim_address: Dict[int, List[int]] = {
            PAGE_TYPE.PAGE_POR_DSLC:[0x11E, 0x114],
            PAGE_TYPE.PAGE_SLC_LP:[0x126],
            PAGE_TYPE.PAGE_MLC_LP:[0x110],
            PAGE_TYPE.PAGE_TLC_LP:[0xB0]
        }
        pass

    def step1(self) -> None:
        self.set_LUN_configuration()

        logger.flow(1, f'Issue C088 to stop refresh')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)

        self.hw_setting.set_to_device(field = api.HwSettingField.POWER_SAVING_CTRL_ENABLE, val= 0x3A)

        logger.flow(2, f'Sequence write data 1 vb size')
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=self.tlc_vb_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=self.slc_vb_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            
        dac_count = 3

        for lun in [self.TestEM1Lun, self.TestNormalLun]:
            
            length = self.slc_vb_size if lun == self.TestEM1Lun else self.tlc_vb_size
            isSLC = True if lun == self.TestEM1Lun else False
            page_type_range = [PAGE_TYPE.PAGE_POR_DSLC] if lun == self.TestEM1Lun else [PAGE_TYPE.PAGE_TLC_LP, PAGE_TYPE.PAGE_MLC_LP, PAGE_TYPE.PAGE_SLC_LP]

            
            for page_type in page_type_range: 
                min_dac = random.randint(0, 0xDA - dac_count)
                # min_dac = 92
                max_dac = min_dac+dac_count-1
                logger.info(f'Random selected DAC = {min_dac} ~ {max_dac}')
                trim_range = list(range(min_dac, max_dac + 1))

                lba = random.randint(0, length)

                # lba = 0
            
                logger.flow(3, f'Issue 4051 to get physical address from LBA{lba}')
                _, pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=lba)
                vb = pca.virtual_block_number.value
                die = pca.die.value
                plane = pca.plane.value
                block = pca.physical_block_number_w_BBT.value
                offset = pca.offset.value
                # page = pca.page.value
                page = get_page_range_by_type(page_type)
                page_order = convert_page_to_page_order(page, isSLC)

                logger.info(f'Lun{lun}, LBA = {lba}: VB = {vb},CE = {die}, Plane = {plane},  PhyBlock = {block}, Page_order = {page_order}, offset = {offset}')

                org_trim : Dict[int, int] = {}
                trim_address_range: List[int] = self.set_trim_address[page_type]
                logger.flow(4, f'Issue 4084 to get NAND trim of address = {trim_address_range}')
                _, trim = project_api.issue_4084_to_get_NAND_trim(target_addr=trim_address_range)
                for i in range(len(trim_address_range)):
                    org_trim.update({trim_address_range[i]: trim.TrimValue[i].value})

                bit_one_counts: List[int] = []
                # TLC page need to set max trim value on address 0xDB
                if page_type == PAGE_TYPE.PAGE_TLC_LP:
                    pre_trim : Dict[int, int] = {0xD8: 0xDA}
                    logger.flow(5, f'Issue C084 to pre-set NAND trim {pre_trim} on page{page} for LUN{lun} if page type is TLC page')
                    project_api.issue_C084_to_set_NAND_trim(set_dict=pre_trim)
                
                for dac in trim_range:
                    set_dict : Dict[int, int] = {}
                    
                    for i in range(len(trim_address_range)):
                        set_dict.update({trim_address_range[i]: dac})
                    logger.flow(5, f'Issue C084 to set NAND trim {set_dict} for LUN{lun}')
                    project_api.issue_C084_to_set_NAND_trim(set_dict=set_dict)

                    logger.flow(6, f'Issue 4060 to read raw data')
                    _, raw_data = issue_4060_to_read_raw_data(Die=die, Plane=plane, Block=block, Page=page, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0)

                    logger.flow(7, f'Count the number of ones')
                    bit_one_count = self.get_bit_one_count(raw_data, offset)
                    bit_one_counts.append(bit_one_count)

                logger.flow(8, f'Issue C084 to recover NAND trim value {org_trim}')
                project_api.issue_C084_to_set_NAND_trim(set_dict=org_trim)
                        
                logger.flow(9, f'Issue 401D with die={die}, plane={plane}, block={block}, page={page_order}, isSLC={isSLC}, index={offset} mode = 0 to get bit = 1 counts')
                _, vt = issue_401D_to_get_vt_distribution(die, plane, block, page_order, isSLC, offset, min_dac, max_dac, 0)
            
                logger.flow(10, f'Compare flips counts between 401D and raw data')
                self.compare_vt_distribution_count(vt, bit_one_counts, page_type, page, trim_range)

        logger.flow(14, f'Issue C088 to start refresh')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
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
    
    def get_wl_number_by_page_on_SLC(self, page:int) -> int:
        return page//4
    
    def get_page_number_by_wl_on_SLC(self, wl:int)-> int:
        return wl*4
    
    def get_bit_one_count(self, data:bytearray, node_index:int) -> int:
        total_bits = 0
        node = 4588
        start = node_index*node
        for b in data[start: start+node]:
            # 將byte轉換為二進位字串，然後計算1的個數
            total_bits += bin(b).count('1')
        return total_bits

    def compare_vt_distribution_count(self, vt: bytearray, bit_one_count:List[int], page_type:PAGE_TYPE, page:int, dac:List[int])->None:
        index = 0
        diff_list:List[int] = []
        for i in range(0, len(vt), 4):
            if len(diff_list) >= len(bit_one_count):
                break
            diff_list.append(int.from_bytes(vt[i:i+4], byteorder = 'little'))
        
        logger.info(f'For DAC={dac}, the vt count list = {diff_list} from 401D, bit_ont_count = {bit_one_count} from raw data on {page_type.label}, page = {page}')
        if not all( x >= y*0.9 and x<= y*1.1 for x, y in zip(diff_list, bit_one_count)):
            logger.error_lb(f'Issue 401D to get VT distribution and compare bit one counts between VT and raw data')
            logger.error_fp(f'Compare failure: Diff count ({diff_list}) from VU 401D must be within ±10% of bit one count ({bit_one_count}) from raw data on page{page} for DAC={dac}.')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def post_process(self) -> None:
        self.hw_setting.recover()
        pass


run = Pattern().run
if __name__ == "__main__":
    run()