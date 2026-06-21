# UFS Pattern Test Implementation Wiki — Part 2

Pattern folders covered: Inhibition_time, luns_reconfiguration, mconfig, mdwlsv, media_scan, outgoing_slx, PPM, program_fail, PSA

---

## Inhibition_time

### Overview — BG Task Inhibition Testing (11 tests + mutual_fun.py)

The Inhibition_time folder contains 11 test files verifying that background (BG) tasks are properly blocked during the inhibition window, and that they resume correctly after the window expires. A shared `mutual_fun.py` provides all trigger/poll/verification helpers used across these tests.

---

### mutual_fun.py — Shared Inhibition Functions

- `trigger_read_disturb()` — triggers a Read Disturb (RD) scan
- `trigger_wear_leveling()` — triggers a Wear Leveling (WL) refresh
- `trigger_read_scan_UECC()` — injects a UECC error to initiate a read scan
- `leave_inhibition_mode()` — issues 1001 consecutive reads to exit the inhibition window
- `trigger_refresh()` — triggers a HIR (High Intensity Refresh) refresh
- `polling_bkops_idle()` — polls `BG_OP_STATUS` until it reaches 0 (idle)
- `check_timeout()` — assertion helper that fails the test if a timeout condition is met
- `write_data()` — sequential write helper used to prepare data before inhibition tests
- `polling_bfea_idle()` — polls BFEA idle state with a 2000-second timeout
- `trigger_bfea_refresh_and_check_if_trigger()` — triggers a BFEA refresh and verifies the trigger succeeded
- `check_if_read_disturb_triggered()` — verifies that a Read Disturb scan was correctly triggered
- `check_if_wear_leveling_triggered()` — verifies that a Wear Leveling scan was correctly triggered
- `get_read_back_node()` — retrieves read-back node information from FW
- `check_if_Read_Back_triggered()` — verifies that a read-back operation was correctly triggered
- `config_lun()` — configures LUN layout for inhibition tests
- `get_sorted_VB_list()` — returns a sorted list of Virtual Blocks (VBs) for scan/refresh targeting
- **Per-test helpers**:
  - `power_cycle()` — performs a random HW_RESET with `powerdown=False` or `powerdown=True`, followed by `access_vendor_mode()`
  - `get_hwsetting_inhibition_time()` — reads the configured inhibition time from HwSetting
- **FW variable**: `read_fw_value('gInhibitMgr.lock')` — returns `1` when inhibition is active, `0` when inactive

---

### PSW_F_P3_InhibitionTime_0001 — Disable/Enable Timing

- **Purpose**: Verify the inhibition timer behavior when BG tasks are triggered but held in the inhibited state. Confirms that the timer starts and expires correctly, and that tasks are blocked for the expected duration before being allowed to proceed.

---

### PSW_F_P3_InhibitionTime_0002 — BG Task Inhibition

- **Purpose**: Verify that Garbage Collection (GC) and other BG tasks are blocked during the active inhibition window. Confirms that `gInhibitMgr.lock == 1` while inhibition is active and that tasks remain queued until the window ends.

---

### PSW_F_P3_InhibitionTime_0003–0011 — Various Inhibition Scenarios

- **0003**: GC inhibition — verifies GC is blocked during the inhibition window
- **0004**: MS/BF/RD scan inhibition — verifies Media Scan, BFEA, and Read Disturb scans are blocked
- **0005**: BBM scan inhibition — verifies Bad Block Management scan is blocked
- **0006**: Read Back Open TLC inhibition — verifies read-back for open TLC blocks is blocked
- **0007**: HIR Read Back inhibition — verifies HIR (High Intensity Refresh) read-back is blocked
- **0008**: Purge Read Back inhibition — verifies read-back during purge is blocked
- **0009**: HID Read Back inhibition — verifies HID (Host-Initiated Defrag) read-back is blocked
- **0010**: PSA Refresh inhibition — verifies PSA-related refresh is blocked during inhibition
- **0011**: Other Refresh inhibition — verifies miscellaneous refresh tasks are blocked

**Note**: Many step bodies are placeholder stubs in the current implementation and are marked for future completion.

**Key Pattern across all 0003–0011 tests**:
1. Write data to prepare target blocks
2. Trigger the relevant BG task
3. Verify `gInhibitMgr.lock == 1` confirms the task is blocked
4. Call `leave_inhibition_mode()` (1001 consecutive reads) to exit the inhibition window
5. Verify the BG task resumes and completes normally

---

## luns_reconfiguration

### PSW_F_P3_Reconfiguration_0001 — PSA Flow Reconfiguration Test

- **Purpose**: Validates LUN reconfiguration permission rules across all four PSA states (`OFF`, `PRE_SOLDERING`, `LOADING_COMPLETE`, `SOLDERED`) and both config descriptor lock states (locked vs. unlocked). Ensures that the device correctly enforces reconfiguration restrictions and that the `lun_reconfig_ec_warning` health report field reflects erase count thresholds.

- **Key APIs**:
  - `api.push_write_config(desc, index)` — chains 4 config descriptor writes; index 0–2 use `ENABLE`, index 3 uses `DISABLE`
  - `api.write_attribute(idn=AttributeIDN.PSA_STATE, val=PSAState.PRE_SOLDERING / LOADING_COMPLETE)` — advances PSA state machine
  - `project_api.issue_40FE_to_read_enhanced_health_report()` — reads enhanced health report; checks `lun_reconfig_ec_warning` field at offset `0x140h`
  - `project_api.VU_clear_PSA_state()` — clears PSA state via VendorCmdWrite in post-processing
  - `project_api.issue_D085_unlock_LU_attribute_configuration()` — D085 vendor unlock command
  - `api.set_all_VB_erase_count(ec)` — sets all VB erase counts to a specified value

- **4 sub-cases executed per PSA state**:
  - **Case A** (unlock + EC ≤ 30): Reconfiguration succeeds; `lun_reconfig_ec_warning == 0`
  - **Case B** (unlock + EC > 30): Returns `GENERAL_FAILURE`; `lun_reconfig_ec_warning != 0`
  - **Case C** (lock + EC ≤ 30): Returns `PARAM_ALREADY_WRITTEN` (config locked, write rejected)
  - **Case D** (restore lock via D085): Re-locks the config descriptor via D085 → attribute write confirms lock restored

- **post_process**: Calls `set_all_VB_erase_count()` to restore erase counts, `VU_clear_PSA_state()` to reset PSA state, and `config_backup()` to restore LUN configuration

- **Exceptions**:
  - `SIGHTING_RESPONSE_UNEXPECTED`
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`

---

### PSW_F_P3_Reconfiguration_0002 — Reconfiguration During Active Module Test

- **Purpose**: Verify that LUN reconfiguration is safe to perform while RPMB, HID, Write Booster, or HIR are actively running. Ensures that each module returns to idle state and that data integrity is maintained after reconfiguration mid-operation.

- **Sub-tests**:
  - `test_RPMB()`: Write RPMB data → perform LUN reconfiguration → read back RPMB data → compare bytes `[228:484]` per 512-byte LBA
  - `test_HID_flow()`: Write until `HID_STATE == Required` → start defragmentation (`bDefragOperation`) → perform reconfiguration mid-defrag → verify `HID_STATE` returns to `Idle` and `HIDProgressRatio == 0`
  - `test_write_booster_flow()`: Enable Write Booster → write until `EXC_EVENT_STATUS` bit 5 is set → enable `bWriteBoosterFlushEn` → perform reconfiguration mid-flush → verify Write Booster status returns to `Idle`
  - `test_HIR_flow()`: Sequential write 4 GB on both LUNs → random write/erase to age data → set `bRefreshEn` → poll until refresh progress wraps around → perform reconfiguration → verify `RefreshStatus` returns to `Idle`

- **Key APIs**:
  - `api.sequential_write()` — sequential write for data preparation
  - `api.random_write()` — random write to trigger wear/refresh conditions
  - `api.write_attribute()` / `api.read_attribute()` — UFS attribute access
  - `rpmb.rpmb_write(lba, data)` / `rpmb.rpmb_read()` — RPMB read/write access

- **Exceptions**:
  - `SIGHTING_RESPONSE_UNEXPECTED`
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `SPEC_ASSERT_RPMB_KEY_NOT_CLEARED`
  - `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT`

---

### PSW_F_P3_Reconfiguration_0003 — Different Normal/Boot LUN Ratio Test

- **Purpose**: Exercises approximately 100+ combinations of EM1 / Normal / Boot AU ratios and verifies correct SCSI boundary behavior for each configuration. Ensures the device correctly rejects out-of-range LBA accesses with the appropriate error response.

- **LUN assignment**: LUN0 = EM1 (`ENHANCED_1`), LUN1 = `BOOT_LUN_A`, LUN2 = `NORMAL`

- **`random_scsi_test()`**: Generates 200 shuffled events of type `WRITE`, `UNMAP`, and `READ_COMPARE`. Out-of-range LBA accesses are expected to return `CHECK_CONDITION` or `ILLEGAL_REQUEST`.

- **`generate_test_cases()`**: Generates test cases spanning the 0–100% EM1 AU range to cover the full ratio space.

- **Exceptions**:
  - `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`

---

## mconfig

### mutual_fun.py — Shared mConfig/pConfig Helpers

- `xlsx_data_process(xlsx_path)` — reads the provided Excel (.xlsx) file; locates the OTP value row; returns a tuple `(otp_index, dict)` mapping each row to its field information
- `load_mConfig_pConfig_from_xlsx()` — loads the Cygnus Auto B68S mConfig Excel file ("Cygnus Auto B68S mConfig rev0.4.xlsx") and the corresponding pConfig Excel file
- `compare_payload(payload, xlsx_dict, vu_value, otp_value)` — performs bit-level field extraction from the payload and compares each field against the expected values from the xlsx dictionary, the VU-read value, and the OTP value
- `get_m_p_config_in_FW_HW_BIN(fw_bin, index_offset)` — extracts mConfig data at offset `0x5000 + index_offset` (437 bytes) and pConfig data at offset `0x5400 + index_offset` (1612 bytes) from the firmware binary
- `get_PRL_in_FW_HW_BIN(fw_bin)` — reads bytes `[0x100:0x102]` from the firmware binary and interprets them as a little-endian `uint16` Product Revision Level (PRL)
- `compare_mConfig_data(payload, xlsx_dict)` — signature validation: checks that `payload[0:7] == b"MCONFIG"`
- `compare_pConfig_data(payload, xlsx_dict)` — signature validation: checks that the payload starts with `b"PCONFIG"`
- `config_lun()` — sets LUN0 = EM1 with size `min(l44_enhanced1_max_n_alloc_u, Total // 2)` AU; LUN1 = NORMAL with size `Total // 2` AU

---

### PSW_F_P3_mConfig_0001 — Cygnus mConfig Normal Test

- **Purpose**: Tests 10 mConfig/pConfig update scenarios covering FFU-based updates (cases 1–3), VU command-based updates (cases 4–6), and X-memory configuration tests (cases 7–10). Verifies that mConfig and pConfig data is correctly written, persisted, and readable after each update method.

- **Key APIs**:
  - `project_api.codesign_ffu_bin(bin_path)` — signs the FFU binary for authenticated update
  - `project_api.send_ffu_write_buffer(bin_data)` — sends the FFU binary payload to the device
  - `project_api.set_mConfig_data(data)` / `project_api.get_mConfig_data()` — C056 vendor command for mConfig write/read
  - `project_api.set_pConfig_data(data)` / `project_api.get_pConfig_data()` — C056 vendor command for pConfig write/read
  - `project_api.set_HW_page_config_data(data)` — C056 vendor command for HW page config write
  - `api.get_fw_address(name)` — returns the firmware symbol address for a given symbol name
  - `api.read_smart_info()` — reads SMART info; offset `0x4A8` contains the ATS timer (8 bytes)

- **FFU verification**: After a successful FFU update, `patch_Trial_Count` must increment by 1 and `patch_Success_Count` must increment by 1.

- **FFU event log type `0x0007`**: Fields verified include `eventCnt`, `oldVer`, `newVer`, and `logType == 0xFF`.

- **PRL check**: `health_report.prl == health_report.fw_current_prl == PRL_from_bin[0x100:0x102]`

- **Exceptions**:
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_mConfig_0002 — Cygnus mConfig Error Test

- **Purpose**: Tests 11–12 error and rejection scenarios for invalid mConfig/pConfig update attempts. Verifies that the firmware correctly rejects malformed or incompatible updates and that counters/state are updated appropriately.

- **Error cases covered**:
  - Wrong OTP value → `MICROCODE_VERSION_MISMATCH` response
  - Corrupted signature → `Trial_Count` increments by 1; `Success_Count` remains unchanged
  - Invalid option byte value `0x3` or `0xFF` → error response
  - Wrong `Name_1` field value → error response
  - Incrementing `compatible_value` beyond range → incompatible FFU rejection

- **Key implementation detail**: Uses a `erroe_case` boolean flag (note: intentional typo in source, not `error_case`) to select the error injection path.

- **Key APIs**:
  - `project_api.send_FFU_and_check_response(bin_data, error_case=True / False)` — sends FFU with expected pass/fail outcome
  - `api.get_ffu_status()` — reads FFU status register to verify response code

- **Exceptions**:
  - `SIGHTING_RESPONSE_UNEXPECTED`
  - `SIGHTING_FFU_STATUS_UNEXPECTED`
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `PATTERN_ASSERT_ATTR_NOT_FOUND`

---

## mdwlsv

### MDWLSV Payload Layout

Each die occupies 60 bytes in the MDWLSV payload. Die base offsets: Die0 = 0, Die1 = +60, Die2 = +120, Die3 = +180. Within each die's 60-byte block, the byte offsets for each stream are:

| Bytes | Stream |
|-------|--------|
| 2, 3 | EM1_HOST offset SB0 |
| 6, 7 | TABLE_PTE |
| 10, 11 | TEMP_RAIN |
| 14, 15 | NORMAL_HOST_SLC |
| 18, 19 | WRITE_BOOSTER |
| 22, 23 | RPMB_HOST |
| 26, 27 | RPMB_GC |
| 30, 31 | SWAPRAIN_WB |
| 34, 35 | SWAPRAIN_EM1 |
| 38, 39 | FTL_SUB |
| 42, 43 | EM1_GC |
| 46, 47 | NORMAL_HOST_TLC |
| 50, 51 | NORMAL_GC |
| 54, 55 | SWAPRAIN_HOST |
| 58, 59 | TABLE_LOG |

**Module IDs**: SLC_L2 = 0, TLC_L2 = 1, PTE = 2, LOG = 3, EM1 = 4, L1 = 5, SLC_GC = 6, TLC_GC = 7, RAID variants = 8–10

---

### PSW_F_P3_MDWLSV_0001 — Normal Test

- **Purpose**: Validates that the MDWLSV offset is correctly updated for each write stream (TLC, EM1, L1, Write Booster, RPMB) after sequential writes. Verifies that the recorded offset matches the P3 value from the NAND feature register for each stream.

- **LUN setup**: 4 LUNs each allocated 25% of total AU capacity — LUN0 = NORMAL, LUN1 = BOOT_A (EM1), LUN2 = BOOT_B (EM1), LUN3 = EM1; Write Booster allocated `0x1000` AU.

- **Key APIs**:
  - `project_api.issue_4029_to_get_MDWLSV_offset_information()` — queries the current MDWLSV table
  - `project_api.issue_4022_to_get_NAND_feature(die)` — returns NAND feature structure; `.P3.value` is the reference offset
  - `project_api.get_previous_info()` — returns the module ID of the last written stream
  - `api.Write10(lun, lba, block_count)` — precise CE-page-aligned write for controlled stream targeting
  - `rpmb.rpmb_write(lba, data)` — RPMB write to populate RPMB stream

- **Verification rule**: `offset != 0 AND offset == P3.value`

- **Exceptions**:
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET`

---

### PSW_F_P3_MDWLSV_0002 — SSU/ATS/H8 Test

- **Purpose**: Validates that MDWLSV offsets persist correctly across power-state transitions including SSU sleep, ATS idle, H8 hibernate, and HW_RESET. Verifies that a HW_RESET with power-down clears all MDWLSV offsets to zero.

- **Flows**:
  - Flow 6: SSU sleep → active; MDWLSV offsets must be preserved
  - Flow 7: Idle for 2 seconds; MDWLSV offsets must be preserved
  - Flow 8: `CmdSeqHibernate(loopcount=10, delayafterenter=500)`; MDWLSV offsets must be preserved
  - Flow 9: HW_RESET with `powerdown=True` → all MDWLSV offsets must be reset to 0

- **After HW_RESET**: `check_all_zero()` — asserts that every byte in the MDWLSV table is 0

- **Helper**: `tables_equal(t1, t2)` — compares two `MDWLSV_format` instances using `vars()` dictionary comparison

- **Exceptions**:
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_MDWLSV_0003 — Boundary Test

- **Purpose**: Tests MDWLSV boundary edge cases including single-plane fill behavior, SLC CE page wrap triggering an offset reset, and per-CE plane-by-plane offset tracking.

- **VC12 — Single plane fill**: Verifies `EM1_SB0_offset == EM1_offset` when only a single plane has been filled

- **VC13 — SLC page wrap**: Verifies that when the SLC Flash Entry Point (FEP) wraps around (`FEP % 4 == 3 AND CE == 1 AND plane == 0`), the MDWLSV offset is reset. The test loops until the wrap condition is met before asserting.

- **VC14 — Per-CE tracking**: Verifies that the MDWLSV offset reported equals the minimum P3 value across all CEs, confirming per-CE plane-by-plane tracking is correct.

- **Exceptions**:
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## media_scan

### Overview — Media Scan Testing (7 test files)

The media_scan folder contains 7 test files (numbered 0001–0007 and 0011) covering foreground (FG) and background (BG) media scan triggering, UECC injection scenarios, PSA interaction, booking queue interaction, and bin threshold logic.

---

### Shared pre_process

All media_scan tests share a common pre_process setup:

- `flash_setting = api.get_flash_setting()` — retrieves `Max_Fdevice` (max CE count) and `Plane_Per_Die`
- `fw_geometry = api.get_fw_geometry()` — retrieves `l84_vb_size_u0` (SLC VB size) and `l88_vb_size_u1` (TLC VB size)
- `TLC_WL_block = max_ce * max_plane * 16384 * 4 * 3` — bytes per TLC write-level
- `SLC_WL_block = max_ce * max_plane * 16384 * 4` — bytes per SLC write-level
- LUN configuration: LUN0 = NORMAL (`Total // 2` AU), LUN1 = ENHANCED_1 (`min(l44_enhanced1_max_n_alloc_u, Total // 2)` AU); RPMB is enabled

---

### PSW_F_P3_MediaScan_0001 — Power-Up Media Scan

- **Purpose**: Verify that a media scan is correctly triggered on HW reset (without power loss) and that the firmware properly handles UECC-injected VBs during the power-up scan.

- **VB types tested**: TLC_L2, SLC_L2, TLC_L1, LOG, PTE

- **UECC injection**:
  - TLC VBs: inject at pages `range(empty_page, empty_page + 12, 3)`
  - SLC / LOG / PTE VBs: inject at pages `range(empty_page, empty_page + 4)`

- **Reset method**: `api.init_tester_to_unit_ready(resetmode=HW_RESET, powerdown=False)` — HW reset without power loss to trigger power-up scan

- **Exceptions**:
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_MediaScan_0002 — FG Trigger Media Scan VHC

- **Purpose**: Verify foreground (FG) media scan triggered via `api.read_compare()` for Valid Host Copy (VHC) mode. Confirms that injected VBs are detected, scanned, and migrated after the scan completes.

- **VB injection**:
  - TLC_L1 / LOG / PTE: inject at `page = 0` (valid page with data)
  - TLC_L2 / SLC_L2: inject at `empty_page`

- **Scan flow**:
  1. `project_api.micron_vu_C085_param_with_data(spend_time)` — configure scan spend time
  2. `api.read_compare()` — trigger FG scan
  3. `issue_40C5_to_get_booking_queue()` — verify target VBs appear in booking queue
  4. `issue_40CF_to_get_scan_progress()` — verify scan progress and coverage

- **Post-scan**: `api.issue_C088_StartRefresh()` → poll bkops idle → verify VB has been migrated to a new location

- **Exceptions**:
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_MediaScan_0003 — BG Trigger Media Scan VHC

- **Purpose**: Same verification as PSW_F_P3_MediaScan_0002 (Valid Host Copy mode scan), but using a background (BG) trigger via `time.sleep(5)` instead of an explicit `api.read_compare()` foreground trigger.

- **Exceptions**:
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_MediaScan_0004 — FG Trigger Media Scan NDEP

- **Purpose**: FG media scan with UECC injected at the Next Defined Empty Page (NDEP), using explicit Physical Cell Address (PCA) construction to target precise NAND locations.

- **PCA field construction**:
  - `b4_mode`: 2 = TLC mode, 1 = SLC mode
  - `b5_ce`: chip enable index
  - `b6_plane`: plane index
  - `b10_block_l` / `b11_block_h`: lower and upper block address bytes
  - `l12_fpage = convert_page_to_page_order(page, isSLC) << 5` — flash page address with mode-appropriate page order

- **Exceptions**:
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_MediaScan_0005 — BG Trigger Media Scan NDEP

- **Purpose**: Same verification as PSW_F_P3_MediaScan_0004 (NDEP UECC injection), but using a background (BG) trigger via `time.sleep(5)` instead of an explicit FG trigger.

- **Exceptions**:
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_MediaScan_0006 — Media Scan With Already Booking RefreshQ

- **Purpose**: Verify that the media scan correctly skips VBs that are already present in the refresh booking queue (booked via C087), preventing duplicate refresh scheduling.

- **VB types tested**: CURRENT_L2_MLC, CURRENT_L1, CURRENT_L2_SLC, CURRENT_PTE, LOG_TAB_BLK, USED_BLK_POOL_MLC, USED_BLK_POOL_SLC

- **Booking VU**: `project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type, VB_list=[target_vb], booking_user=VUC087Paremeter.HighPriority)` — books the target VB into the refresh queue before the scan runs

- **Scan verification**: `issue_40CF_to_get_scan_progress()` — the `target_vb` must NOT appear in the `scanned_blocks` list, confirming it was correctly skipped

- **Exceptions**:
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_MediaScan_0007 — Media Scan With PSA

- **Purpose**: Verify that media scan is blocked during PSA pre-soldering and loading states, and that PSA VBs are correctly excluded from scan results after the SOLDERED state is reached.

- **State flow and expected scan behavior**:
  - `OFF` → scan proceeds normally
  - `PRE_SOLDERING` → scan is blocked
  - `LOADING_COMPLETE` → scan is blocked
  - `SOLDERED` → scan proceeds normally; PSA VBs excluded

- **Key VUs**:
  - `project_api.micron_vu_C085_param_with_data(spend_time)` — configure scan parameters
  - `issue_40CF_to_get_scan_progress()` — verify scan coverage and blocked/allowed behavior per state

- **Exceptions**:
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `SIGHTING_RESPONSE_UNEXPECTED`
  - `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`

---

### PSW_F_P3_MediaScan_0011 — Media Scan Bin Low/High Test

- **Purpose**: Verify BFEA bin threshold logic — VBs with bin values below `BIN_LOW` are skipped by the scanner, VBs above `BIN_HIGH` are added to the refresh queue, and VBs with bin values between `BIN_LOW` and `BIN_HIGH` are actively scanned.

- **VU for bin control**: `project_api.issue_40B0_Bfea_Scan(mode, vb, ce, bin)` — mode `2` sets the bin value; mode `3` reads the current bin value

- **Configuration parameters via C085**:
  - `set_media_scan_bin_low` — sets the lower bin threshold
  - `set_media_scan_bin_high` — sets the upper bin threshold
  - `last_scan_spend_time` — configures the scan time budget

- **4 sub-tests**:
  1. Open TLC block with `bin < BIN_LOW` → block is skipped by scanner
  2. Closed TLC block with `bin < BIN_LOW` → block is skipped by scanner
  3. Closed TLC block with `bin > BIN_HIGH` → block is added to the refresh booking queue
  4. Closed TLC block with `BIN_LOW < bin < BIN_HIGH` → block is actively scanned

- **Exceptions**:
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## outgoing_slx

### Overview — Outgoing SLx (Write/Erase Trim State) Verification (2 tests)

The outgoing_slx folder contains 2 tests verifying that VB trim states (SLx_TRIM vs. POR_TRIM) are correctly assigned at each stage of the device lifecycle, from initial state through RPMB write, LUN configuration, purge, EM1 write, and PSA flow.

---

### Shared Infrastructure

- `api.MP().execute()` — executes the Manufacturing Protocol (MP) initialization sequence
- `api.first_init_to_max_hs_gear(link_startup_mode, ref_clk)` — initializes the UFS link at maximum HS gear speed
- `get_vb_trim_set()` — parses 4-byte VB entries from the VB list:
  - `group[5:0]` — VB group classification
  - `dirty[6]` — dirty flag
  - `access_mode[8]` — current access mode
  - `vb_trim[17:16]` — trim state; `SLx_TRIM` → added to `slx_trim_set`; `POR_TRIM` → added to `por_trim_set`
- `set_LUN_configuration()` — uses `ExecuteCMD.WriteDescriptor` followed by `ExecuteCMD.RequestSense` (NOT `TestUnitReady`) to confirm LUN configuration
- **LUN layout**: LUN0 = NORMAL (8192 AU), LUN1 = ENHANCED_1 (2000 AU), LUN3 = NORMAL (8192 AU)

---

### PSW_F_P3_Outgoing_SLx_0001 — Verify Initial Open VB State

- **Purpose**: Verify that VBs are correctly classified as `SLx_TRIM` or `POR_TRIM` across each lifecycle stage: initial device state, after RPMB write, after LUN configuration, after purge, and after EM1 write.

- **State transitions and expected trim classification**:
  - **Initial**: `FREE_BLK_QUEUE` VBs → `SLx_TRIM`; LIST / PTE / LOG VBs → `POR_TRIM`
  - **After RPMB write**: `CURRENT_L2_SLC` VB appears in `POR_TRIM`
  - **After LUN config**: `CURRENT_L1` and `CURRENT_L2_MLC` VBs appear in `POR_TRIM`
  - **After purge**: `FREE_BLK_QUEUE` VBs transition from `SLx_TRIM` to `POR_TRIM`
  - **After EM1 write**: The same SLC VB index used during the RPMB write is reused

- **`purge_all()`**: `api.set_flag(FlagIDN.PURGE_EN)` → poll `PURGE_STATUS == 0x03` with a 10-minute timeout

- **Exceptions**:
  - `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`
  - `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT`

---

### PSW_F_P3_Outgoing_SLx_0002 — Verify PSA Write VB State

- **Purpose**: Verify that VB trim states are correctly assigned during and after the PSA write sequence. After completing the PSA flow followed by HW_RESET and EM1 write, the expected final state is: `FREE_BLK_QUEUE` in `SLx_TRIM`, `CURRENT_L1` and `CURRENT_L2_SLC` in `POR_TRIM`.

- **PSA sequence**:
  1. `write_attribute(PSA_DATA_SIZE)` — set the PSA data size
  2. `write_attribute(PSA_STATE = PRE_SOLDERING)` — advance to pre-soldering state
  3. `sequential_write()` — write PSA data payload
  4. `write_attribute(PSA_STATE = LOADING_COMPLETE)` — complete the loading phase

- **Key difference from 0001**: Uses `RequestSense` after `WriteDescriptor` to confirm LUN configuration (not `TestUnitReady`), consistent with the outgoing_slx shared infrastructure pattern.

- **Exceptions**:
  - `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`

---

## PPM

### PSW_F_P3_PPM_0001 — PPM (NAND Feature P1/P2/P3/P4) Validation

- **Purpose**: Verify that the P1, P2, P3, and P4 values read from NAND feature address `0xEB` match the expected values for each CE (Chip Enable). The rule is CE count == 4 → specific non-zero expected values per CE; CE count != 4 → all values must be zero.

- **VU**: `project_api.issue_4022_to_get_NAND_feature(ce, feature_address=0xEB)` — returns a structure with fields `P1`, `P2`, `P3`, `P4`

- **CE count calculation**: `api.get_flash_setting()` → uses `.FLH_Quantity` and `.Parallel` fields to compute the effective CE count

- **Verification rule**:
  - If `CE == 4`: compare P1/P2/P3/P4 against expected per-CE values
  - If `CE != 4`: assert all of P1/P2/P3/P4 are zero

- **Exceptions**:
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## program_fail

### Overview — Program Fail Injection Testing (75 tests + program_fail_api.py)

The program_fail folder contains 75 test files covering program fail and erase fail injection across every VB type supported by the FTL. Each test injects a controlled fail event and verifies that the firmware correctly handles the failure by replacing the bad block and updating the Bad Block Table (BBT).

---

### program_fail_api.py — Shared Infrastructure

- `calculate_bbt(payload)` — parses the VU 405E payload: first 4 bytes = bad block count; subsequent 8-byte entries contain:
  - `BB_Block = bytes[0:3]` — bad block address
  - `BB_CE = (byte3 >> 3) // 6` — CE index of the bad block
  - `BB_Plane = (byte3 >> 3) % 6` — plane index of the bad block
- `config_lun(normal_list, em1_list)` — configures LUN layout using `ConfigDescriptor310`
- **`fail_type` values**:
  - `0` = program fail
  - `1` = erase fail
  - `3` = TLC page program fail
- **`pool_type` values**:
  - `1` = normal replacement pool
  - `2` = hidden area replacement pool
- All tests use `skip_response_check=True` during fault injection to avoid false failures on injected error responses
- `G_TIMEOUT_ALL` exceptions are caught to handle cases where FW becomes stuck due to injected faults

---

### VB Types Covered

| Test Range | VB Type |
|-----------|---------|
| 0001–0019 | Normal EM1 / SLC blocks |
| 0020–0026 | TLC page program fail |
| 0027–0033 | MLC program fail |
| 0034–0040 | PTE (Page Table Entry) program fail |
| 0041–0047 | LOG (log block) program fail |
| 0048–0054 | LIST (list block) program fail |
| 0055–0061 | L1 (Level-1 cache) program fail |
| 0062–0068 | EM1 LUN program fail |
| 0069–0075 | WB (Write Booster) LUN program fail |

---

### Key VU Commands (used across all tests)

- `project_api.issue_C012_to_create_program_erase_fail(info, fail_type, block_info_list_count)` — injects the specified program or erase fail event on the target block
- `project_api.issue_40D6_to_get_predicted_next_n_replacement_block(ce, plane, next_n, pool_type, is_CIS, pf_on_open_data)` — queries the FW for the predicted next N replacement blocks from the specified pool
- `project_api.issue_405E_to_get_bad_block_information()` — reads the BBT to verify the bad block was correctly recorded after the injected fail

---

### Assert Codes

| Code | Meaning |
|------|---------|
| `0x204` | Over N replacement tries exceeded — FW has exhausted all replacement attempts |
| `0x202` | No spare normal block available in the replacement pool |
| `0xB7` | No spare hidden area block available |
| `0x510` | Over 1 time hidden replacement — hidden area replacement limit exceeded |

---

## PSA

### Overview — Pre-Soldering Authentication (PSA) Testing (6 tests)

The PSA folder contains 6 tests covering the complete PSA lifecycle, interrupt/recovery flows, event logging, VU command validation, boot LUN programming, and HIR interaction during PSA-related inhibition.

---

### Shared PSA VU Commands

- `project_api.issue_405C_get_PSA_post_reflow_progress()` — reads post-reflow migration progress
- `project_api.issue_404F_get_PSA_migration_state()` — reads current PSA migration state
- `project_api.issue_4050_check_PSA_buffer_size()` — reads remaining PSA buffer size
- `VU_clear_PSA_state()` — clears PSA state in post-process cleanup (called via VendorCmdWrite)

**PSA state machine**: `OFF` → `PRE_SOLDERING` → `LOADING_COMPLETE` → `SOLDERED`

---

### PSW_F_P3_PSA_0001 — Full PSA Flow (38 steps)

- **Purpose**: Complete PSA lifecycle validation covering all 38 steps from initial LUN configuration through the final SOLDERED state. Validates every state transition, data write, and verification point in the production PSA flow.

- **Flow summary**:
  1. Configure LUN layout
  2. Write `PSA_DATA_SIZE` attribute
  3. Issue UNMAP to prepare target LBAs
  4. Advance PSA state to `PRE_SOLDERING`
  5. Load PSA data payload via sequential writes
  6. Advance PSA state to `LOADING_COMPLETE`
  7. Perform power cycle (HW_RESET with power-down)
  8. Write first non-PSA host data
  9. Advance PSA state to `SOLDERED`
  10. Verify all state transitions and data integrity

---

### PSW_F_P3_PSA_0002 — Interrupt Flow

- **Purpose**: Verify PSA behavior under Sudden Power Off and Recovery (SPOR) during the `PRE_SOLDERING` state. Also verifies that HIR (High Intensity Refresh) and HID (Host-Initiated Defrag) are correctly rejected during the PSA flow.

- **Key**: FW PSA state is tracked via `payload[469]` in the health report response

---

### PSW_F_P3_PSA_0003 — Event Log

- **Purpose**: Validate that temperature threshold crossing events and erase count (EC) threshold crossing events are correctly recorded in the firmware event log during PSA mode.

- **Events verified**: Temperature threshold event log entries and EC threshold event log entries with correct field values

---

### PSW_F_P3_PSA_0004 — VU Test

- **Purpose**: Validate the behavior of three PSA-specific vendor commands:
  - VU `4050` — remaining buffer size reporting
  - VU `404F` — migration state reporting
  - VU `405C` — post-reflow migration progress reporting

---

### PSW_F_P3_PSA_0005 — Write Boot EM1

- **Purpose**: Validates the production configuration flow for programming BootLUN A and B with EM1 data. Verifies correct CE count handling and BootLUN A/B assignment after programming.

---

### PSW_F_P3_PSA_0006 — HIR Without Inhibit

- **Purpose**: Verify HIR (High Intensity Refresh) behavior when `INHIBITION_TIME` is set to 240 seconds. Confirms that HIR triggers XTEMP booking and that the VB MLC trim state correctly transitions from PSA trim to POR trim after the refresh.

- **Key API**: `api.write_attribute(idn=AttributeIDN.INHIBITION_TIME, val=240)` — sets the inhibition window to 240 seconds

- **Verification**: `check_vb_mlc_trim(PSA → POR)` — confirms MLC VBs transition from PSA-associated trim state to standard POR_TRIM after HIR completes
