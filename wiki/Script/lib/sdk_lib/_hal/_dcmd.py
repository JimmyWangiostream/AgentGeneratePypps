import ctypes
from ._base import Dll, handle_error_code
from .exception import *

def set_debug_cmd(dll: Dll, idx: int, arg_buf: bytearray, reserved: int, data_buf: bytearray):
    """Set debug command
    
    Args:
        dll: Dll instance
        pbyIndex: Debug command index
        *pbyArgBuf: Argument for debug command
        Reserved: Reserved
        *pbyBuffer: Data buffer
    """
    dll.cdll.Set_Debug_Cmd.argtypes = [ctypes.c_void_p, ctypes.c_ubyte,
                                       ctypes.POINTER(ctypes.c_ubyte), ctypes.c_ubyte,
                                       ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Set_Debug_Cmd.restype = ctypes.c_ubyte
    
    dll.errcode = dll.cdll.Set_Debug_Cmd(
        dll.sdk,
        ctypes.c_ubyte(idx),
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf),
        ctypes.c_ubyte(reserved),
        (ctypes.c_ubyte * len(data_buf)).from_buffer(data_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Set debug command failed"),
            0x02: (DLL_ERROR, "Unsupport on ps2806"),
            0x03: (DLL_ERROR, "Unsupport on ps2807")
        }, "set_debug_cmd")

def get_debug_cmd(dll: Dll, idx: int) -> bytearray:
    """Get debug command information

    Args:
        dll: Dll instance
        pbyIndex: Debug command index
        
    return:
        *pbyInfoBuf: Info. buffer
    """
    dll.cdll.Get_Debug_Cmd.argtypes = [ctypes.c_void_p, ctypes.c_ubyte,
                                       ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Get_Debug_Cmd.restype = ctypes.c_ubyte

    info_buf = bytearray(512)
    dll.errcode = dll.cdll.Get_Debug_Cmd(
        dll.sdk,
        ctypes.c_ubyte(idx),
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Get debug command failed"),
            0x02: (DLL_ERROR, "Unsupport on ps2806"),
            0x03: (DLL_ERROR, "Unsupport on ps2807")
        }, "get_debug_cmd")

    return info_buf

def debug_cmd_monitor(dll: Dll, index: int, arg_buf: bytearray) -> bytearray:
    """Get debug command background operation status

    Args:
        dll: Dll instance
        index: Debug command index
        arg_buf: Argument for debug command monitor
        
    Returns:
        *pbyInfoBuf: Info. buffer
    """
    info_buf = bytearray(512)

    dll.cdll.Debug_Cmd_Monitor.argtypes = [ctypes.c_void_p, ctypes.c_ubyte,
                                           ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Debug_Cmd_Monitor.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Debug_Cmd_Monitor(
        dll.sdk,
        ctypes.c_ubyte(index),
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf),
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Failed"),
            0x02: (DLL_ERROR, "Unsupport on ps2806"),
            0x03: (DLL_ERROR, "Unsupport on ps2807")
        }, "debug_cmd_monitor")
    return info_buf