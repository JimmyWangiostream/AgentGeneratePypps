import ctypes
from ._base import Dll, handle_error_code, const
from .exception import *

def send_cmd_seq(dll: Dll, cmd_buf, qd, opt, cmd_blk_cnt, data_blk_cnt, timeout, ext_opt, fix_ptn):
    """Send Command Sequence
    
    Args:
        dll: Dll instance
        cmd: Dictionary containing command sequence parameters

    Returns:
        Operation status code
    """
    dll.cdll.Send_CMD_SEQ.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte),
                                      ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_uint32,
                                      ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
                                      ctypes.c_longlong]
    dll.cdll.Send_CMD_SEQ.restype = ctypes.c_ubyte

    dll.errcode = dll.cdll.Send_CMD_SEQ(
        dll.sdk,
        (ctypes.c_ubyte * len(cmd_buf)).from_buffer(cmd_buf),
        ctypes.c_ubyte(qd),
        ctypes.c_ubyte(opt),
        ctypes.c_uint32(cmd_blk_cnt),
        ctypes.c_uint32(data_blk_cnt),
        ctypes.c_uint32(timeout),
        ctypes.c_uint32(ext_opt),
        ctypes.c_longlong(fix_ptn)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Send command seq failed"),
        }, "send_cmd_seq")

def cmd_seq_send_ehs(dll: Dll, data_buf: bytearray, data_block_cnt: int):
    """Send Command Sequence EHS data
    
    Args:
        dll: Dll instance
        data_buf: Buffer for EHS data, Max : 512KB
        data_block_cnt: 512 Byte block count of command
    """
    dll.cdll.Send_CMD_SEQ_EHS.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
    dll.cdll.Send_CMD_SEQ_EHS.restype = ctypes.c_ubyte

    dll.errcode = dll.cdll.Send_CMD_SEQ_EHS(
        dll.sdk,
        (ctypes.c_ubyte * len(data_buf)).from_buffer(data_buf),
        ctypes.c_uint32(data_block_cnt)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Send EHS data failed"),
        }, "cmd_seq_send_ehs")

def cmd_seq_get_ehs(dll: Dll, data_block_cnt: int) -> bytearray:
    """Get command sequence EHS
    
    Args:
        dll: Dll instance
        data_block_cnt: Data block count
        
    Returns:
        Bytearray containing EHS data
    """
    dll.cdll.CMD_SEQ_GetEHS.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
    dll.cdll.CMD_SEQ_GetEHS.restype = ctypes.c_ubyte

    ehs_buf = bytearray(data_block_cnt * const.DATA_SIZE_512K_BYTE)
    dll.errcode = dll.cdll.CMD_SEQ_GetEHS(
        dll.sdk,
        (ctypes.c_ubyte * len(ehs_buf)).from_buffer(ehs_buf),
        ctypes.c_uint32(data_block_cnt)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Get command sequence EHS failed"),
        }, "cmd_seq_get_ehs")
    return ehs_buf

def cmd_seq_monitor(dll: Dll, block_cnt: int, data_block_cnt: int, polling_time: int = 0) -> tuple[bytearray, bytearray]:
    EXE_SDRAM_64M = 0x04000000
    """Monitor command sequence
    
    Args:
        dll: Dll instance
        block_cnt: Block count
        data_block_cnt: Data block count
        
    Returns:
        Tuple containing (result_buffer, info_buffer)
    """
    dll.cdll.CMD_SEQ_Monitor.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte),
                                         ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32,
                                         ctypes.c_uint32, ctypes.c_uint]
    dll.cdll.CMD_SEQ_Monitor.restype = ctypes.c_ubyte

    pby_info_buf = bytearray(EXE_SDRAM_64M)
    result_buf = bytearray(512)
    dll.errcode = dll.cdll.CMD_SEQ_Monitor(
        dll.sdk,
        (ctypes.c_ubyte * len(result_buf)).from_buffer(result_buf),
        (ctypes.c_ubyte * len(pby_info_buf)).from_buffer(pby_info_buf),
        ctypes.c_uint32(block_cnt),
        ctypes.c_uint32(data_block_cnt),
        ctypes.c_uint(polling_time)
    )

    if dll.errcode != 0x00:
        err_data = error_data()
        err_data.result_buf = result_buf
        err_data.info_buf = pby_info_buf
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "CMD SEQ Monitor failed"),
        }, "cmd_seq_monitor", err_data)
    return result_buf, pby_info_buf