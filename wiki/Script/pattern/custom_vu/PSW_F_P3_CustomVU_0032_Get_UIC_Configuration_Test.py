import ctypes
from typing import List as list
import package_root
from Script import api
from Script.api.util.functions import dumpfile
from Script.lib import sdk_lib
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api.exception import *

_sdk = api.shared.sdk

class testAttributeslist(api.Enum):
    PA_HIBERN8TIME = 0x15A7
    PA_TXHSG1SYNCLENGTH = 0x1552
    PA_TXHSG2SYNCLENGTH = 0x1554
    PA_TXHSG3SYNCLENGTH = 0x1556
    PA_TXHSG4SYNCLENGTH = 0x15D0
    N_DEVICEID = 0x3000
    T_CONNECTIONSTATE = 0x4020
    RX_Min_ActivateTime_Capability = 0x8F
    MPHY_RX_Advanced_Granularity_Cap = 0x98
    RX_Advanced_Min_ActivateTime_Capability = 0x9A
    RX_Hibern8Time_Capability = 0x92
    RX_Advanced_Hibern8Time_Capability = 0x99
    TX_Advanced_Hibern8Time_Capability = 0x11
    RX_LS_PREPARE_LENGTH_Capability = 0x8D
    RX_HS_G1_PREPARE_LENGTH_Capability = 0x8C
    RX_HS_G2_PREPARE_LENGTH_Capability = 0x96
    RX_HS_G3_PREPARE_LENGTH_Capability = 0x97
    RX_HS_G1_SYNC_LENGTH_Capability = 0x8B
    RX_HS_G2_SYNC_LENGTH_Capability = 0x94
    RX_HS_G3_SYNC_LENGTH_Capability = 0x95

class Pattern(UFSTC):
    def pre_process(self) -> None:
        logger.info(api.CommonPath.root)
        logger.info(api.CommonPath.development_report)
        logger.info(api.CommonPath.ini)
        logger.info(api.CommonPath.mp_tool)
        logger.info(api.CommonPath.tcsp)
        logger.info(api.CommonPath.report)
        pass

    def step1(self) -> None:
        logger.flow(1, 'Issue VU 0x4049 to get UIC configuration')
        UIC_configuration = project_api.issue_4049_get_UIC_configuration()
        dumpfile(filename='VU0x4049', data=UIC_configuration.payload)

        logger.flow(2, 'DME get MIB and PHY attribute')
        byte_list:list[int] = []
        for mib_attr_id in testAttributeslist:
            attr_type = sdk_lib.DMETarget.PEER.value | sdk_lib.AttrSetType.NORMAL.value
            value = self.dme_get_func(attr_get_type=attr_type, sel=0, mib_attr=mib_attr_id.value)
            logger.info(f'DME Get {mib_attr_id.name} = {value}.')
            if mib_attr_id == testAttributeslist.MPHY_RX_Advanced_Granularity_Cap:
                rx_adv_gran_supported = value & 0x01
                rx_adv_gran_step = (value >> 1) & 0x03
                byte_list.append(rx_adv_gran_supported)
                byte_list.append(rx_adv_gran_step)
            else:
                byte_list.append(value)
        
        result_bytearray = bytearray(byte_list)
        dumpfile(filename='UIC_from_DME_get', data=result_bytearray)
        UIC_from_DME_get = project_api.UICconfigdata(result_bytearray)

        logger.flow(3, 'Compare value between VU and DME getting')
        logger.info(f'================= [UIC configuration from VU]=================')
        project_api.print_object_info_ai(object=UIC_configuration)
        logger.info(f'================= [UIC info from DME GETTING]=================')
        project_api.print_object_info_ai(object=UIC_from_DME_get)
        if UIC_from_DME_get.payload[0:21] != UIC_configuration.payload[0:21]:
            logger.error_lb('Compare UIC configuration from VU 0x4049 with UIC info from DME getting')
            logger.error_fp('UIC configuration mismatch')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    
    def dme_get_func(self, attr_get_type:int, sel:int, mib_attr:int) -> int:
        apl_result = ctypes.c_uint32()
        apl_val = ctypes.c_uint32()
        
        _sdk._dll.cdll.DME_Get.argtypes = [ctypes.c_void_p, ctypes.c_uint32, 
                                    ctypes.c_uint32, ctypes.c_uint32,
                                    ctypes.POINTER(ctypes.c_uint32), 
                                    ctypes.POINTER(ctypes.c_uint32)]
        _sdk._dll.cdll.DME_Get.restype = ctypes.c_ubyte
        _sdk._dll.errcode = _sdk._dll.cdll.DME_Get(
            _sdk._dll.sdk,
            ctypes.c_uint32(attr_get_type),
            ctypes.c_uint32(sel),
            ctypes.c_uint32(mib_attr),
            ctypes.byref(apl_result),
            ctypes.byref(apl_val)
        )
        return apl_val.value

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()