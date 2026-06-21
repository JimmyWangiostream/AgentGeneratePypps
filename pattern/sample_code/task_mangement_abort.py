import struct
from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.api.exception import PATTERN_ASSERT_BUFFER_MANAGER_FAIL_CYCLE_INDICATOR_NOT_FOUND
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        w = ExecuteCMD.Write10().assign(lun=0, lba=0, length=256, fua=1)
        r = ExecuteCMD.Read10().assign(lun=0, lba=0, length=10, fua=1)

        w.enqueue()
        r.enqueue()
        target_idx = r.enqueue()
        r.enqueue()
        r.enqueue()
        tm_idx = api.push_abort_task(target_idx)
        
        ExecuteCMD.send(clear_on_success=False)

        api.check_if_target_is_aborted(target_idx=target_idx, tm_abort_idx=tm_idx)

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()