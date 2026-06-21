import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api import shared
import random

from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api import UPIUResponse
from typing import List


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = shared.param
        pass

    def step1(self) -> None:
        
        logger.flow(1, 'Disable ats')
        hw_setting = api.HwSetting.get_instance()
        default_value = hw_setting.get_local_val(api.HwSettingField.POWER_SAVING_CTRL_ENABLE)
        hw_setting.set_to_device(api.HwSettingField.POWER_SAVING_CTRL_ENABLE, 0x3A)

        logger.flow(1, 'Write 1G data')
        total_len = BLOCK4K_SIZE_1G_BYTE 
        self.write_data(lun=0,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
        logger.flow(2, 'Random read 1G data')
        _ = self.random_read_data(lun=0,min_lba=0,max_lba=total_len//2, datalen=BLOCK4K_SIZE_4K_BYTE, total_len=total_len)
        total_read_time_with_pte_pmd = self.random_read_data(lun=0,min_lba=0,max_lba=total_len//2, datalen=BLOCK4K_SIZE_4K_BYTE, total_len=total_len)

        logger.flow(3, 'Send VU D08C to invalid PTE')
        project_api.issue_D08C_to_invalid_table_cache(rainEnable=1)

        logger.flow(4, 'Random read 1G data')
        total_read_time_without_pte = self.random_read_data(lun=0,min_lba=0,max_lba=total_len//2, datalen=BLOCK4K_SIZE_4K_BYTE, total_len=total_len)
        logger.flow(5, 'Expect read time(with PTE/PMD) < read time(without PTE)')
        if total_read_time_without_pte < total_read_time_with_pte_pmd:
            logger.error(f'Expect read time(with PTE/PMD) < read time(without PTE), but read time(with PTE/PMD) = {total_read_time_with_pte_pmd}(us), read time(without PTE) = {total_read_time_without_pte}(us)')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(6, 'Send VU D08C to invalid PMD')
        project_api.issue_D08C_to_invalid_table_cache(rainEnable=2)

        logger.flow(7, 'Random read 1G data')
        total_read_time_without_pmd = self.random_read_data(lun=0,min_lba=0,max_lba=total_len//2, datalen=BLOCK4K_SIZE_4K_BYTE, total_len=total_len)
        
        logger.flow(8, 'Expect read time(with PTE/PMD) < read time(without PMD)')
        if total_read_time_without_pmd < total_read_time_with_pte_pmd:
            logger.error(f'Expect read time(with PTE/PMD) < read time(without PMD), but read time(with PTE/PMD) ={total_read_time_with_pte_pmd}(us), read time(without PMD) = {total_read_time_without_pmd}(us)')
            #raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(9, 'Send VU D08C to invalid PTE/PMD')
        project_api.issue_D08C_to_invalid_table_cache(rainEnable=3)

        logger.flow(10, 'Random read 1G data')
        total_read_time_without_pte_pmd = self.random_read_data(lun=0,min_lba=0,max_lba=total_len//2, datalen=BLOCK4K_SIZE_4K_BYTE, total_len=total_len)
        logger.flow(11, 'Expect read time(with PTE/PMD) < read time(without PMD)')
        if total_read_time_without_pte_pmd < total_read_time_with_pte_pmd:
            logger.error(f'Expect read time(with PTE/PMD) < read time(without PMD), but read time(with PTE/PMD) ={total_read_time_with_pte_pmd}(us), read time(without PMD) = {total_read_time_without_pte_pmd}(us)')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        hw_setting.set_to_device(api.HwSettingField.POWER_SAVING_CTRL_ENABLE, default_value)
        pass

    def post_process(self) -> None:
        pass
    
    def random_read_data(self,lun:int, min_lba:int, max_lba:int, datalen:int, total_len:int) -> float:
        cmd_queue : List[int] = []
        total_read_time = 0
        avg_read_time = 0.0
        while total_len > 0:
            read10 = ExecuteCMD.Read10()
            start_lba = random.randint(min_lba, max_lba)
            #logger.info(f'start lba = {start_lba}, len = {datalen}')
            read10.assign(lun=lun, lba=start_lba, length=datalen, fua=0)
            cmd_queue.append(ExecuteCMD.enqueue(read10))
            start_lba += datalen
            total_len -= datalen

        ExecuteCMD.send(timeout=api.UniformTimeout(val=30000, unit=api.TimeResolution.ms), clear_on_success=False)
        for cmd_index in cmd_queue:
            response = ExecuteCMD.read_response(cmd_index)
            total_read_time += (response.l59_resp_timestamp - response.l54_cmd_timestamp)
            if(response.l59_resp_timestamp < response.l54_cmd_timestamp):
                logger.error(f' resp time = {response.l59_resp_timestamp} > send time = { response.l54_cmd_timestamp}')
            if response.upiu.b6_response != UPIUResponse.TARGET_SUCCESS:
                break
        ExecuteCMD.clear()

        avg_read_time = total_read_time/len(cmd_queue)
        logger.info(f'Avg read time = {avg_read_time}(us)')
        return avg_read_time
    def write_data(self,lun:int, start_lba:int, len:int, total_len:int) -> None:
        while total_len > 0:
            len = min(total_len, len)
            write10 = ExecuteCMD.Write10()
            logger.info(f'start lba = {start_lba}, len = {len}')
            write10.assign(lun=lun, lba=start_lba, length=len, fua=1)
            ExecuteCMD.enqueue(write10)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(timeout=api.UniformTimeout(val=30000, unit=api.TimeResolution.ms), clear_on_success=False)
        ExecuteCMD.clear()
run = Pattern().run
if __name__ == "__main__":
    run()