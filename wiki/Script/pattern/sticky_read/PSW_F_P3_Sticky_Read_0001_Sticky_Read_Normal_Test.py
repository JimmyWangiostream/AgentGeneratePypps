import package_root
from Script import api
from enum import IntEnum
import random
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.exception import SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH, SIGHTING_RESPONSE_UNEXPECTED
from Script.api.ufs_api.vendor_cmd.structs import FlashSetting
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from typing import TypeAlias, List, Dict, cast
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.project_api.custom_vu.lba_convert_vu import \
    issue_4051_to_get_physical_address, \
    issue_4052_to_get_logical_address
from Script.project_api.reh.functions import \
    get_page_range_by_type, \
    issue_D014_to_set_read_recovery_module, \
    issue_D014_to_set_last_table_content, \
    issue_40F9_to_get_rr_number_and_error_bits, \
    issue_4014_to_get_read_recovery_info_read_last, \
    issue_40BA_to_get_error_recovery_statistics, \
    get_error_recovery_record_by_index, \
    create_read_last_ref_table, \
    ERROR_RECOVERY_STATISTICS_RECORD, \
    iter_reh_steps
from Script.project_api.reh.structs import BLOCK_PAGE_TYPE, PAGE_TYPE_MAP, READ_LAST_TABLE, PAGE_TYPE
from Script.project_api.sticky_read.functions import \
    issue_4066_get_sticky_read_status_and_offset, \
    issue_4066_to_dis_en_sticky_read, \
    issue_4066_force_current_read_last_as_sticky_read
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
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        self.flash_setting = FlashSetting()
        self.flash_setting.from_bytes(self.flash_setting_buffer)
        self.fw_geometry = api.get_fw_geometry()
        self.total_au_size = int(self.geometry_desc.q4_total_raw_device_capacity / self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size)
        self.total_capacity_4K = int(self.geometry_desc.q4_total_raw_device_capacity/8)
        self.au_size = (self.total_au_size)//3
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.TestPSALun = 3
        self.write_record = api.get_empty_write_record()
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.read_last_ref_table: Dict[int, READ_LAST_TABLE_TYPE] = create_read_last_ref_table(self.flash_setting.Max_Fdevice)
        self.set_LUN_configuration()
        pass

    def step1(self) -> None:
       
        logger.flow(1, f'Issue D014 op2 VUC to set read last table')
        self.set_all_read_last_table()

        logger.flow(2, f'Issue 4056 to get mconfig REH_ENTER_COUNT_STICKY_ON(428h) value as threshold')
        _, mConfig = project_api.get_mConfig_data()
        sticky_threshold = mConfig.REH_ENTER_COUNT_STICKY_ON.value
        logger.info(f'mconfig REH_ENTER_COUNT_STICKY_ON = {sticky_threshold}')

        for lun in [self.TestNormalLun, self.TestEM1Lun, self.TestPSALun]:
            logger.flow(3, f'Sequence write data for LUN{lun}')
            self.pre_condition_flow(lun)

            length = self.slc_vb_size if lun == self.TestEM1Lun or lun == self.TestPSALun else self.tlc_vb_size
            isSLC = 1 if lun == self.TestEM1Lun or lun == self.TestPSALun else 0
            isPSA = 1 if lun == self.TestPSALun else 0

            lba = random.randint(lun, length-1)
            logger.info(f'Select LUN{lun}, LBA = {lba}')

            logger.flow(4, f'Issue 4051 VUC to get PBA from LBA({lba})')
            _,pca = issue_4051_to_get_physical_address(lun, lba)
            
            die = pca.die.value
            plane = pca.plane.value
            page = pca.page.value 
            block = pca.virtual_block_number.value
            offset = pca.offset.value

            val_bk = self.get_ERS_dummy_read_value(lun, die, plane)

            if lun == self.TestNormalLun:
                block_page_range = [ BLOCK_PAGE_TYPE.TLC_BLOCK_SLC_PAGE, BLOCK_PAGE_TYPE.TLC_BLOCK_MLC_PAGE, BLOCK_PAGE_TYPE.TLC_BLOCK_TLC_PAGE]
            elif lun == self.TestPSALun:
                block_page_range = [BLOCK_PAGE_TYPE.TLC_BLOCK_PSA_PAGE]
            else: 
                block_page_range = [BLOCK_PAGE_TYPE.SLC_BLOCK_SLC_PAGE]

            for block_type in block_page_range:
                for page_type in PAGE_TYPE_MAP.get(BLOCK_PAGE_TYPE(block_type), []):
                    for loop in range(10):
                        page = get_page_range_by_type(page_type)
                        table_index= random.choice([READ_LAST_TABLE.LAST_TABLE_1, READ_LAST_TABLE.LAST_TABLE_2])
                        logger.info(f'Select {page_type.label} page = {page} ' )

                        logger.flow(5, f'Issue D014 op2 VUC to set read last table')
                        write_offsets = self.set_read_last_table(die, page_type.value, page_type.offset_count, table_index, -80, 80)
                        signed_offsets = [self._to_signed_byte(o) for o in write_offsets[:3]]
                        logger.info(f'Set read last table ce: {die}, page_type: {page_type.label}, index: {table_index}, offset:[{signed_offsets[0]}, {signed_offsets[1]}, {signed_offsets[2]}]')

                        logger.flow(6, f'Issue 4014 op0 VUC to get read last table')
                        read_offsets = self.get_read_last_table(die, page_type.value, table_index)

                        logger.flow(7, f'Compare read last offset between flow 4 and flow 5')
                        if write_offsets[:page_type.offset_count] != read_offsets[:page_type.offset_count]:
                            logger.error_lb(f'Host issue vu 4014 to get read last table with {page_type.label} and table index = {table_index}')
                            logger.error_fp(f'Read last offset compare fail, set offset is {write_offsets[:page_type.offset_count]}, but read offset is {read_offsets[:page_type.offset_count]}')
                            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH


                        logger.flow(8, f'Issue 4066 VUC to force read last as sticky read')
                        self.force_read_last_as_sticky_read(die, page_type.value, 0, table_index, isPSA)

                        logger.flow(9, f'Issue 4066 VUC get sticky read status')
                        self.check_sticky_read_status(die, page_type, table_index, STICKY_READ_OUTPUT_STATUS.STICKY_READ_ENTERED, write_offsets)

                        logger.flow(10, f'Issue 4052 VUC to get LBA form PBA')
                        _, la = issue_4052_to_get_logical_address(die, plane, block, page, offset)
                        logger.info(f'page = {page}, offset = {offset}, lun = {la.lun.value}, lba = {la.lba.value}')

                        if not (la.lun.value == lun and la.lba.value > 0 and la.lba.value < length):
                            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
                        
                        logger.flow(11, f'Issue host read 4K size 25 times')
                        testQD = 1
                        for i in range(25):
                            ExecuteCMD.Read10().assign(lun=la.lun.value, lba=la.lba.value, length=1, fua=0).enqueue()
                        ExecuteCMD.send(QD= testQD)
                
                        # self.show_REH_ERS_info(pca.die.value, pca.plane.value)

                        logger.flow(12, f'Issue 40BA VUC get EHS dummy read value')
                        val = self.get_ERS_dummy_read_value(lun, die, plane)
                        diff = val - val_bk
                        logger.info(f'ERS Current val = {val}, backup val = {val_bk}, diff = {diff}')
                            
                        if lun == self.TestPSALun:
                            sticky_status = STICKY_READ_OUTPUT_STATUS.STICKY_READ_NOT_ENTERED if diff >= 1 else STICKY_READ_OUTPUT_STATUS.STICKY_READ_ENTERED
                        else: 
                            sticky_status = STICKY_READ_OUTPUT_STATUS.STICKY_READ_NOT_ENTERED if diff >= sticky_threshold else STICKY_READ_OUTPUT_STATUS.STICKY_READ_ENTERED
                        val_bk = val

                        logger.flow(13, f'Issue 4066 VUC get sticky read status, and expect sticky read status = 0x{sticky_status:02X}')
                        self.check_sticky_read_status(die, page_type, table_index, sticky_status, write_offsets)

            if(lun == self.TestPSALun):
                logger.flow(13, 'Set bPSAState as Off to interrupt PSA flow and check FW internal state, bPSAState should be off and FW internal state should be interrupt(0x01)')
                api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.OFF)
                self.set_LUN_configuration()

        pass


    def set_LUN_configuration(self) -> None:
        config_desc = api.get_config_descriptors(print = True)
        lun_num_per_desc = 8
        
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
                    config_desc[index].units[unit].l4_num_alloc_units = self.au_size
                    config_desc[index].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index ==0 and unit == self.TestEM1Lun :# LUN1
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_desc[index].units[unit].l4_num_alloc_units = self.au_size if self.au_size < self.geometry_desc.l44_enhanced1_max_n_alloc_u else self.geometry_desc.l44_enhanced1_max_n_alloc_u
                    config_desc[index].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_desc[index].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index ==0 and unit == self.TestPSALun :# LUN3
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[index].units[unit].l4_num_alloc_units = self.au_size
                    config_desc[index].units[unit].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
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
        
    def get_ERS_dummy_read_value(self, lun:int, die:int, plane:int)-> int:
        val = 0
        _, ers= issue_40BA_to_get_error_recovery_statistics()
        ers_index = 1 if lun != self.TestPSALun else 37
        rec = get_error_recovery_record_by_index(ers_index) 
        if rec != None:
            val = self.get_ers_value(die = die, plane = plane, rec = rec, payload = bytearray(ers.payload))
            logger.info(f'ERS {rec.name}: {val}')
                        
        return val


    def check_read_recovery_step(self, set_big_index:int, set_small_index:int, get_big_index:int, get_small_index:int, page_type: BLOCK_PAGE_TYPE) -> bool:
        if set_big_index == 8 or set_big_index == 9:
            if get_big_index ==255 and get_small_index == 255:
                return True
        elif set_big_index == get_big_index and set_small_index == get_small_index:
            return True
        return False
    
    def set_sticky_read_en_dis(self, setting:STICKY_READ_SETTING) -> None:
        _, result = issue_4066_to_dis_en_sticky_read(STICKY_READ_SETTING.ENABLE)
        if result == STICKY_READ_STATUS.FAILED:
            logger.error_lb(f'Host issue vu 4066 to enable sticky read feature')
            logger.error_fp(f'Expect the result value is success, but failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def _to_signed_byte(self, val: int) -> int:
        """將 0‑255 的 byte 轉成有號 byte（-128 ~ 127）。"""
        return val - 256 if val > 127 else val

    def set_read_last_table(self, ce:int, page_type: int, count:int, table_index: int, min_value:int, max_value:int)-> list[int]:
        offsets = [(random.randint(min_value, max_value) & 0xFF) for _ in range(count)]
        if count < 3:
            offsets.extend([0] * (3 - count))
        _ = issue_D014_to_set_last_table_content(ce, page_type, table_index, offsets[0], offsets[1], offsets[2])
        # signed_offsets = [_to_signed_byte(o) for o in offsets[:3]]
        # logger.info(f'[Set read last] ce: {ce}, page_type: {page_type.label}, index: {table_index}, offset:[{signed_offsets[0]}, {signed_offsets[1]}, {signed_offsets[2]}]')
        return offsets
    
    def set_all_read_last_table(self) -> None:
        for ce in range(self.flash_setting.Max_Fdevice):
            for page in PAGE_TYPE:
                for index in READ_LAST_TABLE:
                    offsets = self.read_last_ref_table[ce][page][index]
                    _ = issue_D014_to_set_last_table_content(ce, page, index, offsets[0], offsets[1], offsets[2])
        pass

    def get_read_last_table(self, die:int, page_type:int, table_index:int)-> List[int]:
        _, read_last = issue_4014_to_get_read_recovery_info_read_last(die, page_type, table_index)
        offsets = [read_last.offset1.value, read_last.offset2.value, read_last.offset3.value]
        return offsets


    def check_read_last_table(self) -> None:
        for ce in range(self.flash_setting.Max_Fdevice):
            for page in PAGE_TYPE:
                for index in READ_LAST_TABLE:
                    _, read_last = issue_4014_to_get_read_recovery_info_read_last(ce, page, index)
                    offsets = [read_last.offset1.value, read_last.offset2.value, read_last.offset3.value]
                    ref = self.read_last_ref_table[ce][page][index]
                    if offsets != ref: 
                        logger.error_lb(f'Host issue vu 4014 to get read last table with {page.label} and table index = {index}')
                        logger.error_fp(f'Read last offset compare fail, set offset is {ref}, but read offset is {offsets}')
                        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def check_sticky_read_status(self, die:int, type:PAGE_TYPE, table: READ_LAST_TABLE, status: int, read_last_offsets:List[int])-> None:
        _, _sr = issue_4066_get_sticky_read_status_and_offset(die, type, 0)
        if not (
            _sr.result.value == STICKY_READ_STATUS.SUCCESS and 
            _sr.stickyReadStatus.value == status
        ):
            logger.error_lb(f'Host issue vu 4066 to get sticky read status')
            logger.error_fp(f'Expect the result value is success(0) and status = 0x{status:02X}, but current result = {_sr.result.value} and status = 0x{_sr.stickyReadStatus.value:02X}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        
        if status == STICKY_READ_OUTPUT_STATUS.STICKY_READ_ENTERED:
            sticky_offsets = [_sr.offset1.value, _sr.offset2.value, _sr.offset3.value]
            if sticky_offsets != read_last_offsets: 
                logger.error_lb(f'Host issue vu 4066 to get sticky read status')
                logger.error_fp(f'Read last offset compare fail, expect offset is {read_last_offsets}, but current offset is {sticky_offsets}')
                raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
            pass

    def get_ers_value(self, die:int, plane:int, rec:ERROR_RECOVERY_STATISTICS_RECORD, payload: bytearray)->int:
        start = rec.offset+die*self.flash_setting.Plane_Per_Die*rec.occupies+plane*rec.occupies
        val = int.from_bytes(payload[start: start+rec.occupies], byteorder='little')
        return val

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
    
    def force_read_last_as_sticky_read(self, die:int, page_type:int, arc:int, table_index:int, isPSA:int) -> None:
        _, sr = issue_4066_force_current_read_last_as_sticky_read(die, page_type, isPSA, table_index, arc)
        if sr.result.value == STICKY_READ_STATUS.FAILED:
            logger.error_lb(f'Host issue vu 4066 to force read last as sticky read')
            logger.error_fp(f'Expect the status value is success, but failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def pre_condition_flow(self, lun: int)->None:

        if lun == self.TestNormalLun:
            api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=self.tlc_vb_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        elif lun == self.TestEM1Lun:
            api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=self.slc_vb_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        elif lun == self.TestPSALun:
            set_dPSADataSize_value = self.param.gDevice.l37_psa_max_data_size
            api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=set_dPSADataSize_value)


            unmap = ExecuteCMD.Unmap()
            unmap.assign(lun=self.TestNormalLun, lba=0, length=self.param.gUnit[self.TestNormalLun].q11_logical_block_count)
            ExecuteCMD.enqueue(unmap)
            unmap.assign(lun=self.TestPSALun, lba=0, length=self.param.gUnit[self.TestPSALun].q11_logical_block_count)
            ExecuteCMD.enqueue(unmap)

            ExecuteCMD.WriteAttribute().assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0).set_attr(api.PSAState.PRE_SOLDERING).set_option(wait_queue_empty=True).enqueue()
            ExecuteCMD.send()

            api.sequential_write(lun=self.TestPSALun, start_lba=0, total_size=self.slc_vb_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

    def show_REH_ERS_info(self, die:int, plane:int) -> None:
        ERS_Read_Check = list(range(1,3)) # + list(range(37, 62))
        logger.flow(11, f'Issue 40BA VUC get EHS')
        _, ers = issue_40BA_to_get_error_recovery_statistics()
        for idx in ERS_Read_Check:
            rec = get_error_recovery_record_by_index(idx)   
            if rec != None:    
                val = self.get_ers_value(die = die, plane = plane, rec = rec, payload = bytearray(ers.payload))
                logger.info(f'ERS {rec.name}: {val}')


    def post_process(self) -> None:
        pass
run = Pattern().run
if __name__ == "__main__":
    run()