from typing import List, cast
import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger


class Pattern(UFSTC):
    def pre_process(self) -> None:
        logger.info(api.CommonPath.root)
        logger.info(api.CommonPath.development_report)
        logger.info(api.CommonPath.ini)
        logger.info(api.CommonPath.mp_tool)
        logger.info(api.CommonPath.tcsp)
        logger.info(api.CommonPath.report)
        pass

    def step1(self) -> None:
        
        cmd = ExecuteCMD.Unmap()
    
        unmaplist = []

        blockdescriptor = api.UnmapBlockDescriptor()
        blockdescriptor.l4_lba_l = 0
        blockdescriptor.l8_number_of_logical_blocks = 1
        unmaplist.append(blockdescriptor)

        blockdescriptor = api.UnmapBlockDescriptor()
        blockdescriptor.l4_lba_l = 1
        blockdescriptor.l8_number_of_logical_blocks = 2
        unmaplist.append(blockdescriptor)
        
        cmd.assign_multi_cmd(lun=0, block_descriptor=unmaplist)

        ExecuteCMD.enqueue(cmd)
        ExecuteCMD.send()

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()