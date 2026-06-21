import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.ufs_api.defines.enum_define import QueryResponseCode
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api import shared
from Script.lib import sdk_lib as lib
import random

from Script.api.ufs_api import *
from Script.api.exception import *
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from typing import cast
from Script.project_api.functions import print_object_info_ai
from Script.pattern.apl_system_rebuild.mutual_fun import *
import copy
#_sdk = shared.sdk
_param = shared.param

class Pattern(UFSTC):
    def compare_pca_info(self, first_pca: PCA, second_pca: PCA) -> bool:
        #phison_ppage = self.wl_page_2_physical_page(phison_pca.b4_mode.value, phison_pca.w46_page.value, phison_pca.b20_lmu.value)
        #phison_offset = int((phison_pca.l12_fpage.value - phison_pca.w46_page.value *32) /8)
        if not (first_pca.b10_block_l == second_pca.b10_block_l and \
                first_pca.b6_plane == second_pca.b6_plane and \
                first_pca.b5_ce == second_pca.b5_ce and \
                first_pca.b11_block_h == second_pca.b11_block_h) :
            return False
        return True
        
    def pre_process(self) -> None:
        self.disableMDWLSV = 1
        self.EnableMDWLSV = 0
        self.write_record = api.get_empty_write_record()
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting = api.get_flash_setting()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestBootA = 1
        self.TestBootB = 2
        self.TestEM1Lun = 3
        self.Total_AU_Count = self.geometry_desc.q4_total_raw_device_capacity / (self.geometry_desc.l13_segment_size * self.geometry_desc.b17_allocation_unit_size);
        


    def step1(self) -> None:
        
        ce_num = self.flash_setting.Max_Fdevice
        plane_num = self.flash_setting.Plane_Per_Die
        ce_plane_num = ce_num * plane_num
        tlc_ce_page = self.flash_setting.Plane_Per_Die * 4 * 3
        tlc_pageline = tlc_ce_page * ce_num
        slc_ce_page = self.flash_setting.Plane_Per_Die * 4
        logger.flow(1, f'GET Open vb information by VU 0x40C1 as table1')
        get_open_vb = get_and_print_open_vb_information()
        open_vb_1: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
        direc_read_pca = PCA()
        direc_read_pca.b10_block_l = open_vb_1.INDEX_VB_number_logical.value & 0xFF
        direc_read_pca.b11_block_h = (open_vb_1.INDEX_VB_number_logical.value >> 8) & 0xFF
        direc_read_pca.b5_ce = ((open_vb_1.INDEX_block_First_free_physical_page.value - 1)  % ce_plane_num) // plane_num
        direc_read_pca.b6_plane = ((open_vb_1.INDEX_block_First_free_physical_page.value - 1)  % ce_plane_num) % plane_num
        direc_read_pca.l12_fpage = ((open_vb_1.INDEX_block_First_free_physical_page.value - 1) // ce_plane_num) << 5
        logger.flow(2, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        
        logger.flow(3, f'GET Open vb information by VU 0x40C1 as table2')
        get_open_vb = get_and_print_open_vb_information()
        open_vb_2: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
        direc_read_pca_2 = PCA()
        direc_read_pca_2.b10_block_l = open_vb_2.INDEX_VB_number_logical.value & 0xFF
        direc_read_pca_2.b11_block_h = (open_vb_2.INDEX_VB_number_logical.value >> 8) & 0xFF
        direc_read_pca_2.b5_ce = ((open_vb_2.INDEX_block_First_free_physical_page.value - 1)  % ce_plane_num) // plane_num
        direc_read_pca_2.b6_plane = ((open_vb_2.INDEX_block_First_free_physical_page.value - 1)  % ce_plane_num) % plane_num
        direc_read_pca_2.l12_fpage = ((open_vb_2.INDEX_block_First_free_physical_page.value - 1) // ce_plane_num) << 5
        logger.flow(4, 'compare table2 should same with table1')
        if not self.compare_pca_info(direc_read_pca_2, direc_read_pca):
            logger.error_lb(f'Without UECC ')
            logger.error_fp(f'expect Index not refresh, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #VC4
        logger.flow(5, 'inject UECC on Index Mirror page LWP')
        ics_bad_block = project_api.get_ics_bad_block()
        if ics_bad_block.ICSBadBlocks[open_vb_2.INDEX_VB_number_logical.value].VB_index.value == open_vb_2.INDEX_VB_number_logical.value:
                index_ics_plane = ics_bad_block.ICSBadBlocks[open_vb_2.INDEX_VB_number_logical.value].invalid_VB_plane.value
                logger.info(f'index_ics_plane : {index_ics_plane}')
        if index_ics_plane != direc_read_pca_2.b5_ce * 6 + direc_read_pca_2.b6_plane:
            inject_UECC(direc_read_pca_2)
        else:
            direc_read_pca_2.b5_ce = ((open_vb_2.INDEX_block_First_free_physical_page.value - 2)  % ce_plane_num) // plane_num
            direc_read_pca_2.b6_plane = ((open_vb_2.INDEX_block_First_free_physical_page.value - 2)  % ce_plane_num) % plane_num
            direc_read_pca_2.l12_fpage = ((open_vb_2.INDEX_block_First_free_physical_page.value - 2) // ce_plane_num) << 5
            inject_UECC(direc_read_pca_2)
        logger.flow(6, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        logger.flow(7, f'GET Open vb information by VU 0x40C1 as table3')
        get_open_vb = get_and_print_open_vb_information()
        open_vb_3: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
        direc_read_pca_3 = PCA()
        direc_read_pca_3.b10_block_l = open_vb_3.INDEX_VB_number_logical.value & 0xFF
        direc_read_pca_3.b11_block_h = (open_vb_3.INDEX_VB_number_logical.value >> 8) & 0xFF
        direc_read_pca_3.b5_ce = ((open_vb_3.INDEX_block_First_free_physical_page.value - 1)  % ce_plane_num) // plane_num
        direc_read_pca_3.b6_plane = ((open_vb_3.INDEX_block_First_free_physical_page.value - 1)  % ce_plane_num) % plane_num
        direc_read_pca_3.l12_fpage = ((open_vb_3.INDEX_block_First_free_physical_page.value - 1) // ce_plane_num) << 5
        logger.flow(8, 'compare table2 should different with table3')
        if self.compare_pca_info(direc_read_pca_2, direc_read_pca_3):
            logger.error_lb(f'inject UECC on Index Mirror page LWP and SPOR ')
            logger.error_fp(f'expect Index refresh, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #VC2
        logger.flow(8-1, 'check Index 9: ICS bad block')
        self.ics_bad_block = project_api.get_ics_bad_block()
        logger.flow(9, 'inject UECC on Index Major page LWP-1')
        direc_read_pca_4 = PCA()
        loop = 1
        cnt = 1

        while True:
            direc_read_pca_4.b10_block_l = open_vb_3.INDEX_VB_number_logical.value & 0xFF
            direc_read_pca_4.b11_block_h = (open_vb_3.INDEX_VB_number_logical.value >> 8) & 0xFF
            # direc_read_pca_4.b5_ce = ((open_vb_3.INDEX_block_First_free_physical_page.value - 2)  % ce_plane_num) // plane_num
            # direc_read_pca_4.b6_plane = ((open_vb_3.INDEX_block_First_free_physical_page.value - 2)  % ce_plane_num) % plane_num
            # direc_read_pca_4.l12_fpage = ((open_vb_3.INDEX_block_First_free_physical_page.value - 2) // ce_plane_num) << 5
            direc_read_pca_4.b5_ce = ((open_vb_3.INDEX_block_First_free_physical_page.value - cnt)  % ce_plane_num) // plane_num
            direc_read_pca_4.b6_plane = ((open_vb_3.INDEX_block_First_free_physical_page.value - cnt)  % ce_plane_num) % plane_num
            direc_read_pca_4.l12_fpage = ((open_vb_3.INDEX_block_First_free_physical_page.value - cnt) // ce_plane_num) << 5
            if self.ics_bad_block.ICSBadBlocks[open_vb_3.INDEX_VB_number_logical.value].VB_index.value == open_vb_3.INDEX_VB_number_logical.value:
                index_ics_plane = self.ics_bad_block.ICSBadBlocks[open_vb_3.INDEX_VB_number_logical.value].invalid_VB_plane.value
                logger.info(f'index_ics_plane : {index_ics_plane}')
            if index_ics_plane != direc_read_pca_4.b5_ce * 6 + direc_read_pca_4.b6_plane :
                loop = loop+1
                if loop == 3:
                    inject_UECC(direc_read_pca_4)
                    break
            cnt = cnt+1
        
        logger.flow(10, f'HW reset without SSU')
        # api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        status = True
        #api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        try:
            api.init_tester_to_unit_ready(
                resetmode=api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET),
                powerdown=False,
            )
        except Exception as e:                     # 若有特定例外類別，可改成 api.APIError
            # 錯誤處理：印出訊息、寫 log、或設定旗標等
            print(f"[ERROR] init_tester_to_unit_ready failed: {e}")
            assertnum = api.get_fw_assert_number()
            status = False
            
        finally:
            status = status
            # api.MP().execute()
            # api.first_init_to_max_hs_gear(link_startup_mode=_param.current_speed.link_startup_mode, ref_clk=_param.current_speed.refclk)
        if status == False:
            logger.error_lb(f'Inject UECC on Index Major')
            logger.error_fp(f'expect init PASS, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.flow(11, f'GET Open vb information by VU 0x40C1 as table4')
        get_open_vb = get_and_print_open_vb_information()
        open_vb_5: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
        direc_read_pca_5 = PCA()
        direc_read_pca_5.b10_block_l = open_vb_5.INDEX_VB_number_logical.value & 0xFF
        direc_read_pca_5.b11_block_h = (open_vb_5.INDEX_VB_number_logical.value >> 8) & 0xFF
        direc_read_pca_5.b5_ce = ((open_vb_5.INDEX_block_First_free_physical_page.value - 1)  % ce_plane_num) // plane_num
        direc_read_pca_5.b6_plane = ((open_vb_5.INDEX_block_First_free_physical_page.value - 1)  % ce_plane_num) % plane_num
        direc_read_pca_5.l12_fpage = ((open_vb_5.INDEX_block_First_free_physical_page.value - 1) // ce_plane_num) << 5
        logger.flow(12, 'compare table3 should different with table4')
        if self.compare_pca_info(direc_read_pca_4, direc_read_pca_5):
            logger.error_lb(f'inject UECC on Index Mirror page LWP and SPOR ')
            logger.error_fp(f'expect Index refresh, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #VC5 VC6 VC7
        for i in range(3):
            #logger.flow(13, f'GET Open vb information by VU 0x40C1 as table5')
            logger.flow(13, 'check Index 9: ICS bad block')
            self.ics_bad_block = project_api.get_ics_bad_block()
            get_open_vb = get_and_print_open_vb_information()
            open_vb_6: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
            direc_read_pca_6 = PCA()
            direc_read_pca_7 = PCA()
            direc_read_pca_8 = PCA()
            index_ics_plane = 0xFF
            while open_vb_6.INDEX_block_First_free_physical_page.value <= (i*2+3):
                for vb in range(self.fw_geometry.l52_total_vb_count):
                    if self.ics_bad_block.ICSBadBlocks[vb].VB_index.value == open_vb_6.INDEX_VB_number_logical.value:
                        index_ics_plane = self.ics_bad_block.ICSBadBlocks[vb].invalid_VB_plane.value
                        logger.info(f'index_ics_plane : {index_ics_plane}')
                        break
                direc_read_pca_6.b10_block_l = open_vb_6.List_Block_VB_number_logical.value & 0xFF
                direc_read_pca_6.b11_block_h = (open_vb_6.List_Block_VB_number_logical.value >> 8) & 0xFF
                direc_read_pca_6.b5_ce = ((open_vb_6.List_block_First_free_physical_page.value - random.randint(1, 2))  % ce_plane_num) // plane_num
                direc_read_pca_6.b6_plane = ((open_vb_6.List_block_First_free_physical_page.value - random.randint(1, 2))  % ce_plane_num) % plane_num
                direc_read_pca_6.l12_fpage = ((open_vb_6.List_block_First_free_physical_page.value - random.randint(1, 2)) // ce_plane_num) << 5
                
                logger.flow(14, 'inject UECC on List Mirror page LWP')
                if index_ics_plane != direc_read_pca_6.b5_ce * 6 + direc_read_pca_6.b6_plane:
                    inject_UECC(direc_read_pca_6)
                logger.flow(15, f'HW reset without SSU')
                api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
                get_open_vb = get_and_print_open_vb_information()
                open_vb_6 = project_api.OpenVBInformation(get_open_vb.payload.copy())
            neg = 0
            while True:
                neg = neg +1
                logger.flow(16, f'GET Open vb information by VU 0x40C1 as table5')
                direc_read_pca_6.b10_block_l = open_vb_6.INDEX_VB_number_logical.value & 0xFF
                direc_read_pca_6.b11_block_h = (open_vb_6.INDEX_VB_number_logical.value >> 8) & 0xFF
                direc_read_pca_6.b5_ce = ((open_vb_6.INDEX_block_First_free_physical_page.value - neg)  % ce_plane_num) // plane_num
                direc_read_pca_6.b6_plane = ((open_vb_6.INDEX_block_First_free_physical_page.value - neg)  % ce_plane_num) % plane_num
                direc_read_pca_6.l12_fpage = ((open_vb_6.INDEX_block_First_free_physical_page.value - neg) // ce_plane_num) << 5
                
                logger.flow(17, 'inject UECC on Index Mirror page LWP')
                
                if self.ics_bad_block.ICSBadBlocks[open_vb_6.INDEX_VB_number_logical.value].VB_index.value == open_vb_6.INDEX_VB_number_logical.value:
                    index_ics_plane = self.ics_bad_block.ICSBadBlocks[open_vb_6.INDEX_VB_number_logical.value].invalid_VB_plane.value
                    logger.info(f'index_ics_plane : {index_ics_plane}')
                if index_ics_plane != direc_read_pca_6.b5_ce * 6 + direc_read_pca_6.b6_plane:
                    inject_UECC(direc_read_pca_6)
                    break
            while True:
                neg = neg +1
                direc_read_pca_7.b10_block_l = open_vb_6.INDEX_VB_number_logical.value & 0xFF
                direc_read_pca_7.b11_block_h = (open_vb_6.INDEX_VB_number_logical.value >> 8) & 0xFF
                direc_read_pca_7.b5_ce = ((open_vb_6.INDEX_block_First_free_physical_page.value - neg)  % ce_plane_num) // plane_num
                direc_read_pca_7.b6_plane = ((open_vb_6.INDEX_block_First_free_physical_page.value - neg)  % ce_plane_num) % plane_num
                direc_read_pca_7.l12_fpage = ((open_vb_6.INDEX_block_First_free_physical_page.value - neg) // ce_plane_num) << 5
                
                if self.ics_bad_block.ICSBadBlocks[open_vb_6.INDEX_VB_number_logical.value].VB_index.value == open_vb_6.INDEX_VB_number_logical.value:
                    index_ics_plane = self.ics_bad_block.ICSBadBlocks[open_vb_6.INDEX_VB_number_logical.value].invalid_VB_plane.value
                    logger.info(f'index_ics_plane : {index_ics_plane}')
                
                if index_ics_plane != direc_read_pca_7.b5_ce * 6 + direc_read_pca_7.b6_plane:
                    logger.flow(18, 'inject UECC on Index Major page LWP-1')
                    inject_UECC(direc_read_pca_7)
                    break
            N = neg +1
            if i == 1 or i == 2:
                while True:
                    direc_read_pca_8.b10_block_l = open_vb_6.INDEX_VB_number_logical.value & 0xFF
                    direc_read_pca_8.b11_block_h = (open_vb_6.INDEX_VB_number_logical.value >> 8) & 0xFF
                    direc_read_pca_8.b5_ce = ((open_vb_6.INDEX_block_First_free_physical_page.value - N)  % ce_plane_num) // plane_num
                    direc_read_pca_8.b6_plane = ((open_vb_6.INDEX_block_First_free_physical_page.value - N)  % ce_plane_num) % plane_num
                    direc_read_pca_8.l12_fpage = ((open_vb_6.INDEX_block_First_free_physical_page.value - N) // ce_plane_num) << 5
                    
                    if self.ics_bad_block.ICSBadBlocks[open_vb_6.INDEX_VB_number_logical.value].VB_index.value == open_vb_6.INDEX_VB_number_logical.value:
                        index_ics_plane = self.ics_bad_block.ICSBadBlocks[open_vb_6.INDEX_VB_number_logical.value].invalid_VB_plane.value
                        logger.info(f'index_ics_plane : {index_ics_plane}')
                    
                    if i == 1:
                        if index_ics_plane > 1:
                            if direc_read_pca_8.l12_fpage == 0 and direc_read_pca_8.b5_ce == 0 and direc_read_pca_8.b6_plane == 1:
                                break
                        else:
                            if direc_read_pca_8.l12_fpage == 0 and direc_read_pca_8.b5_ce == 0 and direc_read_pca_8.b6_plane == 2:
                                break
                    else:
                        #if open_vb_6.INDEX_block_First_free_physical_page.value - N == 1:
                        
                        if index_ics_plane > 0:
                            if direc_read_pca_8.l12_fpage == 0 and direc_read_pca_8.b5_ce == 0 and direc_read_pca_8.b6_plane == 0:
                                break
                        else:
                            if direc_read_pca_8.l12_fpage == 0 and direc_read_pca_8.b5_ce == 0 and direc_read_pca_8.b6_plane == 1:
                                break
                    logger.flow(18-1, f'inject UECC on Index Major page LWP-{N-1}')
                    if index_ics_plane != direc_read_pca_8.b5_ce * 6 + direc_read_pca_8.b6_plane:
                        inject_UECC(direc_read_pca_8)
                    N = N+1
            
            logger.flow(19, f'HW reset without SSU')
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
            logger.flow(20, f'GET Open vb information by VU 0x40C1 as table6')
            get_open_vb = get_and_print_open_vb_information()
            open_vb_7: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
            direc_read_pca_9 = PCA()
            direc_read_pca_9.b10_block_l = open_vb_7.INDEX_VB_number_logical.value & 0xFF
            direc_read_pca_9.b11_block_h = (open_vb_7.INDEX_VB_number_logical.value >> 8) & 0xFF
            direc_read_pca_9.b5_ce = ((open_vb_7.INDEX_block_First_free_physical_page.value - 1)  % ce_plane_num) // plane_num
            direc_read_pca_9.b6_plane = ((open_vb_7.INDEX_block_First_free_physical_page.value - 1)  % ce_plane_num) % plane_num
            direc_read_pca_9.l12_fpage = ((open_vb_7.INDEX_block_First_free_physical_page.value - 1) // ce_plane_num) << 5
            logger.flow(21, 'compare table6 should different with table5')
            if self.compare_pca_info(direc_read_pca_9, direc_read_pca_6):
                logger.error_lb(f'inject UECC on Index Mirror page LWP and Major page LWP-1 and SPOR ')
                logger.error_fp(f'expect Index refresh, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #VC8
        logger.flow(22, 'inject UECC on Index all page, check Index 9: ICS bad block')
        direc_read_pca_10 = PCA()
        self.ics_bad_block = project_api.get_ics_bad_block()
        if self.ics_bad_block.ICSBadBlocks[open_vb_7.INDEX_VB_number_logical.value].VB_index.value == open_vb_7.INDEX_VB_number_logical.value:
                index_ics_plane = self.ics_bad_block.ICSBadBlocks[open_vb_7.INDEX_VB_number_logical.value].invalid_VB_plane.value
                logger.info(f'index_ics_plane : {index_ics_plane}')
        M=1
        while True:
            direc_read_pca_10.b10_block_l = open_vb_7.INDEX_VB_number_logical.value & 0xFF
            direc_read_pca_10.b11_block_h = (open_vb_7.INDEX_VB_number_logical.value >> 8) & 0xFF
            direc_read_pca_10.b5_ce = ((open_vb_7.INDEX_block_First_free_physical_page.value - M)  % ce_plane_num) // plane_num
            direc_read_pca_10.b6_plane = ((open_vb_7.INDEX_block_First_free_physical_page.value - M)  % ce_plane_num) % plane_num
            direc_read_pca_10.l12_fpage = ((open_vb_7.INDEX_block_First_free_physical_page.value - M) // ce_plane_num) << 5
        
            if index_ics_plane != direc_read_pca_10.b5_ce * 6 + direc_read_pca_10.b6_plane:
                logger.flow(23, f'inject UECC on Index page LWP-{M-1}')
                inject_UECC(direc_read_pca_10)
            if direc_read_pca_10.b5_ce == 0 and direc_read_pca_10.b6_plane == 0 and direc_read_pca_10.l12_fpage == 0:
                break
            M = M+1
        logger.flow(24, f'HW reset without SSU')
        status = True
        #api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        try:
            # 這裡預期會失敗
            api.init_tester_to_unit_ready(
                resetmode=api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET),
                powerdown=False,
            )
        except Exception as e:                     # 若有特定例外類別，可改成 api.APIError
            # 錯誤處理：印出訊息、寫 log、或設定旗標等
            print(f"[ERROR] init_tester_to_unit_ready failed: {e}")
            assertnum = api.get_fw_assert_number()

        else:
            logger.error_lb(f'Inject UECC on BBT page0 and page1')
            logger.error_fp(f'expect init fail, result Fail!')
            status = False
        finally:
            api.MP().execute()
            api.first_init_to_max_hs_gear(link_startup_mode=_param.current_speed.link_startup_mode, ref_clk=_param.current_speed.refclk)
        if status == False:
            logger.error_lb(f'Inject UECC on BBT page0 and page1')
            logger.error_fp(f'expect init fail, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        # direc_read_pca_Log = PCA()
        # direc_read_pca_Log.b10_block_l = open_vb_1.LOG_block_VB_number_logical.value & 0xFF
        # direc_read_pca_Log.b11_block_h = (open_vb_1.LOG_block_VB_number_logical.value >> 8) & 0xFF
        # direc_read_pca_Log.b5_ce = ((open_vb_1.LOG_Block_First_free_physical_page.value - 1)  % ce_plane_num) // plane_num
        # direc_read_pca_Log.b6_plane = ((open_vb_1.LOG_Block_First_free_physical_page.value - 1)  % ce_plane_num) % plane_num
        # direc_read_pca_Log.l12_fpage = (open_vb_1.LOG_Block_First_free_physical_page.value - 1) // ce_plane_num
        # _, open_vb_info = get_open_vb_info()
        # print_open_vb_information_phison(open_vb_info)
        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()