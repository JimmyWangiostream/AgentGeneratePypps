from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def printout_serial_num_str_desc(self, serial_str_desc: api.SerialNumberStringDescriptor) -> None:
        serial_str_desc = cast(api.SerialNumberStringDescriptor410, serial_str_desc)
        logger.info(f"{serial_str_desc.__class__.__name__}")
        logger.info(f"  {serial_str_desc.b0_length=}")
        logger.info(f"  {serial_str_desc.b1_descriptor_idn=}")
        for i in range(serial_str_desc._length):
            var_uc = f'w{i * 2 + 2}_uc_{i}'
            logger.info(f"  serial_str_desc.{var_uc}={getattr(serial_str_desc, var_uc):#X}")

    def step1(self) -> None:
        device_desc = cast(api.DeviceDescriptor410, api.get_device_descriptor())
        logger.info("Get Serial Number String Descriptor")
        desc = api.get_serial_number_descriptor(device_desc.b22_serial_number)
        self.printout_serial_num_str_desc(desc)

    def post_process(self) -> None:
        pass

run = Pattern().run
if __name__ == "__main__":
    run()