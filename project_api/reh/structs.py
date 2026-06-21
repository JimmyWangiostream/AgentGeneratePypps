from __future__ import annotations   # <‑‑ 必須放在所有 import 之前
import struct
from typing import List, Dict, Final
from enum import Enum, IntEnum, auto
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from dataclasses import dataclass

class NAND_MODE(Enum):
    TLC_BLOCK       = 0
    SLC_BLOCK       = 1

class READ_LAST_TABLE(IntEnum):
    LAST_TABLE_1    = 0
    LAST_TABLE_2    = 1

class PAGE_TYPE(IntEnum):
    PAGE_POR_SSLC = (0, "PAGE_POR_SSLC",    1)
    PAGE_SLC_LP =   (1, "PAGE_SLC_LP",      1)
    PAGE_MLC_LP =   (2, "PAGE_MLC_LP",      1) 
    PAGE_MLC_UP =   (3, "PAGE_MLC_UP",      2) 
    PAGE_TLC_LP =   (4, "PAGE_TLC_LP",      2) 
    PAGE_TLC_UP =   (5, "PAGE_TLC_UP",      3) 
    PAGE_TLC_XP =   (6, "PAGE_TLC_XP",      2)
    PAGE_POR_DSLC = (7, "PAGE_POR_DSLC",    1)
    PAGE_PSA_SLC =  (8, "PAGE_PSA_SLC",     1)

    _label_: str
    _offset_count_: int

    def __new__(cls, value: int, label: str, offset_count:int) -> PAGE_TYPE:
        # 先用 int 建立 Enum 成員
        obj = int.__new__(cls, value)
        obj._value_ = value               # 必須手動設定 value
        obj._label_ = label               # 把字串存成私有屬性
        obj._offset_count_ = offset_count
        return obj

    @property
    def label(self) -> str:
        return self._label_
    
    @property
    def offset_count(self) -> int:
        return self._offset_count_

class BLOCK_PAGE_TYPE(IntEnum):
    #  (int value, 顯示字串)
    SLC_BLOCK_SLC_PAGE = (1, "SLC block's SLC page")
    TLC_BLOCK_SLC_PAGE = (2, "TLC block's SLC page")
    TLC_BLOCK_MLC_PAGE = (3, "TLC block's MLC page")
    TLC_BLOCK_TLC_PAGE = (4, "TLC block's TLC page")
    TLC_BLOCK_PSA_PAGE = (5, "TLC block's PSA page")

    _label_: str

    def __new__(cls, value: int, label: str = '') -> BLOCK_PAGE_TYPE:
        # 先用 int 建立 Enum 成員
        obj = int.__new__(cls, value)
        obj._value_ = value               # 必須手動設定 value
        obj._label_ = label               # 把字串存成私有屬性
        return obj

    @property
    def label(self) -> str:
        return self._label_

PAGE_TYPE_MAP: Dict[BLOCK_PAGE_TYPE, List[PAGE_TYPE]] = {
    # SLC Block → 只會出現在 SLC Page
    BLOCK_PAGE_TYPE.SLC_BLOCK_SLC_PAGE: [
        PAGE_TYPE.PAGE_POR_DSLC,
    ],

    # TLC Block → 可能的 Page 類型（視需求自行擴充）
    BLOCK_PAGE_TYPE.TLC_BLOCK_SLC_PAGE: [
        PAGE_TYPE.PAGE_SLC_LP
    ],

    BLOCK_PAGE_TYPE.TLC_BLOCK_MLC_PAGE: [
        PAGE_TYPE.PAGE_MLC_LP,
        PAGE_TYPE.PAGE_MLC_UP,
    ],

    BLOCK_PAGE_TYPE.TLC_BLOCK_TLC_PAGE: [
        PAGE_TYPE.PAGE_TLC_LP,
        PAGE_TYPE.PAGE_TLC_UP,
        PAGE_TYPE.PAGE_TLC_XP,
    ],

    BLOCK_PAGE_TYPE.TLC_BLOCK_PSA_PAGE:[
        PAGE_TYPE.PAGE_PSA_SLC
    ]
}

class PageLimit(Enum):
    MAX_SLC = 1103
    MAX_TLC = 3311


MAX_BLOCK: Final = 408

REH_STEP_TABLE: Dict[BLOCK_PAGE_TYPE, Dict[int, List[int]]] = {
    BLOCK_PAGE_TYPE.SLC_BLOCK_SLC_PAGE: {
        0: [0, 1],
        1: [2, 3],
        2: [8],
        3: [0, 1, 2, 3, 4],
        4: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        6: [1, 2],
        7: [1, 2],
        9: [0]  # REH fail
    },

    BLOCK_PAGE_TYPE.TLC_BLOCK_SLC_PAGE: {
        0: [0, 1],
        1: [2, 3],
        2: [4, 5, 6, 7, 8],
        3: [0, 1, 2, 3, 4],
        4: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        6: [1, 2],
        7: [1, 2],
        9: [0]  # REH fail
    },

    BLOCK_PAGE_TYPE.TLC_BLOCK_PSA_PAGE: {
        0: [0, 1],
        1: [2, 3],
        2: [4, 5, 6, 7, 8],
        3: [0, 1, 2, 3, 4],
        4: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        6: [1, 2],
        7: [1, 2],
        9: [0]  # REH fail
    },

    BLOCK_PAGE_TYPE.TLC_BLOCK_MLC_PAGE: {
        0: [0, 1],
        1: [2, 3],
        2: [4, 5, 6, 7, 8],
        3: [0, 1, 2],
        4: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        6: [1, 2],
        7: [1, 2],
        9: [0]  # REH fail
    },

    BLOCK_PAGE_TYPE.TLC_BLOCK_TLC_PAGE: {
        0: [0, 1],
        1: [2, 3],
        2: [4, 5, 6, 7, 8],
        3: [0, 1, 2],
        4: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        6: [1, 2, 4],
        7: [0, 1, 2, 3, 4],
        8: [0, 1, 2, 4],
        9: [0]  # REH fail
    },
}

@dataclass
class ERROR_RECOVERY_STATISTICS_RECORD:
    index: int
    name: str
    occupies: int
    offset: int
    big_step: int = 0xFFFF
    small_step: int = 0xFFFF
    isSLC: int = 2 # 0: TLC, 1: SLC, 2: Don'care 
    isPSA: int = 0 # 0: non-PSA, 1: PSA

ERROR_RECOVERY_STATISTICS: List[ERROR_RECOVERY_STATISTICS_RECORD] = [
    ERROR_RECOVERY_STATISTICS_RECORD(1, "1_Dummy_Read_ERS",                 2,      4,      0,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(2, "2_Read_Last_1_ERS",                2,      52,     1,  2),
    ERROR_RECOVERY_STATISTICS_RECORD(3, "3_Read_Last_2_ERS",                2,      100,    1,  3),
    ERROR_RECOVERY_STATISTICS_RECORD(4, "4_BRRP1_ERS",                      2,      148,    2,  4),
    ERROR_RECOVERY_STATISTICS_RECORD(5, "5_BRRN1_ERS",                      2,      196,    2,  5),
    ERROR_RECOVERY_STATISTICS_RECORD(6, "6_BRRP2_ERS",                      2,      244,    2,  6),
    ERROR_RECOVERY_STATISTICS_RECORD(7, "7_BRRN2_ERS",                      2,      292,    2,  7),
    ERROR_RECOVERY_STATISTICS_RECORD(8, "8_BINARC1_ERS",                    2,      340,    2,  8),
    ERROR_RECOVERY_STATISTICS_RECORD(9, "9_CFBIT1_ERS",                     2,      388,    3,  0),
    ERROR_RECOVERY_STATISTICS_RECORD(10, "10_CFBIT2_ERS",                   2,      436,    3,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(11, "11_CFBIT3_ERS",                   2,      484,    3,  2),
    ERROR_RECOVERY_STATISTICS_RECORD(12, "12_CFBIT4_ERS",                   2,      532,    3,  3),
    ERROR_RECOVERY_STATISTICS_RECORD(13, "13_CFBIT5_ERS",                   2,      580,    3,  4),
    ERROR_RECOVERY_STATISTICS_RECORD(14, "14_SureArc1_ERS",                 2,      628,    4,  0),
    ERROR_RECOVERY_STATISTICS_RECORD(15, "15_SureArc2_ERS",                 2,      676,    4,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(16, "16_SureArc3_ERS",                 2,      724,    4,  2),
    ERROR_RECOVERY_STATISTICS_RECORD(17, "17_SureArc4_ERS",                 2,      772,    4,  3),
    ERROR_RECOVERY_STATISTICS_RECORD(18, "18_SureArc5_ERS",                 2,      820,    4,  4),
    ERROR_RECOVERY_STATISTICS_RECORD(19, "19_SureArc6_ERS",                 2,      868,    4,  5),
    ERROR_RECOVERY_STATISTICS_RECORD(20, "20_SureArc7_ERS",                 2,      916,    4,  6),
    ERROR_RECOVERY_STATISTICS_RECORD(21, "21_SureArc8_ERS",                 2,      964,    4,  7),
    ERROR_RECOVERY_STATISTICS_RECORD(22, "22_SureArc9_ERS",                 2,      1012,   4,  8),
    ERROR_RECOVERY_STATISTICS_RECORD(23, "23_SureArc10_ERS",                2,      1060,   4,  9),
    ERROR_RECOVERY_STATISTICS_RECORD(24, "24_DP_SOFT_1H_ERS",               2,      1108),
    ERROR_RECOVERY_STATISTICS_RECORD(25, "25_DP_SOFT_1S_ERS",               2,      1156,   6,  1,  0), #TLC
    ERROR_RECOVERY_STATISTICS_RECORD(26, "26_DP_SOFT_2S_ERS",               2,      1204,   6,  2,  0), #TLC
    ERROR_RECOVERY_STATISTICS_RECORD(27, "27_DPSOFTMODE2S_LI_ERSCount",     2,      1252,   6,  4,  0),
    ERROR_RECOVERY_STATISTICS_RECORD(28, "28_EnhancedARC_ERS",              2,      1300,   7,  0,  0),
    ERROR_RECOVERY_STATISTICS_RECORD(29, "29_DP2BCR_1H_ERS",                2,      1348,   7,  1,  0),
    ERROR_RECOVERY_STATISTICS_RECORD(29, "29_DP2BCR_1H_ERS",                2,      1348,   6,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(30, "30_DP2BCR_1S_ERS",                2,      1396,   7,  2,  0),
    ERROR_RECOVERY_STATISTICS_RECORD(30, "30_DP2BCR_1S_ERS",                2,      1396,   6,  2,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(31, "31_DP2BCR_2S_ERS",                2,      1444,   7,  3,  0),
    ERROR_RECOVERY_STATISTICS_RECORD(32, "32_DP2BCRMOD2S_LI_ERSCount",      2,      1492,   7,  4,  0),
    ERROR_RECOVERY_STATISTICS_RECORD(33, "33_DP4BCR_1H_ERS",                2,      1540,   8,  0,  0),
    ERROR_RECOVERY_STATISTICS_RECORD(34, "34_DP4BCR_1S_ERS",                2,      1588,   8,  1,  0),
    ERROR_RECOVERY_STATISTICS_RECORD(34, "34_DP4BCR_1S_ERS",                2,      1588,   7,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(35, "35_DP4BCR_2S_ERS",                2,      1636,   8,  2,  0),
    ERROR_RECOVERY_STATISTICS_RECORD(35, "35_DP4BCR_2S_ERS",                2,      1636,   7,  2,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(36, "36_DP4BCRCnt2S_LI_ERSCount",      2,      1684,   8,  4,  0),
    ERROR_RECOVERY_STATISTICS_RECORD(37, "37_PSA_Dummy_Read_ERS",           2,      1732,   0,  1,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(38, "38_PSA_Read_Last_1_ERS",          2,      1780,   1,  2,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(39, "39_PSA_Read_Last_2_ERS",          2,      1828,   1,  3,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(40, "40_PSA_BINARC1_ERS",              2,      1876,   2,  8,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(41, "41_PSA_CFBIT1_ERS",               2,      1924,   3,  0,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(42, "42_PSA_CFBIT2_ERS",               2,      1972,   3,  1,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(43, "43_PSA_CFBIT3_ERS",               2,      2020,   3,  2,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(44, "44_PSA_CFBIT4_ERS",               2,      2068,   3,  3,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(45, "45_PSA_CFBIT5_ERS",               2,      2116,   3,  4,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(46, "46_PSA_SureArc1_ERS",             2,      2164,   4,  0,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(47, "47_PSA_SureArc2_ERS",             2,      2212,   4,  1,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(48, "48_PSA_SureArc3_ERS",             2,      2260,   4,  2,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(49, "49_PSA_SureArc4_ERS",             2,      2308,   4,  3,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(50, "50_PSA_SureArc5_ERS",             2,      2356,   4,  4,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(51, "51_PSA_SureArc6_ERS",             2,      2404,   4,  5,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(52, "52_PSA_SureArc7_ERS",             2,      2452,   4,  6,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(53, "53_PSA_SureArc8_ERS",             2,      2500,   4,  7,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(54, "54_PSA_SureArc9_ERS",             2,      2548,   4,  8,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(55, "55_PSA_SureArc10_ERS",            2,      2596,   4,  9,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(56, "56_PSA_DP_SOFT_1H_ERS",           2,      2644),
    ERROR_RECOVERY_STATISTICS_RECORD(57, "57_PSA_DP_SOFT_1S_ERS",           2,      2692,   6,  1,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(58, "58_PSA_DP_SOFT_2S_ERS",           2,      2740,   6,  2,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(59, "59_PSA_DP2BCR_1H_ERS",            2,      2788,   7,  1,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(60, "60_PSA_DP2BCR_1S_ERS",            2,      1836,   7,  2,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(61, "61_PSA_DP2BCR_2S_ERS",            2,      2884,   7,  3,  1,  1),
    ERROR_RECOVERY_STATISTICS_RECORD(62, "62_SuccessfulRecoveryCnt",        2,      2932),
    ERROR_RECOVERY_STATISTICS_RECORD(63, "63_TotalUECC_cnt",                2,      2980,   9,  0),
    ERROR_RECOVERY_STATISTICS_RECORD(64, "64_RAIN_CECC_ERScnt",             2,      3028),
    ERROR_RECOVERY_STATISTICS_RECORD(65, "65_DefaultReadPass_counter",      4,      3076),
    ERROR_RECOVERY_STATISTICS_RECORD(66, "66_StickyReadPass_counter",       4,      3172),
    ERROR_RECOVERY_STATISTICS_RECORD(83, "83_StickyEnterERSCount",          2,      3916),
    ERROR_RECOVERY_STATISTICS_RECORD(84, "84_PSA_StickyEnterERSCount",      2,      3964)
]

@dataclass
class ERROR_NUMBER_INFORMATION_RECORD:
    index: int
    name: str
    big_step: int = 0xFFFF
    small_step: int = 0xFFFF
    isSLC: int = 2 # 0: TLC, 1: SLC, 2: Don'care 

ERROR_NUMBER_INFORMATION: List[ERROR_NUMBER_INFORMATION_RECORD] = [
    ERROR_NUMBER_INFORMATION_RECORD(0, "StickyReRead or Skip",                 0,  0),
    ERROR_NUMBER_INFORMATION_RECORD(1, "BinReRead",                            0,  1),
    ERROR_NUMBER_INFORMATION_RECORD(2, "Hard bit read last 1",                 1,  2),
    ERROR_NUMBER_INFORMATION_RECORD(3, "Hard bit read last 2",                 1,  3),
    ERROR_NUMBER_INFORMATION_RECORD(4, "BinReadRetry1",                        2,  4),
    ERROR_NUMBER_INFORMATION_RECORD(5, "BinReadRetry2",                        2,  5),
    ERROR_NUMBER_INFORMATION_RECORD(6, "BinReadRetry3",                        2,  6),
    ERROR_NUMBER_INFORMATION_RECORD(7, "BinReadRetry4",                        2,  7),
    ERROR_NUMBER_INFORMATION_RECORD(8, "BinARC1",                              2,  8),
    ERROR_NUMBER_INFORMATION_RECORD(9, "CFBIT1",                               3,  0),
    ERROR_NUMBER_INFORMATION_RECORD(10, "CFBIT2",                              3,  1),
    ERROR_NUMBER_INFORMATION_RECORD(11, "CFBIT3",                              3,  2),
    ERROR_NUMBER_INFORMATION_RECORD(12, "CFBIT4",                              3,  3),
    ERROR_NUMBER_INFORMATION_RECORD(13, "CFBIT5",                              3,  4),
    ERROR_NUMBER_INFORMATION_RECORD(14, "SureARC1",                            4,  0),
    ERROR_NUMBER_INFORMATION_RECORD(15, "SureARC2",                            4,  1),
    ERROR_NUMBER_INFORMATION_RECORD(16, "SureARC3",                            4,  2),
    ERROR_NUMBER_INFORMATION_RECORD(17, "SureARC4",                            4,  3),
    ERROR_NUMBER_INFORMATION_RECORD(18, "SureARC5",                            4,  4),
    ERROR_NUMBER_INFORMATION_RECORD(19, "SureARC6",                            4,  5),
    ERROR_NUMBER_INFORMATION_RECORD(20, "SureARC7",                            4,  6),
    ERROR_NUMBER_INFORMATION_RECORD(21, "SureARC8",                            4,  7),
    ERROR_NUMBER_INFORMATION_RECORD(22, "SureARC9",                            4,  8),
    ERROR_NUMBER_INFORMATION_RECORD(23, "SureARC10",                           4,  9),
    ERROR_NUMBER_INFORMATION_RECORD(24, "DP_SOFT_1S (LLR0)",                   6,  1,   0), #TLC,
    ERROR_NUMBER_INFORMATION_RECORD(25, "DP_SOFT_1S (LLR1)"), 
    ERROR_NUMBER_INFORMATION_RECORD(26, "DP_SOFT_2S (LLR0)",                   6,  2,   0), #TLC
    ERROR_NUMBER_INFORMATION_RECORD(27, "DP_SOFT_2S (LLR1)"), 
    ERROR_NUMBER_INFORMATION_RECORD(28, "DPSOFTMODE2S_LI_ERSCOUNT (LLR0)",     6,  4,   0), #TLC
    ERROR_NUMBER_INFORMATION_RECORD(29, "DPSOFTMODE2S_LI_ERSCOUNT (LLR1)"), 
    ERROR_NUMBER_INFORMATION_RECORD(30, "EnhancedARC",                         7,  0,   0), #TLC
    ERROR_NUMBER_INFORMATION_RECORD(31, "DP2BCR_1H",                           7,  1,   0),
    ERROR_NUMBER_INFORMATION_RECORD(31, "DP2BCR_1H",                           6,  1,   1),
    ERROR_NUMBER_INFORMATION_RECORD(32, "DP2BCR_1S (LLR0)",                    7,  2,   0),
    ERROR_NUMBER_INFORMATION_RECORD(32, "DP2BCR_1S (LLR0)",                    6,  2,   1),
    ERROR_NUMBER_INFORMATION_RECORD(33, "DP2BCR_1S (LLR1)"),
    ERROR_NUMBER_INFORMATION_RECORD(34, "DP2BCR_2S (LLR0)",                    7,  3,   0),
    ERROR_NUMBER_INFORMATION_RECORD(35, "DP2BCR_2S (LLR1)"),
    ERROR_NUMBER_INFORMATION_RECORD(36, "DP2BCRMOD2S_LI (LLR0)",               7,  4,   0),
    ERROR_NUMBER_INFORMATION_RECORD(37, "DP2BCRMOD2S_LI (LLR1)"),
    ERROR_NUMBER_INFORMATION_RECORD(38, "DP4BCR_1H",                           8,  0,   0),
    ERROR_NUMBER_INFORMATION_RECORD(39, "DP4BCR_1S (LLR0)",                    8,  1,   0),
    ERROR_NUMBER_INFORMATION_RECORD(39, "DP4BCR_1S (LLR0)",                    7,  1,   1),
    ERROR_NUMBER_INFORMATION_RECORD(40, "DP4BCR_1S (LLR1)"),
    ERROR_NUMBER_INFORMATION_RECORD(41, "DP4BCR_2S (LLR0)",                    8,  2,   0),
    ERROR_NUMBER_INFORMATION_RECORD(41, "DP4BCR_2S (LLR0)",                    7,  2,   1),
    ERROR_NUMBER_INFORMATION_RECORD(42, "DP4BCR_2S (LLR1)"),
    ERROR_NUMBER_INFORMATION_RECORD(43, "DP4BCRCnt2S_LI (LLR0)",               8,  4,   0),
    ERROR_NUMBER_INFORMATION_RECORD(44, "DP4BCRCnt2S_LI (LLR1)")
]

class micron_vu_D014_option_0(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.option = self.add_field(12, 12, 'little')
        self.dieId = self.add_field(13, 13, 'little')
        self.bigIndex = self.add_field(14, 14, 'little')
        self.smallIndex = self.add_field(15, 15, 'little')
        self.nandMode = self.add_field(16, 16, 'little')
        self.isSpeciBlock = self.add_field(17, 17, 'little')
        self.block = self.add_field(18, 19, 'little')
        self.isPSA = self.add_field(20, 20, 'little')

class micron_vu_D014_option_1(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.option = self.add_field(12, 12, 'little')
        self.pageType = self.add_field(13, 13, 'little')
        self.bigStepBitMap = self.add_field(14, 17, 'little')
        self.smallStepBitMap = self.add_field(18, 21, 'little')

class micron_vu_D014_option_2(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.option = self.add_field(12, 12, 'little')
        self.dieId = self.add_field(13, 13, 'little')
        self.pageType = self.add_field(14, 14, 'little')
        self.tableIndex = self.add_field(15, 15, 'little')
        self.recipeType = self.add_field(16, 16, 'little')
        self.recipeContent = self.add_field(17, 17, 'little')
        self.offset1 = self.add_field(18, 18, 'little')
        self.offset2 = self.add_field(19, 19, 'little')
        self.offset3 = self.add_field(20, 20, 'little')

class micron_vu_D014_option_6(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.option = self.add_field(12, 12, 'little')
        self.autoSwitch = self.add_field(13, 13, 'little')

class micron_vu_D014_option_7(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.option = self.add_field(12, 12, 'little')
        self.action = self.add_field(13, 13, 'little')

class micron_vu_D014_option_8(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.option = self.add_field(12, 12, 'little')
        self.enable = self.add_field(13, 13, 'little')
        self.temperature = self.add_field(14, 14, 'little')


class micron_vu_40F9(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.dieBitMap = self.add_field(12, 15, 'little')
        self.planeBitMap = self.add_field(16, 19, 'little')
        self.block = self.add_field(20, 23, 'little')
        self.startPage = self.add_field(24, 27, 'little')
        self.stopPage = self.add_field(28, 31, 'little')
        self.isSLCBlock = self.add_field(32, 35, 'little')
        self.isPSA = self.add_field(40, 40, 'little')
        self.bin = self.add_field(41, 41, 'little')
        self.fwBlock = self.add_field(42, 42, 'little')

class rr_number_and_error_bits(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(5), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.bigStep= self.add_field(0, 0, 'little')
        self.smallStep = self.add_field(1, 1, 'little')
        self.maxErrorBits = self.add_field(2, 3, 'little')
        self.bin = self.add_field(4, 4, 'little')

class micron_vu_4014_option_0(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.option = self.add_field(12, 12, 'little')
        self.die = self.add_field(13, 13, 'little')
        self.pageType = self.add_field(14, 14, 'little')
        self.lastTableIndex = self.add_field(15, 15, 'little')

class micron_vu_4014_option_1(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.option = self.add_field(12, 12, 'little')
        self.die = self.add_field(13, 13, 'little')

class micron_vu_4014_option_2(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.option = self.add_field(12, 12, 'little')
        self.die = self.add_field(13, 13, 'little')

class micron_vu_4014_option_5(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.option = self.add_field(12, 12, 'little')
        self.die = self.add_field(13, 13, 'little')

class micron_vu_4014_option_7(micron_vendor_cmd):
    def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.option = self.add_field(12, 12, 'little')

class read_recovery_info_read_last(PacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.reserved= self.add_field(0, 3, 'little')
        self.offset1 = self.add_field(4, 4, 'little')
        self.offset2 = self.add_field(5, 5, 'little')
        self.offset3 = self.add_field(6, 6, 'little')

class micron_vu_409E(micron_vendor_cmd):
     def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.eccInfo = self.add_field(12, 12, 'little')
        self.eccType = self.add_field(13, 13, 'little')

class error_bit_number_of_last_reading(PacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.errorBitNumber1= self.add_field(0, 3, 'little')
        self.errorBitNumber2 = self.add_field(4, 7, 'little')
        self.errorBitNumber3 = self.add_field(8, 11, 'little')
        self.errorBitNumber4 = self.add_field(12, 15, 'little')

class micron_vu_40BB(micron_vendor_cmd):
     def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.die = self.add_field(12, 15, 'little')

class error_bit_number_and_read_retry_step(PacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.errorBitNumber1= self.add_field(0, 1, 'little')
        self.errorBitNumber2 = self.add_field(2, 3, 'little')
        self.errorBitNumber3 = self.add_field(4, 5, 'little')
        self.errorBitNumber4 = self.add_field(6, 7, 'little')
        self.reReadResult = self.add_field(8, 8, 'little')
        self.reReadBigStep = self.add_field(9, 9, 'little')
        self.reReadSmallStep = self.add_field(10, 10, 'little')
        self.reReadErrorBits = self.add_field(11, 14, 'little')
        self.readLastResult = self.add_field(15, 15, 'little')
        self.readLastBigStep = self.add_field(16, 16, 'little')
        self.readLastSmallStep = self.add_field(17, 17, 'little')
        self.readLastErrorBits = self.add_field(18, 21, 'little')
        self.syndromeWeight = self.add_field(22, 25, 'little')

class micron_vu_40BA(micron_vendor_cmd):
     def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)

class error_recovery_statistics(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(4012), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.die_count= self.add_field(0, 3, 'little')
        self.ers_info= self.add_field(4, 4011, 'little')

class micron_vu_D019(micron_vendor_cmd):
     def __init__(self, payload: bytearray = bytearray(44)) -> None:
        super().__init__(payload)
        self.Flag = self.add_field(12, 12, 'little')