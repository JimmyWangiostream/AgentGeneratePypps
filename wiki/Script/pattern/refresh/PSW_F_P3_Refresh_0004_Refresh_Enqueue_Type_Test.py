import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from typing import List, Callable
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.refresh.mutual_fun import *
from Script.project_api.functions import print_object_info_ai

# ══════════════════════════════════════════════════════════════
# Test case table
# Each entry: (name, trigger_fn, expect_user, expect_priority)
#   trigger_fn(write_record) -> list of VBs that should be booked
# ══════════════════════════════════════════════════════════════

REFRESH_TEST_CASES: list[tuple[str, Callable[..., List[int]], int, int]] = [
    # ——— Implemented (natural FW trigger) ———
    ("ReadDisturb",  trigger_ReadDisturb_refresh,
        project_api.BookingUser.RD_SCAN_BOOKING_1,
        project_api.VUC087Paremeter.HighPriority),

    ("ReadUECC",     trigger_UECC_refresh,
        project_api.BookingUser.EH_BOOKSIGNALUECC_BOOKING_0,
        project_api.VUC087Paremeter.HighPriority),

    ("sWL_LowGap",   trigger_wear_leveling_lowgap_refresh,
        project_api.BookingUser.SWL_REFRESH_LOW_GAP,
        project_api.VUC087Paremeter.LowPriority),

    ("sWL_HighGap",  trigger_wear_leveling_highgap_refresh,
        project_api.BookingUser.SWL_REFRESH_HIGH_GAP,
        project_api.VUC087Paremeter.MediumPriority),

    # ("PSA",          trigger_psa_refresh,
    #     project_api.BookingUser.PSA_BOOKING,
    #     project_api.VUC087Paremeter.LowPriority),

    # # ——— Shell / To be implemented ———
    # ("MediaScan",    trigger_mediascan_refresh,
    #     project_api.BookingUser.MEDIA_SCAN_BOOKING_0,
    #     project_api.VUC087Paremeter.HighPriority),

    # ("HIR",          trigger_hir_refresh,
    #     project_api.BookingUser.HOST_INITIATED_REFRESH,
    #     project_api.VUC087Paremeter.HighPriority),

    # ("XTemp",        trigger_xtemp_refresh,
    #     project_api.BookingUser.XTEMP_BOOKING,
    #     project_api.VUC087Paremeter.MediumPriority),

    # ("BFEA",         trigger_bfea_refresh,
    #     project_api.BookingUser.BFEA_SCAN_BOOKING,
    #     project_api.VUC087Paremeter.LowPriority),
]


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.fw_geometry = api.get_fw_geometry()
        self.write_record = api.get_empty_write_record()
        leave_inhibition_mode()
        api.modify_desc_attr_flag(
                    QuerryType=Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_ATTRIBUTE,
                    Index=api.AttributeIDN.PSA_STATE, Value=0, IndexLen=1)

    def step1(self) -> None:
        for name, trigger_fn, expect_user, expect_pri in REFRESH_TEST_CASES:
            logger.info("")
            logger.info("=" * 70)
            logger.info(f"  [{name}] expect BookingUser = "
                        f"{project_api.BookingUser(expect_user).name} "
                        f"({expect_user}), Priority = "
                        f"{project_api.VUC087Paremeter(expect_pri).name}")
            logger.info("=" * 70)

            # ── 0. Config LUN + write data ──
            logger.flow(1, f"[{name}] config LUN + write data")
            _, self.tlc_lun = config_lun()
            self.write_record = api.get_empty_write_record()
            tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
            total_size = int(tlc_vb_size * 1.5)
            api.sequential_write(lun=self.tlc_lun, start_lba=0, total_size=total_size,
                                 chunk_size=api.BLOCK4K_SIZE_128M_BYTE, fua=0,
                                 need_compare=False,
                                 compare_method=api.CompareMethod.SW_COMPARE,
                                 write_record=self.write_record)

            # ── 2. Clear event log ──
            logger.flow(2, f"[{name}] clear event log")
            project_api.clear_event_logs()

            # ── 3. Stop refresh ──
            logger.flow(3, f"[{name}] C088 stop refresh execution")
            project_api.issue_C088_to_start_or_stop_refresh(
                project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)

            # ── 4. Trigger → FW naturally detects condition and books ──
            logger.flow(4, f"[{name}] trigger {name} refresh")
            vb_list = trigger_fn(self.write_record, self.tlc_lun)
            if not vb_list:
                logger.warning(f"  [{name}] no VBs returned, skipping")
                continue
            logger.info(f"  [{name}] triggered, expect VBs = {vb_list}")

            # ── 5. Check BookingQueue ──
            logger.flow(5, f"[{name}] issue 40C5 check BookingQueue")
            try:
                check_booking_user_in_queue(
                    list(vb_list),
                    project_api.BookingUser(expect_user),
                    project_api.VUC087Paremeter(expect_pri))
                logger.info(f"  [{name}] BookingUser check PASSED")
            except SIGHTING_FAIL_DATA_COMPARE_FAIL as exc:
                logger.error_lb(f"[{name}] BookingUser check FAILED — "
                                f"expected {project_api.BookingUser(expect_user).name}")
                raise

            # ── 6. Verify BookRefEventLog (0x3006) now, then clear ──
            logger.flow(6, f"[{name}] check BookRefEventLog then clear")
            verify_refresh_event_logs(vb_list, expect_user, log_ids=(0x3006,))
            project_api.clear_event_logs()

            # ── 7. Start refresh execution ──
            logger.flow(7, f"[{name}] C088 start refresh execution")
            project_api.issue_C088_to_start_or_stop_refresh(
                project_api.VUC088Paremeter.StartRefresh)

            # ── 8. Wait until BKOPS idle ──
            logger.flow(8, f"[{name}] polling until BKOPS idle")
            polling_bkops_idle()

            # ── 9. Verify RefStartEventLog (0x3051) ──
            logger.flow(9, f"[{name}] check RefStartEventLog")
            verify_refresh_event_logs(vb_list, expect_user, log_ids=(0x3051,))

            logger.info(f"  [{name}] — ALL CHECKS PASSED")

            # ── PSA cleanup: clear PSA state so next iteration doesn't inherit ──
            if name == "PSA":
                api.modify_desc_attr_flag(
                    QuerryType=Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_ATTRIBUTE,
                    Index=api.AttributeIDN.PSA_STATE, Value=0, IndexLen=1)

    def post_process(self) -> None:
        pass


run = Pattern().run
if __name__ == "__main__":
    run()
