from ._sdk_base import _SDKLibProtocol
from .. import _hal

class FwEventResult:
    def __init__(self, info_buf: bytearray):
        self.time_stamp = int.from_bytes(info_buf[0:4], byteorder='little')
        self.ctrl_tj = 0
        self.nand_tj_min = 0
        self.rev1 = 0
        self.fw_event = int.from_bytes(info_buf[8:12], byteorder='little')
        self.read_error_handling_cnt = int.from_bytes(info_buf[12:16], byteorder='little')
        self.rev2 = info_buf[20:32]
    
    @classmethod
    def from_large_buffer(cls, large_buf: bytearray):
        """
        Create multiple segment instances from a large buffer.

        :param cls: The class itself, used to create segment instances
        :param large_buf: The large buffer to be split into segments
        :return: A list of segment instances
        """
        segment_size = 32
        assert len(large_buf) % segment_size == 0, f"Buffer length {len(large_buf)} is not a multiple of segment size {segment_size}"

        results = []
        for i in range(0, len(large_buf), segment_size):
            segment = large_buf[i:i + segment_size]
            result = cls(segment)
            results.append(result)
        return results

class _SDKLibDebugFwEventMixin(_SDKLibProtocol):
    def debug_fw_event_activate(self, opt: int):
        _hal.debug_fw_event_activate(self._dll, opt)
    
    def debug_fw_event_reset(self):
        _hal.debug_fw_event_reset(self._dll)

    def debug_fw_event_result(self) -> bytearray:
        return _hal.debug_fw_event_result(self._dll)