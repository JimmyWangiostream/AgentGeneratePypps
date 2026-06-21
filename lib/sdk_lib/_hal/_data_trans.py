import ctypes
from ._base import Dll, handle_error_code
from .exception import *

class CCmdHeader(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("b0_Tran_Type", ctypes.c_ubyte),     # BYTE 0
        ("b1_Flag", ctypes.c_ubyte),          # BYTE 1
        ("b2_Lun", ctypes.c_ubyte),           # BYTE 2
        ("b3_Task_Tag", ctypes.c_ubyte),      # BYTE 3
        ("b4_IID_CMD_Type", ctypes.c_ubyte),  # BYTE 4
        ("b5_Que_Tsk", ctypes.c_ubyte),       # BYTE 5
        ("b6_Res", ctypes.c_ubyte),           # BYTE 6
        ("b7_Sts", ctypes.c_ubyte),           # BYTE 7
        ("b8_EHS_Len", ctypes.c_ubyte),       # BYTE 8
        ("b9_Dev_Info", ctypes.c_ubyte),      # BYTE 9
        ("w10_Dat_Seg_Len", ctypes.c_ushort)  # BYTE 10~11
    ]

class CCmdTran(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("l12_SF0", ctypes.c_uint32),  # BYTE 12~15
        ("l16_SF1", ctypes.c_uint32),  # BYTE 16~19
        ("l20_SF2", ctypes.c_uint32),  # BYTE 20~23
        ("l24_SF3", ctypes.c_uint32),  # BYTE 24~27
        ("l28_SF4", ctypes.c_uint32)   # BYTE 28~31
    ]

def send_cmd(dll: Dll, header, trans, payload, payload_len, timeout, action, 
             ptn_mode, ptn_tag, seed_h, seed_l, by4k_gen):
    """Send General UPIU
    
    Args:
        dll: Dll instance
        header: Header buffer in 12 Bytes
        tran: Transaction specific fields buffer in 32 Bytes
        payload: Payload Buffer(使用Advanced RPMB (V6 Only),將EHS欄位填入此處)
        payload_len: Payload length(使用Advanced RPMB (V6 Only),將EHS欄位填入此處)
        timeout: Command timeout
        action: Action code
        pattern_mode: Pattern mode
        pattern_tag: Pattern tag
        seed_h: High seed value, default is 0, (Only for ps2808)
        seed_l: Low seed value, default is 0, (Only for ps2808)
        by4k_gen: (Only for ps2808)
        mode_select_check: Mode select check, default is 1
        
    Returns:
        Operation status code
    """
    dll.cdll.Send_Cmd.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_uint32, ctypes.c_uint32,
                                  ctypes.c_uint32, ctypes.c_uint32,
                                  ctypes.c_uint32, ctypes.c_uint32,
                                  ctypes.c_uint32, ctypes.c_ubyte]
    dll.cdll.Send_Cmd.restype = ctypes.c_ubyte

    dll.errcode = dll.cdll.Send_Cmd(
        dll.sdk,
        ctypes.byref(header),
        ctypes.byref(trans),
        (ctypes.c_ubyte * len(payload)).from_buffer(payload),
        ctypes.c_uint32(payload_len),
        ctypes.c_uint32(timeout),
        ctypes.c_uint32(action),
        ctypes.c_uint32(ptn_mode),
        ctypes.c_uint32(ptn_tag),
        ctypes.c_uint32(seed_h),
        ctypes.c_uint32(seed_l),
        ctypes.c_ubyte(by4k_gen)
    )

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Send command failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "send_cmd")

def data_payload_xfer(dll: Dll, action: int, data_buf: bytearray, data_len: int) -> int:
    """Data payload transfer
    
    Args:
        dll: Dll instance
        action: Action code
        data_buf: Data buffer
        data_len: Data length
        
    Returns:
        Operation status code
    """
    dll.cdll.DataPayloadXfer.argtypes = [ctypes.c_void_p, ctypes.c_uint32, 
                                        ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
    dll.cdll.DataPayloadXfer.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.DataPayloadXfer(
        dll.sdk,
        ctypes.c_uint32(action),
        (ctypes.c_ubyte * len(data_buf)).from_buffer(data_buf),
        ctypes.c_uint32(data_len)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "data payload xfer failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "data_payload_xfer")

def data_in_out_xfer(dll: Dll, lun, task_tag, data_seq_lun, buf_offset, 
                     data_cnt, seg_cnt, rw, databuf, iid):
    """Data Transfer/Receive

    """
    dll.cdll.DataInOutXfer.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                       ctypes.c_uint32, ctypes.c_uint32,
                                       ctypes.c_uint32, ctypes.c_uint32,
                                       ctypes.c_uint32, ctypes.c_uint32,
                                       ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
    dll.cdll.DataInOutXfer.restype = ctypes.c_ubyte

    dll.errcode = dll.cdll.DataInOutXfer(
        dll.sdk,
        ctypes.c_uint32(lun),
        ctypes.c_uint32(task_tag),
        ctypes.c_uint32(data_seq_lun),
        ctypes.c_uint32(buf_offset),
        ctypes.c_uint32(data_cnt),
        ctypes.c_uint32(seg_cnt),
        ctypes.c_uint32(rw)
        (ctypes.c_ubyte * len(databuf)).from_buffer(databuf),
        ctypes.c_uint32(iid)
    )

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "data_in_out_xfer")

def get_dev_resp(dll: Dll) -> bytearray:
    """Get response from device
    """
    resp_buf = bytearray(512)

    dll.cdll.Get_DevResp.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Get_DevResp.restype = ctypes.c_ubyte

    dll.errcode = dll.cdll.Get_DevResp(
        dll.sdk,
        (ctypes.c_ubyte * len(resp_buf)).from_buffer(resp_buf))
    
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "failed"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "get_dev_resp")

    return resp_buf