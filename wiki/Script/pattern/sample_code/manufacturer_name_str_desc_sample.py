from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def printout_mfr_str_desc(self, mfr_str_desc: api.ManufacturerNameStringDescriptor) -> None:
        mfr_str_desc = cast(api.ManufacturerNameStringDescriptor410, mfr_str_desc)
        logger.info(f"{mfr_str_desc.__class__.__name__}")
        logger.info(f"  {mfr_str_desc.b0_length=}")
        logger.info(f"  {mfr_str_desc.b1_descriptor_idn=}")
        logger.info(f"  {mfr_str_desc.w2_uc_0=:#X}")
        logger.info(f"  {mfr_str_desc.w4_uc_1=:#X}")
        logger.info(f"  {mfr_str_desc.w6_uc_2=:#X}")
        logger.info(f"  {mfr_str_desc.w8_uc_3=:#X}")
        logger.info(f"  {mfr_str_desc.w10_uc_4=:#X}")
        logger.info(f"  {mfr_str_desc.w12_uc_5=:#X}")
        logger.info(f"  {mfr_str_desc.w14_uc_6=:#X}")
        logger.info(f"  {mfr_str_desc.w16_uc_7=:#X}")

    def step1(self) -> None:
        device_desc = cast(api.DeviceDescriptor410, api.get_device_descriptor())
        logger.info("Get Manufacturer Name String Descriptor")
        desc = api.get_manufacturer_name_string_descriptor(device_desc.b20_manufacturer_name)
        self.printout_mfr_str_desc(desc)

    def post_process(self) -> None:
        pass

run = Pattern().run
if __name__ == "__main__":
    run()