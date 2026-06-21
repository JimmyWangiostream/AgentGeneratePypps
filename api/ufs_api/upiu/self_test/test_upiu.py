from Script.api.self_test.base import ApiTestBase
from Script.api import shared
from Script.api.exception import PATTERN_ASSERT_VALUE_EXCEEDS_FIELD_MAX_VALUE, PATTERN_ASSERT_VALUE_SHALL_NOT_BE_NAGTIVE
from Script import api
import Script.api.cmd_seq as ExecuteCMD
from Script.api.ufs_api.defines.enum_define import *

_sdk = shared.sdk

class TestFormatUnitAssign(ApiTestBase):
    def test_min(self) -> None:
        f = ExecuteCMD.FormatUnit()
        f.assign(lun=0, longlist=0, cmplist=0)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.FORMAT_UNIT)
        self.assertEqual(f.upiu.u16_cdb.b1_longlist, 0)
        self.assertEqual(f.upiu.u16_cdb.b1_cmplst, 0)
        self.assertEqual(f.upiu.l12_expected_data_length, 0)

    def test_mid(self) -> None:
        f = ExecuteCMD.FormatUnit()
        f.assign(lun=0x7f, longlist=1, cmplist=1)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.FORMAT_UNIT)
        self.assertEqual(f.upiu.u16_cdb.b1_longlist, 1)
        self.assertEqual(f.upiu.u16_cdb.b1_cmplst, 1)
        self.assertEqual(f.upiu.l12_expected_data_length, 0)  # 根據實際情況調整

    def test_max(self) -> None:
        f = ExecuteCMD.FormatUnit()
        f.assign(lun=0xff, longlist=1, cmplist=1)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0xff)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.FORMAT_UNIT)
        self.assertEqual(f.upiu.u16_cdb.b1_longlist, 1)
        self.assertEqual(f.upiu.u16_cdb.b1_cmplst, 1)
        self.assertEqual(f.upiu.l12_expected_data_length, 0)  # 根據實際情況調整

    def test_below_min(self) -> None:
        f = ExecuteCMD.FormatUnit()
        with self.assertRaises(PATTERN_ASSERT_VALUE_SHALL_NOT_BE_NAGTIVE):
            f.assign(lun=-1, longlist=0, cmplist=0)
        with self.assertRaises(PATTERN_ASSERT_VALUE_SHALL_NOT_BE_NAGTIVE):
            f.assign(lun=0, longlist=-1, cmplist=0)
        with self.assertRaises(PATTERN_ASSERT_VALUE_SHALL_NOT_BE_NAGTIVE):
            f.assign(lun=0, longlist=0, cmplist=-1)

    def test_above_max(self) -> None:
        f = ExecuteCMD.FormatUnit()
        with self.assertRaises(PATTERN_ASSERT_VALUE_EXCEEDS_FIELD_MAX_VALUE):
            f.assign(lun=0x100, longlist=0, cmplist=0)
        with self.assertRaises(PATTERN_ASSERT_VALUE_EXCEEDS_FIELD_MAX_VALUE):
            f.assign(lun=0, longlist=2, cmplist=0)
        with self.assertRaises(PATTERN_ASSERT_VALUE_EXCEEDS_FIELD_MAX_VALUE):
            f.assign(lun=0, longlist=0, cmplist=2)

    def test_to_bytes(self) -> None:
        cdb = api.CdbFormatUnit()
        cdb.b0_opcode = ScsiCmd.FORMAT_UNIT
        cdb.b1_fmtpinfo = 0b10
        cdb.b1_longlist = 1
        cdb.b1_fmtdata = 0
        cdb.b1_cmplst = 1
        cdb.b1_defect_list_format = 0b010
        cdb.b2_vendor_specific = 0x55
        cdb.w3_obsolete = 0x6666
        cdb.b5_control = 0x77
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.FORMAT_UNIT, 0xAA, 0x55, 0x66, 0x66, 0x77, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestInquiryAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Inquiry()
        f.assign(lun=0x7f, evpd=1, page_code=0x01, length=0x100)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.INQUIRY)
        self.assertEqual(f.upiu.u16_cdb.b1_evpd, 1)
        self.assertEqual(f.upiu.u16_cdb.b2_page_code, 0x01)
        self.assertEqual(f.upiu.u16_cdb.w3_allocation_length, 0x100)

    def test_to_bytes(self) -> None:
        cdb = api.CdbInquiry()
        cdb.b0_opcode = ScsiCmd.INQUIRY
        cdb.b1_rsvd = 0
        cdb.b1_obsolete = 0
        cdb.b1_evpd = 1
        cdb.b2_page_code = 0x02
        cdb.w3_allocation_length = 0x100
        cdb.b5_control = 0x00
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.INQUIRY, 0x01, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestModeSelect10Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ModeSelect10()
        f.assign(lun=0x7f, sp=1, length=0x100)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.MODE_SELECT_10)
        self.assertEqual(f.upiu.u16_cdb.b1_sp, 1)
        self.assertEqual(f.upiu.u16_cdb.w7_parameter_list_length, 0x100)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x100)

    def test_to_bytes(self) -> None:
        cdb = api.CdbModeSelect10()
        cdb.b0_opcode = ScsiCmd.MODE_SELECT_10
        cdb.b1_rsvd = 0
        cdb.b1_pf = 1
        cdb.b1_rsvd2 = 0
        cdb.b1_sp = 1
        cdb.b2_rsvd = 0
        cdb.l3_rsvd = 0
        cdb.w7_parameter_list_length = 0x100
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.MODE_SELECT_10, 0x11, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestModeSense10Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ModeSense10()
        f.assign(lun=0x7f, pc=1, page_code=0x01, subpage_code=0x02, length=0x100)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.MODE_SENSE_10)
        self.assertEqual(f.upiu.u16_cdb.b2_pc, 1)
        self.assertEqual(f.upiu.u16_cdb.b2_page_code, 0x01)
        self.assertEqual(f.upiu.u16_cdb.b3_subpage_code, 0x02)
        self.assertEqual(f.upiu.u16_cdb.w7_allocation_length, 0x100)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x100)

    def test_to_bytes(self) -> None:
        cdb = api.CdbModeSense10()
        cdb.b0_opcode = ScsiCmd.MODE_SENSE_10
        cdb.b1_rsvd = 0
        cdb.b1_llbaa = 0
        cdb.b1_dbd = 1
        cdb.b1_rsvd2 = 0
        cdb.b2_pc = 1
        cdb.b2_page_code = 0x01
        cdb.b3_subpage_code = 0x02
        cdb.b4_rsvd = 0
        cdb.w5_rsvd = 0
        cdb.w7_allocation_length = 0x100
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.MODE_SENSE_10, 0x08, 0x41, 0x02, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestPreFetch10Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.PreFetch10()
        f.assign(lun=0x7f, immed=1, lba=0x12345678, length=0x100)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.PREFETCH_10)
        self.assertEqual(f.upiu.u16_cdb.b1_immed, 1)
        self.assertEqual(f.upiu.u16_cdb.b1_obsolete, 0)
        self.assertEqual(f.upiu.u16_cdb.l2_lba, 0x12345678)
        self.assertEqual(f.upiu.u16_cdb.w7_prefetch_length, 0x100)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x100)

    def test_to_bytes(self) -> None:
        cdb = api.CdbPreFetch10()
        cdb.b0_opcode = ScsiCmd.PREFETCH_10
        cdb.b1_rsvd = 0
        cdb.b1_immed = 1
        cdb.b1_obsolete = 0
        cdb.l2_lba = 0x12345678
        cdb.b6_rsvd = 0
        cdb.b6_group_number = 0
        cdb.w7_prefetch_length = 0x100
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.PREFETCH_10, 0x02, 0x12, 0x34, 0x56, 0x78, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestPreFetch16Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.PreFetch16()
        f.assign(lun=0x7f, immed=1, lba=0x1234567887654321, length=0x10000)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.PREFETCH_16)
        self.assertEqual(f.upiu.u16_cdb.b1_immed, 1)
        self.assertEqual(f.upiu.u16_cdb.l2_lba_h, 0x12345678)
        self.assertEqual(f.upiu.u16_cdb.l6_lba_l, 0x87654321)
        self.assertEqual(f.upiu.u16_cdb.l10_prefetch_length, 0x10000)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x10000)

    def test_to_bytes(self) -> None:
        cdb = api.CdbPreFetch16()
        cdb.b0_opcode = ScsiCmd.PREFETCH_16
        cdb.b1_rsvd = 0
        cdb.b1_immed = 1
        cdb.b1_obsolete = 0
        cdb.l2_lba_h = 0x12345678
        cdb.l6_lba_l = 0x87654321
        cdb.l10_prefetch_length = 0x10000
        cdb.b14_rsvd = 0
        cdb.b14_group_number = 0x01
        cdb.b15_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.PREFETCH_16, 0x02, 0x12, 0x34, 0x56, 0x78, 0x87, 0x65, 0x43, 0x21, 0x00, 0x01, 0x00, 0x00, 0x01, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestRead6Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Read6()
        f.assign(lun=0x7f, lba=0x123456, length=0x10)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.READ_6)
        self.assertEqual(f.upiu.u16_cdb.b1_lba_h, 0x12)
        self.assertEqual(f.upiu.u16_cdb.w2_lba_l, 0x3456)
        self.assertEqual(f.upiu.u16_cdb.b4_transfer_length, 0x10)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x10 * 4096)  # 假設每個扇區 512 字節

    def test_to_bytes(self) -> None:
        cdb = api.CdbRead6()
        cdb.b0_opcode = ScsiCmd.READ_6
        cdb.b1_rsvd = 0
        cdb.b1_lba_h = 0x12
        cdb.w2_lba_l = 0x3456
        cdb.b4_transfer_length = 0x10
        cdb.b5_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.READ_6, 0x12, 0x34, 0x56, 0x10, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestRead10Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Read10()
        f.assign(lun=0x7f, lba=0x12345678, length=0x100, fua=1)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.READ_10)
        self.assertEqual(f.upiu.u16_cdb.b1_fua, 1)
        self.assertEqual(f.upiu.u16_cdb.l2_lba, 0x12345678)
        self.assertEqual(f.upiu.u16_cdb.w7_transfer_length, 0x100)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x100 * 4096)  # 假設每個扇區 512 字節

    def test_to_bytes(self) -> None:
        cdb = api.CdbRead10()
        cdb.b0_opcode = ScsiCmd.READ_10
        cdb.b1_rdprotect = 0
        cdb.b1_dpo = 1
        cdb.b1_fua = 1
        cdb.b1_rsvd = 0
        cdb.b1_fua_nv = 0
        cdb.b1_obsolete = 0
        cdb.l2_lba = 0x12345678
        cdb.b6_rsvd = 0
        cdb.b6_group_number = 0x01
        cdb.w7_transfer_length = 0x100
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.READ_10, 0x18, 0x12, 0x34, 0x56, 0x78, 0x01, 0x01, 0x00, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestRead16Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Read16()
        f.assign(lun=0x7f, lba=0x1234567887654321, length=0x10000, fua=1)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.READ_16)
        self.assertEqual(f.upiu.u16_cdb.b1_fua, 1)
        self.assertEqual(f.upiu.u16_cdb.l2_lba_h, 0x12345678)
        self.assertEqual(f.upiu.u16_cdb.l6_lba_l, 0x87654321)
        self.assertEqual(f.upiu.u16_cdb.l10_transfer_length, 0x10000)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x10000 * 4096)  # 假設每個扇區 512 字節

    def test_to_bytes(self) -> None:
        cdb = api.CdbRead16()
        cdb.b0_opcode = ScsiCmd.READ_16
        cdb.b1_rdprotect = 0
        cdb.b1_dpo = 1
        cdb.b1_fua = 1
        cdb.b1_rsvd = 0
        cdb.b1_fua_nv = 0
        cdb.b1_rsvd2 = 0
        cdb.l2_lba_h = 0x12345678
        cdb.l6_lba_l = 0x87654321
        cdb.l10_transfer_length = 0x10000
        cdb.b14_rsvd = 0
        cdb.b14_rsvd2 = 0
        cdb.b14_group_number = 0x01
        cdb.b15_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.READ_16, 0x18, 0x12, 0x34, 0x56, 0x78, 0x87, 0x65, 0x43, 0x21, 0x00, 0x01, 0x00, 0x00, 0x01, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)


class TestReadBufferAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReadBuffer()
        f.assign(lun=0x7f, mode=1, buffer_id=0x01, buffer_offset=0x123456, length=0x789ABC, vendor=True)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.READ_BUFFER)
        self.assertEqual(f.upiu.u16_cdb.b1_mode, 1)
        self.assertEqual(f.upiu.u16_cdb.b2_buffer_id, 0x01)
        self.assertEqual(f.upiu.u16_cdb.b3_buffer_offset_h, 0x12)
        self.assertEqual(f.upiu.u16_cdb.w4_buffer_offset_l, 0x3456)
        self.assertEqual(f.upiu.u16_cdb.b6_allocation_length_h, 0x78)
        self.assertEqual(f.upiu.u16_cdb.w7_allocation_length_l, 0x9ABC)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x789ABC)

    def test_to_bytes(self) -> None:
        cdb = api.CdbReadBuffer()
        cdb.b0_opcode = ScsiCmd.READ_BUFFER
        cdb.b1_rsvd = 0
        cdb.b1_mode = 1
        cdb.b2_buffer_id = 0x01
        cdb.b3_buffer_offset_h = 0x12
        cdb.w4_buffer_offset_l = 0x3456
        cdb.b6_allocation_length_h = 0x78
        cdb.w7_allocation_length_l = 0x9ABC
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.READ_BUFFER, 0x01, 0x01, 0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)


class TestReadCapacity10Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReadCapacity10()
        f.assign(lun=0x7f)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.READ_CAPACITY_10)
        self.assertEqual(f.upiu.l12_expected_data_length, 8)  # READ CAPACITY 10 固定返回 8 字節

    def test_to_bytes(self) -> None:
        cdb = api.CdbReadCapacity10()
        cdb.b0_opcode = ScsiCmd.READ_CAPACITY_10
        cdb.b1_rsvd = 0
        cdb.b1_obsolete = 0
        cdb.l2_lba = 0x12345678
        cdb.b6_rsvd = 0
        cdb.b7_rsvd = 0
        cdb.b8_rsvd = 0
        cdb.b8_pmi = 1
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.READ_CAPACITY_10, 0x00, 0x12, 0x34, 0x56, 0x78, 0x00, 0x00, 0x01, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestReadCapacity16Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReadCapacity16()
        f.assign(lun=0x7f, alloc_length=0x10000)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.READ_CAPACITY_16)
        self.assertEqual(f.upiu.u16_cdb.l10_allocation_length, 0x10000)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x10000)  # READ CAPACITY 16 固定返回 32 字節

    def test_to_bytes(self) -> None:
        cdb = api.CdbReadCapacity16()
        cdb.b0_opcode = ScsiCmd.READ_CAPACITY_16
        cdb.b1_rsvd = 0
        cdb.b1_service_action = 0x10
        cdb.l2_lba_h = 0x12345678
        cdb.l6_lba_l = 0x87654321
        cdb.l10_allocation_length = 0x10000
        cdb.b14_rsvd = 0
        cdb.b14_pmi = 1
        cdb.b15_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.READ_CAPACITY_16, 0x10, 0x12, 0x34, 0x56, 0x78, 0x87, 0x65, 0x43, 0x21, 0x00, 0x01, 0x00, 0x00, 0x01, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestReportLUNsAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReportLUNs()
        f.assign(lun=0x7f, sel_report=0x01, length=0x10000)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.REPORT_LUNS)
        self.assertEqual(f.upiu.u16_cdb.b2_select_report, 0x01)
        self.assertEqual(f.upiu.u16_cdb.l6_allocation_length, 0x10000)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x10000)  # 根據實際情況調整

    def test_to_bytes(self) -> None:
        cdb = api.CdbReportLUNs()
        cdb.b0_opcode = ScsiCmd.REPORT_LUNS
        cdb.b1_rsvd = 0
        cdb.b2_select_report = 0x01
        cdb.b3_rsvd = 0
        cdb.w4_rsvd = 0
        cdb.l6_allocation_length = 0x10000
        cdb.b10_rsvd = 0
        cdb.b11_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.REPORT_LUNS, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestRequestSenseAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.RequestSense()
        f.assign(lun=0x7f, length=0x10)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.REQUEST_SENSE)
        self.assertEqual(f.upiu.u16_cdb.b4_allocation_length, 0x10)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x10)  # 根據實際情況調整

    def test_to_bytes(self) -> None:
        cdb = api.CdbRequestSense()
        cdb.b0_opcode = ScsiCmd.REQUEST_SENSE
        cdb.b1_rsvd = 0
        cdb.b1_desc = 1
        cdb.w2_rsvd = 0
        cdb.b4_allocation_length = 0x10
        cdb.b5_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.REQUEST_SENSE, 0x01, 0x00, 0x00, 0x10, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestSecurityProtocolInAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.SecurityProtocolIn()
        f.assign(lun=0x7f, security_protocol=0x01, security_protocol_spec=0x1234, allocation_length=0x1000)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.SECURITY_PROTOCOL_IN)
        self.assertEqual(f.upiu.u16_cdb.b1_security_protocol, 0x01)
        self.assertEqual(f.upiu.u16_cdb.w2_security_protocol_specific, 0x1234)
        self.assertEqual(f.upiu.u16_cdb.l6_allocation_length, 0x1000)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x1000)  # 根據實際情況調整

    def test_to_bytes(self) -> None:
        cdb = api.CdbSecurityProtocolIn()
        cdb.b0_opcode = ScsiCmd.SECURITY_PROTOCOL_IN
        cdb.b1_security_protocol = 0x01
        cdb.w2_security_protocol_specific = 0x1234
        cdb.b4_inc_512 = 1
        cdb.b4_rsvd = 0
        cdb.b5_rsvd = 0
        cdb.l6_allocation_length = 0x1000
        cdb.b10_rsvd = 0
        cdb.b11_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.SECURITY_PROTOCOL_IN, 0x01, 0x12, 0x34, 0x80, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)


class TestSecurityProtocolOutAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.SecurityProtocolOut()
        f.assign(lun=0x7f, security_protocol=0x01, security_protocol_spec=0x1234, transfer_length=0x1000)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.SECURITY_PROTOCOL_OUT)
        self.assertEqual(f.upiu.u16_cdb.b1_security_protocol, 0x01)
        self.assertEqual(f.upiu.u16_cdb.w2_security_protocol_specific, 0x1234)
        self.assertEqual(f.upiu.u16_cdb.l6_transfer_length, 0x1000)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x1000)  # 根據實際情況調整

    def test_to_bytes(self) -> None:
        cdb = api.CdbSecurityProtocolOut()
        cdb.b0_opcode = ScsiCmd.SECURITY_PROTOCOL_OUT
        cdb.b1_security_protocol = 0x01
        cdb.w2_security_protocol_specific = 0x1234
        cdb.b4_inc_512 = 1
        cdb.b4_rsvd = 0
        cdb.b5_rsvd = 0
        cdb.l6_transfer_length = 0x1000
        cdb.b10_rsvd = 0
        cdb.b11_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.SECURITY_PROTOCOL_OUT, 0x01, 0x12, 0x34, 0x80, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestSendDiagnosticAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.SendDiagnostic()
        f.assign(lun=0x7f, selftest_code=0x01, pf=1, selftest=1, dev=1, unit=1, length=0x100)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.SEND_DIAGNOSTIC)
        self.assertEqual(f.upiu.u16_cdb.b1_self_test_code, 0x01)
        self.assertEqual(f.upiu.u16_cdb.b1_pf, 1)
        self.assertEqual(f.upiu.u16_cdb.b1_selftest, 1)
        self.assertEqual(f.upiu.u16_cdb.b1_devoffl, 1)
        self.assertEqual(f.upiu.u16_cdb.b1_unitoffl, 1)
        self.assertEqual(f.upiu.u16_cdb.w3_parameter_list_length, 0x100)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x100)  # 根據實際情況調整

    def test_to_bytes(self) -> None:
        cdb = api.CdbSendDiagnostic()
        cdb.b0_opcode = ScsiCmd.SEND_DIAGNOSTIC
        cdb.b1_self_test_code = 0x01
        cdb.b1_pf = 1
        cdb.b1_0 = 0
        cdb.b1_selftest = 1
        cdb.b1_devoffl = 1
        cdb.b1_unitoffl = 1
        cdb.b2_rsvd = 0
        cdb.w3_parameter_list_length = 0x100
        cdb.b5_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.SEND_DIAGNOSTIC, 0x37, 0x00, 0x01, 0x00, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestStartStopUnitAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.StartStopUnit()
        f.assign(lun=0x7f, immed=1, power_condition=0x01, no_flush=1, start=1)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.START_STOP_UNIT)
        self.assertEqual(f.upiu.u16_cdb.b1_immed, 1)
        self.assertEqual(f.upiu.u16_cdb.b4_power_conditions, 0x01)
        self.assertEqual(f.upiu.u16_cdb.b4_no_flush, 1)
        self.assertEqual(f.upiu.u16_cdb.b4_start, 1)

    def test_to_bytes(self) -> None:
        cdb = api.CdbStartStopUnit()
        cdb.b0_opcode = ScsiCmd.START_STOP_UNIT
        cdb.b1_rsvd = 0
        cdb.b1_immed = 1
        cdb.b2_rsvd = 0
        cdb.b3_rsvd = 0
        cdb.b3_power_condition_modifier = 0x01
        cdb.b4_power_conditions = 0x01
        cdb.b4_rsvd = 0
        cdb.b4_no_flush = 1
        cdb.b4_loej = 1
        cdb.b4_start = 1
        cdb.b5_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.START_STOP_UNIT, 0x01, 0x00, 0x01, 0x17, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)


class TestSyncCache10Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.SyncCache10()
        f.assign(lun=0x7f, immed=1, lba=0x12345678, length=0x100)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.SYNCHRONIZE_CACHE_10)
        self.assertEqual(f.upiu.u16_cdb.b1_immed, 1)
        self.assertEqual(f.upiu.u16_cdb.l2_lba, 0x12345678)
        self.assertEqual(f.upiu.u16_cdb.w7_number_of_logical_blocks, 0x100)

    def test_to_bytes(self) -> None:
        cdb = api.CdbSyncCache10()
        cdb.b0_opcode = ScsiCmd.SYNCHRONIZE_CACHE_10
        cdb.b1_rsvd = 0
        cdb.b1_sync_nv = 1
        cdb.b1_immed = 1
        cdb.b1_obsolete = 0
        cdb.l2_lba = 0x12345678
        cdb.b6_rsvd = 0
        cdb.b6_group_number = 0x01
        cdb.w7_number_of_logical_blocks = 0x100
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.SYNCHRONIZE_CACHE_10, 0x06, 0x12, 0x34, 0x56, 0x78, 0x01, 0x01, 0x00, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)


class TestSyncCache16Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.SyncCache16()
        f.assign(lun=0x7f, immed=1, lba=0x1234567887654321, length=0x10000)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.SYNCHRONIZE_CACHE_16)
        self.assertEqual(f.upiu.u16_cdb.b1_immed, 1)
        self.assertEqual(f.upiu.u16_cdb.l2_lba_h, 0x12345678)
        self.assertEqual(f.upiu.u16_cdb.l6_lba_l, 0x87654321)
        self.assertEqual(f.upiu.u16_cdb.l10_number_of_logical_blocks, 0x10000)

    def test_to_bytes(self) -> None:
        cdb = api.CdbSyncCache16()
        cdb.b0_opcode = ScsiCmd.SYNCHRONIZE_CACHE_16
        cdb.b1_rsvd = 0
        cdb.b1_sync_nv = 1
        cdb.b1_immed = 1
        cdb.b1_obsolete = 0
        cdb.l2_lba_h = 0x12345678
        cdb.l6_lba_l = 0x87654321
        cdb.l10_number_of_logical_blocks = 0x10000
        cdb.b14_rsvd = 0
        cdb.b14_group_number = 0x01
        cdb.b15_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.SYNCHRONIZE_CACHE_16, 0x06, 0x12, 0x34, 0x56, 0x78, 0x87, 0x65, 0x43, 0x21, 0x00, 0x01, 0x00, 0x00, 0x01, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)


class TestTestUnitReadyAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.TestUnitReady()
        f.assign(lun=0x7f)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.TEST_UNIT_READY)

    def test_to_bytes(self) -> None:
        cdb = api.CdbTestUnitReady()
        cdb.b0_opcode = ScsiCmd.TEST_UNIT_READY
        cdb.l1_rsvd = 0
        cdb.b5_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.TEST_UNIT_READY, 0x00, 0x00, 0x00, 0x00, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestUnmapAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Unmap()
        f.assign(lun=0x7f, lba=0x12, length=0x100)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.UNMAP)
        self.assertEqual(f.upiu.u16_cdb.w7_param_list_length, 24)
        self.assertEqual(f.upiu.l12_expected_data_length, 24)

    def test_multi_assign_mid(self) -> None:
        cmd = ExecuteCMD.Unmap()
        unmaplist = []
        blockdescriptor = api.UnmapBlockDescriptor()
        blockdescriptor.l4_lba_l = 0
        blockdescriptor.l8_number_of_logical_blocks = 1
        unmaplist.append(blockdescriptor)

        blockdescriptor = api.UnmapBlockDescriptor()
        blockdescriptor.l4_lba_l = 1
        blockdescriptor.l8_number_of_logical_blocks = 2
        unmaplist.append(blockdescriptor)
        
        cmd.assign_multi_cmd(lun=0x7f, block_descriptor=unmaplist)
        self.assertEqual(cmd.upiu.b0_transaction_type, 0x01)
        self.assertEqual(cmd.upiu.b2_lun, 0x7f)
        self.assertEqual(cmd.upiu.u16_cdb.b0_opcode, ScsiCmd.UNMAP)
        self.assertEqual(cmd.upiu.u16_cdb.w7_param_list_length, 16 + 16 + 8) 
        self.assertEqual(cmd.upiu.l12_expected_data_length, 16 + 16 + 8)

    def test_to_bytes(self) -> None:
        cdb = api.CdbUnmap()
        cdb.b0_opcode = ScsiCmd.UNMAP
        cdb.b1_rsvd = 0
        cdb.b1_anchor = 1
        cdb.l2_rsvd = 0
        cdb.b6_rsvd = 0
        cdb.b6_group_number = 0x01
        cdb.w7_param_list_length = 0x100
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.UNMAP, 0x01, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 0x00, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestVerify10Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Verify10()
        f.assign(lun=0x7f, lba=0x12345678, length=0x100)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.VERIFY_10)
        self.assertEqual(f.upiu.u16_cdb.l2_lba, 0x12345678)
        self.assertEqual(f.upiu.u16_cdb.w7_verification_length, 0x100)

    def test_to_bytes(self) -> None:
        cdb = api.CdbVerify10()
        cdb.b0_opcode = ScsiCmd.VERIFY_10
        cdb.b1_vrprotect = 0x01
        cdb.b1_dpo = 1
        cdb.b1_rsvd = 0
        cdb.b1_bytchk = 1
        cdb.b1_obsolete = 0
        cdb.l2_lba = 0x12345678
        cdb.b6_rsvd = 0
        cdb.b6_group_number = 0x01
        cdb.w7_verification_length = 0x100
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.VERIFY_10, 0x32, 0x12, 0x34, 0x56, 0x78, 0x01, 0x01, 0x00, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestWrite6Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Write6()
        f.assign(lun=0x7f, lba=0x123456, length=0x10)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.WRITE_6)
        self.assertEqual(f.upiu.u16_cdb.b1_lba_h, 0x12)
        self.assertEqual(f.upiu.u16_cdb.w2_lba_l, 0x3456)
        self.assertEqual(f.upiu.u16_cdb.b4_transfer_length, 0x10)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x10 * 4096)

    def test_to_bytes(self) -> None:
        cdb = api.CdbWrite6()
        cdb.b0_opcode = ScsiCmd.WRITE_6
        cdb.b1_rsvd = 0
        cdb.b1_lba_h = 0x12
        cdb.w2_lba_l = 0x3456
        cdb.b4_transfer_length = 0x10
        cdb.b5_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.WRITE_6, 0x12, 0x34, 0x56, 0x10, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestWrite10Assign(ApiTestBase):
    def test_min(self) -> None:
        w = ExecuteCMD.Write10()
        w.assign(lun=0, lba=0, length=0, fua=0)
        self.assertEqual(w.upiu.b0_transaction_type, 0x01)
        self.assertEqual(w.upiu.b2_lun, 0)
        self.assertEqual(w.upiu.u16_cdb.b0_opcode, 0x2A)
        self.assertEqual(w.upiu.u16_cdb.b1_fua, 0)
        self.assertEqual(w.upiu.u16_cdb.l2_lba, 0)
        self.assertEqual(w.upiu.u16_cdb.w7_transfer_length, 0)
        self.assertEqual(w.upiu.l12_expected_data_length, 0)

    def test_mid(self) -> None:
        w = ExecuteCMD.Write10()
        w.assign(lun=0x7f, lba=0x7fffffff, length=0x7fff, fua=1)
        self.assertEqual(w.upiu.b0_transaction_type, 0x01)
        self.assertEqual(w.upiu.b2_lun, 0x7f)
        self.assertEqual(w.upiu.u16_cdb.b0_opcode, 0x2A)
        self.assertEqual(w.upiu.u16_cdb.b1_fua, 1)
        self.assertEqual(w.upiu.u16_cdb.l2_lba, 0x7fffffff)
        self.assertEqual(w.upiu.u16_cdb.w7_transfer_length, 0x7fff)
        self.assertEqual(w.upiu.l12_expected_data_length, 0x7fff000)

    def test_max(self) -> None:
        w = ExecuteCMD.Write10()
        w.assign(lun=0xff, lba=0xffffffff, length=0xffff, fua=1)
        self.assertEqual(w.upiu.b0_transaction_type, 0x01)
        self.assertEqual(w.upiu.b2_lun, 0xff)
        self.assertEqual(w.upiu.u16_cdb.b0_opcode, 0x2A)
        self.assertEqual(w.upiu.u16_cdb.b1_fua, 1)
        self.assertEqual(w.upiu.u16_cdb.l2_lba, 0xffffffff)
        self.assertEqual(w.upiu.u16_cdb.w7_transfer_length, 0xffff)
        self.assertEqual(w.upiu.l12_expected_data_length, 0xffff000)

    def test_below_min(self) -> None:
        w = ExecuteCMD.Write10()
        with self.assertRaises(PATTERN_ASSERT_VALUE_SHALL_NOT_BE_NAGTIVE):
            w.assign(lun=-1, lba=0, length=0, fua=0)
        with self.assertRaises(PATTERN_ASSERT_VALUE_SHALL_NOT_BE_NAGTIVE):
            w.assign(lun=0, lba=-1, length=0, fua=0)
        with self.assertRaises(PATTERN_ASSERT_VALUE_SHALL_NOT_BE_NAGTIVE):
            w.assign(lun=0, lba=0, length=-1, fua=0)
        with self.assertRaises(PATTERN_ASSERT_VALUE_SHALL_NOT_BE_NAGTIVE):
            w.assign(lun=0, lba=0, length=0, fua=-1)

    def test_above_max(self) -> None:
        w = ExecuteCMD.Write10()
        with self.assertRaises(PATTERN_ASSERT_VALUE_EXCEEDS_FIELD_MAX_VALUE):
            w.assign(lun=0x100, lba=0, length=0, fua=0)
        with self.assertRaises(PATTERN_ASSERT_VALUE_EXCEEDS_FIELD_MAX_VALUE):
            w.assign(lun=0, lba=0x100000000, length=0, fua=0)
        with self.assertRaises(PATTERN_ASSERT_VALUE_EXCEEDS_FIELD_MAX_VALUE):
            w.assign(lun=0, lba=0, length=0x10000, fua=0)
        with self.assertRaises(PATTERN_ASSERT_VALUE_EXCEEDS_FIELD_MAX_VALUE):
            w.assign(lun=0, lba=0, length=0, fua=2)

    def test_to_bytes(self) -> None:
        cdb = api.CdbWrite10()
        cdb.b0_opcode = ScsiCmd.INQUIRY
        cdb.b1_wrprotect = 0b101
        cdb.b1_dpo = 0
        cdb.b1_fua = 1
        cdb.b1_rsvd = 0
        cdb.b1_fua_nv = 1
        cdb.b1_obsolete = 0
        cdb.l2_lba = 0x12345678
        cdb.b6_rsvd = 0b101
        cdb.b6_group_number = 0b11100
        cdb.w7_transfer_length = 0x1234
        cdb.b9_control = 0x56
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([0x12, 0xAA, 0x12, 0x34, 0x56, 0x78, 0xBC, 0x12, 0x34, 0x56])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestWrite16Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.Write16()
        f.assign(lun=0x7f, lba=0x1234567887654321, length=0x10000, fua=1)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.WRITE_16)
        self.assertEqual(f.upiu.u16_cdb.b1_fua, 1)
        self.assertEqual(f.upiu.u16_cdb.l2_lba_h, 0x12345678)
        self.assertEqual(f.upiu.u16_cdb.l6_lba_l, 0x87654321)
        self.assertEqual(f.upiu.u16_cdb.l10_transfer_length, 0x10000)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x10000 * 4096)

    def test_to_bytes(self) -> None:
        cdb = api.CdbWrite16()
        cdb.b0_opcode = ScsiCmd.WRITE_16
        cdb.b1_wrprotect = 0
        cdb.b1_dpo = 1
        cdb.b1_fua = 1
        cdb.b1_rsvd = 0
        cdb.b1_fua_nv = 0
        cdb.b1_rsvd2 = 0
        cdb.l2_lba_h = 0x12345678
        cdb.l6_lba_l = 0x87654321
        cdb.l10_transfer_length = 0x10000
        cdb.b14_ignore = 0
        cdb.b14_rsvd = 0
        cdb.b14_group_number = 0x01
        cdb.b15_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.WRITE_16, 0x18, 0x12, 0x34, 0x56, 0x78, 0x87, 0x65, 0x43, 0x21, 0x00, 0x01, 0x00, 0x00, 0x01, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)


class TestWriteBufferAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.WriteBuffer()
        f.assign(lun=0x7f, mode=1, buffer_id=0x01, buffer_offset=0x123456, length=0x789ABC, vendor=True)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.WRITE_BUFFER)
        self.assertEqual(f.upiu.u16_cdb.b1_rsvd, 0)
        self.assertEqual(f.upiu.u16_cdb.b1_mode, 1)
        self.assertEqual(f.upiu.u16_cdb.b2_buffer_id, 0x01)
        self.assertEqual(f.upiu.u16_cdb.b3_buffer_offset_h, 0x12)
        self.assertEqual(f.upiu.u16_cdb.w4_buffer_offset_l, 0x3456)
        self.assertEqual(f.upiu.u16_cdb.b6_allocation_length_h, 0x78)
        self.assertEqual(f.upiu.u16_cdb.w7_allocation_length_l, 0x9ABC)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x789ABC) 

    def test_to_bytes(self) -> None:
        cdb = api.CdbWriteBuffer()
        cdb.b0_opcode = ScsiCmd.WRITE_BUFFER
        cdb.b1_rsvd = 0
        cdb.b1_mode = 1
        cdb.b2_buffer_id = 0x01
        cdb.b3_buffer_offset_h = 0x12
        cdb.w4_buffer_offset_l = 0x3456
        cdb.b6_allocation_length_h = 0x78
        cdb.w7_allocation_length_l = 0x9ABC
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.WRITE_BUFFER, 0x01, 0x01, 0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestTaskManagementAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.TaskManagement()
        f.assign(lun=0x7f, iid=0b1100, task_management_function=0x01, target_lun=0x02, target_tasktag=0x03, target_iid=0x04)
        self.assertEqual(f.upiu.b0_transaction_type, UPIUTransactionType.TM_REQ)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.b4_iid, 0b1100)
        self.assertEqual(f.upiu.b5_task_manag_function, 0x01)
        self.assertEqual(f.upiu.l12_input_parameter1, 0x02)
        self.assertEqual(f.upiu.l16_input_parameter2, 0x03)
        self.assertEqual(f.upiu.l20_input_parameter3, 0x04)

class TestHpbReadAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.HpbRead()
        f.assign(lun=0x7f, lba=0x12345678, length=0x100, fua=1, hpb_entry=0x8765432112345678, hpb_read_id=0x01)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.HPB_READ)
        self.assertEqual(f.upiu.u16_cdb.b1_fua, 1)
        self.assertEqual(f.upiu.u16_cdb.l2_lba, 0x12345678)
        self.assertEqual(f.upiu.u16_cdb.l6_hpb_entry_h, 0x87654321)
        self.assertEqual(f.upiu.u16_cdb.l10_hpb_entry_l, 0x12345678)
        self.assertEqual(f.upiu.u16_cdb.b14_transfer_length, 0x100)
        self.assertEqual(f.upiu.u16_cdb.b15_hpb_read_id, 0x01)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x100 * 4096)  # 假設每個扇區 512 字節

    def test_to_bytes(self) -> None:
        cdb = api.CdbHpbRead()
        cdb.b0_opcode = ScsiCmd.HPB_READ
        cdb.b1_rsvd = 0
        cdb.b1_dpo = 1
        cdb.b1_fua = 1
        cdb.b1_rsvd2 = 0
        cdb.l2_lba = 0x12345678
        cdb.l6_hpb_entry_h = 0x87654321
        cdb.l10_hpb_entry_l = 0x12345678
        cdb.b14_transfer_length = 0x10
        cdb.b15_hpb_read_id = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.HPB_READ, 0x18, 0x12, 0x34, 0x56, 0x78, 0x87, 0x65, 0x43, 0x21, 0x12, 0x34, 0x56, 0x78, 0x10, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestHpbReadBufferAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.HpbReadBuffer()
        f.assign(lun=0x7f, hpb_region=0x1234, hpb_subregion=0x5678, allocation_length=0x9ABCDE)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.HPB_READ_BUFFER)
        self.assertEqual(f.upiu.u16_cdb.b1_bufferid, 0x01)
        self.assertEqual(f.upiu.u16_cdb.w2_hpb_region, 0x1234)
        self.assertEqual(f.upiu.u16_cdb.w4_hpb_subregion, 0x5678)
        self.assertEqual(f.upiu.u16_cdb.b6_allocation_length_h, 0x9A)
        self.assertEqual(f.upiu.u16_cdb.w7_allocation_length_l, 0xBCDE)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x9ABCDE)  # 根據實際情況調整

    def test_to_bytes(self) -> None:
        cdb = api.CdbHpbReadBuffer()
        cdb.b0_opcode = ScsiCmd.HPB_READ_BUFFER
        cdb.b1_bufferid = 0x01
        cdb.w2_hpb_region = 0x1234
        cdb.w4_hpb_subregion = 0x5678
        cdb.b6_allocation_length_h = 0x9A
        cdb.w7_allocation_length_l = 0xBCDE
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.HPB_READ_BUFFER, 0x01, 0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestHpbWriteBuffer01Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.HpbWriteBuffer01()
        f.assign(lun=0x7f, hpb_region=0x1234)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.HPB_WRITE_BUFFER)
        self.assertEqual(f.upiu.u16_cdb.b1_buffer_id, 0x01)
        self.assertEqual(f.upiu.u16_cdb.w2_hpb_region, 0x1234)
        self.assertEqual(f.upiu.l12_expected_data_length, 0)  # 根據實際情況調整

    def test_to_bytes(self) -> None:
        cdb = api.CdbHpbWriteBuffer01()
        cdb.b0_opcode = ScsiCmd.HPB_WRITE_BUFFER
        cdb.b1_buffer_id = 0x01
        cdb.w2_hpb_region = 0x1234
        cdb.b4_rsvd = 0
        cdb.l5_rsvd = 0
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.HPB_WRITE_BUFFER, 0x01, 0x12, 0x34, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestHpbWriteBuffer02Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.HpbWriteBuffer02()
        f.assign(lun=0x7f, lba=0x12345678, hpb_read_id=0x01, param_list_length=0x100)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.HPB_WRITE_BUFFER)
        self.assertEqual(f.upiu.u16_cdb.b1_buffer_id, 0x02)
        self.assertEqual(f.upiu.u16_cdb.l2_lba, 0x12345678)
        self.assertEqual(f.upiu.u16_cdb.b6_hpb_read_id, 0x01)
        self.assertEqual(f.upiu.u16_cdb.w7_param_list_length, 0x100)
        self.assertEqual(f.upiu.l12_expected_data_length, 0x100)  # 根據實際情況調整

    def test_to_bytes(self) -> None:
        cdb = api.CdbHpbWriteBuffer02()
        cdb.b0_opcode = ScsiCmd.HPB_WRITE_BUFFER
        cdb.b1_buffer_id = 0x02
        cdb.l2_lba = 0x12345678
        cdb.b6_hpb_read_id = 0x01
        cdb.w7_param_list_length = 0x100
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.HPB_WRITE_BUFFER, 0x02, 0x12, 0x34, 0x56, 0x78, 0x01, 0x01, 0x00, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestHpbWriteBuffer03Assign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.HpbWriteBuffer03()
        f.assign(lun=0x7f)
        self.assertEqual(f.upiu.b0_transaction_type, 0x01)
        self.assertEqual(f.upiu.b2_lun, 0x7f)
        self.assertEqual(f.upiu.u16_cdb.b0_opcode, ScsiCmd.HPB_WRITE_BUFFER)
        self.assertEqual(f.upiu.u16_cdb.b1_buffer_id, 0x03)
        self.assertEqual(f.upiu.l12_expected_data_length, 0)  # 根據實際情況調整

    def test_to_bytes(self) -> None:
        cdb = api.CdbHpbWriteBuffer03()
        cdb.b0_opcode = ScsiCmd.HPB_WRITE_BUFFER
        cdb.b1_buffer_id = 0x03
        cdb.b2_rsvd = 0
        cdb.l3_rsvd = 0
        cdb.w7_rsvd = 0
        cdb.b9_control = 0x01
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([ScsiCmd.HPB_WRITE_BUFFER, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestReadDescriptorAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReadDescriptor()
        f.assign(idn=0x01, index=0x02, selector=0x03)
        self.assertEqual(f.upiu.b0_transaction_type, UPIUTransactionType.QRY_REQ)
        self.assertEqual(f.upiu.u12_specific_fields.b12_opcode, QueryFunctionOpcode.READ_DESCRIPTOR)
        self.assertEqual(f.upiu.u12_specific_fields.b13_idn, 0x01)
        self.assertEqual(f.upiu.u12_specific_fields.b14_index, 0x02)
        self.assertEqual(f.upiu.u12_specific_fields.b15_selector, 0x03)
        self.assertEqual(f.upiu.u12_specific_fields.w18_length, 0xFF)
        self.assertEqual(f.upiu.w10_data_segment_length, 0)

    def test_to_bytes(self) -> None:
        cdb = api.SfReadDescriptor()
        cdb.b12_opcode = QueryFunctionOpcode.READ_DESCRIPTOR
        cdb.b13_idn = 0x01
        cdb.b14_index = 0x02
        cdb.b15_selector = 0x03
        cdb.b16_rsvd = 0
        cdb.b17_rsvd = 0
        cdb.w18_length = 0x100
        cdb.l20_rsvd = 0
        cdb.l24_rsvd = 0
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([QueryFunctionOpcode.READ_DESCRIPTOR, 0x01, 0x02, 0x03, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestWriteDescriptorAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.WriteDescriptor()
        f.assign(idn=0x01, index=0x02, selector=0x03, length=0x100)
        self.assertEqual(f.upiu.b0_transaction_type, UPIUTransactionType.QRY_REQ)
        self.assertEqual(f.upiu.u12_specific_fields.b12_opcode, QueryFunctionOpcode.WRITE_DESCRIPTOR)
        self.assertEqual(f.upiu.u12_specific_fields.b13_idn, 0x01)
        self.assertEqual(f.upiu.u12_specific_fields.b14_index, 0x02)
        self.assertEqual(f.upiu.u12_specific_fields.b15_selector, 0x03)
        self.assertEqual(f.upiu.u12_specific_fields.w18_length, 0x100)
        self.assertEqual(f.upiu.w10_data_segment_length, 0x100)

    def test_to_bytes(self) -> None:
        cdb = api.SfWriteDescriptor()
        cdb.b12_opcode = QueryFunctionOpcode.WRITE_DESCRIPTOR
        cdb.b13_idn = 0x01
        cdb.b14_index = 0x02
        cdb.b15_selector = 0x03
        cdb.b16_rsvd = 0
        cdb.b17_rsvd = 0
        cdb.w18_length = 0x100
        cdb.l20_rsvd = 0
        cdb.l24_rsvd = 0
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([QueryFunctionOpcode.WRITE_DESCRIPTOR, 0x01, 0x02, 0x03, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestReadAttributeAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReadAttribute()
        f.assign(idn=0x01, index=0x02, selector=0x03)
        self.assertEqual(f.upiu.b0_transaction_type, UPIUTransactionType.QRY_REQ)
        self.assertEqual(f.upiu.u12_specific_fields.b12_opcode, QueryFunctionOpcode.READ_ATTRIBUTE)
        self.assertEqual(f.upiu.u12_specific_fields.b13_idn, 0x01)
        self.assertEqual(f.upiu.u12_specific_fields.b14_index, 0x02)
        self.assertEqual(f.upiu.u12_specific_fields.b15_selector, 0x03)
        self.assertEqual(f.upiu.w10_data_segment_length, 0)

    def test_to_bytes(self) -> None:
        cdb = api.SfReadAttribute()
        cdb.b12_opcode = QueryFunctionOpcode.READ_ATTRIBUTE
        cdb.b13_idn = 0x01
        cdb.b14_index = 0x02
        cdb.b15_selector = 0x03
        cdb.q16_value = 0x12345678
        cdb.l24_rsvd = 0
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([QueryFunctionOpcode.READ_ATTRIBUTE, 0x01, 0x02, 0x03, 0x00, 0x00, 0x00, 0x00, 0x12, 0x34, 0x56, 0x78, 0x00, 0x00, 0x00, 0x00])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestWriteAttributeAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.WriteAttribute()
        f.assign(idn=0x01, index=0x02, selector=0x03)
        f.set_attr(0x12345678)
        self.assertEqual(f.upiu.b0_transaction_type, UPIUTransactionType.QRY_REQ)
        self.assertEqual(f.upiu.u12_specific_fields.b12_opcode, QueryFunctionOpcode.WRITE_ATTRIBUTE)
        self.assertEqual(f.upiu.u12_specific_fields.b13_idn, 0x01)
        self.assertEqual(f.upiu.u12_specific_fields.b14_index, 0x02)
        self.assertEqual(f.upiu.u12_specific_fields.b15_selector, 0x03)
        self.assertEqual(f.upiu.u12_specific_fields.q16_value, 0x12345678)
        self.assertEqual(f.upiu.w10_data_segment_length, 0)

    def test_to_bytes(self) -> None:
        cdb = api.SfWriteAttribute()
        cdb.b12_opcode = QueryFunctionOpcode.WRITE_ATTRIBUTE
        cdb.b13_idn = 0x01
        cdb.b14_index = 0x02
        cdb.b15_selector = 0x03
        cdb.q16_value = 0x12345678
        cdb.l24_rsvd = 0
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([QueryFunctionOpcode.WRITE_ATTRIBUTE, 0x01, 0x02, 0x03, 0x00, 0x00, 0x00, 0x00, 0x12, 0x34, 0x56, 0x78, 0x00, 0x00, 0x00, 0x00])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestReadFlagAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ReadFlag()
        f.assign(idn=0x01, index=0x02, selector=0x03)
        self.assertEqual(f.upiu.b0_transaction_type, UPIUTransactionType.QRY_REQ)
        self.assertEqual(f.upiu.u12_specific_fields.b12_opcode, QueryFunctionOpcode.READ_FLAG)
        self.assertEqual(f.upiu.u12_specific_fields.b13_idn, 0x01)
        self.assertEqual(f.upiu.u12_specific_fields.b14_index, 0x02)
        self.assertEqual(f.upiu.u12_specific_fields.b15_selector, 0x03)

    def test_to_bytes(self) -> None:
        cdb = api.SfReadFlag()
        cdb.b12_opcode = QueryFunctionOpcode.READ_FLAG
        cdb.b13_idn = 0x01
        cdb.b14_index = 0x02
        cdb.b15_selector = 0x03
        cdb.l16_rsvd = 0
        cdb.b20_rsvd = 0
        cdb.b21_rsvd = 0
        cdb.b22_rsvd = 0
        cdb.b23_flag_value = 0x01
        cdb.l24_rsvd = 0
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([QueryFunctionOpcode.READ_FLAG, 0x01, 0x02, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestSetFlagAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.SetFlag()
        f.assign(idn=0x01, index=0x02, selector=0x03)
        f.set_flag(0x01)
        self.assertEqual(f.upiu.b0_transaction_type, UPIUTransactionType.QRY_REQ)
        self.assertEqual(f.upiu.u12_specific_fields.b12_opcode, QueryFunctionOpcode.SET_FLAG)
        self.assertEqual(f.upiu.u12_specific_fields.b13_idn, 0x01)
        self.assertEqual(f.upiu.u12_specific_fields.b14_index, 0x02)
        self.assertEqual(f.upiu.u12_specific_fields.b15_selector, 0x03)
        self.assertEqual(f.upiu.u12_specific_fields.b23_flag_value, 0x01)

    def test_to_bytes(self) -> None:
        cdb = api.SfSetFlag()
        cdb.b12_opcode = QueryFunctionOpcode.SET_FLAG
        cdb.b13_idn = 0x01
        cdb.b14_index = 0x02
        cdb.b15_selector = 0x03
        cdb.l16_rsvd = 0
        cdb.b20_rsvd = 0
        cdb.b21_rsvd = 0
        cdb.b22_rsvd = 0
        cdb.b23_flag_value = 0x01
        cdb.l24_rsvd = 0
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([QueryFunctionOpcode.SET_FLAG, 0x01, 0x02, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestClearFlagAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ClearFlag()
        f.assign(idn=0x01, index=0x02, selector=0x03)
        self.assertEqual(f.upiu.b0_transaction_type, UPIUTransactionType.QRY_REQ)
        self.assertEqual(f.upiu.u12_specific_fields.b12_opcode, QueryFunctionOpcode.CLEAR_FLAG)
        self.assertEqual(f.upiu.u12_specific_fields.b13_idn, 0x01)
        self.assertEqual(f.upiu.u12_specific_fields.b14_index, 0x02)
        self.assertEqual(f.upiu.u12_specific_fields.b15_selector, 0x03)
        self.assertEqual(f.upiu.w10_data_segment_length, 0)

    def test_to_bytes(self) -> None:
        cdb = api.SfClearFlag()
        cdb.b12_opcode = QueryFunctionOpcode.CLEAR_FLAG
        cdb.b13_idn = 0x01
        cdb.b14_index = 0x02
        cdb.b15_selector = 0x03
        cdb.l16_rsvd = 0
        cdb.b20_rsvd = 0
        cdb.b21_rsvd = 0
        cdb.b22_rsvd = 0
        cdb.b23_flag_value = 0x01
        cdb.l24_rsvd = 0
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([QueryFunctionOpcode.CLEAR_FLAG, 0x01, 0x02, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)

class TestToggleFlagAssign(ApiTestBase):
    def test_mid(self) -> None:
        f = ExecuteCMD.ToggleFlag()
        f.assign(idn=0x01, index=0x02, selector=0x03)
        self.assertEqual(f.upiu.b0_transaction_type, UPIUTransactionType.QRY_REQ)
        self.assertEqual(f.upiu.u12_specific_fields.b12_opcode, QueryFunctionOpcode.TOGGLE_FLAG)
        self.assertEqual(f.upiu.u12_specific_fields.b13_idn, 0x01)
        self.assertEqual(f.upiu.u12_specific_fields.b14_index, 0x02)
        self.assertEqual(f.upiu.u12_specific_fields.b15_selector, 0x03)
        self.assertEqual(f.upiu.w10_data_segment_length, 0)

    def test_to_bytes(self) -> None:
        cdb = api.SfToggleFlag()
        cdb.b12_opcode = QueryFunctionOpcode.TOGGLE_FLAG
        cdb.b13_idn = 0x01
        cdb.b14_index = 0x02
        cdb.b15_selector = 0x03
        cdb.l16_rsvd = 0
        cdb.b20_rsvd = 0
        cdb.b21_rsvd = 0
        cdb.b22_rsvd = 0
        cdb.b23_flag_value = 0x01
        cdb.l24_rsvd = 0
        b = cdb.to_bytes()
        ans = bytearray(16)
        content = bytearray([QueryFunctionOpcode.TOGGLE_FLAG, 0x01, 0x02, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
        ans[0:len(content)] = content
        self.assertEqual(b, ans)
