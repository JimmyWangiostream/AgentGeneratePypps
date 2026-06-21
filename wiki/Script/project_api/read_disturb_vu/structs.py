import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from typing import List

class micron_vu_40CC(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.LogicalVB = self.add_field(12, 13, 'little')

class ReadDisturbTriggerInfo(PacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET, end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload=payload, start_offset=start_offset, end_offset=end_offset)
        self.FAIL_PASS_VU = self.add_field(0, 0, 'little')
        self.ReadDisturbContextBER_LogicalVB = self.add_field(1, 2, 'little')
        self.PhysicalPage = self.add_field(3, 4, 'little')
        self.Plane = self.add_field(5, 5, 'little')
        self.Die = self.add_field(6, 6, 'little')
        # LP:0 / UP:1 / XP:2
        self.PhysicalPageLUX = self.add_field(7, 7, 'little')
        self.Wordline = self.add_field(8, 9, 'little')
        self.IsSLCVBFlag = self.add_field(10, 10, 'little')
        self.ErasePageCheckFlag = self.add_field(11, 11, 'little')
        self.IsSinglePlaneReadFlag = self.add_field(12, 12, 'little')
        
class micron_vu_40CB(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.LogicalVB = self.add_field(12, 13, 'little')
        
class ReadDisturbRC(PacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET, end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload=payload, start_offset=start_offset, end_offset=end_offset)
        self.TotalReadCount_RC_VB = self.add_field(0, 3, 'little')
        self.FlushRCTableThreshold_RC_TH_VB = self.add_field(4, 7, 'little')
        self.SLCScanPageNumber_InputLogicalVB = self.add_field(8, 11, 'little')
        self.TLCScanPageNumber_InputLogicalVB = self.add_field(12, 15, 'little')
        self.RCCritical_InputLogicalVB = self.add_field(16, 19, 'little')
        self.Reserved = self.add_field(20, 23, 'little')
        self.CECCThreshold_ReadDisturbScan = self.add_field(24, 27, 'little')
        self.CECCThreshold_HostRead_REH = self.add_field(28, 31, 'little')
        self.IsScanTaskIdle = self.add_field(32, 35, 'little')
        self.IsVtDumpTaskIdle = self.add_field(36, 39, 'little')

class micron_vu_40CA(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        
class micron_vu_408C(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.wBlockType = self.add_field(12, 13, 'little')
        
class ReadThresholdSet(PacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET, end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload=payload, start_offset=start_offset, end_offset=end_offset)
        self.EraseCountThreshold = self.add_field(0, 3, 'little')
        self.ReadCountThreshold = self.add_field(4, 7, 'little')
        
        
class ReadDisturbSmartInfo(PacketParserComposerABC):
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET, end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload=payload, start_offset=start_offset, end_offset=end_offset)
        self.prdh_rand_trig_cnt       = self.add_field(0x110, 0x113, 'little')
        self.prdh_seq_trig_cnt        = self.add_field(0x114, 0x117, 'little')
        self.prdh_scan_pass_cnt       = self.add_field(0x118, 0x11B, 'little')
        self.prdh_scan_fail_cnt       = self.add_field(0x11C, 0x11F, 'little')
        self.prdh_scan_entry_skip_cnt = self.add_field(0x735, 0x738, 'little')