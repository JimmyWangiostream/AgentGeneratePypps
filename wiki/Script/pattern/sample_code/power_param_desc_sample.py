from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def printout_power_param_desc(self, power_desc: api.PowerParametersDescriptor) -> None:
        power_desc = cast(api.PowerParametersDescriptor410, power_desc)
        logger.info(f"{power_desc.__class__.__name__}")
        logger.info(f"  {power_desc.b0_length=}")
        logger.info(f"  {power_desc.b1_descriptor_idn=}")
        for i in range(power_desc._length):
            var_vcc = f'w{i * 2 + 2}_active_icc_levels_vcc_{i}'
            logger.info(f"  power_desc.{var_vcc}={getattr(power_desc, var_vcc)}")
        for i in range(power_desc._length):
            var_vcc = f'w{i * 2 + 34}_active_icc_levels_vccq_{i}'
            logger.info(f"  power_desc.{var_vcc}={getattr(power_desc, var_vcc)}")
        for i in range(power_desc._length):
            var_vcc = f'w{i * 2 + 66}_active_icc_levels_vccq2_{i}'
            logger.info(f"  power_desc.{var_vcc}={getattr(power_desc, var_vcc)}")

    def step1(self) -> None:
        logger.info("Get Power Parameters Descriptor")
        desc = api.get_power_params_descriptor()
        self.printout_power_param_desc(desc)

    def post_process(self) -> None:
        pass

run = Pattern().run
if __name__ == "__main__":
    run()