from typing import cast
import package_root
from Script import api
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger


class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def printout_device_desc_410(self, dev_desc: api.DeviceDescriptor) -> None:
        dev_desc = cast(api.DeviceDescriptor410, dev_desc)
        logger.info(f"{dev_desc.__class__.__name__}")
        logger.info(f"  {dev_desc.b0_length=}")
        logger.info(f"  {dev_desc.b1_descriptor_idn=}")
        logger.info(f"  {dev_desc.b2_device=}")
        logger.info(f"  {dev_desc.b3_device_class=}")
        logger.info(f"  {dev_desc.b4_device_subclass=}")
        logger.info(f"  {dev_desc.b5_protocol=}")
        logger.info(f"  {dev_desc.b6_number_lu=}")
        logger.info(f"  {dev_desc.b7_number_wlu=}")
        logger.info(f"  {dev_desc.b8_boot_enable=}")
        logger.info(f"  {dev_desc.b9_descr_access_en=}")
        logger.info(f"  {dev_desc.b10_init_power_mode=}")
        logger.info(f"  {dev_desc.b11_high_priority_lun=}")
        logger.info(f"  {dev_desc.b12_secure_removal_type=}")
        logger.info(f"  {dev_desc.b13_security_lu=}")
        logger.info(f"  {dev_desc.b14_background_ops_term_lat=}")
        logger.info(f"  {dev_desc.b15_init_active_icc_level=}")
        logger.info(f"  {dev_desc.w16_spec_version=}")
        logger.info(f"  {dev_desc.w18_manufacturer_date=}")
        logger.info(f"  {dev_desc.b20_manufacturer_name=}")
        logger.info(f"  {dev_desc.b21_product_name=}")
        logger.info(f"  {dev_desc.b22_serial_number=}")
        logger.info(f"  {dev_desc.b23_oem_id=}")
        logger.info(f"  {dev_desc.w24_manufacturer_id=}")
        logger.info(f"  {dev_desc.b26_ud0_base_offset=}")
        logger.info(f"  {dev_desc.b27_ud_config_p_length=}")
        logger.info(f"  {dev_desc.b28_device_rtt_cap=}")
        logger.info(f"  {dev_desc.w29_periodic_rtc_update=}")
        logger.info(f"  {dev_desc.b31_ufs_features_support=}")
        logger.info(f"  {dev_desc.b32_ffu_timeout=}")
        logger.info(f"  {dev_desc.b33_queue_depth=}")
        logger.info(f"  {dev_desc.w34_device_version=}")
        logger.info(f"  {dev_desc.b36_num_secure_wp_area=}")
        logger.info(f"  {dev_desc.l37_psa_max_data_size=}")
        logger.info(f"  {dev_desc.b41_psa_state_timeout=}")
        logger.info(f"  {dev_desc.b42_product_revision_level=}")
        logger.info(f"  {dev_desc.w77_extended_write_booster_support=}")
        logger.info(f"  {dev_desc.l79_extended_ufs_features_support=}")
        logger.info(f"  {dev_desc.b83_write_booster_buffer_preserve_user_space_en=}")
        logger.info(f"  {dev_desc.b84_write_booster_buffer_type=}")
        logger.info(f"  {dev_desc.l85_num_shared_write_booster_buffer_alloc_units=}")

    def printout_features_support_410(self, features: api.UFSFeaturesSupport) -> None:
        features = cast(api.UFSFeaturesSupport410, features)
        logger.info(f"{features.__class__.__name__}")
        logger.info(f"  {features.u0_ffu=}")
        logger.info(f"  {features.u1_psa=}")
        logger.info(f"  {features.u2_device_life_span=}")
        logger.info(f"  {features.u3_refresh_op=}")
        logger.info(f"  {features.u4_too_high_temp=}")
        logger.info(f"  {features.u5_too_low_temp=}")
        logger.info(f"  {features.u6_extended_temp=}")
        logger.info(f"  {features.u7_rsvd=}")

    def printout_extended_features_support_410(self, features: api.ExtendedUFSFeaturesSupport) -> None:
        features = cast(api.ExtendedUFSFeaturesSupport410, features)
        logger.info(f"{features.__class__.__name__}")
        logger.info(f"  {features.u0_ffu=}")
        logger.info(f"  {features.u1_psa=}")
        logger.info(f"  {features.u2_device_life_span=}")
        logger.info(f"  {features.u3_refresh_op=}")
        logger.info(f"  {features.u4_too_high_temp=}")
        logger.info(f"  {features.u5_too_low_temp=}")
        logger.info(f"  {features.u6_extended_temp=}")
        logger.info(f"  {features.u7_rsvd=}")
        logger.info(f"  {features.u8_write_booster=}")
        logger.info(f"  {features.u9_performance_throttling=}")
        logger.info(f"  {features.u10_adv_rpmb=}")
        logger.info(f"  {features.u11_rsvd=}")
        logger.info(f"  {features.u12_device_level_exception_warning=}")
        logger.info(f"  {features.u13_hid=}")
        logger.info(f"  {features.u14_barrier=}")
        logger.info(f"  {features.u15_clear_error_history_functionality=}")
        logger.info(f"  {features.u16_ext_iid=}")
        logger.info(f"  {features.u17_rsvd=}")
        logger.info(f"  {features.u18_fast_recovery_mode=}")
        logger.info(f"  {features.u19_rpmb_authenticated_vendor_cmd=}")

    def printout_extended_wb_support_410(self, features: api.ExtendedWriteBoosterSupport) -> None:
        features = cast(api.ExtendedWriteBoosterSupport410, features)
        logger.info(f"{features.__class__.__name__}")
        logger.info(f"  {features.u0_write_booster_buffer_resize=}")
        logger.info(f"  {features.u1_fifo_partial_flush_mode=}")
        logger.info(f"  {features.u2_pinned_partial_flush_mode=}")

    def step1(self) -> None:
        # UFS spec 4.1
        dev_desc = api.get_device_descriptor()
        self.printout_device_desc_410(dev_desc)
        features = api.get_ufs_features_support()
        self.printout_features_support_410(features)
        extended_features = api.get_extended_ufs_features_support()
        self.printout_extended_features_support_410(extended_features)
        extended_wb = api.get_extended_write_booster_support()
        self.printout_extended_wb_support_410(extended_wb)

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
