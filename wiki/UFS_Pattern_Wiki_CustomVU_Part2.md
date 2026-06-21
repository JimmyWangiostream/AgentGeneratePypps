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
