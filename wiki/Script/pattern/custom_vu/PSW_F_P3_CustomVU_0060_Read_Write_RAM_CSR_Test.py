import package_root
import time
import struct
from typing import cast
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.api.util import dumpfile
from Script.api.ufs_api.descriptors.configuration_desc.functions import print_config, push_write_config
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.lib.sdk_lib.user import _power as pw
#from scriptlib.fw.common import manufacture as mfg

timeout_min = 15

def check_timeout(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        write_ram_segments = [
            (0x7FDA8000, 0x7FDA8003),  #reserved block for test
            #(0x7FDA4000, 0x7FDA1FFF),  # MRAM parpartially accessible
            #(0x7FEA4000, 0x7FFFFFFF),  # MRAM parpartially accessible
        ]

        read_ram_segments:list[tuple[int,int]] = [
            (0x00000000, 0x00033FFF),  # ICCM + ROM
            (0x4C100000, 0x4C1FFFFF),  # COP0
            (0x4C200000, 0x4C2FFFFF),  # COP0
            (0x7FDA4000, 0x7FFFFFFF),  # MRAM
            (0x80000000, 0x8001B5DF),  # DCCM parpartially accessible
            (0x8001CE00, 0x80027FFF),  # DCCM parpartially accessible
        ]

        count_of_byte = 4

        logger.flow(1, 'Modify HW setting to disable suspend')
        hw_setting = api.HwSetting.get_instance()
        hw_setting.set_to_device(field = api.HwSettingField.POWER_SAVING_CTRL_ENABLE, val= 0x3A)

        for addr_seg in write_ram_segments:
            start_addr = addr_seg[0]

        logger.flow(2, f'Issue VU 0xC0F0 write SRAM address 0x{start_addr:08X} with data 0x5A5A5A5A')
        write_data = bytearray(b'\x5A' * 0x4)
        resp = project_api.issue_C0F0_write_RAM_CSR(write_data=write_data, start_address=start_addr)
        
        logger.flow(3, f'Issue VU 0x4027 read SRAM address 0x{start_addr:08X} and check data should be 0x5A5A5A5A')
        resp = project_api.issue_4027_read_SRAM_CSR_data(start_address=start_addr)
        dumpfile(f'test_addr_is_0x{start_addr:08X}_after_write', resp.data)
        hextest:list[str] = []
        for i in range(count_of_byte):
            hextest.append(f'0x{resp.data[i]:02X}')
        logger.info(f'{hextest}')
        hextest.clear()

        if resp.data[0:count_of_byte] != write_data:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(4, f'Issue VU 0x4027 read valid SRAM address and print data')
        cmd_idx_list:list[int] = []
        for addr_seg in read_ram_segments:
            start_addr = addr_seg[0]
            end_addr = addr_seg[1] - 3 #align 4byte
            mid_addr = ((((start_addr + end_addr) // 2) // 4) * 4) #align 4byte
            test_addr:list[int] = [start_addr, mid_addr, end_addr]
            logger.info(f'test address = 0x{start_addr:08X}, 0x{mid_addr:08X}, 0x{end_addr:08X}')

            for i in range(len(test_addr)):
                resp = project_api.issue_4027_read_SRAM_CSR_data(start_address=test_addr[i])
                for j in range(count_of_byte):
                    hextest.append(f'0x{resp.data[j]:02X}')
                logger.info(f'address = 0x{test_addr[i]:08X}, data = {hextest}')
                hextest.clear()

            ExecuteCMD.clear()

        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()