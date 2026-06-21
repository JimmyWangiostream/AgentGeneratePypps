import package_root
from Script import api
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.hir.mutual_fun import *
from Script.api.exception import *
from Script.api.ufs_api.defines.bit_define import *
from Script.pattern.pattern_logger import logger
import random
from enum import Enum, IntEnum
_sdk = api.shared.sdk
class TestCases(IntEnum):
    HOT_RESKY = 0
    COLD_RESKY = 1

class Pattern(UFSTC):
    def pre_process(self) -> None:
        flashsetting = api.get_flash_setting()
        self.fw_geometry = api.get_fw_geometry()
        self.CE = flashsetting.FLH_Quantity * (BIT0 << flashsetting.Parallel)
        pass

    def step1(self) -> None:
        logger.flow(1,f"Config normal lun and boot lun, Set bRefreshMethod = 1, read dRefreshTotalCount")
        config_lun()

        logger.flow("1-1", 'Get xtemp parameter from mconfig')
        XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2 = get_xtemp_parameter()
        idle_wait_detect_temp = 2 * XTEMP_TIME_DETECTION_VALUE

        logger.flow("1-2", f'Set EC as XTEMP_ENABLE_PEC * 100 = {XTEMP_ENABLE_PEC * 100}')
        set_ec_value = XTEMP_ENABLE_PEC * 100
        value_bytes = set_ec_value.to_bytes(4, byteorder='little', signed=False)
        data = bytearray(b'\xFF' * 0x4000)
        data[:(self.fw_geometry.l52_total_vb_count * 4)] = value_bytes * self.fw_geometry.l52_total_vb_count
        set_ec(self.fw_geometry.l52_total_vb_count, data)

        logger.flow("1-3", 'HW reset to enable XTEMP algorithm')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)

        api.write_attribute(idn=api.AttributeIDN.REFRESH_METHOD, val=1)  ##0:not_define #1:force #2:selective

        dev_desc = pattern_get_device_health_descriptor()
        refreshProgress_step1 = int.from_bytes(dev_desc[41:45])
        resfreshCount_step1 = int.from_bytes(dev_desc[37:41])
        logger.info(f'refreshprogress = {refreshProgress_step1}, refreshCount = {resfreshCount_step1}')

        logger.flow("1-4","set wExceptionEventControl bit11")
        api.write_attribute(idn=api.AttributeIDN.EXC_EVENT_CONTROL, val=BIT11)

        for refresh_unit in range(2):
            logger.flow(1,f"Set bRefreshUnit = {refresh_unit}")  #0:slice #1:fullcard
            api.write_attribute(idn=api.AttributeIDN.REFRESH_UNIT, val=refresh_unit)

            dev_desc = pattern_get_device_health_descriptor()
            refreshProgress_step1 = int.from_bytes(dev_desc[41:45])
            resfreshCount_step1 = int.from_bytes(dev_desc[37:41])
            logger.info(f'refreshprogress = {refreshProgress_step1}, refreshCount = {resfreshCount_step1}')

            for case in TestCases: 
                val = api.read_attribute(api.AttributeIDN.REFRESH_STATUS)
                logger.info(f'refresh status = {val}')
                logger.info(f"case = {case.name}")
                logger.flow(2,"write some data on LUN0")
                data_len = WRITE_10_MAX_BLOCK_LEN
                total_len = random.randint(BLOCK4K_SIZE_4K_BYTE, BLOCK4K_SIZE_512K_BYTE)
                write_data(lun=0,start_lba=0,len=data_len,total_len=total_len)  

                self.XTEMP_REFRESH_T1, self.XTEMP_REFRESH_T2, self.XTEMP_TIME_DETECTION_VALUE, self.XTEMP_ENABLE_PEC = get_T1_T2()
                if case == TestCases.COLD_RESKY:
                    logger.flow(3,"make Tnand < T1")
                    set_nand_temp(self.CE, set_temp=self.XTEMP_REFRESH_T1-1)
                    time.sleep(self.XTEMP_TIME_DETECTION_VALUE)
                else:
                    logger.flow(3,"make Tnand > T2")
                    set_nand_temp(self.CE, set_temp=self.XTEMP_REFRESH_T2+1)
                    time.sleep(self.XTEMP_TIME_DETECTION_VALUE)

                logger.flow(4,"read dRefreshProgress, Set RefreshEnable = 1 when cmd queue empty")
                dev_desc = pattern_get_device_health_descriptor()
                refreshProgress_step4 = int.from_bytes(dev_desc[41:45])
                resfreshCount_step4 = int.from_bytes(dev_desc[37:41])
                logger.info(f'refreshprogress = {refreshProgress_step4}, refreshCount = {resfreshCount_step4}')
  
                api.set_flag(api.FlagIDN.REFRESH_EN)

                logger.flow(5,"read bRefreshStatus should == 05h")
                val = api.read_attribute(api.AttributeIDN.REFRESH_STATUS)
                if val != 5:
                    logger.error_lb(f'Read refreshstatus in Tnand < T1')
                    logger.error_fp(f'Expect refresh status = 05h, but = {val}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                logger.flow(6,"read bRefreshStatus should == 00h")
                val = api.read_attribute(api.AttributeIDN.REFRESH_STATUS)
                if val != 0:
                    logger.error_lb(f'Read refreshstatus again')
                    logger.error_fp(f'Expect refresh status = 0, but = {val}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                logger.flow("6-1","Event Alert bit should raise")
                query_idx = ExecuteCMD.ReadFlag().assign(idn=api.FlagIDN.BG_OP_EN).enqueue()
                ExecuteCMD.send(clear_on_success=False)
                rsp = ExecuteCMD.read_response(query_idx)
                if rsp.upiu.b9_device_information != 1:
                    logger.error(f'send read cmd expect event alert = 1, but = {rsp.upiu.b9_device_information}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                ExecuteCMD.clear()
                
                logger.flow(7,"read wExceptionEventStatus BIT11 should raise, read wExceptionEventStatus again BIT11 should reset")
                val = api.read_attribute(api.AttributeIDN.EXC_EVENT_STATUS)
                if (val & BIT11) != BIT11:
                    logger.error_lb(f'Check wExceptionEventStatus BIT11 bcs error flag = 1')
                    logger.error_fp(f'Expect wExceptionEventStatus BIT11 raise, but not, wExceptionEventStatus = {val}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                val = api.read_attribute(api.AttributeIDN.EXC_EVENT_STATUS)
                if (val & BIT11) == BIT11:
                    logger.error_lb(f'Check wExceptionEventStatus BIT11 reset after read again')
                    logger.error_fp(f'Expect wExceptionEventStatus BIT11 reset, but not, wExceptionEventStatus = {val}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
                logger.flow(8,"read dRefreshProgress should not increase (step 4)")
                dev_desc = pattern_get_device_health_descriptor()
                refreshProgress_step8 = int.from_bytes(dev_desc[41:45])
                resfreshCount_step8 = int.from_bytes(dev_desc[37:41])
                logger.info(f'refreshprogress = {refreshProgress_step8}, refreshCount = {resfreshCount_step8}')
                if refreshProgress_step8 != refreshProgress_step4:
                    logger.error_lb(f'Check RefreshProgress not increase')
                    logger.error_fp(f'RefreshProgress(step4) = {refreshProgress_step4}, RefreshProgress(step8) = {refreshProgress_step8}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
        pass

    
    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()