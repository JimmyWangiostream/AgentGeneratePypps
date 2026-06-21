from .base import ApiTestBase
from Script.api import shared
from Script.lib import sdk_lib as lib

_sdk = shared.sdk

#pass
# class TestPwrChange(ApiTestBase):
#     def test_pwr_change(self):
#         setting = lib.PowerChangeSetting()
#         setting.rx_mode = 2
#         setting.tx_mode = 2
#         setting.rx_gear = 1
#         setting.tx_gear = 1
#         setting.rx_lane = 1
#         setting.tx_lane = 1
#         setting.hs_rate = 0
#         _sdk.power_change(setting)

#pass
# class TestPwrCtl(ApiTestBase):
#     def test_pwr_ctl_vcc_off(self):
#         _sdk.power_control(0, 1)
    
#     def test_pwr_ctl_vcc_on(self):
#         _sdk.power_control(1, 1)

#pass
# class TestSwitchVltVal(ApiTestBase):
#     def test_ufs31_switch_vlt_val(self):
#         VCC_STD_UFS3X = 2.5
#         VCCQ_STD = 1.3
#         VCCQ2_STD = 1.8
        
#         _sdk.host_initial(lib.HostInit.TESTER_POWER_OFF.value) # Reset Tester + Power OFF
#         _sdk.switch_voltage_value(VCC_STD_UFS3X, lib.PowerChannel.VCC.value) # vcc to 2.5v
#         vcc = _sdk.measure_voltage(lib.VoltageChannel.VCC.value) / 1000.0  # vcc to V
#         _sdk.switch_voltage_value(VCCQ2_STD, lib.PowerChannel.VCCQ2.value) # vccq2 to 1.8v
#         vccq2 = _sdk.measure_voltage(lib.VoltageChannel.VCCQ2.value) / 1000.0  # vccq2 to V
#         _sdk.switch_voltage_value(VCCQ_STD, lib.PowerChannel.VCCQ.value) # vccq to 1.3v
#         vccq = _sdk.measure_voltage(lib.VoltageChannel.VCCQ.value) / 1000.0  # vccq to V

#         # Round voltage values to one decimal place but keep as float
#         vcc = round(vcc, 1)
#         vccq2 = round(vccq2, 1)
#         vccq = round(vccq, 1)

#         self.assertEqual(vcc, VCC_STD_UFS3X)
#         self.assertEqual(vccq2, VCCQ2_STD)
#         self.assertEqual(vccq, VCCQ_STD)

#pass
# class TestHibernate(ApiTestBase):
#     def test_hibernate(self):
#         SCSI_CMD = 0x00
#         iid = 0
#         #SSU Sleep
#         ssu = lib.SendCmdStruct()
#         ssu.header.tran_type = lib.UPIU_Def.UPIU_CMD.value
#         ssu.header.lun = 208
#         ssu.header.task_tag = 0
#         ssu.header.iid_cmd_type = (SCSI_CMD | iid << 4)
#         ssu.header.ehs_len = 0
#         ssu.header.dat_seg_len = 0

#         ssu.tran.i12_sf0 = 0
#         ssu.tran.i16_sf1 = 27
#         ssu.tran.i20_sf2 = 32
#         ssu.tran.i24_sf3 = 0
#         ssu.tran.i28_sf4 = 0

#         ssu.timeout = 16837216
#         ssu.action = 1
#         ssu.pattern_mode = 0
#         ssu.pattern_tag = 0
#         ssu.seed_h = 0
#         ssu.seed_l = 0
#         ssu.by4k_gen = 0
#         _sdk.send_cmd(ssu)

#         _sdk.hibernate_enter()
#         _sdk.hibernate_exit()

#         #SSU Active
#         ssu.header.tran_type = lib.UPIU_Def.UPIU_CMD.value
#         ssu.header.lun = 208
#         ssu.header.task_tag = 0
#         ssu.header.iidD_CMD_Typee = (SCSI_CMD | iid << 4)
#         ssu.header.ehs_len = 0
#         ssu.header.dat_seg_len = 0

#         ssu.tran.i12_sf0 = 0
#         ssu.tran.i16_sf1 = 27
#         ssu.tran.i20_sf2 = 32
#         ssu.tran.i24_sf3 = 0
#         ssu.tran.i28_sf4 = 0

#         ssu.timeout = 16837216
#         ssu.action = 1
#         ssu.pattern_mode = 0
#         ssu.pattern_tag = 0
#         ssu.seed_h = 0
#         ssu.seed_l = 0
#         ssu.by4k_gen = 0
#         _sdk.send_cmd(ssu)

#pass
# class TestMeasureCurrent(ApiTestBase):
#     def test_measrue_cur(self):
#         vcc_result = _sdk.measure_current(CurrentChannel.VCC.value)
#         vccq2_result = _sdk.measure_current(CurrentChannel.VCCQ2.value)
#         vccq_result = _sdk.measure_current(CurrentChannel.VCC.value)
#         print(f"measrue_cur, vcc = {vcc_result.current}")
#         print(f"measrue_cur, vccq2 = {vccq2_result.current}")
#         print(f"measrue_cur, vccq = {vccq_result.current}")
