import inspect
from typing import cast, List,Dict

from Script.api import shared, cmd_seq as ExecuteCMD

import random
from Script.project_api.structs import micron_vendor_cmd,micron_vu_D017, micron_vu_C071, micron_vu_404B, micron_vu_4071
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.project_api.sgm_vu.structs import C071_param, VU_4071_struct, D017_param
from Script.api.cmd_seq.response import CommandResponse
from Script.api.ufs_api.vendor_cmd import get_vb_info

_log = shared.logger

def issue_D017_to_create_SGM_fail(param:D017_param) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D017()
    vu.b0_opcode.value = 0x17
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 4096 #don't care
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)  #don't care
    vu.die.value = param.die.value
    vu.plane.value = param.plane.value
    vu.block.value = param.block.value
    vu.error_inject_enable.value = param.error_inject_enable.value
    vu.scan_type.value = param.scan_type.value
    vu.first_low_vt_scan.value = param.first_low_vt_scan.value
    vu.touch_up.value = param.touch_up.value
    vu.low_vt_re_scan.value = param.low_vt_re_scan.value
    vu.high_vt_scan.value = param.high_vt_scan.value
    vu.switch.value = param.switch.value
    vu.index.value = param.index.value
    send_no_data_vcmd(micron_vendor_cmd=vu)

    return 
def issue_4071_to_get_SGD_scan_parameter(isSGS:int = 1) -> VU_4071_struct:
    vu = micron_vu_4071()
    vu.b0_opcode.value = 0x71
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096 
    vu.d4_random_stamp.value = random.randint(0x1, 0x10000000) 
    vu.isSGS.value = isSGS 
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu)
    return VU_4071_struct(payload[0:3240])

def issue_404B_to_erase_with_SGM_enabled(input_vb:int, enable_retirement:int) -> int:
    vu = micron_vu_404B()
    vu.b0_opcode.value = 0x4B
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)  #don't care
    vu.input_vb.value = input_vb  #is this right?
    vu.enable_retirement.value = enable_retirement  #is this right?
    reponse, payload = send_data_in_vcmd(micron_vendor_cmd=vu)
    return payload[0]

def issue_C071_to_set_SGD_scan_parameters(param:C071_param, isSGS:int = 1) -> None:
    vu = micron_vu_C071()
    vu.b0_opcode.value = 0x71
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0x100000000)
    vu.isSGS.value = isSGS 
    payload = bytearray(4096) 
    payload[0:len(param.payload)] = param.payload
    
    send_data_out_vcmd(micron_vendor_cmd=vu, data_payload= payload)

class VBList():

    VB_GROUP_LIST = {
                'HIDDEN_BLK_USE': 0,
                'LIST_BLK': 1,
                'LIST_INDEX_BLK': 2,
                'TMP_CODE_BLK': 3,
                'CURRENT_PTE': 4,
                'LOG_TAB_BLK': 5,
                'CURRENT_L2_SLC': 6,
                'CURRENT_L2_MLC': 7,
                'FREEZE_L2_BLK': 8,
                'CURRENT_DATA_GC_BLK_SLC': 9,
                'CURRENT_DATA_GC_BLK_MLC': 10,
                'INCOMPLETE_BLK_SLC': 11,
                'INCOMPLETE_BLK_MLC': 12,
                'CURRENT_L1': 13,
                'PTE_POOL': 14,
                'STATIC_SLC_USED_BLK': 15,
                'USED_BLK_POOL_SLC': 16,
                'USED_BLK_POOL_MLC': 17,
                'CURRENT_L3_SLC': 18,
                'CURRENT_L3_MLC': 19,
                'REFRESH_LINE': 20,
                'RAIN_SWAP_NO_OBR_SLC_L2_SLC':21,
                'RAIN_SWAP_NO_OBR_TLC_L2_SLC':22,
                'RAIN_SWAP_NO_OBR_TLC_L2_TLC':23,
                'RAIN_SWAP_NO_OBR_BLK': 24,
                'RAIN_SWAP_TLC_CURSOR_BLK': 25,
                'FREE_BLK_QUEUE_SLC': 26,
                'FREE_BLK_QUEUE_MLC': 27,
                'FREE_BLK_QUEUE_TABLE': 28,
                'TMP_ERASE_BLK_SLC': 29,
                'TMP_ERASE_BLK_MLC': 30,
                'TMP_ERASE_BLK_TABLE': 31,
                'TMP_USED_BLK_SLC': 32,
                'TMP_USED_BLK_MLC': 33,
                'TMP_USED_BLK_TABLE': 34,
                'TMP_REMOVE_BLK_SLC': 35,
                'TMP_REMOVE_BLK_MLC': 36,
                'TMP_REMOVE_BLK_TABLE': 37,
                'REFERENCE_QUEUE_SLC': 38,
                'REFERENCE_QUEUE_MLC': 39,
                'REVOKE_BLK': 40,
                'REMAP_DATA_GC_BLK_SLC': 41,
                'REMAP_DATA_GC_BLK_MLC': 42,
                'RPMB_COLLECT_BLK': 43,
                'PRE_ERASE_BLK': 44,
                'TMP_PRE_ERASE': 45,
                'PURGE_WAIT_ERASE_SLC': 46,
                'PURGE_WAIT_ERASE_MLC': 47,
                'DRVLOG_BLK': 48,
                'CONSTRAINT_QUEUE': 49,
                'TMP_FORCE_PTE_GC_TARGET': 50,
                'RESERVED_VB_GROUP0': 51,
                'RESERVED_VB_GROUP1': 52,
                'RESERVED_VB_GROUP2': 53,
                'RESERVED_VB_GROUP3': 54,
                'SELF_PE_ERASE_BLK': 55,
                'CONFIG_NUM_LIST_GROUP': 56,
    }


    VB_LIST_DATA_FORMAT = {
        'group': {'pos': 0, 'len': 6, 'mask': 0x3f},
                'access_mode': {'pos': 6, 'len': 2, 'mask': 0x03},
                'dirty': {'pos': 8, 'len': 1, 'mask': 0x01},
                'partition': {'pos': 9, 'len': 2, 'mask': 0x03},
                'cursor_idx': {'pos': 11, 'len': 1, 'mask': 0x01},
                'pte_tbl_mark':{'pos':12,'len':1,'mask':0x01},
                'host_w_mark':{'pos':13,'len':2,'mask':0x01},
                'rsv': {'pos': 15, 'len': 17, 'mask': 0x3f},
    }

    def __init__(self) ->None:
        pass

    def vb_group_list(self) -> Dict[str,int]:
        return self.VB_GROUP_LIST

class VBInfo(VBList):
    def __init__(self)->None:
        super().__init__()
        _, data = get_vb_info()
        self.list = self.__parse(data)

    def __parse(self, payload: bytearray) -> Dict[int, Dict[str,int]]:
        d : Dict[int, Dict[str,int]] = {}
        size = 4
        for vb in range(len(payload) // size):
            byte = vb * size
            d.update({vb: {k: ((int.from_bytes(payload[byte:byte + size], 'little') >>
                     v['pos']) & v['mask']) for k, v in self.VB_LIST_DATA_FORMAT.items()}})

        return d
