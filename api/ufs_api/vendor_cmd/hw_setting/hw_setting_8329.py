from copy import copy
from typing import Final
from Script.api import shared
import Script.api.cmd_seq as ExecuteCMD
from Script.api.exception import PATTERN_ASSERT_UNEXPECTED_CONDITION, SIGHTING_FAIL_DATA_COMPARE_FAIL, SIGHTING_FAIL_WRONG_CE_NUMBER_VALUE
from Script.api.ufs_api.debug_cmd.dcmd_enum import Dcmd5ResetType
from Script.api.ufs_api.defines.constant_define import DATA_SIZE_12K_BYTE, DATA_SIZE_16K_BYTE, DATA_SIZE_4K_BYTE, DATA_SIZE_8K_BYTE
from Script.api.ufs_api.defines.enum_define import VendorCmdRuleCdb2, VendorCmd, VendorCmdRuleCdb3
from Script.api.ufs_api.initial_device import init_tester_to_unit_ready
from Script.api.ufs_api.vendor_cmd.functions import access_vendor_mode
from Script.api.ufs_api.vendor_cmd.hw_setting.field_defines import HwSettingField
from Script.api.ufs_api.vendor_cmd.hw_setting.hw_setting import HwSetting

_log = shared.logger

class HwSetting8329(HwSetting):
    def __init__(self, ce_num: int) -> None:
        self.ce_num = ce_num
        self._data_size = DATA_SIZE_16K_BYTE
        self._data = bytearray(self._data_size)
        self._backup_data = bytearray(self._data_size)
        self._field_offset_map: dict[HwSettingField, int] = {
            HwSettingField.REG_CFG_OPT0_LOW_FIELD: 0x531,
            HwSettingField.REG_CFG_OPT0_HIGH_FIELD: 0x532,
            HwSettingField.CH0_FDIV_RSEL: 0x802,
            HwSettingField.SYS_VDT_MASK_1: 0x80F,
            HwSettingField.SYS_VDT_MASK_2: 0x810,
            HwSettingField.E3D_ENABLE: 0x81C,
            HwSettingField.ONFI_TIMING_MODE: 0x814,
            HwSettingField.MCU_INT_EN_HIGH_FIELD: 0x92E,
            HwSettingField.UNIPRO_ERR_BIT_EN_1_BIT_7_0: 0x931,
            HwSettingField.UNIPRO_ERR_BIT_EN_1_BIT_15_8: 0x932,
            HwSettingField.UNIPRO_ERR_BIT_EN_1_BIT_23_16: 0x933,
            HwSettingField.UNIPRO_ERR_BIT_EN_1_BIT_31_24: 0x934,
            HwSettingField.SDU_SIZE: 0x935,
            HwSettingField.SLC_INVALID_THRESHOLD_BIT_7_0: 0x9D5,
            HwSettingField.SLC_INVALID_THRESHOLD_BIT_15_8: 0x9D6,
            HwSettingField.SLC_INVALID_THRESHOLD_BIT_23_16: 0x9D7,
            HwSettingField.SLC_INVALID_THRESHOLD_BIT_31_24: 0x9D8,
            HwSettingField.TLC_INVALID_THRESHOLD_BIT_7_0: 0x9D9,
            HwSettingField.TLC_INVALID_THRESHOLD_BIT_15_8: 0x9DA,
            HwSettingField.TLC_INVALID_THRESHOLD_BIT_23_16: 0x9DB,
            HwSettingField.TLC_INVALID_THRESHOLD_BIT_31_24: 0x9DC,
            HwSettingField.ENHANCED_SLC_PE_COUNT_THRESHOLD_LOW_FIELD: 0x9E9,
            HwSettingField.ENHANCED_SLC_PE_COUNT_THRESHOLD_HIGH_FIELD: 0x9EA,
            HwSettingField.FW_DEBUG_MODE: 0x9FB,
            HwSettingField.FW_YMTC_DEBUG_MODE: 0x9FB,
            HwSettingField.ENABLE_ULTRA_DMA: 0x9FF,
            HwSettingField.COP0_TO_VALUE_LOW: 0xA00,
            HwSettingField.COP0_TO_VALUE_HIGH: 0xA01,
            HwSettingField.COP0_TO_RESOLUTION: 0xA02,
            HwSettingField.CLOCK_GATING_EN: 0xA05,
            HwSettingField.FFU_FEATURE: 0xA06,
            HwSettingField.POWER_SAVING_CTRL_ENABLE: 0xA07,
            HwSettingField.SUSPEND_SCALE: 0xA08,
            HwSettingField.SUSPEND_TIMER: 0xA09,
            HwSettingField.BKOPS_TIMER: 0xA0A,
            HwSettingField.BKOPS_TIMER_KIC_ONLY: 0xA0B,
            HwSettingField.DATAPREREAD_ENABLE: 0xA1F,
            HwSettingField.PREREAD_THRESHOLD: 0xA21,
            HwSettingField.SCSI_CMD_SUPPORT: 0xA24,
            HwSettingField.DISABLE_FEATURE_SLC_PROGRAM_ON_MAX_GEAR_D3_PROGRAM_MODE: 0xA28,
            HwSettingField.MAX_PURGE_TIMEOUT_THRESHOLD_LOW_FIELD: 0xA31,
            HwSettingField.MAX_PURGE_TIMEOUT_THRESHOLD_HIGH_FIELD: 0xA32,
            HwSettingField.KIC_FFU_SPECIFIC_SVN_BYTE0: 0xA33,
            HwSettingField.KIC_FFU_SPECIFIC_SVN_BYTE1: 0xA34,
            HwSettingField.KIC_FFU_SPECIFIC_SVN_BYTE2: 0xA35,
            HwSettingField.KIC_FFU_SPECIFIC_SVN_BYTE3: 0xA36,
            HwSettingField.TEMPERATURE_EVENT_NOTIFICATION_ENABLE: 0xA39,
            HwSettingField.DEVICE_TOO_HIGH_TEMP_BOUNDARY: 0xA3A,
            HwSettingField.DEVICE_TOO_LOW_TEMP_BOUNDARY: 0xA3B,
            HwSettingField.THERMAL_SOLUTION_ENABLE_BACK_GND_GC_FEATURE_UART_TJ_ENABLE: 0xA3E,
            HwSettingField.DVFS_TS_LEVEL_1: 0xA3F,
            HwSettingField.DVFS_TS_LEVEL_2: 0xA40,
            HwSettingField.MT_DELAY_TS_LEVEL_1: 0xA48,
            HwSettingField.MT_DELAY_TS_LEVEL_2: 0xA49,
            HwSettingField.THERMAL_LV1_CPU_DIV_CTL: 0xA5A,
            HwSettingField.THERMAL_LV1_BUF_DIV_CTL: 0xA5B,
            HwSettingField.THERMAL_LV1_COP1_COR_DIV_CTL: 0xA5C,
            HwSettingField.THERMAL_LV1_ECC_ENC_ECC_DEC_DIV_CTL: 0xA5D,
            HwSettingField.FORCE_TLC_SLC: 0xA80,
            HwSettingField.WRITE_BOOSTER_BUFFER_FLUSH_POLICY: 0xA81,
            HwSettingField.PE_COUNT_THRESHOLD_LSB: 0xA82,
            HwSettingField.PE_COUNT_THRESHOLD_MSB: 0xA83,
            HwSettingField.SLC_CACHE_SIZE_AT_0_PERCENT_LOGICAL_SATURATION: 0xA86,
            HwSettingField.CMD_TIMEOUT_TIMER_WRITE: 0xA92,
            HwSettingField.WB_PE_THRESHOLD: 0xA93,
            HwSettingField.EMPTY_PAGE_SCAN_TRIGGER_TIME_A94: 0xA94,
            HwSettingField.EMPTY_PAGE_SCAN_TRIGGER_TIME_A95: 0xA95,
            HwSettingField.MEDIUM_SCAN_TRIGGER_TIME: 0xA96,
            HwSettingField.HH_ASSERT_EN_TEMP_H: 0xA99,
            HwSettingField.TCODE_SIGN_HH: 0xA99,
            HwSettingField.TEMP_SENSOR_HH_LOW_FIELD: 0xA9A,
            HwSettingField.HH_ASSERT_TEMP: 0xA9A,
            HwSettingField.INHIBITION_TIME: 0xA9F,
            HwSettingField.PRDH_FUNC_OPTION: 0xAC1,
            HwSettingField.PRDH_RAND_SCAN_THRESHOLD_BIT_7_0: 0xAC5,
            HwSettingField.PRDH_RAND_SCAN_THRESHOLD_BIT_15_8: 0xAC6,
            HwSettingField.PRDH_RAND_SCAN_THRESHOLD_BIT_23_16: 0xAC7,
            HwSettingField.PRDH_RAND_SCAN_THRESHOLD_BIT_31_24: 0xAC8,
            HwSettingField.PRDH_SEQ_SCAN_THRESHOLD_BIT_7_0: 0xAC9,
            HwSettingField.PRDH_SEQ_SCAN_THRESHOLD_BIT_15_8: 0xACA,
            HwSettingField.PRDH_SEQ_SCAN_THRESHOLD_BIT_23_16: 0xACB,
            HwSettingField.PRDH_SEQ_SCAN_THRESHOLD_BIT_31_24: 0xACC,
            HwSettingField.HPB_AGING_THRESHOLD: 0xADE,
            HwSettingField.HPB_WRITE_BUFFER_CMD_ABORT: 0xADF,
            HwSettingField.HPB_MISS_CNT_THRESHOLD: 0xADD,
            HwSettingField.PRDH_RAND_SCAN_QLC_PE0_THRESHOLD_BIT_7_0: 0xAEC,
            HwSettingField.PRDH_RAND_SCAN_QLC_PE0_THRESHOLD_BIT_15_8: 0xAED,
            HwSettingField.PRDH_RAND_SCAN_QLC_PE0_THRESHOLD_BIT_23_16: 0xAEE,
            HwSettingField.PRDH_RAND_SCAN_QLC_PE0_THRESHOLD_BIT_31_24: 0xAEF,
            HwSettingField.PRDH_RAND_SCAN_QLC_PE1_THRESHOLD_BIT_7_0: 0xAF0,
            HwSettingField.PRDH_RAND_SCAN_QLC_PE1_THRESHOLD_BIT_15_8: 0xAF1,
            HwSettingField.PRDH_RAND_SCAN_QLC_PE1_THRESHOLD_BIT_23_16: 0xAF2,
            HwSettingField.PRDH_RAND_SCAN_QLC_PE1_THRESHOLD_BIT_31_24: 0xAF3,
            HwSettingField.PRDH_SEQ_SCAN_QLC_PE0_THRESHOLD_BIT_7_0: 0xAF4,
            HwSettingField.PRDH_SEQ_SCAN_QLC_PE0_THRESHOLD_BIT_15_8: 0xAF5,
            HwSettingField.PRDH_SEQ_SCAN_QLC_PE0_THRESHOLD_BIT_23_16: 0xAF6,
            HwSettingField.PRDH_SEQ_SCAN_QLC_PE0_THRESHOLD_BIT_31_24: 0xAF7,
            HwSettingField.PRDH_SEQ_SCAN_QLC_PE1_THRESHOLD_BIT_7_0: 0xAF8,
            HwSettingField.PRDH_SEQ_SCAN_QLC_PE1_THRESHOLD_BIT_15_8: 0xAF9,
            HwSettingField.PRDH_SEQ_SCAN_QLC_PE1_THRESHOLD_BIT_23_16: 0xAFA,
            HwSettingField.PRDH_SEQ_SCAN_QLC_PE1_THRESHOLD_BIT_31_24: 0xAFB,
            HwSettingField.WRITE_DISPATCH_THRESHOLD_B04: 0xB04,
            HwSettingField.WRITE_DISPATCH_THRESHOLD_B05: 0xB05,
            HwSettingField.WRITE_DISPATCH_THRESHOLD_B06: 0xB06,
            HwSettingField.WRITE_DISPATCH_THRESHOLD_B07: 0xB07,
            HwSettingField.READ_COUNTER_THRESHOLD_B08: 0xB08,
            HwSettingField.READ_COUNTER_THRESHOLD_B09: 0xB09,
            HwSettingField.READ_COUNTER_THRESHOLD_B0A: 0xB0A,
            HwSettingField.READ_COUNTER_THRESHOLD_B0B: 0xB0B,
            HwSettingField.SEQ_READ_FACTOR_B0C: 0xB0C,
            HwSettingField.SEQ_READ_FACTOR_B0D: 0xB0D,
            HwSettingField.SEQ_READ_FACTOR_B0E: 0xB0E,
            HwSettingField.SEQ_READ_FACTOR_B0F: 0xB0F,
            HwSettingField.FLUSH_NEEDED_OPTION: 0xB12,
            HwSettingField.MIX_MODE_SLC_THRESHOLD: 0xB13,
            HwSettingField.MIX_MODE_TLC_THRESHOLD: 0xB14,
            HwSettingField.PRE_ERASE_ENABLE: 0xB16,
            HwSettingField.ENABLE_XCOPY_ERR_CHECK: 0xB17,
            HwSettingField.CONFIG_DESCR_THRESHOLD: 0xB18,
            HwSettingField.SENSE_GC_REPORT_LCA_ORDER: 0xB1C,
            HwSettingField.CE0_WRITE_DQ_PAD_DELAY_DQ01: 0xB20,
            HwSettingField.CE4_READ_OFFSET: 0xB79,
            HwSettingField.CE7_READ_OFFSET: 0xBAF,
            HwSettingField.ERASE_GRP_CNT: 0xC03,
            HwSettingField.INJECT_ERROR_TESTING_ENABLE_PWR_TEST_INIT_LOCK: 0xFED,
            HwSettingField.WB_FIFO_SIZE_DECREASE_CURVE_SELECTION: 0xA88,
            HwSettingField.LT_CE0_TX_VREF: 0xEEF,
            HwSettingField.LT_CE1_TX_VREF: 0xEF0,
            HwSettingField.LT_CE2_TX_VREF: 0xEF1,
            HwSettingField.LT_CE3_TX_VREF: 0xEF2,
            HwSettingField.CT_CE0_TX_VREF: 0xC19,
            HwSettingField.CT_CE1_TX_VREF: 0xC1A,
            HwSettingField.CT_CE2_TX_VREF: 0xC1B,
            HwSettingField.CT_CE3_TX_VREF: 0xC1C,
            HwSettingField.HT_CE0_TX_VREF: 0xD8E,
            HwSettingField.HT_CE1_TX_VREF: 0xD8F,
            HwSettingField.HT_CE2_TX_VREF: 0xD90,
            HwSettingField.HT_CE3_TX_VREF: 0xD91,            
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
        HW_setting_skip_offset_end = 0xC19 + 1

        ce_start_offset = self._get_ce_start_offset()
        data = data[ce_start_offset:ce_start_offset + DATA_SIZE_4K_BYTE] # trim to 1CE length
        expect = expect[ce_start_offset:ce_start_offset + DATA_SIZE_4K_BYTE] # trim to 1CE length
        
        # 比對前段與後段（跳過中間 HW setting 區段）
        if (data[:HW_setting_skip_offset_begin] != expect[:HW_setting_skip_offset_begin] or
            data[HW_setting_skip_offset_end:DATA_SIZE_4K_BYTE - 4] != expect[HW_setting_skip_offset_end:DATA_SIZE_4K_BYTE - 4]):
            for i in range(DATA_SIZE_4K_BYTE - 4):
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
        
        if offset > 0x0FFF:
            _log.error(f'HW_Setting offset[0x{offset:X}] is out of range! Expect to be 0x0800~0x0FFF(1CE range). Please check field_offset_map in {type(self)} class.')
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        
        ce_start_offset = self._get_ce_start_offset()
        
        return offset + ce_start_offset
    
    def _get_ce_start_offset(self) -> int:
        if self.ce_num == 1:
            offset = 0
        elif self.ce_num == 2:
            offset = DATA_SIZE_4K_BYTE
        elif self.ce_num == 4:
            offset = DATA_SIZE_8K_BYTE
        elif self.ce_num == 8:
            offset = DATA_SIZE_12K_BYTE
        else:
            _log.error(f'unexpected CE number = {self.ce_num}')
            raise SIGHTING_FAIL_WRONG_CE_NUMBER_VALUE
        return offset