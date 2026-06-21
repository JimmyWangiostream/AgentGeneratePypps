import package_root
from Script import api
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

_sdk = api.shared.sdk

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        # set the parameter that you want to change, the others will remain the same as param.current_speed
        api.speed_change(txgear=api.SpdChgGear.GEAR_4)
        
        # to lower the cmd gap time or mix with other cmds, you can use `push_speed_change`
        api.push_speed_change(txgear=api.SpdChgGear.GEAR_3, rxgear=api.SpdChgGear.GEAR_3)
        api.push_speed_change(txgear=api.SpdChgGear.GEAR_4, rxgear=api.SpdChgGear.GEAR_4)
        api.push_speed_change(txgear=api.SpdChgGear.GEAR_3, rxgear=api.SpdChgGear.GEAR_3)
        api.push_speed_change(txgear=api.SpdChgGear.GEAR_4, rxgear=api.SpdChgGear.GEAR_4)
        ExecuteCMD.send()

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()