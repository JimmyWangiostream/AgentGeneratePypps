import struct
from Script.api.struct_helper import *
from typing import List, Tuple, Dict

class D017_param(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(20), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.die = self.add_field(0,0,'little')
        self.plane = self.add_field(1,1,'little')
        self.block = self.add_field(2,3,'little')
        self.error_inject_enable = self.add_field(4,4,'little')
        self.scan_type = self.add_field(5,5,'little')
        self.first_low_vt_scan = self.add_field(6,6,'little')
        self.touch_up = self.add_field(7,7,'little')
        self.low_vt_re_scan = self.add_field(8,8,'little')
        self.high_vt_scan = self.add_field(9,9,'little')
        self.switch = self.add_field(10,10,'little')
        self.index = self.add_field(11,11,'little')
        self.rev = self.add_field(12,19,'little')
class C071_param(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(64), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.sgs_scan_dynamic_read_count = self.add_field(0,7,'little')
        self.sgs_scan_dynamic_event_cnt: list[BaseField] = []
        self.sgs_scan_static_event_cnt: list[BaseField] = []
        dynamic_offset = 8
        for i in range(6):
            self.sgs_scan_dynamic_event_cnt.append(self.add_field(dynamic_offset+ i*4,dynamic_offset+i*4+3,'little'))
        static_offset = 32
        for i in range(6):
            self.sgs_scan_static_event_cnt.append(self.add_field(static_offset+ i*4,static_offset+i*4+3,'little'))
        self.sgs_scan_static_read_count = self.add_field(56,63,'little')


class VU_4071_struct(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(3240), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.curr_read_count_TLC = self.add_field(0,7,'little')
        self.remain_read_count_trigger_sgs_TLC = self.add_field(8,15,'little')
        self.sgs_read_count_threshold = self.add_field(16,23,'little')
        self.sgs_read_count_threshold_list:list[BaseField] = []
        rc_thres_offset = 24
        for i in range(4):
            self.sgs_read_count_threshold_list.append(self.add_field(rc_thres_offset+ i*8,rc_thres_offset+i*8+7,'little'))

        self.sgs_scan_window_list : list[BaseField] = []
        scan_window_offset = 56
        for i in range(5):
            self.sgs_scan_window_list.append(self.add_field(scan_window_offset+ i*4,scan_window_offset+i*4+3,'little'))
        self.sgs_scan_event_cnt_TLC:list[BaseField] = []
        event_tlc_offset = 76
        for i in range(6):
            self.sgs_scan_event_cnt_TLC.append(self.add_field(event_tlc_offset+ i*4,event_tlc_offset+i*4+3,'little'))

        self.sgs_scan_flagged_physical_vb_cnt = self.add_field(100,103,'little')
        self.sgs_scan_flagged_physical_vbNumb:list[BaseField] = []
        vbnumb_offset = 104
        for i in range(774):
            self.sgs_scan_flagged_physical_vbNumb.append(self.add_field(vbnumb_offset+ i*4,vbnumb_offset+i*4+3,'little'))
        
        self.remain_read_count_trigger_sgs_SLC = self.add_field(3200,3207,'little') 
        self.curr_read_count_SLC = self.add_field(3208,3215,'little') 
        self.sgs_scan_event_cnt_SLC:list[BaseField] = []
        event_slc_offset = 3216
        for i in range(6):
            self.sgs_scan_event_cnt_SLC.append(self.add_field(event_slc_offset+ i*4,event_slc_offset+i*4+3,'little'))



class EventLog0026(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(34), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.log_id          = self.add_field(0, 3, 'little')
        self.magicNum        = self.add_field(4, 7, 'little')
        self.Channel         = self.add_field(8, 8, 'little')
        self.CE              = self.add_field(9, 9, 'little')
        self.LUN             = self.add_field(10, 10, 'little')
        self.SubBlock        = self.add_field(11, 11, 'little')
        self.BlockPhysical   = self.add_field(12, 13, 'little')
        self.ScanCode        = self.add_field(14, 14, 'little')
        self.SelGateTarget   = self.add_field(15, 15, 'little')
        self.SR              = self.add_field(16, 16, 'little')
        self.ESR             = self.add_field(17, 17, 'little')
        self.reserved        = self.add_field(18, 30, 'little')
        self.blockPEC        = self.add_field(31, 32, 'little')
        self.tempC           = self.add_field(33, 33, 'little')
        self.PoS             = self.add_field(34, 37, 'little')
        
class EventLog6002(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(75), start_offset: int = AUTO_OFFSET, end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload=payload, start_offset=start_offset, end_offset=end_offset)
        self.log_id             = self.add_field(0, 3, 'little')
        self.magicNum           = self.add_field(4, 7, 'little')
        self.die                = self.add_field(8, 8, 'little')
        self.opType_slcMode     = self.add_field(9, 9, 'little')
        self.multiPlane         = self.add_field(10, 10, 'little')
        self.startPlane         = self.add_field(11, 11, 'little')
        self.allPlaneFail       = self.add_field(12, 12, 'little')
        self.failedPlane        = self.add_field(13, 13, 'little')
        self.failedSubType      = self.add_field(14, 14, 'little')
        self.bufAddrMode        = self.add_field(15, 15, 'little')
        self.block_list: list[BaseField] = []
        for i in range(6):
            self.block_list.append(self.add_field(16 + i * 2, 17 + i * 2, 'little'))
        self.page_errType       = self.add_field(28, 31, 'little')
        self.refBookingList     = self.add_field(32, 33, 'little')
        self.errTypeOrigin      = self.add_field(34, 34, 'little')
        self.touchUpPlnBit_list: list[BaseField] = []
        for i in range(4):
            self.touchUpPlnBit_list.append(self.add_field(35 + i, 35 + i, 'little'))
        self.dataMode           = self.add_field(39, 39, 'little')
        self.scanSG             = self.add_field(40, 40, 'little')
        self.seedBits           = self.add_field(41, 42, 'little')
        self.tailFlag           = self.add_field(43, 46, 'little')
        self.blockEC            = self.add_field(47, 50, 'little')
        self.esrPresentPlaneLow = self.add_field(51, 54, 'little')
        self.esrPlaneHigh_rev   = self.add_field(55, 57, 'little')
        self.failBitmap         = self.add_field(58, 61, 'little')
        self.driveRc_list: list[BaseField] = []
        for i in range(2):
            self.driveRc_list.append(self.add_field(62 + i * 4, 65 + i * 4, 'little'))
        self.phyVB              = self.add_field(70, 71, 'little')
        self.logVB              = self.add_field(72, 73, 'little')
        self.dppmBitmap         = self.add_field(74, 74, 'little')

class EventLog6009(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(75), start_offset: int = AUTO_OFFSET, end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload=payload, start_offset=start_offset, end_offset=end_offset)
        self.log_id             = self.add_field(0, 3, 'little')
        self.magicNum           = self.add_field(4, 7, 'little')
        self.die                = self.add_field(8, 8, 'little')
        self.opType_slcMode     = self.add_field(9, 9, 'little')
        self.multiPlane         = self.add_field(10, 10, 'little')
        self.startPlane         = self.add_field(11, 11, 'little')
        self.allPlaneFail       = self.add_field(12, 12, 'little')
        self.failedPlane        = self.add_field(13, 13, 'little')
        self.failedSubType      = self.add_field(14, 14, 'little')
        self.bufAddrMode        = self.add_field(15, 15, 'little')
        self.block_list: list[BaseField] = []
        for i in range(6):
            self.block_list.append(self.add_field(16 + i * 2, 17 + i * 2, 'little'))
        self.page_errType       = self.add_field(28, 31, 'little')
        self.refBookingList     = self.add_field(32, 33, 'little')
        self.errTypeOrigin      = self.add_field(34, 34, 'little')
        self.touchUpPlnBit_list: list[BaseField] = []
        for i in range(4):
            self.touchUpPlnBit_list.append(self.add_field(35 + i, 35 + i, 'little'))
        self.dataMode           = self.add_field(39, 39, 'little')
        self.scanSG             = self.add_field(40, 40, 'little')
        self.seedBits           = self.add_field(41, 42, 'little')
        self.tailFlag           = self.add_field(43, 46, 'little')
        self.blockEC            = self.add_field(47, 50, 'little')
        self.esrPresentPlaneLow = self.add_field(51, 54, 'little')
        self.esrPlaneHigh_rev   = self.add_field(55, 57, 'little')
        self.failBitmap         = self.add_field(58, 61, 'little')
        self.driveRc_list: list[BaseField] = []
        for i in range(2):
            self.driveRc_list.append(self.add_field(62 + i * 4, 65 + i * 4, 'little'))
        self.phyVB              = self.add_field(70, 71, 'little')
        self.logVB              = self.add_field(72, 73, 'little')
        self.dppmBitmap         = self.add_field(74, 74, 'little')
        
class EventLog6008(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(75), start_offset: int = AUTO_OFFSET, end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload=payload, start_offset=start_offset, end_offset=end_offset)
        self.log_id             = self.add_field(0, 3, 'little')
        self.magicNum           = self.add_field(4, 7, 'little')
        self.die                = self.add_field(8, 8, 'little')
        self.opType_slcMode     = self.add_field(9, 9, 'little')
        self.multiPlane         = self.add_field(10, 10, 'little')
        self.startPlane         = self.add_field(11, 11, 'little')
        self.allPlaneFail       = self.add_field(12, 12, 'little')
        self.failedPlane        = self.add_field(13, 13, 'little')
        self.failedSubType      = self.add_field(14, 14, 'little')
        self.bufAddrMode        = self.add_field(15, 15, 'little')
        self.block_list: list[BaseField] = []
        for i in range(6):
            self.block_list.append(self.add_field(16 + i * 2, 17 + i * 2, 'little'))
        self.page_errType       = self.add_field(28, 31, 'little')
        self.refBookingList     = self.add_field(32, 33, 'little')
        self.errTypeOrigin      = self.add_field(34, 34, 'little')
        self.touchUpPlnBit_list: list[BaseField] = []
        for i in range(4):
            self.touchUpPlnBit_list.append(self.add_field(35 + i, 35 + i, 'little'))
        self.dataMode           = self.add_field(39, 39, 'little')
        self.scanSG             = self.add_field(40, 40, 'little')
        self.seedBits           = self.add_field(41, 42, 'little')
        self.tailFlag           = self.add_field(43, 46, 'little')
        self.blockEC            = self.add_field(47, 50, 'little')
        self.esrPresentPlaneLow = self.add_field(51, 54, 'little')
        self.esrPlaneHigh_rev   = self.add_field(55, 57, 'little')
        self.failBitmap         = self.add_field(58, 61, 'little')
        self.driveRc_list: list[BaseField] = []
        for i in range(2):
            self.driveRc_list.append(self.add_field(62 + i * 4, 65 + i * 4, 'little'))
        self.phyVB              = self.add_field(70, 71, 'little')
        self.logVB              = self.add_field(72, 73, 'little')
        self.dppmBitmap         = self.add_field(74, 74, 'little')


