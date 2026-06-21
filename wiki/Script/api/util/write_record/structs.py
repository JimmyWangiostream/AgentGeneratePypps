from Script.api.ufs_api.defines import CmdParamPatternMode

class WriteRecordNode:
    def __init__(self) -> None:
        self.start_lba = 0
        self.end_lba = 0
        self.data_pattern_mode = CmdParamPatternMode.HW_INCREASE
        self.add_tag = 0  # LBA & WriteCnt 開關
        self.mark_tag = 0