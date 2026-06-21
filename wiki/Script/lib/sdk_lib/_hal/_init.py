import ctypes
from ._base import Dll, handle_error_code
from .exception import *

def dll_initial(dll: Dll, dll_version_check: int = 0):
    """Authentication between tester and library
    
    Args:
        dll: Dll instance
        dll_version_check:
            0 - (default) Disable check DLL version.
            1 - Enable check DLL version , if DLL version is not expected , return fail (value = 4).
    """
    dll.errcode = dll.cdll.Dll_Initial(
        dll.sdk,
        ctypes.c_ubyte(dll_version_check)
    )

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_VID_ERROR, "VID is not correct"),
            0x02: (DLL_SDK_FW_ERROR, "is not SDK FW"),
            0x03: (DLL_HANDSHAKE_ERROR, "Handshake fail"),
            0x04: (DLL_VERSION_ERROR, "DLL version is not expected"),
            0x05: (DLL_AUTH_ERROR, "Authentication fail"),
            0xFF: (DLL_GENERAL_ERROR, "Others, please check SDK log")
        }, "DLL_Initial")

def set_handle(dll: Dll, handle: int, drive: int = 0):
    """Set handle
    
    Args:
        dll: Dll instance
        handle: Device handle
        drive: Drive number, default is 0
    """
    dll.cdll.SetHandle.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint32]
    dll.cdll.SetHandle.restype = ctypes.c_ubyte
    
    dll.errcode = dll.cdll.SetHandle(
        dll.sdk,
        ctypes.c_uint64(handle),  # HANDLE is void* in Windows
        ctypes.c_uint32(drive)    # DWORD is 32-bit unsigned integer
    )

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Fail"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "set_handle")

def host_initial(dll: Dll, mode: int):
    """Host initialization
    
    Args:
        dll: Dll instance
        mode: Initialization mode
    """
    
    dll.cdll.HostInitial.argtypes = [ctypes.c_void_p, ctypes.c_ubyte]
    dll.cdll.HostInitial.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.HostInitial(
        dll.sdk,
        ctypes.c_ubyte(mode)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Fail"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "host_initial")

def host_link_startup(dll: Dll):
    """Host link startup with device
    
    Args:
        dll: Dll instance
        
    Returns:
        Startup status code
    """

    dll.cdll.HostLinkStartup.argtypes = [ctypes.c_void_p]
    dll.cdll.HostLinkStartup.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.HostLinkStartup(dll.sdk)
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, {
            0x01: (DLL_ERROR, "Fail"),
            0x02: (DLL_UNSUPPORT_ON_PS2806, "Unsupport on ps2806"),
            0x03: (DLL_UNSUPPORT_ON_PS2807, "Unsupport on ps2807")
        }, "host_link_startup")

def set_link_startup_mode(dll: Dll, reset_mode: int):
    """
    Select either HS Link Startup or LS Link Startup (PS2810 Only)
    Args:
        dll: Dll instance
        reset_mode: Reset mode
    """
    dll.cdll.Set_LinkStartup_Mode.argtypes = [ctypes.c_void_p, ctypes.c_ubyte]
    dll.cdll.Set_LinkStartup_Mode.restype = ctypes.c_ubyte
    dll.errcode = dll.cdll.Set_LinkStartup_Mode(
        dll.sdk, 
        ctypes.c_ubyte(reset_mode)
    )
    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, None, "set_link_startup_mode")
    return dll.errcode

def get_dll_version(dll: Dll) -> bytearray:
    """Get DLL version
    
    Args:
        dll: Dll instance
        
    Returns:
        Bytearray containing version information
    """
    version = bytearray(6)
    dll.cdll.Get_Dll_Version.argtypes = [ctypes.c_void_p,  ctypes.POINTER(ctypes.c_ubyte)]
    dll.cdll.Get_Dll_Version.restype = ctypes.c_ubyte    
    dll.cdll.Get_Dll_Version(
        dll.sdk,
        (ctypes.c_ubyte * len(version)).from_buffer(version)
    )

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, None, "get_dll_version")
    return version

def get_hub_info(dll: Dll) -> tuple[str, int, int, int, int, str]:
    """Get USB HUB information
    
    Args:
        dll: Dll instance
        
    Returns:
        Tuple containing (tester_id, port, vid, pid, usb_ver, hub_id)
    """
    tester_id = ctypes.c_char()
    port = ctypes.c_ushort()
    vid = ctypes.c_ushort()
    pid = ctypes.c_ushort()
    usb_ver = ctypes.c_ushort()
    hub_id = ctypes.c_char()
    
    dll.cdll.GetHubInfo.argtypes = [ctypes.c_void_p, 
                                    ctypes.POINTER(ctypes.c_char), 
                                    ctypes.POINTER(ctypes.c_ushort), 
                                    ctypes.POINTER(ctypes.c_ushort), 
                                    ctypes.POINTER(ctypes.c_ushort), 
                                    ctypes.POINTER(ctypes.c_ushort), 
                                    ctypes.POINTER(ctypes.c_char)]
    dll.cdll.GetHubInfo.restype = ctypes.c_ushort
    dll.errcode = dll.cdll.GetHubInfo(
        dll.sdk,
        ctypes.byref(tester_id),
        ctypes.byref(port),
        ctypes.byref(vid),
        ctypes.byref(pid),
        ctypes.byref(usb_ver),
        ctypes.byref(hub_id)
    )

    if dll.errcode != 0x00:
        handle_error_code(dll.errcode, None, "get_hub_info")
    
    return (
        tester_id.value.decode('utf-8'),
        port.value,
        vid.value,
        pid.value,
        usb_ver.value,
        hub_id.value.decode('utf-8')
    )