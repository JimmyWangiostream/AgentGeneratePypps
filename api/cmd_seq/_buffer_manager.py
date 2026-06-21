import math
from typing import Final, Tuple
from Script.api import shared
from Script.api.cmd_seq._cycle_tracker import CmdSeqFuncType, CycleIndicator, CycleTracker
from Script.api.exception import PATTERN_ASSERT_BUFFER_MANAGER_FAIL_BUF_IS_FULL, PATTERN_ASSERT_BUFFER_MANAGER_FAIL_BUF_SIZE_NOT_ALIGN_512, PATTERN_ASSERT_BUFFER_MANAGER_FAIL_CYCLE_INDICATOR_NOT_FOUND, PATTERN_ASSERT_BUFFER_MANAGER_FAIL_EHS_BUF_SIZE_EXCEEDS_LIMIT, PATTERN_ASSERT_BUFFER_MANAGER_FAIL_ENTRY_SIZE_NOT_ALIGN_72, PATTERN_ASSERT_BUFFER_MANAGER_FAIL_PAYLOAD_SIZE_EXCEEDS_EXPECTATION, PATTERN_ASSERT_BUFFER_MANAGER_FAIL_PUSH_CMD_BEFORE_SET_DATA_BEGIN_OFFSET
from Script.api.ufs_api.defines.bit_define import BIT5


_log = shared.logger
ENTRY_SIZE: Final = 72
ALIGN_SIZE_512: Final = 512
ALIGN_SIZE_8K: Final = 8192
NOT_INITIALIZED: Final = -1
BUF_SIZE = 62 * 1024 * 1024
ENTRY_PADDING_SIZE: Final = ALIGN_SIZE_8K % ENTRY_SIZE
ENTRY_CNT_PER_GRP: Final = ALIGN_SIZE_8K // ENTRY_SIZE
BUF_SIZE_IN_8K: Final = BUF_SIZE // 8192
BUF_SIZE_IN_512B: Final = BUF_SIZE // 512
_buffer: bytearray
_entry_ptr: int
"""Next Entry Position. Point to an unoccupied position."""
_data_ptr: int
"""Next Data Position. Point to an unoccupied position."""
_data_begin_offset: int
"""Indicate offset of first byte of data. Initial value is NOT_INITIALIZED(-1) and set by executor,  
the value depends on how many entries in cmd_list,  
and the minimum offset is 32K due to tester limit(instability of Ping-Pong Buffer).  
i.e.    
entries take place of 8K => _data_begin_offset would be 32K.  
entries take place of 32K => _data_begin_offset would be 32K.  
entries take place of 40K => _data_begin_offset would be 40K.  """

ALIGN_EHS_UNIT: Final = 96
EHS_BUF_SIZE = 512 * 1024
_ehs_buffer: bytearray
_ehs_ptr: int

_cycle_indicator_to_offset: dict[CycleIndicator, int]

def print_bytearray(data: bytearray) -> None:
    _log.debug("                 " + ' '.join(f"{i:02}" for i in range(8)))

    for i in range(0, len(data), 8):
        row = data[i:i+8]
        label = f"(byte{i:02}~byte{i+7:02}):"
        values = ' '.join(f"{b:02X}" for b in row)
        if len(row) < 8:
            values += ' ' + ' '.join('--' for _ in range(8 - len(row)))
        _log.debug(f"{label} {values.strip()}")

def align_up(value: int, alignment: int) -> int:
    return math.ceil(value / alignment) * alignment

def align_down(value: int, alignment: int) -> int:
    return value // alignment * alignment

def reset_module() -> None:
    global _buffer, _entry_ptr, _data_ptr, _ehs_ptr, _ehs_buffer, _data_begin_offset, _cycle_indicator_to_offset
    if BUF_SIZE % ALIGN_SIZE_512 != 0:
        raise PATTERN_ASSERT_BUFFER_MANAGER_FAIL_BUF_SIZE_NOT_ALIGN_512
    _buffer = bytearray([0xFF] * BUF_SIZE)
    _entry_ptr = 0
    _data_ptr = 0
    _data_begin_offset = NOT_INITIALIZED

    if EHS_BUF_SIZE > 512 * 1024:
        raise PATTERN_ASSERT_BUFFER_MANAGER_FAIL_EHS_BUF_SIZE_EXCEEDS_LIMIT
    _ehs_buffer = bytearray(EHS_BUF_SIZE)
    _ehs_ptr = 0

    _cycle_indicator_to_offset = {}


def early_check_if_full(entry_cnt: int, total_data_cnt_in_512B: int, total_ehs_cnt_in_96B: int) -> bool:
    grp_cnt = math.ceil(entry_cnt / ENTRY_CNT_PER_GRP)

    # Tester Limit, Data shall place after 32K, due to instability of Ping-Pong Buffer
    if grp_cnt < 4:
        grp_cnt = 4
        
    # Check buffer
    grp_size_in_512B = 8192 // 512
    if BUF_SIZE_IN_512B - grp_cnt * grp_size_in_512B - total_data_cnt_in_512B < 0:
        return True
    
    # Check ehs buffer
    if total_ehs_cnt_in_96B > (EHS_BUF_SIZE // ALIGN_EHS_UNIT):
        return True

    return False

def set_data_begin_offset(entry_cnt: int) -> None:
    global _data_begin_offset, _data_ptr
    _data_begin_offset = align_up(entry_cnt, ENTRY_CNT_PER_GRP) // ENTRY_CNT_PER_GRP * ALIGN_SIZE_8K
    # Tester Limit, Data shall place after 32K, due to instability of Ping-Pong Buffer
    if _data_begin_offset < 32 * 1024:
        _data_begin_offset = 32 * 1024
    _data_ptr = _data_begin_offset

def push_cmd(entry: bytearray, payload: bytearray, ehs: bytearray) -> Tuple[int, int]:
    _log.debug(f'[buf_mngr:push_cmd(print before push)] {_entry_ptr=}, {_data_ptr=}, {_ehs_ptr=}')
    if _data_begin_offset == NOT_INITIALIZED:
        raise PATTERN_ASSERT_BUFFER_MANAGER_FAIL_PUSH_CMD_BEFORE_SET_DATA_BEGIN_OFFSET
    
    data_len = 0
    if entry[0] != 0xFF:
        data_len = int.from_bytes(entry[46:50]) # Data Length in CMD UPIU Parameter

    if _has_room_for_cmd(data_len, len(ehs)) == False:
        raise PATTERN_ASSERT_BUFFER_MANAGER_FAIL_BUF_IS_FULL # shall not catch, fatal error
    data_start_ptr = _push_payload(data_len, payload)
    ehs_start_ptr = _push_ehs(ehs)

    if data_len != 0:
        entry[42:46] = data_start_ptr.to_bytes(4) # Data Address Offset
    if len(ehs) != 0:
        _log.debug('print out ehs bytearray in cmd')
        print_bytearray(ehs)
        entry[54:58] = ehs_start_ptr.to_bytes(4) # EHS Data Address Offset
    _log.debug(f'Data Address Offset={int.from_bytes(entry[42:46])}, Data Length={int.from_bytes(entry[46:50])}, EHS Data Address Offset={int.from_bytes(entry[54:58])}')
    _push_entry(entry)
    return data_start_ptr, ehs_start_ptr

def _has_room_for_cmd(payload_len: int, ehs_len: int) -> bool:
    # _ENTRY_SIZE *2 is to save space for ending cmd
    next_entry_safe_zone = align_up(_entry_ptr + (ENTRY_SIZE * 2), ALIGN_SIZE_8K)
    _log.debug(f'[has_room_for_cmd] {payload_len=}, {ehs_len=}. {next_entry_safe_zone=}, {_data_begin_offset=}, {_data_ptr=}, {_ehs_ptr=}')
    if next_entry_safe_zone > _data_begin_offset:
        return False
    
    if _data_ptr + align_up(payload_len, ALIGN_SIZE_512) > BUF_SIZE:
        return False
    
    if _ehs_ptr + align_up(ehs_len, ALIGN_EHS_UNIT) > EHS_BUF_SIZE:
        return False

    return True

def _push_payload(data_len: int, payload: bytearray) -> int:
    global _data_ptr
    if len(payload) > data_len:
        raise PATTERN_ASSERT_BUFFER_MANAGER_FAIL_PAYLOAD_SIZE_EXCEEDS_EXPECTATION
    start_ptr = _data_ptr
    align_len = align_up(data_len, ALIGN_SIZE_512)
    _buffer[_data_ptr: _data_ptr + len(payload)] = payload
    _data_ptr += align_len
    
    return start_ptr

def _push_entry(entry: bytearray) -> None:
    global _entry_ptr
    if len(entry) != ENTRY_SIZE:
        raise PATTERN_ASSERT_BUFFER_MANAGER_FAIL_ENTRY_SIZE_NOT_ALIGN_72
    _buffer[_entry_ptr: _entry_ptr + ENTRY_SIZE] = entry
    # _ENTRY_SIZE *2 is to check if next entry will cross 8K
    if (_entry_ptr + (ENTRY_SIZE * 2)) % ALIGN_SIZE_8K < ENTRY_SIZE:
        _entry_ptr += (ENTRY_SIZE + ENTRY_PADDING_SIZE)
    else:
        _entry_ptr += ENTRY_SIZE

def _push_ehs(ehs: bytearray) -> int:
    global _ehs_ptr
    start_ptr = _ehs_ptr
    align_len = align_up(len(ehs), ALIGN_EHS_UNIT)
    _ehs_buffer[_ehs_ptr: _ehs_ptr + len(ehs)] = ehs
    _ehs_ptr += align_len

    return start_ptr

def gen_rsp_cycle_indicator(entry_cnt: int) -> None:
    global _cycle_indicator_to_offset
    tracker = CycleTracker()
    for cnt in range(entry_cnt):
        group_idx, entry_idx = divmod(cnt, ENTRY_CNT_PER_GRP)
        group_offset = (ENTRY_SIZE * ENTRY_CNT_PER_GRP + ENTRY_PADDING_SIZE) * group_idx
        offset = group_offset + (entry_idx * ENTRY_SIZE)
        _log.debug(f'gen rsp cycle indicator for offset{offset}')
        transaction_type = _buffer[offset]
        if transaction_type == 0xFF:
            function_code = _buffer[offset+1]
            if function_code == CmdSeqFuncType.DUMMY_RESPONSE_FOR_TASK_MGMT.value:
                abort_tag = _buffer[offset+2]
                indicator = tracker.increment_cycle(CmdSeqFuncType.CMD_UPIU, abort_tag)
            else:
                indicator = tracker.increment_cycle(CmdSeqFuncType(function_code))
        elif transaction_type & BIT5 != 0:
            tasktag = _buffer[offset+3]
            indicator = tracker.increment_cycle(CmdSeqFuncType.CMD_UPIU, tasktag)
        else:
            # parsing complete
            break

        _cycle_indicator_to_offset[indicator] = offset

def get_entry(cycle_indicator: CycleIndicator) -> bytearray:
    # From Response info buffer
    try:
        offset = _cycle_indicator_to_offset[cycle_indicator]
    except KeyError:
        raise PATTERN_ASSERT_BUFFER_MANAGER_FAIL_CYCLE_INDICATOR_NOT_FOUND
    return _buffer[offset: offset+ENTRY_SIZE]

def get_payload(offset: int, length: int) -> bytearray:
    payload = _buffer[offset : offset+length]
    return payload

def get_ehs(offset: int, length: int) -> bytearray:
    ehs = _ehs_buffer[offset: offset+length]
    return ehs


reset_module()