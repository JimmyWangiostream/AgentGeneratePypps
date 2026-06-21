import package_root
from typing import Dict, List, cast, TypeAlias
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.exception import SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH, SIGHTING_RESPONSE_UNEXPECTED
from Script.api.ufs_api.defines.constant_define import DATA_SIZE_4K_BYTE
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api.vendor_cmd.structs import PCA, FlashSetting
from Script.api.ufs_api.descriptors.configuration_desc.structs import ConfigDescriptor310, ConfigDescriptor400, ConfigDescriptor410
from Script.project_api.custom_vu.lba_convert_vu import physical_address_info
from Script.project_api.custom_vu.lba_convert_vu import issue_4051_to_get_physical_address, issue_4052_to_get_logical_address
from Script.api.util.functions import dumpfile
from Script.project_api.refresh_vu.define import VUC088Paremeter
from Script.project_api.refresh_vu.functions import issue_C088_to_start_or_stop_refresh
from Script.project_api.reh.functions import READ_LAST_TABLE_TYPE, create_read_last_ref_table, get_error_recovery_record_by_steps, get_page_range_by_type, issue_40BA_to_get_error_recovery_statistics, issue_40F9_to_get_rr_number_and_error_bits, issue_D014_to_set_last_table_content, issue_D014_to_set_nand_temperature, issue_D014_to_set_read_recovery_module, iter_reh_steps, set_read_last_table
from Script.project_api.reh.structs import BLOCK_PAGE_TYPE, ERROR_RECOVERY_STATISTICS_RECORD, NAND_MODE, PAGE_TYPE, PAGE_TYPE_MAP, READ_LAST_TABLE, rr_number_and_error_bits
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
        self.total_au_size = int(self.geometry_desc.q4_total_raw_device_capacity / self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size)
        self.total_capacity_4K = int(self.geometry_desc.q4_total_raw_device_capacity/8)
        self.TestNormalLun = 0
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.write_record = api.get_empty_write_record()
        self.read_last_ref_table: Dict[int, READ_LAST_TABLE_TYPE] = create_read_last_ref_table(self.flash_setting.Max_Fdevice)
        self.error_ERS_Message: List[str] = []
        pass

    def step1(self) -> None:
        logger.flow(1, 'Config LUN 0 to normal LU')
        self.set_LUN_configuration()

        logger.flow(2, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
        issue_C088_to_start_or_stop_refresh(bParameter0=VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        
        # block_page_range = [BLOCK_PAGE_TYPE.TLC_BLOCK_MLC_PAGE.value]
        block_page_range = [BLOCK_PAGE_TYPE.TLC_BLOCK_TLC_PAGE.value, BLOCK_PAGE_TYPE.TLC_BLOCK_MLC_PAGE.value, BLOCK_PAGE_TYPE.TLC_BLOCK_SLC_PAGE.value]

        length = 3*self.tlc_vb_size

        logger.flow(2, 'Sequential write 1 TLC VB size')
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=length, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        logger.flow(3, f'Issue D014 op2 VUC to set read last table')
        set_read_last_table(maxDie=self.flash_setting.Max_Fdevice, read_last_table=self.read_last_ref_table)

        for die in range(self.flash_setting.Max_Fdevice):
            for page_type in PAGE_TYPE:
                    arc = random.randint(0, 2)
                    self.force_read_last_as_sticky_read(die, page_type, arc, READ_LAST_TABLE.LAST_TABLE_1)

        temp = (random.randint(-37, 125) & 0xFF)
        logger.flow(6, f'Issue D014 op8 VUC to set NAND temperature enable, temperature = {temp}')
        issue_D014_to_set_nand_temperature(isEnable =1, temperature = temp)

        for lun in [self.TestNormalLun]:
            
            logger.flow(4, f'Random select LBA in LUN0')
            lba = random.randint(0, length-1)

            logger.flow(5, f'Issue 4051 VUC to get PBA from selected LBA = {lba} ')
            _,pca = issue_4051_to_get_physical_address(lun, lba)

            logger.flow(6, f'Issue vu 4066 to force read last as sticky read')
           
            for block_type in block_page_range:      
                _, bk_ers = issue_40BA_to_get_error_recovery_statistics()

                for b, s in iter_reh_steps(type = BLOCK_PAGE_TYPE(block_type)):
                    logger.flow(7, f'Issue D014 VUC to make recovery ECC on {BLOCK_PAGE_TYPE(block_type).label} with big step: {b}, small step: {s}')
                    _ = issue_D014_to_set_read_recovery_module(
                        die = pca.die.value, 
                        bigIndex=b, 
                        smallIndex=s, 
                        nandMode=NAND_MODE.TLC_BLOCK.value, 
                        isSpeciBlock=1, 
                        block=pca.virtual_block_number.value, 
                        isPSA=0)
                    
                    for page_type in PAGE_TYPE_MAP.get(BLOCK_PAGE_TYPE(block_type), []):
                        
                        _,pca = issue_4051_to_get_physical_address(lun, lba)
                        page = get_page_range_by_type(page_type)
                        logger.flow(8, f'Random select page = {page} for {page_type.label}' )

                        logger.flow(10, f'Issue 4052 VUC to get LBA form PBA')
                        _, la = issue_4052_to_get_logical_address(pca.die.value, pca.plane.value, pca.physical_block_number_w_BBT.value, page, pca.offset.value)
                        logger.info(f'page = {page}, offset = {pca.offset.value}, lun = {la.lun.value}, lba = {la.lba.value}')
                        
                        if not (la.lun.value == lun and la.lba.value >=0 and la.lba.value < length):
                            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
                        
                        logger.flow(11, f'Issue host read 4K size from LBA')
                        self.read_data(la.lun.value, la.lba.value, 1)

                        logger.flow(12, f'Issue 40F9 VUC to get error step in REH')
                        _, rr_number_raw_data, count = issue_40F9_to_get_rr_number_and_error_bits(1<<pca.die.value, 1<<pca.plane.value, pca.virtual_block_number.value, page, page, NAND_MODE.TLC_BLOCK.value, 0, 0, 0)
                        rr_number_step = rr_number_and_error_bits(rr_number_raw_data[0: len(rr_number_and_error_bits().payload)])
                        logger.info(f'{b}-{s}: 40F9 b-s:{rr_number_step.bigStep.value}-{rr_number_step.smallStep.value}, Max error bits: {rr_number_step.maxErrorBits.value}, bin : {rr_number_step.bin.value}')
                    
                        logger.flow(13, f'Compare big step and small step')
                        if not (self.check_read_recovery_step(b, s, rr_number_step.bigStep.value, rr_number_step.smallStep.value) == True and rr_number_step.maxErrorBits.value > 0):
                                logger.error_lb(f'Host issue vu 40F9 to get rr number and error bit')
                                logger.error_fp(f'Expect big step = {b} , small step = {s}, and max error bit > 0, ' 
                                                f'but 40F9 big step = {rr_number_step.bigStep.value} and small step = {rr_number_step.smallStep.value}, ' 
                                                f'max error bits = {rr_number_step.maxErrorBits.value}, '
                                                f'page = {page}, page type =  {page_type.label}'
                                )
                                raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
                        
                        logger.flow(14, f'Issue 40BA VUC to get current ERS value')
                        _, ers = issue_40BA_to_get_error_recovery_statistics()

                        rec = get_error_recovery_record_by_steps(b, s, 0)
                        if rec != None:
                            val = self.get_ers_value(die = pca.die.value, plane = pca.plane.value, rec = rec, payload = bytearray(ers.payload))
                            org_val = self.get_ers_value(die = pca.die.value, plane = pca.plane.value, rec = rec, payload = bytearray(bk_ers.payload))
                            logger.info(f'D014 op0 {b}-{s} ERS {rec.name} backup value= {org_val}, current value = {val}')
                            if(val <= org_val):
                                self.error_ERS_Message.append(f'Expect current value = {val} is greater than original value = {org_val} in ERS {rec.name} {b}-{s} for LUN{lun}')

                        bk_ers = ers

        logger.flow(17, f'Issue read command to compare data') 
        api.read_compare(self.write_record, api.CompareMethod.HW_COMPARE)

        logger.flow(18, f'Issue D014 op8 VUC to set NAND temperature disable, temperature = {temp}')
        issue_D014_to_set_nand_temperature(isEnable = 0, temperature = temp)

        logger.flow(19, 'Issue C088 to start refrseh')
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
        normal_total_AU = self.total_au_size//3 * 2
        for index in range(int(self.max_number_lu/lun_num_per_desc)):
            config_desc[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            config_desc[index].header.b3_boot_enable = api.BootEnable.BOOT_DISABLE
            config_desc[index].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.DISABLE
            config_desc[index].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
            config_desc[index].header.l18_num_shared_write_booster_buffer_alloc_units = self.geometry_desc.l79_write_booster_buffer_max_n_alloc_units if index==0 else 0
            for unit in range(lun_num_per_desc):
                config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.DISABLE
                if index == 0 and unit == self.TestNormalLun: # LUN 0
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[index].units[unit].l4_num_alloc_units = normal_total_AU
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

        pass
    
    def get_direct_read_data(self, physical_address: physical_address_info) ->tuple[bytearray, bytearray]:
        pca = PCA()
        pca.b4_mode = NAND_MODE.TLC_BLOCK.value
        pca.b5_ce = physical_address.die.value
        pca.b6_plane = physical_address.plane.value
        pca.b11_block_h = (physical_address.virtual_block_number.value>>8) & 0xFF
        pca.b10_block_l = physical_address.virtual_block_number.value & 0xFF
        pca.l12_fpage = int(physical_address.page.value * 32 + physical_address.offset.value * 8)
        payload = api.direct_read(pca=pca, block_count=4, include_FW_spare=True)
        spare = payload[4 * DATA_SIZE_4K_BYTE:4 * DATA_SIZE_4K_BYTE + DATA_SIZE_4K_BYTE]
        data = payload[:4 * DATA_SIZE_4K_BYTE]
        return data, spare
    
    def check_read_recovery_step(self, set_big_index:int, set_small_index:int, get_big_index:int, get_small_index:int) -> bool:
        if set_big_index == get_big_index and set_small_index == get_small_index:
            return True
        elif set_big_index == 7 and set_small_index == 0:
            if get_big_index == 7 and (get_small_index == 0 or get_small_index == 1):
                return True
            else:
                return False
        elif set_big_index == 9:
            if get_big_index ==255 and get_small_index == 255:
                return True
        # if set_big_index == 0 and set_small_index == 0 :
        #     if get_big_index ==0 and get_small_index == 1:
        #         return True
        # elif set_big_index == 1 and set_small_index == 2:
        #     if get_big_index ==2 and get_small_index == 4:
        #         return True
        # elif set_big_index == 1 and set_small_index == 3:
        #     if get_big_index ==2 and get_small_index == 4:
        #         return True
        # elif set_big_index == 8 or set_big_index == 9:
        #     if get_big_index ==255 and get_small_index == 255:
        #         return True
        # elif set_big_index == get_big_index and set_small_index == get_small_index:
        #     return True
        return False

    def force_read_last_as_sticky_read(self, die:int, page_type:int, arc:int, table_index:int) -> None:
        _, sr = issue_4066_force_current_read_last_as_sticky_read(die, page_type, 0, table_index, arc)
        if sr.result.value == STICKY_READ_STATUS.FAILED:
            logger.error_lb(f'Host issue vu 4066 to force read last as sticky read')
            logger.error_fp(f'Expect the status value is success, but failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def get_ers_value(self, die:int, plane:int, rec:ERROR_RECOVERY_STATISTICS_RECORD, payload: bytearray)->int:
        start = rec.offset+die*self.flash_setting.Plane_Per_Die*rec.occupies+plane*rec.occupies
        val = int.from_bytes(payload[start: start+rec.occupies], byteorder='little')
        return val
    
run = Pattern().run
if __name__ == "__main__":
    run()