import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from typing import List, cast
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from typing import Any, Union
import time
from enum import IntEnum

class RiskyType(IntEnum):
    SAFE_GROUP = 0
    COLD_GROUP = 1
    HOT_GROUP = 2
    NA = 3

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.write_record = api.get_empty_write_record()
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting = get_flash_setting()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.tlc_exceed_size = 50
        self.slc_exceed_size = 50
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.TestWBLun = 2
        self.TestGC = 3
        self.TestTemperature = 4
        api.modify_desc_attr_flag(QuerryType=Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_ATTRIBUTE, Index=api.AttributeIDN.PSA_STATE, Value=0, IndexLen=1)
        self.config_lun(normal_list=[self.TestNormalLun, self.TestWBLun, self.TestGC, self.TestTemperature], em1_list=[self.TestEM1Lun])
        self.dev_desc = api.get_device_descriptor()
        self.rpmb = RPMB(RPMBRegion.REGION_0)
        vuc_clear_rpmb_key(RPMBRegion.REGION_0) 
        logger.info('RPMB key progrmming')
        self.rpmb_key_programming()
        resp, DebugInfo = api.ufs_api.vendor_cmd.get_debug_info()    
        resp, self.backup_ec_value = api.ufs_api.vendor_cmd.read_Xmemory(sram_address = DebugInfo.VB_list_cycle_address.value)    
        pass

    def step1(self) -> None:
        logger.flow(1, 'Create PSA Block')
        api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=self.dev_desc.l37_psa_max_data_size)
        api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.PRE_SOLDERING)
        logger.info(f"PSA State = {api.read_attribute(idn=api.AttributeIDN.PSA_STATE)}")
        self.ftl_vb_list_data = self.get_VB_group(show=False)
        VPCT_list, VBINFO_list = self.get_all_VPCT_VBINFO_values()
        for vb in range(len(VPCT_list)):
            if VBINFO_list[vb].VBINFO_BIT_PSA.value == 1 and VPCT_list[vb].VPCT_IS_TLC.value == 1:
                group = self.ftl_vb_list_data[vb]['group']
                self.print_VBCT_VBINFO(VPCT_list[vb])
                self.print_VBCT_VBINFO(VBINFO_list[vb])
                logger.error_lb(f'check VB[{vb}] grouptype = {group} ({project_api.VB_GROUP(group).name}) after pre-soldering')
                logger.error_fp(f'expect there is no VB has PSA and TLC bit, but current VBINFO_BIT_PSA / VPCT_IS_TLC is 1, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=self.slc_vb_size + self.slc_exceed_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.LOADING_COMPLETE)
        logger.info(f"PSA State = {api.read_attribute(idn=api.AttributeIDN.PSA_STATE)}")
        pass
    
    def step2(self) -> None:
        logger.flow(2, 'Check VBCT / VBINFO of PSA VB')
        pca = lba_to_pba(self.TestNormalLun, 0)
        VPCT_value, VBINFO_value = self.get_VPCT_VBINFO_value(pca.w10_block.value)
        self.print_VBCT_VBINFO(VPCT_value)
        self.print_VBCT_VBINFO(VBINFO_value)
        psa_VPCT = project_api.VPCT_values(bytearray(4))
        psa_VBINFO = project_api.VBINFO_values(bytearray(2))
        psa_VPCT.VPC.value = self.slc_vb_size
        psa_VBINFO.VBINFO_BIT_PSA.value = 1
        psa_VBINFO.VBINFO_BIT_PMNTRAINEN.value = 1
        self.compare_VPCT_VBINFO_criteria(expect_value=psa_VPCT, raw_value=VPCT_value, VB=pca.w10_block.value)
        self.compare_VPCT_VBINFO_criteria(expect_value=psa_VBINFO, raw_value=VBINFO_value, VB=pca.w10_block.value)
        api.modify_desc_attr_flag(QuerryType=Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_ATTRIBUTE, Index=api.AttributeIDN.PSA_STATE, Value=0, IndexLen=1)
        self.reconfig_lun()
        pass
    
    def step3(self) -> None:
        logger.flow(3, 'create TLC/SLC/WB VB')
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=self.tlc_vb_size + self.tlc_exceed_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.TLC_closed_pca = lba_to_pba(self.TestNormalLun, 0)
        self.TLC_open_pca = lba_to_pba(self.TestNormalLun, self.tlc_vb_size)
        api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=self.slc_vb_size + self.slc_exceed_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        self.SLC_closed_pca = lba_to_pba(self.TestEM1Lun, 0)
        self.SLC_open_pca = lba_to_pba(self.TestEM1Lun, self.slc_vb_size)
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        api.sequential_write(lun=self.TestWBLun, start_lba=0, total_size=self.slc_vb_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x00)
        pass
    
    def step4(self) -> None:
        logger.flow(4, 'Check VBCT / VBINFO of each VB type')
        self.ftl_vb_list_data = self.get_VB_group(show=True)
        VPCT_list, VBINFO_list = self.get_all_VPCT_VBINFO_values()
        GC_SOURCE_cnt = 0
        GC_DEST_cnt = 0
        for vb, info in self.ftl_vb_list_data.items():
            group = info['group']
            access_mode = info['access_mode']
            partition = info['partition']
            expect_VPCT = project_api.VPCT_values(bytearray(4))
            expect_VBINFO = project_api.VBINFO_values(bytearray(2))
            
            if project_api.VB_GROUP(group) in [project_api.VB_GROUP.FREE_BLK_QUEUE_SLC, 
                                               project_api.VB_GROUP.FREE_BLK_QUEUE_MLC,
                                               project_api.VB_GROUP.FREE_BLK_QUEUE_TABLE,
                                               ]:
                if VPCT_list[vb].VPC.value != 0:
                    logger.info(f'====== VB {vb} grouptype = {group} ({project_api.VB_GROUP(group).name}), check VPC======')
                    logger.error_lb(f'check VPC')
                    logger.error_fp(f'expect VPC = 0, but current value = {VPCT_list[vb].VPC.value}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    continue
            
            if vb in [self.SLC_closed_pca.w10_block.value]:
                expect_VPCT.VPC.value = self.slc_vb_size
            elif vb in [self.SLC_open_pca.w10_block.value]:
                expect_VPCT.VPC.value = self.slc_exceed_size
            elif vb == self.TLC_closed_pca.w10_block.value:
                expect_VPCT.VPC.value = self.tlc_vb_size
            elif vb == self.TLC_open_pca.w10_block.value:
                expect_VPCT.VPC.value = self.tlc_exceed_size
            else:
                expect_VPCT.VPC.value = VPCT_list[vb].VPC.value
                
                
            if project_api.VB_GROUP(group) in [project_api.VB_GROUP.INCOMPLETE_BLK_SLC, 
                                               project_api.VB_GROUP.INCOMPLETE_BLK_MLC,
                                               ]:
                expect_VPCT.VPCT_IS_PARTIAL_BLOCK.value = 1

            if project_api.VB_GROUP(group) in [project_api.VB_GROUP.CURRENT_L2_MLC, 
                                               project_api.VB_GROUP.CURRENT_DATA_GC_BLK_MLC,
                                               project_api.VB_GROUP.INCOMPLETE_BLK_MLC,
                                               project_api.VB_GROUP.USED_BLK_POOL_MLC,
                                               project_api.VB_GROUP.CURRENT_L3_MLC,
                                               project_api.VB_GROUP.TMP_ERASE_BLK_MLC,
                                               project_api.VB_GROUP.TMP_USED_BLK_MLC,
                                               project_api.VB_GROUP.TMP_REMOVE_BLK_MLC,
                                               project_api.VB_GROUP.REFERENCE_QUEUE_MLC,
                                               project_api.VB_GROUP.REMAP_DATA_GC_BLK_MLC,
                                               project_api.VB_GROUP.PURGE_WAIT_ERASE_MLC,
                                               ]:
                if access_mode == 0:
                    expect_VPCT.VPCT_IS_TLC.value = 0
                else:
                    expect_VPCT.VPCT_IS_TLC.value = 1
                    expect_VBINFO.VBINFO_BIT_EM1_NORMAL.value = 0
            if project_api.VB_GROUP(group) in [project_api.VB_GROUP.CURRENT_L2_SLC, 
                                               project_api.VB_GROUP.CURRENT_L2_MLC,
                                               project_api.VB_GROUP.CURRENT_L1,
                                               project_api.VB_GROUP.CURRENT_L3_SLC,
                                               project_api.VB_GROUP.CURRENT_L3_MLC,
                                               project_api.VB_GROUP.CURRENT_DATA_GC_BLK_SLC,
                                               project_api.VB_GROUP.CURRENT_DATA_GC_BLK_MLC,
                                               ]:
                expect_VPCT.VPCT_IS_OPEN.value = 1
                
            if project_api.VB_GROUP(group) in [project_api.VB_GROUP.CURRENT_L2_SLC, 
                                               project_api.VB_GROUP.CURRENT_L2_MLC,
                                               project_api.VB_GROUP.USED_BLK_POOL_SLC,
                                               project_api.VB_GROUP.USED_BLK_POOL_MLC,
                                               project_api.VB_GROUP.CURRENT_L1,
                                               project_api.VB_GROUP.LOG_TAB_BLK,
                                               project_api.VB_GROUP.CURRENT_PTE,
                                               project_api.VB_GROUP.INCOMPLETE_BLK_SLC,
                                               project_api.VB_GROUP.INCOMPLETE_BLK_MLC,
                                               ] \
                and VBINFO_list[vb].VBINFO_BIT_GC_DEST.value != 1:
                expect_VBINFO.VBINFO_BIT_PMNTRAINEN.value = 1
            if project_api.VB_GROUP(group) in [project_api.VB_GROUP.CURRENT_L2_SLC, 
                                               project_api.VB_GROUP.USED_BLK_POOL_SLC,
                                               project_api.VB_GROUP.CURRENT_L3_SLC,
                                               project_api.VB_GROUP.INCOMPLETE_BLK_SLC,
                                               ]:
                expect_VBINFO.VBINFO_BIT_EM1_NORMAL.value = 1
            if project_api.VB_GROUP(group) in [project_api.VB_GROUP.RAIN_SWAP_NO_OBR_BLK, 
                                               ]:
                expect_VBINFO.VBINFO_TEMP_FULL_BLK_PROTECTION_RAIN.value = 1
            if project_api.VB_GROUP(group) in [project_api.VB_GROUP.RAIN_SWAP_NO_OBR_SLC_L2_SLC, 
                                               project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_SLC,
                                               project_api.VB_GROUP.RAIN_SWAP_NO_OBR_TLC_L2_TLC,
                                               ]:
                expect_VBINFO.VBINFO_TEMP_SWAP_BLK_PROTECTION_RAIN.value = 1
            if project_api.VB_GROUP(group) in [project_api.VB_GROUP.INCOMPLETE_BLK_SLC, 
                                               project_api.VB_GROUP.INCOMPLETE_BLK_MLC,
                                               ]:
                expect_VBINFO.VBINFO_CLOSE_BLK_PARTIAL_STATIC.value = 1
            if project_api.VB_GROUP(group) in [project_api.VB_GROUP.CURRENT_DATA_GC_BLK_SLC, 
                                               project_api.VB_GROUP.CURRENT_DATA_GC_BLK_MLC,
                                               ]:
                expect_VBINFO.VBINFO_BIT_GC_DEST.value = 1
            if VBINFO_list[vb].VBINFO_BIT_GC_SOURCE.value == 1:
                expect_VBINFO.VBINFO_BIT_GC_SOURCE.value = 1
                expect_VPCT.VPCT_IS_GC_SRC.value = 1
            # if project_api.VB_GROUP(group) in [project_api.VB_GROUP.CURRENT_DATA_GC_BLK_SLC, 
            #                                    project_api.VB_GROUP.CURRENT_DATA_GC_BLK_MLC,
            #                                    ]:
            #     expect_VBINFO.VBINFO_BIT_COLD_RISKY.value = 1
            # if project_api.VB_GROUP(group) in [project_api.VB_GROUP.CURRENT_DATA_GC_BLK_SLC, 
            #                                    project_api.VB_GROUP.CURRENT_DATA_GC_BLK_MLC,
            #                                    ]:
            #     expect_VBINFO.VBINFO_BIT_HOT_RISKY.value = 1
            self.compare_VPCT_VBINFO_criteria(expect_value=expect_VPCT, raw_value=VPCT_list[vb], VB=vb)
            self.compare_VPCT_VBINFO_criteria(expect_value=expect_VBINFO, raw_value=VBINFO_list[vb], VB=vb)
            pass
        pass
    
    def step5(self) -> None:
        logger.flow(5, 'Verify FG BG GC QUEUE')
        rsp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        project_api.issue_D0FD_disable_all_the_background_operations()
        project_api.issue_D0FD_disable_all_the_foreground_operations()
        vb_EM1 = open_vb_information.open_logical_VB_number_for_EM1_L2_Host.value
        vb_TLC = open_vb_information.L2_Open_logical_VB_Host_TLC_number.value
        vb_list = [vb_EM1]
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.LowPriority)
        
        vb_list = [vb_TLC]
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.MediumPriority)
        time.sleep(3)
        VPCT_value, VBINFO_value = self.get_VPCT_VBINFO_value(vb_EM1)
        self.print_VBCT_VBINFO(VPCT_value)
        self.print_VBCT_VBINFO(VBINFO_value)
        if VBINFO_value.VBINFO_BIT_GC_BG_QUEUE.value != 1:
            logger.error_lb(f'check VBINFO_BIT_GC_BG_QUEUE after refresh enqueue VB {vb_EM1}')
            logger.error_fp(f'expect VBINFO_BIT_GC_BG_QUEUE = 1, but current value = {VBINFO_value.VBINFO_BIT_GC_BG_QUEUE.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if VPCT_value.VPCT_IS_PARTIAL_BLOCK.value != 1:
            logger.error_lb(f'check VPCT_IS_PARTIAL_BLOCK after refresh enqueue VB {vb_EM1}')
            logger.error_fp(f'expect VPCT_IS_PARTIAL_BLOCK = 1, but current value = {VPCT_value.VPCT_IS_PARTIAL_BLOCK.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        VPCT_value, VBINFO_value = self.get_VPCT_VBINFO_value(vb_TLC)
        self.print_VBCT_VBINFO(VPCT_value)
        self.print_VBCT_VBINFO(VBINFO_value)
        if VBINFO_value.VBINFO_BIT_GC_FG_QUEUE.value != 1:
            logger.error_lb(f'check VBINFO_BIT_GC_FG_QUEUE after refresh enqueue VB {vb_TLC}')
            logger.error_fp(f'expect VBINFO_BIT_GC_FG_QUEUE = 1, but current value = {VBINFO_value.VBINFO_BIT_GC_FG_QUEUE.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if VPCT_value.VPCT_IS_PARTIAL_BLOCK.value != 1:
            logger.error_lb(f'check VPCT_IS_PARTIAL_BLOCK after refresh enqueue VB {vb_TLC}')
            logger.error_fp(f'expect VPCT_IS_PARTIAL_BLOCK = 1, but current value = {VPCT_value.VPCT_IS_PARTIAL_BLOCK.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        project_api.issue_D0FD_enable_all_the_background_operations()
        project_api.issue_D0FD_enable_all_the_foreground_operations()
        time.sleep(2)
        self.ftl_vb_list_data = self.get_VB_group(show=True)
        VPCT_list, VBINFO_list = self.get_all_VPCT_VBINFO_values()
        GC_SOURCE_list:List[int] = []
        GC_DEST_list:List[int] = []
        for vb in range(self.fw_geometry.l52_total_vb_count):
            group = project_api.VB_GROUP(self.ftl_vb_list_data[vb]['group'])
            if group in [project_api.VB_GROUP.CURRENT_DATA_GC_BLK_SLC, 
                            project_api.VB_GROUP.CURRENT_DATA_GC_BLK_MLC,
                            ]:
                if VBINFO_list[vb].VBINFO_BIT_GC_DEST.value != 1:
                    self.print_VBCT_VBINFO(VPCT_list[vb])
                    self.print_VBCT_VBINFO(VBINFO_list[vb])
                    logger.error_lb(f'check VBINFO_BIT_GC_DEST after refresh enqueue VB {vb} ({group.name})')
                    logger.error_fp(f'expect VBINFO_BIT_GC_DEST = 1, but current value = {VBINFO_list[vb].VBINFO_BIT_GC_DEST.value}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                GC_DEST_list.append(vb)

            if VBINFO_list[vb].VBINFO_BIT_GC_SOURCE.value == 1:
                GC_SOURCE_list.append(vb)
                if VPCT_list[vb].VPCT_IS_GC_SRC.value + VPCT_list[vb].VPCT_IS_RPMB_EM1_GC_SRC.value != 1:
                    self.print_VBCT_VBINFO(VPCT_list[vb])
                    self.print_VBCT_VBINFO(VBINFO_list[vb])
                    logger.error_lb(f'check VPCT_IS_GC_SRC/VPCT_IS_RPMB_EM1_GC_SRC after refresh enqueue VB {vb} ({group.name})')
                    logger.error_fp(f'expect VPCT_IS_GC_SRC/VPCT_IS_RPMB_EM1_GC_SRC = 1, but VPCT_IS_GC_SRC value = {VPCT_list[vb].VPCT_IS_GC_SRC.value}, VPCT_IS_RPMB_EM1_GC_SRC value = {VPCT_list[vb].VPCT_IS_RPMB_EM1_GC_SRC.value}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if VPCT_list[vb].VPCT_IS_GC_SRC.value + VPCT_list[vb].VPCT_IS_RPMB_EM1_GC_SRC.value == 1:
                if VBINFO_list[vb].VBINFO_BIT_GC_SOURCE.value != 1:
                    self.print_VBCT_VBINFO(VPCT_list[vb])
                    self.print_VBCT_VBINFO(VBINFO_list[vb])
                    logger.error_lb(f'check VBINFO_BIT_GC_SOURCE after refresh enqueue VB {vb} ({group.name})')
                    logger.error_fp(f'expect VBINFO_BIT_GC_SOURCE = 1, but current value = {VBINFO_list[vb].VBINFO_BIT_GC_SOURCE.value}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if len(GC_SOURCE_list)>0 and len(GC_DEST_list) != 1:
            logger.error_lb(f'check VBINFO_BIT_GC_DEST')
            logger.error_fp(f'expect only 1 VB raise VBINFO_BIT_GC_DEST = 1, but current cnt = {GC_DEST_list}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        self.polling_bkops_idle()
        pass
    
    def step6(self) -> None:
        logger.flow(6, 'Write data to create open Block and RPMB')
        lenth = BLOCK256B_SIZE_8K_BYTE
        self.rpmb.rpmb_write_data(0, lenth)
        vpc = lenth * 512 // DATA_SIZE_4K_BYTE
        _, self.rpmb_pca = project_api.issue_4051_to_get_physical_address(luID=api.WellKnownLUN.RPMB, lba=0)
        self.spor_pca = self.create_VB_with_SPOR(lun=self.TestNormalLun)
        
        VPCT_value, VBINFO_value = self.get_VPCT_VBINFO_value(self.rpmb_pca.virtual_block_number.value)
        self.print_VBCT_VBINFO(VPCT_value)
        self.print_VBCT_VBINFO(VBINFO_value)
        if VPCT_value.VPC.value != vpc:
            logger.error_lb(f'check VPC after refresh enqueue VB {self.rpmb_pca.virtual_block_number.value}')
            logger.error_fp(f'expect VPC = {vpc}, but current value = {VPCT_value.VPC.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        self.spor_pca = self.create_VB_with_SPOR(lun=self.TestNormalLun)
        VPCT_value, VBINFO_value = self.get_VPCT_VBINFO_value(self.spor_pca.w10_block.value)
        self.print_VBCT_VBINFO(VPCT_value)
        self.print_VBCT_VBINFO(VBINFO_value)
        if VBINFO_value.VBINFO_BIT_IS_APL.value != 1:
            logger.error_lb(f'check VBINFO_BIT_IS_APL after SPOR')
            logger.error_fp(f'expect VBINFO_BIT_IS_APL = 1, but current value = {VBINFO_value.VBINFO_BIT_IS_APL.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def step7(self) -> None:
        logger.flow(7, 'Get xtemp parameter from mconfig')
        self.reconfig_lun()
        rsp, mconfig = project_api.get_mConfig_data()
        mConfig_in_vu_bkup = copy.deepcopy(mconfig)
        XTEMP_ENABLE_PEC = mconfig.XTEMP_ENABLE_PEC.value
        XTEMP_TEMP_BUFFER = mconfig.XTEMP_TEMP_BUFFER.value
        XTEMP_TIME_DETECTION_VALUE = mconfig.XTEMP_TIME_DETECTION_VALUE.value
        XTEMP_REFRESH_T1 = mconfig.XTEMP_Refresh_T1.value if mconfig.XTEMP_Refresh_T1.value <= 127 else mconfig.XTEMP_Refresh_T1.value - 256
        XTEMP_REFRESH_T2 = mconfig.XTEMP_Refresh_T2.value if mconfig.XTEMP_Refresh_T2.value <= 127 else mconfig.XTEMP_Refresh_T2.value - 256
        logger.info(f'Xtemp enable EPC = {XTEMP_ENABLE_PEC}, temp buffer = {XTEMP_TEMP_BUFFER}, time detection = {XTEMP_TIME_DETECTION_VALUE}')
        logger.info(f'Xtemp refresh T1 = {XTEMP_REFRESH_T1}, Xtemp refresh T2 = {XTEMP_REFRESH_T2}')

        if mconfig.XTEMP_ENABLE_PEC.value != 10:
            mconfig.XTEMP_ENABLE_PEC.value = 10
            mconfig.payload[0:7] = "MCONFIG".encode("ascii")
            project_api.set_mConfig_data(mConfig=mconfig)
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)

            rsp, mconfig = project_api.get_mConfig_data()
            XTEMP_ENABLE_PEC = mconfig.XTEMP_ENABLE_PEC.value
            XTEMP_TEMP_BUFFER = mconfig.XTEMP_TEMP_BUFFER.value
            XTEMP_TIME_DETECTION_VALUE = mconfig.XTEMP_TIME_DETECTION_VALUE.value
            XTEMP_REFRESH_T1 = mconfig.XTEMP_Refresh_T1.value if mconfig.XTEMP_Refresh_T1.value <= 127 else mconfig.XTEMP_Refresh_T1.value - 256
            XTEMP_REFRESH_T2 = mconfig.XTEMP_Refresh_T2.value if mconfig.XTEMP_Refresh_T2.value <= 127 else mconfig.XTEMP_Refresh_T2.value - 256
            logger.info(f'Xtemp enable EPC = {XTEMP_ENABLE_PEC}, temp buffer = {XTEMP_TEMP_BUFFER}, time detection = {XTEMP_TIME_DETECTION_VALUE}')
            logger.info(f'Xtemp refresh T1 = {XTEMP_REFRESH_T1}, Xtemp refresh T2 = {XTEMP_REFRESH_T2}')

        logger.flow(8, f'Set EC as XTEMP_ENABLE_PEC = {XTEMP_ENABLE_PEC * 100}')
        set_ec_value = XTEMP_ENABLE_PEC * 100
        value_bytes = set_ec_value.to_bytes(4, byteorder='little', signed=False)
        data = bytearray(b'\xFF' * 0x4000)
        data[:(self.fw_geometry.l52_total_vb_count * 4)] = value_bytes * self.fw_geometry.l52_total_vb_count
        self.set_ec(data)
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)
        erase_cnt_of_vb, erase_cnt_for_hidden_physical_block, _ = project_api.get_all_VB_erase_count()

        logger.flow(9, f'Set nand temp as XTEMP_REFRESH_T2 + 1 = {XTEMP_REFRESH_T2 + 1}')
        self.set_nand_temp(set_temp=XTEMP_REFRESH_T2 + 1)
        time.sleep(XTEMP_TIME_DETECTION_VALUE)

        logger.flow(10, 'Sequential write 1.5 TLC VB size for creating used VB and current L2, and get VB info for verifying risky type should be "Hot Risky"')
        write_length = self.tlc_vb_size + (self.tlc_vb_size >> 1)
        api.sequential_write(lun=self.TestTemperature, start_lba=0, total_size=write_length, chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 0,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        closed_pca = lba_to_pba(lun=self.TestTemperature , lba=0)
        open_pca = lba_to_pba(lun=self.TestTemperature , lba=write_length - 1)
        self.ftl_vb_list_data = self.get_VB_group(show=True)
        for vb, info in self.ftl_vb_list_data.items():
            group = project_api.VB_GROUP(info['group'])
            risky_type = RiskyType(info['risky_type'])
            logger.info(f'VB[{vb}]: group = {group} ({group.name}), erase_cnt = {erase_cnt_of_vb[vb]}, risky_type = {risky_type} ({risky_type.name})')

        for pca in [closed_pca, open_pca]:
            VPCT_value, VBINFO_value = self.get_VPCT_VBINFO_value(pca.w10_block.value)
            self.print_VBCT_VBINFO(VPCT_value)
            self.print_VBCT_VBINFO(VBINFO_value)
            if VBINFO_value.VBINFO_BIT_HOT_RISKY.value != 1:
                logger.error_lb(f'check VBINFO_BIT_HOT_RISKY after set Nand temperature')
                logger.error_fp(f'expect VBINFO_BIT_HOT_RISKY = 1, but current value = {VBINFO_value.VBINFO_BIT_HOT_RISKY.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            pass
        mConfig_in_vu_bkup.payload[0:7] = "MCONFIG".encode("ascii")
        project_api.set_mConfig_data(mConfig=mConfig_in_vu_bkup)
        
    def post_process(self) -> None:
        self.set_ec(set_ec=self.backup_ec_value)
        pass
    
    def set_nand_temp(self, set_temp:int) -> None:
        temp_set = set_temp
        if temp_set < 0:
            temp_set = 65536 + temp_set
        set_nand_temp = project_api.SetNandTemperature()
        set_nand_temp.bEnableSetVuTemp.value = 1
        set_nand_temp.NAND_TEMPERATURE_DIE_0.value = temp_set
        if self.flash_setting.Max_Fdevice >= 2:
            set_nand_temp.NAND_TEMPERATURE_DIE_1.value = temp_set
        if self.flash_setting.Max_Fdevice >= 4:
            set_nand_temp.NAND_TEMPERATURE_DIE_2.value = temp_set
            set_nand_temp.NAND_TEMPERATURE_DIE_3.value = temp_set
        set_nand_temp.Use_Delayed_fake_tmeperatures.value = 0  
        rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)
        self.get_nand_temp()

    def get_nand_temp(self) -> None:
        rsp , GetNandTemperature = project_api.issue_4021_get_nand_temperature()
        temp_gap = 37
        die0_temp = GetNandTemperature.temperature_of_die_0.value - temp_gap
        die1_temp = GetNandTemperature.temperature_of_die_1.value - temp_gap
        die2_temp = GetNandTemperature.temperature_of_die_2.value - temp_gap
        die3_temp = GetNandTemperature.temperature_of_die_3.value - temp_gap
        logger.info(f'{die0_temp} / {die1_temp} / {die2_temp} / {die3_temp}')      
    
    def check_timeout(self, start_time: float, timeout_min: int) -> bool:
        current_time = time.time()
        if (current_time - start_time) >= timeout_min * 60:
            return True
        else:
            return False
    
    def get_VPCT_VBINFO_value(self, specific_VB:int) -> tuple[project_api.VPCT_values, project_api.VBINFO_values]:
        response, data_payload = project_api.issue_40C0_to_get_VPCT_description(specific_VB, 0x0)
        VPCT = project_api.VPCT_values(data_payload, 4, 7)
        VBINFO = project_api.VBINFO_values(data_payload, 8, 9)
        return VPCT, VBINFO

    def get_all_VPCT_VBINFO_values(self) -> tuple[list[project_api.VPCT_values], list[project_api.VBINFO_values]]:
        response, data_payload = project_api.issue_40C0_to_get_VPCT_description(0xFFFFFFFF, 0x0)
        dumpfile('all_VPCT_values.bin', data_payload)
        VPCT_list = []
        num_of_vb = int.from_bytes(data_payload[0 : 4], 'little')
        offset = 4
        for i in range(num_of_vb):
            VPCT_list.append(project_api.VPCT_values(data_payload, offset + 4*i, offset + 4*(i+1)-1))
        VBINFO_list = []
        offset = 4096
        for i in range(num_of_vb):
            VBINFO_list.append(project_api.VBINFO_values(data_payload, offset + 2*i, offset + 2*(i+1)-1))
        return VPCT_list, VBINFO_list
    
    def print_VBCT_VBINFO(self,input:Union[project_api.VPCT_values, project_api.VBINFO_values]) -> None:
        if isinstance(input, project_api.VPCT_values): 
            logger.info('================= VBCT =================')
        else:
            logger.info('================= VBINFO =================')
        fields = [
            (name, field) for name, field in input.__dict__.items()
            if hasattr(field, "start_bit") and hasattr(field, "end_bit") and hasattr(field, "value")
        ]
        fields.sort(key=lambda kv: kv[1].start_bit)
        for name, field in fields:
            logger.info(
                f'BIT[{field.start_bit}:{field.end_bit}]: {name} = {field.value} (0x{field.value:X})'
            )
        pass
    
    def compare_VPCT_VBINFO_criteria(self, raw_value: Any, expect_value: Any, VB:int) -> None:
        raw_fields = [
            (name, field) for name, field in raw_value.__dict__.items()
            if hasattr(field, "start_bit") and hasattr(field, "end_bit") and hasattr(field, "value")
        ]
        raw_fields.sort(key=lambda kv: kv[1].start_bit)
        expect_fields = [
            (name, field) for name, field in expect_value.__dict__.items()
            if hasattr(field, "start_bit") and hasattr(field, "end_bit") and hasattr(field, "value")
        ]
        expect_fields.sort(key=lambda kv: kv[1].start_bit)
        
        
        for (name0, raw), (name1, expect) in zip(
                                    raw_fields,
                                    expect_fields,
                                ):
            if hasattr(raw, "value") and hasattr(expect, "value") and name0 == name1:
                if raw.value != expect.value:
                    group = self.ftl_vb_list_data[VB]['group']
                    if isinstance(raw_value, project_api.VPCT_values): 
                        logger.info(f'====== VB {VB} grouptype = {group} ({project_api.VB_GROUP(group).name}), check VPCT======')
                    else:
                        logger.info(f'====== VB {VB} grouptype = {group} ({project_api.VB_GROUP(group).name}), check VBINFO======')
                    logger.error_lb(f'check {name0}')
                    logger.error_fp(f'expect {name0} = {expect.value}, but current value = {raw.value}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            pass
    def reconfig_lun(self) -> None:
        config_descs = api.get_config_descriptors(print=False)
        for index in range(4):
            config_descs[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
        for index in range(4):
            api.push_write_config(config_descs[index], index=index)
        ExecuteCMD.send()
        return
    
    def push_spor(self, delay:int) -> None:
        power_cycle = ExecuteCMD.CmdSeqPowerCycle()
        power_cycle.set_option(mode=api.PowerCycleMode.ALL_POWER_DOWN, wait_queue_empty=True, delay_time=delay)
        ExecuteCMD.enqueue(power_cycle)
        for channel in range(1,3 +1):
            power_ctrl = ExecuteCMD.CmdSeqPowerControl()
            power_ctrl.set_option(
                mode=1,
                channel=channel,
                spendtime=500,
                ramptime=100,
                wait_queue_empty=True,
                delay_time=100
            )
            ExecuteCMD.enqueue(power_ctrl)

        power_cycle = ExecuteCMD.CmdSeqPowerCycle()
        power_cycle.set_option(mode=api.PowerCycleMode.LINK_START_UP, wait_queue_empty=True, delay_time=delay)
        ExecuteCMD.enqueue(power_cycle)
        nop = ExecuteCMD.CmdSeqPushNopOutPollNopIn()
        nop.set_option(timeout=5000, wait_queue_empty=True, delay_time=100)
        ExecuteCMD.enqueue(nop)        

    
    def create_VB_with_SPOR(self, lun:int) -> api.L2P_PCA:
        lba = 0
        chunk_size = api.BLOCK4K_SIZE_200M_BYTE
        datalen = self.tlc_vb_size//4
        api.sequential_write(lun=lun, start_lba=lba, total_size=datalen, chunk_size=chunk_size, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        lba += datalen
        apl_created = False
        delay = 100000
        logger.info("============= create APL ================")
        while not apl_created:
            temp_write_record = api.get_empty_write_record()
            write10 = ExecuteCMD.Write10()
            chunk_size = api.BLOCK4K_SIZE_64K_BYTE
            write10.assign(lun=lun, lba=lba, length=chunk_size, fua=0)
            write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX)
            ExecuteCMD.enqueue(write10)
            self.push_spor(delay=delay)
            ExecuteCMD.send(clear_on_success=False)
            for cmd in ExecuteCMD._cmd_list:
                api.save_write_info_by_cmd(cmd, temp_write_record)
            ExecuteCMD.clear()
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
            try:
                api.read_compare(temp_write_record, api.CompareMethod.SW_COMPARE)
                delay -= 50000
                if delay<0:
                    raise SIGHTING_RESPONSE_UNEXPECTED
            except DLL_CRC32_COMPARE_FAIL:
                ExecuteCMD.clear()
                apl_created = True
            lba+=chunk_size
        return lba_to_pba(lun=lun , lba=0)    
    
    def config_lun(self, normal_list:List[int], em1_list:List[int]) -> None:
        selector = 0x00
        length = 0xE6
        Total_AU_Count = shared.param.gGeometry.q4_total_raw_device_capacity // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
        EM1_total_AU = min(shared.param.gGeometry.l44_enhanced1_max_n_alloc_u, Total_AU_Count//(len(normal_list) + len(em1_list)) * len(em1_list))
        normal_total_AU = Total_AU_Count//(len(normal_list) + len(em1_list)) * len(normal_list)
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
                if lun in normal_list:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.NORMAL
                    desc.units[unit_idx].l4_num_alloc_units = (normal_total_AU) // len(normal_list)
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif lun in em1_list:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = (EM1_total_AU) // len(em1_list)
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
    
    def get_VB_group(self, show:bool = False) -> Dict[int, Dict[str, int]]:
        fw_geometry = api.get_fw_geometry()
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'access_mode': {'pos': 6, 'len': 2, 'mask': 0x3}, 
            'dirty': {'pos': 8, 'len': 1, 'mask': 0x1}, 
            'partition': {'pos': 9, 'len': 2, 'mask': 0x3}, 
            'cursor_idx': {'pos': 11, 'len': 1, 'mask': 0x1}, 
            'pte_tbl_mark': {'pos': 12, 'len': 1, 'mask': 0x1}, 
            'host_w_mark': {'pos': 13, 'len': 2, 'mask': 0x3}, 
            'src_uecc': {'pos': 15, 'len': 1, 'mask': 0x1}, 
            'vb_trim': {'pos': 16, 'len': 2, 'mask': 0x3}, 
            'risky_type': {'pos': 18, 'len': 2, 'mask': 0x3}, 
            'rsv': {'pos': 20, 'len': 12, 'mask': 0xFFF}, 
        }
        response, rep_data = api.get_vb_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data) // 4):
            if fw_geometry.l52_total_vb_count <= vb:
                break
            if vb * 4 + 3 >= len(rep_data):
                break
            raw = int.from_bytes(rep_data[vb*4:vb*4+4], byteorder='little')

            ftl_vb_list_data[vb] = {k: (raw >> v['pos']) & v['mask'] for k, v in vb_list_data_format.items()}

            ftl_vb_list_data.update({vb : {k: (((rep_data[vb*4]|rep_data[vb*4+1]<<8) >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        if show:
            for vb, info in ftl_vb_list_data.items():
                group = info['group']
                access_mode = info['access_mode']
                partition = info['partition']
                logger.info(f'VB {vb} grouptype = {group} ({project_api.VB_GROUP(group).name}), access_mode = {access_mode}, partition = {partition}')
        return ftl_vb_list_data
    
    def rpmb_key_programming(self) -> None:
        try:
            write_counter = self.rpmb.rpmb_read_counter()
        except SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
            self.rpmb.rpmb_key_programming()
            write_counter = self.rpmb.rpmb_read_counter()
            
    def polling_bkops_idle(self) -> None:
        while 1:
            bkops_status = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
            if bkops_status == 0:
                break
            time.sleep(1)
    
    def set_ec(self, set_ec:bytearray) -> None:
        total_VB_count = self.fw_geometry.l52_total_vb_count
        data = bytearray(b'\xFF' * 0x4000)
        del set_ec[total_VB_count*4:]
        data[:len(set_ec)] = set_ec

        api.ufs_api.vendor_cmd.access_vendor_mode()
        vuc = ExecuteCMD.VendorCmdWrite()
        vuc.assign(length=api.DATA_SIZE_16K_BYTE, cmd_index=api.VendorCmd.GET_FW_GEOMETRY, cmd_set_type=0x0F)
        vuc.upiu.u16_cdb.b2_rsvd = api.VendorCmdRuleCdb2.CMD_IN_CDB
        vuc.upiu.u16_cdb.b6_cmd2 = 4
        vuc.data = data
        vuc.enqueue()
        ExecuteCMD.send()

run = Pattern().run
if __name__ == "__main__":
    run()