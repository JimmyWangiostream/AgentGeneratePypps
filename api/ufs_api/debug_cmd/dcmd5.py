from dataclasses import dataclass
import struct
import Script.api.shared as shared
from Script import api
from Script.api.ufs_api.debug_cmd.dcmd_enum import Dcmd, Dcmd5Error, Dcmd5ResetType
from Script.api.ufs_api.debug_cmd.structs import PowerFlags
from Script.api.ufs_api.defines.enum_define import Dcmd5SsuActive, RefClk, SpdChgGear, SpdChgHsRate, SpdChgLane, SpdChgPowerMode, SpeedChangeTiming

_sdk = shared.sdk
_log = shared.logger

@dataclass
class ReadBootData:
    lba: int
    len: int
    crc_after_read: int = -1 # not initialized defalut value

@dataclass
class ReadData:
    lun: int
    lba: int
    len: int
    crc_after_read: int = -1 # not initialized defalut value

@dataclass
class Dcmd5SpeedChange:
    timing: SpeedChangeTiming
    mode: SpdChgPowerMode
    gear: SpdChgGear
    lane: SpdChgLane
    hsrate: SpdChgHsRate
    refclk: RefClk
    
    def __repr__(self) -> str:
        return (
            f"Dcmd5SpeedChange("
            f"timing={self.timing.name}, "
            f"mode={self.mode.name}, "
            f"gear={self.gear.name}, "
            f"lane={self.lane.name}, "
            f"hsrate={self.hsrate.name}, "
            f"refclk={self.refclk.name})"
        )



class Set_Dcmd5_Arg():
    def __init__(self) -> None:
        self._ssu_powerdown = 0
        self._reset_type = 0
        self._read_boot_data = 0
        self._spd_change_af_link = 0
        self._spd_change_af_init = 0
        self._ssu_active_af_init = 0
        self._read_data = 0
        self._ref_clk_setting = 0
        self._reserved = 0

    @property
    def ssu_powerdown(self) -> int:
        return self._ssu_powerdown

    @ssu_powerdown.setter
    def ssu_powerdown(self, value: int) -> None:
        if value not in [0, 1]:
            raise ValueError("ssu_powerdown must be a single bit (0 or 1)")
        self._ssu_powerdown = value

    @property
    def reset_type(self) -> int:
        return self._reset_type

    @reset_type.setter
    def reset_type(self, value: int) -> None:
        if value < 0 or value > 15:
            raise ValueError("reset_type must be 4 bits (0-15)")
        self._reset_type = value

    @property
    def read_boot_data(self) -> int:
        return self._read_boot_data

    @read_boot_data.setter
    def read_boot_data(self, value: int) -> None:
        if value not in [0, 1]:
            raise ValueError("read_boot_data must be a single bit (0 or 1)")
        self._read_boot_data = value

    @property
    def spd_change_af_link(self) -> int:
        return self._spd_change_af_link

    @spd_change_af_link.setter
    def spd_change_af_link(self, value: int) -> None:
        if value not in [0, 1]:
            raise ValueError("spd_change_af_link must be a single bit (0 or 1)")
        self._spd_change_af_link = value

    @property
    def spd_change_af_init(self) -> int:
        return self._spd_change_af_init

    @spd_change_af_init.setter
    def spd_change_af_init(self, value: int) -> None:
        if value not in [0, 1]:
            raise ValueError("spd_change_af_init must be a single bit (0 or 1)")
        self._spd_change_af_init = value

    @property
    def ssu_active_af_init(self) -> int:
        return self._ssu_active_af_init

    @ssu_active_af_init.setter
    def ssu_active_af_init(self, value: int) -> None:
        if value not in [0, 1, 2]:
            raise ValueError("ssu_active_af_init must be 2 bits (0-2)")
        self._ssu_active_af_init = value

    @property
    def read_data(self) -> int:
        return self._read_data

    @read_data.setter
    def read_data(self, value: int) -> None:
        if value not in [0, 1]:
            raise ValueError("read_data must be a single bit (0 or 1)")
        self._read_data = value

    @property
    def ref_clk_setting(self) -> int:
        return self._ref_clk_setting

    @ref_clk_setting.setter
    def ref_clk_setting(self, value: int) -> None:
        if value not in [0, 1]:
            raise ValueError("ref_clk_setting must be a single bit (0 or 1)")
        self._ref_clk_setting = value

    @property
    def reserved(self) -> int:
        return self._reserved

    @reserved.setter
    def reserved(self, value: int) -> None:
        if value < 0 or value > 15:
            raise ValueError("reserved must be 4 bits (0-15)")
        self._reserved = value

    def to_bytes(self) -> bytearray:
        # Calculate the first 2 bytes
        byte1 = (self._ssu_powerdown << 0) | (self._reset_type << 1) | (self._read_boot_data << 5) | (self._spd_change_af_link << 6) | (self._spd_change_af_init << 7)
        byte2 = (self._ssu_active_af_init << 0) | (self._read_data << 2) | (self._ref_clk_setting << 3) | (self._reserved << 4)

        # Create the bytearray with 12 bytes
        # The first 2 bytes are the packed values, the rest are reserved and set to 0
        return bytearray(struct.pack('<BB10s', byte1, byte2, b'\x00' * 10))

class Set_Dcmd5_Data():
    def __init__(self) -> None:
        self._mode = 0
        self._gear = 0
        self._lane = 0
        self._hs_rate = 0
        self._boot_lba = 0
        self._boot_len = 0
        self._lun = 0
        self._lba = 0
        self._len = 0
        self._ref_clk = 0

    @property
    def mode(self) -> int:
        return self._mode

    @mode.setter
    def mode(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("mode must be a 4-byte value (0-4294967295)")
        self._mode = value

    @property
    def gear(self) -> int:
        return self._gear

    @gear.setter
    def gear(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("mode must be a 4-byte value (0-4294967295)")
        self._gear = value

    @property
    def lane(self) -> int:
        return self._lane

    @lane.setter
    def lane(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("mode must be a 4-byte value (0-4294967295)")
        self._lane = value

    @property
    def hs_rate(self) -> int:
        return self._hs_rate

    @hs_rate.setter
    def hs_rate(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("mode must be a 4-byte value (0-4294967295)")
        self._hs_rate = value

    @property
    def boot_lba(self) -> int:
        return self._boot_lba

    @boot_lba.setter
    def boot_lba(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("boot_lba must be a 4-byte value (0-4294967295)")
        self._boot_lba = value

    @property
    def boot_len(self) -> int:
        return self._boot_len

    @boot_len.setter
    def boot_len(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("boot_len must be a 4-byte value (0-4294967295)")
        self._boot_len = value

    @property
    def lun(self) -> int:
        return self._lun

    @lun.setter
    def lun(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("mode must be a 4-byte value (0-4294967295)")
        self._lun = value

    @property
    def lba(self) -> int:
        return self._lba

    @lba.setter
    def lba(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("lba must be a 4-byte value (0-4294967295)")
        self._lba = value

    @property
    def len(self) -> int:
        return self._len

    @len.setter
    def len(self, value: int) -> None:
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("len must be a 4-byte value (0-4294967295)")
        self._len = value

    @property
    def ref_clk(self) -> int:
        return self._ref_clk

    @ref_clk.setter
    def ref_clk(self, value: int) -> None:
        if value < 0 or value > 0xFF:
            raise ValueError("mode must be a 1byte value (0-255)")
        self._ref_clk = value

    def to_bytes(self) -> bytearray:
        # follow by c code, not sure why
        mode = (self._mode << 16) | self._mode
        gear = (self._gear << 16) | self._gear
        lane = (self._lane << 16) | self._lane

        buf = bytearray(512)
        buf[0:4] = mode.to_bytes(4, byteorder='little')
        buf[4:8] = gear.to_bytes(4, byteorder='little')
        buf[8:12] = lane.to_bytes(4, byteorder='little')
        buf[12:16] = self.hs_rate.to_bytes(4, byteorder='little')
        buf[16:20] = self.boot_lba.to_bytes(4, byteorder='big')
        buf[20:24] = self.boot_len.to_bytes(4, byteorder='big')
        buf[24:25] = self.lun.to_bytes(1, byteorder='big')
        buf[25:29] = self.len.to_bytes(4, byteorder='big')
        buf[29:33] = self.lba.to_bytes(4, byteorder='big')
        buf[33:34] = self.ref_clk.to_bytes(1, byteorder='little')
        return buf
    
class Dcmd5_Info_Buf():
    def __init__(self, info_buf: bytearray | None=None):
        self.status = 0
        self.device_init_flag = 0
        self.ssu_error_code = 0
        self.generic_error_code = 0
        self.boot_error_code = 0
        self.boot_data_crc = 0
        self.read_data_error_code = 0
        self.read_data_crc = 0
        self.dcmd5_total_time = 0
        self.ssu_power_down_total_time = 0
        self.link_startup_total_time = 0
        self.power_change_time_after_link = 0
        self.nop_out_total_time = 0
        self.boot_data_read_total_time = 0
        self.device_ready_time = 0
        self.power_change_time_after_init = 0
        self.ssu_active_total_time = 0 
        self.read_data_total_time = 0
        self.nop_out_time_after_initial = 0
        self.time_stamp_start = 0
        self.time_stamp_end = 0

        if info_buf:
            self.from_bytearray(info_buf)
    
    def from_bytearray(self, info_buf: bytearray) -> None:
        if len(info_buf) < 66:
            raise ValueError("info_buf is too short. Expected at least 66 bytes.")

        self.status = info_buf[0]
        self.device_init_flag = info_buf[1]
        self.ssu_error_code = info_buf[2]
        self.generic_error_code = info_buf[3]
        self.boot_error_code = info_buf[4]
        self.boot_data_crc = int.from_bytes(info_buf[5:9], byteorder='big')
        self.read_data_error_code = info_buf[9]
        self.read_data_crc = int.from_bytes(info_buf[10:14], byteorder='big')
        self.dcmd5_total_time = int.from_bytes(info_buf[14:18], byteorder='big')
        self.ssu_power_down_total_time = int.from_bytes(info_buf[18:22], byteorder='big')
        self.link_startup_total_time = int.from_bytes(info_buf[22:26], byteorder='big')
        self.power_change_time_after_link = int.from_bytes(info_buf[26:30], byteorder='big')
        self.nop_out_total_time = int.from_bytes(info_buf[30:34], byteorder='big')
        self.boot_data_read_total_time = int.from_bytes(info_buf[34:38], byteorder='big')
        self.device_ready_time = int.from_bytes(info_buf[38:42], byteorder='big')
        self.power_change_time_after_init = int.from_bytes(info_buf[42:46], byteorder='big')
        self.ssu_active_total_time = int.from_bytes(info_buf[46:50], byteorder='big')
        self.read_data_total_time = int.from_bytes(info_buf[50:54], byteorder='big')
        self.nop_out_time_after_initial = int.from_bytes(info_buf[54:58], byteorder='big')
        self.time_stamp_start = int.from_bytes(info_buf[58:62], byteorder='big')
        self.time_stamp_end = int.from_bytes(info_buf[62:66], byteorder='big')

    def show_msg(self, ssu_powerdown: bool, read_boot: bool, read_data: bool, speed_change: SpeedChangeTiming) -> None:
        _log.info(f'DCMD5 Status = {Dcmd5Error(self.status).name}')
        _log.info(f'DCMD5 Total Time = {self.dcmd5_total_time / 1000} (ms)')
        if ssu_powerdown:
            _log.info(f'DCMD5 SSU Power Down Time = {self.dcmd5_total_time / 1000} (ms)')
        _log.info(f'DCMD5 Link Time = {self.link_startup_total_time / 1000} (ms)')
        if speed_change in (SpeedChangeTiming.AFTER_LINK, SpeedChangeTiming.AFTER_LINK_AND_INIT):
            _log.info(f'DCMD5 Power Change time after Link = {self.power_change_time_after_link / 1000} (ms)')
        _log.info(f'DCMD5 NOP Out Time = {self.nop_out_total_time / 1000} (ms)')
        if read_boot:
            _log.info(f'DCMD5 Read Boot data Time = {self.boot_data_read_total_time / 1000} (ms)')
        _log.info(f'DCMD5 Device Polling Flag Ready Time = {self.device_ready_time / 1000} (ms)')
        _log.info(f'DCMD5 SSU Active Time (if needed) = {self.ssu_active_total_time / 1000} (ms)')
        if speed_change in (SpeedChangeTiming.AFTER_INIT, SpeedChangeTiming.AFTER_LINK_AND_INIT):
            _log.info(f'DCMD5 Power Change time after fDevice_Init = {self.power_change_time_after_init / 1000} (ms)')
        _log.info(f'DCMD5 NOP Out time after Init = {self.nop_out_time_after_initial / 1000} (ms)')
        if read_data:
            _log.info(f'DCMD5 Read data Time = {self.read_data_total_time / 1000} (ms)')

    def raise_by_status(self) -> None:
        if self.status != Dcmd5Error.PASS: 
            if self.status == Dcmd5Error.SSU_POWERDOWN_FAIL:
                raise api.DCMD5_SSU_POWERDOWN_FAIL
            elif self.status == Dcmd5Error.LINK_STARTUP_FAIL:
                raise api.DCMD5_LINK_STARTUP_FAIL
            elif self.status == Dcmd5Error.SET_REFERENCE_CLOCK_FAIL:
                raise api.DCMD5_SET_REFERENCE_CLOCK_FAIL
            elif self.status == Dcmd5Error.SPEED_CHANGE_FAIL_AFTER_LINK:
                raise api.DCMD5_SPEED_CHANGE_FAIL_AFTER_LINK
            elif self.status == Dcmd5Error.NOP_OUT_FAIL:
                raise api.DCMD5_NOP_OUT_FAIL
            elif self.status == Dcmd5Error.READ_BOOT_DATA_FAIL:
                raise api.DCMD5_READ_BOOT_DATA_FAIL
            elif self.status == Dcmd5Error.SET_INITIAL_FLAG_FAIL:
                raise api.DCMD5_SET_INITIAL_FLAG_FAIL
            elif self.status == Dcmd5Error.READ_INITIAL_FLAG_FAIL:
                raise api.DCMD5_READ_INITIAL_FLAG_FAIL
            elif self.status == Dcmd5Error.READ_INITIAL_FLAG_TIMEOUT:
                raise api.DCMD5_READ_INITIAL_FLAG_TIMEOUT
            elif self.status == Dcmd5Error.SPEED_CHANGE_FAIL_AFTER_INIT:
                raise api.DCMD5_SPEED_CHANGE_FAIL_AFTER_INIT
            elif self.status == Dcmd5Error.NOP_OUT_FAIL_AFTER_POWER_CHANGE:
                raise api.DCMD5_NOP_OUT_FAIL_AFTER_POWER_CHANGE
            elif self.status == Dcmd5Error.SSU_ACTIVE_FAIL:
                raise api.DCMD5_SSU_ACTIVE_FAIL
            elif self.status == Dcmd5Error.READ_DATA_FAIL:
                raise api.DCMD5_READ_DATA_FAIL
            elif self.status == Dcmd5Error.SPOR_BEFORE_HW_RESET:
                raise api.DCMD5_SPOR_BEFORE_HW_RESET
            elif self.status == Dcmd5Error.SPOR_BEFORE_END_POINT_RESET:
                raise api.DCMD5_SPOR_BEFORE_ENDPOINT_RESET
            elif self.status == Dcmd5Error.READ_ATTR_FAIL_BEFORE_SPEED_CHANGE_AFTER_INIT:
                raise api.DCMD5_READ_ATTR_FAIL_BEFORE_SPEED_CHANGE_AFTER_INIT
            else:
                raise api.DCMD5_UNEXPECTED_STATUS

class Dcmd5:
    def __init__(
        self,
        resetmode: Dcmd5ResetType,
        powerdown: bool,
        read_boot: ReadBootData | None,
        read_data: ReadData | None,
        speed_change: Dcmd5SpeedChange,
        ssu_active: Dcmd5SsuActive,
    ):
        self.resetmode = resetmode
        self.powerdown = powerdown
        self.read_boot = read_boot
        self.read_data = read_data
        self.speed_change = speed_change
        self.ssu_active = ssu_active

        # default
        self._arg = Set_Dcmd5_Arg()
        self._data = Set_Dcmd5_Data()
        self._info_buf = Dcmd5_Info_Buf()

        self._build_arg_and_data()

    def _build_arg_and_data(self) -> None:
        self._arg.reset_type = self.resetmode
        self._arg.ssu_powerdown = self.powerdown
        self._arg.ssu_active_af_init = self.ssu_active
        if self.read_boot is not None:
            self._arg.read_boot_data = True
            self._data.boot_lba = self.read_boot.lba
            self._data.boot_len = self.read_boot.len
        if self.read_data is not None:
            self._arg.read_data = True
            self._data.lun = self.read_data.lun
            self._data.lba = self.read_data.lba
            self._data.len = self.read_data.len
        self._arg.spd_change_af_link = 1 if self.speed_change.timing == SpeedChangeTiming.AFTER_LINK else 0
        self._arg.spd_change_af_init = 1 if self.speed_change.timing == SpeedChangeTiming.AFTER_INIT else 0
        self._arg.ref_clk_setting = 1
        self._data.mode = self.speed_change.mode
        self._data.gear = self.speed_change.gear
        self._data.lane = self.speed_change.lane
        self._data.ref_clk = self.speed_change.refclk  
        hs_rate = PowerFlags()
        if self.speed_change.mode in (SpdChgPowerMode.FAST, SpdChgPowerMode.FAST_AUTO):
            hs_rate.rx_termination = 1
            hs_rate.tx_termination = 1
        hs_rate.line_reset = 0
        hs_rate.hs_series = self.speed_change.hsrate
        hs_rate.user_data_valid = 1
        hs_rate.scramble = 0
        self._data.hs_rate = int.from_bytes(hs_rate.to_bytes())

    def _print_step(self) -> None:
        step = 1
        if self.powerdown:
            _log.info(f'Step {step}: SSU Power Down')
            step += 1
        _log.info(f'Step {step}: {self.resetmode.name}')
        step += 1
        _log.info(f'Step {step}: Link Start Up')
        step += 1
        if self.speed_change.timing in (SpeedChangeTiming.AFTER_LINK, SpeedChangeTiming.AFTER_LINK_AND_INIT):
            _log.info(f'Step {step}: Power Mode Change {str(self.speed_change)}')
            step += 1
        _log.info(f'Step {step}: NOP Out')
        step += 1
        if self.read_boot is not None:
            _log.info(f'Step {step}: Read Boot Area: LBA={self.read_boot.lba}, Len={self.read_boot.len}')
            step += 1
        _log.info(f'Step {step}: Device Polling Flag Ready')
        step += 1
        _log.info(f'Step {step}: SSU {self.ssu_active.name}({self.ssu_active})')
        step += 1
        if self.speed_change.timing in (SpeedChangeTiming.AFTER_INIT, SpeedChangeTiming.AFTER_LINK_AND_INIT):
            _log.info(f'Step {step}: Power Mode Change {str(self.speed_change)}')
            step += 1
        _log.info(f'Step {step}: NOP Out after Init')
        step += 1
        if self.read_data is not None:
            _log.info(f'Step {step}: Read Data Area: LUN={self.read_data.lun}, LBA={self.read_data.lba}, Len={self.read_data.len}')
            step += 1

    def set_debug_cmd5(self, reserved: int=0) -> None:
        _log.debug("_set_debug_cmd")
        arg_buf = self._arg.to_bytes()
        data_buf = self._data.to_bytes()
        self._print_step()
        _sdk.set_debug_cmd(Dcmd.DCMD5_MEASURE_INIT_FLOW, arg_buf, reserved, data_buf)

    def get_debug_cmd5(self) -> Dcmd5_Info_Buf: 
        _log.debug("_get_debug_cmd")
        buf = _sdk.get_debug_cmd(Dcmd.DCMD5_MEASURE_INIT_FLOW)
        self._info_buf = Dcmd5_Info_Buf(buf)
        self._info_buf.show_msg(self.powerdown, bool(self.read_boot), bool(self.read_data), self.speed_change.timing)
        return self._info_buf