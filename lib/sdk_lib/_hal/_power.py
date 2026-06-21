import ctypes
from ._base import Dll, handle_error_code
from .exception import *

def power_change(dll: Dll, mode: int, gear: int, lane: int, hs_rate: int, 
                fc0_protection_timeout: int, tc0_replay_timeout: int, afc0_req_timeout: int,
                fc1_protection_timeout: int, tc1_replay_timeout: int, afc1_req_timeout: int):
    """Configure speed and timeout setting
    ※ Mode, Gear & Lane are set for Device UniPro
    
    Args:
        dll: Dll instance
        mode: [31:16]->tx mode [15:0]->rx mode
        gear: [31:16]->tx gear [15:0]->rx gear
        lane: [31:16]->tx lane [15:0]->rx lane
        hs_rate: HS Rate (PWR.Flags)
        fc0_protection_timeout: FC0 protection timeout, default = 8191
        tc0_replay_timeout: TC0 replay timeout, default = 65535
        afc0_req_timeout: AFC0 request timeout, default = 32767
        fc1_protection_timeout: FC1 protection timeout, default = 8191
        tc1_replay_timeout: TC1 replay timeout, default = 65535
        afc1_req_timeout: AFC1 request timeout, default = 32767
    """
    dll.cdll.PowerChange.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.c_uint32, ctypes.c_uint32
    ]
    dll.cdll.PowerChange.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.PowerChange(
        dll.sdk,
        ctypes.c_uint32(mode),
        ctypes.c_uint32(gear),
        ctypes.c_uint32(lane),
        ctypes.c_uint32(hs_rate),
        ctypes.c_uint32(fc0_protection_timeout),
        ctypes.c_uint32(tc0_replay_timeout),
        ctypes.c_uint32(afc0_req_timeout),
        ctypes.c_uint32(fc1_protection_timeout),
        ctypes.c_uint32(tc1_replay_timeout),
        ctypes.c_uint32(afc1_req_timeout)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Power change failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "power_change")
    return dll.errcode

def power_control(dll: Dll, on_off_value: int, channel_sel: int):
    """Control power switch
    
    Args:
        dll: Dll instance
        on_off_value: Switch value (0: Off, 1: On)
        channel_sel: Channel selection
        
    Returns:
        Operation status code
    """

    dll.cdll.PowerControl.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_ubyte]
    dll.cdll.PowerControl.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.PowerControl(
        dll.sdk,
        ctypes.c_ubyte(on_off_value),
        ctypes.c_ubyte(channel_sel)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Power control failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "power_control")

def switch_voltage_value(dll: Dll, voltage: float, channel_sel: int, vcc_discharge_level: int = 0) -> int:
    """Switch voltage value
    
    Args:
        dll: Dll instance
        voltage: Voltage value, Ex: 3.3 for 3.3V
        channel_sel: Channel selection, 1: VCC (1.6V ~ 3.6V), 2: VCCQ2 (0.8V ~ 2.0V), 3: VCCQ (0.8V ~ 1.5V)
        vcc_discharge_level: VCC discharge level, default is 0
    """
    dll.cdll.SwitchVoltageValue.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_ubyte, ctypes.c_ubyte]
    dll.cdll.SwitchVoltageValue.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.SwitchVoltageValue(
        dll.sdk,
        ctypes.c_double(voltage),
        ctypes.c_ubyte(channel_sel),
        ctypes.c_ubyte(vcc_discharge_level)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Switch voltage value failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "switch_voltage_value")
    return dll.errcode

def hibernate_enter(dll: Dll):
    """Enter hibernate mode
    
    Args:
        dll: Dll instance
    """
    dll.cdll.HibernateEnter.argtypes = [ctypes.c_void_p]
    dll.cdll.HibernateEnter.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.HibernateEnter(dll.sdk)

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Hibernate enter failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "hibernate_enter")
    return dll.errcode

def hibernate_exit(dll: Dll):
    """Exit hibernate mode
    
    Args:
        dll: Dll instance
    """
    dll.cdll.HibernateExit.argtypes = [ctypes.c_void_p]
    dll.cdll.HibernateExit.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.HibernateExit(dll.sdk)
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Hibernate exit failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "hibernate_exit")
    return dll.errcode

def measure_current(dll: Dll, channel_sel: int, option: int = 0) -> bytearray:
    """Measure VCC/ VCCQ2/VCCQ Current
    
    Args:
        dll: Dll instance
        channel_sel: Channel selection
        option: Option, default is 0
        
    Returns:
        output data, 512bytes
    """
    data = bytearray(512)
    dll.cdll.Measure_Current.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, 
                                         ctypes.POINTER(ctypes.c_ubyte), ctypes.c_ubyte]
    dll.cdll.Measure_Current.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Measure_Current(
        dll.sdk,
        ctypes.c_ubyte(channel_sel),
        (ctypes.c_ubyte * len(data)).from_buffer(data),
        ctypes.c_ubyte(option)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Measure current failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "measure_current")
    return data

def measure_current_user_define(dll: Dll, channel_sel: int, count: int) -> bytearray:
    """User-defined current measurement
    
    Args:
        dll: Dll instance
        channel_sel: Channel selection
        count: Measurement count
        
    Returns:
        Bytearray containing measurement results
    """
    data = bytearray(512)

    dll.cdll.Measure_Current_UserDefine.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, 
                                                    ctypes.c_ushort, ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Measure_Current_UserDefine.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Measure_Current_UserDefine(
        dll.sdk,
        ctypes.c_ubyte(channel_sel),
        ctypes.c_ushort(count),
        (ctypes.c_ubyte * len(data)).from_buffer(data)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, None, "measure_current_user_define")
    return data

def measure_voltage(dll: Dll, channel_sel: int) -> bytearray:
    """Measure voltage
    
    Args:
        dll: Dll instance
        channel_sel: Channel selection
        
    Returns:
        Bytearray containing measurement results
    """
    pyb_buff = bytearray(512)
    dll.cdll.Measure_Voltage.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Measure_Voltage.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Measure_Voltage(
        dll.sdk,
        ctypes.c_ubyte(channel_sel),
        (ctypes.c_ubyte * len(pyb_buff)).from_buffer(pyb_buff)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, None, "measure_voltage")
    return pyb_buff 