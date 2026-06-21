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
        vcc_result = _sdk.measure_current(lib.CurrentChannel.VCC.value)
        vccq2_result = _sdk.measure_current(lib.CurrentChannel.VCCQ2.value)
        vccq_result = _sdk.measure_current(lib.CurrentChannel.VCC.value)
        print(f"measrue_cur, vcc = {vcc_result.current}")
        print(f"measrue_cur, vccq2 = {vccq2_result.current}")
        print(f"measrue_cur, vccq = {vccq_result.current}")

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()