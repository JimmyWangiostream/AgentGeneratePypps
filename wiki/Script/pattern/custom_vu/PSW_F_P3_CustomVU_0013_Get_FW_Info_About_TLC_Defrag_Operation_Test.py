import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from typing import cast
from Script.api.exception import *
from Script.api import shared
from Script.api.ufs_api.vendor_cmd.structs import FwGeometry
import math
import random
import time
from Script.api.ufs_api import *
from typing import Dict
class VBList():

    VB_GROUP_LIST = {
                'HIDDEN_BLK_USE': 0,
                'LIST_BLK': 1,
                'LIST_INDEX_BLK': 2,
                'TMP_CODE_BLK': 3,
                'CURRENT_PTE': 4,
                'LOG_TAB_BLK': 5,
                'CURRENT_L2_SLC': 6,
                'CURRENT_L2_MLC': 7,
                'FREEZE_L2_BLK': 8,
                'CURRENT_DATA_GC_BLK_SLC': 9,
                'CURRENT_DATA_GC_BLK_MLC': 10,
                'INCOMPLETE_BLK_SLC': 11,
                'INCOMPLETE_BLK_MLC': 12,
                'CURRENT_L1': 13,
                'PTE_POOL': 14,
                'STATIC_SLC_USED_BLK': 15,
                'USED_BLK_POOL_SLC': 16,
                'USED_BLK_POOL_MLC': 17,
                'CURRENT_L3_SLC': 18,
                'CURRENT_L3_MLC': 19,
                'REFRESH_LINE': 20,
                'RAIN_SWAP_NO_OBR_SLC_L2_SLC':21,
                'RAIN_SWAP_NO_OBR_TLC_L2_SLC':22,
                'RAIN_SWAP_NO_OBR_TLC_L2_TLC':23,
                'RAIN_SWAP_NO_OBR_BLK': 24,
                'RAIN_SWAP_TLC_CURSOR_BLK': 25,
                'FREE_BLK_QUEUE_SLC': 26,
                'FREE_BLK_QUEUE_MLC': 27,
                'FREE_BLK_QUEUE_TABLE': 28,
                'TMP_ERASE_BLK_SLC': 29,
                'TMP_ERASE_BLK_MLC': 30,
                'TMP_ERASE_BLK_TABLE': 31,
                'TMP_USED_BLK_SLC': 32,
                'TMP_USED_BLK_MLC': 33,
                'TMP_USED_BLK_TABLE': 34,
                'TMP_REMOVE_BLK_SLC': 35,
                'TMP_REMOVE_BLK_MLC': 36,
                'TMP_REMOVE_BLK_TABLE': 37,
                'REFERENCE_QUEUE_SLC': 38,
                'REFERENCE_QUEUE_MLC': 39,
                'REVOKE_BLK': 40,
                'REMAP_DATA_GC_BLK_SLC': 41,
                'REMAP_DATA_GC_BLK_MLC': 42,
                'RPMB_COLLECT_BLK': 43,
                'PRE_ERASE_BLK': 44,
                'TMP_PRE_ERASE': 45,
                'PURGE_WAIT_ERASE_SLC': 46,
                'PURGE_WAIT_ERASE_MLC': 47,
                'DRVLOG_BLK': 48,
                'CONSTRAINT_QUEUE': 49,
                'TMP_FORCE_PTE_GC_TARGET': 50,
                'RESERVED_VB_GROUP0': 51,
                'RESERVED_VB_GROUP1': 52,
                'RESERVED_VB_GROUP2': 53,
                'RESERVED_VB_GROUP3': 54,
                'SELF_PE_ERASE_BLK': 55,
                'CONFIG_NUM_LIST_GROUP': 56,
    }


    VB_LIST_DATA_FORMAT = {
        'group': {'pos': 0, 'len': 6, 'mask': 0x3f},
                'access_mode': {'pos': 6, 'len': 2, 'mask': 0x03},
                'dirty': {'pos': 8, 'len': 1, 'mask': 0x01},
                'partition': {'pos': 9, 'len': 2, 'mask': 0x03},
                'cursor_idx': {'pos': 11, 'len': 1, 'mask': 0x01},
                'pte_tbl_mark':{'pos':12,'len':1,'mask':0x01},
                'host_w_mark':{'pos':13,'len':2,'mask':0x01},
                'rsv': {'pos': 15, 'len': 17, 'mask': 0x3f},
    }

    def __init__(self) ->None:
        pass

    def vb_group_list(self) -> Dict[str,int]:
        return self.VB_GROUP_LIST

class VBInfo(VBList):
    def __init__(self)->None:
        super().__init__()
        _, data = get_vb_info()
        self.list = self.__parse(data)

    def __parse(self, payload: bytearray) -> Dict[int, Dict[str,int]]:
        d : Dict[int, Dict[str,int]] = {}
        size = 4
        for vb in range(len(payload) // size):
            byte = vb * size
            d.update({vb: {k: ((int.from_bytes(payload[byte:byte + size], 'little') >>
                     v['pos']) & v['mask']) for k, v in self.VB_LIST_DATA_FORMAT.items()}})

        return d

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = shared.param
        self.total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.au_to_node = (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size * 512 ) // api.DATA_SIZE_4K_BYTE
        self.fw_geometry = api.get_fw_geometry()
        logger.info(f'total vb count = {self.fw_geometry.l52_total_vb_count}')
        self.TLC_VB_4K_SIZE = (self.fw_geometry.l88_vb_size_u1 * 512) // api.DATA_SIZE_4K_BYTE
        self.SLC_VB_4K_SIZE = (self.fw_geometry.l84_vb_size_u0 * 512) // api.DATA_SIZE_4K_BYTE
        self.TLC_PB_AU_SIZE = self.fw_geometry.l16_vb_size_pb_d1 // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.SLC_PB_AU_SIZE = self.fw_geometry.l20_vb_size_pb_d2 // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.TLC_VB_AU_SIZE = self.fw_geometry.l88_vb_size_u1 // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.SLC_VB_AU_SIZE = self.fw_geometry.l84_vb_size_u0 // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        logger.info(f'total au = {self.total_au}')
        hw_setting = api.HwSetting.get_instance()
        hw_setting.update_from_device()

        self.invalid_slc_threshold = hw_setting.get_local_val(api.HwSettingField.SLC_INVALID_THRESHOLD_BIT_7_0)
        self.invalid_slc_threshold |= (hw_setting.get_local_val(api.HwSettingField.SLC_INVALID_THRESHOLD_BIT_15_8) << 8)
        self.invalid_slc_threshold |= (hw_setting.get_local_val(api.HwSettingField.SLC_INVALID_THRESHOLD_BIT_23_16) << 16)
        self.invalid_slc_threshold |= (hw_setting.get_local_val(api.HwSettingField.SLC_INVALID_THRESHOLD_BIT_23_16) << 24)
        logger.info(f'invalid slc threshold = {self.invalid_slc_threshold}')

        self.invalid_tlc_threshold = hw_setting.get_local_val(api.HwSettingField.TLC_INVALID_THRESHOLD_BIT_7_0)
        self.invalid_tlc_threshold |= (hw_setting.get_local_val(api.HwSettingField.TLC_INVALID_THRESHOLD_BIT_15_8) << 8)
        self.invalid_tlc_threshold |= (hw_setting.get_local_val(api.HwSettingField.TLC_INVALID_THRESHOLD_BIT_23_16) << 16)
        self.invalid_tlc_threshold |= (hw_setting.get_local_val(api.HwSettingField.TLC_INVALID_THRESHOLD_BIT_23_16) << 24)
        logger.info(f'invalid tlc threshold = {self.invalid_tlc_threshold}')
        pass
    def get_health_report(self) -> tuple[int,int]:
        response, self.health_report = project_api.issue_40FE_to_read_enhanced_health_report()         
        logger.info(f'gc cnt for normal {self.health_report.urgent_gc_count_for_normal_partition.value}')
        logger.info(f'gc cnt for em1 {self.health_report.urgent_gc_count_for_em1_partition.value}')
        return self.health_report.urgent_gc_count_for_normal_partition.value, self.health_report.urgent_gc_count_for_em1_partition.value
    def step1(self) -> None:

        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()

        logger.flow(1, 'Test offset[0:3] Flags for informing whether BG/FG GC was triggered or not.')
        expect_value = (len(data.payload) - 4 ) // 4
        logger.info(f'offset[0:3] = {data.GC_trigger_fields.value}')
        self.compare_value(data.GC_trigger_fields.value, expect_value, "offset[0:3] GC_trigger_fields")

        logger.flow(2, 'Test offset[4:7] which gc type is triggered.')
        self.compare_value(data.GC_trigger_type.value, 0, "offset[4:7] GC_trigger_type")

        logger.flow(3, 'Test offset[8:11] Current value of threshold for starting BG GC based on current normal area Logical Saturation (LS) (unit: number of VB) .')
        logger.flow("3-1", 'config normal lun')
        slc_lun, tlc_lun = self.config_lun(slc_au=0, tlc_au=self.total_au)
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        slc_threshold , mlc_threshold = api.get_gc_threshold()
        bg_mlc_gc_threshold = mlc_threshold - 3
        self.compare_value(data.start_bg_gc_vb_cnt_normal.value, bg_mlc_gc_threshold, "offset[8:11] start_bg_gc_vb_cnt_normal")

        logger.flow(4, 'Test offset[12:15] Current value of threshold for stopping BG GC based on current normal area Logical Saturation (LS) (unit: number of VB) .')
        self.compare_value(data.stop_bg_gc_vb_cnt_normal.value, bg_mlc_gc_threshold, "offset[12:15] top_bg_gc_vb_cnt_normal")

        logger.flow(5, 'Test offset[16:19] Value of threshold for starting FG IMMEDIATE GC (unit: number of VB).')
        self.compare_value(data.start_fg_gc_vb_cnt_normal.value, mlc_threshold, "offset[16:19] start_fg_gc_vb_cnt_normal")

        logger.flow(6, 'Test offset[20:23] not applicable.')
        self.compare_value(data.l20_not_applicable.value, 0xFFFFFFFF, "offset[20:23] l20_not_applicable")

        logger.flow(7, 'Test offset[24:27] Write Booster Buffer SLC cache size @ Logical Saturation 0 (unit: VB)  .')
        logger.flow("7-1", 'config wb au = 1024')
        config_wb_size = 2048
        self.config_wb(config_wb_size)
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        config_wb_node_size = config_wb_size *  (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size * 512 ) // DATA_SIZE_4K_BYTE
        expect_value = math.ceil(config_wb_node_size / self.SLC_VB_4K_SIZE)
        self.compare_value(data.wb_slc_cache_vb_size_ls0.value, expect_value, "offset[24:27] wb_slc_cache_vb_size_ls0")

        logger.flow(8, 'Test offset[28:31] Write Booster Buffer SLC cache size @ Logical Saturation 100 (unit: VB)  .')
        min_wb_node_size = cast(int,read_fw_value('gUfsApiStruct.ftl->vb_list.head_misc->statistics.non_slc_vc_threshold_min'))
        expect_value = math.ceil( min_wb_node_size / self.SLC_VB_4K_SIZE)
        self.compare_value(data.wb_slc_cache_vb_size_ls100.value, expect_value, "offset[28:31] wb_slc_cache_vb_size_ls100")

        logger.flow(9, 'Test offset[32:35] max size still to be written before Write Booster Buffer size begins to reduce (unit: LBA) .')
        DYNAMIC_SLC_UPPER_BOUND_PERCENT = 25
        total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        total_sector = self._param.gGeometry.q4_total_raw_device_capacity
        total_node_by_sector = (total_sector) * 512 //4096
        config_wb_node_size = config_wb_size * (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size * 512 ) // DATA_SIZE_4K_BYTE
        ls_by_sector = 100 - config_wb_node_size * 100 * 100 //total_node_by_sector // DYNAMIC_SLC_UPPER_BOUND_PERCENT
        expect_value = ls_by_sector * total_node_by_sector // 100
        self.compare_value(data.max_size_to_reduce_wb_size.value, expect_value, "offset[32:35] max_size_to_reduce_wb_size")

        logger.flow(10, 'Test offset[36:39] Write Booster Buffer available Size (unit: LBA).')
        logger.flow("10-1", 'Clear card')
        self.clear_card()
        config_wb_size_lba = (config_wb_size * self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size * 512) // api.DATA_SIZE_4K_BYTE
        self.compare_value(data.wb_available_size.value, config_wb_size_lba, "offset[36:39] wb_available_size")

        logger.flow("10-2", 'Set writebooster enable and disable wb flush')
        api.set_flag(idn=FlagIDN.WRITEBOOSTER_EN)
        api.clear_flag(idn=FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)
        logger.flow("10-3", 'Write all wb size')
        self.write_data(lun=0,start_lba=0,len=WRITE_10_MAX_BLOCK_LEN,total_len=config_wb_size_lba * 2)
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.wb_available_size.value, 0, "offset[36:39] wb_available_size")
        logger.flow("10-4", 'Enable wb flush')
        api.set_flag(idn=FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)
        logger.flow("10-5", 'Polling available wb size = 0xA')
        start_time = time.time()
        timeout_min = 15
        while(api.read_attribute(idn=AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE) != 0xA):
            if self.check_timeout(start_time, timeout_min):
                logger.error(f'Polling writebooster size = 0xA {timeout_min} min but timeout')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.wb_available_size.value , config_wb_size_lba, "offset[36:39] wb_available_size")

        logger.flow(11, 'Test offset[40:43] Invalid VB count in Invalid Pool (Normal Area) .')
        free_tlc_vb_cnt = self.get_vb_group_size('FREE_BLK_QUEUE_MLC')
        self.compare_value(data.invalid_vb_cnt_normal.value , free_tlc_vb_cnt, "offset[40:43] nvalid_vb_cnt_normal")

        logger.flow(12, 'Test offset[44:47] Used SLC VB count (open VB not counted).')
        logger.flow("12-1", 'Config wb size = 1024.')
        self.config_wb(config_wb_size=2048)
        logger.flow("12-2", 'Set writebooster enable and disable wb flush')
        api.set_flag(idn=FlagIDN.WRITEBOOSTER_EN)
        api.clear_flag(idn=FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)
        total_len = self.SLC_VB_4K_SIZE
        data_len = WRITE_10_MAX_BLOCK_LEN
        logger.flow("12-3", 'Write 1 slc vb')
        self.write_data(lun=0,start_lba=0,len=data_len,total_len=total_len)
        self.check_read_scan(lun=0, lba=total_len)
        last_lba = total_len - 1
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.used_slc_vb_cnt.value , 1, "offset[44:47] used_slc_vb_cnt")

        logger.flow(13, 'Test offset[48:51] Used TLC VB count (open VB not counted).')
        logger.flow("13-1", 'Disable wb')
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        total_len = self.TLC_VB_4K_SIZE
        data_len = WRITE_10_MAX_BLOCK_LEN
        logger.flow("13-2", 'Write 1 tlc vb')
        self.write_data(lun=0,start_lba=last_lba+1,len=data_len,total_len=total_len)
        self.check_read_scan(lun=0, lba=last_lba+1)
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.used_tlc_vb_cnt.value , 1, "offset[48:51] used_tlc_vb_cnt")

        logger.flow(14, 'Test offset[52:55] Used VB count in SLC stale zone (most recently written SLC VBs will be skipped by PGC) list  .')
        logger.flow("14-1", 'Enable wb')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        total_len = self.SLC_VB_4K_SIZE
        data_len = WRITE_10_MAX_BLOCK_LEN
        logger.flow("14-2", 'Write 1 slc vb')
        self.write_data(lun=0,start_lba=0,len=data_len,total_len=total_len)
        self.check_read_scan(lun=0,lba=0)
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.used_vb_cnt_in_slc_stale_zone_list.value , 2, "offset[52:55] used_vb_cnt_in_slc_stale_zone_list")

        logger.flow(15, 'Test offset[56:59] VB count in LOCKED_SRC list + count of open VB (they might include Normal TLC L2, Normal GC, Normal S_CHK L1, RPMB open VB for Host/GC) for which first free page == 0  .')
        open_normal_vb_cnt = self.get_open_vb_vc_0_cnt('normal')
        self.compare_value(data.vb_cnt_in_LOCKED_SRC_and_cnt_of_open_vb_normal.value , open_normal_vb_cnt, "offset[56:59] vb_cnt_in_LOCKED_SRC_and_cnt_of_open_vb_normal")

        logger.flow(16, 'Test offset[60:63] Write Booster Buffer Slc cache stale zone (most recently written SLC VBs will be skipped by PGC) size@ ls0 (unit: VB)  ')
        self.compare_value(data.wb_slc_cache_stale_zone_size_ls0.value , data.wb_slc_cache_vb_size_ls100.value, "offset[60:63] wb_slc_cache_stale_zone_size_ls0")

        logger.flow(17, 'Test offset[64:67] Write Booster Buffer Slc cache stale zone (most recently written SLC VBs will be skipped by PGC) size@ ls100 (unit: VB)  ')
        self.compare_value(data.wb_slc_cache_stale_zone_size_ls100.value , data.wb_slc_cache_vb_size_ls0.value, "offset[64:67] wb_slc_cache_stale_zone_size_ls100")

        logger.flow(18, 'Test offset[68:71] one bit flag to show whether the IGC trigger condition in Normal area is met or not. .')
        self.compare_value(data.flag_show_IGC_trigger_in_normal.value , 0, "offset[68:71] flag_show_IGC_trigger_in_normal")

        logger.flow(19, 'Test offset[72:75] how many VPs (space for an LBA) are still to be written before IGC is triggered')
        logger.flow("19-1", 'Disable wb')
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        slc_threshold, mlc_threshold = api.get_gc_threshold()
        used_tlc_vb_cnt = self.get_vb_group_size('USED_BLK_POOL_MLC')
        expect_value = (mlc_threshold - used_tlc_vb_cnt) * self.TLC_VB_4K_SIZE
        logger.info(f'After write tlc vb, expect offse[72:75] = (mlc gc threshold - {used_tlc_vb_cnt}) * tlc vb data node cnt ({expect_value}), but = {data.VPs_be_written_to_trigger_IGC_in_normal.value}')
        self.compare_value(data.VPs_be_written_to_trigger_IGC_in_normal.value , expect_value, "offset[72:75] VPs_be_written_to_trigger_IGC_in_normal")

        logger.flow(20, 'Test offset[76:79] VB count in LOCKED_SRC list (LOCKED_SRC list being the one containing all source VBs chosen for GC), 0x0 if no GC running  .')
        self.compare_value(data.vb_cnt_in_LOCKED_SRC_list_for_normal.value , 0, "offset[76:79] vb_cnt_in_LOCKED_SRC_list_for_normal")

        logger.flow(21, 'Test offset[80:83] volatile flag to show whether or not the GC target VB filling with dummy values has started, since no more source VBs may be inserted in LOCKED_SRC list, being it full. Once set such bit, it is only reset on starting next GC or on power-cycle   .')
        self.compare_value(data.start_filling_GC_target_with_dummy_in_normal.value , 0, "offset[80:83] start_filling_GC_target_with_dummy_in_normal")

        logger.flow(22, 'Test offset[84:87] NOT APPLICABLE')
        self.compare_value(data.l84_not_applicable.value ,0xFFFFFFFF, "offset[84:87] 84_not_applicable")

        logger.flow(23, 'Test offset[88:91] Trigger condition for starting BG GC (unit: VB)  .')
        logger.flow("23-1", 'Config em1 lun, au = total au.')
        slc_lun, tlc_lun = self.config_lun(slc_au=self.total_au,tlc_au=0)
        slc_threshold , mlc_threshold = api.get_gc_threshold()
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.start_bg_gc_vb_cnt_em1.value ,slc_threshold, "offset[88:91] start_bg_gc_vb_cnt_em1")

        logger.flow(24, 'Test offset[92:95] Trigger condition for stopping of BG GC (unit: VB).')
        self.compare_value(data.stop_bg_gc_vb_cnt_em1.value ,slc_threshold, "offset[92:95] stop_bg_gc_vb_cnt_em1")

        logger.flow(25, 'Test offset[96:99] Trigger condition for FG IMMEDIATE GC (unit: VB).')
        self.compare_value(data.start_fg_gc_vb_cnt_em1.value ,slc_threshold, "offset[96:99] start_fg_gc_vb_cnt_em1")

        logger.flow(26, 'Test offset[100:103] NOT APPLICABLE  .')
        self.compare_value(data.l100_not_applicable.value ,0xFFFFFFFF, "offset[100:103] l100_not_applicable")

        logger.flow(27, 'Test offset[104:107] Invalid VB count in Invalid Pool for (EM1 area).')
        free_slc_vb_cnt = self.get_vb_group_size('FREE_BLK_QUEUE_SLC')
        self.compare_value(data.invalid_vb_cnt_em1.value, free_slc_vb_cnt, "offset[104:107] free_slc_vb_cnt")

        logger.flow(28, 'Test offset[108:111]VB count in LOCKED_SRC list + count of open VB (they might include EM1 L2, GC EM1) for which first free page == 0  .')
        self.compare_value(data.vb_cnt_in_LOCKED_SRC_and_cnt_of_open_vb_em1.value, 0, "offset[108:111] vb_cnt_in_LOCKED_SRC_and_cnt_of_open_vb_em1")

        logger.flow(29, 'Test offset[112:115] one bit flag to show whether the IGC trigger condition in EM1 area is met or not.')
        self.compare_value(data.flag_show_IGC_trigger_in_em1.value, 0, "offset[112:115] flag_show_IGC_trigger_in_em1")

        logger.flow(30, 'Test offset[116:119] how many VPs (space for an LBA) are still to be written before IGC is triggered into EM1 area.  .')
        used_slc_vb_cnt = self.get_vb_group_size('USED_BLK_POOL_SLC')
        expect_value = (slc_threshold - used_slc_vb_cnt)* self.SLC_VB_4K_SIZE
        self.compare_value(data.VPs_be_written_to_trigger_IGC_in_em1.value, expect_value, "offset[116:119] VPs_be_written_to_trigger_IGC_in_em1")


        logger.flow(31, 'Test offset[120:123] VB count in LOCKED_SRC list for EM1 area, 0x0 whether no GC running.')
        self.compare_value(data.vb_cnt_in_LOCKED_SRC_list_for_em1.value, 0, "offset[120:123] vb_cnt_in_LOCKED_SRC_list_for_em1")

        logger.flow(32, 'Test offset[124:127] volatile flag to show whether or not the GC target VB filling with dummy values has started, since no more source VBs may be inserted  in LOCKED_SRC list, being it full. Once set such bit, it is only reset on starting next GC or on power-cycle.')
        self.compare_value(data.start_filling_GC_target_with_dummy_in_em1.value, 0, "offset[124:127] start_filling_GC_target_with_dummy_in_em1")

        logger.flow(33, 'Test offset[128:131] Number of VBs allocated for using into EM1 area')
        expect_value = self.get_vb_group_size('USED_BLK_POOL_SLC')
        self.compare_value(data.num_of_vb_allc_for_using_em1.value, expect_value, "offset[128:131] num_of_vb_allc_for_using_em1")

        logger.flow(35, 'Test offset[136:139] EM1 area IGC stop threshold  .')
        self.compare_value(data.em1_area_IGC_stop_threshold.value, slc_threshold, "offset[136:139] em1_area_IGC_stop_threshold")

        logger.flow("23-1", 'Config em1 lun, au = total au.')
        slc_lun, tlc_lun = self.config_lun(slc_au=0,tlc_au=self.total_au)
        slc_threshold , mlc_threshold = api.get_gc_threshold()
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()

        logger.flow(34, 'Test offset[132:135] Normal area IGC stop threshold .')
        self.compare_value(data.noraml_area_IGC_stop_threshold.value, mlc_threshold - 3, "offset[132:135] noraml_area_IGC_stop_threshold")

       
        logger.flow(36, 'Test offset[140:143] normal area total VB count .')
        total_normal_node = (self.total_au * (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size) * 512) // api.DATA_SIZE_4K_BYTE
        last_slc_vb = cast(int, read_fw_value('gUfsApiStruct.ftl->bbt.last_slc_pool_vb'))
        total_vb_cnt = self.fw_geometry.l52_total_vb_count
        expect_value = total_vb_cnt - last_slc_vb - 1
        self.compare_value(data.normal_area_total_vb_cnt.value, expect_value, "offset[140:143] normal area total VB count")

        logger.flow(37, 'Test offset[144:147] normal area remained VB count.')
        free_tlc_vb_cnt = self.get_vb_group_size('FREE_BLK_QUEUE_MLC')
        self.compare_value(data.normal_area_remained_vb_cnt.value, free_tlc_vb_cnt, "offset[144:147] normal_area_remained_vb_cnt")

        logger.flow(38, 'Test offset[148:151] NOT APPLICABLE.')
        self.compare_value(data.l148_not_applicable.value, 0xFFFFFFFF, "offset[148:151] l148_not_applicable")

        logger.flow(39, 'Test offset[152:155] NOT APPLICABLE.')
        self.compare_value(data.l152_not_applicable.value, 0xFFFFFFFF, "offset[152:155] l152_not_applicable")

        logger.flow(40, 'Test offset[156:159] Get last bkop status  .')
        self.compare_value(data.get_last_bkop_status.value, 0, "offset[156:159] get_last_bkop_status")

        logger.flow(50, 'Test offset[160:163] number of invalid entries cumulated along all “fragmented” (== THRESHOLD < invalid entries) VBs in USED / INCOMPLETE Groups in Normal area.')
        logger.flow(50-1, 'Config normal lun au = total au / 2, em1 lun au = total au / 2')
        slc_lun, tlc_lun = self.config_lun(slc_au=self.total_au//2, tlc_au=self.total_au//2)

        total_len = self.TLC_VB_4K_SIZE
        data_len = WRITE_10_MAX_BLOCK_LEN
        logger.flow(50-2, 'Write 1 tlc vb')
        self.write_data(lun=tlc_lun,start_lba=0,len=data_len,total_len=total_len)
        logger.flow(50-3, f'Unmap len = invalid tlc threshold + 1 = {self.invalid_tlc_threshold + 1}')
        unmap_total_len = self.invalid_tlc_threshold + 1
        data_len = WRITE_10_MAX_BLOCK_LEN
        self.unmap_data(lun=tlc_lun,start_lba=0,len=data_len,total_len=unmap_total_len)

        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        expect_value = unmap_total_len
        self.compare_value(data.num_of_invalid_entries_in_normal.value, expect_value, "offset[160:163] num_of_invalid_entries_in_normal")

        logger.flow(51, 'Test offset[164:167] number of “fragmented” (== THRESHOLD < invalid entries) VBs in USED / INCOMPLETE Groups in Normal area  .')
        self.compare_value(data.num_of_fragmented_vb_in_normal.value, 1, "offset[164:167] num_of_fragmented_vb_in_normal")

        logger.flow(52, 'Test offset[168:171] number of invalid entries cumulated along all “fragmented” (== THRESHOLD < invalid entries) VBs in USED / INCOMPLETE Groups in EM1 area')
        total_len = self.SLC_VB_4K_SIZE
        data_len = WRITE_10_MAX_BLOCK_LEN
        logger.flow(52-1, 'Write 1 SLC vb')
        self.write_data(lun=slc_lun,start_lba=0,len=data_len,total_len=total_len)

        unmap_total_len = self.invalid_slc_threshold + 1
        data_len = WRITE_10_MAX_BLOCK_LEN
        logger.flow(52-2, f'Unmap len = invalid tlc threshold + 1 = {self.invalid_tlc_threshold + 1}')
        self.unmap_data(lun=slc_lun,start_lba=0,len=data_len,total_len=unmap_total_len)

        expect_value = unmap_total_len
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.num_of_invalid_entries_in_em1.value, expect_value, "offset[168:171] num_of_invalid_entries_in_em1")

        logger.flow(53, 'Test offset[172:175] number of “fragmented” (== THRESHOLD < invalid entries) VBs in USED / INCOMPLETE Groups in EM1 area   .')
        self.compare_value(data.num_of_fragmented_vb_in_em1.value, 1, "offset[172:175] num_of_fragmented_vb_in_em1")

        logger.flow(54, 'Create GC fill with dummy case in normal')
        MLC_partition = 1
        logger.flow(54-1, 'Config normal lun, au = total au')
        slc_lun, tlc_lun = self.config_lun(slc_au=0, tlc_au=self.total_au)
        slc_threshold, tlc_threshold = api.get_gc_threshold()
        logger.flow(54-3, 'Disable bkops')
        api.clear_flag(idn=api.FlagIDN.BG_OP_EN)
        logger.flow(54-4, 'Write until tlc gc threshold - 3')
        self.write_until_threshold(tlc_lun,'USED_BLK_POOL_MLC', tlc_threshold-3, overwrite=True)
        logger.flow(54-5, 'Enable bkops')
        api.set_flag(idn=api.FlagIDN.BG_OP_EN)
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.start_filling_GC_target_with_dummy_in_normal.value, 1, "offset[80:83] start_filling_GC_target_with_dummy_in_normal")
        logger.flow(54-6, 'Power cycle')
        api.init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.start_filling_GC_target_with_dummy_in_normal.value, 0, "offset[80:83] start_filling_GC_target_with_dummy_in_normal")

        logger.flow(55, 'Create GC fill with dummy case in em1')
        logger.flow(55-1, 'Config em1 lun, au = 10 slc vb')
        slc_lun, tlc_lun = self.config_lun(slc_au=self.SLC_VB_AU_SIZE * 20, tlc_au=0)
        slc_threshold, tlc_threshold = api.get_gc_threshold()
        logger.flow(55-2, 'Disable bkops')
        project_api.issue_D0FD_en_disable_BKOPS(bValue=2)
        logger.flow(55-3, 'Write until slc gc threshold')
        self.write_until_threshold(slc_lun,'USED_BLK_POOL_SLC', slc_threshold, overwrite=True)
        logger.flow(55-4, 'Enable bkops')
        project_api.issue_D0FD_en_disable_BKOPS(bValue=3)
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.start_filling_GC_target_with_dummy_in_em1.value, 1, "offset[124:127] start_filling_GC_target_with_dummy_in_em1")
        logger.flow(55-5, 'Power cycle')
        api.init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.start_filling_GC_target_with_dummy_in_em1.value, 0, "offset[124:127] start_filling_GC_target_with_dummy_in_em1")
        backup_urgent_gc_cnt_nomal, backup_urgent_gc_cnt_em1 =  self.get_health_report()
        logger.flow(56, 'Trigger BG GC in normal and check related fields')
        logger.flow(56-1, 'Config normal lun, au = total au')
        slc_lun, tlc_lun = self.config_lun(slc_au=0, tlc_au=self.total_au)
        slc_threshold, tlc_threshold = api.get_gc_threshold()
        logger.info(f'tlc threshold = {tlc_threshold}')
        logger.flow(56-2, 'Disable bkops')
        api.clear_flag(idn=api.FlagIDN.BG_OP_EN)
        logger.flow(56-3, 'Write until tlc gc threshold - 3')
        loop = self.write_until_threshold(tlc_lun,'USED_BLK_POOL_MLC', tlc_threshold-3)
        logger.flow(56-4, 'Enable bkops')
        api.set_flag(idn=api.FlagIDN.BG_OP_EN)
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.GC_trigger_type.value, 1, "offset[4:7] GC_trigger_type")
        self.compare_value(data.flag_show_IGC_trigger_in_normal.value, 0, "offset[68:71] flag_show_IGC_trigger_in_normal")
        if data.vb_cnt_in_LOCKED_SRC_list_for_normal.value == 0:
            logger.error(f'Expect offset[76:79] > 0, but = {data.vb_cnt_in_LOCKED_SRC_list_for_normal.value}')
        if data.vb_cnt_in_LOCKED_SRC_and_cnt_of_open_vb_normal.value < (data.vb_cnt_in_LOCKED_SRC_list_for_normal.value):
            logger.error(f'Expect offset[56:59]>=offset[76:79]={data.vb_cnt_in_LOCKED_SRC_list_for_normal.value}, but = {data.vb_cnt_in_LOCKED_SRC_and_cnt_of_open_vb_normal.value}')
        logger.info(f'offset[76:79] = {data.vb_cnt_in_LOCKED_SRC_list_for_normal.value}')
        logger.info(f'offset[56:59] = {data.vb_cnt_in_LOCKED_SRC_and_cnt_of_open_vb_normal.value}')

        used_vb_cnt = self.get_vb_group_size('USED_BLK_POOL_MLC')
        logger.info(f'used vb cnt = {used_vb_cnt}')
        logger.flow(57, 'Trigger FG GC in normal and check related fields*')
        logger.flow("57-1", 'Disable bkops')
        project_api.issue_D0FD_en_disable_BKOPS(bValue=2)
        project_api.issue_D0FD_en_disable_BKOPS(bValue=0)
        logger.flow("57-2", 'Write until tlc gc threshold')
        self.write_until_threshold(tlc_lun,'USED_BLK_POOL_MLC', tlc_threshold, loop=loop)
        project_api.issue_D0FD_en_disable_BKOPS(bValue=3)
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.GC_trigger_type.value, 2, "offset[4:7] GC_trigger_type")
        self.compare_value(data.flag_show_IGC_trigger_in_normal.value, 1, "offset[68:71] flag_show_IGC_trigger_in_normal")
        if data.vb_cnt_in_LOCKED_SRC_list_for_normal.value == 0:
            logger.error(f'Expect offset[76:79] > 0, but = {data.vb_cnt_in_LOCKED_SRC_list_for_normal.value}')
        if data.vb_cnt_in_LOCKED_SRC_and_cnt_of_open_vb_normal.value < (data.vb_cnt_in_LOCKED_SRC_list_for_normal.value):
            logger.error(f'Expect offset[56:59]>=offset[76:79]={data.vb_cnt_in_LOCKED_SRC_list_for_normal.value}, but = {data.vb_cnt_in_LOCKED_SRC_and_cnt_of_open_vb_normal.value}')
        logger.info(f'offset[76:79] = {data.vb_cnt_in_LOCKED_SRC_list_for_normal.value}')
        logger.info(f'offset[56:59] = {data.vb_cnt_in_LOCKED_SRC_and_cnt_of_open_vb_normal.value}')
        project_api.issue_D0FD_en_disable_BKOPS(bValue=1)

        logger.flow(58, 'Trigger BG/FG GC in em1 and check related fields*')
        logger.flow(58-1, 'Config em1 lun, au = 10 slc vb')
        slc_lun, tlc_lun = self.config_lun(slc_au=self.SLC_VB_AU_SIZE * 10, tlc_au=0)
        slc_threshold, tlc_threshold = api.get_gc_threshold()
        logger.info(f'slc threshold = {slc_threshold}')
        logger.flow(58-2, 'Disable bkops')
        api.clear_flag(idn=api.FlagIDN.BG_OP_EN)
        logger.flow(58-3, 'Write to trigger slc gc')
        total_len = self.SLC_VB_4K_SIZE * (slc_threshold + 1)
        start_lba = 0
        data_len = WRITE_10_MAX_BLOCK_LEN
        cnt = 1
        while total_len > 0:
            data_len = min(total_len, data_len)
            write10 = ExecuteCMD.Write10()
            if start_lba + data_len > self._param.gLUCapacity[slc_lun]:
                start_lba = cnt
                cnt+=1
            logger.info(f'start_lba ={start_lba}, len = {data_len}')
            write10.assign(lun=slc_lun, lba=start_lba, length=data_len, fua=1)
            ExecuteCMD.enqueue(write10)

            start_lba += data_len
            total_len -= data_len

        cmd_idx = ExecuteCMD.SetFlag().assign(idn=api.FlagIDN.BG_OP_EN, index=0, selector=0).set_option(wait_queue_empty=True).enqueue()
        data = project_api.issue_40C2_to_get_info_about_TLC_defrag_operation()
        self.compare_value(data.GC_trigger_type.value, 32, "offset[4:7] GC_trigger_type")
        self.compare_value(data.flag_show_IGC_trigger_in_em1.value, 1, "offset[112:115] flag_show_IGC_trigger_in_em1")
        if data.vb_cnt_in_LOCKED_SRC_list_for_em1.value == 0:
            logger.error(f'Expect offset[120:123] > 0, but = {data.vb_cnt_in_LOCKED_SRC_list_for_em1.value}')
        if data.vb_cnt_in_LOCKED_SRC_and_cnt_of_open_vb_em1.value < (data.vb_cnt_in_LOCKED_SRC_list_for_em1.value):
            logger.error(f'Expect offset[108:111]>=offset[120:123]={data.vb_cnt_in_LOCKED_SRC_list_for_em1.value}, but = {data.vb_cnt_in_LOCKED_SRC_and_cnt_of_open_vb_em1.value}')
        logger.info(f'offset[120:123] = {data.vb_cnt_in_LOCKED_SRC_list_for_em1.value}')
        logger.info(f'offset[108:111] = {data.vb_cnt_in_LOCKED_SRC_and_cnt_of_open_vb_em1.value}')
        current_urgent_gc_cnt_nomal, current_urgent_gc_cnt_em1 =  self.get_health_report()
        if current_urgent_gc_cnt_nomal < backup_urgent_gc_cnt_nomal:
            logger.error_fp(f'current_urgent_gc_cnt_nomal({current_urgent_gc_cnt_nomal}) < backup_urgent_gc_cnt_nomal({backup_urgent_gc_cnt_nomal})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        if current_urgent_gc_cnt_em1 < backup_urgent_gc_cnt_em1:
            logger.error_fp(f'current_urgent_gc_cnt_em1({current_urgent_gc_cnt_em1}) < backup_urgent_gc_cnt_em1({backup_urgent_gc_cnt_em1})')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    def check_read_scan(self,lun:int, lba:int) -> None:
        _, vu_pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=lba)
        input_vb = vu_pca.virtual_block_number.value
        status = project_api.check_if_current_VB_scan_in_progress_completed(VB=input_vb)
        start_time = time.time()
        timeout_min = 1
        while status != 0:
            status = project_api.check_if_current_VB_scan_in_progress_completed(VB=input_vb)
            if self.check_timeout(start_time, timeout_min):
                logger.error(f'Polling read scan finish in {timeout_min} min but timeout')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
        time.sleep(2)    
        
    def clear_card(self) -> None:
        format_unit = ExecuteCMD.FormatUnit()
        format_unit.assign(lun=0, longlist=0, cmplist=0)
        ExecuteCMD.enqueue(format_unit)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

    def get_open_vb_vc_0_cnt(self,type:str) ->int:
        open_vb_vc_0_cnt = 0
        _, open_vb_info = api.get_open_vb_info()

        if type == "normal":
            vb_list = [open_vb_info.TLC_L2, open_vb_info.TLC_L1,open_vb_info.TLC_GC, open_vb_info.WB]
        else:
            vb_list = [open_vb_info.SLC_L2, open_vb_info.SLC_GC]
        for vb in vb_list:
            if vb.logical_vb.value != 0xFFFFFFFF and all(
                getattr(vb, attr).value == 0
                for attr in ("first_empty_CE", "first_empty_plane",
                            "first_empty_physical_page", "first_empty_node")
                ):
                open_vb_vc_0_cnt += 1
        return open_vb_vc_0_cnt


    def check_timeout(self,start_time: float, timeout_min: int) -> bool:
        current_time = time.time()
        if (current_time - start_time) >= timeout_min * 60:
            return True
        else:
            return False
    def write_1vb_size(self, lun:int, vb_group_name:str, loop:int, overwrite:bool = False) -> None:
        if vb_group_name == 'USED_BLK_POOL_SLC':
            vb_size = self.SLC_VB_4K_SIZE
        else:
            vb_size = self.TLC_VB_4K_SIZE

        total_len = vb_size
        data_len = WRITE_10_MAX_BLOCK_LEN
        if overwrite == False:
            start_lba = loop * vb_size
        else:
            start_lba = loop

        while total_len > 0:
            data_len = min(total_len, data_len)
            if (start_lba + data_len) > self._param.gLUCapacity[lun]:
                start_lba = random.randint(0, self._param.gLUCapacity[lun] - data_len -1)
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=lun, lba=start_lba, length=data_len, fua=1)
            ExecuteCMD.enqueue(write10)
            logger.info(f'startlba={start_lba},len={data_len}')
            start_lba += data_len
            total_len -= data_len

        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

    def write_until_threshold(self, lun:int, vb_group_name:str, threshold:int, overwrite:bool = False, loop:int=0)->int:
        used_vb_cnt = self.get_vb_group_size(vb_group_name)
        print(f'initial used vb cnt = {used_vb_cnt}')
        start_time = time.time()
        elapsed_time = 0
        timeout_min = 180
        while used_vb_cnt < threshold:
            if self.check_timeout(start_time, timeout_min):
                logger.error('fPolling write until used vb cnt >= gc threshold in 3 HOUR but timeout')
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            self.write_1vb_size(lun, vb_group_name, loop, overwrite=overwrite)
            used_vb_cnt = self.get_vb_group_size(vb_group_name)
            logger.info(f'used vb cnt = {used_vb_cnt}')
            loop += 1
        return loop


    def unmap_data(self, lun:int, start_lba:int, len:int, total_len:int) -> None:
        while total_len > 0:
            len = min(total_len, len)
            unmap = ExecuteCMD.Unmap()
            unmap.assign(lun=lun, lba=start_lba, length=len)
            ExecuteCMD.enqueue(unmap)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
    def write_data(self, lun:int, start_lba:int, len:int, total_len:int) -> None:
        while total_len > 0:
            len = min(total_len, len)
            write10 = ExecuteCMD.Write10()
            logger.info(f'start lba = {start_lba}, len = {len}')
            write10.assign(lun=lun, lba=start_lba, length=len, fua=0)
            ExecuteCMD.enqueue(write10)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(timeout=api.UniformTimeout(val=30000, unit=api.TimeResolution.ms), clear_on_success=False)
        ExecuteCMD.clear()
    def config_wb(self, config_wb_size:int) -> None:
        total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        config_descs = api.get_config_descriptors(print=True)
        for table in range(4):
            for unit in range(8):
                config_descs[table].header.b2_conf_desc_continue = 1
                config_descs[table].units[unit].b0_lu_enable = 0
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].l4_num_alloc_units = 0
                config_descs[table].units[unit].b9_logical_block_size = 0xc
                config_descs[table].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                if (table * 8 + unit) == 0:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[table].units[unit].l4_num_alloc_units = total_au
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.ENABLE
        config_descs[0].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = config_wb_size
        config_descs[3].header.b2_conf_desc_continue = 0

        for i in range(4):
            api.push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        ExecuteCMD.clear()
        config_descs = api.get_config_descriptors(print=True)

    def config_lun(self,slc_au:int, tlc_au:int) -> tuple[int,int]:

        config_descs = api.get_config_descriptors(print=True)
        for table in range(4):
            for unit in range(8):
                config_descs[table].header.b2_conf_desc_continue = 1
                config_descs[table].units[unit].b0_lu_enable = 0
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].l4_num_alloc_units = 0
                config_descs[table].units[unit].b9_logical_block_size = 0xc
                config_descs[table].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                if (table * 8 + unit) == 0:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[table].units[unit].l4_num_alloc_units = slc_au
                elif (table * 8 + unit) == 1:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[table].units[unit].l4_num_alloc_units = tlc_au

        config_descs[3].header.b2_conf_desc_continue = 0
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.ENABLE
        config_descs[0].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0
        for i in range(4):
            api.push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        ExecuteCMD.clear()

        unit_desc_idxes:List[int] = []
        for lun in range(0, self._param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            update_descriptor(DescriptorIDN.UNIT, index, cast(QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()
        #test unit ready all enable lun
        for lun in range(self._param.gMaxNumberLU):
            if self._param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
        slc_lun = 0
        tlc_lun = 1
        return (slc_lun, tlc_lun)
    def post_process(self) -> None:
        pass

    def get_vb_group_size(self, vb_group_type:str) ->int:
        #_log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
        access_vendor_mode()
        vuc = ExecuteCMD.VendorCmdRead()
        vuc.assign(length=DATA_SIZE_8K_BYTE, cmd_index=VendorCmd.DUMP_VB_INFO)
        vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
        vuc.upiu.u16_cdb.b3_rsvd = 3
        i = vuc.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        rsp = ExecuteCMD.read_response(i)
        rsp_data = rsp.data
        ExecuteCMD.clear()
        group_index = VBList().VB_GROUP_LIST[vb_group_type]
        group_size = int.from_bytes(rsp_data[group_index*4:group_index*4 + 4],'little')
        return group_size

    def compare_value(self,value:int,expect_value:int, desc:str="") -> None:
        if value != expect_value:
            logger.error(f'Expect {desc}={expect_value}, but = {value}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        logger.info(f'{desc} val = {value}')


run = Pattern().run
if __name__ == "__main__":
    run()