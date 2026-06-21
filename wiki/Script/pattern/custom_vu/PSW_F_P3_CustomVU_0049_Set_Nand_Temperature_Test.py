import package_root
from typing import List
from Script import api
from Script.api.util.functions import dumpfile
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig, get_flash_setting
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api import read_fw_value
import time
from Script.project_api.health_report.structs import ReadEnhanceHealthReport
from Script.project_api.set_get_temperature.structs import GetNandTemperature, SetNandTemperature
import inspect
from Script.api import  cmd_seq as ExecuteCMD


class Pattern(UFSTC):
    def pre_process(self) -> None:
        flash_setting = get_flash_setting()
        self.hw_setting = api.HwSetting.get_instance()
        self.power_saving_ctrl_backup = self.hw_setting.get_local_val(api.HwSettingField.POWER_SAVING_CTRL_ENABLE)
        self.hw_setting.set_to_device(field = api.HwSettingField.POWER_SAVING_CTRL_ENABLE, val= 0x3A)
        self.ce_num = flash_setting.Max_Fdevice
        self.temp_gap = 37
        pass

    def get_nand_temp(self) -> GetNandTemperature:
        rsp , GetNandTemperature = project_api.issue_4021_get_nand_temperature()
        die0_temp = GetNandTemperature.temperature_of_die_0.value - self.temp_gap
        die1_temp = GetNandTemperature.temperature_of_die_1.value - self.temp_gap
        die2_temp = GetNandTemperature.temperature_of_die_2.value - self.temp_gap
        die3_temp = GetNandTemperature.temperature_of_die_3.value - self.temp_gap
        logger.info(f'{die0_temp} / {die1_temp} / {die2_temp} / {die3_temp}')
        return GetNandTemperature

    def set_temp(self, temp:int) -> None:
        temp = 65536 + temp if temp < 0 else temp
        set_nand_temp = SetNandTemperature()
        set_nand_temp.bEnableSetVuTemp.value = 1
        set_nand_temp.NAND_TEMPERATURE_DIE_0.value = temp
        set_nand_temp.UC_TERMAL_SENSOR_1.value = temp
        if self.ce_num >= 2:
            set_nand_temp.NAND_TEMPERATURE_DIE_1.value = temp
        if self.ce_num >= 4:
            set_nand_temp.NAND_TEMPERATURE_DIE_2.value = temp
            set_nand_temp.NAND_TEMPERATURE_DIE_3.value = temp
        set_nand_temp.Use_Delayed_fake_tmeperatures.value = 1
        rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)

    def show_health_report_temp_profile(self, health_report_before:ReadEnhanceHealthReport, health_report:ReadEnhanceHealthReport, detect:int) -> None:
        if detect == 0:
            logger.info(f'count of temp lower than -37 : {health_report.temperature_profile_t_37.value}')
            logger.info(f'count of temp -37 to -25     : {health_report.temperature_profile_37_t_25.value}')
            logger.info(f'count of temp -25 to 0       : {health_report.temperature_profile_25_t_0.value}')
            logger.info(f'count of temp 0 to 95        : {health_report.temperature_profile_0_t_95.value}')
            logger.info(f'count of temp 95 to 115      : {health_report.temperature_profile_95_t_115.value}')
            logger.info(f'count of temp higher than 115: {health_report.temperature_profile_t_115.value}')
        else:
            logger.info(f'count of temp lower than -37 : {health_report_before.temperature_profile_t_37.value} -> {health_report.temperature_profile_t_37.value}')
            logger.info(f'count of temp -37 to -25     : {health_report_before.temperature_profile_37_t_25.value} -> {health_report.temperature_profile_37_t_25.value}')
            logger.info(f'count of temp -25 to 0       : {health_report_before.temperature_profile_25_t_0.value} -> {health_report.temperature_profile_25_t_0.value}')
            logger.info(f'count of temp 0 to 95        : {health_report_before.temperature_profile_0_t_95.value} -> {health_report.temperature_profile_0_t_95.value}')
            logger.info(f'count of temp 95 to 115      : {health_report_before.temperature_profile_95_t_115.value} -> {health_report.temperature_profile_95_t_115.value}')
            logger.info(f'count of temp higher than 115: {health_report_before.temperature_profile_t_115.value} -> {health_report.temperature_profile_t_115.value}')

    def get_temp_profile_detect_zone(self, test_temp:int) -> int:
        if test_temp <= -37:
            return 0
        elif test_temp <= -25:
            return 1
        elif test_temp <= 0:
            return 2
        elif test_temp <= 95:
            return 3
        elif test_temp <= 115:
            return 4
        else:
            return 5

    def judge_health_report_temp_profile_field(self, health_report_before:ReadEnhanceHealthReport, health_report:ReadEnhanceHealthReport, test_temp:int) -> None:
        counter_value_change_str:List[str] = []
        detect_zone:int = 0
        diff_of_detect_zone:List[int] = []
        diff_of_detect_zone.append(health_report.temperature_profile_t_37.value - health_report_before.temperature_profile_t_37.value)
        diff_of_detect_zone.append(health_report.temperature_profile_37_t_25.value - health_report_before.temperature_profile_37_t_25.value)
        diff_of_detect_zone.append(health_report.temperature_profile_25_t_0.value - health_report_before.temperature_profile_25_t_0.value)
        diff_of_detect_zone.append(health_report.temperature_profile_0_t_95.value - health_report_before.temperature_profile_0_t_95.value)
        diff_of_detect_zone.append(health_report.temperature_profile_95_t_115.value - health_report_before.temperature_profile_95_t_115.value)
        diff_of_detect_zone.append(health_report.temperature_profile_t_115.value - health_report_before.temperature_profile_t_115.value)
        counter_value_change_str.append(f'count of temp lower than -37 : {health_report_before.temperature_profile_t_37.value} -> {health_report.temperature_profile_t_37.value}')
        counter_value_change_str.append(f'count of temp -37 to -25     : {health_report_before.temperature_profile_37_t_25.value} -> {health_report.temperature_profile_37_t_25.value}')
        counter_value_change_str.append(f'count of temp -25 to 0       : {health_report_before.temperature_profile_25_t_0.value} -> {health_report.temperature_profile_25_t_0.value}')
        counter_value_change_str.append(f'count of temp 0 to 95        : {health_report_before.temperature_profile_0_t_95.value} -> {health_report.temperature_profile_0_t_95.value}')
        counter_value_change_str.append(f'count of temp 95 to 115      : {health_report_before.temperature_profile_95_t_115.value} -> {health_report.temperature_profile_95_t_115.value}')
        counter_value_change_str.append(f'count of temp higher than 115: {health_report_before.temperature_profile_t_115.value} -> {health_report.temperature_profile_t_115.value}')
        detect_zone = self.get_temp_profile_detect_zone(test_temp=test_temp)

        if diff_of_detect_zone[detect_zone] <= 0:
            logger.error_lb(f'VU set temp = {test_temp} and check health report temperature profile')
            logger.error_fp(f'{counter_value_change_str[detect_zone]}, the value shall be increased but not')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        for zone in range(len(diff_of_detect_zone)):
            if zone != detect_zone and diff_of_detect_zone[zone] != 0:
                logger.error_lb(f'VU set temp = {test_temp} and check health report temperature profile')
                logger.error_fp(f'{counter_value_change_str[zone]}, the value shall keep but not')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def get_highest_lowest_temp_of_health_report(self) -> tuple[List[int],int,int,int,int,int]:
        response, health_report = project_api.issue_40FE_to_read_enhanced_health_report()
        nand_temp:List[int] = []
        nand_temp.append(health_report.current_nand_temp_die_0.value if health_report.current_nand_temp_die_0.value <= 127 else health_report.current_nand_temp_die_0.value - 256)
        nand_temp.append(health_report.current_nand_temp_die_1.value if health_report.current_nand_temp_die_1.value <= 127 else health_report.current_nand_temp_die_1.value - 256)
        nand_temp.append(health_report.current_nand_temp_die_2.value if health_report.current_nand_temp_die_2.value <= 127 else health_report.current_nand_temp_die_2.value - 256)
        nand_temp.append(health_report.current_nand_temp_die_3.value if health_report.current_nand_temp_die_3.value <= 127 else health_report.current_nand_temp_die_3.value - 256)
        uc_temp = health_report.current_uc_temperature.value if health_report.current_uc_temperature.value <= 127 else health_report.current_uc_temperature.value - 256
        highest = health_report.highest_temp.value if health_report.highest_temp.value <= 127 else health_report.highest_temp.value - 256
        lowest = health_report.lowest_temp.value if health_report.lowest_temp.value <= 127 else health_report.lowest_temp.value - 256
        power_on_highest = health_report.power_on_highest_temp.value if health_report.power_on_highest_temp.value <= 127 else health_report.power_on_highest_temp.value - 256
        power_on_lowest = health_report.power_on_lowest_temp.value if health_report.power_on_lowest_temp.value <= 127 else health_report.power_on_lowest_temp.value - 256
        logger.info(f'nand temp (die0 ~ 3)  : {nand_temp}')
        logger.info(f'current uc temp       : {uc_temp}')
        logger.info(f'Highest temp          : {highest}')
        logger.info(f'Lowest temp           : {lowest}')
        logger.info(f'Power On Highest temp : {power_on_highest}')
        logger.info(f'Power On Lowest temp  : {power_on_lowest}')
        return nand_temp, uc_temp, highest, lowest, power_on_highest, power_on_lowest

    def show_health_report_temp_delta(self, health_report_before:ReadEnhanceHealthReport, health_report:ReadEnhanceHealthReport) -> None:
        logger.info(f'count of temp delta less than 1 : {health_report_before.temperature_delta_t_1.value} -> {health_report.temperature_delta_t_1.value}')
        logger.info(f'count of temp delta 1 to 5      : {health_report_before.temperature_delta_1_t_5.value} -> {health_report.temperature_delta_1_t_5.value}')
        logger.info(f'count of temp delta 5 to 10     : {health_report_before.temperature_delta_5_t_10.value} -> {health_report.temperature_delta_5_t_10.value}')
        logger.info(f'count of temp delta 10 to 15    : {health_report_before.temperature_delta_10_t_15.value} -> {health_report.temperature_delta_10_t_15.value}')
        logger.info(f'count of temp delta more than 15: {health_report_before.temperature_delta_t_15.value} -> {health_report.temperature_delta_t_15.value}')

    def get_temp_delta_detect_zone(self, test_temp_gap:int) -> int:
        if test_temp_gap < 1:
            return 0
        elif test_temp_gap < 5:
            return 1
        elif test_temp_gap < 10:
            return 2
        elif test_temp_gap < 15:
            return 3
        else:
            return 4

    def judge_health_report_temp_delta_field(self, health_report_before:ReadEnhanceHealthReport, health_report:ReadEnhanceHealthReport, test_temp_gap:int) -> None:
        counter_value_change_str:List[str] = []
        detect_zone:int = 0
        diff_of_detect_zone:List[int] = []
        diff_of_detect_zone.append(health_report.temperature_delta_t_1.value - health_report_before.temperature_delta_t_1.value)
        diff_of_detect_zone.append(health_report.temperature_delta_1_t_5.value - health_report_before.temperature_delta_1_t_5.value)
        diff_of_detect_zone.append(health_report.temperature_delta_5_t_10.value - health_report_before.temperature_delta_5_t_10.value)
        diff_of_detect_zone.append(health_report.temperature_delta_10_t_15.value - health_report_before.temperature_delta_10_t_15.value)
        diff_of_detect_zone.append(health_report.temperature_delta_t_15.value - health_report_before.temperature_delta_t_15.value)
        counter_value_change_str.append(f'count of temp delta less than 1 : {health_report_before.temperature_delta_t_1.value} -> {health_report.temperature_delta_t_1.value}')
        counter_value_change_str.append(f'count of temp delta 1 to 5      : {health_report_before.temperature_delta_1_t_5.value} -> {health_report.temperature_delta_1_t_5.value}')
        counter_value_change_str.append(f'count of temp delta 5 to 10     : {health_report_before.temperature_delta_5_t_10.value} -> {health_report.temperature_delta_5_t_10.value}')
        counter_value_change_str.append(f'count of temp delta 10 to 15    : {health_report_before.temperature_delta_10_t_15.value} -> {health_report.temperature_delta_10_t_15.value}')
        counter_value_change_str.append(f'count of temp delta more than 15: {health_report_before.temperature_delta_t_15.value} -> {health_report.temperature_delta_t_15.value}')
        detect_zone = self.get_temp_delta_detect_zone(test_temp_gap=test_temp_gap)

        if diff_of_detect_zone[detect_zone] <= 0:
            logger.error_lb(f'VU set temp with gap = {test_temp_gap} and check health report temperature delta')
            logger.error_fp(f'{counter_value_change_str[detect_zone]}, the value shall be increased but not')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        for zone in range(len(diff_of_detect_zone)):
            if zone != detect_zone and diff_of_detect_zone[zone] != 0 and zone != 0:
                logger.error_lb(f'VU set temp with gap = {test_temp_gap} and check health report temperature delta')
                logger.error_fp(f'{counter_value_change_str[zone]}, the value shall keep but not')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def step1(self) -> None:
        logger.flow(1,"issue 4021 to get each nand temperature when pattern starting for log record")
        GetNandTemperature = self.get_nand_temp()

        logger.flow(2,"issue 40FE to get enhanced health report to getting highest/lowest value for default value verification")
        nand_temp, uc_temp, highest, lowest, power_on_highest, power_on_lowest = self.get_highest_lowest_temp_of_health_report()
        default_highest_lowest_verify_pass = True
        environmentLowest = 10
        environmentHighest = 60
        if highest < environmentLowest or highest > environmentHighest: default_highest_lowest_verify_pass = False
        if lowest < environmentLowest or lowest > environmentHighest: default_highest_lowest_verify_pass = False
        if power_on_highest < environmentLowest or power_on_highest > environmentHighest: default_highest_lowest_verify_pass = False
        if power_on_lowest < environmentLowest or power_on_lowest > environmentHighest: default_highest_lowest_verify_pass = False
        if default_highest_lowest_verify_pass == False:
            logger.error_lb(f'Check highest/lowest default values of health report when pattern start')
            logger.error_fp(f'The default value should between {environmentLowest} to {environmentHighest} but not')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        temp_set = 20
        high_temp_test = 85
        logger.flow(3,f"issue D08A to set temperature , with Use_Delayed_fake_tmeperatures = 0, bEnableSetVuTemp = 1,  tempeprature = {temp_set},  , sensor1 (controller) = {high_temp_test}")
        set_nand_temp = SetNandTemperature()
        set_nand_temp.bEnableSetVuTemp.value = 1
        set_nand_temp.NAND_TEMPERATURE_DIE_0.value = temp_set
        set_nand_temp.UC_TERMAL_SENSOR_1.value = high_temp_test
        if self.ce_num >= 2:
            set_nand_temp.NAND_TEMPERATURE_DIE_1.value = temp_set
        if self.ce_num >= 4:
            set_nand_temp.NAND_TEMPERATURE_DIE_2.value = temp_set
            set_nand_temp.NAND_TEMPERATURE_DIE_3.value = temp_set
        set_nand_temp.Use_Delayed_fake_tmeperatures.value = 0  
        rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)
        time.sleep(2)

        logger.flow(4,"issue 4021 to get each nand temperature that values should be the same as D08A setting")
        GetNandTemperature = self.get_nand_temp()
        if (temp_set + self.temp_gap) != GetNandTemperature.temperature_of_die_0.value:
            logger.error_fp(f'temperature ce0 compare fail')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if self.ce_num >= 2:
            if (temp_set + self.temp_gap)!= GetNandTemperature.temperature_of_die_1.value:
                logger.error_fp(f'temperature ce1 compare fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if self.ce_num >= 4:
            if (temp_set + self.temp_gap) != GetNandTemperature.temperature_of_die_2.value:
                logger.error_fp(f'temperature ce2 compare fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if (temp_set + self.temp_gap) != GetNandTemperature.temperature_of_die_3.value:
                logger.error_fp(f'temperature ce3 compare fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(5,"issue 40FD to get controller temperature that value should be the same as D08A setting")
        VU_temp = project_api.issue_40FD_get_uC_temp_value()
        logger.info(f'temp = {VU_temp}')
        if VU_temp != high_temp_test:
            logger.error_fp(f'temperature controller compare fail, VU 0x40FD get temp {VU_temp} != setting temp {high_temp_test}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(6,f"issue 40FE to get nand temp and uC temp of enhanced health report that values should be the same as D08A setting, and the highest temp field should be {high_temp_test}")
        nand_temp, uc_temp, highest, lowest, power_on_highest, power_on_lowest = self.get_highest_lowest_temp_of_health_report()
        for die in range(4):
            if die == self.ce_num:
                break
            elif nand_temp[die] != temp_set:
                logger.error_lb(f'VU 40FE get enhanced health report for verifying after VU D08A set temp')
                logger.error_fp(f'CE{die} temperature compare fail, health report value: {nand_temp[die]}, setting value: {temp_set}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if uc_temp != high_temp_test:
            logger.error_lb(f'VU 40FE get enhanced health report for verifying after VU D08A set temp')
            logger.error_fp(f'Current uc temperature compare fail, health report value: {uc_temp}, setting value: {high_temp_test}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if highest != high_temp_test:
            logger.error_lb(f'VU 40FE get enhanced health report for verifying after VU D08A set temp')
            logger.error_fp(f'Highest temperature compare fail, health report value: {highest}, setting value: {high_temp_test}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if power_on_highest != high_temp_test:
            logger.error_lb(f'VU 40FE get enhanced health report for verifying after VU D08A set temp')
            logger.error_fp(f'Power on highest temperature compare fail, health report value: {power_on_highest}, setting value: {high_temp_test}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        low_temp_test = -25
        logger.flow(7,f"issue D08A to set temperature , with Use_Delayed_fake_tmeperatures = 0, bEnableSetVuTemp = 1,  tempeprature = {temp_set},  , sensor1 (controller) = {low_temp_test}")
        set_nand_temp = SetNandTemperature()
        set_nand_temp.UC_TERMAL_SENSOR_1.value = 65536 + low_temp_test
        rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)
        time.sleep(2)

        logger.flow(8,"issue 4021 to get each nand temperature that values should be the same as D08A setting")
        GetNandTemperature = self.get_nand_temp()
        if (temp_set + self.temp_gap) != GetNandTemperature.temperature_of_die_0.value:
            logger.error_fp(f'temperature ce0 compare fail')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if self.ce_num >= 2:
            if (temp_set + self.temp_gap)!= GetNandTemperature.temperature_of_die_1.value:
                logger.error_fp(f'temperature ce1 compare fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if self.ce_num >= 4:
            if (temp_set + self.temp_gap) != GetNandTemperature.temperature_of_die_2.value:
                logger.error_fp(f'temperature ce2 compare fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if (temp_set + self.temp_gap) != GetNandTemperature.temperature_of_die_3.value:
                logger.error_fp(f'temperature ce3 compare fail')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(9,"issue 40FD to get controller temperature that value should be the same as D08A setting")
        VU_temp = project_api.issue_40FD_get_uC_temp_value()
        logger.info(f'temp = {VU_temp}')
        if VU_temp != low_temp_test:
            logger.error_fp(f'temperature controller compare fail, VU 0x40FD get temp {VU_temp} != setting temp {low_temp_test}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(10,f"issue 40FE to get nand temp and uC temp of enhanced health report that values should be the same as D08A setting, and the highest temp field should be {low_temp_test}")
        nand_temp, uc_temp, highest, lowest, power_on_highest, power_on_lowest = self.get_highest_lowest_temp_of_health_report()
        for die in range(4):
            if die == self.ce_num:
                break
            elif nand_temp[die] != temp_set:
                logger.error_lb(f'VU 40FE get enhanced health report for verifying after VU D08A set temp')
                logger.error_fp(f'CE{die} temperature compare fail, health report value: {nand_temp[die]}, setting value: {temp_set}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if uc_temp != low_temp_test:
            logger.error_lb(f'VU 40FE get enhanced health report for verifying after VU D08A set temp')
            logger.error_fp(f'Current uc temperature compare fail, health report value: {uc_temp}, setting value: {low_temp_test}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if lowest != low_temp_test:
            logger.error_lb(f'VU 40FE get enhanced health report for verifying after VU D08A set temp')
            logger.error_fp(f'Lowest temperature compare fail, health report value: {lowest}, setting value: {low_temp_test}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if power_on_lowest != low_temp_test:
            logger.error_lb(f'VU 40FE get enhanced health report for verifying after VU D08A set temp')
            logger.error_fp(f'Power on lowest temperature compare fail, health report value: {power_on_lowest}, setting value: {low_temp_test}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(11,'HW reset(POR) and check power_on_highest/power_on_lowest should reset and highest/lowest should keep same record')
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=True)
        nand_temp, uc_temp, highest, lowest, power_on_highest, power_on_lowest = self.get_highest_lowest_temp_of_health_report()
        if highest != high_temp_test:
            logger.error_lb(f'VU 40FE get enhanced health report for verifying after power cycle')
            logger.error_fp(f'Highest temperature compare fail, highest value should keep testing value: {high_temp_test}, but current value: {highest}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if power_on_highest < environmentLowest or power_on_highest > environmentHighest:
            logger.error_lb(f'VU 40FE get enhanced health report for verifying after power cycle')
            logger.error_fp(f'Power on highest temperature compare fail, power on highest value should less than testing value: {high_temp_test}, but current value: {power_on_highest}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if lowest != low_temp_test:
            logger.error_lb(f'VU 40FE get enhanced health report for verifying after power cycle')
            logger.error_fp(f'Lowest temperature compare fail, lowest value should keep testing value: {low_temp_test}, but current value: {lowest}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if power_on_lowest < environmentLowest or power_on_lowest > environmentHighest:
            logger.error_lb(f'VU 40FE get enhanced health report for verifying after power cycle')
            logger.error_fp(f'Power on lowest temperature compare fail, power on lowest value should larger than testing value: {low_temp_test}, but current value: {power_on_lowest}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(12,'Set temp with different interval and issue 40FE to get temperature delta values of enhanced health report that values should be increased with mapping zone')
        test_temp = 40
        self.set_temp(temp = test_temp)
        time.sleep(2)
        response, health_report = project_api.issue_40FE_to_read_enhanced_health_report()
        health_report_before = health_report
        for test_temp_gap in range(2,20):
            test_temp = test_temp + test_temp_gap if test_temp_gap % 2 == 0 else test_temp - test_temp_gap
            self.set_temp(temp = test_temp)
            time.sleep(2)
            response, health_report = project_api.issue_40FE_to_read_enhanced_health_report()
            logger.info(f'set temp = {test_temp}, test temp gap = {test_temp_gap}')
            self.show_health_report_temp_delta(health_report_before=health_report_before, health_report=health_report)
            self.judge_health_report_temp_delta_field(health_report_before=health_report_before, health_report=health_report, test_temp_gap=test_temp_gap)
            health_report_before = health_report

        test_temp_list:List[int] = [-37, -36, -26, -25, -24, -1, 0, 1, 94, 95, 96, 114, 115, 116]
        logger.flow(13,f"Set temp with values {test_temp_list} and issue 40FE to get temperature profile values of enhanced health report that values should be increased with mapping zone")
        response, health_report = project_api.issue_40FE_to_read_enhanced_health_report()
        health_report_before = health_report
        for test_temp in test_temp_list:
            self.set_temp(temp = test_temp)
            for detect in range(5):
                time.sleep(2)
                response, health_report = project_api.issue_40FE_to_read_enhanced_health_report()
                logger.info(f'set temp = {test_temp}')
                self.show_health_report_temp_profile(health_report_before=health_report_before, health_report=health_report,detect=detect)
                if detect != 0:
                    self.judge_health_report_temp_profile_field(health_report_before=health_report_before, health_report=health_report, test_temp=test_temp)
                health_report_before = health_report

        # recover
        set_nand_temp.bEnableSetVuTemp.value = 0
        rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)
        pass

    def post_process(self) -> None:
        pass
    



run = Pattern().run
if __name__ == "__main__":
    run()