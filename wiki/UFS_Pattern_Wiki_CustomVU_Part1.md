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
