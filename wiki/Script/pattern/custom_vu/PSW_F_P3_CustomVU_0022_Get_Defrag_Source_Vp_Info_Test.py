import package_root
import time
from Script import api
from typing import cast
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.ufs_api.defines.enum_define import QueryResponseCode, DescriptorIDN
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api import shared
from Script.lib import sdk_lib as lib
import random
from Script.api.exception import *
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from Script.api.ufs_api import *
from typing import cast, List
from Script.project_api.functions import print_object_info_ai

CHUNK_SIZE: int = 4 * 1024  # 4 KB

#_sdk = shared.sdk

def check_timeout(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.EnableMDWLSV = 0
        self.write_record = api.get_empty_write_record()
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestEM1Lun = 1
        self.Total_AU_Count = self.geometry_desc.q4_total_raw_device_capacity / (self.geometry_desc.l13_segment_size * self.geometry_desc.b17_allocation_unit_size);
        

    def step1(self) -> None:
        
        logger.flow(1, 'config lun and WB')
        self.config_lun()
        _param = api.shared.param
        start_time = time.time()
        timeout_min = 15
        
        logger.flow(2, 'Disable WB buffer flush')
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)

        logger.flow(3, 'Write for fill WB buffer until ava wb = 0')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        while True:
            if check_timeout(start_time, timeout_min):
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            cmd_count = random.randint(10, 32)
            min_lun = 0
            max_lun = 0
            min_lba = 0
            max_lba = _param.gLUCapacity[0]
            min_size = api.BLOCK4K_SIZE_64M_BYTE
            max_size = api.BLOCK4K_SIZE_128M_BYTE 
            api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            
            ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
            logger.info(f'Available WB size = {ava_WB_size}')
            if ava_WB_size is 0x0:
                break
        self.next_open_vb_information_after = self.get_and_print_next_open_vb_information(0)  
        logger.flow(4, 'Enable WB buffer flush')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)

        logger.flow(5, 'Polling flush status until in progress')
        polling_cnt = 0
        start_time = time.time()
        while True:
            if check_timeout(start_time, timeout_min):
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            WB_flush_status = api.read_attribute(idn=api.AttributeIDN.WRITEBOOSTER_BUFFER_FLUSH_STATUS)
            ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
            polling_cnt += 1
            logger.info(f'WB flush status = {WB_flush_status}, Available WB size = {ava_WB_size}, polling count = {polling_cnt}')
            if WB_flush_status is 0x01:
                logger.flow(6, 'Host issue VU 0xD0FD with value 0x00-disable all the background operations')
                project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x00)
                break
        
        vb = self.show_vb_info(10)
        #vb = self.next_open_vb_information_after.DM_NORMAL_DEFRAG_VB.value
        die = 0
        plane = 0
        page = 0
        vpIndex = 0

        logger.flow(7, 'issue VU 0x40DD to get GC target vb ,  source vp of first page')
        rsp, sourcevpInfo = project_api.issue_40DD_to_get_defrag_source_vp_information(vb,die,plane,page,vpIndex)
        print_object_info_ai(sourcevpInfo)

        
        logger.flow(8, f'Direct read GC target first page, VB {vb}, Die {die}, Plane {plane}')
        direc_read_pca = PCA()
        direc_read_pca.l0_op = 0x20000
        direc_read_pca.l0_op = 0
        direc_read_pca.b4_mode = 2 #SLC
        direc_read_pca.b5_ce = die
        direc_read_pca.b6_plane = plane
        direc_read_pca.b11_block_h = (vb>>8) & 0xFF
        direc_read_pca.b10_block_l = vb & 0xFF
        direc_read_pca.l12_fpage = 0
        dire_read_payload = api.direct_read(pca=direc_read_pca, block_count=1, include_FW_spare=True)
        logger.info(f'Block = {(direc_read_pca.b11_block_h<<8) | (direc_read_pca.b10_block_l)}, mode = {direc_read_pca.b4_mode}, CE = {direc_read_pca.b5_ce}, Plane = {direc_read_pca.b6_plane}, fPage = {direc_read_pca.l12_fpage}({direc_read_pca.l12_fpage>>5}<<5), lmu = {direc_read_pca.b20_lmu}, FW_Sapre = {dire_read_payload[api.DATA_SIZE_4K_BYTE*1 + 4]}')
        
        dumpfile("directread_data.bin", bytearray(dire_read_payload))

        logger.flow(9, f'Direct read source vp, VB {sourcevpInfo.vbnum.value}, Die {sourcevpInfo.die.value}, Plane {sourcevpInfo.plane.value}, Page {sourcevpInfo.page.value}, vpindex {sourcevpInfo.vpindex.value}')
        direc_read_pca = PCA()
        direc_read_pca.l0_op = 0x20000
        direc_read_pca.l0_op = 0
        direc_read_pca.b4_mode = 1 #SLC
        direc_read_pca.b5_ce = sourcevpInfo.die.value
        direc_read_pca.b6_plane = sourcevpInfo.plane.value
        direc_read_pca.b11_block_h = (sourcevpInfo.vbnum.value>>8) & 0xFF
        direc_read_pca.b10_block_l = sourcevpInfo.vbnum.value & 0xFF
        direc_read_pca.l12_fpage = sourcevpInfo.page.value << 5 | (sourcevpInfo.vpindex.value*8)
        dire_read_payload1 = api.direct_read(pca=direc_read_pca, block_count=1, include_FW_spare=True)
        logger.info(f'Block = {(direc_read_pca.b11_block_h<<8) | (direc_read_pca.b10_block_l)}, mode = {direc_read_pca.b4_mode}, CE = {direc_read_pca.b5_ce}, Plane = {direc_read_pca.b6_plane}, fPage = {direc_read_pca.l12_fpage}({direc_read_pca.l12_fpage>>5}<<5), lmu = {direc_read_pca.b20_lmu}, FW_Sapre = {dire_read_payload[api.DATA_SIZE_4K_BYTE*1 + 4]}')
        
        logger.flow(10, f'Compare GC target vb first page data and source vp data should pass')
        dumpfile("directread_data1.bin", bytearray(dire_read_payload))
        if self.compare_first_4k_bytes(dire_read_payload, dire_read_payload1) == False:
            logger.error_lb(f'issue direct read to compare source vp and gc target node')
            logger.error_fp(f'expect comapre pass, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        # direc_read_pca = PCA()
        # direc_read_pca.l0_op = 0x20000
        # direc_read_pca.l0_op = 0
        # direc_read_pca.b4_mode = 2 #SLC
        # direc_read_pca.b5_ce = sourcevpInfo.die.value
        # direc_read_pca.b6_plane = sourcevpInfo.plane.value
        # direc_read_pca.b11_block_h = (sourcevpInfo.vbnum.value>>8) & 0xFF
        # direc_read_pca.b10_block_l = sourcevpInfo.vbnum.value & 0xFF
        # direc_read_pca.l12_fpage = sourcevpInfo.page.value << 5 | (sourcevpInfo.vpindex.value *8)
        # dire_read_payload = api.direct_read(pca=direc_read_pca, block_count=1, include_FW_spare=True)
        # logger.info(f'Block = {(direc_read_pca.b11_block_h<<8) | (direc_read_pca.b10_block_l)}, mode = {direc_read_pca.b4_mode}, CE = {direc_read_pca.b5_ce}, Plane = {direc_read_pca.b6_plane}, fPage = {direc_read_pca.l12_fpage}({direc_read_pca.l12_fpage>>5}<<5), lmu = {direc_read_pca.b20_lmu}, FW_Sapre = {dire_read_payload[api.DATA_SIZE_4K_BYTE*1 + 4]}')
        
        # dumpfile("directread_data2.bin", bytearray(dire_read_payload))
        pass

    def post_process(self) -> None:
        pass
    def print_next_open_vb_information(self, next_open_vb_information:project_api.NextOpenVBInformation) -> None:
        logger.info('================= Next_open_vb_information =================')
        logger.info(f'amountofvalidvb={hex(next_open_vb_information.amountofvalidvb.value)}')
        logger.info(f'DM_NORMAL_HOST_VB={hex(next_open_vb_information.DM_NORMAL_HOST_VB.value)}')
        logger.info(f'DM_NORMAL_WB_VB_0={hex(next_open_vb_information.DM_NORMAL_WB_VB_0.value)}')
        logger.info(f'DM_NORMAL_SHARE_VB_1={hex(next_open_vb_information.DM_NORMAL_SHARE_VB_1.value)}')
        logger.info(f'DM_NORMAL_SHARE_VB_0={hex(next_open_vb_information.DM_NORMAL_SHARE_VB_0.value)}')
        logger.info(f'DM_RPMB_HOST_VB={hex(next_open_vb_information.DM_RPMB_HOST_VB.value)}')
        logger.info(f'DM_NORMAL_DEFRAG_VB={hex(next_open_vb_information.DM_NORMAL_DEFRAG_VB.value)}')
        logger.info(f'DM_EM1_DEFRAG_VB={hex(next_open_vb_information.DM_EM1_DEFRAG_VB.value)}')
        logger.info(f'List={hex(next_open_vb_information.List.value)}')
        logger.info(f'PTE={hex(next_open_vb_information.PTE.value)}')
        logger.info(f'LOG={hex(next_open_vb_information.LOG.value)}')
        logger.info(f'Index={hex(next_open_vb_information.Index.value)}')
        logger.info(f'DM_RAIN_PARITY_VB={hex(next_open_vb_information.DM_RAIN_PARITY_VB.value)}')
        logger.info(f'TMP_RAIN={hex(next_open_vb_information.TMP_RAIN.value)}')
        logger.info(f'Drive_Log={hex(next_open_vb_information.Drive_Log.value)}')
        logger.info(f'Pointer={hex(next_open_vb_information.Pointer.value)}')
        logger.info(f'BBT={hex(next_open_vb_information.BBT.value)}')

        return   
    def get_and_print_next_open_vb_information(self, openvbtype: int) -> project_api.NextOpenVBInformation:
        rsp, next_open_vb_information = project_api.issue_40DC_to_get_next_open_vb_information(openvbtype)
        print_object_info_ai(next_open_vb_information)
        #self.print_next_open_vb_information(next_open_vb_information)
        return next_open_vb_information  
    
    def print_open_vb_information(self, open_vb_information:project_api.OpenVBInformation) -> None:
        logger.info('================= open_vb_information =================')
        logger.info(f'Byte[{open_vb_information.L2_Open_logical_VB_Host_TLC_number.start_offset}:{open_vb_information.L2_Open_logical_VB_Host_TLC_number.end_offset}]: L2_Open_logical_VB_Host_TLC_number = {open_vb_information.L2_Open_logical_VB_Host_TLC_number.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_L2_Open_logical_VB_Host_TLC.start_offset}:{open_vb_information.first_free_physical_page_of_L2_Open_logical_VB_Host_TLC.end_offset}]: first_free_physical_page_of_L2_Open_logical_VB_Host_TLC = {open_vb_information.first_free_physical_page_of_L2_Open_logical_VB_Host_TLC.value}')
        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC.start_offset}:{open_vb_information.open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC.end_offset}]: open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC = {open_vb_information.open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC.start_offset}:{open_vb_information.first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC.end_offset}]: first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC = {open_vb_information.first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC.value}')

        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_EM1_L2_Host.start_offset}:{open_vb_information.open_logical_VB_number_for_EM1_L2_Host.end_offset}]: open_logical_VB_number_for_EM1_L2_Host = {open_vb_information.open_logical_VB_number_for_EM1_L2_Host.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_EM1_L2_Host_VB.start_offset}:{open_vb_information.first_free_physical_page_of_EM1_L2_Host_VB.end_offset}]: first_free_physical_page_of_EM1_L2_Host_VB_ = {open_vb_information.first_free_physical_page_of_EM1_L2_Host_VB.value}')
        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_EM1_GC.start_offset}:{open_vb_information.open_logical_VB_number_for_EM1_GC.end_offset}]: open_logical_VB_number_for_EM1_GC = {open_vb_information.open_logical_VB_number_for_EM1_GC.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_EM1_GC_VB.start_offset}:{open_vb_information.first_free_physical_page_of_EM1_GC_VB.end_offset}]: first_free_physical_page_of_EM1_GC_VB = {open_vb_information.first_free_physical_page_of_EM1_GC_VB.value}')
        
        
        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_Write_Booster_WB_L2.start_offset}:{open_vb_information.open_logical_VB_number_for_Write_Booster_WB_L2.end_offset}]: open_logical_VB_number_for_Write_Booster_WB_L2 = {open_vb_information.open_logical_VB_number_for_Write_Booster_WB_L2.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_Write_Booster_WB_L2.start_offset}:{open_vb_information.first_free_physical_page_of_Write_Booster_WB_L2.end_offset}]: first_free_physical_page_of_Write_Booster_WB_L2 = {open_vb_information.first_free_physical_page_of_Write_Booster_WB_L2.value}')
        logger.info(f'Byte[{open_vb_information.open_Remap_VB_number_for_Write_Booster_WB_L2.start_offset}:{open_vb_information.open_Remap_VB_number_for_Write_Booster_WB_L2.end_offset}]: open_Remap_VB_number_for_Write_Booster_WB_L2 = {open_vb_information.open_Remap_VB_number_for_Write_Booster_WB_L2.value}')
        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_RPMB_VB.start_offset}:{open_vb_information.open_logical_VB_number_for_RPMB_VB.end_offset}]: open_logical_VB_number_for_RPMB_VB = {open_vb_information.open_logical_VB_number_for_RPMB_VB.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_RPMB_VB.start_offset}:{open_vb_information.first_free_physical_page_of_RPMB_VB.end_offset}]: first_free_physical_page_of_RPMB_VB = {open_vb_information.first_free_physical_page_of_RPMB_VB.value}')
        logger.info(f'Byte[{open_vb_information.open_Remap_VB_number_for_RPMB_VB.start_offset}:{open_vb_information.open_Remap_VB_number_for_RPMB_VB.end_offset}]: open_Remap_VB_number_for_RPMB_VB = {open_vb_information.open_Remap_VB_number_for_RPMB_VB.value}')
        
        logger.info(f'Byte[{open_vb_information.PTE_Block_VB_number_logical.start_offset}:{open_vb_information.PTE_Block_VB_number_logical.end_offset}]: PTE_Block_VB_number_logical = {open_vb_information.PTE_Block_VB_number_logical.value}')
        logger.info(f'Byte[{open_vb_information.PTE_block_First_free_physical_page.start_offset}:{open_vb_information.PTE_block_First_free_physical_page.end_offset}]: PTE_block_First_free_physical_page = {open_vb_information.PTE_block_First_free_physical_page.value}')
        return 

    def get_and_print_open_vb_information(self) -> project_api.OpenVBInformation:
        rsp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        self.print_open_vb_information(open_vb_information)
        return open_vb_information    
    def show_vb_info(self, group:int)-> int:
        retval = 0
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'dirty': {'pos': 6, 'len': 1, 'mask': 0x1}, 
            'access_mode': {'pos': 7, 'len': 1, 'mask': 0x1}, 
        }
        response, rep_data = get_vb_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data)):
            if self.fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break
            ftl_vb_list_data.update({vb : {k: ((rep_data[vb*4] >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        used_mlc_cout = 0
        
        logger.info(f'[show all vb info at begin]')
        for vb, vb_info in ftl_vb_list_data.items():
            last_type = vb_info['group']
            logger.info(f'[vb = {vb}, group type = {last_type}]')
            if last_type == group:
                return vb
        return retval
    
    def compare_first_4k_bytes(self,payload_a: bytes, payload_b: bytes) -> bool:
        """回傳兩個 `bytes` 變數前 4 KB 是否相同。"""
        a_head: bytes = payload_a[:CHUNK_SIZE]
        b_head: bytes = payload_b[:CHUNK_SIZE]
        return a_head == b_head 
    
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
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /2)
                    #desc.units[unit_idx].l4_num_alloc_units = 8092
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == self.TestEM1Lun:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /2)
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
run = Pattern().run
if __name__ == "__main__":
    run()