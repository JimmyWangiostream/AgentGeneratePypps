from typing import cast
import package_root
from Script import api
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        dut = api.Dut.get_instance()
        if dut.ce_num > 0:
            logger.info(f'CE Num = {dut.ce_num}')
        if dut.m1 > api.M1.PS8311:
            logger.info(f'dut.m1 > 8325')
        if dut.m2 == api.M2.KIOXIA_BICS9_CTLC:
            logger.info(f'dut.m2 is BICS9')
        if dut.ufs_version > 0x210:
            logger.info(f'dut.ufs_version > 0x210')
        if dut.vendor_id == api.VendorID.MICRON:
            logger.info(f'vendor id is micron')
        
        # for debugging usage
        dut.set_to_specific_project(M1=25, M2=20, M3=5, M4=1, vendor_id=52, ufs_version=1024)

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()