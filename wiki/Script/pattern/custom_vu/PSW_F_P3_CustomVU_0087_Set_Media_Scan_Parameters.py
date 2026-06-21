from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from typing import List, cast, Optional
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from time import sleep
from Script.project_api.custom_vu.media_scan_vu.structs import *
from Script.pattern.apl_system_rebuild.mutual_fun import *
from Script.pattern.refresh.mutual_fun import get_VB_group

media_scan_open_vb_group_scan_map = [
    project_api.VB_GROUP.CURRENT_L2_MLC.value,
    project_api.VB_GROUP.CURRENT_DATA_GC_BLK_MLC.value,
    project_api.VB_GROUP.INCOMPLETE_BLK_MLC.value,
    project_api.VB_GROUP.CURRENT_L1.value,
    project_api.VB_GROUP.CURRENT_L2_SLC.value,
    project_api.VB_GROUP.CURRENT_DATA_GC_BLK_SLC.value,
    project_api.VB_GROUP.INCOMPLETE_BLK_SLC.value,
    project_api.VB_GROUP.CURRENT_PTE.value,
    project_api.VB_GROUP.LOG_TAB_BLK.value,
    project_api.VB_GROUP.RAIN_SWAP_NO_OBR_SLC_L2_SLC.value,
    project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_SLC.value,
    project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_TLC.value
]

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.write_record = api.get_empty_write_record()
        self.flash_setting = api.get_flash_setting()
        self._fw_geometry = api.get_fw_geometry()
        self.max_ce = self.flash_setting.Max_Fdevice
        self.max_plane = self.flash_setting.Plane_Per_Die
        pageline_block = self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
        self.TLC_WL_block = pageline_block * 4 * 3
        self.SLC_WL_block = pageline_block * 4
        self.tlc_vb_size = (self._fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.slc_vb_size = (self._fw_geometry.l84_vb_size_u0 * 512 // 4096)
        pass

    def step1(self) -> None:
        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)
        pass

    def step2(self) -> None:

#=================================================================================================
        #verify tlc bin < BIN_LOW
#=================================================================================================
        
        logger.flow(2, 'configure lun and write slc tlc one wl size')
        self.config_lun_and_write_slc_tlc_partition()

        logger.flow(3, 'vuC085 set media scan bin_low = 10')
        param = micron_vu_C085_param_with_data()
        param.set_media_scan_bin_low = 10
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        temppca = PCA()
        temppca.from_bytes(bytearray(self.tlc_pca.payload))
        logger.info(f'Block = {(temppca.b11_block_h<<8) | (temppca.b10_block_l)}, mode = {temppca.b4_mode}, CE = {temppca.b5_ce}, Plane = {temppca.b6_plane}, fPage = {temppca.l12_fpage}(pageline = {temppca.l12_fpage>>5}), lmu = {temppca.b20_lmu}, format = {temppca.b7_format}')
        
        logger.flow(4, f'vu4028 trigger media scan vhc with tlc block valid page0, bfea bin set 9 ( tlc bin < BIN_LOW )')
        parm = micron_vu_4028_param()
        parm.d16_die = temppca.b5_ce
        parm.d20_plane = temppca.b6_plane
        parm.d24_block = (temppca.b11_block_h<<8) | (temppca.b10_block_l)
        parm.d28_page = 0
        parm.b40_slc_mode = 0 #0: TLC 1:SLC
        parm.b41_bfea_bin = 9
        parm.b42_page_attr = 3 #page attr: 0--SLC   1--MLC_LP  2--MLC_UP 3--TLC_LP 4--TLC_UP   5--TLC_XP
        parm.b43_is_blank_page = 0 #1： is blank page   0：is not blank page
        parm.b44_is_partial_block = 1 #0: is full block  1: is partial block
        parm.b45_is_em1_vb = 0 #0 is not EM1   1: is EM1

        logger.flow(5, f'vu4028 check media scan status is 0xFF')
        resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(parm)
        if payload.media_scan_status.value != 0xFF:
            logger.error(f'expected media scan status is 0xFF, but result is {payload.media_scan_status.value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

#=================================================================================================
        #verify set bin > BIN_LOW
#=================================================================================================
        
        logger.flow(2, 'configure lun and write slc tlc one wl size')
        self.config_lun_and_write_slc_tlc_partition()

        logger.flow(3, 'vuC085 set media scan bin_low = 10')
        param = micron_vu_C085_param_with_data()
        param.set_media_scan_bin_low = 10
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        temppca = PCA()
        temppca.from_bytes(bytearray(self.tlc_pca.payload))
        logger.info(f'Block = {(temppca.b11_block_h<<8) | (temppca.b10_block_l)}, mode = {temppca.b4_mode}, CE = {temppca.b5_ce}, Plane = {temppca.b6_plane}, fPage = {temppca.l12_fpage}(pageline = {temppca.l12_fpage>>5}), lmu = {temppca.b20_lmu}, format = {temppca.b7_format}')
        
        logger.flow(4, f'vu4028 trigger media scan vhc with tlc block valid page0, bfea bin set 11 ( tlc bin > BIN_LOW )')
        parm = micron_vu_4028_param()
        parm.d16_die = temppca.b5_ce
        parm.d20_plane = temppca.b6_plane
        parm.d24_block = (temppca.b11_block_h<<8) | (temppca.b10_block_l)
        parm.d28_page = 0
        parm.b40_slc_mode = 0 #0: TLC 1:SLC
        parm.b41_bfea_bin = 11
        parm.b42_page_attr = 3 #page attr: 0--SLC   1--MLC_LP  2--MLC_UP 3--TLC_LP 4--TLC_UP   5--TLC_XP
        parm.b43_is_blank_page = 0 #1： is blank page   0：is not blank page
        parm.b44_is_partial_block = 1 #0: is full block  1: is partial block
        parm.b45_is_em1_vb = 0 #0 is not EM1   1: is EM1

        logger.flow(5, f'vu4028 check media scan status is 0xD')
        resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(parm)
        if payload.media_scan_status.value != 0x0D:
            logger.error(f'expected media scan status is 0xD, but result is {payload.media_scan_status.value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
#=================================================================================================
        #verify tlc bin < BIN_HIGH
#=================================================================================================
        
        logger.flow(2, 'configure lun and write slc tlc one wl size')
        self.config_lun_and_write_slc_tlc_partition()

        logger.flow(3, 'vuC085 set media scan bin_high = 10')
        param = micron_vu_C085_param_with_data()
        param.set_media_scan_bin_high = 10
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        temppca = PCA()
        temppca.from_bytes(bytearray(self.tlc_pca.payload))
        logger.info(f'Block = {(temppca.b11_block_h<<8) | (temppca.b10_block_l)}, mode = {temppca.b4_mode}, CE = {temppca.b5_ce}, Plane = {temppca.b6_plane}, fPage = {temppca.l12_fpage}(pageline = {temppca.l12_fpage>>5}), lmu = {temppca.b20_lmu}, format = {temppca.b7_format}')
        
        logger.flow(4, f'vu4028 trigger media scan vhc with tlc block valid page0, bfea bin set 9 ( tlc bin < BIN_HIGH )')
        parm = micron_vu_4028_param()
        parm.d16_die = temppca.b5_ce
        parm.d20_plane = temppca.b6_plane
        parm.d24_block = (temppca.b11_block_h<<8) | (temppca.b10_block_l)
        parm.d28_page = 0
        parm.b40_slc_mode = 0 #0: TLC 1:SLC
        parm.b41_bfea_bin = 9
        parm.b42_page_attr = 3 #page attr: 0--SLC   1--MLC_LP  2--MLC_UP 3--TLC_LP 4--TLC_UP   5--TLC_XP
        parm.b43_is_blank_page = 0 #1： is blank page   0：is not blank page
        parm.b44_is_partial_block = 1 #0: is full block  1: is partial block
        parm.b45_is_em1_vb = 0 #0 is not EM1   1: is EM1

        logger.flow(5, f'vu4028 check media scan status is 0xD')
        resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(parm)
        if payload.media_scan_status.value != 0x0D:
            logger.error(f'expected media scan status is 0xD, but result is {payload.media_scan_status.value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

#=================================================================================================
        #verify set bin > BIN_HIGH
#=================================================================================================
        
        logger.flow(2, 'configure lun and write slc tlc one wl size')
        self.config_lun_and_write_slc_tlc_partition()        

        logger.flow(3, 'vuC085 set media scan bin_high = 10')
        param = micron_vu_C085_param_with_data()
        param.set_media_scan_bin_high = 10
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        temppca = PCA()
        temppca.from_bytes(bytearray(self.tlc_pca.payload))
        logger.info(f'Block = {(temppca.b11_block_h<<8) | (temppca.b10_block_l)}, mode = {temppca.b4_mode}, CE = {temppca.b5_ce}, Plane = {temppca.b6_plane}, fPage = {temppca.l12_fpage}(pageline = {temppca.l12_fpage>>5}), lmu = {temppca.b20_lmu}, format = {temppca.b7_format}')
        
        logger.flow(4, f'vu4028 trigger media scan vhc with tlc block valid page0, bfea bin set 11 ( tlc bin > BIN_HIGH )')
        parm = micron_vu_4028_param()
        parm.d16_die = temppca.b5_ce
        parm.d20_plane = temppca.b6_plane
        parm.d24_block = (temppca.b11_block_h<<8) | (temppca.b10_block_l)
        parm.d28_page = 0
        parm.b40_slc_mode = 0 #0: TLC 1:SLC
        parm.b41_bfea_bin = 11
        parm.b42_page_attr = 3 #page attr: 0--SLC   1--MLC_LP  2--MLC_UP 3--TLC_LP 4--TLC_UP   5--TLC_XP
        parm.b43_is_blank_page = 0 #1： is blank page   0：is not blank page
        parm.b44_is_partial_block = 1 #0: is full block  1: is partial block
        parm.b45_is_em1_vb = 0 #0 is not EM1   1: is EM1

        logger.flow(5, f'vu4028 check media scan status is 0xFF')
        resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(parm)
        if payload.media_scan_status.value != 0xFF:
            logger.error(f'expected media scan status is 0xFF, but result is {payload.media_scan_status.value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
#=================================================================================================
        #verify set MS_SCAN_INSTANCE_FREQ spend time
#=================================================================================================

        logger.flow(2, 'configure lun and write slc tlc one wl size')
        self.config_lun_and_write_slc_tlc_partition()

        logger.flow(3, 'vu40CF record cur scan group')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_vb = payload.cur_scan_vb.value
        old_scan_page = payload.cur_scan_page.value
        old_scan_group = payload.scan_group.value
        logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')

        logger.flow(3, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(4, 'idle trigger media scan and check scan group expected')
        spend_time_set = 0x1000000
        for i in range(5):
            param = micron_vu_C085_param_with_data()
            param.last_scan_spend_time = spend_time_set
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)

            time.sleep(5)

            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            if old_scan_group == 22:
                if new_scan_vb != 0xFFFFFFFF or new_scan_page != 0xFFFFFFFF or new_scan_group != 0:
                    logger.error(f'scan group unexpected, new_scan_group={new_scan_group}, expected scan group=0')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            elif new_scan_vb != 0xFFFFFFFF or new_scan_page != 0xFFFFFFFF or new_scan_group != old_scan_group+1:
                logger.error(f'scan group unexpected, new_scan_group={new_scan_group}, old_scan_group={old_scan_group}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            old_scan_group = new_scan_group
            spend_time_set+=0x100

#=================================================================================================
        #verify set Full scan group spend time
#=================================================================================================

        logger.flow(2, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(3, 'configure lun and write slc tlc one wl size')
        self.config_lun_and_write_slc_tlc_partition()

        logger.flow(4, 'vu40CF get old scan group')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scan_group = payload.scan_group.value

        logger.flow(5, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(6, 'vuC085 scan two group and get scan percentage')
        set_spend_time = 0x1000000
        for i in range(2):
            param = micron_vu_C085_param_with_data()
            param.last_scan_spend_time = set_spend_time
            resp = project_api.issue_C085_to_set_media_scan_parameters(param)

            time.sleep(5)

            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_group = payload.scan_group.value
            scan_percentage = payload.media_scan_percentage.value
            logger.info('scan_percentage=%d', scan_percentage)
            set_spend_time+=0x100

        logger.flow(7, 'vuC085 set full scan group spend time trigger full scan')
        param = micron_vu_C085_param_with_data()
        param.last_full_scan_group_spend_time = set_spend_time
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        logger.flow(8, 'delay 5s')
        time.sleep(5)

        logger.flow(9, 'vu40CF get new scan percentage')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        new_scan_group = payload.scan_group.value
        new_scan_percentage = payload.media_scan_percentage.value

        logger.flow(10, 'check scan percentage are reset')
        if new_scan_percentage != 4:
            logger.error('scan percentage unexpected =%d', new_scan_percentage)
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
#=================================================================================================
        #verify set open block freq in secs (MS_OPEN_CURSOR_FREQ)
#=================================================================================================

        logger.flow(2, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(3, 'configure lun and write slc tlc one wl size')
        self.config_lun_and_write_slc_tlc_partition()

        logger.flow(4, 'vu40CF get scanned blocks')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        old_scanned_blocks=[]
        ftl_vb_list_data = get_VB_group()
        for vb in payload.scanned_blocks:
            group_idx = ftl_vb_list_data[vb]["group"]
            logger.info('scanned blocks=%d group idx=%d', vb, group_idx)
            old_scanned_blocks.append(vb)

        logger.flow(5, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)
        
        logger.flow(6, 'vuC085 set open blk freq in secs=30')
        param = micron_vu_C085_param_with_data()
        param.set_open_blk_freq_in_secs = 30
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)
        
        logger.flow(7, 'vu40CF check open blk freq in secs=30')
        resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
        if payload.media_scan_open_freq_in_sec.value != 30:
            logger.error('media_scan_open_freq_in_sec=%d not expected = 30', payload.media_scan_open_freq_in_sec.value)
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(8, '1st idle trigger current scan open blk finish')
        while 1:
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            if payload.cur_scan_vb.value != 0xFFFFFFFF and payload.cur_scan_page.value != 0xFFFFFFFF:
                old_elapsed_time = payload.elapsed_time.value
                break
        while 1:
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            if payload.cur_scan_vb.value == 0xFFFFFFFF and payload.cur_scan_page.value == 0xFFFFFFFF:
                break

        logger.flow(9, '2nd idle trigger media scan and check trigger time expected')
        while 1:
            time.sleep(1)
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            new_elapsed_time = payload.elapsed_time.value
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            logger.info(f'old_elapsed_time={old_elapsed_time}, new_elapsed_time={new_elapsed_time}')

            if new_scan_vb != 0xFFFFFFFF and new_scan_page != 0xFFFFFFFF:
                logger.info('triggered')
                elapsed_time = new_elapsed_time - old_elapsed_time
                if abs(30 - elapsed_time) > 3:
                    logger.error('next trigger time diff over 3s')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                while 1:
                    resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
                    if payload.cur_scan_vb.value == 0xFFFFFFFF and payload.cur_scan_page.value == 0xFFFFFFFF:
                        break
                
                logger.flow(9, 'check scan vb group idx should open blk group')
                for scan_vb in payload.scanned_blocks:
                    group_idx = ftl_vb_list_data[scan_vb]["group"]
                    logger.info('scanned blocks=%d group idx=%d', scan_vb, group_idx)
                    if group_idx not in media_scan_open_vb_group_scan_map:
                         if scan_vb not in old_scanned_blocks:
                            logger.error('scan_vb=%d not in old_scanned_blocks', scan_vb)
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    
                break

#=================================================================================================
        #verify set scale factor to reduce media scan time (MS_SCAN_INSTANCE_FREQ)
#================================================================================================= 
        
        logger.flow(2, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)

        logger.flow(3, 'configure lun and write slc tlc one wl size')
        self.config_lun_and_write_slc_tlc_partition()

        logger.flow(4, 'vuC08B enable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=True)

        logger.flow(5, 'vuC085 set last scan spend time=0x1000000 to trggier media scan')
        param = micron_vu_C085_param_with_data()
        param.last_scan_spend_time = 0x1000000
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)

        logger.flow(6, 'vuC085 set scale factor reduce scan time = 150 (Triggered once every 6 minutes)')
        param = micron_vu_C085_param_with_data()
        param.set_scale_factor_reduce_scan_time = 150
        resp = project_api.issue_C085_to_set_media_scan_parameters(param)        

        logger.flow(7, '1st idle trigger current media scan finish')
        while 1:
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            if payload.cur_scan_vb.value != 0xFFFFFFFF and payload.cur_scan_page.value != 0xFFFFFFFF:
                old_elapsed_time = payload.elapsed_time.value
                break
        while 1:
            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            old_scan_vb = payload.cur_scan_vb.value
            old_scan_page = payload.cur_scan_page.value
            old_scan_group = payload.scan_group.value
            logger.info(f'old_scan_vb={old_scan_vb}, old_scan_page={old_scan_page}, old_scan_group={old_scan_group}')            
            if payload.cur_scan_vb.value == 0xFFFFFFFF and payload.cur_scan_page.value == 0xFFFFFFFF:
                break        

        logger.flow(8, '2nd idle trigger next scan and check trigger next scan group time expected')
        while 1:
            logger.info('idle 1s')
            time.sleep(1)

            resp, payload = project_api.issue_40CF_to_get_media_scan_parameters()
            new_scan_vb = payload.cur_scan_vb.value
            new_scan_page = payload.cur_scan_page.value
            new_scan_group = payload.scan_group.value
            new_elapsed_time = payload.elapsed_time.value
            logger.info(f'new_scan_vb={new_scan_vb}, new_scan_page={new_scan_page}, new_scan_group={new_scan_group}')
            logger.info(f'old_elapsed_time={old_elapsed_time}, new_elapsed_time={new_elapsed_time}')
            if new_scan_group != old_scan_group:
                if old_scan_group == 22:
                    if new_scan_group != 0:
                        logger.error(f'scan group unexpected, new_scan_group={new_scan_group}, expected scan group=0')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                elif new_scan_group != old_scan_group+1:
                    logger.error(f'scan group unexpected, new_scan_group={new_scan_group}, old_scan_group={old_scan_group}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                elapsed_time = new_elapsed_time - old_elapsed_time
                if abs(360 - elapsed_time) > 3:
                    logger.error('next trigger time diff over 3s')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                break
            
        pass

    def post_process(self) -> None:
        pass
    
    def config_lun_and_write_slc_tlc_partition(self)->None:

        self.config_lun()

        api.sequential_write(lun=0, start_lba=0, total_size=self.TLC_WL_block, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        self.tlc_pca = api.lba_to_pba(lun=0, lba=0)

        api.sequential_write(lun=1, start_lba=0, total_size=self.SLC_WL_block, chunk_size=api.WRITE_10_MAX_BLOCK_LEN, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        self.slc_pca = api.lba_to_pba(lun=1, lba=0)

        pass

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
    
    def get_target_vb_list(self, group:int)-> List[int]:
        retval = 0
        vb_list = []
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'access_mode': {'pos': 6, 'len': 2, 'mask': 0x3}, 
            'dirty': {'pos': 8, 'len': 1, 'mask': 0x1}, 
        }
        response, rep_data = get_vb_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data)):
            if self._fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break

            ftl_vb_list_data.update({vb : {k: (((rep_data[vb*4]|rep_data[vb*4+1]<<8) >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        used_mlc_cout = 0
        map_vb_cnt = {} # type: ignore
        logger.info(f'[show all vb info at begin]')
        for vb, vb_info in ftl_vb_list_data.items():
            last_type = vb_info['group']
            dirtybit = vb_info['dirty']
            if last_type in map_vb_cnt:
                map_vb_cnt[last_type] += 1
            else:
                map_vb_cnt[last_type] = 1
            logger.info(f'[vb = {vb}, group type = {last_type}, dirtybit = {dirtybit}]')
            if last_type == group:
                vb_list.append(vb)
        for k,v in map_vb_cnt.items():
            logger.info(f'group type = {k}, cnt = {v}]')
        logger.info(f'get target vb list of vb {group} cnt = {len(vb_list)}')
        return vb_list

run = Pattern().run
if __name__ == "__main__":
    run()