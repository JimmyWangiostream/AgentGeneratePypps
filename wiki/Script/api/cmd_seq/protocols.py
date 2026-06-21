from abc import abstractmethod
from Script.api.cmd_seq._cycle_tracker import CycleIndicator
from Script.api.exception import PATTERN_ASSERT_EXECUTOR_UNIFORM_TIMEOUT_VALUE_EXCEEDS_MAX
from Script.api.struct_helper import *
from Script.api.ufs_api.defines.enum_define import CmdParamPatternMode, TimeResolution
from Script.api.ufs_api.upiu.protocols import IsUpiu
import bitstruct
from Script.api.ufs_api.defines import CmdParamPatternMode


class UniformTimeout:
    def __init__(self, val: int, unit: TimeResolution=TimeResolution.ms):
        self._val: int
        self.val = val
        self.unit = unit
    @property
    def val(self) -> int:
        return self._val
    @val.setter
    def val(self, new_val: int) -> None:
        if new_val > 0x00FFFFFF:
            raise PATTERN_ASSERT_EXECUTOR_UNIFORM_TIMEOUT_VALUE_EXCEEDS_MAX
        self._val = new_val

class CmdUpiuParam(PacketComposerABC):
    def __init__(self) -> None:
        self.l32_delay_time: int = 0
        self.w36_wait_queue_empty: int = 0
        self.w36_pattern_mode: CmdParamPatternMode = CmdParamPatternMode.HW_INCREASE
        self.w36_add_tag: int = 0
        self.w36_data_in_out: int = 0
        self.w36_crc_compare: int = 0
        self.l38_mark_tag_or_crc32: int = 0x12345678
        self.l42_data_address_offset: int = 0
        self.l46_data_length: int = 0
        self.l50_timeout: int = 0
        self.l54_ehs_data_address: int = 0
    def to_bytes(self) -> bytearray:
        b = bytearray(40)
        b[0:4] = self.l32_delay_time.to_bytes(4)
        # High Bit to Low Bit
        b[4:6] = bitstruct.pack('u7u1u1u1u1u1u2u1u1',0,self.w36_crc_compare,
                                0, self.w36_data_in_out, 0, self.w36_add_tag,
                                self.w36_pattern_mode, 0, self.w36_wait_queue_empty)
        b[6:10] = self.l38_mark_tag_or_crc32.to_bytes(4)
        b[10:14] = self.l42_data_address_offset.to_bytes(4)
        b[14:18] = self.l46_data_length.to_bytes(4)
        b[18:22] = self.l50_timeout.to_bytes(4)
        b[22:26] = self.l54_ehs_data_address.to_bytes(4)
        return b
    
class IsEntry(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.cycle_indicator: CycleIndicator = CycleIndicator()
    @abstractmethod
    def compose_entry_buf(self) -> bytearray:
        pass
    def enqueue(self) -> int:
        from Script.api.cmd_seq.executor import enqueue
        return enqueue(self)

class IsCmdUpiuEntry(IsEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param: CmdUpiuParam = CmdUpiuParam()

        from Script.api.util.timeout.structs import usermode_timeout

        usermode_timeout.set_cmd_timeout(self)


    def compose_entry_buf(self) -> bytearray:
        b = bytearray(72)
        b[0:32] = self.upiu.to_bytes()
        b[32:72] = self.param.to_bytes()
        return b

def is_tester_cmd(cmd: IsEntry) -> bool:
    return cmd.upiu.b0_transaction_type == 0xFF