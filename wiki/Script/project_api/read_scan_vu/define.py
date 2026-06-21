from enum import Enum, IntEnum
from Script.api.ufs_api.defines.bit_define import *


class ReadScanVBInfoSubOperation(IntEnum):
    Enable_Disable_Read_Scan = 0x1
    Get_Normal_VB_Scan_Pages = 0x2
    Get_APL_flag_of_VB = 0x3
    Reserved = 0x4
    set_refresh_stop_page = 0x5
    get_gc_read_scan_released_scan_or_UECC_pageline = 0x6
    get_Normal_lock_list_VBs_number = 0x7
    check_if_source_VB_could_be_recovered_by_GC_source_recovery = 0x8
    check_if_current_VB_scan_in_progress_completed = 0x9

class RSTriggerBy(IntEnum):
    IGC = 0x0
    other = 0x1
