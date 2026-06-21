from enum import Enum, IntEnum
from Script.api.ufs_api.defines.bit_define import BIT

from Script.api.ufs_api.defines.bit_define import BIT0, BIT1, BIT2, BIT3, BIT7

class VBListNum(IntEnum):
    LIST_BLK = 0
    INDEX_BLK = 1
    TMP_CODE_BLK = 2
    CURRENT_PTE = 3
    LOG_TAB_BLK = 4
    CURRENT_L2_EM1 = 5
    CURRENT_L2_TLC = 6
    CURRENT_L2_TLC_WB = 7
    DATA_GC_TARGET_BLK_EM1 = 8
    DATA_GC_TARGET_BLK_TLC = 9
    INCOMPLETE_BLK_EM1 = 10
    INCOMPLETE_BLK_TLC = 11
    CURRENT_L1 = 12
    PTE_POOL = 13
    USED_BLK_POOL_EM1 = 14
    USED_BLK_POOL_TLC = 15
    USED_BLK_POOL_TLC_WB = 16
    CURRENT_L3_EM1 = 17
    CURRENT_L3_TLC = 18
    CURRENT_L3_TLC_WB = 19
    RAIN_SWAP_EM1 = 20
    RAIN_SWAP_WB = 21
    RAIN_SWAP_TLC = 22
    RAIN_SWAP_TEMP_RAIN = 23
    FREE_BLK_QUEUE_EM1 = 24
    FREE_BLK_QUEUE_TLC = 25
    FREE_BLK_QUEUE_TABLE = 26
    OTHER = 0x1F