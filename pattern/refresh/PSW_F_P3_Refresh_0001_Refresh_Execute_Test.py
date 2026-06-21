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


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.fw_geometry = api.get_fw_geometry()
        self.write_record = api.get_empty_write_record()
        self.slc_lun, self.tlc_lun = config_lun()
        pass

    def step1(self) -> None:
        logger.flow(1, f'create Open L2 VB and L1 VB')
        chunksize = api.BLOCK4K_SIZE_128M_BYTE
        total_size = chunksize
        api.sequential_write(lun=self.slc_lun, start_lba=0, total_size=total_size, chunk_size=chunksize, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
        api.sequential_write(lun=self.tlc_lun, start_lba=0, total_size=total_size, chunk_size=chunksize, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
        chunksize = api.BLOCK4K_SIZE_16K_BYTE
        total_size = chunksize
        api.sequential_write(lun=self.tlc_lun, start_lba=api.BLOCK4K_SIZE_128M_BYTE, total_size=total_size, chunk_size=chunksize, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
        _, open_vb_info = api.get_open_vb_info()
        L2_TLC_VB_before = open_vb_info.TLC_L2.logical_vb.value
        L2_SLC_VB_before = open_vb_info.SLC_L2.logical_vb.value
        L1_VB_before = open_vb_info.TLC_L1.logical_vb.value
        PTE_VB_before = open_vb_info.PTE.logical_vb.value

        response, self.health_report_before = project_api.issue_40FE_to_read_enhanced_health_report()
        ftl_vb_list_data_before = get_VB_group()

        logger.info(f'check if VB{PTE_VB_before} group is CURRENT_PTE')
        if project_api.VB_GROUP(ftl_vb_list_data_before[PTE_VB_before]["group"]) != project_api.VB_GROUP.CURRENT_PTE:
            logger.error_lb(f'check VB{PTE_VB_before} group after write')
            logger.error_fp(f'expect VB{PTE_VB_before} is CURRENT_PTE, but current group = {ftl_vb_list_data_before[PTE_VB_before]["group"]}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'check if VB{L2_TLC_VB_before} group is CURRENT_L2_MLC')
        if project_api.VB_GROUP(ftl_vb_list_data_before[L2_TLC_VB_before]["group"]) != project_api.VB_GROUP.CURRENT_L2_MLC:
            logger.error_lb(f'check VB{L2_TLC_VB_before} group after write')
            logger.error_fp(f'expect VB{L2_TLC_VB_before} is CURRENT_L2_MLC, but current group = {ftl_vb_list_data_before[L2_TLC_VB_before]["group"]}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'check if VB{L2_SLC_VB_before} group is CURRENT_L2_SLC')
        if project_api.VB_GROUP(ftl_vb_list_data_before[L2_SLC_VB_before]["group"]) != project_api.VB_GROUP.CURRENT_L2_SLC:
            logger.error_lb(f'check VB{L2_SLC_VB_before} group after write')
            logger.error_fp(f'expect VB{L2_SLC_VB_before} is CURRENT_L2_SLC, but current group = {ftl_vb_list_data_before[L2_SLC_VB_before]["group"]}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'check if VB{L1_VB_before} group is CURRENT_L1')
        if project_api.VB_GROUP(ftl_vb_list_data_before[L1_VB_before]["group"]) != project_api.VB_GROUP.CURRENT_L1:
            logger.error_lb(f'check VB{L1_VB_before} group after write')
            logger.error_fp(f'expect VB{L1_VB_before} is CURRENT_L1, but current group = {ftl_vb_list_data_before[L1_VB_before]["group"]}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(2, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        
        logger.flow(3, f'issue C087 to enqueue as MP/LP refresh')
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=[L2_SLC_VB_before], booking_user=project_api.VUC087Paremeter.MediumPriority)
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=[L2_TLC_VB_before], booking_user=project_api.VUC087Paremeter.MediumPriority)
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=[L1_VB_before], booking_user=project_api.VUC087Paremeter.LowPriority)
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.TableVB, VB_list=[PTE_VB_before], booking_user=project_api.VUC087Paremeter.LowPriority)

        logger.flow(4, f'issue 40C5 to check if the Booking Queue is correct')
        _, booking_q_before = project_api.issue_40C5_to_get_booking_queue()
        logger.info(f'check if LogicalVBNumberInBookingQueue is 4')
        if booking_q_before.LogicalVBNumberInBookingQueue.value != 4:
            logger.error_lb(f'check LogicalVBNumberInBookingQueue after C087')
            logger.error_fp(f'expect LogicalVBNumberInBookingQueue is 4, but current value = {booking_q_before.LogicalVBNumberInBookingQueue.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        for idx, bq in enumerate(booking_q_before.BookingQueueVB):
            if idx >=2:
                BookingUser = project_api.BookingUser.BOOKING_IN_MP
            else:
                BookingUser = project_api.BookingUser.BOOKING_IN_LP
            logger.info(f'check if BookingQueueVB[{idx}] is VU_REFRESH and {BookingUser.name}')
            if (bq.value & project_api.BookingUser.VU_REFRESH != project_api.BookingUser.VU_REFRESH) or \
                (bq.value & project_api.BookingUser.BOOKING_IN_MP != project_api.BookingUser.BOOKING_IN_MP):
                logger.error_lb(f'check BookingQueueVB after C087')
                logger.error_fp(f'expect BookingQueueVB[{idx}] is VU_REFRESH and {BookingUser.name}, but current value = {bq.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
        logger.flow(5, f'SSU sleep + awake')
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.send(QD=1,clear_on_success=True)
        
        logger.flow(6, f'issue 40C5 to check if the Booking Queue not changed')
        _, booking_q_after = project_api.issue_40C5_to_get_booking_queue()
        if booking_q_before.LogicalVBNumberInBookingQueue.value != booking_q_after.LogicalVBNumberInBookingQueue.value:
            logger.error_lb(f'check 40C5 after init')
            logger.error_fp(f'expect value is the same as before but not, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        for idx in range(booking_q_before.LogicalVBNumberInBookingQueue.value):
            if booking_q_before.BookingQueueVB[idx].value != booking_q_after.BookingQueueVB[idx].value:
                logger.error_lb(f'check 40C5 after init')
                logger.error_fp(f'expect value is the same as before but not, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(7, f'SSU Power down + awake')
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x03, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.send(QD=1,clear_on_success=True)
        
        logger.flow(8, f'issue 40C5 to check if the Booking Queue not changed')
        _, booking_q_after = project_api.issue_40C5_to_get_booking_queue()
        if booking_q_before.LogicalVBNumberInBookingQueue.value != booking_q_after.LogicalVBNumberInBookingQueue.value:
            logger.error_lb(f'check 40C5 after init')
            logger.error_fp(f'expect value is the same as before but not, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        for idx in range(booking_q_before.LogicalVBNumberInBookingQueue.value):
            if booking_q_before.BookingQueueVB[idx].value != booking_q_after.BookingQueueVB[idx].value:
                logger.error_lb(f'check 40C5 after init')
                logger.error_fp(f'expect value is the same as before but not, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(9, f'issue C088 to start refresh execution')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        
        logger.flow(10, f'polling until BKOPS is idle')
        polling_bkops(expect_value=0, timeout=900)
        
        logger.flow(11, f'issue 40C5 to check if the Booking Queue is empty')
        _, booking_q_after = project_api.issue_40C5_to_get_booking_queue()
        logger.info(f'check if LogicalVBNumberInBookingQueue is 0')
        if booking_q_after.LogicalVBNumberInBookingQueue.value != 0:
            logger.error_lb(f'check LogicalVBNumberInBookingQueue after bkops idle')
            logger.error_fp(f'expect LogicalVBNumberInBookingQueue is 0, but current value = {booking_q_after.LogicalVBNumberInBookingQueue.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(12, f'check VB after refresh')
        ftl_vb_list_data_after = get_VB_group()
        for vb in range(self.fw_geometry.l52_total_vb_count):
            group_before = project_api.VB_GROUP(ftl_vb_list_data_before[vb]["group"])
            group_after = project_api.VB_GROUP(ftl_vb_list_data_after[vb]["group"])
            partition_before = ftl_vb_list_data_before[vb]["partition"]
            partition_after = ftl_vb_list_data_after[vb]["partition"]
            if group_before != group_after:
                logger.info(f'Before: VB: {vb}, Group = {group_before} ({group_before.name}), Partition = {partition_before}')
                logger.info(f'After:  VB: {vb}, Group = {group_after} ({group_after.name}), Partition = {partition_after}')
                logger.info(f'==================================')
        
        _, open_vb_info = api.get_open_vb_info()
        L2_TLC_VB_after = open_vb_info.TLC_L2.logical_vb.value
        L2_SLC_VB_after = open_vb_info.SLC_L2.logical_vb.value
        L1_VB_after = open_vb_info.TLC_L1.logical_vb.value
        PTE_VB_after = open_vb_info.PTE.logical_vb.value
        
        logger.info(f'check if VB{L2_TLC_VB_before} group is FREE_BLK_QUEUE_MLC')
        if project_api.VB_GROUP(ftl_vb_list_data_after[L2_TLC_VB_before]["group"]) != project_api.VB_GROUP.FREE_BLK_QUEUE_MLC:
            logger.error_lb(f'check VB{L2_TLC_VB_before} group after write')
            logger.error_fp(f'expect VB{L2_TLC_VB_before} is FREE_BLK_QUEUE_MLC, but current group = {ftl_vb_list_data_after[L2_TLC_VB_before]["group"]}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'check if VB{L2_SLC_VB_before} group is FREE_BLK_QUEUE_SLC')
        if project_api.VB_GROUP(ftl_vb_list_data_after[L2_SLC_VB_before]["group"]) != project_api.VB_GROUP.FREE_BLK_QUEUE_SLC:
            logger.error_lb(f'check VB{L2_SLC_VB_before} group after write')
            logger.error_fp(f'expect VB{L2_SLC_VB_before} is FREE_BLK_QUEUE_SLC, but current group = {ftl_vb_list_data_after[L2_SLC_VB_before]["group"]}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'check if VB{PTE_VB_before} group is FREE_BLK_QUEUE_TABLE')
        if project_api.VB_GROUP(ftl_vb_list_data_after[PTE_VB_before]["group"]) not in [project_api.VB_GROUP.FREE_BLK_QUEUE_TABLE, project_api.VB_GROUP.FREE_BLK_QUEUE_SLC]:
            logger.error_lb(f'check VB{PTE_VB_before} group after write')
            logger.error_fp(f'expect VB{PTE_VB_before} is FREE_BLK_QUEUE_TABLE, but current group = {ftl_vb_list_data_after[PTE_VB_before]["group"]}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if L2_SLC_VB_after == L2_SLC_VB_before:
            logger.error_lb(f'check L2 VB index after refresh')
            logger.error_fp(f'expect VB been changed after refresh, but current value = {L2_SLC_VB_after}, before value = {L2_SLC_VB_before}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if PTE_VB_after == PTE_VB_before:
            logger.error_lb(f'check PTE_VB index after refresh')
            logger.error_fp(f'expect VB been changed after refresh, but current value = {PTE_VB_after}, before value = {PTE_VB_before}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if L1_VB_after == L1_VB_before:
            logger.error_lb(f'check L1 VB index after refresh')
            logger.error_fp(f'expect VB been changed after refresh, but current value = {L1_VB_after}, before value = {L1_VB_before}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if L2_TLC_VB_after == L2_TLC_VB_before:
            logger.error_lb(f'check L2_TLC VB index after refresh')
            logger.error_fp(f'expect VB been changed after refresh, but current value = {L2_TLC_VB_after}, before value = {L2_TLC_VB_before}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        
        logger.flow(13, f'Read Compare data')
        api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)
        
        logger.flow(14, f'check health report value')
        response, self.health_report_after = project_api.issue_40FE_to_read_enhanced_health_report()
        self.check_Health_Report_value_increase(self.health_report_before, self.health_report_after, 'read_reclaim_count_for_slc_table')
        self.check_Health_Report_value_increase(self.health_report_before, self.health_report_after, 'read_reclaim_count_for_tlc')
        self.check_Health_Report_value_increase(self.health_report_before, self.health_report_after, 'read_reclaim_count_for_em1')
        pass

    def post_process(self) -> None:
        pass

    def check_Health_Report_value_increase(self, before: project_api.ReadEnhanceHealthReport, after: project_api.ReadEnhanceHealthReport, string:str) -> None:
        value = None
        value_before = None
        for name, field in before.__dict__.items():
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value"):
                if name == string:
                    value_before = field.value
                    break
        for name, field in after.__dict__.items():
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value"):
                if name == string:
                    value = field.value
        if value is None or value_before is None:
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        if value_before >= value:
            logger.error_lb(f'check {string}')
            logger.error_fp(f'expect {string} increase, but before value = {value_before}, current value = {value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    


run = Pattern().run
if __name__ == "__main__":
    run()