import ctypes
from ._base import Dll, handle_error_code
from .exception import *

class CGRW_Err(ctypes.Structure):
    _fields_ = [
        ("byBG_Error", ctypes.c_byte),
        ("byBG_SubError", ctypes.c_byte),
        ("byBG_SK", ctypes.c_byte),
        ("byBG_ASC", ctypes.c_byte)
    ]

class CRW_Info(ctypes.Structure):
    _fields_ = [
        ("byAction", ctypes.c_byte),
        ("bySCSICmd", ctypes.c_byte),
        ("byLun", ctypes.c_byte),
        ("LBA_H", ctypes.c_ulong),
        ("LBA_L", ctypes.c_ulong),
        ("byFUA", ctypes.c_byte),
        ("byDPO", ctypes.c_byte),
        ("byGroupNo", ctypes.c_byte),
        ("dwDataLen", ctypes.c_ulong),
        ("dwDataPattern", ctypes.c_ulong),
        ("dwDataBuf", ctypes.c_ulong),
        ("byModeType", ctypes.c_byte),
        ("byPatternMode", ctypes.c_byte),
        ("byAddTag", ctypes.c_byte),
        ("byLBA_MarkCRC_En", ctypes.c_byte),
        ("bySameTaskTag_En", ctypes.c_byte),
        ("dwLoopTag", ctypes.c_ulong),
        ("dwTimeOut", ctypes.c_ulong),
        ("dwMaxBusyTime", ctypes.c_ulong),
        ("dwTotalBusyTime", ctypes.c_ulong),
        ("dwExpectDataLen", ctypes.c_ulong),
        ("dwAssignLB", ctypes.c_ulong),
        ("byTaskAtt", ctypes.c_byte),
        ("byCP", ctypes.c_byte),
        ("byTaskTag", ctypes.c_byte),
        ("byWKLun", ctypes.c_byte),
        ("byCmdOrder", ctypes.c_byte),
        ("byLBAMark_CheckSum", ctypes.c_byte),
        ("dwDataCRC", ctypes.c_ulong),
        ("u64CheckSum", ctypes.c_ulonglong),
        ("byRDPROTECT", ctypes.c_byte),
        ("stBG_ErrCode", CGRW_Err),
        ("dwIsINTHit", ctypes.c_ulong),
        ("dwStartLBA_Ptn", ctypes.c_ulong),
        ("dwRWType", ctypes.c_ulong),
        ("bCmpCurData", ctypes.c_byte)
    ]

    def __eq__(self, other):
        if isinstance(other, int):
            return self.byTaskTag == other
        elif isinstance(other, CGRW_Err):
            return self.stBG_ErrCode.byBG_Error != other.byBG_Error
        else:
            return False

def monitor(dll: Dll, option: int, block_count: int) -> bytearray:
    """Monitor UFS operations
    
    Args:
        dll: Dll instance
        option: Monitor option
        block_count: Block count, default is 0
        
    Returns:
        Buffer containing monitor data
    """
    buffer = bytearray(512)

    dll.cdll.Monitor.argtypes = [ctypes.c_void_p, ctypes.c_uint32, 
                                 ctypes.POINTER(ctypes.c_ushort), ctypes.c_uint32]
    dll.cdll.Monitor.restype = ctypes.c_ubyte

    dll.errcode = dll.cdll.Monitor(
        dll.sdk,
        ctypes.c_uint32(option),
        (ctypes.c_ubyte * len(buffer)).from_buffer(buffer),
        ctypes.c_uint32(block_count)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "monitor failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "monitor")
    return buffer

def monitor_w_rw_info(dll: Dll, rw_info: list[CRW_Info], option: int, block_count: int = 0) -> bytearray:
    """Monitor UFS operations with rw_info
    
    Args:
        dll: Dll instance
        option: Monitor option
        rw_info_vector: List of dictionaries containing RWInfo data
        block_count: Number of blocks
        
    Returns:
        Buffer containing monitor data
    """
    buffer = bytearray(512)

    dll.errcode = dll.cdll.Monitor(
        rw_info,
        (ctypes.c_ubyte * len(buffer)).from_buffer(buffer),
        ctypes.c_ubyte(option),
        ctypes.c_ubyte(block_count)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "monitor failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "monitor_w_rw_info")
    return buffer

def group_read_write(dll: Dll, gp_rw_buf: bytearray):
    """Group a packed write or read command

    """
    dll.cdll.Group_Read_Write.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Group_Read_Write.restype = ctypes.c_ubyte

    dll.errcode = dll.cdll.Group_Read_Write(
        dll.sdk,
        (ctypes.c_ubyte * len(gp_rw_buf)).from_buffer(gp_rw_buf)
    )

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Group read write failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "group_read_write")