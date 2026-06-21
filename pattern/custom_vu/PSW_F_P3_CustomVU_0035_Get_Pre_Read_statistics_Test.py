import package_root
import time
from Script import api
from typing import cast
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
from typing import cast, Final, Mapping
from Script.project_api.custom_vu.structs import get_nand_feature_format, set_nand_feature_format


CHUNK_SIZE: int = 4 * 1024  # 4 KB
RESET_COMMANDS: Final[Mapping[int, str]] = {
    0:      "POWER ON RESET",      # Hardware Reset
    1:       "HW RESET",       # Reset‑N
    2:  "endpoint_rst",  # Endpoint Reset
    3:    "unipro_rst",    # UniPro Reset
}

#_sdk = shared.sdk

def check_timeout(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.disableMDWLSV = 1
        self.EnableMDWLSV = 0
        self.write_record = api.get_empty_write_record()
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting = api.get_flash_setting()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 4
        self.TestBootA = 25
        self.TestBootB = 8
        self.TestEM1Lun = 3
        # self.TestNormalLun = 0
        # self.TestBootA = 2
        # self.TestBootB = 3
        # self.TestEM1Lun = 4
        # self.TestNormalLun = 0
        # self.TestBootA = 1
        # self.TestBootB = 2
        # self.TestEM1Lun = 3
        self.Total_AU_Count = self.geometry_desc.q4_total_raw_device_capacity / (self.geometry_desc.l13_segment_size * self.geometry_desc.b17_allocation_unit_size);
        
    def step1(self) -> None:
        
        logger.flow(1, 'config normal LUN0, EM1 LUN3, BOOT_A LUN1, BOOT_B LUN2 and WB')
        hw_setting = api.HwSetting.get_instance()
        hw_setting.update_from_device()
        medium_scan_setting_bk = hw_setting.get_local_val(api.HwSettingField.MEDIUM_SCAN_TRIGGER_TIME)
        hw_setting.set_to_device(field = api.HwSettingField.MEDIUM_SCAN_TRIGGER_TIME, val= 0x80)
        self.config_lun()
        for case in range(0,6):
            read_length = 32
            read_lba = 0
            _param = api.shared.param
            rsp, getpreread = project_api.issue_4090_to_get_pre_read_statistics()
            self.print_pre_read_information(getpreread)
            if case == 0:
                testlun = self.TestNormalLun
            elif case == 1:
                testlun = self.TestEM1Lun
            elif case == 2:
                testlun = self.TestBootA
            elif case == 3:
                testlun = self.TestBootB
            elif case == 4:
                testlun = self.TestNormalLun
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            elif case == 5:
                testlun = 0xB0
            if testlun != 0xB0:
                logger.flow('2', f'Write LUN = {testlun}, start lba = {read_lba} , length = 65535')
                ExecuteCMD.Write10().assign(lun=testlun, lba=read_lba, length=65535, fua=1).enqueue()
                ExecuteCMD.send(clear_on_success=True)
            #ExecuteCMD.Write10().assign(lun=3, lba=read_lba, length=65535, fua=1).enqueue()
            cmd_cnt = 32
            loop_max = 15
            testQD = 1
            for loop in range(1,loop_max):
                logger.flow(3, f'Loop ={loop}, seq read LUN = {testlun}, startlba = {read_lba}, chunk = {read_length}, command count = {cmd_cnt}, QD = {testQD}')
                for i in range(cmd_cnt):
                    ExecuteCMD.Read10().assign(lun=testlun, lba=read_lba, length=read_length, fua=0).enqueue()
                    read_lba += read_length            
                logger.flow(4, 'issue write cmd to abort pre-read')
                ExecuteCMD.Write10().assign(lun=self.TestNormalLun, lba=read_lba, length=1, fua=1).enqueue()
                ExecuteCMD.send(QD=testQD,clear_on_success=True)
                logger.flow('5', 'issue 4090 to get pre read statistics')
                rsp, getpreread = project_api.issue_4090_to_get_pre_read_statistics()
                self.print_pre_read_information(getpreread)
                
                logger.flow('5-1', 'check pre_read_enter_counter increase')
                if getpreread.pre_read_enter_counter.value != loop:
                    logger.error_lb(f'seq read LUN = {testlun}, startlba = {read_lba}, chunk = {read_length}, command count = {cmd_cnt}, QD = {testQD}, issue write cmd to abort pre-read')
                    logger.error_fp(f'expect pre_read_enter_counter {getpreread.pre_read_enter_counter.value} should same as loop {loop}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                logger.flow('5-2', 'check pre_read_exit_counter exit')
                if getpreread.pre_read_exit_counter.value != loop:
                    logger.error(f"pre_read_exit_counter {getpreread.pre_read_exit_counter.value} should same as loop {loop}")
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                logger.flow('5-3', 'check pre_read_exit_cause should as 3')
                if getpreread.pre_read_exit_cause.value != 3:
                    logger.error(f"pre_read_exit_cause {getpreread.pre_read_exit_cause.value} should as 3")
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                if testlun != 0xB0:
                    logger.flow('5-4', f'check pre_read_lun should as {testlun}')
                    if getpreread.pre_read_lun.value != testlun:
                        logger.error(f"pre_read_lun {getpreread.pre_read_lun.value} should same as testlun {testlun}")
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                else:
                    logger.flow('5-4', f'check pre_read_lun should as {self.TestBootA}')
                    if getpreread.pre_read_lun.value != self.TestBootA:
                        logger.error(f"pre_read_lun {getpreread.pre_read_lun.value} should same as testlun {testlun}")
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                # else:
                #     if getpreread.pre_read_enter_counter.value != 0 and getpreread.pre_read_exit_counter.value != 0 and getpreread.pre_read_exit_cause.value != 0:
                #         logger.error(f"pre_read_enter_counter {getpreread.pre_read_enter_counter.value} should = 0 on boot lun")
                #         raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            #test ssu 
            logger.flow(6, f'Test SSU abort pre read, seq read startlba = {read_lba}, chunk = {read_length}, command count = {cmd_cnt}, QD = {testQD}')
            last_pre_read_enter_cnt = getpreread.pre_read_enter_counter.value
            last_pre_read_exit_cnt = getpreread.pre_read_exit_counter.value
            for i in range(cmd_cnt):
                ExecuteCMD.Read10().assign(lun=testlun, lba=read_lba, length=read_length, fua=0).enqueue()
                read_lba += read_length
            
            logger.flow(7, 'issue SSU sleep and active to abort pre-read')
            ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
            ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
            
            ExecuteCMD.send(QD=testQD,clear_on_success=True)
            
            logger.flow('8', 'issue 4090 to get pre read statistics')
            rsp, getpreread = project_api.issue_4090_to_get_pre_read_statistics()
            self.print_pre_read_information(getpreread)
            
            #if testlun != self.TestBootA:
            logger.flow('8-1', 'check pre_read_enter_counter increase')
            if getpreread.pre_read_enter_counter.value != last_pre_read_enter_cnt+1:
                logger.error(f"pre_read_enter_counter {getpreread.pre_read_enter_counter.value} should same as {last_pre_read_enter_cnt+1}")
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            logger.flow('8-1', 'check pre_read_exit_counter increase')
            if getpreread.pre_read_exit_counter.value != last_pre_read_exit_cnt+1:
                logger.error(f"pre_read_exit_counter {getpreread.pre_read_exit_counter.value} should same as {last_pre_read_exit_cnt+1}")
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            # logger.flow('5-1', 'check pre_read_exit_cause shoud as')
            # if getpreread.pre_read_exit_cause.value != 1:
            #     logger.error(f"pre_read_exit_cause {getpreread.pre_read_exit_cause.value} should as 1")
            #     #raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            # else:
            #     if getpreread.pre_read_enter_counter.value != last_pre_read_enter_cnt:
            #         logger.error(f"pre_read_enter_counter {getpreread.pre_read_enter_counter.value} should same as {last_pre_read_enter_cnt+1}")
            #         raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            #     if getpreread.pre_read_exit_counter.value != last_pre_read_exit_cnt:
            #         logger.error(f"pre_read_exit_counter {getpreread.pre_read_exit_counter.value} should same as {last_pre_read_exit_cnt+1}")
            #         raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            #     if getpreread.pre_read_exit_cause.value != 0:
            #         logger.error(f"pre_read_exit_cause {getpreread.pre_read_exit_cause.value} should as 0")
            
            last_pre_read_enter_cnt = getpreread.pre_read_enter_counter.value
            last_pre_read_exit_cnt = getpreread.pre_read_exit_counter.value
            logger.flow(9, f'Test Enter ATS abort pre read, seq read startlba = {read_lba}, chunk = {read_length}, command count = {cmd_cnt}, QD = {testQD}')
            last_pre_read_enter_cnt = getpreread.pre_read_enter_counter.value
            last_pre_read_exit_cnt = getpreread.pre_read_exit_counter.value
            for i in range(cmd_cnt):
                ExecuteCMD.Read10().assign(lun=testlun, lba=read_lba, length=read_length, fua=0).enqueue()
                read_lba += read_length
            ExecuteCMD.send(QD=testQD,clear_on_success=True)
            
            logger.flow(10, 'idle 2s to enter ATS')
            time.sleep(2)
            
            logger.flow('11', 'issue 4090 to get pre read statistics')
            rsp, getpreread = project_api.issue_4090_to_get_pre_read_statistics()
            self.print_pre_read_information(getpreread)
            #if testlun != self.TestBootA:
            
            logger.flow('11-1', 'check pre_read_enter_counter increase')
            if getpreread.pre_read_enter_counter.value != last_pre_read_enter_cnt+1:
                logger.error(f"pre_read_enter_counter {getpreread.pre_read_enter_counter.value} should increase as {last_pre_read_enter_cnt+1}")
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            logger.flow('11-2', 'check pre_read_exit_counter increase')
            if getpreread.pre_read_exit_counter.value != last_pre_read_exit_cnt+1:
                logger.error(f"pre_read_exit_counter {getpreread.pre_read_exit_counter.value} should increase as {last_pre_read_exit_cnt+1}")
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            logger.flow('11-3', 'check pre_read_exit_cause as 2 or 3')
            if getpreread.pre_read_exit_cause.value != 2 and getpreread.pre_read_exit_cause.value != 3:
                logger.error_lb(f'Test Enter ATS abort pre read')
                logger.error_fp(f'expect pre_read_exit_cause = 2 or 3,but pre_read_exit_cause = {getpreread.pre_read_exit_cause.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            # else:
            #     if getpreread.pre_read_enter_counter.value != last_pre_read_enter_cnt:
            #         logger.error(f"pre_read_enter_counter {getpreread.pre_read_enter_counter.value} should same as {last_pre_read_enter_cnt+1}")
            #         raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            #     if getpreread.pre_read_exit_counter.value != last_pre_read_exit_cnt:
            #         logger.error(f"pre_read_exit_counter {getpreread.pre_read_exit_counter.value} should same as {last_pre_read_exit_cnt+1}")
            #         raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            #     if getpreread.pre_read_exit_cause.value != 0:
            #         logger.error(f"pre_read_exit_cause {getpreread.pre_read_exit_cause.value} should as 0")
            
            for reset_type in range (api.Dcmd5ResetType.HW_RESET,api.Dcmd5ResetType.HW_RESET+1):
                
                logger.flow(12, f'Test Power on reset reset pre-read statistics, seq read startlba = {read_lba}, chunk = {read_length}, command count = {cmd_cnt}, QD = {testQD}')
            
                for i in range(cmd_cnt):
                    ExecuteCMD.Read10().assign(lun=testlun, lba=read_lba, length=read_length, fua=0).enqueue()
                    read_lba += read_length
                ExecuteCMD.send(QD=testQD,clear_on_success=True)
                
                # logger.flow(9, 'idle 2s to enter ATS')
                # time.sleep(2)
                # rsp, getpreread = project_api.issue_4090_to_get_pre_read_statistics()
                # self.print_pre_read_information(getpreread)
                # #if testlun != self.TestBootA:
                # self.check_not_all_zero(getpreread)

                logger.flow(13, f'reset event = {RESET_COMMANDS.get(reset_type)}')
                api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(reset_type), powerdown = True)
                
                logger.flow('14', 'issue 4090 to get pre read statistics')
                rsp, getpreread = project_api.issue_4090_to_get_pre_read_statistics()
                self.print_pre_read_information(getpreread)
                logger.flow('14-1', 'check pre read statistics should reset')
                self.check_all_zero(getpreread)

                logger.flow('15', 'Disable PreRead detect module')
                rr_enable = 1
                pre_read_en = 0
                project_api.issue_C0F4_to_EnDis_RR_detect(rr_enable,pre_read_en)
                logger.flow('16', 'make a pre read event')
                read_lba = 0
                for i in range(cmd_cnt):
                    ExecuteCMD.Read10().assign(lun=testlun, lba=read_lba, length=read_length, fua=0).enqueue()
                    read_lba += read_length
                ExecuteCMD.send(QD=testQD,clear_on_success=True)
                logger.flow('17', 'issue 409F to get pre read statistics')
                rsp, getpreread = project_api.issue_4090_to_get_pre_read_statistics()
                self.print_pre_read_information(getpreread)
                logger.flow('17-1', 'check pre read statistics specific field should 0')
                #self.check_all_zero(getpreread)
                if getpreread.pre_read_enter_counter.value != 0 or getpreread.pre_read_exit_counter.value != 0 or getpreread.pre_read_exit_cause.value != 0 or getpreread.pre_read_avail_buffer_counter.value !=0 or getpreread.pre_read_start_lba.value !=0 or getpreread.pre_read_lun.value != 0:
                    logger.error_lb(f'Disable PreRead detect module, make a pre read event')
                    logger.error_fp(f'expect pre read statistics specific field should 0, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                logger.flow('18', 'Enable PreRead detect module')
                rr_enable = 1
                pre_read_en = 1
                project_api.issue_C0F4_to_EnDis_RR_detect(rr_enable,pre_read_en)
        
        hw_setting.set_to_device(field = api.HwSettingField.MEDIUM_SCAN_TRIGGER_TIME, val= medium_scan_setting_bk)
        pass

    def post_process(self) -> None:
        pass
    def print_pre_read_information(self, pre_read_information:project_api.pre_read_statistics_info) -> None:
        logger.info('================= Pre_read_information =================')
        logger.info(f'pre_read_enter_counter={hex(pre_read_information.pre_read_enter_counter.value)}')
        logger.info(f'pre_read_exit_counter={hex(pre_read_information.pre_read_exit_counter.value)}')
        logger.info(f'pre_read_exit_cause={hex(pre_read_information.pre_read_exit_cause.value)}')
        logger.info(f'pre_read_avail_buffer_counter={hex(pre_read_information.pre_read_avail_buffer_counter.value)}')
        logger.info(f'next_SR_command_count={hex(pre_read_information.next_SR_command_count.value)}')
        logger.info(f'RR_command_count={hex(pre_read_information.RR_command_count.value)}')
        logger.info(f'current_SR_start_lba={hex(pre_read_information.current_SR_start_lba.value)}')
        logger.info(f'next_SR_start_lba={hex(pre_read_information.next_SR_start_lba.value)}')
        logger.info(f'pre_read_start_lba={hex(pre_read_information.pre_read_start_lba.value)}')
        logger.info(f'pre_read_lun={hex(pre_read_information.pre_read_lun.value)}')
        return   
    def get_and_print_pre_read_information(self) -> project_api.pre_read_statistics_info:
        rsp, pre_read_information = project_api.issue_4090_to_get_pre_read_statistics()
        self.print_pre_read_information(pre_read_information)
        return pre_read_information  
    def assign_get_nand_feature_info(self, data_payload:bytearray) -> get_nand_feature_format:
        self.get_nand_info_format = get_nand_feature_format()
        testbytes = data_payload[0:4]
        print(type(testbytes))
        print(type(data_payload[0:4]))
        self.get_nand_info_format.result.value = int.from_bytes(data_payload[0:4], byteorder='little')
        self.get_nand_info_format.die.value = int.from_bytes(data_payload[4:8], byteorder='little')
        self.get_nand_info_format.P1.value = int.from_bytes(data_payload[8:12], byteorder='little')
        self.get_nand_info_format.P2.value = int.from_bytes(data_payload[12:16], byteorder='little')
        self.get_nand_info_format.P3.value = int.from_bytes(data_payload[16:20], byteorder='little')
        self.get_nand_info_format.P4.value = int.from_bytes(data_payload[20:24], byteorder='little')
        return self.get_nand_info_format       
    def assign_set_nand_feature_info(self, data_payload:bytearray) -> set_nand_feature_format:
        self.set_nand_info_format = set_nand_feature_format()
        testbytes = data_payload[0:4]
        print(type(testbytes))
        print(type(data_payload[0:4]))
        self.get_nand_info_format.result.value = int.from_bytes(data_payload[0:4], byteorder='little')
        return self.set_nand_info_format   
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
            desc.header.b3_boot_enable = api.BootEnable.BOOT_ENABLE
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
                #if index == 0 and unit_idx == self.TestNormalLun:
                if (index *8 + unit_idx) == self.TestNormalLun:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.NORMAL
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    #desc.units[unit_idx].l4_num_alloc_units = 8092
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                #elif index == 0 and unit_idx == self.TestBootA:
                elif (index *8 + unit_idx) == self.TestBootA:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_A
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                #elif index == 0 and unit_idx == self.TestBootB:
                elif (index *8 + unit_idx) == self.TestBootB:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_B
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                #elif index == 0 and unit_idx == self.TestEM1Lun:
                elif (index *8 + unit_idx) == self.TestEM1Lun:
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
    def check_all_zero(self, obj: Any) -> None:
        payload = obj.payload
        for idx, byte_val in enumerate(payload):
            if byte_val != 0:
                logger.error(f"expect data all zero, but result fail")
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    def check_not_all_zero(self, obj: Any) -> None:
        payload = obj.payload
        result = False
        for idx, byte_val in enumerate(payload):
            if byte_val != 0:
                result = True
                break
        if result == False:
            logger.error(f"expect data not all zero, but result fail")
run = Pattern().run
if __name__ == "__main__":
    run()