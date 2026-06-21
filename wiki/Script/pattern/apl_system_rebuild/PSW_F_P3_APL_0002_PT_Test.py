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
        apl_pattern_precondition()


    def step1(self) -> None:
        #VC1        
        logger.flow(1, f'Issue VU 0x40C6 get PT fep as table1')
        #testlist:list[open_block_type_list] = [open_block_type_list.BBT, open_block_type_list.Pointer_to_Index_block, open_block_type_list.Index, open_block_type_list.List, open_block_type_list.LOG, open_block_type_list.TMP_ISP, open_block_type_list.MAIN_ISP, open_block_type_list.PTE]
        subinfo = copy.deepcopy(project_api.get_PT_physical_block_information())
        logger.info(f'ce = {subinfo.CE.value}, plane ={subinfo.plane.value}, fep = {subinfo.FEP.value}')
        print_object_info_ai(subinfo)
        pca = PCA()
        pca.b10_block_l = 0
        pca.b11_block_h = 0
        pca.b5_ce = subinfo.CE.value
        pca.b6_plane = subinfo.plane.value
        pca.l12_fpage = (subinfo.FEP.value-1) <<5
        
        #pca.l0_op = 0x20000
        pca.l0_op = 0
        pca.b4_mode = 1
        dire_read_payload = api.direct_read(pca=pca, block_count=4, include_FW_spare=True)
        dumpfile('testPTread.bin',dire_read_payload)
        logger.flow(2, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        logger.flow(3, f'Issue VU 0x40C6 get PT fep as table2')
        subinfo2 =  copy.deepcopy(project_api.get_PT_physical_block_information()) 
        pca.b5_ce = subinfo2.CE.value
        pca.b6_plane = subinfo2.plane.value
        pca.l12_fpage = (subinfo2.FEP.value-1) <<5      
        dire_read_payload = api.direct_read(pca=pca, block_count=4, include_FW_spare=True)
        dumpfile('testPTread2.bin',dire_read_payload)
        logger.flow(4, 'compare table1 should same as table2')
        if not compare_pb_fep(subinfo,subinfo2):
            logger.error_lb(f'check PT pca should not change after SPOR')
            logger.error_fp(f'expect PT pca not change, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #VC2
        logger.flow(5, 'inject UECC on PT major page')
        uecc_pca = PCA()
        uecc_pca.b10_block_l = subinfo2.physicalblock.value & 0xFF
        uecc_pca.b11_block_h = (subinfo2.physicalblock.value >> 8) & 0xFF
        uecc_pca.b5_ce = subinfo2.CE.value
        uecc_pca.b6_plane = subinfo2.plane.value
        majorpage = subinfo2.FEP.value - 2
        uecc_pca.l12_fpage = majorpage << 5
        inject_UECC(uecc_pca)
        logger.flow(6, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        logger.flow(7, f'Issue VU 0x40C6 get PT fep as table3')
        subinfo3 =  copy.deepcopy(project_api.get_PT_physical_block_information()) 
        pca.b5_ce = subinfo3.CE.value
        pca.b6_plane = subinfo3.plane.value
        pca.l12_fpage = (subinfo3.FEP.value-1) <<5      
        dire_read_payload = api.direct_read(pca=pca, block_count=4, include_FW_spare=True)
        dumpfile('testPTread3.bin',dire_read_payload)
        logger.flow(8, 'compare table2 should not same as table3')
        if compare_pb_fep(subinfo2,subinfo3):
            logger.error_lb(f'check PT pca should change after SPOR')
            logger.error_fp(f'expect PT pca change, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #VC4
        logger.flow(9, 'inject UECC on PT Mirror page')
        uecc_pca = PCA()
        uecc_pca.b10_block_l = subinfo3.physicalblock.value & 0xFF
        uecc_pca.b11_block_h = (subinfo3.physicalblock.value >> 8) & 0xFF
        uecc_pca.b5_ce = subinfo3.CE.value
        uecc_pca.b6_plane = subinfo3.plane.value
        mirrorpage = subinfo3.FEP.value - 1
        uecc_pca.l12_fpage = mirrorpage << 5
        inject_UECC(uecc_pca)
        logger.flow(10, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        logger.flow(11, f'Issue VU 0x40C6 get PT fep as table4')
        subinfo4 =  copy.deepcopy(project_api.get_PT_physical_block_information()) 
        pca.b5_ce = subinfo4.CE.value
        pca.b6_plane = subinfo4.plane.value
        pca.l12_fpage = (subinfo4.FEP.value-1) <<5      
        dire_read_payload = api.direct_read(pca=pca, block_count=4, include_FW_spare=True)
        dumpfile('testPTread4.bin',dire_read_payload)
        logger.flow(12, 'compare table3 should not same as table4')
        if compare_pb_fep(subinfo3,subinfo4):
            logger.error_lb(f'check PT pca should change after SPOR')
            logger.error_fp(f'expect PT pca change, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        #VC5~VC7
        for case in range (3):
            logger.flow(13, f'Issue VU 0x40C6 get PT fep as table5')
            subinfo5 =  copy.deepcopy(project_api.get_PT_physical_block_information()) 
            print_object_info_ai(subinfo5)
            make_index_refresh_update_PT()
            make_index_refresh_update_PT()
            
            make_index_refresh_update_PT()
            make_index_refresh_update_PT()
            subinfo5 =  copy.deepcopy(project_api.get_PT_physical_block_information()) 
            print_object_info_ai(subinfo5)
            logger.flow(14, 'inject UECC on PT Mirror and Major page')
            uecc_pca = PCA()
            uecc_pca.b10_block_l = subinfo5.physicalblock.value & 0xFF
            uecc_pca.b11_block_h = (subinfo5.physicalblock.value >> 8) & 0xFF
            uecc_pca.b5_ce = subinfo5.CE.value
            uecc_pca.b6_plane = subinfo5.plane.value
            cnt = 1
            while True:
                curpage = subinfo5.FEP.value - cnt
                if case == 0:
                    if curpage == 0:
                        break
                elif case == 1:
                    if curpage == 1:
                        break
                elif case == 2:
                    if curpage < 0:
                        break
                uecc_pca.l12_fpage = curpage << 5
                inject_UECC(uecc_pca)
                cnt = cnt+1
            logger.flow(15, f'HW reset without SSU')            
            status = True
            domp = False
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
                if case != 2 and assertnum == 0x5027:
                    status = False
                domp = True
    
            else:
                logger.error_lb(f'Inject UECC on BBT page0 and page1')
                logger.error_fp(f'expect init fail, result Fail!')
                if case == 2:
                    status = False
            finally:
                if domp == True:
                    api.MP().execute()
                    api.first_init_to_max_hs_gear(link_startup_mode=_param.current_speed.link_startup_mode, ref_clk=_param.current_speed.refclk)
            if status == False :
                logger.error_lb(f'Inject UECC on PT until page 1 or page2')
                logger.error_fp(f'expect init fail, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            logger.flow(16, f'Issue VU 0x40C6 get PT fep as table6')
            subinfo6 =  copy.deepcopy(project_api.get_PT_physical_block_information()) 
            print_object_info_ai(subinfo)
            pca.b5_ce = subinfo6.CE.value
            pca.b6_plane = subinfo6.plane.value
            pca.l12_fpage = (subinfo6.FEP.value-1) <<5      
            dire_read_payload = api.direct_read(pca=pca, block_count=4, include_FW_spare=True)
            dumpfile('testPTread5.bin',dire_read_payload)
            logger.flow(17, 'compare table5 should same as table6')
            if compare_pb_fep(subinfo5,subinfo6):
                logger.error_lb(f'check PT pca should change after SPOR')
                logger.error_fp(f'expect PT pca change, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL


      
        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()