import random
from typing import List, cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.api import shared

from Script.api.exception import *

class Pattern(UFSTC):
    def pre_process(self) -> None:
        logger.info(api.CommonPath.root)
        logger.info(api.CommonPath.development_report)
        logger.info(api.CommonPath.ini)
        logger.info(api.CommonPath.mp_tool)
        logger.info(api.CommonPath.tcsp)
        logger.info(api.CommonPath.report)
        pass

    def step1(self) -> None:
        
        write_record = api.get_empty_write_record()

        # api.write_all_lun(write_record)

        _param = shared.param

        for i in range(1):
            cmd_count = random.randint(10, 32)
            min_lun = 0
            max_lun = 2
            min_lba = 0
            max_lba = _param.gLUCapacity[0]
            min_size = api.BLOCK4K_SIZE_128K_BYTE
            max_size = api.BLOCK4K_SIZE_1M_BYTE
        
            api.random_write(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        need_compare=True, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)
            
            api.random_erase(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        write_record=write_record)
            
            api.random_read(cmd_count=cmd_count, min_lun=min_lun, max_lun=max_lun, min_lba=min_lba, max_lba=max_lba, min_size=min_size, max_size=max_size,
                        need_compare=True, write_record=write_record)

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()