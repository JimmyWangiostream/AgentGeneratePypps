# PF003_1647 IR Debug Report

**Pattern**: PF003_1647_NonFUA_SyncCache_L1_PPP-Normalized-TestFlow
**Pattern ID**: PF003_1647

---

## Stage 1 — Rule-based 解析結果

| Phase | Type | Steps | Loop Info |
|-------|------|-------|-----------|
| phase_0 | sequential | 5 |  |
| phase_1 | sequential | 3 |  |
| loop_6 | loop | 9 | until: None |
| phase_F | sequential | 1 |  |

**Fail Condition 識別**:

- `step_0_4`: Expected `Purge 完成，`bPurgeStatus == 0x00`` → 含條件式關鍵字 → `fail_condition` 加入
- `step_3_2`: Expected ``GOOD Status` + `Data Match`` → 含條件式關鍵字 → `fail_condition` 加入
- `step_3_4`: Expected ``GOOD Status` + `Data Match`` → 含條件式關鍵字 → `fail_condition` 加入
- `step_4_3`: Expected ``GOOD Status` + `Data Match`` → 含條件式關鍵字 → `fail_condition` 加入
- `step_F_1`: Expected ``GOOD Status` + `Data Match All Card`` → 含條件式關鍵字 → `fail_condition` 加入

---

## Stage 2 — Wiki 查詢結果

### phase_0 — 初始化與 WriteBooster 配置

| 參考 Wiki Chapter | 標題 |
|------------------|------|
| `06_6_ufs_electrical_clock_reset_signals_and_supplies.md` | 6 UFS Electrical: Clock, Reset, Signals And Supplies |
| `07_7_reset_power-up_and_power-down.md` | 7 Reset, Power-Up And  Power-Down |
| `10_1023_unipro.md` | 10.2.3 UniPro |
| `11_1062_basic_header_format.md` | 10.6.2 Basic Header Format |
| `12_1071_command_upiu.md` | 10.7.1 COMMAND UPIU |
| `14_1073_data_out_upiu.md` | 10.7.3 DATA OUT UPIU |
| `15_1074_data_in_upiu.md` | 10.7.4 DATA IN UPIU |
| `16_1075_ready_to_transfer_upiu.md` | 10.7.5 READY TO TRANSFER UPIU |
| `19_1078_query_request_upiu.md` | 10.7.8 QUERY REQUEST UPIU |
| `20_1079_query_response_upiu.md` | 10.7.9 QUERY RESPONSE UPIU |
| `22_10711_nop_out_upiu.md` | 10.7.11 NOP OUT UPIU |
| `24_10713_data_out_transfer_rules.md` | 10.7.13 Data Out Transfer Rules |
| `26_1098_task_management_function_procedure_calls.md` | 10.9.8  Task Management Function Procedure Calls |
| `28_11_ufs_application_uap_layer_scsi_commands.md` | 11 UFS Application (UAP) Layer – SCSI Commands |
| `32_1136_read_10_command.md` | 11.3.6 READ (10) Command |
| `33_1137_read_16_command.md` | 11.3.7 READ (16) Command |
| `34_1138_read_capacity_10_command.md` | 11.3.8 READ CAPACITY (10) Command |
| `35_1139_read_capacity_16_command.md` | 11.3.9 READ CAPACITY (16) Command |
| `36_11312_report_luns_command.md` | 11.3.12 REPORT LUNS Command |
| `38_11314_write_6_command.md` | 11.3.14 WRITE (6) Command |
| `39_11315_write_10_command.md` | 11.3.15 WRITE (10) Command |
| `40_11316_write_16_command.md` | 11.3.16 WRITE (16) Command |
| `42_11318_format_unit_command.md` | 11.3.18 FORMAT UNIT Command |
| `45_11323_send_diagnostic_command.md` | 11.3.23 SEND DIAGNOSTIC Command |
| `47_11326_unmap_command.md` | 11.3.26 UNMAP Command |
| `48_11327_read_buffer_command.md` | 11.3.27 READ BUFFER Command |
| `49_11328_write_buffer_command.md` | 11.3.28 WRITE BUFFER Command |
| `52_1154_mode_page_policy_vpd_page.md` | 11.5.4 Mode Page Policy VPD Page |
| `54_12233_purge_operation.md` | 12.2.3.3 Purge Operation |
| `55_12236_bsecureremovaltype_parameter.md` | 12.2.3.6 bSecureRemovalType Parameter |
| `56_12431_rpmb_resources.md` | 12.4.3.1 RPMB Resources |
| `57_12437_rpmb_operation_result.md` | 12.4.3.7 RPMB Operation Result |
| `58_12451_advanced_rpmb_message.md` | 12.4.5.1 Advanced RPMB Message |
| `59_12461_cdb_format_of_security_protocol_inout_commands.md` | 12.4.6.1 CDB Format of SECURITY PROTOCOL IN/OUT Commands |
| `62_12473_rpmb_operations_in_normal_rpmb_mode.md` | 12.4.7.3 RPMB Operations in Normal RPMB Mode |
| `63_12474_rpmb_operations_in_advanced_rpmb_mode.md` | 12.4.7.4 RPMB Operations in Advanced RPMB Mode |
| `64_13_ufs_functional_descriptions.md` | 13 UFS Functional Descriptions |
| `65_132_logical_unit_management.md` | 13.2 Logical Unit Management |
| `66_134_host_device_interaction.md` | 13.4 Host Device Interaction |
| `68_14_ufs_descriptors_flags_and_attributes.md` | 14 UFS Descriptors, Flags And Attributes |
| `69_142_flags.md` | 14.2 Flags |
| `70_143_attributes.md` | 14.3 Attributes |
| `71_annex_b_informative_reference_clock_measurement_procedure.md` | Annex B (Informative) Reference Clock Measurement Procedure |
| `73_annex_e_informative_differences_between_revisions.md` | Annex E (Informative) Differences Between Revisions |

### phase_1 — WB Enable + Fill Buffer

| 參考 Wiki Chapter | 標題 |
|------------------|------|
| `06_6_ufs_electrical_clock_reset_signals_and_supplies.md` | 6 UFS Electrical: Clock, Reset, Signals And Supplies |
| `07_7_reset_power-up_and_power-down.md` | 7 Reset, Power-Up And  Power-Down |
| `12_1071_command_upiu.md` | 10.7.1 COMMAND UPIU |
| `14_1073_data_out_upiu.md` | 10.7.3 DATA OUT UPIU |
| `16_1075_ready_to_transfer_upiu.md` | 10.7.5 READY TO TRANSFER UPIU |
| `19_1078_query_request_upiu.md` | 10.7.8 QUERY REQUEST UPIU |
| `20_1079_query_response_upiu.md` | 10.7.9 QUERY RESPONSE UPIU |
| `22_10711_nop_out_upiu.md` | 10.7.11 NOP OUT UPIU |
| `26_1098_task_management_function_procedure_calls.md` | 10.9.8  Task Management Function Procedure Calls |
| `38_11314_write_6_command.md` | 11.3.14 WRITE (6) Command |
| `39_11315_write_10_command.md` | 11.3.15 WRITE (10) Command |
| `40_11316_write_16_command.md` | 11.3.16 WRITE (16) Command |
| `49_11328_write_buffer_command.md` | 11.3.28 WRITE BUFFER Command |
| `55_12236_bsecureremovaltype_parameter.md` | 12.2.3.6 bSecureRemovalType Parameter |
| `56_12431_rpmb_resources.md` | 12.4.3.1 RPMB Resources |
| `57_12437_rpmb_operation_result.md` | 12.4.3.7 RPMB Operation Result |
| `58_12451_advanced_rpmb_message.md` | 12.4.5.1 Advanced RPMB Message |
| `62_12473_rpmb_operations_in_normal_rpmb_mode.md` | 12.4.7.3 RPMB Operations in Normal RPMB Mode |
| `63_12474_rpmb_operations_in_advanced_rpmb_mode.md` | 12.4.7.4 RPMB Operations in Advanced RPMB Mode |
| `65_132_logical_unit_management.md` | 13.2 Logical Unit Management |
| `68_14_ufs_descriptors_flags_and_attributes.md` | 14 UFS Descriptors, Flags And Attributes |
| `69_142_flags.md` | 14.2 Flags |
| `70_143_attributes.md` | 14.3 Attributes |
| `73_annex_e_informative_differences_between_revisions.md` | Annex E (Informative) Differences Between Revisions |

### loop_6 — Burn-in

| 參考 Wiki Chapter | 標題 |
|------------------|------|
| `14_1073_data_out_upiu.md` | 10.7.3 DATA OUT UPIU |
| `15_1074_data_in_upiu.md` | 10.7.4 DATA IN UPIU |
| `16_1075_ready_to_transfer_upiu.md` | 10.7.5 READY TO TRANSFER UPIU |
| `24_10713_data_out_transfer_rules.md` | 10.7.13 Data Out Transfer Rules |
| `32_1136_read_10_command.md` | 11.3.6 READ (10) Command |
| `33_1137_read_16_command.md` | 11.3.7 READ (16) Command |
| `34_1138_read_capacity_10_command.md` | 11.3.8 READ CAPACITY (10) Command |
| `35_1139_read_capacity_16_command.md` | 11.3.9 READ CAPACITY (16) Command |
| `38_11314_write_6_command.md` | 11.3.14 WRITE (6) Command |
| `39_11315_write_10_command.md` | 11.3.15 WRITE (10) Command |
| `40_11316_write_16_command.md` | 11.3.16 WRITE (16) Command |
| `48_11327_read_buffer_command.md` | 11.3.27 READ BUFFER Command |
| `49_11328_write_buffer_command.md` | 11.3.28 WRITE BUFFER Command |
| `55_12236_bsecureremovaltype_parameter.md` | 12.2.3.6 bSecureRemovalType Parameter |
| `56_12431_rpmb_resources.md` | 12.4.3.1 RPMB Resources |
| `57_12437_rpmb_operation_result.md` | 12.4.3.7 RPMB Operation Result |
| `58_12451_advanced_rpmb_message.md` | 12.4.5.1 Advanced RPMB Message |
| `62_12473_rpmb_operations_in_normal_rpmb_mode.md` | 12.4.7.3 RPMB Operations in Normal RPMB Mode |
| `63_12474_rpmb_operations_in_advanced_rpmb_mode.md` | 12.4.7.4 RPMB Operations in Advanced RPMB Mode |
| `65_132_logical_unit_management.md` | 13.2 Logical Unit Management |
| `69_142_flags.md` | 14.2 Flags |
| `70_143_attributes.md` | 14.3 Attributes |
| `73_annex_e_informative_differences_between_revisions.md` | Annex E (Informative) Differences Between Revisions |

### phase_F — Final Read Compare All

| 參考 Wiki Chapter | 標題 |
|------------------|------|
| `15_1074_data_in_upiu.md` | 10.7.4 DATA IN UPIU |
| `16_1075_ready_to_transfer_upiu.md` | 10.7.5 READY TO TRANSFER UPIU |
| `24_10713_data_out_transfer_rules.md` | 10.7.13 Data Out Transfer Rules |
| `32_1136_read_10_command.md` | 11.3.6 READ (10) Command |
| `33_1137_read_16_command.md` | 11.3.7 READ (16) Command |
| `34_1138_read_capacity_10_command.md` | 11.3.8 READ CAPACITY (10) Command |
| `35_1139_read_capacity_16_command.md` | 11.3.9 READ CAPACITY (16) Command |
| `48_11327_read_buffer_command.md` | 11.3.27 READ BUFFER Command |
| `70_143_attributes.md` | 14.3 Attributes |

---

## Stage 3 — LLM 標注決策

### 資料流 (data_flow per edge)

| Edge | data_flow |
|------|-----------|
| phase_0 → phase_1 | total_lba, wb_max_units |
| phase_1 → loop_6 | total_lba |
| loop_6 → phase_F | total_lba, write_records |

### Phase inputs / outputs

| Phase | inputs | outputs |
|-------|--------|---------|
| phase_0 | — | total_lba, wb_max_units |
| phase_1 | total_lba, wb_max_units | — |
| loop_6 | total_lba | write_records |
| phase_F | total_lba, write_records | — |