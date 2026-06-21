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
from Script.project_api.functions import get_physical_layout, print_object_info_ai
from enum import auto

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = shared.param
        self.total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        config_lun(normal_list=[0], em1_list=[])
        leave_inhibition_mode()
        self.write_record = api.get_empty_write_record()
        _flash_setting = api.get_flash_setting()
        self.fw_geometry = api.get_fw_geometry()
        self.TLC_VB_AU_SIZE = self.fw_geometry.l88_vb_size_u1 // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.SLC_VB_AU_SIZE = self.fw_geometry.l84_vb_size_u0 // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.max_ce = _flash_setting.Max_Fdevice
        self.max_plane = _flash_setting.Plane_Per_Die
        self.pageline_block = self.max_ce * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        _, self.mConfig = project_api.get_mConfig_data()
        self.mConfig.payload[0:7] = "MCONFIG".encode("ascii")
        logger.info('Pre-process completed')
        pass

    
    def check_timeout(self,start_time: float, timeout_min: int) -> bool:
        current_time = time.time()
        if (current_time - start_time) >= timeout_min * 60:
            return True
        else:
            return False
        
    def write_until_threshold(self, lun:int, start_lba:int, threshold:int, loop:int=0)->int:
        sorted_VB_list_dict = get_sorted_VB_list()
        used_vb_cnt = len(sorted_VB_list_dict.get(project_api.VBListNum.USED_BLK_POOL_EM1, []))
        print(f'initial used vb cnt = {used_vb_cnt}')
        start_time = time.time()
        elapsed_time = 0
        timeout_min = 180
        while used_vb_cnt < threshold:
            if self.check_timeout(start_time, timeout_min):
                logger.error('fPolling write until used vb cnt >= gc threshold in 3 HOUR but timeout')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            total_len = self.slc_vb_size
            temp_lba = loop + start_lba
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

            ExecuteCMD.send(clear_on_success=False)
            ExecuteCMD.clear()
            
            sorted_VB_list_dict = get_sorted_VB_list()
            used_vb_cnt = len(sorted_VB_list_dict.get(project_api.VBListNum.USED_BLK_POOL_EM1, []))
            logger.info(f'used vb cnt = {used_vb_cnt}')
            loop += 1
        return loop
        

    def step1(self) -> None:
        class GC_case(IntEnum):
            L1_GC = auto()
            EM1_GC = auto()
            WB_GC = auto()
            PSA_GC = auto()
            DUMMY = auto()
        VB_list = []
        for testcase in GC_case:
            if testcase == GC_case.DUMMY:
                continue
            logger.info(f'=================== Test: {testcase.name} ======================')
            logger.flow(1, 'reconfig to clear data')
            api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            if testcase == GC_case.L1_GC:
                slc_lun, lun = self.config_lun(slc_au=0, tlc_au=self.total_au)
                pass
            elif testcase == GC_case.EM1_GC:
                lun, tlc_lun = self.config_lun(slc_au=self.SLC_VB_AU_SIZE * 20, tlc_au=0)
                slc_threshold, tlc_threshold = api.get_gc_threshold()
                pass
            elif testcase == GC_case.WB_GC:
                slc_lun, lun = self.config_lun(slc_au=0, tlc_au=self.total_au)
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)
                pass
            elif testcase == GC_case.PSA_GC:
                api.modify_desc_attr_flag(QuerryType=Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_ATTRIBUTE, Index=api.AttributeIDN.PSA_STATE, Value=0, IndexLen=1)
                slc_lun, lun = self.config_lun(slc_au=0, tlc_au=self.total_au)
                pass
            self.write_record = api.get_empty_write_record()
        
            logger.flow(2, 'write data to create source block')
            lba = 0
            if testcase == GC_case.PSA_GC:
                self.dev_desc = api.get_device_descriptor()
                api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=self.dev_desc.l37_psa_max_data_size)
                api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.PRE_SOLDERING)
                logger.info(f"PSA State = {api.read_attribute(idn=api.AttributeIDN.PSA_STATE)}")
                total_size = self.slc_vb_size
                api.sequential_write(lun=lun, start_lba=0, total_size=total_size, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 1,
                                need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                api.write_attribute(idn=api.AttributeIDN.PSA_STATE, val=api.PSAState.LOADING_COMPLETE)
                logger.info(f"PSA State = {api.read_attribute(idn=api.AttributeIDN.PSA_STATE)}")
            else:
                if testcase == GC_case.L1_GC:
                    chunk_size = self.pageline_block * 3
                else:
                    chunk_size = api.BLOCK4K_SIZE_16K_BYTE
                total_size = chunk_size
                api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunk_size, fua = 1,
                                need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            lba += total_size
            
            sorted_VB_list_dict_A = get_sorted_VB_list()
            
            logger.flow(3, 'issue D014 to trigger CECC on source block')
            self.VB, pca = get_PCA_VB_and_print(lun=lun, lba=0)
            isSLC = 1
            b=0
            s=1
            _ = project_api.issue_D014_to_set_read_recovery_module(
                die = pca.die.value, 
                bigIndex=b, 
                smallIndex=s, 
                nandMode=isSLC, 
                isSpeciBlock=1, 
                block=pca.physical_block_number_w_BBT.value, 
                isPSA=1 if testcase == GC_case.PSA_GC else 0)
            
            logger.flow(4, 'read compare data')
            api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)
                        
            logger.flow(5, 'Disable bkops')
            project_api.issue_D0FD_en_disable_BKOPS(bValue=2)
            
            logger.flow(6, 'continue write data to trigger GC')
            if testcase == GC_case.L1_GC:
                for vb in range(self.fw_geometry.l52_total_vb_count):
                    if testcase == GC_case.L1_GC and vb in sorted_VB_list_dict_A[project_api.VBListNum.CURRENT_L2_TLC]:
                        logger.info('Issue VU C012 to create erase fail.')
                        info = project_api.PhysicalAddressInformation()
                        info.BlockInfoList_0_die.value = 0
                        info.BlockInfoList_0_plane.value = 0
                        info.BlockInfoList_0_block.value = vb
                        info.BlockInfoList_0_page.value = 0
                        info.BlockInfoList_0_tg_bitmap.value = 0
                        project_api.issue_C012_to_create_program_erase_fail(info, fail_type=3, block_info_list_count=1, skip_uecc=0)
                        VB_list.append(vb)
                one_prog = self.max_plane * 3 *api.BLOCK4K_SIZE_16K_BYTE
                while one_prog:
                    chunk_size = api.BLOCK4K_SIZE_16K_BYTE
                    total_size = chunk_size
                    api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunk_size, fua = 1,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                    lba += total_size
                    one_prog -= chunk_size
                
                chunk_size = api.WRITE_10_MAX_BLOCK_LEN
                total_size = self.tlc_vb_size//2
                api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunk_size, fua = 1,
                                need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                lba += total_size
                one_prog -= chunk_size
                pass
            elif testcase == GC_case.EM1_GC:
                logger.info('Write until slc gc threshold')
                self.write_until_threshold(slc_lun, lba, slc_threshold)
                pass
            elif testcase == GC_case.WB_GC:
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                available_WB_size = 0xA
                start_time = time.time()
                timeout_min = 5
                while available_WB_size == 0xA:
                    if self.check_timeout(start_time = start_time, timeout_min = timeout_min):
                        logger.error_lb('Sequential write data for filling WB buffer size')
                        logger.error_fp(f'Flow timeout 5 min, current available WB size = 0x{available_WB_size:X}, write cumulative data size = {lba}')
                        raise SPEC_ASSERT_UFS_RSP_OP_SHALL_WRITE_ATTRIBUTE
                    api.sequential_write(lun=lun, start_lba=lba, total_size=self.tlc_vb_size, chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 1,
                                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                    lba += self.tlc_vb_size
                    available_WB_size = api.read_attribute(idn = api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)
                pass
            elif testcase == GC_case.PSA_GC:
                logger.info('POR')
                api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
                chunk_size = api.BLOCK4K_SIZE_16K_BYTE
                total_size = chunk_size
                logger.info('first write')
                api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunk_size, fua = 1,
                                need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
                lba += total_size
                logger.info(f"PSA State = {api.read_attribute(idn=api.AttributeIDN.PSA_STATE)}")
                pass
            
            logger.flow(7, 'Inject UECC in GC_DEST')
            sorted_VB_list_dict_B = get_sorted_VB_list()
            VPCT_list, VBINFO_list = self.get_all_VPCT_VBINFO_values()
            for vb in range(self.fw_geometry.l52_total_vb_count):
                if VBINFO_list[vb].VBINFO_BIT_GC_DEST.value:
                    logger.info('Issue VU C012 to create erase fail.')
                    info = project_api.PhysicalAddressInformation()
                    info.BlockInfoList_0_die.value = 0
                    info.BlockInfoList_0_plane.value = 0
                    info.BlockInfoList_0_block.value = vb
                    info.BlockInfoList_0_page.value = 6
                    info.BlockInfoList_0_tg_bitmap.value = 0
                    project_api.issue_C012_to_create_program_erase_fail(info, fail_type=3, block_info_list_count=1, skip_uecc=0)
                    VB_list.append(vb)
                    
            logger.flow(8, 'SPOR')
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)

            logger.flow(9, 'Enable bkops')
            project_api.issue_D0FD_en_disable_BKOPS(bValue=3)

            sorted_VB_list_dict_C = get_sorted_VB_list()
            logger.flow(10, 'polling until BKOP idle')
            polling_bkops_idle()
            
            sorted_VB_list_dict_D = get_sorted_VB_list()
            
            if testcase == GC_case.PSA_GC:
                api.modify_desc_attr_flag(QuerryType=Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_ATTRIBUTE, Index=api.AttributeIDN.PSA_STATE, Value=0, IndexLen=1)
            
            AA = self.invert_mapping(sorted_VB_list_dict_A)
            BB = self.invert_mapping(sorted_VB_list_dict_B)
            CC = self.invert_mapping(sorted_VB_list_dict_C)
            DD = self.invert_mapping(sorted_VB_list_dict_D)
            
            for vb in range(self.fw_geometry.l52_total_vb_count):
                type_A = AA.get(vb, project_api.VBListNum.OTHER)
                type_B = BB.get(vb, project_api.VBListNum.OTHER)
                type_C = CC.get(vb, project_api.VBListNum.OTHER)
                type_D = DD.get(vb, project_api.VBListNum.OTHER)
                if type_A == type_B and type_A == type_C and type_A == type_D:
                    continue
                else:
                    if VBINFO_list[vb].VBINFO_BIT_GC_FG_QUEUE.value:
                        q_mark = "(GC_FG_QUEUE)"
                    elif VBINFO_list[vb].VBINFO_BIT_GC_BG_QUEUE.value:
                        q_mark = "(GC_BG_QUEUE)"
                    else:
                        q_mark = ""
                    if VBINFO_list[vb].VBINFO_BIT_GC_SOURCE.value:
                        mark = "(GC_SOURCE)"
                    elif VBINFO_list[vb].VBINFO_BIT_GC_DEST.value:
                        mark = "(GC_DEST)"
                    else:
                        mark = ""
                    
                    logger.info(f"VB {vb} : {type_A.name} -> {type_B.name} -> {type_C.name} -> {type_D.name} {mark} {q_mark}")
            
            logger.flow(11, 'read compare data')
            api.read_compare(write_record = self.write_record, compare_method = api.CompareMethod.HW_COMPARE)
            continue
        
        logger.flow(12, 'Check BB retirement reason')
        check_BB_retirementafter_refresh(VB_list = VB_list, expect_reason=project_api.BBRetirementReaspnType.READBACK)
        pass
    

    def post_process(self) -> None:
        logger.info('Post process completed')
        pass
    
    
    def invert_mapping(self, data: Dict[project_api.VBListNum, List[int]]) -> Dict[int, project_api.VBListNum]:
        result = {}
        for vb_list_num, vb_list in data.items():
            for vb in vb_list:
                result[vb] = vb_list_num
        return result

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
            
    def config_lun(self,slc_au:int, tlc_au:int) -> tuple[int,int]:
        config_descs = api.get_config_descriptors(print=True)
        for table in range(4):
            for unit in range(8):
                config_descs[table].header.b2_conf_desc_continue = 1
                config_descs[table].units[unit].b0_lu_enable = 0
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].l4_num_alloc_units = 0
                config_descs[table].units[unit].b9_logical_block_size = 0xc
                config_descs[table].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                if (table * 8 + unit) == 0:
                    config_descs[table].units[unit].b0_lu_enable = 1 if slc_au else 0
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[table].units[unit].l4_num_alloc_units = slc_au
                elif (table * 8 + unit) == 1:
                    config_descs[table].units[unit].b0_lu_enable = 1 if tlc_au else 0
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[table].units[unit].l4_num_alloc_units = tlc_au

        config_descs[3].header.b2_conf_desc_continue = 0
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.ENABLE
        config_descs[0].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = shared.param.gGeometry.l79_write_booster_buffer_max_n_alloc_units

        for i in range(4):
            api.push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        ExecuteCMD.clear()

        unit_desc_idxes:List[int] = []
        for lun in range(0, self._param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()
        #test unit ready all enable lun
        for lun in range(self._param.gMaxNumberLU):
            if self._param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
        slc_lun = 0
        tlc_lun = 1
        return (slc_lun, tlc_lun)

run = Pattern().run

if __name__ == "__main__":
    run()