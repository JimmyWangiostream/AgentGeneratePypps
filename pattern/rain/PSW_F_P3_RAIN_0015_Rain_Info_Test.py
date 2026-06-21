import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.rain.mutual_fun import *
import copy

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.TestNormalLun, self.TestEM1Lun, self.TestWBLun, self.flash_setting, self.fw_geometry = rain_pattern_precondition()
        self.max_ce, self.max_plane, self.max_pageline = get_geometry_parameter()
        self.write_record = api.get_empty_write_record()
        pass

    def step1(self) -> None:
        logger.flow(1, f'issue 4054 to get rain info')
        _, self.rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
        dumpfile(f"rain_info.bin", self.rain_info.payload)
        print_rain_info(rain_info=self.rain_info)
        self.rain_info_bkup = copy.deepcopy(self.rain_info)
        pass
        
    def step2(self) -> None:
        logger.flow(2, f'check fixed rain info fields')
        expect_value = 0xFFFFFFFF
        self.check_value(parent=self.rain_info, checkfield=self.rain_info.dummy, expect_value=expect_value)
        expect_value = 1104
        self.check_value(parent=self.rain_info, checkfield=self.rain_info.host_data_pageline_count_in_SLC_VB, expect_value=expect_value)
        rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode=TestMode.TEST_SLC)
        expect_value = 1104 * 4 * self.max_plane * self.max_ce - (rain_goup_cnt + 2) * 4
        self.check_value(parent=self.rain_info, checkfield=self.rain_info.host_data_LBA_size_in_SLC_VB, expect_value=expect_value)
        expect_value = 3312
        self.check_value(parent=self.rain_info, checkfield=self.rain_info.host_data_pageline_count_in_TLC_VB, expect_value=expect_value)
        rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode=TestMode.TEST_TLC)
        expect_value = 3312 * 4 * self.max_plane * self.max_ce - (rain_goup_cnt + 2) * 4
        self.check_value(parent=self.rain_info, checkfield=self.rain_info.host_data_LBA_size_in_TLC_VB, expect_value=expect_value)
        expect_value = 1104
        self.check_value(parent=self.rain_info, checkfield=self.rain_info.max_raw_pageline_count_in_in_SLC_VB, expect_value=expect_value)
        expect_value = 1104 * 4 * self.max_plane * self.max_ce
        self.check_value(parent=self.rain_info, checkfield=self.rain_info.max_raw_LBA_size_in_SLC_VB, expect_value=expect_value)
        expect_value = 3312
        self.check_value(parent=self.rain_info, checkfield=self.rain_info.max_raw_pageline_count_in_in_TLC_VB, expect_value=expect_value)
        expect_value = 3312 * 4 * self.max_plane * self.max_ce
        self.check_value(parent=self.rain_info, checkfield=self.rain_info.max_raw_LBA_size_in_TLC_VB, expect_value=expect_value)
        expect_value = self.max_ce
        self.check_value(parent=self.rain_info, checkfield=self.rain_info.CE, expect_value=expect_value)
        

    def step3(self) -> None:
        logger.flow(3, f'issue D08B to disable RAIN')
        Table_and_S_CHK_rain = 0
        Host_Permanent_Rain = 0
        Host_Simple_Rain = 0
        host_full_block_protection_rain = 0
        project_api.issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain, Host_Permanent_Rain, Host_Simple_Rain, host_full_block_protection_rain)
        pass
        
    def step4(self) -> None:
        logger.flow(4, f'check BIT_MAP of rain_info all disabled after D08B')
        _, self.rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
        expect_value = 0
        print_rain_info(rain_info=self.rain_info)
        self.check_RAIN_bit_map_value(expect_value=expect_value)
    
    def step5(self) -> None:
        logger.flow(5, f'issue D08B to enable RAIN')
        Table_and_S_CHK_rain = cast(int, project_api.RainVB.ALL)
        Host_Permanent_Rain = cast(int, project_api.RainVB.ALL)
        Host_Simple_Rain = cast(int, project_api.RainVB.ALL)
        host_full_block_protection_rain = cast(int, project_api.RainVB.ALL)
        project_api.issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain, Host_Permanent_Rain, Host_Simple_Rain, host_full_block_protection_rain)
        pass
        
    def step6(self) -> None:
        logger.flow(6, f'check BIT_MAP of rain_info all enabled after D08B')
        _, self.rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
        expect_value = 1
        print_rain_info(rain_info=self.rain_info)
        self.check_RAIN_bit_map_value(expect_value=expect_value)
        pass
        
    def step7(self) -> None:
        logger.info(f'check RAIN accumulation count')
        for testMode in [TestMode.TEST_TLC, TestMode.TEST_SLC, TestMode.TEST_WB, TestMode.TEST_L1, TestMode.TEST_PTE, TestMode.TEST_LOG]:
            lun, mode_str = get_general_parameter(testMode)            
            Rain_in_SRAM, data_recovery = get_rain_enable_disable_parameter(testMode)            
            rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode)
            logger.info(f'============ Test {mode_str} VB ============')
            if testMode == TestMode.TEST_WB:
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            
            logger.flow(7, f'write data to create open vb')
            if testMode == TestMode.TEST_LOG:
                self.ssu_sleep_and_active()
                cursor = get_specific_open_vb_cursor(testMode)
            else:
                if rain_goup_cnt>1:
                    last_lba, cursor = write_data_more_than_N_pageline(pageline_cnt=rain_goup_cnt-1, lun=lun, testMode=testMode, write_record=self.write_record)
                else:
                    last_lba, cursor = write_data_more_than_N_page(page_cnt=int(self.max_ce * self.max_plane * 0.75), lun=lun, testMode=testMode, write_record=self.write_record)
                
            logger.flow(8, f'check RAIN accumulation count is correct')
            _, self.rain_info = project_api.issue_4054_to_get_rain_info(currentCE=self.max_ce)
            self.check_RAIN_accumulation_count(cursor=cursor, testMode=testMode, mode_str = mode_str)
            print_rain_info(rain_info=self.rain_info)
        pass

    def post_process(self) -> None:
        pass
    
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
    
    def check_RAIN_bit_map_value(self, expect_value:int) -> None:
        check_list = [
            self.rain_info.Plane_based_RAIN_encoding_state,
            self.rain_info.Open_Host_VB_simple_RAIN_encoding_state,
            self.rain_info.Open_Host_VB_Full_Block_Protection_RAIN_encoding_state,
            self.rain_info.Global_permanent_RAIN_enable_flag,
            self.rain_info.Permanent_RAIN_enable_bitmap,
        ]
        for parent in check_list:
            for name, field in parent.__dict__.items():
                if hasattr(field, "value"):
                    self.check_value(parent=parent, checkfield=field, expect_value=expect_value)
        return
    
    def check_RAIN_accumulation_count(self, cursor:api.OpenVBInfoUnit, testMode:TestMode, mode_str:str) -> None:
        def format_list(l:List[int]) -> str:
            return f"[{', '.join(f'{b}' for b in l)}]"
        if testMode == TestMode.TEST_TLC:
            raw_check_list = self.rain_info.current_RAIN_accumulation_count_for_each_parity.Host_TLC
        elif testMode == TestMode.TEST_SLC:
            raw_check_list = self.rain_info.current_RAIN_accumulation_count_for_each_parity.Host_EM1
        elif testMode == TestMode.TEST_WB:
            raw_check_list = self.rain_info.current_RAIN_accumulation_count_for_each_parity.WB
        elif testMode == TestMode.TEST_PTE:
            raw_check_list = self.rain_info.current_RAIN_accumulation_count_for_each_parity.PTE
        elif testMode == TestMode.TEST_L1:
            raw_check_list = self.rain_info.current_RAIN_accumulation_count_for_each_parity.S_CHK
        elif testMode == TestMode.TEST_LOG:
            raw_check_list = self.rain_info.current_RAIN_accumulation_count_for_each_parity.LOG
        else:
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        check_list = [[raw_check_list[ce][group].value for group in range(len(raw_check_list[ce]))] for ce in range(len(raw_check_list))]
        
        rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode)
        last_pageline = cursor.first_empty_physical_page.value
        invalid_plane_list = get_invalid_plane_list()
        block = cursor.logical_vb.value
        max_ce_plane = self.max_plane * self.max_ce - 1
        if invalid_plane_list[block] == max_ce_plane:
            max_ce_plane -= 1
        for ce in range(self.max_ce):
            accumulation_list = [0 for _ in range(rain_goup_cnt)]
            if rain_goup_cnt == 1:
                for plane in range(cursor.first_empty_plane.value):
                    ce_plane = self.max_plane * ce + plane
                    if invalid_plane_list[block] == ce_plane:
                        continue
                    if max_ce_plane == ce_plane:
                        break
                    accumulation_list[0] += 4
                break
            else:
                for pageline in range(last_pageline):
                    group = pageline % rain_goup_cnt
                    for plane in range(self.max_plane):
                        ce_plane = self.max_plane * ce + plane
                        if invalid_plane_list[block] == ce_plane:
                            continue
                        accumulation_list[group] += 4
            if check_list[ce] != accumulation_list:
                logger.error_lb(f'check {mode_str} RAIN_accumulation_count')
                logger.error_fp(f'CE:{ce}, current RAIN_accumulation_count = {format_list(check_list[ce])}, manual RAIN_accumulation_count = {format_list(accumulation_list)}, result Fail!')
                dumpfile(f"rain_info_after_write.bin", self.rain_info.payload)
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    
    def check_value(self, parent:api.ABC, checkfield:api.BaseField|api.BaseFieldBit, expect_value:int) -> None:
        for name, field in parent.__dict__.items():
            if field == checkfield and hasattr(field, "value"):
                if field.value != expect_value:
                    logger.error_lb(f'check {name} in rain info')
                    logger.error_fp(f'expect {name} equal to {expect_value}, but current value = {field.value}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        return


run = Pattern().run
if __name__ == "__main__":
    run()