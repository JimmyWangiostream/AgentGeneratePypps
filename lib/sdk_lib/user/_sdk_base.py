from enum import Enum
import functools
from typing import Protocol
from . import exception
from .. import _hal

class _SDKLibProtocol(Protocol):
    drive: int
    _dll: _hal.Dll

class ResponseInfo:
    class ErrorCategory(Enum):
        PASS = 0x0
        HW_FAIL = 0x1
        CMD_FAIL = 0x2
        WRITE_READ_DATA_FAIL = 0x3
        SCSI_FAIL = 0x4
        TESTER_FAIL = 0x5
        GROUP_WR_FAIL = 0x6
        SPI_MODE_FAIL = 0x9

    def __init__(self, buffer: bytearray):
        self.buffer = buffer

    @property
    def status_info(self) -> bytearray:
        return self.buffer[200:216]
    
    @property
    def is_clk_pin_high(self) -> bool:
        return bool(self.buffer[253] & 0x1)
    
    @property
    def is_cmd_pin_high(self) -> bool:
        return bool(self.buffer[253] & 0x2)
    
    @property
    def error_code_category(self) -> ErrorCategory:
        try:
            return self.ErrorCategory(self.buffer[256])
        except ValueError as e:
            raise ValueError(f"Undefined error code category: buffer[256] = {self.buffer[256]}") from e
    
    @property
    def error_code_exception(self) -> type[exception.CommonLibErrorBase] | None:
        """Check SDK error code and return the corresponding exception. Return None if error code is not set."""
        if self.error_code_category == self.ErrorCategory.PASS:
            return None
        
        key = (self.error_code_category, self.buffer[257])
        table = {
            # hw
            (self.ErrorCategory.HW_FAIL, 0x1): exception.DUT_NOT_DETECT,
            (self.ErrorCategory.HW_FAIL, 0x2): exception.POWER_SHORT,
            (self.ErrorCategory.HW_FAIL, 0x3): exception.USB_RESET,
            # cmd
            (self.ErrorCategory.CMD_FAIL, 0x1): exception.CMD_R1B_TIMEOUT,
            (self.ErrorCategory.CMD_FAIL, 0x2): exception.CMD_AND_WAIT_TRANS_STATE_ERROR,
            (self.ErrorCategory.CMD_FAIL, 0x3): exception.CMD_CRC7_ERROR,
            (self.ErrorCategory.CMD_FAIL, 0x4): exception.CMD_NO_RESP,
            (self.ErrorCategory.CMD_FAIL, 0x5): exception.CMD_INDEX_OF_R2R3_ERROR,
            (self.ErrorCategory.CMD_FAIL, 0x6): exception.CMD1_NO_RESP,
            (self.ErrorCategory.CMD_FAIL, 0x7): exception.CMD_RESP_ERROR,
            (self.ErrorCategory.CMD_FAIL, 0x8): exception.CMD1_TIMEOUT,
            (self.ErrorCategory.CMD_FAIL, 0x9): exception.CMD8_ERROR,
        }
        exc = table.get(key, exception.SDK_UNDEFINED_ERROR)
        return exc
    
    @property
    def r1_response(self) -> int:
        return int.from_bytes(self.buffer[397:401], byteorder="big")  
    

def _get_response_info(dll: _hal.Dll, drive: int) -> ResponseInfo:
    resp_buf = _hal.get_response_info(dll, drive)
    resp_info = ResponseInfo(resp_buf)
    return resp_info

def _try_get_sdk_error_message(dll: _hal.Dll, drive: int) -> str:
    try:
        errmsg = _hal.sdk_error_message(dll, drive)
        return errmsg
    except Exception:
        return ""


def explain_dll_error(sdk_method):
    """
    Explain DLL error: Catch `DLL_ERROR` and replace it by an user-friendly exception.
    """
    @functools.wraps(sdk_method)
    def wrapper(self: _SDKLibProtocol, *args, **kwargs):
        try:
            ret = sdk_method(self, *args, **kwargs)
            return ret
        except exception.DLL_ERROR as e:
            resp_info = _get_response_info(self._dll, self.drive)
            exc = resp_info.error_code_exception
            if exc is None:
                raise exception.SDK_UNDEFINED_ERROR("SDK failed but no error code.")
            else:
                errmsg = _try_get_sdk_error_message(self._dll, self.drive)
                print("ERROR MSG: ", errmsg)
                raise exc(str(e)) from None   # DLL_ERROR is not needed anymore
    return wrapper

def swap_endian(num, length):
    """
    Swap the byte order of an integer.

    :param num: The integer to convert
    :param length: The byte length of the integer
    :return: The converted integer
    """
    # Convert the integer to a little-endian byte sequence
    byte_array = num.to_bytes(length, byteorder='little')
    
    # Reverse the byte sequence to get a big-endian byte sequence
    swapped_byte_array = byte_array[::-1]
    
    # Convert the reversed byte sequence back to an integer, using little-endian
    return int.from_bytes(swapped_byte_array, byteorder='little')

        