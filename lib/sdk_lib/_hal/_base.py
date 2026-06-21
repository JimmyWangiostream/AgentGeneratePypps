import dataclasses
import ctypes
from typing import Union
from ..user import log_callback
from .exception import SDK_UNDEFINED_ERROR, error_data
from ..user import constant as const

@dataclasses.dataclass
class Dll:
    cdll: ctypes.CDLL
    sdk: ctypes.c_void_p
    errcode: int = 0
    msg: str = ""

def create_sdk_win32(dll_path: str) -> Dll:
    """Create SDK instance for 32-bit DLL
    
    Args:
        dll_path: Path to the DLL
        
    Returns:
        Dll instance
    """
    print("create win32 sdk...")
    dll = ctypes.CDLL(dll_path)
    sdk = ctypes.c_void_p(dll.CVendorCmd_Create())
    return Dll(dll, sdk)

def create_sdk_x64(dll_path: str) -> Dll:
    """Create SDK instance for 64-bit DLL
    
    Args:
        dll_path: Path to the DLL
        
    Returns:
        Dll instance
    """
    print("create x64 sdk...")
    dll = ctypes.CDLL(dll_path)
    dll.CVendorCmd_Create.restype = ctypes.c_uint64
    sdk = ctypes.c_void_p(dll.CVendorCmd_Create())
    return Dll(dll, sdk)

def delete_sdk(dll: Dll):
    """Delete SDK instance
    
    Args:
        dll: Dll instance
    """
    print("delete sdk...")
    dll.cdll.CVendorCmd_Delete(dll.sdk)
    dll.sdk = ctypes.c_void_p(None)

# Define the GuiLogEntry structure for logging
class _GuiLogEntry(ctypes.LittleEndianStructure):
    _fields_ = [
        ("logGroup_No", ctypes.c_uint),
        ("logMSG_Type", ctypes.c_uint),
        ("logMSG_No", ctypes.c_uint),
        ("srcline", ctypes.c_uint),
        ("tcstreline", ctypes.c_uint),
        ("logtreeLevel", ctypes.c_uint),
        ("logFormatType", ctypes.c_uint),
        ("pbfilename", ctypes.c_char * 1024),
        ("pbmsg", ctypes.c_char_p),
        ("msglen", ctypes.c_uint),
        ("pbdata", ctypes.c_char_p),
        ("datalen", ctypes.c_uint)
    ]

pflogData_callback_phison = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(_GuiLogEntry))
@pflogData_callback_phison
def _sdk_logger(p_log_entry):
    """SDK logger callback function
    Args:
        p_log_entry: Pointer to GuiLogEntry structure
    Returns:
        0 for success
    """
    if p_log_entry.contents.pbmsg is not None:
        try:
            content = p_log_entry.contents.pbmsg.decode("utf-8")
        except Exception as e:
            content = f"Unexpected error decoding log message: {e}"
    else:
        content = "p_log_entry.contents.pbmsg is None, cannot decode."

    log = log_callback.prepare_log_entry(
        message=content,
        level=log_callback.LogEntry.Level.INFO,
        source=log_callback.LogEntry.Source.SDK
    )
    log_callback.print_log(log)
    return 0

def set_log_data_callback_ui(dll: Dll):
    """Set log data callback for UI
    
    Args:
        dll: Dll instance
        drive: Drive number
    """
    dll.cdll.SetLogDataCallBackUI.argtypes = [ctypes.c_void_p ,pflogData_callback_phison]
    dll.cdll.SetLogDataCallBackUI.restype = None
    dll.cdll.SetLogDataCallBackUI(dll.sdk, _sdk_logger)

def handle_error_code(errcode, error_map, fun_name, error_data: error_data = None):
    if error_map is None:
        error_map = {}
    if errcode in error_map:
        error_class, error_message = error_map[errcode]
        if error_data is not None:
            raise error_class(f"[{fun_name}] {error_message}", error_data)
        raise error_class(f"[{fun_name}] {error_message}")
    else:
        raise SDK_UNDEFINED_ERROR(f"[{fun_name}] Unknown DLL error: {hex(errcode)}")