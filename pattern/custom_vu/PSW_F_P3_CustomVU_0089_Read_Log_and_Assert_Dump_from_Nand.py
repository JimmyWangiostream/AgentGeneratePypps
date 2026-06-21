import package_root
import time
from collections import Counter
from dataclasses import dataclass
from typing import Callable, List, cast

from Script import api
from Script import project_api
from Script.api.exception import *
from Script.api import cmd_seq as ExecuteCMD
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.pattern_logger import logger
from Script.pattern.pattern_template import UFSTC
from Script.project_api.custom_vu.VDET_vu.functions import issue_40B8_to_get_VDET_information
from Script.project_api.custom_vu.read_log import issue_4080_read_log_from_nand
from Script.project_api.custom_vu.open_vb_information_vu.functions import issue_40C1_to_get_open_vb_information
from Script.project_api.health_report.functions import issue_40FE_to_read_enhanced_health_report
from Script.project_api.set_get_temperature.functions import issue_4021_get_nand_temperature, issue_40FD_get_uC_temp_123
from Script.project_api.set_string_description.functions import get_smart_info

from Script.project_api.thermal_protection_vu.structs import *
from Script.project_api.thermal_protection_vu.define import *

_param = api.shared.param

EVENT_LOG_TRANSFER_LENGTH = 0x4000
EVENT_LOG_HEADER_SIZE = 8
COMMON_INFO_OFFSET = EVENT_LOG_HEADER_SIZE
COMMON_INFO_SIZE = 1024
SYSTEM_STATUS_INFO_OFFSET = COMMON_INFO_OFFSET + COMMON_INFO_SIZE
SYSTEM_STATUS_INFO_SIZE = 512
HOST_SSR_INFO_OFFSET = SYSTEM_STATUS_INFO_OFFSET + SYSTEM_STATUS_INFO_SIZE
HOST_SSR_INFO_SIZE = 1024
SPECIFIC_LOG_INFO_OFFSET = HOST_SSR_INFO_OFFSET + HOST_SSR_INFO_SIZE

COMMON_INFO_SYSTEM_TEMPERATURE_OFFSET = 8
COMMON_INFO_NAND_TEMPERATURE_OFFSET = 12
COMMON_INFO_TIMESTAMP_OFFSET = 16
COMMON_INFO_VCC_DROP_COUNT_OFFSET = 20
COMMON_INFO_VCCQ_DROP_COUNT_OFFSET = 24
COMMON_INFO_SMART_INFO_OFFSET = 36
COMMON_INFO_SMART_INFO_LENGTH = 540
SMART_INFO_COMPARE_RANGES = (
    (0, 8),  # Host total write cmd count
    (8, 16),  # Host total read cmd count
)
SYSTEM_STATUS_INFO_COMPARE_RANGES = (
    (0, 4),  # TLC L2 VB number
    (4, 8),  # TLC L2 next program page
    (16, 20),  # TLC L2 RemapVB number
)
HOST_SSR_INFO_COMPARE_RANGES = (
    (32, 36),  # Min block erase count for SLC
    (36, 40),  # Max block erase count for SLC
    (40, 44),  # Avg block erase count for SLC
)

RAIN_RECOVERY_LOG_ID = 0x3011
UECC_LOG_ID = 0x6001
HIGH_PRIORITY = 0
LOW_PRIORITY = 1
MMESG_UNIT_SIZE = 0x20
REQUIRED_NEW_MMESG_LOG_IDS = {
    39: "EVENT_SOFTBIT",
    43: "EVENT_READ_DISTURB_REFRESH",
    45: "EVENT_RAID_RECOVERY",
    54: "EVEN_UFS_WRITE",
}

EXPECTED_ASSERT_CODE = 0x464
ASSERT_DUMP_TOTAL_COUNT_OFFSET = 12
ASSERT_DUMP_ASSERT_NUMBER_OFFSET = 16


@dataclass(frozen=True)
class EventLogCase:
    name: str
    event_log_ids: tuple[int, ...]
    expected_priority: int | None
    trigger: Callable[["Pattern"], None]
    check_system_status_info: bool = True


@dataclass(frozen=True)
class MmesgCase:
    name: str
    trigger: Callable[["Pattern"], None]
    required_new_log_ids: dict[int, str]


@dataclass(frozen=True)
class EventLogReferenceData:
    vcc_drop_count: int
    vccq_drop_count: int
    system_temperature: float
    nand_temperature: float
    smart_info_prefix: bytes
    system_status_info: bytes
    host_ssr_info: bytes


@dataclass(frozen=True)
class AssertDumpSummary:
    physical_block: int
    plane: int
    ce: int
    total_assert_count: int
    assert_numbers: tuple[int, ...]


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.validation_failures: list[str] = []
        self.total_au = _param.gGeometry.q4_total_raw_device_capacity // (
            _param.gGeometry.l13_segment_size * _param.gGeometry.b17_allocation_unit_size
        )
        self.slc_lun, self.tlc_lun = self.config_lun(
            slc_au=self.total_au // 2,
            tlc_au=self.total_au // 2,
        )

        self.fw_geometry = api.get_fw_geometry()
        self.SLC_VB_4K_SIZE = (self.fw_geometry.l84_vb_size_u0 * 512) // api.DATA_SIZE_4K_BYTE

    def step1(self) -> None:
        logger.info("=" * 60)
        logger.info("PHASE 1: Event Log Verification")
        self.verify_event_logs()
        logger.info("PHASE 1 COMPLETE")
        pass

    def step2(self) -> None:
        logger.info("=" * 60)
        logger.info("PHASE 2: MMesg Log Verification")
        self.verify_mmesg_logs()
        logger.info("PHASE 2 COMPLETE")
        pass

    def step3(self) -> None:
        logger.info("=" * 60)
        logger.info("PHASE 3: Assert Dump Verification")
        self.verify_assert_dump()
        logger.info("PHASE 3 COMPLETE")
        pass

    def post_process(self) -> None:
        if self.validation_failures:
            logger.error_fp("\n\n".join(self.validation_failures))
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def get_event_log_cases(self) -> list[EventLogCase]:
        # Add new events here. Each owner only needs to provide a trigger and
        # the expected event_log_ids; the common header/common-info checks are shared.
        return [
            EventLogCase(
                name="RAIN_RECOVERY",
                event_log_ids=(RAIN_RECOVERY_LOG_ID, UECC_LOG_ID),
                expected_priority=HIGH_PRIORITY,
                trigger=Pattern.trigger_rain_recovery_event,
            )
        ]

    def verify_event_logs(self) -> None:
        for event_case in self.get_event_log_cases():
            logger.info(f"Verify event log [{event_case.name}]")
            case_failures = self.verify_event_log_case(event_case)
            if case_failures:
                self.validation_failures.append(self.format_case_failures(f"Event Log [{event_case.name}]", case_failures))

    def verify_event_log_case(self, event_case: EventLogCase) -> list[str]:
        case_failures: list[str] = []

        logger.flow(1, "Erase all event logs")
        self.clear_event_logs()
        baseline_count = self.get_event_log_count()
        if baseline_count != 0:
            case_failures.append(f"[Setup] Expected event log count to be 0 after erase, got {baseline_count}")

        logger.flow(2, f"Trigger case[{event_case.name}]")
        try:
            event_case.trigger(self)
        except Exception as exc:
            case_failures.append(f"[Trigger] Failed to trigger event [{event_case.name}]: {exc}")
            return case_failures

        logger.flow(3, "Check event log count increased")
        try:
            current_count = self.wait_for_event_log_count_increase(baseline_count)
        except Exception as exc:
            case_failures.append(f"[Count] Failed while waiting event log count increase: {exc}")
            return case_failures

        logger.flow(4, "Find expected event log ID")
        matched_events = self.find_event_log(event_case.event_log_ids, baseline_count, current_count)
        searched_count = current_count - baseline_count
        logger.info(f"Event log search: checked {searched_count} entries, found {len(matched_events)}/{len(event_case.event_log_ids)} expected event log IDs")
        missing_event_log_ids = tuple(
            event_log_id for event_log_id in event_case.event_log_ids if event_log_id not in matched_events
        )
        if missing_event_log_ids:
            case_failures.append(
                f"[Search] Event log IDs {self.format_hex_values(missing_event_log_ids)} were not found between "
                + f"counts {baseline_count} and {current_count}. Expected all IDs: "
                + f"{self.format_hex_values(event_case.event_log_ids)}"
            )
            return case_failures

        logger.flow(5, "Collect reference data for comparison")
        reference_data: EventLogReferenceData | None = None
        try:
            reference_data = self.collect_event_log_reference_data()
        except Exception as exc:
            case_failures.append(f"[Reference Data] Failed to collect compare references: {exc}")

        logger.flow(6, "Compare Header/Common info/System status info/Host SSR info")
        for event_log_id in event_case.event_log_ids:
            event_index, event_output = matched_events[event_log_id]
            logger.info(f"Verify matched event_log_id = 0x{event_log_id:04X}, read index = {event_index}")
            case_failures.extend(self.verify_event_log_header(event_case, event_index, event_output))
            if reference_data is not None:
                case_failures.extend(self.verify_event_log_common_info(event_output, reference_data))
                if event_case.check_system_status_info:
                    case_failures.extend(self.verify_event_log_system_status_info(event_output, reference_data))
                case_failures.extend(self.verify_event_log_host_ssr_info(event_output, reference_data))

        if not case_failures:
            matched_indexes = ", ".join(
                f"0x{event_log_id:04X}@{matched_events[event_log_id][0]}" for event_log_id in event_case.event_log_ids
            )
            logger.info(
                f"Verified event log [{event_case.name}] at read indexes {matched_indexes}, "
                + f"event_log_ids = {self.format_hex_values(event_case.event_log_ids)}"
            )

        return case_failures

    def collect_event_log_reference_data(self) -> EventLogReferenceData:
        logger.info("Collecting reference data for Event Log comparison")

        logger.info("Read VDET info (VU 0x40B8)")
        _, vdet_information = issue_40B8_to_get_VDET_information()

        logger.info("Read uC temperature (VU 0x40FD)")
        _, uC_temp_payload = issue_40FD_get_uC_temp_123()

        logger.info("Read NAND temperature (VU 0x4021)")
        _, nand_temperature = issue_4021_get_nand_temperature()

        logger.info("Read Open VB info (VU 0x40C1)")
        _, open_vb_information = issue_40C1_to_get_open_vb_information()

        logger.info("Read enhanced health report (VU 0x40FE)")
        _, health_report = issue_40FE_to_read_enhanced_health_report()

        smart_info = bytes(get_smart_info()[:COMMON_INFO_SMART_INFO_LENGTH])
        system_status_info = bytes(open_vb_information.payload.copy()[:SYSTEM_STATUS_INFO_SIZE])
        host_ssr_info = bytes(health_report.payload.copy()[:HOST_SSR_INFO_SIZE])
        nand_temperature_average = self.get_average_nand_temperature(nand_temperature)

        logger.info(f"Reference: VccDrop={vdet_information.VccDropCnt.value}, VccqDrop={vdet_information.VccqDropCnt.value}")
        logger.info(f"Reference: system_temp={self.parse_40FD_uC_temperature(uC_temp_payload):.2f}, nand_temp_avg={nand_temperature_average:.2f}")

        return EventLogReferenceData(
            vcc_drop_count=vdet_information.VccDropCnt.value,
            vccq_drop_count=vdet_information.VccqDropCnt.value,
            system_temperature=self.parse_40FD_uC_temperature(uC_temp_payload),
            nand_temperature=nand_temperature_average,
            smart_info_prefix=smart_info,
            system_status_info=system_status_info,
            host_ssr_info=host_ssr_info,
        )

    def verify_event_log_header(self, event_case: EventLogCase, event_index: int, event_output: bytearray) -> list[str]:
        failures: list[str] = []
        log_index = self.read_u32(event_output, 0)
        if log_index != event_index:
            failures.append(f"[Log Header] Event log index mismatch: header={log_index}, wPara2={event_index}")

        if event_case.expected_priority is None:
            return failures

        priority = self.read_u32(event_output, 4)
        if priority != event_case.expected_priority:
            failures.append(
                f"Event log priority mismatch for [{event_case.name}]: "
                f"expected={event_case.expected_priority}, actual={priority}"
            )
        if failures:
            return [f"[Log Header] {failure}" if not failure.startswith("[Log Header]") else failure for failure in failures]
        return failures

    def verify_event_log_common_info(self, event_output: bytearray, reference_data: EventLogReferenceData) -> list[str]:
        failures: list[str] = []
        timestamp = self.read_u32(event_output, COMMON_INFO_TIMESTAMP_OFFSET)
        if timestamp in (0x00000000, 0xFFFFFFFF):
            failures.append(f"[Common Info] Invalid event log timestamp: 0x{timestamp:08X}")

        vcc_drop_count = self.read_u32(event_output, COMMON_INFO_VCC_DROP_COUNT_OFFSET)
        vccq_drop_count = self.read_u32(event_output, COMMON_INFO_VCCQ_DROP_COUNT_OFFSET)
        if vcc_drop_count != reference_data.vcc_drop_count:
            failures.append(
                f"Vcc drop count mismatch: event_log={vcc_drop_count}, VU40B8={reference_data.vcc_drop_count}"
            )
        if vccq_drop_count != reference_data.vccq_drop_count:
            failures.append(
                f"Vccq drop count mismatch: event_log={vccq_drop_count}, VU40B8={reference_data.vccq_drop_count}"
            )

        system_temperature = self.read_s32(event_output, COMMON_INFO_SYSTEM_TEMPERATURE_OFFSET)
        if abs(system_temperature - reference_data.system_temperature) > 5:
            failures.append(
                f"System temperature mismatch: event_log={system_temperature}, "
                f"VU40FD={reference_data.system_temperature:.2f}"
            )

        nand_temperature = self.read_s32(event_output, COMMON_INFO_NAND_TEMPERATURE_OFFSET)
        if abs(nand_temperature - reference_data.nand_temperature) > 5:
            failures.append(
                f"NAND temperature mismatch: event_log={nand_temperature}, "
                f"VU4021_avg_minus_37={reference_data.nand_temperature:.2f}"
            )

        smart_info = bytes(
            event_output[
                COMMON_INFO_SMART_INFO_OFFSET : COMMON_INFO_SMART_INFO_OFFSET + COMMON_INFO_SMART_INFO_LENGTH
            ]
        )
        smart_info_failure = self.compare_bytearray_ranges(
            section="Smart Info - Write/Read CMD count",
            actual=smart_info,
            expected=reference_data.smart_info_prefix,
            compare_ranges=SMART_INFO_COMPARE_RANGES,
            base_offset=COMMON_INFO_SMART_INFO_OFFSET,
            mismatch_label="Smart info stable fields mismatch with VU42FF",
        )
        if smart_info_failure is not None:
            failures.append(smart_info_failure)

        return [f"[Common Info] {failure}" if not failure.startswith("[Common Info]") else failure for failure in failures]

    def verify_event_log_system_status_info(
        self,
        event_output: bytearray,
        reference_data: EventLogReferenceData,
    ) -> list[str]:
        system_status_info = bytes(
            event_output[SYSTEM_STATUS_INFO_OFFSET : SYSTEM_STATUS_INFO_OFFSET + SYSTEM_STATUS_INFO_SIZE]
        )
        failure = self.compare_bytearray_ranges(
            section="System Status Info - TLC L2 VB/Page/RemapVB",
            actual=system_status_info,
            expected=reference_data.system_status_info,
            compare_ranges=SYSTEM_STATUS_INFO_COMPARE_RANGES,
            base_offset=SYSTEM_STATUS_INFO_OFFSET,
            mismatch_label="System status info stable fields mismatch with VU40C1",
        )
        return [failure] if failure is not None else []

    def verify_event_log_host_ssr_info(self, event_output: bytearray, reference_data: EventLogReferenceData) -> list[str]:
        host_ssr_info = bytes(event_output[HOST_SSR_INFO_OFFSET : HOST_SSR_INFO_OFFSET + HOST_SSR_INFO_SIZE])
        failure = self.compare_bytearray_ranges(
            section="Host SSR Info - SLC erase count Min/Max/Avg",
            actual=host_ssr_info,
            expected=reference_data.host_ssr_info,
            compare_ranges=HOST_SSR_INFO_COMPARE_RANGES,
            base_offset=HOST_SSR_INFO_OFFSET,
            mismatch_label="Host SSR info stable fields mismatch with VU40FE",
        )
        return [failure] if failure is not None else []

    def get_mmesg_cases(self) -> list[MmesgCase]:
        return [
            MmesgCase(
                name="RAIN_RECOVERY",
                trigger=Pattern.trigger_rain_recovery_event,
                required_new_log_ids=REQUIRED_NEW_MMESG_LOG_IDS,
            )
        ]

    def verify_mmesg_logs(self) -> None:
        cases = self.get_mmesg_cases()
        if not cases:
            logger.info("No MMesg cases configured. Add cases in get_mmesg_cases() when the trigger is ready.")
            return

        for case in cases:
            logger.info(f"Verify MMesg [{case.name}]")
            case_failures = self.verify_mmesg_case(case)
            if case_failures:
                self.validation_failures.append(self.format_case_failures(f"MMesg [{case.name}]", case_failures))

    def verify_mmesg_case(self, case: MmesgCase) -> list[str]:
        case_failures: list[str] = []

        logger.flow(1, "Erase all mmesg logs")
        self.clear_mmesg()
        baseline_count = self.get_mmesg_count()
        if baseline_count > 1:  # Allow count=1; immediate flush may occur after erase
            case_failures.append(f"[Setup] Expected MMesg count < 2 after erase, got {baseline_count}")
        
        logger.flow(2, f"Trigger case[{case.name}]")
        try:
            case.trigger(self)
        except Exception as exc:
            case_failures.append(f"[Trigger] Failed to trigger MMesg case [{case.name}]: {exc}")
            return case_failures

        logger.flow(3, "Read all mmesg logs")
        after_logs = self.read_all_mmesg_logs(stage="after")

        added_log_ids = self.collect_mmesg_log_ids(after_logs)
        logger.flow(4, "Check expected mmesg")
        case_failures.extend(
            self.check_expected_added_mmesg_log_ids(
                case_name=case.name,
                required_new_log_ids=case.required_new_log_ids,
                added_log_ids=added_log_ids,
            )
        )

        # Split read verification: para_4=0 with 0x2000 length = first 8KB
        # para_4=2 with 0x2000 length = second 8KB
        current_count = self.get_mmesg_count()
        logger.flow(5, "Verify MMesg split read via wPara4 offset")
        split_failures = self.verify_mmesg_split_read_in_case(current_count)
        case_failures.extend(split_failures)

        if not case_failures:
            logger.info(f"Verified MMesg [{case.name}] with added_log_ids = {sorted(added_log_ids.items())}")

        return case_failures

    def verify_mmesg_split_read_in_case(self, mmesg_count: int) -> list[str]:
        """Verify MMesg split read within MMesg case verification.

        Only MMesg output data exceeds 8KB (valid data in second 8KB page).
        This test verifies split read by reading MMesg in two parts:
        - First read: para_4=0, transfer_length=0x2000 (first 8KB)
        - Second read: para_4=2, transfer_length=0x2000 (second 8KB)
        Then verify the combined data matches single full read.

        Args:
            mmesg_count: MMesg count after trigger (already read in verify_mmesg_case)

        Returns:
            List of failure strings, empty if all checks pass
        """
        failures: list[str] = []

        if mmesg_count == 0:
            failures.append("[Split Read] No MMesg logs available for split read verification")
            return failures

        # Read the last MMesg log (most recent)
        log_index = mmesg_count - 1

        logger.info(f"Split read verification for most recent MMesg (index={log_index})")
        logger.info("Purpose: MMesg log size may exceed 8KB, test para_4 offset access")
        logger.info("Method: Compare single 0x4000 read vs two 0x2000 reads (para_4=0 and para_4=2)")

        logger.flow(6, "Read full MMesg log as reference (single 0x4000 read)")
        full_output = self.read_mmesg_log_by_index(log_index)
        logger.info(f"Full read length = 0x{len(full_output):X} bytes")

        logger.flow(7, "Read MMesg log in two splits via wPara4 offset")
        # para_4=0, transfer_length=0x2000 = first 8KB
        # para_4=2, transfer_length=0x2000 = second 8KB
        first_half = self.read_mmesg_log_by_index_with_offset(log_index, offset=0)
        second_half = self.read_mmesg_log_by_index_with_offset(log_index, offset=2)
        logger.info(f"Split 1 (para_4=0): 0x{len(first_half):X} bytes, Split 2 (para_4=2): 0x{len(second_half):X} bytes")

        logger.flow(8, "Compare combined split data with full read data")
        combined = first_half + second_half
        if combined != full_output:
            failures.append(
                f"[Split Read] Combined split data does not match full read: "
                f"combined_len={len(combined)}, full_len={len(full_output)}"
            )
        else:
            logger.info("Split read verification PASSED: combined == full")

        return failures

    def verify_assert_dump(self) -> None:
        case_failures: list[str] = []

        logger.flow(1, "Erase all assert dump")
        self.erase_assert_dump()
        erased_summary = self.parse_assert_dump_summary(self.read_assert_dump_summary())
        case_failures.extend(self.verify_assert_dump_erased(erased_summary))
        if case_failures:
            self.validation_failures.append(self.format_case_failures("Assert Dump", case_failures))

        logger.flow(2, "Trigger Thermal Proctection to get assert")
        try:
            self.trigger_thermal_protection_assert()
        except Exception as exc:
            case_failures.append(f"[Trigger] Failed to trigger Thermal Proctection: {exc}")
            self.validation_failures.append(self.format_case_failures("Assert Dump", case_failures))
            return

        logger.flow(3, "Read all assert number")
        assert_summary = self.parse_assert_dump_summary(self.read_assert_dump_summary())

        case_failures.extend(self.verify_assert_dump_summary(assert_summary))
        if case_failures:
            self.validation_failures.append(self.format_case_failures("Assert Dump", case_failures))
            return
        
        logger.flow(4, "Read Thermal Protection detail info")
        tp_info = self.read_tp_assert_info(assert_summary.assert_numbers.index(EXPECTED_ASSERT_CODE))
        
        logger.flow(5, "Check Thermal Protection information")
        case_failures.extend(self.verify_tp_assert_info(tp_info))
        if case_failures:
            self.validation_failures.append(self.format_case_failures("Assert Dump", case_failures))
            return
        
        logger.info(
            f"Verified assert dump: PB={assert_summary.physical_block}, plane={assert_summary.plane}, "
            + f"CE={assert_summary.ce}, total_assert_count={assert_summary.total_assert_count}, "
            + f"assert_numbers={self.format_hex_values(assert_summary.assert_numbers)}"
        )

    def trigger_thermal_protection_assert(self) -> None:
        logger.info("=== TRIGGER: Thermal Protection Assert ===")

        logger.info("Step 1: Read current thermal stuck threshold (VU 0x40FA)")
        _, StuckThreshold = project_api.issue_40FA_read_thermal_stuck_threshold()
        current_low = StuckThreshold.threshold_for_low_thermal_stuck_area.value
        logger.info(f"Current LOW threshold = {current_low}")

        logger.info("Step 2: Modify threshold to trigger thermal protection (set HIGH = 80C)")
        tp_threshold = WriteThermalStuckThreshold()
        tp_threshold.low_thermal_protection_threshold.value = current_low
        tp_threshold.high_thermal_protection_threshold.value = 80
        project_api.issue_D0F1_write_thermal_stuck_threshold(tp_threshold)
        logger.info(f"VU 0xD0F1 written: LOW={current_low}, HIGH=80 (UFS temp = real + 80)")

        logger.info("Step 3: Write 4K data (expect write stuck due to thermal protection)")
        try:
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=0, lba=0, length=DATA_SIZE_4K_BYTE, fua=1)
            ExecuteCMD.enqueue(write10)
            ExecuteCMD.send(clear_on_success=False)

            logger.error_fp("FW did NOT stuck - unexpected!")
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION

        except api.TIMEOUT_EXCEPTIONS:
            ExecuteCMD.clear()
            logger.info("Write timeout as expected - FW stuck due to thermal protection")

        logger.info("Step 4: Verify assert code is recorded (DME Get)")
        assert_code = api.get_fw_assert_number()
        logger.info(f"Assert code = 0x{assert_code:04X}")
        if assert_code == 0x0:
            logger.error_fp("No assert code recorded!")
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.info("Step 5: Power cycle to recover from thermal stuck")
        api.init_tester_to_unit_ready(resetmode=api.Dcmd5ResetType.HW_RESET, powerdown=False)
        logger.info("Power cycle complete - device recovered")
            
    def parse_assert_dump_summary(self, output: bytearray) -> AssertDumpSummary:
        total_assert_count = self.read_u32(output, ASSERT_DUMP_TOTAL_COUNT_OFFSET)
        assert_numbers = tuple(
            self.read_u32(output, ASSERT_DUMP_ASSERT_NUMBER_OFFSET + assert_index * 4)
            for assert_index in range(total_assert_count)
        )
        return AssertDumpSummary(
            physical_block=self.read_u32(output, 0),
            plane=self.read_u32(output, 4),
            ce=self.read_u32(output, 8),
            total_assert_count=total_assert_count,
            assert_numbers=assert_numbers,
        )

    def verify_assert_dump_erased(self, assert_summary: AssertDumpSummary) -> list[str]:
        if assert_summary.total_assert_count == 0:
            return []
        return [
            "[Setup] Expected assert dump count to be 0 after erase, "
            + f"got {assert_summary.total_assert_count}. "
            + f"assert_numbers={self.format_hex_values(assert_summary.assert_numbers)}"
        ]

    def verify_assert_dump_summary(self, assert_summary: AssertDumpSummary) -> list[str]:
        failures: list[str] = []

        if assert_summary.total_assert_count == 0:
            failures.append("[Summary] Expected at least one assert number, got total_assert_count=0")
            return failures

        if EXPECTED_ASSERT_CODE not in assert_summary.assert_numbers:
            failures.append(
                f"[Summary] Expected assert code 0x{EXPECTED_ASSERT_CODE:04X} was not found. "
                + f"assert_numbers={self.format_hex_values(assert_summary.assert_numbers)}"
            )

        return failures
    
    def verify_tp_assert_info(self, output: bytearray) -> list[str]:
        failures: list[str] = []

        assert_number = self.read_u32(output, 0)
        logger.info(f"Assert number = 0x{assert_number:04X}")
        if assert_number != EXPECTED_ASSERT_CODE:
            failures.append(f"[TpAssert] Expected assert code 0x{EXPECTED_ASSERT_CODE:04X} was not found, get 0x{assert_number:04X}")

        tmprStas = output[4]
        logger.info(f"TmprStas = {tmprStas}")
        if tmprStas != 1:
            failures.append(f"[TpAssert] Expected TmprStas=1, get TmprStas = {tmprStas}")

        for idx in range(5, 16, 2):
            value = int.from_bytes(output[idx: idx + 2], 'little')
            logger.info(f"Index {idx}-{idx+1} = {value}")
            if value == 0xFFFF:
                failures.append(f"[TpAssert] Expected Index {idx}-{idx+1} is not 0xFFFF")

        return failures

    def trigger_rain_recovery_event(self) -> None:
        logger.info("=== TRIGGER: RAIN Recovery Event ===")

        logger.info("Step 1: Stop refresh to allow UECC injection")
        project_api.issue_C088_to_start_or_stop_refresh(
            bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue
        )

        logger.info(f"Step 2: Write data to SLC LUN {self.slc_lun} to create VB for UECC injection")
        self.write_data(
            lun=self.slc_lun,
            start_lba=0,
            len=WRITE_10_MAX_BLOCK_LEN,
            total_len=self.SLC_VB_4K_SIZE // 2,
        )

        pca = self.get_PCA_and_print(lun=self.slc_lun, lba=0)
        logger.info(f"Step 3: Inject UECC @ VB={pca.virtual_block_number.value}, CE={pca.die.value}, Plane={pca.plane.value}")
        self.inject_UECC(pca, SLC_enable=True)

        logger.info("Step 4: Read to trigger UECC")
        self.read_data(lun=self.slc_lun, start_lba=0, len=1, total_len=1)

        logger.info("Step 5: Check booking queue has entries")
        _, booking_q_before = project_api.issue_40C5_to_get_booking_queue()
        booking_count = booking_q_before.LogicalVBNumberInBookingQueue.value
        logger.info(f"Booking queue entries before StartRefresh = {booking_count}")
        if booking_count == 0:
            raise api.PATTERN_ASSERT_UNEXPECTED_CONDITION("Rain recovery did not enqueue any booking queue entry")

        logger.info("Step 6: Start refresh execution (triggers RAIN recovery)")
        project_api.issue_C088_to_start_or_stop_refresh(
            bParameter0=project_api.VUC088Paremeter.StartRefresh
        )
        logger.info("RAIN recovery triggered successfully")

    def clear_event_logs(self) -> None:
        issue_4080_read_log_from_nand(
            para_0=0,
            para_1=0xFFFFFFFF,
            para_2=0,
            para_3=0,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )

    def get_event_log_count(self) -> int:
        _, output = issue_4080_read_log_from_nand(
            para_0=0,
            para_1=0,
            para_2=0,
            para_3=0,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )
        count = self.read_u32(output, 0)
        logger.info(f"event log count = {count}")
        return count

    def clear_mmesg(self) -> None:
        issue_4080_read_log_from_nand(
            para_0=2,
            para_1=0xFFFFFFFF,
            para_2=0,
            para_3=0,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )

    def get_mmesg_count(self) -> int:
        _, output = issue_4080_read_log_from_nand(
            para_0=2,
            para_1=0,
            para_2=0,
            para_3=0,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )
        count = self.read_u32(output, 0)
        logger.info(f"MMesg total page count = {count}")
        return count

    def wait_for_event_log_count_increase(
        self,
        baseline_count: int,
        retry_count: int = 10,
        sleep_sec: float = 1.0,
    ) -> int:
        for retry in range(retry_count):
            current_count = self.get_event_log_count()
            if current_count > baseline_count:
                return current_count
            logger.info(f"Event log is not ready yet, retry = {retry + 1}/{retry_count}")
            time.sleep(sleep_sec)
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION(f"Event log count did not increase from baseline count {baseline_count}")

    def read_event_log_by_index(self, event_index: int) -> bytearray:
        _, output = issue_4080_read_log_from_nand(
            para_0=0,
            para_1=1,
            para_2=event_index,
            para_3=0,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )
        return output

    def find_event_log(
        self,
        event_log_ids: tuple[int, ...],
        baseline_count: int,
        current_count: int,
    ) -> dict[int, tuple[int, bytearray]]:
        candidate_indexes = list(range(baseline_count, current_count))
        logger.info(f"Search event log IDs {self.format_hex_values(event_log_ids)} in indexes: {candidate_indexes}")
        matched_events: dict[int, tuple[int, bytearray]] = {}
        last_index = candidate_indexes[-1] if candidate_indexes else None

        for event_index in reversed(candidate_indexes):
            output = self.read_event_log_by_index(event_index)
            returned_event_log_id = self.read_u32(output, SPECIFIC_LOG_INFO_OFFSET)
            log_index = self.read_u32(output, 0)
            if returned_event_log_id in event_log_ids and returned_event_log_id not in matched_events:
                logger.info(f"Found target: 0x{returned_event_log_id:04X} at index {event_index}")
                matched_events[returned_event_log_id] = (event_index, output)
                if len(matched_events) == len(set(event_log_ids)):
                    break
            elif event_index == last_index:
                logger.info(
                    f"Read event log index = {event_index}, returned log index = {log_index}, "
                    f"event_log_id = 0x{returned_event_log_id:04X}"
                )

        missing_event_log_ids = tuple(event_log_id for event_log_id in event_log_ids if event_log_id not in matched_events)
        if missing_event_log_ids:
            logger.info(f"Missing event log IDs: {self.format_hex_values(missing_event_log_ids)}")

        return matched_events

    def read_all_mmesg_logs(self, stage: str) -> list[tuple[int, int, int, int]]:
        total_logs = self.get_mmesg_count()

        logs: list[tuple[int, int, int, int]] = []
        for log_index in range(total_logs):
            output = self.read_mmesg_log_by_index(log_index)

            for unit_index in range(len(output) // MMESG_UNIT_SIZE):
                start = unit_index * MMESG_UNIT_SIZE
                timestamp = self.read_u32(output, start)
                log_id = int.from_bytes(output[start + 6:start + 8], 'little')
                logs.append((log_index, unit_index, log_id, timestamp))

        logger.info(f"[{stage}] Read {len(logs)} MMesg entries from {total_logs} log pages")
        return logs

    def collect_mmesg_log_ids(
        self,
        all_logs: list[tuple[int, int, int, int]],
    ) -> dict[int, int]:
        logger.info("Collect MMesg results")

        all_log_id_count = Counter(log_id for _, _, log_id, _ in all_logs)

        added_log_ids: list[tuple[int, int]] = []
        for log_id, count in all_log_id_count.items():
            added_log_ids.append((log_id, count))

        for log_id, added_count in sorted(added_log_ids):
            event_name = REQUIRED_NEW_MMESG_LOG_IDS.get(log_id, "UNKNOWN")
            logger.info(f"added_mmesg_log_id={log_id} ({event_name}), added_count={added_count}")

        return {log_id: added_count for log_id, added_count in added_log_ids}

    def check_expected_added_mmesg_log_ids(
        self,
        case_name: str,
        required_new_log_ids: dict[int, str],
        added_log_ids: dict[int, int],
    ) -> list[str]:
        found_log_ids: list[int] = []
        missing_log_ids: list[int] = []

        for log_id, event_name in required_new_log_ids.items():
            if log_id in added_log_ids:
                logger.info(f"found_mmesg_log_id={log_id}, event={event_name}, added_count={added_log_ids[log_id]}")
                found_log_ids.append(log_id)
            else:
                logger.info(f"missing_mmesg_log_id={log_id}, event={event_name}")
                missing_log_ids.append(log_id)

        required_count = len(required_new_log_ids)
        found_count = len(found_log_ids)
        logger.info(f"[{case_name}] Found {found_count}/{required_count} required new MMesg log IDs")

        if found_log_ids:
            return []

        return [
            f"[Search] No required new MMesg log IDs found for [{case_name}]. Missing log IDs: {missing_log_ids}"
        ]

    def read_mmesg_log_by_index(self, log_index: int) -> bytearray:
        _, output = issue_4080_read_log_from_nand(
            para_0=2,
            para_1=1,
            para_2=log_index,
            para_3=0,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )
        return output

    def read_mmesg_log_by_index_with_offset(self, log_index: int, offset: int) -> bytearray:
        """Read MMesg log with wPara4 offset for split read verification.

        Args:
            log_index: MMesg log index to read
            offset: Read offset in bytes (wPara4 value).
                   0 = first 8KB (para_4=0, transfer_length=0x2000)
                   2 = second 8KB (para_4=2, transfer_length=0x2000)
        """
        _, output = issue_4080_read_log_from_nand(
            para_0=2,
            para_1=1,
            para_2=log_index,
            para_3=0,
            para_4=offset,
            transfer_length=0x2000,
        )
        return output

    def read_assert_dump_summary(self) -> bytearray:
        _, output = issue_4080_read_log_from_nand(
            para_0=1,
            para_1=0,
            para_2=0,
            para_3=0,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )
        return output

    def erase_assert_dump(self) -> None:
        issue_4080_read_log_from_nand(
            para_0=1,
            para_1=1,
            para_2=0,
            para_3=0,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )
    
    def read_tp_assert_info(self, page_index: int) -> bytearray:
        _, output = issue_4080_read_log_from_nand(
            para_0=1,
            para_1=2,
            para_2=page_index,
            para_3=0,
            para_4=0,
            transfer_length=EVENT_LOG_TRANSFER_LENGTH,
        )
        return output

    def get_average_nand_temperature(self, nand_temperature: object) -> float:
        die_count = min(getattr(nand_temperature, "die_count_of_system").value, 4)
        temperatures: list[int] = []
        for die_index in range(die_count):
            temperatures.append(getattr(nand_temperature, f"temperature_of_die_{die_index}").value)
        if not temperatures:
            raise AssertionError("VU4021 did not report any NAND temperature")
        return sum(temperatures) / len(temperatures) - 37

    def parse_40FD_uC_temperature(self, payload: bytes | bytearray) -> float:
        if len(payload) < 5:
            raise AssertionError(f"VU40FD output is too short: {len(payload)} bytes")

        sign_bit = (payload[4] & 0x04) >> 2
        value_bits = payload[4] & 0x03
        if sign_bit == 1:
            raw_temperature = -int.from_bytes([payload[3], value_bits], byteorder="little")
        else:
            raw_temperature = int.from_bytes([payload[3], value_bits], byteorder="little")
        return raw_temperature * 0.25

    def read_u32(self, output: bytes | bytearray, offset: int) -> int:
        return int.from_bytes(output[offset : offset + 4], byteorder="little", signed=False)

    def read_s32(self, output: bytes | bytearray, offset: int) -> int:
        return int.from_bytes(output[offset : offset + 4], byteorder="little", signed=True)

    def get_mismatch_offsets(self, actual: bytes, expected: bytes) -> list[int]:
        compare_length = min(len(actual), len(expected))
        mismatch_offsets = [offset for offset in range(compare_length) if actual[offset] != expected[offset]]
        mismatch_offsets.extend(range(compare_length, len(actual)))
        mismatch_offsets.extend(range(compare_length, len(expected)))
        return mismatch_offsets

    def get_mismatch_offsets_in_ranges(
        self,
        actual: bytes,
        expected: bytes,
        compare_ranges: tuple[tuple[int, int], ...],
    ) -> list[int]:
        mismatch_offsets: list[int] = []
        for start, end in compare_ranges:
            for offset in range(start, end):
                if offset >= len(actual) or offset >= len(expected) or actual[offset] != expected[offset]:
                    mismatch_offsets.append(offset)
        return mismatch_offsets

    def format_offsets(self, offsets: list[int], base_offset: int = 0) -> str:
        if not offsets:
            return "none"

        ranges: list[str] = []
        start = offsets[0]
        end = offsets[0]

        for offset in offsets[1:]:
            if offset == end + 1:
                end = offset
                continue

            ranges.append(self.format_offset_range(start, end, base_offset))
            start = offset
            end = offset

        ranges.append(self.format_offset_range(start, end, base_offset))
        return ", ".join(ranges)

    def format_offset_range(self, start: int, end: int, base_offset: int = 0) -> str:
        start += base_offset
        end += base_offset
        if start == end:
            return f"0x{start:X}"
        return f"0x{start:X}-0x{end:X}"

    def compare_bytearrays(
        self,
        section: str,
        actual: bytes,
        expected: bytes,
        base_offset: int,
        mismatch_label: str,
    ) -> str | None:
        if actual == expected:
            return None

        mismatch_offsets = self.get_mismatch_offsets(actual, expected)
        lines = [f"[{section}] {mismatch_label}"]
        lines.append("offsets:")
        lines.extend(self.format_offset_lines(mismatch_offsets, base_offset=base_offset))
        lines.append("values:")
        lines.extend(self.format_mismatch_value_lines(actual, expected, base_offset))
        return "\n".join(lines)

    def compare_bytearray_ranges(
        self,
        section: str,
        actual: bytes,
        expected: bytes,
        compare_ranges: tuple[tuple[int, int], ...],
        base_offset: int,
        mismatch_label: str,
    ) -> str | None:
        compare_offsets = [self.format_offset_range(start, end - 1, base_offset) for start, end in compare_ranges]
        logger.info(f"[{section}] Compare offsets: {', '.join(compare_offsets)}")
        mismatch_offsets = self.get_mismatch_offsets_in_ranges(actual, expected, compare_ranges)
        if not mismatch_offsets:
            return None

        lines = [f"[{section}] {mismatch_label}"]
        lines.append("offsets:")
        lines.extend(self.format_offset_lines(mismatch_offsets, base_offset=base_offset))
        lines.append("values:")
        lines.extend(self.format_mismatch_value_lines_for_offsets(actual, expected, mismatch_offsets, base_offset))
        return "\n".join(lines)

    def format_offset_lines(self, offsets: list[int], base_offset: int = 0) -> list[str]:
        if not offsets:
            return ["- none"]

        ranges: list[str] = []
        start = offsets[0]
        end = offsets[0]

        for offset in offsets[1:]:
            if offset == end + 1:
                end = offset
                continue

            ranges.append(f"- {self.format_offset_range(start, end, base_offset)}")
            start = offset
            end = offset

        ranges.append(f"- {self.format_offset_range(start, end, base_offset)}")
        return ranges

    def format_mismatch_value_lines(self, actual: bytes, expected: bytes, base_offset: int = 0) -> list[str]:
        mismatch_offsets = self.get_mismatch_offsets(actual, expected)
        return self.format_mismatch_value_lines_for_offsets(actual, expected, mismatch_offsets, base_offset)

    def format_mismatch_value_lines_for_offsets(
        self,
        actual: bytes,
        expected: bytes,
        mismatch_offsets: list[int],
        base_offset: int = 0,
    ) -> list[str]:
        if not mismatch_offsets:
            return ["- none"]

        mismatch_details: list[str] = []
        for offset in mismatch_offsets:
            actual_value = f"0x{actual[offset]:02X}" if offset < len(actual) else "missing"
            expected_value = f"0x{expected[offset]:02X}" if offset < len(expected) else "missing"
            mismatch_details.append(
                f"- offset=0x{offset + base_offset:X} actual={actual_value} expected={expected_value}"
            )
        return mismatch_details

    def format_hex_values(self, values: tuple[int, ...]) -> str:
        return "[" + ", ".join(f"0x{value:04X}" for value in values) + "]"

    def format_case_failures(self, title: str, failures: list[str]) -> str:
        lines = [f"{title} Failures:"]
        for failure in failures:
            failure_lines = failure.splitlines()
            if not failure_lines:
                continue
            lines.append(f"- {failure_lines[0]}")
            for failure_line in failure_lines[1:]:
                lines.append(f"  {failure_line}")
        return "\n".join(lines)

    def write_data(self, lun: int, start_lba: int, len: int, total_len: int) -> None:
        while total_len > 0:
            len = min(total_len, len)
            write10 = ExecuteCMD.Write10()
            logger.info(f"start lba = {start_lba}, len = {len}")
            write10.assign(lun=lun, lba=start_lba, length=len, fua=0)
            ExecuteCMD.enqueue(write10)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

    def read_data(self, lun: int, start_lba: int, len: int, total_len: int) -> None:
        while total_len > 0:
            len = min(total_len, len)
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=lun, lba=start_lba, length=len, fua=0)
            ExecuteCMD.enqueue(read10)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

    def config_lun(self, slc_au: int, tlc_au: int) -> tuple[int, int]:
        config_descs = api.get_config_descriptors(print=True)
        for table in range(4):
            for unit in range(8):
                config_descs[table].header.b2_conf_desc_continue = 1
                config_descs[table].units[unit].b0_lu_enable = 0
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].l4_num_alloc_units = 0
                config_descs[table].units[unit].b9_logical_block_size = 0xC
                config_descs[table].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_DISCARD
                if (table * 8 + unit) == 0:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[table].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                    config_descs[table].units[unit].l4_num_alloc_units = slc_au
                elif (table * 8 + unit) == 1:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[table].units[unit].l4_num_alloc_units = tlc_au

        config_descs[3].header.b2_conf_desc_continue = 0
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.ENABLE
        config_descs[0].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = _param.gGeometry.l79_write_booster_buffer_max_n_alloc_units
        for i in range(4):
            api.push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        ExecuteCMD.clear()

        unit_desc_idxes: list[int] = []
        for lun in range(0, _param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

        for lun in range(_param.gMaxNumberLU):
            if _param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
        return 0, 1

    def get_PCA_and_print(self, lun: int, lba: int) -> project_api.physical_address_info:
        _, pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=lba)
        vb = pca.virtual_block_number.value
        die = pca.die.value
        plane = pca.plane.value
        block = pca.physical_block_number_w_BBT.value
        page = pca.page.value
        logger.info(
            f"Lun{lun}, LBA = {lba}: VB = {vb}, PhyBlock = {block}, CE = {die}, Plane = {plane}, Page = {page}"
        )
        return pca

    def inject_UECC(self, pca: project_api.physical_address_info, SLC_enable: bool = False) -> None:
        die = pca.die.value
        plane = pca.plane.value
        block = pca.physical_block_number_w_BBT.value
        page = pca.page.value
        logger.info(
            f"Inject UECC: PhyBlock = {block}, CE = {die}, Plane = {plane}, Page = {page}, "
            f"SLC_enable = {SLC_enable}"
        )
        if SLC_enable:
            direct_write_payload = bytearray(DATA_SIZE_16K_BYTE)
        else:
            direct_write_payload = bytearray(DATA_SIZE_20K_BYTE * 3)
        for i in range(len(direct_write_payload)):
            direct_write_payload[i] = 0xAA
        project_api.issue_C060_to_write_raw_data(
            Ce=die,
            Block=block,
            Plane=plane,
            Page=page,
            SLC_Enable=SLC_enable,
            Ecc_Enable=1,
            datapayload=direct_write_payload,
        )


run = Pattern().run
if __name__ == "__main__":
    run()
