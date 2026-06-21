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

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.fw_geometry = api.get_fw_geometry()
        self.write_record = api.get_empty_write_record()
        _, self.debug_info = api.get_debug_info()
        self.slc_lun, self.tlc_lun = config_lun()
        
        
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        vb_cnt = 10
        total_size = int(self.tlc_vb_size * vb_cnt)
        chunksize = api.BLOCK4K_SIZE_128M_BYTE
        api.sequential_write(lun=self.tlc_lun, start_lba=0, total_size=total_size, chunk_size=chunksize, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
        self.sorted_vb_dict = get_sorted_VB_list()
        pass

    def step1(self) -> None:
        logger.flow(1, "issue C088 with 0x00:stop refresh execution, but refresh can still be enqueued")
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        
        logger.flow(2, "issue C087 to enqueue HP/MP/LP refresh")
        temp_vb_list = self.sorted_vb_dict[project_api.VBListNum.USED_BLK_POOL_TLC].copy()
        random.shuffle(temp_vb_list)
        LP_list = [temp_vb_list[0], temp_vb_list[1], temp_vb_list[2], temp_vb_list[3]]
        MP_list = [temp_vb_list[0], temp_vb_list[4], temp_vb_list[5]]
        HP_list = [temp_vb_list[1], temp_vb_list[4], temp_vb_list[6]]
        temp_Dict =  {project_api.VUC087Paremeter.HighPriority: HP_list, project_api.VUC087Paremeter.MediumPriority: MP_list, project_api.VUC087Paremeter.LowPriority: LP_list}
        for Priority, vb_list in temp_Dict.items():
            logger.info(f"push VB {vb_list} as {Priority.name}")
            project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=Priority)
        LP_list = [temp_vb_list[2], temp_vb_list[3]]
        MP_list = [temp_vb_list[0], temp_vb_list[5]]
        HP_list = [temp_vb_list[1], temp_vb_list[4], temp_vb_list[6]]
        PriorityDict =  {project_api.VUC087Paremeter.HighPriority: HP_list, project_api.VUC087Paremeter.MediumPriority: MP_list, project_api.VUC087Paremeter.LowPriority: LP_list}
        
        logger.flow(3, "issue 40C5 to check if the Booking Queue is correct")
        self.booking_q_before = check_booking_queue(PriorityDict)
        
        logger.flow(4, "issue C088 with 0x01:start refresh execution")
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        
        logger.flow(5, "polling until BKOPS is idle and issue 40C5 to check if the Booking Queue is empty")
        polling_bkops_idle()
        self.booking_q_before = check_booking_queue({})
        self.sorted_vb_dict = check_vb_release(PriorityDict)
        
        logger.flow(6, "issue C088 with 0x00:stop refresh execution, but refresh can still be enqueued")
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        
        logger.flow(7, "issue C087 to enqueue HP/MP/LP refresh")
        temp_vb_list = self.sorted_vb_dict[project_api.VBListNum.USED_BLK_POOL_TLC].copy()
        random.shuffle(temp_vb_list)
        LP_list = [temp_vb_list[0], temp_vb_list[1], temp_vb_list[2], temp_vb_list[3]]
        MP_list = [temp_vb_list[0], temp_vb_list[4], temp_vb_list[5]]
        HP_list = [temp_vb_list[1], temp_vb_list[4], temp_vb_list[6]]
        temp_Dict =  {project_api.VUC087Paremeter.LowPriority: LP_list, project_api.VUC087Paremeter.MediumPriority: MP_list, project_api.VUC087Paremeter.HighPriority: HP_list}
        for Priority, vb_list in temp_Dict.items():
            logger.info(f"push VB {vb_list} as {Priority.name}")
            project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=Priority)
        LP_list = [temp_vb_list[2], temp_vb_list[3]]
        MP_list = [temp_vb_list[0], temp_vb_list[5]]
        HP_list = [temp_vb_list[1], temp_vb_list[4], temp_vb_list[6]]
        PriorityDict =  {project_api.VUC087Paremeter.HighPriority: HP_list, project_api.VUC087Paremeter.MediumPriority: MP_list, project_api.VUC087Paremeter.LowPriority: LP_list}
        
        logger.flow(8, "issue 40C5 to check if the Booking Queue is correct")
        self.booking_q_before = check_booking_queue(PriorityDict)
        
        logger.flow(9, "issue C088 with 0x04:Disable Enqueue in refresh BQ")
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.DisableEnqueueInRefreshBQ)

        logger.flow(10, "issue C087 to enqueue HP/MP/LP refresh")
        temp_Dict = get_HP_MP_LP_list(self.sorted_vb_dict[project_api.VBListNum.USED_BLK_POOL_TLC])
        for Priority, vb_list in temp_Dict.items():
            logger.info(f"push VB {vb_list} as {Priority.name}")
            project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=Priority)
    
        logger.flow(11, "issue 40C5 to check if the Booking Queue is correct")
        self.booking_q_before = check_booking_queue(PriorityDict)

        logger.flow(12, "issue C088 with 0x01:start refresh execution")
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        
        logger.flow(13, "polling until BKOPS is idle and issue 40C5 to check if the Booking Queue is empty")
        polling_bkops_idle()
        self.booking_q_before = check_booking_queue({})
        self.sorted_vb_dict = check_vb_release(PriorityDict)
    
        logger.flow(14, "issue C087 to enqueue HP/MP/LP refresh")
        temp_Dict = get_HP_MP_LP_list(self.sorted_vb_dict[project_api.VBListNum.USED_BLK_POOL_TLC])
        for Priority, vb_list in temp_Dict.items():
            logger.info(f"push VB {vb_list} as {Priority.name}")
            project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=Priority)

        logger.flow(15, "polling until BKOPS is idle and issue 40C5 to check if the Booking Queue is empty")
        self.booking_q_before = check_booking_queue({})
        
        logger.flow(16, "issue C088 with 0x05:Enabling Enqueue in refresh BQ")
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.EnableEnqueueInRefreshBQ)
        
        logger.flow(17, "issue C087 to enqueue HP/MP/LP refresh")
        PriorityDict = get_HP_MP_LP_list(self.sorted_vb_dict[project_api.VBListNum.USED_BLK_POOL_TLC])
        for Priority, vb_list in PriorityDict.items():
            logger.info(f"push VB {vb_list} as {Priority.name}")
            project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=Priority)
        
        logger.flow(18, "polling until BKOPS is idle and issue 40C5 to check if the Booking Queue is empty")
        polling_bkops_idle()
        self.booking_q_before = check_booking_queue({})
        self.sorted_vb_dict = check_vb_release(PriorityDict)
        
    
    def post_process(self) -> None:
        pass
    
    
    
    



run = Pattern().run
if __name__ == "__main__":
    run()