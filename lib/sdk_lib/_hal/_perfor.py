import ctypes
from ._base import Dll, const, handle_error_code
from .exception import *

def performance(dll: Dll, arg_buf: bytearray, addr_buf: bytearray) -> tuple[bytearray, bytearray]:
    """Execute performance test
    
    Args:
        dll: Dll instance
        arg_buf: Argument buffer
        addr_buf: Address buffer
        
    Returns:
        Tuple containing (result_buffer, info_buffer)
    """
    result_buf = bytearray(512 * [0xff])
    info_buf = bytearray(const.DATA_SIZE_64M_BYTE)

    dll.cdll.Performance.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), 
                                     ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte),
                                     ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Performance.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Performance(
        dll.sdk,
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf),
        (ctypes.c_ubyte * len(addr_buf)).from_buffer(addr_buf),
        (ctypes.c_ubyte * len(result_buf)).from_buffer(result_buf),
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Performance failed")
        }, "performance", result_buf)
    return (result_buf, info_buf)

# do not use, sdk dll not support
def performance_with_data_length(dll: Dll, arg_buf: bytearray, addr_buf: bytearray, 
                               data_length: int, rpmb_test: int) -> bytearray:
    """Execute performance test with data length
    
    Args:
        dll: Dll instance
        arg_buf: Argument buffer
        addr_buf: Address buffer
        data_length: Data length
        rpmb_test: RPMB test flag
        
    Returns:
        Result buffer
    """
    result_buf = bytearray(data_length * [0xff])  # Buffer size based on data_length
    dll.cdll.Performance.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), 
                                     ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte),
                                     ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32,
                                     ctypes.c_uint32]
    dll.cdll.Performance.restype = ctypes.c_ubyte

    dll.errcode = dll.cdll.Performance(
        dll.sdk,
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf),
        (ctypes.c_ubyte * len(addr_buf)).from_buffer(addr_buf),
        (ctypes.c_ubyte * len(result_buf)).from_buffer(result_buf),
        ctypes.c_uint32(data_length),
        ctypes.c_ubyte(rpmb_test)
    )
    if dll.errcode != 0:
        raise DLL_ERROR("Performance test with data length failed")
    return result_buf

def generic_ehs_performance(dll: Dll, arg_buf: bytearray, addr_buf: bytearray) -> tuple[bytearray, bytearray, bytearray]:
    """Execute generic EHS performance test
    
    Args:
        dll: Dll instance
        arg_buf: Argument buffer
        addr_buf: Address buffer
        
    Returns:
        Tuple containing (result_buffer, info_buffer, ehs_info_buffer)
    """
    result_buf = bytearray(512*[0xff])
    info_buf = bytearray(const.DATA_SIZE_64M_BYTE)
    ehs_info_buf = bytearray(const.DATA_SIZE_64M_BYTE)
    
    dll.cdll.GenericEHS_Performance.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), 
                                     ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte),
                                     ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.GenericEHS_Performance.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.GenericEHS_Performance(
        dll.sdk,
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf),
        (ctypes.c_ubyte * len(addr_buf)).from_buffer(addr_buf),
        (ctypes.c_ubyte * len(result_buf)).from_buffer(result_buf),
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf),
        (ctypes.c_ubyte * len(ehs_info_buf)).from_buffer(ehs_info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Generic EHS performance test failed")
        }, "generic_ehs_performance", result_buf)
        
    return (result_buf, info_buf, ehs_info_buf)

def en_performance(dll: Dll, arg_buf: bytearray, addr_buf: bytearray) -> tuple[bytearray, bytearray]:
    """Execute EN performance test
    
    Args:
        dll: Dll instance
        arg_buf: Argument buffer
        addr_buf: Address buffer
        
    Returns:
        Tuple containing (result_buffer, info_buffer)
    """
    result_buf = bytearray(512*[0xff])
    info_buf = bytearray(const.DATA_SIZE_64M_BYTE)

    dll.cdll.EN_Performance.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), 
                                     ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte),
                                     ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.EN_Performance.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.EN_Performance(
        dll.sdk,
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf),
        (ctypes.c_ubyte * len(addr_buf)).from_buffer(addr_buf),
        (ctypes.c_ubyte * len(result_buf)).from_buffer(result_buf),
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "EN performance failed")
        }, "en_performance", result_buf)
    return (result_buf, info_buf)

def hpb_read_performance(dll: Dll, arg_buf: bytearray, addr_buf: bytearray) -> tuple[bytearray, bytearray]:
    """Execute HPB read performance test
    
    Args:
        dll: Dll instance
        arg_buf: Argument buffer
        addr_buf: Address buffer
        
    Returns:
        Tuple containing (result_buffer, info_buffer)
    """
    result_buf = bytearray(512*[0xff])
    info_buf = bytearray(const.DATA_SIZE_64M_BYTE)

    dll.cdll.HPB_ReadPerformance.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), 
                                     ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte),
                                     ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.HPB_ReadPerformance.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.HPB_ReadPerformance(
        dll.sdk,
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf),
        (ctypes.c_ubyte * len(addr_buf)).from_buffer(addr_buf),
        (ctypes.c_ubyte * len(result_buf)).from_buffer(result_buf),
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "EN read performance failed")
        }, "hpb_read_performance", result_buf)
    return (result_buf, info_buf)

def hpb_en_performance(dll: Dll, arg_buf: bytearray, addr_buf: bytearray) -> tuple[bytearray, bytearray]:
    """Execute HPB EN performance test
    
    Args:
        dll: Dll instance
        arg_buf: Argument buffer
        addr_buf: Address buffer
        
    Returns:
        Tuple containing (result_buffer, info_buffer)
    """
    result_buf = bytearray(512*[0xff])
    info_buf = bytearray(const.DATA_SIZE_64M_BYTE)

    dll.cdll.HPB_EN_Performance.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), 
                                            ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte),
                                            ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.HPB_EN_Performance.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.HPB_EN_Performance(
        dll.sdk,
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf),
        (ctypes.c_ubyte * len(addr_buf)).from_buffer(addr_buf),
        (ctypes.c_ubyte * len(result_buf)).from_buffer(result_buf),
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "HPB EN performance failed")
        }, "hpb_en_performance", result_buf)
    return (result_buf, info_buf)

def rpmb_performance(dll: Dll, arg_buf: bytearray, addr_buf: bytearray) -> tuple[bytearray, bytearray]:
    """Execute RPMB performance test
    
    Args:
        dll: Dll instance
        arg_buf: Argument buffer
        addr_buf: Address buffer
        
    Returns:
        Tuple containing (result_buffer, info_buffer)
    """
    result_buf = bytearray(512*[0xff])
    info_buf = bytearray(const.DATA_SIZE_64M_BYTE)

    dll.cdll.RPMB_Performance.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), 
                                          ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte),
                                          ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.RPMB_Performance.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.RPMB_Performance(
        dll.sdk,
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf),
        (ctypes.c_ubyte * len(addr_buf)).from_buffer(addr_buf),
        (ctypes.c_ubyte * len(result_buf)).from_buffer(result_buf),
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "RPMB performance test failed")
        }, "rpmb_performance", result_buf)
    return (result_buf, info_buf) 

def adv_rpmb_performance(dll: Dll, arg_buf: bytearray, addr_buf: bytearray) -> tuple[bytearray, bytearray]:
    """Execute advanced RPMB performance test
    
    Args:
        dll: Dll instance
        arg_buf: Argument buffer
        addr_buf: Address buffer
        
    Returns:
        Tuple containing (result_buffer, info_buffer)
    """
    result_buf = bytearray(512*[0xff])
    info_buf = bytearray(const.DATA_SIZE_64M_BYTE)

    dll.cdll.Adv_RPMB_Performance.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), 
                                              ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte),
                                              ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Adv_RPMB_Performance.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Adv_RPMB_Performance(
        dll.sdk,
        (ctypes.c_ubyte * len(arg_buf)).from_buffer(arg_buf),
        (ctypes.c_ubyte * len(addr_buf)).from_buffer(addr_buf),
        (ctypes.c_ubyte * len(result_buf)).from_buffer(result_buf),
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "RPMB performance test failed")
        }, "adv_rpmb_performance", result_buf)
    return (result_buf, info_buf) 