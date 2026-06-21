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

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.TestNormalLun, self.TestEM1Lun, self.TestWBLun, self.flash_setting, self.fw_geometry = rain_pattern_precondition()
        self.max_ce, self.max_plane, self.max_pageline = get_geometry_parameter()
        self.write_record = api.get_empty_write_record()
        pass

    def step1(self) -> None:
        for testMode in [TestMode.TEST_TLC, TestMode.TEST_SLC, TestMode.TEST_WB]:
            SLC_en = testMode != TestMode.TEST_TLC
            lun, mode_str = get_general_parameter(testMode)            
            rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode)
            logger.info(f'============ Test {mode_str} VB ============')
            logger.flow(1, f'Write until {mode_str} VB has enough data')
            if testMode == TestMode.TEST_WB:
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)

            vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096) if testMode == TestMode.TEST_TLC else (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
            last_size = (self.max_plane -3) * api.BLOCK4K_SIZE_16K_BYTE
            total_size = vb_size - last_size
            chunksize = api.BLOCK4K_SIZE_128M_BYTE // (self.max_plane * api.BLOCK4K_SIZE_16K_BYTE) * (self.max_plane * api.BLOCK4K_SIZE_16K_BYTE)
            lba = 0
            api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunksize, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
            lba += total_size
            UECC_lba = lba-1 - 4096
            pca = get_PCA_and_print(lun=lun, lba=UECC_lba)
            old_cursor = get_specific_open_vb_cursor(testMode=testMode)
    
            logger.flow(2, f'inject UECC')
            inject_UECC(pca=pca, SLC_enable=SLC_en)
            
            for attempt, delay in enumerate([100,200,300,400,500,600,700,800,900, 1000]):
                logger.flow(3, f'Write data with SPOR to close VB (attempt {attempt+1}, delay={delay})')
                write10 = ExecuteCMD.Write10()
                write10.assign(lun=lun, lba=lba, length=last_size, fua=1)
                write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX)
                lba += last_size
                ExecuteCMD.enqueue(write10)
                self.push_spor(delay=delay)
                ExecuteCMD.send(clear_on_success=True)
                api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
                spor_cursor = get_specific_open_vb_cursor(testMode=testMode)

                logger.flow(4, f'check Open VB info after SPOR (attempt {attempt+1})')
                new_cursor = get_specific_open_vb_cursor(testMode=testMode)
                if old_cursor.logical_vb.value != new_cursor.logical_vb.value:
                    break  # VB closed successfully, continue to flow 4

                logger.warning(f'VB not closed after first SPOR, retrying with increased delay')
            polling_bkops_idle()
            
            logger.flow(5, f'Read compare data')
            read_compare_rain_result(write_record=self.write_record)

            pass

    def post_process(self) -> None:
        pass

    
    def push_spor(self, delay:int) -> None:
        power_cycle = ExecuteCMD.CmdSeqPowerCycle()
        power_cycle.set_option(mode=api.PowerCycleMode.ALL_POWER_DOWN, wait_queue_empty=True, delay_time=delay)
        ExecuteCMD.enqueue(power_cycle)
        for channel in range(1,3 +1):
            power_ctrl = ExecuteCMD.CmdSeqPowerControl()
            power_ctrl.set_option(
                mode=1,
                channel=channel,
                spendtime=500,
                ramptime=100,
                wait_queue_empty=True,
                delay_time=100
            )
            ExecuteCMD.enqueue(power_ctrl)

        power_cycle = ExecuteCMD.CmdSeqPowerCycle()
        power_cycle.set_option(mode=api.PowerCycleMode.LINK_START_UP, wait_queue_empty=True, delay_time=delay)
        ExecuteCMD.enqueue(power_cycle)
        nop = ExecuteCMD.CmdSeqPushNopOutPollNopIn()
        nop.set_option(timeout=5000, wait_queue_empty=True, delay_time=100)
        ExecuteCMD.enqueue(nop) 


run = Pattern().run
if __name__ == "__main__":
    run()