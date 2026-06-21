from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def printout_oem_id_str_desc(self, oem_str_desc: api.OEMIDStringDescriptor) -> None:
        oem_str_desc = cast(api.OEMIDStringDescriptor410, oem_str_desc)
        logger.info(f"{oem_str_desc.__class__.__name__}")
        logger.info(f"  {oem_str_desc.b0_length=}")
        logger.info(f"  {oem_str_desc.b1_descriptor_idn=}")
        for i in range(oem_str_desc._length):
            var_uc = f'w{i*2+2}_uc_{i}'
            logger.info(f"  oem_str_desc.{var_uc}={getattr(oem_str_desc, var_uc):#X}")

    def step1(self) -> None:
        device_desc = cast(api.DeviceDescriptor410, api.get_device_descriptor())
        logger.info("Get OEM ID String Descriptor")
        desc = api.get_oem_id_string_descriptor(device_desc.b23_oem_id)
        self.printout_oem_id_str_desc(desc)

    def post_process(self) -> None:
        pass

run = Pattern().run
if __name__ == "__main__":
    run()