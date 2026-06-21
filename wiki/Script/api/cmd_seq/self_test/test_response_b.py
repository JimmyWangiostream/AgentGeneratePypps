import inspect
from typing import cast

from Script.api.self_test.base import ApiTestBase
from Script.api import (shared, ExecuteCMD,
                        Dcmd5ResetType,
                        PATTERN_ASSERT_BUFFER_MANAGER_FAIL_CYCLE_INDICATOR_NOT_FOUND,
                        SfReadDescriptor, TaskManagementFunction, ConfigDescriptor410, ConfigDescriptorHeader410, ConfigDescriptorUnit410, MemoryType, ProvisioningType)
from Script.api.ufs_api import WellKnownLUN, init_tester_to_unit_ready, DescriptorIDN
from Script.api.ufs_api.upiu import BaseWrite10, BaseRead10
from Script.api.cmd_seq.response import CommandResponse, TaskMgmtResponse, QueryResponse, CmdSeqInitialFlowResponse, CmdSeqTestUnitReadyResponse, NopInResponse, CmdSeqTaskMgmtDummyResponse, get_scsi_status_str, get_sense_key_str, get_asc_ascq_description

_sdk = shared.sdk
logger = shared.logger


class TestCmdSeqResponse(ApiTestBase):

    def setUp(self) -> None:
        ExecuteCMD.clear()

    def printout_init_flow_resp(self, resp: CmdSeqInitialFlowResponse) -> None:
        logger.debug("%s" % resp.__class__.__name__)
        logger.debug("  l32_delay_time = %d us" % resp.l32_delay_time)
        logger.debug("  w36_wait_queue_empty = %s" % bool(resp.w36_wait_queue_empty))
        logger.debug("  l40_link_startup_time = %d us" % resp.l40_link_startup_time)
        logger.debug("  l44_nop_out_time = %d us" % resp.l44_nop_out_time)
        logger.debug("  l48_init_flag_time = %d us" % resp.l48_init_flag_time)

    def printout_cmdseq_test_unit_ready_resp(self, resp: CmdSeqTestUnitReadyResponse) -> None:
        logger.debug("%s" % resp.__class__.__name__)
        logger.debug("  b2_lun = %d" % resp.b2_lun)
        logger.debug("  l3_timeout = %d us" % resp.l3_timeout)
        logger.debug("  l32_delay_time = %d us" % resp.l32_delay_time)
        logger.debug("  w36_wait_queue_empty = %s" % bool(resp.w36_wait_queue_empty))
        logger.debug("  l40_test_unit_ready_time = %d us" % resp.l40_test_unit_ready_time)

    def printout_command_response(self, resp: CommandResponse) -> None:
        scsi_status = get_scsi_status_str(resp)
        sense_key = get_sense_key_str(resp)
        asc_ascq = get_asc_ascq_description(resp)
        logger.debug("%s" % resp.__class__.__name__)
        logger.debug("  UPIU")
        logger.debug("    b1_flags %d" % resp.upiu.b1_flags)
        logger.debug("    b2_lun %d" % resp.upiu.b2_lun)
        logger.debug("    b3_tasktag %d" % resp.upiu.b3_tasktag)
        logger.debug("    b4_iid %d" % resp.upiu.b4_iid)
        logger.debug("    b4_command_set_type %d" % resp.upiu.b4_command_set_type)
        logger.debug("    b5_ext_iid %d" % resp.upiu.b5_ext_iid)
        logger.debug("    b6_response %d" % resp.upiu.b6_response)
        logger.debug("    b7_status %d" % resp.upiu.b7_status)
        logger.debug("    b8_total_ehs_length %d" % resp.upiu.b8_total_ehs_length)
        logger.debug("    b9_device_information %d" % resp.upiu.b9_device_information)
        logger.debug("    w10_data_segment_length %d" % resp.upiu.w10_data_segment_length)
        logger.debug("    l12_residual_transfer_count %d" % resp.upiu.l12_residual_transfer_count)
        logger.debug("  b32_sense_data: %s " % resp.b32_sense_data)
        logger.debug("    SCSI status = %s, Sense Key = %s, ASC/ASCQ Description = %s" % (scsi_status, sense_key, asc_ascq))
        logger.debug("    w_sense_data_length %d" % resp.b32_sense_data.w_sense_data_length)
        logger.debug("    b0_valid %d" % resp.b32_sense_data.b0_valid)
        logger.debug("    b0_response_code %d" % resp.b32_sense_data.b0_response_code)
        logger.debug("    b2_filemark %d" % resp.b32_sense_data.b2_filemark)
        logger.debug("    b2_eom %d" % resp.b32_sense_data.b2_eom)
        logger.debug("    b2_ili %d" % resp.b32_sense_data.b2_ili)
        logger.debug("    b2_sense_key %d" % resp.b32_sense_data.b2_sense_key)
        logger.debug("    l3_information %d" % resp.b32_sense_data.l3_information)
        logger.debug("    b7_additional_sense_length %d" % resp.b32_sense_data.b7_additional_sense_length)
        logger.debug("    l8_command_specific_information %d" % resp.b32_sense_data.l8_command_specific_information)
        logger.debug("    b12_asc %d" % resp.b32_sense_data.b12_asc)
        logger.debug("    b13_ascq %d" % resp.b32_sense_data.b13_ascq)
        logger.debug("    b14_fruc %d" % resp.b32_sense_data.b14_fruc)
        logger.debug("    w15_sksv %d" % resp.b32_sense_data.w15_sksv)
        logger.debug("    w15_sense_key_specific %d" % resp.b32_sense_data.w15_sense_key_specific)
        logger.debug("  b53_cmd_tag %d" % resp.b53_cmd_tag)
        logger.debug("  l54_cmd_timestamp %d" % resp.l54_cmd_timestamp)
        logger.debug("  b58_resp_tag %d" % resp.b58_resp_tag)
        logger.debug("  l59_resp_timestamp %d" % resp.l59_resp_timestamp)
        logger.debug("  data %s" % resp.data)

    def printout_query_response(self, resp: QueryResponse) -> None:
        logger.debug("%s" % resp.__class__.__name__)
        logger.debug("  UPIU")
        logger.debug("    b1_flags %d" % resp.upiu.b1_flags)
        logger.debug("    b3_tasktag %d" % resp.upiu.b3_tasktag)
        logger.debug("    b5_query_function %d" % resp.upiu.b5_query_function)
        logger.debug("    b6_query_response %d" % resp.upiu.b6_query_response)
        logger.debug("    b8_total_ehs_length %d" % resp.upiu.b8_total_ehs_length)
        logger.debug("    b9_device_information %d" % resp.upiu.b9_device_information)
        logger.debug("    w10_data_segment_length %d" % resp.upiu.w10_data_segment_length)
        logger.debug("    u12_specific_fields %s" % resp.upiu.u12_specific_fields)

    def printout_specific_field_read_desc(self, sf: SfReadDescriptor) -> None:
        logger.debug("%s" % sf.__class__.__name__)
        logger.debug("    b12_opcode %d" % sf.b12_opcode)
        logger.debug("    b13_idn %d" % sf.b13_idn)
        logger.debug("    b14_index %d" % sf.b14_index)
        logger.debug("    b15_selector %d" % sf.b15_selector)
        logger.debug("    w18_length %d" % sf.w18_length)

    def printout_config_desc_header(self, cfg_desc_hdr: ConfigDescriptorHeader410) -> None:
        logger.debug("%s" % cfg_desc_hdr.__class__.__name__)
        logger.debug("    b0_length %d" % cfg_desc_hdr.b0_length)
        logger.debug("    b1_descriptor_idn %d" % cfg_desc_hdr.b1_descriptor_idn)
        logger.debug("    b2_conf_desc_continue %d" % cfg_desc_hdr.b2_conf_desc_continue)
        logger.debug("    b3_boot_enable %d" % cfg_desc_hdr.b3_boot_enable)
        logger.debug("    b4_descr_access_en %d" % cfg_desc_hdr.b4_descr_access_en)
        logger.debug("    b5_init_power_mode %d" % cfg_desc_hdr.b5_init_power_mode)
        logger.debug("    b6_high_priority_lun %d" % cfg_desc_hdr.b6_high_priority_lun)
        logger.debug("    b7_secure_removal_type %d" % cfg_desc_hdr.b7_secure_removal_type)
        logger.debug("    b8_init_active_icc_level %d" % cfg_desc_hdr.b8_init_active_icc_level)
        logger.debug("    w9_periodic_rtc_update %d" % cfg_desc_hdr.w9_periodic_rtc_update)
        logger.debug("    b11_hpb_control %d" % cfg_desc_hdr.b11_hpb_control)
        logger.debug("    b12_rpmb_region_enable %d" % cfg_desc_hdr.b12_rpmb_region_enable)
        logger.debug("    b13_rpmb_region1_size %d" % cfg_desc_hdr.b13_rpmb_region1_size)
        logger.debug("    b14_rpmb_region2_size %d" % cfg_desc_hdr.b14_rpmb_region2_size)
        logger.debug("    b15_rpmb_region3_size %d" % cfg_desc_hdr.b15_rpmb_region3_size)
        logger.debug("    b16_write_booster_buffer_preserve_user_space_en %d" % cfg_desc_hdr.b16_write_booster_buffer_preserve_user_space_en)
        logger.debug("    b17_write_booster_buffer_type %d" % cfg_desc_hdr.b17_write_booster_buffer_type)
        logger.debug("    l18_num_shared_write_booster_buffer_alloc_units %d" % cfg_desc_hdr.l18_num_shared_write_booster_buffer_alloc_units)

    def printout_config_desc_unit(self, cfg_desc_unit: ConfigDescriptorUnit410) -> None:
        logger.debug("%s" % cfg_desc_unit.__class__.__name__)
        logger.debug("    b0_lu_enable %d" % cfg_desc_unit.b0_lu_enable)
        logger.debug("    b1_boot_lun_id %d" % cfg_desc_unit.b1_boot_lun_id)
        logger.debug("    b2_lu_write_protect %d" % cfg_desc_unit.b2_lu_write_protect)
        logger.debug("    b3_memory_type %d" % cfg_desc_unit.b3_memory_type)
        logger.debug("    l4_num_alloc_units %d" % cfg_desc_unit.l4_num_alloc_units)
        logger.debug("    b8_data_reliability %d" % cfg_desc_unit.b8_data_reliability)
        logger.debug("    b9_logical_block_size %d" % cfg_desc_unit.b9_logical_block_size)
        logger.debug("    b10_provisioning_type %d" % cfg_desc_unit.b10_provisioning_type)
        logger.debug("    w11_context_capabilities %d" % cfg_desc_unit.w11_context_capabilities)
        logger.debug("    w16_lu_max_active_hpb_region %d" % cfg_desc_unit.w16_lu_max_active_hpb_region)
        logger.debug("    w18_hpb_pinned_region_start_idx %d" % cfg_desc_unit.w18_hpb_pinned_region_start_idx)
        logger.debug("    w20_num_hpb_pinned_regions %d" % cfg_desc_unit.w20_num_hpb_pinned_regions)
        logger.debug("    l22_lu_num_write_booster_buffer_alloc_units %d" % cfg_desc_unit.l22_lu_num_write_booster_buffer_alloc_units)

    def printout_task_mgmt_response(self, resp: TaskMgmtResponse) -> None:
        logger.debug("%s" % resp.__class__.__name__)
        logger.debug("  UPIU")
        logger.debug("    b1_flags %d" % resp.upiu.b1_flags)
        logger.debug("    b2_lun %d" % resp.upiu.b2_lun)
        logger.debug("    b3_tasktag %d" % resp.upiu.b3_tasktag)
        logger.debug("    b4_iid %d" % resp.upiu.b4_iid)
        logger.debug("    b5_ext_iid %d" % resp.upiu.b5_ext_iid)
        logger.debug("    b6_response %d" % resp.upiu.b6_response)
        logger.debug("    b8_total_ehs_length %d" % resp.upiu.b8_total_ehs_length)
        logger.debug("    w10_data_segment_length %d" % resp.upiu.w10_data_segment_length)
        logger.debug("    l12_output_parameter1 %s" % resp.upiu.l12_output_parameter1)
        logger.debug("    l16_output_parameter2 %s" % resp.upiu.l16_output_parameter2)

    def printout_task_mgmt_dummy_response(self, resp: CmdSeqTaskMgmtDummyResponse) -> None:
        logger.debug("%s" % resp.__class__.__name__)
        logger.debug("  b0_transaction_type %d" % resp.b0_transaction_type)
        logger.debug("  b1_function_code %d" % resp.b1_function_code)
        logger.debug("  b2_abort_tag %d" % resp.b2_abort_tag)
        logger.debug("  l32_delay_time %d" % resp.l32_delay_time)
        logger.debug("  w36_wait_queue_empty %d" % resp.w36_wait_queue_empty)
        logger.debug("  l54_send_cmd_timestamp %d" % resp.l54_send_cmd_timestamp)
        logger.debug("  b58_abort_tag %d" % resp.b58_abort_tag)
        logger.debug("  l59_abort_timestamp %d" % resp.l59_abort_timestamp)

    def _test_cmd_seq_init_flow(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore
        init_flow = ExecuteCMD.CmdSeqInitialFlow()
        init_flow.set_option(wait_queue_empty=True, delay_time=0)
        ExecuteCMD.enqueue(init_flow)

        ExecuteCMD.send(clear_on_success=False)

        resp = ExecuteCMD.read_response(0)
        self.assertIsInstance(resp, CmdSeqInitialFlowResponse)
        self.printout_init_flow_resp(resp)

    def _test_cmd_seq_test_unit_ready(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore
        tur = ExecuteCMD.CmdSeqTestUnitReady()
        tur.set_option(WellKnownLUN.UFS_DEVICE, wait_queue_empty=True, timeout=100000)
        ExecuteCMD.enqueue(tur)

        ExecuteCMD.send(clear_on_success=False)

        resp = ExecuteCMD.read_response(0)
        self.assertIsInstance(resp, CmdSeqTestUnitReadyResponse)
        self.printout_cmdseq_test_unit_ready_resp(resp)

    def _test_test_unit_ready(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore
        tur = ExecuteCMD.TestUnitReady()
        tur.assign(0)
        tur.set_option(wait_queue_empty=True, timeout=100000)
        ExecuteCMD.enqueue(tur)

        ExecuteCMD.send(QD=1, clear_on_success=False)

        resp = ExecuteCMD.read_response(0)
        self.assertIsInstance(resp, CommandResponse)
        logger.debug("Test Unit Ready")
        self.printout_command_response(resp)

        ExecuteCMD.clear()

    def _test_combine_init_flow_test_unit_ready(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        init_flow = ExecuteCMD.CmdSeqInitialFlow()
        init_flow.set_option(wait_queue_empty=True, delay_time=0)
        ExecuteCMD.enqueue(init_flow)

        tur = ExecuteCMD.CmdSeqTestUnitReady()
        tur.set_option(0, wait_queue_empty=True, timeout=100000)
        ExecuteCMD.enqueue(tur)

        tur2 = ExecuteCMD.CmdSeqTestUnitReady()
        tur2.set_option(WellKnownLUN.UFS_DEVICE, wait_queue_empty=True, timeout=100000)
        ExecuteCMD.enqueue(tur2)

        tur3 = ExecuteCMD.TestUnitReady()
        tur3.assign(WellKnownLUN.UFS_DEVICE)
        tur3.set_option(wait_queue_empty=True, timeout=0)
        ExecuteCMD.enqueue(tur3)

        ExecuteCMD.send(clear_on_success=False)

        i = 0
        resp = ExecuteCMD.read_response(i)
        self.assertIsInstance(resp, CmdSeqInitialFlowResponse)
        logger.debug("[%d] InitFlowResponse %s" % (i, resp))
        self.printout_init_flow_resp(resp)
        i = 1
        resp2 = ExecuteCMD.read_response(i)
        self.assertIsInstance(resp2, CmdSeqTestUnitReadyResponse)
        logger.debug("[%d] CMD SEQ Test Unit Ready %s" % (i, resp2))
        self.printout_cmdseq_test_unit_ready_resp(resp2)
        i = 2
        resp3 = ExecuteCMD.read_response(i)
        self.assertIsInstance(resp3, CmdSeqTestUnitReadyResponse)
        logger.debug("[%d] CMD SEQ Test Unit Ready %s" % (i, resp3))
        self.printout_cmdseq_test_unit_ready_resp(resp3)
        i = 3
        resp4 = ExecuteCMD.read_response(i)
        self.assertIsInstance(resp4, CommandResponse)
        logger.debug("[%d] CommandResponse Test Unit Ready %s" % (i, resp4))
        self.printout_command_response(resp4)

    def _test_write10_manual(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore
        init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)

        # w_data = bytearray([0x5A]) * 4096
        w_data = bytearray([0xBE, 0xEF]) * 2048
        w_len = 3
        lun = 0
        lba = 0

        write10 = ExecuteCMD.Write10()
        write10.assign(lun, lba, w_len, fua=1)
        write10.set_option(manual_mode=True)
        write10.data = w_data * 3
        ExecuteCMD.enqueue(write10)

        ExecuteCMD.send(QD=1, clear_on_success=False)

        resp = ExecuteCMD.read_response(0)
        self.assertIsInstance(resp, CommandResponse)
        logger.debug("CommandResponse Write10 %s" % resp)
        self.printout_command_response(resp)

    def _test_read10_manual(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore
        init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)

        r_len = 3
        lun = 0
        lba = 0

        read10 = ExecuteCMD.Read10()
        read10.assign(lun, lba, r_len)
        read10.set_option(manual_mode=True)
        ExecuteCMD.enqueue(read10)

        ExecuteCMD.send(QD=1, clear_on_success=False)

        resp = ExecuteCMD.read_response(0)
        self.assertIsInstance(resp, CommandResponse)
        logger.debug("CommandResponse Read10 %s" % resp)
        self.printout_command_response(resp)

        ExecuteCMD.clear()

    def _test_write10_read10_unmap_manual(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore
        init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)

        data_a = bytearray([0xDE, 0xAD]) * 2048  # 4kB
        data_b = bytearray([0xBE, 0xEF]) * 2048  # 4kB
        wr_len = 3
        lun = 0
        cmd_indices = []

        write10 = ExecuteCMD.Write10()
        write10.assign(lun, 0, wr_len, fua=1)
        write10.set_option(manual_mode=True)
        write10.data = data_a * wr_len
        i = ExecuteCMD.enqueue(write10)
        cmd_indices.append(i)

        write10 = ExecuteCMD.Write10()
        write10.assign(lun, 1, wr_len, fua=1)
        write10.set_option(manual_mode=True)
        write10.data = data_b * wr_len
        i = ExecuteCMD.enqueue(write10)
        cmd_indices.append(i)

        read10 = ExecuteCMD.Read10()
        read10.assign(lun, 0, wr_len)
        read10.set_option(manual_mode=True)
        i = ExecuteCMD.enqueue(read10)
        cmd_indices.append(i)

        unmap = ExecuteCMD.Unmap()
        unmap.assign(lun, 0, wr_len - 1)
        unmap.set_option(wait_queue_empty=True)
        i = ExecuteCMD.enqueue(unmap)
        cmd_indices.append(i)

        read10 = ExecuteCMD.Read10()
        read10.assign(lun, 0, wr_len + 1)
        read10.set_option(manual_mode=True)
        i = ExecuteCMD.enqueue(read10)
        cmd_indices.append(i)

        ExecuteCMD.send(QD=10, clear_on_success=False)

        for idx in cmd_indices:
            resp = ExecuteCMD.read_response(idx)
            self.assertIsInstance(resp, CommandResponse)
            logger.debug("[%d] CommandResponse %s" % (idx, resp))
            self.printout_command_response(resp)
            if idx == cmd_indices[-1]:
                self.assertEqual(resp.data[0:4096], bytearray(4096))
                self.assertEqual(resp.data[4096:8192], bytearray(4096))
                self.assertEqual(resp.data[8192:12288], data_b)
                self.assertEqual(resp.data[12288:16384], data_b)

    def _test_write10_read10_error(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore
        init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)

        wr_len = 3
        lun = 0
        lba = 0xFFFFFFFE
        cmd_indices = []

        write10 = ExecuteCMD.Write10()
        write10.assign(lun, lba, wr_len, fua=1)
        write10.set_option(wait_queue_empty=True)
        i = ExecuteCMD.enqueue(write10)
        cmd_indices.append(i)

        read10 = ExecuteCMD.Read10()
        read10.assign(lun, lba, wr_len)
        read10.set_option(wait_queue_empty=True)
        i = ExecuteCMD.enqueue(read10)
        cmd_indices.append(i)

        ExecuteCMD.send(clear_on_success=False)

        for idx in cmd_indices:
            try:
                resp = ExecuteCMD.read_response(idx)
                self.assertIsInstance(resp, CommandResponse)
                logger.debug("[%d] CommandResponse %s" % (idx, resp))
                self.printout_command_response(resp)
            except PATTERN_ASSERT_BUFFER_MANAGER_FAIL_CYCLE_INDICATOR_NOT_FOUND as e:
                logger.error("Expected error: PATTERN_ASSERT_BUFFER_MANAGER_FAIL_CYCLE_INDICATOR_NOT_FOUND")

    def _test_task_mgmt_bad_lun_response(self) -> None:  # SDK bug: TM response always success
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore
        init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)

        lun = 64  # Bad LUN
        tm_func = TaskManagementFunction.QUERY_TASK

        w = ExecuteCMD.Write10()
        w.assign(0, 0, 1, 0)
        i = ExecuteCMD.enqueue(w)

        w_new = cast(BaseRead10, ExecuteCMD._cmd_list[i])  # Query read10
        tm = ExecuteCMD.TaskManagement()
        tm.assign(lun, w.upiu.b4_iid, tm_func, lun, w_new.upiu.b3_tasktag, w_new.upiu.b4_iid)
        j = ExecuteCMD.enqueue(tm)

        ExecuteCMD.send(clear_on_success=False)

        resp1 = ExecuteCMD.read_response(i)
        resp2 = ExecuteCMD.read_response(j)  # Query TM

        self.assertIsInstance(resp1, CommandResponse)
        self.printout_command_response(resp1)
        self.assertIsInstance(resp2, TaskMgmtResponse)
        self.printout_task_mgmt_response(resp2)

    def _test_task_mgmt_abort_response(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore
        init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)

        lun = 0
        tm_func = TaskManagementFunction.ABORT_TASK

        w = ExecuteCMD.Write10()
        w.assign(lun, 0, 1, 0)
        i = ExecuteCMD.enqueue(w)

        r = ExecuteCMD.Read10()
        r.assign(lun, 0, 1)
        j = ExecuteCMD.enqueue(r)

        r_new = cast(BaseRead10, ExecuteCMD._cmd_list[j])  # Abort read10
        tm = ExecuteCMD.TaskManagement()
        tm.assign(lun, tm_func, lun, r_new.upiu.b3_tasktag, r_new.upiu.b4_iid)
        k = ExecuteCMD.enqueue(tm)

        ExecuteCMD.send(clear_on_success=False)

        resp1 = ExecuteCMD.read_response(i)
        resp3 = ExecuteCMD.read_response(k)
        # resp2 = ExecuteCMD.read_response(j)  # aborted cmd, can't get

        self.assertIsInstance(resp1, CommandResponse)
        self.printout_command_response(resp1)
        # self.assertIsInstance(resp2, CmdSeqTaskMgmtDummyResponse)  # Aborted cmd, replaced with TM dummy resp
        # self.printout_task_mgmt_dummy_response(resp2)
        self.assertIsInstance(resp3, TaskMgmtResponse)
        self.printout_task_mgmt_response(resp3)


    def _test_query_response(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore
        for desc_idn, index, selector in [(0xFF, 0x00, 0x00),  # Bad desc_idn
                                          (0x00, 0xFF, 0x00),  # Bad index
                                          (0x00, 0x00, 0xFF),  # Bad selector
                                          ]:
            init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)

            device_desc = ExecuteCMD.ReadDescriptor()
            logger.info(f"Test {device_desc.__class__.__name__}, desc_idn {desc_idn}, index {index}, selector {selector}")

            device_desc.assign(desc_idn, index=index, selector=selector)
            ExecuteCMD.enqueue(device_desc)
            ExecuteCMD.send(clear_on_success=False)

            resp = ExecuteCMD.read_response(0)
            self.assertIsInstance(resp, QueryResponse)
            read_desc_sf = SfReadDescriptor()
            read_desc_sf.from_bytes(resp.upiu.u12_specific_fields)
            self.printout_query_response(resp)
            self.printout_specific_field_read_desc(read_desc_sf)

            ExecuteCMD.clear()

    def _test_query_read_config_desc_response(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore
        init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)

        lun_id = 0
        cmd_idx_l  = []

        selector = 0
        for index in range(4):
            rd = ExecuteCMD.ReadDescriptor()
            rd.assign(DescriptorIDN.CONFIGURATION, index, selector)
            i = ExecuteCMD.enqueue(rd)
            cmd_idx_l.append(i)

        ExecuteCMD.send(clear_on_success=False)

        resp_l = [ExecuteCMD.read_response(i) for i in cmd_idx_l]

        for i, resp in enumerate(resp_l):
            self.assertIsInstance(resp, QueryResponse)
            read_descriptor = SfReadDescriptor()
            read_descriptor.from_bytes(resp.upiu.u12_specific_fields)
            self.printout_specific_field_read_desc(read_descriptor)
            self.assertEqual(read_descriptor.b12_opcode, 1)
            self.assertEqual(read_descriptor.b13_idn, DescriptorIDN.CONFIGURATION)
            self.assertEqual(read_descriptor.b14_index, i)
            self.assertEqual(read_descriptor.b15_selector, selector)

            # data
            config_desc = ConfigDescriptor410()
            config_desc.from_bytes(resp.data)

            # config_desc.config_desc_header.from_bytes(resp.data[0:22])
            self.printout_config_desc_header(config_desc.header)
            self.assertEqual(config_desc.header.b0_length, 22 + 26 * 8)
            self.assertEqual(config_desc.header.b1_descriptor_idn, DescriptorIDN.CONFIGURATION)

            # offset = 22
            for unit_desc in config_desc.units:
                logger.info(f"[LUN-{lun_id}] Read unit config descriptor")
                # unit_desc.from_bytes(resp.data[offset:offset+26])
                self.printout_config_desc_unit(unit_desc)
                if lun_id in (0, 1, 2):
                    self.assertEqual(unit_desc.b1_boot_lun_id, lun_id)
                    self.assertEqual(unit_desc.b0_lu_enable, 1)
                    if lun_id == 0:
                        self.assertEqual(unit_desc.b3_memory_type, MemoryType.NORMAL)
                        self.assertEqual(unit_desc.b10_provisioning_type, ProvisioningType.THIN_PROVISIONING_ERASE)
                    else:  # LUN-1, 2
                        self.assertEqual(unit_desc.b3_memory_type, MemoryType.ENHANCED_1)
                        self.assertEqual(unit_desc.b10_provisioning_type, ProvisioningType.THIN_PROVISIONING_ERASE)
                else:
                    self.assertEqual(unit_desc.b0_lu_enable, 0)
                self.assertEqual(unit_desc.b9_logical_block_size, 12)

                # offset += 26
                lun_id += 1

    def _test_nop_out_in(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore
        init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)

        nop_out = ExecuteCMD.NopOut()
        ExecuteCMD.enqueue(nop_out)

        ExecuteCMD.send(clear_on_success=False)

        resp = ExecuteCMD.read_response(0)
        logger.debug("Response [%s]" % type(resp))
        self.assertIsInstance(resp, NopInResponse)

    def _test_task_mgmt_dummy_response(self) -> None:

        x = bytearray(b'$\x00\x00%\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00$$\x03\x0e&\xd0%\x03\x0e+\xe5\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        y = bytearray(b'\xff\xfe$%\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00$\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00%%\x03\x0e&\xd5$\x03\x0e+\xe8\x00\x00\x00\x00\x00\x00\x00\x00\x00')

        resp = ExecuteCMD.identify_response(x)
        logger.info(f"Check response type: {type(resp)}")
        self.assertIsInstance(resp, TaskMgmtResponse)
        self.printout_task_mgmt_response(resp)

        resp2 = ExecuteCMD.identify_response(y)
        logger.info(f"Check response type: {type(resp2)}")
        self.assertIsInstance(resp2, CmdSeqTaskMgmtDummyResponse)
        self.printout_task_mgmt_dummy_response(resp2)
