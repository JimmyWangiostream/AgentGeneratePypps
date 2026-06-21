from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def printout_product_revision_level_str_desc(self, prl_str_desc: api.ProductRevisionLevelStringDescriptor) -> None:
        prl_str_desc = cast(api.ProductRevisionLevelStringDescriptor410, prl_str_desc)
        logger.info(f"{prl_str_desc.__class__.__name__}")
        logger.info(f"  {prl_str_desc.b0_length=}")
        logger.info(f"  {prl_str_desc.b1_descriptor_idn=}")
        logger.info(f"  {prl_str_desc.w2_uc_0=:#X}")
        logger.info(f"  {prl_str_desc.w4_uc_1=:#X}")
        logger.info(f"  {prl_str_desc.w6_uc_2=:#X}")
        logger.info(f"  {prl_str_desc.w8_uc_3=:#X}")

    def step1(self) -> None:
        device_desc = cast(api.DeviceDescriptor410, api.get_device_descriptor())
        logger.info("Get Product Revision Level String Descriptor")
        desc = api.get_product_revision_level_string_descriptor(device_desc.b42_product_revision_level)
        self.printout_product_revision_level_str_desc(desc)

    def post_process(self) -> None:
        pass

run = Pattern().run
if __name__ == "__main__":
    run()