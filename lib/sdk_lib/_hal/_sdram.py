import ctypes
from ._base import Dll, const, handle_error_code
from .exception import *


def get_sdram_data(dll: Dll, block_cnt: int) -> bytearray:
    """Get SDRAM data

    Args:
        dll: Dll instance
        block_cnt: Number of blocks
    
    Return:
        Bytearray containing SDRAM data
    """
    data_buf = bytearray(const.DATA_SIZE_64M_BYTE)
    
    dll.cdll.Get_SDRAM_Data.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint]
    dll.cdll.Get_SDRAM_Data.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Get_SDRAM_Data(
        dll.sdk,
        (ctypes.c_ubyte * len(data_buf)).from_buffer(data_buf),
        ctypes.c_uint(block_cnt)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Get SDRAM Data failed."),
        }, "Get_SDRAM_Data")

    return data_buf
    