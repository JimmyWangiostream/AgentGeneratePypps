import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        w = ExecuteCMD.Write10().assign(lun=0, lba=0, length=0xFFFF, fua=1)
        # w.set_option(timeout=10) # CMD Level Timeout
        w.enqueue()
        try:
            # uniform timeout us
            ExecuteCMD.send(timeout=api.UniformTimeout(val=20, unit=api.TimeResolution.us)) 

            # uniform timeout ms
            # ExecuteCMD.send(timeout=api.UniformTimeout(val=5))
        except: # this is a bad practice
            pass

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()