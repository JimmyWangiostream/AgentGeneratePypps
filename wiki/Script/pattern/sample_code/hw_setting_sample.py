import struct
from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass
    def step1(self) -> None:
        hw_setting = api.HwSetting.get_instance()
        hw_setting.get_local_val(api.HwSettingField.SUSPEND_SCALE)
        hw_setting.get_local_val(api.HwSettingField.SUSPEND_TIMER)

        # multiple field style
        # hw_setting.set_local_val(api.HwSettingField.SUSPEND_SCALE, 5)
        # hw_setting.set_local_val(api.HwSettingField.SUSPEND_TIMER, 12)
        # hw_setting.set_to_device()

        # single field style
        hw_setting.set_to_device(api.HwSettingField.SUSPEND_SCALE, 5)

        hw_setting.get_local_val(api.HwSettingField.SUSPEND_SCALE)
        hw_setting.get_local_val(api.HwSettingField.SUSPEND_TIMER)
    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()