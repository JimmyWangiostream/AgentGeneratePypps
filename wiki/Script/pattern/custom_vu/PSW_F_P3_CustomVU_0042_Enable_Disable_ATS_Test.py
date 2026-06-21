import package_root
from Script import api
from Script.api.util.functions import dumpfile
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig, get_flash_setting
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api import read_fw_value
import time
from Script.project_api.set_string_description.structs import SerialNumberString, ProductNameString,WWYY, ReadUid, AllManufacturingSetting, ManufactureDate



import package_root
from Script import api
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script.api.cmd_seq.response import QueryResponse
from Script.api.ufs_api.defines.enum_define import DescriptorIDN, MaxNumberLUN
from Script.api.ufs_api.descriptors.geometry_desc.structs import GeometryDescriptor310, GeometryDescriptor400, GeometryDescriptor410
from Script.api.ufs_api.descriptors.device_desc.structs import (DeviceDescriptor310, DeviceDescriptor400, DeviceDescriptor410)
from Script.api.ufs_api.descriptors.configuration_desc.structs import ConfigDescriptor, ConfigDescriptor310, ConfigDescriptor400, ConfigDescriptor410
from Script.api.ufs_api.descriptors.device_health_desc.structs import DeviceHealthDescriptor310, DeviceHealthDescriptor400, DeviceHealthDescriptor410
from Script.api.ufs_api.descriptors.power_params_desc.structs import PowerParametersDescriptor310, PowerParametersDescriptor400, PowerParametersDescriptor410
from Script.api.ufs_api.descriptors.rpmb_unit_desc.structs import RPMBUnitDescriptor310, RPMBUnitDescriptor400, RPMBUnitDescriptor410
from typing import Any, List, cast, Tuple
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig, get_flash_setting
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api import read_fw_value
import Script.api.shared as shared
import time
from Script.api.cmd_seq.response import CommandResponse
from typing import TypeAlias, cast
from Script.pattern.pattern_logger import logger
from importlib import import_module
from Script.api.util.dut.dut import Dut
_structs_path = 'Script.api.ufs_api.descriptors.geometry_desc.structs'
from dataclasses import dataclass
import os
from enum import Enum
from Script.lib.sdk_lib.user.exception import  DLL_RESPONSE_ERROR

GeometryDescriptorUnion: TypeAlias = GeometryDescriptor310 | GeometryDescriptor400 | GeometryDescriptor410
DeviceDescriptorUnion: TypeAlias = DeviceDescriptor310 | DeviceDescriptor400 | DeviceDescriptor410
DeviceHealthDescriptorUnion: TypeAlias = DeviceHealthDescriptor310 | DeviceHealthDescriptor400 | DeviceHealthDescriptor410
ConfigDescriptorUnion: TypeAlias = ConfigDescriptor310 | ConfigDescriptor400 | ConfigDescriptor410
PowerParametersDescriptorUnion: TypeAlias = PowerParametersDescriptor310 | PowerParametersDescriptor400 | PowerParametersDescriptor410
RPMBUnitDescriptorUnion: TypeAlias = RPMBUnitDescriptor310 | RPMBUnitDescriptor400 | RPMBUnitDescriptor410

class Action(Enum):
    COMPARE = 0
    TBD = 1
    NOTREADABLE = 2
    NOTWRITEABLE = 3


class CompareFlagAttribute:
    name: str
    idn: int
    action : Action # 0 : tdb, 1: do comprae, 2 : not readable, 3 : not writeable
    target_value: int

class CompareDescriptor:
    name: str
    offset: int
    do_compare : int
    action : Action # 0 : tdb, 1: do comprae, 2 : not readable, 3 : not writeable
    target_value: int

class CompareAttributePerLun:
    name: str
    lun_id: int
    idn: int
    selector: int
    action : Action # 0 : tdb, 1: do comprae, 2 : not readable, 3 : not writeable
    target_value: int


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.D088_test()


    def get_ast_times(self) -> int:
        payload_get = project_api.get_smart_info()
        offset_ats_timer = 0x4a8
        data_size_byte = 8
        ats_times_payload = payload_get[offset_ats_timer: offset_ats_timer + data_size_byte]
        ats_times = int.from_bytes(ats_times_payload, 'little')
        logger.info(f'ats_times = {ats_times}')
        dumpfile('smart_info.bin',payload_get)
        return ats_times
    def D088_test(self) -> None:
        logger.flow(1,"get smart_info[0x4a8:0x4b0] ats_times")
        ast_sec = 15
        backup_ats_times = self.get_ast_times()
        logger.flow(2,"idle 15 s")
        time.sleep(ast_sec)
        get_ats_times = self.get_ast_times()  
        do_disable_enable_ats = False
        if backup_ats_times < get_ats_times:
            logger.flow(3,"get smart_info[0x4a8:0x4b0] ats_times expected increase")
            logger.info(f'ats_times increase, do disable -> enable ats test')
            do_disable_enable_ats = True
        else:
            logger.info(f'ats_times not increase, do enable -> disable ats test')

        backup_ats_times = get_ats_times
        if do_disable_enable_ats:
            logger.info(4,"issue D088 with paylody[12] = 0 (disable ats)")
            project_api.issue_D088_enable_disable_auto_standby(0)
            backup_ats_times = self.get_ast_times()  
            logger.flow(5,"idle 15 s")
            time.sleep(ast_sec)
            get_ats_times = self.get_ast_times()    
            logger.flow(6,"get smart_info[0x4a8:0x4b0] ats_times expected not increase")          
            if(get_ats_times > backup_ats_times):
                logger.info(f'ats_times should not increase when do  disable ats test')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            logger.info(f'recover to enable ats')
            logger.flow(7,"issue D088 with paylody[12] = 1 (enable ats)")
            project_api.issue_D088_enable_disable_auto_standby(1)
        else:
            project_api.issue_D088_enable_disable_auto_standby(1)
            backup_ats_times = self.get_ast_times()  
            time.sleep(ast_sec)
            get_ats_times = self.get_ast_times()   
            if(get_ats_times > backup_ats_times):
                logger.info(f'ats_times should  increase when do  enable ats test')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL            
            logger.info(f'recover to disble ats')
            project_api.issue_D088_enable_disable_auto_standby(0)                
        logger.info(f'D088 test pass')   

    def step1(self) -> None:  
        pass
    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()