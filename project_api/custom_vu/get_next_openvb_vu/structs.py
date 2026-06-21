import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
# 0 == return, in output buffer, the VB index to be opened, given the current FW status, for all the open VB types (1 ÷ 16) next defined;
# 1 == DM_NORMAL_HOST_VB == TLC L2 == TLC type open VB for writing Host Data in Normal area partition when Write Booster disabled and chunk size enough for TLC die line;
# 2 == DM_NORMAL_WB_VB_0 == WB L2 == SLC type open VB for writing Host Data in Normal area partition when Write Booster enabled;
# 3 == DM_NORMAL_SHARE_VB_ 1 == SLC S_CHK L1 == SLC type open VB for writing Host Data in Normal area partition when Write Booster disabled and chunk size NOT enough for TLC die line (SLC small Chunk L1)
# 4 == DM_NORMAL_SHARE_VB_0 == EM1 L2 == SLC type open VB for writing Host Data in EM1 area (SLC only) partition;
# 5 == DM_RPMB_HOST_VB == SLC type open VB for writing Host Data in Replay Protected Mode Block (RPMB);
# 6 == DM_NORMAL_DEFRAG_VB == GC Normal == TLC type for writing Garbage Collection Data into Normal Area partition;
# 7 == DM_EM1_DEFRAG_VB == GC EM1 == SLC type for writing Garbage Collection Data into EM1 area partition;
# 8 == List == open VB used for storing tables;
# 9 == PTE == open VB used for storing 3rd-level tables;
# 10 == LOG == open VB used for storing tables;
# 11 == Index == open VB used for storing tables;
# 12 == DM_RAIN_PARITY_VB == SWAP_RAIN == open VB used for storing RAIN Parities;
# 13 == TMP_RAIN == open VB used for storing RAIN Parities;
# 14 == Drive Log == open VB used for storing tables;
# 15 == Pointer;
# 16 == BB Table;
class NextOpenVBInformation(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(68), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.amountofvalidvb = self.add_field(0, 3, 'little')
        self.DM_NORMAL_HOST_VB = self.add_field(4, 7, 'little')
        self.DM_NORMAL_WB_VB_0 = self.add_field(8, 11, 'little')
        self.DM_NORMAL_SHARE_VB_1 = self.add_field(12, 15, 'little')
        self.DM_NORMAL_SHARE_VB_0 = self.add_field(16, 19, 'little')
        self.DM_RPMB_HOST_VB = self.add_field(20, 23, 'little')
        self.DM_NORMAL_DEFRAG_VB = self.add_field(24, 27, 'little')
        self.DM_EM1_DEFRAG_VB = self.add_field(28, 31, 'little')
        self.List = self.add_field(32, 35, 'little')
        self.PTE = self.add_field(36, 39, 'little')
        self.LOG = self.add_field(40, 43, 'little')
        self.Index = self.add_field(44, 47, 'little')
        self.DM_RAIN_PARITY_VB = self.add_field(48, 51, 'little')
        self.TMP_RAIN = self.add_field(52, 55, 'little')
        self.Drive_Log = self.add_field(56, 59, 'little')
        self.Pointer = self.add_field(60, 63, 'little')
        self.BBT = self.add_field(64, 67, 'little')
