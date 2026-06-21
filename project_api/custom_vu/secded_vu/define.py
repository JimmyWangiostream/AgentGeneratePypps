from enum import Enum, IntEnum
from Script.api.ufs_api.defines.bit_define import BIT

from Script.api.ufs_api.defines.bit_define import BIT0, BIT1, BIT2, BIT3, BIT7

class ErrorInjection(IntEnum):
    DISABLE_ERROR_INJECTION = 0
    FIP_SRAM = 1
    RS_SRAM = 2
    COP0_SRAM = 3
    COP1_SRAM = 4
    BMU_SRAM = 5
    DBUF_SRAM = 6
    SEC_SRAM = 7