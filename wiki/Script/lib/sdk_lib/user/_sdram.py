from ._sdk_base import _SDKLibProtocol
from . import _hal

class _SDKLibSdramMixin(_SDKLibProtocol):
    def get_sdram_data(self, block_cnt: int) -> bytearray:
        return _hal.get_sdram_data(self._dll, block_cnt)