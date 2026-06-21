import package_root
from Script import api
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

from Script.api import (
    ExecuteCMD,
    access_vendor_mode, vuc_clear_rpmb_key, vuc_backup_desc_attr_flag, buffer_factory_reset,
    RPMBRegion
)


class Pattern(UFSTC):

    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        access_vendor_mode()
        vuc_clear_rpmb_key(RPMBRegion.REGION_0)

    def step2(self) -> None:
        vuc_backup_desc_attr_flag()
        buffer_factory_reset()

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
