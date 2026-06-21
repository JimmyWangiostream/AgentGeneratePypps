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
class open_block_type_list(IntEnum):
    DM_NORMAL_HOST_VB = 0
    DM_NORMAL_DEFRAG_VB = 1
    PTE = 4
    Refresh_VB = 6
    DM_RPMB_HOST_VB = 7
    RPMB_DEFRAG = 8
    DM_NORMAL_SHARE_VB_1 = 9
    DM_NORMAL_WB_VB_0 = 10
    DM_RAIN_PARITY_VB = 11
    TMP_RAIN = 13
    Drive_Log = 14
    Pointer_to_Index_block = 15
    BBT = 16
    DM_NORMAL_SHARE_VB_0 = 17
    DM_EM1_DEFRAG_VB = 18
    List = 19
    LOG = 20
    Index = 21
    MAIN_ISP = 22
    TMP_ISP = 23

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
        show_pca(first_pca)
        show_pca(second_pca)
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
        #VC1
        pattern_status = True
        logger.flow(1, 'Get ISP1 ISP2 info from VU 0x4097 as table1')
        self.fw_code_physical_address = project_api.get_FW_code_physical_address_information()
        
        pca_isp1 = PCA()
        pca_isp2 = PCA()
        pca_isp1, pca_isp2 = get_isp_pca()
        #logger.flow(2, f'Issue VU 0x40C6 get temp isp vb')
        # tempisp_subinfo = project_api.get_TEMP_ISP_physical_block_information()
        # print_object_info_ai(tempisp_subinfo)       
        logger.flow(2, f'Issue VU 0x4097 get temp isp vb') 
        tempcode_vb = get_temp_code_vb()

        logger.flow(3, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        
        logger.flow(4, 'Get ISP1 ISP2 info from VU 0x4097 as table2')
        pca_isp1_after = PCA()
        pca_isp2_after = PCA()
        pca_isp1_after, pca_isp2_after = get_isp_pca()
        logger.flow(5, 'compare table1 should same as table2, temp isp should same')
        if not self.compare_pca_info(pca_isp1, pca_isp1_after):
            logger.error_lb(f'check ISP1 pca should not change after SPOR')
            logger.error_fp(f'expect ISP1 pca not change, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if not self.compare_pca_info(pca_isp2, pca_isp2_after):
            logger.error_lb(f'check ISP2 pca should not change after SPOR')
            logger.error_fp(f'expect ISP2 pca not change, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        #logger.flow('5-1', f'Issue VU 0x40C6 get temp isp vb')
        # tempisp_subinfo_after = project_api.get_TEMP_ISP_physical_block_information()
        # print_object_info_ai(tempisp_subinfo_after)
        # if tempisp_subinfo.logicalvb.value != tempisp_subinfo_after.logicalvb.value:
        #     logger.error_lb(f'check TEMP ISP vb should not change after SPOR')
        #     logger.error_fp(f'expect TEMP ISP vb not change,but {tempisp_subinfo.logicalvb.value} -> {tempisp_subinfo_after.logicalvb.value} result Fail!')
        #     raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow('5-1', f'Issue VU 0x4097 get temp isp vb')
        tempcode_vb_after = get_temp_code_vb()
        if tempcode_vb != tempcode_vb_after:
            logger.error_lb(f'check TEMP ISP vb should not change after SPOR')
            logger.error_fp(f'expect TEMP ISP vb not change,but {tempcode_vb} -> {tempcode_vb_after} result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(6, f'Inject UECC on ISP1')
        
        inject_UECC(pca_isp1)
        logger.flow(7, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        pca_isp1_origin = pca_isp1_after
        pca_isp2_origin = pca_isp2_after
        logger.flow(8, 'Get ISP1 ISP2 info from VU 0x4097 as table3')
        pca_isp1_after = PCA()
        pca_isp2_after = PCA()
        pca_isp1_after, pca_isp2_after = get_isp_pca()
        logger.flow(9, 'compare table3 should different with table2(table3 ISP1 = table2 ISP2, table3 ISP change), temp isp should same')
        if not self.compare_pca_info(pca_isp2_origin, pca_isp1_after):
            logger.error_lb(f'check ISP1  pca should change after SPOR and will be the origin ISP2 pca')
            logger.error_fp(f'expect ISP1 pca change, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if self.compare_pca_info(pca_isp1_origin, pca_isp2_after) or self.compare_pca_info(pca_isp2_origin, pca_isp2_after) :
            logger.error_lb(f'check ISP2 pca should change after SPOR')
            logger.error_fp(f'expect ISP2 pca change, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        # if self.compare_pca_info(pca_isp1_origin, pca_isp1_after):
        #     logger.error_lb(f'check ISP1  pca should change after SPOR')
        #     logger.error_fp(f'expect ISP1 pca change, result Fail!')
        #     raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        # if not self.compare_pca_info(pca_isp2_origin, pca_isp2_after):
        #     logger.error_lb(f'check ISP2 pca should not change after SPOR')
        #     logger.error_fp(f'expect ISP2 pca not change, result Fail!')
        #     raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #logger.flow('9-1', f'Issue VU 0x40C6 get temp isp vb')
        # tempisp_subinfo_after = project_api.get_TEMP_ISP_physical_block_information()
        # print_object_info_ai(tempisp_subinfo_after)
        # if tempisp_subinfo.logicalvb.value != tempisp_subinfo_after.logicalvb.value:
        #     logger.error_lb(f'check TEMP ISP vb should not change after SPOR')
        #     logger.error_fp(f'expect TEMP ISP vb not change,but {tempisp_subinfo.logicalvb.value} -> {tempisp_subinfo_after.logicalvb.value} result Fail!')
        #     raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.flow('9-1', f'Issue VU 0x4097 get temp isp vb')
        tempcode_vb_after = get_temp_code_vb()
        if tempcode_vb != tempcode_vb_after:
            logger.error_lb(f'check TEMP ISP vb should not change after SPOR')
            logger.error_fp(f'expect TEMP ISP vb not change,but {tempcode_vb} -> {tempcode_vb_after} result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(10, f'Inject UECC on ISP2')
        
        inject_UECC(pca_isp2_after)
        logger.flow(11, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        pca_isp1_origin = pca_isp1_after
        pca_isp2_origin = pca_isp2_after
        logger.flow(12, 'Get ISP1 ISP2 info from VU 0x4097 as table4')
        pca_isp1_after = PCA()
        pca_isp2_after = PCA()
        pca_isp1_after, pca_isp2_after = get_isp_pca()
        logger.flow(13, 'compare table4 should different with table3(only ISP2 change), temp isp should same')
        if not self.compare_pca_info(pca_isp1_origin, pca_isp1_after):
            logger.error_lb(f'check ISP1  pca should not change after SPOR')
            logger.error_fp(f'expect ISP1 pca not change, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if self.compare_pca_info(pca_isp2_origin, pca_isp2_after):
            logger.error_lb(f'check ISP2 pca should change after SPOR')
            logger.error_fp(f'expect ISP2 pca change, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        # logger.flow('13-1', f'Issue VU 0x40C6 get temp isp vb')
        # tempisp_subinfo_after = project_api.get_TEMP_ISP_physical_block_information()
        # print_object_info_ai(tempisp_subinfo_after)
        # if tempisp_subinfo.logicalvb.value != tempisp_subinfo_after.logicalvb.value:
        #     logger.error_lb(f'check TEMP ISP vb should not change after SPOR')
        #     logger.error_fp(f'expect TEMP ISP vb not change,but {tempisp_subinfo.logicalvb.value} -> {tempisp_subinfo_after.logicalvb.value} result Fail!')
        #     raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.flow('13-1', f'Issue VU 0x4097 get temp isp vb')
        tempcode_vb_after = get_temp_code_vb()
        if tempcode_vb != tempcode_vb_after:
            logger.error_lb(f'check TEMP ISP vb should not change after SPOR')
            logger.error_fp(f'expect TEMP ISP vb not change,but {tempcode_vb} -> {tempcode_vb_after} result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        # tempisp_subinfo_origin = tempisp_subinfo_after
        # logger.flow(14, 'check Index 9: ICS bad block')
        # self.ics_bad_block = project_api.get_ics_bad_block()
        # pca_temp = PCA()
        # pca_temp.b10_block_l = tempisp_subinfo_after.logicalvb.value & 0xFF
        # pca_temp.b11_block_h = (tempisp_subinfo_after.logicalvb.value>>8) & 0xFF
        tempisp_subinfo_origin = tempcode_vb_after
        logger.flow(14, 'check Index 9: ICS bad block')
        self.ics_bad_block = project_api.get_ics_bad_block()
        pca_temp = PCA()
        pca_temp.b10_block_l = tempcode_vb_after & 0xFF
        pca_temp.b11_block_h = (tempcode_vb_after>>8) & 0xFF
        ce_num = self.flash_setting.Max_Fdevice
        plane_num = self.flash_setting.Plane_Per_Die
        logger.flow(15, f'Inject UECC on TEMP ISP valid plane')
        while(True):
            pca_temp.b5_ce = get_temp_code_ce()
            pca_temp.b6_plane = random.randint(0, plane_num-1)
            # if self.ics_bad_block.ICSBadBlocks[tempisp_subinfo_after.logicalvb.value].VB_index.value == tempisp_subinfo_after.logicalvb.value:
            #     index_ics_plane = self.ics_bad_block.ICSBadBlocks[tempisp_subinfo_after.logicalvb.value].invalid_VB_plane.value
            #     logger.info(f'index_ics_plane : {index_ics_plane}')
            if self.ics_bad_block.ICSBadBlocks[tempcode_vb_after].VB_index.value == tempcode_vb_after:
                index_ics_plane = self.ics_bad_block.ICSBadBlocks[tempcode_vb_after].invalid_VB_plane.value
                logger.info(f'index_ics_plane : {index_ics_plane}')
            if index_ics_plane != pca_temp.b5_ce * plane_num + pca_temp.b6_plane :
                inject_UECC(pca_temp)
                break

        logger.flow(16, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        
        #tempisp_subinfo_origin = tempisp_subinfo_after
        tempisp_subinfo_origin = tempcode_vb_after
        pca_isp1_origin = pca_isp1_after
        pca_isp2_origin = pca_isp2_after
        logger.flow(17, 'Get ISP1 ISP2 info from VU 0x4097 as table5')
        pca_isp1_after = PCA()
        pca_isp2_after = PCA()
        pca_isp1_after, pca_isp2_after = get_isp_pca()
        logger.flow(18, 'compare table5 should same table4, temp isp should different')
        if not self.compare_pca_info(pca_isp1_origin, pca_isp1_after) and not self.compare_pca_info(pca_isp2_origin, pca_isp1_after) :
            logger.error_lb(f'check ISP1  pca should not change after SPOR')
            logger.error_fp(f'expect ISP1 pca not change, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if not self.compare_pca_info(pca_isp2_origin, pca_isp2_after) and not self.compare_pca_info(pca_isp1_origin, pca_isp2_after):
            logger.error_lb(f'check ISP2 pca should not change after SPOR')
            logger.error_fp(f'expect ISP2 pca not change, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        # logger.flow('18-1', f'Issue VU 0x40C6 get temp isp vb')
        # tempisp_subinfo_after = project_api.get_TEMP_ISP_physical_block_information()
        # print_object_info_ai(tempisp_subinfo_after)
        # if tempisp_subinfo_origin.logicalvb.value == tempisp_subinfo_after.logicalvb.value:
        #     logger.error_lb(f'check TEMP ISP vb should change after SPOR')
        #     logger.error_fp(f'expect TEMP ISP vb change,but {tempisp_subinfo_origin.logicalvb.value} -> {tempisp_subinfo_after.logicalvb.value} result Fail!')
        #     #raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.flow('18-1', f'Issue VU 0x4097 get temp isp vb')
        tempcode_vb_after = get_temp_code_vb()
        if tempisp_subinfo_origin == tempcode_vb_after:
            logger.error_lb(f'check TEMP ISP vb should not change after SPOR')
            logger.error_fp(f'expect TEMP ISP vb not change,but {tempisp_subinfo_origin} -> {tempcode_vb_after} result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(19, f'Inject UECC on ISP1 and ISP2')
        inject_UECC(pca_isp1_after)
        inject_UECC(pca_isp2_after)
        logger.flow(20, f'HW reset without SSU, should stuck')
        status = SPOR_init_mp()
        if status != False:
            pattern_status = False
            logger.error_lb(f'inject uecc on ISP1 and ISP2 and SPOR ')
            logger.error_fp(f'expect SPOR Fail and get assert, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()