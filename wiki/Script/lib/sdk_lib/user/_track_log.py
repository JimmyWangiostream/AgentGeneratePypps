from ._sdk_base import _SDKLibProtocol
from .. import _hal
from enum import Enum

class SDKTrackListItem(Enum):
    USB_CDB_LIST = 0
    SEND_CMD_LIST = 1
    RESPONSE_LIST = 2

class SdkTrackList0:
    def __init__(self):
        self.usb_scsi_cdb = bytearray(16)
        self.time_stamp = 0
        self.time_seq_num = 0
        self.reserved = bytearray(7)

class SdkTrackList1:
    def __init__(self):
        self.cmd_upiu = bytearray(32)
        self.time_stamp = 0
        self.ptng_ctrl = 0
        self.ptng_cfg = 0
        self.rand_seed_h = 0
        self.rand_seed_l = 0
        self.reserved = bytearray(14)

class SdkTrackList2:
    def __init__(self):
        self.resp_upiu = bytearray(52)
        self.time_stamp = 0
        self.crc32_0 = 0
        self.crc32_1 = 0

class SdkTrackActivateArgs:
    def __init__(self):
        self.activate_cmd = False
        self.activate_resp = False
        self.activate_unipro = False
        self.activate_host = False
        self.activate_usb = False
        self.activate_latency = False
        self.activate_group_rw = False
        self.activate_cmd_seq = False
        self.activate_perfc = False

class _SDKLibTrackLogMixin(_SDKLibProtocol):
    def sdk_track_activate(self, arg: SdkTrackActivateArgs):
        arg_buf = bytearray(512)

        # convert flag to 0 or 1
        arg_buf[0] = int(arg.activate_cmd)
        arg_buf[1] = int(arg.activate_resp)
        arg_buf[2] = int(arg.activate_unipro)
        arg_buf[3] = int(arg.activate_host)
        arg_buf[4] = int(arg.activate_usb)
        arg_buf[5] = int(arg.activate_latency)
        arg_buf[6] = int(arg.activate_group_rw)
        arg_buf[7] = int(arg.activate_cmd_seq)
        arg_buf[8] = int(arg.activate_perfc)

        _hal.sdk_track_activate(self._dll, arg_buf)

    def sdk_track_reset(self):
        _hal.sdk_track_reset(self._dll)

    def sdk_track_result(self) -> bytearray:
        """alawys dump info after call api
        """
        return _hal.sdk_track_result(self._dll) 

    def sdk_track_list(self, item: bytes, time_stamp_start: int, time_stamp_end: int) -> tuple[int, bytearray]:
        assert 0 <= item <= 2, "item need select 0~2"
        return _hal.sdk_track_list(self._dll, item, time_stamp_start, time_stamp_end)

    def sdk_track_parsing(self) -> bytearray:
        return _hal.sdk_track_parsing(self._dll)
    
    def sdk_track_log(self, log_str: str, print_on_console_en: int, log_type: int):
        _hal.print_log_sdk(self._dll, log_str, print_on_console_en, log_type)

    def print_buffer_sdk(self, data_buf: bytearray, length: int, col_length: int, print_on_console_en: int, log_type: int):
        _hal.print_buffer_sdk(self._dll, data_buf, length, col_length, print_on_console_en, log_type)

    def log_fa_setting(self, log_setting: int, str_folder_name: str, str_file_name: str, log_line: int):
        _hal.log_fa_setting(self._dll, log_setting, str_folder_name, str_file_name, log_line)

    def log_fa_dump(self):
        _hal.log_fa_dump(self._dll)

    def log_setting(self, log_setting: int, str_folder_name: str, str_file_name: str):
        _hal.log_setting(self._dll, log_setting, str_folder_name, str_file_name)