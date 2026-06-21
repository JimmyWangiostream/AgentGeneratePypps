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
        self._param = shared.param
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        pass

    def step1(self) -> None:
        for testMode in [TestMode.TEST_TLC, TestMode.TEST_SLC, TestMode.TEST_WB]:
            SLC_enable = testMode!=TestMode.TEST_TLC
            reconfig_to_erase_all_lun(write_record=self.write_record)
            response, self.health_report_before = project_api.issue_40FE_to_read_enhanced_health_report()

            self.write_record = api.get_empty_write_record()
            lun, mode_str = get_general_parameter(testMode) 
            rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode)
            logger.flow(1, f'Write {mode_str} data to create a full written VB (rand insert write SPOR)')
            if testMode == TestMode.TEST_WB:
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            after_spor_lba = self.write_1_VB_with_SPOR(lun=lun, mode=testMode)
            pca = get_PCA_and_print(lun=lun, lba=after_spor_lba)
            
            logger.flow(2, 'check APL flag after SPOR')
            APL_flag = project_api.get_APL_flag_of_VB(log_VB=pca.virtual_block_number.value)
            if APL_flag != 1:
                logger.error_lb(f'check APL_flag after SPOR occur')
                logger.error_fp(f'expect APL_flag of vb {pca.virtual_block_number.value} is 1, but current value = {APL_flag}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(3, 'Inject UECC in each VB type')
            inject_UECC(pca=pca, SLC_enable=SLC_enable)

            logger.flow(4, 'SPOR after UECC injection')
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
            logger.flow(5, 'Compare data')
            read_compare_rain_result(write_record=self.write_record)

            logger.flow(8, f"check RAIN counter in health report")
            d1_closed_raind_recovery_ok_count = True if SLC_enable else False
            d3_closed_raind_recovery_ok_count = True if not SLC_enable else False
            check_RAIN_cnt_in_heatlth_report(self.health_report_before,
                                                d1_closed_raind_recovery_ok_count = d1_closed_raind_recovery_ok_count,
                                                d3_closed_raind_recovery_ok_count = d3_closed_raind_recovery_ok_count
                                            )
        
            logger.flow(6, 'reconfig to clear data')
            reconfig_to_erase_all_lun(write_record=self.write_record)
            self.write_record = api.get_empty_write_record()
            if testMode == TestMode.TEST_WB:
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            logger.flow(7, 'Write half VB')
            vb_size = self.tlc_vb_size if testMode == TestMode.TEST_TLC else self.slc_vb_size
            lba = 0
            api.sequential_write(lun=lun, start_lba=lba, total_size=vb_size//2, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            logger.flow(8, 'Inject UECC in rand area')
            rand_lba = random.randint(0, vb_size//2)
            pca = get_PCA_and_print(lun=lun, lba=rand_lba)
            inject_UECC(pca=pca, SLC_enable=SLC_enable)
            logger.flow(9, 'Write data to close VB')
            lba += vb_size//2
            api.sequential_write(lun=lun, start_lba=lba, total_size=vb_size//2, chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
            logger.flow(10, 'Compare data')
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

    
    def write_1_VB_with_SPOR(self, lun:int, mode:TestMode) -> int:
        lba = 0
        vb_size = self.tlc_vb_size if mode == TestMode.TEST_TLC else self.slc_vb_size
        chunk_size = api.BLOCK4K_SIZE_128M_BYTE
        datalen = vb_size//2
        api.sequential_write(lun=lun, start_lba=lba, total_size=datalen, chunk_size=chunk_size, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        lba += datalen
        apl_created = False
        delay = 100000
        logger.info("============= create APL ================")
        while not apl_created:
            temp_write_record = api.get_empty_write_record()
            write10 = ExecuteCMD.Write10()
            chunk_size = api.BLOCK4K_SIZE_64K_BYTE
            write10.assign(lun=lun, lba=lba, length=chunk_size, fua=0)
            write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX)
            ExecuteCMD.enqueue(write10)
            self.push_spor(delay=delay)
            ExecuteCMD.send(clear_on_success=False)
            for cmd in ExecuteCMD._cmd_list:
                api.save_write_info_by_cmd(cmd, temp_write_record)
            ExecuteCMD.clear()
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
            try:
                api.read_compare(temp_write_record, api.CompareMethod.SW_COMPARE)
                delay -= 50000
                if delay<0:
                    raise SIGHTING_RESPONSE_UNEXPECTED
            except DLL_CRC32_COMPARE_FAIL:
                ExecuteCMD.clear()
                apl_created = True
            lba+=chunk_size
        if mode == TestMode.TEST_WB:
            api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        else:
            api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        chunk_size = api.BLOCK4K_SIZE_128M_BYTE
        api.sequential_write(lun=lun, start_lba=lba, total_size=vb_size, chunk_size=chunk_size, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
        return lba

run = Pattern().run
if __name__ == "__main__":
    run()