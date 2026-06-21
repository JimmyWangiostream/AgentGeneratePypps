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
        hw_setting = api.HwSetting.get_instance()
        hw_setting.update_from_device()
        flashsettingdata = api.get_flash_setting()
        svn = flashsettingdata.FW_SVN
        logger.info(f"origianl svn = {svn}")
        orign = api.api.search_ffu_bin(api.api.FFUBinType.FW_BIN, api.api.FFUSvnType.CURRENT_SVN_BIN)
        test = api.search_ffu_bin(api.FFUBinType.FW_BIN, api.FFUSvnType.OLD_SVN_BIN)
        hw_setting.set_to_device(api.HwSettingField.FFU_FEATURE, api.FFUFeature.FFU_SAMVE_SVN_BACKWARD_EN)
        api.send_ffu_write_buffer(len(test), 0, test)
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET)
        ffustatus = api.read_attribute(idn=api.AttributeIDN.DEVICE_FFU_STATUS)
        if ffustatus != api.FFUStatus.SUCCESSFUL_MICROCODE_UPDATE:
            raise api.SIGHTING_FFU_STATUS_UNEXPECTED
        flashsettingdata = api.get_flash_setting()
        svn = flashsettingdata.FW_SVN
        logger.info(f"after ffu original -> old, svn = {svn}")
        hw_setting.set_to_device(api.HwSettingField.FFU_FEATURE, api.FFUFeature.FFU_SAMVE_SVN_BACKWARD_EN)
        api.send_ffu_write_buffer(len(orign), 0, orign)
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET)
        ffustatus = api.read_attribute(idn=api.AttributeIDN.DEVICE_FFU_STATUS)
        if ffustatus != api.FFUStatus.SUCCESSFUL_MICROCODE_UPDATE:
            raise api.SIGHTING_FFU_STATUS_UNEXPECTED
        flashsettingdata = api.get_flash_setting()
        svn = flashsettingdata.FW_SVN
        logger.info(f"after ffu old -> original, svn = {svn}")


        logger.info(f"origianl svn = {svn}")
        orign = api.search_ffu_bin(api.FFUBinType.FW_HW_BIN, api.FFUSvnType.CURRENT_SVN_BIN)
        test = api.search_ffu_bin(api.FFUBinType.FW_HW_BIN, api.FFUSvnType.OLD_SVN_BIN)
        hw_setting.set_to_device(api.HwSettingField.FFU_FEATURE, api.FFUFeature.FFU_SAMVE_SVN_BACKWARD_EN)
        api.send_ffu_write_buffer(len(test), 0, test)
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET)
        ffustatus = api.read_attribute(idn=api.AttributeIDN.DEVICE_FFU_STATUS)
        if ffustatus != api.FFUStatus.SUCCESSFUL_MICROCODE_UPDATE:
            raise api.SIGHTING_FFU_STATUS_UNEXPECTED
        flashsettingdata = api.get_flash_setting()
        svn = flashsettingdata.FW_SVN
        logger.info(f"after ffu original -> old, svn = {svn}")
        hw_setting.set_to_device(api.HwSettingField.FFU_FEATURE, api.FFUFeature.FFU_SAMVE_SVN_BACKWARD_EN)
        api.send_ffu_write_buffer(len(orign), 0, orign)
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET)
        ffustatus = api.read_attribute(idn=api.AttributeIDN.DEVICE_FFU_STATUS)
        if ffustatus != api.FFUStatus.SUCCESSFUL_MICROCODE_UPDATE:
            raise api.SIGHTING_FFU_STATUS_UNEXPECTED
        flashsettingdata = api.get_flash_setting()
        svn = flashsettingdata.FW_SVN
        logger.info(f"after ffu old -> original, svn = {svn}")

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()