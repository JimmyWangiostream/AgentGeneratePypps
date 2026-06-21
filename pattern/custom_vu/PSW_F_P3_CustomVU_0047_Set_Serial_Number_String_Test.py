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
from Script.api import  cmd_seq as ExecuteCMD
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
    error_msg_for_debug = ""
    manufacture_name = 0
    product_string_name = 0
    manufacture_name = 0
    serial_number = 0
    product_revision_level = 0
    oem_id = 0
    assignd_index_for_idn5 = 0
    pattern_error = False
    device_manufacture_id = 0
    device_manufacture_date = 0
    device_manufacture_name = 0
    wwyy_from_health_descriptor = 0
    def pre_process(self) -> None:

        self.pattern_get_device_descriptor()
        self.C04A_test()
        pass
    def C04A_test(self) -> None:
        self.assignd_index_for_idn5 = self.serial_number
        descriptor = self.pattern_get_descriptor(5)
        descriptor_backup = descriptor.copy()
        descriptor_setting = descriptor.copy()
        serial_number = SerialNumberString()

        setting_value_offset = 3
        # Error Case
        logger.flow(1, f'set serial number error case')
        max_transfer_len_serial_number = 65
        serial_number.size_of_descriptor.value = max_transfer_len_serial_number
        serial_number.string_type_identifier.value = 5
        end_offset = (serial_number.size_of_descriptor.value) - 1
        end_offset = int(end_offset)
        setting_payload = descriptor[2:end_offset]
        setting_payload[setting_value_offset] = setting_payload[setting_value_offset] + 1 # make difference
        if len(setting_payload) < len(serial_number.unicode_string_chracter.payload):
            for i in range(len(serial_number.unicode_string_chracter.payload) - len(setting_payload)):
                setting_payload.append(0)
        print(len(setting_payload))
        serial_number.unicode_string_chracter.payload = setting_payload
        dumpfile("setting_serial_string_error_case.bin",serial_number.payload)
        
        try:
            rsp = project_api.issue_C04A_to_set_serial_number_string(serial_number,True)
        except DLL_RESPONSE_ERROR:
            logger.info('send command error')
        if rsp.b32_sense_data.b12_asc != 0x26 and rsp.upiu.b7_status == 0:
            logger.error_fp(f'C04A error case, but rsp not fail and asc = 0x26')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        ExecuteCMD.clear()
        descriptor = self.pattern_get_descriptor(5)
        if descriptor_backup != descriptor:
            logger.error_fp(f'C04A error case, expected_descriptor no change after error case, but change')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        # Normal Case
        logger.flow(2, f'set serial number normal case')
        max_transfer_len_serial_number = 64
        serial_number.size_of_descriptor.value = max_transfer_len_serial_number
        serial_number.string_type_identifier.value = 5
        end_offset = (serial_number.size_of_descriptor.value) - 1
        end_offset = int(end_offset)
        setting_payload = descriptor[2:end_offset]
        
        setting_payload[setting_value_offset] = setting_payload[setting_value_offset] + 1 # make difference
        descriptor_setting[setting_value_offset + 2] = descriptor_setting[setting_value_offset] + 1 # make difference
        if len(setting_payload) < len(serial_number.unicode_string_chracter.payload):
            for i in range(len(serial_number.unicode_string_chracter.payload) - len(setting_payload)):
                setting_payload.append(0)
        print(len(setting_payload))
        serial_number.unicode_string_chracter.payload = setting_payload
        dumpfile("setting_serial_string_error_case.bin",serial_number.payload)
        
        rsp = project_api.issue_C04A_to_set_serial_number_string(serial_number)

        dumpfile("setting_serial_string.bin",serial_number.payload)
        descriptor = self.pattern_get_descriptor(5)
        if descriptor_setting != descriptor:
            logger.error_fp(f'C04A normal case, expected_descriptor no change after error case, but change')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        # recover flow
        max_transfer_len_serial_number = 64
        serial_number.size_of_descriptor.value = max_transfer_len_serial_number
        serial_number.string_type_identifier.value = 5
        end_offset = (serial_number.size_of_descriptor.value) - 1
        end_offset = int(end_offset)
        setting_payload = descriptor_backup[2:end_offset]
        if len(setting_payload) < len(serial_number.unicode_string_chracter.payload):
            for i in range(len(serial_number.unicode_string_chracter.payload) - len(setting_payload)):
                setting_payload.append(0)
        print(len(setting_payload))
        serial_number.unicode_string_chracter.payload = setting_payload
        dumpfile("setting_serial_string_error_case.bin",serial_number.payload)
        
        rsp = project_api.issue_C04A_to_set_serial_number_string(serial_number)

        dumpfile("setting_serial_string.bin",serial_number.payload)
        descriptor = self.pattern_get_descriptor(5)
        if descriptor_backup != descriptor:
            logger.error_fp(f'C04A normal case, expected_descriptor no change after error case, but change')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        pass        
    def step1(self) -> None:  
        shared.param.gDevice
        device_desc = self.pattern_get_device_descriptor()
        config_desc = self.pattern_get_configure_descriptor(0)
        health_desc = self.pattern_get_health_descriptor()
        # wait for eng2 vu
        # response = self.set_serial_number_string()
        pass
    def post_process(self) -> None:
        pass

    def pattern_get_descriptor(self, idn:int) -> bytearray:
        selector = 0x00
        index = 0
        if idn == 0x2: # RPMB
            index = 0xC4
        elif idn == 0x5:
            index = self.assignd_index_for_idn5
        cmd = ExecuteCMD.ReadDescriptor()
        cmd.assign(idn, index, selector)
        cmd_index = ExecuteCMD.enqueue(cmd)

        ExecuteCMD.send(clear_on_success=False)
        resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
        ExecuteCMD.clear()
        if index == self.serial_number:
            dumpfile("serial_string.bin",resp.data)
        elif index == self.product_string_name:
            dumpfile("product_string_name.bin",resp.data)
        #desc.from_bytes(resp.data)
        return resp.data

    def pattern_get_device_descriptor(self) -> bytearray:
        idn = DescriptorIDN.DEVICE
        selector = 0x00
        index = 0
        cmd = ExecuteCMD.ReadDescriptor()
        cmd.assign(idn, index, selector)
        cmd_index = ExecuteCMD.enqueue(cmd)

        ExecuteCMD.send(clear_on_success=False)
        resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
        ExecuteCMD.clear()
        config_desc_name = f'Device{Dut.get_instance().ufs_version:x}'
        desc = DeviceDescriptor310()
        desc.from_bytes(resp.data)
        self.manufacture_name = desc.b20_manufacturer_name
        self.product_string_name = desc.b21_product_name
        self.serial_number = desc.b22_serial_number
        self.product_revision_level = desc.b42_product_revision_level
        self.oem_id = desc.b23_oem_id

        self.device_manufacture_id = desc.w24_manufacturer_id
        self.device_manufacture_date = desc.w18_manufacturer_date
        #desc.from_bytes(resp.data)
        return resp.data

    def pattern_get_configure_descriptor(self, index:int) -> ConfigDescriptorUnion:
        idn = DescriptorIDN.CONFIGURATION
        selector = 0x00
        cmd = ExecuteCMD.ReadDescriptor()
        cmd.assign(idn, index, selector)
        cmd_index = ExecuteCMD.enqueue(cmd)

        ExecuteCMD.send(clear_on_success=False)
        resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
        ExecuteCMD.clear()
        #config_desc_name = f'Configuration{Dut.get_instance().ufs_version:x}'
        desc = ConfigDescriptor310()
        desc.from_bytes(resp.data)
        return desc

    def pattern_get_power_descriptor(self, index:int) -> PowerParametersDescriptorUnion:
        idn = DescriptorIDN.POWER
        selector = 0x00
        cmd = ExecuteCMD.ReadDescriptor()
        cmd.assign(idn, index, selector)
        cmd_index = ExecuteCMD.enqueue(cmd)

        ExecuteCMD.send(clear_on_success=False)
        resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
        ExecuteCMD.clear()
        #config_desc_name = f'Configuration{Dut.get_instance().ufs_version:x}'
        desc = PowerParametersDescriptor310()
        desc.from_bytes(resp.data)
        return desc

    def pattern_get_rpmb_unit_descriptor(self) -> RPMBUnitDescriptorUnion:
        idn = DescriptorIDN.UNIT
        index = 0xC4
        selector = 0x00
        cmd = ExecuteCMD.ReadDescriptor()
        cmd.assign(idn, index, selector)
        cmd_index = ExecuteCMD.enqueue(cmd)

        ExecuteCMD.send(clear_on_success=False)
        resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
        ExecuteCMD.clear()

        desc_name = f'RPMBUnitDescriptor{Dut.get_instance().ufs_version:x}'
        desc = RPMBUnitDescriptor310()
        desc.from_bytes(resp.data)
        
        return desc

    def pattern_get_health_descriptor(self) -> DeviceHealthDescriptorUnion:
        idn = DescriptorIDN.DEVICE_HEALTH
        index = 0x00
        selector = 0x00
        cmd = ExecuteCMD.ReadDescriptor()
        cmd.assign(idn, index, selector)
        cmd_index = ExecuteCMD.enqueue(cmd)

        ExecuteCMD.send(clear_on_success=False)
        resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
        ExecuteCMD.clear()

        
        desc = DeviceHealthDescriptor310()
        desc.from_bytes(resp.data)
        tmp_data = resp.data[5:7]
        self.wwyy_from_health_descriptor = int.from_bytes(tmp_data, 'big')
        return desc

    def pattern_get_geometry_descriptor(self) -> GeometryDescriptorUnion:
        idn = DescriptorIDN.GEOMETRY
        index = 0x00
        selector = 0x00
        cmd = ExecuteCMD.ReadDescriptor()
        cmd.assign(idn, index, selector)
        cmd_index = ExecuteCMD.enqueue(cmd)

        ExecuteCMD.send(clear_on_success=False)
        resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
        ExecuteCMD.clear()

        desc_name = f'GeometryDescriptor{Dut.get_instance().ufs_version:x}'
        
        desc = GeometryDescriptor310()
        desc.from_bytes(resp.data)
        return desc

    def set_serial_number_string(self) -> CommandResponse :
        serial_number_string = project_api.SerialNumberString()
        response = project_api.issue_C04A_to_set_serial_number_string(serial_number_string)
        return response


run = Pattern().run
if __name__ == "__main__":
    run()