import os
import struct
import atexit

# ---------------------- Export ----------------------
#from ._hal import *  # DON'T!
#from ._sdk_base import *  # DON'T
from .log_callback import LogEntry, set_log_callback

from .constant import *
from .exception import *
from ._cmd_seq import *
from ._data_trans import *
from ._debug_fw import *
from ._dme import *
from ._group_rw import *
from ._host import *
from ._init import *
from ._others import *
from ._perfor import *
from ._power import *
from ._rest import *
from ._track_log import *
# ----------------------------------------------------

from .. import _hal
from ._cmd_seq import _SDKLibCmdSeqMixin
from ._data_trans import _SDKLibCmdTransMixin
from ._dcmd import _SDKLibDebugCmdMixin
from ._debug_fw import _SDKLibDebugFwEventMixin
from ._dme import _SDKLibDmeMixin
from ._group_rw import _SDKLibGroupRWMixin
from ._host import _SDKLibHostMixin
from ._hpb import _SDKLibHpbMixin
from ._init import _SDKLibInitMixin
from ._others import _SDKLibOthersMixin
from ._perfor import _SDKLibPerformanceMixin
from ._power import _SDKLibPowerMixin
from ._rest import _SDKLibRestMixin
from ._scmd import _SDKLibScmdMixin
from ._sdram import _SDKLibSdramMixin
from ._track_log import _SDKLibTrackLogMixin

class SDKLib(
    _SDKLibCmdSeqMixin,
    _SDKLibCmdTransMixin,
    _SDKLibDebugCmdMixin,
    _SDKLibDebugFwEventMixin,
    _SDKLibDmeMixin,
    _SDKLibGroupRWMixin,
    _SDKLibHostMixin,
    _SDKLibHpbMixin,
    _SDKLibInitMixin,
    _SDKLibOthersMixin,
    _SDKLibPerformanceMixin,
    _SDKLibPowerMixin,
    _SDKLibRestMixin,
    _SDKLibScmdMixin,
    _SDKLibSdramMixin,
    _SDKLibTrackLogMixin
):
    DLL_DIRPATH = os.path.normpath(os.path.dirname(__file__) + "/sdk_dll")

    _dll_cache: dict[int, _hal.Dll] = {}

    def __init__(self, drive: int):
        self.drive: int = drive

        if drive in self._dll_cache:
            self._dll = self._dll_cache[drive]
            return

        is_win32 = struct.calcsize("P") * 8 == 32
        config = "Win32" if is_win32 else "x64"
        dll_path = f"{self.DLL_DIRPATH}//{config}//ReleaseCstyle//VendorCmdDll.dll"

        if is_win32:
            self._dll = _hal.create_sdk_win32(dll_path)
        else:
            self._dll = _hal.create_sdk_x64(dll_path)

        self._dll_cache[drive] = self._dll

        #set handle
        device_handle = os.open(r'\\.\PhysicalDrive' + str(self.drive), os.O_RDWR | os.O_BINARY)
        _hal.set_handle(self._dll, device_handle, self.drive)
        os.close(device_handle)

        # set SDK log
        _hal.set_log_data_callback_ui(self._dll)

        # delete SDK if program ends
        atexit.register(self.delete_sdk)

    def delete_sdk(self):
        if self._dll is None:
            return

        if self._dll.sdk:
            _hal.delete_sdk(self._dll)
            self._dll = None   # type: ignore
            self._dll_cache.pop(self.drive)
        else:
            print("no need to delete sdk ^_^")