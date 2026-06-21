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
from Script.project_api.custom_vu.do_power_loss_analysing_vu.functions import *
from Script.project_api.custom_vu.lba_convert_vu.structs import physical_address_info, logical_address_info
from Script.project_api.custom_vu.get_VB_list_info.functions import issue_4099_to_get_ftl_blk_list
from Script.api.ufs_api.vendor_cmd.functions import *
import copy

from Script.project_api.custom_vu.lba_convert_vu import issue_4051_to_get_physical_address, issue_4052_to_get_logical_address

from Script.project_api.custom_vu.raw_data_vu.functions import issue_4060_to_read_raw_data
from Script.project_api.reh.functions import issue_D014_to_set_read_recovery_module, \
    issue_40F9_to_get_rr_number_and_error_bits, \
    issue_D014_to_set_last_table_content, \
    issue_409E_to_get_ECC_information, \
    issue_409E_to_get_error_bit_numbers, \
    issue_40BB_to_get_error_bit_numbers_and_read_retry_step, \
    create_read_last_ref_table ,\
    get_page_type_by_physical_page ,\
    iter_reh_steps
from Script.project_api.custom_vu.erase_nand_pte.functions import issue_40F6_to_erase_in_direct_nand_mode
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

def is_bit3_set(n:int)->bool:
    # 0x08 是 1000 (binary)，即第3位为1，其余为0
    return (n & 0x08) != 0
def rebuild_payload_mv(src: bytearray) -> bytearray:
    mv = memoryview(src)                     # 零拷貝視圖
    # 計算新 payload 大小
    new_len = 16384 + (16452 - 16388)        # = 16448
    result = bytearray(new_len)

    # 前段
    result[:16384] = mv[:16384]
    # 後段
    result[16384:] = mv[16388:16452]

    return result
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
        self.config_lun()
        apl_pattern_precondition()

    def step1(self) -> None:
        #VC1
        ce_num = self.flash_setting.Max_Fdevice
        plane_num = self.flash_setting.Plane_Per_Die
        ce_plane_num = ce_num * plane_num
        tlc_ce_page = self.flash_setting.Plane_Per_Die * 4 * 3
        tlc_pageline = tlc_ce_page * ce_num
        slc_ce_page = self.flash_setting.Plane_Per_Die * 4
        per_tlcwl_cepage = 4 * ce_num * tlc_ce_page
        pattern_status = True
        isSLC = 0
        TLC = 0 #correct
        SLC = 1 #correct
        slc_max_page = 1103
        tlc_max_page = 3311
        for i in range(0,self.flash_setting.Plane_Per_Die):
            already_write_cepage= 0
            #VC4 &VC5
            newdata_pages = 2
            logger.flow(1, f'[write TLC vb until page5 last CE Plane5]')
            write_len = tlc_ce_page * ce_num * newdata_pages 
            old_data_startlba = tlc_ce_page * ce_num * 1 
            old_data_len = tlc_ce_page * ce_num * 1
            nonlwp_old_data_startlba = 0
            start_lba = 0
            api.sequential_write(lun=self.TestNormalLun, start_lba=start_lba, total_size=write_len, chunk_size=tlc_ce_page, fua = 1,
                            need_compare=True, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            already_write_cepage = already_write_cepage + write_len
            start_lba = start_lba + write_len
            
            logger.flow(2, f'[inject UECC on page3 CE0 plane{i}]')
            get_open_vb = self.get_and_print_open_vb_information()
            open_vb_1: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
            vb = open_vb_1.L2_Open_logical_VB_Host_TLC_number.value
            ce = 0
            plane = 0
            opcode = 0
            startpage = 0
            stoppage = tlc_max_page
            uecc_pca = PCA()
            uecc_pca.b10_block_l = vb & 0xFF
            uecc_pca.b11_block_h = (vb >> 8) & 0xFF
            uecc_pca.b5_ce = 0
            uecc_pca.b6_plane = i
            uecc_pca.b4_mode = 2 #tlc
            if(newdata_pages):
                uecc_pca.l12_fpage = (newdata_pages - 1) << 5
            inject_UECC(uecc_pca)
            if i%2 == 1: 
                logger.flow('2-1', f'[Non LWP inject UECC on page0 CE0 plane{i}]')
                uecc_pca.l12_fpage = 0
                inject_UECC(uecc_pca)
                nonlwp_old_data_startlba = 4*i
            logger.flow(3, f'get current LWP on each plane as LWP_A')
            lwpA = collect_lwp_checks(opcode, vb, TLC, startpage, stoppage)
            logger.flow(4, f'HW reset without SSU')
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
            get_open_vb = self.get_and_print_open_vb_information()
            open_vb_2: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
            vb = open_vb_2.L2_Open_logical_VB_Host_TLC_number.value
            logger.flow(5, f'get current LWP on each plane as LWP_B')
            lwpB = collect_lwp_checks(opcode, vb, TLC, startpage, stoppage)
            identical, diff_report = compare_lwp_checks(lwpA, lwpB)
            logger.flow(6, f'compare LWP_A and LWP_B should same')
            if identical == False:
                logger.error_lb(f'write data and SPOR and LWP check')
                logger.error_fp(f'expect LWP same, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
           
            if i%2 != 1:
                logger.flow(7, f'compare data, old data from UECC LBA ce page , others new')
            else:
                logger.flow(7, f'compare data, old data from UECC LBA ce page and non lwp UECC LBAs , others new')
            save_write_info(old_data_startlba, old_data_len, data_pattern_mode=CmdParamPatternMode.PTN_ERASE, add_tag=0, mark_tag=0, write_record=self.write_record[self.TestNormalLun])
            if i%2 == 1:
                save_write_info(nonlwp_old_data_startlba, 4, data_pattern_mode=CmdParamPatternMode.PTN_ERASE, add_tag=0, mark_tag=0, write_record=self.write_record[self.TestNormalLun])
                save_write_info(nonlwp_old_data_startlba+(slc_ce_page*1), 4, data_pattern_mode=CmdParamPatternMode.PTN_ERASE, add_tag=0, mark_tag=0, write_record=self.write_record[self.TestNormalLun])
                save_write_info(nonlwp_old_data_startlba+(slc_ce_page*2), 4, data_pattern_mode=CmdParamPatternMode.PTN_ERASE, add_tag=0, mark_tag=0, write_record=self.write_record[self.TestNormalLun])
            read_compare(self.write_record,CompareMethod.SW_COMPARE)
            self.config_lun()
        pass

    def post_process(self) -> None:
        pass

    def print_open_vb_information(self, open_vb_information:project_api.OpenVBInformation) -> None:
        logger.info('================= open_vb_information =================')
        print_object_info_ai(open_vb_information)
        return 
    def get_and_print_open_vb_information(self) -> project_api.OpenVBInformation:
        rsp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        self.print_open_vb_information(open_vb_information)
        return open_vb_information    
    def config_lun(self) -> None:
        _param = shared.param
        selector = 0x00
        length = 0xE6
        self.unit_desc_idxes:List[int] = []
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
            desc.header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.DISABLE
            desc.header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
            desc.header.l18_num_shared_write_booster_buffer_alloc_units = self.geometry_desc.l79_write_booster_buffer_max_n_alloc_units
            desc.header.l18_num_shared_write_booster_buffer_alloc_units = 0x1000

            for unit_idx in range(8):
                if index == 0 and unit_idx == self.TestNormalLun:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.NORMAL
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    #desc.units[unit_idx].l4_num_alloc_units = 8092
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == self.TestBootA:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_A
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == self.TestBootB:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_B
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == self.TestEM1Lun:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
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
           
        for lun in range(0, _param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(DescriptorIDN.UNIT, lun)
            self.unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in self.unit_desc_idxes:
            update_descriptor(DescriptorIDN.UNIT, index, cast(QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()
        #test unit ready all enable lun
        for lun in range(_param.gMaxNumberLU):
            if  _param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
        api.write_attribute(idn=api.AttributeIDN.BOOT_LUN_EN, val=api.BootLUNID.BOOT_LUN_A)
run = Pattern().run
if __name__ == "__main__":
    run()