from abc import ABC, abstractmethod
import struct
from typing import Any, Tuple
import bitstruct
from Script.api.struct_helper import *

class Descptor_Att_Flag(PacketParserComposerABC):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(16)
        super().__init__(payload, start_offset = AUTO_OFFSET, end_offset = AUTO_OFFSET)
        self.QueryType = self.add_field(0, 1, 'little')
        self.QueryCount = self.add_field(2, 3, 'little')
        self.Index = self.add_field(4, 7, 'little')
        self.ValueOft = self.add_field(8, 11, 'little')
        self.IndexLen = self.add_field(12, 15, 'little')

class ICSUnit(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.ICS_block_index = self.add_field(0, 1, 'little')
        self.Invalid_logical_plane = self.add_field(2, 2, 'little')
        
class OpenVBInfoUnit(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.logical_vb = self.add_field(0,3,'little')
        self.physical_vb = self.add_field(4,7,'little')
        self.first_empty_CE = self.add_field(8,11,'little')
        self.first_empty_plane = self.add_field(12,15,'little')
        self.first_empty_physical_page = self.add_field(16,19,'little')
        self.first_empty_node = self.add_field(20,23,'little')

class OpenVBInfo(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.SLC_L2 = OpenVBInfoUnit(payload, 0, 23)
        self.WB = OpenVBInfoUnit(payload, 24, 47)
        self.TLC_L2 = OpenVBInfoUnit(payload, 48, 71)
        self.TLC_L1 = OpenVBInfoUnit(payload, 72, 95)
        self.SLC_GC = OpenVBInfoUnit(payload, 96, 119)
        self.TLC_GC = OpenVBInfoUnit(payload, 120, 143)
        self.PTE = OpenVBInfoUnit(payload, 144, 167)
        self.LOG = OpenVBInfoUnit(payload, 168, 191)
        self.SWAP = OpenVBInfoUnit(payload, 192, 215)
        self.SWAP_for_RAID = OpenVBInfoUnit(payload, 216, 239)

class SmartInfo8329Bics8(PacketParserABC):
    """
    Python translation of SMART_INFO_8329_BICS8 with field order and sizes
    exactly aligned to the provided C typedef. Assumes LITTLE-ENDIAN layout.
    Change '<' to '<' in unpack calls if your payload is big-endian.

    C type mapping:
      - unsigned long long -< Q (8 bytes)
      - unsigned long      -< I (4 bytes)
      - unsigned short     -< H (2 bytes)
      - unsigned char      -< B (1 byte)
    """
    def __init__(self) -> None:
        # host (180 bytes)
        self.host_total_write_cmd_count = 0
        self.host_total_read_cmd_count = 0
        self.host_total_trim_cmd_count = 0
        self.host_total_flush_cmd_count = 0
        self.host_total_ssu_cmd_count = 0
        self.host_total_write_count = 0
        self.host_total_read_count = 0
        self.host_total_uncor_err_cnt = 0
        self.host_trig_hpb_reset_count = 0
        self.host_config_hpb_backdoor_cnt = 0
        self.ufs_fw_ver_record = [0]*8
        self.host_total_write_fua_count = 0
        self.host_total_write_booster_count = 0
        self.host_write_fua_cmd_count = 0
        self.host_total_discard_cmd_count = 0
        self.host_discard_cmd_count_less_than_32KB = 0
        self.host_discard_count_less_than_32KB = 0
        self.host_total_discard_count = 0
        self.host_purge_enable_count = 0
        self.host_purge_disable_count = 0
        self.host_total_verify_cmd_cnt = 0
        self.host_refresh_enable_count = 0
        self.host_refresh_disable_count = 0
        self.host_enable_turbo_write_count = 0
        self.host_disable_turbo_write_count = 0
        self.host_read_fail_lca = 0
        self.host_read_fail_pca = 0

        # ftl (128 bytes)
        self.pte_gc_trigger_count = 0
        self.pte_gc_rd_trigger_count = 0
        self.data_gc_trigger_count = 0
        self.force_slc_gc_trigger_count = 0
        self.force_tlc_gc_trigger_count = 0
        self.wl_slc_gc_trigger_count = 0
        self.wl_tlc_gc_trigger_count = 0
        self.rd_slc_gc_trigger_count = 0
        self.rd_tlc_gc_trigger_count = 0
        self.revoke_trigger_count = 0
        self.bkops_tlc_gc_trigger_count = 0
        self.bkops_slc_gc_trigger_count = 0
        self.purge_slc_gc_trigger_count = 0
        self.purge_tlc_gc_trigger_count = 0
        self.fbo_slc_gc_trigger_count = 0
        self.fbo_tlc_gc_trigger_count = 0
        self.pre_read_mistrig_count = 0
        self.pre_read_enable_count = 0
        self.pre_read_abort_count = 0
        self.pre_read_unc_retry_count = 0
        self.pre_load_reset_count = 0
        self.pre_load_enable_count = 0
        self.pre_load_gain_count = 0
        self.prdh_rand_trig_cnt = 0
        self.prdh_seq_trig_cnt = 0
        self.prdh_scan_pass_cnt = 0
        self.prdh_scan_fail_cnt = 0
        self.prdh_patrol_trig_cnt = 0
        self.rebuild_flush_pte_count = 0
        self.rsv_ftl_0 = [0]*6
        self.trim_fg_job_merge_cnt = 0
        self.rsv_ftl = [0]*4

        # nand (128 bytes)
        self.total_d1_program_count = 0
        self.total_d3_program_count = 0
        self.d1_erase_fail_count = 0
        self.d3_erase_fail_count = 0
        self.d1_program_fail_count = 0
        self.d3_program_fail_count = 0
        self.erase_suspend_count = 0
        self.program_suspend_count = 0
        self.d1_read_retry_ok_count = 0
        self.d3_read_retry_ok_count = 0
        self.d1_read_retry_fail_count = 0
        self.d3_read_retry_fail_count = 0
        self.aom_read_retry_ok_count = 0
        self.aom_read_retry_fail_count = 0
        self.d1_softbit_recovery_ok_count = 0
        self.d3_softbit_recovery_ok_count = 0
        self.d1_softbit_recovery_fail_count = 0
        self.d3_softbit_recovery_fail_count = 0
        self.d1_raid_recovery_ok_count = 0
        self.d3_raid_recovery_ok_count = 0
        self.d1_raid_recovery_fail_count = 0
        self.d3_raid_recovery_fail_count = 0
        self.raid_q_err_over_thres_count = 0
        self.empty_page_cnt_caused_by_prog_fail = 0
        self.cop0_tag_shortage_to_skip_raid_cnt = 0
        self.total_d1_program_count_wo_rd = 0
        self.total_d3_program_count_wo_rd = 0
        self.rsv_nand = [0]*16

        # checkcount (128 bytes)
        self.l2_vb_count = [0]*2
        self.max_one_for_one_gc_count = 0
        self.gc_fill_dummy_count = 0
        self.gc_fast_release_vc_zero_source_cnt = 0
        self.rd_src_vb_vld_cnt_zero = 0
        self.wl_src_vb_vld_cnt_zero = 0
        self.replace_die_src_vb_vld_cnt_zero = 0
        self.imcomplete_src_vb_vld_cnt_zero = 0
        self.close_l2_vld_cnt_zero = 0
        self.refresh_l2_flush_count = 0
        self.refresh_l2_remap_count = 0
        self.ts_level_1_cnt = 0
        self.ts_level_2_cnt = 0
        self.ts_speed_control_cnt = 0
        self.ts_speed_resume_cnt = 0
        self.rebuild_tbl_err_cnt = [0]*14
        self.fast_release_zero_valid_cnt = 0
        self.tlc_vb_count = [0]*6
        self.refresh_gc_target_count = 0
        self.l2_continue_program_count = 0

        # DME (debug) 316 bytes
        self.DME_PA_LAYER_ERR_CNT = [0]*4
        self.DME_DL_LAYER_ERR_CNT = [0]*16
        self.DME_N_LAYER_ERR_CNT = [0]*4
        self.DME_T_LAYER_ERR_CNT = [0]*8
        self.dme_interrupt_status = [0]*3
        self.dme_error_bit_map1 = [0]*3
        self.dme_tx_power_mode_status = [0]*3
        self.dme_rx_power_mode_status = [0]*3
        self.dme_error_mphy = [0]*3
        self.dme_error_dl = [0]*3
        self.dme_error_nl = [0]*3
        self.dme_error_tl = [0]*3
        self.pa_total_err_cnt = 0
        self.dl_total_err_cnt = 0
        self.nl_total_err_cnt = 0
        self.tl_total_err_cnt = 0
        self.DME_ERR_MAP0 = 0
        self.link_lost_cnt = 0
        self.link_fail_cnt = 0
        self.link_up_cnt = 0
        self.pwr_chg_fail_cnt = 0
        self.link_endpoint_rst_cnt = 0
        self.link_success_cnt = 0
        self.hib8_cnt = 0
        self.dme_error_fifo = [0]*2
        self.dme_rsv = [0]*76
        self.nand_error_idx = 0
        self.nand_error_info = [0]*10
        self.nand_error_ce = [0]*10
        self.nand_error_block = [0]*10
        self.nand_error_wl = [0]*10
        self.nand_error_page = [0]*10
        self.max_gc_life_time = 0
        self.rsv4B = 0
        self.fw_build_config = 0
        self.rsv_debug = [0]*3
        self.smart_ver = 0

        # temp (start of the rest — not guaranteed in comment, but defined)
        self.ts_level_3_cnt = 0
        self.ts_maximum = 0
        self.create_l2_wait_free_vb_tlc_part = 0
        self.create_l2_wait_free_pte = 0
        self.st1_full_hit_count = 0
        self.st1_full_wait_max_time = 0
        self.gc_total_release_source_count = 0
        self.gc_release_src = [0]*16
        self.gc_first_src_vb_vc_ratio = [0]*11
        self.gc_rebuild_rtv_valid_cnt_mismatch = 0
        self.gc_load_pte_bmp_fail_cnt = 0
        self.refresh_l2_uecc_happen = 0
        self.refresh_gc_uecc_happen = 0
        self.d1_safe_scan_exec_cnt = 0
        self.d3_safe_scan_exec_cnt = 0
        self.d1_max_erase_cnt = 0
        self.d3_max_erase_cnt = 0
        self.move_back_erase_fail = 0
        self.erase_multi_fail_and_erase_again_fail = 0
        self.pef_erase_fail = 0
        self.pef_prog_fail = 0
        self.recov_read_uecc = 0
        self.move_back_recov_read_uecc = 0
        self.move_back_recov_prog_fail = 0
        self.reprg_read_uecc = 0
        self.move_back_reprg_read_uecc = 0
        self.move_back_reprg_prog_fail = 0
        self.bbt_skip_erase_multi_fail_and_erase_again_pass = 0
        self.bbt_save_erase_multi_fail_and_erase_again_fail = 0
        self.bbt_save_program_back_ok = 0
        self.bbt_skip_program_back_fail = 0
        self.bbt_save_program_multi_fail_with_fail_and_cecc = 0
        self.total_cis_update_count = 0
        self.flush_cnt = [0]*5
        self.flush_dummy_cnt = [0]*5
        self.ts_nand_maximum = [0]*8
        self.ts_nand_minimum = [0]*8

        # hpb (80 bytes)
        self.hpb_read_cmd_cnt = 0
        self.hpb_read_buf_cmd_cnt = 0
        self.hpb_decrypt_pass = 0
        self.hpb_decrypt_fail = 0
        self.hpb_dirty_region_cnt = 0
        self.hpb_dcm_read_cnt = 0
        self.hpb_dcm_read_buffer_cnt = 0
        self.hpb_push_job_fail_cnt = 0
        self.hpb_dcm_write_buffer_buf_id_0x02_cnt = 0
        self.hpb_backup_hpb_data = 0
        self.hpb_inactive_cnt = 0
        self.hpb_unmap_inactive_cnt = 0
        self.hpb_againg_inactive_cnt = 0
        self.hpb_active_cnt = 0
        self.hpb_region_fail_cnt = 0
        self.hpb_prefetch_cnt = 0
        self.hpb_seq_map_out_of_range_cnt = 0
        self.hpb_single_read_decrypt_pass_cnt = 0
        self.hpb_single_read_decrypt_fail_cnt = 0
        self.hpb_seq_map_in_range_cnt = 0
        self.pte_gc_move_node_cnt = 0
        self.log_collect_node_cnt = 0
        self.prog_fail_reason = [0]*7
        self.mp_level_assert_0x400C = 0

        # power / misc following
        self.power_good_count = 0
        self.power_bad_count = 0
        self.auto_standby_count = 0
        self.ssu_awake_count = 0
        self.flh_vdt_num = 0
        self.l2_prog_fail_cnt = 0
        self.l2_prog_fail_only_8k_fail_cnt = 0
        self.prdh_force_vb_scan_cnt = 0
        self.read_refresh_cnt = [0]*17
        self.raid_decode_fail_err_no = 0
        self.rsv_2 = [0]*1
        self.raid_decode_fail_pca = 0
        self.raid_decode_pass_pca = 0
        self.raid_decode_pass_lca = 0
        self.aom_banking_cnt = 0
        self.uecc_pca = [[0]*3 for _ in range(4)]
        self.uecc_lca = [[0]*3 for _ in range(2)]
        self.uecc_cnt = [0]*4
        self.gc_refresh_fail_count = 0
        self.read_ECC_over_cnt = 0
        self.vcc_vdt_cnt = 0
        self.erase_fail_reason = [0]*7
        self.debug_assert_record = [0]*16
        self.debug_assert_record_pointer = 0
        self.raid_decode_err = [[0]*12 for _ in range(2)]
        self.ctrl_max_ts_code = 0
        self.ctrl_min_ts_code = 0
        self.skip_max_pe_case = 0
        self.ctrl_ts_over_85C_cnt = 0
        self.ce_prog_fail_cnt = [0]*8
        self.ce_erase_fail_cnt = [0]*8
        self.d1_gc_prog_count = 0
        self.d3_gc_prog_count = 0
        self.slc_wl_check_count = 0
        self.slc_wl_trigger_count = [0]*4
        self.swap_from_slc_pool = 0
        self.swap_from_mlc_pool = 0
        self.swap_from_mlc_over_4 = 0
        self.used_over_gc_th = 0
        self.slc_pe_lower_multiple_times_mlc = 0
        self.erase_trig_cnt = [0]*40
        self.hist_avg_slc_pe = 0
        self.hist_avg_mlc_pe = 0
        self.ce_read_fail_cnt = [0]*8
        self.his_err_io_cmd_cnt = 0
        self.table_max_erase_cnt = 0
        self.ufs_refresh_total_cnt = 0
        self.prdh_force_refresh_trig_scan_cnt = 0
        self.prdh_log_update_count = 0
        self.prdh_scan_entry_cnt = 0
        self.prdh_scan_open_entry_cnt = 0
        self.prdh_seq_scan_cnt = 0
        self.prdh_scan_entry_skip_cnt = 0
        self.prdh_scan_done_cnt = 0
        self.prdh_force_refresh_trig_refresh_cnt = 0
        self.gc_read_back_verify_fail = 0
        self.gc_read_back_verify_pass = 0
        self.l2_read_back_verify_fail = 0
        self.config_cnt_before_lock = 0
        self.config_lun_running_spor = 0
        self.his_err_tm_cnt = 0
        self.his_err_query_cnt = 0
        self.table_rtbb_uecc_count = 0
        self.vu_multi_gear_write_on_off_cnt = 0
        self.his_err_sync_cmd_cnt = 0
        self.auto_read_op = [0]*8
        self.load_l1_uecc = [0]*2
        self.ep_chk_trig_cnt = [0]*3
        self.ep_chk_pass_cnt = 0
        self.ep_chk_fail_cnt = [0]*3
        self.ISR_CNT = [0]*2
        self.CRC_CNT = [0]*2
        self.PREV_INT = [0]*2
        self.CURR_INT = [0]*2
        self.read_check_fail_times = 0
        self.bkops_exec_time = 0
        self.hist_avg_ehn_pe = 0
        self.flush_cache_to_l1_cnt = 0
        self.hist_avg_hid_pe = 0
        self.prdh_scan_range_unexpected = 0
        self.ep_chk_fail_count_by_group = [0]*7
        self.ep_chk_fail_pca = 0
        self.purge_time = [0]*4
        self.load_swap_parity_uecc = [0]*3
        self.get_attr_time = [0]*2
        self.mphy_wo_refclk_num = 0
        self.data_our_err_srst = 0
        self.cis_double_prog_for_erase_ok_count = 0
        self.cis_double_prog_for_erase_ng_count = 0
        self.fbo_flush_D2_SLC_L2 = 0
        self.fbo_flush_D2_TLC_L2 = 0
        self.fbo_flush_D1_SLC_L2 = 0
        self.factory_reset_cnt = 0
        self.rpmb_block_cnt = 0
        self.total_SLC_use_ec_of_TLC = 0
        self.amount_of_SLC_write = 0
        self.ssu_active_cnt = 0
        self.ssu_sleep_cnt = 0
        self.ssu_power_down_cnt = 0
        self.ssu_deep_sleep_cnt = 0
        self.write_booster_flush_enable_cnt = 0
        self.write_booster_flush_disable_cnt = 0
        self.inquiry_cnt = 0
        self.LU_config_cnt = 0
        self.format_unit_cnt = 0
        self.mode_select_cnt = 0
        self.mode_sense_cnt = 0
        self.pre_fetch_cnt = 0
        self.read_capacity_cnt = 0
        self.report_luns_cnt = 0
        self.request_sense_cnt = 0
        self.send_diagnostic_cnt = 0
        self.test_unit_ready_cnt = 0
        self.mode_select_sp1_cnt = 0
        self.sec_protocol_in_cnt = 0
        self.sec_protocol_out_cnt = 0
        self.AuthWriteReq_Count = 0
        self.AuthReadReq_Count = 0
        self.read_buffer_cnt = 0
        self.write_buffer_cnt = 0
        self.query_cnt = 0
        self.task_abort_cnt = 0
        self.lun_reset_cnt = 0
        self.query_req_read_cnt = 0
        self.query_req_write_cnt = 0
        self.AuthReadFrame = [0]*4
        self.AuthWriteFrame = [0]*4
        self.fdeviceinit_cnt = 0
        self.AuthErrReq_Count = 0
        self.SecurityProtoclInfo_cnt = 0
        self.fatal_dme_error_count = 0
        self.tag_write_cmd_count = 0
        self.tag_write_count = 0
        self.d1_rrt_correct_count = [0]*11
        self.d3_rrt_correct_count = [0]*32
        self.read_stage_error_cnt_slc = [0]*4
        self.read_stage_error_cnt_tlc = [0]*6
        self.host_data_L2 = [[0]*3 for _ in range(3)]
        self.host_data_L1 = [0]*3
        self.FG_GC_TLC_partition_slc_early_gc = [0]*4
        self.FG_GC_TLC_partition_WL = [0]*4
        self.FG_GC_TLC_partition_FBO = [0]*4
        self.FG_GC_TLC_partition_RD = [0]*4
        self.FG_GC_TLC_partition_Urgent_GC = [0]*4
        self.BG_GC_TLC_partition_slc = [0]*4
        self.BG_GC_TLC_partition_tlc = [0]*4
        self.FG_GC_SLC_partition_WL = 0
        self.FG_GC_SLC_partition_FBO = 0
        self.FG_GC_SLC_partition_RD = 0
        self.FG_GC_SLC_partition_Urgent_GC = 0
        self.FG_GC_SLC_partition_Purge = 0
        self.swap_tlc_cursor1_cnt = 0
        self.swap_tlc_gc = 0
        self.swap_slc_gc = 0
        self.swap_tlc_ssu = [0]*3
        self.swap_slc_ssu = 0
        self.swap_tlc_gc_ssu = 0
        self.swap_slc_gc_ssu = 0
        self.swap_tlc_switch_part = [0]*3
        self.swap_slc_switch_part = 0
        self.dummy_node_2_GC_target = [0]*3
        self.GC_target_refresh = [0]*3
        self.L2_refresh = [0]*3
        self.gc_reselect_source_trig_count = 0
        self.gc_reselect_source_vc = 0
        self.DefragSize = 0
        self.HID_Count = 0
        self.HID_GC_trigger_count = 0
        self.HID_GC_SLC_partition = 0
        self.HID_GC_TLC_partition_SLC = 0
        self.HID_GC_TLC_partition_TLC = 0
        self.l1_prog_conti_flush_tlc_cnt = 0
        self.update_list_block_count = 0
        self.update_index_block_count = 0
        self.update_pt_block_count = 0
        self.create_l2_wait_free_vb_slc_part = 0
        self.query_start_timestamp = 0
        self.query_end_timestamp = 0
        self.ndep_pass_pca = 0
        self.ndep_fail_cnt = 0
        self.rb_verify_total_read_page_count = 0
        self.prev_gc_recovery_target = 0
        self.gc_parity_read_back_verify_fail = 0
        self.rsv = 0

    def from_bytes(self, payload: bytearray) -> None:
        o = 0
        # --- host ---
        (self.host_total_write_cmd_count,
         self.host_total_read_cmd_count,
         self.host_total_trim_cmd_count,
         self.host_total_flush_cmd_count,
         self.host_total_ssu_cmd_count,
         self.host_total_write_count,
         self.host_total_read_count) = struct.unpack_from('<QQQQQQQ', payload, o); o += 8*7

        (self.host_total_uncor_err_cnt,
         self.host_trig_hpb_reset_count,
         self.host_config_hpb_backdoor_cnt) = struct.unpack_from('<III', payload, o); o += 4*3

        self.ufs_fw_ver_record = list(struct.unpack_from('<IIIIIIII', payload, o)); o += 4*8

        (self.host_total_write_fua_count,
         self.host_total_write_booster_count) = struct.unpack_from('<QQ', payload, o); o += 16

        (self.host_write_fua_cmd_count,
         self.host_total_discard_cmd_count) = struct.unpack_from('<II', payload, o); o += 8

        (self.host_discard_cmd_count_less_than_32KB,) = struct.unpack_from('<I', payload, o); o += 4
        (self.host_discard_count_less_than_32KB,
         self.host_total_discard_count) = struct.unpack_from('<QQ', payload, o); o += 16

        (self.host_purge_enable_count,
         self.host_purge_disable_count,
         self.host_total_verify_cmd_cnt,
         self.host_refresh_enable_count,
         self.host_refresh_disable_count,
         self.host_enable_turbo_write_count,
         self.host_disable_turbo_write_count,
         self.host_read_fail_lca) = struct.unpack_from('<IIIIIIII', payload, o); o += 32

        (self.host_read_fail_pca,) = struct.unpack_from('<I', payload, o); o += 4

        # --- ftl ---
        (self.pte_gc_trigger_count,
         self.pte_gc_rd_trigger_count,
         self.data_gc_trigger_count,
         self.force_slc_gc_trigger_count,
         self.force_tlc_gc_trigger_count,
         self.wl_slc_gc_trigger_count,
         self.wl_tlc_gc_trigger_count,
         self.rd_slc_gc_trigger_count,
         self.rd_tlc_gc_trigger_count,
         self.revoke_trigger_count,
         self.bkops_tlc_gc_trigger_count,
         self.bkops_slc_gc_trigger_count,
         self.purge_slc_gc_trigger_count,
         self.purge_tlc_gc_trigger_count,
         self.fbo_slc_gc_trigger_count,
         self.fbo_tlc_gc_trigger_count,
         self.pre_read_mistrig_count,
         self.pre_read_enable_count,
         self.pre_read_abort_count,
         self.pre_read_unc_retry_count,
         self.pre_load_reset_count,
         self.pre_load_enable_count,
         self.pre_load_gain_count,
         self.prdh_rand_trig_cnt,
         self.prdh_seq_trig_cnt,
         self.prdh_scan_pass_cnt,
         self.prdh_scan_fail_cnt,
         self.prdh_patrol_trig_cnt) = struct.unpack_from('<' + 'I'*28, payload, o); o += 4*28

        (self.rebuild_flush_pte_count,) = struct.unpack_from('<H', payload, o); o += 2
        self.rsv_ftl_0 = list(struct.unpack_from('<' + 'B'*6, payload, o)); o += 6
        (self.trim_fg_job_merge_cnt,) = struct.unpack_from('<I', payload, o); o += 4
        self.rsv_ftl = list(struct.unpack_from('<' + 'B'*4, payload, o)); o += 4

        # --- nand ---
        (self.total_d1_program_count,
         self.total_d3_program_count) = struct.unpack_from('<QQ', payload, o); o += 16
        (self.d1_erase_fail_count,
         self.d3_erase_fail_count,
         self.d1_program_fail_count,
         self.d3_program_fail_count,
         self.erase_suspend_count,
         self.program_suspend_count) = struct.unpack_from('<' + 'H'*6, payload, o); o += 12
        (self.d1_read_retry_ok_count,
         self.d3_read_retry_ok_count,
         self.d1_read_retry_fail_count,
         self.d3_read_retry_fail_count,
         self.aom_read_retry_ok_count,
         self.aom_read_retry_fail_count,
         self.d1_softbit_recovery_ok_count,
         self.d3_softbit_recovery_ok_count,
         self.d1_softbit_recovery_fail_count,
         self.d3_softbit_recovery_fail_count,
         self.d1_raid_recovery_ok_count,
         self.d3_raid_recovery_ok_count,
         self.d1_raid_recovery_fail_count,
         self.d3_raid_recovery_fail_count,
         self.raid_q_err_over_thres_count,
         self.empty_page_cnt_caused_by_prog_fail,
         self.cop0_tag_shortage_to_skip_raid_cnt) = struct.unpack_from('<' + 'I'*17, payload, o); o += 4*17
        (self.total_d1_program_count_wo_rd,
         self.total_d3_program_count_wo_rd) = struct.unpack_from('<QQ', payload, o); o += 16
        self.rsv_nand = list(struct.unpack_from('<' + 'B'*16, payload, o)); o += 16

        # --- checkcount ---
        self.l2_vb_count = list(struct.unpack_from('<II', payload, o)); o += 8
        (self.max_one_for_one_gc_count,
         self.gc_fill_dummy_count,
         self.gc_fast_release_vc_zero_source_cnt,
         self.rd_src_vb_vld_cnt_zero,
         self.wl_src_vb_vld_cnt_zero,
         self.replace_die_src_vb_vld_cnt_zero,
         self.imcomplete_src_vb_vld_cnt_zero,
         self.close_l2_vld_cnt_zero,
         self.refresh_l2_flush_count,
         self.refresh_l2_remap_count) = struct.unpack_from('<' + 'I'*10, payload, o); o += 40
        (self.ts_level_1_cnt,
         self.ts_level_2_cnt,
         self.ts_speed_control_cnt,
         self.ts_speed_resume_cnt) = struct.unpack_from('<' + 'H'*4, payload, o); o += 8
        self.rebuild_tbl_err_cnt = list(struct.unpack_from('<' + 'H'*14, payload, o)); o += 28
        (self.fast_release_zero_valid_cnt,) = struct.unpack_from('<I', payload, o); o += 4
        self.tlc_vb_count = list(struct.unpack_from('<' + 'H'*6, payload, o)); o += 12
        (self.refresh_gc_target_count,
         self.l2_continue_program_count) = struct.unpack_from('<II', payload, o); o += 8

        # --- DME (debug) ---
        self.DME_PA_LAYER_ERR_CNT = list(struct.unpack_from('<' + 'H'*4, payload, o)); o += 8
        self.DME_DL_LAYER_ERR_CNT = list(struct.unpack_from('<' + 'H'*16, payload, o)); o += 32
        self.DME_N_LAYER_ERR_CNT = list(struct.unpack_from('<' + 'H'*4, payload, o)); o += 8
        self.DME_T_LAYER_ERR_CNT = list(struct.unpack_from('<' + 'H'*8, payload, o)); o += 16
        self.dme_interrupt_status = list(struct.unpack_from('<' + 'I'*3, payload, o)); o += 12
        self.dme_error_bit_map1 = list(struct.unpack_from('<' + 'B'*3, payload, o)); o += 3
        self.dme_tx_power_mode_status = list(struct.unpack_from('<' + 'B'*3, payload, o)); o += 3
        self.dme_rx_power_mode_status = list(struct.unpack_from('<' + 'B'*3, payload, o)); o += 3
        self.dme_error_mphy = list(struct.unpack_from('<' + 'B'*3, payload, o)); o += 3
        self.dme_error_dl = list(struct.unpack_from('<' + 'B'*3, payload, o)); o += 3
        self.dme_error_nl = list(struct.unpack_from('<' + 'B'*3, payload, o)); o += 3
        self.dme_error_tl = list(struct.unpack_from('<' + 'B'*3, payload, o)); o += 3
        (self.pa_total_err_cnt,
         self.dl_total_err_cnt,
         self.nl_total_err_cnt,
         self.tl_total_err_cnt,
         self.DME_ERR_MAP0,
         self.link_lost_cnt,
         self.link_fail_cnt,
         self.link_up_cnt,
         self.pwr_chg_fail_cnt,
         self.link_endpoint_rst_cnt,
         self.link_success_cnt,
         self.hib8_cnt) = struct.unpack_from('<' + 'I'*12, payload, o); o += 48
        self.dme_error_fifo = list(struct.unpack_from('<' + 'I'*2, payload, o)); o += 8
        self.dme_rsv = list(struct.unpack_from('<' + 'B'*76, payload, o)); o += 76
        (self.nand_error_idx,) = struct.unpack_from('<B', payload, o); o += 1
        self.nand_error_info = list(struct.unpack_from('<' + 'B'*10, payload, o)); o += 10
        self.nand_error_ce = list(struct.unpack_from('<' + 'B'*10, payload, o)); o += 10
        self.nand_error_block = list(struct.unpack_from('<' + 'H'*10, payload, o)); o += 20
        self.nand_error_wl = list(struct.unpack_from('<' + 'H'*10, payload, o)); o += 20
        self.nand_error_page = list(struct.unpack_from('<' + 'B'*10, payload, o)); o += 10
        (self.max_gc_life_time,
         self.rsv4B) = struct.unpack_from('<II', payload, o); o += 8
        (self.fw_build_config,) = struct.unpack_from('<B', payload, o); o += 1
        self.rsv_debug = list(struct.unpack_from('<' + 'B'*3, payload, o)); o += 3
        (self.smart_ver,) = struct.unpack_from('<I', payload, o); o += 4

        # --- temp & following sections ---
        (self.ts_level_3_cnt,
         self.ts_maximum) = struct.unpack_from('<HH', payload, o); o += 4
        (self.create_l2_wait_free_vb_tlc_part,
         self.create_l2_wait_free_pte,
         self.st1_full_hit_count,
         self.st1_full_wait_max_time,
         self.gc_total_release_source_count) = struct.unpack_from('<' + 'I'*5, payload, o); o += 20
        self.gc_release_src = list(struct.unpack_from('<' + 'I'*16, payload, o)); o += 64
        self.gc_first_src_vb_vc_ratio = list(struct.unpack_from('<' + 'I'*11, payload, o)); o += 44
        (self.gc_rebuild_rtv_valid_cnt_mismatch,
         self.gc_load_pte_bmp_fail_cnt,
         self.refresh_l2_uecc_happen,
         self.refresh_gc_uecc_happen,
         self.d1_safe_scan_exec_cnt,
         self.d3_safe_scan_exec_cnt,
         self.d1_max_erase_cnt,
         self.d3_max_erase_cnt) = struct.unpack_from('<' + 'I'*8, payload, o); o += 32
        (self.move_back_erase_fail,
         self.erase_multi_fail_and_erase_again_fail) = struct.unpack_from('<HH', payload, o); o += 4
        (self.pef_erase_fail,
         self.pef_prog_fail) = struct.unpack_from('<BB', payload, o); o += 2
        (self.recov_read_uecc,
         self.move_back_recov_read_uecc,
         self.move_back_recov_prog_fail,
         self.reprg_read_uecc,
         self.move_back_reprg_read_uecc,
         self.move_back_reprg_prog_fail,
         self.bbt_skip_erase_multi_fail_and_erase_again_pass,
         self.bbt_save_erase_multi_fail_and_erase_again_fail,
         self.bbt_save_program_back_ok,
         self.bbt_skip_program_back_fail,
         self.bbt_save_program_multi_fail_with_fail_and_cecc) = struct.unpack_from('<' + 'H'*11, payload, o); o += 22
        (self.total_cis_update_count,) = struct.unpack_from('<I', payload, o); o += 4
        self.flush_cnt = list(struct.unpack_from('<' + 'I'*5, payload, o)); o += 20
        self.flush_dummy_cnt = list(struct.unpack_from('<' + 'I'*5, payload, o)); o += 20
        self.ts_nand_maximum = list(struct.unpack_from('<' + 'B'*8, payload, o)); o += 8
        self.ts_nand_minimum = list(struct.unpack_from('<' + 'B'*8, payload, o)); o += 8

        # hpb 80B
        (self.hpb_read_cmd_cnt,
         self.hpb_read_buf_cmd_cnt,
         self.hpb_decrypt_pass,
         self.hpb_decrypt_fail,
         self.hpb_dirty_region_cnt,
         self.hpb_dcm_read_cnt,
         self.hpb_dcm_read_buffer_cnt,
         self.hpb_push_job_fail_cnt,
         self.hpb_dcm_write_buffer_buf_id_0x02_cnt,
         self.hpb_backup_hpb_data,
         self.hpb_inactive_cnt,
         self.hpb_unmap_inactive_cnt,
         self.hpb_againg_inactive_cnt,
         self.hpb_active_cnt,
         self.hpb_region_fail_cnt,
         self.hpb_prefetch_cnt,
         self.hpb_seq_map_out_of_range_cnt,
         self.hpb_single_read_decrypt_pass_cnt,
         self.hpb_single_read_decrypt_fail_cnt,
         self.hpb_seq_map_in_range_cnt) = struct.unpack_from('<' + 'I'*20, payload, o); o += 80
        (self.pte_gc_move_node_cnt,
         self.log_collect_node_cnt) = struct.unpack_from('<II', payload, o); o += 8
        self.prog_fail_reason = list(struct.unpack_from('<' + 'H'*7, payload, o)); o += 14
        (self.mp_level_assert_0x400C,) = struct.unpack_from('<H', payload, o); o += 2

        # power / misc
        (self.power_good_count,
         self.power_bad_count,
         self.auto_standby_count,
         self.ssu_awake_count) = struct.unpack_from('<QQQQ', payload, o); o += 32
        (self.flh_vdt_num,
         self.l2_prog_fail_cnt,
         self.l2_prog_fail_only_8k_fail_cnt,
         self.prdh_force_vb_scan_cnt) = struct.unpack_from('<' + 'I'*4, payload, o); o += 16
        self.read_refresh_cnt = list(struct.unpack_from('<' + 'H'*17, payload, o)); o += 34
        (self.raid_decode_fail_err_no,) = struct.unpack_from('<B', payload, o); o += 1
        self.rsv_2 = list(struct.unpack_from('<B', payload, o)); o += 1
        (self.raid_decode_fail_pca,
         self.raid_decode_pass_pca,
         self.raid_decode_pass_lca,
         self.aom_banking_cnt) = struct.unpack_from('<' + 'I'*4, payload, o); o += 16
        # uecc_pca[4][3] (u32)
        flat = list(struct.unpack_from('<' + 'I'*12, payload, o)); o += 48
        self.uecc_pca = [flat[i*3:(i+1)*3] for i in range(4)]
        # uecc_lca[2][3] (u32)
        flat = list(struct.unpack_from('<' + 'I'*6, payload, o)); o += 24
        self.uecc_lca = [flat[i*3:(i+1)*3] for i in range(2)]
        self.uecc_cnt = list(struct.unpack_from('<' + 'I'*4, payload, o)); o += 16
        (self.gc_refresh_fail_count,) = struct.unpack_from('<H', payload, o); o += 2
        (self.read_ECC_over_cnt,) = struct.unpack_from('<I', payload, o); o += 4
        (self.vcc_vdt_cnt,) = struct.unpack_from('<H', payload, o); o += 2
        self.erase_fail_reason = list(struct.unpack_from('<' + 'H'*7, payload, o)); o += 14
        self.debug_assert_record = list(struct.unpack_from('<' + 'H'*16, payload, o)); o += 32
        (self.debug_assert_record_pointer,) = struct.unpack_from('<B', payload, o); o += 1
        # raid_decode_err[2][12] (u32)
        flat = list(struct.unpack_from('<' + 'I'*24, payload, o)); o += 96
        self.raid_decode_err = [flat[i*12:(i+1)*12] for i in range(2)]
        (self.ctrl_max_ts_code,
         self.ctrl_min_ts_code,
         self.skip_max_pe_case,
         self.ctrl_ts_over_85C_cnt) = struct.unpack_from('<' + 'I'*4, payload, o); o += 16
        self.ce_prog_fail_cnt = list(struct.unpack_from('<' + 'B'*8, payload, o)); o += 8
        self.ce_erase_fail_cnt = list(struct.unpack_from('<' + 'B'*8, payload, o)); o += 8
        (self.d1_gc_prog_count,
         self.d3_gc_prog_count) = struct.unpack_from('<QQ', payload, o); o += 16
        (self.slc_wl_check_count,) = struct.unpack_from('<I', payload, o); o += 4
        self.slc_wl_trigger_count = list(struct.unpack_from('<' + 'I'*4, payload, o)); o += 16
        (self.swap_from_slc_pool,
         self.swap_from_mlc_pool,
         self.swap_from_mlc_over_4,
         self.used_over_gc_th,
         self.slc_pe_lower_multiple_times_mlc) = struct.unpack_from('<' + 'I'*5, payload, o); o += 20
        self.erase_trig_cnt = list(struct.unpack_from('<' + 'H'*40, payload, o)); o += 80
        (self.hist_avg_slc_pe,
         self.hist_avg_mlc_pe) = struct.unpack_from('<II', payload, o); o += 8
        self.ce_read_fail_cnt = list(struct.unpack_from('<' + 'I'*8, payload, o)); o += 32
        (self.his_err_io_cmd_cnt,
         self.table_max_erase_cnt,
         self.ufs_refresh_total_cnt) = struct.unpack_from('<' + 'I'*3, payload, o); o += 12
        (self.prdh_force_refresh_trig_scan_cnt,
         self.prdh_log_update_count) = struct.unpack_from('<HH', payload, o); o += 4
        (self.prdh_scan_entry_cnt,
         self.prdh_scan_open_entry_cnt,
         self.prdh_seq_scan_cnt,
         self.prdh_scan_entry_skip_cnt,
         self.prdh_scan_done_cnt) = struct.unpack_from('<' + 'I'*5, payload, o); o += 20
        (self.prdh_force_refresh_trig_refresh_cnt,
         self.gc_read_back_verify_fail,
         self.gc_read_back_verify_pass,
         self.l2_read_back_verify_fail) = struct.unpack_from('<' + 'H'*4, payload, o); o += 8
        (self.config_cnt_before_lock,) = struct.unpack_from('<H', payload, o); o += 2
        (self.config_lun_running_spor,) = struct.unpack_from('<B', payload, o); o += 1
        (self.his_err_tm_cnt,
         self.his_err_query_cnt) = struct.unpack_from('<II', payload, o); o += 8
        (self.table_rtbb_uecc_count,
         self.vu_multi_gear_write_on_off_cnt) = struct.unpack_from('<HH', payload, o); o += 4
        (self.his_err_sync_cmd_cnt,) = struct.unpack_from('<I', payload, o); o += 4
        # auto_read_op[8] (u64)
        self.auto_read_op = list(struct.unpack_from('<' + 'Q'*8, payload, o)); o += 64
        self.load_l1_uecc = list(struct.unpack_from('<' + 'H'*2, payload, o)); o += 4
        self.ep_chk_trig_cnt = list(struct.unpack_from('<' + 'I'*3, payload, o)); o += 12
        (self.ep_chk_pass_cnt,) = struct.unpack_from('<I', payload, o); o += 4
        self.ep_chk_fail_cnt = list(struct.unpack_from('<' + 'I'*3, payload, o)); o += 12
        self.ISR_CNT = list(struct.unpack_from('<' + 'I'*2, payload, o)); o += 8
        self.CRC_CNT = list(struct.unpack_from('<' + 'I'*2, payload, o)); o += 8
        self.PREV_INT = list(struct.unpack_from('<' + 'I'*2, payload, o)); o += 8
        self.CURR_INT = list(struct.unpack_from('<' + 'I'*2, payload, o)); o += 8
        (self.read_check_fail_times,
         self.bkops_exec_time,
         self.hist_avg_ehn_pe,
         self.flush_cache_to_l1_cnt,
         self.hist_avg_hid_pe,
         self.prdh_scan_range_unexpected) = struct.unpack_from('<' + 'I'*6, payload, o); o += 24
        self.ep_chk_fail_count_by_group = list(struct.unpack_from('<' + 'I'*7, payload, o)); o += 28
        (self.ep_chk_fail_pca,) = struct.unpack_from('<I', payload, o); o += 4
        self.purge_time = list(struct.unpack_from('<' + 'I'*4, payload, o)); o += 16
        self.load_swap_parity_uecc = list(struct.unpack_from('<' + 'I'*3, payload, o)); o += 12
        self.get_attr_time = list(struct.unpack_from('<' + 'I'*2, payload, o)); o += 8
        (self.mphy_wo_refclk_num,) = struct.unpack_from('<H', payload, o); o += 2
        (self.data_our_err_srst,) = struct.unpack_from('<I', payload, o); o += 4
        (self.cis_double_prog_for_erase_ok_count,
         self.cis_double_prog_for_erase_ng_count) = struct.unpack_from('<HH', payload, o); o += 4
        (self.fbo_flush_D2_SLC_L2,
         self.fbo_flush_D2_TLC_L2,
         self.fbo_flush_D1_SLC_L2) = struct.unpack_from('<' + 'I'*3, payload, o); o += 12
        (self.factory_reset_cnt,) = struct.unpack_from('<H', payload, o); o += 2
        (self.rpmb_block_cnt,
         self.total_SLC_use_ec_of_TLC) = struct.unpack_from('<II', payload, o); o += 8
        (self.amount_of_SLC_write,) = struct.unpack_from('<Q', payload, o); o += 8
        (self.ssu_active_cnt,
         self.ssu_sleep_cnt,
         self.ssu_power_down_cnt,
         self.ssu_deep_sleep_cnt,
         self.write_booster_flush_enable_cnt,
         self.write_booster_flush_disable_cnt,
         self.inquiry_cnt) = struct.unpack_from('<' + 'I'*7, payload, o); o += 28
        (self.LU_config_cnt,
         self.format_unit_cnt,
         self.mode_select_cnt,
         self.mode_sense_cnt,
         self.pre_fetch_cnt,
         self.read_capacity_cnt,
         self.report_luns_cnt,
         self.request_sense_cnt,
         self.send_diagnostic_cnt,
         self.test_unit_ready_cnt,
         self.mode_select_sp1_cnt) = struct.unpack_from('<' + 'B'*11, payload, o); o += 11
        (self.sec_protocol_in_cnt,
         self.sec_protocol_out_cnt,
         self.AuthWriteReq_Count,
         self.AuthReadReq_Count) = struct.unpack_from('<' + 'I'*4, payload, o); o += 16
        (self.read_buffer_cnt,
         self.write_buffer_cnt) = struct.unpack_from('<BB', payload, o); o += 2
        (self.query_cnt,
         self.task_abort_cnt,
         self.lun_reset_cnt) = struct.unpack_from('<' + 'H'*3, payload, o); o += 6
        (self.query_req_read_cnt,
         self.query_req_write_cnt) = struct.unpack_from('<QQ', payload, o); o += 16
        self.AuthReadFrame = list(struct.unpack_from('<' + 'Q'*4, payload, o)); o += 32
        self.AuthWriteFrame = list(struct.unpack_from('<' + 'Q'*4, payload, o)); o += 32
        (self.fdeviceinit_cnt,) = struct.unpack_from('<I', payload, o); o += 4
        (self.AuthErrReq_Count,
         self.SecurityProtoclInfo_cnt) = struct.unpack_from('<BB', payload, o); o += 2
        (self.fatal_dme_error_count,
         self.tag_write_cmd_count,
         self.tag_write_count) = struct.unpack_from('<' + 'I'*3, payload, o); o += 12
        self.d1_rrt_correct_count = list(struct.unpack_from('<' + 'I'*11, payload, o)); o += 44
        self.d3_rrt_correct_count = list(struct.unpack_from('<' + 'I'*32, payload, o)); o += 128
        self.read_stage_error_cnt_slc = list(struct.unpack_from('<' + 'I'*4, payload, o)); o += 16
        self.read_stage_error_cnt_tlc = list(struct.unpack_from('<' + 'I'*6, payload, o)); o += 24
        # host_data_L2[3][3] (u64)
        flat = list(struct.unpack_from('<' + 'Q'*9, payload, o)); o += 72
        self.host_data_L2 = [flat[i*3:(i+1)*3] for i in range(3)]
        # host_data_L1[3] (u64)
        self.host_data_L1 = list(struct.unpack_from('<' + 'Q'*3, payload, o)); o += 24

        # GC 256B (u64 groups)
        self.FG_GC_TLC_partition_slc_early_gc = list(struct.unpack_from('<' + 'Q'*4, payload, o)); o += 32
        self.FG_GC_TLC_partition_WL = list(struct.unpack_from('<' + 'Q'*4, payload, o)); o += 32
        self.FG_GC_TLC_partition_FBO = list(struct.unpack_from('<' + 'Q'*4, payload, o)); o += 32
        self.FG_GC_TLC_partition_RD = list(struct.unpack_from('<' + 'Q'*4, payload, o)); o += 32
        self.FG_GC_TLC_partition_Urgent_GC = list(struct.unpack_from('<' + 'Q'*4, payload, o)); o += 32
        self.BG_GC_TLC_partition_slc = list(struct.unpack_from('<' + 'Q'*4, payload, o)); o += 32
        self.BG_GC_TLC_partition_tlc = list(struct.unpack_from('<' + 'Q'*4, payload, o)); o += 32
        (self.FG_GC_SLC_partition_WL,
         self.FG_GC_SLC_partition_FBO,
         self.FG_GC_SLC_partition_RD,
         self.FG_GC_SLC_partition_Urgent_GC,
         self.FG_GC_SLC_partition_Purge) = struct.unpack_from('<' + 'Q'*5, payload, o); o += 40

        # SWAP 104B
        (self.swap_tlc_cursor1_cnt,
         self.swap_tlc_gc,
         self.swap_slc_gc) = struct.unpack_from('<QQQ', payload, o); o += 24
        self.swap_tlc_ssu = list(struct.unpack_from('<' + 'Q'*3, payload, o)); o += 24
        (self.swap_slc_ssu,
         self.swap_tlc_gc_ssu,
         self.swap_slc_gc_ssu) = struct.unpack_from('<QQQ', payload, o); o += 24
        self.swap_tlc_switch_part = list(struct.unpack_from('<' + 'Q'*3, payload, o)); o += 24
        (self.swap_slc_switch_part,) = struct.unpack_from('<Q', payload, o); o += 8
        self.dummy_node_2_GC_target = list(struct.unpack_from('<' + 'Q'*3, payload, o)); o += 24
        self.GC_target_refresh = list(struct.unpack_from('<' + 'Q'*3, payload, o)); o += 24
        self.L2_refresh = list(struct.unpack_from('<' + 'Q'*3, payload, o)); o += 24

        (self.gc_reselect_source_trig_count,
         self.gc_reselect_source_vc) = struct.unpack_from('<II', payload, o); o += 8
        (self.DefragSize,) = struct.unpack_from('<Q', payload, o); o += 8
        (self.HID_Count,
         self.HID_GC_trigger_count,
         self.HID_GC_SLC_partition,
         self.HID_GC_TLC_partition_SLC,
         self.HID_GC_TLC_partition_TLC,
         self.l1_prog_conti_flush_tlc_cnt,
         self.update_list_block_count,
         self.update_index_block_count,
         self.update_pt_block_count,
         self.create_l2_wait_free_vb_slc_part,
         self.query_start_timestamp,
         self.query_end_timestamp,
         self.ndep_pass_pca) = struct.unpack_from('<' + 'I'*13, payload, o); o += 52
        (self.ndep_fail_cnt,
         self.rb_verify_total_read_page_count,
         self.prev_gc_recovery_target,
         self.gc_parity_read_back_verify_fail) = struct.unpack_from('<' + 'H'*4, payload, o); o += 8
        (self.rsv,) = struct.unpack_from('<B', payload, o); o += 1


class FlashSetting(PacketParserABC):
    def __init__(self) -> None:
        self.Flash_Setting_Version = 0
        self.IC_Version = 0
        self.HW_Version = 0
        self.ROM_Code_Version = 0
        self.M1 = 0
        self.M2 = 0
        self.FW_SVN = 0
        self.FW_Vendor = 0
        self.Vendor_Minor_Code = 0
        self.ROM_Code_Version_Minor = 0
        self.FW_Version_Minor = 0
        self.MakerCode = 0
        self.FlashID = 0
        self.Flash_Cell_Type = 0
        self.Flash_Page_Type = 0
        self.Density_Per_Die = 0
        self.FLH_Technology = 0
        self.Flash_Initialize_Status = 0
        self.X_Preformat_Result = 0
        self.X_CodeBlockFail = 0
        self.X_CodeBlock = 0
        self.X_CodePlane = 0
        self.X_Code2Block = 0
        self.X_InfoBlock = 0
        self.X_InfoPlane = 0
        self.FLH_Quantity = 0
        self.Parallel = 0
        self.Max_Fdevice = 0
        self.Max_PB = 0
        self.Max_LB = 0
        self.Max_Fpage = 0
        self.X_Boot_Header_Page = 0
        self.ECC_Mode = 0
        self.Reserved_51_60 = 0
        self.UFS_PWR_Mode = 0
        self.FLH_VTG = 0
        self.FLH_Mode = 0
        self.FLH_CurrentMode = 0
        self.FLH_Speed_Grade = 0
        self.FLH_Current_Speed_Grade = 0
        self.HW_Max_Write_Speed_Grade = 0
        self.HW_Max_Read_Speed_Grade = 0
        self.Reserved_73_83 = 0
        self.X_GuessPlane = 0
        self.Plane_Per_Die = 0
        self.X_GuessInterleave = 0
        self.FW_Interleave = 0
        self.Ext_Interleave = 0
        self.N_Way_Interleave = 0
        self.Force_NAND_IF_Speed_Mode = 0
        self.DQSA_Write_DLY = 0
        self.DQSA_Read_DLY = 0
        self.DQSB_Write_DLY = 0
        self.DQSB_Read_DLY = 0
        self.DQSA_Write_OFFSET_L = 0
        self.DQSA_Write_OFFSET_H = 0
        self.DQSB_Write_OFFSET_L = 0
        self.DQSB_Write_OFFSET_H = 0
        self.DQSA_Read_OFFSET_L = 0
        self.DQSA_Read_OFFSET_H = 0
        self.DQSB_Read_OFFSET_L = 0
        self.DQSB_Read_OFFSET_H = 0
        self.FCTL_DQ_Reverse_L = 0
        self.FCTL_DQ_Reverse_H = 0
        self.ST_Feature = 0
        self.Multi_Die_Support = 0
        self.Vendor_Minor_Code2 = 0
        self.FW_MAX_WRITE_READ_BUFFER_SIZE = 0
        self.Reserved_113_126 = 0
        self.FFU_Format = 0
        self.FW_UFS_version_M3_128 = 0
        self.FW_UFS_application_M4_129 = 0
        self.Reserved_130 = 0
        self.FFU_Artichect_Version_131_b0_b6 = 0
        self.FFU_Artichect_Version_131_b7 = 0
        self.Reserved_132_299 = 0
        self.Customer_ID_300 = 0
        self.Reserved_301_467 = 0
        self.HM_RPMB_special_case_468 = 0
        self.UFS_Feature_Support_469 = 0
        self.Feature_Reference_470 = 0
        self.Feature_Reference_471 = 0
        self.Feature_Reference_472 = 0
        self.Feature_Reference_473 = 0
        self.Reserved_474_479 = 0
        self.DME_ERR_MAP_History = 0
        self.Reserved_484_495 = 0
        self.DME_ERR_VALUE = 0
        self.DME_ERR_MAP = 0
        self.Assert_Number = 0
        self.Reserved_508_1023 = 0
        self.EVSID_field_name = 0
        self.EVSID_field_SN = 0
        self.SLC_PE_cycles = 0
        self.TLC_PE_cycles = 0
        self.QLC_PE_cycles = 0
        self.PE_cycles_reserved = 0
        self.Reserved_1056_4095 = 0
    def from_bytes(self, payload: bytearray) -> None:
        def unpack_byte(offset: int) -> int:
            return payload[offset]
        
        def unpack_bytes(offset: int, count: int) -> int:
            return int.from_bytes(payload[offset:offset+count], 'big')

        def unpack_bitfield(offset: int, mask: int, shift: int) -> int:
            byte = unpack_byte(offset)
            return (byte & mask) >> shift

        # Assign fields
        self.Flash_Setting_Version = unpack_byte(0)
        self.IC_Version = unpack_bytes(1, 2)
        self.HW_Version = unpack_byte(3)
        self.ROM_Code_Version = unpack_bytes(4, 2)
        self.M1 = unpack_byte(6)
        self.M2 = unpack_byte(7)
        self.FW_SVN = unpack_bytes(8, 3)
        self.FW_Vendor = unpack_byte(11)
        self.Vendor_Minor_Code = unpack_byte(12)
        self.ROM_Code_Version_Minor = unpack_byte(13)
        self.FW_Version_Minor = unpack_bytes(14, 2)
        self.MakerCode = unpack_byte(16)
        self.FlashID = unpack_bytes(17, 6)
        self.Flash_Cell_Type = unpack_byte(23)
        self.Flash_Page_Type = unpack_byte(24)
        self.Density_Per_Die = unpack_byte(25)
        self.FLH_Technology = unpack_byte(26)
        self.Flash_Initialize_Status = unpack_byte(27)
        self.X_Preformat_Result = unpack_byte(28)
        self.X_CodeBlockFail = unpack_byte(29)
        self.X_CodeBlock = unpack_bytes(30, 2)
        self.X_CodePlane = unpack_byte(32)
        self.X_Code2Block = unpack_bytes(33, 2)
        self.X_InfoBlock = unpack_bytes(35, 2)
        self.X_InfoPlane = unpack_byte(37)
        self.FLH_Quantity = unpack_byte(38)
        self.Parallel = unpack_byte(39)
        self.Max_Fdevice = unpack_byte(40)
        self.Max_PB = unpack_bytes(41, 2)
        self.Max_LB = unpack_bytes(43, 2)
        self.Max_Fpage = unpack_bytes(45, 4)
        self.X_Boot_Header_Page = unpack_byte(49)
        self.ECC_Mode = unpack_byte(50)
        self.Reserved_51_60 = unpack_bytes(51, 10)
        self.UFS_PWR_Mode = unpack_byte(61)
        self.FLH_VTG = unpack_byte(62)
        self.FLH_Mode = unpack_byte(63)
        self.FLH_CurrentMode = unpack_byte(64)
        self.FLH_Speed_Grade = unpack_bytes(65, 2)
        self.FLH_Current_Speed_Grade = unpack_bytes(67, 2)
        self.HW_Max_Write_Speed_Grade = unpack_bytes(69, 2)
        self.HW_Max_Read_Speed_Grade = unpack_bytes(71, 2)
        self.Reserved_73_83 = unpack_bytes(73, 11)
        self.X_GuessPlane = unpack_byte(84)
        self.Plane_Per_Die = unpack_byte(85)
        self.X_GuessInterleave = unpack_byte(86)
        self.FW_Interleave = unpack_byte(87)
        self.Ext_Interleave = unpack_byte(88)
        self.N_Way_Interleave = unpack_byte(89)
        self.Force_NAND_IF_Speed_Mode = unpack_byte(90)
        self.DQSA_Write_DLY = unpack_bytes(91, 2)
        self.DQSA_Read_DLY = unpack_bytes(93, 2)
        self.DQSB_Write_DLY = unpack_bytes(95, 2)
        self.DQSB_Read_DLY = unpack_bytes(97, 2)
        self.DQSA_Write_OFFSET_L = unpack_byte(99)
        self.DQSA_Write_OFFSET_H = unpack_byte(100)
        self.DQSB_Write_OFFSET_L = unpack_byte(101)
        self.DQSB_Write_OFFSET_H = unpack_byte(102)
        self.DQSA_Read_OFFSET_L = unpack_byte(103)
        self.DQSA_Read_OFFSET_H = unpack_byte(104)
        self.DQSB_Read_OFFSET_L = unpack_byte(105)
        self.DQSB_Read_OFFSET_H = unpack_byte(106)
        self.FCTL_DQ_Reverse_L = unpack_byte(107)
        self.FCTL_DQ_Reverse_H = unpack_byte(108)
        self.ST_Feature = unpack_byte(109)
        self.Multi_Die_Support = unpack_byte(110)
        self.Vendor_Minor_Code2 = unpack_byte(111)
        self.FW_MAX_WRITE_READ_BUFFER_SIZE = unpack_byte(112)
        self.Reserved_113_126 = unpack_bytes(113, 14)
        self.FFU_Format = unpack_byte(127)
        self.FW_UFS_version_M3_128 = unpack_byte(128)
        self.FW_UFS_application_M4_129 = unpack_byte(129)
        self.Reserved_130 = unpack_byte(130)
        self.FFU_Artichect_Version_131_b0_b6 = unpack_bitfield(131, 0x7F, 0)
        self.FFU_Artichect_Version_131_b7 = unpack_bitfield(131, 0x80, 7)
        self.Reserved_132_299 = unpack_bytes(132, 168)
        self.Customer_ID_300 = unpack_byte(300)
        self.Reserved_301_467 = unpack_bytes(301, 167)
        self.HM_RPMB_special_case_468 = unpack_byte(468)
        self.UFS_Feature_Support_469 = unpack_byte(469)
        self.Feature_Reference_470 = unpack_byte(470)
        self.Feature_Reference_471 = unpack_byte(471)
        self.Feature_Reference_472 = unpack_byte(472)
        self.Feature_Reference_473 = unpack_byte(473)
        self.Reserved_474_479 = unpack_bytes(474, 6)
        self.DME_ERR_MAP_History = unpack_bytes(480, 1)
        self.Reserved_484_495 = unpack_bytes(484, 12)
        self.DME_ERR_VALUE = unpack_bytes(496, 4)
        self.DME_ERR_MAP = unpack_bytes(500, 1)
        self.Assert_Number = unpack_bytes(504, 4)
        self.Reserved_508_1023 = unpack_bytes(508, 516)
        self.EVSID_field_name = unpack_bytes(1024, 8)
        self.EVSID_field_SN = unpack_bytes(1032, 8)
        self.SLC_PE_cycles = unpack_bytes(1040, 2)
        self.TLC_PE_cycles = unpack_bytes(1042, 2)
        self.QLC_PE_cycles = unpack_bytes(1044, 2)
        self.PE_cycles_reserved = unpack_bytes(1046, 5)
        self.Reserved_1056_4095 = unpack_bytes(1056, 3040)

class L2P_PCA(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(116), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.l0_op = self.add_field(0, 3, 'little')
        self.b4_mode = self.add_field(4, 4, 'little')
        self.b5_ce = self.add_field(5, 5, 'little')
        self.b6_plane = self.add_field(6, 6, 'little')
        self.b7_format = self.add_field(7, 7, 'little')
        self.w8_len_4k = self.add_field(8, 9, 'little')
        self.w10_block = self.add_field(10, 11, 'little')
        self.l12_fpage = self.add_field(12, 15, 'little')
        self.l16_force_blk_seed = self.add_field(16, 19, 'little')
        self.b20_lmu = self.add_field(20, 23, 'little')
        self.w24_remap_vb = self.add_field(24, 25, 'little')
        self.w26_rsvd = self.add_field(26, 31, 'little')
        self.b32_attrib = self.add_field(32, 32, 'little')
        self.b33_raidecc_protection = self.add_field(33, 33, 'little')
        self.b34_addr_type = self.add_field(34, 34, 'little')
        self.b35_seq = self.add_field(35, 35, 'little')
        self.b36_invalid_vb_plane = self.add_field(36, 36, 'little')
        self.b37_entry = self.add_field(37, 37, 'little')
        self.b38_plane = self.add_field(38, 38, 'little')
        self.b39_lmu = self.add_field(39, 39, 'little')
        self.b40_ch = self.add_field(40, 40, 'little')
        self.b41_bank = self.add_field(41, 41, 'little')
        self.b42_die_page = self.add_field(42, 42, 'little')
        self.b43_erased_block_cnt = self.add_field(43, 43, 'little')
        self.b44_valid_block_cnt = self.add_field(44, 44, 'little')
        self.b45_block_erased_done = self.add_field(45, 45, 'little')
        self.w46_page = self.add_field(46, 47, 'little')
        self.w48_block = self.add_field(48, 49, 'little')
        self.l50_node = self.add_field(50, 53, 'little')
        self.l54_rsvd = self.add_field(54, 103, 'little')
        self.l104_status = self.add_field(104, 107, 'little')
        self.l108_pca = self.add_field(108, 111, 'little')
        self.l112_lca = self.add_field(112, 115, 'little')

class PCA(PacketParserABC, PacketComposerABC):
    def __init__(self) -> None:
        self.l0_op = 0
        self.b4_mode = 0
        self.b5_ce = 0
        self.b6_plane = 0
        self.b7_format = 0
        self.w8_len_4k = 0
        self.b10_block_l = 0
        self.b11_block_h = 0
        self.l12_fpage = 0
        self.l16_force_blk_seed = 0
        self.b20_lmu = 0
        self.b21_rsvd = 0
        self.w22_rsvd = 0
        self.w24_remap_vb = 0
        self.w26_rsvd = 0
        self.l28_rsvd = 0
        self.b32_attrib = 0
        self.b33_raidecc_protection = 0
        self.b34_addr_type = 0
        self.b35_seq = 0
        self.b36_invalid_vb_plane = 0
        self.b37_entry = 0
        self.b38_plane = 0
        self.b39_lmu = 0
        self.b40_ch = 0
        self.b41_bank = 0
        self.b42_die_page = 0
        self.b43_erased_block_cnt = 0
        self.b44_valid_block_cnt = 0
        self.b45_block_erased_done = 0
        self.w46_page = 0
        self.w48_block = 0
        self.l50_node = 0


    def to_bytes(self) -> bytearray:
        buf = bytearray(54)
        struct.pack_into(
            '<LBBBBHBBLLBBHHHLBBBBBBBBBBBBBBHHL', buf, 0,
            self.l0_op,
            self.b4_mode,
            self.b5_ce,
            self.b6_plane,
            self.b7_format,
            self.w8_len_4k,
            self.b10_block_l,
            self.b11_block_h,
            self.l12_fpage,
            self.l16_force_blk_seed,
            self.b20_lmu,
            self.b21_rsvd,
            self.w22_rsvd,
            self.w24_remap_vb,
            self.w26_rsvd,
            self.l28_rsvd,
            self.b32_attrib,
            self.b33_raidecc_protection,
            self.b34_addr_type,
            self.b35_seq,
            self.b36_invalid_vb_plane,
            self.b37_entry,
            self.b38_plane,
            self.b39_lmu,
            self.b40_ch,
            self.b41_bank,
            self.b42_die_page,
            self.b43_erased_block_cnt,
            self.b44_valid_block_cnt,
            self.b45_block_erased_done,
            self.w46_page,
            self.w48_block,
            self.l50_node
        )
        return buf

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '<LBBBBHBBLLBBHHHLBBBBBBBBBBBBBBHHL'
        unpacked_data = struct.unpack(format_string, payload[0:54])

        self.l0_op = unpacked_data[0]
        self.b4_mode = unpacked_data[1]
        self.b5_ce = unpacked_data[2]
        self.b6_plane = unpacked_data[3]
        self.b7_format = unpacked_data[4]
        self.w8_len_4k = unpacked_data[5]
        self.b10_block_l = unpacked_data[6]
        self.b11_block_h = unpacked_data[7]
        self.l12_fpage = unpacked_data[8]
        self.l16_force_blk_seed = unpacked_data[9]
        self.b20_lmu = unpacked_data[10]
        self.b21_rsvd = unpacked_data[11]
        self.w22_rsvd = unpacked_data[12]
        self.w24_remap_vb = unpacked_data[13]
        self.w26_rsvd = unpacked_data[14]
        self.l28_rsvd = unpacked_data[15]
        self.b32_attrib = unpacked_data[16]
        self.b33_raidecc_protection = unpacked_data[17]
        self.b34_addr_type = unpacked_data[18]
        self.b35_seq = unpacked_data[19]
        self.b36_invalid_vb_plane = unpacked_data[20]
        self.b37_entry = unpacked_data[21]
        self.b38_plane = unpacked_data[22]
        self.b39_lmu = unpacked_data[23]
        self.b40_ch = unpacked_data[24]
        self.b41_bank = unpacked_data[25]
        self.b42_die_page = unpacked_data[26]
        self.b43_erased_block_cnt = unpacked_data[27]
        self.b44_valid_block_cnt = unpacked_data[28]
        self.b45_block_erased_done = unpacked_data[29]
        self.w46_page = unpacked_data[30]
        self.w48_block = unpacked_data[31]
        self.l50_node = unpacked_data[32]

class FwGeometry(PacketParserABC):
    def __init__(self) -> None:
        self.l0_partition_count = 0        # 0: 1 partition, 1: 2 partition
        self.l4_cache_prog_size_d1 = 0     # sector
        self.l8_cache_prog_size_d2 = 0     # sector
        self.l12_cache_size = 0            # sector, write buffer size
        self.l16_vb_size_pb_d1 = 0         # page base d1, sector // whole slc vb size = user data + raid parity data + fw internal data
        self.l20_vb_size_pb_d2 = 0         # page base d2, sector // whole tlc vb size
        self.l24_vb_size_b = 0             # block base, sector   // whole qlc vb size(8325)
        self.l28_flush_pte_win_size_d1 = 0 # sector
        self.l32_flush_pte_win_size_d2 = 0 # sector
        self.l36_data_gc_threshold_nor = 0 # vb count // slc
        self.l40_data_gc_threshold_act = 0 # vb count
        self.l44_pte_gc_threshold = 0      # vb count
        self.l48_wl_gap = 0                # activate wear-leveling criterion (slc)
        self.l52_total_vb_count = 0
        self.l56_nodes_per_pte_table = 0
        self.l60_nodes_per_pmd_table = 0
        self.l64_nodes_per_pgd_table = 0
        self.l68_logical_clustor_per_virtual_wl_0 = 0 # d1, 4k
        self.l72_logical_clustor_per_virtual_wl_1 = 0 # d2, 4k
        self.l76_data_gc_src_vb_max = 0               # vb cnt
        self.l80_pte_gc_src_vb_max = 0                # vb cnt
        self.l84_vb_size_u0 = 0                       #slc vb size = user data
        self.l88_vb_size_u1 = 0                       #tlc
        self.l92_vb_size_u2 = 0                       #qlc(8325)
        self.l96_incomplete_gc_threshold = 0          #fw incomplete gc threshold
        self.rsvd1 = [0] * 999
        self.l4096_data_gc_threshold_nor_1 = 0 # vb count // mlc
        self.l4100_lun0_node_begin = 0
        self.l4104_lun1_node_begin = 0
        self.l4108_lun2_node_begin = 0
        self.l4112_lun3_node_begin = 0
        self.l4116_lun4_node_begin = 0
        self.l4120_lun5_node_begin = 0
        self.l4124_lun6_node_begin = 0
        self.l4128_lun7_node_begin = 0
        self.l4132_lun_rpmb_node_begin = 0
        self.l4136_geometry_parameter_version = 0             #4139:4136
        self.l4140_slc_partition_vb_boundary = 0              #not in 8325
        self.l4144_fw_geometry_data_gc_threshold_active_1 = 0 #bkops gc threshold //mlc partition
        self.l4148_fw_geometry_used_vb_p0 = 0                 # slc partition
        self.l4152_fw_geometry_used_vb_p1 = 0                 # mlc partition
        self.l4156_d1_max_erase_cnt = 0                       #4159:4156
        self.l4160_d1_min_erase_cnt = 0                       #4163:4160
        self.l4164_d1_avg_erase_cnt = 0                       #4167:4164
        self.l4168_d1_total_erase_cnt = 0                     #4171:4168
        self.l4172_d2d3_max_erase_cnt = 0                     #4175:4172
        self.l4176_d2d3_min_erase_cnt = 0                     #4179:4176
        self.l4180_d2d3_avg_erase_cnt = 0                     #4183:4180
        self.l4184_d2d3_total_erase_cnt = 0                   #4187:4184
        self.l4188_device_op = 0                              #4191:4188, data area over provision
        self.l4192_device_wa = 0                              #4195:4192, waf from smart info
        self.l4196_device_slc_op = 0                          #4199:4196, system area  over provision
        self.l4200_device_pivot = 0
        self.l4204_waf_dicard_grp_size = 0
        self.l4208_waf_dicard_grp = [0] * 8
        self.l4240_device_last_bbs_vb = 0
        self.l4244_data_gc_slc_early_gc_threshold = 0
        self.l4248_d3_slc_vb_cnt = 0
        self.rsvd2 = [0] * 958

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '<' + 'I' * (25+999+28+8+3+958)
        unpacked_data = struct.unpack(format_string, payload[0:8084])

        self.l0_partition_count = unpacked_data[0]
        self.l4_cache_prog_size_d1 = unpacked_data[1]
        self.l8_cache_prog_size_d2 = unpacked_data[2]
        self.l12_cache_size = unpacked_data[3]
        self.l16_vb_size_pb_d1 = unpacked_data[4]
        self.l20_vb_size_pb_d2 = unpacked_data[5]
        self.l24_vb_size_b = unpacked_data[6]
        self.l28_flush_pte_win_size_d1 = unpacked_data[7]
        self.l32_flush_pte_win_size_d2 = unpacked_data[8]
        self.l36_data_gc_threshold_nor = unpacked_data[9]
        self.l40_data_gc_threshold_act = unpacked_data[10]
        self.l44_pte_gc_threshold = unpacked_data[11]
        self.l48_wl_gap = unpacked_data[12]
        self.l52_total_vb_count = unpacked_data[13]
        self.l56_nodes_per_pte_table = unpacked_data[14]
        self.l60_nodes_per_pmd_table = unpacked_data[15]
        self.l64_nodes_per_pgd_table = unpacked_data[16]
        self.l68_logical_clustor_per_virtual_wl_0 = unpacked_data[17]
        self.l72_logical_clustor_per_virtual_wl_1 = unpacked_data[18]
        self.l76_data_gc_src_vb_max = unpacked_data[19]
        self.l80_pte_gc_src_vb_max = unpacked_data[20]
        self.l84_vb_size_u0 = unpacked_data[21]
        self.l88_vb_size_u1 = unpacked_data[22]
        self.l92_vb_size_u2 = unpacked_data[23]
        self.l96_incomplete_gc_threshold = unpacked_data[24]
        
        # Copy reserved array (indices 25-1023)
        for i in range(999):
            self.rsvd1[i] = unpacked_data[25 + i]

        self.l4096_data_gc_threshold_nor_1 = unpacked_data[25+999]
        self.l4100_lun0_node_begin = unpacked_data[26+999]
        self.l4104_lun1_node_begin = unpacked_data[27+999]
        self.l4108_lun2_node_begin = unpacked_data[28+999]
        self.l4112_lun3_node_begin = unpacked_data[29+999]
        self.l4116_lun4_node_begin = unpacked_data[30+999]
        self.l4120_lun5_node_begin = unpacked_data[31+999]
        self.l4124_lun6_node_begin = unpacked_data[32+999]
        self.l4128_lun7_node_begin = unpacked_data[33+999]
        self.l4132_lun_rpmb_node_begin = unpacked_data[34+999]
        self.l4136_geometry_parameter_version = unpacked_data[35+999]
        self.l4140_slc_partition_vb_boundary = unpacked_data[36+999]
        self.l4144_fw_geometry_data_gc_threshold_active_1 = unpacked_data[37+999]
        self.l4148_fw_geometry_used_vb_p0 = unpacked_data[38+999]
        self.l4152_fw_geometry_used_vb_p1 = unpacked_data[39+999]
        self.l4156_d1_max_erase_cnt = unpacked_data[40+999]
        self.l4160_d1_min_erase_cnt = unpacked_data[41+999]
        self.l4164_d1_avg_erase_cnt = unpacked_data[42+999]
        self.l4168_d1_total_erase_cnt = unpacked_data[43+999]
        self.l4172_d2d3_max_erase_cnt = unpacked_data[44+999]
        self.l4176_d2d3_min_erase_cnt = unpacked_data[45+999]
        self.l4180_d2d3_avg_erase_cnt = unpacked_data[46+999]
        self.l4184_d2d3_total_erase_cnt = unpacked_data[47+999]
        self.l4188_device_op = unpacked_data[48+999]
        self.l4192_device_wa = unpacked_data[49+999]
        self.l4196_device_slc_op = unpacked_data[50+999]
        self.l4200_device_pivot = unpacked_data[51+999]
        self.l4204_waf_dicard_grp_size = unpacked_data[52+999]

        # Copy waf_discard_grp array (indices 54-61)
        for i in range(8):            
            self.l4208_waf_dicard_grp[i] = unpacked_data[53+999+i]

        self.l4240_device_last_bbs_vb = unpacked_data[61+999]
        self.l4244_data_gc_slc_early_gc_threshold = unpacked_data[62+999]
        self.l4248_d3_slc_vb_cnt = unpacked_data[63+999]

        # Copy reserved array (indices 65-1022)
        for i in range(958):
            self.rsvd2[i] = unpacked_data[64+999+i]

class EventInfo(PacketParserABC):
    def __init__(self) -> None:
        self.l0_event_info_ver = 0
        self.l4_normal_bch_offline_cnt = 0
        self.l8_normal_retry_cnt = 0
        self.l12_normal_auto_read_calib_cnt = 0
        self.l16_normal_lpi_cnt = 0
        self.l20_normal_softbit_cnt = 0
        self.l24_normal_raid_cnt = 0
        self.l28_normal_uecc_cnt = 0
        self.l32_spor_bch_offline_cnt = 0
        self.l36_spor_retry_cnt = 0
        self.l40_spor_auto_read_calib_cnt = 0
        self.l44_spor_lpi_cnt = 0
        self.l48_spor_softbit_cnt = 0
        self.l52_spor_raid_cnt = 0
        self.l56_spor_uecc_cnt = 0
        self.l60_pre_read_unc_retry_count = 0
        self.l64_pre_read_abort_count = 0
        self.l68_pre_read_enable_count = 0
        self.l72_total_pre_read_trigger_count = 0
        self.w76_auto_standby_gc_count = 0
        self.w78_open_block_refresh_count = 0
        self.w80_read_disturb_count = 0
        self.w82_dynamic_slc_cache_policy_count = 0
        self.l84_safe_scan_closed_vb_count = 0
        self.l88_safe_scan_open_vb_count = 0
        self.w92_current_ctrl_temperature = 0
        self.w94_highest_ctrl_temperature = 0
        self.b96_nand_temperature_ce0 = 0
        self.b97_nand_temperature_ce1 = 0
        self.b98_nand_temperature_ce2 = 0
        self.b99_nand_temperature_ce3 = 0
        self.b100_nand_temperature_ce4 = 0
        self.b101_nand_temperature_ce5 = 0
        self.b102_nand_temperature_ce6 = 0
        self.b103_nand_temperature_ce7 = 0
        self.b104_high_ctrl_temperature_threshold = 0
        self.b105_low_ctrl_temperature_threshold = 0
        self.w106_ctrl_over_threshold_counter = 0
        self.w108_ctrl_lower_threshold_counter = 0
        self.w110_level1_thermal_throttling_count = 0
        self.w112_level2_thermal_throttling_count = 0
        self.l114_code_block_total_erase_count = 0
        self.l118_data_gc_programmed_dummy_data_count = 0
        self.l122_data_gc_wo_increasing_free_vb_max_num = 0
        self.l126_interrupt_gc_count = 0
        self.l130_urgent_data_gc_count = 0
        self.l134_background_gc_count = 0
        self.l138_static_wear_leveling_count = 0
        self.l142_pte_gc_count = 0
        self.l146_log_table_gc_count = 0
        self.l150_force_data_gc_count = 0
        self.l154_data_gc_caused_by_read_disturb_count = 0
        self.l158_gc_source_w_no_valid_data_count = 0
        self.l162_create_l2_waiting_free_vb_count = 0
        self.l166_create_l2_waiting_free_pte_count = 0
        self.l170_slc_program_data_4k_size = 0
        self.l174_tlc_program_data_4k_size = 0
        self.w178_read_unc_rebuild_code_blk_count = 0
        self.w180_read_unc_init_bbt_blk_count = 0
        self.w182_read_unc_init_pt_blk_count = 0
        self.w184_read_unc_init_index_blk_count = 0
        self.w186_read_unc_init_list_blk_count = 0
        self.w188_read_unc_init_log_blk_count = 0
        self.w190_read_unc_init_pte_blk_count = 0
        self.w192_read_unc_init_temp_code_count = 0
        self.w194_read_unc_init_slc_l2_count = 0
        self.w196_read_unc_init_tlc_l2_count = 0
        self.w198_read_unc_init_slc_gc_target_count = 0
        self.w200_read_unc_init_tlc_gc_target_count = 0
        self.w202_read_unc_init_l2_raid_swap_count = 0
        self.w204_read_unc_init_gc_raid_swap_count = 0
        self.b206_slc_read_retry_table_number = 0
        self.b207_tlc_read_retry_table_number = 0
        self.l208_swap_block_cnt_from_slc_pool = 0
        self.l212_swap_block_cnt_from_mlc_pool = 0
        self.l216_swap_block_cnt_for_slc_l2 = 0
        self.l220_swap_block_cnt_for_tlc_l2 = 0
        self.l224_swap_block_cnt_for_gc = 0
        self.w228_lowest_ctrl_temperature = 0
        self.w230_write_buffer_size = 0
        self.reserved = [0] * 8
        self.b240_max_nand_tj = 0
        self.b241_min_nand_tj = 0
        self.reserved2 = [0] * 2
        self.l244_total_count_xtemp_scan = 0
        self.l248_total_count_xtemp_refresh = 0
        self.l252_diff_q_iwl_read_count = 0
        self.b256_auto_standby_count = [0] * 8
        self.l264_refresh_gc_target_count = 0
        self.l268_aom_banking_count = 0

    def from_bytes(self, payload: bytearray) -> None:
        format_string = '<' + 'L' * 19 + 'H' * 4  + 'L' * 2 + 'H' * 2 + 'B' * 10 + 'H' * 4 + 'L' * 16 + 'H' * 14 + 'B' * 2 + 'L' * 5 + 'H' * 2 + 'B' * 12 + 'L' * 3 + 'B' * 8 + 'L' * 2
        unpacked_data = struct.unpack(format_string, payload[0:272])
        
        self.l0_event_info_ver = unpacked_data[0]
        self.l4_normal_bch_offline_cnt = unpacked_data[1]
        self.l8_normal_retry_cnt = unpacked_data[2]
        self.l12_normal_auto_read_calib_cnt = unpacked_data[3]
        self.l16_normal_lpi_cnt = unpacked_data[4]
        self.l20_normal_softbit_cnt = unpacked_data[5]
        self.l24_normal_raid_cnt = unpacked_data[6]
        self.l28_normal_uecc_cnt = unpacked_data[7]
        self.l32_spor_bch_offline_cnt = unpacked_data[8]
        self.l36_spor_retry_cnt = unpacked_data[9]
        self.l40_spor_auto_read_calib_cnt = unpacked_data[10]
        self.l44_spor_lpi_cnt = unpacked_data[11]
        self.l48_spor_softbit_cnt = unpacked_data[12]
        self.l52_spor_raid_cnt = unpacked_data[13]
        self.l56_spor_uecc_cnt = unpacked_data[14]
        self.l60_pre_read_unc_retry_count = unpacked_data[15]
        self.l64_pre_read_abort_count = unpacked_data[16]
        self.l68_pre_read_enable_count = unpacked_data[17]
        self.l72_total_pre_read_trigger_count = unpacked_data[18]
        self.w76_auto_standby_gc_count = unpacked_data[19]
        self.w78_open_block_refresh_count = unpacked_data[20]
        self.w80_read_disturb_count = unpacked_data[21]
        self.w82_dynamic_slc_cache_policy_count = unpacked_data[22]
        self.l84_safe_scan_closed_vb_count = unpacked_data[23]
        self.l88_safe_scan_open_vb_count = unpacked_data[24]
        self.w92_current_ctrl_temperature = unpacked_data[25]
        self.w94_highest_ctrl_temperature = unpacked_data[26]
        self.b96_nand_temperature_ce0 = unpacked_data[27]
        self.b97_nand_temperature_ce1 = unpacked_data[28]
        self.b98_nand_temperature_ce2 = unpacked_data[29]
        self.b99_nand_temperature_ce3 = unpacked_data[30]
        self.b100_nand_temperature_ce4 = unpacked_data[31]
        self.b101_nand_temperature_ce5 = unpacked_data[32]
        self.b102_nand_temperature_ce6 = unpacked_data[33]
        self.b103_nand_temperature_ce7 = unpacked_data[34]
        self.b104_high_ctrl_temperature_threshold = unpacked_data[35]
        self.b105_low_ctrl_temperature_threshold = unpacked_data[36]
        self.w106_ctrl_over_threshold_counter = unpacked_data[37]
        self.w108_ctrl_lower_threshold_counter = unpacked_data[38]
        self.w110_level1_thermal_throttling_count = unpacked_data[39]
        self.w112_level2_thermal_throttling_count = unpacked_data[40]
        self.l114_code_block_total_erase_count = unpacked_data[41]
        self.l118_data_gc_programmed_dummy_data_count = unpacked_data[42]
        self.l122_data_gc_wo_increasing_free_vb_max_num = unpacked_data[43]
        self.l126_interrupt_gc_count = unpacked_data[44]
        self.l130_urgent_data_gc_count = unpacked_data[45]
        self.l134_background_gc_count = unpacked_data[46]
        self.l138_static_wear_leveling_count = unpacked_data[47]
        self.l142_pte_gc_count = unpacked_data[48]
        self.l146_log_table_gc_count = unpacked_data[49]
        self.l150_force_data_gc_count = unpacked_data[50]
        self.l154_data_gc_caused_by_read_disturb_count = unpacked_data[51]
        self.l158_gc_source_w_no_valid_data_count = unpacked_data[52]
        self.l162_create_l2_waiting_free_vb_count = unpacked_data[53]
        self.l166_create_l2_waiting_free_pte_count = unpacked_data[54]
        self.l170_slc_program_data_4k_size = unpacked_data[55]
        self.l174_tlc_program_data_4k_size = unpacked_data[56]
        self.w178_read_unc_rebuild_code_blk_count = unpacked_data[57]
        self.w180_read_unc_init_bbt_blk_count = unpacked_data[58]
        self.w182_read_unc_init_pt_blk_count = unpacked_data[59]
        self.w184_read_unc_init_index_blk_count = unpacked_data[60]
        self.w186_read_unc_init_list_blk_count = unpacked_data[61]
        self.w188_read_unc_init_log_blk_count = unpacked_data[62]
        self.w190_read_unc_init_pte_blk_count = unpacked_data[63]
        self.w192_read_unc_init_temp_code_count = unpacked_data[64]
        self.w194_read_unc_init_slc_l2_count = unpacked_data[65]
        self.w196_read_unc_init_tlc_l2_count = unpacked_data[66]
        self.w198_read_unc_init_slc_gc_target_count = unpacked_data[67]
        self.w200_read_unc_init_tlc_gc_target_count = unpacked_data[68]
        self.w202_read_unc_init_l2_raid_swap_count = unpacked_data[69]
        self.w204_read_unc_init_gc_raid_swap_count = unpacked_data[70]
        self.b206_slc_read_retry_table_number = unpacked_data[71]
        self.b207_tlc_read_retry_table_number = unpacked_data[72]
        self.l208_swap_block_cnt_from_slc_pool = unpacked_data[73]
        self.l212_swap_block_cnt_from_mlc_pool = unpacked_data[74]
        self.l216_swap_block_cnt_for_slc_l2 = unpacked_data[75]
        self.l220_swap_block_cnt_for_tlc_l2 = unpacked_data[76]
        self.l224_swap_block_cnt_for_gc = unpacked_data[77]
        self.w228_lowest_ctrl_temperature = unpacked_data[78]
        self.w230_write_buffer_size = unpacked_data[79]
        
        for i in range(8):            
            self.reserved[i] = unpacked_data[80 + i]
            
        self.b240_max_nand_tj = unpacked_data[88]
        self.b241_min_nand_tj = unpacked_data[89]

        for i in range(2):            
            self.reserved2[i] = unpacked_data[90 + i]

        self.l244_total_count_xtemp_scan = unpacked_data[92]
        self.l248_total_count_xtemp_refresh = unpacked_data[93]
        self.l252_diff_q_iwl_read_count = unpacked_data[94]

        for i in range(8):            
            self.b256_auto_standby_count[i] = unpacked_data[95 + i]

        self.l264_refresh_gc_target_count = unpacked_data[103]
        self.l268_aom_banking_count = unpacked_data[104]





