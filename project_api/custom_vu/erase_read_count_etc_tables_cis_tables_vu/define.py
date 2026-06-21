from enum import Enum, IntEnum
from Script.api.ufs_api.defines.bit_define import BIT

from Script.api.ufs_api.defines.bit_define import BIT0, BIT1, BIT2, BIT3, BIT7

class VU4097Paremeter(IntEnum):
    GET_EC_TABLE = 0
    GET_RC_TABLE = 1
    GET_L2P_VB_TABLE = 2
    GET_CIS_VB_TABLE = 3
    RESERVED = 4
    GET_SYSTEM_ALL_SUB_VB_VERSIONS = 5
    GET_BBT_SUB_VB_INFO = 6
    GET_EC_TABLE_RAW = 7
    RESERVED1 = 8
    ICS_BAD_BLOCK = 9
    GET_VERSION = 10
    RESERVED2 = 11
    RESERVED3 = 12
    RESERVED4 = 13
    GET_PTE_REGION_NUMBER = 14
    GET_EC_TLC_TABLE = 15
    
class VUC083Paremeter(IntEnum):
    SET_EC_TABLE = 0x00
    SET_RC_TABLE = 0x01
    SET_RC_THRESHOLD_VALUE = 0x04

class VUC083VB_Num(IntEnum):
    FLUSH_THE_EC_CHANGE_IN_SYSTEM_TABLE = 0x01
    CHANGE_THE_EC_ONLY_IN_RAM = 0x00
