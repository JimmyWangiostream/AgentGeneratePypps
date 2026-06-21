import ctypes
from ._base import Dll, handle_error_code
from .exception import *

def dme_set(dll: Dll, attr_set_type: int, mib_val: int, sel: int, mib_attr: int) -> int:
    """Set Host/Device DME attribute value
    
    Args:
        dll: Dll instance
        attr_set_type: Attribute set type
        mib_val: MIB value
        sel: Selector
        mib_attr: MIB attribute
        
    Returns:
        Result value
    """
    apb_result = ctypes.c_uint32()

    dll.cdll.DME_Set.argtypes = [ctypes.c_void_p, ctypes.c_uint32, 
                                 ctypes.c_uint32, ctypes.c_uint32,
                                 ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
    dll.cdll.DME_Set.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.DME_Set(
        dll.sdk,
        ctypes.c_uint32(attr_set_type),
        ctypes.c_uint32(mib_val),
        ctypes.c_uint32(sel),
        ctypes.c_uint32(mib_attr),
        ctypes.byref(apb_result)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "DME set failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "dme_set")
    return apb_result.value

def dme_get(dll: Dll, attr_set_type: int, sel: int, mib_attr: int) -> tuple[int, int]:
    """Get Host/Device DME attribute value
    
    Args:
        dll: Dll instance
        attr_set_type: Attribute set type
        sel: Selector
        mib_attr: MIB attribute
        
    Returns:
        Tuple containing (result, value)
    """
    apl_result = ctypes.c_uint32()
    apl_val = ctypes.c_uint32()
    
    dll.cdll.DME_Get.argtypes = [ctypes.c_void_p, ctypes.c_uint32, 
                                 ctypes.c_uint32, ctypes.c_uint32,
                                 ctypes.POINTER(ctypes.c_uint32), 
                                 ctypes.POINTER(ctypes.c_uint32)]
    dll.cdll.DME_Get.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.DME_Get(
        dll.sdk,
        ctypes.c_uint32(attr_set_type),
        ctypes.c_uint32(sel),
        ctypes.c_uint32(mib_attr),
        ctypes.byref(apl_result),
        ctypes.byref(apl_val)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "DME get failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "dme_get")
    return (apl_result.value, apl_val.value)

def dme_req(dll: Dll, option: int, lane_cnt: int = 0):
    """DME request
    
    Args:
        dll: Dll instance
        option: Request option
        lane_cnt: Lane count, default is 0
        
    Returns:
        Operation status code
    """

    dll.cdll.DME_Req.argtypes = [ctypes.c_void_p, ctypes.c_uint32, 
                                 ctypes.c_ubyte]
    dll.cdll.DME_Req.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.DME_Req(
        dll.sdk,
        ctypes.c_uint32(option),
        ctypes.c_ubyte(lane_cnt)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, None, "dme_req")

def dme_reg_set(dll: Dll, offset: int, value: int):
    """Set Host DME register value
    
    Args:
        dll: Dll instance
        offset: Register offset
        value: Register value
        
    Returns:
        Operation status code
    """
    dll.cdll.DME_Req.argtypes = [ctypes.c_void_p, ctypes.c_uint32, 
                                 ctypes.c_ubyte]
    dll.cdll.DME_Req.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.DME_REG_Set(
        dll.sdk,
        ctypes.c_uint32(offset),
        ctypes.c_ubyte(value)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "DME reg set failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "dme_reg_set")

def dme_reg_get(dll: Dll, offset: int) -> int:
    """Get Host DME register value

    Args:
        dll: Dll instance
        offset: Register offset
        
    Returns:
        Register value
    """
    result = ctypes.c_ubyte()
    
    dll.cdll.DME_REG_Get.argtypes = [ctypes.c_void_p, ctypes.c_uint32, 
                                     ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.DME_REG_Get.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.DME_REG_Get(
        dll.sdk,
        ctypes.c_uint32(offset),
        ctypes.byref(result)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "DME reg get failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "dme_reg_get")
    return result.value

def read_dme_reg(dll: Dll, sel: int) -> bytearray:
    """Read data from DME Reg. and MPHY Reg.
    
    Args:
        dll: Dll instance
        sel: Selector
        length: Data length to read
        
    Returns:
        Bytearray containing read data
    """
    length_param = ctypes.c_ushort()
    read_data = bytearray(2048)

    dll.cdll.Read_DME_Reg.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, 
                                     ctypes.POINTER(ctypes.c_ushort),
                                     ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Read_DME_Reg.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Read_DME_Reg(
        dll.sdk,
        ctypes.c_ubyte(sel),
        ctypes.byref(length_param),
        (ctypes.c_ubyte * len(read_data)).from_buffer(read_data)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Read dme register failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "read_dme_reg")
    return read_data[:length_param.value]  # Return only the valid data