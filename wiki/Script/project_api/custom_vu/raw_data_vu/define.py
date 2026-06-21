from enum import Enum, IntEnum
from Script.api.ufs_api.defines.bit_define import BIT

from Script.api.ufs_api.defines.bit_define import BIT0, BIT1, BIT2, BIT3, BIT7

class ReadStatus(IntEnum):
    Normal = 0
    Empty = 1
    UECC = 2
