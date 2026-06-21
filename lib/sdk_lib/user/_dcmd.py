from ._sdk_base import _SDKLibProtocol
from .. import _hal

class _SDKLibDebugCmdMixin(_SDKLibProtocol):
    def set_debug_cmd(self, idx: int, arg_buf: bytearray, reserved: int, data_buf: bytearray):
        _hal.set_debug_cmd(self._dll, idx, arg_buf, reserved, data_buf)

    def get_debug_cmd(self, idx: int) -> bytearray:
        return _hal.get_debug_cmd(self._dll, idx)
    
    def debug_cmd_monitor(self, idx: int, arg_buf: bytearray) -> bytearray:
        return _hal.debug_cmd_monitor(self._dll, idx, arg_buf)