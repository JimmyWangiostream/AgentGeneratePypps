from __future__ import annotations   # <‑‑ 必須放在所有 import 之前
import struct
from typing import List, Dict, Final
from enum import Enum, IntEnum
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class TRIM_STATE(IntEnum):
    POR_TRIM       = 0
    PSA_TRIM       = 1
    SLx_TRIM       = 2

class VB_GROUP_TYPE(IntEnum):
    LIST_BLK                    = 0x01
    LIST_INDEX_BLK              = 0x02
    TMP_CODE_BLK                = 0x03
    CURRENT_PTE                 = 0x04
    LOG_TAB_BLK                 = 0x05
    CURRENT_L2_SLC              = 0x06
    CURRENT_L2_MLC              = 0x07
    CURRENT_DATA_GC_BLK_SLC     = 0x09
    CURRENT_DATA_GC_BLK_MLC     = 0x0A
    INCOMPLETE_BLK_SLC          = 0x0B
    INCOMPLETE_BLK_MLC          = 0x0C
    CURRENT_L1                  = 0x0D
    PTE_POOL                    = 0x0E
    STATIC_SLC_USED_BLK         = 0x0F
    USED_BLK_POOL_SLC           = 0x10
    USED_BLK_POOL_MLC           = 0x11
    CURRENT_L3_SLC              = 0x12
    CURRENT_L3_MLC              = 0x13
    RAIN_SWAP_NO_OBR_SLC_L2_SLC = 0X15
    RAIN_SWAP_NO_OBR_TLC_L2_SLC = 0X16
    RAIN_SWAP_NO_OBR_TLC_L2_TLC = 0X17
    RAIN_SWAP_NO_OBR_TEMP_BLK   = 0X18
    FREE_BLK_QUEUE_SLC          = 0X1A
    FREE_BLK_QUEUE_MLC          = 0X1B
    FREE_BLK_QUEUE_TABLE        = 0X1C

