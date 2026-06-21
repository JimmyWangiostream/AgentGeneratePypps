import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from typing import List

class micron_vu_C072(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        
class micron_vu_4098(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.bParameter0 = self.add_field(12, 12, 'little')
        self.bParameter1 = self.add_field(13, 13, 'little')

class WearLevelingECData(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.EC = self.add_field_bit(0,19, 'little')
        self.VBListNum = self.add_field_bit(20,24, 'little')
        self.OpenVBType = self.add_field_bit(27,30, 'little')
        self.IsDfgSrc = self.add_field_bit(31,31, 'little')

class WearLevelingVERData(BITPacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.version = self.add_field_bit(0,26, 'little')
        self.force_bit = self.add_field_bit(27,27, 'little')
        self.open_type = self.add_field_bit(28,31, 'little')

class WearLevelingInformation(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        DM_NUM_ALL_VB = 502
        DM_OPEN_VB_TYPE_NUM = 8

        # ---------- Header ----------
        self.data_size = self.add_field(0, 3, 'little')

        # ---------- EC data of VBs ----------
        self.EC_data_of_VBs: List[WearLevelingECData] = []
        offset = 4
        for vb in range(DM_NUM_ALL_VB):
            self.EC_data_of_VBs.append(
                WearLevelingECData(payload,
                                   offset + vb * 4,
                                   offset + (vb + 1) * 4 - 1)
            )

        # ---------- VER data of VBs ----------
        self.VER_data_of_VBs: List[WearLevelingVERData] = []
        offset = 4096
        for vb in range(DM_NUM_ALL_VB):
            self.VER_data_of_VBs.append(
                WearLevelingVERData(payload,
                                    offset + vb * 4,
                                    offset + (vb + 1) * 4 - 1)
            )

        # ---------- Global fields (from Dword 0 at 8192) ----------
        d = lambda n: (8192 + n * 4, 8192 + n * 4 + 3)

        self.size_in_byte_of_following_data = self.add_field(*d(0), 'little')
        self.SWLEnable = self.add_field(*d(1), 'little')

        self.EC_Threshold_of_static_pool = self.add_field(*d(2), 'little')
        self.EC_Threshold_of_dynamic_pool = self.add_field(*d(3), 'little')
        self.EC_Threshold_of_ICS_pool = self.add_field(*d(4), 'little')

        self.Global_Erase_Counter_of_static_pool = self.add_field(*d(5), 'little')
        self.Global_Erase_Counter_of_dynamic_pool = self.add_field(*d(6), 'little')
        self.Global_Erase_Counter_of_ICS_pool = self.add_field(*d(7), 'little')

        self.Global_Erase_Counter_of_static_pool_for_open_block = self.add_field(*d(8), 'little')
        self.Global_Erase_Counter_of_dynamic_pool_for_open_block = self.add_field(*d(9), 'little')
        self.reserved_open_ICS = self.add_field(*d(10), 'little')

        self.EC_gap_delta_Threshold_TH1_of_static_pool = self.add_field(*d(11), 'little')
        self.EC_gap_delta_Threshold_TH1_of_dynamic_pool = self.add_field(*d(12), 'little')
        self.EC_gap_delta_Threshold_TH1_of_ICS_pool = self.add_field(*d(13), 'little')

        self.EC_gap_delta_Threshold_TH2_of_static_pool = self.add_field(*d(14), 'little')
        self.EC_gap_delta_Threshold_TH2_of_dynamic_pool = self.add_field(*d(15), 'little')
        self.EC_gap_delta_Threshold_TH2_of_ICS_pool = self.add_field(*d(16), 'little')

        self.Search_selection_range_length_of_static_pool = self.add_field(*d(17), 'little')
        self.Search_selection_range_length_of_dynamic_pool = self.add_field(*d(18), 'little')
        self.Search_selection_range_length_of_ICS_pool = self.add_field(*d(19), 'little')

        self.globalVersion_of_static_pool = self.add_field(*d(20), 'little')
        self.globalVersion_of_dynamic_pool = self.add_field(*d(21), 'little')
        self.globalVersion_of_ICS_pool = self.add_field(*d(22), 'little')

        self.boundaryVersion_of_static_pool = self.add_field(*d(23), 'little')
        self.boundaryVersion_of_dynamic_pool = self.add_field(*d(24), 'little')
        self.boundaryVersion_of_ICS_pool = self.add_field(*d(25), 'little')

        # ✅ Version delta threshold
        self.Version_delta_Threshold_of_static_pool = self.add_field(*d(26), 'little')
        self.Version_delta_Threshold_of_dynamic_pool = self.add_field(*d(27), 'little')
        self.Version_delta_Threshold_of_ICS_pool = self.add_field(*d(28), 'little')

        self.pendingSrcDepth_for_Low_priority_of_static_pool = self.add_field(*d(29), 'little')
        self.pendingSrcDepth_for_Low_priority_of_dynamic_pool = self.add_field(*d(30), 'little')
        self.pendingSrcDepth_for_Low_priority_of_ICS_pool = self.add_field(*d(31), 'little')

        self.pendingSrcCount_for_Low_priority_of_static_pool = self.add_field(*d(32), 'little')
        self.pendingSrcCount_for_Low_priority_of_dynamic_pool = self.add_field(*d(33), 'little')
        self.pendingSrcCount_for_Low_priority_of_ICS_pool = self.add_field(*d(34), 'little')

        self.totalSWLTriggerCount_of_static_pool = self.add_field(*d(35), 'little')
        self.totalSWLTriggerCount_of_dynamic_pool = self.add_field(*d(36), 'little')
        self.totalSWLTriggerCount_of_ICS_pool = self.add_field(*d(37), 'little')

        self.totalSWLJudgeCount_of_static_pool = self.add_field(*d(38), 'little')
        self.totalSWLJudgeCount_of_dynamic_pool = self.add_field(*d(39), 'little')
        self.totalSWLJudgeCount_of_ICS_pool = self.add_field(*d(40), 'little')

        self.totalSWLJudgePassCount_of_static_pool = self.add_field(*d(41), 'little')
        self.totalSWLJudgePassCount_of_dynamic_pool = self.add_field(*d(42), 'little')
        self.totalSWLJudgePassCount_of_ICS_pool = self.add_field(*d(43), 'little')

        self.totalSWLRefreshBookCount_of_static_pool = self.add_field(*d(44), 'little')
        self.totalSWLRefreshBookCount_of_dynamic_pool = self.add_field(*d(45), 'little')
        self.totalSWLRefreshBookCount_of_ICS_pool = self.add_field(*d(46), 'little')

        self.totalSWLRefreshDoneCount_of_static_pool = self.add_field(*d(47), 'little')
        self.totalSWLRefreshDoneCount_of_dynamic_pool = self.add_field(*d(48), 'little')
        self.totalSWLRefreshDoneCount_of_ICS_pool = self.add_field(*d(49), 'little')

        self.totalSWLRefreshMissCount_of_static_pool = self.add_field(*d(50), 'little')
        self.totalSWLRefreshMissCount_of_dynamic_pool = self.add_field(*d(51), 'little')
        self.totalSWLRefreshMissCount_of_ICS_pool = self.add_field(*d(52), 'little')

        self.totalSWLGCTriggerCount_of_static_pool = self.add_field(*d(53), 'little')
        self.totalSWLGCTriggerCount_of_dynamic_pool = self.add_field(*d(54), 'little')

        self.totalSWLBGGCTriggerCount_of_static_pool = self.add_field(*d(55), 'little')
        self.totalSWLBGGCTriggerCount_of_dynamic_pool = self.add_field(*d(56), 'little')

        self.totalSWLFGGCTriggerCount_of_static_pool = self.add_field(*d(57), 'little')
        self.totalSWLFGGCTriggerCount_of_dynamic_pool = self.add_field(*d(58), 'little')

        self.totalSWLGCDoneCount_of_static_pool = self.add_field(*d(59), 'little')
        self.totalSWLGCDoneCount_of_dynamic_pool = self.add_field(*d(60), 'little')

        self.totalSWLGCMissCount_of_static_pool = self.add_field(*d(61), 'little')
        self.totalSWLGCMissCount_of_dynamic_pool = self.add_field(*d(62), 'little')

        # ---------- Open VB versions ----------
        self.version_of_open_VBs: List[BaseField] = []
        for i in range(DM_OPEN_VB_TYPE_NUM):
            self.version_of_open_VBs.append(
                self.add_field(*d(63 + i), 'little')
            )

        self.max_erase_counter_0_for_Static_pool = self.add_field(*d(71), 'little')
        self.max_erase_counter_0_for_Dynamic_pool = self.add_field(*d(72), 'little')
        self.max_erase_counter_0_for_ICS_pool = self.add_field(*d(73), 'little')
        self.SWL_ongoing_flag = self.add_field(*d(74), 'little')
        self.total_op_block_of_static_pool = self.add_field(*d(75), 'little')
        self.total_op_block_of_dynamic_pool = self.add_field(*d(76), 'little')