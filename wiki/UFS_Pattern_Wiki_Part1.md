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
