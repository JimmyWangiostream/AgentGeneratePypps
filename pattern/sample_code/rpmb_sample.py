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
        for i in range(2):
            api.vuc_clear_rpmb_key(api.RPMBRegion.REGION_0)
            rpmb = api.RPMB(api.RPMBRegion.REGION_0)
            try:
                write_counter = rpmb.rpmb_read_counter()
            except api.SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
                logger.info("RPMB key is cleared")
                rpmb.rpmb_key_programming()
            else:
                logger.error("RPMB key is not cleared")
                raise api.SPEC_ASSERT_RPMB_KEY_NOT_CLEARED
            
            rpmb.rpmb_write_data(0, 4)
            rpmb.rpmb_read_data(0, 4)

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()