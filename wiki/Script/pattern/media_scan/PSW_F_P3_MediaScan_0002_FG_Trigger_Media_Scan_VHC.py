import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.pattern.refresh.mutual_fun import get_VB_group, polling_bkops
from Script.project_api.custom_vu.media_scan_vu.structs import *
from Script.pattern.apl_system_rebuild.mutual_fun import *

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.write_record = api.get_empty_write_record()
        self.flash_setting = api.get_flash_setting()
        self.fw_geometry = api.get_fw_geometry()
        self.geometry_desc = api.get_geometry_descriptor()
        self.max_ce = self.flash_setting.Max_Fdevice
        self.max_plane = self.flash_setting.Plane_Per_Die
        pageline_block = self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
        self.TLC_WL_block = pageline_block * 4 * 3
        self.SLC_WL_block = pageline_block * 4
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.Total_AU_Count = self.geometry_desc.q4_total_raw_device_capacity / (self.geometry_desc.l13_segment_size * self.geometry_desc.b17_allocation_unit_size)
        pass

    def step1(self) -> None:
        
#=================================================================================================
        #open TLC L2
#=================================================================================================
        
        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(2, 'configure lun and write tlc vb one wl size')
        self.config_lun()
        self.write_record = api.get_empty_write_record()
        write_size=self.TLC_WL_block
        api.sequential_write(lun=0, start_lba=0, total_size=write_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        _, open_vb_info = api.get_open_vb_info()
        old_tlc_l2_vb=open_vb_info.TLC_L2.logical_vb.value
        empty_ce=open_vb_info.TLC_L2.first_empty_CE.value
        empty_plane=open_vb_info.TLC_L2.first_empty_plane.value
        empty_page=open_vb_info.TLC_L2.first_empty_physical_page.value

        logger.flow(3, 'inject page0 UECC')
        pca=get_PCA_and_print(lun=0, lba=0)
        inject_UECC(pca=pca)

        logger.flow(4, 'vu40CF record cur scan group')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value
        logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

        logger.flow(5, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)  

        logger.flow(6, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(7, 'idle trigger media scan and check scan group expected')
        spend_time_set = 0x1000000
        while 1:
            param = micron_vu_C085_param_with_data()
            param.last_scan_spend_time = spend_time_set
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)

            api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)

            logger.flow(2, f'issue 40C5 to check if the Booking Queue is correct')
            _, booking_q_before = project_api.issue_40C5_to_get_booking_queue()
            if booking_q_before.LogicalVBNumberInBookingQueue.value != 0:
                for idx, vb in enumerate(booking_q_before.BookingQueueVB):
                    logger.info(f'BookingQ[{idx}]: VB {vb.LogicalVBNumber.value}')
                    if vb.LogicalVBNumber.value != old_tlc_l2_vb:
                        logger.error(f'BookingQ_VB not vb{old_tlc_l2_vb}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                break

            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            for scan_vb in payload.scanned_blocks:
                logger.info('scanned blocks=%d', scan_vb)
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            if new_scan_group == old_scan_group:
                logger.error('scan all group not booking vb')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            spend_time_set+=0x100


        logger.flow(8, f'issue C088 to start refresh execution')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        
        logger.flow(9, f'polling until BKOPS is idle')
        polling_bkops(expect_value=0, timeout=900)

        logger.flow(10, f'issue 40C5 to check if the Booking Queue is empty')
        _, booking_q_after = project_api.issue_40C5_to_get_booking_queue()
        if booking_q_after.LogicalVBNumberInBookingQueue.value != 0:
            logger.error_lb(f'check LogicalVBNumberInBookingQueue after bkops idle')
            logger.error_fp(f'expect LogicalVBNumberInBookingQueue is 0, but current value = {booking_q_after.LogicalVBNumberInBookingQueue.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(11, f'check tlc l2 vb is change')
        _, open_vb_info = api.get_open_vb_info()
        new_tlc_l2_vb=open_vb_info.TLC_L2.logical_vb.value
        if new_tlc_l2_vb == old_tlc_l2_vb:
            logger.info('tlc l2 vb should change')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(12, f'Read Compare data')
        api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)
        
#=================================================================================================
        #open SLC L2
#=================================================================================================

        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(2, 'configure lun and write slc vb one wl size')
        self.config_lun()
        self.write_record = api.get_empty_write_record()
        write_size=self.SLC_WL_block
        api.sequential_write(lun=1, start_lba=0, total_size=write_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        _, open_vb_info = api.get_open_vb_info()
        old_slc_l2_vb=open_vb_info.SLC_L2.logical_vb.value
        empty_ce=open_vb_info.SLC_L2.first_empty_CE.value
        empty_plane=open_vb_info.SLC_L2.first_empty_plane.value
        empty_page=open_vb_info.SLC_L2.first_empty_physical_page.value

        logger.flow(3, 'inject page0 UECC')
        pca=get_PCA_and_print(lun=1, lba=0)
        inject_UECC(pca=pca)

        logger.flow(4, 'vu40CF record cur scan group')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value
        logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

        logger.flow(5, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)  

        logger.flow(6, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(7, 'idle trigger media scan and check scan group expected')
        spend_time_set = 0x1000000
        while 1:
            param = micron_vu_C085_param_with_data()
            param.last_scan_spend_time = spend_time_set
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)

            api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)

            logger.flow(2, f'issue 40C5 to check if the Booking Queue is correct')
            _, booking_q_before = project_api.issue_40C5_to_get_booking_queue()
            if booking_q_before.LogicalVBNumberInBookingQueue.value != 0:
                for idx, vb in enumerate(booking_q_before.BookingQueueVB):
                    logger.info(f'BookingQ[{idx}]: VB {vb.LogicalVBNumber.value}')
                    if vb.LogicalVBNumber.value != old_slc_l2_vb:
                        logger.error(f'BookingQ_VB not vb{old_slc_l2_vb}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                break

            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            for scan_vb in payload.scanned_blocks:
                logger.info('scanned blocks=%d', scan_vb)
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            if new_scan_group == old_scan_group:
                logger.error('scan all group not booking vb')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            spend_time_set+=0x100


        logger.flow(8, f'issue C088 to start refresh execution')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        
        logger.flow(9, f'polling until BKOPS is idle')
        polling_bkops(expect_value=0, timeout=900)

        logger.flow(10, f'issue 40C5 to check if the Booking Queue is empty')
        _, booking_q_after = project_api.issue_40C5_to_get_booking_queue()
        if booking_q_after.LogicalVBNumberInBookingQueue.value != 0:
            logger.error_lb(f'check LogicalVBNumberInBookingQueue after bkops idle')
            logger.error_fp(f'expect LogicalVBNumberInBookingQueue is 0, but current value = {booking_q_after.LogicalVBNumberInBookingQueue.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(11, f'check slc l2 vb is change')
        _, open_vb_info = api.get_open_vb_info()
        new_slc_l2_vb=open_vb_info.SLC_L2.logical_vb.value
        if new_slc_l2_vb == old_slc_l2_vb:
            logger.info('slc l2 vb should change')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(12, f'Read Compare data')
        api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)

#=================================================================================================
        #open TLC L1
#=================================================================================================
        
        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(2, 'configure lun and write tlc l1 vb')
        self.config_lun()
        self.write_record = api.get_empty_write_record()
        write_size = BLOCK4K_SIZE_16K_BYTE
        api.sequential_write(lun=0, start_lba=0, total_size=write_size, chunk_size=BLOCK4K_SIZE_16K_BYTE, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        _, open_vb_info = api.get_open_vb_info()
        old_l1_vb=open_vb_info.TLC_L1.logical_vb.value
        empty_ce=open_vb_info.TLC_L1.first_empty_CE.value
        empty_plane=open_vb_info.TLC_L1.first_empty_plane.value
        empty_page=open_vb_info.TLC_L1.first_empty_physical_page.value

        logger.flow(3, 'inject l1 blk valid page UECC')
        pca = PCA()
        pca.b4_mode = 2
        pca.b5_ce = 0
        pca.b6_plane = 0    
        pca.b11_block_h = (old_l1_vb >> 8) & 0xFF
        pca.b10_block_l = old_l1_vb & 0xFF
        pca.l12_fpage = 0
        inject_UECC(pca=pca)

        logger.flow(4, 'vu40CF record cur scan group')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value
        logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

        logger.flow(5, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)  

        logger.flow(6, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(7, 'idle trigger media scan and check scan group expected')
        spend_time_set = 0x1000000
        while 1:
            param = micron_vu_C085_param_with_data()
            param.last_scan_spend_time = spend_time_set
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)

            api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)

            logger.info('issue 40C5 to check if the Booking Queue is correct')
            _, booking_q_before = project_api.issue_40C5_to_get_booking_queue()
            if booking_q_before.LogicalVBNumberInBookingQueue.value != 0:
                for idx, vb in enumerate(booking_q_before.BookingQueueVB):
                    logger.info(f'BookingQ[{idx}]: VB {vb.LogicalVBNumber.value}')
                    if vb.LogicalVBNumber.value != old_l1_vb:
                        logger.error(f'BookingQ_VB not vb{old_l1_vb}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                break

            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            for scan_vb in payload.scanned_blocks:
                logger.info('scanned blocks=%d', scan_vb)
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            if new_scan_group == old_scan_group:
                logger.error('scan all group not booking vb')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            spend_time_set+=0x100

        logger.flow(8, f'issue C088 to start refresh execution')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        
        logger.flow(9, f'polling until BKOPS is idle')
        polling_bkops(expect_value=0, timeout=900)

        logger.flow(10, f'issue 40C5 to check if the Booking Queue is empty')
        _, booking_q_after = project_api.issue_40C5_to_get_booking_queue()
        if booking_q_after.LogicalVBNumberInBookingQueue.value != 0:
            logger.error_lb(f'check LogicalVBNumberInBookingQueue after bkops idle')
            logger.error_fp(f'expect LogicalVBNumberInBookingQueue is 0, but current value = {booking_q_after.LogicalVBNumberInBookingQueue.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(11, f'check tlc l1 vb is change')
        _, open_vb_info = api.get_open_vb_info()
        new_l1_vb=open_vb_info.TLC_L1.logical_vb.value
        empty_ce=open_vb_info.TLC_L1.first_empty_CE.value
        empty_plane=open_vb_info.TLC_L1.first_empty_plane.value
        empty_page=open_vb_info.TLC_L1.first_empty_physical_page.value
        if new_l1_vb == old_l1_vb:
            logger.info('tlc l1 vb should change')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(12, f'Read Compare data')
        api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)
        
#=================================================================================================
        #open LOG
#=================================================================================================
        
        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)
        
        logger.flow(2, 'configure lun and write tlc vb 12M')
        self.config_lun()
        self.write_record = api.get_empty_write_record()
        api.sequential_write(lun=0, start_lba=0, total_size=BLOCK4K_SIZE_12M_BYTE, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        _, open_vb_info = api.get_open_vb_info()
        old_log_vb=open_vb_info.LOG.logical_vb.value
        empty_ce=open_vb_info.LOG.first_empty_CE.value
        empty_plane=open_vb_info.LOG.first_empty_plane.value
        empty_page=open_vb_info.LOG.first_empty_physical_page.value

        logger.flow(3, 'inject log blk valid page UECC')
        pca = PCA()
        pca.b4_mode = 1
        pca.b5_ce = 0
        pca.b6_plane = 0    
        pca.b11_block_h = (old_log_vb >> 8) & 0xFF
        pca.b10_block_l = old_log_vb & 0xFF
        pca.l12_fpage = 0
        inject_UECC(pca=pca)

        logger.flow(4, 'vu40CF record cur scan group')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value
        logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

        logger.flow(5, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)        

        logger.flow(6, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(7, 'idle trigger media scan and check scan group expected')
        spend_time_set = 0x1000000
        while 1:
            param = micron_vu_C085_param_with_data()
            param.last_scan_spend_time = spend_time_set
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)

            api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)

            logger.flow(2, f'issue 40C5 to check if the Booking Queue is correct')
            _, booking_q_before = project_api.issue_40C5_to_get_booking_queue()
            if booking_q_before.LogicalVBNumberInBookingQueue.value != 0:
                for idx, vb in enumerate(booking_q_before.BookingQueueVB):
                    logger.info(f'BookingQ[{idx}]: VB {vb.LogicalVBNumber.value}')
                    if vb.LogicalVBNumber.value != old_log_vb:
                        logger.error(f'BookingQ_VB not vb{old_log_vb}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                break

            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            for scan_vb in payload.scanned_blocks:
                logger.info('scanned blocks=%d', scan_vb)
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            if new_scan_group == old_scan_group:
                logger.error('scan all group not booking vb')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            spend_time_set+=0x100


        logger.flow(8, f'issue C088 to start refresh execution')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        
        logger.flow(9, f'polling until BKOPS is idle')
        polling_bkops(expect_value=0, timeout=900)

        logger.flow(10, f'issue 40C5 to check if the Booking Queue is empty')
        _, booking_q_after = project_api.issue_40C5_to_get_booking_queue()
        if booking_q_after.LogicalVBNumberInBookingQueue.value != 0:
            logger.error_lb(f'check LogicalVBNumberInBookingQueue after bkops idle')
            logger.error_fp(f'expect LogicalVBNumberInBookingQueue is 0, but current value = {booking_q_after.LogicalVBNumberInBookingQueue.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(11, f'check log vb is refresh')
        _, open_vb_info = api.get_open_vb_info()
        new_log_vb=open_vb_info.LOG.logical_vb.value
        if new_log_vb == old_log_vb:
            logger.error('log vb is not change')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
#=================================================================================================
        #open PTE
#=================================================================================================

        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        #4096 node才會flush pte
        logger.flow(2, 'configure lun and write tlc vb 4096 size')
        self.config_lun()
        self.write_record = api.get_empty_write_record()
        api.sequential_write(lun=0, start_lba=0, total_size=4096, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        _, open_vb_info = api.get_open_vb_info()
        old_pte_vb=open_vb_info.PTE.logical_vb.value
        empty_ce=open_vb_info.PTE.first_empty_CE.value
        empty_plane=open_vb_info.PTE.first_empty_plane.value
        empty_page=open_vb_info.PTE.first_empty_physical_page.value

        logger.flow(3, 'inject pte blk empty page UECC')
        pca = PCA()
        pca.b4_mode = 1
        pca.b5_ce = 0
        pca.b6_plane = 0    
        pca.b11_block_h = (old_pte_vb >> 8) & 0xFF
        pca.b10_block_l = old_pte_vb & 0xFF
        pca.l12_fpage = 0
        inject_UECC(pca=pca)

        logger.flow(4, 'vu40CF record cur scan group')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value
        logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

        logger.flow(5, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)        

        logger.flow(6, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(7, 'idle trigger media scan and check scan group expected')
        spend_time_set = 0x1000000
        while 1:
            param = micron_vu_C085_param_with_data()
            param.last_scan_spend_time = spend_time_set
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)

            api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)

            logger.flow(2, f'issue 40C5 to check if the Booking Queue is correct')
            _, booking_q_before = project_api.issue_40C5_to_get_booking_queue()
            if booking_q_before.LogicalVBNumberInBookingQueue.value != 0:
                for idx, vb in enumerate(booking_q_before.BookingQueueVB):
                    logger.info(f'BookingQ[{idx}]: VB {vb.LogicalVBNumber.value}')
                    if vb.LogicalVBNumber.value != old_pte_vb:
                        logger.error(f'BookingQ_VB not vb{old_pte_vb}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                break

            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            for scan_vb in payload.scanned_blocks:
                logger.info('scanned blocks=%d', scan_vb)
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            if new_scan_group == old_scan_group:
                logger.error('scan all group not booking vb')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            spend_time_set+=0x100


        logger.flow(8, f'issue C088 to start refresh execution')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        
        logger.flow(9, f'polling until BKOPS is idle')
        polling_bkops(expect_value=0, timeout=900)

        logger.flow(10, f'issue 40C5 to check if the Booking Queue is empty')
        _, booking_q_after = project_api.issue_40C5_to_get_booking_queue()
        if booking_q_after.LogicalVBNumberInBookingQueue.value != 0:
            logger.error_lb(f'check LogicalVBNumberInBookingQueue after bkops idle')
            logger.error_fp(f'expect LogicalVBNumberInBookingQueue is 0, but current value = {booking_q_after.LogicalVBNumberInBookingQueue.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(11, f'check pte vb is refresh')
        _, open_vb_info = api.get_open_vb_info()
        new_pte_vb=open_vb_info.PTE.logical_vb.value
        if new_pte_vb == old_pte_vb:
            logger.error('pte vb is not change')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
#=================================================================================================
        #Used Pool Mlc (close TLC L2)
#=================================================================================================

        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(2, 'configure lun and write one tlc vb size')
        self.config_lun()
        self.write_record = api.get_empty_write_record()
        write_size=self.tlc_vb_size
        api.sequential_write(lun=0, start_lba=0, total_size=write_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        pca=get_PCA_and_print(lun=0, lba=0)
        old_used_pool_mlc_vb = pca.b11_block_h<<8 | pca.b10_block_l
        ftl_vb_list_data = get_VB_group()
        if project_api.VB_GROUP(ftl_vb_list_data[old_used_pool_mlc_vb]["group"]) != project_api.VB_GROUP.USED_BLK_POOL_MLC:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(3, 'inject used pool mlc vb page UECC')
        inject_UECC(pca=pca)

        logger.flow(4, 'vu40CF record cur scan group')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value
        logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

        logger.flow(5, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)  

        logger.flow(6, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(7, 'idle trigger media scan and check scan group expected')
        spend_time_set = 0x1000000
        while 1:
            param = micron_vu_C085_param_with_data()
            param.last_scan_spend_time = spend_time_set
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)

            api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)

            logger.info(f'issue 40C5 to check if the Booking Queue is correct')
            _, booking_q_before = project_api.issue_40C5_to_get_booking_queue()
            if booking_q_before.LogicalVBNumberInBookingQueue.value != 0:
                for idx, vb in enumerate(booking_q_before.BookingQueueVB):
                    logger.info(f'BookingQ[{idx}]: VB {vb.LogicalVBNumber.value}')
                    if vb.LogicalVBNumber.value != old_used_pool_mlc_vb:
                        logger.error(f'BookingQ_VB not vb{old_used_pool_mlc_vb}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                break

            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            for scan_vb in payload.scanned_blocks:
                logger.info('scanned blocks=%d', scan_vb)
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            if new_scan_group == old_scan_group:
                logger.error('scan all group not booking vb')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            spend_time_set+=0x100

        logger.flow(8, f'issue C088 to start refresh execution')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        
        logger.flow(9, f'polling until BKOPS is idle')
        polling_bkops(expect_value=0, timeout=900)

        logger.flow(10, f'issue 40C5 to check if the Booking Queue is empty')
        _, booking_q_after = project_api.issue_40C5_to_get_booking_queue()
        if booking_q_after.LogicalVBNumberInBookingQueue.value != 0:
            logger.error_lb(f'check LogicalVBNumberInBookingQueue after bkops idle')
            logger.error_fp(f'expect LogicalVBNumberInBookingQueue is 0, but current value = {booking_q_after.LogicalVBNumberInBookingQueue.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(11, f'check used pool mlc vb is change')
        pca=get_PCA_and_print(lun=0, lba=0)
        new_used_pool_mlc_vb = pca.b11_block_h<<8 | pca.b10_block_l
        if new_used_pool_mlc_vb == old_used_pool_mlc_vb:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(12, f'Read Compare data')
        api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)
        
#=================================================================================================
        #Used Pool Slc (close SLC L2)
#=================================================================================================

        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(2, 'configure lun and write one slc vb size')
        self.config_lun()
        self.write_record = api.get_empty_write_record()
        write_size=self.slc_vb_size
        api.sequential_write(lun=1, start_lba=0, total_size=write_size, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        
        pca=get_PCA_and_print(lun=1, lba=0)
        old_used_pool_slc_vb = pca.b11_block_h<<8 | pca.b10_block_l
        ftl_vb_list_data = get_VB_group()
        if project_api.VB_GROUP(ftl_vb_list_data[old_used_pool_slc_vb]["group"]) != project_api.VB_GROUP.USED_BLK_POOL_SLC:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(3, 'inject used pool slc vb page UECC')
        inject_UECC(pca=pca)

        logger.flow(4, 'vu40CF record cur scan group')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value
        logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

        logger.flow(5, f'issue C088 to stop refresh execution, but refresh can still be enqueued')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)  

        logger.flow(6, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(7, 'idle trigger media scan and check scan group expected')
        spend_time_set = 0x1000000
        while 1:
            param = micron_vu_C085_param_with_data()
            param.last_scan_spend_time = spend_time_set
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)

            api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)

            logger.info(f'issue 40C5 to check if the Booking Queue is correct')
            _, booking_q_before = project_api.issue_40C5_to_get_booking_queue()
            if booking_q_before.LogicalVBNumberInBookingQueue.value != 0:
                for idx, vb in enumerate(booking_q_before.BookingQueueVB):
                    logger.info(f'BookingQ[{idx}]: VB {vb.LogicalVBNumber.value}')
                    if vb.LogicalVBNumber.value != old_used_pool_slc_vb:
                        logger.error(f'BookingQ_VB not vb{old_used_pool_slc_vb}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                break

            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            for scan_vb in payload.scanned_blocks:
                logger.info('scanned blocks=%d', scan_vb)
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            if new_scan_group == old_scan_group:
                logger.error('scan all group not booking vb')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            spend_time_set+=0x100


        logger.flow(8, f'issue C088 to start refresh execution')
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
        
        logger.flow(9, f'polling until BKOPS is idle')
        polling_bkops(expect_value=0, timeout=900)

        logger.flow(10, f'issue 40C5 to check if the Booking Queue is empty')
        _, booking_q_after = project_api.issue_40C5_to_get_booking_queue()
        if booking_q_after.LogicalVBNumberInBookingQueue.value != 0:
            logger.error_lb(f'check LogicalVBNumberInBookingQueue after bkops idle')
            logger.error_fp(f'expect LogicalVBNumberInBookingQueue is 0, but current value = {booking_q_after.LogicalVBNumberInBookingQueue.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(11, f'check used pool slc vb is change')
        pca=get_PCA_and_print(lun=1, lba=0)
        new_used_pool_slc_vb = pca.b11_block_h<<8 | pca.b10_block_l
        if new_used_pool_slc_vb == old_used_pool_slc_vb:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(12, f'Read Compare data')
        api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)        

        pass

    def post_process(self) -> None:
        pass

    def get_health_report(self)->None:
        response, self.health_report = project_api.issue_40FE_to_read_enhanced_health_report()
        
    def config_lun(self) -> None:
        selector = 0x00
        length = 0xE6
        Total_AU_Count = shared.param.gGeometry.q4_total_raw_device_capacity // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
        EM1_total_AU = min(shared.param.gGeometry.l44_enhanced1_max_n_alloc_u, Total_AU_Count//2)
        normal_total_AU = Total_AU_Count//2
        for index in range(4):
            cmd = ExecuteCMD.WriteDescriptor()
            cmd.assign(api.DescriptorIDN.CONFIGURATION, index, selector, length)

            desc = api.ConfigDescriptor310()
            desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            desc.header.b3_boot_enable = api.BootEnable.BOOT_DISABLE
            desc.header.b4_descr_access_en = api.DescrAccessEn.DISABLE
            desc.header.b5_init_power_mode = api.InitPowerMode.ACTIVE
            desc.header.b6_high_priority_lun = api.HighPriorityLUN.ALL_LUN_SAME_PRIORITY
            desc.header.b7_secure_removal_type = api.SecureRemovalType.BY_PHYSICAL_ERASE
            desc.header.b8_init_active_icc_level = api.InitActiveICCLevel.LVL_00
            desc.header.w9_periodic_rtc_update = 0
            desc.header.b11_hpb_control = 0
            desc.header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE
            desc.header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.DISABLE
            desc.header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
            desc.header.l18_num_shared_write_booster_buffer_alloc_units = shared.param.gGeometry.l79_write_booster_buffer_max_n_alloc_units if index==0 else 0
            
            for unit_idx in range(8):
                lun = index * 8 + unit_idx
                if lun ==0:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.NORMAL
                    desc.units[unit_idx].l4_num_alloc_units = normal_total_AU
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif lun==1:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = EM1_total_AU
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                else:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.DISABLE
                    desc.units[unit_idx].l4_num_alloc_units = 0
                    desc.units[unit_idx].b9_logical_block_size = 0

            cmd.set_desc(desc)
            ExecuteCMD.enqueue(cmd)
            ExecuteCMD.send()
        unit_desc_idxes:List[int] = []
        for lun in range(0, shared.param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

        for lun in range(shared.param.gMaxNumberLU):
            if shared.param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send()
        return

run = Pattern().run
if __name__ == "__main__":
    run()