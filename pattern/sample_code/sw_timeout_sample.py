from datetime import datetime
import time
from typing import cast
import package_root
from Script import api
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:           
        pass

    def step1(self) -> None:
        t = datetime.now()
        while True:
            time.sleep(1)
            logger.info('polling...')
            if api.sw_timeout(t, sec=10):
                logger.info('timeout.')
                break

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()