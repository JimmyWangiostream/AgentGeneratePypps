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

class TestCase(IntEnum):
    ReadCnt_100K = 0
    SSU_Sleep = 1

NUM_100K = 100000

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
        self.TestWBLun = 2
        config_lun(normal_list=[self.TestNormalLun, self.TestWBLun], em1_list=[self.TestEM1Lun])
        _, self.mConfig_in_vu = project_api.get_mConfig_data()
        self.lun_lba_vb:List[tuple[int,int,int]] = []
        pass

    def step1(self) -> None:
        logger.flow(1, f"write data to create TLC/SLC block")
        total_size = int(self.tlc_vb_size*4.5)
        lun = self.TestNormalLun
        api.sequential_write(lun=lun, start_lba=0, total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        for lba in range(0,total_size, self.tlc_vb_size):
            pca = get_PCA_and_print(lun=lun, lba=lba)
            vb = pca.virtual_block_number.value
            self.lun_lba_vb.append((lun, lba, vb))
        total_size = int(self.slc_vb_size*4.5)
        lun = self.TestEM1Lun
        api.sequential_write(lun=lun, start_lba=0, total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        for lba in range(0,total_size, self.slc_vb_size):
            pca = get_PCA_and_print(lun=lun, lba=lba)
            vb = pca.virtual_block_number.value
            self.lun_lba_vb.append((lun, lba, vb))
        pass
    
    def step2(self) -> None:
        for testcase in TestCase:
            logger.info(f"======== TestCase: {testcase.name} ========")
            logger.flow(2, 'Set RC and RC_TH to random value')
            read_cnt_of_vb_before = project_api.get_all_VB_read_count()
            vb_dict:Dict[int, Dict[str,int]] = {}
            data_payload = bytearray(4096)
            for vb in range(self.fw_geometry.l52_total_vb_count):
                data_payload[vb*4:(vb+1)*4] = read_cnt_of_vb_before[vb].to_bytes(4, 'little')
            for lun, lba, vb in self.lun_lba_vb:
                temp_RC = random.randint(1, 0xFFF00000)
                temp_RC_TH = random.randint(0xFFFF0000,0xFFFFFFF0)
                set_RC_TH_value = temp_RC_TH
                set_RC_value = temp_RC
                project_api.set_specific_VB_read_count_threshold(VB_Num=vb, RC_TH_Value=set_RC_TH_value)
                data_payload[vb*4:(vb+1)*4] = (set_RC_value).to_bytes(4, 'little')
                vb_dict[vb] = {
                    "RC_TH" : set_RC_TH_value,
                    "RC" : set_RC_value
                }
            project_api.set_all_VB_read_count(data_payload=data_payload)
                
            logger.flow(3, 'POR')
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
            
            logger.flow(4, 'get RC and RC_TH and check if the value matches the setting value')
            self.check_RC_and_TH(vb_dict=vb_dict)
                
            logger.flow(5, f"Reading data leads to an increase in RC.")
            for lun, lba, vb in self.lun_lba_vb:
                times = random.randint(10,100)
                logger.info(f"read LUN = {lun}, LBA = {lba},  {times} times")
                read_LBA_repeatedly(lun=lun, lba = lba, read_times=times)
                vb_dict[vb]["RC"] += times
            if testcase == TestCase.SSU_Sleep:
                logger.flow(6, f'SSU Sleep and awake')
                ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
                ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
                ExecuteCMD.send(QD=1,clear_on_success=True)
            else:
                logger.flow(6, f'issue C071 to set sgs_scan_dynamic_read_count / sgs_scan_static_read_count to Multiples of 100K')
                param = project_api.C071_param()
                param.sgs_scan_dynamic_read_count.value = random.randint(1,30000) * NUM_100K
                param.sgs_scan_static_read_count.value = random.randint(1,30000) * NUM_100K            
                project_api.issue_C071_to_set_SGD_scan_parameters(param, isSGS=1)

            logger.flow(7, 'polling bkops idle')
            polling_bkops_idle()
            
            logger.flow(8, 'SPOR')
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
            
            logger.flow(9, 'get RC and RC_TH and check if the value matches the value after read')
            self.check_RC_and_TH(vb_dict=vb_dict)
            pass
    
    def check_RC_and_TH(self, vb_dict:Dict[int, Dict[str,int]]) -> None:
        buffer = 2
        ftl_vb_list_data = get_VB_group(show=False)
        read_cnt_of_vb_after = project_api.get_all_VB_read_count()
        _, rc_threshold_of_vb_after = project_api.issue_40CA_to_get_get_Read_Count_threshold_table()
        for vb, info in vb_dict.items():
            vb_group = project_api.VB_GROUP(ftl_vb_list_data[vb]['group'])
            RC_TH = info["RC_TH"]
            RC = info["RC"]
            if abs(read_cnt_of_vb_after[vb] - RC) > buffer :
                logger.error_lb(f'check Read Count of VB {vb} ({vb_group.name})')
                logger.error_fp(f'expect Read Count of VB {vb} ({vb_group.name}) is {RC}, but current value = {read_cnt_of_vb_after[vb]}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                vb_dict[vb]["RC"] = read_cnt_of_vb_after[vb]
            if RC_TH != rc_threshold_of_vb_after[vb]:
                logger.error_lb(f'check Read Count Threshold of VB {vb} ({vb_group.name})')
                logger.error_fp(f'expect Read Count Threshold of VB {vb} ({vb_group.name}) is {RC_TH}, but current value = {rc_threshold_of_vb_after[vb]}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def post_process(self) -> None:
        pass
    
    

run = Pattern().run
if __name__ == "__main__":
    run()