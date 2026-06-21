import inspect
import time
from Script.api import shared
import random
from Script.project_api.custom_vu.read_log.structs import *
from Script.project_api.custom_vu.read_log.define import *
from Script.project_api.functions import send_data_in_vcmd
from Script.api.cmd_seq.response import CommandResponse
from typing import List

_log = shared.logger

# ── Event log layout ──
EVENT_LOG_TRANSFER_LENGTH = 0x4000
SPECIFIC_LOG_INFO_OFFSET = 0x0A08  # after Header(8)+Common(1024)+SystemStatus(512)+HostSSR(1024)


def _read_u32(data: bytes | bytearray, offset: int) -> int:
    return int.from_bytes(data[offset: offset + 4], "little", signed=False)


def _get_event_log_count(priority:EventLogPriority, retry_count: int = 5, sleep_sec: float = 1.0) -> int:
    for retry in range(retry_count):
        try:
            _, output = issue_4080_read_log_from_nand(
                para_0=0, para_1=0, para_2=0, para_3=priority, para_4=0,
                transfer_length=EVENT_LOG_TRANSFER_LENGTH,
            )
            count = _read_u32(output, 0)
            if count > 0 or retry == retry_count - 1:
                return count
        except Exception:
            if retry == retry_count - 1:
                raise
        _log.info(f"Event log count not ready yet, retry = {retry + 1}/{retry_count}")
        time.sleep(sleep_sec)
    return 0


def _read_event_log_by_index(event_index: int, priority:EventLogPriority) -> bytearray:
    _, output = issue_4080_read_log_from_nand(
        para_0=0, para_1=1, para_2=event_index,
        para_3=priority, para_4=0,
        transfer_length=EVENT_LOG_TRANSFER_LENGTH,
    )
    return output

def clear_event_logs(priority:int = EventLogPriority.LowPriority|EventLogPriority.HighPriority) -> None:
    if priority & EventLogPriority.HighPriority:
        issue_4080_read_log_from_nand(
            para_0=0,
            para_1=0xFFFFFFFF,
            para_2=0,
            para_3=EventLogPriority.HighPriority,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )
    if priority & EventLogPriority.LowPriority:
        issue_4080_read_log_from_nand(
            para_0=0,
            para_1=0xFFFFFFFF,
            para_2=0,
            para_3=EventLogPriority.LowPriority,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )

def issue_find_event_log_by_id(log_id: int, priority:EventLogPriority) -> List[bytearray]:
    """Find all event logs matching the given LogID.

    Scans all existing event logs and returns every entry whose LogID matches.
    Results are ordered from oldest (index=0) to newest.

    Args:
        log_id: Event LogID value (e.g. 0x3006, 0x6001).

    Returns:
        List of full 0x4000 bytearray outputs, one per matching entry.
        Empty list if none found.

    The specific log fields start at offset SPECIFIC_LOG_INFO_OFFSET (0x0A08).
    """
    _log.info(f"{inspect.currentframe().f_code.co_name}(0x{log_id:04X})")  # type: ignore

    count = _get_event_log_count(priority)
    if count == 0:
        _log.info("No event logs in NAND")
        return []

    found: List[bytearray] = []
    for idx in range(count):
        output = _read_event_log_by_index(idx, priority)
        found_id = _read_u32(output, SPECIFIC_LOG_INFO_OFFSET)
        if found_id == log_id:
            _log.info(f"Found 0x{log_id:04X} at index={idx}")
            found.append(output)

    if not found:
        _log.info(f"LogID 0x{log_id:04X} not found in NAND")

    return found


def issue_4080_read_log_from_nand(para_0:int, para_1:int, para_2:int, para_3:int = 0, para_4:int = 0, transfer_length:int = 0x4000, keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4080()
    vu.b0_opcode.value = 0x80
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = transfer_length
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)

    vu.para_0.value = para_0
    vu.para_1.value = para_1
    vu.para_2.value = para_2
    vu.para_3.value = para_3
    vu.para_4.value = para_4

    return send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)


def issue_4082_read_log(keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4082()
    vu.b0_opcode.value = 0x82
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x4000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)

    return send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
