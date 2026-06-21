from typing import cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        ## dirty card 
        w = ExecuteCMD.Write10()
        w.assign(lun=0, lba=0, length=101, fua=1)
        w.set_option(delay_time=1)
        w.enqueue()
        ExecuteCMD.send(clear_on_success = True)
        for lba in range(45):
            w = ExecuteCMD.Write10()
            w.assign(lun=0, lba= 45 - 1 - lba , length=1, fua=1)
            w.set_option(delay_time=1)
            w.enqueue()
            ExecuteCMD.send(clear_on_success = True)

    def step1(self) -> None:
        logger.info("Flow = FBO Analysis Flow")
        fbo = api.FboVersion0101()
        fbo.get_descriptor() ## update descriptor

        logger.info("Flow = Set FBO WriteBuffer")
        number_of_wb_entries = 10
        fbo_write_buffer_entry_list = []
        for i in range(0, number_of_wb_entries):
            fbo_write_buffer_entry_list.append(api.FboWriteBufferEntry0101(start_lba = i * 100 , length = 100))
        fbo_write_buffer_struct = api.FboWriteBufferStruct0101(fbo_type = 0, fbo_version = 0, car = 1, write_buffer_entry_list = fbo_write_buffer_entry_list )
        fbo.set_fbo_write_buffer(fbo_write_buffer_struct)

        logger.info("Flow = Set FBO Control")
        fbo.set_fbo_control(value = api.FboControlType.START_FBO_ANALYSIS)

        logger.info("Flow = Get FBO ProgressState")
        fbo_progress_state = fbo.get_fbo_progress_state()

        logger.info("Flow = Get FBO ReadBuffer")
        FboReadBufferStruct0101 = fbo.get_fbo_read_buffer()

        logger.info("Flow = FBO Optimization Flow")

        logger.info("Flow = Set FBOExecuteThreshold")
        fbo.set_fbo_execute_threshold(value = 0x0)

        logger.info("Flow = Set FBO Control")
        fbo.set_fbo_control(value = api.FboControlType.START_FBO_OPTIMIZATION)

        logger.info("Flow = Get FBO ProgressState")
        fbo_progress_state = fbo.get_fbo_progress_state()

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
