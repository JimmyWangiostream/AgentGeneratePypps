import struct
from typing import Self
import bitstruct
import math
from Script.api.cmd_seq.protocols import IsCmdUpiuEntry, IsEntry
from Script.api.exception import PATTERN_ASSERT_ILLEGAL_PARAM_BAD_DIVM, PATTERN_ASSERT_ILLEGAL_PARAM_HW_COMPARE_MIX_WITH_MANUAL_MODE, PATTERN_ASSERT_ILLEGAL_PARAM_BAD_REF_CLK
from Script.api.ufs_api.defines.enum_define import UPIUTransactionType
from Script.api.ufs_api.upiu import upiu
from Script.api.ufs_api.upiu.structs import PacketComposerABC
from Script.api.ufs_api.defines import PowerCycleMode, SpdChgPowerMode, SpdChgGear, SpdChgLane, SpdChgHsRate, CmdParamPatternMode
from Script.api import shared

_log = shared.logger

############### Spec Commands ###############

class NopOut(upiu.BaseNopOut, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class FormatUnit(upiu.BaseFormatUnit, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class Inquiry(upiu.BaseInquiry, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class ModeSelect10(upiu.BaseModeSelect10, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class ModeSense10(upiu.BaseModeSense10, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class PreFetch10(upiu.BasePreFetch10, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class PreFetch16(upiu.BasePreFetch16, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class Read6(upiu.BaseRead6, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, manual_mode: bool | None=None, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_data_in_out = self.param.w36_data_in_out if manual_mode is None else manual_mode
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self
    def set_sw_cmp(self, crc32: int) -> Self:
        self.param.l38_mark_tag_or_crc32 = crc32
        self.param.w36_add_tag = 0
        self.param.w36_crc_compare = 1
        return self
    def set_hw_cmp(self, mark_tag: int, pattern_mode: CmdParamPatternMode) -> Self:
        if self.param.w36_data_in_out == 1:
            raise PATTERN_ASSERT_ILLEGAL_PARAM_HW_COMPARE_MIX_WITH_MANUAL_MODE
        self.param.w36_add_tag = 1
        self.param.w36_crc_compare = 0
        self.param.l38_mark_tag_or_crc32 = mark_tag
        self.param.w36_pattern_mode = pattern_mode
        return self


class Read10(upiu.BaseRead10, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, manual_mode: bool | None=None, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_data_in_out = self.param.w36_data_in_out if manual_mode is None else manual_mode
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self
    def set_sw_cmp(self, crc32: int) -> Self:
        self.param.l38_mark_tag_or_crc32 = crc32
        self.param.w36_add_tag = 0
        self.param.w36_crc_compare = 1
        return self
    def set_hw_cmp(self, mark_tag: int, pattern_mode: CmdParamPatternMode) -> Self:
        if self.param.w36_data_in_out == 1:
            raise PATTERN_ASSERT_ILLEGAL_PARAM_HW_COMPARE_MIX_WITH_MANUAL_MODE
        self.param.w36_add_tag = 1
        self.param.w36_crc_compare = 0
        self.param.l38_mark_tag_or_crc32 = mark_tag
        self.param.w36_pattern_mode = pattern_mode
        return self


class Read16(upiu.BaseRead16, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, manual_mode: bool | None=None, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_data_in_out = self.param.w36_data_in_out if manual_mode is None else manual_mode
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self
    def set_sw_cmp(self, crc32: int) -> Self:
        self.param.l38_mark_tag_or_crc32 = crc32
        self.param.w36_add_tag = 0
        self.param.w36_crc_compare = 1
        return self
    def set_hw_cmp(self, mark_tag: int, pattern_mode: CmdParamPatternMode) -> Self:
        if self.param.w36_data_in_out == 1:
            raise PATTERN_ASSERT_ILLEGAL_PARAM_HW_COMPARE_MIX_WITH_MANUAL_MODE
        self.param.w36_add_tag = 1
        self.param.w36_crc_compare = 0
        self.param.l38_mark_tag_or_crc32 = mark_tag
        self.param.w36_pattern_mode = pattern_mode
        return self


class ReadBuffer(upiu.BaseReadBuffer, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class ReadCapacity10(upiu.BaseReadCapacity10, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class ReadCapacity16(upiu.BaseReadCapacity16, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class ReportLUNs(upiu.BaseReportLUNs, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class RequestSense(upiu.BaseRequestSense, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class SecurityProtocolIn(upiu.BaseSecurityProtocolIn, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class SecurityProtocolOut(upiu.BaseSecurityProtocolOut, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self

class SendDiagnostic(upiu.BaseSendDiagnostic, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class StartStopUnit(upiu.BaseStartStopUnit, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class SyncCache10(upiu.BaseSyncCache10, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class SyncCache16(upiu.BaseSyncCache16, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class TestUnitReady(upiu.BaseTestUnitReady, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class Unmap(upiu.BaseUnmap, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class Verify10(upiu.BaseVerify10, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class Write6(upiu.BaseWrite6, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.specific_tag: int | None = None
        self.param.w36_add_tag = True
    def set_option(self, manual_mode: bool | None=None, mark_tag: int | None=None, wait_queue_empty: bool | None=None, 
                   timeout: int | None=None, delay_time: int | None=None, pattern_mode: CmdParamPatternMode | None = None,
                    auto_mode_add_tag: bool | None=None) -> Self:
        """
        Auto Mode parameters include:
            - `mark_tag`: e.g. 0x12345678
            - `pattern_mode`: e.g. `CmdParamPatternMode.HW_FIX`
            - `auto_mode_add_tag`: e.g True

        These Auto Mode parameters take effect **only when `manual_mode` is False**.  
        """
        self.specific_tag = self.specific_tag if mark_tag is None else mark_tag
        self.param.w36_add_tag = self.param.w36_add_tag if auto_mode_add_tag is None else auto_mode_add_tag
        self.param.w36_pattern_mode = self.param.w36_pattern_mode if pattern_mode is None else pattern_mode
        self.param.w36_data_in_out = self.param.w36_data_in_out if manual_mode is None else manual_mode
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class Write10(upiu.BaseWrite10, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.specific_tag: int | None = None
        self.param.w36_add_tag = True
    def set_option(self, manual_mode: bool | None=None, mark_tag: int | None=None, wait_queue_empty: bool | None=None, 
                   timeout: int | None=None, delay_time: int | None=None, pattern_mode: CmdParamPatternMode | None = None,
                    auto_mode_add_tag: bool | None=None) -> Self:
        """
        Auto Mode parameters include:
            - `mark_tag`: e.g. 0x12345678
            - `pattern_mode`: e.g. `CmdParamPatternMode.HW_FIX`
            - `auto_mode_add_tag`: e.g True

        These Auto Mode parameters take effect **only when `manual_mode` is False**.  
        """
        self.specific_tag = self.specific_tag if mark_tag is None else mark_tag
        self.param.w36_add_tag = self.param.w36_add_tag if auto_mode_add_tag is None else auto_mode_add_tag
        self.param.w36_pattern_mode = self.param.w36_pattern_mode if pattern_mode is None else pattern_mode
        self.param.w36_data_in_out = self.param.w36_data_in_out if manual_mode is None else manual_mode
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class Write16(upiu.BaseWrite16, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.specific_tag: int | None = None
        self.param.w36_add_tag = True
    def set_option(self, manual_mode: bool | None=None, mark_tag: int | None=None, wait_queue_empty: bool | None=None, 
                   timeout: int | None=None, delay_time: int | None=None, pattern_mode: CmdParamPatternMode | None = None,
                    auto_mode_add_tag: bool | None=None) -> Self:
        """
        Auto Mode parameters include:
            - `mark_tag`: e.g. 0x12345678
            - `pattern_mode`: e.g. `CmdParamPatternMode.HW_FIX`
            - `auto_mode_add_tag`: e.g True

        These Auto Mode parameters take effect **only when `manual_mode` is False**.  
        """
        self.specific_tag = self.specific_tag if mark_tag is None else mark_tag
        self.param.w36_add_tag = self.param.w36_add_tag if auto_mode_add_tag is None else auto_mode_add_tag
        self.param.w36_pattern_mode = self.param.w36_pattern_mode if pattern_mode is None else pattern_mode
        self.param.w36_data_in_out = self.param.w36_data_in_out if manual_mode is None else manual_mode
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class WriteBuffer(upiu.BaseWriteBuffer, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:

        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class TaskManagement(upiu.BaseTaskManagement, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:

        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class HpbRead(upiu.BaseHpbRead, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class HpbReadBuffer(upiu.BaseHpbReadBuffer, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class HpbWriteBuffer01(upiu.BaseHpbWriteBuffer01, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class HpbWriteBuffer02(upiu.BaseHpbWriteBuffer02, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class HpbWriteBuffer03(upiu.BaseHpbWriteBuffer03, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self

class VendorCmdWrite(upiu.BaseVendorCmdWrite, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self

class VendorCmdRead(upiu.BaseVendorCmdRead, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self

class VendorCmdNoWR(upiu.BaseVendorCmdNoWR, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self

class ReadDescriptor(upiu.BaseReadDescriptor, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class WriteDescriptor(upiu.BaseWriteDescriptor, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
        self.param.w36_data_in_out = 1
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class ReadAttribute(upiu.BaseReadAttribute, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class WriteAttribute(upiu.BaseWriteAttribute, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class ReadFlag(upiu.BaseReadFlag, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class SetFlag(upiu.BaseSetFlag, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class ClearFlag(upiu.BaseClearFlag, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


class ToggleFlag(upiu.BaseToggleFlag, IsCmdUpiuEntry):
    def __init__(self) -> None:
        super().__init__()
    def set_option(self, wait_queue_empty: bool | None=None,
                   timeout: int | None=None, delay_time: int | None=None) -> Self:
        self.param.w36_wait_queue_empty = self.param.w36_wait_queue_empty if wait_queue_empty is None else wait_queue_empty
        self.param.l32_delay_time = self.param.l32_delay_time if delay_time is None else delay_time
        self.param.l50_timeout = self.param.l50_timeout if timeout is None else timeout
        return self


############### Spec Commands end ###############


############### Tester Commands ###############

class CmdSeqPowerCycle(IsEntry):
    class _32B(PacketComposerABC):
        def __init__(self) -> None:
            self.b0_transaction_type = UPIUTransactionType.SDK_CMD
            self.b1_function_code = 0x01
            self.b2_mode = 0
        def to_bytes(self) -> bytearray:
            b = bytearray(32)
            b[0] = self.b0_transaction_type
            b[1] = self.b1_function_code
            b[2] = self.b2_mode
            return b
    def __init__(self) -> None:
        super().__init__()
        self.upiu: "CmdSeqPowerCycle._32B" = self._32B()
        self.w36_wait_queue_empty = False
        self.l32_delay_time = 0
    def compose_entry_buf(self) -> bytearray:
        b = bytearray(72)
        b[0:32] = self.upiu.to_bytes()
        b[32:36] = self.l32_delay_time.to_bytes(4, 'big')
        b[36:38] = bitstruct.pack('u15u1', 0, self.w36_wait_queue_empty)
        return b
    def set_option(self, mode: PowerCycleMode, wait_queue_empty: bool=False, delay_time: int=0) -> Self:
        self.upiu.b2_mode = mode
        self.l32_delay_time = delay_time
        self.w36_wait_queue_empty = wait_queue_empty
        return self

class CmdSeqSwitchVoltage(IsEntry):
    class _32B(PacketComposerABC):
        def __init__(self) -> None:
            self.b0_transaction_type = UPIUTransactionType.SDK_CMD
            self.b1_function_code = 0x02
            self.w2_vcc = 0
            self.w4_vccq2 = 0
            self.w6_vccq = 0
        def to_bytes(self) -> bytearray:
            b = bytearray(32)
            b[0] = self.b0_transaction_type
            b[1] = self.b1_function_code
            b[2:4] = self.w2_vcc.to_bytes(2, 'big')
            b[4:6] = self.w4_vccq2.to_bytes(2, 'big')
            b[6:8] = self.w6_vccq.to_bytes(2, 'big')
            return b
    def __init__(self) -> None:
        super().__init__()
        self.upiu:"CmdSeqSwitchVoltage._32B" = self._32B()
        self.w36_wait_queue_empty = False
        self.l32_delay_time = 0
    def compose_entry_buf(self) -> bytearray:
        b = bytearray(72)
        b[0:32] = self.upiu.to_bytes()
        b[32:36] = self.l32_delay_time.to_bytes(4, 'big')
        b[36:38] = bitstruct.pack('u15u1', 0, self.w36_wait_queue_empty)
        return b
    def set_option(self, vcc: int, vccq2: int, vccq: int, wait_queue_empty: bool=False, delay_time: int=0) -> Self:
        """
        e.g.  
        vcc=33000 means 3.30v  
        vccq2=18000 means 1.80v  
        vccq=12000 menas 1.20v  
        """
        self.upiu.w2_vcc = vcc
        self.upiu.w4_vccq2 = vccq2
        self.upiu.w6_vccq = vccq
        self.l32_delay_time = delay_time
        self.w36_wait_queue_empty = wait_queue_empty
        return self

class CmdSeqSwitchReferenceClock(IsEntry):
    class _32B(PacketComposerABC):
        def __init__(self) -> None:
            self.b0_transaction_type = UPIUTransactionType.SDK_CMD
            self.b1_function_code = 0x03
            self.b2_refclk = 0
            self.b3_divca = 0
            self.b4_divm = 0
            self.b5_locktime = 0
        def to_bytes(self) -> bytearray:
            b = bytearray(32)
            b[0] = self.b0_transaction_type
            b[1] = self.b1_function_code
            b[2] = self.b2_refclk
            b[3] = self.b3_divca
            b[4] = self.b4_divm
            b[5] = self.b5_locktime
            return b
    def __init__(self) -> None:
        super().__init__()
        self.upiu: "CmdSeqSwitchReferenceClock._32B" = self._32B()
        self.w36_wait_queue_empty = False
        self.l32_delay_time = 0
    def compose_entry_buf(self) -> bytearray:
        b = bytearray(72)
        b[0:32] = self.upiu.to_bytes()
        b[32:36] = self.l32_delay_time.to_bytes(4, 'big')
        b[36:38] = bitstruct.pack('u15u1', 0, self.w36_wait_queue_empty)
        return b
    def set_option(self, refclk: float = 26.0, wait_queue_empty: bool=True, delay_time: int=0) -> Self:
        refclkstd1 = (19.2 + 26) / 2.0
        refclkstd2 = (26 + 38.4) / 2.0
        refclkstd3 = (38.4 + 52) / 2.0
        refclkstd4 = 52 + (52 / 10.0)

        dest_value = (4 * refclk) / 32.0
        dest_value = math.ceil(dest_value * 100) / 100.0

        if refclk <= refclkstd1:
            set_refclk = 0x6c
        elif refclk <= refclkstd2:
            set_refclk = 0x6d
        elif refclk <= refclkstd3:
            set_refclk = 0x6e
        elif refclk <= refclkstd4:
            set_refclk = 0x6f
        else:
            _log.error(f'Wrong Reference Clock Parameter Fail. {refclk=}')
            raise PATTERN_ASSERT_ILLEGAL_PARAM_BAD_REF_CLK

        found = False
        for divm in range(16, 69):
            for divca in range(1, 16):
                scr_value = float(divm) / float(divca)
                scr_value = math.ceil(scr_value * 100) / 100.0
                if scr_value == dest_value:
                    band = 32 / 1 * divm
                    if band <= 576:
                        locktime = 0x30 | 0x01
                    elif band <= 928:
                        locktime = 0x30 | 0x01
                    elif band <= 1280:
                        locktime = 0x30 | 0x01
                    elif band <= 1728:
                        locktime = 0x30 | 0x01
                    else:
                        _log.error(f'DIVM Wrong Parameter Fail. {divm=}, {divca=}, {scr_value=}, {dest_value=}, {band=}')
                        raise PATTERN_ASSERT_ILLEGAL_PARAM_BAD_DIVM
                    
                    self.upiu.b2_refclk = set_refclk
                    self.upiu.b3_divca = divca
                    self.upiu.b4_divm = divm
                    self.upiu.b5_locktime = locktime

                    found = True
                    break
            if found:
                break

        self.l32_delay_time = delay_time
        self.w36_wait_queue_empty = wait_queue_empty
        return self

class CmdSeqSpeedChange(IsEntry):
    class _32B(PacketComposerABC):
        def __init__(self) -> None:
            self.b0_transaction_type = UPIUTransactionType.SDK_CMD
            self.b1_function_code = 0x04
            self.b2_hs_rate = 0
            self.b3_rx_gear = 0
            self.b3_rx_lane = 0
            self.b3_rx_mode = 0
            self.b4_tx_gear = 0
            self.b4_tx_lane = 0
            self.b4_tx_mode = 0            
            self.w5_fc0_protection_timeout = 0
            self.w7_tc0_replay_timeout = 0
            self.w9_afc0_req_timeout = 0
            self.w11_fc1_protection_timeout = 0
            self.w13_tc1_replay_timeout = 0
            self.w15_afc1_req_timeout = 0
        def to_bytes(self) -> bytearray:
            b = bytearray(32)
            struct.pack_into(
                '>BBBBBHHHHHH', b, 0,
                self.b0_transaction_type,
                self.b1_function_code,
                bitstruct.pack('u4u1u3', 0, self.b2_hs_rate, 0)[0],
                bitstruct.pack('u3u2u3', self.b3_rx_mode, self.b3_rx_lane, self.b3_rx_gear)[0],
                bitstruct.pack('u3u2u3', self.b4_tx_mode, self.b4_tx_lane, self.b4_tx_gear)[0],
                self.w5_fc0_protection_timeout,
                self.w7_tc0_replay_timeout,
                self.w9_afc0_req_timeout,
                self.w11_fc1_protection_timeout,
                self.w13_tc1_replay_timeout,
                self.w15_afc1_req_timeout
            )
            return b
    def __init__(self) -> None:
        super().__init__()
        self.upiu: "CmdSeqSpeedChange._32B" = self._32B()
        self.w36_wait_queue_empty = False
        self.l32_delay_time = 0
    def compose_entry_buf(self) -> bytearray:
        b = bytearray(72)
        b[0:32] = self.upiu.to_bytes()
        b[32:36] = self.l32_delay_time.to_bytes(4, 'big')
        b[36:38] = bitstruct.pack('u15u1', 0, self.w36_wait_queue_empty)
        return b
    def set_option(self, txmode: int = SpdChgPowerMode.FAST, rxmode: int = SpdChgPowerMode.FAST, txgear: int = SpdChgGear.GEAR_3, rxgear: int = SpdChgGear.GEAR_3,
               txlane: int = SpdChgLane.LANE_2, rxlane: int = SpdChgLane.LANE_2, hsrate: int = SpdChgHsRate.RATE_B, fc0protectiontimeout: int = 8191,
               tc0replaytimeout: int = 65535, afc0reqtimeout: int = 32767, fc1protectiontimeout: int = 8191, 
               tc1replaytimeout: int = 65535, afc1reqtimeout: int = 32767, wait_queue_empty: bool=True, delay_time: int=0) -> Self:
        self.upiu.b2_hs_rate = hsrate
        self.upiu.b3_rx_mode = rxmode
        self.upiu.b3_rx_lane = rxlane
        self.upiu.b3_rx_gear = rxgear
        self.upiu.b4_tx_mode = txmode
        self.upiu.b4_tx_lane = txlane
        self.upiu.b4_tx_gear = txgear
        self.upiu.w5_fc0_protection_timeout = fc0protectiontimeout
        self.upiu.w7_tc0_replay_timeout = tc0replaytimeout
        self.upiu.w9_afc0_req_timeout = afc0reqtimeout
        self.upiu.w11_fc1_protection_timeout = fc1protectiontimeout
        self.upiu.w13_tc1_replay_timeout = tc1replaytimeout
        self.upiu.w15_afc1_req_timeout = afc1reqtimeout
        self.l32_delay_time = delay_time
        self.w36_wait_queue_empty = wait_queue_empty
        return self

class CmdSeqInitialFlow(IsEntry):
    class _32B(PacketComposerABC):
        def __init__(self) -> None:
            self.b0_transaction_type = UPIUTransactionType.SDK_CMD
            self.b1_function_code = 0x05
        def to_bytes(self) -> bytearray:
            b = bytearray(32)
            b[0] = self.b0_transaction_type
            b[1] = self.b1_function_code
            return b
    def __init__(self) -> None:
        super().__init__()
        self.upiu: "CmdSeqInitialFlow._32B" = self._32B()
        self.w36_wait_queue_empty = False
        self.l32_delay_time = 0
    def compose_entry_buf(self) -> bytearray:
        b = bytearray(72)
        b[0:32] = self.upiu.to_bytes()
        b[32:36] = self.l32_delay_time.to_bytes(4, 'big')
        b[36:38] = bitstruct.pack('u15u1', 0, self.w36_wait_queue_empty)
        return b
    def set_option(self, wait_queue_empty: bool=True, delay_time: int=0) -> Self:
        self.l32_delay_time = delay_time
        self.w36_wait_queue_empty = wait_queue_empty
        return self

class CmdSeqGpioTrigger(IsEntry):
    class _32B(PacketComposerABC):
        def __init__(self) -> None:
            self.b0_transaction_type = UPIUTransactionType.SDK_CMD
            self.b1_function_code = 0x06
            self.b2_mode = 0
            self.b3_toggle_delay = 0            
        def to_bytes(self) -> bytearray:
            b = bytearray(32)
            b[0] = self.b0_transaction_type
            b[1] = self.b1_function_code
            b[2] = self.b2_mode
            b[3] = self.b3_toggle_delay
            return b
    def __init__(self) -> None:
        super().__init__()
        self.upiu: "CmdSeqGpioTrigger._32B" = self._32B()
        self.w36_wait_queue_empty = False
        self.l32_delay_time = 0
    def compose_entry_buf(self) -> bytearray:
        b = bytearray(72)
        b[0:32] = self.upiu.to_bytes()
        b[32:36] = self.l32_delay_time.to_bytes(4, 'big')
        b[36:38] = bitstruct.pack('u15u1', 0, self.w36_wait_queue_empty)
        return b
    def set_option(self, mode: int, toggle_delay: int, wait_queue_empty: bool=False, delay_time: int=0) -> Self:
        self.upiu.b2_mode = mode
        self.upiu.b3_toggle_delay = toggle_delay
        self.l32_delay_time = delay_time
        self.w36_wait_queue_empty = wait_queue_empty
        return self

class CmdSeqHibernate(IsEntry):
    class _32B(PacketComposerABC):
        def __init__(self) -> None:
            self.b0_transaction_type = UPIUTransactionType.SDK_CMD
            self.b1_function_code = 0x07
            self.b2_hiberopt_enter = 0
            self.b2_hiberopt_exit = 0            
            self.w3_loopcount = 0
            self.l5_delayafterenter = 0
            self.l9_delayafterexit = 0            
        def to_bytes(self) -> bytearray:
            b = bytearray(32)
            struct.pack_into(
                '>BBBHLL', b, 0,
                self.b0_transaction_type,
                self.b1_function_code,
                bitstruct.pack('u6u1u1', 0, self.b2_hiberopt_exit, self.b2_hiberopt_enter)[0],
                self.w3_loopcount,
                self.l5_delayafterenter,
                self.l9_delayafterexit
            )
            return b
    def __init__(self) -> None:
        super().__init__()
        self.upiu: "CmdSeqHibernate._32B" = self._32B()
        self.w36_wait_queue_empty = False
        self.l32_delay_time = 0
    def compose_entry_buf(self) -> bytearray:
        b = bytearray(72)
        b[0:32] = self.upiu.to_bytes()
        b[32:36] = self.l32_delay_time.to_bytes(4, 'big')
        b[36:38] = bitstruct.pack('u15u1', 0, self.w36_wait_queue_empty)
        return b
    def set_option(self, hibernate_enter: int, hibernate_exit: int, loopcount: int, delayafterenter: int, delayafterexit: int, wait_queue_empty: bool=False, delay_time: int=0) -> Self:
        self.upiu.b2_hiberopt_enter = hibernate_enter
        self.upiu.b2_hiberopt_exit = hibernate_exit
        self.upiu.w3_loopcount = loopcount
        self.upiu.l5_delayafterenter = delayafterenter
        self.upiu.l9_delayafterexit = delayafterexit
        self.l32_delay_time = delay_time
        self.w36_wait_queue_empty = wait_queue_empty
        return self

class CmdSeqTestUnitReady(IsEntry):
    class _32B(PacketComposerABC):
        def __init__(self) -> None:
            self.b0_transaction_type = UPIUTransactionType.SDK_CMD
            self.b1_function_code = 0x08
            self.b2_lun = 0
            self.l3_timeout = 0
        def to_bytes(self) -> bytearray:
            b = bytearray(32)
            b[0] = self.b0_transaction_type
            b[1] = self.b1_function_code
            b[2] = self.b2_lun
            b[3:7] = self.l3_timeout.to_bytes(4, 'big')
            return b
    def __init__(self) -> None:
        super().__init__()
        self.upiu: "CmdSeqTestUnitReady._32B" = self._32B()
        self.w36_wait_queue_empty = False
        self.l32_delay_time = 0
    def compose_entry_buf(self) -> bytearray:
        b = bytearray(72)
        b[0:32] = self.upiu.to_bytes()
        b[32:36] = self.l32_delay_time.to_bytes(4, 'big')
        b[36:38] = bitstruct.pack('u15u1', 0, self.w36_wait_queue_empty)
        return b
    def set_option(self, lun: int, timeout: int = 100000, wait_queue_empty: bool=False, delay_time: int=0) -> Self:
        self.upiu.b2_lun = lun
        self.upiu.l3_timeout = timeout
        self.l32_delay_time = delay_time
        self.w36_wait_queue_empty = wait_queue_empty
        return self

class CmdSeqPowerControl(IsEntry):
    class _32B(PacketComposerABC):
        def __init__(self) -> None:
            self.b0_transaction_type = UPIUTransactionType.SDK_CMD
            self.b1_function_code = 0x09
            self.b2_mode = 0
            self.b3_channel = 0
            self.w4_spendtime = 0
            self.w6_ramptime = 0
        def to_bytes(self) -> bytearray:
            b = bytearray(32)
            b[0] = self.b0_transaction_type
            b[1] = self.b1_function_code
            b[2] = self.b2_mode
            b[3] = self.b3_channel
            b[4:6] = self.w4_spendtime.to_bytes(2, 'big')
            b[6:8] = self.w6_ramptime.to_bytes(2, 'big')            
            return b
    def __init__(self) -> None:
        super().__init__()
        self.upiu: "CmdSeqPowerControl._32B" = self._32B()
        self.w36_wait_queue_empty = False
        self.l32_delay_time = 0
    def compose_entry_buf(self) -> bytearray:
        b = bytearray(72)
        b[0:32] = self.upiu.to_bytes()
        b[32:36] = self.l32_delay_time.to_bytes(4, 'big')
        b[36:38] = bitstruct.pack('u15u1', 0, self.w36_wait_queue_empty)
        return b
    def set_option(self, mode: int, channel: int, spendtime: int, ramptime: int, wait_queue_empty: bool=False, delay_time: int=0) -> Self:
        self.upiu.b2_mode = mode
        self.upiu.b3_channel = channel
        self.upiu.w4_spendtime = spendtime
        self.upiu.w6_ramptime = ramptime
        self.l32_delay_time = delay_time
        self.w36_wait_queue_empty = wait_queue_empty
        return self

class CmdSeqReadyDeviceInitFlag(IsEntry):
    class _32B(PacketComposerABC):
        def __init__(self) -> None:
            self.b0_transaction_type = UPIUTransactionType.SDK_CMD
            self.b1_function_code = 0x0A
        def to_bytes(self) -> bytearray:
            b = bytearray(32)
            b[0] = self.b0_transaction_type
            b[1] = self.b1_function_code      
            return b
    def __init__(self) -> None:
        super().__init__()
        self.upiu: "CmdSeqReadyDeviceInitFlag._32B" = self._32B()
        self.w36_wait_queue_empty = False
        self.l32_delay_time = 0
    def compose_entry_buf(self) -> bytearray:
        b = bytearray(72)
        b[0:32] = self.upiu.to_bytes()
        b[32:36] = self.l32_delay_time.to_bytes(4, 'big')
        b[36:38] = bitstruct.pack('u15u1', 0, self.w36_wait_queue_empty)
        return b
    def set_option(self, wait_queue_empty: bool=False, delay_time: int=0) -> Self:
        self.l32_delay_time = delay_time
        self.w36_wait_queue_empty = wait_queue_empty
        return self

class CmdSeqPushNopOutPollNopIn(IsEntry):
    class _32B(PacketComposerABC):
        def __init__(self) -> None:
            self.b0_transaction_type = UPIUTransactionType.SDK_CMD
            self.b1_function_code = 0x0B
            self.l2_timeout = 0
        def to_bytes(self) -> bytearray:
            b = bytearray(32)
            b[0] = self.b0_transaction_type
            b[1] = self.b1_function_code
            b[2:6] = self.l2_timeout.to_bytes(4, 'big')
            return b
    def __init__(self) -> None:
        super().__init__()
        self.upiu: "CmdSeqPushNopOutPollNopIn._32B" = self._32B()
        self.w36_wait_queue_empty = False
        self.l32_delay_time = 0
    def compose_entry_buf(self) -> bytearray:
        b = bytearray(72)
        b[0:32] = self.upiu.to_bytes()
        b[32:36] = self.l32_delay_time.to_bytes(4, 'big')
        b[36:38] = bitstruct.pack('u15u1', 0, self.w36_wait_queue_empty)
        return b
    def set_option(self, timeout: int, wait_queue_empty: bool=False, delay_time: int=0) -> Self:
        self.upiu.l2_timeout = timeout
        self.l32_delay_time = delay_time
        self.w36_wait_queue_empty = wait_queue_empty
        return self

############### Tester Commands end ###############
