import ctypes
from ._base import Dll, const, handle_error_code
from .exception import *

def debug_fw_event_activate(dll: Dll, opt: int):
    """Debug FW Event function activate
    Args:
        dll: Dll instance
        opt: Option to activate or deactivate
    """
    dll.cdll.debug_fw_event_activate.argtypes = [ctypes.c_void_p, ctypes.c_ubyte]
    dll.cdll.debug_fw_event_activate.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.debug_fw_event_activate(
        dll.sdk,
        ctypes.c_ubyte(opt) # 0-disable, 1-enable
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Debug FW Event Activate failed.")
        }, "debug_fw_event_activate")
    
def debug_fw_event_result(dll: Dll) -> bytearray:
    """Get Debug FW Event Result
    Args:
        dll: Dll instance

    Returns:
        Bytearray containing debug fw event result informat
    """
    info_buf = bytearray(const.DATA_SIZE_256K_BYTE)

    dll.cdll.debug_fw_event_result.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.debug_fw_event_result.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.debug_fw_event_result(
        dll.sdk,
         (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Debug FW Event Result failed.")
        }, "debug_fw_event_result")

    return info_buf

def debug_fw_event_reset(dll: Dll):
    """Reset Debug FW Event
    Args:
        dll: Dll instance
    """
    dll.cdll.debug_fw_event_reset.argtypes = [ctypes.c_void_p]
    dll.cdll.debug_fw_event_reset.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.debug_fw_event_reset(dll.sdk)
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Debug FW Event Reset failed.")
        }, "debug_fw_event_reset")
    