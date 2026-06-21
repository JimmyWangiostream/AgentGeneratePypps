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

class Pattern(UFSTC):
    def compare_pca_info(self, first_pca: PCA, second_pca: PCA) -> bool:
        #phison_ppage = self.wl_page_2_physical_page(phison_pca.b4_mode.value, phison_pca.w46_page.value, phison_pca.b20_lmu.value)
        #phison_offset = int((phison_pca.l12_fpage.value - phison_pca.w46_page.value *32) /8)
        logger.info(f'first_pca.b10_block_l = {first_pca.b10_block_l}, first_pca.b6_plane  = {first_pca.b6_plane}, first_pca.b5_ce ={first_pca.b5_ce}, first_pca.b11_block_h= {first_pca.b11_block_h}')
        logger.info(f'second_pca.b10_block_l = {second_pca.b10_block_l}, second_pca.b6_plane  = {second_pca.b6_plane}, second_pca.b5_ce ={second_pca.b5_ce}, second_pca.b11_block_h= {second_pca.b11_block_h}')
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
        self.config_lun()


    def step1(self) -> None:
        
        ce_num = self.flash_setting.Max_Fdevice
        plane_num = self.flash_setting.Plane_Per_Die
        ce_plane_num = ce_num * plane_num
        tlc_ce_page = self.flash_setting.Plane_Per_Die * 4 * 3
        tlc_pageline = tlc_ce_page * ce_num
        slc_ce_page = self.flash_setting.Plane_Per_Die * 4
        pattern_status = True
        FW_spare:List[bytearray] = []
        FW_spare.clear()
        logger.flow(1, f'GET Open vb information by VU 0x40C1 as table1')
        get_open_vb = get_and_print_open_vb_information()
        open_vb_1: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
        logger.flow(2, f'HW reset without SSU')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
        
        logger.flow(3, f'GET Open vb information by VU 0x40C1 as table2')
        get_open_vb = get_and_print_open_vb_information()
        open_vb_2: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
        logger.flow(4, 'compare table2 should same with table1')
        vb = open_vb_1.LOG_block_VB_number_logical.value
        vb2 = open_vb_2.LOG_block_VB_number_logical.value
        fep = open_vb_1.LOG_Block_First_free_physical_page.value
        fep2 = open_vb_2.LOG_Block_First_free_physical_page.value
        if vb != vb2 :
            logger.error_lb(f'Without UECC ')
            logger.error_fp(f'expect Log not refresh, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #VC3
        startoffset = 1
        num = 1
        logger.flow(5, f'GET Open vb information by VU 0x40C1 as table3')
        get_open_vb = get_and_print_open_vb_information()
        open_vb_current: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
        pca = PCA()
        vb = open_vb_current.LOG_block_VB_number_logical.value
        fep = open_vb_current.LOG_Block_First_free_physical_page.value
        pca.b10_block_l = open_vb_current.LOG_block_VB_number_logical.value & 0xFF
        pca.b11_block_h = (open_vb_current.LOG_block_VB_number_logical.value >> 8) & 0xFF
        findcnt = 0
        lastvalid = 0
        secondvalid = 0
        splitinfo: List[int] = [] 
        for i in range(1,open_vb_current.LOG_Block_First_free_physical_page.value):
            pca.b5_ce = ((open_vb_current.LOG_Block_First_free_physical_page.value - i)  % ce_plane_num) // plane_num
            pca.b6_plane = ((open_vb_current.LOG_Block_First_free_physical_page.value - i)  % ce_plane_num) % plane_num
            pca.l12_fpage = ((open_vb_current.LOG_Block_First_free_physical_page.value - i) // ce_plane_num) << 5
            
            #pca.l0_op = 0x20000
            pca.l0_op = 0
            pca.b4_mode = 1
            dire_read_payload = api.direct_read(pca=pca, block_count=4, include_FW_spare=True)
            dumpfile('testlogread.bin',dire_read_payload)
            if dire_read_payload[0x4004] == 0x94:
                if findcnt == 0:
                    lastvalid = i
                    findcnt = findcnt+1
                elif findcnt == 1:
                    secondvalid = i
                    break
        logger.flow(6, 'inject UECC on Log LWP-1 page')
        startoffset = lastvalid -1
        injectUECC_from_FEP(vb,fep,startoffset,num)
        logger.flow(7, f'HW reset without SSU')
        status = SPOR_init_mp()
        if status == False:
            pattern_status = False
            logger.error_lb(f'inject uecc unitl last ics plane on List VB and SPOR ')
            logger.error_fp(f'expect SPOR Pass, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.flow(8, f'GET Open vb information by VU 0x40C1 as table4')
        get_open_vb = get_and_print_open_vb_information()
        open_vb_after: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
        
        logger.flow(9, 'compare table4 should different with table5')
        vb = open_vb_current.LOG_block_VB_number_logical.value
        vb2 = open_vb_after.LOG_block_VB_number_logical.value
        fep = open_vb_current.LOG_Block_First_free_physical_page.value
        fep2 = open_vb_after.LOG_Block_First_free_physical_page.value
        if compare_vb_fep(vb,vb2,fep,fep2):
            logger.error_lb(f'inject UECC on Log LWP-1 page and SPOR ')
            logger.error_fp(f'expect List refresh, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #VC3 more case
        startoffset = 1
        num = 1
        logger.flow(10, f'GET Open vb information by VU 0x40C1 as table5')
        get_open_vb = get_and_print_open_vb_information()
        open_vb_current: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
        pca = PCA()
        vb = open_vb_current.LOG_block_VB_number_logical.value
        fep = open_vb_current.LOG_Block_First_free_physical_page.value
        pca.b10_block_l = open_vb_current.LOG_block_VB_number_logical.value & 0xFF
        pca.b11_block_h = (open_vb_current.LOG_block_VB_number_logical.value >> 8) & 0xFF
        findcnt = 0
        lastvalid = 0
        secondvalid = 0
        splitinfo = [] 
        for i in range(1,open_vb_current.LOG_Block_First_free_physical_page.value):
            pca.b5_ce = ((open_vb_current.LOG_Block_First_free_physical_page.value - i)  % ce_plane_num) // plane_num
            pca.b6_plane = ((open_vb_current.LOG_Block_First_free_physical_page.value - i)  % ce_plane_num) % plane_num
            pca.l12_fpage = ((open_vb_current.LOG_Block_First_free_physical_page.value - i) // ce_plane_num) << 5
            
            #pca.l0_op = 0x20000
            pca.l0_op = 0
            pca.b4_mode = 1
            dire_read_payload = api.direct_read(pca=pca, block_count=4, include_FW_spare=True)
            dumpfile('testlogread.bin',dire_read_payload)
            if dire_read_payload[0x4004] == 0x94:
                if findcnt == 0:
                    lastvalid = i
                    findcnt = findcnt+1
                elif findcnt == 1:
                    secondvalid = i
                    findcnt = findcnt +1
                else:
                    findcnt = findcnt +1
                splitinfo.append(i)
                if findcnt > 3:
                    break
        size = len(splitinfo)
        if size > 3:
            testcnt = 2
            num = splitinfo[1]
        elif size > 2:
            testcnt = 1
            num = splitinfo[0]
        else:
            testcnt = 0
            num = 0
        if testcnt > 0:
            logger.flow(11, f'inject UECC on Log LWP {num} page')
            startoffset = 0
            injectUECC_from_FEP(vb,fep,startoffset,num)
            logger.flow(12, f'HW reset without SSU')
            status = SPOR_init_mp()
            if status == False:
                pattern_status = False
                logger.error_lb(f'inject uecc unitl last ics plane on List VB and SPOR ')
                logger.error_fp(f'expect SPOR Pass, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            logger.flow(13, f'GET Open vb information by VU 0x40C1 as table6')
            get_open_vb = get_and_print_open_vb_information()
            open_vb_after = project_api.OpenVBInformation(get_open_vb.payload.copy())
            
            logger.flow(14, 'compare table5 should different with table6')
            vb = open_vb_current.LOG_block_VB_number_logical.value
            vb2 = open_vb_after.LOG_block_VB_number_logical.value
            fep = open_vb_current.LOG_Block_First_free_physical_page.value
            fep2 = open_vb_after.LOG_Block_First_free_physical_page.value
            if compare_vb_fep(vb,vb2,fep,fep2):
                logger.error_lb(f'inject UECC on Log LWP-1 page and SPOR ')
                logger.error_fp(f'expect List refresh, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def post_process(self) -> None:
        pass
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