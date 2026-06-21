from enum import Enum, IntEnum
from Script.api.ufs_api.defines.bit_define import BIT

from Script.api.ufs_api.defines.bit_define import BIT0, BIT1, BIT2, BIT3, BIT7

class OpenVBType(IntEnum):
    INDEX_BLK = 0
    TEMP_CODE_BLK = 1
    EM1_L2_BLK = 2
    L2_OPEN_LOGICAL_VB = 3
    WRITE_BOOSTER_L2 = 4
    EM1_GC = 5
    NORMAL_DEFRAG_VB = 6
    L1_OPEN_VB = 7
    OTHER = 0xF
