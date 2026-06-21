import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
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

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.write_once_flag_list = [api.FlagIDN.PERMANENT_WP_EN,api.FlagIDN.PERMANENTLY_DIS_FW_UPDATE]
        self.write_once_attribute_list = [api.AttributeIDN.OUT_OF_ORDER_DATA_EN,api.AttributeIDN.CONFIG_DESCR_LOCK]

    def step1(self) -> None:
        
        idn = 0
        for index in range (len(self.write_once_flag_list)):
            idn = self.write_once_flag_list[index]
            logger.flow(2, 'Host issue read flag idn = %d' % idn)
            read_flag = ExecuteCMD.ReadFlag().assign(idn).enqueue()
            ExecuteCMD.send(clear_on_success=False,skip_response_check=True)
            rsp = cast(api.QueryResponse, ExecuteCMD.read_response(read_flag))
            idn, index, selector, val = api.parse_flag_rsp(rsp)
            logger.info(f'{idn=},{index=},{selector=},{val=}')
            ExecuteCMD.clear()
            logger.flow(3, 'Host issue set flag idn = %d' % idn)
            set_flag = ExecuteCMD.SetFlag().assign(idn).enqueue()
            ExecuteCMD.send(clear_on_success=False,skip_response_check=True)
            rsp = cast(api.QueryResponse, ExecuteCMD.read_response(set_flag))
            idn, index, selector, val = api.parse_flag_rsp(rsp)
            logger.info(f'{idn=},{index=},{selector=},{val=}')
            ExecuteCMD.clear()
            logger.flow(4, 'Host issue read flag idn = %d' % idn)
            read_flag = ExecuteCMD.ReadFlag().assign(idn).enqueue()
            ExecuteCMD.send(clear_on_success=False,skip_response_check=True)
            rsp = cast(api.QueryResponse, ExecuteCMD.read_response(read_flag))
            idn, index, selector, val = api.parse_flag_rsp(rsp)
            logger.info(f'{idn=},{index=},{selector=},{val=}')            
            if val != 1:
                logger.error_lb(f'Host issue set flag ')
                logger.error_fp(f'expect value be 1, but value = %d' % val)
                raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
            ExecuteCMD.clear()
            #should setflag fail
            set_flag = ExecuteCMD.SetFlag().assign(idn).enqueue()
            try:
                ExecuteCMD.send(clear_on_success=False,skip_response_check=True)
                response = ExecuteCMD.read_response(set_flag)
            except DLL_RESPONSE_ERROR:
                response = ExecuteCMD.read_response(set_flag)

            rsp = cast(api.QueryResponse, ExecuteCMD.read_response(set_flag))
            idn, index, selector, val = api.parse_flag_rsp(rsp)
            if not (rsp.upiu.b6_query_response == QueryResponseCode.PARAM_ALREADY_WRITTEN):
                logger.error_lb(f'Host issue set flag (write once) after already set')
                logger.error_fp(f'expect response PARAM_ALREADY_WRITTEN, but response = %d' % rsp.upiu.b6_query_response)
                raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
            ExecuteCMD.clear()
        
            project_api.issue_D083_clean_up_write_once()
            read_flag = ExecuteCMD.ReadFlag().assign(idn).enqueue()
            ExecuteCMD.send(clear_on_success=False,skip_response_check=True)
            rsp = cast(api.QueryResponse, ExecuteCMD.read_response(read_flag))
            idn, index, selector, val = api.parse_flag_rsp(rsp)
            logger.info(f'{idn=},{index=},{selector=},{val=}')
            ExecuteCMD.clear()
            if val != 0:
                logger.error_lb(f'Host issue Vendor cmd D083 to clean write once flags or attributes ')
                logger.error_fp(f'expect value recover to 0, but value = %d' % val)
                raise SIGHTING_FAIL_CLEAN_WRITE_ONCE_ATTRIBUTE_FLAG
            
        for index in range (len(self.write_once_attribute_list)):
            idn = self.write_once_attribute_list[index]
            read_attribute = ExecuteCMD.ReadAttribute().assign(idn).enqueue()
            ExecuteCMD.send(clear_on_success=False,skip_response_check=True)
            rsp = cast(api.QueryResponse, ExecuteCMD.read_response(read_flag))
            idn, index, selector, val = api.parse_read_attr_rsp(rsp)
            logger.info(f'{idn=},{index=},{selector=},{val=}')
            ExecuteCMD.clear()   
            origin_val = val         
            if val == 0:
                set_val = 1
            else:
                set_val = 0
            write_attribute = ExecuteCMD.WriteAttribute().assign(idn).set_attr(set_val).enqueue()
            ExecuteCMD.send(clear_on_success=False,skip_response_check=True)
            rsp = cast(api.QueryResponse, ExecuteCMD.read_response(set_flag))
            idn, index, selector, val = api.parse_read_attr_rsp(rsp)
            logger.info(f'{idn=},{index=},{selector=},{val=}')   
            if val != set_val:
                logger.error_lb(f'Host issue read attribute')
                logger.error_fp(f'expect value be %d, but value = %d' % (set_val,val))
                raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
            ExecuteCMD.clear()
            read_attribute = ExecuteCMD.ReadAttribute().assign(idn).enqueue()
            ExecuteCMD.send(clear_on_success=False,skip_response_check=True)
            rsp = cast(api.QueryResponse, ExecuteCMD.read_response(read_flag))
            idn, index, selector, val = api.parse_read_attr_rsp(rsp)
            logger.info(f'{idn=},{index=},{selector=},{val=}')
            ExecuteCMD.clear()
            #should setflag fail
            write_attribute = ExecuteCMD.WriteAttribute().assign(idn).set_attr(origin_val).enqueue()
            try:
                ExecuteCMD.send(clear_on_success=False,skip_response_check=True)
                response = ExecuteCMD.read_response(write_attribute)
            except DLL_RESPONSE_ERROR:
                response = ExecuteCMD.read_response(write_attribute)
                
            rsp = cast(api.QueryResponse, ExecuteCMD.read_response(write_attribute))
            if not (rsp.upiu.b6_query_response == QueryResponseCode.PARAM_ALREADY_WRITTEN):
                logger.error_lb(f'Host issue set flag (write once) after already set')
                logger.error_fp(f'expect response PARAM_ALREADY_WRITTEN, but response = %d' % rsp.upiu.b6_query_response)
                raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
            ExecuteCMD.clear()
        
            project_api.issue_D083_clean_up_write_once()
            read_attribute = ExecuteCMD.ReadAttribute().assign(idn).enqueue()
            ExecuteCMD.send(clear_on_success=False,skip_response_check=True)
            rsp = cast(api.QueryResponse, ExecuteCMD.read_response(read_flag))
            idn, index, selector, val = api.parse_read_attr_rsp(rsp)
            logger.info(f'{idn=},{index=},{selector=},{val=}')
            ExecuteCMD.clear()
            if val != origin_val:
                logger.error_lb(f'Host issue Vendor cmd D083 to clean write once flags or attributes ')
                logger.error_fp(f'expect value recover to origin_val = %d, but value = %d' % (origin_val, val))
                raise SIGHTING_FAIL_CLEAN_WRITE_ONCE_ATTRIBUTE_FLAG

        pass

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()