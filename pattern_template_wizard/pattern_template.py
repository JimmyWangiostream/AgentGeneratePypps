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
        pass
    
    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()