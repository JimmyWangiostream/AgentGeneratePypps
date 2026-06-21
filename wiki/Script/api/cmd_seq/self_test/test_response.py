import inspect

from Script.api.self_test.base import ApiTestBase
from Script.api import shared, ExecuteCMD, UPIUTransactionType, ScsiStatus, SenseKey, SfReadDescriptor, SfWriteDescriptor, SfReadAttribute, SfWriteAttribute, QueryFunctionOpcode, DescriptorIDN, \
    AttributeIDN, FlagIDN, SfReadFlag, SfSetFlag, SfClearFlag, SfToggleFlag, SfNop
from Script.api.cmd_seq.response import CommandResponse, TaskMgmtResponse, QueryResponse, NopInResponse, get_scsi_status_str, get_sense_key_str, get_asc_ascq_description
import Script.api.cmd_seq._buffer_manager as _buf_mngr

from Script.lib import sdk_lib as lib
from Script.lib.sdk_lib.user import exception

_sdk = shared.sdk
logger = shared.logger


class TestCommandResponse(ApiTestBase):
    def setUp(self) -> None:
        ExecuteCMD.clear()

    def test_ut_command_response(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        cmd_resp = bytearray([0x21, 0x10, 0x1F, 0xFF, 0x00, 0x00, 0x01, 0x02, 0x00, 0x01, 0x00, 0x14, 0x00, 0x00, 0x00, 0x00,
                              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        sense_data = bytearray([0x00, 0x12, 0x70, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x25, 0x00, 0x00, 0x00, 0x00, 0x00])
        cmd_tag = bytearray([0xAA])
        cmd_timestamp = bytearray([0x00, 0x01, 0x23, 0x45])
        resp_tag = bytearray([0xBB])
        resp_timestamp = bytearray([0x54, 0x32, 0x10, 0x00])
        entry = cmd_resp + sense_data + bytearray([0x00]) + cmd_tag + cmd_timestamp + resp_tag + resp_timestamp + bytearray([0x00]) * 9

        logger.info("Check CMD response 72B & from_bytes() mapping")
        resp = CommandResponse()
        resp.raw_data = entry
        resp.upiu.from_bytes(entry)
        resp.b32_sense_data.from_bytes(entry[32:52])
        resp.b53_cmd_tag = entry[53]
        resp.l54_cmd_timestamp = int.from_bytes(entry[54:58], byteorder='big')
        resp.b58_resp_tag = entry[58]
        resp.l59_resp_timestamp = int.from_bytes(entry[59:63], byteorder='big')
        # cmd = cast(IsCmdUpiuEntry, cmd)
        # resp.data = _buf_mngr.get_payload(cmd.param.l42_data_address_offset, cmd.param.l46_data_length)

        self.assertEqual(resp.upiu.b0_transaction_type, UPIUTransactionType.RSP)
        self.assertEqual(resp.upiu.b1_flags, 0x10)
        self.assertEqual(resp.upiu.b2_lun, 0x1F)
        self.assertEqual(resp.upiu.b3_tasktag, 0xFF)
        self.assertEqual(resp.upiu.b4_iid, 0x00)
        self.assertEqual(resp.upiu.b4_command_set_type, 0x00)
        self.assertEqual(resp.upiu.b5_ext_iid, 0x00)
        self.assertEqual(resp.upiu.b6_response, 0x01)
        self.assertEqual(resp.upiu.b7_status, ScsiStatus.CHECK_CONDITION)
        self.assertEqual(resp.upiu.b8_total_ehs_length, 0x00)
        self.assertEqual(resp.upiu.b9_device_information, 0x01)
        self.assertEqual(resp.upiu.w10_data_segment_length, 0x14)
        self.assertEqual(resp.upiu.l12_residual_transfer_count, 0x00)

        self.assertEqual(resp.b53_cmd_tag, 0xAA)
        self.assertEqual(resp.l54_cmd_timestamp, 0x00012345)
        self.assertEqual(resp.b58_resp_tag, 0xBB)
        self.assertEqual(resp.l59_resp_timestamp, 0x54321000)

        logger.info("Check sense data")
        self.assertEqual(resp.b32_sense_data.w_sense_data_length, 0x12)
        self.assertEqual(resp.b32_sense_data.b0_response_code, 0x70)
        self.assertEqual(resp.b32_sense_data.b2_sense_key, SenseKey.ILLEGAL_REQUEST)
        self.assertEqual(resp.b32_sense_data.l3_information, 0x00)
        self.assertEqual(resp.b32_sense_data.b7_additional_sense_length, 0x0A)
        self.assertEqual(resp.b32_sense_data.l8_command_specific_information, 0x00)
        self.assertEqual(resp.b32_sense_data.b12_asc, 0x25)
        self.assertEqual(resp.b32_sense_data.b13_ascq, 0x00)
        logger.info("SCSI status %s, Sense key: %s, ASC/ASCQ %s" % (get_scsi_status_str(resp), get_sense_key_str(resp), get_asc_ascq_description(resp)))


class TestTaskMgmtResponse(ApiTestBase):
    def setUp(self) -> None:
        ExecuteCMD.clear()

    def test_ut_task_mgmt_response(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        cmd_resp = bytearray([0x24, 0x10, 0x07, 0xFF, 0xFF, 0xEE, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x23, 0x45, 0x67,
                              0x76, 0x54, 0x32, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        sense_data = bytearray([0x00]) * 20
        cmd_tag = bytearray([0xAA])
        cmd_timestamp = bytearray([0x00, 0x01, 0x23, 0x45])
        resp_tag = bytearray([0xBB])
        resp_timestamp = bytearray([0x54, 0x32, 0x10, 0x00])
        entry = cmd_resp + sense_data + bytearray([0x00]) + cmd_tag + cmd_timestamp + resp_tag + resp_timestamp + bytearray([0x00]) * 9

        logger.info("Check Task Mgmt response 72B & from_bytes() mapping")
        resp = TaskMgmtResponse()
        resp.raw_data = entry
        resp.upiu.from_bytes(entry)
        resp.b53_cmd_tag = entry[53]
        resp.l54_cmd_timestamp = int.from_bytes(entry[54:58], byteorder='big')
        resp.b58_resp_tag = entry[58]
        resp.l59_resp_timestamp = int.from_bytes(entry[59:63], byteorder='big')
        # cmd = cast(IsCmdUpiuEntry, cmd)
        # resp.data = _buf_mngr.get_payload(cmd.param.l42_data_address_offset, cmd.param.l46_data_length)

        self.assertEqual(resp.upiu.b0_transaction_type, UPIUTransactionType.TM_RSP)
        self.assertEqual(resp.upiu.b1_flags, 0x10)
        self.assertEqual(resp.upiu.b2_lun, 0x07)
        self.assertEqual(resp.upiu.b3_tasktag, 0xFF)
        self.assertEqual(resp.upiu.b4_iid, 0xFF)
        self.assertEqual(resp.upiu.b5_ext_iid, 0xEE)
        self.assertEqual(resp.upiu.b6_response, 0x01)
        self.assertEqual(resp.upiu.b8_total_ehs_length, 0x00)
        self.assertEqual(resp.upiu.w10_data_segment_length, 0x00)
        self.assertEqual(resp.upiu.l12_output_parameter1, 0x01234567)
        self.assertEqual(resp.upiu.l16_output_parameter2, 0x76543210)

        self.assertEqual(resp.b53_cmd_tag, 0xAA)
        self.assertEqual(resp.l54_cmd_timestamp, 0x00012345)
        self.assertEqual(resp.b58_resp_tag, 0xBB)
        self.assertEqual(resp.l59_resp_timestamp, 0x54321000)

        logger.info("Check sense data")
        self.assertEqual(resp.b32_sense_data.w_sense_data_length, 0)
        self.assertEqual(resp.b32_sense_data.b0_response_code, 0)
        self.assertEqual(resp.b32_sense_data.b2_sense_key, 0)
        self.assertEqual(resp.b32_sense_data.l3_information, 0)
        self.assertEqual(resp.b32_sense_data.b7_additional_sense_length, 0)
        self.assertEqual(resp.b32_sense_data.l8_command_specific_information, 0)
        self.assertEqual(resp.b32_sense_data.b12_asc, 0)
        self.assertEqual(resp.b32_sense_data.b13_ascq, 0)


class TestQueryResponse(ApiTestBase):
    def setUp(self) -> None:
        ExecuteCMD.clear()

    def test_ut_query_response(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        cmd_resp = bytearray([0x36, 0x20, 0x00, 0xFF, 0x00, 0x40, 0xFF, 0x00, 0x00, 0x01, 0x00, 0x20, 0x01, 0x02, 0x03, 0x04,
                              0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x00, 0x00, 0x00, 0x00])
        sense_data = bytearray([0x00]) * 20
        cmd_tag = bytearray([0xAA])
        cmd_timestamp = bytearray([0x00, 0x01, 0x23, 0x45])
        resp_tag = bytearray([0xBB])
        resp_timestamp = bytearray([0x54, 0x32, 0x10, 0x00])
        entry = cmd_resp + sense_data + bytearray([0x00]) + cmd_tag + cmd_timestamp + resp_tag + resp_timestamp + bytearray([0x00]) * 9

        logger.info("Check Query response 72B & from_bytes() mapping")
        resp = QueryResponse()
        resp.raw_data = entry
        resp.upiu.from_bytes(entry)
        resp.b53_cmd_tag = entry[53]
        resp.l54_cmd_timestamp = int.from_bytes(entry[54:58], byteorder='big')
        resp.b58_resp_tag = entry[58]
        resp.l59_resp_timestamp = int.from_bytes(entry[59:63], byteorder='big')
        # cmd = cast(IsCmdUpiuEntry, cmd)
        # resp.data = _buf_mngr.get_payload(cmd.param.l42_data_address_offset, cmd.param.l46_data_length)

        self.assertEqual(resp.upiu.b0_transaction_type, UPIUTransactionType.QRY_RSP)
        self.assertEqual(resp.upiu.b1_flags, 0x20)
        self.assertEqual(resp.upiu.b3_tasktag, 0xFF)
        self.assertEqual(resp.upiu.b5_query_function, 0x40)
        self.assertEqual(resp.upiu.b6_query_response, 0xFF)
        self.assertEqual(resp.upiu.b8_total_ehs_length, 0x00)
        self.assertEqual(resp.upiu.b9_device_information, 0x01)
        self.assertEqual(resp.upiu.w10_data_segment_length, 0x20)
        self.assertEqual(resp.upiu.u12_specific_fields, bytearray([ 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10]))

        self.assertEqual(resp.b53_cmd_tag, 0xAA)
        self.assertEqual(resp.l54_cmd_timestamp, 0x00012345)
        self.assertEqual(resp.b58_resp_tag, 0xBB)
        self.assertEqual(resp.l59_resp_timestamp, 0x54321000)

        logger.info("Check sense data")
        self.assertEqual(resp.b32_sense_data.w_sense_data_length, 0)
        self.assertEqual(resp.b32_sense_data.b0_response_code, 0)
        self.assertEqual(resp.b32_sense_data.b2_sense_key, 0)
        self.assertEqual(resp.b32_sense_data.l3_information, 0)
        self.assertEqual(resp.b32_sense_data.b7_additional_sense_length, 0)
        self.assertEqual(resp.b32_sense_data.l8_command_specific_information, 0)
        self.assertEqual(resp.b32_sense_data.b12_asc, 0)
        self.assertEqual(resp.b32_sense_data.b13_ascq, 0)

    def test_ut_read_descriptor(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        trans_specific_field = bytearray([QueryFunctionOpcode.READ_DESCRIPTOR, DescriptorIDN.CONFIGURATION, 0x01, 0x02, 0x00, 0x00, 0xFF, 0xFF,
                                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0x00])
        read_desc = SfReadDescriptor()
        read_desc.from_bytes(trans_specific_field)
        self.assertEqual(read_desc.b12_opcode, QueryFunctionOpcode.READ_DESCRIPTOR)
        self.assertEqual(read_desc.b13_idn, DescriptorIDN.CONFIGURATION)
        self.assertEqual(read_desc.b14_index, 0x01)
        self.assertEqual(read_desc.b15_selector, 0x02)
        self.assertEqual(read_desc.w18_length, 0xFFFF)

    def test_ut_write_descriptor(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        trans_specific_field = bytearray([QueryFunctionOpcode.WRITE_DESCRIPTOR, DescriptorIDN.CONFIGURATION, 0x03, 0x04, 0x00, 0x00, 0xAB, 0xCD,
                                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0x00])
        write_desc = SfWriteDescriptor()
        write_desc.from_bytes(trans_specific_field)
        self.assertEqual(write_desc.b12_opcode, QueryFunctionOpcode.WRITE_DESCRIPTOR)
        self.assertEqual(write_desc.b13_idn, DescriptorIDN.CONFIGURATION)
        self.assertEqual(write_desc.b14_index, 0x03)
        self.assertEqual(write_desc.b15_selector, 0x04)
        self.assertEqual(write_desc.w18_length, 0xABCD)

    def test_ut_read_attribute(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        trans_specific_field = bytearray([QueryFunctionOpcode.READ_ATTRIBUTE, AttributeIDN.BOOT_LUN_EN, 0x05, 0x06, 0x08, 0x07, 0x06, 0x05,
                                          0x04, 0x03, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0x00])
        read_attr = SfReadAttribute()
        read_attr.from_bytes(trans_specific_field)
        self.assertEqual(read_attr.b12_opcode, QueryFunctionOpcode.READ_ATTRIBUTE)
        self.assertEqual(read_attr.b13_idn, AttributeIDN.BOOT_LUN_EN)
        self.assertEqual(read_attr.b14_index, 0x05)
        self.assertEqual(read_attr.b15_selector, 0x06)
        self.assertEqual(read_attr.q16_value, 0x0807060504030201)

    def test_ut_write_attribute(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        trans_specific_field = bytearray([QueryFunctionOpcode.WRITE_ATTRIBUTE, AttributeIDN.ACTIVE_ICC_LVL, 0x07, 0x08, 0x01, 0x02, 0x03, 0x04,
                                          0x05, 0x06, 0x07, 0x08, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0x00])
        write_attr = SfWriteAttribute()
        write_attr.from_bytes(trans_specific_field)
        self.assertEqual(write_attr.b12_opcode, QueryFunctionOpcode.WRITE_ATTRIBUTE)
        self.assertEqual(write_attr.b13_idn, AttributeIDN.ACTIVE_ICC_LVL)
        self.assertEqual(write_attr.b14_index, 0x07)
        self.assertEqual(write_attr.b15_selector, 0x08)
        self.assertEqual(write_attr.q16_value, 0x0102030405060708)

    def test_ut_read_flag(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        trans_specific_field = bytearray([QueryFunctionOpcode.READ_FLAG, FlagIDN.PERMANENT_WP_EN, 0x0A, 0x0B, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0x00])
        read_flag = SfReadFlag()
        read_flag.from_bytes(trans_specific_field)
        self.assertEqual(read_flag.b12_opcode, QueryFunctionOpcode.READ_FLAG)
        self.assertEqual(read_flag.b13_idn, FlagIDN.PERMANENT_WP_EN)
        self.assertEqual(read_flag.b14_index, 0x0A)
        self.assertEqual(read_flag.b15_selector, 0x0B)
        self.assertEqual(read_flag.b23_flag_value, 0xFF)

    def test_ut_set_flag(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        trans_specific_field = bytearray([QueryFunctionOpcode.SET_FLAG, FlagIDN.REFRESH_EN, 0x0C, 0x0D, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0x00])
        set_flag = SfSetFlag()
        set_flag.from_bytes(trans_specific_field)
        self.assertEqual(set_flag.b12_opcode, QueryFunctionOpcode.SET_FLAG)
        self.assertEqual(set_flag.b13_idn, FlagIDN.REFRESH_EN)
        self.assertEqual(set_flag.b14_index, 0x0C)
        self.assertEqual(set_flag.b15_selector, 0x0D)
        self.assertEqual(set_flag.b23_flag_value, 0xFF)

    def test_ut_clear_flag(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        trans_specific_field = bytearray([QueryFunctionOpcode.CLEAR_FLAG, FlagIDN.WRITEBOOSTER_EN, 0x0E, 0x0F, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0x00])
        clr_flag = SfClearFlag()
        clr_flag.from_bytes(trans_specific_field)
        self.assertEqual(clr_flag.b12_opcode, QueryFunctionOpcode.CLEAR_FLAG)
        self.assertEqual(clr_flag.b13_idn, FlagIDN.WRITEBOOSTER_EN)
        self.assertEqual(clr_flag.b14_index, 0x0E)
        self.assertEqual(clr_flag.b15_selector, 0x0F)
        self.assertEqual(clr_flag.b23_flag_value, 0xFF)

    def test_ut_toggle_flag(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        trans_specific_field = bytearray([QueryFunctionOpcode.TOGGLE_FLAG, FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN, 0x10, 0x11, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0x00])
        toggle_flag = SfToggleFlag()
        toggle_flag.from_bytes(trans_specific_field)
        self.assertEqual(toggle_flag.b12_opcode, QueryFunctionOpcode.TOGGLE_FLAG)
        self.assertEqual(toggle_flag.b13_idn, FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)
        self.assertEqual(toggle_flag.b14_index, 0x10)
        self.assertEqual(toggle_flag.b15_selector, 0x11)
        self.assertEqual(toggle_flag.b23_flag_value, 0xFF)

    def test_ut_nop(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        trans_specific_field = bytearray([QueryFunctionOpcode.NOP, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                          0x00, 0x00, 0x00, 0x00])
        nop = SfNop()
        nop.from_bytes(trans_specific_field)
        self.assertEqual(nop.b12_opcode, QueryFunctionOpcode.NOP)


class TestNopIn(ApiTestBase):
    def setUp(self) -> None:
        ExecuteCMD.clear()

    def test_ut_nop_in(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        cmd_resp = bytearray([0x20, 0x40, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        sense_data = bytearray([0x00]) * 20
        cmd_tag = bytearray([0xAA])
        cmd_timestamp = bytearray([0x00, 0x01, 0x23, 0x45])
        resp_tag = bytearray([0xBB])
        resp_timestamp = bytearray([0x54, 0x32, 0x10, 0x00])
        entry = cmd_resp + sense_data + bytearray([0x00]) + cmd_tag + cmd_timestamp + resp_tag + resp_timestamp + bytearray([0x00]) * 9

        logger.info("Check NOP IN 72B & from_bytes() mapping")
        resp = NopInResponse()
        resp.raw_data = entry
        resp.upiu.from_bytes(entry)
        resp.b53_cmd_tag = entry[53]
        resp.l54_cmd_timestamp = int.from_bytes(entry[54:58], byteorder='big')
        resp.b58_resp_tag = entry[58]
        resp.l59_resp_timestamp = int.from_bytes(entry[59:63], byteorder='big')
        # cmd = cast(IsCmdUpiuEntry, cmd)
        # resp.data = _buf_mngr.get_payload(cmd.param.l42_data_address_offset, cmd.param.l46_data_length)

        self.assertEqual(resp.upiu.b0_transaction_type, UPIUTransactionType.NOP_IN)
        self.assertEqual(resp.upiu.b1_flags, 0x40)
        self.assertEqual(resp.upiu.b3_tasktag, 0xFF)
        self.assertEqual(resp.upiu.b6_response, 0x00)
        self.assertEqual(resp.upiu.b8_total_ehs_length, 0x00)
        self.assertEqual(resp.upiu.b9_device_information, 0x00)
        self.assertEqual(resp.upiu.w10_data_segment_length, 0x00)

        self.assertEqual(resp.b53_cmd_tag, 0xAA)
        self.assertEqual(resp.l54_cmd_timestamp, 0x00012345)
        self.assertEqual(resp.b58_resp_tag, 0xBB)
        self.assertEqual(resp.l59_resp_timestamp, 0x54321000)

        self.assertEqual(resp.b32_sense_data.w_sense_data_length, 0)
        self.assertEqual(resp.b32_sense_data.b0_response_code, 0)
        self.assertEqual(resp.b32_sense_data.b2_sense_key, 0)
        self.assertEqual(resp.b32_sense_data.l3_information, 0)
        self.assertEqual(resp.b32_sense_data.b7_additional_sense_length, 0)
        self.assertEqual(resp.b32_sense_data.l8_command_specific_information, 0)
        self.assertEqual(resp.b32_sense_data.b12_asc, 0)
        self.assertEqual(resp.b32_sense_data.b13_ascq, 0)
