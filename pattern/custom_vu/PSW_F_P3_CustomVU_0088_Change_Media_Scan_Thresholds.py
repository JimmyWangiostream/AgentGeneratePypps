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
from Script.project_api.custom_vu.media_scan_vu.structs import *
from Script.project_api.custom_vu.lba_convert_vu import issue_4051_to_get_physical_address
from Script.project_api.custom_vu.raw_data_vu.functions import issue_4060_to_read_raw_data
from Script.pattern.apl_system_rebuild.mutual_fun import *
from Script.project_api.reh.functions import issue_409E_to_get_error_bit_numbers
from Script.project_api.set_get_temperature.structs import GetNandTemperature, SetNandTemperature

class MEDIA_SCAN_STATUS(IntEnum):
    BE_STATUS_MEDIA_SCAN_WRONG_PAGE_ATTR = 1
    BE_STATUS_MEDIA_SCAN_BLOCK_WRONG_EMPTY_PAGE = 2
    BE_STATUS_MEDIA_SCAN_WRONG_PAGE_FOR_VALLEY_CHECK = 3
    BE_STATUS_MEDIA_SCAN_BLOCK_FOLD_FOR_MLCLP_BEC = 4
    BE_STATUS_MEDIA_SCAN_BLOCK_FOLD_FOR_VRLC_LEFT_RIGHT_READ_UECC = 6
    BE_STATUS_MEDIA_SCAN_BLOCK_FOLD_FOR_DIFFEC = 7
    BE_STATUS_MEDIA_SCAN_BLOCK_FOLD_FOR_TEMP = 8
    BE_STATUS_MEDIA_SCAN_BLOCK_FOLD_EMPTY_FOR_EPC = 11
    BE_STATUS_MEDIA_SCAN_BLOCK_UNFOLD_FOR_GOOD_BEC = 13
    BE_STATUS_MEDIA_SCAN_BLOCK_UNFOLD_FOR_TEMP = 14
    BE_STATUS_MEDIA_SCAN_BLOCK_UNFOLD_FOR_VALLEY_OFFSET_CENTER_EC = 15
    BE_STATUS_MEDIA_SCAN_BLOCK_UNFOLD_EMPTY = 16
    BE_STATUS_MEDIA_SCAN_INVALID = 0xFF

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
        logger.flow(1, 'vuC08B disable media scan')
        response = project_api.issue_C08B_to_enable_diable_media_scan(enable_media_scan=False)
        pass

    def step2(self) -> None:

#=================================================================================================
        
        #verify vu change BEC_VALLEY_TH

#=================================================================================================        
        
        logger.flow(2, 'configure lun and write slc tlc one wl size')
        self.config_lun_and_write_slc_tlc_partition()

        logger.flow(3, 'inject error bit cnt=100 at lba 0')
        self.flipbit_on_SLC(testlba=0, flipbit_set=100, index_4k=0)

        logger.flow(4, f'vu4028 trigger media scan vhc with slc block valid page0')
        _,micron_pca = issue_4051_to_get_physical_address(1, lba=0)
        vu_4028_param = micron_vu_4028_param()
        vu_4028_param.d16_die = micron_pca.die.value
        vu_4028_param.d20_plane = micron_pca.plane.value
        vu_4028_param.d24_block = micron_pca.virtual_block_number.value
        vu_4028_param.d28_page = 0
        vu_4028_param.b40_slc_mode = 1 #0: TLC 1:SLC
        vu_4028_param.b41_bfea_bin = 0
        vu_4028_param.b42_page_attr = 0 #page attr: 0--SLC   1--MLC_LP  2--MLC_UP 3--TLC_LP 4--TLC_UP   5--TLC_XP
        vu_4028_param.b43_is_blank_page = 0 #1： is blank page   0：is not blank page
        vu_4028_param.b44_is_partial_block = 1 #0: is full block  1: is partial block
        vu_4028_param.b45_is_em1_vb = 1 #0 is not EM1   1: is EM1

        resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(vu_4028_param)
        logger.info('bec = %d', payload.bec.value)
        logger.info('diff_ec = %d', payload.diff_ec.value)
        logger.info('arc_offset = %d', payload.arc_offset.value)
        logger.info('center_ec = %d', payload.center_ec.value)
        if payload.media_scan_status.value == MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_INVALID.value:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(5, f'get golden bec value')
        bec=payload.bec.value

        logger.flow(6, f'vuD08E change bec_th and execute media scan status expected')
        test_bec_th = [bec-1, bec, bec+1]
        for bec_th in test_bec_th:
            vu_D08E_param = micron_vu_D08E_param()
            vu_D08E_param.w14_bec_valley_th_slc = bec_th
            vu_D08E_param.b22_is_partial_block = 1 #0: is full block  1: is partial block
            vu_D08E_param.b23_is_em1 = 1 #0 is not EM1  1: is EM1
            resp = project_api.issue_D08E_to_change_media_scan_thresholds(vu_D08E_param)

            resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(vu_4028_param)
            if payload.bec.value > bec_th:
                if payload.media_scan_status.value != MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_BLOCK_UNFOLD_FOR_VALLEY_OFFSET_CENTER_EC.value:
                    logger.error(f'expected media scan status is 15, but result is {payload.media_scan_status.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                if payload.media_scan_status.value != MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_BLOCK_UNFOLD_FOR_GOOD_BEC.value:
                    logger.error(f'expected media scan status is 13, but result is {payload.media_scan_status.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
#=================================================================================================
        
        #verify vu change VALLEY_DIFFEC_TH

#================================================================================================= 

        logger.flow(2, 'configure lun and write slc tlc one wl size')
        self.config_lun_and_write_slc_tlc_partition()
        
        param = micron_vu_D08E_param()
        param.b22_is_partial_block = 1 #0: is full block  1: is partial block
        param.b23_is_em1 = 1 #0 is not EM1  1: is EM1
        resp = project_api.issue_D08E_to_change_media_scan_thresholds(param)
        
        logger.flow(3, 'inject error bit cnt 150 to each 4k in a 16K ')
        for idx_of_4k in range(4): 
            self.flipbit_on_SLC(testlba=0, flipbit_set=150, index_4k=idx_of_4k)

        logger.flow(4, f'vu4028 trigger media scan vhc with slc block valid page0')
        _,micron_pca = issue_4051_to_get_physical_address(1, lba=0)
        vu_4028_param = micron_vu_4028_param()
        vu_4028_param.d16_die = micron_pca.die.value
        vu_4028_param.d20_plane = micron_pca.plane.value
        vu_4028_param.d24_block = micron_pca.virtual_block_number.value
        vu_4028_param.d28_page = 0
        vu_4028_param.b40_slc_mode = 1 #0: TLC 1:SLC
        vu_4028_param.b41_bfea_bin = 0
        vu_4028_param.b42_page_attr = 0 #page attr: 0--SLC   1--MLC_LP  2--MLC_UP 3--TLC_LP 4--TLC_UP   5--TLC_XP
        vu_4028_param.b43_is_blank_page = 0 #1： is blank page   0：is not blank page
        vu_4028_param.b44_is_partial_block = 1 #0: is full block  1: is partial block
        vu_4028_param.b45_is_em1_vb = 1 #0 is not EM1   1: is EM1

        resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(vu_4028_param)
        logger.info('status = %d', payload.media_scan_status.value)
        logger.info('bec = %d', payload.bec.value)
        logger.info('diff_ec = %d', payload.diff_ec.value)
        logger.info('arc_offset = %d', payload.arc_offset.value)
        logger.info('center_ec = %d', payload.center_ec.value)
        if payload.media_scan_status.value == MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_INVALID.value:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(5, f'get golden diff_ec value')
        diff_ec=payload.diff_ec.value

        logger.flow(6, f'vuD08E change diffec_th and execute media scan status expected')
        test_diff_ec_th = [diff_ec-1, diff_ec, diff_ec+1]
        for diff_ec_th in test_diff_ec_th:
            vu_D08E_param = micron_vu_D08E_param()
            vu_D08E_param.b20_valley_ofs_th_slc = 0xFF
            vu_D08E_param.w16_valley_center_ecth_slc = 0xFFFF
            vu_D08E_param.w18_valley_diffec_th_slc = diff_ec_th
            vu_D08E_param.b22_is_partial_block = 1 #0: is full block  1: is partial block
            vu_D08E_param.b23_is_em1 = 1 #0 is not EM1  1: is EM1
            resp = project_api.issue_D08E_to_change_media_scan_thresholds(vu_D08E_param)

            resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(vu_4028_param)
            logger.info('status = %d', payload.media_scan_status.value)
            logger.info('bec = %d', payload.bec.value)
            logger.info('diff_ec = %d', payload.diff_ec.value)
            logger.info('arc_offset = %d', payload.arc_offset.value)
            logger.info('center_ec = %d', payload.center_ec.value)            
            if payload.diff_ec.value >= diff_ec_th:
                if payload.media_scan_status.value != MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_BLOCK_FOLD_FOR_DIFFEC.value:
                    logger.error(f'expected media scan status is 7, but result is {payload.media_scan_status.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                if payload.media_scan_status.value != MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_BLOCK_UNFOLD_FOR_VALLEY_OFFSET_CENTER_EC.value:
                    logger.error(f'expected media scan status is 15, but result is {payload.media_scan_status.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

#=================================================================================================
        
        #verify vu change VALLEY_OFST_TH

#================================================================================================= 

        logger.flow(2, 'configure lun and write slc tlc one wl size')
        self.config_lun_and_write_slc_tlc_partition()
        
        param = micron_vu_D08E_param()
        param.b22_is_partial_block = 1 #0: is full block  1: is partial block
        param.b23_is_em1 = 1 #0 is not EM1  1: is EM1
        resp = project_api.issue_D08E_to_change_media_scan_thresholds(param)
        
        logger.flow(3, 'inject error bit cnt 150 to each 4k in a 16K ')
        for idx_of_4k in range(4): 
            self.flipbit_on_SLC(testlba=0, flipbit_set=150, index_4k=idx_of_4k)

        logger.flow(4, f'vu4028 trigger media scan vhc with slc block valid page0')
        _,micron_pca = issue_4051_to_get_physical_address(1, lba=0)
        vu_4028_param = micron_vu_4028_param()
        vu_4028_param.d16_die = micron_pca.die.value
        vu_4028_param.d20_plane = micron_pca.plane.value
        vu_4028_param.d24_block = micron_pca.virtual_block_number.value
        vu_4028_param.d28_page = 0
        vu_4028_param.b40_slc_mode = 1 #0: TLC 1:SLC
        vu_4028_param.b41_bfea_bin = 0
        vu_4028_param.b42_page_attr = 0 #page attr: 0--SLC   1--MLC_LP  2--MLC_UP 3--TLC_LP 4--TLC_UP   5--TLC_XP
        vu_4028_param.b43_is_blank_page = 0 #1： is blank page   0：is not blank page
        vu_4028_param.b44_is_partial_block = 1 #0: is full block  1: is partial block
        vu_4028_param.b45_is_em1_vb = 1 #0 is not EM1   1: is EM1
        resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(vu_4028_param)
        if payload.media_scan_status.value == MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_INVALID.value:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(5, f'get golden arc_offset value')
        arc_offset=abs(int.from_bytes(payload.arc_offset.value.to_bytes(), byteorder='big', signed=True))
        logger.info('arc_offset = %d', arc_offset)

        logger.flow(6, f'vuD08E change valley_ofs_th and execute media scan status expected')
        test_arc_offset_th = [arc_offset-1, arc_offset, arc_offset+1]
        for arc_offset_th in test_arc_offset_th:
            vu_D08E_param = micron_vu_D08E_param()
            vu_D08E_param.b20_valley_ofs_th_slc = arc_offset_th
            vu_D08E_param.w16_valley_center_ecth_slc = 0xFFFF
            vu_D08E_param.w18_valley_diffec_th_slc = 0xFFFF
            vu_D08E_param.b22_is_partial_block = 1 #0: is full block  1: is partial block
            vu_D08E_param.b23_is_em1 = 1 #0 is not EM1  1: is EM1
            resp = project_api.issue_D08E_to_change_media_scan_thresholds(vu_D08E_param)

            resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(vu_4028_param)
            arc_offset=abs(int.from_bytes(payload.arc_offset.value.to_bytes(), byteorder='big', signed=True))
            logger.info('arc_offset = %d', arc_offset)
            if arc_offset > arc_offset_th:
                if payload.media_scan_status.value != MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_BLOCK_FOLD_FOR_DIFFEC.value:
                    logger.error(f'expected media scan status is 7, but result is {payload.media_scan_status.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                if payload.media_scan_status.value != MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_BLOCK_UNFOLD_FOR_VALLEY_OFFSET_CENTER_EC.value:
                    logger.error(f'expected media scan status is 15, but result is {payload.media_scan_status.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
#=================================================================================================
        
        #verify vu change VALLEY_CENTER_EC_TH

#================================================================================================= 

        logger.flow(2, 'configure lun and write slc tlc one wl size')
        self.config_lun_and_write_slc_tlc_partition()
        
        param = micron_vu_D08E_param()
        param.b22_is_partial_block = 1 #0: is full block  1: is partial block
        param.b23_is_em1 = 1 #0 is not EM1  1: is EM1
        resp = project_api.issue_D08E_to_change_media_scan_thresholds(param)
        
        logger.flow(3, 'inject error bit cnt 150 to each 4k in a 16K ')
        for idx_of_4k in range(4): 
            self.flipbit_on_SLC(testlba=0, flipbit_set=150, index_4k=idx_of_4k)

        logger.flow(4, f'vu4028 trigger media scan vhc with slc block valid page0')
        _,micron_pca = issue_4051_to_get_physical_address(1, lba=0)
        vu_4028_param = micron_vu_4028_param()
        vu_4028_param.d16_die = micron_pca.die.value
        vu_4028_param.d20_plane = micron_pca.plane.value
        vu_4028_param.d24_block = micron_pca.virtual_block_number.value
        vu_4028_param.d28_page = 0
        vu_4028_param.b40_slc_mode = 1 #0: TLC 1:SLC
        vu_4028_param.b41_bfea_bin = 0
        vu_4028_param.b42_page_attr = 0 #page attr: 0--SLC   1--MLC_LP  2--MLC_UP 3--TLC_LP 4--TLC_UP   5--TLC_XP
        vu_4028_param.b43_is_blank_page = 0 #1： is blank page   0：is not blank page
        vu_4028_param.b44_is_partial_block = 1 #0: is full block  1: is partial block
        vu_4028_param.b45_is_em1_vb = 1 #0 is not EM1   1: is EM1

        resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(vu_4028_param)
        logger.info('status = %d', payload.media_scan_status.value)
        logger.info('bec = %d', payload.bec.value)
        logger.info('diff_ec = %d', payload.diff_ec.value)
        logger.info('arc_offset = %d', payload.arc_offset.value)
        logger.info('center_ec = %d', payload.center_ec.value)
        if payload.media_scan_status.value == MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_INVALID.value:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(5, f'get golden center_ec value')
        center_ec=payload.center_ec.value

        logger.flow(6, f'vuD08E change center_ec_th and execute media scan status expected')
        test_center_ec_th = [center_ec-1, center_ec, center_ec+1]
        for center_ec_th in test_center_ec_th:
            vu_D08E_param = micron_vu_D08E_param()
            vu_D08E_param.b20_valley_ofs_th_slc = 0xFF
            vu_D08E_param.w16_valley_center_ecth_slc = center_ec_th
            vu_D08E_param.w18_valley_diffec_th_slc = 0xFFFF
            vu_D08E_param.b22_is_partial_block = 1 #0: is full block  1: is partial block
            vu_D08E_param.b23_is_em1 = 1 #0 is not EM1  1: is EM1
            resp = project_api.issue_D08E_to_change_media_scan_thresholds(vu_D08E_param)

            resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(vu_4028_param)
            logger.info('status = %d', payload.media_scan_status.value)
            logger.info('bec = %d', payload.bec.value)
            logger.info('diff_ec = %d', payload.diff_ec.value)
            logger.info('arc_offset = %d', payload.arc_offset.value)
            logger.info('center_ec = %d', payload.center_ec.value)
            if payload.center_ec.value > center_ec_th:
                if payload.media_scan_status.value != MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_BLOCK_FOLD_FOR_DIFFEC.value:
                    logger.error(f'expected media scan status is 7, but result is {payload.media_scan_status.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                if payload.media_scan_status.value != MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_BLOCK_UNFOLD_FOR_VALLEY_OFFSET_CENTER_EC.value:
                    logger.error(f'expected media scan status is 15, but result is {payload.media_scan_status.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        

#=================================================================================================
        
        #verify vu change XTEMP_DELTA_TH

#================================================================================================= 

        logger.flow(2, 'configure lun and write slc tlc one wl size')
        self.config_lun_and_write_slc_tlc_partition()

        logger.flow(3, 'inject error bit cnt 150 to each 4k in a 16K ')
        for idx_of_4k in range(4): 
            self.flipbit_on_SLC(testlba=0, flipbit_set=150, index_4k=idx_of_4k)

        logger.flow(4, 'set nand temperature=20 ')
        ce_num = self.flash_setting.Max_Fdevice
        temp_gap = 37
        temp_set = 20
        temp_set_controller = 85
        set_nand_temp = SetNandTemperature()
        set_nand_temp.bEnableSetVuTemp.value = 1
        set_nand_temp.NAND_TEMPERATURE_DIE_0.value = temp_set
        set_nand_temp.UC_TERMAL_SENSOR_1.value = temp_set_controller
        if ce_num >= 2:
            set_nand_temp.NAND_TEMPERATURE_DIE_1.value = temp_set
        if ce_num >= 4:
            set_nand_temp.NAND_TEMPERATURE_DIE_2.value = temp_set
            set_nand_temp.NAND_TEMPERATURE_DIE_3.value = temp_set
        set_nand_temp.Use_Delayed_fake_tmeperatures.value = 0
        rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)
        logger.flow(4,"issue 4021 to get each nand temperature")
        rsp , GetNandTemperature = project_api.issue_4021_get_nand_temperature()
        if (temp_set + temp_gap) != GetNandTemperature.temperature_of_die_0.value:
            logger.error_fp(f'temperature ce0 compare fail')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(5, f'vu4028 trigger media scan vhc with slc block valid page0')
        _,micron_pca = issue_4051_to_get_physical_address(1, lba=0)
        vu_4028_param = micron_vu_4028_param()
        vu_4028_param.d16_die = micron_pca.die.value
        vu_4028_param.d20_plane = micron_pca.plane.value
        vu_4028_param.d24_block = micron_pca.virtual_block_number.value
        vu_4028_param.d28_page = 0
        vu_4028_param.b40_slc_mode = 1 #0: TLC 1:SLC
        vu_4028_param.b41_bfea_bin = 0
        vu_4028_param.b42_page_attr = 0 #page attr: 0--SLC   1--MLC_LP  2--MLC_UP 3--TLC_LP 4--TLC_UP   5--TLC_XP
        vu_4028_param.b43_is_blank_page = 0 #1： is blank page   0：is not blank page
        vu_4028_param.b44_is_partial_block = 1 #0: is full block  1: is partial block
        vu_4028_param.b45_is_em1_vb = 1 #0 is not EM1   1: is EM1
        resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(vu_4028_param)
        if payload.media_scan_status.value == MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_INVALID.value:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(6, f'vuD08E change xtemp_th_delta and execute media scan status expected')
        test_temp_th = [0x01, 0xFF] #min/max
        for temp_th in test_temp_th:
            vu_D08E_param = micron_vu_D08E_param()
            vu_D08E_param.b21_xtemp_th_delta_slc = temp_th
            vu_D08E_param.b22_is_partial_block = 1 #0: is full block  1: is partial block
            vu_D08E_param.b23_is_em1 = 1 #0 is not EM1  1: is EM1
            resp = project_api.issue_D08E_to_change_media_scan_thresholds(vu_D08E_param)

            resp, payload = project_api.issue_4028_to_get_media_scan_without_dm(vu_4028_param)
            logger.info('status = %d', payload.media_scan_status.value)
            logger.info('bec = %d', payload.bec.value)
            logger.info('diff_ec = %d', payload.diff_ec.value)
            logger.info('arc_offset = %d', payload.arc_offset.value)
            logger.info('center_ec = %d', payload.center_ec.value)
            if temp_th == 0xFF:
                if payload.media_scan_status.value != MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_BLOCK_FOLD_FOR_DIFFEC.value:
                    logger.error(f'expected media scan status is 7, but result is {payload.media_scan_status.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                if payload.media_scan_status.value != MEDIA_SCAN_STATUS.BE_STATUS_MEDIA_SCAN_BLOCK_FOLD_FOR_TEMP.value:
                    logger.error(f'expected media scan status is 8, but result is {payload.media_scan_status.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL   
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
        
    def flipbit_on_SLC(self, testlba:int=0, flipbit_set:int=0, index_4k:int=0)->None:

        logger.flow(1, f'GET Open vb information by VU 0x40C1')
        get_open_vb = get_and_print_open_vb_information()
        isSLC = 1
        logger.flow(2, f'GET LUN {self.TestEM1Lun}，LBA {testlba} physical address by VU 0x4051')
        _,micron_pca = issue_4051_to_get_physical_address(self.TestEM1Lun, testlba)

        logger.flow(3, f'VU 4060 read raw data on LBA {testlba} with ECC on')
        _, raw_data = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=1, Scrambler_Enable=1)
        dumpfile(f"direct_read_data_idx1.bin", raw_data)
        logger.flow(4, f'Issue 409E VUC with ECC information = 1 to get error bit numbers')
        _, output_409E = issue_409E_to_get_error_bit_numbers()
        error_bits_409E = [output_409E.errorBitNumber1.value, output_409E.errorBitNumber2.value, output_409E.errorBitNumber3.value, output_409E.errorBitNumber4.value]
        logger.info(f'409E error bits ={error_bits_409E}')
        logger.flow(5, f'Issue D0FD VUC disable BKOPS')
        project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x00)
        logger.flow(6, f'VU 4060 read raw data on LBA {testlba} with ECC Off')
        _, raw_dataLP = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0)
        raw_dataLP_1 = copy.deepcopy(raw_dataLP)
        dumpfile(f"pageLP.bin", raw_dataLP)
        #LP_fwrite = rebuild_payload_mv(raw_data)
        LP_fwrite = raw_dataLP
        raw_data_flip = LP_fwrite #ecc off
        
        diffcount = count_diff_bytes(raw_dataLP, raw_data_flip)
        logger.info(f'step 6: LP different count ={diffcount}')
        #flipped = flip_bits(raw_data_flip)                # 直接使用預設 start_bit=0, count=500
        flipbit = flipbit_set
        logger.flow(7, f'Flip bits = {flipbit} on raw data')
        flipped = flip_bits_one_per_byte(raw_data_flip, total_bits=flipbit, block_index=index_4k) 
        diffcount = count_diff_bytes(raw_dataLP_1, raw_data_flip)
        logger.info(f'LP different count ={diffcount} after flip bits {flipbit}')
        print_bit_positions(flipped, title=f"{flipbit} bits position")
        logger.info(f"Flip first {flipbit} bits – done")
        logger.info(f"raw_data_flip = {len(raw_data_flip)}") 
        write_payload = build_write_payload20K(raw_data_flip)[:18352]
        print(len(write_payload))
        #erase
        die = 1 << micron_pca.die.value
        plane = 1 << micron_pca.plane.value
        #rsp, payload = issue_40F6_to_erase_in_direct_nand_mode(die, plane, micron_pca.virtual_block_number.value, micron_pca.virtual_block_number.value+1,slc_enable=0)   
        logger.flow(3, 'issue D060 to erase original data')
        project_api.issue_D060_to_erase_specific_block(Ce=micron_pca.die.value,Plane=micron_pca.plane.value,Block=micron_pca.virtual_block_number.value,SlcEnable=1,psaEnable=0)
            
        #write raw data
        dumpfile(f"FLIP_Write.bin", write_payload)
        _ = project_api.issue_C060_to_write_raw_data(Ce=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC,Ecc_Enable=0, datapayload=write_payload)
        
        #read raw data
        _, raw_data_1 = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=1, Scrambler_Enable=1)
        raw_data_11 = copy.deepcopy(raw_data_1)
        diffcount = count_diff_bytes(raw_dataLP, raw_data_11)
        logger.info(f'LP different count ={diffcount}')
        dumpfile(f"FW_FLOW_READ.bin", raw_data_11)
        logger.flow(13, f'Issue 409E VUC with ECC information = 1 to get error bit numbers')
        _, output_409E = issue_409E_to_get_error_bit_numbers()
        error_bits_409E = [output_409E.errorBitNumber1.value, output_409E.errorBitNumber2.value, output_409E.errorBitNumber3.value, output_409E.errorBitNumber4.value]
        logger.info(f'409E error bits ={error_bits_409E}')

        _, raw_dataLP_after = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0)
        raw_dataLP_after_1 = copy.deepcopy(raw_dataLP_after)
        dumpfile(f"pageLP_after.bin", raw_dataLP_after_1)
        diffcount = count_diff_bytes(raw_dataLP_1, raw_dataLP_after_1)
        logger.info(f'LP different count ={diffcount}')
        
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

run = Pattern().run
if __name__ == "__main__":
    run()