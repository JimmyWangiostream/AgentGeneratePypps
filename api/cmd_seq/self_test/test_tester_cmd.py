from Script.api.self_test.base import ApiTestBase
from Script import api
from Script.api import shared
import Script.api.cmd_seq as ExecuteCMD

class TestNormalCase(ApiTestBase):
    def setUp(self) -> None:
        ExecuteCMD.clear()

    def test_power_cycle(self) -> None:
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET)
        cmd = ExecuteCMD.CmdSeqPowerCycle()
        cmd.set_option(api.PowerCycleMode.ALL_POWER_DOWN)
        idx = cmd.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        r = ExecuteCMD.read_response(idx)
        self.assertIsInstance(r, api.CmdSeqPowerCycleResponse) 

    def test_switch_voltage(self) -> None:
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET)
        cmd = ExecuteCMD.CmdSeqSwitchVoltage()
        cmd.set_option(vcc=33000, vccq2=18000, vccq=12000)
        idx = cmd.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        r = ExecuteCMD.read_response(idx)
        self.assertIsInstance(r, api.CmdSeqSwitchVoltageResponse) 

    def test_switch_ref_clk(self) -> None:
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET)
        cmd = ExecuteCMD.CmdSeqSwitchReferenceClock()
        cmd.set_option()
        idx = cmd.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        r = ExecuteCMD.read_response(idx)
        self.assertIsInstance(r, api.CmdSeqSwitchReferenceClockResponse) 

    def test_speed_change(self) -> None:
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET)
        cmd = ExecuteCMD.CmdSeqSpeedChange()
        cmd.set_option()
        idx = cmd.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        r = ExecuteCMD.read_response(idx)
        self.assertIsInstance(r, api.CmdSeqSpeedChangeResponse) 

    def test_initial_flow(self) -> None:
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET)
        cmd = ExecuteCMD.CmdSeqInitialFlow()
        cmd.set_option()
        idx = cmd.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        r = ExecuteCMD.read_response(idx)
        self.assertIsInstance(r, api.CmdSeqInitialFlowResponse) 

    def test_gpio_trigger(self) -> None:
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET)
        cmd = ExecuteCMD.CmdSeqGpioTrigger()
        cmd.set_option(mode=1, toggle_delay=0)
        idx = cmd.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        r = ExecuteCMD.read_response(idx)
        self.assertIsInstance(r, api.CmdSeqGpioTriggerResponse) 

    def test_hibernate(self) -> None:
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET)
        cmd = ExecuteCMD.CmdSeqHibernate()
        cmd.set_option(1, 1, loopcount=0, delayafterenter=100, delayafterexit=100)
        idx = cmd.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        r = ExecuteCMD.read_response(idx)
        self.assertIsInstance(r, api.CmdSeqHibernateResponse) 

    def test_testunitready(self) -> None:
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET)
        cmd = ExecuteCMD.CmdSeqTestUnitReady()
        cmd.set_option(lun=0)
        idx = cmd.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        r = ExecuteCMD.read_response(idx)
        self.assertIsInstance(r, api.CmdSeqTestUnitReadyResponse) 

    def test_powercontrol(self) -> None:
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET)
        cmd = ExecuteCMD.CmdSeqPowerControl()
        cmd.set_option(mode=0, channel=1, spendtime=0, ramptime=0)
        cmd.set_option(mode=1, channel=1, spendtime=0, ramptime=0, delay_time=100)
        idx = cmd.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        r = ExecuteCMD.read_response(idx)
        self.assertIsInstance(r, api.CmdSeqPowerControlResponse) 

    def test_ready_device_init_flag(self) -> None:
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET)
        cmd = ExecuteCMD.CmdSeqReadyDeviceInitFlag()
        idx = cmd.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        r = ExecuteCMD.read_response(idx)
        self.assertIsInstance(r, api.CmdSeqReadyDeviceInitFlagResponse) 

    def test_push_nop_out_poll_nop_in(self) -> None:
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET)
        cmd = ExecuteCMD.CmdSeqPushNopOutPollNopIn()
        cmd.set_option(timeout=10000000)
        idx = cmd.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        r = ExecuteCMD.read_response(idx)
        self.assertIsInstance(r, api.CmdSeqPushNopOutPollNopInResponse) 
