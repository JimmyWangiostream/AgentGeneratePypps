import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api import *
from Script.project_api.health_report.functions import *
from Script.project_api.custom_vu.VDET_vu.functions import issue_40B8_to_get_VDET_information, issue_D074_to_disable_VDET
from Script.api.ufs_api.vendor_cmd.functions import *


ENG2_WA = True
_sdk = shared.sdk
import time
class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.fw_geometry = api.get_fw_geometry()
        self.geometry_desc = api.get_geometry_descriptor()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.test_vb = 0
        self.test_ce = 0
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)      
        self.random_en_lun = 0 #random.randint(0, 31) disable ats bug?
        self.Total_AU_Count = self.geometry_desc.q4_total_raw_device_capacity / (self.geometry_desc.l13_segment_size * self.geometry_desc.b17_allocation_unit_size)        
        pass
    def config_lun(self) -> None:
        self.unit_desc_idxes:List[int] = []
        config_descs = api.get_config_descriptors(print=True)
        #config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x0
        config_descs[0].header.b17_write_booster_buffer_type =  api.WriteBoosterBufferType.SHARED
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.DISABLE
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x400        
        
        for i in range(4): 
            for unit in range(8):
                if (i * 8 + unit) == 0:
                    config_descs[i].units[unit].b0_lu_enable = 1
                    config_descs[i].units[unit].b1_boot_lun_id = 0
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[i].units[unit].l4_num_alloc_units = int(self.Total_AU_Count/3)
                    config_descs[i].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif (i * 8 + unit) == 3:
                    config_descs[i].units[unit].b0_lu_enable = 1
                    config_descs[i].units[unit].b1_boot_lun_id = 0
                    config_descs[i].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[i].units[unit].l4_num_alloc_units = int(self.Total_AU_Count/3)
                    config_descs[i].units[unit].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    config_descs[i].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                else:
                    config_descs[i].units[unit].b0_lu_enable = 0
                    config_descs[i].units[unit].l4_num_alloc_units = 0
            if i == 3:
                config_descs[i].header.b2_conf_desc_continue = 0
            else:
                config_descs[i].header.b2_conf_desc_continue = 1
            push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        _param = api.shared.param
        for lun in range(0, _param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(DescriptorIDN.UNIT, lun)
            self.unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in self.unit_desc_idxes:
            update_descriptor(DescriptorIDN.UNIT, index, cast(QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()
        #test unit ready all enable lun
        for lun in range(_param.gMaxNumberLU):
            if  _param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
        pass
    def get_health_report(self)->None:
        response, self.health_report = project_api.issue_40FE_to_read_enhanced_health_report() 
            
    def compare_data_show_log(self,variable1_name:str,variable1_val:int, variable2_name:str,variable2_val:int,increase_val:int, compare_method:str = "=")->None:
        if compare_method == "=":
            if(variable1_val != (variable2_val + increase_val)):
                logger.error_fp(f'{variable1_name}({variable1_val}) != {variable2_name}({variable2_val}) + {increase_val}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL     
        if compare_method == ">":
            if(variable1_val <= (variable2_val + increase_val)):
                logger.error_fp(f'{variable1_name}({variable1_val}) <= {variable2_name}({variable2_val}) + {increase_val}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL    
        if compare_method == ">=":
            if(variable1_val < (variable2_val + increase_val)):
                logger.error_fp(f'{variable1_name}({variable1_val}) < {variable2_name}({variable2_val}) + {increase_val}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL                    

    def read_data_size_tlc_test(self)->None:
        logger.info(f'read_data_size_tlc_cnt = {self.health_report.read_data_size_tlc_unit_100mb}')
        original_total_read_size = self.health_report.read_data_size_tlc_unit_100mb.value
        read_data_4k = BLOCK4K_SIZE_100M_BYTE
        self.read_data(0,0,read_data_4k,read_data_4k)
        self.get_health_report()
        current_total_read_size = self.health_report.read_data_size_tlc_unit_100mb.value
        self.compare_data_show_log("current_total_read_size",current_total_read_size,"original_total_write_size",original_total_read_size,1,">")              
    
    def config_lock_test(self)->None:
        config_clock_health_report_cnt = self.health_report.bconfigdescrlock.value
        bConfigDescrLock = api.read_attribute(idn=api.AttributeIDN.CONFIG_DESCR_LOCK)
        logger.info(f'attribute 0Bh(bConfigDescrLock) value = {bConfigDescrLock}')
        if bConfigDescrLock != config_clock_health_report_cnt:
            logger.error_fp(f'bConfigDescrLock {bConfigDescrLock} != config_clock_health_report_cnt {config_clock_health_report_cnt}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH   
        api.write_attribute(idn = api.AttributeIDN.CONFIG_DESCR_LOCK, val = 0x1)
        bConfigDescrLock = api.read_attribute(idn=api.AttributeIDN.CONFIG_DESCR_LOCK)
        logger.info(f'attribute 0Bh(bConfigDescrLock) value = {bConfigDescrLock}')
        self.get_health_report()
        config_clock_health_report_cnt = self.health_report.bconfigdescrlock.value
        if bConfigDescrLock != config_clock_health_report_cnt:
            logger.error_fp(f'bConfigDescrLock {bConfigDescrLock} != config_clock_health_report_cnt {config_clock_health_report_cnt}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH   
        project_api.issue_D085_unlock_LU_attribute_configuration()
        bConfigDescrLock = api.read_attribute(idn=api.AttributeIDN.CONFIG_DESCR_LOCK)
        if bConfigDescrLock != 0x0:
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH        
        self.get_health_report()
        config_clock_health_report_cnt = self.health_report.bconfigdescrlock.value        
        if bConfigDescrLock != config_clock_health_report_cnt:
            logger.error_fp(f'bConfigDescrLock {bConfigDescrLock} != config_clock_health_report_cnt {config_clock_health_report_cnt}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH   

    def wr100mb_test(self)->None:

        original_read_data_size_tlc_unit_100mb = self.health_report.read_data_size_tlc_unit_100mb.value
        logger.info(f'read_data_size_tlc_unit_100mb = {self.health_report.read_data_size_tlc_unit_100mb.value}')

        original_read_data_size_for_em1_unit_100mb = self.health_report.read_data_size_for_em1_unit_100mb.value
        logger.info(f'read_data_size_em1_unit_100mb = {self.health_report.read_data_size_for_em1_unit_100mb.value}')

        original_write_data_size_tlc_unit_100mb = self.health_report.write_data_size_tlc_unit_100mb.value
        logger.info(f'write_data_size_tlc_unit_100mb = {self.health_report.write_data_size_tlc_unit_100mb.value}')

        original_write_data_size_for_em1_unit_100mb = self.health_report.write_data_size_for_em1_unit_100mb.value
        logger.info(f'write_data_size_for_em1_unit_100mb = {self.health_report.write_data_size_for_em1_unit_100mb.value}')        
        read_data_4k = BLOCK4K_SIZE_100M_BYTE
        self.write_data(0,0,read_data_4k,read_data_4k)
        self.read_data(0,0,read_data_4k,read_data_4k)

        self.write_data(3,0,read_data_4k,read_data_4k)
        self.read_data(3,0,read_data_4k,read_data_4k)        
        
        self.get_health_report()
        current_read_data_size_tlc_unit_100mb = self.health_report.read_data_size_tlc_unit_100mb.value
        logger.info(f'read_data_size_tlc_unit_100mb = {self.health_report.read_data_size_tlc_unit_100mb.value}')

        current_read_data_size_for_em1_unit_100mb = self.health_report.read_data_size_for_em1_unit_100mb.value
        logger.info(f'read_data_size_em1_unit_100mb = {self.health_report.read_data_size_for_em1_unit_100mb.value}')

        current_write_data_size_tlc_unit_100mb = self.health_report.write_data_size_tlc_unit_100mb.value
        logger.info(f'write_data_size_tlc_unit_100mb = {self.health_report.write_data_size_tlc_unit_100mb.value}')

        current_write_data_size_for_em1_unit_100mb = self.health_report.write_data_size_for_em1_unit_100mb.value
        logger.info(f'write_data_size_for_em1_unit_100mb = {self.health_report.write_data_size_for_em1_unit_100mb.value}')

        self.compare_data_show_log("current_read_data_size_tlc_unit_100mb",current_read_data_size_tlc_unit_100mb,"original_read_data_size_tlc_unit_100mb",original_read_data_size_tlc_unit_100mb,1,'>=')  
        
        self.compare_data_show_log("current_read_data_size_for_em1_unit_100mb",current_read_data_size_for_em1_unit_100mb,"original_read_data_size_for_em1_unit_100mb",original_read_data_size_for_em1_unit_100mb,1,'>=')  
        
        self.compare_data_show_log("current_write_data_size_tlc_unit_100mb",current_write_data_size_tlc_unit_100mb,"original_write_data_size_tlc_unit_100mb",original_write_data_size_tlc_unit_100mb,1,'>=')  
        
        self.compare_data_show_log("current_write_data_size_for_em1_unit_100mb",current_write_data_size_for_em1_unit_100mb,"original_write_data_size_for_em1_unit_100mb",original_write_data_size_for_em1_unit_100mb,1,'>=')  

    def read_data_size_em1_test(self)->None:
         logger.info(f'read_data_size_em1_cnt = {self.health_report.read_data_size_for_em1_unit_100mb}')


    def spare_block_count_test(self)->None:
         logger.info(f'spare_block_cnt = {self.health_report.spare_block_count_including_the_initial_2_always_reserved_bad_blocks}')

    def vdet_test(self)->None:
        original_vdet_cnt = self.health_report.vdet_count.value

        self.drop_vcc_vccq_voltage()
        self.get_health_report()
        current_vdet_cnt = self.health_report.vdet_count.value
        self.compare_data_show_log("current_vdet_cnt",current_vdet_cnt,"original_vdet_cnt",original_vdet_cnt,1,'>=')
    def total_running_time_test(self)->None:
        original_total_running_time = self.health_report.total_running_time.value
        time.sleep(3600)
        self.get_health_report()
        current_total_running_time = self.health_report.total_running_time.value
        self.compare_data_show_log("current_total_running_time",current_total_running_time,"original_total_running_time",original_total_running_time,1,'>=')  

    def device_on_time_test(self)->None:
        original_device_on_time = self.health_report.device_on_time.value
        time.sleep(120)
        self.get_health_report()
        current_device_on_time = self.health_report.device_on_time.value
        self.compare_data_show_log("current_device_on_time",current_device_on_time,"original_device_on_time",original_device_on_time,1,'>=')        
    def drop_vcc_vccq_voltage(self, isDisableVDET: bool = False)-> None:

        if(isDisableVDET):
            _ = issue_D074_to_disable_VDET()

        self.switch_voltage_value(lib.PowerChannel.VCCQ, 1.08, 2)
        self.switch_voltage_value(lib.PowerChannel.VCCQ, 1.3, 1)
        logger.info('Switch SSU to sleep and active')
        self.ssu_sleep_and_active()

        if(isDisableVDET):
            _ = issue_D074_to_disable_VDET()
        
        self.switch_voltage_value(lib.PowerChannel.VCC, 2.1, 1)
        self.switch_voltage_value(lib.PowerChannel.VCC, 2.5, 1)
        logger.info('Unipro Reset')
        init_tester_to_unit_ready(Dcmd5ResetType.UNIPRO_RESET)
        logger.info('Switch SSU to sleep and active')
        self.ssu_sleep_and_active()
    def switch_voltage_value(self, channel: lib.PowerChannel, voltage: float, digits:int ) -> None:
        
        logger.info(f'Channel {channel.value} switch voltage to {voltage}V')

        if(channel == lib.PowerChannel.VCC):
            measureChannel = lib.VoltageChannel.VCC
        elif(channel == lib.PowerChannel.VCCQ):
            measureChannel = lib.VoltageChannel.VCCQ
        else: 
            measureChannel = lib.VoltageChannel.VCCQ2        
        _sdk.switch_voltage_value(voltage, channel.value) 
        pass
            
    def ssu_sleep_and_active(self) -> None:
        testQD = 1
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.send(QD=testQD,clear_on_success=True)
        pass            
    def write_booster_related_cnt_test(self) -> None:
        ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
        logger.info(f'Available WB size is 0x{ava_WB_size:02X}')        
        cur_WB_size = api.read_attribute(idn=api.AttributeIDN.CURRENT_WRITEBOOSTER_BUFFER_SIZE)
        logger.info(f'Cur WB size is 0x{cur_WB_size:02X}')        
        expectd_val = int(4096 / 1242)
        logger.info(f'available_write_booster_size = {self.health_report.available_write_booster_size.value}')        
        if self.health_report.available_write_booster_size.value != expectd_val:
            logger.error_fp(f'self.health_report.available_write_booster_size.value {self.health_report.available_write_booster_size.value} != {expectd_val}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH               
        expectd_val = int(4096 / 10)
        logger.info(f'max_slc_cache_wb_size = {self.health_report.max_slc_cache_wb_size.value}')    
        if self.health_report.max_slc_cache_wb_size.value != expectd_val:
            logger.error_fp(f'self.health_report.max_slc_cache_wb_size.value {self.health_report.max_slc_cache_wb_size.value} != {expectd_val}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH          
        logger.info(f'available_slc_cache_wb_buffer_size = {self.health_report.available_slc_cache_wb_buffer_size.value}')
        if self.health_report.available_slc_cache_wb_buffer_size.value != 100:
            logger.error_fp(f'self.health_report.available_slc_cache_wb_buffer_size.value {self.health_report.available_slc_cache_wb_buffer_size.value} != 100')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH          
        ori_available_normal_size = self.health_report.available_normal_size.value
        logger.info(f'available_normal_size = {self.health_report.available_normal_size.value}')
        self.write_data(0, 0, BLOCK4K_SIZE_1M_BYTE * 1242, 65535)    
        self.get_health_report()
        cur_available_normal_size = self.health_report.available_normal_size.value
        self.compare_data_show_log("ori_available_normal_size",ori_available_normal_size,"cur_available_normal_size",cur_available_normal_size,1,'>=')        
        ori_available_em1_size = self.health_report.available_em1_size.value
        self.write_data(3, 0, BLOCK4K_SIZE_1M_BYTE * 1242, 65535)
        self.get_health_report()        
        cur_available_em1_size = self.health_report.available_em1_size.value
        logger.info(f'available_em1_size = {self.health_report.available_em1_size.value}')
        self.compare_data_show_log("ori_available_em1_size",ori_available_em1_size,"cur_available_em1_size",cur_available_em1_size,1,'>=')        

    def pattern_get_health_descriptor_then_check(self) -> None:
        idn = 0xF8
        index = 0x00
        selector = 0x00
        cmd = ExecuteCMD.ReadDescriptor()
        cmd.upiu.u12_specific_fields.w18_length = 4096
        cmd.assign(idn, index, selector)
        cmd_index = ExecuteCMD.enqueue(cmd)

        ExecuteCMD.send(clear_on_success=False)
        resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
        ExecuteCMD.clear()

        #desc_name = f'DeviceHealthDescriptor{Dut.get_instance().ufs_version:x}'
        
        desc = DeviceHealthDescriptor310()
        desc.from_bytes(resp.data)
        dumpfile('health_report_IDN_F8h',resp.data)

        diff_item = 0        
        for i, (x, y) in enumerate(zip(resp.data, self.health_report.payload)):
            if x != y:
                print(f"diff at {i}: {x} != {y}")
                diff_item += 1
        if(diff_item > 10):
            logger.info(f'health_report_IDN_F8h , 40FE health report diff item > 10')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH       
        pass
        #return desc        

    
    def compare_vendorinfo(self) -> None:
        

        idn = DescriptorIDN.DEVICE_HEALTH
        index = 0x00
        selector = 0x00
        cmd = ExecuteCMD.ReadDescriptor()
        cmd.assign(idn, index, selector)
        cmd_index = ExecuteCMD.enqueue(cmd)

        ExecuteCMD.send(clear_on_success=False)
        resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))

        #desc_name = f'DeviceHealthDescriptor{Dut.get_instance().ufs_version:x}'
        
        desc = DeviceHealthDescriptor310()
        desc.from_bytes(resp.data)
        health_descr_payload = resp.data
        dumpfile('health_report_vu_40FE.bin',self.health_report.payload)
        dumpfile('health_descr_payload.bin', health_descr_payload)
        ExecuteCMD.clear()

        idn = DescriptorIDN.DEVICE
        index = 0x00
        selector = 0x00
        cmd = ExecuteCMD.ReadDescriptor()
        cmd.assign(idn, index, selector)
        cmd_index = ExecuteCMD.enqueue(cmd)

        ExecuteCMD.send(clear_on_success=False)
        resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))

        #desc_name = f'DeviceHealthDescriptor{Dut.get_instance().ufs_version:x}'
        device_descr_payload = resp.data
        dumpfile('device_descr_payload.bin',device_descr_payload)

        get_val = self.health_report.pre_eol_em1.value
        value = int.from_bytes(health_descr_payload[7:9], byteorder='little')
        if get_val != value:
            logger.error_fp(f'{get_val} != {value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH




        get_val = self.health_report.highest_temp.value
        value = int.from_bytes(health_descr_payload[0xC:0xD], byteorder='little')
        if (get_val + 80) != value:
            logger.error_fp(f'{get_val} != {value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH


        get_val = self.health_report.lowest_temp.value
        value = int.from_bytes(health_descr_payload[0xD:0xE], byteorder='little')
        if (get_val + 80) != value:
            logger.error_fp(f'{get_val} != {value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        
        get_val = self.health_report.power_on_highest_temp.value
        value = int.from_bytes(health_descr_payload[0xE:0xF], byteorder='little')
        if (get_val + 80) != value:
            logger.error_fp(f'{get_val} != {value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

        get_val = self.health_report.power_on_lowest_temp.value
        value = int.from_bytes(health_descr_payload[0xF:0x10], byteorder='little')
        if (get_val + 80) != value:
            logger.error_fp(f'{get_val} != {value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        
        get_val = self.health_report.exhausted_life_for_em1.value
        value = int.from_bytes(health_descr_payload[7:8], byteorder='little')
        if get_val != value:
            logger.error_fp(f'{get_val} != {value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH


        get_val = self.health_report.exhausted_life_for_tlc.value
        value = int.from_bytes(health_descr_payload[8:9], byteorder='little')
        if get_val != value:
            logger.error_fp(f'{get_val} != {value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

        
        get_val = self.health_report.exhausted_life_for_slc_table_only.value
        value = int.from_bytes(health_descr_payload[9:10], byteorder='little')
        if get_val != value:
            logger.error_fp(f'{get_val} != {value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH


        get_val = self.health_report.write_data_size_for_em1_unit_100mb.value
        value = int.from_bytes(health_descr_payload[0x10:0x10 + 4], byteorder='little')
        if get_val != value:
            logger.error_fp(f'{get_val} != {value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

        get_val = self.health_report.write_data_size_tlc_unit_100mb.value
        value = int.from_bytes(health_descr_payload[0x14:0x14 + 4], byteorder='little')
        if get_val != value:
            logger.error_fp(f'{get_val} != {value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

        get_val = self.health_report.read_data_size_for_em1_unit_100mb.value
        value = int.from_bytes(health_descr_payload[0x18:0x18 + 4], byteorder='little')
        if get_val != value:
            logger.error_fp(f'{get_val} != {value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH        

        get_val = self.health_report.read_data_size_tlc_unit_100mb.value
        value = int.from_bytes(health_descr_payload[0x1C:0x1C + 4], byteorder='little')
        if get_val != value:
            logger.error_fp(f'{get_val} != {value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH        

        return


    def step1(self) -> None:
        _param = shared.param
        flow_cnt = 1
        logger.flow(flow_cnt, 'get enhanced health report')
        flow_cnt += 1
        self.config_lun()    
        self.get_health_report()
        self.compare_vendorinfo()
        dumpfile('health_report_vu_40FE',self.health_report.payload)
        if 'V6' in api.Dut.get_instance().tester_info.tester_generation:
            self.pattern_get_health_descriptor_then_check()
        # test
        # logger.info(f'spare_block_count_including_the_initial_2_always_reserved_bad_blocks = {self.health_report.spare_block_count_including_the_initial_2_always_reserved_bad_blocks.value}')  
        # bbtmax_revoke_cnt = cast(int,read_fw_value('gUfsApiStruct.ftl->bbt.max_revoke_cnt'))
        # print(f'bbtmax_revoke_cnt = {bbtmax_revoke_cnt}')   

        # debug info 
        
    

        self.write_booster_related_cnt_test()
        #
        logger.flow(flow_cnt, 'config_lock_test')
        self.config_lock_test()
        flow_cnt += 1
        # pre_fdc doing
        
        self.wr100mb_test()
        logger.flow(flow_cnt, 'do Initialization_count_success_test: init flow w ssu powerdown')
        self.spare_block_count_test()
        flow_cnt += 1
        logger.flow(flow_cnt, 'do Read data Size TLC')
        self.read_data_size_tlc_test()
        flow_cnt += 1
        logger.flow(flow_cnt, 'do Read data Size EM1')
        self.read_data_size_tlc_test()
        flow_cnt += 1
        # already done
        logger.flow(flow_cnt, 'device_on_time_test')
        flow_cnt += 1
        self.device_on_time_test()        
        logger.flow(flow_cnt, 'vdet test')
        self.vdet_test()
        flow_cnt += 1
        logger.flow(2, 'do Initialization_count_success_test: init flow w ssu powerdown')
        self.initialization_count_success_test()
        logger.flow(3, 'do Initialization_count_failure_test: : init flow wo ssu powerdown')
        self.initialization_count_failure_test()
        logger.flow(4, 'do write_size_test: write normal partition & em1')
        self.write_size_test()
        logger.flow(5, 'do sleep_cnt_test: ssu sleep')
        self.sleep_cnt_test()       
        logger.flow(6, 'do powerdown_cnt_test: ssu powerdown')
        self.powerdown_cnt_test()                
        logger.flow(7, 'do powerdown_cnt_test: ssu deepsleep')
        self.deepsleep_cnt_test()  
        logger.flow(8, "do temp_boundary_test: too high/low temp count")
        self.temp_boundary_test()
        logger.flow(flow_cnt, 'total_running_time_test')
        flow_cnt += 1
        self.total_running_time_test()
        pass
    def temp_boundary_test(self) -> None:
        
        def VUC_modify_attr(idn: int, value: int) -> None:
            api.access_vendor_mode()
            vuc = ExecuteCMD.VendorCmdWrite()
            vuc.assign(length=api.DATA_SIZE_4K_BYTE, cmd_index=api.VendorCmd.WRITE_PARAMETER, cmd_set_type=0x0F)
            vuc.upiu.u16_cdb.b2_rsvd = api.VendorCmdRuleCdb2.CMD_IN_DOUT
            data = bytearray(b'\x00' * 0x1000)
            data[0] = 0x04  # UFS_version
            data[4] = 0x01  # total_4k_input
            data[8] = 0x44  # 'D' (0x44), high 16 bits = 0 → write_num[DESC]=0
            data[12] = 0x41 # 'A' (0x41), high 16 bits = 1 → write_num[ATTR]=1
            data[14] = 0x01
            data[16] = idn  # modify_index
            data[20] = 36   # Data byte offset in the buffer
            data[24] = 0x01 # Write 1 byte
            data[28] = 0x46 # 'F' (0x46), high 16 bits = 0 → write_num[FLAG]=0
            data[32] = 0x53 # 'S' (0x53), high 16 bits = 0 → write_num[SCSI]=0
            data[data[20]] = value
            vuc.data = data
            vuc.enqueue()
            ExecuteCMD.send()
        
        cmp_fail = False
        high_temp_boundary = api.read_attribute(idn=api.AttributeIDN.DEVICE_TOO_HIGH_TEMP_BOUNDARY)
        low_temp_boundary = api.read_attribute(idn=api.AttributeIDN.DEVICE_TOO_LOW_TEMP_BOUNDARY)
        logger.info(f"Original high boundary={high_temp_boundary}, low boundary={low_temp_boundary}")

        self.get_health_report()
        bf_high_cnt = self.health_report.too_high_temperature_count.value
        bf_low_cnt = self.health_report.too_low_temperature_count.value
        
        VUC_modify_attr(api.AttributeIDN.DEVICE_TOO_HIGH_TEMP_BOUNDARY, 80)
        high_temp_boundary = api.read_attribute(idn=api.AttributeIDN.DEVICE_TOO_HIGH_TEMP_BOUNDARY)
        low_temp_boundary = api.read_attribute(idn=api.AttributeIDN.DEVICE_TOO_LOW_TEMP_BOUNDARY)
        logger.info(f"Modified high boundary={high_temp_boundary}, low boundary={low_temp_boundary}")

        logger.info("Check TooHighTempBoundary Case")
        self.get_health_report()
        if self.health_report.too_high_temperature_count.value == bf_high_cnt:
            logger.error_fp(f"Too High Temp Count should increased, before = {bf_high_cnt}, after = {self.health_report.too_high_temperature_count.value}")
            cmp_fail = True

        VUC_modify_attr(api.AttributeIDN.DEVICE_TOO_HIGH_TEMP_BOUNDARY, high_temp_boundary)
        VUC_modify_attr(api.AttributeIDN.DEVICE_TOO_LOW_TEMP_BOUNDARY, 180)
        high_temp_boundary = api.read_attribute(idn=api.AttributeIDN.DEVICE_TOO_HIGH_TEMP_BOUNDARY)
        low_temp_boundary = api.read_attribute(idn=api.AttributeIDN.DEVICE_TOO_LOW_TEMP_BOUNDARY)
        logger.info(f"Modified high boundary={high_temp_boundary}, low boundary={low_temp_boundary}")

        logger.info("Check TooLowTempBoundary Case")
        self.get_health_report()
        if self.health_report.too_low_temperature_count.value == bf_low_cnt:
            logger.error_fp(f"Too Low Temp Count should increased, before = {bf_low_cnt}, after = {self.health_report.too_low_temperature_count.value}")
            cmp_fail = True

        if cmp_fail:
            logger.error_fp("too high/low temp count unexpected")
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.info("TooHighTempBoundary/TooLowTempBoundary Check Pass")
        
        logger.info("Recover attribute")
        VUC_modify_attr(api.AttributeIDN.DEVICE_TOO_HIGH_TEMP_BOUNDARY, high_temp_boundary)
        VUC_modify_attr(api.AttributeIDN.DEVICE_TOO_LOW_TEMP_BOUNDARY, low_temp_boundary)
    def deepsleep_cnt_test(self)->None:
        original_deep_sleep_state_counter = self.health_report.deep_sleep_state_counter.value
        #         self.sleep_state_counter = self.add_field(0x100, 0x103, 'little')
        # self.deep_sleep_state_counter = self.add_field(0x104, 0x107, 'little')
        # self.power_down_state_counter = self.add_field(0x108, 0x10B, 'little')
        SSU = ExecuteCMD.StartStopUnit()
        SSU.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=4, no_flush=0,start=0)
        SSU.set_option(wait_queue_empty=True)
        ExecuteCMD.enqueue(SSU)
        ExecuteCMD.send()
        init_tester_to_unit_ready(resetmode = Dcmd5ResetType.HW_RESET, powerdown = False)
        self.get_health_report()
        current_deep_sleep_state_counter = self.health_report.deep_sleep_state_counter.value
        self.compare_data_show_log("current_deep_sleep_state_counter",current_deep_sleep_state_counter,"original_deep_sleep_state_counter",original_deep_sleep_state_counter,1)    
    def sleep_cnt_test(self)->None:
        original_sleep_state_counter = self.health_report.sleep_state_counter.value
        #         self.sleep_state_counter = self.add_field(0x100, 0x103, 'little')
        # self.deep_sleep_state_counter = self.add_field(0x104, 0x107, 'little')
        # self.power_down_state_counter = self.add_field(0x108, 0x10B, 'little')
        SSU = ExecuteCMD.StartStopUnit()
        SSU.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=2, no_flush=0,start=0)
        SSU.set_option(wait_queue_empty=True)
        ExecuteCMD.enqueue(SSU)
        ExecuteCMD.send()
        SSU.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=1, no_flush=0,start=0)
        ExecuteCMD.enqueue(SSU)
        ExecuteCMD.send()        
        self.get_health_report()
        current_sleep_state_counter = self.health_report.sleep_state_counter.value
        self.compare_data_show_log("current_sleep_state_counter",current_sleep_state_counter,"original_sleep_state_counter",original_sleep_state_counter,1)     
    def powerdown_cnt_test(self)->None:
        original_power_down_state_counter = self.health_report.power_down_state_counter.value
        #         self.sleep_state_counter = self.add_field(0x100, 0x103, 'little')
        # self.deep_sleep_state_counter = self.add_field(0x104, 0x107, 'little')
        # self.power_down_state_counter = self.add_field(0x108, 0x10B, 'little')
        SSU = ExecuteCMD.StartStopUnit()
        SSU.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=3, no_flush=0,start=0)
        SSU.set_option(wait_queue_empty=True)
        ExecuteCMD.enqueue(SSU)
        ExecuteCMD.send()
        SSU.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=1, no_flush=0,start=0)
        ExecuteCMD.enqueue(SSU)
        ExecuteCMD.send()        
        self.get_health_report()
        current_power_down_state_counter = self.health_report.power_down_state_counter.value
        self.compare_data_show_log("current_power_down_state_counter",current_power_down_state_counter,"original_power_down_state_counter",original_power_down_state_counter,1)        
    def write_size_test(self)->None:
        original_total_write_size = self.health_report.total_write_size.value
        original_total_tlc_write_size = self.health_report.total_tlc_write_size.value
        write_data_4k = random.randint(1,128)
        self.write_data(0,0,write_data_4k,write_data_4k)
        self.get_health_report()
        current_total_write_size = self.health_report.total_write_size.value
        current_total_tlc_write_size = self.health_report.total_tlc_write_size.value
        self.compare_data_show_log("current_total_write_size",current_total_write_size,"original_total_write_size",original_total_write_size,write_data_4k,">")        
        self.compare_data_show_log("current_total_tlc_write_size",current_total_tlc_write_size,"original_total_tlc_write_size",original_total_tlc_write_size,write_data_4k,">")        
        original_total_write_size = current_total_write_size
        original_total_slc_write_size = self.health_report.total_slc_write_size.value
        write_data_4k = random.randint(1,128)
        self.write_data(3,0,write_data_4k,write_data_4k)        
        self.get_health_report()
        current_total_write_size = self.health_report.total_write_size.value
        current_total_slc_write_size = self.health_report.total_slc_write_size.value 
        self.compare_data_show_log("current_total_write_size",current_total_write_size,"original_total_write_size",original_total_write_size,write_data_4k,">")        
        self.compare_data_show_log("current_total_slc_write_size",current_total_slc_write_size,"original_total_slc_write_size",original_total_slc_write_size,write_data_4k,">")           

    def initialization_count_success_test(self)->None:
        original_init_success_cnt = self.health_report.initialization_count_success.value
        original_safe_shutdown_initialization_count = self.health_report.safe_shutdown_initialization_count.value
        original_init_count_pon = self.health_report.init_count_pon.value

        init_tester_to_unit_ready(resetmode = Dcmd5ResetType.HW_RESET, powerdown = True)
        self.get_health_report()
        current_init_success_cnt = self.health_report.initialization_count_success.value
        current_safe_shutdown_initialization_count = self.health_report.safe_shutdown_initialization_count.value
        current_init_count_pon = self.health_report.init_count_pon.value
        self.compare_data_show_log("current_init_success_cnt",current_init_success_cnt,"original_init_success_cnt",original_init_success_cnt,1)
        self.compare_data_show_log("current_safe_shutdown_initialization_count",current_safe_shutdown_initialization_count,"original_safe_shutdown_initialization_count",original_safe_shutdown_initialization_count,1)
        self.compare_data_show_log("current_init_count_pon",current_init_count_pon,"original_init_count_pon",original_init_count_pon,1)
        
    def write_data(self, lun:int, start_lba:int, total_size: int, chunk_size:int) -> None:

        chunk_size = 65535

        lba = start_lba

        total_len = total_size

        while(total_len):

            write10 = ExecuteCMD.Write10()

            chunk_size = min(int(chunk_size),int(total_len))

            write10.assign(lun=lun, lba=lba, length=chunk_size, fua=0)

            write10.set_option(pattern_mode=CmdParamPatternMode.HW_FIX)

            ExecuteCMD.enqueue(write10)

            total_len -= chunk_size    

            lba += chunk_size

        ExecuteCMD.send(clear_on_success=True)  
    def read_data(self, lun:int, start_lba:int, total_size: int, chunk_size:int) -> None:

        chunk_size = 65535

        lba = start_lba

        total_len = total_size

        while(total_len):

            read10 = ExecuteCMD.Read10()

            chunk_size = min(int(chunk_size),int(total_len))
            ExecuteCMD.Read10().assign(lun = lun, lba=lba, length=chunk_size, fua=0).enqueue()

            total_len -= chunk_size    

            lba += chunk_size

        ExecuteCMD.send(clear_on_success=True)         

    def initialization_count_failure_test(self)->None:
        original_init_failure_cnt = self.health_report.initialization_count_failure.value
        original_init_count_spor = self.health_report.init_count_spor.value
        original_unsafe_shutdown_initialization_count = self.health_report.unsafe_shutdown_initialization_count.value
        original_spor_recovery_count = self.health_report.spor_recovery_count.value
        # self.init_count_spor 
        # unsafe_shutdown_initialization_count
        self.write_data(0, 0, 128, 65535)
        init_tester_to_unit_ready(resetmode = Dcmd5ResetType.HW_RESET, powerdown = False)
        self.get_health_report()
        current_init_failure_cnt = self.health_report.initialization_count_failure.value
        current_init_count_spor = self.health_report.init_count_spor.value
        current_unsafe_shutdown_initialization_count = self.health_report.unsafe_shutdown_initialization_count.value
        current_spor_recovery_count = self.health_report.spor_recovery_count.value
        self.compare_data_show_log("current_init_count_spor",current_init_count_spor,"original_init_count_spor",original_init_count_spor,1)
        self.compare_data_show_log("current_unsafe_shutdown_initialization_count",current_unsafe_shutdown_initialization_count,"original_unsafe_shutdown_initialization_count",original_unsafe_shutdown_initialization_count,1)
        self.compare_data_show_log("current_spor_recovery_count",current_spor_recovery_count,"original_spor_recovery_count",original_spor_recovery_count,1)

        init_tester_to_unit_ready(resetmode = Dcmd5ResetType.RESET_N, powerdown = False)
        self.get_health_report()
        final_spor_recovery_count = self.health_report.spor_recovery_count.value

        self.compare_data_show_log("final_spor_recovery_count",final_spor_recovery_count,"current_spor_recovery_count",current_spor_recovery_count,1)
        init_tester_to_unit_ready(resetmode = Dcmd5ResetType.HW_RESET, powerdown = True)
        self.get_health_report()
        final_spor_recovery_count_2 = self.health_report.spor_recovery_count.value

        self.compare_data_show_log("final_spor_recovery_count_2",final_spor_recovery_count_2,"final_spor_recovery_count",final_spor_recovery_count,0)
    def post_process(self) -> None:
        pass
    
    def find_diff_positions(self, ba1: bytearray, ba2: bytearray) -> List[int]:
        diff_positions = []
        min_len = min(len(ba1), len(ba2))
        
        # ?�d�ۦP?�׳���
        for i in range(min_len):
            if ba1[i] != ba2[i]:
                diff_positions.append(i)
        
        # ?�d?�פ��P������
        if len(ba1) != len(ba2):
            max_len = max(len(ba1), len(ba2))
            for i in range(min_len, max_len):
                diff_positions.append(i)
        
        return diff_positions

run = Pattern().run
if __name__ == "__main__":
    run()