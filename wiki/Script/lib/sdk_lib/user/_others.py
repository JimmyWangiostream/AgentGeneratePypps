from ._sdk_base import _SDKLibProtocol
from .. import _hal
from .._hal._others import *

class MphyEyeMonitorElement:
    def __init__(self, c_element: MPHY_EYE_MONITOR_ELEMENT = None):
        self.s32Timing = 0
        self.s32Voltage = 0
        self.u32ErrCnt = 0
        self.u32TestCnt = 0
        if c_element:
            self.s32Timing = c_element.s32Timing
            self.s32Voltage = c_element.s32Voltage
            self.u32ErrCnt = c_element.u32ErrCnt
            self.u32TestCnt = c_element.u32TestCnt

class MphyEyeMonitorResult:
    def __init__(self, c_result: MPHY_EYE_MONITOR_RESULT = None):
        self.u8_error = 0
        self.u8_sub_error = 0
        self.u8_fail_step = 0
        self.u8_rsvd1 = 0
        self.u32_l0_ro_curr_sslms_c0_c1_bk1 = 0
        self.u32_l0_ro_curr_sslms_c2_c3_bk1 = 0
        self.u32_l0_ro_curr_sslms_c4_c5_bk1 = 0
        self.u32_l0_ro_curr_sum_c1_c2_bk1 = 0
        self.u32_l0_ro_curr_sum_c3_c4_bk1 = 0
        self.u32_l0_ro_curr_sum_c5_tot_bk1 = 0
        self.u32_l1_ro_curr_sslms_c0_c1_bk1 = 0
        self.u32_l1_ro_curr_sslms_c2_c3_bk1 = 0
        self.u32_l1_ro_curr_sslms_c4_c5_bk1 = 0
        self.u32_l1_ro_curr_sum_c1_c2_bk1 = 0
        self.u32_l1_ro_curr_sum_c3_c4_bk1 = 0
        self.u32_l1_ro_curr_sum_c5_tot_bk1 = 0
        self.u32_l0_ro_curr_sslms_c0_c1_bk2 = 0
        self.u32_l0_ro_curr_sslms_c2_c3_bk2 = 0
        self.u32_l0_ro_curr_sslms_c4_c5_bk2 = 0
        self.u32_l0_ro_curr_sum_c1_c2_bk2 = 0
        self.u32_l0_ro_curr_sum_c3_c4_bk2 = 0
        self.u32_l0_ro_curr_sum_c5_tot_bk2 = 0
        self.u32_l1_ro_curr_sslms_c0_c1_bk2 = 0
        self.u32_l1_rocurr_sslms_c2_c3_bk2 = 0
        self.u32_l1_ro_curr_sslms_c4_c5_bk2 = 0
        self.u32_l1_ro_curr_sum_c1_c2_bk2 = 0
        self.u32_l1_ro_curr_sum_c3_c4_bk2 = 0
        self.u32_l1_ro_curr_sum_c5_tot_bk2 = 0
        self.u8_em_attr_eyemon_cap = 0
        self.u8_em_attr_timing_max_step_cap = 0
        self.u8_em_attr_timing_max_offset_cap = 0
        self.u8_em_attr_voltage_max_step_cap = 0
        self.u8_em_attr_voltage_max__offset_cap = 0
        self.u8_em_attr_eyemon_enable = 0
        self.u8_em_attr_timing_step = 0
        self.u8_em_attr_voltage_step = 0
        self.u8_em_attr_target_test_cnt = 0
        self.u24_rsvd2 = 0
        self.mDataArray = [MPHY_EYE_MONITOR_ELEMENT() for _ in range(127 * 127)]
        if c_result:
            self._from_c_result(c_result)

    def _from_c_result(self, c_result: MPHY_EYE_MONITOR_RESULT):
        self.u8_error = c_result.monitorData.mData.u8Err
        self.u8_sub_error = c_result.monitorData.mData.u8SubErr
        self.u8_fail_step = c_result.monitorData.mData.u8FailStep
        self.u8_rsvd1 = c_result.monitorData.mData.u8Rsvd1
        self.u32_l0_ro_curr_sslms_c0_c1_bk1 = c_result.monitorData.mData.u32L0_RO_CURR_SSLMS_C0_C1_BK1
        self.u32_l0_ro_curr_sslms_c2_c3_bk1 = c_result.monitorData.mData.u32L0_RO_CURR_SSLMS_C2_C3_BK1
        self.u32_l0_ro_curr_sslms_c4_c5_bk1 = c_result.monitorData.mData.u32L0_RO_CURR_SSLMS_C4_C5_BK1
        self.u32_l0_ro_curr_sum_c1_c2_bk1 = c_result.monitorData.mData.u32L0_RO_CURR_SUM_C1_C2_BK1
        self.u32_l0_ro_curr_sum_c3_c4_bk1 = c_result.monitorData.mData.u32L0_RO_CURR_SUM_C3_C4_BK1
        self.u32_l0_ro_curr_sum_c5_tot_bk1 = c_result.monitorData.mData.u32L0_RO_CURR_SUM_C5_TOT_BK1
        self.u32_l1_ro_curr_sslms_c0_c1_bk1 = c_result.monitorData.mData.u32L1_RO_CURR_SSLMS_C0_C1_BK1
        self.u32_l1_ro_curr_sslms_c2_c3_bk1 = c_result.monitorData.mData.u32L1_RO_CURR_SSLMS_C2_C3_BK1
        self.u32_l1_ro_curr_sslms_c4_c5_bk1 = c_result.monitorData.mData.u32L1_RO_CURR_SSLMS_C4_C5_BK1
        self.u32_l1_ro_curr_sum_c1_c2_bk1 = c_result.monitorData.mData.u32L1_RO_CURR_SUM_C1_C2_BK1
        self.u32_l1_ro_curr_sum_c3_c4_bk1 = c_result.monitorData.mData.u32L1_RO_CURR_SUM_C3_C4_BK1
        self.u32_l1_ro_curr_sum_c5_tot_bk1 = c_result.monitorData.mData.u32L1_RO_CURR_SUM_C5_TOT_BK1
        self.u32_l0_ro_curr_sslms_c0_c1_bk2 = c_result.monitorData.mData.u32L0_RO_CURR_SSLMS_C0_C1_BK2
        self.u32_l0_ro_curr_sslms_c2_c3_bk2 = c_result.monitorData.mData.u32L0_RO_CURR_SSLMS_C2_C3_BK2
        self.u32_l0_ro_curr_sslms_c4_c5_bk2 = c_result.monitorData.mData.u32L0_RO_CURR_SSLMS_C4_C5_BK2
        self.u32_l0_ro_curr_sum_c1_c2_bk2 = c_result.monitorData.mData.u32L0_RO_CURR_SUM_C1_C2_BK2
        self.u32_l0_ro_curr_sum_c3_c4_bk2 = c_result.monitorData.mData.u32L0_RO_CURR_SUM_C3_C4_BK2
        self.u32_l0_ro_curr_sum_c5_tot_bk2 = c_result.monitorData.mData.u32L0_RO_CURR_SUM_C5_TOT_BK2
        self.u32_l1_ro_curr_sslms_c0_c1_bk2 = c_result.monitorData.mData.u32L1_RO_CURR_SSLMS_C0_C1_BK2
        self.u32_l1_rocurr_sslms_c2_c3_bk2 = c_result.monitorData.mData.u32L1_ROCURR_SSLMS_C2_C3_BK2
        self.u32_l1_ro_curr_sslms_c4_c5_bk2 = c_result.monitorData.mData.u32L1_RO_CURR_SSLMS_C4_C5_BK2
        self.u32_l1_ro_curr_sum_c1_c2_bk2 = c_result.monitorData.mData.u32L1_RO_CURR_SUM_C1_C2_BK2
        self.u32_l1_ro_curr_sum_c3_c4_bk2 = c_result.monitorData.mData.u32L1_RO_CURR_SUM_C3_C4_BK2
        self.u32_l1_ro_curr_sum_c5_tot_bk2 = c_result.monitorData.mData.u32L1_RO_CURR_SUM_C5_TOT_BK2
        self.u8_em_attr_eyemon_cap = c_result.monitorData.mData.u8EM_ATTR_EYEMON_CAP
        self.u8_em_attr_timing_max_step_cap = c_result.monitorData.mData.u8EM_ATTR_TIMING_MAX_STEP_CAP
        self.u8_em_attr_timing_max_offset_cap = c_result.monitorData.mData.u8EM_ATTR_TIMING_MAX_OFFSET_CAP
        self.u8_em_attr_voltage_max_step_cap = c_result.monitorData.mData.u8EM_ATTR_VOLTAGE_MAX_STEP_CAP
        self.u8_em_attr_voltage_max__offset_cap = c_result.monitorData.mData.u8EM_ATTR_VOLTAGE_MAX_OFFSET_CAP
        self.u8_em_attr_eyemon_enable = c_result.monitorData.mData.u8EM_ATTR_EYEMON_ENABLE
        self.u8_em_attr_timing_step = c_result.monitorData.mData.u8EM_ATTR_TIMING_STEP
        self.u8_em_attr_voltage_step = c_result.monitorData.mData.u8EM_ATTR_VOLTAGE_STEP
        self.u8_em_attr_target_test_cnt = c_result.monitorData.mData.u8EM_ATTR_TARGET_TEST_CNT
        self.u24_rsvd2 = c_result.monitorData.mData.u24Rsvd2
        for i in range(127 * 127):
            self.mDataArray[i] = MphyEyeMonitorElement(c_result.mDataArray[i])

class MphyEyeMonitorParam:
    def __init__(self):
        self.u8_action = 0
        self.is_peer = 0
        self.is_hs = 0
        self.is_rate = 0
        self.is_lane = 0
        self.is_scramble = 0
        self.u3_gear = 0
        self.u2_before_adapt = 0
        self.u2_test_adapt = 0
        self.u7_target_test_cnt = 0
    
    def to_c_param(self) -> MPHY_EYE_MONITOR_PARAM:
        c_param = MPHY_EYE_MONITOR_PARAM()
        c_param.u8Action = self.u8_action
        c_param.isPeer = self.is_peer
        c_param.isHS = self.is_hs
        c_param.isRateB = self.is_rate
        c_param.isLANE1 = self.is_lane
        c_param.isScramble = self.is_scramble
        c_param.u3Gear = self.u3_gear
        c_param.u2BeforeAdapt = self.u2_before_adapt
        c_param.u2TestAdapt = self.u2_test_adapt
        c_param.u7TargetTestCnt = self.u7_target_test_cnt
        return c_param

class _SDKLibOthersMixin(_SDKLibProtocol):
    def software_crc(self, s: bytearray, length: int, first_in: int, last_crc: int):
        _hal.software_crc(self._dll, s, length, first_in, last_crc)
    
    def cal_sha2_hmac(self, key: bytearray, key_len: int, input: bytearray, ilen: int, output: bytearray, is_224: int):
        _hal.cal_sha2_hmac(self._dll, key, key_len, input, ilen, output, is_224)

    def on_switch_ref_clk(self, ref_clk: float):
        _hal.on_switch_ref_clk(self._dll, ref_clk)

    def direct_read_page(self, info_buff: bytearray):
        _hal.direct_read_page(self._dll, info_buff)

    def get_sdk_tester_internal_info(self) -> str:
        return _hal.get_sdk_tester_internal_info(self._dll)
    
    def force_boot_code(self, mode: int, sl_delay: int, ll_delay: int, sll_delay, slh_delay: int):
        _hal.force_boot_code(self._dll, mode, sl_delay, ll_delay, sll_delay, slh_delay)

    def mphy_eye_monitor(self, param: MphyEyeMonitorParam) -> MphyEyeMonitorResult:
        c_param = param.to_c_param()
        result = _hal.mphy_eye_monitor(self._dll, c_param)
        return MphyEyeMonitorResult(result)
    
    def generate_ptng_data(self, lun: int, read_task_tag: int, lba: int, data_byte: int, data_cnt: int, write_buf: bytearray, read_buf: bytearray):
        return _hal.generate_ptng_data(self._dll, lun, read_task_tag, lba, data_byte, data_cnt, write_buf, read_buf)