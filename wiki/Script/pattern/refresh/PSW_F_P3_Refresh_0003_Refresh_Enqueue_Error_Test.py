import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from typing import List
from Script.pattern.refresh.mutual_fun import *
from Script.project_api.functions import print_object_info_ai

DEBUG = True
class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.fw_geometry = api.get_fw_geometry()
        self.write_record = api.get_empty_write_record()
        _, self.debug_info = api.get_debug_info()
        self.slc_lun, self.tlc_lun = config_lun()
        
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        vb_cnt = 15
        total_size = int(self.tlc_vb_size * vb_cnt)
        chunksize = api.BLOCK4K_SIZE_128M_BYTE
        api.sequential_write(lun=self.tlc_lun, start_lba=0, total_size=total_size, chunk_size=chunksize, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
        self.sorted_vb_dict = get_sorted_VB_list()
        pass

    def step1(self) -> None:
        vb_in_Q_limit = 10
        logger.flow(1, "issue C088 with 0x00:stop refresh execution, but refresh can still be enqueued")
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.EnableEnqueueInRefreshBQ)
        
        logger.flow(2, "issue C087 to enqueue HP/MP/LP refresh, Case: push HostVB but VB_type = TableVB")
        PriorityDict = get_HP_MP_LP_list(self.sorted_vb_dict[project_api.VBListNum.USED_BLK_POOL_TLC], max_cnt=5)
        for Priority, vb_list in PriorityDict.items():
            logger.info(f"push VB {vb_list} as {Priority.name}")
            self.enqueu_error_case(VB_type=project_api.VUC087VB_type.TableVB, VB_list=vb_list, booking_user=Priority)
        
        logger.flow(3, "issue C087 to enqueue HP/MP/LP refresh, Case: push TableVB but VB_type = HostVB")
        PriorityDict = get_HP_MP_LP_list(self.sorted_vb_dict[project_api.VBListNum.LIST_BLK])
        for Priority, vb_list in PriorityDict.items():
            logger.info(f"push VB {vb_list} as {Priority.name}")
            self.enqueu_error_case(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=Priority)
            
        logger.flow(4, "issue C087 to enqueue HP/MP/LP refresh, Case: push FREE_BLK but VB_type = HostVB")
        PriorityDict = get_HP_MP_LP_list(self.sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_EM1])
        for Priority, vb_list in PriorityDict.items():
            logger.info(f"push VB {vb_list} as {Priority.name}")
            self.enqueu_error_case(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=Priority)
        
        logger.flow(5, "issue C087 to enqueue HP/MP/LP refresh, Case: push FREE_BLK but VB_type = TableVB")
        PriorityDict = get_HP_MP_LP_list(self.sorted_vb_dict[project_api.VBListNum.FREE_BLK_QUEUE_TLC])
        for Priority, vb_list in PriorityDict.items():
            logger.info(f"push VB {vb_list} as {Priority.name}")
            self.enqueu_error_case(VB_type=project_api.VUC087VB_type.TableVB, VB_list=vb_list, booking_user=Priority)
        
        logger.flow(6, f"issue C087 to enqueue HP/MP/LP refresh, Case: push VB exceed {vb_in_Q_limit} in one cmd")
        vb_list = [vb for vb in self.sorted_vb_dict[project_api.VBListNum.USED_BLK_POOL_TLC][:vb_in_Q_limit+1]]
        logger.info(f"push VB {vb_list} as HighPriority")
        self.enqueu_error_case(VB_type=project_api.VUC087VB_type.TableVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.HighPriority)
        
        logger.flow(7, f"issue C087 to enqueue HP/MP/LP refresh, Case: push VB exceed {vb_in_Q_limit} in two cmds")
        vb_list = [vb for vb in self.sorted_vb_dict[project_api.VBListNum.USED_BLK_POOL_TLC][:vb_in_Q_limit]]
        logger.info(f"push VB {vb_list} as HighPriority")
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.HighPriority)
        vb_list = self.sorted_vb_dict[project_api.VBListNum.USED_BLK_POOL_TLC][vb_in_Q_limit:vb_in_Q_limit+1]
        logger.info(f"push VB {vb_list} as HighPriority")
        self.enqueu_error_case(VB_type=project_api.VUC087VB_type.TableVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.HighPriority)
        
        logger.flow(8, f"issue C087 to enqueue HP/MP/LP refresh, Case: push VB exceed {vb_in_Q_limit} in multi cmds")
        PriorityDict = get_HP_MP_LP_list(self.sorted_vb_dict[project_api.VBListNum.USED_BLK_POOL_TLC], max_cnt=vb_in_Q_limit+1)
        for Priority, vb_list in PriorityDict.items():
            logger.info(f"push VB {vb_list} as {Priority.name}")
            self.enqueu_error_case(VB_type=project_api.VUC087VB_type.TableVB, VB_list=vb_list, booking_user=Priority)
            
        logger.flow(9, "issue C087 to enqueue HP/MP/LP refresh, Case: push non-exist VB")
        vb_list = [0xFFFF]
        logger.info(f"push VB {vb_list} as HighPriority")
        self.enqueu_error_case(VB_type=project_api.VUC087VB_type.TableVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.HighPriority)
    
    def post_process(self) -> None:
        pass
    
    def enqueu_error_case(self, VB_type:project_api.VUC087VB_type, VB_list:List[int], booking_user:int) -> None:
        response = project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=VB_type, VB_list=VB_list, booking_user=booking_user, keep_error=True)
        logger.info("issue C087 error case and expect resp: UPIUResponse.TARGET_FAILURE, ScsiStatus.CHECK_CONDITION, SenseKey.ILLEGAL_REQUEST")
        if not (response.upiu.b6_response == api.UPIUResponse.TARGET_FAILURE and 
            response.upiu.b7_status == api.ScsiStatus.CHECK_CONDITION and
            response.b32_sense_data.b2_sense_key == api.SenseKey.ILLEGAL_REQUEST and
            response.b32_sense_data.b12_asc == 0x1A and
            response.b32_sense_data.b13_ascq == 0x00):
            logger.error_lb(f'issue_C087_to_add_VB_to_bookingQ_and_book_refresh while can not be enqueued situation')
            logger.error_fp(f'expect response fail, but status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}')
            raise SIGHTING_RESPONSE_UNEXPECTED    
    
    



run = Pattern().run
if __name__ == "__main__":
    run()