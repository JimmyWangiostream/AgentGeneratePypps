from ._sdk_base import _SDKLibProtocol
from .. import _hal
from . import log_callback as logger
from enum import Enum, auto

class PowerChannel(Enum):
    VCC = 1
    VCCQ2 = auto()
    VCCQ = auto()

class VoltageChannel(Enum):
    VCC = 4
    VCCQ2 = auto()
    VCCQ = auto()

class CurrentChannel(Enum):
    VCC = 1
    VCCQ2 = auto()
    VCCQ = auto()

class Power_Control(Enum):
    POWER_OFF = 0
    POWER_ON = 1

class Power_Channel(Enum):
    POWER_CHANNEL_ALL = 0
    POWER_CHANNEL_VCC = 1
    POWER_CHANNEL_VCCQ2 = 2
    POWER_CHANNEL_VCCQ = 3

class MeasureCurrentResult:
    def __init__(self, info_buf: bytearray):
        self.current = int.from_bytes(info_buf[0:4], byteorder='big') #unit: uA
        self.table_state = info_buf[4]
        self.reserved = info_buf[5:]

class PowerChangeSetting:
    def __init__(self):
        self.tx_mode = 0 #1-Fase, 2-Slow, 3-Hibernate, 4-Fast Auto, 5-Slow Auto, 7-Unchange
        self.rx_mode = 0 #1-Fase, 2-Slow, 3-Hibernate, 4-Fast Auto, 5-Slow Auto, 7-Unchange
        self.tx_gear = 0 #1-Gear1, 2-Gear2, 3-Gear3, 4-Gear4, 5-Gear5, 6-Gear6, 7-Gear7
        self.rx_gear = 0 #1-Gear1, 2-Gear2, 3-Gear3, 4-Gear4, 5-Gear5, 6-Gear6, 7-Gear7
        self.tx_lane = 0 #1-1 Lane, 2-2 Lane
        self.rx_lane = 0 #1-1 Lane, 2-2 Lane
        self.hs_rate = 0 #Bit 0 – Rx_Termination, Bit 1 – Tx_Termination, Bit 2 – LINE-RESET
                         #Bit 3 – HS_Series, 0 – Rate A series, 1 – Rate B series
                         #Bit 4 – UserDataValid, 0 – Using HW default setting, ignore api timeout setting, 1 – Refer api timeout setting
                         #Bit 5 – Scramble,
        self.fc0_protection_timeout = 8191 #Attribute ID 0x2041
        self.tc0_relay_timeout = 65535 #Attribute ID 0x2042
        self.afc0_req_timeout = 32767 #Attribute ID 0x2043
        self.fc1_protection_timeout = 8191 #Attribute ID 0x2061
        self.tc1_relay_timeout = 65535 #Attribute ID 0x2062
        self.afc1_req_timeout = 32767 #Attribute ID 0x2063

class _SDKLibPowerMixin(_SDKLibProtocol):
    def power_change(self, power_change_setting: PowerChangeSetting):

        mode = (power_change_setting.rx_mode << 16) | power_change_setting.tx_mode
        gear = (power_change_setting.rx_gear << 16) | power_change_setting.tx_gear
        lane = (power_change_setting.rx_lane << 16) | power_change_setting.tx_lane
        hs_rate = power_change_setting.hs_rate

        fc0_protection_timeout = power_change_setting.fc0_protection_timeout
        tc0_relay_timeout = power_change_setting.tc0_relay_timeout
        afc0_req_timeout = power_change_setting.afc0_req_timeout
        fc1_protection_timeout = power_change_setting.fc1_protection_timeout
        tc1_relay_timeout = power_change_setting.tc1_relay_timeout
        afc1_req_timeout = power_change_setting.afc1_req_timeout

        _hal.power_change(self._dll, 
                          mode, 
                          gear, 
                          lane, 
                          hs_rate, 
                          fc0_protection_timeout, 
                          tc0_relay_timeout, 
                          afc0_req_timeout, 
                          fc1_protection_timeout, 
                          tc1_relay_timeout, 
                          afc1_req_timeout)
        
    def power_control(self, on_off_value: int, channel_sel: int):
        _hal.power_control(self._dll, on_off_value, channel_sel)

    def switch_voltage_value(self, voltage: float, power_channel: int, vcc_discharge_level: int = 0):
        _hal.switch_voltage_value(self._dll, voltage, power_channel, vcc_discharge_level)

    def hibernate_enter(self):
        _hal.hibernate_enter(self._dll)
    
    def hibernate_exit(self):
        _hal.hibernate_exit(self._dll)

    def measure_current(self, channel_sel: int, option: int = 0) -> MeasureCurrentResult:
        tmp_buf = _hal.measure_current(self._dll, channel_sel, option)
        return MeasureCurrentResult(tmp_buf)
    
    def measure_current_user_define(self, channel_sel: int, count: int) -> bytearray:
        return _hal.measure_current_user_define(self._dll, channel_sel, count)

    def measure_voltage(self, channel_sel: int) -> int:
        tmp_bytearray = _hal.measure_voltage(self._dll, channel_sel)
        voltage = int.from_bytes(tmp_bytearray[0:4], byteorder='big') # unit: mv
        return voltage