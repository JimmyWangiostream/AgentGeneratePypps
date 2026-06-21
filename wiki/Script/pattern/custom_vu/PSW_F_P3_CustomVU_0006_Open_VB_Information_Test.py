import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from typing import List, cast, Optional
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from time import sleep
import math
from typing import Any
from Script.project_api.functions import print_object_info_ai
import time

ENG2_WA = True

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = shared.param
        self.write_record = api.get_empty_write_record()
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.tlc_exceed_size = 50
        self.slc_exceed_size = 50
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.TestWBLun = 3
        pass

    def step1(self) -> None:
        logger.flow(1, 'config lun and RPMB key programming')
        self.config_lun(normal_list=[self.TestNormalLun, self.TestWBLun], em1_list=[self.TestEM1Lun])
        self.dev_desc = api.get_device_descriptor()
        self.rpmb = RPMB(RPMBRegion.REGION_0)
        self.rpmb_key_programming()
        pass

    def step2(self) -> None:
        logger.flow(2, 'write data to create open block')
        self.open_vb_information_original = self.get_and_print_open_vb_information()
        self.check_open_vb_information_value_default_exist(self.open_vb_information_original)
        api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=api.BLOCK4K_SIZE_1M_BYTE, chunk_size=api.BLOCK4K_SIZE_1M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        # self.print_l2p(lun = self.TestNormalLun, lba = 0)
        api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=api.BLOCK4K_SIZE_1M_BYTE, chunk_size=api.BLOCK4K_SIZE_1M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        # self.print_l2p(lun = self.TestEM1Lun, lba = 0)
        self.rpmb.rpmb_write_data(0,BLOCK256B_SIZE_4K_BYTE)
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)
        api.sequential_write(lun=self.TestWBLun, start_lba=0, total_size=api.BLOCK4K_SIZE_1M_BYTE, chunk_size=api.BLOCK4K_SIZE_1M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        # self.print_l2p(lun = self.TestWBLun, lba = api.BLOCK4K_SIZE_1M_BYTE-1)
        pass

    def step3(self) -> None:
        logger.flow(3, 'get original open_vb_information_before and check VB exist')
        self.ssu_sleep_and_active()
        self.open_vb_information_before = self.get_and_print_open_vb_information()
        self.print_info_different(self.open_vb_information_original, self.open_vb_information_before)
        self.check_open_vb_information_value_default_exist(self.open_vb_information_before)
        self.check_value_increase(self.open_vb_information_original, self.open_vb_information_before, "first_free_physical_page_of_L2_Open_logical_VB_Host_TLC")
        self.check_value_increase(self.open_vb_information_original, self.open_vb_information_before, "first_free_physical_page_of_Write_Booster_WB_L2")
        self.check_value_increase(self.open_vb_information_original, self.open_vb_information_before, "first_free_physical_page_of_SWAP_RAIN_TLC")
        self.check_value_increase(self.open_vb_information_original, self.open_vb_information_before, "first_free_physical_page_of_SWAP_RAIN_WB")
        self.check_value_increase(self.open_vb_information_original, self.open_vb_information_before, "List_block_First_free_physical_page")
        self.check_value_increase(self.open_vb_information_original, self.open_vb_information_before, "LOG_Block_First_free_physical_page")
        pass
        

    def step4(self) -> None:
        logger.flow(4, 'continue write data in open block')
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        api.sequential_write(lun=self.TestNormalLun, start_lba=api.BLOCK4K_SIZE_1M_BYTE, total_size=api.BLOCK4K_SIZE_1M_BYTE, chunk_size=api.BLOCK4K_SIZE_1M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        # self.print_l2p(lun = self.TestNormalLun, lba = 0)
        api.sequential_write(lun=self.TestEM1Lun, start_lba=api.BLOCK4K_SIZE_1M_BYTE, total_size=api.BLOCK4K_SIZE_1M_BYTE, chunk_size=api.BLOCK4K_SIZE_1M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        # self.print_l2p(lun = self.TestEM1Lun, lba = 0)
        self.rpmb.rpmb_write_data(BLOCK256B_SIZE_4K_BYTE,BLOCK256B_SIZE_4K_BYTE)
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        api.sequential_write(lun=self.TestWBLun, start_lba=api.BLOCK4K_SIZE_1M_BYTE, total_size=api.BLOCK4K_SIZE_1M_BYTE, chunk_size=api.BLOCK4K_SIZE_1M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        # self.print_l2p(lun = self.TestWBLun, lba = 0)
        self.ssu_sleep_and_active()
        pass

    def step5(self) -> None:
        logger.flow(5, 'get original open_vb_information_after and check criteria')
        self.ssu_sleep_and_active()
        self.open_vb_information_after = self.get_and_print_open_vb_information()
        self.print_info_different(self.open_vb_information_before, self.open_vb_information_after)
        self.check_open_vb_information_value_default_exist(self.open_vb_information_after)
        self.check_value_increase(self.open_vb_information_before, self.open_vb_information_after, "first_free_physical_page_of_L2_Open_logical_VB_Host_TLC")
        self.check_value_increase(self.open_vb_information_before, self.open_vb_information_after, "first_free_physical_page_of_EM1_L2_Host_VB")
        self.check_value_increase(self.open_vb_information_before, self.open_vb_information_after, "start_physical_page_of_VB_of_TMP_RAIN_VB_SSU_VB")
        self.check_value_increase(self.open_vb_information_before, self.open_vb_information_after, "first_free_physical_page_of_Write_Booster_WB_L2")
        self.check_value_increase(self.open_vb_information_before, self.open_vb_information_after, "first_free_physical_page_of_RPMB_VB")
        self.check_value_increase(self.open_vb_information_before, self.open_vb_information_after, "first_free_physical_page_of_SWAP_RAIN_TLC")
        self.check_value_increase(self.open_vb_information_before, self.open_vb_information_after, "first_free_physical_page_of_SWAP_RAIN_WB")
        self.check_value_increase(self.open_vb_information_before, self.open_vb_information_after, "first_free_physical_page_of_SWAP_RAIN_EM1")
        self.check_value_increase(self.open_vb_information_before, self.open_vb_information_after, "List_block_First_free_physical_page")
        self.check_value_increase(self.open_vb_information_before, self.open_vb_information_after, "PTE_block_First_free_physical_page")
        self.check_value_increase(self.open_vb_information_before, self.open_vb_information_after, "LOG_Block_First_free_physical_page")
        pass


    def step6(self) -> None:
        logger.flow(6, 'enable WB flush to create TLC GC')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        available_WB_size = 0xA
        start_time = time.time()
        timeout_min = 5
        lba = api.BLOCK4K_SIZE_1M_BYTE * 2
        while available_WB_size == 0xA:
            if self.check_timeout(start_time = start_time, timeout_min = timeout_min):
                logger.error_lb('Sequential write data for filling WB buffer size')
                logger.error_fp(f'Flow timeout 5 min, current available WB size = 0x{available_WB_size:X}, write cumulative data size = {lba}')
                raise SPEC_ASSERT_UFS_RSP_OP_SHALL_WRITE_ATTRIBUTE
            api.sequential_write(lun=0, start_lba=lba, total_size=self.tlc_vb_size, chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 1,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            lba += self.tlc_vb_size
            available_WB_size = api.read_attribute(idn = api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
        
        self.open_vb_information = self.get_and_print_open_vb_information()
        project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x00)
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)

        self.open_vb_information_TLC_GC = self.get_and_print_open_vb_information()
        self.print_info_different(self.open_vb_information, self.open_vb_information_TLC_GC)
        self.check_value_exist(self.open_vb_information_TLC_GC, "open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC")
        self.check_value_exist(self.open_vb_information_TLC_GC, "first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC")
        self.check_value_exist(self.open_vb_information_TLC_GC, "open_Remap_VB_number_for_GC_Open_VB_TLC")
        project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x01)
        self.polling_bkops_idle()
        pass

    def step7(self) -> None:
        logger.flow(7, 'write em1 to create EM1 GC')
        self.SLC_VB_AU_SIZE = self.fw_geometry.l84_vb_size_u0 // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.config_lun(normal_list=[], em1_list=[self.TestEM1Lun], slc_au=self.SLC_VB_AU_SIZE * 20)
        slc_threshold, tlc_threshold = api.get_gc_threshold()
        project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x02)
        self.write_until_threshold(self.TestEM1Lun, project_api.VBListNum.USED_BLK_POOL_EM1, slc_threshold)
        
        self.open_vb_information_EM1 = self.get_and_print_open_vb_information()
        self.print_info_different(self.open_vb_information_after, self.open_vb_information_EM1)
        self.check_value_exist(self.open_vb_information_EM1, "open_logical_VB_number_for_EM1_GC")
        self.check_value_exist(self.open_vb_information_EM1, "first_free_physical_page_of_EM1_GC_VB")
        self.check_value_exist(self.open_vb_information_EM1, "open_Remap_VB_number_for_EM1_GC")
        project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x03)
        self.polling_bkops_idle()
        pass
    
    def post_process(self) -> None:
        pass
    
    def check_timeout(self,start_time: float, timeout_min: int) -> bool:
        current_time = time.time()
        if (current_time - start_time) >= timeout_min * 60:
            return True
        else:
            return False
        
    def get_sorted_VB_list(self) -> Dict[project_api.VBListNum, List[int]]:
        resp = project_api.custom_vu.issue_406D_get_VB_list_info()
        sorted_VB_list_dict:Dict[project_api.VBListNum, List[int]] = {}
        offset = 0
        VB_list = 0
        while offset < len(resp.data):
            vb_count = int.from_bytes(resp.data[offset:offset+2], byteorder='little')
            offset +=2
            for i in range(vb_count):
                vb = int.from_bytes(resp.data[offset:offset+2], byteorder='little')
                if project_api.VBListNum(VB_list) not in sorted_VB_list_dict:
                    sorted_VB_list_dict[project_api.VBListNum(VB_list)] = []
                sorted_VB_list_dict[project_api.VBListNum(VB_list)].append(vb)
                offset +=2
            VB_list+=1
        return sorted_VB_list_dict
    
    def write_until_threshold(self, lun:int, vb_type:project_api.VBListNum, threshold:int, loop:int=0)->int:
        sorted_VB_list_dict = self.get_sorted_VB_list()
        used_vb_cnt = len(sorted_VB_list_dict.get(vb_type, []))
        print(f'initial used vb cnt = {used_vb_cnt}')
        start_time = time.time()
        elapsed_time = 0
        timeout_min = 180
        while used_vb_cnt < threshold:
            if self.check_timeout(start_time, timeout_min):
                logger.error('fPolling write until used vb cnt >= gc threshold in 3 HOUR but timeout')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            total_len = self.tlc_vb_size if "TLC" in vb_type.name else self.slc_vb_size
            temp_lba = loop
            while total_len > 0:
                data_len = min(total_len, WRITE_10_MAX_BLOCK_LEN)
                if (temp_lba + data_len) > self._param.gLUCapacity[lun]:
                    temp_lba = random.randint(0, self._param.gLUCapacity[lun] - data_len -1)
                write10 = ExecuteCMD.Write10()
                write10.assign(lun=lun, lba=temp_lba, length=data_len, fua=1)
                ExecuteCMD.enqueue(write10)
                logger.info(f'startlba={temp_lba},len={data_len}')
                temp_lba += data_len
                total_len -= data_len

            ExecuteCMD.send(clear_on_success=False, timeout=api.UniformTimeout(val=write10.param.l50_timeout//1000, unit=api.TimeResolution.ms))
            ExecuteCMD.clear()
            
            sorted_VB_list_dict = self.get_sorted_VB_list()
            used_vb_cnt = len(sorted_VB_list_dict.get(vb_type, []))
            logger.info(f'used vb cnt = {used_vb_cnt}')
            loop += 1
        return loop
    
    
    def print_l2p(self, lun:int, lba:int) -> None:
        _pca = lba_to_pba(lun, lba)
        pca = PCA()
        pca.from_bytes(bytearray(_pca.payload))
        logger.info(f'Lun{lun}, LBA = {lba}: Block = {(pca.b11_block_h<<8) | (pca.b10_block_l)}, mode = {pca.b4_mode}, CE = {pca.b5_ce}, Plane = {pca.b6_plane}, fPage = {pca.l12_fpage}({pca.l12_fpage>>5}<<5), lmu = {pca.b20_lmu}')
        return

    def get_and_print_open_vb_information(self) -> project_api.OpenVBInformation:
        rsp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        print_object_info_ai(open_vb_information)
        return open_vb_information

    def config_lun(self, normal_list:List[int], em1_list:List[int], slc_au:int = 0, tlc_au:int = 0) -> None:
        selector = 0x00
        length = 0xE6
        Total_AU_Count = shared.param.gGeometry.q4_total_raw_device_capacity // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
        EM1_total_AU = slc_au if slc_au else min(shared.param.gGeometry.l44_enhanced1_max_n_alloc_u, Total_AU_Count//(len(normal_list) + len(em1_list)) * len(em1_list))
        normal_total_AU = tlc_au if tlc_au else Total_AU_Count//(len(normal_list) + len(em1_list)) * len(normal_list)
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

    def rpmb_key_programming(self) -> None:
        try:
            write_counter = self.rpmb.rpmb_read_counter()
        except SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
            self.rpmb.rpmb_key_programming()
            write_counter = self.rpmb.rpmb_read_counter()

    def check_value_exist(self, before: Any, string:str) -> None:
        value_before = None
        for name, field in before.__dict__.items():
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value"):
                if name == string:
                    value_before = field.value
                    break
        if value_before == 0xFFFFFFFF:
            logger.error_lb(f'check {string}')
            logger.error_fp(f'expect {string} exist, but current value = {value_before}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    
    def check_value_increase(self, before_value: Any, cur_value: Any, string:str) -> None:
        current_fields = [
            (name, field) for name, field in cur_value.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        current_fields.sort(key=lambda kv: kv[1].start_offset)
        before_fields = [
            (name, field) for name, field in before_value.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        before_fields.sort(key=lambda kv: kv[1].start_offset)
        
        for (name0, current), (name1, before) in zip(
                                    current_fields,
                                    before_fields,
                                ):
            if name0 == string:
                value = current.value
                value_before = before.value
                if value <= value_before:
                    logger.error_lb(f'check {string} should increase')
                    logger.error_fp(f'expect {string} increased, but current value = {value}, before value = {value_before}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                return
            pass
        
    def check_open_vb_information_value_default_exist(self, open_vb_information:project_api.OpenVBInformation) -> None:
        self.check_value_exist(open_vb_information, "L2_Open_logical_VB_Host_TLC_number")
        self.check_value_exist(open_vb_information, "first_free_physical_page_of_L2_Open_logical_VB_Host_TLC")
        self.check_value_exist(open_vb_information, "open_Remap_VB_number_for_L2_Open_logical_VB_Host_TLC")
        self.check_value_exist(open_vb_information, "open_logical_VB_number_for_Write_Booster_WB_L2")
        self.check_value_exist(open_vb_information, "first_free_physical_page_of_Write_Booster_WB_L2")
        self.check_value_exist(open_vb_information, "open_Remap_VB_number_for_Write_Booster_WB_L2")
        self.check_value_exist(open_vb_information, "open_logical_VB_number_for_SWAP_RAIN_TLC")
        self.check_value_exist(open_vb_information, "first_free_physical_page_of_SWAP_RAIN_TLC")
        self.check_value_exist(open_vb_information, "open_Remap_VB_number_for_TLC_SWAP_RAIN")
        self.check_value_exist(open_vb_information, "start_physical_page_ofparity_storage_VB_for_SWAP_RAIN_TLC")
        self.check_value_exist(open_vb_information, "open_logical_VB_number_for_SWAP_RAIN_WB")
        self.check_value_exist(open_vb_information, "first_free_physical_page_of_SWAP_RAIN_WB")
        self.check_value_exist(open_vb_information, "open_Remap_VB_number_for_SWAP_RAIN_WB")
        self.check_value_exist(open_vb_information, "start_physical_page_ofparity_storage_of_SWAP_RAIN_WB")
        self.check_value_exist(open_vb_information, "List_Block_VB_number_logical")
        self.check_value_exist(open_vb_information, "List_Block_VB_number_Remap")
        self.check_value_exist(open_vb_information, "List_block_First_free_physical_page")
        self.check_value_exist(open_vb_information, "INDEX_VB_number_logical")
        self.check_value_exist(open_vb_information, "INDEX_VB_number_Remap")
        self.check_value_exist(open_vb_information, "INDEX_block_First_free_physical_page")
        self.check_value_exist(open_vb_information, "LOG_block_VB_number_logical")
        self.check_value_exist(open_vb_information, "LOG_Block_VB_number_Remap")
        self.check_value_exist(open_vb_information, "LOG_Block_First_free_physical_page")
        self.check_value_exist(open_vb_information, "L1_open_VB_S_CHUNK_logical_number")
        self.check_value_exist(open_vb_information, "L1_open_VB_S_CHUNK_VB_number_Remap")
        self.check_value_exist(open_vb_information, "L1_open_VB_S_CHUNK_first_free_physical_page")
        
    def check_open_vb_information_value_after_write_exist(self, open_vb_information:project_api.OpenVBInformation) -> None:
        self.check_value_exist(open_vb_information, "open_logical_VB_number_for_EM1_L2_Host")
        self.check_value_exist(open_vb_information, "first_free_physical_page_of_EM1_L2_Host_VB")
        self.check_value_exist(open_vb_information, "open_Remap_VB_number_for_EM1_L2_Host")
        self.check_value_exist(open_vb_information, "open_Logical_VB_of_TMP_RAIN_VB_SSU_VB")
        self.check_value_exist(open_vb_information, "open_Remap_VB_of_TMP_RAIN_VB_SSU_VB")
        self.check_value_exist(open_vb_information, "start_physical_page_of_VB_of_TMP_RAIN_VB_SSU_VB")
        self.check_value_exist(open_vb_information, "open_logical_VB_number_for_RPMB_VB")
        self.check_value_exist(open_vb_information, "first_free_physical_page_of_RPMB_VB")
        self.check_value_exist(open_vb_information, "open_Remap_VB_number_for_RPMB_VB")
        self.check_value_exist(open_vb_information, "open_logical_VB_number_for_SWAP_RAIN_EM1")
        self.check_value_exist(open_vb_information, "first_free_physical_page_of_SWAP_RAIN_EM1")
        self.check_value_exist(open_vb_information, "open_Remap_VB_number_for_SWAP_RAIN_EM1")
        self.check_value_exist(open_vb_information, "PTE_Block_VB_number_logical")
        self.check_value_exist(open_vb_information, "PTE_Block_VB_number_Remap")
        self.check_value_exist(open_vb_information, "PTE_block_First_free_physical_page")

    def ssu_sleep_and_active(self) -> None:
        ssu = ExecuteCMD.StartStopUnit()
        ssu.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0)
        ssu.set_option(wait_queue_empty=True)
        ExecuteCMD.enqueue(ssu)
        ssu.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0)
        ssu.set_option(wait_queue_empty=True)
        ExecuteCMD.enqueue(ssu)
        ExecuteCMD.send(clear_on_success=True)
        pass
    
    def check_format_value(self, before: Any, string:str, modify_value:int) -> None:
        value_before = None
        for name, field in before.__dict__.items():
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value"):
                if name == string:
                    value_before = field.value
                    break
        if value_before  != modify_value:
            logger.error_lb(f'check {string}')
            logger.error_fp(f'expect {string} equel to {modify_value}, but current value = {value_before}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def print_info_different(self, raw_value: Any, expect_value: Any) -> None:
        raw_fields = [
            (name, field) for name, field in raw_value.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        raw_fields.sort(key=lambda kv: kv[1].start_offset)
        expect_fields = [
            (name, field) for name, field in expect_value.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        expect_fields.sort(key=lambda kv: kv[1].start_offset)
        
        for (name0, raw), (name1, expect) in zip(
                                    raw_fields,
                                    expect_fields,
                                ):
            if hasattr(raw, "value") and hasattr(expect, "value") and name0 == name1:
                if raw.value != expect.value:
                    logger.info(f'{name0}: {raw.value} (0x{raw.value:X}) -> {expect.value} (0x{expect.value:X})')
            pass
    
    def polling_bkops_idle(self) -> None:
        while 1:
            bkops_status = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
            if bkops_status == 0:
                break
            time.sleep(1)
 

run = Pattern().run
if __name__ == "__main__":
    run()