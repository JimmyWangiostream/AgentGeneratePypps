import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.wear_leveling.mutual_fun import *
from Script.project_api.functions import print_object_info_ai
from typing import Any

class ConfigCase(IntEnum):
    EM1_larger_than_30 = 0
    EM1_less_than_30 = 1

class Pattern(UFSTC):
    def pre_process(self) -> None:
        leave_inhibition_mode()
        self.slc_lun, self.tlc_lun = config_lun()
        self.fw_geometry = api.get_fw_geometry()
        self.write_record = api.get_empty_write_record()
        _, self.debug_info = api.get_debug_info()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        _, self.erase_cnt_buffer_backup = api.read_Xmemory(sram_address=self.debug_info.VB_list_cycle_address.value)
        pass
    
    def step1(self) -> None:
        logger.info(f"============ Test TLC ===============")
        select_idx = 5
        logger.flow(1, f"issue 4098 to get WL information as before")
        _, self.wear_leveling_A = project_api.issue_4098_to_get_wear_leveling_information()
        free_MLC:List[int] = []
        logger.flow(2, f"issue 406D to get sorted VB list")
        sorted_vb_dict = get_sorted_VB_list()
        free_MLC = sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_TLC].copy()
        
        logger.flow(3, f"issue C083 to set Free Blk EC")
        set_erase_cnt_payload = bytearray(api.DATA_SIZE_4K_BYTE)
        for idx,vb in enumerate(free_MLC):
            if idx < select_idx:
                set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (666).to_bytes(4, 'little')
            else:
                set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (0).to_bytes(4, 'little')
        project_api.set_all_VB_erase_count(data_payload=set_erase_cnt_payload, set_in_ram=True)
        
        logger.flow(4, f"write data to create TLC L2")
        total_size = int(self.tlc_vb_size*1.5)
        chunksize = api.BLOCK4K_SIZE_128M_BYTE
        lba = 0
        api.sequential_write(lun=self.tlc_lun, start_lba=lba, total_size=total_size, chunk_size=chunksize, fua = 0,
                    need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
        _, open_vb_info = api.get_open_vb_info()
        vb = open_vb_info.TLC_L2.logical_vb.value
        
        logger.flow(5, f"issue 4098 to get WL information and check VB selection is correct")
        _, self.wear_leveling_B = project_api.issue_4098_to_get_wear_leveling_information()
        EC_data_before = self.wear_leveling_A.EC_data_of_VBs[vb]
        EC_data_after = self.wear_leveling_B.EC_data_of_VBs[vb]
        logger.info(f'Before: VB: {vb}, EC = {EC_data_before.EC.value} VBListNum = {EC_data_before.VBListNum.value} ({project_api.VBListNum(EC_data_before.VBListNum.value).name}), OpenType = {EC_data_before.OpenVBType.value} ({project_api.OpenVBType(EC_data_before.OpenVBType.value).name})')
        logger.info(f'After:  VB: {vb}, EC = {EC_data_after.EC.value} VBListNum = {EC_data_after.VBListNum.value} ({project_api.VBListNum(EC_data_after.VBListNum.value).name}), OpenType = {EC_data_after.OpenVBType.value} ({project_api.OpenVBType(EC_data_after.OpenVBType.value).name})')
        if EC_data_before.VBListNum.value != project_api.VBListNum.FREE_BLK_QUEUE_TLC:
            logger.error_lb(f'check VBListNum before create TLC')
            logger.error_fp(f'expect VBListNum is FREE_BLK_QUEUE_TLC, but current value = {EC_data_before.VBListNum.value} ({project_api.VBListNum(EC_data_before.VBListNum.value).name}), result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if EC_data_after.VBListNum.value != project_api.VBListNum.CURRENT_L2_TLC:
            logger.error_lb(f'check VBListNum after create TLC')
            logger.error_fp(f'expect VBListNum is CURRENT_L2_TLC, but current value = {EC_data_after.VBListNum.value} ({project_api.VBListNum(EC_data_after.VBListNum.value).name}), result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if vb != free_MLC[select_idx]:
            logger.error_lb(f'check VB num after create TLC')
            logger.error_fp(f'expect VB is the first EC < threshold VB before, expect idx = {select_idx}, but current index = {free_MLC.index(vb)} , result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(6, f"write data to closed VB")
        total_size = self.tlc_vb_size
        chunksize = api.BLOCK4K_SIZE_128M_BYTE
        lba = 0
        api.sequential_write(lun=self.tlc_lun, start_lba=lba, total_size=total_size, chunk_size=chunksize, fua = 0,
                    need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
        lba += total_size
        pca = lba_to_pba(lun=self.tlc_lun, lba=0)
        vb = pca.w10_block.value
        
        logger.flow(7, f"issue 4098 to get WL information and check VB move to USED pool")
        _, wear_leveling = project_api.issue_4098_to_get_wear_leveling_information()
        EC_data = wear_leveling.EC_data_of_VBs[vb]
        logger.info(f'VB: {vb}, EC = {EC_data.EC.value} VBListNum = {EC_data.VBListNum.value} ({project_api.VBListNum(EC_data.VBListNum.value).name}), OpenType = {EC_data.OpenVBType.value} ({project_api.OpenVBType(EC_data.OpenVBType.value).name})')
        if EC_data.VBListNum.value != project_api.VBListNum.USED_BLK_POOL_TLC:
            logger.error_lb(f'check VBListNum after create TLC')
            logger.error_fp(f'expect VBListNum is USED_BLK_POOL_TLC, but current value = {EC_data.VBListNum.value} ({project_api.VBListNum(EC_data.VBListNum.value).name}), result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def step2(self) -> None:
        logger.info(f"============ Test PTE/L1 ===============")
        for testcase in ConfigCase:
            logger.flow(7, f"config lun {testcase.name}")
            if testcase == ConfigCase.EM1_less_than_30:
                self.slc_lun, self.tlc_lun = config_lun(SLC_Ratio=0.25)
            else:
                self.slc_lun, self.tlc_lun = config_lun(SLC_Ratio=0.5)
            _, self.wear_leveling_B = project_api.issue_4098_to_get_wear_leveling_information()
            
            logger.flow(8, f"issue 406D to get sorted VB list")
            sorted_vb_dict = get_sorted_VB_list()
            free_PTE = sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_TABLE].copy()
            free_MLC = sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_TLC].copy()
            free_SLC = sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_EM1].copy()
            
            logger.flow(9, f"issue C083 to set Free Blk EC")
            temp_select_idx = [5, 6]
            set_erase_cnt_payload = bytearray(api.DATA_SIZE_4K_BYTE)
            for vb in range(self.fw_geometry.l52_total_vb_count):
                randvalue = random.randint(100, 500)
                set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (randvalue).to_bytes(4, 'little')
            for idx,vb in enumerate(free_PTE):
                if idx > self.wear_leveling_A.Search_selection_range_length_of_ICS_pool.value:
                    set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (0).to_bytes(4, 'little')
                elif idx in temp_select_idx:
                    set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (10).to_bytes(4, 'little')
            for idx,vb in enumerate(free_MLC):
                if idx > self.wear_leveling_A.Search_selection_range_length_of_dynamic_pool.value:
                    set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (0).to_bytes(4, 'little')
                elif idx in temp_select_idx:
                    set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (10).to_bytes(4, 'little')
            for idx,vb in enumerate(free_SLC):
                if idx > self.wear_leveling_A.Search_selection_range_length_of_static_pool.value:
                    set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (0).to_bytes(4, 'little')
                elif idx in temp_select_idx:
                    set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (10).to_bytes(4, 'little')
            project_api.set_all_VB_erase_count(data_payload=set_erase_cnt_payload, set_in_ram=True)
            
            logger.flow(10, f"issue C087 to closed L1")
            if project_api.VBListNum.PTE_POOL in sorted_vb_dict:
                vb_list = [vb for vb in sorted_vb_dict[project_api.VBListNum.PTE_POOL]]
                project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.TableVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.MediumPriority)
            if project_api.VBListNum.CURRENT_L1 in sorted_vb_dict:
                vb_list = [vb for vb in sorted_vb_dict[project_api.VBListNum.CURRENT_L1]]
                project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.MediumPriority)
            polling_bkops_idle()
            
            
            _, wear_leveling = project_api.issue_4098_to_get_wear_leveling_information()
            EC_record:Dict[int, List[int]] = {}
            PEC_AVG_partition:Dict[int, int] = {}
            ftl_vb_list = get_VB_group()
            for vb, info in ftl_vb_list.items():
                vu_EC = wear_leveling.EC_data_of_VBs[vb].EC.value
                group = project_api.VB_GROUP(info['group'])
                partition = info['partition']
                if vu_EC == 0xFFFFF:
                    continue
                if partition not in EC_record:
                    EC_record[partition] = []
                EC_record[partition].append(vu_EC)
            for partition, ec_list in EC_record.items():
                max_value = max(ec_list)
                avg_value = sum(ec_list)//len(ec_list)
                min_value = min(ec_list)
                exhausted_life = avg_value * 100 // (3000 if partition == 2 else 100000)
                logger.info(f"partition:{partition}, max = {max_value}, avg = {avg_value}, min = {min_value}, exhausted_life = {exhausted_life}")
                PEC_AVG_partition[partition] = avg_value
            
            logger.flow(11, f"write data to create PTE/L1")
            api.sequential_write(lun=self.tlc_lun, start_lba=0, total_size=api.BLOCK4K_SIZE_16K_BYTE, chunk_size=api.BLOCK4K_SIZE_16K_BYTE, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
            api.sequential_write(lun=self.slc_lun, start_lba=0, total_size=api.BLOCK4K_SIZE_16K_BYTE, chunk_size=api.BLOCK4K_SIZE_16K_BYTE, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
            _, open_vb_info = api.get_open_vb_info()
            pte_vb = open_vb_info.PTE.logical_vb.value
            L1_vb = open_vb_info.TLC_L1.logical_vb.value
            
            
            logger.flow(12, f"issue 4098 to get WL information and check VB selection is correct")
            _, self.wear_leveling_C = project_api.issue_4098_to_get_wear_leveling_information()
            for vb in [pte_vb, L1_vb]:
                if testcase == ConfigCase.EM1_less_than_30:
                    expect_pool = project_api.VBListNum.FREE_BLK_QUEUE_TABLE if vb == pte_vb else project_api.VBListNum.FREE_BLK_QUEUE_TLC
                else:
                    if vb == pte_vb and PEC_AVG_partition[1]>PEC_AVG_partition[0]*1.1:
                        expect_pool = project_api.VBListNum.FREE_BLK_QUEUE_TABLE
                    elif vb != pte_vb and PEC_AVG_partition[1]>PEC_AVG_partition[2]*1.1:
                        expect_pool = project_api.VBListNum.FREE_BLK_QUEUE_TLC
                    else:
                        expect_pool = project_api.VBListNum.FREE_BLK_QUEUE_EM1

                EC_data_before = self.wear_leveling_B.EC_data_of_VBs[vb]
                EC_data_after = self.wear_leveling_C.EC_data_of_VBs[vb]
                logger.info(f'Before: VB: {vb}, EC = {EC_data_before.EC.value} VBListNum = {EC_data_before.VBListNum.value} ({project_api.VBListNum(EC_data_before.VBListNum.value).name}), OpenType = {EC_data_before.OpenVBType.value} ({project_api.OpenVBType(EC_data_before.OpenVBType.value).name})')
                logger.info(f'After:  VB: {vb}, EC = {EC_data_after.EC.value} VBListNum = {EC_data_after.VBListNum.value} ({project_api.VBListNum(EC_data_after.VBListNum.value).name}), OpenType = {EC_data_after.OpenVBType.value} ({project_api.OpenVBType(EC_data_after.OpenVBType.value).name})')
                logger.info(f'==================================')
                if EC_data_before.VBListNum.value != expect_pool:
                    logger.error_lb(f'check VBListNum before create VB')
                    logger.error_fp(f'expect VBListNum is {expect_pool.name}, but current value = {EC_data_before.VBListNum.value} ({project_api.VBListNum(EC_data_before.VBListNum.value).name}), result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                expect_vb = [sorted_vb_dict[expect_pool][idx] for idx in temp_select_idx]
                if vb not in expect_vb:
                    logger.error_lb(f'check VB num after create VB')
                    logger.error_fp(f'expect VB is the smallest EC VB before, expect VB = {expect_vb}, but current VB = {vb} , result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            pass
        pass
        
    def step3(self) -> None:
        logger.info(f"============ Test SLC ===============")
        select_idx = 5
        _, self.wear_leveling_A = project_api.issue_4098_to_get_wear_leveling_information()
        free_SLC:List[int] = []
        
        logger.flow(13, f"issue 406D to get sorted VB list")
        sorted_vb_dict = get_sorted_VB_list()
        free_SLC = sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_EM1].copy()

        logger.flow(14, f"issue C083 to set Free Blk EC")
        set_erase_cnt_payload = bytearray(api.DATA_SIZE_4K_BYTE)
        for idx,vb in enumerate(free_SLC):
            if idx > self.wear_leveling_A.Search_selection_range_length_of_static_pool.value:
                set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (0).to_bytes(4, 'little')
            elif idx == select_idx:
                set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (10).to_bytes(4, 'little')
            else:
                set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (666).to_bytes(4, 'little')
        project_api.set_all_VB_erase_count(data_payload=set_erase_cnt_payload, set_in_ram=True)
        total_size = int(self.slc_vb_size*1.5)
        chunksize = api.BLOCK4K_SIZE_128M_BYTE
        lba = 0
        
        logger.flow(15, f"write data to create SLC L2")
        api.sequential_write(lun=self.slc_lun, start_lba=lba, total_size=total_size, chunk_size=chunksize, fua = 0,
                    need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
        _, open_vb_info = api.get_open_vb_info()
        vb = open_vb_info.SLC_L2.logical_vb.value
        
        logger.flow(16, f"issue 4098 to get WL information and check VB selection is correct")
        _, self.wear_leveling_B = project_api.issue_4098_to_get_wear_leveling_information()
        EC_data_before = self.wear_leveling_A.EC_data_of_VBs[vb]
        EC_data_after = self.wear_leveling_B.EC_data_of_VBs[vb]
        logger.info(f'Before: VB: {vb}, EC = {EC_data_before.EC.value} VBListNum = {EC_data_before.VBListNum.value} ({project_api.VBListNum(EC_data_before.VBListNum.value).name}), OpenType = {EC_data_before.OpenVBType.value} ({project_api.OpenVBType(EC_data_before.OpenVBType.value).name})')
        logger.info(f'After:  VB: {vb}, EC = {EC_data_after.EC.value} VBListNum = {EC_data_after.VBListNum.value} ({project_api.VBListNum(EC_data_after.VBListNum.value).name}), OpenType = {EC_data_after.OpenVBType.value} ({project_api.OpenVBType(EC_data_after.OpenVBType.value).name})')
        if EC_data_before.VBListNum.value != project_api.VBListNum.FREE_BLK_QUEUE_EM1:
            logger.error_lb(f'check VBListNum before create SLC')
            logger.error_fp(f'expect VBListNum is FREE_BLK_QUEUE_EM1, but current value = {EC_data_before.VBListNum.value} ({project_api.VBListNum(EC_data_before.VBListNum.value).name}), result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if EC_data_after.VBListNum.value != project_api.VBListNum.CURRENT_L2_EM1:
            logger.error_lb(f'check VBListNum after create SLC')
            logger.error_fp(f'expect VBListNum is CURRENT_L2_EM1, but current value = {EC_data_after.VBListNum.value} ({project_api.VBListNum(EC_data_after.VBListNum.value).name}), result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if vb != free_SLC[select_idx]:
            logger.error_lb(f'check VB num after create SLC')
            logger.error_fp(f'expect VB is the smallest EC in Search_selection_range, expect idx = {select_idx}, but current index = {free_SLC.index(vb)} , result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(17, f"write data to closed VB")
        total_size = self.slc_vb_size
        chunksize = api.BLOCK4K_SIZE_128M_BYTE
        lba = 0
        api.sequential_write(lun=self.slc_lun, start_lba=lba, total_size=total_size, chunk_size=chunksize, fua = 0,
                    need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
        lba += total_size
        pca = lba_to_pba(lun=self.slc_lun, lba=0)
        vb = pca.w10_block.value
        
        logger.flow(18, f"issue 4098 to get WL information and check VB move to USED pool")
        _, wear_leveling = project_api.issue_4098_to_get_wear_leveling_information()
        EC_data = wear_leveling.EC_data_of_VBs[vb]
        logger.info(f'VB: {vb}, EC = {EC_data.EC.value} VBListNum = {EC_data.VBListNum.value} ({project_api.VBListNum(EC_data.VBListNum.value).name}), OpenType = {EC_data.OpenVBType.value} ({project_api.OpenVBType(EC_data.OpenVBType.value).name})')
        if EC_data.VBListNum.value != project_api.VBListNum.USED_BLK_POOL_EM1:
            logger.error_lb(f'check VBListNum after create SLC')
            logger.error_fp(f'expect VBListNum is USED_BLK_POOL_EM1, but current value = {EC_data.VBListNum.value} ({project_api.VBListNum(EC_data.VBListNum.value).name}), result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    
    def post_process(self) -> None:
        project_api.set_all_VB_erase_count(data_payload=self.erase_cnt_buffer_backup, set_in_ram=False)
        pass
    


run = Pattern().run
if __name__ == "__main__":
    run()