import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.ufs_api.defines.enum_define import QueryResponseCode
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api import shared
from Script.lib import sdk_lib as lib
import random, array

from Script.api.ufs_api import *
from Script.api.exception import *
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from typing import cast
from Script.project_api.custom_vu.structs import get_nand_feature_format, set_nand_feature_format
from Script.project_api.custom_vu.mdwlsv_vu.structs import MDWLSV_format, MDWLSV_format_H
import copy
from Script.project_api.functions import print_object_info_ai, page_to_pageOrder
#_sdk = shared.sdk
SADVersion = 3
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
        MDWLSV_SLC_L2 =0
        MDWLSV_TLC_L2 =1
        MDWLSV_PTE =2
        MDWLSV_LOG =3
        MDWLSV_EM1 =4
        MDWLSV_L1 =5
        MDWLSV_SLC_GC =6
        MDWLSV_TLC_GC =7
        MDWLSV_RAID_SWAP_SLC_L2_SLC =8
        MDWLSV_RAID_SWAP_TLC_L2_SLC =9
        MDWLSV_RAID_SWAP_TLC_L2_TLC =10
        MDWLSV_MODULE_CNT =11
        MDWLSV_INVALID =0xFF
        logger.flow(1, 'config lun and WB')
        self.config_lun()
        wlsv_default = 0
        ce_num = self.flash_setting.Max_Fdevice
        write10 = ExecuteCMD.Write10()
        cur_lba = 0
        tlc_ce_page = self.flash_setting.Plane_Per_Die * 4 * 3
        tlc_pageline = tlc_ce_page * ce_num
        slc_ce_page = self.flash_setting.Plane_Per_Die * 4
        slc_pageline = slc_ce_page * ce_num
        logger.info(f'tlc_ce_page = {tlc_ce_page}')
        write_len = 1
        #VC12 Program on single-plane type VB A 's CE0 full plane(skip ICS), switch to program another VB B's CE0
        #check MDWLSV[CE0][VB A].WLSVOffsetSub0 = MDWLSV[CE0][VB A].WLSVOffset
        
        logger.flow(2, 'write 1 slc CE page size on EM1 LUN')
        write10.assign(lun=self.TestEM1Lun, lba=cur_lba, length=slc_ce_page, fua=1)
        ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=True)
        logger.flow(3, 'write 1 tlc CE page size on normal LUN')
        write10.assign(lun=self.TestNormalLun, lba=cur_lba, length=tlc_ce_page, fua=1)
        ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=True)
        logger.info('VU 0x4029 get MDWLSV Offset')
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,60, 4)
        MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        #self.print_object_info_ai(MDWLSV_info)
        
        if MDWLSV_info.mdwlsv_md[0].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value != MDWLSV_info.mdwlsv_md[0].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value:
            logger.error_lb(f'write 1 slc CE page size on EM1 LUN , then write tlc l2')
            logger.error_fp(f'expect EM1 wlsv offset: {MDWLSV_info.mdwlsv_md[0].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value} = EM1 SB0 wlsv offset: {MDWLSV_info.mdwlsv_md[0].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #VC13
        logger.flow(4, 'config lun and WB')
        self.config_lun()
        em1_cur_lba = 0
        logger.flow(5, f'write length ={BLOCK4K_SIZE_16K_BYTE} on EM1 LUN')
        write10.assign(lun=self.TestEM1Lun, lba=em1_cur_lba, length=BLOCK4K_SIZE_16K_BYTE, fua=1)
        ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=True)
        em1_cur_lba += BLOCK4K_SIZE_16K_BYTE
        logger.flow(6, 'write 1 tlc CE page size on normal LUN')
        write10.assign(lun=self.TestNormalLun, lba=cur_lba, length=tlc_ce_page, fua=1)
        ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=True)
        loop = 1
        while True:
            logger.flow(f'7-{loop}', f'write lba ={em1_cur_lba}, length ={BLOCK4K_SIZE_16K_BYTE} on EM1 LUN')
            write10.assign(lun=self.TestEM1Lun, lba=em1_cur_lba, length=BLOCK4K_SIZE_16K_BYTE, fua=1)
            ExecuteCMD.enqueue(write10)
            ExecuteCMD.send(clear_on_success=True)
            loop+=1
            _, open_vb_info = get_open_vb_info()
            self.print_open_vb_information_phison(open_vb_info)
            open_vb_1: OpenVBInfo = OpenVBInfo(open_vb_info.payload.copy())
            if ce_num > 1:
                if open_vb_1.SLC_L2.first_empty_physical_page.value % 4 == 3 and open_vb_1.SLC_L2.first_empty_CE.value == 1 and open_vb_1.SLC_L2.first_empty_plane.value == 0:
                    break
            else:
                if open_vb_1.SLC_L2.first_empty_physical_page.value == 4:
                    break

        logger.flow(8, f'write 1 tlc share page size = {tlc_pageline} on normal LUN')
        write10.assign(lun=self.TestNormalLun, lba=cur_lba, length=tlc_pageline, fua=1)
        ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=True)

        logger.info('VU 0x4029 get MDWLSV Offset')
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,60, 4)
        MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        if MDWLSV_info.mdwlsv_md[0].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value != 0:
            logger.error_lb(f'write 1 page size on EM1 LUN , then write tlc l2 CE0 , then write EM1 LUN until SB3 CE0 last plane, then write tlc sharepage size')
            logger.error_fp(f'expect EM1 wlsv offset: {MDWLSV_info.mdwlsv_md[0].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value} = 0, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        #VC14        
        logger.flow(9, 'config lun and WB')
        self.config_lun()
        em1_cur_lba = 0
        vc14_loop = 0
        firstEM1P3:list[int] = []
        checkEM1P3:list[bool] = []
        minEM1P3:list[int] = []
        if (ce_num) >= len(firstEM1P3):
            firstEM1P3.extend([0xFF] * ((ce_num) - len(firstEM1P3)))
            checkEM1P3.extend([False] * ((ce_num) - len(checkEM1P3)))
            minEM1P3.extend([0] * ((ce_num) - len(minEM1P3)))
        if SADVersion == 2:
            for ce in range(ce_num):
                # logger.flow(f'10-{vc14_loop}', f'write length ={slc_pageline/2} on EM1 LUN')
                # write10.assign(lun=self.TestEM1Lun, lba=em1_cur_lba, length= int(slc_pageline/2), fua=1)
                # ExecuteCMD.enqueue(write10)
                # ExecuteCMD.send(clear_on_success=True)
                for i in range (self.flash_setting.Plane_Per_Die):
                    logger.flow(f'10-{vc14_loop}', f'write length ={BLOCK4K_SIZE_16K_BYTE} on EM1 LUN')
                    write10.assign(lun=self.TestEM1Lun, lba=em1_cur_lba, length=BLOCK4K_SIZE_16K_BYTE, fua=1)
                    ExecuteCMD.enqueue(write10)
                    ExecuteCMD.send(clear_on_success=True)
                    em1_cur_lba += BLOCK4K_SIZE_16K_BYTE
                    rsp, previos_payload = get_previous_info()
                    project_api.print_array_tohex(previos_payload,60, 4)
                    logger.info(f'get_previous_info: {hex(previos_payload[0])} {hex(previos_payload[1])} {hex(previos_payload[2])} {hex(previos_payload[3])}')
                if previos_payload[ce*2+0] == MDWLSV_EM1:
                    response, data_payload = project_api.issue_4022_to_get_NAND_feature(ce,0x7F)
                    project_api.print_array_tohex(data_payload,60, 4)
                    get_nand_feature = self.assign_get_nand_feature_info(data_payload)
                    first_CE0_EM1_get_nand_feature: get_nand_feature_format = get_nand_feature_format(get_nand_feature.payload.copy())
                    firstEM1P3[ce] = first_CE0_EM1_get_nand_feature.P3.value
                else:
                    firstEM1P3[ce] = 0xFF

        # logger.flow(f'10-{vc14_loop}', f'write length ={slc_pageline/2} on EM1 LUN')
        # write10.assign(lun=self.TestEM1Lun, lba=em1_cur_lba, length= int(slc_pageline/2), fua=1)
        # ExecuteCMD.enqueue(write10)
        # ExecuteCMD.send(clear_on_success=True)
        # rsp, previos_payload = get_previous_info()
        # project_api.print_array_tohex(previos_payload,60, 4)
        # if previos_payload[0] == MDWLSV_EM1:
        #     response, data_payload = project_api.issue_4022_to_get_NAND_feature(0,0x7F)
        #     project_api.print_array_tohex(data_payload,60, 4)
        #     get_nand_feature = self.assign_get_nand_feature_info(data_payload)
        #     first_CE0_EM1_get_nand_feature: get_nand_feature_format = get_nand_feature_format(get_nand_feature.payload.copy())
        # logger.flow(f'10-{vc14_loop}', f'write length ={slc_pageline/2} on EM1 LUN')
        # write10.assign(lun=self.TestEM1Lun, lba=em1_cur_lba, length= int(slc_pageline/2), fua=1)
        # ExecuteCMD.enqueue(write10)
        # ExecuteCMD.send(clear_on_success=True)
        # rsp, open_vb_info = get_open_vb_info()
        # self.print_open_vb_information_phison(open_vb_info)
        # rsp, previos_payload = get_previous_info()
        # project_api.print_array_tohex(previos_payload,60, 4)
        # if previos_payload[1*2] == MDWLSV_EM1:
        #     response, data_payload = project_api.issue_4022_to_get_NAND_feature(0,0x7F)
        #     project_api.print_array_tohex(data_payload,60, 4)
        #     get_nand_feature = self.assign_get_nand_feature_info(data_payload)
        #     first_CE1_EM1_get_nand_feature: get_nand_feature_format = get_nand_feature_format(get_nand_feature.payload.copy())
        logger.info('VU 0x4029 get MDWLSV Offset')
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,ce_num*60, 60)
        MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        logger.info(f'EM1 ce0 wlsv offset: {MDWLSV_info.mdwlsv_md[0].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value}')
        logger.info(f'EM1 ce1 wlsv offset: {MDWLSV_info.mdwlsv_md[1].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value}')

        if SADVersion == 2:    
            for ce in range (ce_num):
                if MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value == 0:
                    checkEM1P3[ce] = True
                else:
                    checkEM1P3[ce] = False
        # logger.flow(10, 'VU C08C disable MDWLSV')
        # response = project_api.issue_C08C_to_EnDis_MDWLSV(self.disableMDWLSV) 
        # logger.flow(10, 'VU C08C enable MDWLSV')
        # response = project_api.issue_C08C_to_EnDis_MDWLSV(self.EnableMDWLSV) 
        vc14_loop += 1
        #for t in range(1000):
        for ce in range (ce_num):
            numbers = array.array('i')
            if SADVersion == 2:
                if firstEM1P3[ce] != 0xFF:
                    numbers.append(firstEM1P3[ce])
            for i in range (self.flash_setting.Plane_Per_Die):
                logger.flow(f'10-{vc14_loop}', f'write length ={BLOCK4K_SIZE_16K_BYTE} on EM1 LUN')
                write10.assign(lun=self.TestEM1Lun, lba=em1_cur_lba, length=BLOCK4K_SIZE_16K_BYTE, fua=1)
                ExecuteCMD.enqueue(write10)
                ExecuteCMD.send(clear_on_success=True)
                em1_cur_lba += BLOCK4K_SIZE_16K_BYTE
                rsp, previos_payload = get_previous_info()
                project_api.print_array_tohex(previos_payload,60, 4)
                logger.info(f'get_previous_info: {hex(previos_payload[0])} {hex(previos_payload[1])} {hex(previos_payload[2])} {hex(previos_payload[3])}')
                logger.info('VU 0x4029 get MDWLSV Offset')
                response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
                project_api.print_array_tohex(data_payload,ce_num*60, 60)
                MDWLSV_info = self.assign_MDWLSV_info(data_payload)
                logger.info(f'EM1 ce0 wlsv offset: {MDWLSV_info.mdwlsv_md[0].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value}')
                logger.info(f'EM1 ce1 wlsv offset: {MDWLSV_info.mdwlsv_md[1].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value}')
            
                if firstEM1P3[ce] != 0xFF and checkEM1P3[ce] == True:
                    checkEM1P3[ce] = False
                    if MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value != firstEM1P3[ce]:
                        logger.error_lb(f'write CE page size on EM1 LUN and get P3 util full CE{ce_num} , then write EM1 CE{ce} ')
                        logger.error_fp(f'EM1 CE{ce} wlsv offset: {MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value} expect = firstEM1P3 ce{ce}: {firstEM1P3[ce]} , result Fail!')
                        rsp, previos_payload = get_previous_info()
                        project_api.print_array_tohex(previos_payload,60, 4)
                        logger.info(f'get_previous_info: {hex(previos_payload[0])} {hex(previos_payload[1])} {hex(previos_payload[2])} {hex(previos_payload[3])}')
                
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                if firstEM1P3[ce] != 0xFF:
                    if len(numbers):
                        p3_min = min(numbers)
                        if MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value != p3_min:
                            logger.error_lb(f'write 1 Plane size on EM1 LUN and get P3 on CE{ce_num}')
                            logger.error_fp(f'EM1 CE{ce} wlsv offset: {MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value} expect = p3_min ce{ce}: {p3_min} , result Fail!')
                            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                vc14_loop += 1
                EM1_get_nand_feature: get_nand_feature_format
                if SADVersion == 2:
                    if previos_payload[ce*2] == MDWLSV_EM1 and i < (self.flash_setting.Plane_Per_Die-1):
                        response, data_payload = project_api.issue_4022_to_get_NAND_feature(ce,0x7F)
                        project_api.print_array_tohex(data_payload,60, 4)
                        get_nand_feature = self.assign_get_nand_feature_info(data_payload)
                        EM1_get_nand_feature = get_nand_feature_format(get_nand_feature.payload.copy())
                        numbers.append(EM1_get_nand_feature.P3.value)
                        logger.info(f'P3 = {EM1_get_nand_feature.P3.value}, CE{ce} lastprogram vb type = EM1, plane = {hex(previos_payload[ce*2+1])}')
                        #if EM1_get_nand_feature.P3.value == 0:
                if SADVersion == 3:
                    if previos_payload[ce*2] == MDWLSV_EM1 and i < self.flash_setting.Plane_Per_Die:
                        response, data_payload = project_api.issue_4022_to_get_NAND_feature(ce,0x7F)
                        project_api.print_array_tohex(data_payload,60, 4)
                        get_nand_feature = self.assign_get_nand_feature_info(data_payload)
                        EM1_get_nand_feature = get_nand_feature_format(get_nand_feature.payload.copy())
                        if SADVersion == 3 and i == 0:
                            firstEM1P3[ce] = EM1_get_nand_feature.P3.value
                            checkEM1P3[ce] = True
                        numbers.append(EM1_get_nand_feature.P3.value)
                        logger.info(f'P3 = {EM1_get_nand_feature.P3.value}, CE{ce} lastprogram vb type = EM1, plane = {hex(previos_payload[ce*2+1])}')
                        #if EM1_get_nand_feature.P3.value == 0:
                    
                if previos_payload[ce*2] == MDWLSV_EM1 and i == (self.flash_setting.Plane_Per_Die-1) and SADVersion == 2:
                    if MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value != MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value:
                        logger.error_lb(f'Bitmap should be 0x3F on CE{ce_num} ')
                        logger.error_fp(f'EM1 CE{ce} MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset : {MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value} expect = MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset ce{ce}: {MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value} , result Fail!')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            minEM1P3[ce] = min(numbers)
            if SADVersion == 2:
                logger.flow(11, f'write 1 tlc share page size = {tlc_pageline} on normal LUN')
                write10.assign(lun=self.TestNormalLun, lba=cur_lba, length=tlc_pageline, fua=1)
                ExecuteCMD.enqueue(write10)
                ExecuteCMD.send(clear_on_success=True)
            
                rsp, previos_payload = get_previous_info()
                project_api.print_array_tohex(previos_payload,60, 4)
                logger.info(f'get_previous_info: {hex(previos_payload[0])} {hex(previos_payload[1])} {hex(previos_payload[2])} {hex(previos_payload[3])}')
                logger.info('VU 0x4029 get MDWLSV Offset')
                response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
                project_api.print_array_tohex(data_payload,ce_num*60, 60)
                MDWLSV_info = self.assign_MDWLSV_info(data_payload)
                logger.info(f'EM1 ce0 wlsv offset: {MDWLSV_info.mdwlsv_md[0].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value}')
                logger.info(f'EM1 ce1 wlsv offset: {MDWLSV_info.mdwlsv_md[1].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value}')
                if len(numbers):
                    em1_p3_min = min(numbers)
                    if MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value != em1_p3_min:
                        logger.error_lb(f'write 1 Plane size on EM1 LUN and get P3 util full plane on CE{ce} , then write tlc l2 CE{ce} ')
                        logger.error_fp(f'EM1 ce{ce} wlsv offset: {MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value} expect = minimun P3: {em1_p3_min} , result Fail!')
                        rsp, previos_payload = get_previous_info()
                        project_api.print_array_tohex(previos_payload,60, 4)
                        logger.info(f'get_previous_info: {hex(previos_payload[0])} {hex(previos_payload[1])} {hex(previos_payload[2])} {hex(previos_payload[3])}')
                
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if SADVersion == 3:
            logger.flow(11, f'write 1 slc share page size = {slc_pageline} on EM1 LUN')
            for i in range (ce_num * self.flash_setting.Plane_Per_Die):
                write10.assign(lun=self.TestEM1Lun, lba=cur_lba, length=BLOCK4K_SIZE_16K_BYTE, fua=1)
                cur_lba += BLOCK4K_SIZE_16K_BYTE
                ExecuteCMD.enqueue(write10)
            ExecuteCMD.send(clear_on_success=True)
            logger.info('VU 0x4029 get MDWLSV Offset')
            response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
            project_api.print_array_tohex(data_payload,ce_num*60, 60)
            MDWLSV_info = self.assign_MDWLSV_info(data_payload)
            logger.info(f'EM1 ce0 wlsv offset: {MDWLSV_info.mdwlsv_md[0].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value}')
            logger.info(f'EM1 ce1 wlsv offset: {MDWLSV_info.mdwlsv_md[1].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value}')
            for ce in range (ce_num):
                if MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value != minEM1P3[ce]:
                    logger.error_lb(f'write 1 Plane size on EM1 LUN and get P3 util full plane on CE{ce} , then write SLC l2 CE{ce} ')
                    logger.error_fp(f'EM1 ce{ce} wlsv offset: {MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value} expect = minimun P3: {minEM1P3[ce]} , result Fail!')
                    rsp, previos_payload = get_previous_info()
                    project_api.print_array_tohex(previos_payload,60, 4)
                    logger.info(f'get_previous_info: {hex(previos_payload[0])} {hex(previos_payload[1])} {hex(previos_payload[2])} {hex(previos_payload[3])}')
                
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #VC new open vb reset tlc        
        logger.flow(12, 'config lun and WB')
        self.config_lun()
        _, open_vb_info = get_open_vb_info()
        self.print_open_vb_information_phison(open_vb_info)
        open_vb_1 = OpenVBInfo(open_vb_info.payload.copy())
        pageorder = page_to_pageOrder(open_vb_1.SLC_L2.first_empty_physical_page.value)
        logger.flow(13, 'write 1 slc vb page size - 1 ce page sizeon EM1 LUN')
        logger.info(f'[write 1 slc vb size {self.tlc_vb_size}]')
        api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=int(self.slc_vb_size*1 - 1*slc_ce_page), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        # pageorder = page_to_pageOrder(open_vb_1.TLC_L2.first_empty_physical_page.value)
        # logger.flow(13, 'write 1 tlc vb page size - 1 share page sizeon normal LUN')
        # logger.info(f'[write 1 tlc vb size {self.tlc_vb_size}]')
        # api.sequential_write(lun=self.TestNormalLun, start_lba=0, total_size=int(self.tlc_vb_size*1 - 1*tlc_pageline), chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 0,
        #                 need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        logger.info('VU 0x4029 get MDWLSV Offset')
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,60, 4)
        MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        
        
        while True:
            _, open_vb_info = get_open_vb_info()
            self.print_open_vb_information_phison(open_vb_info)
            open_vb_2: OpenVBInfo = OpenVBInfo(open_vb_info.payload.copy())
            pageorder = open_vb_2.SLC_L2.first_empty_physical_page.value
            #pageorder = page_to_pageOrder(open_vb_2.TLC_L2.first_empty_physical_page.value)
            #if open_vb_2.SLC_L2.first_empty_physical_page.value < 1103:
            if open_vb_2.SLC_L2.first_empty_physical_page.value != 0:
                logger.flow(14, f'write 1 page size = {tlc_ce_page} on EM1 LUN')
                write10.assign(lun=self.TestEM1Lun, lba=cur_lba, length=4, fua=1)
                ExecuteCMD.enqueue(write10)
                ExecuteCMD.send(clear_on_success=True)
            else:
                break
        _, open_vb_info = get_open_vb_info()
        self.print_open_vb_information_phison(open_vb_info)
        open_vb_3: OpenVBInfo = OpenVBInfo(open_vb_info.payload.copy())
        logger.info('VU 0x4029 get MDWLSV Offset')
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,60, 4)
        self.check_all_zero(data_payload[0:4])
        


        
        pass

    def post_process(self) -> None:
        pass
    def assign_MDWLSV_info(self, data_payload:bytearray) -> MDWLSV_format_H:
        MDWLSV_info = MDWLSV_format_H()
        for ce in range (self.flash_setting.Max_Fdevice):
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value=data_payload[2+60*ce] 
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value=data_payload[3+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_offset.value=data_payload[6+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_SB0_offset.value=data_payload[7+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_offset.value=data_payload[10+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_SB0_offset.value=data_payload[11+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value=data_payload[14+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_SB0_offset.value=data_payload[15+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_offset.value=data_payload[18+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_SB0_offset.value=data_payload[19+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_offset.value=data_payload[22+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_SB0_offset.value=data_payload[23+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_RPMB_GC_offset.value=data_payload[26+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_RPMB_GC_SB0_offset.value=data_payload[27+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_offset.value=data_payload[30+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_SB0_offset.value=data_payload[31+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_offset.value=data_payload[34+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_SB0_offset.value=data_payload[35+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_SM_OPEN_BLOCK_FTL_SUB_offset.value=data_payload[38+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_SM_OPEN_BLOCK_FTL_SUB_SB0_offset.value=data_payload[39+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_SM_OPEN_BLOCK_EM1_GC_offset.value=data_payload[42+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_SM_OPEN_BLOCK_EM1_GC_SB0_offset.value=data_payload[43+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value=data_payload[46+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_SB0_offset.value=data_payload[47+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_offset.value=data_payload[50+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_SB0_offset.value=data_payload[51+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_offset.value=data_payload[54+60*ce]
            MDWLSV_info.mdwlsv_md[ce].MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_SB0_offset.value=data_payload[55+60*ce]
            print_object_info_ai(MDWLSV_info.mdwlsv_md[ce])
        return MDWLSV_info
    #def assign_MDWLSV_info(self, data_payload:bytearray) -> MDWLSV_format:
    #     self.MDWLSV_info = MDWLSV_format()
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value=data_payload[2]            
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value=data_payload[3]        
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_offset.value=data_payload[6]          
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_SB0_offset.value=data_payload[7]      
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_offset.value=data_payload[10]        
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_SB0_offset.value=data_payload[11]    
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value=data_payload[14]    
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_SB0_offset.value=data_payload[15]
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_offset.value=data_payload[18]    
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_SB0_offset.value=data_payload[19]
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_offset.value=data_payload[22]        
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_SB0_offset.value=data_payload[23]    
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_offset.value=data_payload[26]          
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_SB0_offset.value=data_payload[27]      
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_offset.value=data_payload[30]      
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_SB0_offset.value=data_payload[31]  
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_offset.value=data_payload[34]      
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_SB0_offset.value=data_payload[35]  
    #     self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_offset.value=data_payload[38]          
    #     self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_SB0_offset.value=data_payload[39]      
    #     self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_EM1_GC_offset.value=data_payload[42]            
    #     self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_EM1_GC_SB0_offset.value=data_payload[43]        
    #     self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value=data_payload[46]    
    #     self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_SB0_offset.value=data_payload[47]
    #     self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_offset.value=data_payload[50]        
    #     self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_SB0_offset.value=data_payload[51]    
    #     self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_offset.value=data_payload[54]    
    #     self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_SB0_offset.value=data_payload[55]
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_offset.value=data_payload[58]        
    #     self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_SB0_offset.value=data_payload[59]
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value=data_payload[2+1*60]            
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value=data_payload[3+1*60]        
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_offset.value=data_payload[6+1*60]          
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_SB0_offset.value=data_payload[7+1*60]      
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_offset.value=data_payload[10+1*60]        
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_SB0_offset.value=data_payload[11+1*60]    
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value=data_payload[14+1*60]    
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_SB0_offset.value=data_payload[15+1*60]
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_offset.value=data_payload[18+1*60]    
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_SB0_offset.value=data_payload[19+1*60]
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_offset.value=data_payload[22+1*60]        
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_SB0_offset.value=data_payload[23+1*60]    
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_offset.value=data_payload[26+1*60]          
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_SB0_offset.value=data_payload[27+1*60]      
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_offset.value=data_payload[30+1*60]      
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_SB0_offset.value=data_payload[31+1*60]  
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_offset.value=data_payload[34+1*60]      
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_SB0_offset.value=data_payload[35+1*60]  
    #     self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_offset.value=data_payload[38+1*60]          
    #     self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_SB0_offset.value=data_payload[39+1*60]      
    #     self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_EM1_GC_offset.value=data_payload[42+1*60]            
    #     self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_EM1_GC_SB0_offset.value=data_payload[43+1*60]        
    #     self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value=data_payload[46+1*60]    
    #     self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_SB0_offset.value=data_payload[47+1*60]
    #     self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_offset.value=data_payload[50+1*60]        
    #     self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_SB0_offset.value=data_payload[51+1*60]    
    #     self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_offset.value=data_payload[54+1*60]    
    #     self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_SB0_offset.value=data_payload[55+1*60]
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_offset.value=data_payload[58+1*60]        
    #     self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_SB0_offset.value=data_payload[59+1*60]  
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value=data_payload[2+2*60]            
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value=data_payload[3+2*60]        
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_offset.value=data_payload[6+2*60]          
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_SB0_offset.value=data_payload[7+2*60]      
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_offset.value=data_payload[10+2*60]        
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_SB0_offset.value=data_payload[11+2*60]    
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value=data_payload[14+2*60]    
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_SB0_offset.value=data_payload[15+2*60]
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_offset.value=data_payload[18+2*60]    
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_SB0_offset.value=data_payload[19+2*60]
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_offset.value=data_payload[22+2*60]        
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_SB0_offset.value=data_payload[23+2*60]    
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_offset.value=data_payload[26+2*60]          
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_SB0_offset.value=data_payload[27+2*60]      
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_offset.value=data_payload[30+2*60]      
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_SB0_offset.value=data_payload[31+2*60]  
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_offset.value=data_payload[34+2*60]      
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_SB0_offset.value=data_payload[35+2*60]  
    #     self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_offset.value=data_payload[38+2*60]          
    #     self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_SB0_offset.value=data_payload[39+2*60]      
    #     self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_EM1_GC_offset.value=data_payload[42+2*60]            
    #     self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_EM1_GC_SB0_offset.value=data_payload[43+2*60]        
    #     self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value=data_payload[46+2*60]    
    #     self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_SB0_offset.value=data_payload[47+2*60]
    #     self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_offset.value=data_payload[50+2*60]        
    #     self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_SB0_offset.value=data_payload[51+2*60]    
    #     self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_offset.value=data_payload[54+2*60]    
    #     self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_SB0_offset.value=data_payload[55+2*60]
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_offset.value=data_payload[58+2*60]        
    #     self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_SB0_offset.value=data_payload[59+2*60]
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value=data_payload[2+3*60]            
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value=data_payload[3+3*60]        
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_offset.value=data_payload[6+3*60]          
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_SB0_offset.value=data_payload[7+3*60]      
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_offset.value=data_payload[10+3*60]        
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_SB0_offset.value=data_payload[11+3*60]    
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value=data_payload[14+3*60]    
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_SB0_offset.value=data_payload[15+3*60]
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_offset.value=data_payload[18+3*60]    
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_SB0_offset.value=data_payload[19+3*60]
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_offset.value=data_payload[22+3*60]        
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_SB0_offset.value=data_payload[23+3*60]    
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_offset.value=data_payload[26+3*60]          
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_SB0_offset.value=data_payload[27+3*60]      
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_offset.value=data_payload[30+3*60]      
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_SB0_offset.value=data_payload[31+3*60]  
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_offset.value=data_payload[34+3*60]      
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_SB0_offset.value=data_payload[35+3*60]  
    #     self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_offset.value=data_payload[38+3*60]          
    #     self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_SB0_offset.value=data_payload[39+3*60]      
    #     self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_EM1_GC_offset.value=data_payload[42+3*60]            
    #     self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_EM1_GC_SB0_offset.value=data_payload[43+3*60]        
    #     self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value=data_payload[46+3*60]    
    #     self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_SB0_offset.value=data_payload[47+3*60]
    #     self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_offset.value=data_payload[50+3*60]        
    #     self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_SB0_offset.value=data_payload[51+3*60]    
    #     self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_offset.value=data_payload[54+3*60]    
    #     self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_SB0_offset.value=data_payload[55+3*60]
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_offset.value=data_payload[58+3*60]        
    #     self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_SB0_offset.value=data_payload[59+3*60]
    #     return self.MDWLSV_info
    def assign_get_nand_feature_info(self, data_payload:bytearray) -> get_nand_feature_format:
        get_nand_info_format = get_nand_feature_format()
        #testbytes = data_payload[0:4]
        # print(type(testbytes))
        # print(type(data_payload[0:4]))
        get_nand_info_format.result.value = int.from_bytes(data_payload[0:4], byteorder='little')
        get_nand_info_format.die.value = int.from_bytes(data_payload[4:8], byteorder='little')
        get_nand_info_format.P1.value = int.from_bytes(data_payload[8:12], byteorder='little')
        get_nand_info_format.P2.value = int.from_bytes(data_payload[12:16], byteorder='little')
        get_nand_info_format.P3.value = int.from_bytes(data_payload[16:20], byteorder='little')
        get_nand_info_format.P4.value = int.from_bytes(data_payload[20:24], byteorder='little')
        
        logger.info(f'get_nand_info_format.P3.value = {get_nand_info_format.P3.value}')
        return get_nand_info_format       
    # def assign_set_nand_feature_info(self, data_payload:bytearray) -> set_nand_feature_format:
    #     self.set_nand_info_format = set_nand_feature_format()
    #     testbytes = data_payload[0:4]
    #     print(type(testbytes))
    #     print(type(data_payload[0:4]))
    #     self.get_nand_info_format.result.value = int.from_bytes(data_payload[0:4], byteorder='little')
    #     return self.set_nand_info_format      
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
    def print_open_vb_information_phison(self, open_vb_info: OpenVBInfo) -> None:
    
        logger.info('================= open_vb_information =================')
        # 取得所有屬於 OpenVBInfoUnit 的子單元
        sub_units = {
            name: obj
            for name, obj in open_vb_info.__dict__.items()
            if hasattr(obj, "__dict__")               # 必須是物件
            and any(hasattr(v, "start_offset") for v in obj.__dict__.values())  # 內含欄位
        }

        for unit_name, unit_obj in sub_units.items():
            # 收集該單元內所有具有 start_offset / end_offset / value 的欄位
            fields = [
                (fname, fobj)
                for fname, fobj in unit_obj.__dict__.items()
                if hasattr(fobj, "start_offset")
                and hasattr(fobj, "end_offset")
                and hasattr(fobj, "value")
            ]

            # 依起始位元組排序
            fields.sort(key=lambda kv: kv[1].start_offset)

            # 輸出單元標頭
            logger.info(f'--- {unit_name} ---')
            # 輸出欄位資訊
            for fname, fobj in fields:
                logger.info(
                    f'Byte[{fobj.start_offset}:{fobj.end_offset}]: '
                    f'{unit_name}.{fname} = {fobj.value}'
                )  
    def check_all_zero(self, obj: Any) -> None:
        if isinstance(obj, (bytearray, bytes)):
             payload = obj 
        else:
            payload = obj.payload
        for idx, byte_val in enumerate(payload):
            if byte_val != 0:
                logger.error(f"expect data all zero, but result fail")
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
run = Pattern().run
if __name__ == "__main__":
    run()