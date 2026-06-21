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
    def print_object_info_ai(self, object: Any) -> None:
        logger.info(f'================= [{object.__class__.__name__}]=================')
        fields = [
            (name, field) for name, field in object.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        fields.sort(key=lambda kv: kv[1].start_offset)
        for name, field in fields:
            logger.info(
                f'Byte[{field.start_offset}:{field.end_offset}]: {name} = {field.value}'
            )
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
        #VC1
        logger.flow(1, 'Get BBT info from VU 0x4097 as table1')
        self.bbt_sub_vb_info = project_api.get_BBT_physical_block_information()
        print_object_info_ai(self.bbt_sub_vb_info)
        direc_read_pca = PCA()
        direc_read_pca.b10_block_l = self.bbt_sub_vb_info.Block.value
        direc_read_pca.b5_ce = self.bbt_sub_vb_info.CE.value
        direc_read_pca.b6_plane = self.bbt_sub_vb_info.plane.value

        # BBT address A
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=int(tlc_ce_page), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                         need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.sequential_write(lun=1, start_lba=0, total_size=int(slc_ce_page), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                         need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
         
        reset_type = api.Dcmd5ResetType.HW_RESET
        logger.flow(2, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        
        #logger.flow(3, 'VU 40C6 get single open vb info on BBT')
        logger.flow(3, 'Get BBT info from VU 0x4097  as table2')
        self.bbt_sub_vb_info_after = project_api.get_BBT_physical_block_information()
        print_object_info_ai(self.bbt_sub_vb_info_after)
        direc_read_pca_after = PCA()
        direc_read_pca_after.b10_block_l = self.bbt_sub_vb_info_after.Block.value
        direc_read_pca_after.b5_ce = self.bbt_sub_vb_info_after.CE.value
        direc_read_pca_after.b6_plane = self.bbt_sub_vb_info_after.plane.value
        
        logger.flow(4, 'compare table1 should same as table2')
        if not self.compare_pca_info(direc_read_pca_after, direc_read_pca):
            logger.error_lb(f'check BBT pca should not change after SPOR')
            logger.error_fp(f'expect BBT pca not change, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        # BBT address B
        # BBT A should equal to B
        #VC2
        logger.flow(5, 'inject UECC on BBT page0')
        inject_UECC(direc_read_pca_after)

        logger.flow(6, f'HW reset without SSU')
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=int(tlc_ce_page), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                         need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.sequential_write(lun=1, start_lba=0, total_size=int(slc_ce_page), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                         need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        logger.flow(7, 'Get BBT info from VU 0x4097 as table3')
        self.bbt_sub_vb_info_after = project_api.get_BBT_physical_block_information()
        print_object_info_ai(self.bbt_sub_vb_info_after)
        direc_read_pca_after3 = PCA()
        direc_read_pca_after3.b10_block_l = self.bbt_sub_vb_info_after.Block.value
        direc_read_pca_after3.b5_ce = self.bbt_sub_vb_info_after.CE.value
        direc_read_pca_after3.b6_plane = self.bbt_sub_vb_info_after.plane.value
        logger.flow(8, 'compare table2 should different with table3')
        if self.compare_pca_info(direc_read_pca_after3, direc_read_pca_after):
            logger.error_lb(f'Inject UECC on BBT page0')
            logger.error_fp(f'expect BBT pca refresh, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #VC4
        direc_read_pca_after4 = PCA()
        direc_read_pca_after4 = copy.deepcopy(direc_read_pca_after3)
        direc_read_pca_after4.l12_fpage = 1<<5
        logger.flow(9, 'inject UECC on BBT page1')
        inject_UECC(direc_read_pca_after4)

        logger.flow(10, f'HW reset without SSU')
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=int(tlc_ce_page), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                         need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.sequential_write(lun=1, start_lba=0, total_size=int(slc_ce_page), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                         need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        logger.flow(11, 'Get BBT info from VU 0x4097 as table4')
        self.bbt_sub_vb_info_after = project_api.get_BBT_physical_block_information()
        print_object_info_ai(self.bbt_sub_vb_info_after)
        direc_read_pca_after5 = PCA()
        direc_read_pca_after5.b10_block_l = self.bbt_sub_vb_info_after.Block.value
        direc_read_pca_after5.b5_ce = self.bbt_sub_vb_info_after.CE.value
        direc_read_pca_after5.b6_plane = self.bbt_sub_vb_info_after.plane.value
        logger.flow(12, 'compare table3 should different with table4')
        if self.compare_pca_info(direc_read_pca_after4, direc_read_pca_after5):
            logger.error_lb(f'Inject UECC on BBT page1')
            logger.error_fp(f'expect BBT pca refresh, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #VC5
        direc_read_pca_after6 = PCA()
        direc_read_pca_after6 = copy.deepcopy(direc_read_pca_after5)
        logger.flow(13, 'inject UECC on BBT page0')
        inject_UECC(direc_read_pca_after6)
        direc_read_pca_after6.l12_fpage = 1<<5
        logger.flow(14, 'inject UECC on BBT page1')
        inject_UECC(direc_read_pca_after6)
        
        logger.flow(15, f'HW reset without SSU, expect init fail')
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=int(tlc_ce_page), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                         need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.sequential_write(lun=1, start_lba=0, total_size=int(slc_ce_page), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                         need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
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

        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()