# UFS Pattern Test Implementation Wiki — Part 3

Pattern folders covered: `rain`, `read_disturb`, `read_scan`, `refresh`, `reh`, `sample_code`, `sgm`, `srambler`, `sticky_read`, `tempco`, `Thermal_Protection`, `vth_sweep`, `wear_leveling`, `xtemp`

---

## rain

### Overview — RAIN (Redundant Array of Independent NAND) Testing (19 tests + mutual_fun.py)

RAIN provides parity-based data protection across NAND blocks. Tests cover parity calculation verification, UECC injection and recovery, open/closed VB protection, enable/disable controls via VU D08B, and multi-UECC failure scenarios.

---

### mutual_fun.py — Shared RAIN Functions

- `rain_pattern_precondition()` → `(TestNormalLun, TestEM1Lun, TestWBLun, flash_setting, fw_geometry)` — configures LUNs (0=Normal, 1=EM1, 3=WB), refreshes PTE/L1 VBs, polls BKOPS idle
- `get_geometry_parameter()` → `(max_ce, max_plane, max_pageline)`
- `config_lun(normal_list, em1_list)` — writes 4 config descriptor tables
- `inject_UECC(pca, SLC_enable)` — writes 0xAA raw data (SLC: 16KB, TLC: 60KB) with ECC=1
- `inject_bitflip(pca, SLC_enable, flip_bits)` — reads raw (ECC=0), flips bits, erases, rewrites (ECC=0)
- `direct_read_raw_data_and_check_status(pca, SLC_enable, expect_status, REH_Enable)` — reads and checks `payload[0x4000:0x4004]`
- `create_closed_vb(testMode, lun, write_record)` → `(last_lba, vb)`
- `read_compare_rain_result(write_record, compare_method, expect_error)` — wraps `api.read_compare`
- `write_data_more_than_N_pageline(pageline_cnt, lun, testMode, write_record)` → `(last_lba, cursor)`
- `write_data_more_than_N_page(page_cnt, lun, testMode, write_record)` → `(last_lba, cursor)`
- `get_specific_open_vb_cursor(testMode)` → `OpenVBInfoUnit`
- `get_specific_RAIN_SWAP_vb(testMode)` → `(vb, pageline, ffp)`
- `get_rain_parity_parameter(testMode)` → `(rain_group_cnt, rain_user)`:
  - TLC: 24 / `HOST_TLC_RAIN`
  - SLC: 8 / `HOST_EM1_RAIN`
  - WB: 8 / `WB_RAIN`
  - PTE/L1/LOG: 1 / `TABLE_RAIN`
- `get_rain_enable_disable_parameter(testMode)` → `(keep_rain, data_recovery)` as `RainVB` enum values
- `bytearray_xor(bytearray_list, initXOR, check_len)` — XOR multiple buffers for parity calculation
- `phison_pca_to_micron_pca(pca)` — converts PCA format
- `UFSMapper` class — LBA ↔ physical location conversion (M=CE count, N=plane count)

**Key project_api calls:**

- `issue_4055_to_get_rain_parity(rain_user, group)`
- `issue_4054_to_get_rain_info(currentCE)`
- `issue_D08B_to_enable_or_disable_Rain(Table_and_S_CHK_rain, Host_Permanent_Rain, Host_Simple_Rain, host_full_block_protection_rain)`
- `issue_C087_to_add_VB_to_bookingQ_and_book_refresh()`
- `issue_C088_to_start_or_stop_refresh()`

**Enums:**

- `TestMode`: `TEST_TLC(0)` / `SLC(1)` / `WB(2)` / `PTE(3)` / `L1(4)` / `LOG(5)` / `TMP_RAIN(6)`
- `RainUser`: `HOST_TLC_RAIN`, `HOST_EM1_RAIN`, `WB_RAIN`, `TABLE_RAIN`, `RECOVER_USER`
- `RainVB`: `TLC`, `EM1`, `WB`, `Table`, `S_CHK`, `ALL`

---

### PSW_F_P3_RAIN_0001 — Parity In RAM Calculate Test

- **Purpose**: Verify RAIN parity calculated manually from raw NAND matches VU4055 value
- **Flow**: Write ≥3 pages → SPOR → direct read each CE/plane → XOR first 8 bytes → compare vs VU4055 parity bytes[0:8]
- **Key**: `group = first_empty_physical_page % rain_group_cnt`; skips invalid planes from ICS table
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0002 — Temporary Protection Test

- **Purpose**: Verify RAIN recovery for open (temp protection) VBs; check event logs 0x300C (InitUECCEventLog), 0x6001 (BeUeccEvent), 0x3011 (RainRecoveryEventLog), booking queue, health report
- **Flow**: Write TLC/WB/EM1 → inject UECC → SPOR → read_compare → check_UECC_refresh_booking_Q → verify health report counters
- **Event log 0x3011 fields**:
  - `errblock`, `die`, `errType=0`, `logVB=0xFFFF`, `pvb=0xFFFF`, `pageInfo`
  - `recovResult=0`, `openVbFlag=1`, `vbType`, `parityPosition=2`, `abnormalUECCPhy=0`
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0003 — Permanent Protection Test

- **Purpose**: RAIN recovery for closed VBs with SPOR-induced APL; `get_APL_flag_of_VB(log_VB)` must return 1
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `DLL_CRC32_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0004 — MultiUECC Host Read Test

- **Purpose**: Host can read non-UECC areas after injecting 24 multi-UECC locations; unmap UECC LBAs, then verify trimmed reads succeed
- **UFSMapper**: `lba_to_location(lba, is_TLC)` → `{ce, plane, fpage, lmu, pageline}`
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0005 — RAM Flush Test

- **Purpose**: RAIN parity flush from SRAM to SWAP VB under Nothing / DeepSleep+SPOR / POR / SwitchPartition+SPOR scenarios
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0006 — Plane Based Protection Test (PTE)

- **Purpose**: PTE VB RAIN (plane-based last valid page parity); manual XOR vs last page content; inject UECC → SPOR → verify recovery
- **Detail**: PTE uses BIT20 op for last CE/plane (parity page), BIT24 for data pages
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0007 — UECC Recovery Fail Test

- **Purpose**: Inject 2 UECCs in same RAIN group → recovery failure → host read returns `MEDIUM_ERROR`; health report fail counter increments; tests open/closed VBs of TLC/SLC/WB/PTE
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `SIGHTING_RESPONSE_UNEXPECTED`, `DLL_RESPONSE_ERROR`

---

### PSW_F_P3_RAIN_0008 — Host Simple Rain Enable/Disable

- **Purpose**: VU D08B byte 14 bit control over Host Simple RAIN (BIT4/5/6=data_recovery, BIT0/1/2=SRAM encode); parity held when disabled, updates when re-enabled
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0009 — Table S_CHK Rain Enable/Disable

- **Purpose**: VU D08B byte 12 BIT control for Table/S_CHK RAIN; FW spare mark = 0x83 (DUMMY) when last_valid_page encode disabled
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0010 — Host Permanent RAIN Enable/Disable

- **Purpose**: VU D08B byte 13 BIT control; last_pageline: TLC=1111, SLC=1103
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0011 — Host Full Block Protection RAIN Enable/Disable

- **Purpose**: VU D08B byte 16 BIT control; SWAP VB pointer must not advance when disabled
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0012 — SWAP Parity UECC Test

- **Purpose**: RAIN recovery when SWAP parity block itself has UECC, plus host data VB has UECCs
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0013 — Last Valid Page Parity UECC Test

- **Purpose**: Recovery fails when both last valid page and host data page have UECC simultaneously
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0014 — Temp RAIN VB Parity Invalid Test

- **Purpose**: SWAP/Temp RAIN VB has UECC + host data block also gets UECC = unrecoverable
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0015 — Rain Info Test

- **Purpose**: Validate all VU4054 RAIN info fields; D08B enable/disable bitmap toggling; RAIN accumulation count accuracy per VB type
- **Fixed fields**: SLC pageline=1104, TLC pageline=3312; accumulation = 4 sectors per CE/plane per pageline
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `PATTERN_ASSERT_UNEXPECTED_CONDITION`

---

### PSW_F_P3_RAIN_0016 — Parity Rebuild Fail Test

- **Purpose**: UECC in last valid page of open VB (parity not yet flushed to SWAP) triggers rebuild fail
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0017 — APL Closed VB RAIN Protection Test

- **Purpose**: RAIN recovery for closed VB with SPOR-induced APL; 10 retry attempts with increasing delay (100ms–1000ms)
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_RAIN_0018 — Host Read No UECC Area Test

- **Purpose**: After injecting UECC + unmapping some LBAs in EM1 LUN, verify: non-UECC reads succeed, UECC area reads return `MEDIUM_ERROR`
- **Config**: 50/50 split Normal/EM1; fixed UECC LBA list [13098..13121]; unmap LBAs 13107–13118
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `DLL_RESPONSE_ERROR`

---

### PSW_F_P3_RAIN_0019 — All Page UECC Test

- **Purpose**: All pages of TLC VB last WL subblock have UECC; verify data compare still passes with remaining parity
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## read_disturb

### Overview — Read Disturb Testing (5 tests + mutual_fun.py)

Read Disturb tests verify that the FW correctly tracks read counts per VB, triggers RD scans when thresholds are exceeded, updates RC_TH post-scan, and handles refresh booking. Tests also cover EC-based threshold initialization, RC persistence across power cycles, and quick-scan triggering via BFEA errors.

---

### mutual_fun.py — Shared Read Disturb Functions

- `get_VB_group(show)` → `Dict[int, Dict[str,int]]` — parses 32-bit VB bitmap:
  - `group[5:0]`, `access_mode[7:6]`, `dirty[8]`, `partition[10:9]`
  - `src_uecc[15]`, `vb_trim[17:16]`, `risky_type[19:18]`
- `polling_Read_Disturb_idle(vb)` — polls `issue_40CB_to_get_total_Read_Count_and_Flush_RC_table_threshold(LogicalVB=vb)` until `IsScanTaskIdle.value==1`; timeout=1 min
- `get_EC_RC_TH(mConfig, EC, is_SLC, is_open, vb)` → `(field_name, value)` — finds EC group bracket (0–4), returns `XLC_EC_RC_TH_{FP}B{group}*1000`
- `leave_inhibition_mode()` — 1001 reads of lba=0 with FUA
- `read_LBA_repeatedly(lun, lba, read_times)` — enqueues `read_times` Read10 commands with `fua=1`

**Key project_api calls:**

- `project_api.get_all_VB_read_count()`
- `set_all_VB_read_count(data_payload)`
- `set_specific_VB_read_count_threshold(VB_Num, RC_TH_Value)`
- `issue_40CA_to_get_get_Read_Count_threshold_table()`
- `issue_40CB_to_get_total_Read_Count_and_Flush_RC_table_threshold(LogicalVB)`
- `issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(flag)`
- `issue_40CC_to_trigger_Read_Disturb_scan(target_vb)`
- `issue_408C_to_get_EC_RC_threshold_table(wBlockType)`
- `get_read_disturb_counter()`
- `issue_40FE_to_read_enhanced_health_report()`

---

### PSW_F_P3_Read_Disturb_0001 — RD Trigger Test

- **Purpose**: Verify RC increases after reads; RD scan triggers when RC > RC_TH; RC_TH updates post-scan; validates 40CB output
- **Test matrix**: 4 BlockCases (TLC_Open/Closed, SLC_Open/Closed) × 2 ScanCases (RC=10 vs RC=RC_ALL_WL_SCAN+1) × 2 UpdateCases
- **Key**:
  - `mConfig.RC_ALL_WL_SCAN * 1000000` threshold for full-VB scan
  - 40CB fields: `TotalReadCount_RC_VB`, `FlushRCTableThreshold_RC_TH_VB`, `CECCThreshold_ReadDisturbScan`, `IsScanTaskIdle`
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_Read_Disturb_0002 — RD Refresh Test

- **Purpose**: When RC reaches 0xFFFFFFFF, VBs booked for refresh with `RD_SCAN_BOOKING_1` at HighPriority; health report counters verified per VB type
- **VB type → health field mapping**:
  - `CURRENT_L2_EM1` / `USED_BLK_POOL_EM1` → `em1`
  - `CURRENT_L2_TLC` / `USED_BLK_POOL_TLC` → `normal_tlc`
  - `CURRENT_L2_TLC_WB` / `USED_BLK_POOL_TLC_WB` → `normal_slc`
  - `PTE_POOL` / `CURRENT_PTE` → `table`
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_Read_Disturb_0003 — RD Create Block Test

- **Purpose**: Verify RC_TH initialized based on EC bracket at block creation; 5 EC groups (0–4); validates VU 408C EC_RC_TH table
- **EC bracket**: `XLC_EC_group = mConfig.XLC_EC_{group} * 100`; RC_TH = `XLC_EC_RC_TH_{FP}B{group}*1000`
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_Read_Disturb_0004 — RD Flush Test

- **Purpose**: RC and RC_TH persist correctly across POR and SSU Sleep; set random RC/RC_TH → verify after POR; reads before SPOR accumulate correctly
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_Read_Disturb_0005 — UECC BF Quick Scan Test

- **Purpose**: Triggering RD scan via VU 40CC on VB with BFEA error causes FW to raise quick-scan flag
- **VU**: `project_api.issue_40CC_to_trigger_Read_Disturb_scan(target_vb)`, `polling_Read_Disturb_idle()`
- **Note**: Current verification steps are mostly placeholders
- **Exceptions**: None currently raised

---

## read_scan

### Overview — Read Scan Testing (5 tests + mutual_fun.py)

Read Scan tests verify the FW mechanism that tracks UECC errors per WL across open VBs and triggers background scanning when errors pass the SAFE_AREA boundary. Tests cover normal scan flow, selective disabling, SSU-triggered release, POR persistence, and interaction with GC.

---

### mutual_fun.py — Shared Read Scan Functions

- `erase_all_lun(write_record)` — Unmap all LBAs + FormatUnit
- `get_PCA_VB_and_print(lun, lba)` → `(vb, pca)` — with remap lookup via `issue_40C7_to_get_bad_block_info`
- `ssu_sleep_and_active()` — SSU Sleep + Active

**Key project_api calls:**

- `check_if_current_VB_scan_in_progress_completed(VB)` → 0=not scanning / 1=scanning with errors
- `get_Normal_VB_Scan_Pages(RSTriggerBy)` → WL list
- `get_gc_read_scan_released_scan_pageline()` → WL numbers with errors
- `get_APL_flag_of_VB(log_VB)`
- `set_Enable_Disable_Read_Scan(enable)`
- `issue_D014_to_set_read_recovery_module(die, bigIndex, smallIndex, nandMode, isSpeciBlock, block, isPSA)`
- `issue_40C0_to_get_VPCT_description(0xFFFFFFFF, 0x0)`
- `issue_C012_to_create_program_erase_fail()`

---

### PSW_F_P3_Read_Scan_0001 — Read Scan Normal Test

- **Purpose**: Full integration test; inject UECCs at WL 0/1/3/9; verify scan detects progressively as data passes SAFE_AREA boundary; tests SPOR with APL interaction
- **Key parameters**:
  - `READ_SCAN_SAFE_AREA` from mConfig
  - `WL_block = max_ce * max_plane * 16384 * 4 * 3`
  - Only WL%3==0 pages included in scan list
- **Flow**:
  1. Write 15 WLs → inject UECC at multiple WLs → write to 16 WLs → SSU
  2. Verify scan triggered → `get_gc_read_scan_released_scan_pageline()`
  3. Expect WL0 and WL3 (WL%3==0)
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `DLL_CRC32_COMPARE_FAIL`

---

### PSW_F_P3_Read_Scan_0002 — Read Scan Error Test

- **Purpose**: Disable scan via VU or mConfig fields (`PAGE_TYPE_SELECT`, `TLC_data_block`, `SUBBLOCK_SELECT`, `TEMP_LOW/HIGH`); when disabled, scan status=0 even with UECC; when only some subblocks disabled, scan still triggers for enabled ones
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_Read_Scan_0003 — Read Scan SSU Release Test

- **Purpose**: SSU Sleep triggers scan release at `READ_SCAN_SAFE_AREA * (SliceCnt + 2) - 1` LWWL boundary; after VB close parity released (VU4055 returns error); VB migrates to `FREE_BLK_QUEUE_TLC` after refresh
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `SIGHTING_RESPONSE_UNEXPECTED`

---

### PSW_F_P3_Read_Scan_0004 — Read Scan Init Test

- **Purpose**: Verify Read Scan state preserved across POR (init); when `CompleteSlice == Slice`, scan resets to status=0 after POR
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `DLL_CRC32_COMPARE_FAIL`

---

### PSW_F_P3_Read_Scan_0005 — Read Scan GC Test

- **Purpose**: Read Scan interaction with GC for L1_GC/EM1_GC/WB_GC/PSA_GC; inject CECC to trigger GC, then inject UECC in GC destination block; verify data integrity
- **VPCT tracking**: `issue_40C0_to_get_VPCT_description()` → `GC_DEST` / `GC_SOURCE` / `GC_FG_QUEUE` / `GC_BG_QUEUE` bits
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT`

---

## refresh

### Overview — Refresh Queue Management Testing (4 tests + mutual_fun.py)

Refresh tests verify the booking queue mechanism (VU C087/C088), priority handling (HP/MP/LP), deduplication, error cases, and event log generation. Tests ensure VBs correctly transition from booked state through refresh to FREE_BLK_QUEUE_TLC.

---

### mutual_fun.py — Shared Refresh Functions

- `config_lun()` → `(slc_lun=0, tlc_lun=1)` — fixed: LUN0=ENHANCED_1 (half AU), LUN1=NORMAL (half AU), WB=0
- Trigger functions:
  - `trigger_ReadDisturb_refresh()`
  - `trigger_UECC_refresh()`
  - `trigger_wear_leveling_lowgap_refresh()`
  - `trigger_wear_leveling_highgap_refresh()`
  - `trigger_mediascan_refresh()`
  - `trigger_hir_refresh()`
  - `trigger_xtemp_refresh()`
  - `trigger_psa_refresh()`
  - `trigger_bfea_refresh()`
- `verify_refresh_event_logs(vb_list, expect_user, log_ids=(0x3006, 0x3051))` — validates BookRefEventLog (0x3006) and RefStartEventLog (0x3051)
- `get_HP_MP_LP_list(vb_list, max_cnt)` → `Dict[VUC087Paremeter, List[int]]`
- `check_booking_queue(PriorityDict)` → `BookingQueue` — verifies 40C5 matches expected priority→VB mapping
- `check_vb_release(PriorityDict)` → `sorted_vb_dict` — verifies VBs migrated to `FREE_BLK_QUEUE_TLC`
- `check_booking_user_in_queue(VB_list, expect_user, expect_priority)`

**Key project_api calls:**

- `issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type, VB_list, booking_user)`
- `issue_C088_to_start_or_stop_refresh(bParameter0)`
- `issue_40C5_to_get_booking_queue()`
- `issue_C085_to_set_media_scan_parameters()`
- `clear_event_logs()`

---

### PSW_F_P3_Refresh_0001 — Refresh Execute Test

- **Purpose**: Full end-to-end refresh: create open VBs (L2_TLC/SLC, L1, PTE) → C087 enqueue at HP/MP/LP → verify queue → persist across SSU/power-down → C088 StartRefresh → verify VB groups changed → health report counters incremented
- **Counters verified**:
  - `read_reclaim_count_for_slc_table`
  - `read_reclaim_count_for_tlc`
  - `read_reclaim_count_for_em1`
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `PATTERN_ASSERT_UNEXPECTED_CONDITION`

---

### PSW_F_P3_Refresh_0002 — Refresh Enqueue Normal Test

- **Purpose**: Booking queue handles HP/MP/LP priority sorting with deduplication; `DisableEnqueueInRefreshBQ` (C088 mode 4) blocks new entries; `EnableEnqueueInRefreshBQ` (mode 5) resumes
- **Dedup rule**: HP wins over MP/LP for same VB; verified via `check_booking_queue()`
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_Refresh_0003 — Refresh Enqueue Error Test

- **Purpose**: All error cases for C087: wrong VB type, free block VBs, queue overflow (>10 VBs), non-existent VB → each returns `TARGET_FAILURE` / `CHECK_CONDITION` / `ILLEGAL_REQUEST` / `ASC=0x1A` / `ASCQ=0x00`
- **Key helper**: `enqueu_error_case()` → checks:
  - `b6_response=TARGET_FAILURE`
  - `b7_status=CHECK_CONDITION`
  - `b2_sense_key=ILLEGAL_REQUEST`
  - `b12_asc=0x1A`
  - `b13_ascq=0x00`
- **Exceptions**: `SIGHTING_RESPONSE_UNEXPECTED`

---

### PSW_F_P3_Refresh_0004 — Refresh Enqueue Type Test

- **Purpose**: Different refresh trigger types result in correct BookingUser and Priority in booking queue; BookRefEventLog (0x3006) and RefStartEventLog (0x3051) correctly generated
- **Test cases**:
  - `ReadDisturb` → `RD_SCAN_BOOKING_1` / High
  - `ReadUECC` → `EH_BOOKSIGNALUECC_BOOKING_0` / High
  - `sWL_LowGap` → `SWL_REFRESH_LOW_GAP` / Low
  - `sWL_HighGap` → `SWL_REFRESH_HIGH_GAP` / Medium
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## reh

### Overview — Read Error Handling Testing (2 tests)

REH tests verify the FW error recovery path when NAND pages return ECC errors. Tests cover both SLC and TLC block types, validating ERS statistics, sticky read entry conditions, and correct interaction with the read recovery module.

---

### PSW_F_P3_REH_0001 — SLC REH Test

- **Purpose**: Read Error Handling for SLC blocks; verify ERS statistics and sticky read behavior
- **VU Commands**:
  - VU 4066: `project_api.issue_4066_force_current_read_last_as_sticky_read()`
  - VU D014: `project_api.issue_D014_to_set_read_recovery_module(die, bigIndex, smallIndex, nandMode, isSpeciBlock, block, isPSA)`
  - VU D014 (set table): `project_api.issue_D014_to_set_last_table_content()`
  - VU 40BA: `project_api.issue_40BA_to_get_error_recovery_statistics()`
  - VU 40F9: `project_api.issue_40F9_to_get_rr_number_and_error_bits()`
- **Flip bits**: 150-bit flip on SLC page for HECC injection
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_REH_0002 — TLC REH Test

- **Purpose**: Same as 0001 but for TLC blocks; tests `TLC_BLOCK_TLC` / `MLC` / `SLC` page types
- **Also uses**: `api.direct_read()` for raw page reads
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## sample_code

### Overview — API Sample Code (39 files)

Comprehensive API reference samples covering common UFS test patterns. These files serve as canonical usage examples for test developers integrating new patterns.

---

### Key Patterns Demonstrated

**Config descriptors:**

- `api.get_config_descriptors()` → modify → `api.push_write_config(desc, index)`
  - index 0–2: `b2_conf_desc_continue=ENABLE`
  - index 3: `DISABLE`
- → `ExecuteCMD.send()`

**Manual mode:**

- `cmd.set_option(manual_mode=True).enqueue()` returns index
- `send(clear_on_success=False)` then `read_response(index)`

**Timeouts:**

- `api.UniformTimeout(val, unit=api.TimeResolution.us)` for command timeouts

**Task abort:**

- `api.push_abort_task(target_idx)` + `api.check_if_target_is_aborted(target_idx, tm_idx)`

**FBO:**

- `api.FboVersion0101()` with analysis and optimization flows

**FFU:**

- `api.search_ffu_bin(FFUBinType, FFUSvnType)`
- `api.send_ffu_write_buffer()`

**RPMB:**

- Key programming, counter read, authenticated read/write

**Speed change:**

- HS gear/series changes via DME attributes

**Write record pattern:**

- `api.get_empty_write_record()` → `api.save_write_info_by_cmd(cmd, write_record)` → `api.read_compare(write_record)`

---

## sgm

### Overview — Scan Guard Mechanism Testing (5 tests + mutual_fun.py)

SGM tests verify the FW scan-guard mechanism that detects and retires bad blocks based on dynamic and static read count thresholds. Tests cover normal scan flow, error event log validation, multi-VB simultaneous flagging, system VB handling, and POR persistence.

---

### mutual_fun.py — Shared SGM Functions

- `choose_D017_param()` — 13 cases mapping test scenarios to D017 parameters
- `check_vb_in_BBT()` — verify VB entered BBT after retirement
- `compare_eventlog_0x0026()` / `0x6009()` / `0x6008()` / `0x6002()` — event log validators
- `purge_operation()` — full purge cycle
- `config_lun()` — LUN configuration
- `VBPolicy` enum

**Key VU Commands:**

- VU 4071: `project_api.issue_4071_to_get_SGD_scan_parameters()` — get scan parameters
- VU C071: `project_api.issue_C071_to_set_SGD_scan_parameters(param, isSGS)` — set scan parameters
- VU D017: `project_api.issue_D017_to_create_SGM_fail(...)` — create SGM fail (13 scenarios)
- VU D018: `project_api.issue_D018_Disable_Enable_DM_Bg_Task_In_Bank(flag)` — disable DM background
- VU 404B: `project_api.issue_404B_to_erase_with_SGM(vb, ce, plane, block)` — erase with SGM

**Event log IDs:**

- `0x6008` — touchup
- `0x6009` — scan done
- `0x0026` — BB retirement
- `0x6002` — BB retirement HP

**SGM parameters:**

- `sgs_scan_dynamic_read_count` — RC level trigger threshold for dynamic scan
- `sgs_scan_static_read_count` — RC level trigger threshold for static scan

---

### PSW_F_P3_SGM_0001 — Normal SGM Test

- **Purpose**: mConfig SGS thresholds; RC level trigger loop for TLC_L2/WB_L2/SLC_L2; verifies normal scan/retirement flow
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_SGM_0002 — Error SGM Test

- **Purpose**: Same as 0001 plus event log validation per scan result (0x6008/0x6009/0x0026/0x6002)
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_SGM_0003 — MultiVB SGM Test

- **Purpose**: 3+ VBs flagged simultaneously; `REVOKE_BLK` special case handling
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_SGM_0004 — SystemVB SGM Test

- **Purpose**: PTE/LOG/SWAP VBs as SGM targets; SSU flush required for LOG VBs
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_SGM_0005 — POR SGM Test

- **Purpose**: SGM state persistence across power cycles and reconfig
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## srambler

### Overview — Scrambler Seed Periodicity Testing (1 test)

Scrambler tests verify that the NAND scrambler seed cycles with erase count, ensuring identical data written at EC and EC+8 produces the same physical NAND state, while data written at EC+1 differs.

---

### PSW_F_P3_Srambler_0001 — Scrambler Seed Periodicity Test

- **Purpose**: Verify scrambler seed = EC mod 8; data differs at EC+1, matches at EC+8
- **Key APIs**:
  - VU 40F6: `project_api.issue_40F6_to_erase_in_direct_nand_mode(die, plane, start_blk, end_blk, slc_enable)` — die/plane as bitmasks
  - VU C083: `project_api.issue_C083_to_set_erase_read_count_parameter(Parameter0=GET_EC_TABLE, VB_Num=CHANGE_EC_ONLY_IN_RAM, ...)` — set EC in RAM only
- **Pattern**: write data → verify matches at EC+8 → verify differs at EC+1 (different scrambler seed)
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## sticky_read

### Overview — Sticky Read Testing (2 tests)

Sticky Read tests verify that when read error count exceeds the `REH_ENTER_COUNT_STICKY_ON` threshold, the FW enters sticky read mode and applies more aggressive read retry parameters. Tests cover multiple LUN types and power-down persistence.

---

### Shared Infrastructure

**VU Commands:**

- VU 4014: `get_read_last_table()`
- VU D014: `set_last_table_content()`, `set_read_recovery_module()`
- VU 4066: `force_sticky_read()` / `get_sticky_status()` / `enable_disable_sticky_read()`
- VU 40BA: `get_error_recovery_statistics()`, `get_error_recovery_record_by_index(1 or 37 for PSA)`

**Status enums:**

- `STICKY_READ_OUTPUT_STATUS.STICKY_READ_ENTERED` / `NOT_ENTERED`
- `STICKY_READ_STATUS.SUCCESS` / `FAILED`

**Threshold:** `mConfig.REH_ENTER_COUNT_STICKY_ON`

---

### PSW_F_P3_StickyRead_0001 — Multi-LUN Sticky Read Test

- **Purpose**: Tests 3 LUNs (Normal/EM1/PSA); 10 iterations per block type; sticky read entered when error count exceeds `REH_ENTER_COUNT_STICKY_ON`
- **Flow**: Write → inject HECC → read → verify sticky read entered → check ERS counters
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_StickyRead_0002 — Power-Down Persistence Test

- **Purpose**: Verify sticky read state persists across power-down cycles
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## tempco

### Overview — Temperature Coefficient (NAND Trim) Testing (2 tests)

TempCo tests verify that the FW switches NAND trim values at the correct erase count thresholds defined in the EC table. Trim switching ensures optimal NAND read margins across the device lifetime.

---

### Shared Infrastructure

- `project_api.mconfig_vu.get_pConfig_data()` → XTEMP_EC_value at bytes 28–35, TEMPCO_TRIM_ADDR at 36–99, TEMPCO_TRIM at `100+ec*32`
- `project_api.issue_4084_to_get_NAND_trim(target_addr)` → `.TrimValue[i].value`
- EC table write via VendorCmdWrite with `GET_FW_GEOMETRY, cmd_set_type=0x0F, b6_cmd2=4`

---

### PSW_F_P3_TempCo_0001 — Trim Switch Test

- **Purpose**: Verify trim switches at XTEMP_EC thresholds (EC1–EC4); validated across POR/SPOR and SSU conditions
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_TempCo_0002 — Boundary EC Test

- **Purpose**: Set EC=threshold-1, random writes until EC crosses, verify trim switches
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## Thermal_Protection

### Overview — Thermal Protection Testing (7 tests)

Thermal Protection tests verify that the FW correctly detects out-of-range temperatures (hot and cold), enters stuck/throttled state, and can be released via VU D0F3. Tests also cover ATS timer behavior, ASIC-NAND temperature delta, and auto-standby interaction.

---

### Shared Infrastructure

**Temperature encoding:** UFS reported temp = real + 80 (0°C=80, 100°C=180)

**VU Commands:**

- VU D0F1: `project_api.issue_D0F1_write_thermal_stuck_threshold(WriteThermalStuckThreshold)` — set thresholds
- VU 40FA: `project_api.issue_40FA_read_thermal_stuck_threshold()` — read thresholds
- VU D0F3: `project_api.issue_D0F3_disable_thermal_stuck(ThermalProtectionType, HardThermalProtectionType)` — disable TP modes
- VU D08A: `project_api.issue_D08A_set_vu_temperature(SetNandTemperature)` — inject fake temperature
- `manual_rst_n()` — shared reset function

**Structs:** `WriteThermalStuckThreshold` with low/high threshold fields

**Enums:**

- `ThermalProtectionType`: `HOT_ONLY` / `COLD_ONLY` / `HOT_COLD`
- `HardThermalProtectionType`

---

### PSW_F_P3_ThermalProtection_0001 — HOT_ONLY Stuck Test

- **Purpose**: Set hot threshold, inject temperature above threshold, verify device enters stuck state; verify D0F3 disable releases stuck
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `G_TIMEOUT_ALL`

---

### PSW_F_P3_ThermalProtection_0002 — COLD_ONLY Stuck Test

- **Purpose**: Same as 0001 but cold temperature (below threshold)
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `G_TIMEOUT_ALL`

---

### PSW_F_P3_ThermalProtection_0003 — HOT_COLD Stuck Test

- **Purpose**: Both hot and cold thresholds tested together
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `G_TIMEOUT_ALL`

---

### PSW_F_P3_ThermalProtection_0004–0006 — Shipping Mode Switches

- **Purpose**: Verify thermal protection behavior when switching between shipping mode configurations
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_ThermalProtection_0010 — Temperature Measurement Check

- **Purpose**: Verify ATS timer, delta_asic_nand temperature delta, FW symbol reads, auto-standby interaction
- **Key FW symbols**: `read_fw_value('gUfsApiStruct.ftl->temp.*')`
- **VU**:
  - VU D088: `project_api.issue_D088_enable_disable_auto_standby()` — enable/disable auto-standby
  - VU D08A: `project_api.issue_D08A_set_vu_temperature()` — inject fake temperature
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## vth_sweep

### Overview — Vth (Threshold Voltage) Sweep Testing (2 tests)

Vth Sweep tests verify that FW correctly measures and reports threshold voltage distributions across NAND pages. These measurements validate read margin health and are used to track retention-related degradation.

---

### Shared Infrastructure

**VU Commands:**

- VU 401D: `project_api.issue_401D_to_get_vt_distribution(die, plane, block, page, isSLC, ...)` — Vth distribution
- VU 4080: `project_api.issue_4080_read_log_from_nand(para_0, para_1, para_2, para_4)` — event log

**Event log:** 0x6004 with `VT_DIFF_COUNT` at offset `2568+28` (`0xDA×4` bytes)

---

### PSW_F_P3_VthSweep_0001 — SLC VT Distribution Test

- **Purpose**: `TestEM1Lun=1`; neighbor WL collection; VT diff comparison
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_VthSweep_0002 — TLC VT Distribution Test

- **Purpose**: `TestNormalLun=0`; PAGE_TYPE iteration (LP/MLC LP/TLC LP); `convert_page_to_page_order()`
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## wear_leveling

### Overview — Wear Leveling Testing (4 tests + mutual_fun.py)

Wear Leveling tests verify that the FW distributes writes evenly across all VBs by tracking EC and version values, triggering static/dynamic WL when EC gaps or version gaps exceed thresholds, and moving blocks via refresh or GC.

---

### mutual_fun.py — Shared WL Functions

- `get_VB_group()` — parses 4-byte VB entry:
  - bits 0–5: `group`
  - bits 6–7: `access_mode`
  - bit 8: `dirty`
  - bits 9–10: `partition`
  - bit 15: `src_uecc`
  - bits 16–17: `vb_trim`
  - bits 18–19: `risky_type`
- `check_WL_value_change()` — verifies WL trigger counters changed
- `get_sorted_VB_list()` — sorted VB list helper

**Key project_api calls:**

- `project_api.issue_4098_to_get_wear_leveling_information()` → `WearLevelingInformation` with:
  - `EC_data`, `VER_data`
  - `global/boundary versions`
  - `EC gaps`
  - Counters: `totalSWLTriggerCount`, `totalSWLGCTriggerCount`, etc.
- `project_api.issue_C072_to_set_static_wear_leveling_EC_gap_threshold(...)` — 11 parameters (C072)
- `api.set_ftl_version(mlc_partition_current_vb_version)` — set version per VB

---

### PSW_F_P3_WearLeveling_0001 — WL Info Test

- **Purpose**: VBListNum/OpenVBType per VB; EC/version set and readback; health report cross-check
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_WearLeveling_0002 — Static WL Refresh Test

- **Purpose**: ICS/Static/Dynamic pool triggers; cold/prior-round; TH1/TH2 thresholds; booking queue verification
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_WearLeveling_0003 — Static WL GC Test

- **Purpose**: GC trigger for `USED_BLK_POOL_EM1` / `TLC` / `TLC_WB`; `totalSWLGCTriggerCount` increments
- **Also**: `project_api.custom_vu.issue_406D_get_VB_list_info()` — VB list by pool type
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_WearLeveling_0004 — Dynamic WL Test

- **Purpose**: VB selection by lowest EC within search range; `project_api.custom_vu.issue_406D_get_VB_list_info()` for verification
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## xtemp

### Overview — Cross-NAND Temperature Testing (3 tests)

XTemp tests verify that the FW correctly classifies VBs as Safe/Hot/Cold based on NAND temperature relative to T1/T2 thresholds, applies appropriate read margins, and auto-triggers refresh when VBs exit the temperature buffer zone.

---

### Shared Infrastructure

- `project_api.set_mConfig_data(mConfig)` — `XTEMP_ENABLE_PEC` must be 10 to enable XTEMP
- `project_api.issue_D08A_set_vu_temperature(SetNandTemperature)` — inject fake NAND temp
- `project_api.issue_4021_get_nand_temperature()` — read actual NAND temp; subtract `TEMP_GAP=37°C`
- VB risky_type bits 18–19 (from `api.get_vb_info()` 4-byte VB entry):
  - `0` = Safe
  - `1` = Hot
  - `2` = Cold
- T1/T2 thresholds from mConfig

---

### PSW_F_P3_XTemp_0001 — CrossNandTemp Test

- **Purpose**: Safe/Hot/Cold group marking based on temperature; `TEMP_BUFFER` zone; auto-refresh when exiting buffer zone
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_XTemp_0002 — OpenTLCVB Test

- **Purpose**: EC threshold crossing causes risky type activation; VPCT tracking via `issue_40C0_to_get_VPCT_description(0xFFFFFFFF, 0x0)`
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### PSW_F_P3_XTemp_0003 — GCTLCVB Test

- **Purpose**: GC target VB (`open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC`) risky tracking during WB flush; sequential Hot→Cold→Hot transitions verified
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`
