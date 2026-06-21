import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.default_value = {
            0x4A2: 0x3,
            0x4A3: 0x1,
            0x4A4: 0x4,
            0x4A5: 0x1,
            0x6FF: 0x0,
        }
        self.set_dict = {
            0x4A3: 10,
            0x4A4: 20,
            0x4A5: 30,
        }
        pass

    def step1(self) -> None:
        logger.flow(1, 'issue 4084 to get Nand trim and backup value')
        self.backup = {}
        for addr in list(self.default_value.keys()):
            _, self.get_trim = project_api.issue_4084_to_get_NAND_trim(target_addr=[addr])
            if self.get_trim.TrimValue[0].value != self.default_value[addr]:
                logger.error_lb(f'check addr = {addr}')
                logger.error_fp(f'addr:{addr}, read value = {self.get_trim.TrimValue[0].value}, but expect default value = {self.default_value[addr]}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            if addr in self.set_dict:
                self.backup[addr] = self.get_trim.TrimValue[0].value
        pass
        
    def step2(self) -> None:
        logger.flow(2, 'issue C084 to set Nand trim')
        project_api.issue_C084_to_set_NAND_trim(set_dict=self.set_dict)
        _, self.get_trim = project_api.issue_4084_to_get_NAND_trim(target_addr=list(self.set_dict.keys()))
        pass
        
    def step3(self) -> None:
        logger.flow(3, 'issue C084 to set Nand trim')
        logger.info(f"GetTrimItemCnt: {self.get_trim.GetTrimItemCnt.value}")
        for addr, item in zip(list(self.set_dict.keys()), self.get_trim.TrimValue):
            logger.info(f"addr: {addr} , value: {item.value}")
            if self.set_dict[addr] != item.value:
                logger.error_lb(f'check addr = {addr}')
                logger.error_fp(f'addr:{addr}, set value = {self.set_dict[addr]}, but get value = {item.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            pass

    def step4(self) -> None:
        logger.flow(4, 'issue C084 to recover the trim value')
        project_api.issue_C084_to_set_NAND_trim(set_dict=self.backup)
        pass

    def post_process(self) -> None:
        pass

run = Pattern().run
if __name__ == "__main__":
    run()