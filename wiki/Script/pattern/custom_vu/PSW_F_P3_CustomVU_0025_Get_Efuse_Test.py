import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from typing import cast
from Script.api import shared
from Script.api.ufs_api import *
from Script.api.cmd_seq import QueryResponse
from Script.api.ufs_api.vendor_cmd.structs import FwGeometry
from typing import Callable
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_data_in_vcmd


class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass
    def step1(self) -> None:
  
        logger.flow(1, 'Send VU 40F4 to get Efuse')
        vu_data = project_api.issue_40F4_to_get_eFus()

        logger.flow(2, 'Send VUC = READ_Xmemory(0xAC) to get efuse')
        _, efuse_data_from_xmemory = api.read_Xmemory(sram_address=0xF8F80800)

        logger.flow(3, 'Compare efuse from VU40F4 and efuse from sram')
        for i in range(len(vu_data.efuse)): 
            value_from_sram = int.from_bytes(efuse_data_from_xmemory[i*4:i*4+4],byteorder='little')

            value_from_sram_str = format(value_from_sram, '08X')
            value_from_vu_str = format(vu_data.efuse[i].value, '08X')
            
            if vu_data.efuse[i].value != value_from_sram:
                logger.error(f'Expect VU offset[{i*4}:{i*4+3}](EFUSE{i}) = {value_from_sram_str}, but = {value_from_vu_str}')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            else:
                logger.info(f'VU offset[{i*4}:{i*4+3}](EFUSE{i}) = {value_from_sram_str}')
        pass

    def post_process(self) -> None:
        pass
    

run = Pattern().run
if __name__ == "__main__":
    run()