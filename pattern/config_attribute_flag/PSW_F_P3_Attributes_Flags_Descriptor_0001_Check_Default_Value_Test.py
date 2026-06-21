import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
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
import pandas
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
    
    def pre_process(self) -> None:
        
        target_file_name = "UfsRegisterModePageDmeReport_Cygnus"
        target_sheet_name = "Attributes_Flags"
        logger.info(f'Get Sheet data target xlsx ={target_file_name}, sheet = {target_sheet_name}')
        load_data_sheet = self.load_xlsx_sheet(target_file_name,target_sheet_name)
        key_word_to_get = "Flags"
        flag_sheet, last_line_of_sheet = self.extraction_xlsx(load_data_sheet, key_word_to_get)
        compare_fail = self.check_if_sheet_correct_attr_flag(key_word_to_get, flag_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error
        key_word_to_get = "Device Attributes"
        device_attribute_sheet, last_line_of_sheet = self.extraction_xlsx(load_data_sheet,key_word_to_get,last_line_of_sheet)
        compare_fail = self.check_if_sheet_correct_attr_flag(key_word_to_get, device_attribute_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error
        special_attribute_per_lun, last_line_of_sheet = self.extraction_xlsx_per_lun(load_data_sheet, "IDN", last_line_of_sheet)
        compare_fail =self.check_if_sheet_correct_special_attribute_per_lun(special_attribute_per_lun)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error
        pass
        self.pattern_get_device_descriptor()
        target_sheet_name = "Descriptors"
        logger.info(f'Get Sheet data target xlsx ={target_file_name}, sheet = {target_sheet_name}')
        load_data_sheet = self.load_xlsx_sheet(target_file_name,target_sheet_name)  
        key_word_to_get = "Device Descriptor" 
        device_descriptor_sheet,last_line_of_sheet = self.extraction_descriptor_xlsx(load_data_sheet, key_word_to_get,0,"device_descriptor")
        compare_fail = self.check_if_sheet_correct_descriptor(0, device_descriptor_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error
        key_word_to_get = "Configuration Descriptor(Device)" 
        configuration_descriptor_sheet,last_line_of_sheet = self.extraction_descriptor_xlsx(load_data_sheet, key_word_to_get, last_line_of_sheet,"config_descriptor")
        compare_fail = self.check_if_sheet_correct_descriptor(1, configuration_descriptor_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error

        key_word_to_get = "Geometry Descriptor" 
        geometry_descriptor_sheet,last_line_of_sheet = self.extraction_descriptor_xlsx(load_data_sheet, key_word_to_get, last_line_of_sheet,"geometry_descriptor")
        compare_fail = self.check_if_sheet_correct_descriptor(7, geometry_descriptor_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error

        key_word_to_get = "RPMB Unit Descriptor" 
        rpmb_unit_descriptor_sheet,last_line_of_sheet = self.extraction_descriptor_xlsx(load_data_sheet, key_word_to_get, last_line_of_sheet)
        compare_fail = self.check_if_sheet_correct_descriptor(2, rpmb_unit_descriptor_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error

        key_word_to_get = "Power Parameters Descriptor" 
        power_parameters_descriptor_sheet,last_line_of_sheet = self.extraction_descriptor_xlsx(load_data_sheet, key_word_to_get, last_line_of_sheet)
        compare_fail = self.check_if_sheet_correct_descriptor(8, power_parameters_descriptor_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error

        key_word_to_get = "Interconnect Descriptor" 
        interconnect_descriptor_sheet,last_line_of_sheet = self.extraction_descriptor_xlsx(load_data_sheet, key_word_to_get, last_line_of_sheet)
        compare_fail = self.check_if_sheet_correct_descriptor(4, interconnect_descriptor_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error

        key_word_to_get = "Manufacturer Name String Descriptor" 
        manufacturer_name_string_descriptor_sheet, last_line_of_sheet = self.extraction_descriptor_xlsx(load_data_sheet, key_word_to_get,last_line_of_sheet,"manufacturer_name")
        self.assignd_index_for_idn5 = self.manufacture_name
        compare_fail = self.check_if_sheet_correct_descriptor(5, manufacturer_name_string_descriptor_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error

        key_word_to_get = "Product Name String Descriptor" 
        product_name_string_descriptor_sheet, last_line_of_sheet = self.extraction_descriptor_xlsx(load_data_sheet, key_word_to_get,last_line_of_sheet,"product_name")
        self.assignd_index_for_idn5 = self.product_string_name
        compare_fail = self.check_if_sheet_correct_descriptor(5, product_name_string_descriptor_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error

        key_word_to_get = "OEM ID String Descriptor" 
        oem_id_string_descriptor_sheet, last_line_of_sheet = self.extraction_descriptor_xlsx(load_data_sheet, key_word_to_get,last_line_of_sheet,"oem_id")
        self.assignd_index_for_idn5 = self.oem_id
        compare_fail = self.check_if_sheet_correct_descriptor(5, oem_id_string_descriptor_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error

        key_word_to_get = "Serial Number String Descriptor" 
        serial_number_string_descriptor_sheet, last_line_of_sheet = self.extraction_descriptor_xlsx(load_data_sheet, key_word_to_get,last_line_of_sheet,"serial_number")
        self.assignd_index_for_idn5 = self.serial_number
        compare_fail = self.check_if_sheet_correct_descriptor(5, serial_number_string_descriptor_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error

        key_word_to_get = "Product Revision Level String Descriptor" 
        product_revision_level_string_descriptor_sheet, last_line_of_sheet = self.extraction_descriptor_xlsx(load_data_sheet, key_word_to_get,last_line_of_sheet,"product_revision")
        self.assignd_index_for_idn5 = self.product_revision_level
        compare_fail = self.check_if_sheet_correct_descriptor(5, product_revision_level_string_descriptor_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error

        key_word_to_get = "Device Health Descriptor" 
        device_health_descriptor_sheet, last_line_of_sheet = self.extraction_descriptor_xlsx(load_data_sheet, key_word_to_get,last_line_of_sheet,"device_health")                
        compare_fail = self.check_if_sheet_correct_descriptor(9, device_health_descriptor_sheet)
        self.pattern_error = compare_fail if compare_fail else self.pattern_error        
        if self.pattern_error:
            logger.error_fp(f'compare fail')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL  
        pass

    def modify_answer_tmp(self,answer:CompareDescriptor) -> int:
        if "bSupportedSecRTypes" in answer.name:
            logger.info(f'modify answer {answer.name} to 15')
            return 15
        elif "bMaxContexIDNumber" in answer.name:
            logger.info(f'modify answer {answer.name} to 15')
            return 15
        else:
            return answer.target_value

    def check_if_sheet_correct_descriptor(self,idn:int, answer_list:list[CompareDescriptor]) -> bool:
        pattern_fail = False
        fail_result = False
        logger.info(f"check idn {idn} descriptor")
        descriptor = self.pattern_get_descriptor(idn)
        byte_len = 1
      
        error_msg = ""
        for answer in answer_list:
            logger.info(f"answer name = {answer.name}, answer offset = {answer.offset}, answer action = {answer.action}, answer.value = {answer.target_value}")        
            if answer.action == Action.TBD:
                logger.info(f"TBD")
                fail_result = False
            else:
                if answer.name.startswith('w'):
                    byte_len = 2
                elif answer.name.startswith('d'):
                    byte_len = 4
                elif answer.name.startswith('q'):
                    byte_len = 8                    
                else:
                    byte_len = 1
                if answer.name == 'bcdUniproVersion':
                    byte_len = 2
                elif answer.name == 'bcdMphyVersion':
                    byte_len = 2
                elif answer.name == 'UC[':
                    byte_len = 2                    
                descriptor_answer = int.from_bytes(descriptor[answer.offset:answer.offset+byte_len], byteorder='big')
                answer.target_value = self.modify_answer_tmp(answer)
                if (answer.target_value != descriptor_answer):
                    error_msg = f'compare descriptor fail, idn = {idn}, offset = {answer.offset}, read value {descriptor_answer} != expected value {answer.target_value}'
                    logger.error(error_msg)
                    fail_result = True
                else:
                    fail_result = False
            pattern_fail = fail_result if fail_result else pattern_fail 
        return pattern_fail
    
    

    def compare_flag_or_attribute_correct(self,mode:int, expected_result:Action, idn:int, expected_val:int,index:int = 0, selector:int = 0) -> bool:
        compare_fail = False
        result_val = 0
        error_msg = ""
        rsp = QueryResponse()
        if mode == 0:
            error_msg = "read flag, "
            rsp, result_val = self.get_flag(idn,index,selector)
        elif mode == 1:
            error_msg = "read attribute, "
            rsp, result_val = self.get_attribute(idn,index,selector)
        if expected_result == Action.COMPARE:
            if result_val != expected_val:
                error_msg += f'compare value fail, idn = {idn}, index = {index}, selector = {selector}, read value {result_val} != expected value {expected_val}'
                logger.error(error_msg)
                self.error_msg_for_debug += error_msg
                compare_fail = True
            if rsp.upiu.b6_query_response != 0x0:
                error_msg += f'idn = {idn}, index = {index}, selector = {selector}, read query rsp is {rsp.upiu.b6_query_response} rsp = {rsp.upiu.b6_query_response} != PASS'
                logger.error(error_msg)
                self.error_msg_for_debug += error_msg
                compare_fail = True
        elif expected_result == Action.NOTREADABLE:
            if rsp.upiu.b6_query_response != 0xF6:
                error_msg += f'idn = {idn}, index = {index}, selector = {selector}, read query rsp is {rsp.upiu.b6_query_response} != NOT_READABLE(0xF6)'
                logger.error(error_msg)
                self.error_msg_for_debug += error_msg
                compare_fail = True
        elif expected_result == Action.NOTWRITEABLE:                
            if rsp.upiu.b6_query_response != 0xF7:
                error_msg += f'idn = {idn}, index = {index}, selector = {selector}, read query rsp is {rsp.upiu.b6_query_response} != NOT_WRITEABLE(0xF7)'
                logger.error(error_msg)
                self.error_msg_for_debug += error_msg
                compare_fail = True                
        return compare_fail

    def check_if_sheet_correct_special_attribute_per_lun(self, answer_list:list[CompareAttributePerLun]) -> bool:
        pattern_fail = False
        for answer in answer_list:
            logger.info(f"answer name = {answer.name}, answer idn = {answer.idn}, answer action = {answer.action}, answer.lun_id = {answer.lun_id}")        
            result = self.compare_flag_or_attribute_correct(1,answer.action,answer.idn, answer.target_value,answer.lun_id, answer.selector)
            pattern_fail = result if result else pattern_fail
        return pattern_fail        
    def check_if_sheet_correct_attr_flag(self, compare_topic:str, answer_list:list[CompareFlagAttribute]) -> bool:
        pattern_fail = False
        read_flag_or_attribute = 0 # 0: flag , 1: attribute
        if "flag" in compare_topic.lower():
            read_flag_or_attribute = 0
            logger.info("compare flags")
        elif "attribute" in compare_topic.lower():
            read_flag_or_attribute = 1
            logger.info("compare attribute")
        for answer in answer_list:
            logger.info(f"answer name = {answer.name}, answer idn = {answer.idn}, answer action = {answer.action}")
            if answer.action == Action.TBD:
                logger.info(f"TBD")
            else:
                result = self.compare_flag_or_attribute_correct(read_flag_or_attribute,answer.action,answer.idn, answer.target_value)
                pattern_fail = result if result else pattern_fail
        return pattern_fail


    def __find_target_xlsx(self, target_file_name:str) -> str:
        logger.info(f'[Execute Function] __find_target_xlsx(), target={target_file_name}')
        file_list = os.listdir(self.xlsx_root)
        for xlsx_file in file_list:
            if target_file_name.lower() in xlsx_file.lower() and (xlsx_file.endswith('.xlsx') or xlsx_file.endswith('.xlsm')):
                logger.info(f'Found: {xlsx_file}')
                return xlsx_file
        logger.error(f'cant find {target_file_name} xlsx in {self.xlsx_root}')    
        raise api.PATTERN_ASSERT_UNEXPECTED_CONDITION    
            
    def load_xlsx_sheet(self, target_file_name:str, sheet_name:str) -> pandas.DataFrame:
        self.xlsx_root = os.path.dirname(os.path.abspath(__file__))
        self.xlsx_file_name:str = self.__find_target_xlsx(target_file_name)
        self.xlsx_file:str = f'{self.xlsx_root}//{self.xlsx_file_name}'
        try:
            logger.info(f'Read all sheet name in xlsx')
            xlsx = pandas.ExcelFile(self.xlsx_file)
        except Exception as e:
            logger.error(e)    
            raise api.PATTERN_ASSERT_UNEXPECTED_CONDITION    
        found_sheet = False
        for sheet in xlsx.sheet_names:
            if sheet_name.lower() in str(sheet).lower():
                found_sheet = True
                logger.info(f'Read sheet: {sheet_name}')
                break
        if not found_sheet:
            logger.error(f'Can not find sheet name contains {sheet_name}')
            raise api.PATTERN_ASSERT_UNEXPECTED_CONDITION
        try:
            xlsx_data = pandas.read_excel(self.xlsx_file, sheet_name=sheet_name, header=None)
        except Exception as e:
            logger.error(f'Can not find sheet name contains {sheet_name}')
            raise api.PATTERN_ASSERT_UNEXPECTED_CONDITION
        else:
            return xlsx_data
        pass
    def extraction_xlsx_per_lun(self, sheet_data:pandas.DataFrame, key_word_start:str, last_line_of_last_sheet:int = 0) -> Tuple[list[CompareAttributePerLun], int]:
        get_target_item = False
        start_extrack = False
        leave_extrack = False
        return_list = []
        line_count = 0
        oneanwser = CompareAttributePerLun()
        oneanwser.target_value = 0
        for index, row in sheet_data.iterrows():
            line_count = index
            line_count = cast(int, index)
            if line_count < last_line_of_last_sheet:
                logger.info(f'now line {line_count} < threshold {last_line_of_last_sheet}')
                continue
            if leave_extrack:
                logger.info(f'get nan data, break outer loop')
                break
            print(f"Index: {index}")
            for col_index, value in enumerate(row):
                if pandas.isna(value) and col_index == 0:
                    logger.info(f'get nan data, break inner loop')
                    leave_extrack = True
                    break         
                if pandas.isna(value):
                    logger.info(f'go next row')
                    break
                if col_index == 0 and value.lower() == key_word_start.lower():
                    get_target_item = True
                if start_extrack:
                    if col_index == 0:
                        oneanwser.idn = int(value,16)
                    elif col_index == 1:
                        oneanwser.name = str(value)
                    elif col_index >= 2:
                        lun_id = col_index - 2
                        if 'tbd' in str(value).lower():
                            oneanwser.action = Action.TBD
                            return_list.append(oneanwser)
                        elif 'not readable' in str(value).lower():
                            oneanwser.action = Action.NOTREADABLE
                            return_list.append(oneanwser)
                        elif 'not write' in str(value).lower():
                            oneanwser.action = Action.NOTWRITEABLE
                            return_list.append(oneanwser)
                        else:
                            oneanwser.action = Action.COMPARE
                            if ('[' in str(value) and ']' in str(value)):
                                logger.info('get value as list, as a special selector rule')
                                list_value = value.split('[')[1]
                                list_value = list_value.split(']')[0]
                                for selector, expected_value in enumerate(list_value.split(',')):
                                    logger.info(f"Index: {selector}, Value: {expected_value}")
                                    oneanwser.lun_id = lun_id
                                    if "wcontextconf" in oneanwser.name.lower():
                                        oneanwser.selector = selector + 1 # due to spec start valid selector value = 1
                                    else:
                                        oneanwser.selector = selector
                                    if expected_value.lower().startswith('0x'):
                                        oneanwser.target_value = int(expected_value,16)
                                    else:
                                        oneanwser.target_value = int(expected_value)
                                    tmpanwser = CompareAttributePerLun()
                                    tmpanwser.idn = oneanwser.idn
                                    tmpanwser.lun_id = oneanwser.lun_id
                                    tmpanwser.name = oneanwser.name
                                    tmpanwser.selector = oneanwser.selector
                                    tmpanwser.target_value = oneanwser.target_value
                                    tmpanwser.action = oneanwser.action
                                    return_list.append(tmpanwser)                                                                           

                            else:
                                oneanwser.selector = 0
                                oneanwser.lun_id = lun_id
                                if str(value).lower().startswith('0x'):
                                    oneanwser.target_value = int(value,16)
                                else:
                                    oneanwser.target_value = int(value)
                                tmpanwser = CompareAttributePerLun()
                                tmpanwser.idn = oneanwser.idn
                                tmpanwser.lun_id = oneanwser.lun_id
                                tmpanwser.name = oneanwser.name
                                tmpanwser.selector = oneanwser.selector
                                tmpanwser.target_value = oneanwser.target_value
                                tmpanwser.action = oneanwser.action
                                return_list.append(tmpanwser)
                        logger.info(f'extrack next items')
                        #break
                print(f"Column {col_index}: {value}")  
                if get_target_item and col_index == 0 and value == "IDN":
                    start_extrack = True
                    logger.info(f'go next row to extrack items')
                    break
        return return_list, line_count
    def check_if_name_included_special_skip_rule(self, compare_str:str, rule:str)->bool:
        device_descriptor_list = ["bNumberLU", "bBootEnable", "dPSAMaxDataSize","wManufacturerID"]
        config_descriptor_list = ["bBootEnable"]
        product_name_string_list = ["bLength","bDescriptorType","UC[0]","UC[1]","UC[2]","UC[3]","UC[4]","UC[5]","UC[6]","UC[7]","UC[8]","UC[9]","UC[10]","UC[11]"\
                                    ,"UC[12]","UC[13]","UC[14]","UC[15]"]
        geometry_descriptor_list = ["qTotalRawDeviceCapacity","dSegmentSize","dEnhanced1MaxNAllocU","dWriteBoosterBufferMaxNAllocUnits","wEnhanced1CapAdjFac"]
        device_health_descriptor_list = ["ExhaustedLifeEM1", "ExhaustedLifeSystem", "VendorPropInfoTlcEC","ExhaustedLifeNormal"]
        oem_id_list = ["bLength","UC[0]","UC[1]","UC[2]","UC[3]","UC[4]","UC[5]"]
        serial_number_list = ["bLength"]
        product_revision_level_string_list = ["bLength","bDescriptorType","UC[0]","UC[1]","UC[2]","UC[3]"]
        manufacturer_name_list = ["UC[0]","UC[1]","UC[2]","UC[3]","UC[4]","UC[5]","UC[6]","UC[7]"]
        compare_list = []
        
        if "device_descriptor" in rule:
            compare_list = device_descriptor_list
        elif "config_descriptor" in rule:
            compare_list = config_descriptor_list
        elif "product_name" in rule:
            compare_list = product_name_string_list        
        elif "geometry_descriptor" in rule:
            compare_list = geometry_descriptor_list          
        elif "device_health" in rule:
            compare_list = device_health_descriptor_list    
        elif "oem_id" in rule:
            compare_list = oem_id_list  
        elif "serial_number" in rule:
            compare_list = serial_number_list     
        elif "product_revision" in rule:
            compare_list = product_revision_level_string_list  
        elif "manufacturer_name" in rule:
            compare_list = manufacturer_name_list
        else:
            compare_list = []                   
        for keyword in compare_list:
            if keyword in compare_str:
                logger.info(f"{keyword} in {compare_str}, shall skip")
                return True
        return False


    def extraction_descriptor_xlsx(self, sheet_data:pandas.DataFrame, key_word_start:str, last_line_of_last_sheet:int = 0, rule:str = "") -> Tuple[list[CompareDescriptor], int]:
        get_target_item = False
        start_extrack = False
        leave_extrack = False
        return_list:list[CompareDescriptor] = []
        line_count = 0
        for index, row in sheet_data.iterrows():
            line_count = index
            line_count = cast(int, index)
            if line_count < last_line_of_last_sheet:
                logger.info(f'now line {line_count} < threshold {index}')
                continue
            if leave_extrack:
                logger.info(f'get nan data, break outer loop')
                break
            print(f"Index: {index}")
            oneanwser = CompareDescriptor()
            oneanwser.target_value = 0
            for col_index, value in enumerate(row):
                if pandas.isna(value) and col_index == 0 and (len(return_list) > 0):
                    logger.info(f'get nan data, break inner loop')
                    leave_extrack = True
                    break         
                if pandas.isna(value):
                    logger.info(f'go next row')
                    break
                if col_index == 0 and str(value).lower() == key_word_start.lower():
                    get_target_item = True
                if start_extrack:
                    if col_index == 0:
                        if str(value).lower().startswith('0x'):
                            oneanwser.offset = int(value,16)
                        else:
                            oneanwser.offset = int(value)                        
                    elif col_index == 1:
                        oneanwser.name = str(value)
                    elif col_index == 2:
                        print(str(value).lower())
                        if len(return_list) >= 2 and ("string" in key_word_start.lower() or "name" in key_word_start.lower()):
                            if 'tbd' in str(value).lower() or "'x'" == str(value).lower() or "'na'" == str(value).lower():
                                oneanwser.action = Action.TBD
                            else:
                                oneanwser.action = Action.COMPARE
                                tmp_value = value.strip("'\'")

                                tmp_value = bytes(tmp_value, "utf-8").decode("unicode_escape")
                                print(f'tmp value = {tmp_value}')
                                decode_value = ord(tmp_value)
                                print(f'decode_value = {decode_value}')
                                oneanwser.target_value = decode_value
                            # special rule skip
                            if self.check_if_name_included_special_skip_rule(oneanwser.name,rule):
                                oneanwser.action = Action.TBD
                            return_list.append(oneanwser)
                            logger.info(f'extrack next items')  
                            break                                                              
                        else:
                            if 'tbd' in str(value).lower() or "'x'" == str(value).lower() or "'na'" == str(value).lower():
                                oneanwser.action = Action.TBD
                            elif 'not readable' in str(value).lower():
                                oneanwser.action = Action.NOTREADABLE
                            elif 'not write' in str(value).lower():
                                oneanwser.action = Action.NOTWRITEABLE
                            else:
                                oneanwser.action = Action.COMPARE
                                if str(value).lower().startswith('0x'):
                                    oneanwser.target_value = int(value,16)
                                else:
                                    oneanwser.target_value = int(value)
                            # special rule skip
                            if self.check_if_name_included_special_skip_rule(oneanwser.name,rule):
                                oneanwser.action = Action.TBD                                    
                            return_list.append(oneanwser)
                            logger.info(f'extrack next items')
                            break
                print(f"Column {col_index}: {value}")  
                if get_target_item and col_index == 0 and (not start_extrack):
                    start_extrack = True
                    logger.info(f'go next row to extrack items')
                    break
        return return_list, line_count

    def extraction_xlsx(self, sheet_data:pandas.DataFrame, key_word_start:str, last_line_of_last_sheet:int = 0) -> Tuple[list[CompareFlagAttribute], int]:
        get_target_item = False
        start_extrack = False
        leave_extrack = False
        return_list = []
        line_count = 0
        for index, row in sheet_data.iterrows():
            line_count = index
            line_count = cast(int, index)
            if line_count < last_line_of_last_sheet:
                logger.info(f'now line {line_count} < threshold {index}')
                continue
            if leave_extrack:
                logger.info(f'get nan data, break outer loop')
                break
            print(f"Index: {index}")
            oneanwser = CompareFlagAttribute()
            oneanwser.target_value = 0
            for col_index, value in enumerate(row):
                if pandas.isna(value) and col_index == 0:
                    logger.info(f'get nan data, break inner loop')
                    leave_extrack = True
                    break         
                if pandas.isna(value):
                    logger.info(f'go next row')
                    break
                if col_index == 0 and str(value).lower() == key_word_start.lower():
                    get_target_item = True
                if start_extrack:
                    if col_index == 0:
                        oneanwser.idn = int(value,16)
                    elif col_index == 1:
                        oneanwser.name = str(value)
                    elif col_index == 2:
                        if 'tbd' in str(value).lower():
                            oneanwser.action = Action.TBD
                        elif 'not readable' in str(value).lower():
                            oneanwser.action = Action.NOTREADABLE
                        elif 'not write' in str(value).lower():
                            oneanwser.action = Action.NOTWRITEABLE
                        else:
                            oneanwser.action = Action.COMPARE
                            if str(value).lower().startswith('0x'):
                                oneanwser.target_value = int(value,16)
                            else:
                                oneanwser.target_value = int(value)
                        return_list.append(oneanwser)
                        logger.info(f'extrack next items')
                        break
                print(f"Column {col_index}: {value}")  
                if get_target_item and col_index == 0 and value.lower() == "idn":
                    start_extrack = True
                    logger.info(f'go next row to extrack items')
                    break
        return return_list, line_count
    def step1(self) -> None:  
        rsp, flag = self.get_flag(0x1)
        attr = self.get_attribute(0)
        shared.param.gDevice
        device_desc = self.pattern_get_device_descriptor()
        config_desc = self.pattern_get_configure_descriptor(0)
        health_desc = self.pattern_get_health_descriptor()
        # wait for eng2 vu
        # response = self.set_serial_number_string()
        pass
    def post_process(self) -> None:
        pass

    def load_xlsx_get_info(self) -> None:
        pass

    def get_flag(self, idn:int, index:int = 0, selector:int = 0) -> Tuple[QueryResponse, int]:
        #flag_value = api.read_flag(idn=idn)
        cmd_idx = ExecuteCMD.ReadFlag().assign(idn=idn, index=index, selector=selector).enqueue()
        try:
            ExecuteCMD.send(clear_on_success=False)
            rsp = cast(QueryResponse, ExecuteCMD.read_response(cmd_idx))
        except DLL_RESPONSE_ERROR:
            logger.info('send command error')
            rsp = cast(QueryResponse, ExecuteCMD.read_response(cmd_idx))
            
        ret_idn, ret_index, ret_selector, ret_val = api.parse_flag_rsp(rsp)
        if ret_idn != idn:
            raise SPEC_ASSERT_UFS_RSP_IDN_NOT_MATCH
        if ret_index != index:
            raise SPEC_ASSERT_UFS_RSP_IDX_NOT_MATCH
        if ret_selector != selector:
            raise SPEC_ASSERT_UFS_RSP_SELECTOR_NOT_MATCH
        ExecuteCMD.clear()
        logger.info(f'read flag idn = {idn}, value = {ret_val}')
        return rsp, ret_val

    def get_attribute(self, idn:int, index:int = 0, selector:int = 0) -> Tuple[QueryResponse, int]:
        #attr_value = api.read_attribute(idn=idn)
        read_attr = ExecuteCMD.ReadAttribute().assign(idn=idn, index=index, selector=selector).enqueue()
        try:
            ExecuteCMD.send(clear_on_success=False)
            rsp = cast(QueryResponse, ExecuteCMD.read_response(read_attr))
        except DLL_RESPONSE_ERROR:
            logger.info('send command error')
            rsp = cast(QueryResponse, ExecuteCMD.read_response(read_attr))        
        ExecuteCMD.clear()
        ret_idn, ret_index, ret_selector, ret_val = api.parse_read_attr_rsp(rsp)
        if ret_idn != idn:
            raise SPEC_ASSERT_UFS_RSP_IDN_NOT_MATCH
        if ret_index != index:
            raise SPEC_ASSERT_UFS_RSP_IDX_NOT_MATCH
        if ret_selector != selector:
            raise SPEC_ASSERT_UFS_RSP_SELECTOR_NOT_MATCH        
        logger.info(f'read attribute idn = {idn}, value = {ret_val}')
        return rsp, ret_val

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

        #desc_name = f'DeviceHealthDescriptor{Dut.get_instance().ufs_version:x}'
        
        desc = DeviceHealthDescriptor310()
        desc.from_bytes(resp.data)
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