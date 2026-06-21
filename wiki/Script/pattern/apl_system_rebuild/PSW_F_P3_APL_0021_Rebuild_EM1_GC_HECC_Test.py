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
_sdk = shared.sdk
_param = shared.param
class Access_Mode(int):
    ACCESS_MODE_SLC = 0
    ACCESS_MODE_MLC = 1
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
    def check_timeout(self,start_time: float, timeout_min: int) -> bool:
        current_time = time.time()
        if (current_time - start_time) >= timeout_min * 60:
            return True
        else:
            return False
    def write_until_threshold(self, lun:int, start_lba:int, threshold:int, loop:int=0)->int:
        self.write_record: List[List[api.WriteRecordNode]]
        erase_all_lun(self.write_record)        
        self.write_record = api.get_empty_write_record()
        sorted_VB_list_dict = get_sorted_VB_list()
        used_vb_cnt = len(sorted_VB_list_dict.get(project_api.VBListNum.USED_BLK_POOL_EM1, []))
        print(f'initial used vb cnt = {used_vb_cnt}')
        start_time = time.time()
        elapsed_time = 0
        timeout_min = 180
        
        project_api.issue_D0FD_disable_all_the_foreground_operations()
        project_api.issue_D0FD_disable_all_the_background_operations()
        # project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.DisableEnqueueInRefreshBQ)
        
        while used_vb_cnt < threshold:
            if self.check_timeout(start_time, timeout_min):
                logger.error('fPolling write until used vb cnt >= gc threshold in 3 HOUR but timeout')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            total_len = self.slc_vb_size
            temp_lba = loop + start_lba
            while total_len > 0:
                data_len = min(total_len, WRITE_10_MAX_BLOCK_LEN)
                if (temp_lba + data_len) > _param.gLUCapacity[lun]:
                    temp_lba = random.randint(0, _param.gLUCapacity[lun] - data_len -1)
                # write10 = ExecuteCMD.Write10()
                # write10.assign(lun=lun, lba=temp_lba, length=data_len, fua=1)
                # ExecuteCMD.enqueue(write10)
                # api.sequential_write(lun=lun, start_lba=temp_lba, total_size=data_len, chunk_size=data_len, fua = 1,
                #             need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                testlun = lun
                cmd_count = 1
                min_lun = lun
                max_lun = lun
                min_lba = 0
                max_lba = _param.gLUCapacity[testlun]
                min_size = data_len
                max_size = data_len
                api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            
                logger.info(f'startlba={temp_lba},len={data_len}')
                temp_lba += (data_len)
                total_len -= data_len

            # ExecuteCMD.send(clear_on_success=False)
            # ExecuteCMD.clear()
            
            sorted_VB_list_dict = get_sorted_VB_list()
            used_vb_cnt = len(sorted_VB_list_dict.get(project_api.VBListNum.USED_BLK_POOL_EM1, []))
            logger.info(f'used vb cnt = {used_vb_cnt}')
            loop += 1
            
            
            get_open_vb = self.get_and_print_open_vb_information()
            if get_open_vb.open_logical_VB_number_for_EM1_GC.value != 0xFFFFFFFF:
                project_api.issue_D0FD_enable_all_the_foreground_operations()
                project_api.issue_D0FD_enable_all_the_background_operations()
                project_api.issue_D0FD_disable_all_the_foreground_operations()
                project_api.issue_D0FD_disable_all_the_background_operations()
                get_open_vb = self.get_and_print_open_vb_information()
                if get_open_vb.first_free_physical_page_of_EM1_GC_VB.value != 0 and get_open_vb.first_free_physical_page_of_EM1_GC_VB.value != 0xFFFFFFFF:
                    break
                # else:
                #     project_api.issue_D0FD_enable_all_the_foreground_operations()
                #     project_api.issue_D0FD_enable_all_the_background_operations()
            # if used_vb_cnt > (threshold - 3):
            #     project_api.issue_D0FD_enable_all_the_foreground_operations()
            #     project_api.issue_D0FD_enable_all_the_background_operations()
            #     get_open_vb = self.get_and_print_open_vb_information()
            #     if get_open_vb.open_logical_VB_number_for_EM1_GC.value != 0xFFFFFFFF and get_open_vb.first_free_physical_page_of_EM1_GC_VB.value != 0:
            #         project_api.issue_D0FD_disable_all_the_foreground_operations()
            #         project_api.issue_D0FD_disable_all_the_background_operations()
            # if used_vb_cnt > (threshold - 2):
            #     project_api.issue_D0FD_enable_all_the_foreground_operations()
            #     project_api.issue_D0FD_enable_all_the_background_operations()
            #     time.sleep(5)

        return loop
    def polling_bkops_inprogress(self) -> None:
        while 1:
            bkops_status = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
            if bkops_status == 1:
                break
            time.sleep(1)
    def polling_bkops_idle(self) -> None:
        while 1:
            bkops_status = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
            if bkops_status == 0:
                break
            time.sleep(1)
    def config_lun_test(self,normal_list:List[int], em1_list:List[int],testlun:int) -> None:
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
                    if lun == testlun:
                        if random.randint(0,0):
                            desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                            logger.info(f'lun{testlun}, ProvisioningType discard')
                        else:
                            desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                            logger.info(f'lun{testlun}, ProvisioningType ERASE')
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
    def VCC_power_off_power_on(self) -> None:
        logger.info('VCC_power_off_power_on')
        _sdk.power_control(on_off_value=lib.Power_Control.POWER_OFF.value, channel_sel=lib.Power_Channel.POWER_CHANNEL_VCC.value)
        _sdk.power_control(on_off_value=lib.Power_Control.POWER_ON.value, channel_sel=lib.Power_Channel.POWER_CHANNEL_VCC.value)

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
        slc_threshold, tlc_threshold = api.get_gc_threshold()
        set_slc_threshold = 20
        logger.flow('1-1', 'Set SLC GC threshold as 10')
        logger.info(f'default mlc_gc_threhold = {tlc_threshold}')
        #api.ufs_api.vendor_cmd.set_gc_threshold(Access_Mode.ACCESS_MODE_SLC, set_slc_threshold)
        for i in range(0,self.flash_setting.Plane_Per_Die):
            already_write_cepage= 0
            newdata_pages = 2
            logger.flow(1, f'[write EM1 vb until page5 last CE Plane5 with slc ce page chunksize]')
            
            write_len = tlc_ce_page * ce_num * newdata_pages 
            old_data_startlba = tlc_ce_page * ce_num * 1 
            old_data_len = tlc_ce_page * ce_num * 1
            start_lba = 0
            already_write_cepage = already_write_cepage + write_len
            start_lba = start_lba + write_len
            
            #project_api.issue_D0FD_disable_all_the_foreground_operations()
            self.write_until_threshold(self.TestEM1Lun, project_api.VBListNum.USED_BLK_POOL_EM1, set_slc_threshold)
            get_open_vb = self.get_and_print_open_vb_information()
            open_vb_1: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
            vb = open_vb_1.open_logical_VB_number_for_EM1_GC.value
            
            opcode = 0
            startpage = 0
            stoppage = slc_max_page
            logger.flow('1-2', f'get current LWP on each plane as LWP_GC')
            lwp_gc = collect_lwp_checks(opcode, vb, SLC, startpage, stoppage)

            logger.flow(2, f'[inject UECC on page3 CE0 plane{i}]')
            ce = 0
            plane = 0
            uecc_pca = PCA()
            uecc_pca.b10_block_l = vb & 0xFF
            uecc_pca.b11_block_h = (vb >> 8) & 0xFF
            uecc_pca.b5_ce = 0
            uecc_pca.b6_plane = i
            if(newdata_pages):
                uecc_pca.l12_fpage = (lwp_gc[i].LWP.value) << 5
            inject_UECC(uecc_pca)
            logger.flow(2, f'[inject UECC on page0 CE0 plane{i}]')
            uecc_pca.l12_fpage = 0
            inject_UECC(uecc_pca)
            
            logger.flow(3, f'get current LWP on each plane as LWP_A')
            lwpA = collect_lwp_checks(opcode, vb, SLC, startpage, stoppage)
            logger.flow(4, f'HW reset without SSU')
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
            get_open_vb = self.get_and_print_open_vb_information()
            open_vb_2: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
            #vb = open_vb_2.L2_Open_logical_VB_Host_TLC_number.value
            logger.flow(5, f'get current LWP on each plane as LWP_B')
            lwpB = collect_lwp_checks(opcode, vb, SLC, startpage, stoppage)
            identical, diff_report = compare_lwp_checks(lwpA, lwpB)
            logger.flow(6, f'compare LWP_A and LWP_B should same')
            if identical == False:
                logger.error_lb(f'write data and SPOR and LWP check')
                logger.error_fp(f'expect LWP same, result Fail!')
                #raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            sorted_vb_list_from_VU = get_sorted_VB_group_from_VU_406D()
            errgroup = 0
            if vb not in sorted_vb_list_from_VU[14] and vb not in sorted_vb_list_from_VU[8] and vb not in sorted_vb_list_from_VU[24]: #14: used slc, 8: slc gc target
                for t in range(0,len(sorted_vb_list_from_VU)):
                    if vb in sorted_vb_list_from_VU[t]:
                        errgroup = t
                        break
                logger.error_lb(f'GC target UECC and spor')
                logger.error_fp(f'expect GC target should in used vb group or gc target, but in group{errgroup}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            logger.flow(7, f'compare data, all new')
            #save_write_info(old_data_startlba, old_data_len, data_pattern_mode=CmdParamPatternMode.PTN_ERASE, add_tag=0, mark_tag=0, write_record=self.write_record[self.TestNormalLun])
            read_compare(self.write_record,CompareMethod.HW_COMPARE)
            project_api.issue_D0FD_enable_all_the_foreground_operations()
            project_api.issue_D0FD_enable_all_the_background_operations()
            project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.EnableEnqueueInRefreshBQ)
            
            api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
            self.config_lun()
        logger.flow(24, 'Recover slc gc threshold')
        #api.ufs_api.vendor_cmd.set_gc_threshold(Access_Mode.ACCESS_MODE_SLC, slc_threshold)
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
        self.TLC_VB_AU_SIZE = self.fw_geometry.l88_vb_size_u1 // (_param.gGeometry.l13_segment_size * _param.gGeometry.b17_allocation_unit_size)
        self.SLC_VB_AU_SIZE = self.fw_geometry.l84_vb_size_u0 // (_param.gGeometry.l13_segment_size * _param.gGeometry.b17_allocation_unit_size)
        
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
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                elif index == 0 and unit_idx == self.TestBootA:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_A
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    desc.units[unit_idx].l4_num_alloc_units = 1
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                elif index == 0 and unit_idx == self.TestBootB:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_B
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    desc.units[unit_idx].l4_num_alloc_units = 1
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                elif index == 0 and unit_idx == self.TestEM1Lun:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    desc.units[unit_idx].l4_num_alloc_units = self.SLC_VB_AU_SIZE  * 10
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
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

    def flipbit_on_SLC_pca(self,pca: PCA | None = None, pca_micron: physical_address_info | None = None)->None:
        slc_ce_page = self.flash_setting.Plane_Per_Die * 4
        isSLC = 1
        micron_pca = physical_address_info()
        if pca is None and pca_micron is None:
            logger.error_lb(f'pca should not none')
            logger.error_fp(f'result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if pca_micron is not None:
            micron_pca = pca_micron
       
        opcode = 0
        startpage = 0
        stoppage = 1103

        rsp, lwpcheck_raw = issue_409D_to_do_power_loss_analysing(
                opcode,
                micron_pca.die.value,
                micron_pca.plane.value,
                micron_pca.virtual_block_number.value,
                isSLC,
                startpage,
                stoppage,
            )
            # 依型別檢查器的需求把回傳值轉為 APL_LWP_Check
        lwpcheck: APL_LWP_Check = cast(APL_LWP_Check, lwpcheck_raw)
        pagelist:List[bytearray] = []
        for idx_page in range(0,lwpcheck.LWP.value+1):
            if idx_page == micron_pca.page.value:
                logger.info(f'VU 4060 read raw data on page {idx_page} with ECC off')
                _, raw_data = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=0)
                #dumpfile("read_raw_data.bin", raw_data)
                flip_data = copy.deepcopy(raw_data)
                flipBitCount = 100
                flipbit = flipBitCount
                flipped = flip_bits_one_per_byte(flip_data, total_bits=flipbit, block_index=0) 
                diffcount = count_diff_bytes(raw_data, flip_data)
                logger.info(f'LP different count ={diffcount} after flip bits {flipbit}')
                
                print_bit_positions(flipped, title=f"{flipbit} bits position")
                logger.info(f"Flip first {flipbit} bits – done")
                logger.info(f"raw_data_flip = {len(flip_data)}") 
                write_payload = flip_data 
                pagelist.append(flip_data)
            else:
                logger.info(f'VU 4060 read raw data on page {idx_page} with ECC off')
                _, raw_data_nonflip = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=idx_page, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=0)
                #dumpfile("read_raw_data_nonflop.bin", raw_data_nonflip)
                pagelist.append(raw_data_nonflip)
        #erase
        logger.info('issue D060 to erase original data')
        project_api.issue_D060_to_erase_specific_block(Ce=micron_pca.die.value,Plane=micron_pca.plane.value,Block=micron_pca.virtual_block_number.value,SlcEnable=isSLC, psaEnable = 0)
            
        #write raw data
        for idx_page in range(0,lwpcheck.LWP.value+1):
            write_payload = pagelist[idx_page]
            #dumpfile(f"write_raw_data.bin", write_payload)
            _ = project_api.issue_C060_to_write_raw_data(Ce=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=idx_page, SLC_Enable=isSLC,Ecc_Enable=0, datapayload=write_payload)
        
        #read raw data
        _, raw_data_1 = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=1, Scrambler_Enable=1, PSA_Enable=0)
        raw_data_11 = copy.deepcopy(raw_data_1)
        # diffcount = self.count_diff_bytes(raw_dataLP, raw_data_11)
        diffcount = count_diff_bytes(raw_data, raw_data_1)
        logger.info(f'LP different count ={diffcount}')
        #dumpfile(f"FW_FLOW_READ.bin", raw_data_1)

        logger.info(f'Issue 409E VUC with ECC information = 1 to get error bit numbers')
        _, output_409E = issue_409E_to_get_error_bit_numbers()
        error_bits_409E = [output_409E.errorBitNumber1.value, output_409E.errorBitNumber2.value, output_409E.errorBitNumber3.value, output_409E.errorBitNumber4.value]
        logger.info(f'409E error bits ={error_bits_409E}')

        _, raw_data_after_flip = issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=0)
        #dumpfile(f"pageLP_after.bin", raw_data_after_flip)
        diffcount = count_diff_bytes(raw_data, raw_data_after_flip)
        logger.info(f'LP different count ={diffcount}')
        pass
run = Pattern().run
if __name__ == "__main__":
    run()