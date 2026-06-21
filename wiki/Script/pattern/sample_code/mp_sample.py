from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.api import shared

_param = shared.param

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        api.MP().execute()
        api.first_init_to_max_hs_gear(link_startup_mode=_param.current_speed.link_startup_mode, ref_clk=_param.current_speed.refclk)

        ExecuteCMD.Write10().assign(lun=0, lba=0, length=1, fua=1).enqueue()
        ExecuteCMD.send()

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()