import ctypes
from ._base import Dll, handle_error_code
from .exception import *

def reset_n(dll: Dll, mode: int, tRSTW: int):
    """Hard Reset
    Args:
        mode: RSTN_N control mode
        tRSTW: Delay time
    """
    dll.cdll.Reset_N.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_uint]
    dll.cdll.Reset_N.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Reset_N(
        dll.sdk,
        ctypes.c_ubyte(mode),
        ctypes.c_uint(tRSTW)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Reset N failed"),
            0x02: (DLL_ERROR, "Unsupport on ps2806"),
            0x03: (DLL_ERROR, "Unsupport on ps2807")
        }, "Reset_N")

def reset_n_key(dll: Dll, mode: int, option: int):
    """Reset N with Key
    Args:
        mode: Select execute item
        option: 
            Mode 0: Test Loop Count
            Mode 1: 1 = Enable , 0 = Disable
            Mode 2: None use
            Mode 3: None use
            Mode 4: 0 = 8317, 1 = 8318
    """
    dll.cdll.ResetN_Key.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_uint16]
    dll.cdll.ResetN_Key.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.ResetN_Key(
        dll.sdk,
        ctypes.c_ubyte(mode),
        ctypes.c_uint16(option)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Rest N Key failed"),
            0x02: (DLL_ERROR, "Unsupport on ps2806"),
            0x03: (DLL_ERROR, "Unsupport on ps2807")
        }, "ResetN_Key")
    
def reset_n_vendor_cmd(dll: Dll, direction: int, block_cnt: int, arg_pag: bytearray, data: bytearray):
    """Send VendorCMD by RSTN Pin
    Arg:
        direction: 0 = Read, 1 = Write
        block_cnt: Read/Write Block Count
        arg_pag: VendorCMD Argument
        data: Data In out buffer
    """
    dll.cdll.ResetN_VendorCMD.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_uint16, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.ResetN_VendorCMD.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.ResetN_VendorCMD(
        dll.sdk,
        ctypes.c_ubyte(direction),
        ctypes.c_uint16(block_cnt),
        (ctypes.c_ubyte * len(arg_pag)).from_buffer(arg_pag),
        (ctypes.c_ubyte * len(data)).from_buffer(data)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Reset N Vendor CMD failed"),
            0x02: (DLL_ERROR, "Unsupport on ps2806"),
            0x03: (DLL_ERROR, "Unsupport on ps2807")
        }, "ResetN_VendorCMD")

def clear_done_queue(dll: Dll, type: int, clear_item: int):
    """Clear Done Queue
    Arg:
        type: type for clear
        clear_item: item select for Tag done queue and LUN done queue
    """
    dll.cdll.Clear_DoneQueue.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_ubyte]
    dll.cdll.Clear_DoneQueue.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Clear_DoneQueue(
        dll.sdk,
        ctypes.c_ubyte(type),
        ctypes.c_ubyte(clear_item)
    )

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Clear Done Queue failed"),
            0x02: (DLL_ERROR, "Unsupport on ps2806"),
            0x03: (DLL_ERROR, "Unsupport on ps2807")
        }, "Clear_DoneQueue")
