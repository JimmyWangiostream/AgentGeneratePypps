import ctypes
from ._base import Dll, handle_error_code, const
from .exception import *

def hpb_activate(dll: Dll, arg_buf: bytearray):
    """Activate HPB (Host Performance Booster)
    
    Args:
        dll: Dll instance
        arg_buf: Argument buffer
    """
    dll.cdll.HPB_Activate.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.HPB_Activate.restype = ctypes.c_ubyte

    dll.errcode = dll.cdll.HPB_Activate(
        dll.sdk,
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "HPB activation failed"),
            0x02: (DLL_ERROR, "API with wrong parameters")
        }, "hpb_activate")

def hpb_auto_setting(dll: Dll, arg_buf: bytearray):
    """Configure HPB auto settings
    
    Args:
        dll: Dll instance
        arg_buf: Argument buffer
    """
    dll.cdll.HPB_AutoSetting.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.HPB_AutoSetting.restype = ctypes.c_ubyte

    dll.errcode = dll.cdll.HPB_AutoSetting(
        dll.sdk,
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "HPB auto settings failed, Not active HPB function (HPB result status shall get 0x01)"),
            0x02: (DLL_ERROR, "API with wrong parameters")
        }, "hpb_auto_setting")

def hpb_reset(dll: Dll):
    """Reset HPB
    
    Args:
        dll: Dll instance
    """
    dll.cdll.HPB_Reset.argtypes = ctypes.c_void_p
    dll.cdll.HPB_Reset.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.HPB_Reset(dll.sdk)
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Reset HPB failed"),
            0x02: (DLL_ERROR, "API with wrong parameters")
        }, "hpb_reset")

def hpb_get_entry(dll: Dll, arg_buf: bytearray) -> bytearray:
    """Get HPB entry
    
    Args:
        dll: Dll instance
        arg_buf: Argument buffer
    
    Returns:
        Return PBA value
    """
    entry_buf = bytearray(8)
    
    dll.cdll.HPB_GetEntry.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), 
                                      ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.HPB_GetEntry.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.HPB_GetEntry(
        dll.sdk,
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf),
        (ctypes.c_ubyte * len(entry_buf)).from_buffer(entry_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Get HPB entry failed, Not active HPB function (HPB result status shall get 0x01)"),
            0x02: (DLL_ERROR, "API with wrong parameters"),
            0x12: (DLL_ERROR, "LBA can't mapping active region (HPB result status shall get 0x12)")
        }, "hpb_get_entry")

    return entry_buf

def hpb_dump_table(dll: Dll, arg_buf: bytearray) -> bytearray:
    """Dump HPB table
    
    Args:
        dll: Dll instance
        arg_buf: Argument buffer
        
    Returns:
        Table data buffer
    """
    table_buf = bytearray(const.DATA_SIZE_32M_BYTE) # hpb table max is 32mb
    
    dll.cdll.HPB_Dump_Table.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), 
                                        ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.HPB_Dump_Table.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.HPB_Dump_Table(
        dll.sdk,
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf),
        (ctypes.c_ubyte * len(table_buf)).from_buffer(table_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Get HPB entry failed, Not active HPB function (HPB result status shall get 0x01)"),
            0x02: (DLL_ERROR, "API with wrong parameters"),
            0x03: (DLL_ERROR, "Input region is Inactive .You can get region mapping table by HPB_Result , and get active region number.")
        }, "hpb_dump_table")
    return table_buf

def hpb_result(dll: Dll) -> tuple[bytearray, bytearray]:
    """When HPB API execution fail, get debug message through this API

    Args:
        dll: Dll instance
        
    Returns:
        Tuple containing (info_buffer, table_info_buffer)
    """
    info_buf = bytearray(2048)
    table_info_buf = bytearray(const.DATA_SIZE_1M_BYTE)

    dll.cdll.HPB_Result.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), 
                                    ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.HPB_Result.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.HPB_Result(
        dll.sdk,
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf),
        (ctypes.c_ubyte * len(table_info_buf)).from_buffer(table_info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, None, "hpb_result")
    return (info_buf, table_info_buf)

def hpb_dump_bitmap(dll: Dll, arg: bytearray, bitmap_buf: bytearray):
    # No ref Doc
    dll.cdll.HPB_Dump_BitMap.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), 
                                         ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.HPB_Dump_BitMap.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.HPB_Dump_BitMap(
        dll.sdk,
        (ctypes.c_ubyte * len(arg)).from_buffer(arg),
        (ctypes.c_ubyte * len(bitmap_buf)).from_buffer(bitmap_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, None, "hpb_dump_bitmap")
