import package_root
from typing import cast
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.exception import SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
from Script.api.ufs_api.vendor_cmd.structs import FlashSetting
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from typing import TypeAlias, Dict, List
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api.vendor_cmd.functions import lba_to_pba, load_PMD_data, load_PTE_data, direct_read
from Script.api.ufs_api.descriptors.configuration_desc.structs import  ConfigDescriptor310, ConfigDescriptor400, ConfigDescriptor410
from Script.project_api.custom_vu.lba_convert_vu import issue_4051_to_get_physical_address
from Script.project_api.reh.functions import create_read_last_ref_table, get_error_recovery_record_by_steps, issue_4014_to_get_read_recovery_info_read_last, issue_40BA_to_get_error_recovery_statistics, issue_40F9_to_get_rr_number_and_error_bits, issue_D014_to_set_last_table_content, issue_D014_to_set_read_recovery_module, iter_reh_steps, set_read_last_table
from Script.project_api.reh.structs import READ_LAST_TABLE, NAND_MODE, BLOCK_PAGE_TYPE,  PAGE_TYPE, ERROR_RECOVERY_STATISTICS_RECORD
from Script.api.util.functions import dumpfile


ReadLastTableDict = Dict[READ_LAST_TABLE, List[int]]
READ_LAST_TABLE_TYPE= Dict[PAGE_TYPE, ReadLastTableDict]   # die0、die1…的最外層型別

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.param = api.shared.param
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.total_au_size = int(self.geometry_desc.q4_total_raw_device_capacity / self.geometry_desc.l13_segment_size *  self.geometry_desc.b17_allocation_unit_size)
        self.total_capacity_4K = int(self.geometry_desc.q4_total_raw_device_capacity/8)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.max_number_lu = 8 if self.geometry_desc.b12_max_number_lu == 0 else 32
        self.flash_setting_buffer = api.get_flash_setting_buffer()
        self.flash_setting = FlashSetting()
        self.flash_setting.from_bytes(self.flash_setting_buffer)
        self.write_record = api.get_empty_write_record()
        self.read_last_ref_table: Dict[int, READ_LAST_TABLE_TYPE] = create_read_last_ref_table(self.flash_setting.Max_Fdevice)
        self.error_ERS_Message: List[str] = []
        pass

    def step1(self) -> None:
        logger.flow(1, 'Config LUN 0 to normal LU')
        self.set_LUN_configuration()

        logger.flow(1, f'Issue 40BA VUC to get ERS and check all values are zero in ERS')
        _, bk_ers = issue_40BA_to_get_error_recovery_statistics()
        if  any(byte > 1 for byte in bk_ers.payload[4:]):
            dumpfile("Initial_ERS.bin", bk_ers.payload)
            logger.error_lb(f'Host issue vu 40BA to get error recovery statistic')
            logger.error_fp(f'Expected all zero values in ERS, but verification failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

        length = self.tlc_vb_size

        logger.flow(2, f'Sequential write LUN0 to 1 vb size')
        api.sequential_write(lun=0, start_lba=0, total_size=length, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        logger.flow(3, f'Random select LBA in LUN0')
        lun = 0
        lba = random.randint(0, length-1)

        logger.flow(4, f'Issue 4051 VUC to get PBA from LBA({lba})')
        _,pca = issue_4051_to_get_physical_address(lun, lba)

        die = pca.die.value
        plane = pca.plane.value

        logger.flow(5, f'Issue D014 op2 VUC to set read last table')
        set_read_last_table(maxDie=self.flash_setting.Max_Fdevice, read_last_table=self.read_last_ref_table)

        logger.flow(6, f'Issue 4014 op0 VUC to get read last table')
        self.check_read_last_table()

        logger.flow(7, f'Issue 40BA VUC to get backup ERS value')
        _, bk_ers = issue_40BA_to_get_error_recovery_statistics()

        for b, s in iter_reh_steps(type = BLOCK_PAGE_TYPE(BLOCK_PAGE_TYPE.TLC_BLOCK_TLC_PAGE)):
            logger.flow(8, f'Issue D014 VUC  with big step: {b}, small step: {s} to make recovery ECC on {BLOCK_PAGE_TYPE(BLOCK_PAGE_TYPE.TLC_BLOCK_TLC_PAGE).label}')
            _ = issue_D014_to_set_read_recovery_module(
                die = pca.die.value, 
                bigIndex=b, 
                smallIndex=s, 
                nandMode=NAND_MODE.TLC_BLOCK.value, 
                isSpeciBlock=1, 
                block=pca.virtual_block_number.value, 
                isPSA=0)
            
            logger.flow(9, f'Issue 40F9 VUC get error step in REH')
            _, rr_number_raw_data, count = issue_40F9_to_get_rr_number_and_error_bits(1<<pca.die.value, 1<<pca.plane.value, pca.virtual_block_number.value, pca.page.value, pca.page.value, NAND_MODE.TLC_BLOCK.value, 0, 0, 0)

            logger.flow(10, f'Issue 40BA VUC to get current ERS value')
            _, ers = issue_40BA_to_get_error_recovery_statistics()
            dumpfile("ers_cur.bin", ers.payload)

            logger.flow(11, f'Compare ERS between backup value and current value')
            rec = get_error_recovery_record_by_steps(b, s, 0)
            if rec != None:
                    val = self.get_ers_value(die = die, plane = plane, rec = rec, payload = bytearray(ers.payload))
                    org_val = self.get_ers_value(die = die, plane = plane, rec = rec, payload = bytearray(bk_ers.payload))
                    logger.info(f'D014 op0 {b}-{s} ERS {rec.name} backup value= {org_val}, current value = {val}')
                    if val <= org_val :
                        self.error_ERS_Message.append(f'Expect current value {val} is greater than original value {org_val} in ERS: {b}-{s} {rec.name}')
        
        
        if self.error_ERS_Message:
            for err in self.error_ERS_Message:
                logger.error(err)
            logger.error_lb(f'Host issue vu 40BA to get error recovery statistic')
            logger.error_fp(f'Expect all the current values in ERS are greater than original values, verification failed')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def post_process(self) -> None:
        pass

    def set_LUN_configuration(self) -> None:
        config_desc = api.get_config_descriptors(print = True)
        lun_num_per_desc = 8

        for index in range(int(self.max_number_lu/lun_num_per_desc)):
            config_desc[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            config_desc[index].header.b3_boot_enable = api.BootEnable.BOOT_DISABLE
            for unit in range(lun_num_per_desc):
                config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.DISABLE
                if index == 0 and unit == 0: # LUN 0
                    config_desc[index].units[unit].b0_lu_enable = api.LUNEnable.ENABLE
                    config_desc[index].units[unit].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    config_desc[index].units[unit].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    config_desc[index].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_desc[index].units[unit].l4_num_alloc_units = self.total_au_size
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

    def get_ers_value(self, die:int, plane:int, rec:ERROR_RECOVERY_STATISTICS_RECORD, payload: bytearray)->int:
        start = rec.offset+die*self.flash_setting.Plane_Per_Die*rec.occupies+plane*rec.occupies
        val = int.from_bytes(payload[start: start+rec.occupies], byteorder='little')
        return val

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
    
run = Pattern().run
if __name__ == "__main__":
    run()