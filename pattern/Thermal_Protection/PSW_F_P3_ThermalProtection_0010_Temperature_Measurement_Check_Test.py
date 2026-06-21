import package_root
from Script import api
from Script.api import dumpfile
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api.ufs_api import *
import time
from typing import cast
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.project_api.thermal_protection_vu.structs import *
from Script.project_api.thermal_protection_vu.define import *
from Script.project_api.set_get_temperature.structs import SetNandTemperature

class Pattern(UFSTC):
    def get_ast_times(self) -> int:
        payload_get = project_api.get_smart_info()
        offset_ats_timer = 0x4a8
        data_size_byte = 8
        ats_times_payload = payload_get[offset_ats_timer: offset_ats_timer + data_size_byte]
        ats_times = int.from_bytes(ats_times_payload, 'little')
        logger.info(f'ats_times = {ats_times}')
        dumpfile('smart_info.bin',payload_get)
        return ats_times

    def set_temperature(self, uc: int, nand: int) -> None:
        flash_setting = get_flash_setting()
        ce_num = flash_setting.Max_Fdevice

        set_nand_temp = SetNandTemperature()
        set_nand_temp.bEnableSetVuTemp.value = 1
        set_nand_temp.NAND_TEMPERATURE_DIE_0.value = nand
        set_nand_temp.UC_TERMAL_SENSOR_1.value = uc
        if ce_num >= 2:
            set_nand_temp.NAND_TEMPERATURE_DIE_1.value = nand
        if ce_num >= 4:
            set_nand_temp.NAND_TEMPERATURE_DIE_2.value = nand
            set_nand_temp.NAND_TEMPERATURE_DIE_3.value = nand
        set_nand_temp.Use_Delayed_fake_tmeperatures.value = 0  
        project_api.issue_D08A_set_vu_temperature(set_nand_temp)
    
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        logger.flow(1, f'Send VU D088 to disable auto-standby')
        project_api.issue_D088_enable_disable_auto_standby(0)
        
        logger.flow(2, f'Send VU D08A to set Tasic=50, Tnand=30')
        self.set_temperature(uc=50, nand=30)

        logger.flow(3, f'Idle 10s to let FW update variable')
        time.sleep(10)
        
        logger.flow(4, f'Read fw value to check DeltaAsicNand correctness')
        t_asic = cast(int, read_fw_value('gUfsApiStruct.ftl->temp.ts_asic'))
        t_nand = cast(int, read_fw_value('gUfsApiStruct.ftl->temp.avg_ts_nand'))
        delta_asic_nand = cast(int, read_fw_value('gUfsApiStruct.ftl->temp.delta_asic_nand'))
        logger.info(f"Tasic={t_asic}, Tnand={t_nand}, Delta_T={delta_asic_nand}")
        if delta_asic_nand != (t_asic - t_nand):
            logger.info(f"Delta_T is not correct, Test Fail!")
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(5, f'Send VU D088 to enable auto-standby')
        project_api.issue_D088_enable_disable_auto_standby(1)

        logger.flow(6, f'Send VU D08A to set Tasic=40, Tnand=30')
        self.set_temperature(uc=40, nand=30)

        backup_ats_times = self.get_ast_times()  
        time.sleep(10)
        get_ats_times = self.get_ast_times()   
        if(get_ats_times < backup_ats_times):
            logger.info(f'ats_times should increase when do  enable ats test')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(7, f'Read fw value to check Tand correctness')
        t_asic = cast(int, read_fw_value('gUfsApiStruct.ftl->temp.ts_asic'))
        t_nand = cast(int, read_fw_value('gUfsApiStruct.ftl->temp.avg_ts_nand'))
        delta_asic_nand = cast(int, read_fw_value('gUfsApiStruct.ftl->temp.delta_asic_nand'))
        logger.info(f"After awake. Tasic={t_asic}, Tnand={t_nand}, Delta_T={delta_asic_nand}")
        if t_nand != (t_asic - delta_asic_nand):
            logger.info(f"Tnand is not correct, Test Fail!")
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL


    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()