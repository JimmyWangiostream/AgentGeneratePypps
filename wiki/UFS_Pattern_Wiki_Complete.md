# UFS Pattern Wiki — Complete Reference

Generated: 2026-06-21 | Covers all 31 pattern folders

---

## Table of Contents

1. [apl_system_rebuild](#apl_system_rebuild)
2. [block_budget](#block_budget)
3. [config_attribute_flag](#config_attribute_flag)
4. [custom_vu](#custom_vu)
5. [data_training](#data_training)
6. [erase_fail](#erase_fail)
7. [health_report](#health_report)
8. [hir](#hir)
9. [Inhibition_time](#inhibition_time)
10. [luns_reconfiguration](#luns_reconfiguration)
11. [mconfig](#mconfig)
12. [mdwlsv](#mdwlsv)
13. [media_scan](#media_scan)
14. [outgoing_slx](#outgoing_slx)
15. [PPM](#ppm)
16. [program_fail](#program_fail)
17. [PSA](#psa)
18. [rain](#rain)
19. [read_disturb](#read_disturb)
20. [read_scan](#read_scan)
21. [refresh](#refresh)
22. [reh](#reh)
23. [sample_code](#sample_code)
24. [sgm](#sgm)
25. [srambler](#srambler)
26. [sticky_read](#sticky_read)
27. [tempco](#tempco)
28. [Thermal_Protection](#thermal_protection)
29. [vth_sweep](#vth_sweep)
30. [wear_leveling](#wear_leveling)
31. [xtemp](#xtemp)

---

# UFS Pattern Test Implementation Wiki — Part 1

Pattern folders: apl_system_rebuild, block_budget, config_attribute_flag, custom_vu (0001–0030), data_training, erase_fail, health_report, hir

---

## apl_system_rebuild

### Overview

Tests the APL (Application Layer) rebuild feature after UECC/HECC injection + SPOR. 21 test files + mutual_fun.py.

### mutual_fun.py — Shared Functions

- `TestMode` enum: `TEST_TLC` / `SLC` / `WB` / `PTE` / `L1` / `LOG` / `TMP_RAIN`
- `WL_Group` enum with TLC page boundaries:
  - GroupA (0–1619)
  - GroupB MLC (1620–1651)
  - GroupC TLC (1652–3307)
  - GroupD SLC (3308–3311)
- `apl_pattern_precondition()` — sets up LUNs and geometry
- `inject_UECC(pca)` — raw NAND write with 0xAA data (SLC: 16KB, TLC: 60KB) to corrupt page
- `injectUECC_from_FEP(vb, fep, startoffset, num)` — inject UECC starting from first empty page
- `flipbit_on_SLC_lba_smart(lba)` — flips 100 bits for SLC HECC injection
- `flipbit_on_TLC_smart(micron_pca)` — flips 150 bits for TLC HECC injection
- `collect_lwp_checks()` / `compare_lwp_checks()` — LWP (Last Written Page) validation
- `write_data_until_dedicate_lwp()` — writes until a specific LWP position
- `build_write_payload(lp, up, xp)` — builds 60KB TLC page payload
- `SPOR_init_mp()` — SPOR followed by manufacturing protocol init
- Key VU commands used:
  - `0x4051` — get physical address
  - `0x4060` — read raw
  - `0xC060` — write raw
  - `0xD060` — erase specific block
  - `0x40C1` — open VB info
  - `0x409D` — power loss analysis / LWP
  - `0x40FE` — enhanced health report

### Tests 0001–0007 — BBT/PT/Index/List/Log/ISP/PTE Rebuild

- **Purpose**: After UECC injection in system table blocks (BBT, Page Table, Index, List, Log, ISP, PTE) + SPOR, verify FW rebuilds them correctly
- **VU Commands**:
  - `issue_40C1_to_get_open_vb_information()`
  - `issue_4051_to_get_physical_address(luID, lba)`
  - `issue_4060_to_read_raw_data(Die, Plane, Block, Page, SLC_Enable, Ecc_Enable, Scrambler_Enable, REH_Enable)`
  - `issue_C060_to_write_raw_data(Ce, Block, Plane, Page, SLC_Enable, Ecc_Enable, datapayload)`
  - `issue_D060_to_erase_specific_block(Ce, Plane, Block, SlcEnable, psaEnable)`
- **Pattern**: `inject_UECC` → `SPOR_init_mp()` → verify rebuild via LWP checks and data compare
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `SIGHTING_RESPONSE_UNEXPECTED`

### Tests 0008–0021 — EM1/TLC UECC/HECC Rebuild

- **0008, 0020**: GC UECC scenarios — UECC in source VB during GC
- **0018–0019**: PSA mode rebuild — tests rebuild under PSA (Pre-Soldering Authentication) state
- **HECC injection**:
  - `flipbit_on_SLC_lba_smart(lba)` — flips 100 bits
  - `flipbit_on_TLC_smart(micron_pca)` — flips 150 bits
- **Pattern**: write data → inject UECC/HECC → SPOR → verify data integrity via `api.read_compare()`
- **VU 0x409D**: `issue_409D_to_do_power_loss_analysing()` — post-SPOR LWP analysis

---

## block_budget

### PSW_F_P3_Block_Budget_0001 — VB Pool Allocation Test

- **Purpose**: Verify FW correctly allocates VBs across TLC/SLC pools for 27 ratio configurations
- **Key Structure**: `VBCount` (36-byte, 9 × 4-byte fields at offsets 0–35):
  - `system_table`
  - `slc_user_data`
  - `slc_op`
  - `rev_for_gc_and_open_slc`
  - `tlc_user_data`
  - `tlc_op`
  - `rev_for_gc_and_open_tlc`
  - `hidden_blk`
  - `max_bb_replacement_cnt`
- **Key APIs**:
  - `api.get_block_read_count_table()` → bytes at offset 2560 parsed as `VBCount`
  - `api.push_write_config()`
  - `api.random_write()`
  - `api.random_erase()`
  - `project_api.issue_4004_get_boundaryblocks_for_hiddentable_static_dynamicpool()`
- **Pattern**: config LUN ratios → `random_write` → `random_erase` → PURGE cycle → verify `VBCount` fields
- **27 test cases**: TLC/SLC ratio combinations from 0% EM1 to 100% EM1
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## config_attribute_flag

### PSW_F_P3_Config_Attribute_Flag_0001 — Full Config/Attribute/Flag/Descriptor Validation

- **Purpose**: Validate all UFS flags, device attributes, per-LUN attributes, and all descriptors against expected values from xlsx file
- **Key APIs**:
  - `pandas.read_excel()` — loads expected values from xlsx
  - `ExecuteCMD.ReadFlag()` — read flag by `idn`, `index`, `selector`
  - `ExecuteCMD.ReadAttribute()` — read attribute by `idn`, `index`, `selector`
  - `ExecuteCMD.ReadDescriptor()` — read descriptor by `idn`, `index`, `selector`
  - `api.parse_flag_rsp()`
  - `api.parse_read_attr_rsp()`
- **Skip rules**:
  - Geometry descriptor skips `qTotalRawDeviceCapacity`, `dSegmentSize`
  - Other descriptors have similar per-field skip lists
- **Pattern**: load xlsx → iterate all flags/attrs/descriptors → read from device → compare vs expected
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## custom_vu

### Overview

Tests for all Vendor-Unique (VU) commands. 95 test files covering device info, FW state, NAND operations, manufacturing, and diagnostics.

### CustomVU_0001 — VPCT (Virtual Physical Cell Table) Test

- **VU**: `project_api.issue_40C0_to_get_VPCT_description(vb_num, option)`
- **Structures**: `project_api.VPCT_values()`, `VBINFO_values()`
- **Key**: XTEMP risky type at bits 18–19 of VB info (0=Safe, 1=Hot, 2=Cold); GC destination/source bits; comprehensive VB classification
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0002 — FW Version

- **VU**: `project_api.issue_4001_to_get_fw_version()` → `GetFwVersion`
- **Fields**: firmware version string, build date, variant

### CustomVU_0003 — FW Configuration

- **VU**: `project_api.issue_408A_to_get_fw_version()` → `GetFwConfiguration`
- **Also**: `api.ufs_api.read_fw_value(symbol_string)` — read FW variable by symbol name

### CustomVU_0004 — EC/ICS Table

- **VU**: Multi-index VU 4097 table queries
- **APIs**:
  - `api.get_remap_table()`
  - `api.get_ics_table()`
  - `api.get_vb_info()`
  - `api.direct_read()`
- **Purpose**: Validate Erase Count and Invalid Cell Status tables per VB

### CustomVU_0005 — BBT Info

- **VU**: `project_api.issue_405E_to_get_bad_block_information()`
- **Payload decode**: 4 bytes count, then 8-byte entries per bad block:
  - `BB_Block = bytes[0:3]`
  - `BB_CE = (byte3 >> 3) // 6`
  - `BB_Plane = (byte3 >> 3) % 6`

### CustomVU_0006 — Open VB Information

- **VU**: `project_api.issue_40C1_to_get_open_vb_information()` → `OpenVBInformation`
- **Trigger**: GC trigger via WB flush to change open VB state
- **Fields**: current open VB number, first empty page, CE/plane info per VB type:
  - `TLC_L2`, `SLC_L2`, `WB`, `PTE`, `L1`, `LOG`, `SWAP`

### CustomVU_0007 — Disable/Enable Background Operations

- **VU**: `project_api.issue_D0FD_en_disable_BKOPS(bValue)` — `0`=disable, `3`=enable
- **Test**: trigger WL GC with EC manipulation; `G_TIMEOUT_ALL` when BG trim disabled and FormatUnit runs
- **Exceptions**: `G_TIMEOUT_ALL`

### CustomVU_0008 — uC Temperature

- **VU**:
  - `project_api.push_40FD_get_uC_temp()`
  - `push_40FE_to_read_enhanced_health_report()`
- **Range**: 20–75°C valid range
- **Attribute**: `bDeviceCaseRoughTemperature` cross-validation

### CustomVU_0009 — RPMB Write Counter / Clear Key

- **VU**:
  - `project_api.issue_D079_clear_rpmb_key()` (D079)
  - `project_api.issue_D078_set_rpmb_write_counter()` (D078)
- **Regions**: 4 RPMB regions tested

### CustomVU_0010 — Write-Once Cleanup

- **VU**: `project_api.issue_D083_clean_up_write_once()`
- **Flags**: `PERMANENT_WP_EN`, `PERMANENTLY_DIS_FW_UPDATE`
- **Attrs**: `OUT_OF_ORDER_DATA_EN`, `CONFIG_DESCR_LOCK`

### CustomVU_0011 — MDWLSV Enable/Disable

- **VU**:
  - `project_api.issue_C08C_enable_disable_mdwlsv()` (C08C) — enable/disable
  - `project_api.issue_4029_to_get_MDWLSV_offset_information()` (4029)
- **Also**: feature address `0x7F` P3 from `issue_4022_to_get_NAND_feature()`

### CustomVU_0012 — L2P Normal Test

- **VU**:
  - `project_api.issue_4051_to_get_physical_address(lun, lba)`
  - `project_api.issue_4052_to_get_logical_address(pca)`
- **Also**:
  - `lba_to_pba()` (Phison)
  - `load_PMD_data()`, `load_PTE_data()` — L2P table direct read
- **Purpose**: Cross-validate LBA→PCA via both VU and direct table read

### CustomVU_0013 — TLC Defrag Info

- **VU**: VU 40C2 with 40+ fields
- **Fields**: GC trigger type, WB SLC cache sizes, IGC (Idle GC) flags, defrag state

### CustomVU_0014 — BKOPS Status

- **VU**: VU 40DB vs standard attribute `05h`
- **States**:
  - `0` = idle
  - `1` = perf_impact
  - `2` = critical
  - `3` = not_avail
- **Triggers**: WB flush and refresh to change BKOPS state

### CustomVU_0015 — Set EC (Erase Count)

- **VU**: `project_api.set_all_VB_erase_count()` (C083)
- **Note**: RAM vs flash persistence modes

### CustomVU_0016 — Device State in RAM

- **VU**:
  - `project_api.set_device_state(only_in_ram=True)` (D0FC)
  - `project_api.get_FW_states_in_RAM()` (40FC)
- **Memory**: Xmemory at `0xF8F80800`, byte 38

### CustomVU_0017 — Device State Permanent

- **VU**:
  - `project_api.set_device_state(only_in_ram=False)` (D0E2)
  - `project_api.issue_40E2_to_get_device_state()` (40E2)
- **Storage**: eFuse at `0xF8F80800 + 0x24`; 8-change limit enforced

### CustomVU_0018 — Unlock LU Attribute Configuration

- **VU**: `project_api.issue_D085_unlock_LU_attribute_configuration()` (D085)
- **Purpose**: Manage `bConfigDescrLock` lifecycle for LUN reconfiguration

### CustomVU_0019 — Device Write Status

- **VU**: VU 4064
- **States**:
  - `1` = burst
  - `2` = sustain
  - `3` = dirty
- **Interactions**: WB/GC threshold effects on write status

### CustomVU_0020 — Set/Get NAND Feature

- **VU**:
  - `project_api.issue_4022_to_get_NAND_feature(ce, feature_address)` (4022)
  - `project_api.issue_4023_to_set_NAND_feature()` (4023)
- **Coverage**: 39 feature addresses; iterates all CEs

### CustomVU_0021 — Next Open VB

- **VU**: `project_api.issue_40DC_to_get_next_open_vb_information()` (40DC)
- **Predicts**: TLC/EM1/L1/WB next open VBs before they actually open

### CustomVU_0022 — Defrag Source VP

- **VU**: `project_api.issue_40DD_to_get_defrag_source_vp_information()` (40DD)
- **Purpose**: Shows GC/defrag source VP info; flush in-progress state

### CustomVU_0023 — Host LBA to FTL LBA

- **VU**: VU 40D4 (host LBA to FTL LBA conversion)
- **Cross-validate**: `lba_to_pba()` LCA comparison

### CustomVU_0024 — Physical Block to Logical VB

- **VU**: VU 40C9
- **Also**: BBR table from BBT direct-read; remap table from SRAM

### CustomVU_0025 — eFuse

- **VU**: VU 40F4
- **Cross-validate**: Xmemory at `0xF8F80800`

### CustomVU_0026 — Used Mapping/Size

- **VU**: VU 40A8
- **Modes**:
  - `1` = free MB
  - `2` = mapping nodes count

### CustomVU_0027 — CLK Frequency

- **VU**: VU 40EE
- **Expected values**:
  - CPU = 667 MHz
  - BUF = 200 MHz
  - LDPC = 266 MHz
  - ONFI PHY = 1600 MHz

### CustomVU_0028 — Task Abort

- **VU**:
  - `project_api.issue_D0B0_enable_task_abort_assert()` (D0B0)
  - `project_api.issue_40F0_get_abort_hit_info()` (40F0)
- **Task Management**: `ABORT_TASK`, `ABORT_TASK_SET`, `CLEAR_TASK_SET`, `LU_RESET`
- **Assert**: `0xF400` abort hit

### CustomVU_0029 — OTP

- **VU**: VU 40BC pages 0/1/2
- **Cross-validate**: BBT direct-read

### CustomVU_0030 — MPHY Register

- **VU**: VU 4083
- **Memory**: Xmemory at `0xF8F86000`; bytes `0x750`–`0x754` masked

---

## data_training

### PSW_F_P3_Data_Training_0001 — NAND Data Training Temperature Verification

- **Purpose**: Verify FW switches NAND data training parameters at correct temperature thresholds (LT/CT/HT)
- **Key APIs**:
  - `api.HwSetting.get_instance()` → fields: `LT_CE0_TX_VREF`, `CT_CE0_TX_VREF`, `HT_CE0_TX_VREF`
  - `project_api.issue_D08A_set_vu_temperature()` — inject fake temperatures
  - `project_api.issue_4022_to_get_NAND_feature(die=0, feature=0x23)` — data training temp at `byte[8]`
- **Verification**: `ct_ce0 << 1 == nand_feature`; LT at −11°C, HT at 100°C
- **Pattern**: set fake temp → read NAND feature → compare vs `HwSetting` value
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

## erase_fail

### Overview — Erase Fail Injection Testing (12 tests)

### Shared Infrastructure

- **VU Commands**:
  - `project_api.issue_40C1_to_get_open_vb_information()` — find target block
  - `project_api.issue_40DC_to_get_next_open_vb_information(0)` — predict next open VB
  - `project_api.issue_405E_to_get_bad_block_information()` — verify BBT after fail
  - `project_api.issue_40D6_to_get_predicted_next_n_replacement_block(ce, plane, next_n, pool_type, is_CIS, pf_on_open_data)` — get replacement block candidate
  - `project_api.issue_C012_to_create_program_erase_fail(info, fail_type=1, block_info_list_count)` — inject erase fail (`fail_type=1`)
- **Hidden area block decode**:
  - `block = (raw_u32 & 0xFFFFFFE0) >> 5`
  - `plane = (raw_u32 & 0x1C) >> 2`
  - `ce = raw_u32 & 0x03`
- **Assert codes**:
  - `0x203` — static pool exhausted
  - `0x204` — over N tries
  - `0x202` — no spare normal
  - `0xB7` — no spare hidden
  - `0x510` — over 1 time hidden
- `program_fail_api.calculate_bbt(payload)` — BBT parsing
- **Exceptions**: `G_TIMEOUT_ALL` for FW stuck scenarios

---

## health_report

### PSW_F_P3_HealthReport_0001 — Basic Health Report

- **Purpose**: Minimal validation of health report retrieval
- **VU**: `project_api.get_micron_health_report()`

### PSW_F_P3_HealthReport_0002 — Enhanced Health Report

- **Purpose**: Comprehensive validation of 30+ fields in enhanced health report
- **VU**:
  - `project_api.issue_40FE_to_read_enhanced_health_report()` (40FE)
  - VU 40B8 VDET information
- **Power management**: SSU sleep (`0x02`), powerdown (`0x03`), deepsleep (`0x04`) tested
- **Temperature**: boundary testing via `VendorCmdWrite`

---

## hir

### Overview — Host-Initiated Refresh (6 tests + mutual_fun.py)

### mutual_fun.py — Shared HIR Functions

- `config_lun()` — sets LUN0=SLC(EM1), LUN1=TLC(NORMAL)
- `Tnand_in_T1_T2_range(temp)` — checks if temperature is in XTEMP threshold range
- `get_xtemp_parameter()` — reads mConfig, enables XTEMP if PEC≠10
- `set_nand_temp(temp)` — `project_api.issue_D08A_set_vu_temperature(SetNandTemperature)` — inject fake NAND temp
- `inject_UECC(pca)` — raw write to create UECC
- `write_data(lun, size)` — sequential write helper
- **Temperature offset**: `TEMP_GAP = 37°C` (device reports temp + 37)

### PSW_F_P3_HIR_0001 — XTemp UECC Refresh

- **Purpose**: `XTEMP_BOOKING | BOOKING_IN_MP` causes UECC refresh booking; verify `RefreshStatus` transitions to `05h` then `00h`
- **APIs**:
  - `api.set_flag(FlagIDN.REFRESH_EN)`
  - `api.read_attribute(AttributeIDN.REFRESH_STATUS)` — poll until `05h` then `00h`
- **Event**: `wExceptionEventStatus` BIT11 verified
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### PSW_F_P3_HIR_0002 — XTemp Hot/Cold Refresh

- **Purpose**: Temperature out-of-range triggers `REFRESH_STATUS=05h` immediately
- **Events**: `wExceptionEventStatus` BIT11; `b9_device_information==1` alert
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### PSW_F_P3_HIR_0003 — XTemp Hot/Cold Selective Refresh

- **Purpose**: `REFRESH_METHOD=2` (selective) — progress increments by `(1 / total_vb_cnt) * 100000` per slice
- **APIs**: `api.write_attribute(idn=AttributeIDN.REFRESH_METHOD, val=2)`
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### PSW_F_P3_HIR_0004 — VB Refresh Order

- **Purpose**: Verify VB refresh priority order:
  1. `CURRENT_VB`
  2. `OPENVB_TLC_SLC`
  3. `TABLE_AND_SYSTEM`
  4. `CLOSED_TLC_VB`
  5. `CLOSED_SLC_STATIC`
  6. `CLOSED_SLC_DYNAMIC`
- **APIs**: `api.get_vb_info()` — VBType classification for order verification
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### PSW_F_P3_HIR_0005 — Operation Config

- **Purpose**: `REFRESH_METHOD=0` → `SetFlag` returns `GENERAL_FAILURE` (`0xFF`); attributes persist across ATS/H8/SSU/POR/SPOR; reconfig resets progress to 0
- **Exceptions**: `SIGHTING_RESPONSE_UNEXPECTED`, `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### PSW_F_P3_HIR_0006 — Power Management

- **Purpose**: Verify HIR behavior across 21 power management flows (ATS, H8, SSU, POR, SPOR combinations)
- **Exceptions**: `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

# UFS Pattern Wiki — custom_vu (Part 1: CustomVU_0001–0030)

## custom_vu

This section documents UFS custom Vendor Unit (VU) pattern test files `PSW_F_P3_CustomVU_0001` through `PSW_F_P3_CustomVU_0030`. Each test exercises a specific UFS FW feature using a ReadBuffer/WriteBuffer VU protocol with opcode/func fields. The test framework uses a `pre_process → step1 → … → stepN → post_process` structure inherited from `UFSTC`.

No `mutual_fun.py` helper file exists in this directory; shared utilities are imported from `api`, `project_api`, and `Script.api.ufs_api`.

---

### CustomVU_0001 — VPCT and VBINFO Bits Test

**File:** `PSW_F_P3_CustomVU_0001_VPCT_Test.py`

- **Feature Name:** VB Pointer/Count Table (VPCT) and VBINFO bit verification — covers PSA blocks, TLC/SLC/WB open VBs, GC queue VBs, RAIN swap blocks, RPMB VPC, APL block after SPOR, and XTEMP hot-risky temperature marking.
- **Test Cases:**
  - Verify all VPCT/VBINFO bits are set correctly after creating blocks of each type (PSA, TLC L2, SLC L2, WB, GC source/dest, RAIN, RPMB, APL, temperature-risky).
  - Confirm FG/BG GC queue state after C087 refresh booking.
  - Confirm APL block creation via RPMB write + SPOR.
  - Confirm XTEMP hot-risky marking when NAND temperature exceeds XTEMP_REFRESH_T2.
- **Key APIs Used:**
  - `api.read_Xmemory()` — backup EC from SRAM; read VPCT/VBINFO from SRAM address
  - `api.get_fw_geometry()` — `l84_vb_size_u0` (SLC VB size), `l88_vb_size_u1` (TLC VB size)
  - `api.get_flash_setting()` — mConfig XTEMP parameters (XTEMP_ENABLE_PEC, XTEMP_REFRESH_T2)
  - `api.sequential_write()`, `api.random_write()` — generate VBs of each type
  - `project_api.issue_40C0_to_get_VPCT_description()` — read VPCT for a specific VB
  - `project_api.issue_C087_to_book_refresh_job()` — trigger refresh job for GC queue test
  - `project_api.get_all_VB_erase_count()` — EC table read
  - `project_api.rpmb_key_programming()` — RPMB key setup
  - `api.init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET, powerdown=True)` — SPOR for APL test
- **Key Parameters:**
  - LUN configuration: 5 LUNs (normal, EM1/SLC, WB, GC, Temperature)
  - VBINFO bits checked: `IS_TLC`, `IS_OPEN`, `IS_PARTIAL_BLOCK`, `GC_DEST`, `GC_SOURCE`, RAIN bits, `VBINFO_BIT_IS_APL`, `VBINFO_BIT_HOT_RISKY`
  - XTEMP: EC set to `XTEMP_ENABLE_PEC * 100`, NAND temp set to `XTEMP_REFRESH_T2 + 1`, write 1.5 TLC VBs
- **Test Pattern:**
  - `pre_process`: `config_lun` (5 LUNs), RPMB key programming, backup EC via `read_Xmemory`
  - `step1–2`: PSA block creation → check `VBINFO_BIT_IS_PSA`, VPC, `PMNTRAINEN`
  - `step3–4`: Write TLC/SLC/WB VBs → verify all VPCT/VBINFO bits per VB type
  - `step5`: Issue C087 refresh booking → verify FG/BG GC queue VBs
  - `step6`: RPMB write + SPOR → verify `VBINFO_BIT_IS_APL == 1`
  - `step7–10` (in `step7` method): Read XTEMP params → set EC → set NAND temp → write 1.5 TLC VB → verify `VBINFO_BIT_HOT_RISKY == 1`
  - `post_process`: Restore EC via custom `set_ec()`
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `SIGHTING_RESPONSE_UNEXPECTED`
  - `SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET`

---

### CustomVU_0002 — Get FW Version Test

**File:** `PSW_F_P3_CustomVU_0002_Get_FW_Version.py`

- **Feature Name:** FW version retrieval and cross-validation between flash settings and a dedicated VU.
- **Test Cases:**
  - Read FW version via `get_flash_setting()` (Vendor_Minor_Code, Vendor_Minor_Code2, compile date from Reserved_508_1023).
  - Read FW version via VU 4001 and compare against flash setting values.
  - Validate controller string prefix.
- **Key APIs Used:**
  - `api.get_flash_setting()` — `Vendor_Minor_Code`, `Vendor_Minor_Code2`, `Reserved_508_1023` (year/month/day)
  - `project_api.issue_4001_to_get_fw_version()` — returns `FwVersion`, `CompileVersion`, `ControllerNand`
- **Key Parameters:**
  - `ControllerNand` must start with `"PS8329 B68S"`
  - `FwVersion` bytes must match `Vendor_Minor_Code` / `Vendor_Minor_Code2`
  - `CompileVersion` year/month/day must match `Reserved_508_1023` fields
- **Test Pattern:**
  - `pre_process`: (empty)
  - `step1`: `get_flash_setting()` → parse version fields; `issue_4001_to_get_fw_version()` → compare all fields
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### CustomVU_0003 — Get FW Configuration Test

**File:** `PSW_F_P3_CustomVU_0003_Get_FW_Configuration.py`

- **Feature Name:** FW configuration validation via VU 408A.
- **Test Cases:**
  - Read FTL internal struct fields via `read_fw_value()`.
  - Issue VU 408A to get `GetFwConfiguration` structure.
  - Validate geometry/metadata fields against internal FTL values.
- **Key APIs Used:**
  - `api.read_fw_value()` — read FTL internal fields (ce_num, physical_ch_cnt, block_per_plane)
  - `project_api.issue_408A_to_get_fw_version()` — returns `GetFwConfiguration`
- **Key Parameters:**
  - `NumberOfTotalDie == ce_num`
  - `NumberOfChannels == physical_ch_cnt`
  - `NumberOfBlocksPerPlane == block_per_plane`
  - `SizeOfPhysicalPage == 18352`
  - `SizeOfPhysicalAddressUnit == 16384`
  - `MetadataSpareSizePerKB == 16`
  - `ECCSpareSizePerKB == 456`
- **Test Pattern:**
  - `pre_process`: (empty)
  - `step1`: `read_fw_value()` → `issue_408A_to_get_fw_version()` → compare all fields
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### CustomVU_0004 — Erase/Read Count, EC/ICS Table Test

**File:** `PSW_F_P3_CustomVU_0004_Erase_Read_Count_ETC_ICS_Table_Test.py`

- **Feature Name:** Multi-index VU sub-table verification — EC table, L2P VB table, CIS VB table, BBT sub-VB info, ICS bad block table.
- **Test Cases:**
  - Index 0 (EC table): Compare VU EC with SRAM EC; verify hidden block EC from flash_setting_buffer.
  - Index 2 (L2P VB table): Compare `get_VB_to_PB_mapping()` with `get_remap_table()`.
  - Index 3 (CIS VB table): Validate CIS Block1/2 addresses, TempCodeValidPlaneBitmap, TempCodePhysicalAddress[0..11].
  - Index 6 (BBT sub-VB info): Find BBT block (FW spare 0x8B), verify Sub_VB_version, First_empty_page==9, BBT_block_count==1.
  - Index 7 (EC table raw + VB type): Classify VBs via `get_all_VB_type()`.
  - Index 9 (ICS bad block): Compare `get_ics_bad_block()` with `get_ics_table()`.
- **Key APIs Used:**
  - `api.read_Xmemory()` — read SRAM EC
  - `api.get_flash_setting_buffer()` — hidden block EC at offset `2284 + idx*4`
  - `api.direct_read()` — raw NAND page read for BBT
  - `project_api.get_all_VB_erase_count()` — EC table from VU
  - `project_api.get_VB_to_PB_mapping()` — L2P VB table
  - `api.get_remap_table()` — remap table from SRAM
  - `project_api.get_FW_code_physical_address_information()` — CIS block info
  - `project_api.get_BBT_physical_block_information()` — BBT sub-VB info (FW spare marker 0x8B)
  - `project_api.get_all_VB_type()` — VB type classification
  - `project_api.get_ics_bad_block()`, `api.get_ics_table()` — ICS table
- **Key Parameters:**
  - BBT FW spare byte marker: `0x8B` at `data[4K*4+4]`
  - `First_empty_page == 9`, `BBT_block_count == 1`
  - CIS fields: `gwFwTmpCodeVbPlnBitmap`, `gaFwTmpCodeBlkPackAddr[]`
- **Test Pattern:**
  - `pre_process`: Read FW geometry, debug info, flash setting buffer
  - `step1` (Index 0): EC compare
  - `step3` (Index 2): L2P VB compare
  - `step4` (Index 3): CIS VB compare
  - `step6` (Index 6): BBT sub-VB info
  - `step7` (Index 7): EC raw + VB type
  - `step8` (Index 9): ICS bad block compare
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `SIGHTING_PBA_UNEXPECTED`

---

### CustomVU_0005 — Bad Block Information Test

**File:** `PSW_F_P3_CustomVU_0005_Bad_Block_Information_Test.py`

- **Feature Name:** Bad block reporting consistency between VU 405E and direct BBT NAND read.
- **Test Cases:**
  - Read bad block list from VU 405E.
  - Find BBT block via direct NAND read (FW spare byte check for `0x8B`).
  - Parse raw BBT (bit2 = bad per CE/plane/block).
  - Compare total count and verify each BBT entry appears in 405E response.
- **Key APIs Used:**
  - `project_api.issue_405E_to_get_bad_block_information()` — VU bad block list
  - `api.direct_read()` — raw BBT read (FW spare byte `[4K*4+4] == 0x8B`)
- **Key Parameters:**
  - BBT spare marker: byte offset `4K*4+4 == 0x8B`
  - BBT bit2: indicates bad block per CE/plane/block entry
- **Test Pattern:**
  - `pre_process`: (empty)
  - `step1`: `issue_405E_to_get_bad_block_information()`
  - `step2`: `find_bbt_block()` — direct_read scan for FW spare 0x8B
  - `step3`: `calculate_bbt()` — parse raw BBT
  - `step4`: Compare total count; verify each BBT entry exists in 405E data
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `SIGHTING_PBA_UNEXPECTED`

---

### CustomVU_0006 — Open VB Information Test

**File:** `PSW_F_P3_CustomVU_0006_Open_VB_Information_Test.py`

- **Feature Name:** Open VB information reporting via VU 40C1 across multiple write scenarios.
- **Test Cases:**
  - After writes to normal/EM1/RPMB/WB LUNs, verify 40C1 fields are present and increase.
  - After SSU sleep/active cycle, verify TLC, WB, SWAP_RAIN, List, LOG VB fields increase.
  - After continued writes, verify EM1, TMP_RAIN, RPMB, SWAP_RAIN_EM1, PTE, LOG VB fields appear.
  - After WB buffer fill (flush disabled), verify TLC GC VB fields appear.
  - After small EM1 config write until SLC GC threshold, verify EM1 GC VB fields appear.
- **Key APIs Used:**
  - `project_api.issue_40C1_to_get_open_vb_information()` — open VB info
  - `api.sequential_write()`, `api.random_write()` — drive VB state transitions
  - `api.ssu_sleep_and_active()` — trigger power state cycle
  - `api.set_flag(FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)` — enable WB flush
  - `api.clear_flag(FlagIDN.BKOPS_ENABLE)` — disable background ops
- **Key Parameters:**
  - Initial write size: 1 MB to each LUN type
  - WB fill timeout: 5 minutes
  - Fields verified: `L2_Open_logical_VB_Host_TLC_number`, `open_logical_VB_number_for_EM1_L2_Host`, `open_logical_VB_number_for_Write_Booster_WB_L2`, `open_logical_VB_number_for_RPMB_VB`, `PTE_Block_VB_number_logical`, `LOG_block_VB_number_logical`
- **Test Pattern:**
  - `pre_process`: (empty)
  - `step2`: Write 1 MB; get initial 40C1 info
  - `step3`: SSU sleep/active; verify TLC/WB/SWAP_RAIN/List/LOG increase
  - `step4`: Continue writing
  - `step5`: Verify EM1/TMP_RAIN/RPMB/SWAP_RAIN_EM1/PTE/LOG fields
  - `step6`: Fill WB (timeout 5 min); disable BKOPS; enable flush; verify TLC GC VB fields
  - `step7`: Config small EM1; write until SLC GC threshold; verify EM1 GC VB fields
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `SPEC_ASSERT_UFS_RSP_OP_SHALL_WRITE_ATTRIBUTE`

---

### CustomVU_0007 — Enable/Disable Background Operation Test

**File:** `PSW_F_P3_CustomVU_0007_En_Disable_BackgroundOperation_Test.py`

- **Feature Name:** VU D0FD enable/disable of BG ops, FG ops, and BG trim (FormatUnit).
- **Test Cases:**
  - WB flush: normal fill → flush → verify `ava_WB_size == 0xA` (full).
  - Disable BG ops → WB flush freezes; re-enable → flush completes.
  - Disable BG ops + power cycle + WB fill + flush sequence.
  - Trigger WL GC: set low/high EC on source/free VBs; set WL params; disable FG ops → BKOPS stays non-zero for 1 minute; re-enable (or HW reset) → BKOPS goes to 0.
  - Disable BG trim → FormatUnit times out (G_TIMEOUT_ALL); HW reset; FormatUnit succeeds; disable then re-enable BG trim; FormatUnit succeeds.
- **Key APIs Used:**
  - `project_api.issue_D0FD_en_disable_BKOPS()` — enable/disable BG ops (0x00=disable, 0x01=enable)
  - `api.read_attribute(AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)` — WB available size
  - `api.read_attribute(AttributeIDN.BG_OP_STATUS)` — BKOPS status
  - `api.set_flag(FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)` — enable WB flush
  - `project_api.set_all_VB_erase_count()` — set EC for WL trigger
  - `api.init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)` — power cycle
  - `ExecuteCMD.FormatUnit()` — BG trim test
- **Key Parameters:**
  - `ava_WB_size == 0xA` means WB fully flushed/available
  - WL GC test: 2 loop iterations, 1-minute poll for BKOPS=0
  - FormatUnit timeout: `G_TIMEOUT_ALL`
  - Flows 1–12: WB flush; Flows 13–18: BG ops + power cycle; Flows 19–30: WL GC; Flows 31–39: BG trim
- **Test Pattern:**
  - `pre_process`: (empty)
  - Flows 1–12: WB flush normal path
  - Flows 6–12: Disable BG ops → flush frozen; re-enable → flush completes
  - Flows 13–18: Disable + power cycle + fill + flush
  - Flows 19–30 (`trigger_WL_GC`): EC manipulation + WL trigger + FG ops disable/enable
  - Flows 31–39: BG trim disable/enable + FormatUnit validation
  - `post_process`: (empty)
- **Exceptions Used:**
  - `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT`
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### CustomVU_0008 — Get uC Temperature Test

**File:** `PSW_F_P3_CustomVU_0008_Get_uC_temperature_Test.py`

- **Feature Name:** Microcontroller (uC) temperature measurement via VU 40FD and attribute 18h.
- **Test Cases:**
  - Check device for TOO_HIGH/TOO_LOW_TEMP feature support.
  - Idle for 3 minutes, then read uC temperature from three sources: VU 40FD, attribute 18h, VU 40FE.
  - Parse 40FD response (sign bit[2], value bits[1:0] × 0.25°C resolution).
  - Verify temperature is in range 20–75°C.
  - Verify max diff across all sources ≤ 4°C.
- **Key APIs Used:**
  - `project_api.issue_40FD_to_get_uC_temperature()` — uC temp from VU (ReadBuffer)
  - `api.read_attribute(idn=0x18)` — temperature attribute
  - `project_api.issue_40FE_to_get_uC_temperature()` — secondary temp source
  - `api.check_feature_support()` — TOO_HIGH/LOW_TEMP feature check
- **Key Parameters:**
  - Temperature range: 20–75°C
  - Max diff across sources: 4°C
  - Resolution: 0.25°C (sign bit[2], value bits[1:0])
  - Idle sleep: 180 seconds
  - `temp_gap == 37` (internal calibration reference)
- **Test Pattern:**
  - `pre_process`: (empty)
  - `step1`: Check feature support → idle 3 min → read VU 40FD + attr 18h + VU 40FE → parse → range check → diff check
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### CustomVU_0009 — Set RPMB Write Counter / Clear Key Test

**File:** `PSW_F_P3_CustomVU_0009_Set_RPMB_WriteCounter_Clear_key_Test.py`

- **Feature Name:** RPMB write counter set and key clear across 4 RPMB regions.
- **Test Cases:**
  - For each of 4 RPMB regions (0–3): clear key via D079, program key if needed, set random counter via D078, verify counter via `rpmb_read_counter()`, clear key again, verify counter resets to 0.
- **Key APIs Used:**
  - `project_api.issue_D079_to_clear_rpmb_key()` — clear RPMB authentication key
  - `project_api.issue_D078_to_set_rpmb_write_counter()` — set RPMB write counter
  - `rpmb.rpmb_key_programming()` — program RPMB key
  - `rpmb.rpmb_read_counter()` — read RPMB write counter
- **Key Parameters:**
  - `config_region_num == 4`
  - Region sizes: `region1_size == region2_size == region3_size == 1`
  - Random counter: `randint(1, 0xFFFFFFFF)`
- **Test Pattern:**
  - `pre_process`: Configure 4 RPMB regions
  - `step1`: For region 0–3: D079 clear → key program → D078 set counter → verify → D079 clear → verify counter==0
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET`
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### CustomVU_0010 — Cleanup Write-Once Test

**File:** `PSW_F_P3_CustomVU_0010_Cleanup_Write_Once_Test.py`

- **Feature Name:** Write-once flags/attributes test with cleanup via VU D083.
- **Test Cases:**
  - For each write-once flag (`PERMANENT_WP_EN`, `PERMANENTLY_DIS_FW_UPDATE`) and attribute (`OUT_OF_ORDER_DATA_EN`, `CONFIG_DESCR_LOCK`):
    - Set → verify equals 1 → attempt re-set → expect `PARAM_ALREADY_WRITTEN` → D083 cleanup → verify restored to default.
- **Key APIs Used:**
  - `api.set_flag()`, `api.write_attribute()` — set write-once items
  - `api.read_flag()`, `api.read_attribute()` — verify values
  - `project_api.issue_D083_to_cleanup_write_once()` — VU cleanup
- **Key Parameters:**
  - Flags: `PERMANENT_WP_EN`, `PERMANENTLY_DIS_FW_UPDATE`
  - Attributes: `OUT_OF_ORDER_DATA_EN`, `CONFIG_DESCR_LOCK`
  - Expected response on re-set: `PARAM_ALREADY_WRITTEN`
- **Test Pattern:**
  - `pre_process`: (empty)
  - Per item: set → verify → re-set (expect fail) → D083 cleanup → verify default
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`
  - `SIGHTING_FAIL_CLEAN_WRITE_ONCE_ATTRIBUTE_FLAG`

---

### CustomVU_0011 — Get MDWLSV Offset Enable/Disable Test

**File:** `PSW_F_P3_CustomVU_0011_Get_MDWLSV_Offset_En_Dis_Test.py`

- **Feature Name:** MDWLSV (Minimum Die Write Level Shift Voltage) offset tracking per die, with enable/disable via VU C08C.
- **Test Cases:**
  - Disable C08C → verify VU 4029 all-zero.
  - Enable C08C → write TLC CE page to Normal → get VU 4029 + VU 4022 NAND feature → verify TLC L2 MDWLSV offset equals P3 of 4022.
  - Write EM1 LBA → verify EM1 MDWLSV offset equals P3 of 4022.
  - Write Normal L1 → verify EM1 MDWLSV offset equals P3.
  - Disable C08C → offsets unchanged.
  - Re-enable C08C → all-zero again.
  - 10-minute random write with random C08C toggle; verify table resets on re-enable.
- **Key APIs Used:**
  - `project_api.issue_C08C_to_EnDis_MDWLSV()` — enable(0) / disable(1) MDWLSV
  - `project_api.issue_4029_to_get_MDWLSV_offset_information()` — MDWLSV offset table (4 dies × 15 block types × 2 = 120 fields)
  - `project_api.issue_4022_to_get_NAND_feature()` — NAND feature (P1–P4) per CE
  - `api.sequential_write()`, `api.random_write()` — drive MDWLSV updates
- **Key Parameters:**
  - Die0–Die3 × 15 block types: MM_OPEN_BLOCK (EM1_HOST, TABLE_PTE, TEMP_RAIN, NORMAL_HOST_SLC, WRITE_BOOSTER, RPMB_HOST, RPMB_GC, SWAPRAIN_WB, SWAPRAIN_EM1, TABLE_LOG) + SM_OPEN_BLOCK (FTL_SUB, EM1_GC, NORMAL_HOST_TLC, NORMAL_GC, SWAPRAIN_HOST)
  - Random write duration: 10 minutes (flow 19)
- **Test Pattern:**
  - `pre_process`: (empty)
  - Iterations 1–2 and flow 19
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### CustomVU_0012 — L2P Normal Test

**File:** `PSW_F_P3_CustomVU_0012_L2P_Normal_Test.py`

- **Feature Name:** L2P (Logical-to-Physical) address translation consistency check between Phison VU and Micron VU.
- **Test Cases:**
  - For all enabled LUNs (up to 32): write random region; select random LBA; compare Phison `lba_to_pba()` vs Micron VU `issue_4051_to_get_physical_address()` (CE/plane/block/page/offset).
  - If PPT ≠ 0xFFFFFFFF: load PTE data via `load_PTE_data()` and direct_read; compare.
  - If PPT2 ≠ 0xFFFFFFFF: load PMD data via `load_PMD_data()` and direct_read; compare.
  - Issue `issue_4052_to_get_logical_address()` from physical address; compare LUN + LBA.
- **Key APIs Used:**
  - `api.lba_to_pba()` — Phison L2P VU (returns `L2P_PCA`)
  - `project_api.issue_4051_to_get_physical_address()` — Micron L2P VU (returns `physical_address_info`)
  - `project_api.issue_4052_to_get_logical_address()` — Micron P2L VU (returns `logical_address_info`)
  - `api.load_PTE_data()`, `api.load_PMD_data()` — read PTE/PMD from Phison VU
  - `api.direct_read()` — direct NAND read for PTE/PMD verification
  - `api.sequential_write()` — populate L2P table
- **Key Parameters:**
  - Max LUNs: 32
  - Default write size: 16 MB per LUN
  - PTE sentinel: `PPT_virtual_block_number == 0xFFFFFFFF` (not yet flushed)
  - PMD sentinel: `PPT2_virtual_block_number == 0xFFFFFFFF`
  - `wl_page_2_physical_page()`: TLC access_mode=2, WL page regions: [0,540,556,1108,1112]
- **Test Pattern:**
  - `pre_process`: Get geometry, compute AU/LUN sizes
  - `step1`: Config all LUNs → for each LUN: write → get Phison PCA → get Micron PCA → compare → PTE compare (if valid) → PMD compare (if valid) → reverse lookup via 4052 → compare LBA
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `SIGHTING_RESPONSE_UNEXPECTED`

---

### CustomVU_0013 — Get FW Info About TLC Defrag Operation Test

**File:** `PSW_F_P3_CustomVU_0013_Get_FW_Info_About_TLC_Defrag_Operation_Test.py`

- **Feature Name:** Comprehensive test of all fields returned by VU 40C2 (TLC Defrag / GC operation info).
- **Test Cases (58 test flows covering):**
  - `GC_trigger_fields` count, `GC_trigger_type` (0=none, 1=BG, 2=FG, 32=EM1)
  - BG/FG GC thresholds for normal area (`mlc_threshold - 3` / `mlc_threshold`)
  - BG/FG GC thresholds for EM1 area
  - WB cache sizes at `LS0` / `LS100`
  - `max_size_to_reduce_wb_size`
  - Available WB size
  - Invalid VB counts, used SLC/TLC VB counts
  - Stale zone sizes, `LOCKED_SRC` counts
  - IGC trigger flags, VPs to trigger IGC
  - Fill-dummy flags (cleared after power cycle)
  - BG/FG GC trigger confirmation for normal and EM1 areas
  - Fragmented VB counts
- **Key APIs Used:**
  - `project_api.issue_40C2_to_get_TLC_defrag_operation_info()` — returns all 40C2 fields
  - `api.read_attribute(AttributeIDN.BG_OP_STATUS)` — BKOPS status
  - `api.set_gc_threshold()` / `api.get_gc_threshold()` — set/get GC thresholds
  - `api.sequential_write()`, `api.random_write()` — drive GC triggers
  - `api.set_flag(FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)` — enable WB flush
- **Key Parameters:**
  - `config_wb_size == 2048 AU`
  - `DYNAMIC_SLC_UPPER_BOUND_PERCENT == 25`
  - `timeout_min == 15` (short), `timeout_min == 180` (long)
  - BG GC threshold = `mlc_threshold - 3` for normal area
  - FG GC threshold = `mlc_threshold` for normal area
- **Test Pattern:**
  - `pre_process`: Config WB LUN
  - 58 test flows verifying each 40C2 field under various write/GC/power-cycle scenarios
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT`

---

### CustomVU_0014 — BKOPS Status Test

**File:** `PSW_F_P3_CustomVU_0014_BKOPS_Status_Test.py`

- **Feature Name:** All 4 bBackgroundOpStatus levels (0/1/2/3) via VU 40DB and UFS attribute 05h.
- **Test Cases:**
  - Level 0 (idle): Default state → BKOPS=0; verify attr 05h == VU 40DB.
  - Level 1 (recommended): Write entire TLC LUN; check VU 40DB=1 during write (interspersed VU polls).
  - Level 2 (urgent — WB flush): WB 4 GB config → fill WB → set EventControl BIT2|BIT5 → write 2× WB → check EventStatus=BIT5 → event alert raised in UPIU → enable flush → poll BKOPS=2 → compare attr==VU 40DB → poll BKOPS=0 → verify `ava_WB_size==0xA`.
  - Level 3 (critical — refresh): Config normal+EM1 → set EventControl BIT2 → write 1 TLC VB → C088 stop refresh → `force_trigger_refresh_job()` → poll BKOPS=3 → compare attr==VU 40DB → check EventStatus=BIT2 → NO event alert → C088 start refresh.
- **Key APIs Used:**
  - `project_api.issue_40DB_to_get_BKOPS_status()` — VU BKOPS status
  - `api.read_attribute(AttributeIDN.BG_OP_STATUS)` — BKOPS attribute 05h
  - `api.read_attribute(AttributeIDN.EXCEPTION_EVENT_STATUS)` — EventStatus
  - `api.write_attribute(AttributeIDN.EXCEPTION_EVENT_CONTROL)` — EventControl
  - `project_api.issue_C088_to_start_stop_refresh()` — start/stop NAND refresh
  - `project_api.force_trigger_refresh_job()` — force refresh trigger
  - `api.sequential_write()` — fill TLC LUN / WB
- **Key Parameters:**
  - Wait timeout: 900 seconds (`wait_until`)
  - `BIT2 == 4`, `BIT5 == 32`
  - `ava_WB_size == 0xA` (WB fully available after flush)
  - WB config: 4 GB
- **Test Pattern:**
  - `pre_process`: (empty)
  - `step1`: Default → BKOPS=0 check
  - `step2`: Fill TLC LUN → poll BKOPS=1
  - `step3`: WB fill → EventControl → verify BKOPS=2 → flush → verify BKOPS=0
  - `step4`: Config refresh → stop refresh → force trigger → verify BKOPS=3
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT`

---

### CustomVU_0015 — Set Erase/Read Count Test

**File:** `PSW_F_P3_CustomVU_0015_Set_Erase_Read_Count_Test.py`

- **Feature Name:** EC (Erase Count) table manipulation — RAM-only (volatile) vs permanent (NVM) set, and LUN reconfiguration EC warning.
- **Test Cases:**
  - Set random EC in RAM; verify via SRAM; HW reset → verify restored to backup (volatile).
  - Set EC=0 permanently; HW reset → verify all EC==0.
  - Reconfig LUN → verify `lun_reconfig_ec_warning==0` (no warning when EC is 0).
  - Set random EC 0x100–0x300 permanently; reconfig → verify `lun_reconfig_ec_warning==1`.
  - Recover EC to backup.
- **Key APIs Used:**
  - `api.read_Xmemory()` — backup EC from SRAM (`debug_info.VB_list_cycle_address`)
  - `project_api.set_all_VB_erase_count(data_payload, set_in_ram=True/False)` — set EC table
  - `project_api.get_all_VB_read_count()` — RC table backup
  - `project_api.issue_4098_to_get_wear_leveling_information()` — WL info
  - `project_api.issue_40FE_to_read_enhanced_health_report()` — check `lun_reconfig_ec_warning`
  - `api.init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)` — power cycle
  - `api.push_write_config()`, `ExecuteCMD.send()` — LUN reconfig
- **Key Parameters:**
  - RAM-only EC: `random.randint(0x1, 0x1000)`
  - Permanent EC=0 (step3), then EC=0x100–0x300 (step5)
  - `lun_reconfig_ec_warning == 0` when EC=0; `== 1` when EC > threshold
- **Test Pattern:**
  - `pre_process`: Get FW geometry, debug info, flash setting buffer
  - `step1`: Backup EC and RC tables
  - `step2`: Set RAM EC → verify → HW reset → verify restored
  - `step3`: Set permanent EC=0 → HW reset → verify all-zero
  - `step4`: Reconfig LUN → check `lun_reconfig_ec_warning==0`
  - `step5`: Set permanent EC 0x100–0x300 → HW reset → verify
  - `step6`: Reconfig LUN → check `lun_reconfig_ec_warning==1`
  - `step7`: Recover EC to backup
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### CustomVU_0016 — Set Device State In RAM Test

**File:** `PSW_F_P3_CustomVU_0016_Set_Device_State_In_Ram_Test.py`

- **Feature Name:** Device state setting in RAM (volatile) via VU D0FC, verified via SRAM read and VU 40FC.
- **Test Cases:**
  - Set Device_state=1 via D0FC (RAM-only).
  - Verify via SRAM addr 0xF8F80826 == 1 and VU 40FC `device_state==1`.
  - Attempt VU C083 (set EC) while device_state=1; expect TARGET_FAILURE (ASC=0x24, ASCQ=0x0).
  - Power cycle (HW reset + powerdown).
  - Verify SRAM and VU 40FC both return `device_state==0` after POR.
- **Key APIs Used:**
  - `project_api.set_device_state(Device_state=1, only_in_ram=True)` — VU D0FC
  - `project_api.get_FW_states_in_RAM()` — VU 40FC returns `(_, device_state)`
  - `api.read_Xmemory(0xF8F80800)` — SRAM read; payload[38] = device_state
  - `project_api.issue_C083_to_set_erase_read_count_parameter(keep_error=True)` — expect failure
  - `api.init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET, powerdown=True)` — POR
- **Key Parameters:**
  - SRAM address: `0xF8F80800`, device_state at byte offset 38 (`payload[38]`)
  - Expected failure: `response == TARGET_FAILURE`, `status == CHECK_CONDITION`, `ASC == 0x24`, `ASCQ == 0x0`
- **Test Pattern:**
  - `pre_process`: (empty)
  - `step1`: D0FC set device_state=1 in RAM
  - `step2`: Verify SRAM and 40FC both return 1
  - `step3`: C083 → expect TARGET_FAILURE
  - `step4`: HW_RESET + powerdown
  - `step5`: Verify SRAM and 40FC both return 0
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `SIGHTING_RESPONSE_UNEXPECTED`

---

### CustomVU_0017 — Set Device State Permanently Test

**File:** `PSW_F_P3_CustomVU_0017_Set_Device_State_Permanently_Test.py`

- **Feature Name:** Device state permanent write via VU D0E2 (efuse burn), with remaining-change count tracking and limit enforcement.
- **Test Cases:**
  - Set Device_state=1 permanently (D0E2 or direct efuse D0F4); HW reset; verify `device_state == (1 << modify_cnt) - 1` and `NumOfRemainingStateChanges == 8 - modify_cnt`.
  - Perform C083 EC set while device_state=1; expect TARGET_FAILURE (same as 0016).
  - Repeat 6 more times with alternating states (some via D0E2, some via D0F4 direct efuse).
  - After 7 changes (modify_cnt=7): attempt D0E2 → expect TARGET_FAILURE (limit exhausted).
  - Verify `device_state == 2` (Failure Analysis state) and `NumOfRemainingStateChanges == 0`.
- **Key APIs Used:**
  - `project_api.set_device_state(Device_state, only_in_ram=False)` — VU D0E2 permanent
  - `project_api.issue_40E2_to_get_device_state()` — returns `(_, device_state, NumOfRemainingStateChanges)`
  - `project_api.issue_D0F4_to_set_eFuse(eFuse_addr, eFuse_value)` — direct efuse set
  - `api.read_Xmemory(0xF8F80800)` — SRAM read of efuse data
  - `project_api.issue_C083_to_set_erase_read_count_parameter(keep_error=True)` — expect failure
  - `api.init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET, powerdown=True)` — POR after each set
- **Key Parameters:**
  - `modify_limit == 8`
  - After modify_cnt sets: `device_state == (1 << modify_cnt) - 1`
  - `NumOfRemainingStateChanges == 8 - modify_cnt`
  - After 7th change: `device_state == 2` (FA state), `NumOfRemainingStateChanges == 0`
  - Efuse address: `0xF8F80800 + 0x24`, efuse data offset `[0x24:0x28]`
- **Test Pattern:**
  - `pre_process`: Read initial efuse data from SRAM; set `modify_cnt=0`, `modify_limit=8`
  - `step1`: D0E2 permanent set
  - `step2`: HW reset
  - `step3`: Verify 40E2 values
  - `step4`: C083 → expect failure
  - `step5`: 6 alternating set+verify cycles (3 via D0F4, 3 via D0E2)
  - `step6`: 8th attempt → expect TARGET_FAILURE
  - `step7`: Verify device_state==2, NumOfRemainingStateChanges==0
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `SIGHTING_RESPONSE_UNEXPECTED`

---

### CustomVU_0018 — Unlock LU Attribute Configuration-Description Test

**File:** `PSW_F_P3_CustomVU_0018_Unlock_LU_Attribute_Configuration_Test.py`

- **Feature Name:** `bConfigDescrLock` (attribute 0Bh) lock/unlock cycle with VU D085 and Write Descriptor interaction.
- **Test Cases:**
  - Verify `bConfigDescrLock == 0` initially.
  - Config WB partition successfully.
  - Write `bConfigDescrLock = 0` → success; write again → `PARAM_ALREADY_WRITTEN`.
  - Config WB partition again → success (still unlocked).
  - Issue VU D085 to unlock.
  - Config WB partition → success.
  - Write `bConfigDescrLock = 1` → lock.
  - Write `bConfigDescrLock = 0` again → `PARAM_ALREADY_WRITTEN`.
  - Config WB partition → expect `GENERAL_FAILURE` or `PARAM_ALREADY_WRITTEN`.
  - Issue VU D085 again → unlock.
  - Verify `bConfigDescrLock == 0`; config WB partition → success.
- **Key APIs Used:**
  - `api.read_attribute(AttributeIDN.CONFIG_DESCR_LOCK)` — read lock state
  - `api.write_attribute(AttributeIDN.CONFIG_DESCR_LOCK, val)` — write lock state
  - `project_api.issue_D085_unlock_LU_attribute_configuration()` — VU D085 unlock
  - `api.get_config_descriptors()`, `push_write_config()` — WB config operations
  - `ExecuteCMD.WriteDescriptor()` — raw descriptor write for error-case testing
- **Key Parameters:**
  - WB config: `b17_write_booster_buffer_type=1`, `b16_write_booster_buffer_preserve_user_space_en=1`, `l18_num_shared_write_booster_buffer_alloc_units=0x1000`
  - Expected responses: `PARAM_ALREADY_WRITTEN`, `GENERAL_FAILURE`
- **Test Pattern:**
  - `pre_process`: (empty)
  - `step1` (flows 1–16): Full lock/unlock/config sequence as above
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`

---

### CustomVU_0019 — Get Device Status of Host Write Test

**File:** `PSW_F_P3_CustomVU_0019_Get_Device_Status_Of_Host_Write_Test.py`

- **Feature Name:** Host write device status reporting via VU 4064 (burst/sustain/dirty modes).
- **Test Cases:**
  - After init: verify 4064 returns 2 (sustain).
  - Config WB; enable WB; verify 4064 returns 1 (burst).
  - Fill WB (`ava_WB_size==0x0`); verify 4064 returns 2 (sustain).
  - Disable WB; remove WB config; set EC = `PE_count_threshold` (from HwSetting); config WB; verify `bWriteBoosterbufferLifeTimeEst == 0xB`; enable WB; verify 4064 returns 2 (sustain — WB lifetime exceeded).
  - Config Normal+EM1 (no WB): write EM1 LUN → verify 4064=1 (burst); write Normal LUN → verify 4064=2 (sustain).
  - Config default; random write 5 loops; set TLC GC threshold=10 → BKOPS=2; verify 4064=3 (dirty).
- **Key APIs Used:**
  - `project_api.issue_4064_get_device_status_of_host_write()` — VU 4064 status (0-byte of data)
  - `api.read_attribute(AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)` — WB fill check
  - `api.read_attribute(AttributeIDN.WRITEBOOSTER_BUFFER_LIFETIME_EST)` — WB lifetime
  - `api.HwSetting.get_local_val(HwSettingField.PE_COUNT_THRESHOLD_LSB/MSB)` — EC threshold
  - `api.ufs_api.vendor_cmd.set_gc_threshold(ACCESS_MODE_MLC, 10)` — trigger FG GC
  - `api.set_flag(FlagIDN.WRITEBOOSTER_EN)`, `api.clear_flag(FlagIDN.WRITEBOOSTER_EN)` — WB toggle
- **Key Parameters:**
  - Status values: 1=burst, 2=sustain, 3=dirty
  - WB config: `l18_num_shared_write_booster_buffer_alloc_units=0x400`
  - WB lifetime threshold: `bWriteBoosterbufferLifeTimeEst == 0xB`
  - `TLC_Max_PEC == 3000`, timeout_min=15
- **Test Pattern:**
  - `pre_process`: (empty)
  - `step1` (flows 1–24): full sequence as above
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT`

---

### CustomVU_0020 — Set/Get NAND Feature Test

**File:** `PSW_F_P3_CustomVU_0020_Set_Get_NAND_Feature_Test.py`

- **Feature Name:** NAND feature register get/set via VU 4022 / VU 4023 across all CEs and feature addresses.
- **Test Cases:**
  - For each CE (0 to `ce_num-1`) and each feature address in the list: issue VU 4022 to get current value (P1–P4); issue VU 4023 to re-set with same value (read-modify-write restore). Feature addr 0x58 is skipped for set.
  - For feature address 0x01 per CE: get current; set random P1–P4 (`randint(0x1, 0xFF)` × 4); verify by reading back; then restore original P1–P4.
- **Key APIs Used:**
  - `project_api.issue_4022_to_get_NAND_feature(CE, feature_addr)` — returns `(response, data_payload)` parsed as `get_nand_feature_format` (result, die, P1–P4)
  - `project_api.issue_4023_to_set_NAND_feature(CE, feature_addr, P1, P2, P3, P4)` — returns `(response, data_payload)` parsed as `set_nand_feature_format`
  - `api.get_flash_setting()` — `Max_Fdevice` for CE count
  - `api.get_fw_geometry()` — `l84_vb_size_u0`, `l88_vb_size_u1`
- **Key Parameters:**
  - Feature address list: `[0x01, 0x02, 0x10, 0x20, 0x22, 0x23, 0x24, 0x40, 0x58, 0x7F, 0x80, 0x81, 0x83, 0x84, 0x86, 0x87, 0x90, 0x93, 0x96, 0xA0, 0xA1, 0xA2, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xAB, 0xB1, 0xB2, 0xB3, 0xB4, 0xDA, 0xE1, 0xE2, 0xE3, 0xE7]`
  - Skip set for addr `0x58`
  - Random set P1–P4: `randint(0x1, 0xFF)` per parameter
- **Test Pattern:**
  - `pre_process`: Get geometry, flash_setting, compute VB sizes; set LUN config indices
  - `step1`: For each CE × feature addr: 4022 get → 4023 set same; for addr 0x01: set random → verify → restore
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### CustomVU_0021 — Get Next Open VB Test

**File:** `PSW_F_P3_CustomVU_0021_Get_Next_OpenVB_Test.py`

- **Feature Name:** Prediction of next open VB via VU 40DC, cross-verified against actual open VB from VU 40C1.
- **Test Cases:**
  - TLC L2 test: get next TLC open VB (A) from 40DC; write 1 TLC VB; confirm old VB A becomes current L2 MLC pool; verify open VB from 40C1 (B) equals A.
  - EM1 (SLC) L2 test: get next SLC open VB (A); write 1 SLC VB; confirm old VB A becomes current L2 SLC pool; verify 40C1 (B) equals A.
  - L1 Small Chunk test: get next L1 VB (A); write small chunk until L1 VB changes; verify old A becomes current L1.
  - WB test: enable WB; get next WB open VB (A); write 1 SLC VB; verify 40C1 WB open VB (B) equals A.
- **Key APIs Used:**
  - `project_api.issue_40DC_to_get_next_open_vb_information(openvbtype)` — `NextOpenVBInformation` (fields: DM_NORMAL_HOST_VB, DM_NORMAL_WB_VB_0, DM_NORMAL_SHARE_VB_0/1, DM_RPMB_HOST_VB, DM_NORMAL_DEFRAG_VB, DM_EM1_DEFRAG_VB, List, PTE, LOG, TMP_RAIN, etc.)
  - `project_api.issue_40C1_to_get_open_vb_information()` — `OpenVBInformation`
  - `get_vb_info()` — VB group/dirty/access_mode status per VB
  - `api.sequential_write()`, `ExecuteCMD.Write10()` — write data
  - `api.set_flag(FlagIDN.WRITEBOOSTER_EN)` / `api.clear_flag()` — WB toggle
- **Key Parameters:**
  - VB groups: `used_blk_pool_slc=16`, `used_blk_pool_mlc=17`, `current_blk_pool_mlc=7`, `current_blk_pool_slc=6`, `current_l1=13`
  - L1 chunk size: `BLOCK4K_SIZE_16K_BYTE`
  - timeout_min=15 for L1 loop
- **Test Pattern:**
  - `pre_process`: Get geometry, FW geometry, config 2 LUNs (Normal + EM1); write 4 LBAs each
  - `step1` (flow 1–4): TLC / EM1 / L1 / WB next-open-VB prediction tests
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT`

---

### CustomVU_0022 — Get Defrag Source VP Info Test

**File:** `PSW_F_P3_CustomVU_0022_Get_Defrag_Source_Vp_Info_Test.py`

- **Feature Name:** GC defrag source VP (Valid Page) information via VU 40DD, cross-verified by direct NAND read.
- **Test Cases:**
  - Fill WB buffer; enable GC trigger; freeze FG GC via D0FD; identify GC target VB.
  - Issue VU 40DD to get source VP info (vbnum, die, plane, page, vpindex).
  - Direct read GC target VB first page (mode=2/SLC).
  - Direct read source VP from source VB (mode=1/TLC) using page/vpindex offset.
  - Compare first 4 KB of both reads — must match.
- **Key APIs Used:**
  - `project_api.issue_40DD_to_get_defrag_source_vp_information(vb, die, plane, page, vpIndex)` — returns `sourcevpInfo`
  - `project_api.issue_D0FD_en_disable_BKOPS(bValue=0x00)` — freeze FG GC
  - `project_api.issue_40DC_to_get_next_open_vb_information(0)` — get next open VB
  - `api.direct_read(pca, block_count, include_FW_spare=True)` — raw NAND read
  - `get_vb_info()` — find VB in GC pool (group=10)
- **Key Parameters:**
  - `PCA.b4_mode`: 2=SLC (target), 1=TLC (source)
  - Source VP page offset: `page * 32 + vpindex * 8` (in flash pages)
  - Comparison: first 4096 bytes of each direct-read payload
  - CHUNK_SIZE = 4096
- **Test Pattern:**
  - `pre_process`: Get geometry, FW geometry; config 2 LUNs (Normal + EM1)
  - `step1` (flows 1–10): Fill WB → enable flush → freeze GC → identify target VB → 40DD get source VP → direct read target → direct read source → compare
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT`

---

### CustomVU_0023 — Host LBA to FTL LBA Test

**File:** `PSW_F_P3_CustomVU_0023_Host_LBA to_FTL_LBA_Test.py`

- **Feature Name:** Host LBA to FTL LBA translation via VU 40D4, cross-validated against Phison `lba_to_pba()` LCA field.
- **Test Cases:**
  - For each of 4 LUNs (Normal × 2, EM1 × 2 with Boot A/B): write 4 MB; select random LBA; issue Phison `lba_to_pba()` to get `l112_lca`; issue Micron VU 40D4 to get `ftl_lba.lba`; compare both values.
- **Key APIs Used:**
  - `api.lba_to_pba(lun, lba)` — Phison L2P (returns `L2P_PCA` with `l112_lca`)
  - `project_api.issue_40D4_to_get_FTL_LBA(lun, lba)` — Micron VU 40D4 (returns `(_, ftl_lba)` with `ftl_lba.lba`)
  - `api.get_unit_descriptor(lun)` — `q11_logical_block_count`
  - `api.get_config_descriptors()`, `api.push_write_config()` — LUN config
  - `ExecuteCMD.Write10()`, `ExecuteCMD.RequestSense()` — write and sense
- **Key Parameters:**
  - LUN config: LUN0=Normal, LUN1=Enhanced_1/Boot_A, LUN2=Enhanced_1/Boot_B, LUN3=Enhanced_1
  - Default write size: 4 MB
  - AU sizes derived from geometry descriptor
- **Test Pattern:**
  - `pre_process`: Get geometry, compute AU/LUN sizes
  - `step1` (flows 1–6): Config 4 LUNs → for each LUN: write → random LBA → Phison L2P → Micron 40D4 → compare LCA
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`

---

### CustomVU_0024 — Physical Block to Logical VB Test

**File:** `PSW_F_P3_CustomVU_0024_Physical_Block_to_Logical_VB_Test.py`

- **Feature Name:** Physical block to logical VB mapping via VU 40C9, cross-validated against BBR table + remap table.
- **Test Cases:**
  - Fetch BBR (Bad Block Replacement) table from direct NAND read (FW spare `0x8B`, page 2).
  - Fetch remap table from SRAM (`debug_info.VB_list_remap_address`).
  - For each physical block 20–total_vb_count: look up BBR entry → get BBR VB → look up remap entry → get logical VB.
  - For each remapped entry: issue VU 40C9 (`issue_40C9_to_get_logical_vb(pb, plnId)`) → compare `vb.logical_vb` with remap table logical VB.
- **Key APIs Used:**
  - `project_api.issue_40C9_to_get_logical_vb(pb, plnId)` — VU 40C9 PB→VB
  - `api.direct_read(pca, block_count=4, include_FW_spare=True)` — BBT raw read
  - `api.read_Xmemory(debug_info.VB_list_remap_address)` — remap table from SRAM
  - `api.get_fw_geometry()` — `l52_total_vb_count`
  - `api.get_flash_setting_buffer()` — `Max_Fdevice`, `Plane_Per_Die`
- **Key Parameters:**
  - BBT FW spare: `spare[0:5] == [0xFF, 0xFF, 0xFF, 0xFF, 0x8B]` and `spare[128] & 0x10 == 0`
  - BBR table: `plane_shift=3`, indexed as `(ce << 3 + pln) * 256`; pairs at `i*2` (original), `i*2+2` (replacement)
  - `plnId = ce * 6 + pln`
  - Physical block scan range: 20 to `l52_total_vb_count`
- **Test Pattern:**
  - `pre_process`: Get FW geometry, debug info, flash setting buffer
  - `step1` (flows 1–5): Fetch BBR → fetch remap → build map → 40C9 verify per entry
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### CustomVU_0025 — Get eFuse Test

**File:** `PSW_F_P3_CustomVU_0025_Get_Efuse_Test.py`

- **Feature Name:** eFuse data retrieval and cross-validation between VU 40F4 and SRAM read.
- **Test Cases:**
  - Issue VU 40F4 to get eFuse data.
  - Read SRAM at address `0xF8F80800` via `read_Xmemory`.
  - For each 32-bit eFuse word: compare VU value with SRAM value (4-byte little-endian).
- **Key APIs Used:**
  - `project_api.issue_40F4_to_get_eFus()` — returns struct with `efuse[]` array
  - `api.read_Xmemory(sram_address=0xF8F80800)` — raw SRAM data
- **Key Parameters:**
  - SRAM base address: `0xF8F80800`
  - Comparison: `vu_data.efuse[i].value == int.from_bytes(sram[i*4:i*4+4], 'little')`
- **Test Pattern:**
  - `pre_process`: (empty)
  - `step1` (flows 1–3): 40F4 get eFuse → SRAM read → compare each word
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### CustomVU_0026 — Get Used Mapping / Used Size / Device Free Size Test

**File:** `PSW_F_P3_CustomVU_0026_Get_used_mapping_used_size_Device_free_size_Test.py`

- **Feature Name:** Device storage accounting via VU 40A8 — data free size (mode 1) and mapping size (mode 2).
- **Test Cases:**
  - For 2 WB cases (no WB / with WB) × 2 LUN ratio cases (100% Normal / 50-50 Normal+EM1):
    - Before write: 40A8 mode1 = total_normal_MB, mode2 = 0.
    - After random write to Normal LUNs (random len 1–1 GB each): 40A8 mode1 = total_normal_MB - written_MB, mode2 = written_nodes.
    - After random unmap of portion of written data: 40A8 mode1 = previous_free + unmapped, mode2 = written_nodes - unmapped.
- **Key APIs Used:**
  - `project_api.issue_40A8_to_get_used_mapping_used_size_device_free_size(mode, lun)` — returns integer (MB or node count)
  - `api.get_config_descriptors()`, `api.push_write_config()` — LUN config
  - `ExecuteCMD.Write10()`, `ExecuteCMD.Unmap()` — write and unmap
  - `api.read_attribute(DescriptorIDN.UNIT)` — LUN capacity
- **Key Parameters:**
  - mode=1: data free size in MB
  - mode=2: mapping (used) size in 4K nodes
  - `DATA_SIZE_4K_BYTE = 4096`
  - Write len: `random.randint(1, min(1 GB, LUN_capacity))`
  - WB config: `b16_write_booster_buffer_preserve_user_space_en=1`
- **Test Pattern:**
  - `pre_process`: Get `_param` (shared)
  - `step1` (flows 1–15 per case): Config LUN → 40A8 before write → write Normal LUNs → 40A8 after write → unmap → 40A8 after unmap
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### CustomVU_0027 — Get Current CLK Frequency Test

**File:** `PSW_F_P3_CustomVU_0027_Get_Current_CLK_Freq_Test.py`

- **Feature Name:** Clock tree frequency verification via VU 40EE.
- **Test Cases:**
  - Issue VU 40EE to get clock frequency data.
  - Verify each clock domain against expected values.
- **Key APIs Used:**
  - `project_api.issue_40EE_to_get_current_clk_freq()` — returns clock struct
- **Key Parameters:**
  - `clk_tree_grp2_cpu == 667` MHz
  - `clk_tree_grp3_buf == 200` MHz
  - `clk_tree_grp3_cop0 == 200` MHz
  - `domain_12_ldpc_dec_clk == 266` MHz
  - `domain_13_ldpc_enc_clk == 266` MHz
  - `domain_15_onfi_phy_mdll == 1600` MHz
- **Test Pattern:**
  - `pre_process`: (empty)
  - `step1` (flows 1–7): Issue 40EE → compare each clock domain value
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### CustomVU_0028 — Task Abort Test

**File:** `PSW_F_P3_CustomVU_0028_Task_Abort_Test.py`

- **Feature Name:** Task Management (ABORT_TASK, ABORT_TASK_SET, CLEAR_TASK_SET, LU_RESET) behavior and abort hit counting via VU 40F0 and VU D0B0.
- **Test Cases:**
  - For each TM function (ABORT_TASK, ABORT_TASK_SET, CLEAR_TASK_SET, LU_RESET):
    - Enable assert via D0B0; send random SCSI cmds + TM; verify FW assert number == 0xF400.
    - Verify unipro/endpoint reset fails during assert state.
    - HW reset; verify health report `latest_assert_or_panic_triggered == 0xF400`, `total_panic_count > 0`.
    - Disable assert via D0B0; for each cmd category (ONLY_WRITE, ONLY_READ, ONLY_VERIFY, ONLY_OTHER, RANDOM):
      - Issue random SCSI cmds + TM; check each cmd's abort status via `check_if_target_is_aborted()`.
      - Issue VU 40F0 before and after; verify abort count increases for writes/reads/others match actual.
      - Verify reserved fields == 0; verify cumulative counters non-decreasing.
- **Key APIs Used:**
  - `project_api.issue_D0B0_to_switch_abort_task_assert(enable)` — enable/disable FW assert on TM
  - `project_api.issue_40F0_to_get_task_abort_hit_information()` — returns `VU_40F0_struct` (num_of_write/read/other_cmd_been_abort, total, verify_abort_*, abort_*_stage, etc.)
  - `api.get_fw_assert_number()` — FW assert number
  - `project_api.issue_40FE_to_read_enhanced_health_report()` — `latest_assert_or_panic_triggered`, `total_panic_count`
  - `api.check_if_target_is_aborted(target_idx, tm_idx)` — check abort status per cmd
  - `api.init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)` — power cycle
  - `ExecuteCMD.TaskManagement()` — issue TM (ABORT_TASK, ABORT_TASK_SET, etc.)
  - `ExecuteCMD.Write6/10/16()`, `Read6/10/16()`, `Verify10()`, `Unmap()`, etc. — random SCSI
- **Key Parameters:**
  - FW assert number: `0xF400`
  - TOTAL_CMDS: 3 (2 targets + 1 TM)
  - TM position: always last (TOTAL_CMDS - 1)
  - Config: 32 LUNs, random EM1/Normal, `total_au / 32` AU each
  - RPMB region 0 key programmed in precondition
- **Test Pattern:**
  - `pre_process`: Get param; config 32 LUNs (random EM1/Normal); RPMB key programming
  - `step1`: For each TM function: assert-enable test → reset → assert-disable test (5 cmd categories × abort count verify)
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`
  - `SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET`
  - `DCMD5_LINK_STARTUP_FAIL`

---

### CustomVU_0029 — Get OTP Test

**File:** `PSW_F_P3_CustomVU_0029_Get_OTP_Test.py`

- **Feature Name:** OTP (One-Time Programmable) data retrieval and cross-validation against direct BBT read.
- **Test Cases:**
  - Issue VU 40BC with page_index 0 (full), 1 (top deck), 2 (bottom deck) to get OTP data.
  - Verify top deck BB page (index 1) == bottom deck BB page (index 2).
  - Parse OTP full page (index 0) and top deck page (index 1) using die-header format (0xFFF0–0xFFF3 markers, 0xFFFF terminator).
  - Verify parsed bad block lists match between full and top.
  - Get BBT physical block info from VU 4097; direct read BBT (4 CEs × 4 KB).
  - Format direct-read BBT (bit 0x04 in nibbles = bad block) into per-die bad block list.
  - Verify OTP full page data matches direct-read BBT data.
- **Key APIs Used:**
  - `project_api.issue_40BC_get_OTP(OTP_page_index)` — returns response with `.data`
  - `project_api.get_BBT_physical_block_information()` — BBT block address
  - `api.direct_read(pca, block_count=4*4096, include_FW_spare=True)` — raw BBT
  - `api.dumpfile()` — save OTP/BBT raw data
- **Key Parameters:**
  - OTP page indices: 0=full, 1=top deck, 2=bottom deck
  - Die header markers: `0xFFF0` (die0), `0xFFF1` (die1), `0xFFF2` (die2), `0xFFF3` (die3); `0xFFFF` = end
  - BBT format: nibble value `0x04` = bad block; vb = `byte_idx // 3`, plane = `(byte_idx % 3) * 2 [+ 1]`
  - Comparison: `otp[1] == otp[2]` (top == bottom); `otp_dict0 == otp_dict1` (full == top); `otp_dict0 == direct_read_bbt_dict`
- **Test Pattern:**
  - `pre_process`: Get FW geometry, flash setting buffer
  - `step1` (flows 1–5): 40BC page 0/1/2 → top==bottom check → parse dicts → full==top check → 4097 BBT info → direct read BBT → format → OTP==BBT check
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

### CustomVU_0030 — Dump MPHY Register Test

**File:** `PSW_F_P3_CustomVU_0030_Dump_MPHY_Register_Test.py`

- **Feature Name:** M-PHY register dump via VU 4083, cross-validated against SRAM and document spec values.
- **Test Cases:**
  - Issue VU 4083 to dump first 2048 bytes of M-PHY registers.
  - Read SRAM address `0xF8F86000` via `read_Xmemory`; take first 2048 bytes.
  - Mask out volatile bytes at offsets `0x750–0x754` in both (set to 0).
  - Compare VU dump vs SRAM — must be identical.
  - Compare VU dump against document expected values (`project_api.MPHY_REG_CHECKS` list of `CompareItem(offset, expected)`).
- **Key APIs Used:**
  - `project_api.issue_4083_dump_the_MPHY_register()` — returns response with `.data[0:2048]`
  - `api.ufs_api.vendor_cmd.read_Xmemory(sram_address=0xF8F86000)` — SRAM M-PHY registers
  - `api.dumpfile()` — save raw and masked dumps
  - `project_api.MPHY_REG_CHECKS` — list of `CompareItem(offset, expected_byte)` from document
- **Key Parameters:**
  - M-PHY register base SRAM address: `0xF8F86000`
  - Data size: 2048 bytes
  - Volatile offsets masked: `0x750–0x754` (5 bytes zeroed before compare)
  - Document check list: `MPHY_REG_CHECKS` (defined in `project_api`)
- **Test Pattern:**
  - `pre_process`: (empty)
  - `step1` (flows 1–4): VU 4083 dump → SRAM read → mask volatile bytes → VU==SRAM compare → VU vs document compare
  - `post_process`: (empty)
- **Exceptions Used:**
  - `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0031 — Get VB List Info Test
- **Feature Name:** VB List Information — verify VU 0x406D returns correct VB group/access-mode categorization; tested before and after multi-LU + WriteBooster configuration and after WB flush
- **VU Commands Used:** `project_api.custom_vu.issue_406D_get_VB_list_info()`
- **Key APIs:** `api.get_config_descriptors()`, `push_write_config()`, `api.HwSetting.get_instance()`, `hw_setting.set_to_device(HwSettingField.POWER_SAVING_CTRL_ENABLE, 0x3A)`, `api.set_flag(FlagIDN.WRITEBOOSTER_EN)`, `api.set_flag(FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)`, `api.read_attribute(AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)`, `api.random_write()`
- **Test Flow:** pre_process: Compute total_au. step1: (1) Disable power saving. (2) Issue VU 406D; compare sorted VB list vs SW-calculated list. (3) Config multi-LU+WB (LUN0=NORMAL, LUN1=ENHANCED_1, shared WB=0x400 AU). (4) Re-issue 406D and re-compare. (5) Fill WB buffer via random writes; poll until AVAILABLE_WB_SIZE=0. (6) Re-issue 406D and compare. (7) Flush WB; poll until SIZE=0xA and STATUS=COMPLETED. (8) Re-issue 406D and compare. post_process: Restore HW power-saving; restore original LU config.
- **Key Parameters/Data Structures:** `VB_group_for_list` enum (LIST_BLK=0x01 ... FREE_BLK_QUEUE_TABLE=0x1C); VB entry layout: bits[5:0]=group, bits[7:6]=access_mode; Groups 0x07/0x11/0x13 split by access_mode; group 0x1B merged; result sorted 2-byte-LE per entry padded to 0x1000 bytes; timeout_min=15
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT`

### CustomVU_0032 — Get UIC Configuration Test
- **Feature Name:** UIC (UniPro Interface Configuration) — verify VU 0x4049 UIC config payload matches live DME_Get MIB attribute reads
- **VU Commands Used:** `project_api.issue_4049_get_UIC_configuration()`
- **Key APIs:** `sdk_lib.DMETarget.PEER`, `sdk_lib.AttrSetType.NORMAL`, `_sdk._dll.cdll.DME_Get(sdk, attr_get_type, sel, mib_attr, &apl_result, &apl_val)` — ctypes DLL call
- **Test Flow:** pre_process: Log common paths. step1: (1) Issue VU 0x4049; dump payload. (2) Loop through testAttributeslist MIB IDs calling DME_Get (PEER/NORMAL). (3) Compare first 21 bytes of VU response vs DME-get bytearray.
- **Key Parameters/Data Structures:** `testAttributeslist` enum — 19 MIB attribute IDs: PA_HIBERN8TIME (0x15A7), N_DEVICEID (0x3000), T_CONNECTIONSTATE (0x4020), and 16 others; comparison window: payload[0:21]
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0033 — Get Page Attribute Test
- **Feature Name:** NAND Page Attribute — verify VU 0x4010 returns correct page type (SLC/MLC/TLC-LP/UP/XP) and TLC grouped page indices for all 3312 valid page indices; out-of-range (page 3312) returns ILLEGAL_REQUEST
- **VU Commands Used:** `project_api.issue_4010_get_page_attribute(page_index, keep_error=True)`
- **Key APIs:** `ExecuteCMD.clear()`, `api.UPIUResponse.TARGET_SUCCESS/TARGET_FAILURE`, `api.ScsiStatus.CHECK_CONDITION`, `api.SenseKey.ILLEGAL_REQUEST`
- **Test Flow:** pre_process: no-op. step1: Loop page_index 0–3312. For 0–3311: check TARGET_SUCCESS, parse resp.data[0:3]=page_attribute, [4:7]=TLC_lower, [8:11]=TLC_upper, [12:15]=TLC_extra; compare to SW formula. For page 3312: check TARGET_FAILURE + CHECK_CONDITION + ILLEGAL_REQUEST + ASC=0x1A.
- **Key Parameters/Data Structures:** expected_page_attribute logic: 0-1619=TLC group (type=idx%3+3); 1652-3307=TLC group (type=(idx+1)%3+3); 1620-1651=MLC (type=(idx-1620)%2+1); 3308-3311=SLC (type=0); encoding: 0=SLC, 1=MLC_lower, 2=MLC_upper, 3=TLC_lower, 4=TLC_upper, 5=TLC_extra
- **Exceptions Used:** `SIGHTING_RESPONSE_UNEXPECTED`, `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0034 — Get Random Read Statistics Test
- **Feature Name:** Random Read Statistics — verify VU 0x409F counters (enter/exit/cause) increment correctly on write-abort, SSU-abort, ATS-abort; verify disable via VU 0xC0F4 suppresses counting; reset to zero after power cycle
- **VU Commands Used:** `project_api.issue_409F_to_get_random_read_statistics()`, `project_api.issue_C0F4_to_EnDis_RR_detect(rr_enable, pre_read_en)`
- **Key APIs:** `api.HwSetting.get_instance()`, `hw_setting.set_to_device(HwSettingField.MEDIUM_SCAN_TRIGGER_TIME, 0x80)`, `ExecuteCMD.StartStopUnit().assign(power_condition=0x02/0x01)`, `api.init_tester_to_unit_ready(resetmode=Dcmd5ResetType.HW_RESET, powerdown=True)`
- **Test Flow:** pre_process: Config LUN0=NORMAL, LUN1=BOOT_A(EM1), LUN2=BOOT_B(EM1), LUN3=EM1. step1: Loop 6 cases (LUN0, EM1, BOOT_A, BOOT_B, LUN0+WB, 0xB0). For each: (a) random read, abort with Write10; poll 409F — verify enter/exit=loop count. (b) SSU SLEEP→ACTIVE abort, verify +1. (c) ATS abort (sleep 2s), verify +1 and exit_cause. (d) HW reset, verify all 409F counters=0. (e) Disable via C0F4, trigger, verify no increment; re-enable. post_process: Restore MEDIUM_SCAN_TRIGGER_TIME.
- **Key Parameters/Data Structures:** random_read_statistics_info fields: Small_chunk_RR_enter/exit_counter, Random_Read_exit_cause, Large_chunk_RR_enter/exit, Sequential_Read_enter/exit/cause, Random_Write_enter/exit/cause, Sequential_Write_enter/exit/cause, random_read_count_threshold, random_read_max_chunk_size, Current_power_pattern; rand-read chunk: 4K-32K bytes, 6-10 commands
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT`

### CustomVU_0035 — Get Pre-Read Statistics Test
- **Feature Name:** Pre-Read Statistics — verify VU 0x4090 counters (enter/exit/cause/lun) increment correctly on write-abort, SSU-abort, ATS-abort of sequential reads; verify reset after power cycle; disable via VU 0xC0F4 suppresses counting
- **VU Commands Used:** `project_api.issue_4090_to_get_pre_read_statistics()`, `project_api.issue_C0F4_to_EnDis_RR_detect(rr_enable, pre_read_en)`
- **Key APIs:** `ExecuteCMD.Read10().assign(lun=testlun, lba=read_lba, length=32, fua=0)` — sequential reads (chunk=32, count=32)
- **Test Flow:** Similar to 0034 but with sequential reads (chunk=32 LBAs, count=32 commands, starting at 0). Loop 6 LUN cases. Verify: enter=loop, exit=loop, exit_cause=3, lun matches. SSU and ATS aborts verify +1. HW reset verifies all_zero. Disable C0F4 verify specific fields=0.
- **Key Parameters/Data Structures:** pre_read_statistics_info fields: pre_read_enter/exit_counter, pre_read_exit_cause, pre_read_avail_buffer_counter, next_SR_command_count, RR_command_count, current_SR_start_lba, next_SR_start_lba, pre_read_start_lba, pre_read_lun; 0xB0 LUN maps to BOOT_A physical LUN
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0036 — Trigger RPMB Erase Status Test
- **Feature Name:** RPMB Erase with Password — set/clear/query RPMB erase password (VU 0x4047), trigger RPMB erase (VU 0x4048), poll completion, verify RPMB data zeroed, test wrong-password rejection
- **VU Commands Used:** `project_api.issue_4047_to_set_clear_query_RPMB_erase_password(password, cmd)`, `project_api.issue_4048_to_trigger_RPMB_erase_status(password, cmd)`
- **Key APIs:** `RPMB(RPMBRegion.REGION_0)`, `rpmb.rpmb_read_counter()`, `rpmb.rpmb_key_programming()`, `rpmb.rpmb_write_data(0, 4)`, `rpmb.rpmb_read_data(0, N)`, `access_vendor_mode()`, `vuc_clear_rpmb_key(RPMBRegion.REGION_0)`
- **Test Flow:** pre_process: Config LUN0=NORMAL, LUN1=EM1. step1: (1) Query password status. (2) Clear any existing password. (3) Set random 64-bit password. (4) Query — expect status=1 (set). (5) Write RPMB region0 data. (6) Trigger erase (cmd=0); poll query (cmd=1) until status=1. (7) Verify RPMB data reads as zero. (8) Attempt clear with wrong password (password-1) — expect result=2. (9) Clear with correct password — expect result=0.
- **Key Parameters/Data Structures:** set_cmd=0, clear_cmd=1, query_cmd=2; trigger cmd=0 (trigger), cmd=1 (query status); status codes: 0=idle/success, 1=complete, 2=in-progress; password: 64-bit random; RPMB data check: resp.data[lba*512+228:lba*512+484] for 4 LBAs
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET`, `SPEC_ASSERT_RPMB_KEY_NOT_CLEARED`

### CustomVU_0037 — Do Power Loss Analysing Test
- **Feature Name:** Power Loss Analysis (APL) — verify VU 0x409D opcodes 0 (LWP check), 1 (APL param set), 2 (APL param get), 3 (blank check), 4 (power-loss check) on TLC open VB after SPOR
- **VU Commands Used:** `project_api.issue_409D_to_do_power_loss_analysing(opcode, ce, plane, vb, TLC/SLC, startpage, stoppage [, param_index [, param_value]])`
- **Key APIs:** `project_api.issue_40C1_to_get_open_vb_information()`, `project_api.issue_C060_to_write_raw_data()`, `api.init_tester_to_unit_ready(resetmode=Dcmd5ResetType.HW_RESET, powerdown=False)`, `ExecuteCMD.Write10().assign(lun=0, lba=0, length=tlc_ce_page, fua=1)`
- **Test Flow:** pre_process: Config LUNs; compute TLC/SLC CE-page sizes. step1: (1) Write 4x CE-pages; after each issue opcode 0 LWP check on all CE/plane — verify LWP != 0xFFFF. (2) Opcode 2: get max param index (expect 27); read all 28 params. (3) Opcode 1: toggle each param. (4) HW reset (no power-down). (5) Opcode 3 blank check at LWP and LWP+1 — verify LWP page=0xE (programmed), FEP=0x0 (blank). (6) Opcode 4 power-loss check — verify LWP=0x0 (good), FEP=0x2.
- **Key Parameters/Data Structures:** APL_LWP_Check struct: .LWP.value; APL_Get_Parameter: .appoint_param_value.value; APL_Blank_Check: .pagelist[idx].blank_result.value (0xE=programmed, 0x0=blank); APL_Powerloss_Check: .pagelist[idx].blank_result.value (0x0=good, 0x2=FEP); TLC=0, SLC=1; tlc_ce_page = plane_per_die × 4 × 3
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0038 — Set SLC Block Mode Test
- **Feature Name:** SLC Block Mode — verify VU D098 modes 0/1/2 do not disrupt normal SLC/WB reads
- **VU Commands Used:** `project_api.issue_D098_to_set_slc_block_mode(mode)`
- **Key APIs:** `api.get_config_descriptors()`, `api.push_write_config()`, `api.set_flag(FlagIDN.WRITEBOOSTER_EN)`, `ExecuteCMD.Read10()`, `ExecuteCMD.Write10()`, `ExecuteCMD.send(timeout=api.UniformTimeout(val=30000, unit=TimeResolution.ms))`
- **Test Flow:** Config LUN0=EM1(SLC), LUN1=NORMAL(TLC), shared WB=max AU. Write 1 block to SLC LUN0. Enable WB; write 1 block to TLC LUN1. Set mode=0 (D098); read SLC and WB. Set mode=1; read. Set mode=2; read. Verify no errors for all modes.
- **Key Parameters/Data Structures:** D098 modes: 0/1/2; max_wb_size from geometry; slc_au = tlc_au = total_au // 2
- **Exceptions Used:** None explicitly (inherits framework exceptions)

### CustomVU_0039 — Get CIS Block Information Test
- **Feature Name:** CIS (Code Image Storage) Block Information — verify VU 0x40B9 returns correct CIS VB numbers, die numbers, plane numbers, bad-block flags, erase counts, FW image page ranges, and bank page ranges
- **VU Commands Used:** `project_api.issue_40B9_to_get_cis_block_Information()`
- **Key APIs:** `project_api.get_FW_code_physical_address_information()` → CISCode1/CISCode2 block/CE/Plane; `api.get_flash_setting_buffer()`; `api.read_fw_value("gUfsApiStruct.ftl->hidden_area.address[i].u16")`, `api.read_fw_value("gbyUseCode")`, `api.read_fw_value("gUfsApiStruct.ftl->fvl[0]->fpl->code_start_page")`, `api.read_fw_value("gby_code_bank_count")`
- **Test Flow:** step1: (1) Issue 40B9. (2) Check physical_blk_number_of_cis_vb vs CISCode1.Block. (3) Check die/plane/copy numbers. (4) Check bitmap_of_the_copies_pending_on_refresh=0. (5-8) Check cis0/1 bad_blk=0, cis2/3 bad_blk=0xFF. (9-10) Match cis0/cis1 erase counts from hidden_area mapping. (11-13) Check cis2/3 ec_count=0xFFFFFFFF. (14-17) Check FW bank load flags, page start, page end (start+12-1), bank start/end.
- **Key Parameters/Data Structures:** Hidden-area block encoding: block = u16 & 0x1FFF, ce = u16 >> 13; CIS0 block: (CISCode1.Block << 3) + CISCode1.Plane; erase counts at flash_setting_buffer offset 2284 (4 bytes per entry, 8 entries); FW image: pages [code_start_page, code_start_page+11]; bank: [code_start_page+12, ...]
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0040 — Get ASIC Id Test
- **Feature Name:** ASIC ID — verify VU 0x40B3 returns correct NAND die count, controller/NAND type ASCII string, and per-die NAND Flash IDs
- **VU Commands Used:** `project_api.issue_40B3_to_get_asic_id()`
- **Key APIs:** `get_flash_setting()` — for Max_Fdevice (CE count)
- **Test Flow:** step1: (1) Issue 40B3. (2) Verify nand_id_item_count == ce_num. (3) Decode controller_and_nand_type_ascii as little-endian ASCII; expect 'PS8329 B68S'. (4) Per CE: verify die_idx_N.value == CE index (0-3). (5) Verify nand_flash_id_idxN.value == 0x2cd30832e8361200.
- **Key Parameters/Data Structures:** ASICId struct fields: nand_id_item_count, controller_and_nand_type_ascii, die_idx_0/1/2/3, nand_flash_id_idx0/1/2/3; Expected NAND ID: 0x2cd30832e8361200; Expected controller string: 'PS8329 B68S'
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0041 — READ Uid Test
- **Feature Name:** NAND UID — verify VU 0x4061 returns per-die UID matching health report flash IDs, with correct ce/ch/cpu die mapping
- **VU Commands Used:** `project_api.issue_4061_to_get_uid()`
- **Key APIs:** `project_api.get_health_report()` — flash_id_ce0/1/2/3 payloads; `get_flash_setting()` — Max_Fdevice
- **Test Flow:** step1: Get health report; issue 4061; per CE: compare uid.uid_of_physical_dieN.payload vs health_report.flash_id_ceN.payload; verify ce_dieN=N, ch_dieN=0, cpu_dieN=0.
- **Key Parameters/Data Structures:** ReadUid struct: uid_of_physical_die0/1/2/3, ce_die0/1/2/3, ch_die0/1/2/3, cpu_die0/1/2/3
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0042 — Enable/Disable ATS Test
- **Feature Name:** Auto Standby (ATS) Enable/Disable — verify VU D088 can disable ATS (ATS timer stops) and re-enable; validated via SMART info ATS counter at offset 0x4A8
- **VU Commands Used:** `project_api.issue_D088_enable_disable_auto_standby(enable_flag)`
- **Key APIs:** `project_api.get_smart_info()` — ATS timer at [0x4A8:0x4B0] (8 bytes LE)
- **Test Flow:** pre_process: Read initial ATS timer; sleep 15s; check if timer increased to determine current ATS state. If ATS enabled: disable (D088=0), sleep 15s, verify timer NOT increased; re-enable. If disabled: enable (D088=1), sleep 15s, verify timer increased; disable.
- **Key Parameters/Data Structures:** SMART offset 0x4A8, size 8 bytes; ast_sec=15; D088 payload byte[12]: 0=disable, 1=enable
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0043 — Set Manufacture Date Test
- **Feature Name:** Set Manufacture Date — verify VU C04E can update the Device Descriptor w18_manufacturer_date field
- **VU Commands Used:** `project_api.issue_C04E_to_set_manufacture_date(manufacture_date_struct)`
- **Key APIs:** `ExecuteCMD.ReadDescriptor().assign(DescriptorIDN.DEVICE, 0, 0)`, `DeviceDescriptor310.from_bytes()` — w18_manufacturer_date field
- **Test Flow:** pre_process: Read Device Descriptor to capture baseline device_manufacture_date. C04E_test: (1) Set manufacture_date = original + 3; re-read; verify field updated (big-endian). (2) Restore to original; re-read; verify restored.
- **Key Parameters/Data Structures:** ManufactureDate struct: .manufacturedate.value; comparison as 2-byte big-endian int; increase_val=3
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `DLL_RESPONSE_ERROR`

### CustomVU_0044 — Set WWYY Test
- **Feature Name:** Set WWYY (Week/Year manufacturing code) — verify VU C04F can update Device Health Descriptor WWYY field at bytes[5:7]
- **VU Commands Used:** `project_api.issue_C04F_to_set_wwyy(wwyy_struct)`
- **Key APIs:** `ExecuteCMD.ReadDescriptor().assign(DescriptorIDN.DEVICE_HEALTH, 0, 0)`, `DeviceHealthDescriptor310.from_bytes()` — WWYY from resp.data[5:7]
- **Test Flow:** pre_process: Read Health Descriptor to get WWYY baseline. C04F_test: (1) Set wwyy = original + 3; re-read; verify wwyy_from_health_descriptor == original+3. (2) Restore; verify restored.
- **Key Parameters/Data Structures:** WWYY struct: .wwyy.value; Health descriptor WWYY bytes: resp.data[5:7] decoded as big-endian int; increase_val=3
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `DLL_RESPONSE_ERROR`

### CustomVU_0045 — Get All Manufacturing Settings Test
- **Feature Name:** Get All Manufacturing Settings — verify VU 0x4040 returns manufacturer_name, product_name_string, oem_id, product_revision_level, serial_number_string, manufacturer_date, and manufacturer_id matching individual String Descriptor reads
- **VU Commands Used:** `project_api.issue_4040_to_get_all_manufacturing_setting()`
- **Key APIs:** `ExecuteCMD.ReadDescriptor().assign(5, index, ...)` — String Descriptor reads; `DeviceDescriptor310.from_bytes()` — fields b20/b21/b22/b23/b42/w18/w24
- **Test Flow:** pre_process: Read Device Descriptor to capture string indices and manufacture_id/date. test_4040: Read String Descriptors for manufacturer_name/product_name/oem_id/product_revision_level/serial_number; Issue VU 0x4040; Compare each field against String Descriptor data (offset 2 into descriptor).
- **Key Parameters/Data Structures:** AllManufacturingSetting struct: manufacturer_name.payload (16B), product_name_string.payload (32B), oem_id.payload (62B), product_revision_level.payload (8B), serial_number_string.payload (62B), manufacturer_date.value, manufacturer_id.value; String Descriptor payload starts at byte[2]
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `DLL_RESPONSE_ERROR`

### CustomVU_0046 — Set Product Name String Test
- **Feature Name:** Set Product Name String — verify VU C04B can update UFS String Descriptor (IDN=5) for product name
- **VU Commands Used:** `project_api.issue_C04B_to_set_serial_product_string(product_name_struct)`
- **Key APIs:** `ExecuteCMD.ReadDescriptor().assign(5, product_string_name_index, ...)`, `DeviceDescriptor310` — b21_product_name string index
- **Test Flow:** pre_process: Read Device Descriptor; read current product string descriptor (backup). C04B_test: (1) Modify byte[3] by +1; issue C04B; re-read; verify change at offset 2+3. (2) Restore original; issue C04B again; verify descriptor matches backup.
- **Key Parameters/Data Structures:** ProductNameString struct: unicode_string_chracter.payload (32 bytes); setting: descriptor[2:34]; setting_value_offset=3
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `DLL_RESPONSE_ERROR`

### CustomVU_0047 — Set Serial Number String Test
- **Feature Name:** Set Serial Number String — verify VU C04A rejects oversized serial number (65-byte payload → ASC 0x26 error), accepts correct 64-byte payload, restores on recover
- **VU Commands Used:** `project_api.issue_C04A_to_set_serial_number_string(serial_number_struct [, keep_error=True])`
- **Key APIs:** `ExecuteCMD.ReadDescriptor().assign(5, serial_number_index, ...)`, `DeviceDescriptor310` — b22_serial_number string index
- **Test Flow:** C04A_test: (1) Error case: size=65, send with keep_error=True; expect b32_sense_data.b12_asc=0x26; verify descriptor unchanged. (2) Normal case: size=64, modify byte[3]+1; verify descriptor updated. (3) Recover: restore original payload.
- **Key Parameters/Data Structures:** SerialNumberString struct: size_of_descriptor.value, string_type_identifier.value=5, unicode_string_chracter.payload (62 bytes); Max valid size=64, error size=65
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `DLL_RESPONSE_ERROR`

### CustomVU_0048 — Get Nand Temperature Test
- **Feature Name:** NAND Temperature Read — verify VU 0x4021 reflects temperatures set by VU D08A, including per-die NAND temp (+37 offset), error cases for out-of-range values
- **VU Commands Used:** `project_api.issue_4021_get_nand_temperature()`, `project_api.issue_D08A_set_vu_temperature(set_nand_temp_struct)`
- **Key APIs:** `get_flash_setting()` — Max_Fdevice (CE count)
- **Test Flow:** test_4021: (1) Issue 4021 (baseline). (2) Set D08A: bEnableSetVuTemp=1, NAND_TEMPERATURE_DIE=20, Use_Delayed=0. (3) Issue 4021; verify each die=20+37=57. (4) Error: set temp=126; expect DLL_RESPONSE_ERROR. (5) Error: set temp=-38; expect DLL_RESPONSE_ERROR. (6) Restore: bEnableSetVuTemp=0.
- **Key Parameters/Data Structures:** SetNandTemperature struct: bEnableSetVuTemp, NAND_TEMPERATURE_DIE_0/1/2/3, UC_TERMAL_SENSOR_1, Use_Delayed_fake_tmeperatures; GetNandTemperature struct: temperature_of_die_0/1/2/3; Temperature offset: FW adds 37; Valid range: approximately -37 to 125 (exclusive)
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `DLL_RESPONSE_ERROR`

### CustomVU_0049 — Set Nand Temperature Test
- **Feature Name:** Set NAND Temperature + Enhanced Health Report — verify D08A/4021/40FD/40FE interactions: NAND temp, UC temp, highest/lowest lifetime tracking, temperature profile zone counters, temperature delta counters
- **VU Commands Used:** `project_api.issue_D08A_set_vu_temperature()`, `project_api.issue_4021_get_nand_temperature()`, `project_api.issue_40FD_get_uC_temp_value()`, `project_api.issue_40FE_to_read_enhanced_health_report()`
- **Key APIs:** `api.HwSetting.get_instance()`, `hw_setting.set_to_device(POWER_SAVING_CTRL_ENABLE, 0x3A)`, `api.init_tester_to_unit_ready(resetmode=Dcmd5ResetType.HW_RESET, powerdown=True)`
- **Test Flow:** step1: (1) Baseline 4021 and 40FE. (2) Set D08A NAND=20°C, UC=85°C. (3) Verify 4021=57, 40FD=85, 40FE highest=85. (4) Set D08A UC=-25°C; verify 40FD=-25, 40FE lowest=-25. (5) POR; verify highest/lowest kept, power_on_highest/lowest reset. (6) Temperature delta: cycle through 18 gaps; verify delta zone counter incremented. (7) Temperature profile: test 14 boundary temps; verify correct zone counter incremented.
- **Key Parameters/Data Structures:** ReadEnhanceHealthReport: highest_temp, lowest_temp, power_on_highest/lowest_temp, temperature_profile_t_37/37_t_25/25_t_0/0_t_95/95_t_115/t_115, temperature_delta_t_1/1_t_5/5_t_10/10_t_15/t_15; Profile zones: ≤-37, -37 to -25, -25 to 0, 0 to 95, 95 to 115, >115; Delta zones: <1, 1-5, 5-10, 10-15, ≥15
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0050 — FW Event Set Test
- **Feature Name:** FW Event Set (D0FB) — verify VU D0FB can control POWER_ON_WB_EN flag persistence across HW reset, and trigger SCSI command timeout via mode=2
- **VU Commands Used:** `project_api.issue_D0FB_set_fw_state_in_ram(mode)`
- **Key APIs:** `ExecuteCMD.SetFlag().assign(idn=FlagIDN.POWER_ON_WB_EN)`, `ExecuteCMD.ReadFlag().assign(idn=FlagIDN.POWER_ON_WB_EN)`, `api.init_tester_to_unit_ready(Dcmd5ResetType.RESET_N)`, `api.TIMEOUT_EXCEPTIONS`
- **Test Flow:** test_D0FB: (1) Set POWER_ON_WB_EN=1; D0FB mode=0 (no-save); RESET_N; verify flag still=1. (2) D0FB mode=1 (clear); RESET_N; verify flag=0. (3) D0FB mode=2 (trigger ISR); expect TIMEOUT_EXCEPTION; then verify ReadFlag also times out; HW_RESET to recover.
- **Key Parameters/Data Structures:** D0FB modes: 0=no state change, 1=clear POWER_ON_WB_EN after reset, 2=trigger ISR/timeout; FlagIDN.POWER_ON_WB_EN
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `api.TIMEOUT_EXCEPTIONS`

### CustomVU_0051 — Get FTL Block List Information
- **Feature Name:** FTL Block List (VU 0x4099) — verify VU 0x4099 (param0=0) returns correct per-VB-group block head/tail/count matching VU 0x406D data
- **VU Commands Used:** `issue_4099_to_get_ftl_blk_list(param0)`, `project_api.issue_406D_get_VB_list_info()`
- **Key APIs:** `vendor_cmd.direct_read(pca, block_count, include_FW_spare=True)`, `api.get_fw_geometry()` — l52_total_vb_count
- **Test Flow:** test_4099: (1) Issue 406D; parse into list[BlockInfo] (cnt, head, tail per group). (2) Issue 4099 (param0=0). (3) Compare: per group: 4099 entry at offset N×12 bytes (head=+0, tail=+4, cnt=+8); if group non-empty verify match; if empty verify cnt=0 or 0xFFFFFFFF and head/tail=0xFFFFFFFF. (4) Verify remaining payload bytes = all 0xFF.
- **Key Parameters/Data Structures:** GetBlkList struct: payload with head(4B)+tail(4B)+count(4B) per group, stride=12 bytes; BlockInfo local class: blk_cnt, blk_head, blk_tail; MmesgBlkLocation: raw 32-bit → block[0:10], die[11:13], plane[14:16], pb_status[17:18]
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0053 — Set/Get NAND Trim Test
- **Feature Name:** NAND Trim Parameters — verify VU 0x4084 reads correct default trim values; VU C084 sets new values; 0x4084 reads back set values; C084 restores defaults
- **VU Commands Used:** `project_api.issue_4084_to_get_NAND_trim(target_addr=[addr])`, `project_api.issue_C084_to_set_NAND_trim(set_dict)`
- **Test Flow:** step1: For each addr in default_value: issue 4084; verify TrimValue[0].value == default_value[addr]; backup. step2: Issue C084 with set_dict. step3: Issue 4084; verify each address value matches set_dict. step4: Issue C084 with backup (restore originals).
- **Key Parameters/Data Structures:** default_value = {0x4A2: 0x3, 0x4A3: 0x1, 0x4A4: 0x4, 0x4A5: 0x1, 0x6FF: 0x0}; set_dict = {0x4A3: 10, 0x4A4: 20, 0x4A5: 30}; GetNANDTrimResult struct fields: GetTrimItemCnt.value, TrimValue[N].value
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0054 — Error Bits and Read Retry Step Test
- **Feature Name:** ECC Error Bits & Read Retry (REH) — verify VU 409E (ECC info + error bits), VU D014 (set read recovery), VU 40BB (error bits + read retry step), and VU 4066 (sticky read) produce consistent results across LUN0 (TLC) and LUN1 (EM1/SLC)
- **VU Commands Used:** `issue_409E_to_get_ECC_information()`, `issue_409E_to_get_error_bit_numbers()`, `issue_D014_to_set_read_recovery_module()`, `issue_D014_to_set_last_table_content()`, `issue_40BB_to_get_error_bit_numbers_and_read_retry_step(die)`, `issue_4066_force_current_read_last_as_sticky_read()`, `issue_4066_to_dis_en_sticky_read()`, `issue_4051_to_get_physical_address()`, `issue_4060_to_read_raw_data()`
- **Key APIs:** `api.sequential_write()`, `create_read_last_ref_table(max_die)`, `set_read_last_table(maxDie, table)`, `iter_reh_steps(type=BLOCK_PAGE_TYPE)`, `push_write_config()`, `api.update_descriptor()`
- **Test Flow:** step1: (1) Config LUN0=NORMAL, LUN1=EM1. (2) Sequential write both LUNs. (3) Issue 409E mode=0 → verify cw_size=4096, max_error_num=320. (4) Set read-last table (D014 op2). (5) For each LUN: (6) 4066 force current read-last as sticky-read. (7) Enable sticky read. (8) Loop REH steps: D014 op0 set step; read data; 40BB: check b=0,s≠0 LUN0→reRead good/readLast=0x3FFF; b=1 LUN0→readLast good/reRead=0x3FFF; b≥2→both 0x3FFF. (9) Loop all REH steps: 40F9 and 40BB compare error_bits. (10) Disable sticky read.
- **Key Parameters/Data Structures:** 40BB output: reReadResult, reReadErrorBits, reReadBigStep, reReadSmallStep, readLastResult, readLastErrorBits, readLastBigStep, readLastSmallStep, errorBitNumber1/2/3/4; 409E output: errorBitNumber1/2/3/4; 0x3FFF = "invalid/no error" sentinel; READ_LAST_TABLE.LAST_TABLE_1/2; STICKY_READ_STATUS.FAILED
- **Exceptions Used:** `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`

### CustomVU_0055 — PTE Recovery Related
- **Feature Name:** PTE Recovery — verify VU 0x40F5 sub-opcodes 1-6 for VB classification (free vs. used), UECC detection, and VB group transfer (used→free)
- **VU Commands Used:** `issue_40F5_to_PTE_Recovery(opcode, vb_index)`
- **Key APIs:** `api.ufs_api.vendor_cmd.functions.get_vb_info()`, `vendor_cmd.direct_read(pca, 1, include_FW_spare=True)`, `vendor_cmd.direct_write(pca, 1, write_buffer)`, `project_api.issue_40DC_to_get_next_open_vb_information(0)`, `project_api.issue_4051_to_get_physical_address()`, `ExecuteCMD.Unmap()`, `ExecuteCMD.SetFlag().assign(FlagIDN.PURGE_EN)`
- **Test Flow:** pre_process: Erase all card (Unmap + Purge); write 256 4K-blocks; opcode5 → expect 0 (no UECC). Write full TLC VB; inject UECC via direct_write; opcode6 to transfer to free list; direct_read to confirm UECC bit4=1. sub_opcode1_test: Get free VB (group 27) and used VB (group 17); opcode1(free_vb)=1, opcode1(used_vb)=2. sub_opcode2-4_test: Similar. sub_opcode6_test: opcode6 → expect=1; verify VB moves from group 17 to group 27.
- **Key Parameters/Data Structures:** VB group encoding (2-byte): bits[5:0]=group, bits[7:6]=access_mode, bit[8]=dirty; Group 17=used/MLC, Group 27=free queue MLC; 40F5 return codes: opcode1/2: 1=in-free-list, 2=in-used-list; opcode3/4: 1=success; opcode5: 0=no UECC, 1=UECC found; opcode6: 1=success; spare status byte offset: payload[128 + N * DATA_SIZE_4K_BYTE]; bit4=1 means UECC/blank/invalid
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT`

### CustomVU_0056 — Get Read Recovery Statistics Test
- **Feature Name:** ERS (Error Recovery Statistics) verification — validates ERS counters increment correctly after REH steps applied
- **VU Commands Used:** `issue_40BA_to_get_error_recovery_statistics`, `issue_4051_to_get_physical_address`, `issue_D014_to_set_read_recovery_module`, `issue_D014_to_set_last_table_content`, `issue_40F9_to_get_rr_number_and_error_bits`, `issue_4014_to_get_read_recovery_info_read_last`
- **Key APIs:** `api.sequential_write`, `create_read_last_ref_table`, `set_read_last_table`, `iter_reh_steps`, `get_error_recovery_record_by_index`, `ExecuteCMD.Read10`
- **Test Flow:** step1: Configure LUN0 as normal; verify initial ERS all-zero; write 1 VB; randomly select LBA; get PBA via 4051; set read-last table (D014 op2); get backup ERS; iterate all REH big/small steps: set recovery module (D014), read, get ERS (40BA); compare each ERS entry > backup.
- **Key Parameters/Data Structures:** ERROR_RECOVERY_STATISTICS_RECORD (offset, occupies); PAGE_TYPE, BLOCK_PAGE_TYPE, NAND_MODE; tlc_vb_size = fw_geometry.l88_vb_size_u1 * 512 // 4096
- **Exceptions Used:** `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`

### CustomVU_0057 — Get VDET Information Test
- **Feature Name:** VDET (Voltage Detection) — verify VCC/VCCQ voltage drop events counted correctly; disabling VDET suppresses counting
- **VU Commands Used:** `issue_4073_get_ONFI_speed`, `issue_40B8_to_get_VDET_information`, `issue_D074_to_disable_VDET`
- **Key APIs:** `lib.PowerChannel.VCC/VCCQ`, `lib.VoltageChannel`, `sdk.switch_voltage_value`, `api.init_tester_to_unit_ready`, `ExecuteCMD.StartStopUnit`
- **Test Flow:** step1: Confirm ONFI frequency=1600. step2: Drop VCC+VCCQ → verify counts increased; drop VCCQ only → VccDropCnt unchanged. step3: HW reset; disable VDET (D074) → drop → counts unchanged. step4: HW reset → drop without disabling → counts increased.
- **Key Parameters/Data Structures:** VccDropCnt, VccqDropCnt from 40B8; VCCQ voltage thresholds: 1.08V, 1.15V, 1.3V; VCC: 2.1V, 2.5V
- **Exceptions Used:** `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`

### CustomVU_0058 — Get ERS Read Pass Counter Test
- **Feature Name:** ERS Read Pass Counter — ERS index 65 (Default Read Pass Count) and index 66 (Sticky Read Pass Count) increment under D019 enable/disable; counts non-persistent after power cycle
- **VU Commands Used:** `issue_40BA_to_get_error_recovery_statistics`, `issue_D019_to_en_dis_success_read_count`, `issue_4066_to_dis_en_sticky_read`, `issue_4066_force_current_read_last_as_sticky_read`, `issue_4051_to_get_physical_address`, `issue_4052_to_get_logical_address`, `issue_C088_to_start_or_stop_refresh`
- **Test Flow:** step1: Stop refresh; write 1 VB; get PBA; loop DEFAULT_READ_PASS_CASE and STICKY_READ_PASS_CASE: enable D019; optionally enable sticky read; loop all block/page types: host read; get ERS; verify index-65 increments (default) or both 65/66 increment (sticky); then disable D019 and verify no increment; verify after power cycle counts non-persistent.
- **Key Parameters/Data Structures:** ERSIndex.DEFAULT_READ_PASS_COUNT=65, ERSIndex.STICKY_READ_PASS_COUNT=66; STICKY_READ_SETTING.ENABLE/DISABLE; ReadCountTest enum
- **Exceptions Used:** `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`

### CustomVU_0059 — Codeword Buffer To Save REH Info Test
- **Feature Name:** Codeword Buffer Allocation/Release for REH Tracing — verify D014 option 7 (alloc/release codeword buffer) gates REH tracing data and SURE ARC data visibility
- **VU Commands Used:** `issue_D014_to_alloc_release_codeword_buffer_to_save_REH_info`, `issue_4014_to_get_REH_tracing_info`, `issue_4014_to_get_sure_ARC_data`, `issue_4060_to_read_raw_data`, `issue_C060_to_write_raw_data`, `issue_D060_to_erase_specific_block`
- **Test Flow:** step1: Stop refresh; write LUN0 and LUN1; verify D014 op7 release without prior alloc → expect TARGET_FAILURE; set read-last table; for each LUN and block/page type: alloc codeword buffer (action=0); verify REH tracing empty; verify SURE ARC empty; generate read fails; verify REH tracing non-empty; verify SURE ARC non-empty; release (action=1); verify both empty again.
- **Key Parameters/Data Structures:** LUN0=normal/TLC, LUN1=EM1/SLC; write data pattern=0xAA; SLC page size=16K+16*4 bytes; TLC LP/MLC/TLC sizes; UPIUResponse.TARGET_FAILURE for error case
- **Exceptions Used:** `SIGHTING_RESPONSE_UNEXPECTED`, `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`

### CustomVU_0060 — Read/Write RAM CSR Test
- **Feature Name:** RAM/CSR Read-Write — verify FW SRAM and MRAM can be read/written via VU 0x4027 (read) and 0xC0F0 (write)
- **VU Commands Used:** `project_api.issue_C0F0_write_RAM_CSR`, `project_api.issue_4027_read_SRAM_CSR_data`
- **Test Flow:** step1: Disable HW suspend; write 0x5A5A5A5A to SRAM address 0x7FDA8000 (VU C0F0); read back (VU 4027) and verify; iterate valid read regions (ICCM+ROM 0x0-0x33FFF, COP0 0x4C1xxxxx, MRAM 0x7FDAxxxx, DCCM 0x80xxxxxx) reading start/mid/end addresses.
- **Key Parameters/Data Structures:** Write segment: (0x7FDA8000, 0x7FDA8003); write data=b'\x5A'*4; count_of_byte=4; HwSettingField.POWER_SAVING_CTRL_ENABLE=0x3A
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0061 — Get CS/ICS/HGB Info
- **Feature Name:** CS/ICS/HGB boundary information — validates VU 4087 (CS/ICS info) and 4004 (boundary blocks) against FW internal values
- **VU Commands Used:** `project_api.issue_4087_get_ics_cs_info_description()`, `project_api.issue_4004_get_boundaryblocks_for_hiddentable_static_dynamicpool()`
- **Key APIs:** `api.read_fw_value` for: total_vb, lc_per_page, bbt.max_revoke_cnt, bbt.revoke_cnt, bbt.bbt_info_ce[].bbt_info[].bad_blk_cnt
- **Test Flow:** test_4087: Issues 4087 and 4004; reads FW values; verifies number_of_ics_table == ics_bound - spare_bound; max_number_of_cs == total_vb - number_of_ics_table; number_of_early_bb_at_t0 == sum of bad_blk_cnt; remaining_cs formula.
- **Key Parameters/Data Structures:** GetCSICSInfoDescription: number_of_ics_table, max_number_of_cs, number_of_early_bb_at_t0, remianing_cs_at_run_time; GetBoundaryBlocksForHiddenTableStaticDynamicPool: ics_bound_ce0plane0, spare_bound_ce0plane0
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0062 — Get Boundary Blocks For Hidden/Static/Dynamic Pool Test
- **Feature Name:** Block pool boundary verification — validates VU 4004 boundary values match FW internal pointer variables
- **VU Commands Used:** Same as 0061
- **Key APIs:** `api.read_fw_value` for: bbt.bbt_info_ce[].bbt_info[].hidden_bound, bbt.pivot (spare_bound), bbt.last_bbs_vb (ics_bound), bbt.last_tbl_pool_vb (table_bound), bbt.last_slc_pool_vb, bbt.user_floor (dynamic_bound0), bbt.user_ceil (dynamic_bound)
- **Test Flow:** test_4004: for each CE/plane reads FW bbt_info fields and compares against payload offsets (0×48=hidden, 1×48=spare, 2×48=ics, 3×48=table, 4×48=slc_pool, 5×48=dynamic_floor, 6×48=dynamic_ceil).
- **Key Parameters/Data Structures:** Payload layout: 7 regions × 48 bytes each (6 CE×planes × 2 bytes each); ENG3 offset correction (+1) for hidden/spare/dynamic; dynamic compares as (value - spare_bound)
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0063 — Invalid Table Cache Test
- **Feature Name:** Table Cache Invalidation (PTE/PMD) — verify VU D08C causes measurable read latency increase
- **VU Commands Used:** `project_api.issue_D08C_to_invalid_table_cache(rainEnable=1/2/3)`
- **Key APIs:** `ExecuteCMD.Read10()`, `ExecuteCMD.Write10()`, `api.UniformTimeout(val=30000, unit=TimeResolution.ms)`, `response.l59_resp_timestamp - response.l54_cmd_timestamp`
- **Test Flow:** step1: Disable ATS; write 1G data; random read 1G twice (baseline avg); D08C invalidate PTE (rainEnable=1); random read — verify time > baseline; D08C invalidate PMD (rainEnable=2); D08C invalidate both PTE+PMD (rainEnable=3) — verify time > baseline.
- **Key Parameters/Data Structures:** BLOCK4K_SIZE_1G_BYTE; read timing from response timestamps; api.TimeResolution.ms
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0066 — Get Bad Block Count Test
- **Feature Name:** Bad Block Count verification — validates VU 40C8 bad block count against actual BBT parsed from direct NAND read (spare mark 0x8B)
- **VU Commands Used:** `project_api.issue_40C8_to_get_bad_blocks_count()`
- **Key APIs:** `api.get_fw_geometry()`, `api.get_flash_setting()`, `api.direct_read(pca, block_count=4, include_FW_spare=True)`, PCA struct
- **Test Flow:** step1: Issue 40C8 to get bad block count per CePlane. step2: Scan all blocks/CEs/planes via direct_read; identify BBT block by spare mark 0x8B at DATA_SIZE_4K_BYTE*4+4; parse BBT bitmap. step3: Verify total BB count from 40C8 matches bitmap count; verify per-CePlane counts match.
- **Key Parameters/Data Structures:** PCA struct: l0_op, b4_mode, b5_ce, b6_plane, b10_block_l, b11_block_h, l12_fpage, b20_lmu; BBT marker = 0x8B; bad block type bit check: data[offset] >> 4*(plane%2) & 0xF bit2 set
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `SIGHTING_PBA_UNEXPECTED`

### CustomVU_0067 — Direct Read/Write Data
- **Feature Name:** Direct NAND Mode Read/Write — validates direct erase/write/read operations in SLC and TLC modes via VUs 40F6/40F7/40F8
- **VU Commands Used:** `project_api.issue_40F6_to_erase_in_direct_nand_mode_1(die_bitmask, plane_bitmask, block_start, block_end, slc_mode)`, `project_api.issue_40F7_to_write_raw_data_in_direct_nand_mode(die_bitmask, plane_bitmask, block_start, block_end, page_start, page_end, slc_mode, pattern)`, `project_api.issue_40F8_to_read_in_direct_nand_mode(die_bitmask, plane_bitmask, block_start, block_end, page_start, page_end, slc_mode)`
- **Test Flow:** step1 (SLC mode): erase block 100 (SLC=1); iterate pages 0-1103 step 10; write pattern; read back; compare against pattern * 4096. step2 (TLC mode): erase block 100 (SLC=0); iterate pages 0-3311 handling region boundaries; write+read+compare.
- **Key Parameters/Data Structures:** pattern_array = [0xABCDABCD, 0x5A5A5A5A, ...]; MAX_PAGE_SLC=1103, MAX_PAGE_TLC=3311; page regions: TLC LP 0-1619 (groups of 3), MLC 1620-1651 (groups of 2), TLC 1652-3307 (groups of 3), last 3308-3311 (single); page size 16384+64 bytes
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0068 — Erase Fail Test
- **Feature Name:** Erase Fail injection and BBT update verification
- **VU Commands Used:** `project_api.issue_40C1_to_get_open_vb_information()`, `project_api.issue_40DC_to_get_next_open_vb_information()`, `project_api.issue_405E_to_get_bad_block_information()`, `project_api.issue_C012_to_create_program_erase_fail(fail_type=1)`, `project_api.issue_4013_to_get_BE_fail_status()`
- **Test Flow:** step1: Get current/next L2 VB; record BB count; inject erase fail on next L2 VB (C012, fail_type=1); write until L2 VB changes; get BE fail status (4013); verify fail_type==2, fail_times>0, address fields match; verify BBT count increased by 1.
- **Key Parameters/Data Structures:** fail_type=1 for erase fail → 4013 returns fail_type=2; L2_vb_next = next_open_vb_information.DM_NORMAL_HOST_VB.value
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0069 — Program Fail Test Block Base
- **Feature Name:** Program Fail injection (block-base) — inject program fail on current L2 VB and verify 4013 and BBT update
- **VU Commands Used:** Same as 0068 except `fail_type=0`
- **Test Flow:** Get current L2 VB; record BB count; inject program fail (C012, fail_type=0); write one chunk; get 4013 (fail_type==1); verify BBT +1.
- **Key Parameters/Data Structures:** fail_type=0 for program fail → 4013 returns fail_type=1
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0070 — Erase on Direct NAND Mode
- **Feature Name:** Direct NAND mode erase verification — erase via VU 40F6; verify ERASE status bit in spare area
- **VU Commands Used:** `issue_40F6_to_erase_in_direct_nand_mode(ce_bit, plane_bitmask=3, blk, blk+1, slc_enable=0)`, `vendor_cmd.direct_read(pca, block_count=1, include_FW_spare=True)`
- **Test Flow:** pre_process: Write 1.5 TLC VBs; get PCA from LBA 0; issue 40F6 to erase all CEs/planes of block; direct_read; verify bit3 set in payload[128 + DATA_SIZE_4K_BYTE]: (payload[128 + DATA_SIZE_4K_BYTE] & 0x08) != 0.
- **Key Parameters/Data Structures:** PCA: b10_block_l, b11_block_h, b5_ce, b6_plane; ce_bit accumulation over Max_Fdevice; plane_bitmask=3
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0071 — Erase/Write/Read Raw Data Test
- **Feature Name:** Raw data erase/write/read cycle — uses VUs D060 (erase), C060 (write raw), 4060 (read raw) to test raw data integrity
- **VU Commands Used:** `project_api.issue_4051_to_get_physical_address()`, `project_api.issue_4060_to_read_raw_data()`, `project_api.issue_D060_to_erase_specific_block()`, `project_api.issue_C060_to_write_raw_data()`, `project_api.issue_40C7_to_get_bad_block_info()`
- **Test Flow:** step2: For each PCA (TLC and SLC): find remap block (40C7); get physical layout; read raw (4060 ECC on) verify read_status==0; erase (D060); verify read_status==1 (Empty); write all-0xAA (C060); read back verify read_status==0 and data==0xAA.
- **Key Parameters/Data Structures:** Read status at payload[0x4000:0x4004]: b'\x00\x00\x00\x00'=normal, b'\x01\x01\x01\x01'=empty; SLC write size=DATA_SIZE_16K_BYTE, TLC write size=DATA_SIZE_20K_BYTE*3
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0073 — Disable REH Step and Read Error Bits Test
- **Feature Name:** REH step disable mask verification — when a specific REH big/small step is disabled via D014 op1, corresponding ECC error number reads zero while other steps remain non-zero
- **VU Commands Used:** `issue_D014_to_en_dis_read_recovery_module(pageType, bigStepBitMap, disSmallMap)`, `issue_4014_to_get_ecc_result_for_all_step(die)`, `issue_40F9_to_get_rr_number_and_error_bits()`
- **Test Flow:** step1: Config LUNs; stop refresh; write LUN0 and LUN1; set read-last table; enable sticky read; alloc codeword buffer; for each LUN and block/page type: for each disabled mask (cb, cs): issue D014 op1 to mask step; loop all REH steps: set recovery module; get LBA (4052); read; get error bits (40F9) and ECC result (4014 op2); verify masked step has all-zero error number, others have non-zero < 0x3FFF; release codeword buffer.
- **Key Parameters/Data Structures:** disBigMap/disSmallMap bitmaps; error_number per plane; masked step expect all 0, others expect non-zero and < 0x3FFF
- **Exceptions Used:** `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH`

### CustomVU_0074 — Dump VT Distribution Test
- **Feature Name:** VT Distribution verification — validates VU 401D (get_vt_distribution) returns bit-one counts within ±10% of raw NAND data counts across different DAC trim settings
- **VU Commands Used:** `project_api.issue_401D_to_get_vt_distribution(die, plane, block, page_order, isSLC, offset, min_dac, max_dac, 0)`, `project_api.issue_4084_to_get_NAND_trim(target_addr)`, `project_api.issue_C084_to_set_NAND_trim(set_dict)`, `issue_4060_to_read_raw_data()`
- **Test Flow:** step1: Config LUNs; stop refresh; disable ATS; write TLC and SLC VBs; for each LUN and page_type: pick 3 DAC values; get PBA; backup trim; optionally pre-set TLC 0xD8=0xDA; for each DAC value: set NAND trim; read raw (4060 ECC off); count bit-ones; restore trim; issue 401D; compare vs raw bit-one counts (±10%).
- **Key Parameters/Data Structures:** set_trim_address: PAGE_POR_DSLC→[0x11E, 0x114], SLC_LP→[0x126], MLC_LP→[0x110], TLC_LP→[0xB0]; node=4588 bytes; DAC range 0-0xDA; Tolerance: ±10%
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0075 — Program Fail Test Page Base
- **Feature Name:** Program Fail injection (page-base, TLC) — inject program fail at specific logical page within open TLC VB
- **VU Commands Used:** `project_api.issue_405E_to_get_bad_block_information()`, `project_api.issue_C012_to_create_program_erase_fail(fail_type=3)`, `project_api.issue_4013_to_get_BE_fail_status()`
- **Key APIs:** `ExecuteCMD.Write16` (not Write10); `OpenVBInfo` struct; page region translation logic
- **Test Flow:** step1: Get open VB info (TLC_L2); extract L2 VB and first_empty_physical_page; record BB count; translate physical page to logical page via region boundaries [0-1619 LP, 1620-1651 MLC, 1652-3307 TLC, 3308-3311]; inject program fail at logical_page+1 (C012, fail_type=3); write large chunk (Write16); get 4013; verify; verify BBT +1.
- **Key Parameters/Data Structures:** region_max_wl = [540, 556, 1108]; page boundaries: 1620, 1652, 3308, 3312; fail_type=3; info.BlockInfoList_0_page.value = logical_page + 1
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0076 — Get Bad Block Info Test
- **Feature Name:** Bad Block Info per physical block (40C7) — validates initial conditions (no later bad blocks), then erase/program fail tests verifying 40C7 counters and 405E BBT update
- **VU Commands Used:** `project_api.issue_405E_to_get_bad_block_information()`, `project_api.issue_40C7_to_get_bad_block_info()`, `project_api.issue_40C1_to_get_open_vb_information()`, `project_api.issue_40DC_to_get_next_open_vb_information()`, `project_api.issue_C012_to_create_program_erase_fail()`, `project_api.issue_4013_to_get_BE_fail_status(1)`
- **Test Flow:** step1: Verify initial state — later_VB_count==0, program/erase fail max counts==0; iterate all physical blocks via 40C7 and verify status matches 405E BBT. step2: Erase fail → verify BBT +1; 40C7 later_VB_count+1, later_VB_max_count-1, later_erase_fail_VB_max_count+1. step3: Program fail → same verification pattern.
- **Key Parameters/Data Structures:** BB_info fields: later_VB_count, later_VB_max_count, later_program_fail_VB_max_count, later_erase_fail_VB_max_count, early_pool_physical_VB_count, status (0=good, 1=bad), replaced_physical_block (0xFFFFFFFF=no remap); flash_setting.Max_PB
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0077 — Get Predicted Next N Replacement Block Test
- **Feature Name:** Predicted Replacement Block verification (user pool) — predict next replacement block via VU 40D6, trigger erase fail, verify predicted block is now logical VB via 40C9
- **VU Commands Used:** `project_api.issue_40D6_to_get_predicted_next_n_replacement_block(ce, plane, next_n=1, pool_type=1, is_CIS=0, pf_on_open_data=0)`, `project_api.issue_40C9_to_get_logical_vb(physical_block, plane)`, `project_api.issue_C012_to_create_program_erase_fail(fail_type=1)`
- **Test Flow:** step1: Get current/next L2 VB; record BB count; predict replacement block via 40D6 (pool_type=1); get its logical VB (40C9); inject erase fail on next L2 VB; write until L2 VB changes; get 4013; verify BBT +1; re-query 40C9 for replacement block and verify it now maps to failed L2 VB.
- **Key Parameters/Data Structures:** 40D6 params: ce=0, plane=0, next_n=1, pool_type=1, is_CIS=0, pf_on_open_data=0
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0078 — Get Predicted Next N Replacement Block Test (Hidden Area)
- **Feature Name:** Predicted Replacement Block for hidden area (pool_type=2) — inject erase fail on both L2 VB and predicted replacement simultaneously
- **VU Commands Used:** Same as 0077 with `pool_type=2`, `block_info_list_count=2`
- **Test Flow:** Get L2 VB and next L2 VB; predict replacement (40D6, pool_type=2); decode block/plane/ce from 32-bit result: block=(result & 0xFFFFFFE0) >> 5, plane=(result & 0x1C) >> 2, ce=result & 0x03; inject erase fail on both (C012 with block_info_list_count=2); write until L2 VB changes; verify BBT +2.
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0079 — Get Params of FTL Status
- **Feature Name:** FTL Status Parameters — comprehensive FTL status monitoring via VU 40C3 covering multiple sub-tests: discard count, erase count, refresh count, BFEA scan, GC info, APL book VB count, SPOR write fail count, one-shot table defrag count, media scan, XTEMP, reh_book_vb_count
- **VU Commands Used:** `project_api.issue_40C3_value (get_40C3_value helper)`, `project_api.issue_40C1_to_get_open_vb_information()`, `project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh()`, `project_api.issue_40B0_Bfea_Scan()`, `project_api.issue_D088_enable_disable_auto_standby()`, `project_api.issue_D08A_set_vu_temperature()`, `project_api.get_mConfig_data()`, `project_api.set_mConfig_data()`, `issue_4060_to_read_raw_data()`, `issue_C060_to_write_raw_data()`, `issue_D060_to_erase_specific_block()`
- **Key APIs:** `api.sequential_write()`, `api.random_write()`, `api.read_compare()`, `api.write_attribute()`, `api.set_flag()`, `api.lba_to_pba()`, `api.get_fw_assert_number()`, `ExecuteCMD.Unmap()`
- **Key Parameters/Data Structures:** mConfig fields: MANDATORY_WL_15, FB_SCAN_WL_MIN, PB_SCAN_PAGE, FB_SCAN_WL_MAX, XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_Refresh_T1/T2; VERIFY_METHOD enum: EQUAL=0, GREATER=1, NOT_EQUAL=2; PowerLossFlag, OpenDataVBType, OpenSystemVBType enums
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT`, `SIGHTING_RESPONSE_UNEXPECTED`, `DLL_CRC32_COMPARE_FAIL`

### CustomVU_0081 — Get/Set Device Safe Mode State
- **Feature Name:** Device Safe Mode — verify VU D089 (set safe mode) and VU 40A0 (get safe mode) behavior; mode 0=off/success; mode 1/2=FW timeout requiring MP recovery; invalid mode 3-255=error
- **VU Commands Used:** `project_api.issue_40A0_get_device_safe_mode_state()`, `project_api.issue_D089_set_safe_mode(setting_mode)`
- **Key APIs:** `api.MP().execute()`, `api.first_init_to_max_hs_gear()`, `api.get_fw_assert_number()`, `ExecuteCMD.clear()`
- **Test Flow:** step1: Get 40A0 (expect 255=default); issue D089 with random mode 3-255 (expect error DLL_RESPONSE_ERROR); get 40A0 (expect 0); set mode 0 → success; set mode 1 → expect G_TIMEOUT_ALL; get assert number; MP recovery; verify payload[0]==0; set mode 2 → expect G_TIMEOUT_ALL; MP recovery.
- **Key Parameters/Data Structures:** Safe mode values: 0=off, 1=safe_mode_1 (timeout), 2=safe_mode_2 (timeout), 3-255=illegal
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `DLL_RESPONSE_ERROR`, `G_TIMEOUT_ALL`

### CustomVU_0082 — Clear SSR Temp History
- **Feature Name:** SSR Temperature History clear — verify VU D011 clears temperature profile buckets in enhanced health report (40FE); power cycle restores non-zero data
- **VU Commands Used:** `project_api.issue_40FE_to_read_enhanced_health_report()`, `project_api.issue_D011_clear_ssr_temp_history()`
- **Key APIs:** `api.init_tester_to_unit_ready(Dcmd5ResetType.HW_RESET)`
- **Test Flow:** step1: Get health report; issue D011; get health report again; verify all 6 temperature profile buckets are zero; power cycle (HW_RESET); get health report; verify at least one bucket is non-zero.
- **Key Parameters/Data Structures:** Health report fields: temperature_profile_t_37, temperature_profile_37_t_25, temperature_profile_25_t_0, temperature_profile_0_t_95, temperature_profile_95_t_115, temperature_profile_t_115
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0083a — Get BEC Histograms
- **Feature Name:** BEC (Bit Error Count) Histogram verification — flip specific error bits in TLC block, trigger media scan via VU 4028, reset BEC histogram via 4026, re-trigger and verify histogram bin counts match injected error level
- **VU Commands Used:** `project_api.issue_4026_to_get_BEC_histograms_information(reset_enable=0/1)`, `project_api.issue_4028_to_get_media_scan_without_dm(parm)`, `project_api.issue_C08B_to_enable_diable_media_scan()`, `issue_4060_to_read_raw_data()`, `issue_409E_to_get_error_bit_numbers()`
- **Test Flow:** step2: For each flipbit in [0, 4, 8, ..., 380]: config LUN and write TLC CE-page; inject flipbit count errors on TLC page; reset BEC histogram (4026 reset_enable=1) verify all-zero; trigger media scan (4028 on TLC block LP page); re-read histogram; verify: flipbit≤8→bins 0-2 total=4; flipbit≥320→bin80=4; otherwise bin near expected=1.
- **Key Parameters/Data Structures:** micron_vu_4028_param: d16_die, d20_plane, d24_block, d28_page, b40_slc_mode=0, b41_bfea_bin=0, b42_page_attr=3(TLC_LP), b43_is_blank_page=0, b44_is_partial_block=1, b45_is_em1_vb=0; histogram: 95 bins × 4 bytes each (per die); bin = error_bits/4
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0083b — Manufacture Set Production FW Signature State
- **Feature Name:** Production FW Signature State / VU Illegal Test — all VUs return "Invalid CDB" (ASC=0x24) when device is in production state
- **VU Commands Used:** `project_api.issue_40E2_to_get_device_state()`, `project_api.issue_406D_get_VB_list_info()`; tests ~100+ VU IDs in no_data/data_in/data_out categories
- **Test Flow:** step1: Issue 40E2 to get device state; if state==0: issue 406D; else: run issue_vu_illegal_test() which iterates 3 lists of VU IDs and verifies each returns TARGET_FAILURE + CHECK_CONDITION + ASC=0x24.
- **Key Parameters/Data Structures:** no_data_list (~40 VU IDs D00D-D0FE), data_in_list (~70 VU IDs 400F-4004), data_out_list (~25 VU IDs C012-C0F7); check: b6_response=TARGET_FAILURE, b12_asc=0x24
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0084 — Force Trigger Media Scan
- **Feature Name:** Force Trigger Media Scan — verify VU 4028 returns expected media scan status codes (1-16) for different injection scenarios
- **VU Commands Used:** `project_api.issue_4028_to_get_media_scan_without_dm(parm)`, `project_api.issue_C08B_to_enable_diable_media_scan()`, `project_api.issue_D08A_set_vu_temperature()`, `project_api.issue_D08E_to_change_media_scan_thresholds()`, `issue_4051_to_get_physical_address()`, `issue_4060_to_read_raw_data()`, `issue_C060_to_write_raw_data()`, `issue_D060_to_erase_specific_block()`
- **Test Flow:** step2: Multiple sub-scenarios each returning different MEDIA_SCAN_STATUS codes: 1=WRONG_PAGE_ATTR, 2=BLOCK_WRONG_EMPTY_PAGE, 3=WRONG_PAGE_FOR_VALLEY_CHECK, 4=BLOCK_FOLD_FOR_MLCLP_BEC, 6=BLOCK_FOLD_FOR_VRLC_UECC (flipbit=380), 7=BLOCK_FOLD_FOR_DIFFEC (flipbit=150×4 blocks), 8=BLOCK_FOLD_FOR_TEMP (set NAND temp=20, XTEMP_TH=1), 11=BLOCK_FOLD_EMPTY_FOR_EPC, 13=BLOCK_UNFOLD_FOR_GOOD_BEC, 14=BLOCK_UNFOLD_FOR_TEMP, 15=BLOCK_UNFOLD_FOR_VALLEY_OFFSET_CENTER_EC, 16=BLOCK_UNFOLD_EMPTY.
- **Key Parameters/Data Structures:** micron_vu_4028_param: b42_page_attr (0=SLC,1=MLC_LP,2=MLC_UP,3=TLC_LP,4=TLC_UP,5=TLC_XP); micron_vu_D08E_param: b21_xtemp_th_delta_slc, w16_valley_center_ecth_slc, w18_valley_diffec_th_slc, b22_is_partial_block, b23_is_em1; MEDIA_SCAN_STATUS enum
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0085 — Get Media Scan Parameters
- **Feature Name:** Media Scan Parameters Get (40CF) — verify media scan cycles through VB groups in expected scan map order, controlled by C085 spend-time triggers
- **VU Commands Used:** `project_api.issue_C08B_to_enable_diable_media_scan()`, `project_api.issue_C085_to_set_media_scan_parameters(micron_vu_C085_param_with_data)`, `project_api.issue_40CF_to_get_media_scan_parameters()`
- **Test Flow:** step1: Enable media scan; write 10 VBs TLC+SLC; set C085 last_scan_spend_time=0x1000000; poll 40CF until scan_vb==0xFFFFFFFF; verify group sequence follows media_scan_vb_group_scan_map order.
- **Key Parameters/Data Structures:** media_scan_vb_group_scan_map: ordered VB_GROUP values (CURRENT_L2_MLC, GC_BLK_MLC, INCOMPLETE_MLC, L1, CURRENT_L2_SLC, GC_BLK_SLC, INCOMPLETE_SLC, PTE, LOG_TAB, RAIN groups, PTE_POOL, L3_MLC, USED_MLC, L3_SLC, USED_SLC); 40CF fields: cur_scan_vb, cur_scan_page, scan_group, media_scan_percentage
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0086 — Enable/Disable Media Scan
- **Feature Name:** Media Scan Enable/Disable control — verify D018 (disable/enable DM BG task), C08B, and reset behavior (HW/RESET_N re-enables; Endpoint/UniPro keeps disabled)
- **VU Commands Used:** `project_api.issue_D018_Disable_Enable_DM_Bg_Task_In_Bank()`, `project_api.issue_C08B_to_enable_diable_media_scan()`, `project_api.issue_C085_to_set_media_scan_parameters()`, `project_api.issue_40CF_to_get_media_scan_parameters()`
- **Test Flow:** step1: Sub-scenarios: (a) disable D018, write, spend_time=0x1000000, verify no scan 60s, reset, verify scan triggers; (b) disable D018, enable D018 → scan triggers; (c) disable C08B, verify no scan; (d) enable C08B → scan triggers; (e) for each reset type (HW/RESET_N/ENDPOINT/UNIPRO): disable C08B, reset, check HW/RESET_N → scan_status=enabled; ENDPOINT/UNIPRO → scan_status=disabled; (f) scan resume test: disable mid-scan, re-enable, verify resumes from last position.
- **Key Parameters/Data Structures:** 40CF: scan_status, cur_scan_vb, cur_scan_page, scan_group; reset types: 0=HW_RESET, 1=RESET_N, 2=ENDPOINT_RESET, 3=UNIPRO_RESET
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0087 — Set Media Scan Parameters
- **Feature Name:** Set Media Scan Parameters (C085) — verify multiple configurable parameters: bin_low, bin_high, MS_SCAN_INSTANCE_FREQ (spend time), full scan group, open block freq, scale factor
- **VU Commands Used:** `project_api.issue_C08B_to_enable_diable_media_scan()`, `project_api.issue_C085_to_set_media_scan_parameters()`, `project_api.issue_40CF_to_get_media_scan_parameters()`, `project_api.issue_4028_to_get_media_scan_without_dm(parm)`
- **Test Flow:** step2: (a) bin_low=10, bfea_bin=9 → expect status 0xFF (INVALID); bin=11 → expect 0x0D. (b) bin_high=10, bfea_bin=9 → expect 0x0D; bin=11 → expect 0xFF. (c) MS_SCAN_INSTANCE_FREQ: 5 scan groups increment sequentially. (d) full_scan_group_spend_time: scan_percentage resets to 4. (e) open_blk_freq_in_secs=30: next trigger ≈30s. (f) scale_factor_reduce_scan_time=150: next group trigger ≈360s.
- **Key Parameters/Data Structures:** micron_vu_C085_param_with_data fields: last_scan_spend_time, set_media_scan_bin_low, set_media_scan_bin_high, last_full_scan_group_spend_time, set_open_blk_freq_in_secs, set_scale_factor_reduce_scan_time; 40CF: elapsed_time, scanned_blocks
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0088 — Change Media Scan Thresholds
- **Feature Name:** Change Media Scan Thresholds (D08E) — verify changing BEC_VALLEY_TH, VALLEY_DIFFEC_TH, VALLEY_OFST_TH, VALLEY_CENTER_EC_TH, XTEMP_DELTA_TH via D08E correctly affects 4028 media scan status output
- **VU Commands Used:** `project_api.issue_D08E_to_change_media_scan_thresholds(micron_vu_D08E_param)`, `project_api.issue_4028_to_get_media_scan_without_dm(parm)`, `project_api.issue_D08A_set_vu_temperature()`, `project_api.issue_4021_get_nand_temperature()`
- **Test Flow:** step2: (a) BEC_VALLEY_TH: inject flipbit=100, get golden bec, test [bec-1, bec, bec+1] → bec>bec_th gives status 15, else 13. (b) VALLEY_DIFFEC_TH: inject 150×4, get golden diff_ec, test thresholds → diff_ec≥th gives status 7, else 15. (c) VALLEY_OFST_TH: golden arc_offset, test thresholds → arc>th gives status 7, else 15. (d) VALLEY_CENTER_EC_TH: golden center_ec → center>th gives status 7, else 15. (e) XTEMP_DELTA_TH: NAND temp=20, th=[1, 0xFF] → th=0xFF: status 7, th=1: status 8.
- **Key Parameters/Data Structures:** micron_vu_D08E_param: w14_bec_valley_th_slc, w18_valley_diffec_th_slc, b20_valley_ofs_th_slc, w16_valley_center_ecth_slc, b21_xtemp_th_delta_slc, b22_is_partial_block, b23_is_em1; 4028 output: bec, diff_ec, arc_offset, center_ec, media_scan_status
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0089 — Read Log and Assert Dump from NAND
- **Feature Name:** Event Log and Assert Dump from NAND — verify Event Log (40B0 para_0=0), MMesg Log (para_0=2), and Assert Dump (para_0=1) content and structure
- **VU Commands Used:** `issue_4080_read_log_from_nand(para_0, para_1, para_2, para_3, para_4, transfer_length)`, `project_api.issue_40B8_to_get_VDET_information()`, `project_api.issue_40FD_get_uC_temp_123()`, `project_api.issue_4021_get_nand_temperature()`, `project_api.issue_40C1_to_get_open_vb_information()`, `project_api.issue_40FE_to_read_enhanced_health_report()`, `project_api.issue_40FA_read_thermal_stuck_threshold()`, `project_api.issue_D0F1_write_thermal_stuck_threshold()`, `project_api.issue_C088_to_start_or_stop_refresh()`, `project_api.issue_40C5_to_get_booking_queue()`, `project_api.issue_C060_to_write_raw_data()`
- **Test Flow:** step1 (Event Log): Erase logs; trigger RAIN recovery; find RAIN_RECOVERY_LOG_ID (0x3011) and UECC_LOG_ID (0x6001); collect reference data; verify event log header, common_info (timestamp, vcc/vccq, temperatures, smart_info), system_status_info, host_ssr_info. step2 (MMesg): Erase mmesg; trigger RAIN recovery; read 40B0 para_0=2; check required log IDs 39/43/45/54; verify split-read (para_4=0 + para_4=2 == single 0x4000 read). step3 (Assert Dump): Set thermal HIGH=80°C via D0F1; write; expect timeout; get assert; verify assert code 0x464; parse assert detail; verify TmprStas=1, all temperature indices non-0xFFFF.
- **Key Parameters/Data Structures:** Event log layout: header(8B) + common_info(1KB) + system_status_info(512B) + host_ssr_info(1KB) + specific_log_info; MMSEG_UNIT_SIZE=0x20; Required MMesg IDs: {39, 43, 45, 54}; WriteThermalStuckThreshold; EXPECTED_ASSERT_CODE=0x464
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `PATTERN_ASSERT_UNEXPECTED_CONDITION`

### CustomVU_0090 — Read Log from RAM
- **Feature Name:** MMesg Log from RAM (VU 4082) — reads MMesg log before and after RAIN recovery trigger; verifies required log IDs appear
- **VU Commands Used:** `issue_4082_read_log()` (VU 4082)
- **Key APIs:** `project_api.issue_C088_to_start_or_stop_refresh()`, `project_api.issue_40C5_to_get_booking_queue()`, `project_api.issue_C060_to_write_raw_data()`
- **Test Flow:** step1: Read 4082 log headers (before). step2: Trigger RAIN recovery (stop refresh, write SLC half-VB, inject UECC, read, check booking queue, start refresh). step3: Read 4082 headers (after); compare; verify required IDs {39, 43, 45, 54} present.
- **Key Parameters/Data Structures:** LOG_UNIT_SIZE=0x20; EXPECTED_UNIT_COUNT=512; per unit: timestamp at offset 0, log_id at offset 6 (2 bytes LE); REQUIRED_NEW_LOG_IDS = {39, 43, 45, 54}
- **Exceptions Used:** `PATTERN_ASSERT_UNEXPECTED_CONDITION`

### CustomVU_0091 — Check NAND Die Crack Test
- **Feature Name:** NAND Die Crack detection — NAND trim manipulation to simulate die crack; verify VU 40E6 reports crack status per die
- **VU Commands Used:** `project_api.issue_40E6_to_check_nand_die_crack()`, `project_api.issue_4084_to_get_NAND_trim(target_addr)`, `project_api.issue_C084_to_set_NAND_trim(set_dict)` (logic present; calls commented out in current code)
- **Test Flow:** pre_process: Read flash_setting; define default_dict and force_crack_dict. step1: Get trim; issue 40E6; verify all dies=0 (no crack); power cycle; for each force_crack address: set trim; verify 40E6 all dies=1 (crack); power cycle; restore trim; verify all dies=0.
- **Key Parameters/Data Structures:** default_dict: {0x150:0x3, 0x350:0x1, 0x050:0x4, 0x250:0x1}; force_crack_dict: {0x150:0x0, 0x350:0x0, 0x050:0xFF, 0x250:0xFF}; CE count = FLH_Quantity * 2^Parallel
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0092 — Verify ERS Default Read Pass Counter for PSA After Power Cycle
- **Feature Name:** ERS Default Read Pass Counter persistence for PSA — verify ERS index 65 preserved across PSA write/read and power cycles
- **VU Commands Used:** `issue_40BA_to_get_error_recovery_statistics`, `issue_D019_to_en_dis_success_read_count`, `issue_C088_to_start_or_stop_refresh`, `issue_40CA_to_get_get_Read_Count_threshold_table`, `issue_40CF_to_get_media_scan_parameters`, `issue_4021_get_nand_temperature`, `issue_405E_to_get_bad_block_information`
- **Key APIs:** `api.write_attribute(AttributeIDN.PSA_STATE/PSA_DATA_SIZE)`, `api.PSAState.PRE_SOLDERING/LOADING_COMPLETE/OFF`
- **Test Flow:** step1: Config LUNs; stop refresh; get ERS 1st count; power cycle; enable D019; PSA flow (PSA_DATA_SIZE, unmap, PSA_STATE=PRE_SOLDERING); write PSA max data size; get ERS 2nd; set LOADING_COMPLETE; read PSA; get ERS 3rd; power cycle; enable D019; issue 405E/4021/40CA/40CF; get ERS 4th; verify 4th ≥ 3rd (no decrease after power cycle). post_process: Set PSA_STATE=OFF; re-config.
- **Key Parameters/Data Structures:** ERSIndex.DEFAULT_READ_PASS_COUNT=65; param.gDevice.l37_psa_max_data_size; read counts per CE per plane from ERS payload offset
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0093 — BBT System Block EC Test
- **Feature Name:** BBT/System Block Erase Count Set/Get — verify VU D048 correctly programs FW_CIS0, FW_CIS1, BBM_Table_EC, ISP_Block_EC, Pointer_Block_EC values
- **VU Commands Used:** `project_api.issue_40B9_to_get_cis_block_Information()`, `project_api.get_BBT2_physical_block_information()`, `project_api.get_PT_physical_block_information()`, `project_api.issue_D048_to_set_FW_BBT_and_system_block_EC(FW_CIS0, FW_CIS1, BBM_Table_EC, ISP_Block_EC, Pointer_Block_EC)`
- **Test Flow:** pre_process: Backup current CIS/BBT/PT info. step1: Get current system block EC values; issue D048 with random values [1,255] for each (ISP always=0xFFFFFFFF); read back and verify; restore original values via D048.
- **Key Parameters/Data Structures:** D048 params: FW_CIS0, FW_CIS1, BBM_Table_EC, ISP_Block_EC, Pointer_Block_EC; ISP always set to 0xFFFFFFFF; 40B9 returns cis0_ec_count, cis1_ec_count; BBT2/PT return erase_cnt
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

### CustomVU_0094 — SECDED Test
- **Feature Name:** SECDED (Single Error Correction, Double Error Detection) SRAM error injection — verify VU 40BD (inject SECDED event) for different SRAM regions causes expected FW assert codes
- **VU Commands Used:** `project_api.issue_40BD_to_inject_SER_SECDED_event(opCode=ErrorInjection.*)`
- **Key APIs:** `api.sequential_write()`, `api.read_compare()`, `api.get_fw_assert_number()`, `api.init_tester_to_unit_ready()`, `api.HwSetting`, `read_Xmemory(sram_address, keep_error=True)`, `write_memory(data_buffer)`
- **Test Flow:** pre_process: Config LUN0; disable FW_DEBUG_MODE. step1 (DISABLE): inject DISABLE, read all SRAM regions — all succeed. steps 2-7: For each ErrorInjection type: inject → write 1G + read_compare → catch G_TIMEOUT_ALL → verify assert number → HW reset.
- **Key Parameters/Data Structures:** ErrorInjection enum: DISABLE, FIP_SRAM (addr=0xF8E40000, assert=0xF500), RS_SRAM (assert=0xF501), COP0_SRAM (0x4C100000-0x4C1FFFFF, assert=0xF500), COP1_SRAM (0x4C200000-0x4C2FFFFF, assert in [0xF502,0xF503,0xF504]), BMU_SRAM (0xF8F0C000-0xF8F0CFFF, assert=0xF501), DBUF_SRAM (0xF8F81600-0xF8F816FF, assert in [0xF502,0xF503,0xF504]), SEC_SRAM (0xF8F81000-0xF8F810FF, probe addrs {0xF8F82810,0xF8F83010,0xF8F83810}, assert=0xF500); api.HwSettingField.FW_DEBUG_MODE
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `G_TIMEOUT_ALL`

### CustomVU_0095 — Write Bad Block Info Test
- **Feature Name:** Write Bad Block Information (C0BC) — verify newly written bad block entries via VU C0BC appear correctly in BBT (405E) after MP; early pool count (40C7) increases accordingly
- **VU Commands Used:** `project_api.issue_40C7_to_get_bad_block_info()`, `project_api.issue_405E_to_get_bad_block_information()`, `project_api.issue_C0BC_to_write_BB_information(bytearray)`
- **Key APIs:** `open_card_basic()` — MP (re-init with open card); `open_card()` — recovery
- **Test Flow:** pre_process: Read flash_setting. step1: Get 40C7 early_pool_physical_VB_count; get 405E BB count; generate 5-10 random (CE, Plane, Block) tuples not already in BBT; encode to bytearray (CE die marker 0xFFF0+ce, then (block & 0x1FFF) << 3 | plane entries, terminated with 0xFFFF, padded to 0x4000); issue C0BC; open_card_basic (MP); re-read 405E; verify BB count = old + len(info_list); verify all new blocks in BBT; verify 40C7 early_pool_physical_VB_count increased by same count. post_process: open_card()
- **Key Parameters/Data Structures:** Payload format: per CE group: 2-byte die marker (0xFFF0+ce) + 2-byte entries per block ((block & 0x1FFF) << 3 | plane) + terminator 0xFFFF; padded to 0x4000 bytes; 405E parse: 8-byte records at offset 8, CE=CE_Plane//6, Plane=CE_Plane%6
- **Exceptions Used:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`

---

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

---

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
