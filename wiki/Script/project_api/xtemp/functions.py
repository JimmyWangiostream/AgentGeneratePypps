import inspect
import time
from Script import api, project_api
from Script.api import shared, dumpfile, cmd_seq as ExecuteCMD
import random
from Script.api.ufs_api.vendor_cmd.structs import FlashSetting, FwGeometry
from Script.project_api.PSA.structs import *
from Script.project_api.functions import send_data_in_vcmd, push_data_in_vcmd
from Script.project_api.structs import micron_vendor_cmd
from Script.pattern.pattern_logger import logger
from Script.api.exception import *

from Script.api.cmd_seq.response import CommandResponse
TEMP_GAP = 37

def set_xtemp_environment(Set_Tstatus:str, fw_geometry:FwGeometry, flash_setting:FlashSetting) -> tuple[int,int,int,int,int]:
    status_uc = Set_Tstatus.upper()
    if status_uc not in {"HOT", "SAFE", "COLD"}:
        logger.error_lb(f'Set xtemp environment with risky Tstatus')
        logger.error_fp(f'Input parameter Tstatus = "{Set_Tstatus}" is unexpected')
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION

    XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2 = get_xtemp_parameter()

    if fw_geometry.l4180_d2d3_avg_erase_cnt < (XTEMP_ENABLE_PEC * 100):
        set_ec_value = XTEMP_ENABLE_PEC * 100
        value_bytes = set_ec_value.to_bytes(4, byteorder='little', signed=False)
        data = bytearray(b'\xFF' * 0x4000)
        data[:(fw_geometry.l52_total_vb_count * 4)] = value_bytes * fw_geometry.l52_total_vb_count
        set_ec(data)
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)

    if status_uc == "HOT":
        set_nand_temp(set_temp=XTEMP_REFRESH_T2 + 1, flash_setting=flash_setting)
    elif status_uc == "COLD":
        set_nand_temp(set_temp=XTEMP_REFRESH_T1 - 1, flash_setting=flash_setting)
    else:
        set_nand_temp(set_temp=(XTEMP_REFRESH_T1 + XTEMP_REFRESH_T2) // 2, flash_setting=flash_setting)
    time.sleep(XTEMP_TIME_DETECTION_VALUE)

    return XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2


def get_xtemp_parameter(set_enable_PEC:bool = True, expected_enable_PEC:int = 10) -> tuple[int,int,int,int,int]:
    rsp, mconfig = project_api.get_mConfig_data()
    XTEMP_ENABLE_PEC = mconfig.XTEMP_ENABLE_PEC.value
    XTEMP_TEMP_BUFFER = mconfig.XTEMP_TEMP_BUFFER.value
    XTEMP_TIME_DETECTION_VALUE = mconfig.XTEMP_TIME_DETECTION_VALUE.value
    XTEMP_REFRESH_T1 = mconfig.XTEMP_Refresh_T1.value if mconfig.XTEMP_Refresh_T1.value <= 127 else mconfig.XTEMP_Refresh_T1.value - 256
    XTEMP_REFRESH_T2 = mconfig.XTEMP_Refresh_T2.value if mconfig.XTEMP_Refresh_T2.value <= 127 else mconfig.XTEMP_Refresh_T2.value - 256
    logger.info(f'Xtemp enable EPC = {XTEMP_ENABLE_PEC}, temp buffer = {XTEMP_TEMP_BUFFER}, time detection = {XTEMP_TIME_DETECTION_VALUE}')
    logger.info(f'Xtemp refresh T1 = {XTEMP_REFRESH_T1}, Xtemp refresh T2 = {XTEMP_REFRESH_T2}')

    if mconfig.XTEMP_ENABLE_PEC.value != expected_enable_PEC and set_enable_PEC == True:
        logger.info(f'Current Xtemp enable EPC = {XTEMP_ENABLE_PEC}, modify as {expected_enable_PEC} for testing')
        mconfig.XTEMP_ENABLE_PEC.value = expected_enable_PEC
        mconfig.payload[0:7] = "MCONFIG".encode("ascii")
        project_api.set_mConfig_data(mConfig=mconfig)
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)    

        rsp, mconfig = project_api.get_mConfig_data()
        XTEMP_ENABLE_PEC = mconfig.XTEMP_ENABLE_PEC.value
        XTEMP_TEMP_BUFFER = mconfig.XTEMP_TEMP_BUFFER.value
        XTEMP_TIME_DETECTION_VALUE = mconfig.XTEMP_TIME_DETECTION_VALUE.value
        XTEMP_REFRESH_T1 = mconfig.XTEMP_Refresh_T1.value if mconfig.XTEMP_Refresh_T1.value <= 127 else mconfig.XTEMP_Refresh_T1.value - 256
        XTEMP_REFRESH_T2 = mconfig.XTEMP_Refresh_T2.value if mconfig.XTEMP_Refresh_T2.value <= 127 else mconfig.XTEMP_Refresh_T2.value - 256
        logger.info(f'Xtemp enable EPC = {XTEMP_ENABLE_PEC}, temp buffer = {XTEMP_TEMP_BUFFER}, time detection = {XTEMP_TIME_DETECTION_VALUE}')
        logger.info(f'Xtemp refresh T1 = {XTEMP_REFRESH_T1}, Xtemp refresh T2 = {XTEMP_REFRESH_T2}')
    return XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2
    
def set_ec(data:bytearray) -> None:
    api.ufs_api.vendor_cmd.access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdWrite()
    vuc.assign(length=api.DATA_SIZE_16K_BYTE, cmd_index=api.VendorCmd.GET_FW_GEOMETRY, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = api.VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b6_cmd2 = 4
    vuc.data = data
    vuc.enqueue()
    ExecuteCMD.send()

def set_nand_temp(set_temp:int, flash_setting:FlashSetting) -> None:
    temp_set = 65536 + set_temp if set_temp < 0 else set_temp
    set_nand_temp = project_api.SetNandTemperature()
    set_nand_temp.bEnableSetVuTemp.value = 1
    set_nand_temp.UC_TERMAL_SENSOR_1.value = temp_set
    set_nand_temp.NAND_TEMPERATURE_DIE_0.value = temp_set
    if flash_setting.Max_Fdevice >= 2:
        set_nand_temp.NAND_TEMPERATURE_DIE_1.value = temp_set
    if flash_setting.Max_Fdevice >= 4:
        set_nand_temp.NAND_TEMPERATURE_DIE_2.value = temp_set
        set_nand_temp.NAND_TEMPERATURE_DIE_3.value = temp_set
    set_nand_temp.Use_Delayed_fake_tmeperatures.value = 0  
    rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)
    get_nand_temp()    

def get_nand_temp() -> None:
    rsp , GetNandTemperature = project_api.issue_4021_get_nand_temperature()
    die0_temp = GetNandTemperature.temperature_of_die_0.value - TEMP_GAP
    die1_temp = GetNandTemperature.temperature_of_die_1.value - TEMP_GAP
    die2_temp = GetNandTemperature.temperature_of_die_2.value - TEMP_GAP
    die3_temp = GetNandTemperature.temperature_of_die_3.value - TEMP_GAP
    logger.info(f'{die0_temp} / {die1_temp} / {die2_temp} / {die3_temp}')   