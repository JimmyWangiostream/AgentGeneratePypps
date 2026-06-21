import package_root
from Script import api
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.pattern.hir.mutual_fun import *
from Script.api.exception import *
import random
from typing import Dict
from Script.api.ufs_api.defines.bit_define import *
from enum import Enum, IntEnum
_sdk = api.shared.sdk
class LV1LV2_TestCases(IntEnum):
    LV1_ATS_H8 = 0
    LV1_ATS_WO_H8 = 1
    LV2_SLEEP_H8 = 2
    LV2_SLEEP_WO_H8 = 3
    LV2_POWERDOWN_H8 = 4
    LV2_POWERDOWN_WO_H8 = 5

class Pattern(UFSTC):
    def pre_process(self) -> None:
        flashsetting = api.get_flash_setting()
        self.CE = flashsetting.FLH_Quantity * (BIT0 << flashsetting.Parallel)
        self.fw_geometry = api.get_fw_geometry()
        self.TLC_VB_4K_SIZE = (self.fw_geometry.l88_vb_size_u1 * 512) // api.DATA_SIZE_4K_BYTE
        self.SLC_VB_4K_SIZE = (self.fw_geometry.l84_vb_size_u0 * 512) // api.DATA_SIZE_4K_BYTE
        logger.info(f'total vb count = {self.fw_geometry.l52_total_vb_count}')
        pass

    def step1(self) -> None:
        logger.flow(1,"Config normal LUN0 LUN4 and boot LUN1 LUN2, EM1 LUN3, writebooster max AU")
        self.config_lun()

        logger.flow("1-1","Set bRefreshUnit = 0, bRefreshMethod = 1, read dRefreshTotalCount")
        api.write_attribute(idn=api.AttributeIDN.REFRESH_UNIT, val=0) #0:slice #1:fullcard
        api.write_attribute(idn=api.AttributeIDN.REFRESH_METHOD, val=1) #0:not_define #1:force #2:selective

        dev_desc = pattern_get_device_health_descriptor()
        refreshProgress_step1 = int.from_bytes(dev_desc[41:45])
        resfreshCount_step1 = int.from_bytes(dev_desc[37:41])
        logger.info(f'refreshprogress = {refreshProgress_step1}, refreshCount = {resfreshCount_step1}')
        if refreshProgress_step1 != 0:
            logger.error_lb(f'check bRefreshProgress = 0')
            logger.error_fp(f'Expect bRefreshProgress = 0, but = {refreshProgress_step1}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

       
        logger.flow("2-1","write LUN 0 1.5 TLC VB size (small chunk and big chunk both)")
        api.clear_flag(api.FlagIDN.WRITEBOOSTER_EN)
        data_len = WRITE_10_MAX_BLOCK_LEN
        total_len = (self.TLC_VB_4K_SIZE * 15) // 10
        write_data(lun=0,start_lba=0,len=data_len,total_len=total_len, random_chunk=True)

        logger.flow("2-2","write LUN3 1.5 SLC VB size")
        data_len = WRITE_10_MAX_BLOCK_LEN
        total_len = (self.SLC_VB_4K_SIZE * 15) // 10
        write_data(lun=3,start_lba=0,len=data_len,total_len=total_len)  

        logger.flow("2-3","enable write booster, write LUN4 1.5 SLC VB size")
        api.set_flag(api.FlagIDN.WRITEBOOSTER_EN)
        data_len = WRITE_10_MAX_BLOCK_LEN
        total_len = (self.SLC_VB_4K_SIZE * 15) // 10
        write_data(lun=4,start_lba=0,len=data_len,total_len=total_len)
        api.clear_flag(api.FlagIDN.WRITEBOOSTER_EN)

        logger.flow(3,"read dRefreshProgress, Set RefreshEnable = 1 when cmd queue empty")
        dev_desc = pattern_get_device_health_descriptor()
        refreshProgress_step3 = int.from_bytes(dev_desc[41:45])
        resfreshCount_step3 = int.from_bytes(dev_desc[37:41])
        logger.info(f'refreshProgress = {refreshProgress_step3}')
        api.set_flag(api.FlagIDN.REFRESH_EN)

        logger.flow(4,"read bRefreshStatus")
        start_time_inner = time.time()
        while True:
            check_timeout(start_time=start_time_inner,timeout_min=15)
            
            val = api.read_attribute(api.AttributeIDN.REFRESH_STATUS)
            if val == 3:
                break
            elif val == 1:
                continue
            else:
                logger.error_lb(f'check bRefreshStatus until 03h')
                logger.error_fp(f'Expect refresh status = 03h, but = {val}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        

        logger.flow(5,"read bRefreshStatus should == 00h")
        val = api.read_attribute(api.AttributeIDN.REFRESH_STATUS)
        if val != 0:
            logger.error_lb(f'Read refreshstatus again')
            logger.error_fp(f'Expect refresh status = 0, but = {val}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(6,"read dRefreshProgress should increase 1 / total vb count")
        dev_desc = pattern_get_device_health_descriptor()
        refreshProgress_step6 = int.from_bytes(dev_desc[41:45])
        resfreshCount_step6 = int.from_bytes(dev_desc[37:41])
        logger.info(f'refreshprogress = {refreshProgress_step6}, refreshCount = {resfreshCount_step6}')

        increase_val = (1 * 100* 1000  // self.fw_geometry.l52_total_vb_count)
        if (refreshProgress_step6 - refreshProgress_step3) != increase_val:
            logger.error_lb(f'Refresh unit = 0, expect refreshProgress increase (1 / total_vb_cnt) * 100')
            logger.error_fp(f'Expect refreshProgress increase val = {increase_val}, but = {refreshProgress_step6 - refreshProgress_step3}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        

        logger.flow(7,"reconfig")
        self.config_lun()

        logger.flow(8,"read dRefreshProgress should = 0")
        dev_desc = pattern_get_device_health_descriptor()
        refreshProgress_step8 = int.from_bytes(dev_desc[41:45])
        resfreshCount_step8 = int.from_bytes(dev_desc[37:41])
        logger.info(f'refreshprogress = {refreshProgress_step8}, refreshCount = {resfreshCount_step8}')
        if refreshProgress_step8 != 0:
            logger.error_lb(f'After reconfig, refreshProgress shall = 0')
            logger.error_fp(f'Expect refreshProgress = 0, but = {refreshProgress_step8}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(9,"Set bRefreshMethod = 0")
        api.write_attribute(idn=api.AttributeIDN.REFRESH_METHOD, val=0)

        logger.flow(10,"Set RefreshEnable = 1, should response General Failure(0xFF)")
        set_flag = ExecuteCMD.SetFlag().assign(idn=api.FlagIDN.REFRESH_EN, index=0, selector=0).enqueue()
        response = cast(api.QueryResponse, self.sendcmd_keeperror(cmd_index=set_flag))
        if response.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE:
            logger.error_lb(f'Set bRefreshMethold = 0 -> set flag = refresh enable')
            logger.error_fp(f'Expect the response should be 0xFF general failure, but current value is 0x{response.upiu.b6_query_response:02X}')
            raise SIGHTING_RESPONSE_UNEXPECTED

            
        pass
    
    def post_process(self) -> None:
        pass
    def  sendcmd_keeperror(self, cmd_index:int) -> api.CommandResponse:
        try:
            ExecuteCMD.send(clear_on_success=False)
            response = ExecuteCMD.read_response(cmd_index)
        except api.DLL_RESPONSE_ERROR:
            response = ExecuteCMD.read_response(cmd_index)
        ExecuteCMD.clear()
        return response
    def compare_value(self,value:int,expect_value:int, desc:str="") -> None:
        if value != expect_value:
            logger.error_lb(f'compare value')
            logger.error_fp(f'Expect {desc}={expect_value}, but = {value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.info(f'{desc} val = {value}')
    def enter_exit_h8(self) -> None:
        f = ExecuteCMD.CmdSeqHibernate() 
        f.set_option(
            hibernate_enter=1,
            hibernate_exit=1,
            loopcount=10,
            delayafterenter=500,
            delayafterexit=1000,
            wait_queue_empty=True,
            delay_time=100
        )
        
        ExecuteCMD.enqueue(f)
        ExecuteCMD.send(clear_on_success=True)
    def config_lun(self) -> None:
        total_au = shared.param.gGeometry.q4_total_raw_device_capacity // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
        bootlun_au = 0
        for unit_idx in range(32):
            logger.info(f"Get Unit Descriptor [{unit_idx}]")
            unit_desc =  api.get_unit_descriptor(unit_idx)
            if unit_desc.b4_boot_lun_id == 1 or unit_desc.b4_boot_lun_id == 2:
                logger.info(f'lun = {unit_idx}, bootlun au = {unit_desc.q11_logical_block_count}')
                if unit_desc.b8_memory_type == api.MemoryType.ENHANCED_1:
                    bootlun_au = 3 * (unit_desc.q11_logical_block_count * 4096) // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size * 512)
                else:
                    bootlun_au = (unit_desc.q11_logical_block_count * 4096) // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size * 512)

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
                    config_descs[table].units[unit].l4_num_alloc_units = (total_au - 2*bootlun_au) // 3
                elif (table * 8 + unit) == 1:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 1
                    config_descs[table].units[unit].l4_num_alloc_units = bootlun_au
                elif (table * 8 + unit) == 2:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 2
                    config_descs[table].units[unit].l4_num_alloc_units = bootlun_au
                elif (table * 8 + unit) == 3:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[table].units[unit].l4_num_alloc_units = (total_au - 2*bootlun_au) // 3
                elif (table * 8 + unit) == 4:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[table].units[unit].l4_num_alloc_units = (total_au - 2*bootlun_au) // 3
        
        config_descs[3].header.b2_conf_desc_continue = 0
        config_descs[0].header.b7_secure_removal_type = 0
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.ENABLE
        config_descs[0].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = shared.param.gGeometry.l79_write_booster_buffer_max_n_alloc_units
        for i in range(4):
            api.push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        ExecuteCMD.clear()

        unit_desc_idxes:List[int] = []
        _param = api.shared.param
        for lun in range(0, _param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

        #test unit ready all enable lun
        for lun in range(_param.gMaxNumberLU):
            if _param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
        return

run = Pattern().run
if __name__ == "__main__":
    run()