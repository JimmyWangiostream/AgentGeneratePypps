from enum import Enum, IntEnum
from Script.api.ufs_api.defines.bit_define import *

class RainUser(IntEnum):
    WB_RAIN = 0
    HOST_TLC_RAIN = 1
    HOST_EM1_RAIN = 2
    TABLE_RAIN = 3
    RECOVER_USER = 4

class RainVB(IntEnum):
    Table = BIT0
    S_CHK = BIT1
    WB = BIT2
    TLC = BIT3
    EM1 = BIT4
    Table_recovery = BIT5
    S_CHK_recovery = BIT6
    WB_recovery = BIT7
    TLC_recovery = BIT8
    EM1_recovery = BIT9
    ALL = 0xFFFFFFFF
