import ctypes
from ._base import Dll, handle_error_code
from .exception import *

def scmd_unipro_error_inject(dll: Dll, arg_buf: bytearray):
    """SCMD Unipro Error Inject, scmd index 0, ref DCMD4, 

    """
    dll.errcode = dll.cdll.SCMD_Unipro_Error_Inject(
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "scmd unipro error inject failed")
        }, "scmd_unipro_error_inject")
    
def scmd_gpio_trigger(dll: Dll, arg_buf: bytearray):
    """SCMD GPIO Trigger, scmd index 1, ref DCMD16

    """
    dll.errcode = dll.cdll.SCMD_GPIO_Trigger(
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "scmd gpio trigger failed")
        }, "scmd_gpio_trigger")
    
def scmd_dme_error_count(dll: Dll, arg_buf: bytearray):
    """SCMD DME Error Count, scmd index 2, ref DCMD17

    """
    dll.errcode = dll.cdll.SCMD_DME_Error_Count(
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "scmd dme error count failed")
        }, "scmd_dme_error_count")

def scmd_spor(dll: Dll, arg_buf: bytearray):
    """SCMD SPOR, , scmd index 3, ref DCMD7

    """
    dll.errcode = dll.cdll.SCMD_SPOR(
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "scmd spor failed")
        }, "scmd_spor")

def scmd_uart(dll: Dll, arg_buf: bytearray):
    """SCMD UART

    """
    dll.errcode = dll.cdll.SCMD_UART(
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "scmd uart failed")
        }, "scmd_uart")

def scmd_get_info(dll: Dll, scmd_idx: bytes) -> bytearray:
    """SCMD Get Info

    """
    info_buf = bytearray(512)
    dll.errcode = dll.cdll.SCMD_UART(
        ctypes.c_ubyte(scmd_idx)
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "scmd get info failed")
        }, "scmd_get_info")