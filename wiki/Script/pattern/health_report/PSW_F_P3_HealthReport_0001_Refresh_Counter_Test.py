import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig
from Script.api.ufs_api.defines.constant_define import *


ENG2_WA = True

class Pattern(UFSTC):
    def pre_process(self) -> None:
        
        pass

    def step1(self) -> None:
        logger.flow(1, 'search bin and get mconfig follow mConfig Format in FFU bin')
        response, health_report = project_api.get_micron_health_report()
        x=0
        pass

    def post_process(self) -> None:
        pass
    

run = Pattern().run
if __name__ == "__main__":
    run()