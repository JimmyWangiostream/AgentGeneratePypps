from ._sdk_base import _SDKLibProtocol
from .. import _hal
from . import log_callback as logger
from enum import Enum

class HostInit(Enum):
    TESTER_SHORT_DETECT = 0x00
    TESTER_POWER_OFF = 0x5A
    TESTER_KEEP_VOL_SET = 0xBA

class HubInfo:
    def __init__(self):
        self.tester_id = ""
        self.port_num = [0] * 256
        self.vid = [0] * 256
        self.pid = [0] * 256
        self.usb_version = [0] * 256
        self.hubID = ""

class DllVersion:
    def __init__(self):
        self.v = 0
        self.main_ver = 0
        self.minor_ver = 0
        self.year = 0
        self.month = 0
        self.date = 0

class _SDKLibInitMixin(_SDKLibProtocol):
    def set_handle(dll: _hal.Dll, handle: int, drive: int = 0):
        _hal.set_handle(dll, handle, drive)

    def get_hub_info(self) -> HubInfo:
        (tester_id, port, vid, pid, usb_ver, hub_id) = _hal.get_hub_info(self._dll)
        
        hub_info = HubInfo()
        hub_info.tester_id = tester_id.rstrip('\x00')
        hub_info.hubID = hub_id.rstrip('\x00')

        for i in range(256):
            hub_info.port_num[i] = int.from_bytes(port.raw[i*2:(i+1)*2], byteorder='little')
            hub_info.vid[i] = int.from_bytes(vid.raw[i*2:(i+1)*2], byteorder='little')
            hub_info.pid[i] = int.from_bytes(pid.raw[i*2:(i+1)*2], byteorder='little')
            hub_info.usb_version[i] = int.from_bytes(usb_ver.raw[i*2:(i+1)*2], byteorder='little')

        return hub_info

    def dll_initial(self, dll_version_check: int = 0):
        _hal.dll_initial(self._dll, dll_version_check)

    def host_initial(self, mode: int):
        _hal.host_initial(self._dll, mode)

    def host_link_startup(self):
        _hal.host_link_startup(self._dll)

    def set_link_startup_mode(self, reset_mode: int):
        _hal.set_link_startup_mode(self._dll, reset_mode)

    def get_dll_version(self) -> DllVersion:
        dll_version = DllVersion()
        tmp_bytearray = _hal.get_dll_version(self._dll)
        
        # fill dll_version
        dll_version.v = tmp_bytearray[0]
        dll_version.main_ver = tmp_bytearray[1]
        dll_version.minor_ver = tmp_bytearray[2]
        dll_version.year = tmp_bytearray[3]
        dll_version.month = tmp_bytearray[4]
        dll_version.date = tmp_bytearray[5]
        
        return dll_version