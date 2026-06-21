import struct
import bitstruct
import Script.api.shared as shared
from .dcmd_enum import Dcmd, Dcmd9Status
from Script import api

_sdk = shared.sdk
_log = shared.logging


class set_dcmd9_arg():
    def __init__(self) -> None:
        self._set_purge_flag = 0
        self._rsvd = 0
        self._reset_type = 0
        self._rsvd1 = 0
        self._detect_time = 0
        self._escape_time = 0

    @property
    def set_purge_flag(self) -> int:
        return self._set_purge_flag

    @set_purge_flag.setter
    def set_purge_flag(self, value: int) -> None:
        if value not in [0, 1]:
            raise ValueError("set_purge_flag must be a single bit (0 or 1)")
        self._set_purge_flag = value

    @property
    def reset_type(self) -> int:
        return self._reset_type

    @reset_type.setter
    def reset_type(self, value: int) -> None:
        if value not in [0, 1, 2, 3]:
            raise ValueError("reset_type must be a 2 bits (0-3)")
        self._reset_type = value
    
    @property
    def detect_time(self) -> int:
        return self._detect_time

    @detect_time.setter
    def detect_time(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("detect_time must be a 4-byte value (0-4294967295)")
        self._detect_time = value

    @property
    def escape_time(self) -> int:
        return self._escape_time

    @escape_time.setter
    def escape_time(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("escape_time must be a 4-byte value (0-4294967295)")
        self._escape_time = value

    def to_bytearray(self) -> bytearray:
        buf = bytearray(9)
        struct.pack_into(
            "<BLL", buf, 0,
            bitstruct.pack('u1u2u4u1', self._rsvd1, self._reset_type, self._rsvd, self._set_purge_flag)[0],
            self._detect_time,
            self._escape_time
        )
        return buf

class dcmd9_info_buf():
    def __init__(self, info_buf: bytearray | None=None):
        self.status = 0
        self.interrupt_status = 0
        self.purge_status = 0

        if info_buf:
            self.from_bytearray(info_buf)
    
    def from_bytearray(self, info_buf: bytearray) -> None:
        if len(info_buf) < 3:
            raise ValueError("info_buf is too short. Expected at least 3 bytes.")

        self.status = info_buf[0]
        self.interrupt_status = info_buf[1]
        self.purge_status = info_buf[2]

def set_debug_cmd9(arg: set_dcmd9_arg, timeout: int) -> None:
    _log.debug("_set_debug_cmd")
    arg_buf = arg.to_bytearray()
    data_buf = bytearray(0)

    _sdk.set_debug_cmd(Dcmd.DCMD9_PURGE_SPOR_DEBUG, arg_buf, timeout, data_buf)

def get_debug_cmd9() -> dcmd9_info_buf:
    _log.debug("_get_debug_cmd")
    buf = _sdk.get_debug_cmd(Dcmd.DCMD9_PURGE_SPOR_DEBUG)
    info_buf = dcmd9_info_buf(buf)

    # if info_buf.status != Dcmd9Status.SPOR_PASS:
    #     if info_buf.status == Dcmd9Status.SKIP_SPOR_DUE_TO_READ_ATTRIBUTE_ERROR:
    #         raise api.DCMD9_SKIP_SPOR_DUE_TO_READ_ATTRIBUTE_ERROR
    #     elif info_buf.status == Dcmd9Status.SKIP_SPOR_DUE_TO_PURGE_STATUS_GREATER_EQUAL_2:
    #         raise api.DCMD9_SKIP_SPOR_DUE_TO_PURGE_STATUS_GREATER_EQUAL_2
    #     elif info_buf.status == Dcmd9Status.SKIP_SPOR_DUE_TO_IDLE:
    #         raise api.DCMD9_SKIP_SPOR_DUE_TO_IDLE
    #     elif info_buf.status == Dcmd9Status.END_POINT_RESET_OR_UNIPRO_RESET_FAIL:
    #         raise api.DCMD9_END_POINT_RESET_OR_UNIPRO_RESET_FAIL
    #     elif info_buf.status == Dcmd9Status.TIMEOUT:
    #         raise api.DCMD9_TIMEOUT
    #     elif info_buf.status == Dcmd9Status.SET_PURGE_FLAG_FAIL:
    #         raise api.DCMD9_SET_PURGE_FLAG_FAIL
           
    return info_buf