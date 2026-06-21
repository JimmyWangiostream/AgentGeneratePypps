from copy import copy
from typing import Final
from Script.api import shared
import Script.api.cmd_seq as ExecuteCMD
from Script.api.exception import PATTERN_ASSERT_UNEXPECTED_CONDITION, SIGHTING_FAIL_DATA_COMPARE_FAIL
from Script.api.ufs_api.debug_cmd.dcmd_enum import Dcmd5ResetType
from Script.api.ufs_api.defines.constant_define import DATA_SIZE_4K_BYTE
from Script.api.ufs_api.defines.enum_define import VendorCmdRuleCdb2, VendorCmd, VendorCmdRuleCdb3
from Script.api.ufs_api.initial_device import init_tester_to_unit_ready
from Script.api.ufs_api.vendor_cmd.functions import access_vendor_mode
from Script.api.ufs_api.vendor_cmd.hw_setting.field_defines import HwSettingField
from Script.api.ufs_api.vendor_cmd.hw_setting.hw_setting import HwSetting

_log = shared.logger

class HwSetting8317(HwSetting):
    def __init__(self, ce_num: int) -> None:
        self.ce_num = ce_num
        self._data_size = DATA_SIZE_4K_BYTE
        self._data = bytearray(self._data_size)
        self._backup_data = bytearray(self._data_size)
        self._field_offset_map: dict[HwSettingField, int] = {
            HwSettingField.SYS_VDT_MASK_1: 1154 ,
            HwSettingField.ENABLE_ULTRA_DMA: 1229 ,
            HwSettingField.ENABLE_ULTRA_DMA: 1229 ,
            HwSettingField.COP0_TO_VALUE_LOW: 1230 ,
            HwSettingField.COP0_TO_VALUE_HIGH: 1231 ,
            HwSettingField.COP0_TO_RESOLUTION: 1232 ,
            HwSettingField.FLH_DQS_EXTRA_MODE: 1233 ,
            HwSettingField.E3D_ENABLE: 1234 ,
            HwSettingField.CLOCK_GATING_EN: 1235 ,
            HwSettingField.FFU_FEATURE: 1286 ,
            HwSettingField.POWER_SAVING_CTRL_ENABLE: 1287 ,
            HwSettingField.SUSPEND_SCALE: 1288 ,
            HwSettingField.SUSPEND_TIMER: 1289 ,
            HwSettingField.FW_DEBUG_MODE: 1275 ,
            HwSettingField.DATARELIBILITY_INDEX: 1309 ,
            HwSettingField.DATAPREREAD_ENABLE: 1311 ,
            HwSettingField.SCSI_CMD_SUPPORT: 1316 ,
            HwSettingField.MAX_PURGE_TIMEOUT_THRESHOLD_FIELD: 1329 ,
            HwSettingField.BKOPS_TIMER: 1336 ,
            HwSettingField.TEMPERATURE_EVENT_NOTIFICATION_ENABLE: 1337 ,
            HwSettingField.DEVICE_TOO_HIGH_TEMP_BOUNDARY: 1338 ,
            HwSettingField.DEVICE_TOO_LOW_TEMP_BOUNDARY: 1339 ,
            HwSettingField.THERMAL_SOLUTION_ENABLE_BACK_GND_GC_FEATURE_UART_TJ_ENABLE: 1342,
            HwSettingField.DVFS_TS_LEVEL_1: 1343 ,
            HwSettingField.DVFS_TS_LEVEL_2: 1344 ,
            HwSettingField.MT_DELAY_TS_LEVEL_1: 1352 ,
            HwSettingField.MT_DELAY_TS_LEVEL_2: 1353 ,
            HwSettingField.EOB_WA: 1378 ,
            HwSettingField.SIM_POWER_ENABLE: 1385 ,
            HwSettingField.FORCE_TLC_SLC: 1408 ,
            HwSettingField.SLC_CACHE_SIZE_AT_0_PERCENT_LOGICAL_SATURATION: 1414 ,
            HwSettingField.FLUSH_DATA_TO_L1_THRESHOLD: 1419 ,
            HwSettingField.CURRENT_WRITEBOOSTERBUFFERSIZE_DISPLAY_MODE: 1437 ,
            HwSettingField.SDU_SIZE: 1438 ,
            HwSettingField.ENABLE_XCOPY_ERR_CHECK: 1443 ,
            HwSettingField.HPB_MISS_CNT_THRESHOLD: 1501 ,
            HwSettingField.HPB_AGING_THRESHOLD: 1502 ,
            HwSettingField.HPB_WRITE_BUFFER_CMD_ABORT: 1503 ,
            HwSettingField.ERASE_GRP_CNT: 1819 ,
            HwSettingField.SLC_ERASE_GRP0_READ_CNT_THRESHOLD_LOW_FIELD: 1820 ,
            HwSettingField.SLC_ERASE_GRP0_READ_CNT_THRESHOLD_HIGH_FIELD: 1821 ,
            HwSettingField.SLC_ERASE_GRP1_READ_CNT_THRESHOLD_LOW_FIELD: 1822 ,
            HwSettingField.SLC_ERASE_GRP1_READ_CNT_THRESHOLD_HIGH_FIELD: 1823 ,
            HwSettingField.TLC_ERASE_GRP0_READ_CNT_THRESHOLD_LOW_FIELD: 1834 ,
            HwSettingField.TLC_ERASE_GRP0_READ_CNT_THRESHOLD_HIGH_FIELD: 1835 ,
            HwSettingField.TLC_ERASE_GRP1_READ_CNT_THRESHOLD_LOW_FIELD: 1836 ,
            HwSettingField.TLC_ERASE_GRP1_READ_CNT_THRESHOLD_HIGH_FIELD: 1837 ,
            HwSettingField.SLC_ERASE_GRP0_URGENT_READ_CNT_THRESHOLD_LOW_FIELD: 1848 ,
            HwSettingField.SLC_ERASE_GRP0_URGENT_READ_CNT_THRESHOLD_HIGH_FIELD: 1849 ,
            HwSettingField.SLC_ERASE_GRP1_URGENT_READ_CNT_THRESHOLD_LOW_FIELD: 1850 ,
            HwSettingField.SLC_ERASE_GRP1_URGENT_READ_CNT_THRESHOLD_HIGH_FIELD: 1851 ,
            HwSettingField.TLC_ERASE_GRP0_URGENT_READ_CNT_THRESHOLD_LOW_FIELD: 1862 ,
            HwSettingField.TLC_ERASE_GRP0_URGENT_READ_CNT_THRESHOLD_HIGH_FIELD: 1863 ,
            HwSettingField.TLC_ERASE_GRP1_URGENT_READ_CNT_THRESHOLD_LOW_FIELD: 1864 ,
            HwSettingField.TLC_ERASE_GRP1_URGENT_READ_CNT_THRESHOLD_HIGH_FIELD: 1865 ,
            HwSettingField.SLC_ERASE_GRP0_ERASE_CNT_THRESHOLD_LOW_FIELD: 1876 ,
            HwSettingField.SLC_ERASE_GRP0_ERASE_CNT_THRESHOLD_HIGH_FIELD: 1877 ,
            HwSettingField.TLC_ERASE_GRP0_ERASE_CNT_THRESHOLD_LOW_FIELD: 1888 ,
            HwSettingField.TLC_ERASE_GRP0_ERASE_CNT_THRESHOLD_HIGH_FIELD: 1889 ,
            HwSettingField.ONFI_TIMING_MODE: 0x422,
        }

    def update_from_device(self) -> None:
        access_vendor_mode() #todo shall not specified vendor
        vuc = ExecuteCMD.VendorCmdRead()
        vuc.assign(length=self._data_size, cmd_index=VendorCmd.READ_HW_SETTING, cmd_set_type=0x0F)

        i = vuc.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        rsp = ExecuteCMD.read_response(i)
        self._data = rsp.data
        ExecuteCMD.clear()

    def set_to_device(self, field: HwSettingField | None=None, val: int | None=None) -> None:
        if self._is_only_one_none(field, val):
            _log.error('Missing a parameter in set_to_device, shall field and val have value or both be None.')
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        if field is not None and val is not None:
            self.set_local_val(field, val)

        set_val_buf = bytearray(self._data)
        access_vendor_mode() #todo shall not specified vendor
        vuc = ExecuteCMD.VendorCmdWrite()
        vuc.assign(length=self._data_size, cmd_index=VendorCmd.WRITE_HW_SETTING, cmd_set_type=0x0F)
        vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
        vuc.upiu.u16_cdb.b3_rsvd = VendorCmdRuleCdb3.CMD_OTHER
        vuc.data = self._data
        vuc.enqueue()
        ExecuteCMD.send()
        init_tester_to_unit_ready(resetmode=Dcmd5ResetType.HW_RESET)
        self.update_from_device()
        self._compare_diff(self._data, set_val_buf)
    
    def _compare_diff(self, data: bytearray, expect: bytearray) -> None:
        HW_setting_skip_offset_begin = 0xB20
        HW_setting_skip_offset_end = 0xB79 + 1

        # 比對前段與後段（跳過中間 HW setting 區段）
        if (data[:HW_setting_skip_offset_begin] != expect[:HW_setting_skip_offset_begin] or
            data[HW_setting_skip_offset_end:self._data_size - 4] != expect[HW_setting_skip_offset_end:self._data_size - 4]):
            for i in range(self._data_size - 4):
                if HW_setting_skip_offset_begin <= i < HW_setting_skip_offset_end:
                    continue
                if data[i] != expect[i]:
                    _log.info(f'Expect[0x{i:X}] = 0x{expect[i]:X}, but Curr[0x{i:X}] = 0x{data[i]:X}')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                
    def get_offset(self, field: HwSettingField) -> int:
        try:
            offset = self._field_offset_map[field]
        except KeyError:
            _log.error(f'Cannot find HW_Setting field = {field.name} with this project.')
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        
        if offset > self._data_size:
            _log.error(f'HW_Setting offset[0x{offset:X}] is out of range! Expect to be smaller than 0x{self._data_size:X}.Please check field_offset_map in {type(self)} class.')
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        
        return offset