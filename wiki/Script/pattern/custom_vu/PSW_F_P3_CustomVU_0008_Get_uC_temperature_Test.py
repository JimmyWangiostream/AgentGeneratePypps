import package_root
import time
from Script import api
from typing import cast, List
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.cmd_seq.response import CommandResponse
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.project_api.health_report.structs import ReadEnhanceHealthReport
from Script.project_api.structs import micron_vu_40FE



class Pattern(UFSTC):
    def push_read_attr(self, cmd_idx:List[int], idn: int, index: int=0, selector: int=0) -> None:
        cmd_idx.append(ExecuteCMD.ReadAttribute().assign(idn=idn, index=index, selector=selector).enqueue())

    def pre_process(self) -> None:
        pass

    def step1(self) -> None:
        logger.flow(1, 'Check device feature support with TOO_HIGH_TEMPERATURE and TOO_LOW_TEMPERATURE')
        featuresSupport = api.get_ufs_features_support()
        evnet_control = (featuresSupport.u4_too_high_temp << 3) | (featuresSupport.u5_too_low_temp << 4)

        logger.flow(2, 'Set event control with bit[3]:TOO_HIGH_TEMP_EN and bit[4]:TOO_LOW_TEMP_EN when device supported')
        if evnet_control != 0x0:
            api.write_attribute(idn=api.AttributeIDN.EXC_EVENT_CONTROL, val=evnet_control)
        else:
            logger.info('Device does not support TOO_HIGH_TEMPERATURE and TOO_LOW_TEMPERATURE')

        logger.flow(3, 'Idle 3 min for device stabilize')
        time.sleep(3 * 60)

        logger.flow(4, 'Issue VU 0x40FD to get uC temperature and Read attribute 18h:bDeviceCaseRoughTemperature')
        cmd_idx:List[int] = []
        project_api.push_40FD_get_uC_temp(cmd_idx=cmd_idx)
        if evnet_control != 0x0:
            self.push_read_attr(cmd_idx=cmd_idx, idn=api.AttributeIDN.DEVICE_CASE_ROUGH_TEMPERATURE)
        else:
            logger.info('Device does not support TOO_HIGH_TEMPERATURE and TOO_LOW_TEMPERATURE')
        project_api.push_40FE_to_read_enhanced_health_report(cmd_idx=cmd_idx)
        ExecuteCMD.send(clear_on_success=False)

        idx:int = 0
        response_40FD = ExecuteCMD.read_response(index=cmd_idx[idx])
        idx = idx + 1
        if evnet_control != 0x0:
            rsp = cast(api.QueryResponse, ExecuteCMD.read_response(index=cmd_idx[idx]))
            idx = idx + 1
            ret_idn, ret_index, ret_selector, attr_temp = api.parse_read_attr_rsp(rsp)
            attr_temp = cast(float, attr_temp) - 80
        response_40FE = ExecuteCMD.read_response(index=cmd_idx[idx])
        idx = idx + 1

        sign_bit = (response_40FD.data[4] & 0x04) >> 2
        value_bits = response_40FD.data[4] & 0x03
        VU_temp = -(int.from_bytes([response_40FD.data[3], value_bits], byteorder='little')) if sign_bit == 1 else int.from_bytes([response_40FD.data[3], value_bits], byteorder='little')
        VU_temp = VU_temp * 0.25
        health_report = project_api.ReadEnhanceHealthReport(response_40FE.data)
        ExecuteCMD.clear()

        logger.info(f'VU 0x40FD = {VU_temp}')
        logger.info(f'VU 0x40FE = {health_report.current_uc_temperature.value}')
        if evnet_control != 0x0:
            logger.info(f'attr var  = {attr_temp}')
        temp_list:list[float] = []
        temp_list.append(VU_temp)
        temp_list.append((float)(health_report.current_uc_temperature.value))
        if evnet_control != 0x0:
            temp_list.append((float)(attr_temp))

        logger.flow(5, 'Verify temperature should be: 1.between -40 DC to 125 DC snesor ability, 2.between 20 to 75 in normal environment, 3.Close nearly bDeviceCaseRoughTemperature(diff <= 4)')
        if VU_temp < 20 or VU_temp > 75:
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        if evnet_control != 0x0:
            temp_diff = abs(max(temp_list) - min(temp_list))
            if temp_diff > 4:
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        pass

    def post_process(self) -> None:
        pass
    

run = Pattern().run
if __name__ == "__main__":
    run()