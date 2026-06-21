import struct
import Script.api.cmd_seq._buffer_manager as _buf_mngr
from Script.api.exception import PATTERN_ASSERT_BUFFER_MANAGER_FAIL_BUF_IS_FULL, PATTERN_ASSERT_BUFFER_MANAGER_FAIL_BUF_SIZE_NOT_ALIGN_512, PATTERN_ASSERT_BUFFER_MANAGER_FAIL_EHS_BUF_SIZE_EXCEEDS_LIMIT, PATTERN_ASSERT_BUFFER_MANAGER_FAIL_PUSH_CMD_BEFORE_SET_DATA_BEGIN_OFFSET
from Script.api.self_test.base import ApiTestBase
from Script.api import shared
from Script.lib import sdk_lib as lib
from Script.lib.sdk_lib.user import constant

_sdk = shared.sdk

_backup_buf_size = 0
_backup_ehs_buf_size = 0
def backup_buf_mngr_param() -> None:
    global _backup_buf_size, _backup_ehs_buf_size
    _backup_buf_size = _buf_mngr.BUF_SIZE
    _backup_ehs_buf_size = _buf_mngr.EHS_BUF_SIZE

def restore_buf_mngr_param() -> None:
    _buf_mngr.BUF_SIZE = _backup_buf_size
    _buf_mngr.EHS_BUF_SIZE = _backup_ehs_buf_size

def entry_idx_to_offset(idx: int) -> int:
    group_idx, entry_idx = divmod(idx, 113)
    group_offset = (72 * 113 + 56) * group_idx
    return group_offset + (entry_idx * 72)

class TestPushCmd(ApiTestBase):
    def setUp(self) -> None:
        backup_buf_mngr_param()
        _buf_mngr.BUF_SIZE = 512 * 100
        _buf_mngr.EHS_BUF_SIZE = 512 * 1024
        _buf_mngr.reset_module()

    def tearDown(self) -> None:
        restore_buf_mngr_param()

    def push_50_entry_expect_get_right_entry(self) -> None:
        _buf_mngr.reset_module()
        _buf_mngr.set_data_begin_offset(50)
        for _ in range(50):
            data = 0x01
            b = bytearray(data * 72)
            data = (data + 1) & 0xFF
            _buf_mngr.push_cmd(b, bytearray(0),bytearray(0))
        for i in range(50):
            data = 0x01
            b = bytearray(data * 72)
            data = (data + 1) & 0xFF
            offset = entry_idx_to_offset(i)
            self.assertEqual(_buf_mngr._buffer[offset: offset+72], b)
        self.assertEqual(_buf_mngr._entry_ptr, 50 * 72)

    def push_226_entry_expect_get_right_entry(self) -> None:
        _buf_mngr.reset_module()
        _buf_mngr.set_data_begin_offset(226)
        for _ in range(226):
            data = 0x01
            b = bytearray(data * 72)
            data = (data + 1) & 0xFF
            _buf_mngr.push_cmd(b, bytearray(0),bytearray(0))
        for i in range(226):
            print(f'[get entry {i}]')
            data = 0x01
            b = bytearray(data * 72)
            data = (data + 1) & 0xFF
            offset = entry_idx_to_offset(i)
            self.assertEqual(_buf_mngr._buffer[offset: offset+72], b)
        self.assertEqual(_buf_mngr._entry_ptr, 16 * 1024)
    
    def push_payload_less_than_512B_expect_data_ptr_align_512(self) -> None:
        _buf_mngr.reset_module()
        _buf_mngr.set_data_begin_offset(1130) # 10 grp -> 80K
        length = 511
        entry = bytearray(72)
        entry[46:50] = struct.pack('>L', 512)
        b = bytearray([0xAB] * length)
        b[0] = 0x11
        b[-1] = 0x99
        _buf_mngr.push_cmd(entry, b, bytearray(0))
        self.assertEqual(_buf_mngr._data_ptr, 80 * 1024 + 512)
        self.assertEqual(_buf_mngr.get_payload(80 * 1024, length),  b)

    def push_payload_larger_than_512B_expect_data_ptr_align_512(self) -> None:
        _buf_mngr.reset_module()
        _buf_mngr.set_data_begin_offset(1130) # 10 grp -> 80K
        length = 513
        entry = bytearray(72)
        entry[46:50] = struct.pack('>L', 1024)
        b = bytearray([0xAB] * length)
        b[0] = 0x11
        b[-1] = 0x99
        _buf_mngr.push_cmd(entry, b, bytearray(0))
        self.assertEqual(_buf_mngr._data_ptr, 80 * 1024 + 512 + 512)
        self.assertEqual(_buf_mngr.get_payload(80 * 1024, length),  b)

    def push_payload_512B_expect_data_ptr_align_512(self) -> None:
        _buf_mngr.reset_module()
        _buf_mngr.set_data_begin_offset(1130) # 10 grp -> 80K
        length = 512
        entry = bytearray(72)
        entry[46:50] = struct.pack('>L', 512)
        b = bytearray([0xAB] * length)
        b[0] = 0x11
        b[-1] = 0x99
        _buf_mngr.push_cmd(entry, b, bytearray(0))
        self.assertEqual(_buf_mngr._data_ptr, 80 * 1024 + 512)
        self.assertEqual(_buf_mngr.get_payload(80 * 1024, length),  b)

    def push_payload_0_size_expect_data_ptr_at_right_offset(self) -> None:
        _buf_mngr.reset_module()
        _buf_mngr.set_data_begin_offset(1130) # 10 grp -> 80K
        _buf_mngr.push_cmd(bytearray(72), bytearray(0), bytearray(0))
        self.assertEqual(_buf_mngr._data_ptr, 80 * 1024)

    def test_diff_buf_size(self) -> None:
        sizes = [62 * 1024 * 1024, 31 * 1024 * 1024, 100 * 1024]
        for size in sizes:
            _buf_mngr.BUF_SIZE = size
            self.push_50_entry_expect_get_right_entry()
            self.push_226_entry_expect_get_right_entry()
            self.push_payload_less_than_512B_expect_data_ptr_align_512()
            self.push_payload_larger_than_512B_expect_data_ptr_align_512()
            self.push_payload_512B_expect_data_ptr_align_512()
            self.push_payload_0_size_expect_data_ptr_at_right_offset()

class TestResetModule(ApiTestBase):
    def setUp(self) -> None:
        backup_buf_mngr_param()
        _buf_mngr.BUF_SIZE = 512 * 100
        _buf_mngr.EHS_BUF_SIZE = 512 * 1024
        _buf_mngr.reset_module()

    def tearDown(self) -> None:
        restore_buf_mngr_param()

    def test_val_after_reset_expect_all_variable_to_default(self) -> None:
        _buf_mngr._buffer[0] = 0xFF
        _buf_mngr._entry_ptr = 123
        _buf_mngr._data_ptr = 456
        _buf_mngr._ehs_buffer[0] = 0xFF
        _buf_mngr._ehs_ptr = 789
        _buf_mngr._data_begin_offset = 101112

        _buf_mngr.reset_module()
        self.assertEqual(_buf_mngr._buffer, bytearray([0xFF] * _buf_mngr.BUF_SIZE))
        self.assertEqual(_buf_mngr._entry_ptr, 0)
        self.assertEqual(_buf_mngr._data_ptr, 0)
        self.assertEqual(_buf_mngr._data_begin_offset, -1)
        self.assertEqual(_buf_mngr._ehs_buffer, bytearray([0x00] * _buf_mngr.EHS_BUF_SIZE))
        self.assertEqual(_buf_mngr._ehs_ptr, 0)

    def test_set_buf_size_error_case_expect_raise_exception(self) -> None:
        _buf_mngr.BUF_SIZE = 512 * 100 + 1
        with self.assertRaises(PATTERN_ASSERT_BUFFER_MANAGER_FAIL_BUF_SIZE_NOT_ALIGN_512):
            _buf_mngr.reset_module()

    def test_set_ehs_buf_size_error_case_expect_raise_exception(self) -> None:
        _buf_mngr.EHS_BUF_SIZE = 512 * 1024 + 1
        with self.assertRaises(PATTERN_ASSERT_BUFFER_MANAGER_FAIL_EHS_BUF_SIZE_EXCEEDS_LIMIT):
            _buf_mngr.reset_module()

class TestEarlyCheck(ApiTestBase):
    def setUp(self) -> None:
        backup_buf_mngr_param()
        _buf_mngr.BUF_SIZE = 512 * 100
        _buf_mngr.EHS_BUF_SIZE = 512 * 1024
        _buf_mngr.reset_module()

    def tearDown(self) -> None:
        restore_buf_mngr_param()

    def test_full_of_entry_expect_early_check_return_true(self) -> None:
        entry_cnt = _buf_mngr.BUF_SIZE_IN_8K  * 113
        status = _buf_mngr.early_check_if_full(entry_cnt=entry_cnt,
                                    total_data_cnt_in_512B=0,
                                    total_ehs_cnt_in_96B=0)
        self.assertFalse(status)

        status = _buf_mngr.early_check_if_full(entry_cnt=entry_cnt + 1,
                                    total_data_cnt_in_512B=0,
                                    total_ehs_cnt_in_96B=0)
        self.assertTrue(status)
    
    def test_full_of_payload_expect_early_check_return_true(self) -> None:
        full_payload = _buf_mngr.BUF_SIZE_IN_512B - 32 * 1024 // 512
        status = _buf_mngr.early_check_if_full(113 * 4, full_payload, 0)
        self.assertFalse(status)

        status = _buf_mngr.early_check_if_full(113 * 2 + 50, full_payload, 0)
        self.assertFalse(status)

        status = _buf_mngr.early_check_if_full(1, full_payload, 0)
        self.assertFalse(status)

        status = _buf_mngr.early_check_if_full(113 * 4, full_payload  + 1, 0)
        self.assertTrue(status)

    def test_mix_entry_payload_expect_early_check_return_true(self) -> None:
        entry_len  = 32 * 1024  + 72
        full_payload_in_512B = _buf_mngr.BUF_SIZE_IN_512B - 40 * 1024 // 512
        status = _buf_mngr.early_check_if_full(113 * 4 + 1, full_payload_in_512B, 0)
        self.assertFalse(status)

        status = _buf_mngr.early_check_if_full(113 * 4 + 1, full_payload_in_512B + 1, 0)
        self.assertTrue(status)

    def test_full_ehs_expect_early_check_return_true(self) -> None:
        full_ehs_in_96B = _buf_mngr.EHS_BUF_SIZE // 96
        status = _buf_mngr.early_check_if_full(1, 0, full_ehs_in_96B)
        self.assertFalse(status)

        status = _buf_mngr.early_check_if_full(1, 0, full_ehs_in_96B + 1)
        self.assertTrue(status)

class TestSetDataBeginOffset(ApiTestBase):
    def setUp(self) -> None:
        backup_buf_mngr_param()
        _buf_mngr.BUF_SIZE = 512 * 100
        _buf_mngr.EHS_BUF_SIZE = 512 * 1024
        _buf_mngr.reset_module()

    def tearDown(self) -> None:
        restore_buf_mngr_param()

    def test_entry_less_than_32K_expect_ptr_still_at_32K(self) -> None:
        _buf_mngr.set_data_begin_offset(113 * 4 - 1)
        self.assertEqual(_buf_mngr._data_ptr,  32 * 1024)
        self.assertEqual(_buf_mngr._data_begin_offset,  32 * 1024)

    def test_entry_equals_to_32K_expect_ptr_equals_to_32K(self) -> None:
        _buf_mngr.set_data_begin_offset(113 * 4)
        self.assertEqual(_buf_mngr._data_ptr,  32 * 1024)
        self.assertEqual(_buf_mngr._data_begin_offset,  32 * 1024)

    def test_entry_larger_than_32K_expect_ptr_works_fine(self) -> None:
        _buf_mngr.set_data_begin_offset(113 * 4 + 1)
        self.assertEqual(_buf_mngr._data_ptr,  40 * 1024)
        self.assertEqual(_buf_mngr._data_begin_offset,  40 * 1024)

    def test_push_before_set_data_ptr_expect_raise_exception(self) -> None:
        with self.assertRaises(PATTERN_ASSERT_BUFFER_MANAGER_FAIL_PUSH_CMD_BEFORE_SET_DATA_BEGIN_OFFSET):
            _buf_mngr.push_cmd(bytearray(72), bytearray(0), bytearray(0))
        
class TestHasRoomForCmd(ApiTestBase):
    def setUp(self) -> None:
        backup_buf_mngr_param()
        _buf_mngr.BUF_SIZE = 512 * 100
        _buf_mngr.EHS_BUF_SIZE = 512 * 1024
        _buf_mngr.reset_module()

    def tearDown(self) -> None:
        restore_buf_mngr_param()

    def test_entry_full_boundary_expect_raise_exception(self) -> None:
        _buf_mngr.set_data_begin_offset(113 * 4)
        for _ in range(113 * 4 - 1): # save one entry space for ending entry
            _buf_mngr.push_cmd(bytearray(72), bytearray(), bytearray())
        with self.assertRaises(PATTERN_ASSERT_BUFFER_MANAGER_FAIL_BUF_IS_FULL):
            _buf_mngr.push_cmd(bytearray(72), bytearray(), bytearray())

    def test_payload_full_boundary_expect_raise_exception(self) -> None:
        max_payload_size = _buf_mngr.BUF_SIZE - 32 * 1024
        _buf_mngr.set_data_begin_offset(113 * 4)
        entry = bytearray(72)
        entry[46:50] = struct.pack('>L', max_payload_size - 1)
        b = bytearray([0xAB] * (max_payload_size - 1))
        b[0] = 0x11
        b[-1] = 0x99
        _buf_mngr.push_cmd(entry, b, bytearray(0))

        entry[46:50] = struct.pack('>L', 1)
        with self.assertRaises(PATTERN_ASSERT_BUFFER_MANAGER_FAIL_BUF_IS_FULL):
            _buf_mngr.push_cmd(entry, bytearray(1), bytearray(0))

