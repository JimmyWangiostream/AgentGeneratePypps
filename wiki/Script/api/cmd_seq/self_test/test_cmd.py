from Script.api.exception import PATTERN_ASSERT_ILLEGAL_PARAM_HW_COMPARE_MIX_WITH_MANUAL_MODE
from Script.api.self_test.base import ApiTestBase
from Script.api import shared
import Script.api.cmd_seq as ExecuteCMD
from Script.api.ufs_api.defines import PowerCycleMode, SpdChgPowerMode, SpdChgGear, SpdChgLane, SpdChgHsRate, CmdParamPatternMode


_sdk = shared.sdk

class TestNopOutAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.NopOut()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestFormatUnitAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.FormatUnit()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestInquiryAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Inquiry()        
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestModeSelect10(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ModeSelect10()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestModeSense10(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ModeSense10()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestPreFetch10(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.PreFetch10()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestPreFetch16(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.PreFetch16()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestRead6(ApiTestBase):
    def test_mid_with_sw_cmp(self) -> None:
        f = ExecuteCMD.Read6()
        f.set_option(manual_mode=True, wait_queue_empty=True, timeout=100, delay_time=1000)
        f.set_sw_cmp(crc32=12345)
        self.assertEqual(f.param.w36_crc_compare, 1)
        self.assertEqual(f.param.w36_add_tag, 0)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)
        self.assertEqual(f.param.l38_mark_tag_or_crc32, 12345)
    def test_mid_with_hw_cmp_expect_raise_bad_param_exception(self) -> None:
        f = ExecuteCMD.Read6()
        f.set_option(manual_mode=True, wait_queue_empty=True, timeout=100, delay_time=1000)
        with self.assertRaises(PATTERN_ASSERT_ILLEGAL_PARAM_HW_COMPARE_MIX_WITH_MANUAL_MODE):
            f.set_hw_cmp(mark_tag=54321, pattern_mode=CmdParamPatternMode.HW_FIX)
    def test_mid_with_hw_cmp(self) -> None:
        f = ExecuteCMD.Read6()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        f.set_hw_cmp(mark_tag=54321, pattern_mode=CmdParamPatternMode.HW_FIX)
        self.assertEqual(f.param.w36_crc_compare, 0)
        self.assertEqual(f.param.w36_add_tag, 1)
        self.assertEqual(f.param.w36_data_in_out, 0)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)
        self.assertEqual(f.param.l38_mark_tag_or_crc32, 54321)
        self.assertEqual(f.param.w36_pattern_mode, CmdParamPatternMode.HW_FIX)

class TestRead10(ApiTestBase):
    def test_mid_with_sw_cmp(self) -> None:
        f = ExecuteCMD.Read10()
        f.set_option(manual_mode=True, wait_queue_empty=True, timeout=100, delay_time=1000)
        f.set_sw_cmp(crc32=12345)
        self.assertEqual(f.param.w36_crc_compare, 1)
        self.assertEqual(f.param.w36_add_tag, 0)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)
        self.assertEqual(f.param.l38_mark_tag_or_crc32, 12345)
    def test_mid_with_hw_cmp_expect_raise_bad_param_exception(self) -> None:
        f = ExecuteCMD.Read10()
        f.set_option(manual_mode=True, wait_queue_empty=True, timeout=100, delay_time=1000)
        with self.assertRaises(PATTERN_ASSERT_ILLEGAL_PARAM_HW_COMPARE_MIX_WITH_MANUAL_MODE):
            f.set_hw_cmp(mark_tag=54321, pattern_mode=CmdParamPatternMode.HW_FIX)
    def test_mid_with_hw_cmp(self) -> None:
        f = ExecuteCMD.Read10()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        f.set_hw_cmp(mark_tag=54321, pattern_mode=CmdParamPatternMode.HW_FIX)
        self.assertEqual(f.param.w36_crc_compare, 0)
        self.assertEqual(f.param.w36_add_tag, 1)
        self.assertEqual(f.param.w36_data_in_out, 0)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)
        self.assertEqual(f.param.l38_mark_tag_or_crc32, 54321)
        self.assertEqual(f.param.w36_pattern_mode, CmdParamPatternMode.HW_FIX)

class TestRead16(ApiTestBase):
    def test_mid_with_sw_cmp(self) -> None:
        f = ExecuteCMD.Read16()
        f.set_option(manual_mode=True, wait_queue_empty=True, timeout=100, delay_time=1000)
        f.set_sw_cmp(crc32=12345)
        self.assertEqual(f.param.w36_crc_compare, 1)
        self.assertEqual(f.param.w36_add_tag, 0)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)
        self.assertEqual(f.param.l38_mark_tag_or_crc32, 12345)
    def test_mid_with_hw_cmp_expect_raise_bad_param_exception(self) -> None:
        f = ExecuteCMD.Read16()
        f.set_option(manual_mode=True, wait_queue_empty=True, timeout=100, delay_time=1000)
        with self.assertRaises(PATTERN_ASSERT_ILLEGAL_PARAM_HW_COMPARE_MIX_WITH_MANUAL_MODE):
            f.set_hw_cmp(mark_tag=54321, pattern_mode=CmdParamPatternMode.HW_FIX)
    def test_mid_with_hw_cmp(self) -> None:
        f = ExecuteCMD.Read16()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        f.set_hw_cmp(mark_tag=54321, pattern_mode=CmdParamPatternMode.HW_FIX)
        self.assertEqual(f.param.w36_crc_compare, 0)
        self.assertEqual(f.param.w36_add_tag, 1)
        self.assertEqual(f.param.w36_data_in_out, 0)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)
        self.assertEqual(f.param.l38_mark_tag_or_crc32, 54321)
        self.assertEqual(f.param.w36_pattern_mode, CmdParamPatternMode.HW_FIX)
        
class TestReadBuffer(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReadBuffer()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestReadCapacity10(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReadCapacity10()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestReadCapacity16(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReadCapacity16()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestReportLUNs(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReportLUNs()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestRequestSense(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.RequestSense()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestSecurityProtocolIn(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.SecurityProtocolIn()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestSecurityProtocolOut(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.SecurityProtocolOut()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestSendDiagnostic(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.SendDiagnostic()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestStartStopUnit(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.StartStopUnit()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestSyncCache10(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.SyncCache10()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestSyncCache16(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.SyncCache16()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestTestUnitReady(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.TestUnitReady()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestUnmap(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Unmap()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestVerify10(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Verify10()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestWrite6(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Write6()
        f.set_option(manual_mode=True, mark_tag=123, wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.specific_tag, 123)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestWrite10(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Write10()
        f.set_option(manual_mode=True, mark_tag=123, wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.specific_tag, 123)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestWrite16(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Write16()
        f.set_option(manual_mode=True, mark_tag=123, wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.specific_tag, 123)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestWriteBuffer(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.WriteBuffer()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestTaskManagement(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.TaskManagement()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestHpbRead(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.HpbRead()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestHpbReadBuffer(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.HpbReadBuffer()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestHpbWriteBuffer01(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.HpbWriteBuffer01()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestHpbWriteBuffer02(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.HpbWriteBuffer02()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestHpbWriteBuffer03(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.HpbWriteBuffer03()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestReadDescriptor(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReadDescriptor()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestWriteDescriptor(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.WriteDescriptor()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertEqual(f.param.w36_data_in_out, 1)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestReadAttribute(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReadAttribute()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestWriteAttribute(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.WriteAttribute()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestReadFlag(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReadFlag()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestSetFlag(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.SetFlag()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestClearFlag(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ClearFlag()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestToggleFlag(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ToggleFlag()
        f.set_option(wait_queue_empty=True, timeout=100, delay_time=1000)
        self.assertTrue(f.param.w36_wait_queue_empty)
        self.assertEqual(f.param.l50_timeout, 100)
        self.assertEqual(f.param.l32_delay_time, 1000)

class TestCmdSeqPowerCycle(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.CmdSeqPowerCycle()
        f.set_option(mode=PowerCycleMode.ALL_POWER_DOWN, wait_queue_empty=True, delay_time=100)
        self.assertEqual(f.upiu.b2_mode, PowerCycleMode.ALL_POWER_DOWN)
        self.assertTrue(f.w36_wait_queue_empty)
        self.assertEqual(f.l32_delay_time, 100)

class TestCmdSeqSwitchVoltage(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.CmdSeqSwitchVoltage()
        f.set_option(vcc=25000, vccq2=18000, vccq=13000, wait_queue_empty=True, delay_time=100)
        
        self.assertEqual(f.upiu.w2_vcc, 25000)
        self.assertEqual(f.upiu.w4_vccq2, 18000)
        self.assertEqual(f.upiu.w6_vccq, 13000)
        self.assertTrue(f.w36_wait_queue_empty)
        self.assertEqual(f.l32_delay_time, 100)

class TestCmdSeqSwitchReferenceClock(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.CmdSeqSwitchReferenceClock()
        f.set_option(wait_queue_empty=True, delay_time=100)
        
        self.assertTrue(f.w36_wait_queue_empty)
        self.assertEqual(f.l32_delay_time, 100)

class TestCmdSeqSpeedChange(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.CmdSeqSpeedChange()
        f.set_option(
            txmode=SpdChgPowerMode.FAST,
            rxmode=SpdChgPowerMode.FAST,
            txgear=SpdChgGear.GEAR_3,
            rxgear=SpdChgGear.GEAR_3,
            txlane=SpdChgLane.LANE_2,
            rxlane=SpdChgLane.LANE_2,
            hsrate=SpdChgHsRate.RATE_B,
            fc0protectiontimeout=8191,
            tc0replaytimeout=65535,
            afc0reqtimeout=32767,
            fc1protectiontimeout=8191,
            tc1replaytimeout=65535,
            afc1reqtimeout=32767,
            wait_queue_empty=True,
            delay_time=100
        )
        
        # Verify the attributes
        self.assertEqual(f.upiu.b2_hs_rate, SpdChgHsRate.RATE_B)
        self.assertEqual(f.upiu.b3_rx_mode, SpdChgPowerMode.FAST)
        self.assertEqual(f.upiu.b3_rx_lane, SpdChgLane.LANE_2)
        self.assertEqual(f.upiu.b3_rx_gear, SpdChgGear.GEAR_3)
        self.assertEqual(f.upiu.b4_tx_mode, SpdChgPowerMode.FAST)
        self.assertEqual(f.upiu.b4_tx_lane, SpdChgLane.LANE_2)
        self.assertEqual(f.upiu.b4_tx_gear, SpdChgGear.GEAR_3)
        self.assertEqual(f.upiu.w5_fc0_protection_timeout, 8191)
        self.assertEqual(f.upiu.w7_tc0_replay_timeout, 65535)
        self.assertEqual(f.upiu.w9_afc0_req_timeout, 32767)
        self.assertEqual(f.upiu.w11_fc1_protection_timeout, 8191)
        self.assertEqual(f.upiu.w13_tc1_replay_timeout, 65535)
        self.assertEqual(f.upiu.w15_afc1_req_timeout, 32767)
        self.assertTrue(f.w36_wait_queue_empty)
        self.assertEqual(f.l32_delay_time, 100)

class TestCmdSeqInitialFlow(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.CmdSeqInitialFlow()
        f.set_option(wait_queue_empty=True, delay_time=100)
        
        # Verify the attributes
        self.assertTrue(f.w36_wait_queue_empty)
        self.assertEqual(f.l32_delay_time, 100)

class TestCmdSeqGpioTrigger(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.CmdSeqGpioTrigger()
        f.set_option(mode=1, toggle_delay=5, wait_queue_empty=True, delay_time=100)
        
        # Verify the attributes
        self.assertEqual(f.upiu.b2_mode, 1)
        self.assertEqual(f.upiu.b3_toggle_delay, 5)
        self.assertTrue(f.w36_wait_queue_empty)
        self.assertEqual(f.l32_delay_time, 100)

class TestCmdSeqHibernate(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.CmdSeqHibernate()
        f.set_option(
            hibernate_enter=1,
            hibernate_exit=1,
            loopcount=10,
            delayafterenter=500,
            delayafterexit=1000,
            wait_queue_empty=True,
            delay_time=100
        )
        
        # Verify the attributes
        self.assertEqual(f.upiu.b2_hiberopt_enter, 1)
        self.assertEqual(f.upiu.b2_hiberopt_exit, 1)
        self.assertEqual(f.upiu.w3_loopcount, 10)
        self.assertEqual(f.upiu.l5_delayafterenter, 500)
        self.assertEqual(f.upiu.l9_delayafterexit, 1000)
        self.assertTrue(f.w36_wait_queue_empty)
        self.assertEqual(f.l32_delay_time, 100)

class TestCmdSeqTestUnitReady(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.CmdSeqTestUnitReady()
        f.set_option(lun=1, timeout=100000, wait_queue_empty=True, delay_time=100
        )
        
        # Verify the attributes
        self.assertEqual(f.upiu.b2_lun, 1)
        self.assertEqual(f.upiu.l3_timeout, 100000)
        self.assertTrue(f.w36_wait_queue_empty)
        self.assertEqual(f.l32_delay_time, 100)

class TestCmdSeqPowerControl(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.CmdSeqPowerControl()
        f.set_option(
            mode=1,
            channel=2,
            spendtime=500,
            ramptime=100,
            wait_queue_empty=True,
            delay_time=100
        )
        
        # Verify the attributes
        self.assertEqual(f.upiu.b2_mode, 1)
        self.assertEqual(f.upiu.b3_channel, 2)
        self.assertEqual(f.upiu.w4_spendtime, 500)
        self.assertEqual(f.upiu.w6_ramptime, 100)
        self.assertTrue(f.w36_wait_queue_empty)
        self.assertEqual(f.l32_delay_time, 100)

class TestCmdSeqReadyDeviceInitFlag(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.CmdSeqReadyDeviceInitFlag()
        f.set_option(wait_queue_empty=True, delay_time=100)
        
        # Verify the attributes
        self.assertTrue(f.w36_wait_queue_empty)
        self.assertEqual(f.l32_delay_time, 100)

class TestCmdSeqPushNopOutPollNopIn(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.CmdSeqPushNopOutPollNopIn()
        f.set_option(timeout=5000, wait_queue_empty=True, delay_time=100)
        
        # Verify the attributes
        self.assertEqual(f.upiu.l2_timeout, 5000)
        self.assertTrue(f.w36_wait_queue_empty)
        self.assertEqual(f.l32_delay_time, 100)
