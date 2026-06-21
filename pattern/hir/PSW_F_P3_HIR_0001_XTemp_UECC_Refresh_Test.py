import package_root
from Script import api
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.defines.bit_define import *
from Script.api.exception import *
from Script.pattern.hir.mutual_fun import *

from math import ceil
import time
import random
_sdk = api.shared.sdk
BOOKING_IN_MP = BIT9


class Pattern(UFSTC):
    def pre_process(self) -> None:
        flashsetting = api.get_flash_setting()
        self.fw_geometry = api.get_fw_geometry()
        self.CE = flashsetting.FLH_Quantity * (BIT0 << flashsetting.Parallel)
        
        self.TLC_VB_4K_SIZE = (self.fw_geometry.l88_vb_size_u1 * 512) // api.DATA_SIZE_4K_BYTE
        self.write_record = api.get_empty_write_record()
        
        pass

    def step1(self) -> None:

        logger.flow(1,"Config normal lun and boot lun, Set bRefreshUnit = 0, bRefreshMethod = 1, read dRefreshTotalCount")
        config_lun()
        api.write_attribute(idn=api.AttributeIDN.REFRESH_UNIT, val=0)
        api.write_attribute(idn=api.AttributeIDN.REFRESH_METHOD, val=1)
        dev_desc = pattern_get_device_health_descriptor()
        refreshProgress_step1 = int.from_bytes(dev_desc[41:45])
        resfreshCount_step1 = int.from_bytes(dev_desc[37:41])
        logger.info(f'refreshprogress = {refreshProgress_step1}, refreshCount = {resfreshCount_step1}')

        logger.flow("2-1", 'Get xtemp parameter from mconfig')
        XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2 = get_xtemp_parameter()
        idle_wait_detect_temp = XTEMP_TIME_DETECTION_VALUE

        logger.flow("2-2", f'Set EC as XTEMP_ENABLE_PEC * 100 = {XTEMP_ENABLE_PEC * 100}')
        set_ec_value = XTEMP_ENABLE_PEC * 100
        value_bytes = set_ec_value.to_bytes(4, byteorder='little', signed=False)
        data = bytearray(b'\xFF' * 0x4000)
        data[:(self.fw_geometry.l52_total_vb_count * 4)] = value_bytes * self.fw_geometry.l52_total_vb_count
        set_ec(self.fw_geometry.l52_total_vb_count, data)

        logger.flow("2-3", 'Issue HW reset to enable xtemp algo')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType.HW_RESET, powerdown = True)

        logger.flow("2-4","make Tnand >= T1 and Tnand <= T2( if Tnand already in this range , skip)")
        
        if not Tnand_in_T1_T2_range(self.CE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2):
            set_temp = (XTEMP_REFRESH_T2 - XTEMP_REFRESH_T1) // 2
            set_nand_temp(self.CE, set_temp=set_temp)
            time.sleep(idle_wait_detect_temp)

        logger.flow("2-5","write some data on LUN0")
        data_len = WRITE_10_MAX_BLOCK_LEN
        total_len = random.randint(BLOCK4K_SIZE_4K_BYTE, BLOCK4K_SIZE_512K_BYTE)
        write_data(lun=0,start_lba=0,len=data_len,total_len=total_len)

        logger.flow(3,"issue C088 to stop refresh execution, but refresh can still be enqueued")
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        
        logger.flow(4,"inject XTEMP UECC refresh on current L2")

        logger.flow("4-1","make Tnand < T1 or > T2")
        set_nand_temp(self.CE, set_temp=XTEMP_REFRESH_T2 + 1)
        time.sleep(idle_wait_detect_temp)

        logger.flow("4-2","write some data on LUN0")
        api.sequential_write(lun=0, start_lba=0, total_size=self.TLC_VB_4K_SIZE, chunk_size=api.BLOCK4K_SIZE_64M_BYTE, fua = 0,
                                    need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)

        logger.flow("4-3","make Tnand >= T1 and Tnand <= T2( if Tnand already in this range , skip)")
        set_nand_temp(self.CE, set_temp=XTEMP_REFRESH_T1 - 1)
        time.sleep(idle_wait_detect_temp)

        logger.flow("4-4","Inject UECC on written data")
        pca = get_PCA_and_print(lun=0,lba=0)

        self.vb_number = (pca.b11_block_h << 8) + pca.b10_block_l
        inject_UECC(pca)

        logger.flow(5,"issue 40C5 to check if the Booking Queue is correct")
        find = False
        _, self.booking_q = project_api.issue_40C5_to_get_booking_queue()
        logger.info(self.booking_q.LogicalVBNumberInBookingQueue.value)

        for idx, bq in enumerate(self.booking_q.BookingQueueVB):
            if bq.LogicalVBNumber.value == self.vb_number:
                print(f'booking user = {bq.TheBookingUser.value}, correctbits = {bq.CorrectedBits.value}')
                find = True
                if bq.TheBookingUser.value != (project_api.BookingUser.XTEMP_BOOKING | BOOKING_IN_MP):
                    logger.error_lb(f'After cross temp check vb = {self.vb_number} booking user = 20')
                    logger.error_fp(f'Expect booking user = 20(XTEMP_BOOKING), but = {bq.TheBookingUser.value}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if find == False:
            logger.error_lb(f'After cross temp check vb = {self.vb_number} in BookingQueue')
            logger.error_fp(f'BookingQueue can not find {self.vb_number}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    
        logger.flow(6,"issue C088 to start refresh execution")
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)

        logger.flow(7,"read dRefreshProgress, Set RefreshEnable = 1 when cmd queue empty")
        dev_desc = api.get_device_health_descriptor()
        refreshProgress= dev_desc.l41_refresh_progress
        logger.info(f'refreshProgress = {refreshProgress}')

        logger.flow(8,"read bRefreshStatus more times until 05h, (in polling time , only 01h should happen)")
        api.set_flag(api.FlagIDN.REFRESH_EN)
        start_time = time.time()
        while True:
            check_timeout(start_time=start_time,timeout_min=15)
            val = api.read_attribute(api.AttributeIDN.REFRESH_STATUS)
            if val == 5:
                break
            elif val == 1:
                continue
            else:
                logger.error_lb(f'check bRefreshStatus until 05h')
                logger.error_fp(f'Expect refresh status = 01h or 05h, but = {val}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(9,"read bRefreshStatus should == 00h")
        val = api.read_attribute(api.AttributeIDN.REFRESH_STATUS)
        if val != 0:
            logger.error_lb(f'Read refreshstatus again')
            logger.error_fp(f'Expect refresh status = 0, but = {val}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        

        logger.flow(10,"read wExceptionEventStatus BIT11 should raise, read wExceptionEventStatus again BIT11 should reset")
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
        
        pass
    
    def step8(self) -> None:
        
        pass
    def step9(self) -> None:
        
        pass
    def step10(self) -> None:
        
        pass
    
    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()