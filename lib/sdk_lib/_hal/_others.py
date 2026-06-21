import ctypes
from ._base import Dll, handle_error_code
from .exception import *

class MPHY_EYE_MONITOR_PARAM(ctypes.Structure):
    _fields_ = [
        ("u8Action", ctypes.c_uint32, 8),
        ("isPeer", ctypes.c_uint32, 1),
        ("isHS", ctypes.c_uint32, 1),
        ("isRateB", ctypes.c_uint32, 1),
        ("isLANE1", ctypes.c_uint32, 1),
        ("isScramble", ctypes.c_uint32, 1),
        ("u3Gear", ctypes.c_uint32, 3),
        ("u2BeforeAdapt", ctypes.c_uint32, 2),
        ("u2TestAdapt", ctypes.c_uint32, 2),
        ("u7TargetTestCnt", ctypes.c_uint32, 7)
    ]

class MPHY_EYE_MONITOR_ELEMENT(ctypes.Structure):
    _fields_ = [
        ("s32Timing", ctypes.c_int32),
        ("s32Voltage", ctypes.c_int32),
        ("u32ErrCnt", ctypes.c_uint32),
        ("u32TestCnt", ctypes.c_uint32)
    ]

class _MphyEyeMonitorData(ctypes.Structure):
    _fields_ = [
        ("u8Err", ctypes.c_uint8),  # [0]
        ("u8SubErr", ctypes.c_uint8),  # [1]
        ("u8FailStep", ctypes.c_uint8),  # [2]
        ("u8Rsvd1", ctypes.c_uint8),  # [3]
        ("u32L0_RO_CURR_SSLMS_C0_C1_BK1", ctypes.c_uint32),  # [4:7]
        ("u32L0_RO_CURR_SSLMS_C2_C3_BK1", ctypes.c_uint32),  # [8:11]
        ("u32L0_RO_CURR_SSLMS_C4_C5_BK1", ctypes.c_uint32),  # [12:15]
        ("u32L0_RO_CURR_SUM_C1_C2_BK1", ctypes.c_uint32),  # [16:19]
        ("u32L0_RO_CURR_SUM_C3_C4_BK1", ctypes.c_uint32),  # [20:23]
        ("u32L0_RO_CURR_SUM_C5_TOT_BK1", ctypes.c_uint32),  # [24:27]
        ("u32L1_RO_CURR_SSLMS_C0_C1_BK1", ctypes.c_uint32),  # [28:31]
        ("u32L1_RO_CURR_SSLMS_C2_C3_BK1", ctypes.c_uint32),  # [32:35]
        ("u32L1_RO_CURR_SSLMS_C4_C5_BK1", ctypes.c_uint32),  # [36:39]
        ("u32L1_RO_CURR_SUM_C1_C2_BK1", ctypes.c_uint32),  # [40:43]
        ("u32L1_RO_CURR_SUM_C3_C4_BK1", ctypes.c_uint32),  # [44:47]
        ("u32L1_RO_CURR_SUM_C5_TOT_BK1", ctypes.c_uint32),  # [48:51]
        ("u32L0_RO_CURR_SSLMS_C0_C1_BK2", ctypes.c_uint32),  # [52:55]
        ("u32L0_RO_CURR_SSLMS_C2_C3_BK2", ctypes.c_uint32),  # [56:59]
        ("u32L0_RO_CURR_SSLMS_C4_C5_BK2", ctypes.c_uint32),  # [60:63]
        ("u32L0_RO_CURR_SUM_C1_C2_BK2", ctypes.c_uint32),  # [64:67]
        ("u32L0_RO_CURR_SUM_C3_C4_BK2", ctypes.c_uint32),  # [68:71]
        ("u32L0_RO_CURR_SUM_C5_TOT_BK2", ctypes.c_uint32),  # [72:75]
        ("u32L1_RO_CURR_SSLMS_C0_C1_BK2", ctypes.c_uint32),  # [76:79]
        ("u32L1_ROCURR_SSLMS_C2_C3_BK2", ctypes.c_uint32),  # [80:83]
        ("u32L1_RO_CURR_SSLMS_C4_C5_BK2", ctypes.c_uint32),  # [84:87]
        ("u32L1_RO_CURR_SUM_C1_C2_BK2", ctypes.c_uint32),  # [88:91]
        ("u32L1_RO_CURR_SUM_C3_C4_BK2", ctypes.c_uint32),  # [92:95]
        ("u32L1_RO_CURR_SUM_C5_TOT_BK2", ctypes.c_uint32),  # [96:99]
        ("u8EM_ATTR_EYEMON_CAP", ctypes.c_ubyte),  # [100]
        ("u8EM_ATTR_TIMING_MAX_STEP_CAP", ctypes.c_ubyte),  # [101]
        ("u8EM_ATTR_TIMING_MAX_OFFSET_CAP", ctypes.c_ubyte),  # [102]
        ("u8EM_ATTR_VOLTAGE_MAX_STEP_CAP", ctypes.c_ubyte),  # [103]
        ("u8EM_ATTR_VOLTAGE_MAX_OFFSET_CAP", ctypes.c_ubyte),  # [104]
        ("u8EM_ATTR_EYEMON_ENABLE", ctypes.c_ubyte),  # [105]
        ("u8EM_ATTR_TIMING_STEP", ctypes.c_ubyte),  # [106]
        ("u8EM_ATTR_VOLTAGE_STEP", ctypes.c_ubyte),  # [107]
        ("u8EM_ATTR_TARGET_TEST_CNT", ctypes.c_ubyte),  # [108]
        ("u24Rsvd2", ctypes.c_ubyte * 3),  # [109-111]

    ]

class MPHY_EYE_MONITOR_UNION(ctypes.Union):
    _fields_ = [
        ("mResult", ctypes.c_uint8 * 512),
        ("mData", _MphyEyeMonitorData)
    ]

class MPHY_EYE_MONITOR_RESULT(ctypes.Structure):
    _fields_ = [
        ("monitorData", MPHY_EYE_MONITOR_UNION),
        ("mDataArray", MPHY_EYE_MONITOR_ELEMENT * (127 * 127))
    ]

def software_crc(dll: Dll, s: bytearray, length: int, first_in: int, last_crc: int):
    """Calculate Software CRC

    """
    dll.errcode = dll.cdll.Software_CRC(
        (ctypes.c_ubyte * len(s)).from_buffer(s),
        ctypes.c_uint(length),
        ctypes.c_ushort(first_in),
        ctypes.c_uint(last_crc)

    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (ex.DLL_ERROR, "Software CRC calculation failed")
        }, "software_crc")
    
def cal_sha2_hmac(dll: Dll, key: bytearray, key_len:int, input: bytearray, ilen: int, output: bytearray, is_224: int):
    """Calculate SHA2 HMAC

    """
    dll.errcode = dll.cdll.Cal_sha2_hmac(
        (ctypes.c_ubyte * len(key)).from_buffer(key),
        ctypes.c_uint(key_len),
        (ctypes.c_ubyte * len(input)).from_buffer(input),
        ctypes.c_uint(ilen),
        (ctypes.c_ubyte * len(output)).from_buffer(output),
        ctypes.c_int(is_224)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "SHA2 HMAC calculation failed")
        }, "cal_sha2_hmac")
    
def on_switch_ref_clk(dll: Dll, ref_clk: float):
    """Switch reference clock
    Arg:
        ref_clk: reference clock
    """
    dll.cdll.OnSwitchRefClk.argtypes = [ctypes.c_void_p, ctypes.c_double]
    dll.cdll.OnSwitchRefClk.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.OnSwitchRefClk(
        dll.sdk,
        ctypes.c_double(ref_clk)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Switch reference clock fail"),
            0x02: (DLL_ERROR, "Unsupport on ps2806"),
            0x03: (DLL_ERROR, "Unsupport on ps2807")
        }, "OnSwitchRefClk")

def direct_read_page(dll: Dll, info_buf: bytearray):
    """Direct read page

    """
    dll.errcode = dll.cdll.Direct_Read_Page(
        (ctypes.c_ubyte * len(info_buf)).from_buffer(info_buf)
    )

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Direct read page fail")
        }, "direct_read_page")
    
def get_sdk_tester_internal_info(dll: Dll) -> str:
    """Get SDK tester internal info
        Return:
            str: SDK tester internal info string 
    """
    dll.cdll.GetSDKTesterInternalInfo.argtypes = [ctypes.c_void_p]
    dll.cdll.GetSDKTesterInternalInfo.restype = ctypes.c_char_p
    result = dll.cdll.GetSDKTesterInternalInfo(dll.sdk)
    result_str = result.decode('utf-8')
    return result_str

def force_boot_code(dll: Dll, mode: int, sl_delay: int, ll_delay: int, sll_delay: int, slh_delay: int):
    """Force boot code
        Arg:
            mode: force boot mode type
            sl_delay: SL delay time
            ll_delay: LL delay time
            sll_delay: SLL delay time
            slh_delay: SLH delay time
    """
    dll.cdll.ForceBootCode.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_ushort, ctypes.c_ubyte, ctypes.c_ubyte]
    dll.cdll.ForceBootCode.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.ForceBootCode(
        dll.sdk,
        ctypes.c_ubyte(mode),
        ctypes.c_ushort(sl_delay),
        ctypes.c_ubyte(ll_delay),
        ctypes.c_ubyte(sll_delay),
        ctypes.c_ubyte(slh_delay)
    )

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Force boot code fail"),
            0x02: (DLL_ERROR, "Unsupport on ps2806"),
            0x03: (DLL_ERROR, "Unsupport on ps2807")
        }, "force_boot_code")

def mphy_eye_monitor(dll: Dll, param: MPHY_EYE_MONITOR_PARAM) -> MPHY_EYE_MONITOR_RESULT:
    """MPHY eye monitor    
    Args:
        dll: Dll instance
        param: MPHY eye monitor parameters
    """
    #c_param = param.to_c_param()
    c_result = MPHY_EYE_MONITOR_RESULT()

    dll.cdll.MPHYEyeMonitor.argtypes = [ctypes.c_void_p, ctypes.POINTER(MPHY_EYE_MONITOR_PARAM), ctypes.POINTER(MPHY_EYE_MONITOR_RESULT)]
    dll.cdll.MPHYEyeMonitor.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.MPHYEyeMonitor(
        dll.sdk,
        ctypes.byref(param),
        ctypes.byref(c_result)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "MPHY eye monitor failed")
        }, "MPHYEyeMonitor")

    return c_result

def generate_ptng_data(dll: Dll, lun: int, read_task_tag: int, lba: int, data_byte: int, data_cnt: int, write_buf: bytearray, read_buf: bytearray):
    """gernerate auto mode write pattern and read data selected area
        Arg:
            lun: Lun selected
            read_task_tag: Task Tag for read task
            lba: Start LBA for read/write
            data_byte: Total byte to generate and read
            data_cnt: Block Size
            write_buf: Generate write buffer
            read_buf: Generate read buffer
    """

    dll.cdll.Generate_PTNG_Data.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Generate_PTNG_Data.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Generate_PTNG_Data(
        dll.sdk,
        ctypes.c_uint(lun),
        ctypes.c_uint(read_task_tag),
        ctypes.c_uint(lba),
        ctypes.c_uint(data_byte),
        ctypes.c_uint(data_cnt),
        (ctypes.c_ubyte * len(write_buf)).from_buffer(write_buf),
        (ctypes.c_ubyte * len(read_buf)).from_buffer(read_buf)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Generate pattern data fail"),
            0x02: (DLL_ERROR, "Unsupport on ps2806"),
            0x03: (DLL_ERROR, "Unsupport on ps2807")
        }, "Generate_PTNG_Data")
