from enum import Enum, IntEnum
from Script.api.ufs_api.defines.bit_define import BIT

from Script.api.ufs_api.defines.bit_define import BIT0, BIT1, BIT2, BIT3, BIT7

class BBRetirementReaspnType(IntEnum):
    EARLY = 0x0
    WRITE = 0x1
    ERASE = 0x2
    READ_SCAN_UECC = 0x3
    READBACK = 0x4
    SGM_LVT_FAIL_AFTER_TOUCHUP = 0x5
    SGM_HVT_FAIL = 0x6
    SGM_LVT = 0x7
    SYSTEM = 0x8
    DUMMY = 0xF

class BBRetirementReaspnBlkType(IntEnum):
    GENERIC = 0x0
    EM1_GC_REFRESH = 0x1
    EM1_OPEN_HOST = 0x2
    EM1_SMALL_CHUNK = 0x3
    EM1_CLOSED = 0x4
    TLC_GC_REFRESH = 0x5
    TLC_OPEN_HOST = 0x6
    WB = 0x7
    PTE_CLOSED = 0x8
    PTE_OPEN = 0x9
    TMP_RAIN = 0xA
    SWAP_RAIN = 0xB
    LOG_OPEN = 0xC
    TLC_CLOSED = 0xD
    LOG_CLOSED = 0xE
    DUMMY = 0xF