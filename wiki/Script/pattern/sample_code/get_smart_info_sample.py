import struct
from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.api.ufs_api.defines import WellKnownLUN
from Script.api.ufs_api.vendor_cmd.functions import buffer_get_smart_info
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.api.exception import *

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        
        buffer_get_smart_info()

        pass

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()