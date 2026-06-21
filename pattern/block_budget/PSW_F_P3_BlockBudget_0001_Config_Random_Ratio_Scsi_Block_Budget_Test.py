import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.api.struct_helper import *
import struct
from Script.api.ufs_api.defines.enum_define import *
from Script.api.exception import *
from Script.api import shared
import random
from Script.api.ufs_api import *
import math, time
from typing import Dict
from Script import project_api

class EVENT(IntEnum):
    WRITE = 0
    UNMAP = 1
    FFU = 2
    PURGE = 3
    READ_COMPARE = 4
    EVENT_CNT = 5

class BlockInfo:
    def __init__(self, hidden_blk: int = 0, spare_blk: int = 0, ics_blk: int = 0,
                 table_blk: int = 0, slc_blk: int = 0,
                 dynamic_bounday0: int = 0, dynamic_bounday1: int = 0):

        self.hidden_blk = hidden_blk
        self.spare_blk = spare_blk
        self.ics_blk = ics_blk
        self.table_blk = table_blk
        self.slc_blk = slc_blk
        self.dynamic_bounday0 = dynamic_bounday0
        self.dynamic_bounday1 = dynamic_bounday1


block_budget_criteria_dict_CE1 = {
    "Open_Card":{"system_table": 23,"slc_user_data":1,"slc_op":1,"rev_blk_for_gc_open_blk_slc":6,"tlc_user_data":394,"tlc_op":18,"rev_blk_for_gc_open_blk_tlc":8,"hidden_blk":8,"max_bb_replacement_cnt":4},
    "TLC_100_SLC_0":{"system_table": 23,"slc_user_data":1,"slc_op":1,"rev_blk_for_gc_open_blk_slc":6,"tlc_user_data":394,"tlc_op":18,"rev_blk_for_gc_open_blk_tlc":8,"hidden_blk":8,"max_bb_replacement_cnt":4},
    "TLC_0_SLC_100":{"system_table": 23,"slc_user_data":394,"slc_op":18,"rev_blk_for_gc_open_blk_slc":6,"tlc_user_data":0,"tlc_op":0,"rev_blk_for_gc_open_blk_tlc":8,"hidden_blk":8,"max_bb_replacement_cnt":4},
    "TLC_50_SLC_50":{"system_table": 23,"slc_user_data":198,"slc_op":9,"rev_blk_for_gc_open_blk_slc":6,"tlc_user_data":197,"tlc_op":9,"rev_blk_for_gc_open_blk_tlc":8,"hidden_blk":8,"max_bb_replacement_cnt":4},
}
block_budget_criteria_dict_CE2 = {
    "Open_Card":{"system_table": 23,"slc_user_data":1,"slc_op":1,"rev_blk_for_gc_open_blk_slc":6,"tlc_user_data":394,"tlc_op":18,"rev_blk_for_gc_open_blk_tlc":8,"hidden_blk":8,"max_bb_replacement_cnt":4},
    "TLC_100_SLC_0":{"system_table": 23,"slc_user_data":1,"slc_op":1,"rev_blk_for_gc_open_blk_slc":6,"tlc_user_data":394,"tlc_op":18,"rev_blk_for_gc_open_blk_tlc":8,"hidden_blk":8,"max_bb_replacement_cnt":4},
    "TLC_0_SLC_100":{"system_table": 23,"slc_user_data":394,"slc_op":18,"rev_blk_for_gc_open_blk_slc":6,"tlc_user_data":0,"tlc_op":0,"rev_blk_for_gc_open_blk_tlc":8,"hidden_blk":8,"max_bb_replacement_cnt":4},
    "TLC_50_SLC_50":{"system_table": 23,"slc_user_data":197,"slc_op":9,"rev_blk_for_gc_open_blk_slc":6,"tlc_user_data":197,"tlc_op":9,"rev_blk_for_gc_open_blk_tlc":8,"hidden_blk":8,"max_bb_replacement_cnt":4},
}
block_budget_criteria_dict_CE4 = {
    "Open_Card":{"system_table": 23,"slc_user_data":1,"slc_op":1,"rev_blk_for_gc_open_blk_slc":6,"tlc_user_data":394,"tlc_op":18,"rev_blk_for_gc_open_blk_tlc":8,"hidden_blk":8,"max_bb_replacement_cnt":4},
    "TLC_100_SLC_0":{"system_table": 23,"slc_user_data":1,"slc_op":1,"rev_blk_for_gc_open_blk_slc":6,"tlc_user_data":394,"tlc_op":18,"rev_blk_for_gc_open_blk_tlc":8,"hidden_blk":8,"max_bb_replacement_cnt":4},
    "TLC_0_SLC_100":{"system_table": 23,"slc_user_data":394,"slc_op":18,"rev_blk_for_gc_open_blk_slc":6,"tlc_user_data":0,"tlc_op":0,"rev_blk_for_gc_open_blk_tlc":8,"hidden_blk":8,"max_bb_replacement_cnt":4},
    "TLC_50_SLC_50":{"system_table": 23,"slc_user_data":197,"slc_op":9,"rev_blk_for_gc_open_blk_slc":6,"tlc_user_data":197,"tlc_op":9,"rev_blk_for_gc_open_blk_tlc":8,"hidden_blk":8,"max_bb_replacement_cnt":4},
}
block_budget_criteria_dict = {
    "1" : block_budget_criteria_dict_CE1,
    "2" : block_budget_criteria_dict_CE2,
    "4" : block_budget_criteria_dict_CE4
}
least_vb_cnt_criteria_dict = {
    "1": 457,
    "2": 455,
    "4": 455
}
class VBCount(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(36), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.system_table = self.add_field(0, 3, 'little')
        self.slc_user_data = self.add_field(4, 7, 'little')
        self.slc_op = self.add_field(8, 11, 'little')
        self.rev_for_gc_and_open_slc = self.add_field(12, 15, 'little')
        self.tlc_user_data = self.add_field(16, 19, 'little')
        self.tlc_op = self.add_field(20, 23, 'little')
        self.rev_for_gc_and_open_tlc = self.add_field(24, 27, 'little')
        self.hidden_blk = self.add_field(28, 31, 'little')
        self.max_bb_replacement_cnt = self.add_field(32, 35, 'little')

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = shared.param
        self.write_record = api.get_empty_write_record()
        flashsetting = api.get_flash_setting()
        self.CE = str(flashsetting.FLH_Quantity * (BIT0 << flashsetting.Parallel))
        self.ce_num = flashsetting.Max_Fdevice
    def step1(self) -> None:
        logger.flow(0, 'Check if all vb cnt meet block budget criteria')
        logger.flow("0-1", 'Get all vb cnt')
        vb_cnt = self.get_all_vb_cnt()
        self.check_meet_block_budget_criteria(vb_cnt, case=0, config_setting="Open_Card")

        logger.flow("0-2", 'Check if all vb cnt >=  least bloct count')
        self.check_least_vb_cnt(vb_cnt)

    def step2(self) -> None:
        logger.flow(1, 'Precondition SLC & MLC Partition')
        for case in range(1, 28):
            if case == 1:
                normal_ratio = 100
                em1_ratio = 0
            elif case == 2:
                normal_ratio = 25
                em1_ratio = 75
            elif case == 3:
                normal_ratio = 75
                em1_ratio = 25
            elif case == 4:
                normal_ratio = 50
                em1_ratio = 50
            elif case == 5:
                normal_ratio = 10
                em1_ratio = 90
            elif case == 6:
                normal_ratio = 90
                em1_ratio = 10
            elif case == 7:
                normal_ratio = 0
                em1_ratio = 100
            elif case >= 8 and case <= 17 :
                normal_ratio = case - 7  # 1~10
                em1_ratio = 100 - normal_ratio 
            elif case >= 18 and case <= 27:
                em1_ratio = case - 17 # 1~10
                normal_ratio = 100 - em1_ratio
            
            logger.flow(1, f'case = {case}, TLC ratio = {normal_ratio}, SLC ratio = {em1_ratio}')
            normal_lun_list, em1_lun_list = self.config_lun(normal_ratio, em1_ratio)

            config_setting = "TLC_" + str(normal_ratio) + "_SLC_" + str(em1_ratio)

            logger.flow(2, 'Check if all vb cnt meet block budget criteria')
            vb_cnt = self.get_all_vb_cnt()
            self.check_meet_block_budget_criteria(vb_cnt, case, config_setting)

            logger.flow("2-1", 'Check TotalRawCap Size as expect')
            self.check_total_capacity()

            logger.flow(3, 'random scsi test')
            enable_lun_list = normal_lun_list + em1_lun_list
            self.random_scsi_test(enable_lun_list)
            self.write_record = api.get_empty_write_record()

    def check_total_capacity(self) -> None:
        
        flashsetting = api.get_flash_setting()
        CE = flashsetting.FLH_Quantity * (BIT0 << flashsetting.Parallel)
        if CE == 1:
            expect_value = 0xEE64000
        elif CE == 2:
            expect_value = 0x1DCBC000
        elif CE == 4:
            expect_value = 0x3B96C000

        if self._param.gGeometry.q4_total_raw_device_capacity != expect_value:
            logger.error(f'Expect total raw device capacity = {expect_value}, but = {self._param.gGeometry.q4_total_raw_device_capacity}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        
    def check_least_vb_cnt(self, vb_cnt:VBCount) -> None:
        all_vb_cnt =    vb_cnt.slc_user_data.value + vb_cnt.slc_op.value + vb_cnt.tlc_op.value + vb_cnt.tlc_user_data.value + \
                        vb_cnt.system_table.value + vb_cnt.hidden_blk.value + vb_cnt.rev_for_gc_and_open_slc.value + \
                        vb_cnt.rev_for_gc_and_open_tlc.value + vb_cnt.max_bb_replacement_cnt.value
        
        if all_vb_cnt < least_vb_cnt_criteria_dict[self.CE]:
            logger.error(f'Expect total vb cnt >= {least_vb_cnt_criteria_dict[self.CE]}, but = {all_vb_cnt}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
    def random_scsi_test(self, enable_lun_list:list[int]) -> None:
        
        event_sequence = [i for i in range(EVENT.EVENT_CNT)]
        random.shuffle(event_sequence)
        enable_lun_list.sort()
        for event in event_sequence:
            if event == EVENT.WRITE:
                lun_idx = random.randint(0, len(enable_lun_list) - 1)
                cmd_count = 32
                min_lun = enable_lun_list[0]
                max_lun = enable_lun_list[len(enable_lun_list)-1]
                min_lba = 0
                max_lba = BLOCK4K_SIZE_128K_BYTE
                min_size = BLOCK4K_SIZE_4K_BYTE
                max_size = BLOCK4K_SIZE_128K_BYTE
                api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

            elif event == EVENT.UNMAP:
                lun_idx = random.randint(0, len(enable_lun_list) - 1)
                cmd_count = 32
                min_lun = enable_lun_list[0]
                max_lun = enable_lun_list[len(enable_lun_list)-1]
                min_lba = 0
                max_lba = BLOCK4K_SIZE_128K_BYTE
                min_size = BLOCK4K_SIZE_4K_BYTE
                max_size = BLOCK4K_SIZE_128K_BYTE
                api.random_erase(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                            write_record=self.write_record)

            elif event == EVENT.FFU:
                pass
                # hw_setting = api.HwSetting.get_instance()
                # hw_setting.update_from_device()
                # flashsettingdata = api.get_flash_setting()
                # svn = flashsettingdata.FW_SVN
                # logger.info(f"origianl svn = {svn}")
                # orign = api.api.search_ffu_bin(api.api.FFUBinType.FW_BIN, api.api.FFUSvnType.CURRENT_SVN_BIN)
                # test = api.search_ffu_bin(api.FFUBinType.FW_BIN, api.FFUSvnType.OLD_SVN_BIN)
                # hw_setting.set_to_device(api.HwSettingField.FFU_FEATURE, api.FFUFeature.FFU_SAMVE_SVN_BACKWARD_EN)
                # api.send_ffu_write_buffer(len(test), 0, test)
                # api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET)
                # ffustatus = api.read_attribute(idn=api.AttributeIDN.DEVICE_FFU_STATUS)
                # if ffustatus != api.FFUStatus.SUCCESSFUL_MICROCODE_UPDATE:
                #     raise api.SIGHTING_FFU_STATUS_UNEXPECTED
                # flashsettingdata = api.get_flash_setting()
                # svn = flashsettingdata.FW_SVN
                # logger.info(f"after ffu original -> old, svn = {svn}")

            elif event == EVENT.PURGE:
                
                api.set_flag(idn=FlagIDN.PURGE_EN)
                purge_timeout = 30 
                
                start_time = time.time()
                while True:
                    if self.check_timeout(start_time, purge_timeout):
                        raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
                    val = api.read_attribute(idn=AttributeIDN.PURGE_STATUS)
                    if val == PurgeStatus.PURGE_STS_COMPLETE_SUCCESS:
                        break
                    time.sleep(1)


            elif event == EVENT.READ_COMPARE:
                read_compare(self.write_record, api.CompareMethod.HW_COMPARE)

    def check_timeout(self,start_time: float, timeout_sec: int) -> bool:
        current_time = time.time()
        if (current_time - start_time) >= timeout_sec:
            return True
        else:
            return False
    
    def random_distribute(self,config_au:int,lun_list:list[int]) -> Dict[int,int]:
        base_au = config_au // len(lun_list)
        extra_au = config_au % len(lun_list)
        lun_au_map = {i:base_au for i in lun_list}
        for i in random.sample(lun_list, extra_au):
            lun_au_map[i] += 1
        return lun_au_map
    
    def config_lun(self, normal_ratio:int, em1_ratio:int) -> tuple[list[int], list[int]]:
        max_lun_cnt = self._param.gMaxNumberLU 
        normal_lun_count = 0
        em1_lun_count = 0
        total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        
        #get each config au
        config_normal_au = (total_au * normal_ratio) // 100
        config_em1_au = total_au - config_normal_au

        #dispatch each lun cnt
        if normal_ratio > 0 and em1_ratio > 0:
            normal_lun_count = random.randint(1, max_lun_cnt -1)
            em1_lun_count = random.randint(1, max_lun_cnt - normal_lun_count)
        elif normal_ratio > 0:
            normal_lun_count = random.randint(1, max_lun_cnt)
        else:
            em1_lun_count = random.randint(1, max_lun_cnt)
        
        #get choosen lun list
        all_luns = list(range(max_lun_cnt))
        normal_luns_list = random.sample(all_luns, normal_lun_count)
        remaining = [i for i in all_luns if i not in normal_luns_list]
        em1_luns_list = random.sample(remaining, em1_lun_count)
        
        if config_normal_au > 0:
            normal_lun_au_map = self.random_distribute(config_normal_au, normal_luns_list)
        if config_em1_au > 0:
            em1_lun_au_map = self.random_distribute(config_em1_au, em1_luns_list)
        
        config_descs = api.get_config_descriptors(print=False)
        for table in range(4):
            for unit in range(8):
                config_descs[table].header.b2_conf_desc_continue = 1
                config_descs[table].units[unit].b0_lu_enable = 0
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].l4_num_alloc_units = 0
                config_descs[table].units[unit].b9_logical_block_size = 0xc
                config_descs[table].units[unit].b10_provisioning_type = ProvisioningType.THIN_PROVISIONING_ERASE
                if (table * 8 + unit) in normal_luns_list:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b3_memory_type = MemoryType.NORMAL
                    config_descs[table].units[unit].l4_num_alloc_units = normal_lun_au_map[table * 8 + unit]
                elif (table * 8 + unit) in em1_luns_list:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b3_memory_type = MemoryType.ENHANCED_1
                    config_descs[table].units[unit].l4_num_alloc_units =em1_lun_au_map[table * 8 + unit]
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0
        config_descs[3].header.b2_conf_desc_continue = 0

        for table in range(4):
            api.push_write_config(config_descs[table], index=table)

        ExecuteCMD.send()
        ExecuteCMD.clear()
        config_descs = api.get_config_descriptors(print=True)

        #update descriptor to get new capacity
        unit_desc_idxes:List[int] = []
        for lun in range(0, self._param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            update_descriptor(DescriptorIDN.UNIT, index, cast(QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

        #test unit ready all enable lun
        for lun in range(self._param.gMaxNumberLU):
            if self._param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

        return (normal_luns_list, em1_luns_list)
    def get_hidden_blk(self, hidden_blk_boundary:int) -> int:
        if hidden_blk_boundary == 0xFFFF:
            return 0
        return hidden_blk_boundary + 1


    def get_block_boundary(self)->None:
        self.blk_info_4040 = BlockInfo()
        rsp, get_boundary_blocks= project_api.issue_4004_get_boundaryblocks_for_hiddentable_static_dynamicpool()
        dumpfile('get_boundary_blocks.bin', get_boundary_blocks.payload)
        if self.ce_num >= 1:
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce0plane0.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce0plane1.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce0plane2.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce0plane3.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce0plane4.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce0plane5.value)
        if self.ce_num >= 2:
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce1plane0.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce1plane1.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce1plane2.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce1plane3.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce1plane4.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce1plane5.value)
        if self.ce_num >= 3:
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce2plane0.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce2plane1.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce2plane2.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce2plane3.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce2plane4.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce2plane5.value)                        
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce3plane0.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce3plane1.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce3plane2.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce3plane3.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce3plane4.value)
            self.blk_info_4040.hidden_blk += self.get_hidden_blk(get_boundary_blocks.hidden_bound_ce3plane5.value)  
        logger.info(f'self.blk_info_4040.hidden_blk = {self.blk_info_4040.hidden_blk}') # >= 8 pb
        self.blk_info_4040.spare_blk = get_boundary_blocks.spare_bound_ce0plane0.value - math.ceil(self.blk_info_4040.hidden_blk / 6)
        self.blk_info_4040.ics_blk = get_boundary_blocks.ics_bound_ce0plane0.value - get_boundary_blocks.spare_bound_ce0plane0.value
        self.blk_info_4040.table_blk = get_boundary_blocks.table_bound_ce0plane0.value - get_boundary_blocks.spare_bound_ce0plane0.value
        self.blk_info_4040.slc_blk = get_boundary_blocks.slc_stop_ce0plane0.value - get_boundary_blocks.table_bound_ce0plane0.value
        self.blk_info_4040.dynamic_bounday0 = get_boundary_blocks.dynamic_bound0_ce0plane0.value - get_boundary_blocks.slc_stop_ce0plane0.value
        self.blk_info_4040.dynamic_bounday1 = get_boundary_blocks.dynamic_bound_ce0plane0.value - get_boundary_blocks.dynamic_bound0_ce0plane0.value
        logger.info(f'self.blk_info_4040.spare_blk = {self.blk_info_4040.spare_blk}') # changes
        logger.info(f'self.blk_info_4040.ics_blk = {self.blk_info_4040.ics_blk}') # >= 23 (system table)
        logger.info(f'self.blk_info_4040.table_blk = {self.blk_info_4040.table_blk}') # >= 23 (system table)
        logger.info(f'self.blk_info_4040.slc_blk = {self.blk_info_4040.slc_blk}') # SLC partition:>= 8 for 100%TLC, 212(2ce) for 50% TLC , 417 for 0% TLC
        logger.info(f'self.blk_info_4040.dynamic_bounday0 = {self.blk_info_4040.dynamic_bounday0}') # TLC partition >= 420 for 100%TLC, 216 for 50% TLC , 0 for 0% TLC
        logger.info(f'self.blk_info_4040.dynamic_bounday1 = {self.blk_info_4040.dynamic_bounday1}')
    def check_meet_block_budget_criteria(self,vb_cnt:VBCount, case:int, config_setting:str) -> None:

        if case == 0 or case == 1 or case == 4 or case == 7:
            criteria = block_budget_criteria_dict[self.CE][config_setting]
        
            logger.info(f'CE = {self.CE}, case = {case}, config setting = {config_setting}')

            if vb_cnt.system_table.value < criteria["system_table"]:
                logger.error(f'Expect system table >= {criteria["system_table"]}, but = {vb_cnt.system_table.value }')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if vb_cnt.slc_user_data.value < criteria["slc_user_data"]:
                logger.error(f'Expect slc_user_data >= {criteria["slc_user_data"]}, but = {vb_cnt.slc_user_data.value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if vb_cnt.slc_op.value < criteria["slc_op"]:
                logger.error(f'Expect slc_op >= {criteria["slc_op"]}, but = {vb_cnt.slc_op.value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if vb_cnt.rev_for_gc_and_open_slc.value < criteria["rev_blk_for_gc_open_blk_slc"]:
                logger.error(f'Expect rev_blk_for_gc_open_blk_slc >= {criteria["rev_blk_for_gc_open_blk_slc"]}, but = {vb_cnt.rev_for_gc_and_open_slc.value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if vb_cnt.tlc_user_data.value < criteria["tlc_user_data"]:
                logger.error(f'Expect tlc_user_data >= {criteria["tlc_user_data"]}, but = {vb_cnt.tlc_user_data.value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if vb_cnt.tlc_op.value < criteria["tlc_op"]:
                logger.error(f'Expect tlc_op >= {criteria["tlc_op"]}, but = {vb_cnt.tlc_op}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if vb_cnt.rev_for_gc_and_open_tlc.value < criteria["rev_blk_for_gc_open_blk_tlc"]:
                logger.error(f'Expect rev_blk_for_gc_open_blk_tlc >= {criteria["rev_blk_for_gc_open_blk_tlc"]}, but = {vb_cnt.rev_for_gc_and_open_tlc.value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if vb_cnt.hidden_blk.value < criteria["hidden_blk"]:
                logger.error(f'Expect hidden_blk >= {criteria["hidden_blk"]}, but = {vb_cnt.hidden_blk.value}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            if case == 0:
                if vb_cnt.max_bb_replacement_cnt.value < criteria["max_bb_replacement_cnt"]:
                    logger.error(f'Expect max_bb_replacement_cnt >= {criteria["max_bb_replacement_cnt"]}, but = {vb_cnt.max_bb_replacement_cnt.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            # Add for 4040
            self.get_block_boundary()
            if self.blk_info_4040.hidden_blk< criteria["hidden_blk"]:
                logger.error(f'Expect hidden_blk >= {criteria["hidden_blk"]}, but = {self.blk_info_4040.hidden_blk}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            if self.blk_info_4040.ics_blk < criteria["system_table"]:
                logger.error(f'Expect system_table >= {criteria["system_table"]}, but = {self.blk_info_4040.ics_blk}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            if self.blk_info_4040.table_blk < criteria["system_table"]:
                logger.error(f'Expect table_blk >= {criteria["table_blk"]}, but = {self.blk_info_4040.table_blk}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            slc_criteria = criteria["slc_user_data"] + criteria["slc_op"] + criteria["rev_blk_for_gc_open_blk_slc"]
            if self.blk_info_4040.slc_blk < slc_criteria:
                logger.error(f'Expect slc >= {slc_criteria}, but = {self.blk_info_4040.slc_blk}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL            
            tlc_criteria = criteria["tlc_user_data"] + criteria["tlc_op"] + criteria["rev_blk_for_gc_open_blk_tlc"]
            # if case != 7: # fw bug , due to slc = 481 , (dynamic_bound0 - slc ) will over flow
            if case == 7 :
                if self.blk_info_4040.dynamic_bounday0 != 0:
                    logger.error_lb(f'case = {config_setting}')
                    logger.error_fp(f'Expect dynamic_bound0_ce0plane0 - blocks.slc_stop_ce0plane0 = 0, but = {self.blk_info_4040.dynamic_bounday0}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL  
            else:
                if self.blk_info_4040.dynamic_bounday0 < tlc_criteria:
                    logger.error(f'Expect dynamic_bounday0 >= {tlc_criteria}, but = {self.blk_info_4040.dynamic_bounday0}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL        
            if self.blk_info_4040.dynamic_bounday1 < criteria["max_bb_replacement_cnt"]:
                logger.error(f'Expect dynamic_bounday1 >= {criteria["max_bb_replacement_cnt"]}, but = {self.blk_info_4040.dynamic_bounday1}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL                

        logger.info(f'system block = {vb_cnt.system_table.value}')
        logger.info(f'slc user data = {vb_cnt.slc_user_data.value}')
        logger.info(f'slc op = {vb_cnt.slc_op.value}')
        logger.info(f'reserved blk for gc + fw open blk handler = {vb_cnt.rev_for_gc_and_open_slc.value}')
        logger.info(f'tlc user data = {vb_cnt.tlc_user_data.value}')
        logger.info(f'tlc op = {vb_cnt.tlc_op.value}')
        logger.info(f'Reserved blk for gc + fw open block hanlder = {vb_cnt.rev_for_gc_and_open_tlc.value}')
        logger.info(f'hidden blk = {vb_cnt.hidden_blk.value}')
        logger.info(f'max bb replacement count = {vb_cnt.max_bb_replacement_cnt.value}')
        
    def get_all_vb_cnt(self) -> VBCount:
        offset = 2560
        rsp_data = api.get_block_read_count_table()
        return VBCount(rsp_data[offset:offset+36])

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()