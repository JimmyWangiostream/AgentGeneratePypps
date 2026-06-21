from typing import cast
import package_root
from Script import api
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger


class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def printout_device_health_desc(self, dev_health_desc: api.DeviceHealthDescriptor) -> None:
        dev_health_desc = cast(api.DeviceHealthDescriptor410, dev_health_desc)
        logger.info(f"{dev_health_desc.__class__.__name__}")
        logger.info(f"  {dev_health_desc.b0_length=}")
        logger.info(f"  {dev_health_desc.b1_descriptor_idn=}")
        logger.info(f"  {dev_health_desc.b2_pre_eol_info=} ({api.PreEndOfLifeInfo(dev_health_desc.b2_pre_eol_info).name})")
        logger.info(f"  {dev_health_desc.b3_device_life_time_est_a=}")
        logger.info(f"  {dev_health_desc.b4_device_life_time_est_b=}")
        logger.info(f"  {dev_health_desc.q5_vendor_prop_info_1=}")
        logger.info(f"  {dev_health_desc.q13_vendor_prop_info_2=}")
        logger.info(f"  {dev_health_desc.q21_vendor_prop_info_3=}")
        logger.info(f"  {dev_health_desc.q29_vendor_prop_info_4=}")
        logger.info(f"  {dev_health_desc.l37_refresh_total_count=}")
        logger.info(f"  {dev_health_desc.l41_refresh_progress=}")

    def step1(self) -> None:
        dev_desc = api.get_device_health_descriptor()
        logger.info("Get Device Health Descriptor")
        self.printout_device_health_desc(dev_desc)

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
