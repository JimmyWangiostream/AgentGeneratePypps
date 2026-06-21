import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api import shared
from Script.lib import sdk_lib as lib
import random
from Script.api.ufs_api import *
from Script.api.exception import *
from Script.api.cmd_seq.response import CommandResponse,QueryResponse
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from typing import cast, Callable
import time

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = shared.param
        self.total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.au_to_node = (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size * 512 ) // api.DATA_SIZE_4K_BYTE
        self.fw_geometry = api.get_fw_geometry()
        self.TLC_VB_4K_SIZE = (self.fw_geometry.l88_vb_size_u1 * 512) // api.DATA_SIZE_4K_BYTE
        self.SLC_VB_4K_SIZE = (self.fw_geometry.l84_vb_size_u0 * 512) // api.DATA_SIZE_4K_BYTE
        pass
    def step1(self) -> None:
        logger.flow("Case", 'bBackgroundOpStatus = 0 Test')
        value_from_attribute = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)

        logger.flow(1, 'Check attr = BackgroundOpStatus = 0')
        value_from_vu = project_api.issue_40DB_to_get_bkops_status()
        if value_from_vu != 0:
            logger.error(f'Expect defalut bkops value = 0, but = {value_from_vu}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(2, 'Compare attribute = bBackgroundOpStatus(05h) value = VU 40DB value')
        self.compare_value(value_from_attribute, value_from_vu, case = 0)

    def step2(self) -> None:
        logger.flow("Case", 'bBackgroundOpStatus = 1 Test')
        slc_lun, tlc_lun = self.config_lun(slc_au=0,tlc_au=self.total_au)
        
        data_len = api.WRITE_10_MAX_BLOCK_LEN

        total_len = self._param.gLUCapacity[tlc_lun]
        start_lba = 0
        
        bkops_status_index_list :List[int] = []
        vu_index_list :List[int] = []
        bkops_equal_1 = False
        vu_data_equal_1 = False
        logger.flow(3, '=== Write with VU 40DB ===')  
        total_len = self._param.gLUCapacity[tlc_lun]
        data_len = api.WRITE_10_MAX_BLOCK_LEN
        start_lba = 0
        while total_len :
            data_len = min(data_len, total_len)
            if (start_lba + data_len) > self._param.gLUCapacity[tlc_lun] :
                start_lba = random.randint(0, self._param.gLUCapacity[tlc_lun] - data_len -1)
            
            logger.info(f'[WRITE10] lun = {tlc_lun},start lba = {start_lba}, len = {data_len}, total_len = {data_len}')
            self.write_data(lun=tlc_lun, start_lba=start_lba, len=data_len,total_len=data_len, send=False)
            
            vu = self.my_40DB_vu_cmd()
            logger.info(f'vu read buffer idx = {vu}')
            vu_index_list.append(vu)
            start_lba += data_len
            total_len -= data_len

        ExecuteCMD.send(timeout=api.UniformTimeout(val=30000, unit=api.TimeResolution.ms), clear_on_success=False)
        for idx in vu_index_list:
            rsp = ExecuteCMD.read_response(idx)
            vu_value = rsp.data[0]
            logger.info(f'idx = {idx}, VU40DB = {vu_value}')
            if vu_value == 1:
                vu_data_equal_1 = True
        ExecuteCMD.clear()
        if vu_data_equal_1 == False:
            logger.error(f'Expect get VU40DB = 1, but not')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
        
    def step3(self) -> None:
        logger.flow("Case", 'bBackgroundOpStatus = 2 Test')

        logger.flow(7, '=== Config writebooster size = 4GB ===')
        config_wb_size = 4 * api.DATA_SIZE_1G_BYTE // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size * 512)
        self.config_wb(config_wb_size)

        logger.flow(8, '=== Enable writebooster ===')
        if api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN) != 1:
            logger.error('Set WRITEBOOSTER_EN fail')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(9, '=== Set EventControl bit[2] urgent_bkops_en / bit[5] WRITEBOOSTER_EVNET_EN ===')
        val = BIT2 | BIT5
        api.write_attribute(idn=api.AttributeIDN.EXC_EVENT_CONTROL, val=val)

        logger.flow(10, 'Sequential write to full writebooster')
        total_len = (config_wb_size * self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size * 512 ) // api.DATA_SIZE_4K_BYTE
        data_len = api.WRITE_10_MAX_BLOCK_LEN
        self.write_data(lun=0,start_lba=0,len=data_len,total_len=total_len*2)

        logger.flow(11, '=== Check EventStatus bit[2] urgent_bkops_en = 0 / bit[5] WRITEBOOSTER_EVENT_EN = 1 ===')
        event_status = api.read_attribute(idn=api.AttributeIDN.EXC_EVENT_STATUS)
        if event_status != BIT5:
            logger.error('Set eventcontrol bit5 = 1 -> write all wb size -> check eventstatus bit5 = 1, but not')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(12, '=== Check event alert raise in read/write(fua)/write(w/o fua)/query ===')
        self.check_event_alert(expect_event_alert_val = 1)

        logger.flow(13, 'Enable writebooster flush')
        if api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN) != 1:
            logger.error('Set WRITEBOOSTER_BUFFER_FLUSH_EN fail')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(14, 'Polling bkops = 2 ')
        func = lambda: api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS) 
        value_from_attribute = self.wait_until(func, expect_value=2,timeout=900)
        
        logger.flow(15, 'Get value from VU 40DB')
        value_from_vu = project_api.issue_40DB_to_get_bkops_status()
        logger.info(f'VU 40DB = {value_from_vu}')

        logger.flow(16, 'Compare attribute = bBackgroundOpStatus(05h) value = VU 40DB value')
        self.compare_value(value_from_attribute, value_from_vu, case=2)

        logger.flow(17, 'Polling VU 40DB = 0 to check wb flush finish')
        func = lambda: project_api.issue_40DB_to_get_bkops_status()
        value_from_attribute = self.wait_until(func, expect_value=0,timeout=900)
        
        logger.flow(18, 'Check available writebooster size = 0xA when VU 40DB = 0')
        func = lambda: api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
        available_wb_size = self.wait_until(func, expect_value=0xA,timeout=900)
    
        
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)
        pass
    def my_read_attribute(self,idn: int, index: int=0, selector: int=0)->int:
        logger.info(f'Push read bkops status')
        read_attr = ExecuteCMD.ReadAttribute().assign(idn=idn, index=index, selector=selector).set_option(wait_queue_empty=True).enqueue()
        
        return read_attr
    def step4(self) -> None:
        logger.flow("Case", 'bBackgroundOpStatus = 3 Test') 
        logger.flow(19, 'Config 1 normal lun 1 em1 lun, au = total au // 2')
        slc_lun, tlc_lun = self.config_lun(slc_au=self.total_au//2,tlc_au=self.total_au//2)

        logger.flow(20, '=== Set EventControl bit[2] urgent_bkops_en ===')
        val = BIT2
        api.write_attribute(idn=api.AttributeIDN.EXC_EVENT_CONTROL, val=val)

        logger.flow(21, 'write 1 used tlc vb')
        total_len = self.TLC_VB_4K_SIZE
        data_len = api.WRITE_10_MAX_BLOCK_LEN
        start_lba = 0

        while total_len > 0:
            data_len = min(total_len, data_len)
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=tlc_lun, lba=start_lba, length=data_len, fua=0)
            ExecuteCMD.enqueue(write10)
            
            start_lba += data_len
            total_len -= data_len
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
            
        logger.flow(22, 'VUC l2p(0x88) get lba = 0 pca')
        
        pca = api.lba_to_pba(lun=tlc_lun,lba=0)
        vb_number = pca.w10_block.value

        logger.flow(23, 'Issue C088 to stop refrseh')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)

        logger.flow(24, f'VUC force trigger refresh on vb={vb_number}')
        api.force_trigger_refresh_job(vb_number)

        logger.flow(25, 'Read bBackgroundOpStatus(05h)')
        func = lambda: api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS) 
        value_from_attribute = self.wait_until(func, expect_value=3,timeout=900)

        logger.flow(26, 'Get value from VU 40DB')
        value_from_vu = project_api.issue_40DB_to_get_bkops_status()
        logger.info(f'VU 40DB = {value_from_vu}')

        logger.flow(27, '=== Check EventStatus bit[2] urgent_bkops_en = 1 ===')
        event_status = api.read_attribute(idn=api.AttributeIDN.EXC_EVENT_STATUS)
        if event_status != BIT2:
            logger.error('Expect eventstatus bit2 = 1 when bkops status = 3, but not')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(28, '=== Check event alert not raise in read/write(fua)/write(w/o fua)/query ===')
        self.check_event_alert(expect_event_alert_val = 0)

        logger.flow(29, 'Issue C088 to start refrseh')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        
        logger.flow(30, 'Compare attribute = bBackgroundOpStatus(05h) value = VU 40DB value')
        self.compare_value(value_from_attribute, value_from_vu, case=3)


    def check_event_alert(self, expect_event_alert_val:int)->None:
        logger.info('Send read cmd')
        read10_idx = ExecuteCMD.Read10().assign(lun=0, lba=0, length=1).enqueue() 
        logger.info('Send write cmd wtih fua')
        write10_fua_idx = ExecuteCMD.Write10().assign(lun=0, lba=0, length=1, fua=1).enqueue() 
        logger.info('Send write cmd without fua')
        write10_no_fua_idx = ExecuteCMD.Write10().assign(lun=0, lba=0, length=1, fua=0).enqueue()
        logger.info('Send query cmd')
        query_idx = ExecuteCMD.ReadFlag().assign(idn=api.FlagIDN.BG_OP_EN).enqueue()

        ExecuteCMD.send(clear_on_success=False)
        rsp = ExecuteCMD.read_response(read10_idx)
        if rsp.upiu.b9_device_information != expect_event_alert_val:
            logger.error(f'send read cmd expect event alert = {expect_event_alert_val}, but = {rsp.upiu.b9_device_information}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        rsp = ExecuteCMD.read_response(write10_fua_idx)
        if rsp.upiu.b9_device_information != expect_event_alert_val:
            logger.error(f'send write cmd with fua expect event alert = {expect_event_alert_val}, but = {rsp.upiu.b9_device_information}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        rsp = ExecuteCMD.read_response(write10_no_fua_idx)
        if rsp.upiu.b9_device_information != expect_event_alert_val:
            logger.error(f'send write cmd without fua expect event alert = {expect_event_alert_val}, but = {rsp.upiu.b9_device_information}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        rsp = ExecuteCMD.read_response(query_idx)
        if rsp.upiu.b9_device_information != expect_event_alert_val:
            logger.error(f'send read flag expect event alert = {expect_event_alert_val}, but = {rsp.upiu.b9_device_information}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        ExecuteCMD.clear()

    def my_40DB_vu_cmd(self)-> int:
        logger.info(f'Push VU 40DB')
        vu = project_api.micron_vendor_cmd()
        vu.b0_opcode.value = 0xDB
        vu.b1_func.value = 0x40
        vu.w2_transfer_length.value = 4096
        vu.d4_random_stamp.value = random.randint(0x1, 0x100000000) 

        write_buffer = ExecuteCMD.WriteBuffer()
        write_buffer.assign(lun=1, mode=0xE1, buffer_id=0, buffer_offset=0, length=44, vendor=True)
        write_buffer.set_option(wait_queue_empty=True)
        write_buffer.data = bytearray(vu.payload)
        ExecuteCMD.enqueue(write_buffer)

        read_buffer = ExecuteCMD.ReadBuffer()
        read_buffer_len = vu.w2_transfer_length.value
        read_buffer.assign(lun=1, mode=0xC1, buffer_id=0, buffer_offset=0, length=read_buffer_len, vendor=True)
        read_buffer.set_option(wait_queue_empty=True)
        cmd_index = ExecuteCMD.enqueue(read_buffer)
        return cmd_index

    def config_lun(self,slc_au:int, tlc_au:int) -> tuple[int,int]:
        
        config_descs = api.get_config_descriptors(print=True)
        for table in range(4):
            for unit in range(8):
                config_descs[table].header.b2_conf_desc_continue = 1
                config_descs[table].units[unit].b0_lu_enable = 0
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].l4_num_alloc_units = 0
                config_descs[table].units[unit].b9_logical_block_size = 0xc
                config_descs[table].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                if (table * 8 + unit) == 0:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[table].units[unit].l4_num_alloc_units = slc_au
                elif (table * 8 + unit) == 1:
                    config_descs[0].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[0].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[0].units[unit].l4_num_alloc_units = tlc_au
        
        config_descs[3].header.b2_conf_desc_continue = 0
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.ENABLE
        config_descs[0].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0
        for i in range(4):
            api.push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        ExecuteCMD.clear()

        unit_desc_idxes:List[int] = []
        for lun in range(0, self._param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            update_descriptor(DescriptorIDN.UNIT, index, cast(QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

        for lun in range(self._param.gMaxNumberLU):
            if self._param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

        slc_lun = 0
        tlc_lun = 1
        return (slc_lun, tlc_lun)
    def read_data(self,lun:int, start_lba:int, len:int, total_len:int) -> None:
        while total_len > 0:
            len = min(total_len, len)
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=lun, lba=start_lba, length=len, fua=0)
            ExecuteCMD.enqueue(read10)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
    def write_data(self, lun:int=0, start_lba:int=0, len:int=0, total_len:int=0, send:bool = True) -> None:
        while total_len > 0:
            len = min(total_len, len)
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=lun, lba=start_lba, length=len, fua=0)
            ExecuteCMD.enqueue(write10)
            start_lba += len
            total_len -= len
        if send == True:
            ExecuteCMD.send(timeout=api.UniformTimeout(val=30000, unit=api.TimeResolution.ms), clear_on_success=False)
            ExecuteCMD.clear()
        

    T = TypeVar("T")
    def wait_until(self,func:Callable[[], T], expect_value:int, timeout:int) -> T:
        elapsed_time = 0
        start_time = time.time()
        while True:
            value_from_attribute = func()
            if value_from_attribute == expect_value:
                break
            if (time.time() - start_time) > timeout:
                logger.error('timeout!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        return value_from_attribute
                    

    def config_wb(self, config_wb_size:int) -> None:
        total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        config_descs = api.get_config_descriptors(print=True)
        for table in range(4):
            for unit in range(8):
                config_descs[table].header.b2_conf_desc_continue = 1
                config_descs[table].units[unit].b0_lu_enable = 0
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].l4_num_alloc_units = 0
                config_descs[table].units[unit].b9_logical_block_size = 0xc
                config_descs[table].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                if (table * 8 + unit) == 0:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[table].units[unit].l4_num_alloc_units = total_au
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.ENABLE
        config_descs[0].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = config_wb_size
        config_descs[3].header.b2_conf_desc_continue = 0

        for i in range(4):
            api.push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        ExecuteCMD.clear()
        config_descs = api.get_config_descriptors(print=True)

    def compare_value(self, value_from_attribute :int, value_from_vu:int,  case:int) -> None:
        if value_from_attribute != value_from_vu:
            logger.error_lb(f'bBackgroundOpStatus = {case} test')
            logger.error_fp(f'VU 40DB value = {value_from_vu}, not match attribute = bBackgroundStatus(05h) = {value_from_attribute}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def post_process(self) -> None:
        pass
    

run = Pattern().run
if __name__ == "__main__":
    run()