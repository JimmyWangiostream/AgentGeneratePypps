import ctypes
from ._base import Dll, const, handle_error_code
from .exception import *

def sdk_track_activate(dll: Dll, arg_buf: bytearray):
    """Drive log activate
    Args:
        dll: Dll instance
        arg_buf: Bytearray containing arguments for sdk_track_activate function
    """
    dll.cdll.SDK_Track_Activate.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.SDK_Track_Activate.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.SDK_Track_Activate(
        dll.sdk,
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "sdk track activate failed"),
            0x02: (DLL_ERROR, "API with wrong parameters")
        }, "SDK_Track_Activate")
    
def sdk_track_reset(dll: Dll):
    """Reset drive log Info
    Args:
        dll: Dll instance
    """
    dll.cdll.SDK_Track_Reset.argtypes = [ctypes.c_void_p]
    dll.cdll.SDK_Track_Reset.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.SDK_Track_Reset(dll.sdk)
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "sdk track activate failed"),
            0x02: (DLL_ERROR, "API with wrong parameters")
        }, "SDK_Track_Reset")

def sdk_track_result(dll: Dll) -> bytearray:
    """Search drive log and return list that during time stamp.
    This API must be used immediately, because drive log have amount limit.
    Args:
        info_buf: bytearray to store the track result

    Returns:
        info_buf: bytearray to store the track result

    """
    info_buf = bytearray(284 * const.DATA_SIZE_1K_BYTE)

    dll.cdll.SDK_Track_Result.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.SDK_Track_Result.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.SDK_Track_Result(
        dll.sdk,
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "sdk track result failed"),
            0x02: (DLL_ERROR, "API with wrong parameters")
        }, "SDK_Track_Result")
    return info_buf

def sdk_track_list(dll: Dll, item: bytes ,time_stamp_start: int, time_stamp_end: int) -> tuple[int, bytearray]:
    """Search drive log and return list that during time stamp. This API must be used immediately, because drive log have amount limit.
    Args:
        dll: Dll instance
        item: item select
        time_stamp_start: Start time stamp during drive log
        time_stamp_end: End time stamp during drive log
        count: Return list count
        info_buf: Return list info

    Return:
       Tuple contains count and info_buf
    """
    info_buf = bytearray(const.DATA_SIZE_256K_BYTE)
    count = 0

    count_ptr = ctypes.pointer(ctypes.c_uint(count))
    dll.cdll.SDK_Track_List.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.SDK_Track_List.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.SDK_Track_List(
        dll.sdk,
        ctypes.c_ubyte(item),
        ctypes.c_uint(time_stamp_start),
        ctypes.c_uint(time_stamp_end),
        count_ptr,
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "sdk track list failed"),
            0x02: (DLL_ERROR, "API with wrong parameters")
        }, "SDK_Track_List")
    
    return (count, info_buf)

def sdk_track_parsing(dll: Dll, info_buf: bytearray):
    """Parse SDK Track Result, no ref doc

    """
    info_buf = bytearray(262144)

    dll.errcode = dll.cdll.SDK_Track_Result(
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "sdk track result failed"),
            0x02: (DLL_ERROR, "API with wrong parameters")
        }, "sdk_track_result")
    return info_buf

def print_log_sdk(dll: Dll, log_str: str, print_on_console_en: int, log_type: int):
    """Print Log SDK

    """
    dll.cdll.PrintLogSDK(
        ctypes.c_char_p(log_str.encode('utf-8')),
        ctypes.c_ubyte(print_on_console_en),
        ctypes.c_ubyte(log_type)
    )
    
def print_buffer_sdk(dll: Dll, data_buf: bytearray, length: int, col_length: int, print_on_console_en: int, log_type: int):
    """Print Buffer SDK

    """
    dll.errcode = dll.cdll.PrintBufferSDK(
        (ctypes.c_ubyte * len(data_buf)).from_buffer(data_buf),
        ctypes.c_uint(length),
        ctypes.c_ubyte(col_length),
        ctypes.c_ubyte(print_on_console_en),
        ctypes.c_ubyte(log_type)
    )

def log_fa_setting(dll: Dll, log_setting: int, str_folder_name: str, str_file_name: str, log_line: int):
    """Log FA Setting SDK

    """
    dll.cdll.Log_FASetting(
        ctypes.c_ubyte(log_setting),
        ctypes.c_char_p(str_folder_name.encode('utf-8')),
        ctypes.c_char_p(str_file_name.encode('utf-8')),
        ctypes.c_uint(log_line),
    )
    
def log_fa_dump(dll: Dll):
    """Log FA Dump SDK  

    """
    dll.cdll.Log_FADump()

def log_setting(dll: Dll, log_setting: int, str_folder_name: str, str_file_name: str):
    """Log Setting SDK

    """
    dll.cdll.LogSetting(
        ctypes.c_ubyte(log_setting),
        ctypes.c_char_p(str_folder_name.encode('utf-8')),
        ctypes.c_char_p(str_file_name.encode('utf-8')),
    )