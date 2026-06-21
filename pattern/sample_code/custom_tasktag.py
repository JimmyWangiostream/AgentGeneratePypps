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
        w = ExecuteCMD.Write10()
        w.assign(lun=0, lba=0, length=1, fua=1)
        #===== auto increase tasktag =====#
        ExecuteCMD.enqueue(w)
        ExecuteCMD.enqueue(w)
        ExecuteCMD.enqueue(w)
        ExecuteCMD.enqueue(w)

        #===== assign tasktag manually =====#
        w.upiu.b3_tasktag = 0xAB
        ExecuteCMD.enqueue(w)
        w.upiu.b3_tasktag = 0xCD
        ExecuteCMD.enqueue(w)
        w.upiu.b3_tasktag = 0xFE
        ExecuteCMD.enqueue(w)

        ExecuteCMD.send()

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()