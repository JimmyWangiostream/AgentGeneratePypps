from ._sdk_base import _SDKLibProtocol
from .. import _hal

class _SDKLibScmdMixin(_SDKLibProtocol):
    def scmd_unipro_error_inject(self, arg_buf: bytearray):
        _hal.scmd_unipro_error_inject(self._dll, arg_buf)

    def scmd_gpio_trigger(self, arg_buf: bytearray):
        _hal.scmd_gpio_trigger(self._dll, arg_buf)

    def scmd_dme_error_count(self, arg_buf: bytearray):
        _hal.scmd_dme_error_count(self._dll, arg_buf)

    def scmd_spor(self, arg_buf: bytearray):
        _hal.scmd_spor(self._dll, arg_buf)

    def scmd_uart(self, arg_buf: bytearray):
        _hal.scmd_uart(self._dll, arg_buf)
    
    def scmd_get_info(self, scmd_idx: bytes) -> bytearray:
        return _hal.scmd_get_info(self._dll, scmd_idx)
