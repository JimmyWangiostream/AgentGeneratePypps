import struct
import bitstruct
import Script.api.shared as shared
from .dcmd_enum import Dcmd, Dcmd7Status
from Script import api

_sdk = shared.sdk
_log = shared.logging


class set_dcmd13_arg():
    def __init__(self) -> None:
        self._feature_setup = 0
        self._no_timeout_active = 0
        self._rsvd = 0

    @property
    def feature_setup(self) -> int:
        return self._feature_setup

    @feature_setup.setter
    def feature_setup(self, value: int) -> None:
        if value not in [0, 1]:
            raise ValueError("feature_setup must be a single bit (0 or 1)")
        self._feature_setup = value

    @property
    def no_timeout_active(self) -> int:
        return self._no_timeout_active

    @no_timeout_active.setter
    def no_timeout_active(self, value: int) -> None:
        if value < 0 or value > 8:
            raise ValueError("no_timeout_active must be a single bit (0 or 1)")
        self._no_timeout_active = value

    def to_bytearray(self) -> bytearray:
        buf = bytearray(2)
        struct.pack_into(
            "<BB", buf, 0,
            self._feature_setup,
            self._no_timeout_active
        )
        return buf

class set_dcmd13_data():
    def __init__(self) -> None:
        self._standard_cmd = 0
        self._vendor_cmd = 0
        self._group_rw = 0
        self._nop_out = 0
        self._hiber_enter = 0
        self._hiber_exit = 0
        self._linkstartup_tx_fsm = 0
        self._pwr_mode_chg = 0
        self._current_timeout_0 = 0
        self._first_read_lun_ready_timeout = 0
        self._boot_lun_ready_timeout = 0
        self._fdev_init_timeout = 0
        self._rstn_afterpwrreset_delay = 0
        self._rstn_sendkey_timeout = 0
        self._rstn_authcmd_timeout = 0
        self._rstn_authdata_timeout = 0
        self._all_timeout_multiplenum = 0
        self._ssu_timeout = 0
        self._dcmd10_process1_timeout = 0
        self._hpb_reset_timeout = 0
        self._linkstartup_poweron_req_timeout = 0   # only for v4
        self._linkstartup_reset_req_timeout = 0   # only for v4
        self._linkstartup_enable_req_timeout = 0   # only for v4
        self._linkstartup_linkup_req_timeout = 0   # only for v4
        self._linkstartup_hwlinkup_polling_timeout = 0  # only for v6

    @property
    def standard_cmd(self) -> int:
        return self._standard_cmd

    @standard_cmd.setter
    def standard_cmd(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("standard_cmd must be a 4-byte value (0-4294967295)")
        self._standard_cmd = value
    
    @property
    def vendor_cmd(self) -> int:
        return self._vendor_cmd

    @vendor_cmd.setter
    def vendor_cmd(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("vendor_cmd must be a 4-byte value (0-4294967295)")
        self._vendor_cmd = value

    @property
    def group_rw(self) -> int:
        return self._group_rw

    @group_rw.setter
    def group_rw(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("group_rw must be a 4-byte value (0-4294967295)")
        self._group_rw = value

    @property
    def nop_out(self) -> int:
        return self._nop_out

    @nop_out.setter
    def nop_out(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("nop_out must be a 4-byte value (0-4294967295)")
        self._nop_out = value

    @property
    def hiber_enter(self) -> int:
        return self._hiber_enter

    @hiber_enter.setter
    def hiber_enter(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("hiber_enter must be a 4-byte value (0-4294967295)")
        self._hiber_enter = value

    @property
    def hiber_exit(self) -> int:
        return self._hiber_exit

    @hiber_exit.setter
    def hiber_exit(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("hiber_exit must be a 4-byte value (0-4294967295)")
        self._hiber_exit = value

    @property
    def linkstartup_tx_fsm(self) -> int:
        return self._linkstartup_tx_fsm

    @linkstartup_tx_fsm.setter
    def linkstartup_tx_fsm(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("linkstartup_tx_fsm must be a 4-byte value (0-4294967295)")
        self._linkstartup_tx_fsm = value

    @property
    def pwr_mode_chg(self) -> int:
        return self._pwr_mode_chg

    @pwr_mode_chg.setter
    def pwr_mode_chg(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("pwr_mode_chg must be a 4-byte value (0-4294967295)")
        self._pwr_mode_chg = value

    @property
    def current_timeout_0(self) -> int:
        return self._current_timeout_0

    @current_timeout_0.setter
    def current_timeout_0(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("current_timeout_0 must be a 4-byte value (0-4294967295)")
        self._current_timeout_0 = value

    @property
    def first_read_lun_ready_timeout(self) -> int:
        return self._first_read_lun_ready_timeout

    @first_read_lun_ready_timeout.setter
    def first_read_lun_ready_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("_1st_read_lun_ready_timeout must be a 4-byte value (0-4294967295)")
        self._first_read_lun_ready_timeout = value

    @property
    def boot_lun_ready_timeout(self) -> int:
        return self._boot_lun_ready_timeout

    @boot_lun_ready_timeout.setter
    def boot_lun_ready_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("boot_lun_ready_timeout must be a 4-byte value (0-4294967295)")
        self._boot_lun_ready_timeout = value

    @property
    def fdev_init_timeout(self) -> int:
        return self._fdev_init_timeout

    @fdev_init_timeout.setter
    def fdev_init_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("fdev_init_timeout must be a 4-byte value (0-4294967295)")
        self._fdev_init_timeout = value

    @property
    def rstn_afterpwrreset_delay(self) -> int:
        return self._rstn_afterpwrreset_delay

    @rstn_afterpwrreset_delay.setter
    def rstn_afterpwrreset_delay(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("rstn_afterpwrreset_delay must be a 4-byte value (0-4294967295)")
        self._rstn_afterpwrreset_delay = value

    @property
    def rstn_sendkey_timeout(self) -> int:
        return self._rstn_sendkey_timeout

    @rstn_sendkey_timeout.setter
    def rstn_sendkey_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("rstn_sendkey_timeout must be a 4-byte value (0-4294967295)")
        self._rstn_sendkey_timeout = value

    @property
    def rstn_authcmd_timeout(self) -> int:
        return self._rstn_authcmd_timeout

    @rstn_authcmd_timeout.setter
    def rstn_authcmd_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("rstn_authcmd_timeout must be a 4-byte value (0-4294967295)")
        self._rstn_authcmd_timeout = value

    @property
    def rstn_authdata_timeout(self) -> int:
        return self._rstn_authdata_timeout

    @rstn_authdata_timeout.setter
    def rstn_authdata_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("rstn_authdata_timeout must be a 4-byte value (0-4294967295)")
        self._rstn_authdata_timeout = value

    @property
    def all_timeout_multiplenum(self) -> int:
        return self._all_timeout_multiplenum

    @all_timeout_multiplenum.setter
    def all_timeout_multiplenum(self, value: int) -> None:
        if value < 0 or value > 0xFF:
            raise ValueError("all_timeout_multiplenum must be a 1-byte value (0-256)")
        self._all_timeout_multiplenum = value

    @property
    def ssu_timeout(self) -> int:
        return self._ssu_timeout

    @ssu_timeout.setter
    def ssu_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("ssu_timeout must be a 4-byte value (0-4294967295)")
        self._ssu_timeout = value

    @property
    def dcmd10_process1_timeout(self) -> int:
        return self._dcmd10_process1_timeout

    @dcmd10_process1_timeout.setter
    def dcmd10_process1_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("dcmd10_process1_timeout must be a 4-byte value (0-4294967295)")
        self._dcmd10_process1_timeout = value

    @property
    def hpb_reset_timeout(self) -> int:
        return self._hpb_reset_timeout

    @hpb_reset_timeout.setter
    def hpb_reset_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("hpb_reset_timeout must be a 4-byte value (0-4294967295)")
        self._hpb_reset_timeout = value

    @property
    def linkstartup_poweron_req_timeout(self) -> int:
        return self._linkstartup_poweron_req_timeout

    @linkstartup_poweron_req_timeout.setter
    def linkstartup_poweron_req_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("linkstartup_poweron_req_timeout must be a 4-byte value (0-4294967295)")
        self._linkstartup_poweron_req_timeout = value

    @property
    def linkstartup_reset_req_timeout(self) -> int:
        return self._linkstartup_reset_req_timeout

    @linkstartup_reset_req_timeout.setter
    def linkstartup_reset_req_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("linkstartup_reset_req_timeout must be a 4-byte value (0-4294967295)")
        self._linkstartup_reset_req_timeout = value

    @property
    def linkstartup_enable_req_timeout(self) -> int:
        return self._linkstartup_enable_req_timeout

    @linkstartup_enable_req_timeout.setter
    def linkstartup_enable_req_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("linkstartup_enable_req_timeout must be a 4-byte value (0-4294967295)")
        self._linkstartup_enable_req_timeout = value

    @property
    def linkstartup_linkup_req_timeout(self) -> int:
        return self._linkstartup_linkup_req_timeout

    @linkstartup_linkup_req_timeout.setter
    def linkstartup_linkup_req_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("linkstartup_linkup_req_timeout must be a 4-byte value (0-4294967295)")
        self._linkstartup_linkup_req_timeout = value

    @property
    def linkstartup_hwlinkup_polling_timeout(self) -> int:
        return self._linkstartup_hwlinkup_polling_timeout

    @linkstartup_hwlinkup_polling_timeout.setter
    def linkstartup_hwlinkup_polling_timeout(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("linkstartup_hwlinkup_polling_timeout must be a 4-byte value (0-4294967295)")
        self._linkstartup_hwlinkup_polling_timeout = value
    
    def to_bytearray(self) -> bytearray:
        buf = bytearray(97)
        struct.pack_into(
            ">LLLLLLLLLLLLLLLLBLLLLLLLL", buf, 0,
            self.standard_cmd,
            self.vendor_cmd,
            self.group_rw,
            self.nop_out,
            self.hiber_enter,
            self.hiber_exit,
            self.linkstartup_tx_fsm,
            self.pwr_mode_chg,
            self.current_timeout_0,
            self.first_read_lun_ready_timeout,
            self.boot_lun_ready_timeout,
            self.fdev_init_timeout,
            self.rstn_afterpwrreset_delay,
            self.rstn_sendkey_timeout,
            self.rstn_authcmd_timeout,
            self.rstn_authdata_timeout,
            self.all_timeout_multiplenum,
            self.ssu_timeout,
            self.dcmd10_process1_timeout,
            self.hpb_reset_timeout,
            self.linkstartup_poweron_req_timeout,
            self.linkstartup_reset_req_timeout,
            self.linkstartup_enable_req_timeout,
            self.linkstartup_linkup_req_timeout,
            self.linkstartup_hwlinkup_polling_timeout
        )
        return buf

class dcmd13_info_buf():
    def __init__(self, info_buf: bytearray | None=None):
        self.standard_cmd = 0
        self.vendor_cmd = 0
        self.group_rw = 0
        self.nop_out = 0
        self.hiber_enter = 0
        self.hiber_exit = 0
        self.linkstartup_tx_fsm = 0
        self.pwr_mode_chg = 0
        self.current_timeout_0 = 0
        self.first_read_lun_ready_timeout = 0
        self.boot_lun_ready_timeout = 0
        self.fdev_init_timeout = 0
        self.rstn_afterpwrreset_delay = 0
        self.rstn_sendkey_timeout = 0
        self.rstn_authcmd_timeout = 0
        self.rstn_authdata_timeout = 0
        self.all_timeout_multiplenum = 0
        self.ssu_timeout = 0
        self.dcmd10_process1_timeout = 0
        self.hpb_reset_timeout = 0
        self.linkstartup_poweron_req_timeout = 0
        self.linkstartup_reset_req_timeout = 0
        self.linkstartup_enable_req_timeout = 0
        self.linkstartup_linkup_req_timeout = 0

        if info_buf:
            self.from_bytearray(info_buf)
    
    def from_bytearray(self, info_buf: bytearray) -> None:
        if len(info_buf) < 97:
            raise ValueError("info_buf is too short. Expected at least 96 bytes.")

        self.standard_cmd = int.from_bytes(info_buf[0:4], byteorder='big')
        self.vendor_cmd = int.from_bytes(info_buf[4:8], byteorder='big')
        self.group_rw = int.from_bytes(info_buf[8:12], byteorder='big')
        self.nop_out = int.from_bytes(info_buf[12:16], byteorder='big')
        self.hiber_enter = int.from_bytes(info_buf[16:20], byteorder='big')
        self.hiber_exit = int.from_bytes(info_buf[20:24], byteorder='big')
        self.linkstartup_tx_fsm = int.from_bytes(info_buf[24:28], byteorder='big')
        self.pwr_mode_chg = int.from_bytes(info_buf[28:32], byteorder='big')
        self.current_timeout_0 = int.from_bytes(info_buf[32:36], byteorder='big')
        self.first_read_lun_ready_timeout = int.from_bytes(info_buf[36:40], byteorder='big')
        self.boot_lun_ready_timeout = int.from_bytes(info_buf[40:44], byteorder='big')
        self.fdev_init_timeout = int.from_bytes(info_buf[44:48], byteorder='big')
        self.rstn_afterpwrreset_delay = int.from_bytes(info_buf[48:52], byteorder='big')
        self.rstn_sendkey_timeout = int.from_bytes(info_buf[52:56], byteorder='big')
        self.rstn_authcmd_timeout = int.from_bytes(info_buf[56:60], byteorder='big')
        self.rstn_authdata_timeout = int.from_bytes(info_buf[60:64], byteorder='big')
        self.all_timeout_multiplenum = info_buf[64]
        self.ssu_timeout = int.from_bytes(info_buf[65:69], byteorder='big')
        self.dcmd10_process1_timeout = int.from_bytes(info_buf[69:73], byteorder='big')
        self.hpb_reset_timeout = int.from_bytes(info_buf[73:77], byteorder='big')
        self.linkstartup_poweron_req_timeout = int.from_bytes(info_buf[77:81], byteorder='big')
        self.linkstartup_reset_req_timeout = int.from_bytes(info_buf[81:85], byteorder='big')
        self.linkstartup_enable_req_timeout = int.from_bytes(info_buf[85:89], byteorder='big')
        self.linkstartup_linkup_req_timeout = int.from_bytes(info_buf[89:93], byteorder='big')

def set_debug_cmd13(arg: set_dcmd13_arg, data: set_dcmd13_data, timeout: int) -> None:
    _log.debug("_set_debug_cmd")
    arg_buf = arg.to_bytearray()
    data_buf = data.to_bytearray()

    _sdk.set_debug_cmd(Dcmd.DCMD13_TIMEOUT_SETTING, arg_buf, timeout, data_buf)

def get_debug_cmd13() -> dcmd13_info_buf:
    _log.debug("_get_debug_cmd")
    buf = _sdk.get_debug_cmd(Dcmd.DCMD13_TIMEOUT_SETTING)
    info_buf = dcmd13_info_buf(buf)

    return info_buf