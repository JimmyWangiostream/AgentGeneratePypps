import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.api.ufs_api.descriptors.configuration_desc.functions import push_write_config
from Script.api.ufs_api.defines.enum_define import QueryResponseCode
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api import shared
from Script.lib import sdk_lib as lib
import random
from Script.api.exception import *
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from typing import cast

#_sdk = shared.sdk
def check_already_written(idn: int, val: int, index: int=0, selector: int=0) -> None:
    write_attr = ExecuteCMD.WriteAttribute().assign(idn=idn, index=index, selector=selector).set_attr(val).enqueue()
    try:
        ExecuteCMD.send(clear_on_success=False, skip_response_check=True)
    except DLL_RESPONSE_ERROR:
        response = cast(api.QueryResponse, ExecuteCMD.read_response(write_attr))
        logger.info(f'response = {response.upiu.b6_query_response}')
    write_attr_rsp = cast(api.QueryResponse, ExecuteCMD.read_response(write_attr))
    if write_attr_rsp.upiu.b6_query_response != api.QueryResponseCode.PARAM_ALREADY_WRITTEN:
        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
    ExecuteCMD.clear()

def push_write_config_error_case(config_desc: api.ConfigDescriptorUnion, index: int, selector: int=0) -> int:
    cmd = ExecuteCMD.WriteDescriptor()
    cmd.assign(api.DescriptorIDN.CONFIGURATION, index, selector, config_desc.header.b0_length)
    cmd.set_desc(config_desc)
    return ExecuteCMD.enqueue(cmd)

class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        logger.flow(1, 'Read attribute 0Bh(bConfigDescrLock) value that should be 0h(Configuration Descriptor not locked)')
        bConfigDescrLock = api.read_attribute(idn = api.AttributeIDN.CONFIG_DESCR_LOCK)
        logger.info(f'attribute 0Bh(bConfigDescrLock) value = {bConfigDescrLock}')
        if bConfigDescrLock != 0x0:
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        
        logger.flow(2, 'Config WB partition')
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.b2_conf_desc_continue = 0
        config_descs[0].header.b17_write_booster_buffer_type = 1
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x1000
        push_write_config(config_descs[0], index=0)
        ExecuteCMD.send()

        logger.flow(3, 'Write attribute 0Bh(bConfigDescrLock) with value 0h(Configuration Descriptor not locked) expect response is success')
        api.write_attribute(idn = api.AttributeIDN.CONFIG_DESCR_LOCK, val = 0x0)

        logger.flow(4, 'Read attribute 0Bh(bConfigDescrLock) value that should be 0h(Configuration Descriptor not locked)')
        bConfigDescrLock = api.read_attribute(idn=api.AttributeIDN.CONFIG_DESCR_LOCK)
        logger.info(f'attribute 0Bh(bConfigDescrLock) value = {bConfigDescrLock}')
        if bConfigDescrLock != 0x0:
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        
        logger.flow(5, 'Write attribute 0Bh(bConfigDescrLock) with value 0h(Configuration Descriptor not locked) expect response is already written')
        check_already_written(idn = api.AttributeIDN.CONFIG_DESCR_LOCK, val = 0x0)

        logger.flow(6, 'Config again and response should be success')
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.b2_conf_desc_continue = 0
        config_descs[0].header.b17_write_booster_buffer_type = 1
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x1000
        push_write_config(config_descs[0], index=0)
        ExecuteCMD.send()

        logger.flow(7, 'Issue VU 0xD085 to Unlock LU Attribute Configuration-Description')
        project_api.issue_D085_unlock_LU_attribute_configuration()

        logger.flow(8, 'Read attribute 0Bh(bConfigDescrLock) value that should be 0h(Configuration Descriptor not locked)')
        bConfigDescrLock = api.read_attribute(idn=api.AttributeIDN.CONFIG_DESCR_LOCK)
        logger.info(f'attribute 0Bh(bConfigDescrLock) value = {bConfigDescrLock}')
        if bConfigDescrLock != 0x0:
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        
        logger.flow(9, 'Config again and response should be success')
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.b2_conf_desc_continue = 0
        config_descs[0].header.b17_write_booster_buffer_type = 1
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x1000
        push_write_config(config_descs[0], index=0)
        ExecuteCMD.send()

        logger.flow(10, 'Write attribute 0Bh(bConfigDescrLock) with value 1h(Configuration Descriptor locked) expect response is success')
        api.write_attribute(idn = api.AttributeIDN.CONFIG_DESCR_LOCK, val = 0x1)

        logger.flow(11, 'Read attribute 0Bh(bConfigDescrLock) value that should be 1h(Configuration Descriptor locked)')
        bConfigDescrLock = api.read_attribute(idn=api.AttributeIDN.CONFIG_DESCR_LOCK)
        logger.info(f'attribute 0Bh(bConfigDescrLock) value = {bConfigDescrLock}')
        if bConfigDescrLock != 0x1:
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        
        logger.flow(12, 'Write attribute 0Bh(bConfigDescrLock) with value 0h(Configuration Descriptor not locked) expect response is already written')
        check_already_written(idn = api.AttributeIDN.CONFIG_DESCR_LOCK, val = 0x0)        

        logger.flow(13, 'Config again and response should be failure')
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.b2_conf_desc_continue = 0
        config_descs[0].header.b17_write_booster_buffer_type = 1
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x1000
        config_rsp_index = push_write_config_error_case(config_descs[0], index=0)
        try:
            ExecuteCMD.send(clear_on_success=False, skip_response_check=True)
        except:
            response = cast(api.QueryResponse ,ExecuteCMD.read_response(config_rsp_index))
            logger.info(f'response = {response.upiu.b6_query_response}')
        config_rsp = cast(api.QueryResponse ,ExecuteCMD.read_response(config_rsp_index))
        if config_rsp.upiu.b6_query_response != api.QueryResponseCode.GENERAL_FAILURE and config_rsp.upiu.b6_query_response != api.QueryResponseCode.PARAM_ALREADY_WRITTEN:
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
        ExecuteCMD.clear()

        logger.flow(14, 'Issue VU 0xD085 to Unlock LU Attribute Configuration-Description')
        project_api.issue_D085_unlock_LU_attribute_configuration()

        logger.flow(15, 'Read attribute 0Bh(bConfigDescrLock) value that should be 0h(Configuration Descriptor not locked)')
        bConfigDescrLock = api.read_attribute(idn=api.AttributeIDN.CONFIG_DESCR_LOCK)
        logger.info(f'attribute 0Bh(bConfigDescrLock) value = {bConfigDescrLock}')
        if bConfigDescrLock != 0x0:
            raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH

        logger.flow(16, 'Config again and response should be success')
        config_descs = api.get_config_descriptors(print=True)
        config_descs[0].header.b2_conf_desc_continue = 0
        config_descs[0].header.b17_write_booster_buffer_type = 1
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x1000
        push_write_config(config_descs[0], index=0)
        ExecuteCMD.send()

        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()