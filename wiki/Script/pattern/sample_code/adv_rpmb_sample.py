import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        config = api.get_config_descriptors()
        config[0].header.b12_rpmb_region_enable = (api.RPMBRegionEnable.REGION_0_ENABLE | 
                                                   api.RPMBRegionEnable.ADVANCED_RPMB_MODE | 
                                                   api.RPMBRegionEnable.RPMB_PURGE_ENABLE)
        config[0].header.b2_conf_desc_continue = 0
        api.push_write_config(config[0], 0)
        api.print_config(config[0], 0)
        ExecuteCMD.send()

    def step2(self) -> None:
        for i in range(2):
            api.vuc_clear_rpmb_key(api.RPMBRegion.REGION_0)
            adv_rpmb = api.AdvRPMB(api.RPMBRegion.REGION_0)
            try:
                write_counter = adv_rpmb.adv_rpmb_read_counter()
            except api.SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET as e:
                logger.info("RPMB key is cleared")
                adv_rpmb.adv_rpmb_key_programming()
            else:
                logger.error("RPMB key is not cleared")
                raise api.SPEC_ASSERT_RPMB_KEY_NOT_CLEARED
            
            adv_rpmb.adv_rpmb_write_data(0, 4)
            adv_rpmb.adv_rpmb_read_data(0, 4)

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()