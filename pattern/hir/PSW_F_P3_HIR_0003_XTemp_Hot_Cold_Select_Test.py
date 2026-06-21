import package_root
from Script import api
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.pattern.hir.mutual_fun import *
from Script.api.exception import *
import random
from Script.api.ufs_api.defines.bit_define import *
from enum import Enum, IntEnum
_sdk = api.shared.sdk
class TestCases(IntEnum):
    COLD_RESKY = 0
    HOT_RESKY = 1
class Pattern(UFSTC):
    def pre_process(self) -> None:
        flashsetting = api.get_flash_setting()
        self.CE = flashsetting.FLH_Quantity * (BIT0 << flashsetting.Parallel)
        self.fw_geometry = api.get_fw_geometry()
        logger.info(f'total vb count = {self.fw_geometry.l52_total_vb_count}')
        pass

    def step1(self) -> None:
        logger.flow(1,f"Config normal lun and boot lun, Set bRefreshUnit = 0, bRefreshMethod = 2, read dRefreshTotalCount")
        config_lun()
        api.write_attribute(idn=api.AttributeIDN.REFRESH_UNIT, val=0)

        api.write_attribute(idn=api.AttributeIDN.REFRESH_METHOD, val=2)

        for case in TestCases: 
            logger.info(f"case = {case.name}")

            dev_desc = pattern_get_device_health_descriptor()
            refreshProgress_step1 = int.from_bytes(dev_desc[41:45])
            resfreshCount_step1 = int.from_bytes(dev_desc[37:41])
            logger.info(f'refreshTotalCount = {resfreshCount_step1}')

            logger.flow(2,f"write some data on all enable lun")
            data_len = WRITE_10_MAX_BLOCK_LEN
            _param = api.shared.param
            for lun in range(4):
                total_len = min(_param.gLUCapacity[lun], data_len)
                write_data(lun=lun,start_lba=0,len=data_len,total_len=total_len)  #need not overlay lba?
    
            self.XTEMP_REFRESH_T1, self.XTEMP_REFRESH_T2, self.XTEMP_TIME_DETECTION_VALUE, self.XTEMP_ENABLE_PEC = get_T1_T2()
            if case == TestCases.COLD_RESKY:
                logger.flow(3,"make Tnand < T1")
                set_nand_temp(self.CE, set_temp=self.XTEMP_REFRESH_T1-1)
                time.sleep(self.XTEMP_TIME_DETECTION_VALUE)
            else:
                logger.flow(3,"make Tnand > T2")
                self.XTEMP_REFRESH_T1, self.XTEMP_REFRESH_T2, self.XTEMP_TIME_DETECTION_VALUE, self.XTEMP_ENABLE_PEC = get_T1_T2()
                set_nand_temp(self.CE, set_temp=self.XTEMP_REFRESH_T2+1)
                time.sleep(self.XTEMP_TIME_DETECTION_VALUE)

            start_time_outer = time.time()
            scan_vb_count = 0

            while True:
                check_timeout(start_time=start_time_outer,timeout_min=30)

                logger.flow(4,f"read dRefreshProgress, Set RefreshEnable = 1 when cmd queue empty")
                dev_desc = pattern_get_device_health_descriptor()
                refreshProgress_step4 = int.from_bytes(dev_desc[41:45])
                resfreshCount_step4 = int.from_bytes(dev_desc[37:41])
                logger.info(f'refreshProgress = {refreshProgress_step4}')

                api.set_flag(api.FlagIDN.REFRESH_EN)

                
                logger.flow(5,"read bRefreshStatus more times until 03h, (in polling time , only 01h should happen)")
                start_time_inner = time.time()
                while True:
                    check_timeout(start_time=start_time_inner,timeout_min=15)
                    val = api.read_attribute(api.AttributeIDN.REFRESH_STATUS)
                    if val == 3:
                        break
                    elif val == 1:
                        continue
                    else:
                        logger.error_lb(f'check bRefreshStatus until 03h')
                        logger.error_fp(f'Expect refresh status = 03h, but = {val}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    
                logger.flow(6,f"read bRefreshStatus should == 00h")
                val = api.read_attribute(api.AttributeIDN.REFRESH_STATUS)
                if val != 0:
                    logger.error_lb(f'Read refreshstatus again')
                    logger.error_fp(f'Expect refresh status = 0, but = {val}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                

                logger.flow(7,f"read dRefreshProgress should increase 1 / total vb count")
                dev_desc = pattern_get_device_health_descriptor()
                refreshProgress_step7 = int.from_bytes(dev_desc[41:45])
                resfreshCount_step7 = int.from_bytes(dev_desc[37:41])
                logger.info(f'refreshprogress = {refreshProgress_step7}, refreshCount = {resfreshCount_step7}')
                
                if refreshProgress_step7 != 0:
                    scan_vb_count += 1

                    last_refreshProgress = ((scan_vb_count - 1) * 100* 1000)  // self.fw_geometry.l52_total_vb_count
                    current_refreshProgress = (scan_vb_count * 100* 1000)  // self.fw_geometry.l52_total_vb_count
                    logger.info(f'last refresh progress = {last_refreshProgress}')
                    logger.info(f'current refresh progress = {current_refreshProgress}')

                    increase_val = current_refreshProgress - last_refreshProgress
                    if (refreshProgress_step7 - refreshProgress_step4) != increase_val:
                        logger.error_lb(f'Refresh unit = 0, expect refreshProgress increase (1 / total_vb_cnt) * 100')
                        logger.error_fp(f'Expect refreshProgress increase val = {increase_val}, but = {refreshProgress_step7 - refreshProgress_step4}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    
                    
                logger.flow(8,f"goto step4~step7 until step7 dRefreshProgress reach 1000000(100%) or 0")
                if refreshProgress_step7 == 100000 or refreshProgress_step7 == 0:
                    if resfreshCount_step7 != (resfreshCount_step4 + 1):
                        logger.error_lb(f'When dRefreshProgress reach 1000000(100%) or 0, check refreshTotalCount increase')
                        logger.error_fp(f'Expect refreshTotalCount_after = refreshTotalCount_before + 1, but refreshTotalCount_after = {resfreshCount_step7}, refreshTotalCount_before = {resfreshCount_step4}')
                        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                    else:
                        break
                if refreshProgress_step7 > 100000:
                    logger.error_lb(f'Check refreshProgress')
                    logger.error_fp(f'RefreshProgress should not > 100000, but = {refreshProgress_step7}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        pass
    
    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()