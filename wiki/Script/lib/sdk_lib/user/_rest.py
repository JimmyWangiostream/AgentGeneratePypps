from ._sdk_base import _SDKLibProtocol, swap_endian
from .. import _hal
from . import log_callback as logger
from enum import Enum, auto

class HostDQType(Enum):
    TAG_DONE_QUEUE = 1
    LUN_DONE_QUEUE = auto()
    ALL_DONE_QUEUE = auto()
    ALL_DONE_QUEUE_ERR_HANDLE = auto()

class _SDKLibRestMixin(_SDKLibProtocol):
    def reset_n (self, mode: int = 0, tRSTW: int = 0):
        _hal.reset_n(self._dll, mode, tRSTW)

    def reset_n_key(self, mode: int, option: int = 0):
        _hal.reset_n_key(self._dll, mode, option)

    def reset_n_vendor_cmd(self, direction: int, block_cnt: int, arg_pag: bytearray, data: bytearray):
        _hal.reset_n_vendor_cmd(self._dll, direction, block_cnt, arg_pag, data)

    def clear_done_queue(self, type: int, clear_item: int):
        _hal.clear_done_queue(self._dll, type, clear_item)
