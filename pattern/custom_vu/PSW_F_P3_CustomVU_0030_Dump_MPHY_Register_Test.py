import package_root
import time
import struct
from typing import List, cast
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
from Script.project_api.custom_vu.dump_the_MPHY_register.structs import CompareItem
#from scriptlib.fw.common import manufacture as mfg

def get_MPHY_register_from_customVU() -> bytearray:
    VU4083_resp = project_api.issue_4083_dump_the_MPHY_register()
    dumpfile(filename = 'MPHY_register_from_customVU', data=VU4083_resp.data)
    return VU4083_resp.data[0:2048]

def get_MPHY_register_from_SRAM() -> bytearray:
    _, MPHY_register = api.ufs_api.vendor_cmd.read_Xmemory(sram_address = 0xF8F86000)
    dumpfile(filename = 'MPHY_register_from_SRAM',data=MPHY_register)
    return MPHY_register[0:2048]

def compare_payload(payload: bytearray, checks: List[CompareItem]) -> tuple[bool, List[int]]:
    check_result:bool = True
    error_offset:List[int] = []
    for item in checks:
        if item.offset < 0 or item.offset >= len(payload):
            logger.warning(f'offset {item.offset:#04x} out of range (payload len={len(payload)})')
            continue

        actual = payload[item.offset]
        if actual != item.expected:
            logger.error(f'offset {item.offset:#04x}: expected {item.expected:#04x}, got {actual:#04x}')
            error_offset.append(item.offset)
            check_result = False

    return check_result, error_offset

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        logger.flow(1, 'Host Issue VU 0x4083 to dump the MPHY register when device init done')
        MPHY_register_from_customVU = get_MPHY_register_from_customVU()

        logger.flow(2, 'Host Read SRAM address = 0xF8F86000 and compare with VU output data, it should be same values')
        MPHY_register_from_SRAM = get_MPHY_register_from_SRAM()

        MPHY_register_from_customVU[0x750:0x755] = [0] * 5
        MPHY_register_from_SRAM[0x750:0x755] = [0] * 5
        dumpfile(filename = 'MPHY_register_from_customVU(skip_750t754)', data=MPHY_register_from_customVU)
        dumpfile(filename = 'MPHY_register_from_SRAM(skip_750t754)', data=MPHY_register_from_SRAM)

        logger.flow(3, 'Compare VU data with read SRAM data should be same')
        if MPHY_register_from_customVU != MPHY_register_from_SRAM:
            logger.error('VU data mismatch with read SRAM data')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.info(f'Verify VU data match with read SRAM data, test pass')

        logger.flow(4, 'Compare VU data with document')
        check_result, error_offset = compare_payload(payload=MPHY_register_from_customVU,checks=project_api.MPHY_REG_CHECKS)
        if check_result == False:
            logger.error_lb(f'Compare MPHY_register_from_customVU 0x4083 with document')
            logger.error_fp(f'Data mismatch with offset: {error_offset}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()