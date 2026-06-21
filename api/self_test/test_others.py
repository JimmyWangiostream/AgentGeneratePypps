from .base import ApiTestBase
from Script.api import shared
from Script.lib import sdk_lib as lib

_sdk = shared.sdk

#pass
# class TestOnSwitchRefClk(ApiTestBase):
#     def test_on_switch_ref_clk(self):
#         _sdk.on_switch_ref_clk(19.2)
#         _sdk.on_switch_ref_clk(26)
#         _sdk.on_switch_ref_clk(38.4)
#         _sdk.on_switch_ref_clk(52)

#no data
# class TestGetSDKTesterInternalInfo(ApiTestBase):
#     def test_get_sdk_tester_internal_info(self):
#         internal_info = _sdk.get_sdk_tester_internal_info()
#         print(internal_info)

#pass
# class TestForceBootCode(ApiTestBase):
#     def test_force_boot_code(self):
#         _sdk.force_boot_code(0, 0, 0, 0, 0)

#stop work
# class TestMPHYEyeMonitor(ApiTestBase):
#     def test_mphy_eye_monitor(self):
#         arg_buf  = lib.MphyEyeMonitorParam()
#         arg_buf.u8_action = 0
#         arg_buf.is_peer = 0
#         arg_buf.is_hs = 1
#         arg_buf.is_rate = 0
#         arg_buf.is_lane = 0
#         arg_buf.is_scramble = 0
#         arg_buf.u3_gear = 4
#         arg_buf.u2_before_adapt = 0
#         arg_buf.u2_test_adapt = 0
#         arg_buf.u7_target_test_count = 1

#         #run eye monitor flow
#         result = _sdk.mphy_eye_monitor(arg_buf)

#         #dump eye monitor flow
#         arg_buf.u8_action = 1
#         result = _sdk.mphy_eye_monitor(arg_buf)
#         print("u8_error: ", result.u8_error)
#         print("u8_sub_error: ", result.u8_sub_error)
#         print("u8_fail_step: ", result.u8_fail_step)
#         print("u8_rsvd1: ", result.u8_rsvd1)
#         print("u32_l0_ro_curr_sslms_c0_c1_bk1: ", result.u32_l0_ro_curr_sslms_c0_c1_bk1)
#         print("u32_l0_ro_curr_sslms_c2_c3_bk1: ", result.u32_l0_ro_curr_sslms_c2_c3_bk1)
#         print("u32_l0_ro_curr_sslms_c4_c5_bk1: ", result.u32_l0_ro_curr_sslms_c4_c5_bk1)
#         print("u32_l0_ro_curr_sum_c1_c2_bk1: ", result.u32_l0_ro_curr_sum_c1_c2_bk1)
#         print("u32_l0_ro_curr_sum_c3_c4_bk1: ", result.u32_l0_ro_curr_sum_c3_c4_bk1)
#         print("u32_l0_ro_curr_sum_c5_tot_bk1: ", result.u32_l0_ro_curr_sum_c5_tot_bk1)
#         print("u32_l1_ro_curr_sslms_c0_c1_bk1: ", result.u32_l1_ro_curr_sslms_c0_c1_bk1)
#         print("u32_l1_ro_curr_sslms_c2_c3_bk1: ", result.u32_l1_ro_curr_sslms_c2_c3_bk1)
#         print("u32_l1_ro_curr_sslms_c4_c5_bk1: ", result.u32_l1_ro_curr_sslms_c4_c5_bk1)
#         print("u32_l1_ro_curr_sum_c1_c2_bk1: ", result.u32_l1_ro_curr_sum_c1_c2_bk1)
#         print("u32_l1_ro_curr_sum_c3_c4_bk1: ", result.u32_l1_ro_curr_sum_c3_c4_bk1)
#         print("u32_l1_ro_curr_sum_c5_tot_bk1: ", result.u32_l1_ro_curr_sum_c5_tot_bk1)
#         print("u32_l0_ro_curr_sslms_c0_c1_bk2: ", result.u32_l0_ro_curr_sslms_c0_c1_bk2)
#         print("u32_l0_ro_curr_sslms_c2_c3_bk2: ", result.u32_l0_ro_curr_sslms_c2_c3_bk2)
#         print("u32_l0_ro_curr_sslms_c4_c5_bk2: ", result.u32_l0_ro_curr_sslms_c4_c5_bk2)
#         print("u32_l0_ro_curr_sum_c1_c2_bk2: ", result.u32_l0_ro_curr_sum_c1_c2_bk2)
#         print("u32_l0_ro_curr_sum_c3_c4_bk2: ", result.u32_l0_ro_curr_sum_c3_c4_bk2)
#         print("u32_l0_ro_curr_sum_c5_tot_bk2: ", result.u32_l0_ro_curr_sum_c5_tot_bk2)
#         print("u32_l1_ro_curr_sslms_c0_c1_bk2: ", result.u32_l1_ro_curr_sslms_c0_c1_bk2)
#         print("u32_l1_rocurr_sslms_c2_c3_bk2: ", result.u32_l1_rocurr_sslms_c2_c3_bk2)
#         print("u32_l1_ro_curr_sslms_c4_c5_bk2: ", result.u32_l1_ro_curr_sslms_c4_c5_bk2)
#         print("u32_l1_ro_curr_sum_c1_c2_bk2: ", result.u32_l1_ro_curr_sum_c1_c2_bk2)
#         print("u32_l1_ro_curr_sum_c3_c4_bk2: ", result.u32_l1_ro_curr_sum_c3_c4_bk2)
#         print("u32_l1_ro_curr_sum_c5_tot_bk2: ", result.u32_l1_ro_curr_sum_c5_tot_bk2)
#         print("u8_em_attr_eyemon_cap: ", result.u8_em_attr_eyemon_cap)
#         print("u8_em_attr_timing_max_step_cap: ", result.u8_em_attr_timing_max_step_cap)
#         print("u8_em_attr_timing_max_offset_cap: ", result.u8_em_attr_timing_max_offset_cap)
#         print("u8_em_attr_voltage_max_step_cap: ", result.u8_em_attr_voltage_max_step_cap)
#         print("u8_em_attr_voltage_max__offset_cap: ", result.u8_em_attr_voltage_max__offset_cap)
#         print("u8_em_attr_eyemon_enable: ", result.u8_em_attr_eyemon_enable)
#         print("u8_em_attr_timing_step: ", result.u8_em_attr_timing_step)
#         print("u8_em_attr_voltage_step: ", result.u8_em_attr_voltage_step)
#         print("u8_em_attr_target_test_cnt: ", result.u8_em_attr_target_test_cnt)
#         print("u24_rsvd2: ", list(result.u24_rsvd2))
#         print("1st Timing: ", result.mDataArray[0].s32Timing)
#         print("1st Voltage: ", result.mDataArray[0].s32Voltage)
#         print("1st Err Cnt: ", result.mDataArray[0].u32ErrCnt)
#         print("1st Test Cnt: ", result.mDataArray[0].u32TestCnt)

#         #free eye monitor buffer
#         arg_buf.u8_action = 2
#         result = _sdk.mphy_eye_monitor(arg_buf)


#fail
# class GeneratePTNGData(ApiTestBase):
#     def test_generate_ptng_data(self):
#         write_buf = bytearray(512)
#         read_buf = bytearray(512)
#         _sdk.generate_ptng_data(0, 0, 0, 512, 1, write_buf, read_buf)
#         print(list(write_buf))
#         print(list(read_buf))
