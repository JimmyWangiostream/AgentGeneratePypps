import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.read_scan.mutual_fun import *
from typing import Any
import time
from Script.project_api.functions import get_physical_layout

class Pattern(UFSTC):
    def pre_process(self) -> None:
        leave_inhibition_mode()
        config_lun(normal_list=[0], em1_list=[1])
        self.write_record = api.get_empty_write_record()
        _flash_setting = api.get_flash_setting()
        _fw_geometry = api.get_fw_geometry()
        self.max_ce = _flash_setting.Max_Fdevice
        self.max_plane = _flash_setting.Plane_Per_Die
        self.pageline_block = self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
        self.WL_block = self.pageline_block * 4 * 3
        self.tlc_vb_size = (_fw_geometry.l88_vb_size_u1 * 512 // 4096)
        _, self.mConfig = project_api.get_mConfig_data()
        logger.info('Pre-process completed')
        pass

    def step1(self) -> None:
        logger.info('Starting: TLC data writing and SSU release test')
        lun = 0
        lba = 0
        datalen = self.tlc_vb_size
        page = 0
        sorted_VB_list_dict_A = get_sorted_VB_list()
        logger.info(f'Initial VB list retrieved: {len(sorted_VB_list_dict_A)} pools')
        # A = int(cast(int, api.read_fw_value('gUfsApiStruct.ftl->split_info->data_gc.target.rb_verify.current.node')))
        vb = 0
        logger.info('Entering main write loop')
        logger.flow(1, 'push write cmd to write each WL')
        logger.flow(2, 'push SSU cmd while LWWL = READ_SCAN_SAFE_AREA * (SliceCnt + 2) - 1')
        while page <= 3311:
            logger.info(f'Processing page {page}')
            _, WL_type, phy_WL, SubBlock, FlushGroup, TwoWLGroup, RainGoup = get_physical_layout(pageline=page, block_type="TLC")
            logger.info(f'Physical layout info - WL_type: {WL_type}, phy_WL: {phy_WL}')
            if WL_type == "TLC":
                prog_page = 3 * 4
            elif WL_type == "MLC":
                prog_page = 2 * 4
            else:
                prog_page = 1 * 4
            chunk_size = self.pageline_block * prog_page
            logger.info(f'Chunk size calculated: {chunk_size} bytes')
            if lba + chunk_size >= self.tlc_vb_size:
                chunk_size = self.tlc_vb_size - lba
                logger.info(f'Adjusting chunk size to fit remaining data: {chunk_size} bytes')
            
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=lun, lba=lba, length=chunk_size, fua=0)
            write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX)
            page += prog_page
            LWWL = phy_WL
            SliceCnt = (LWWL + 1) // self.mConfig.READ_SCAN_SAFE_AREA.value - 2
            logger.info(f'LWWL: {LWWL}, SliceCnt: {SliceCnt}')
            if LWWL == self.mConfig.READ_SCAN_SAFE_AREA.value * (SliceCnt + 2) - 1:
                logger.info('Trigger SSU release at specific WL: LWWL = READ_SCAN_SAFE_AREA * (SliceCnt + 2) - 1')
                push_ssu()
            if LWWL == self.mConfig.READ_SCAN_SAFE_AREA.value * 4 -1:
                logger.info('Sending write command and checking status at specific WL')
                ExecuteCMD.send(clear_on_success=True, timeout=api.UniformTimeout(val=write10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
                sorted_VB_list_dict_B = get_sorted_VB_list()
                logger.info('VB list retrieved after write command')
                # B = int(cast(int, api.read_fw_value('gUfsApiStruct.ftl->split_info->data_gc.target.rb_verify.current.node')))
                vb = sorted_VB_list_dict_B[project_api.VBListNum.CURRENT_L2_TLC][0]
                logger.info(f'Current VB identified: {vb}')
                status = project_api.check_if_current_VB_scan_in_progress_completed(VB=vb)
                logger.flow(3, f'issue 40BF to check VB scan status,  check result: {status}')
                if status != 1:
                    logger.error_lb(f'check status in vu 40BF')
                    logger.error_fp(f'expect status equal to 1 when LWWL = 15, but current value = {status}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            datalen -= chunk_size
            lba += chunk_size
            ExecuteCMD.enqueue(write10)
            logger.info(f'Enqueued write command, remaining data: {datalen} bytes')
        logger.info('Writing TLC data completed')
        ExecuteCMD.send(clear_on_success=True, timeout=api.UniformTimeout(val=write10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
        polling_bkops_idle()
        logger.info('Waiting for BKOPS idle state')
        
        logger.info('Getting VB list after writing data')
        sorted_VB_list_dict_C = get_sorted_VB_list()
        logger.flow(4, 'issue 4055 to check parity released after VB closed')
        response, fw_spare_list, get_recover_parity = project_api.issue_4055_to_get_rain_parity(rain_user=project_api.RainUser.HOST_TLC_RAIN, group=0, keep_error=True)
        if response.upiu.b6_response != api.UPIUResponse.TARGET_FAILURE or response.upiu.b7_status != api.ScsiStatus.CHECK_CONDITION or response.b32_sense_data.b2_sense_key != api.SenseKey.ILLEGAL_REQUEST:
            logger.error_lb(f'check read resp after read parity')
            logger.error_fp(f'expect response fail, but status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}')
            raise SIGHTING_RESPONSE_UNEXPECTED

        # C = int(cast(int, api.read_fw_value('gUfsApiStruct.ftl->split_info->data_gc.target.rb_verify.current.node')))

        logger.flow(5, 'issue C087 to adding VB to booking queue and book refresh')
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=[vb], booking_user=project_api.VUC087Paremeter.MediumPriority)
        polling_bkops_idle()
        logger.info('Waiting for BKOPS idle state after booking')
        
        logger.info(6, 'Checking VB has been release to free block')
        sorted_VB_list_dict_E = get_sorted_VB_list()
        logger.info('VB list retrieved for release status check')
        # D = int(cast(int, api.read_fw_value('gUfsApiStruct.ftl->split_info->data_gc.target.rb_verify.current.node')))
        for pool, list in sorted_VB_list_dict_E.items():
            if vb in list:
                if pool != project_api.VBListNum.FREE_BLK_QUEUE_TLC:
                    logger.error_lb(f'check source VB{vb} released after Read Scan finished')
                    logger.error_fp(f'expect VB{vb} release to FREE_BLK_QUEUE_TLC but current pool = {pool.name}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    

    def post_process(self) -> None:
        logger.info('Post process completed')
        pass
            
    def reconfig_lun(self) -> None:
        config_descs = api.get_config_descriptors(print=False)
        for index in range(4):
            config_descs[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
        for index in range(4):
            api.push_write_config(config_descs[index], index=index)
        ExecuteCMD.send()
        logger.info('LUN reconfiguration completed')
        return

run = Pattern().run

if __name__ == "__main__":
    run()