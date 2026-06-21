---
type: source
title: "Script Pattern Code Library — UFS Pattern Wiki Complete Reference"
tags: [script, pattern, implementation, custom-vu, test-framework]
ingested: 2026-06-21
updated: 2026-06-21
entities: [lun, write-booster, rpmb, psa-state, inhibition-timeout, thermal-protection-mode,
           rain, hid, refresh, read-disturb, wear-leveling, media-scan, sgm]
concepts: [psa, power-management, background-operations, gc, ftl, wear-leveling]
---

# Script Pattern Code Library — Complete Reference

**Source**: `UFS_Pattern_Wiki_Complete.md` — generated 2026-06-21, covers all 31 pattern folders.

All patterns extend the `UFSTC` base class from `pattern_template` and follow a `pre_process → step1 → … → stepN → post_process` structure.

---

## All 31 Pattern Folders — One-Sentence Descriptions

| # | Folder | Description |
|---|--------|-------------|
| 01 | `apl_system_rebuild` | Tests APL (Application Layer) rebuild after UECC/HECC injection and SPOR across 21 scenarios covering BBT, Page Table, Index, List, Log, ISP, PTE, and GC rebuild |
| 02 | `block_budget` | Verifies FW correctly allocates VBs across TLC/SLC pools for 27 TLC/SLC ratio configurations using a 9-field `VBCount` structure |
| 03 | `config_attribute_flag` | Validates all UFS flags, device attributes, per-LUN attributes, and descriptors against expected values loaded from an Excel file |
| 04 | `custom_vu` | 95 test files covering all Vendor-Unique (VU) commands: device info, FW state, NAND operations, L2P, RPMB, manufacturing, BKOPS, MDWLSV, SECDED, and diagnostics |
| 05 | `data_training` | Verifies FW switches NAND data training parameters at the correct LT/CT/HT temperature thresholds by comparing NAND feature register values |
| 06 | `erase_fail` | Injects erase fail events on 12 target blocks and verifies FW replaces bad blocks, updates BBT, and handles pool exhaustion assert codes (0x203/0x204/0x202/0xB7/0x510) |
| 07 | `health_report` | Validates basic and enhanced (40FE) health report retrieval, including 30+ fields across power states and temperature boundary conditions |
| 08 | `hir` | Verifies Host-Initiated Refresh (HIR) behavior for XTEMP UECC booking, Hot/Cold temperature refresh, selective refresh, VB priority ordering, operation config, and power management across 21 flows |
| 09 | `Inhibition_time` | Verifies BG tasks (GC, media scan, BBM, read-back, HIR, purge, HID, PSA refresh, other refresh) are blocked during the inhibition window and resume after `leave_inhibition_mode()` |
| 10 | `luns_reconfiguration` | Validates LUN reconfiguration permission rules across all four PSA states, config descriptor lock states, mid-operation reconfiguration safety (RPMB/HID/WB/HIR), and ~100 AU ratio combinations |
| 11 | `mconfig` | Tests mConfig/pConfig update via FFU (cases 1–3), VU command C056 (cases 4–6), and X-memory (cases 7–10), plus 11–12 error rejection scenarios |
| 12 | `mdwlsv` | Validates MDWLSV (Minimum Die Write Level Shift Voltage) offset tracking per die and stream type, persistence across SSU/ATS/H8/HW_RESET, and boundary/wrap conditions |
| 13 | `media_scan` | Verifies FG and BG media scan triggering (VHC/NDEP modes), PSA interaction, refresh booking queue deduplication, and bin low/high threshold logic |
| 14 | `outgoing_slx` | Verifies VB trim states (SLx_TRIM vs POR_TRIM) are correctly assigned at each lifecycle stage from initial state through RPMB write, LUN config, purge, EM1 write, and PSA flow |
| 15 | `PPM` | Validates NAND feature register P1/P2/P3/P4 values at address 0xEB per CE (expected non-zero for CE==4, all-zero for CE!=4) |
| 16 | `program_fail` | Injects program fail and erase fail events across 75 tests covering all VB types (EM1/SLC, TLC page, MLC, PTE, LOG, LIST, L1, EM1 LUN, WB LUN) and verifies BBT updates |
| 17 | `PSA` | Covers complete PSA lifecycle (38 steps), SPOR interrupt/recovery, event log validation, PSA-specific VU commands, Boot EM1 programming, and HIR inhibition interaction |
| 18 | `rain` | RAIN parity-based protection testing across 19 tests: parity calculation, UECC injection/recovery, open/closed VB protection, enable/disable via D08B, SWAP parity failures, and multi-UECC scenarios |
| 19 | `read_disturb` | Verifies RC tracking, RD scan triggers when RC exceeds RC_TH, RC_TH updates post-scan, EC-based threshold initialization, RC persistence across POR/SSU, and BFEA quick-scan |
| 20 | `read_scan` | Verifies FW tracks UECC errors per WL, triggers BG scan at SAFE_AREA boundary, handles selective disable, SSU-triggered release, POR persistence, and GC interaction |
| 21 | `refresh` | Validates booking queue (VU C087/C088), HP/MP/LP priority handling, deduplication, error cases, event log generation (0x3006/0x3051), and end-to-end refresh execution |
| 22 | `reh` | Read Error Handling for SLC and TLC blocks: ERS statistics, sticky read entry conditions, read recovery module interaction |
| 23 | `sample_code` | 39 canonical API reference samples covering config descriptors, manual mode, timeouts, task abort, FBO, FFU, RPMB, speed change, and write record patterns |
| 24 | `sgm` | Scan Guard Mechanism (SGM) tests verifying dynamic/static RC threshold retirement, event log validation (0x6008/0x6009/0x0026/0x6002), multi-VB flagging, system VBs, and POR persistence |
| 25 | `srambler` | Verifies scrambler seed periodicity: data matches at EC and EC+8, differs at EC+1, validating seed = EC mod 8 |
| 26 | `sticky_read` | Verifies sticky read mode entry when read error count exceeds `REH_ENTER_COUNT_STICKY_ON`, across multiple LUN types and power-down persistence |
| 27 | `tempco` | Verifies FW switches NAND trim values at EC thresholds from EC table, validated across POR/SPOR/SSU conditions and boundary EC crossing |
| 28 | `Thermal_Protection` | Tests HOT_ONLY/COLD_ONLY/HOT_COLD thermal stuck entry via D0F3, shipping mode switches, ATS timer, ASIC-NAND temperature delta, and auto-standby interaction |
| 29 | `vth_sweep` | Validates Vth (threshold voltage) distribution measurement for SLC and TLC via VU 401D, with event log 0x6004 VT_DIFF_COUNT cross-validation |
| 30 | `wear_leveling` | Verifies WL distributes writes evenly using EC/version tracking, static/dynamic WL triggers, pool-based selection, and health report cross-check |
| 31 | `xtemp` | Verifies FW classifies VBs as Safe/Hot/Cold based on T1/T2 NAND temperature thresholds, applies read margins, and auto-triggers refresh when exiting the temperature buffer zone |

---

## Cross-Pattern Shared API Summary

These APIs appear across multiple pattern folders and are considered core utilities:

### NAND Operations

| API | VU Code | Description |
|-----|---------|-------------|
| `project_api.issue_4051_to_get_physical_address(lun, lba)` | 4051 | LBA → Physical Cell Address (CE/plane/block/page) |
| `project_api.issue_4052_to_get_logical_address(pca)` | 4052 | Physical → LBA (reverse lookup) |
| `project_api.issue_4060_to_read_raw_data(Die, Plane, Block, Page, SLC, ECC, Scrambler, REH)` | 4060 | Raw NAND page read |
| `project_api.issue_C060_to_write_raw_data(Ce, Block, Plane, Page, SLC, ECC, payload)` | C060 | Raw NAND page write (inject UECC: 0xAA data) |
| `project_api.issue_D060_to_erase_specific_block(Ce, Plane, Block, SlcEnable, psaEnable)` | D060 | Erase specific NAND block |
| `project_api.issue_40C0_to_get_VPCT_description(vb_num, option)` | 40C0 | VB Pointer/Count Table — VBINFO bits per VB |
| `project_api.issue_40C1_to_get_open_vb_information()` | 40C1 | Open VB info (TLC_L2, SLC_L2, WB, PTE, L1, LOG, SWAP) |

### EC / Read Count

| API | VU Code | Description |
|-----|---------|-------------|
| `project_api.get_all_VB_erase_count()` | — | Read EC table |
| `project_api.set_all_VB_erase_count(data, set_in_ram=True/False)` | C083 | Set EC table (RAM-only or permanent) |
| `project_api.get_all_VB_read_count()` | — | Read RC table |
| `project_api.set_specific_VB_read_count_threshold(VB_Num, RC_TH)` | — | Set per-VB read count threshold |

### Refresh / Booking Queue

| API | VU Code | Description |
|-----|---------|-------------|
| `project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type, VB_list, booking_user)` | C087 | Book VBs into refresh queue at HP/MP/LP priority |
| `project_api.issue_C088_to_start_or_stop_refresh(bParameter0)` | C088 | Start/stop refresh; mode 4=disable enqueue, mode 5=enable enqueue |
| `project_api.issue_40C5_to_get_booking_queue()` | 40C5 | Read current booking queue |
| `api.set_flag(FlagIDN.REFRESH_EN)` | — | fRefreshEnable (IDN=07h) — trigger refresh |
| `api.read_attribute(AttributeIDN.REFRESH_STATUS)` | — | bRefreshStatus (IDN=2Ch) — poll refresh progress |

### WriteBooster

| API | Description |
|-----|-------------|
| `api.set_flag(FlagIDN.WRITEBOOSTER_EN)` | fWriteBoosterEn (IDN=0Eh) |
| `api.set_flag(FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)` | fWriteBoosterBufferFlushEn (IDN=0Fh) |
| `api.read_attribute(AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)` | WB available size; value 0xA = fully available |
| `api.read_attribute(AttributeIDN.BG_OP_STATUS)` | bBackgroundOpStatus (IDN=05h) |

### Health Report

| API | VU Code | Description |
|-----|---------|-------------|
| `project_api.get_micron_health_report()` | — | Basic health report |
| `project_api.issue_40FE_to_read_enhanced_health_report()` | 40FE | Enhanced health report (30+ fields) |

### Power / Reset

| API | Description |
|-----|-------------|
| `api.init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET, powerdown=True/False)` | HW reset with optional power-down (POR) |
| `api.first_init_to_max_hs_gear(link_startup_mode, ref_clk)` | Initialize UFS link at maximum HS gear |

---

## `power_cycle()` — Standard Implementation

Found in `Inhibition_time/mutual_fun.py`:

```python
def power_cycle():
    """Performs a random HW_RESET with powerdown=False or powerdown=True,
    followed by access_vendor_mode().
    Used across all inhibition tests to reset device state."""
    powerdown = random.choice([False, True])
    api.init_tester_to_unit_ready(
        resetmode=Dcmd5ResetType.HW_RESET,
        powerdown=powerdown
    )
    api.access_vendor_mode()
```

Key behaviors:
- `powerdown=False` — HW_RESET without power loss (preserves SRAM state where applicable)
- `powerdown=True` — Full power-cycle (POR); clears all volatile state including MDWLSV offsets, device_state (RAM), temp VU temperature overrides
- Always followed by `access_vendor_mode()` to re-establish VU protocol access

---

## Test Exception Types

### SIGHTING_* — Device behavior deviations (data or response)

| Exception | Trigger Condition |
|-----------|-------------------|
| `SIGHTING_FAIL_DATA_COMPARE_FAIL` | Read-back data does not match written data (most common across all patterns) |
| `SIGHTING_RESPONSE_UNEXPECTED` | UFS response code (sense key/ASC/ASCQ) does not match expected value |
| `SIGHTING_PBA_UNEXPECTED` | Physical Block Address returned by VU does not match expected value |
| `SIGHTING_FFU_STATUS_UNEXPECTED` | FFU status register does not match expected update result |
| `SIGHTING_FAIL_CLEAN_WRITE_ONCE_ATTRIBUTE_FLAG` | Write-once cleanup did not restore attribute/flag to expected default |

### PATTERN_ASSERT_* — Test framework assertion failures

| Exception | Trigger Condition |
|-----------|-------------------|
| `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT` | BKOPS or WB flush did not complete within timeout window |
| `PATTERN_ASSERT_UNEXPECTED_CONDITION` | Unexpected internal state detected (e.g., RAIN info field mismatch) |
| `PATTERN_ASSERT_ATTR_NOT_FOUND` | Expected attribute not found in response (mConfig error cases) |

### SPEC_ASSERT_* — UFS Spec protocol compliance failures

| Exception | Trigger Condition |
|-----------|-------------------|
| `SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET` | RPMB key operation attempted before authentication key is programmed |
| `SPEC_ASSERT_RPMB_KEY_NOT_CLEARED` | RPMB key not cleared when expected |
| `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH` | UFS response value violates spec-defined expected value |
| `SPEC_ASSERT_UFS_RSP_OP_SHALL_WRITE_ATTRIBUTE` | Attribute write returned failure when spec requires success |

### G_TIMEOUT_ALL — Device unresponsive / FW stuck

| Exception | Trigger Condition |
|-----------|-------------------|
| `G_TIMEOUT_ALL` | Device did not respond within global timeout (injected fault caused FW hang; FormatUnit with BG trim disabled) |

### DLL_* — Low-level communication errors

| Exception | Trigger Condition |
|-----------|-------------------|
| `DLL_CRC32_COMPARE_FAIL` | CRC32 data compare failure at DLL level |
| `DLL_RESPONSE_ERROR` | Response error at DLL/link layer (used in RAIN multi-UECC read tests) |

---

## Where This Fits

Touches: [[lun]], [[write-booster]], [[rpmb]], [[psa-state]], [[inhibition-timeout]], [[thermal-protection-mode]], [[rain]], [[hid]], [[refresh]], [[read-disturb]], [[wear-leveling]], [[media-scan]], [[sgm]], [[psa]], [[power-management]], [[background-operations]], [[gc]], [[ftl]], [[conflicts]]
