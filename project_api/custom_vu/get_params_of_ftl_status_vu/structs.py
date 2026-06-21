import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd
from typing import List
from enum import Enum, IntEnum
class PowerLossFlag(IntEnum):
    """Power‑loss / flag bits defined in the DM_PL_FLAG_MASK docs."""
    INIT_DONE                                   = 1 << 0   # DM_PL_FLAG_MASK_INIT_DONE
    SYS_PL                                      = 1 << 1   # DM_PL_FLAG_MASK_SYS_PL
    REBUILD_ST_FROM_APLLOG                      = 1 << 2   # DM_PL_FLAG_MASK_REBUILD_ST_FROM_APLLOG
    HOST_PL                                     = 1 << 3   # DM_PL_FLAG_MASK_HOST_PL
    DEFG_PL                                     = 1 << 4   # DM_PL_FLAG_MASK_DEFG_PL
    APL_REWRITE                                 = 1 << 5   # DM_PL_FLAG_MASK_APL_REWRITE
    APL_RELOCATE                                = 1 << 6   # DM_PL_FLAG_MASK_APL_RELOCATE
    BBT_DANCING                                 = 1 << 7   # DM_PL_FLAG_MASK_BBT_DANCING
    FLUSH_FGCL                                  = 1 << 8   # DM_PL_FLAG_MASK_FLUSH_FGCL
    RPMB_GROUP_NEED_DROP                        = 1 << 9   # DM_PL_FLAG_MASK_RPMB_GROUP_NEED_DROP
    FLUSH_ST_TO_TLC_IN_RELOCATE                 = 1 << 10  # DM_PL_FLAG_MASK_FLUSH_ST_TO_TLC_IN_RELOCATE
    HOST_VB_UECC_VP_REBUILD                     = 1 << 11  # DM_PL_FLAG_MASK_HOST_VB_UECC_VP_REBUILD
    UNEXPECTED_VER_REBUILD                      = 1 << 12  # DM_PL_FLAG_MASK_UNEXPECTED_VER_REBUILD
    REBUILD_HOST_VB                             = 1 << 13  # DM_PL_FLAG_MASK_REBUILD_HOST_VB
    REBUILD_DEFRAG_VB                           = 1 << 14  # DM_PL_FLAG_MASK_REBUILD_DEFRAG_VB
    LOAD_BVRT                                   = 1 << 15  # DM_PL_FLAG_MASK_LOAD_BVRT
    READ_UECC                                   = 1 << 16  # DM_PL_FLAG_MASK_READ_UECC
    HOST_DUMMY_BOOT_LUN                         = 1 << 17  # DM_PL_FLAG_MASK_HOST_DUMMY_BOOT_LUN
    RPMB_READ_UECC                              = 1 << 18  # DM_PL_FLAG_MASK_RPMB_READ_UECC
    CHANGE_DEFRAG_VB                            = 1 << 19  # DM_PL_FLAG_MASK_CHANGE_DEFRAG_VB
    CHANGE_HOST_VB                              = 1 << 20  # DM_PL_FLAG_MASK_CHANGE_HOST_VB
    DEFRAG_EOB_NOT_DO_RELIABLE_CHECK            = 1 << 21  # DM_PL_FLAG_MASK_DEFRAG_EOB_NOT_DO_RELIABLE_CHECK
    HOST_EOB_NOT_DO_RELIABLE_CHECK              = 1 << 22  # DM_PL_FLAG_MASK_HOST_EOB_NOT_DO_RELIABLE_CHECK
    LOAD_BGCL                                   = 1 << 23  # DM_PL_FLAG_MASK_LOAD_BGCL
    HOST_CHANGE_LOG_FULL                        = 1 << 24  # DM_PL_FLAG_MASK_HOST_CHANGE_LOG_FULL
    BACK_TO_BACK_APL_HAPPEN                     = 1 << 25  # DM_PL_FLAG_BACK_TO_BACK_APL_HAPPEN
    REFRESH_PL                                  = 1 << 26  # DM_PL_FLAG_MASK_REFRESH_PL
    UECC_BEFORE_LSP                             = 1 << 27  # DM_PL_FLAG_MASK_UECC_BEFORE_LSP
    CHANGE_SOURCE_VB                            = 1 << 28  # DM_PL_FLAG_MASK_CHANGE_SOURCE_VB
    START_PPT_RECOVERY                          = 1 << 29  # DM_PL_FLAG_MASK_START_PPT_RECOVERY
    REFRESH_BACKUP_VB                           = 1 << 30  # DM_PL_FLAG_MASK_REFRESH_BACKUP_VB
    FLUSH_PERMANENT_IN_RELOCATE                 = 1 << 31  # DM_PL_FLAG_MASK_FLUSH_PERMANENT_IN_RELOCATE

class OpenDataVBType(IntEnum):
    DM_NORMAL_HOST_VB = 0										
    DM_NORMAL_WB_VB_0 = 1										
    DM_NORMAL_SHARE_VB_1 = 2									
    DM_NORMAL_SHARE_VB_0 = 3		#EM1							
    DM_RPMB_HOST_VB = 4				#not used						
    DM_NORMAL_DEFRAG_VB	= 5										
    DM_EM1_DEFRAG_VB = 6
class OpenSystemVBType(IntEnum):
    PT = 0										
    INDEX = 1										
    DUMMY = 2																		

class AplInfo(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(12), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)								
        self.last_written_page = self.add_field(0,3,'little')
        self.apl_status_of_host_vb = self.add_field(4,7,'little')
        self.apl_status_of_first_empty_page = self.add_field(8,11,'little')

class OpenDataVB(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(320), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.host_logic_vb_number = self.add_field(0, 3, 'little')
        self.host_physical_vb_number = self.add_field(4, 7, 'little')
        self.vb_is_slc = self.add_field(8, 11, 'little')
        self.host_vb_first_free_pp = self.add_field(12,15,'little')
        self.host_vb_last_valid_page = self.add_field(16,19,'little')
        self.host_vb_last_stable_page = self.add_field(20,23,'little')
        offset = start_offset + 24 + 8
        size_per_item = 12
        stride_m = 6 * size_per_item
        stride_n = size_per_item
        self.apl_status_list: List[List[AplInfo]] = [[] for _ in range(4)]   
        for m in range(4):  #ce
            for n in range(6): #plane
                start = offset + m * stride_m + n * stride_n
                end   = start + size_per_item - 1
                self.apl_status_list[m].append(
                    AplInfo(payload, start_offset=start, end_offset=end)
                )
class OpenSystemVB(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(30), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.ftl_system_info_vb_number = self.add_field(0, 3, 'little')
        self.ftl_system_info_die_number = self.add_field(4, 7, 'little')
        self.ftl_system_info_start_plane = self.add_field(8, 11, 'little')
        self.ftl_system_info_block_count = self.add_field(12, 15, 'little')
        self.ftl_system_info_version = self.add_field(16, 19, 'little')
        self.ftl_system_info_ffpp = self.add_field(20, 23, 'little')
        self.preboot_bsearch = self.add_field(24, 47, 'little')

class TableVB(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(296), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.table_vb_number = self.add_field(0,3,'little')
        self.first_free_pp_in_table_vb = self.add_field(4,7,'little')
        offset = start_offset + 8
        size_per_item = 12
        stride_m = 6 * size_per_item
        stride_n = size_per_item
        self.apl_status_list: List[List[AplInfo]] = [[] for _ in range(4)]   
        for m in range(4):  #ce
            for n in range(6): #plane
                start = offset + m * stride_m + n * stride_n
                end   = start + size_per_item - 1
                self.apl_status_list[m].append(
                    AplInfo(payload, start_offset=start, end_offset=end)
                )
class VU_40C3_struct(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(6144), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        #-- part1 --
        self.buffer_size = self.add_field(0, 3, 'little')
        self.power_loss_flag = self.add_field(4, 7, 'little')
        
        #-- APL for 7 Open data VB cursors --
        self.open_data_vb : List[OpenDataVB]= []
        offset = 8
        for i in range(len(OpenDataVBType)):
            self.open_data_vb.append(OpenDataVB(payload, start_offset=offset+i*320,end_offset=offset+(i+1)*320 -1))
        
        #-- APL for Table VB --
        table_offset = 2248
        self.table_vb = TableVB(payload,start_offset=table_offset, end_offset=table_offset+296-1)
        
        #-- APL for 3 Open system VB cursors loops --
        self.open_system_vb : List[OpenSystemVB]= []
        system_offset = 2544
        for i in range(len(OpenSystemVBType)):
            self.open_system_vb.append(OpenSystemVB(payload, start_offset=system_offset+i*30,end_offset=system_offset+(i+1)*30 -1))
        
        self.init_latency_info = self.add_field(2634, 2753, 'little')
        self.check_info = self.add_field(2754, 2769, 'little')
        self.recordB2BAplNotHappen = self.add_field(2770, 2773, 'little')
        self.AplEmptyInfo = self.add_field(2774, 2845, 'little')
        
        #-- part2 --
        p2_offset = 3072
        p3_offset = 3072 + 1024
        p4_offset = 3072 + 1024 * 2
        self.hostSLCDataSize_NORMAL           = self.add_field(p2_offset +   0, p2_offset +   3, 'little')
        self.hostSLCDataSize_WriteBooster     = self.add_field(p2_offset +   4, p2_offset +   7, 'little')
        self.l1032_do_not_care                = self.add_field(p2_offset +   8, p2_offset +  11, 'little')
        self.hostSLCDataSize_EM1              = self.add_field(p2_offset +  12, p2_offset +  15, 'little')
        self.hostSLCDataSize_RPMB             = self.add_field(p2_offset +  16, p2_offset +  19, 'little')
        self.hostTLCDataSize_NORMAL           = self.add_field(p2_offset +  20, p2_offset +  23, 'little')
        self.hostTLCDataSize_WriteBooster     = self.add_field(p2_offset +  24, p2_offset +  27, 'little')
        self.l1052_do_not_care                = self.add_field(p2_offset +  28, p2_offset +  31, 'little')
        self.hostTLCDataSize_EM1              = self.add_field(p2_offset +  32, p2_offset +  35, 'little')
        self.hostTLCDataSize_RPMB             = self.add_field(p2_offset +  36, p2_offset +  39, 'little')
        self.GCSLCDataSize_NORMAL             = self.add_field(p2_offset +  40, p2_offset +  43, 'little')
        self.GCSLCDataSize_EM1                = self.add_field(p2_offset +  44, p2_offset +  47, 'little')
        self.GCTLCDataSize_NORMAL             = self.add_field(p2_offset +  48, p2_offset +  51, 'little')
        self.GCTLCDataSize_EM1                = self.add_field(p2_offset +  52, p2_offset +  55, 'little')
        self.hostSLCDummySize_NORMAL          = self.add_field(p2_offset +  56, p2_offset +  59, 'little')
        self.hostSLCDummySize_WriteBooster    = self.add_field(p2_offset +  60, p2_offset +  63, 'little')
        self.do_not_care_1                    = self.add_field(p2_offset +  64, p2_offset +  67, 'little')
        self.hostSLCDummySize_EM1             = self.add_field(p2_offset +  68, p2_offset +  71, 'little')
        self.hostSLCDummySize_RPMB            = self.add_field(p2_offset +  72, p2_offset +  75, 'little')
        self.hostTLCDummySize_NORMAL          = self.add_field(p2_offset +  76, p2_offset +  79, 'little')
        self.hostTLCDummySize_WriteBooster    = self.add_field(p2_offset +  80, p2_offset +  83, 'little')
        self.do_not_care_2                    = self.add_field(p2_offset +  84, p2_offset +  87, 'little')
        self.hostTLCDummySize_EM1             = self.add_field(p2_offset +  88, p2_offset +  91, 'little')
        self.hostTLCDummySize_RPMB            = self.add_field(p2_offset +  92, p2_offset +  95, 'little')
        self.GCSLCDummySize_NORMAL            = self.add_field(p2_offset +  96, p2_offset +  99, 'little')
        self.GCSLCDummySize_EM1               = self.add_field(p2_offset + 100, p2_offset + 103, 'little')
        self.GCTLCDummySize_NORMAL            = self.add_field(p2_offset + 104, p2_offset + 107, 'little')
        self.GCTLCDummySize_EM1               = self.add_field(p2_offset + 108, p2_offset + 111, 'little')
        self.hostSLCOpenVBCount        = self.add_field(p2_offset + 112,  p2_offset + 115, 'little')  # 保留
        self.hostTLCOpenVBCount        = self.add_field(p2_offset + 116,  p2_offset + 119, 'little')
        self.GCOpenVBCount             = self.add_field(p2_offset + 120,  p2_offset + 123, 'little')
        self.EM1OpenVBCount            = self.add_field(p2_offset + 124,  p2_offset + 127, 'little')
        self.EM1GCOpenVBCount          = self.add_field(p2_offset + 128,  p2_offset + 131, 'little')
        self.flowCtrlCount             = self.add_field(p2_offset + 132,  p2_offset + 387, 'little')
        self.maxResourceRequireCount   = self.add_field(p2_offset + 388,  p2_offset + 415, 'little')
        self.oneShotTableDefragCount   = self.add_field(p2_offset + 416,  p2_offset + 419, 'little')
        self.sliceTableDefragCount     = self.add_field(p2_offset + 420,  p2_offset + 423, 'little')
        self.maxHostGCCadence          = self.add_field(p2_offset + 424,  p2_offset + 431, 'little')
        self.maxTableGCCadence         = self.add_field(p2_offset + 432,  p2_offset + 435, 'little')
        self.discardCount              = self.add_field(p2_offset + 436,  p2_offset + 439, 'little')
        self.eraseCount                = self.add_field(p2_offset + 440,  p2_offset + 443, 'little')
        self.rpmbUnmapCount            = self.add_field(p2_offset + 444,  p2_offset + 447, 'little')
        self.wipeDeviceCount           = self.add_field(p2_offset + 448,  p2_offset + 451, 'little')
        self.hostSlcECCount            = self.add_field(p2_offset + 452,  p2_offset + 455, 'little')
        self.hostTlcECCount            = self.add_field(p2_offset + 456,  p2_offset + 459, 'little')
        self.EM1ECCount                = self.add_field(p2_offset + 460,  p2_offset + 463, 'little')
        self.hostLastSLCOpenVBCount    = self.add_field(p2_offset + 464,  p2_offset + 467, 'little')
        self.hostLastTLCOpenVBCount    = self.add_field(p2_offset + 468,  p2_offset + 471, 'little')
        self.GCLastOpenVBCount         = self.add_field(p2_offset + 472,  p2_offset + 475, 'little')
        self.tableSize                 = self.add_field(p2_offset + 476,  p2_offset + 515, 'little')
        self.tableDummySize            = self.add_field(p2_offset + 516,  p2_offset + 519, 'little')
        self.FTLECCount                = self.add_field(p2_offset + 520,  p2_offset + 523, 'little')
        self.FEECCount                 = self.add_field(p2_offset + 524,  p2_offset + 527, 'little')
        self.RefreshCnt                = self.add_field(p2_offset + 528,  p2_offset + 531, 'little')
        self.vRLC_trim_Update_number   = self.add_field(p2_offset + 532,  p2_offset + 535, 'little')
        self.Read_Disturb_Trigger_Num  = self.add_field(p2_offset + 536,  p2_offset + 539, 'little')
        self.Media_Scan_finished_Instance_Num = self.add_field(p2_offset + 540,  p2_offset + 543, 'little')
        self.FBOParticalData           = self.add_field(p2_offset + 544,  p2_offset + 547, 'little')
        self.FBOData100MB              = self.add_field(p2_offset + 548,  p2_offset + 551, 'little')
        self.FBODummyData              = self.add_field(p2_offset + 552,  p2_offset + 555, 'little')
        self.counterDeltaT1            = self.add_field(p2_offset + 556,  p2_offset + 559, 'little')
        self.counterDeltaT2            = self.add_field(p2_offset + 560,  p2_offset + 563, 'little')
        self.counterDeltaT3            = self.add_field(p2_offset + 564,  p2_offset + 567, 'little')
        self.counterDeltaT4            = self.add_field(p2_offset + 568,  p2_offset + 571, 'little')
        self.counterDeltaT5            = self.add_field(p2_offset + 572,  p2_offset + 575, 'little')
        self.pinSlcData                                    = self.add_field(p2_offset + 576,  p2_offset + 583, 'little')
        self.pinSlcDfgData                                 = self.add_field(p2_offset + 584,  p2_offset + 591, 'little')
        self.xTempColdToHotStatCounter                     = self.add_field(p2_offset + 592,  p2_offset + 595, 'little') #40
        self.xTempHotToColdStatCounter                     = self.add_field(p2_offset + 632,  p2_offset + 635, 'little') #40
        self.idleTimeAndHybernate                          = self.add_field(p2_offset + 672,  p2_offset + 675, 'little')
        self.refreshCountDone                              = self.add_field(p2_offset + 676,  p2_offset + 679, 'little')
        self.sliceRefreshDone                              = self.add_field(p2_offset + 680,  p2_offset + 683, 'little')
        self.bfeaFinishScanVB                              = self.add_field(p2_offset + 684,  p2_offset + 687, 'little')
        self.mediaScanFinishScanVB                         = self.add_field(p2_offset + 688,  p2_offset + 691, 'little')
        self.mediaScanBookVbCount                          = self.add_field(p2_offset + 692,  p2_offset + 695, 'little')
        self.aplBookVbCount                                = self.add_field(p2_offset + 696,  p2_offset + 699, 'little')
        self.rehBookVbCount                                = self.add_field(p2_offset + 700,  p2_offset + 703, 'little')
        self.vRLC_scan_trigger_VB_total_count              = self.add_field(p2_offset + 704,  p2_offset + 707, 'little')
        self.read_disturb_scan_trigger_VB_total_count      = self.add_field(p2_offset + 708,  p2_offset + 711, 'little')
        self.media_scan_trigger_vb_total_count             = self.add_field(p2_offset + 712,  p2_offset + 715, 'little')
        self.Table_defrag_source_VB                        = self.add_field(p2_offset + 716,  p2_offset + 719, 'little')
        self.Total_slice_table_defrag_count                = self.add_field(p2_offset + 720,  p2_offset + 723, 'little')
        self.Total_one_shot_table_defrag_count             = self.add_field(p2_offset + 724,  p2_offset + 727, 'little')
        self.Max_reduced_table_VB_count                    = self.add_field(p2_offset + 728,  p2_offset + 731, 'little')
        self.Table_defrag_PVT_slice_count                  = self.add_field(p2_offset + 732,  p2_offset + 735, 'little')

        self.isbbtInfoValid                 = self.add_field(p3_offset + 0, p3_offset + 3, 'little')
        self.bbtCurSubVBIdx                 = self.add_field(p3_offset + 4, p3_offset + 7, 'little')
        self.bbtFirstFreePP                 = self.add_field(p3_offset + 8, p3_offset + 11, 'little')

        self.write_data_volume_25MB          = self.add_field(p4_offset +   0, p4_offset +   3, 'little')
        self.write_data_volume_4KB           = self.add_field(p4_offset +   4, p4_offset +   7, 'little')
        self.read_reclaim_count              = self.add_field(p4_offset +   8, p4_offset +  11, 'little')
        self.read_data_volume_25MB           = self.add_field(p4_offset +  12, p4_offset +  15, 'little')
        self.read_data_volume_4KB            = self.add_field(p4_offset +  16, p4_offset +  19, 'little')
        self.SLC_read_reclaim_count          = self.add_field(p4_offset +  20, p4_offset +  23, 'little')
        self.TLC_read_reclaim_count          = self.add_field(p4_offset +  24, p4_offset +  27, 'little')
        self.EM1_read_reclaim_count          = self.add_field(p4_offset +  28, p4_offset +  31, 'little')
        self.clean_init_count                = self.add_field(p4_offset +  32, p4_offset +  35, 'little')
        self.dirty_init_count                = self.add_field(p4_offset +  36, p4_offset +  39, 'little')
        self.dirty_HW_reset_count            = self.add_field(p4_offset +  40, p4_offset +  43, 'little')
        self.SPOR_write_fail_count           = self.add_field(p4_offset +  44, p4_offset +  47, 'little')
        self.SPOR_recovery_count             = self.add_field(p4_offset +  48, p4_offset +  51, 'little')
        self.RPMB_write_data_volume_25MB     = self.add_field(p4_offset +  52, p4_offset +  55, 'little')
        self.RPMB_write_data_volume_4KB      = self.add_field(p4_offset +  56, p4_offset +  59, 'little')
        self.temperature_history_record      = self.add_field(p4_offset +  60, p4_offset +  63, 'little')
        self.clean_HW_reset_count            = self.add_field(p4_offset +  64, p4_offset +  67, 'little')
        self.write_EM1_data_volume_25MB      = self.add_field(p4_offset +  68, p4_offset +  71, 'little')
        self.write_EM1_data_volume_4KB       = self.add_field(p4_offset +  72, p4_offset +  75, 'little')
        self.read_EM1_data_volume_25MB       = self.add_field(p4_offset +  76, p4_offset +  79, 'little')
        self.read_EM1_data_volume_4KB        = self.add_field(p4_offset +  80, p4_offset +  83, 'little')
        self.Urgent_GC_command_count         = self.add_field(p4_offset +  84, p4_offset +  87, 'little')
        self.RPMB0WT_100M                    = self.add_field(p4_offset +  88, p4_offset +  91, 'little')
        self.RPMB0WT_SEC_PART100M            = self.add_field(p4_offset +  92, p4_offset +  95, 'little')
        self.RPMB1WT_100M                    = self.add_field(p4_offset +  96, p4_offset +  99, 'little')
        self.RPMB1WT_SEC_PART100M            = self.add_field(p4_offset + 100, p4_offset + 103, 'little')
        self.RPMB2WT_100M                    = self.add_field(p4_offset + 104, p4_offset + 107, 'little')
        self.RPMB2WT_SEC_PART100M            = self.add_field(p4_offset + 108, p4_offset + 111, 'little')
        self.RPMBWT_100M                     = self.add_field(p4_offset + 112, p4_offset + 115, 'little')
        self.RPMB3WT_SEC_PART100M            = self.add_field(p4_offset + 116, p4_offset + 119, 'little')
        self.WRITTEN_WB_100M                 = self.add_field(p4_offset + 120, p4_offset + 123, 'little')
        self.WRITTENSEC_WB_PART100M          = self.add_field(p4_offset + 124, p4_offset + 127, 'little')
        self.WRITTEN_NORMAL_100M             = self.add_field(p4_offset + 128, p4_offset + 131, 'little')
        self.WRITTENSEC_NORMAL_PART100M      = self.add_field(p4_offset + 132, p4_offset + 135, 'little')
        self.EM1_URGENT_GC_COMMAND_CNT       = self.add_field(p4_offset + 136, p4_offset + 139, 'little')
        self.DEVICE_ON_TIME                  = self.add_field(p4_offset + 140, p4_offset + 143, 'little')
        self.DEVICE_ON_TIME_PARTIAL          = self.add_field(p4_offset + 144, p4_offset + 147, 'little')
        self.READ_RECLAIM_UNIT_CNT           = self.add_field(p4_offset + 148, p4_offset + 151, 'little')
        self.HOST_WRITE_COMMAND_COUNT_LOWER  = self.add_field(p4_offset + 152, p4_offset + 155, 'little')
        self.HOST_WRITE_COMMAND_COUNT_UPPER  = self.add_field(p4_offset + 156, p4_offset + 159, 'little')
        self.HOST_READ_COMMAND_COUNT_LOWER   = self.add_field(p4_offset + 160, p4_offset + 163, 'little')
        self.HOST_READ_COMMAND_COUNT_UPPER   = self.add_field(p4_offset + 164, p4_offset + 167, 'little')
        self.VALID_CNT                       = self.add_field(p4_offset + 168, p4_offset + 171, 'little')
        self.DEVICE_SLEEP_H8_TIME            = self.add_field(p4_offset + 172, p4_offset + 175, 'little')
        self.DEVICE_SLEEP_H8_TIME_PARTIAL    = self.add_field(p4_offset + 176, p4_offset + 179, 'little')
        self.POWER_CONFIGURATION             = self.add_field(p4_offset + 180, p4_offset + 183, 'little')



