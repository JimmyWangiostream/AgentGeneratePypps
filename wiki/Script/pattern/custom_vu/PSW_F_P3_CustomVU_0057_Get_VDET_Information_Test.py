import package_root
from Script.lib import sdk_lib as lib
from time import sleep
from typing import cast
from Script import api
from Script.api import shared, dumpfile, Dcmd5ResetType, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from typing import TypeAlias, cast, List
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api import init_tester_to_unit_ready
from Script.api.ufs_api.descriptors.configuration_desc.structs import ConfigDescriptor, ConfigDescriptor310, ConfigDescriptor400, ConfigDescriptor410
from enum import Enum, auto
from Script.project_api.custom_vu.get_ONFI.functions import issue_4073_get_ONFI_speed
from Script.project_api.custom_vu.VDET_vu.functions import issue_40B8_to_get_VDET_information, issue_D074_to_disable_VDET
from Script.api.ufs_api.vendor_cmd.functions import *

ENG2_WA = True

_sdk = shared.sdk

ConfigDescriptorUnion: TypeAlias = ConfigDescriptor310 | ConfigDescriptor400 | ConfigDescriptor410


class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        logger.flow(1, 'Verify ONFI frequency value is correct')

        logger.info('Modify HW setting to disable suspend')
        hw_setting = api.HwSetting.get_instance()
        hw_setting.set_to_device(field = api.HwSettingField.POWER_SAVING_CTRL_ENABLE, val= 0x3A)

        logger.info('Issue VU 4073 to get ONFI speed')
        _, speed = issue_4073_get_ONFI_speed()

        logger.info(f'Expect ONFI frequency value is equal 1600, and current ONFI frequency value is {speed.ONFI_frequency.value}')
        if speed.ONFI_frequency.value != 1600:
            logger.error_lb(f'Host issue vu 4073 to get ONFI speed')
            logger.error_fp(f'Expect the ONFI frequency = 1600, but frequency = {speed.ONFI_frequency.value}')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def step2(self) -> None:
        
        logger.flow(2, 'Modify HW setting to disable suspend')
        hw_setting = api.HwSetting.get_instance()
        hw_setting.set_to_device(field = api.HwSettingField.POWER_SAVING_CTRL_ENABLE, val= 0x3A)

        logger.flow(3, 'Issue VU 40B8 to get VDET Information')
        _, vdet_bk = issue_40B8_to_get_VDET_information()
        logger.info(f' vcc drop count = {vdet_bk.VccDropCnt.value}, vccq drop count = {vdet_bk.VccqDropCnt.value}')
        
        logger.flow(4, 'Drop VCC/VCCQ voltage')
        self.drop_vcc_vccq_voltage()

        logger.flow(5, 'Issue VU 40B8 to get VDET information')
        _, vdet = issue_40B8_to_get_VDET_information()
        logger.info(f' vcc drop count = {vdet.VccDropCnt.value}, vccq drop count = {vdet.VccqDropCnt.value}')

        logger.flow(6, 'Verify that VCC and VCCQ drop counts exceed')
        logger.info(f'Before VCC/VCCQ voltage drop: vcc drop count = {vdet_bk.VccDropCnt.value}, vccq drop count = {vdet_bk.VccqDropCnt.value}')
        logger.info(f'After VCC/VCCQ voltage drop: vcc drop count = {vdet.VccDropCnt.value}, vccq drop count = {vdet.VccqDropCnt.value}')
        if not (vdet.VccDropCnt.value > vdet_bk.VccDropCnt.value and vdet.VccqDropCnt.value > vdet_bk.VccqDropCnt.value):
            logger.error_lb(f'Host triggers voltage drop, then issue 40B8 for VDET information')
            logger.error_fp(f'VCC/VCCQ drop count did not increase as expected, before count = [{vdet_bk.VccDropCnt.value}, {vdet_bk.VccqDropCnt.value}], after counts = [{vdet.VccDropCnt.value}, {vdet.VccqDropCnt.value}]')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        
        vdet_bk = vdet

        logger.flow(7, 'Drop VCCQ voltage')
        self.switch_voltage_value(lib.PowerChannel.VCCQ, 1.15, 2)
        self.switch_voltage_value(lib.PowerChannel.VCCQ, 1.04, 1)
        self.switch_voltage_value(lib.PowerChannel.VCCQ, 1.3, 1)

        logger.flow(7, 'Unipro Reset')
        init_tester_to_unit_ready(Dcmd5ResetType.UNIPRO_RESET)
        logger.flow(7, 'Switch SSU to sleep and active')
        self.ssu_sleep_and_active()

        logger.flow(8, 'Issue VU 40B8 to get VDET information')
        _, vdet = issue_40B8_to_get_VDET_information()
        logger.info(f' vcc drop count = {vdet.VccDropCnt.value}, vccq drop count = {vdet.VccqDropCnt.value}')

        logger.flow(9, 'Verify that VCC and VCCQ drop counts do not exceed')
        logger.info(f'Before VCC/VCCQ voltage drop: vcc drop count = {vdet_bk.VccDropCnt.value}, vccq drop count = {vdet_bk.VccqDropCnt.value}')
        logger.info(f'After VCC/VCCQ voltage drop: vcc drop count = {vdet.VccDropCnt.value}, vccq drop count = {vdet.VccqDropCnt.value}')
        if not (vdet.VccDropCnt.value == vdet_bk.VccDropCnt.value and vdet.VccqDropCnt.value == vdet_bk.VccqDropCnt.value):
            logger.error_lb(f'Host triggers voltage drop, then issue 40B8 for VDET information')
            logger.error_fp(f'VCC/VCCQ drop count did not increase as expected, before count = [{vdet_bk.VccDropCnt.value}, {vdet_bk.VccqDropCnt.value}], after counts = [{vdet.VccDropCnt.value}, {vdet.VccqDropCnt.value}]')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

        pass

    def step3(self) -> None:
        logger.flow(10, f'Hardware reset')
        init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)

        logger.flow(11, 'Issue VU 40B8 to get VDET Information')
        _, vdet_bk = issue_40B8_to_get_VDET_information()

        logger.flow(12, 'Issue VU 4074 to disable VDET and drop VCC/VCCQ')
        self.drop_vcc_vccq_voltage(isDisableVDET= True)

        logger.flow(13, 'Verify that VCC and VCCQ drop counts do not exceed')
        logger.info('Issue VU 40B8 to get VDET information')
        _, vdet = issue_40B8_to_get_VDET_information()
        logger.info(f'Before VCC/VCCQ voltage drop: vcc drop count = {vdet_bk.VccDropCnt.value}, vccq drop count = {vdet_bk.VccqDropCnt.value}')
        logger.info(f'After VCC/VCCQ voltage drop: vcc drop count = {vdet.VccDropCnt.value}, vccq drop count = {vdet.VccqDropCnt.value}')
        if not (vdet.VccDropCnt.value == vdet_bk.VccDropCnt.value and vdet.VccqDropCnt.value == vdet_bk.VccqDropCnt.value):
            logger.error_lb(f'Host triggers voltage drop, then issue 40B8 for VDET information')
            logger.error_fp(f'VCC/VCCQ drop count did not equal as expected, before count = [{vdet_bk.VccDropCnt.value}, {vdet_bk.VccqDropCnt.value}], after counts = [{vdet.VccDropCnt.value}, {vdet.VccqDropCnt.value}]')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def step4(self) -> None:
        logger.flow(14, f'Hardware reset')
        init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)

        logger.flow(15, 'Issue VU 40B8 to get VDET Information')
        _, vdet_bk = issue_40B8_to_get_VDET_information()

        logger.flow(26, 'Drop VCC/VCCQ voltage')
        self.drop_vcc_vccq_voltage()

        logger.flow(17, 'Verify that VCC and VCCQ drop counts exceed')
        logger.info('Issue VU 40B8 to get VDET information')
        _, vdet = issue_40B8_to_get_VDET_information()
        logger.info(f'Before VCC/VCCQ voltage drop: vcc drop count = {vdet_bk.VccDropCnt.value}, vccq drop count = {vdet_bk.VccqDropCnt.value}')
        logger.info(f'After VCC/VCCQ voltage drop: vcc drop count = {vdet.VccDropCnt.value}, vccq drop count = {vdet.VccqDropCnt.value}')
        if not (vdet.VccDropCnt.value > vdet_bk.VccDropCnt.value and vdet.VccqDropCnt.value > vdet_bk.VccqDropCnt.value):
            logger.error_lb(f'Host triggers voltage drop, then issue 40B8 for VDET information')
            logger.error_fp(f'VCC/VCCQ drop count did not increase as expected, before count = [{vdet_bk.VccDropCnt.value}, {vdet_bk.VccqDropCnt.value}], after counts = [{vdet.VccDropCnt.value}, {vdet.VccqDropCnt.value}]')
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        pass

    def post_process(self) -> None:
        pass

    def switch_voltage_value(self, channel: lib.PowerChannel, voltage: float, digits:int ) -> None:
        
        logger.info(f'Channel {channel.value} switch voltage to {voltage}V')

        if(channel == lib.PowerChannel.VCC):
            measureChannel = lib.VoltageChannel.VCC
        elif(channel == lib.PowerChannel.VCCQ):
            measureChannel = lib.VoltageChannel.VCCQ
        else: 
            measureChannel = lib.VoltageChannel.VCCQ2        
        _sdk.switch_voltage_value(voltage, channel.value) 
        pass
    
    def ssu_sleep_and_active(self) -> None:
        testQD = 1
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.send(QD=testQD,clear_on_success=True)
        pass

    def drop_vcc_vccq_voltage(self, isDisableVDET: bool = False)-> None:

        if(isDisableVDET):
            _ = issue_D074_to_disable_VDET()

        self.switch_voltage_value(lib.PowerChannel.VCCQ, 1.08, 2)
        self.switch_voltage_value(lib.PowerChannel.VCCQ, 1.3, 1)
        logger.info('Switch SSU to sleep and active')
        self.ssu_sleep_and_active()

        if(isDisableVDET):
            _ = issue_D074_to_disable_VDET()
        
        self.switch_voltage_value(lib.PowerChannel.VCC, 2.1, 1)
        self.switch_voltage_value(lib.PowerChannel.VCC, 2.5, 1)
        logger.info('Unipro Reset')
        init_tester_to_unit_ready(Dcmd5ResetType.UNIPRO_RESET)
        logger.info('Switch SSU to sleep and active')
        self.ssu_sleep_and_active()


run = Pattern().run
if __name__ == "__main__":
    run()

    