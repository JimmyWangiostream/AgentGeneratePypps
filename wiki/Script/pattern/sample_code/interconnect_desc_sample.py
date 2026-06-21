from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def printout_interconnect_desc(self, interconnect_desc: api.InterconnectDescriptor) -> None:
        interconnect_desc = cast(api.InterconnectDescriptor410, interconnect_desc)
        logger.info(f"{interconnect_desc.__class__.__name__}")
        logger.info(f"  {interconnect_desc.b0_length=}")
        logger.info(f"  {interconnect_desc.b1_descriptor_idn=}")
        logger.info(f"  {interconnect_desc.w2_bcd_unipro_version=:#X}")
        logger.info(f"  {interconnect_desc.w4_bcd_mphy_version=:#X}")

    def step1(self) -> None:
        logger.info("Get Interconnect Descriptor")
        desc = api.get_interconnect_descriptor()
        self.printout_interconnect_desc(desc)

    def post_process(self) -> None:
        pass

run = Pattern().run
if __name__ == "__main__":
    run()