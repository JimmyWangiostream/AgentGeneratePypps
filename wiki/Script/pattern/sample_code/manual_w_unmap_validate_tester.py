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
        logger.info('[data1 4KB]')
        data1 = bytearray([0x5B] * 4096)
        data1[0] = 0x66
        data1[-1] = 0x77
        logger.print_buffer(data1)

        logger.info('[data2 4KB]')
        data2 = bytearray([0xAB] * 4096)
        data2[0] = 0x88
        data2[-1] = 0x99
        logger.print_buffer(data2)

        for i in range(1000):
            logger.info(f'loop {i+1}')
            try:
                while True:
                    w = ExecuteCMD.Write10()
                    w.data = data1 * 3
                    w.assign(lun=0, lba=0, length=3, fua=1).set_option(manual_mode=True).enqueue()

                    w.data = data2
                    w.assign(lun=0, lba=3, length=1, fua=1).set_option(manual_mode=True).enqueue()

                    ExecuteCMD.Unmap().assign(lun=0, lba=0, length=1).enqueue()
                    
            except api.PATTERN_ASSERT_EXECUTOR_CMD_LIST_IS_FULL:
                logger.warning(f'cmd seq is full: size = {len(ExecuteCMD._cmd_list)}')    

            ExecuteCMD.send(clear_on_success=False)

            for idx in range(len(ExecuteCMD._cmd_list)):
                res = ExecuteCMD.read_response(idx)

            ExecuteCMD.clear()

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()