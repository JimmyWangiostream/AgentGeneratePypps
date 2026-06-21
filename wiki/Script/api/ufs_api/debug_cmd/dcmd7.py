import struct
import bitstruct
import Script.api.shared as shared
from .dcmd_enum import Dcmd, Dcmd7Status
from Script import api

_sdk = shared.sdk
_log = shared.logging


class set_dcmd7_arg():
    def __init__(self) -> None:
        self._activate = 0
        self._detect_type = 0
        self._reset_type = 0
        self._power_on = 0
        self._detect_time = 0
        self._rsvd = 0
        self._enhance = 0
        self._first_step = 0
        self._second_step = 0
        self._rsvd2 = 0
        self._gap_time = 0
        self._response_detect_count = 0
        self._response_detect_delay_time = 0

    @property
    def activate(self) -> int:
        return self._activate

    @activate.setter
    def activate(self, value: int) -> None:
        if value not in [0, 1]:
            raise ValueError("activate must be a single bit (0 or 1)")
        self._activate = value

    @property
    def detect_type(self) -> int:
        return self._detect_type

    @detect_type.setter
    def detect_type(self, value: int) -> None:
        if value < 0 or value > 8:
            raise ValueError("detect_type must be a 4 bits (0-8)")
        self._detect_type = value

    @property
    def reset_type(self) -> int:
        return self._reset_type

    @reset_type.setter
    def reset_type(self, value: int) -> None:
        if value not in [0, 1, 2, 3]:
            raise ValueError("reset_type must be a 2 bits (0-3)")
        self._reset_type = value

    @property
    def power_on(self) -> int:
        return self._power_on

    @power_on.setter
    def power_on(self, value: int) -> None:
        if value not in [0, 1]:
            raise ValueError("power_on must be a single bit (0 or 1)")
        self._power_on = value
    
    @property
    def detect_time(self) -> int:
        return self._detect_time

    @detect_time.setter
    def detect_time(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("detect_time must be a 4-byte value (0-4294967295)")
        self._detect_time = value

    @property
    def enhance(self) -> int:
        return self._enhance

    @enhance.setter
    def enhance(self, value: int) -> None:
        if value not in [0, 1]:
            raise ValueError("enhance must be a single bit (0 or 1)")
        self._enhance = value

    @property
    def first_step(self) -> int:
        return self._first_step

    @first_step.setter
    def first_step(self, value: int) -> None:
        if value not in [1, 2]:
            raise ValueError("first_step must be a 2 bits (1-2)")
        self._first_step = value

    @property
    def second_step(self) -> int:
        return self._second_step

    @second_step.setter
    def second_step(self, value: int) -> None:
        if value not in [0, 1]:
            raise ValueError("second_step must be a 2 bits (0-1)")
        self._second_step = value

    @property
    def gap_time(self) -> int:
        return self._gap_time

    @gap_time.setter
    def gap_time(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("gap_time must be a 4-byte value (0-4294967295)")
        self._gap_time = value

    @property
    def response_detect_count(self) -> int:
        return self._response_detect_count

    @response_detect_count.setter
    def response_detect_count(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("response_detect_count must be a 4-byte value (0-4294967295)")
        self._response_detect_count = value

    @property
    def response_detect_delay_time(self) -> int:
        return self._response_detect_delay_time

    @response_detect_delay_time.setter
    def response_detect_delay_time(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("response_detect_count must be a 4-byte value (0-4294967295)")
        self._response_detect_delay_time = value

    def to_bytearray(self) -> bytearray:
        buf = bytearray(19)
        struct.pack_into(
            "<BLBBLLL", buf, 0,
            bitstruct.pack('u1u2u4u1', self._power_on, self._reset_type, self._detect_type, self._activate)[0],
            self._detect_time,
            self._rsvd,
            bitstruct.pack('u3u2u2u1', self._rsvd2, self._second_step, self._first_step, self._enhance)[0],
            self._gap_time,
            self._response_detect_count,
            self._response_detect_delay_time
        )
        return buf

        # byte1 = (self._activate << 0) | (self._detect_type << 1) | (self._reset_type << 5) | (self._power_on << 7) 
        # byte2 = (self._enhance << 0) | (self._first_step << 1) | (self._second_step << 3) | (self._rsvd2 << 5) 

        # return bytearray(struct.pack('<BLBBLLL', byte1, self._detect_time, self._rsvd, byte2, self._gap_time, self._response_detect_count, self._response_detect_delay_time))
  
class dcmd7_info_buf():
    def __init__(self, info_buf: bytearray | None=None):
        self.status = 0
        self.interrupt_status = 0
        self.vcc_state = 0
        self.vccq_state = 0
        self.vccq2_state = 0
        self.sim_power_count_buff = 0
        self.sim_power_spor_case_index = 0
        self.sim_power_spor_time = 0
        self.generic_error_code = 0

        if info_buf:
            self.from_bytearray(info_buf)
    
    def from_bytearray(self, info_buf: bytearray) -> None:
        if len(info_buf) < 310:
            raise ValueError("info_buf is too short. Expected at least 309 bytes.")

        self.status = info_buf[0]
        self.interrupt_status = info_buf[1]
        self.vcc_state = info_buf[2]
        self.vccq_state = info_buf[3]
        self.vccq2_state = info_buf[4]
        self.sim_power_count_buff = int.from_bytes(info_buf[5:305], byteorder='big')
        self.sim_power_spor_case_index = int.from_bytes(info_buf[305:307], byteorder='big')
        self.sim_power_spor_time = int.from_bytes(info_buf[307:309], byteorder='big')
        self.generic_error_code = info_buf[309]

def set_debug_cmd7(arg: set_dcmd7_arg, timeout: int) -> None:
    _log.debug("_set_debug_cmd")
    arg_buf = arg.to_bytearray()
    data_buf = bytearray(0)

    _sdk.set_debug_cmd(Dcmd.DCMD7_INTERRUPT_DEBUG, arg_buf, timeout, data_buf)

def get_debug_cmd7() -> dcmd7_info_buf:
    _log.debug("_get_debug_cmd")
    buf = _sdk.get_debug_cmd(Dcmd.DCMD7_INTERRUPT_DEBUG)
    info_buf = dcmd7_info_buf(buf)

    if info_buf.status != Dcmd7Status.PASS:
        raise api.DCMD7_FAIL
    else:        
        return info_buf