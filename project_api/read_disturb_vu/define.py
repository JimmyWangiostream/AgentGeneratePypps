from enum import Enum, IntEnum

class EC_RC_BlockType(IntEnum):
    SLC_OPEN = 0x0
    SLC_CLOSE = 0x1
    TLC_OPEN = 0x2
    TLC_CLOSE = 0x3