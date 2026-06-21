import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.api import dumpfile
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api import shared
from Script.api.exception import *
from Script.api.ufs_api.defines.bit_define import *
from typing import List,cast

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = shared.param
        flashsetting = api.get_flash_setting()
        self.write_record = api.get_empty_write_record()
        self.CE = flashsetting.FLH_Quantity * (BIT0 << flashsetting.Parallel)
        self.PLANE_PER_DIE = flashsetting.Plane_Per_Die
        pass

    def step1(self) -> None:
        feature_address = 0xEB
        if self.CE != 4:
            for ce in range(self.CE):
                logger.flow(1, f'Send VU 4022 to get Nand feature with feature address = 0xEB, ce = {ce}')
                response, data_payload = project_api.issue_4022_to_get_NAND_feature(ce,feature_address)
                data = project_api.get_nand_feature_format(data_payload)
                logger.flow(1, f'Check default value as expect')
                self.compare_value(data.P1.value, 0, "P1")
                self.compare_value(data.P1.value, 0, "P2")
                self.compare_value(data.P1.value, 0, "P3")
                self.compare_value(data.P1.value, 0, "P4")
        else:
            for ce in range(self.CE):
                response, data_payload = project_api.issue_4022_to_get_NAND_feature(ce,feature_address)
                data = project_api.get_nand_feature_format(data_payload)
                logger.flow(1, f'Check default value as expect')
                if ce == 0:
                    self.compare_value(data.P1.value, 0x81, "P1")
                    self.compare_value(data.P2.value, 0x14, "P2")
                    self.compare_value(data.P3.value, 0x6E, "P3")
                    self.compare_value(data.P4.value, 0x0, "P4")
                elif ce == 1:
                    self.compare_value(data.P1.value, 0x89, "P1")
                    self.compare_value(data.P2.value, 0x14, "P2")
                    self.compare_value(data.P3.value, 0x2E, "P3")
                    self.compare_value(data.P4.value, 0x0, "P4")
                elif ce == 2:
                    self.compare_value(data.P1.value, 0x91, "P1")
                    self.compare_value(data.P2.value, 0x14, "P2")
                    self.compare_value(data.P3.value, 0x2E, "P3")
                    self.compare_value(data.P4.value, 0x0, "P4")
                elif ce == 3:
                    self.compare_value(data.P1.value, 0x99, "P1")
                    self.compare_value(data.P2.value, 0x14, "P2")
                    self.compare_value(data.P3.value, 0x2E, "P3")
                    self.compare_value(data.P4.value, 0x0, "P4")

        pass
    def compare_value(self, value:int,expect_value:int, desc:str="") -> None:
        if value != expect_value:
            logger.error(f'Expect {desc}={hex(expect_value)}, but = {hex(value)}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'{desc} val = {hex(value)}')
    def post_process(self) -> None:
    
        pass  
        

   
run = Pattern().run
if __name__ == "__main__":
    run()