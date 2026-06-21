import ctypes
from ._base import Dll, handle_error_code
from .exception import *

def get_host_info(dll: Dll) -> bytearray:
    """Group a packed write or read command
    Arg:
        dll: Dll instance
        info_buf: Bytearray containing host information
    Returns:
        info_buf: Bytearray containing host information

    """
    info_buf = bytearray(16384)

    dll.cdll.Get_HostInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Get_HostInfo.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Get_HostInfo(
        dll.sdk,
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Get host info operation failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "Get_HostInfo")
    
    return info_buf

def get_host_reg(dll: Dll, reg_idx: int) -> bytearray:
    """Read a register value from the host
    Arg:
        dll: Dll instance
        reg_idx: Register index
        data_buf: Bytearray containing host register data

    Returns:
        data_buf: Bytearray containing host register data
    """
    data_buf = bytearray(2048)

    dll.cdll.Get_HostReg.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Get_HostReg.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Get_HostReg(
        dll.sdk,
        ctypes.c_ubyte(reg_idx),
        (ctypes.c_ubyte * len(data_buf)).from_buffer(data_buf),
    )

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Get host reg operation failed"),
        }, "Get_HostReg")
    
    return data_buf
