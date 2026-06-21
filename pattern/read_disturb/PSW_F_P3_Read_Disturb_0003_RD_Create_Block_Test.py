import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.read_disturb.mutual_fun import *
from Script.project_api.functions import print_object_info_ai

class Pattern(UFSTC):
    def pre_process(self) -> None:
        leave_inhibition_mode()
        self.fw_geometry = api.get_fw_geometry()
        self.write_record = api.get_empty_write_record()
        _, self.debug_info = api.get_debug_info()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.TestDummyLun2 = 2
        self.TestDummyLun3= 3
        self.TestDummyLun4 = 4
        config_lun(normal_list=[self.TestNormalLun, self.TestDummyLun2, self.TestDummyLun3, self.TestDummyLun4], em1_list=[self.TestEM1Lun])
        self.startLBA: Dict[int, int] = {self.TestNormalLun: 0, self.TestEM1Lun:0}
        _, self.mConfig_in_vu = project_api.get_mConfig_data()
        _, self.erase_cnt_buffer_backup = api.read_Xmemory(sram_address=self.debug_info.VB_list_cycle_address.value)
        project_api.set_Enable_Disable_Read_Scan(enable=0)
        pass

    def step1(self) -> None:
        last_XLC_EC_group:Dict[bool, int] = {False:0, True:0}
        for group in range(0, 4+1):
            for lun in self.startLBA:
                is_SLC = lun == self.TestEM1Lun
                vb_size = self.slc_vb_size if is_SLC else self.tlc_vb_size
                XLC = "SLC" if is_SLC else "TLC"
                EC_field = f"{XLC}_EC_{group}"
                logger.info(f"============ Test {XLC} EC <= {EC_field} ============")
                logger.flow(1, f"get VB list")
                sorted_VB_list_dict = get_sorted_VB_list()
                
                XLC_EC_group = get_mConfig_value(mConfig=self.mConfig_in_vu, field_name=EC_field) * 100
                if group == 4:
                    set_value = last_XLC_EC_group[is_SLC] + 1
                else:
                    set_value = XLC_EC_group-1
                    
                free_group = project_api.VBListNum.FREE_BLK_QUEUE_EM1 if is_SLC else project_api.VBListNum.FREE_BLK_QUEUE_TLC
                L2_group = project_api.VBListNum.CURRENT_L2_EM1 if is_SLC else project_api.VBListNum.CURRENT_L2_TLC
                logger.flow(2, f"set EC of all {free_group.name} VB to {set_value} (<= {EC_field})")
                set_vb_list = sorted_VB_list_dict.get(free_group, [])
                self.set_vb_erase_cnt_by_list(vb_list=set_vb_list, set_value=set_value)
                
                logger.flow(3, f"issue VU C087 to refresh all {L2_group.name}")
                refresh_vb_list = sorted_VB_list_dict.get(L2_group, [])
                if refresh_vb_list:
                    project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=refresh_vb_list, booking_user=project_api.VUC087Paremeter.LowPriority)
                polling_bkops_idle()
                
                logger.flow(4, f"write data to create VB")
                total_size = int(vb_size*1.5)
                api.sequential_write(lun=lun, start_lba=self.startLBA[lun], total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                                need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                _, closed_pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=self.startLBA[lun])
                _, open_pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=self.startLBA[lun] + total_size-1)
                self.startLBA[lun] += total_size
                ftl_vb_list_data = get_VB_group(show=False)
                
                logger.flow(5, f"get RC and RC_TH of VB and check cretiria")
                erase_cnt_of_vb, erase_cnt_for_hidden_physical_block, _ = project_api.get_all_VB_erase_count()
                read_cnt_of_vb = project_api.get_all_VB_read_count()
                _, rc_threshold_of_vb = project_api.issue_40CA_to_get_get_Read_Count_threshold_table()
                
                for pca in [closed_pca, open_pca]:
                    vb = pca.virtual_block_number.value
                    vb_group = project_api.VB_GROUP(ftl_vb_list_data[vb]['group'])
                    FP = "P" if pca==open_pca else "F"
                    RC = read_cnt_of_vb[vb]
                    RC_TH = rc_threshold_of_vb[vb]
                    expect_field = f"{XLC}_EC_RC_TH_{FP}B{group}"
                    EC_RC_TH = get_mConfig_value(mConfig=self.mConfig_in_vu, field_name=expect_field) * 1000
                    logger.info(f"VB {vb} ({vb_group.name}): RC = {read_cnt_of_vb[vb]}, RC_TH = {rc_threshold_of_vb[vb]}, EC = {erase_cnt_of_vb[vb]}, {EC_field} = {XLC_EC_group}, {expect_field} = {EC_RC_TH}")
                    logger.info(f"check RC = 0 and RC_TH = {EC_RC_TH} ({expect_field})")
                    if RC != 0:
                        logger.error_lb(f'check RC of vb {vb} after creation')
                        logger.error_fp(f'expect RC[{vb}] is 0,  but current value = {RC}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    if RC_TH != EC_RC_TH:
                        logger.error_lb(f'check RC_TH of vb {vb} after creation, EC[{vb}] = {erase_cnt_of_vb[vb]} <= {XLC_EC_group} ({EC_field})')
                        logger.error_fp(f'expect RC_TH[{vb}] is {EC_RC_TH} ({expect_field}), but current value = {RC_TH}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    pass
                    if is_SLC:
                        wBlockType = project_api.EC_RC_BlockType.SLC_OPEN if pca==open_pca else project_api.EC_RC_BlockType.SLC_CLOSE
                    else:
                        wBlockType = project_api.EC_RC_BlockType.TLC_OPEN if pca==open_pca else project_api.EC_RC_BlockType.TLC_CLOSE
                    logger.info(f"check 408C value")
                    
                    logger.flow(6, f"get EC_RC_TH of wBlockType and check cretiria")
                    _, ReadThresholdSet = project_api.issue_408C_to_get_EC_RC_threshold_table(wBlockType=wBlockType)
                    if len(ReadThresholdSet) != 5:
                        logger.error_lb(f'check ReadThresholdSet of {wBlockType.name}')
                        logger.error_fp(f'expect Number of Read Threshold sets is 5, but current value = {len(ReadThresholdSet)}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    if ReadThresholdSet[group].EraseCountThreshold.value != XLC_EC_group:
                        logger.error_lb(f'check ReadThresholdSet.EraseCountThreshold[{group}] of {wBlockType.name}')
                        logger.error_fp(f'expect EraseCountThreshold[{group}] of {wBlockType.name} is {XLC_EC_group}, but current value = {ReadThresholdSet[group].EraseCountThreshold.value}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    if ReadThresholdSet[group].ReadCountThreshold.value != EC_RC_TH:
                        logger.error_lb(f'check ReadThresholdSet.ReadCountThreshold[{group}] of {wBlockType.name}')
                        logger.error_fp(f'expect ReadCountThreshold[{group}] of {wBlockType.name} is {EC_RC_TH}, but current value = {ReadThresholdSet[group].ReadCountThreshold.value}, result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                logger.flow(7, 'POR and polling bkops idle')
                api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
                polling_bkops_idle()
                last_XLC_EC_group[is_SLC] = XLC_EC_group
                project_api.set_Enable_Disable_Read_Scan(enable=0)
        pass

    def post_process(self) -> None:
        project_api.set_all_VB_erase_count(data_payload=self.erase_cnt_buffer_backup, set_in_ram=False)
        pass
    
    def set_vb_erase_cnt_by_list(self, vb_list:List[int], set_value:int) -> None:
        erase_cnt_of_vb, erase_cnt_for_hidden_physical_block, _ = project_api.get_all_VB_erase_count()
        set_erase_cnt_payload = bytearray(api.DATA_SIZE_4K_BYTE)
        for vb in range(self.fw_geometry.l52_total_vb_count):
            if vb in vb_list:
                temp_set_value = set_value
            else:
                temp_set_value = erase_cnt_of_vb[vb]
            set_erase_cnt_payload[vb * 4 : (vb+1)*4] = (temp_set_value).to_bytes(4, 'little')
        project_api.set_all_VB_erase_count(data_payload=set_erase_cnt_payload, set_in_ram=True)
    
    

run = Pattern().run
if __name__ == "__main__":
    run()