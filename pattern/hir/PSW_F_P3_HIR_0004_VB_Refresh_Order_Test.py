import package_root
from Script import api
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.pattern.hir.mutual_fun import *
from Script.api.exception import *
import random
from Script.api.ufs_api.defines.bit_define import *
from enum import Enum, IntEnum
from typing import Dict

_sdk = api.shared.sdk
class TestCases(IntEnum):
    COLD_RESKY = 0
    HOT_RESKY = 1
class Access_Mode(int):
    ACCESS_MODE_SLC = 0
    ACCESS_MODE_MLC = 1
class VBTYPE(IntEnum):
    CURRENT_VB = 0
    OPENVB_TLC_SLC = 1
    TABLE_AND_SYSTEM = 2
    CLOSED_TLC_VB = 3
    CLOSED_SLC_STATIC_VB = 4
    CLOSED_SLC_DYNAMIC_WB = 5
    OTHER = 6
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
        self.erase_purge_all()
        

        logger.flow("1-1","Set bRefreshUnit = 0, bRefreshMethod = 1, read dRefreshTotalCount")
        api.write_attribute(idn=api.AttributeIDN.REFRESH_UNIT, val=0)
        api.write_attribute(idn=api.AttributeIDN.REFRESH_METHOD, val=1)
        dev_desc = pattern_get_device_health_descriptor()
        refreshProgress_step1 = int.from_bytes(dev_desc[41:45])
        resfreshCount_step1 = int.from_bytes(dev_desc[37:41])
        logger.info(f'refreshprogress = {refreshProgress_step1}, refreshCount = {resfreshCount_step1}')

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

        last_refresh_vb_type = -1
        start_time_outer = time.time()
        scan_vb_count = 0
        while True:
            logger.flow(3,"get all VB info and record each group type and remap vb of total vbs ")
            ftl_vb_list_data_before = self.get_VB_group()

            check_timeout(start_time=start_time_outer,timeout_min=30)
            logger.flow(4,"read dRefreshProgress, Set RefreshEnable = 1 when cmd queue empty")
            dev_desc = pattern_get_device_health_descriptor()
            refreshProgress_step4 = int.from_bytes(dev_desc[41:45])
            resfreshCount_step4 = int.from_bytes(dev_desc[37:41])
            logger.info(f'refreshProgress = {refreshProgress_step4}')

            api.set_flag(api.FlagIDN.REFRESH_EN)
            logger.flow(5,"read bRefreshStatus")
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

            logger.flow(6,"read bRefreshStatus should == 00h")
            val = api.read_attribute(api.AttributeIDN.REFRESH_STATUS)
            if val != 0:
                logger.error_lb(f'Read refreshstatus again')
                logger.error_fp(f'Expect refresh status = 0, but = {val}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(7,"read dRefreshProgress should increase 1 / total vb count")
            dev_desc = pattern_get_device_health_descriptor()
            refreshProgress_step7 = int.from_bytes(dev_desc[41:45])
            resfreshCount_step7 = int.from_bytes(dev_desc[37:41])
            logger.info(f'refreshprogress = {refreshProgress_step7}, refreshCount = {resfreshCount_step7}')
            
            if refreshProgress_step7 != 0:
                scan_vb_count += 1

                last_refreshProgress = ((scan_vb_count - 1) * 100* 1000)  // self.fw_geometry.l52_total_vb_count
                current_refreshProgress = (scan_vb_count * 100* 1000)  // self.fw_geometry.l52_total_vb_count
                logger.info(f'last refresh progress = {last_refreshProgress}')
                logger.info(f'current refresh progress = {current_refreshProgress}')

                increase_val = current_refreshProgress - last_refreshProgress
                
                if (refreshProgress_step7 - refreshProgress_step4) != increase_val:
                    logger.error_lb(f'Refresh unit = 0, expect refreshProgress increase (1 / total_vb_cnt) * 100')
                    logger.error_fp(f'Expect refreshProgress increase val = {increase_val}, but = {refreshProgress_step7 - refreshProgress_step4}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            

            logger.flow(8,"get all VB info and record each group type and remap vb of total vbs")
            logger.flow("8-1","find different group type and remap vb of vb between step3 and step8 and push diff vb to checkvb list in order")
            
            logger.info('create diff vb list')
            ftl_vb_list_data_after = self.get_VB_group()
            diff_vb : List[Dict[str, int]] = self.check_vb_after_refresh(ftl_vb_list_data_before, ftl_vb_list_data_after)
            
            if len(diff_vb) != 1:
                logger.error_lb(f'Refresh methold = slice -> do refresh')
                logger.error_fp(f'check only one vb do refresh but not')
                #raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            if len(diff_vb) != 0:
                logger.info('current refresh vb info')
                logger.info(diff_vb[0])

                logger.flow(10, "check check vb order : current VB-> OpenVB(TLC&SLC) -> Table and System VB -> \
                        Closed TLC VB -> Closed SLC static(EM1) VB -> Closed SLC dynamic (WB) each group select from oldest to newest)")
                
                current_refresh_vb_type = diff_vb[0]["vb_type"] 
                if current_refresh_vb_type < last_refresh_vb_type:
                    logger.error_lb(f'check vb in specific order')
                    logger.error_fp(f'last vb type = {VBTYPE(last_refresh_vb_type).name}, current vb type = {VBTYPE(current_refresh_vb_type).name}')
                    #raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            last_refresh_vb_type = current_refresh_vb_type

            logger.flow(9,"goto step4~step7 until step7 dRefreshProgress reach 1000000(100%) or 0")
            if refreshProgress_step7 == 100000 or refreshProgress_step7 == 0:
                if resfreshCount_step7 != (resfreshCount_step4 + 1):
                    logger.error_lb(f'When dRefreshProgress reach 1000000(100%) or 0, check refreshTotalCount increase')
                    logger.error_fp(f'Expect refreshTotalCount_after = refreshTotalCount_before + 1, but refreshTotalCount_after = {resfreshCount_step7}, refreshTotalCount_before = {resfreshCount_step4}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    break
            if refreshProgress_step7 > 100000:
                    logger.error_lb(f'Check refreshProgress')
                    logger.error_fp(f'RefreshProgress should not > 100000, but = {refreshProgress_step7}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    
        pass
    
    def post_process(self) -> None:
        pass
    def get_VB_group(self,show:bool = False) -> Dict[int, Dict[str, int]]:
        fw_geometry = api.get_fw_geometry()
        resp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        self.physical_block_index_of_vb = project_api.get_VB_to_PB_mapping()
        valid_cnt_list = self.get_vb_valid_count_info()
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'access_mode': {'pos': 6, 'len': 2, 'mask': 0x3}, 
            'dirty': {'pos': 8, 'len': 1, 'mask': 0x1}, 
            'partition': {'pos': 9, 'len': 2, 'mask': 0x3}, 
        }
        response, rep_data = api.get_vb_info()
        api.dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data)):
            if fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break

            ftl_vb_list_data.update({vb : {k: (((rep_data[vb*4]|rep_data[vb*4+1]<<8) >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
            ftl_vb_list_data[vb]["remap_vb"] =  self.physical_block_index_of_vb[vb]
            ftl_vb_list_data[vb]["group"] = project_api.VB_GROUP(ftl_vb_list_data[vb]["group"])
            ftl_vb_list_data[vb]["vb_type"] = self.get_vb_type(vb, ftl_vb_list_data[vb]["group"], ftl_vb_list_data[vb]["access_mode"], open_vb_information)
            ftl_vb_list_data[vb]["valid_cnt"] = valid_cnt_list[vb]["value"]
            pass
        if show:
            for vb, info in ftl_vb_list_data.items():
                group = info['group']
                access_mode = info['access_mode']
                partition = info['partition']
                logger.info(f'VB {vb} grouptype = {group} ({project_api.VB_GROUP(group).name}), access_mode = {access_mode}, partition = {partition}')
        return ftl_vb_list_data
    
    def check_vb_after_refresh(self, ftl_vb_list_data_before:Dict[int, Dict[str, int]], ftl_vb_list_data_after:Dict[int, Dict[str, int]]) -> List[Dict[str, int]]:
        logger.flow(11, f'check VB after refresh')
        diff_vb : List[Dict[str, int]] = []
        for vb in range(self.fw_geometry.l52_total_vb_count):
            valid_cnt_before = ftl_vb_list_data_before[vb]["valid_cnt"]
            valid_cnt_after = ftl_vb_list_data_after[vb]["valid_cnt"]
            group_before = project_api.VB_GROUP(ftl_vb_list_data_before[vb]["group"])
            group_after = project_api.VB_GROUP(ftl_vb_list_data_after[vb]["group"])
            vbtype_before = VBTYPE(ftl_vb_list_data_before[vb]["vb_type"])
            vbtype_after = VBTYPE(ftl_vb_list_data_after[vb]["vb_type"])
            remap_before = ftl_vb_list_data_before[vb]["remap_vb"]
            remap_after = ftl_vb_list_data_after[vb]["remap_vb"]
            if group_before != group_after or remap_before != remap_after:
                if "FREE" in group_before.name: #skip duplicate
                    continue
                if valid_cnt_before == 0:
                    continue
                logger.info(f'Before: VB: {vb}, Group = {group_before} ({group_before.name}), VB TYPTE = {vbtype_before.name}, remap vb = {remap_before}, vc = {valid_cnt_before}')
                logger.info(f'After:  VB: {vb}, Group = {group_after} ({group_after.name}), VB TYPTE = {vbtype_after.name}, , remap vb = {remap_after}, vc = {valid_cnt_after}')
                logger.info(f'==================================')
                diff_vb.append(ftl_vb_list_data_before[vb])
            
        return diff_vb
    def get_vb_valid_count_info(self)-> Dict[int,Dict[str,int]]:
        vb_valid_count_list_data_format = {
            'value': {'pos': 0, 'len': 32, 'mask': 0xffffffff}, 
        }
        response, rep_data = api.get_vb_valid_cnt_info()
       
        ftl_vb_valid_count_list_data = dict()

        for vb in range(len(rep_data)):
            if self.fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break
            ftl_vb_valid_count_list_data.update({vb : {k: (((rep_data[vb*4] | rep_data[vb*4 +1] << 8 | rep_data[vb*4 +2] << 16 | rep_data[vb*4 +3] << 24) >> v['pos']) & v['mask']) for k, v in vb_valid_count_list_data_format.items()}})
        
        for vb, vb_info in ftl_vb_valid_count_list_data.items():
            validcnt = vb_info['value']
            logger.info(f'[vb = {vb}, valid count = {validcnt}]')
            if validcnt != 0:
                logger.info(f'[has node vb = {vb}, valid count = {validcnt}]')
        return ftl_vb_valid_count_list_data
    def get_vb_type(self,vb_number:int, vb_group_type:int, access_mode:int, open_vb_information:project_api.OpenVBInformation) -> VBTYPE:
        if vb_group_type in [project_api.VB_GROUP.CURRENT_L2_SLC, project_api.VB_GROUP.CURRENT_L2_MLC, project_api.VB_GROUP.CURRENT_L1]:
            return VBTYPE.CURRENT_VB
        elif self.check_open_vb(vb_number, open_vb_information):
            return VBTYPE.OPENVB_TLC_SLC
        elif self.check_table_system_vb(vb_group_type):
            return VBTYPE.TABLE_AND_SYSTEM
        elif vb_group_type == project_api.VB_GROUP.USED_BLK_POOL_MLC and access_mode == Access_Mode.ACCESS_MODE_MLC:
            return VBTYPE.CLOSED_TLC_VB
        elif vb_group_type == project_api.VB_GROUP.USED_BLK_POOL_SLC:
            return VBTYPE.CLOSED_SLC_STATIC_VB
        elif vb_group_type == project_api.VB_GROUP.USED_BLK_POOL_MLC and access_mode == Access_Mode.ACCESS_MODE_SLC:
            return VBTYPE.CLOSED_SLC_DYNAMIC_WB
        else:
            return VBTYPE.OTHER
    def check_open_vb(self,vb_number:int, open_vb_information:project_api.OpenVBInformation) ->bool:
        
        vb_list = [open_vb_information.L2_Open_logical_VB_Host_TLC_number, 
                   open_vb_information.L1_open_VB_S_CHUNK_logical_number, 
                   open_vb_information.open_logical_VB_number_for_Write_Booster_WB_L2,
                   open_vb_information.open_logical_VB_number_for_EM1_L2_Host]
        return any(vb.value == vb_number for vb in vb_list)
    
    def check_table_system_vb(self, vb_group_type:int) -> bool:
        vb_list = [project_api.VB_GROUP.LIST_BLK, 
                   project_api.VB_GROUP.LIST_INDEX_BLK,
                   project_api.VB_GROUP.TMP_CODE_BLK,
                   project_api.VB_GROUP.CURRENT_PTE, 
                   project_api.VB_GROUP.LOG_TAB_BLK, 
                   project_api.VB_GROUP.PTE_POOL, 
                   project_api.VB_GROUP.REFRESH_LINE, 
                   project_api.VB_GROUP.RAIN_SWAP_NO_OBR_SLC_L2_SLC,
                   project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_SLC, 
                   project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_TLC, 
                   project_api.VB_GROUP.RAIN_SWAP_NO_OBR_BLK, 
                   project_api.VB_GROUP.RAIN_SWAP_TLC_CURSOR_BLK, 
                   project_api.VB_GROUP.RESERVED_VB_GROUP0, 
                   project_api.VB_GROUP.RESERVED_VB_GROUP1, 
                   project_api.VB_GROUP.RESERVED_VB_GROUP2,
                   project_api.VB_GROUP.RESERVED_VB_GROUP3]
        return any(vb == vb_group_type for vb in vb_list)
    def purge_operation(self) ->None:
        api.set_flag(idn=api.FlagIDN.PURGE_EN)
        purge_timeout = 30 
        
        start_time = time.time()
        while True:
            if check_timeout(start_time, purge_timeout):
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            val = api.read_attribute(idn=api.AttributeIDN.PURGE_STATUS)
            if val == api.PurgeStatus.PURGE_STS_COMPLETE_SUCCESS:
                break
            time.sleep(1)
    def unmap_data(self,lun:int, start_lba:int, len:int, total_len:int) -> None:
        while total_len > 0:
            len = min(total_len, len)
            unmap = ExecuteCMD.Unmap()
            unmap.assign(lun=lun, lba=start_lba, length=len)
            ExecuteCMD.enqueue(unmap)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
    def erase_purge_all(self) -> None:
        logger.flow(2,'erase all card') 
        _param = shared.param
        continue_push_unmap = True
        for lun in range(32):
            if _param.gUnit[lun].b3_lu_enable == True:
                self.unmap_data(lun=lun,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=_param.gLUCapacity[lun])
        self.purge_operation()
        pass
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