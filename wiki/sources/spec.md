---
type: source
title: "JEDEC UFS 4.1 Specification — Structured Knowledge Report"
tags: [ufs, spec, reference, jedec, ufs4.1]
ingested: 2026-06-21
updated: 2026-06-21
entities: [device-descriptor, unit-descriptor, configuration-descriptor, geometry-descriptor,
           device-health-descriptor, rpmb, write-booster, psa-state, hid,
           inhibition-timeout, lun, flags, attributes, upiu, scsi-commands]
concepts: [psa, power-management, background-operations, ffu, out-of-order-transfer,
           exception-events, dynamic-capacity, purge, refresh, barrier, rpmb-purge]
---

# JEDEC UFS 4.1 Specification — Structured Knowledge Report

**Source**: JEDEC Standard No. 220G (UFS 4.1)
**Coverage**: All 73 chapters — all UPIU types, all descriptors (IDN 00h–09h), all flags (IDN 01h–13h), all attributes (IDN 00h–3Fh+), all mandatory SCSI commands, RPMB protocol, and all functional features.

---

## Chapter Map (73 chapters — one-sentence summaries)

### Chapters 01–10 — Foundation & Transport

| Ch | File | Summary |
|----|------|---------|
| 01 | title_page | JEDEC Standard No. 220G title page and copyright information |
| 02 | table_of_contents | Complete table of contents for all 73 chapters and annexes |
| 03 | terms_definitions_keywords | Definitions: application client, device server, initiator, target, transaction, UFS keywords |
| 04 | introduction | UFS 4.1 general features: all HS gears GEAR1–GEAR5 mandatory, PWM-GEAR1 only mandatory PWM gear, 3 power supplies, BER ≤10⁻¹² |
| 05 | ufs_architecture | Three-layer UFS architecture (UAP/UTP/UIC), SAPs (UDM, UIO, UTP_CMD, UTP_TM), physical signals, I_T_L_Q Nexus |
| 06 | ufs_electrical | Power supply specs (VCC/VCCQ/VCCQ2), reference clock frequencies (default=52 MHz), HS gear data rates, RST_n timing |
| 07 | reset_power-up_and_power-down | Power mode state machine (Active/Idle/Sleep/PowerDown/DeepSleep), bCurrentPowerMode values, START STOP UNIT values |
| 08 | ufs_uic_layer_mipi_m-phy | M-PHY configuration: LA only, Type I state machine, PWM in LS mode, all HS gears mandatory, Adapt sequence |
| 09 | ufs_uic_layer_mipi_unipro | UniPro: single CPort 0, no E2E flow control, N_DeviceID assignments, DME attributes |
| 10 | 1023_unipro | UPIU Transaction Codes table, General UPIU Format (Table 10.3), UTP overview, size limits (min 32B / max 65600B) |

### Chapters 11–27 — UPIU Formats & Transport Services

| Ch | File | Summary |
|----|------|---------|
| 11 | 1062_basic_header_format | Basic UPIU Header (12 bytes): Transaction Type, Flags, LUN, Task Tag, IID, EXT_IID, Response, Status, EHS, DSL |
| 12 | 1071_command_upiu | COMMAND UPIU: Transaction Code=01h, Flags (R/W/ATTR/CP), Expected Data Transfer Length, 16-byte CDB |
| 13 | 1072_response_upiu | RESPONSE UPIU: Code=21h, SCSI Status, Device Information (EVENT_ALERT/FAST_RECOVERY_NEEDED), 18-byte sense data |
| 14 | 1073_data_out_upiu | DATA OUT UPIU: Code=02h, Flags.T=retransmit, Data Buffer Offset/Count (multiples of LBS) |
| 15 | 1074_data_in_upiu | DATA IN UPIU: Code=22h, HintControl/HintIID/HintLUN/Hint Data fields for out-of-order transfer |
| 16 | 1075_ready_to_transfer_upiu | RTT UPIU: Code=31h, Data Buffer Offset (multiple of 4), Data Transfer Count max=bMaxDataOutSize |
| 17 | 1076_task_management_request_upiu | TM REQUEST: Code=04h, TM Functions (Abort/Clear/Reset/Query), Input Parameters |
| 18 | 1077_task_management_response_upiu | TM RESPONSE: Code=24h, Service Response codes (00h=Complete, 08h=Succeeded, 09h=Incorrect LU) |
| 19 | 1078_query_request_upiu | QUERY REQUEST: Code=16h, Query Functions (01h/81h), OPCODE values (00h-08h), descriptor/attribute/flag access |
| 20 | 1079_query_response_upiu | QUERY RESPONSE: Code=36h, Response codes (00h=Success→FFh=general failure), Flag Value at byte 23 |
| 21 | 10710_reject_upiu | REJECT UPIU: Code=3Fh, sent for invalid Transaction Type only; NOT for wrong LUN or Query Function |
| 22 | 10711_nop_out_upiu | NOP OUT: Code=00h, connection ping, no data segment |
| 23 | 10712_nop_in_upiu | NOP IN: Code=20h, Response=00h, echoes NOP OUT Task Tag |
| 24 | 10713_data_out_transfer_rules | Three data-out transfer rules: one DATA OUT per RTT, max RTTs=bMaxNumOfRTT, order matches RTT order |
| 25 | 1097_data_transfer_scsi_transport | Send Data-In / Data-In Delivered / Receive Data-Out / Data-Out Received service primitives |
| 26 | 1098_task_management_function_procedure | Task Management Function procedure calls: ABORT TASK, LU RESET invocation and response |
| 27 | 1099_query_function_transport | Query Function transport protocol services for descriptor/attribute/flag access |

### Chapters 28–49 — UFS SCSI Command Set

| Ch | File | Summary |
|----|------|---------|
| 28 | 11_ufs_application_uap_scsi | UFS SCSI command set overview (Table 11.1), all mandatory/optional commands, CONTROL=00h always |
| 29 | 1132_inquiry_command | INQUIRY (12h): Standard 36-byte + VPD; PERIPHERAL DEVICE TYPE, VERSION=06h, VENDOR/PRODUCT/REVISION |
| 30 | 1133_mode_select_10 | MODE SELECT (10) (55h): sets mode pages; no block descriptor in UFS |
| 31 | 1134_mode_sense_10 | MODE SENSE (10) (5Ah): reads mode pages; Mode Parameter Header format |
| 32 | 1136_read_10 | READ (10) (28h): DPO/FUA flags, LBA (4B), Transfer Length (2B), GROUP NUMBER/ContextID |
| 33 | 1137_read_16 | READ (16) (88h): optional; LBA (8B), Transfer Length (4B); same parameter semantics as READ (10) |
| 34 | 1138_read_capacity_10 | READ CAPACITY (10) (25h): 8 bytes (Last LBA 4B + Block Length 4B); min block size=4096 bytes |
| 35 | 1139_read_capacity_16 | READ CAPACITY (16) (9Eh): 32 bytes including TPE, TPRZ bits, Logical Blocks per Physical Block Exponent |
| 36 | 11312_report_luns | REPORT LUNS (A0h): returns list of enabled LUs and well-known LUs |
| 37 | 11313_verify_10 | VERIFY (10) (2Fh): verification implies FUA + cache sync |
| 38 | 11314_write_6 | WRITE (6) (0Ah): mandatory; small CDB variant |
| 39 | 11315_write_10 | WRITE (10) (2Ah): DPO/FUA, LBA, Transfer Length, GROUP NUMBER; 11000b=Pinned WB, 10000b=System Data |
| 40 | 11316_write_16 | WRITE (16) (8Ah): optional; extended LBA addressing |
| 41 | 11317_request_sense | REQUEST SENSE (03h): returns 18-byte fixed sense data; clears UAC if pending |
| 42 | 11318_format_unit | FORMAT UNIT (04h): to Device W-LUN formats all LUs except RPMB; post-format unmapped reads return zeros |
| 43 | 11319_pre-fetch_10 | PRE-FETCH (10) (34h): hints device to prefetch data into cache |
| 44 | 11322_security_protocol_out | SECURITY PROTOCOL OUT (B5h): sends data to RPMB via ECh protocol; data delivered via RTT/DATA OUT |
| 45 | 11323_send_diagnostic | SEND DIAGNOSTIC (1Dh): self-test and diagnostic functions |
| 46 | 11324_synchronize_cache_10 | SYNCHRONIZE CACHE (10) (35h): flushes cached writes to medium |
| 47 | 11326_unmap | UNMAP (42h): de-allocates LBAs on thin-provisioned LUs; parameter list with 16B block descriptors |
| 48 | 11327_read_buffer | READ BUFFER (3Ch): MODE 02h=Data, 1Ch=Error History; Error History Directory format |
| 49 | 11328_write_buffer | WRITE BUFFER (3Bh): MODE 02h=Data, 0Eh=FFU download; BARRIER (F0h); FFU activation on next power-on only |

### Chapters 50–63 — Mode Pages & RPMB

| Ch | File | Summary |
|----|------|---------|
| 50 | 1141_mode_page_overview | Mode page overview: page/subpage code structure, Mode Parameter List format, Mode Parameter Header (10) |
| 51 | 1142_ufs_supported_pages | UFS supported mode pages: Control (0Ah), Read-Write Error Recovery (01h), Caching (08h); VPD pages |
| 52 | 1154_mode_page_policy_vpd | Mode Page Policy VPD page format and device-level vs LU-level scope |
| 53 | 12224_purge_operation | Purge: secure data removal; fPurgeEnable flag flow; bPurgeStatus state machine; RPMB Purge variant |
| 54 | 12233_purge_operation | Purge/Discard/Erase via UNMAP; bProvisioningType=02h (discard) or 03h (erase); Wipe Device via FORMAT UNIT |
| 55 | 12236_bsecureremovaltype | bSecureRemovalType: 00h=erase, 01h=overwrite+erase, 02h=3-pass, 03h=vendor |
| 56 | 12431_rpmb_resources | RPMB resources: Auth Key (32B write-once), Write Counter (4B), Data Area (128KB–16MB), Secure WP Config Block |
| 57 | 12437_rpmb_operation_result | RPMB Result codes (0000h–000Ch); bit[7]=Write Counter expired; Request/Response message types |
| 58 | 12451_advanced_rpmb_message | Advanced RPMB message in EHS (60B): bEHSType=01h; data via DATA IN/OUT; SECURITY PROTOCOL=ECh |
| 59 | 12461_cdb_format_security_protocol | SECURITY PROTOCOL IN (A2h)/OUT (B5h) CDB; ECh=JEDEC UFS; RPMB Protocol IDs (00h–03h=Regions 0–3) |
| 60 | 12471_request_type_message_delivery | RPMB request message delivery flow (host→device via SECURITY PROTOCOL OUT/IN sequence) |
| 61 | 12472_response_type_message_delivery | RPMB response message delivery flow (device→host) |
| 62 | 12473_rpmb_operations_normal | RPMB Normal mode: Auth Key Programming, Counter Read, Authenticated Data Write/Read, Secure WP Config |
| 63 | 12474_rpmb_operations_advanced | RPMB Advanced mode using EHS; same operations with 4KB blocks and EHS-based message delivery |

### Chapters 64–73 — Functional Descriptions, Descriptors & Annexes

| Ch | File | Summary |
|----|------|---------|
| 64 | 13_ufs_functional_descriptions | Boot sequence (three phases), bBootEnable values, fDeviceInit polling, Boot W-LUN read-only access |
| 65 | 132_logical_unit_management | LU management: Normal LU (up to 32), W-LUN types, RPMB regions (0–3), LU config, dNumAllocUnits formula |
| 66 | 134_host_device_interaction | Background ops, dynamic capacity, context management, exception events, WriteBooster, BARRIER, HID, Refresh, Fast Recovery |
| 67 | 136_production_state_awareness_psa | PSA flow: Off→Pre-soldering→Loading Complete→Soldered; bPSAState values; Soldered is irreversible |
| 68 | 14_ufs_descriptors_flags_and_attributes | All descriptor types (IDN 00h–09h, F0h–FFh), Device Descriptor fields, Configuration Descriptor (4 indexes) |
| 69 | 142_flags | Complete flags table (IDN 01h–13h, 80h–FFh): names, access types, default values |
| 70 | 143_attributes | Complete attributes table (IDN 00h–47h+, 80h–FFh): IDN, names, access types, sizes, MDV values |
| 71 | annex_b_reference_clock_measurement | Reference clock jitter measurement: Random RMS Jitter (max 2.8–5.9 ps), Deterministic Jitter (max 15 ps) |
| 72 | annex_d_board_design_guideline | Board design guidelines for UFS 4.0: max impedance for VCC/VCCQ/VCCQ2, capacitor recommendations, PMIC noise budgets |
| 73 | annex_e_differences_between_revisions | Differences between JESD220A through 220G: new features per revision, mandatory-ization of gears, removed features |

---

## Key Entity / Concept List

### Descriptors (IDN)

| IDN | Name | Key Notes |
|-----|------|-----------|
| 00h | Device Descriptor | wSpecVersion=0410h for UFS4.1; bUFSFeaturesSupport; dExtendedUFSFeaturesSupport (bit0=WB, bit13=HID, bit14=FastRecovery) |
| 01h | Configuration Descriptor | 4 indexes (00h–03h), each covers 8 LUs; bConfDescContinue; bConfigDescrLock permanently locks all configs |
| 02h | Unit Descriptor | bLUEnable, bBootLunID, bLUWriteProtect, bMemoryType, dNumAllocUnits, bDataReliability, bLogicalBlockSize, bProvisioningType |
| 04h | Interconnect Descriptor | UniPro/M-PHY capability and version info |
| 05h | String Descriptor | Manufacturer Name (IDN 12h), Product Name (IDN 22h), OEM ID, Serial Number, Product Revision Level |
| 07h | Geometry Descriptor | dSegmentSize, bMaxNumberLU (up to 32), bAllocationUnitSize, dOptimalLogicalBlockSize, bDataOrdering |
| 08h | Power Parameters Descriptor | bActiveICCLevel ranges, power profiles |
| 09h | Device Health Descriptor | bPreEOLInfo (01h=normal, 02h=≥80% warning, 03h=≥90% critical); bDeviceLifeTimeEstA/B (01h–0Ah=0–100%); dRefreshTotalCount/dRefreshProgress |
| F0h–FFh | Vendor Specific Descriptor | Vendor defined |

### Flags (IDN) — Accessed via QUERY REQUEST OPCODE 05h/06h/07h/08h

| IDN | Name | Access | Default |
|-----|------|--------|---------|
| 01h | fDeviceInit | Set only | 0 |
| 02h | fPermanentWPEn | Write once | 0 |
| 03h | fPowerOnWPEn | Power-on-reset | 0 |
| 04h | fBackgroundOpsEn | Volatile | 1 |
| 05h | fDeviceLifeSpanModeEn | Volatile | 0 |
| 06h | fPurgeEnable | Write-only volatile | 0 |
| 07h | fRefreshEnable | Write-only volatile | 0 |
| 08h | fPhyResourceRemoval | Persistent | 0 |
| 09h | fBusyRTC | Read Only | 0 |
| 0Bh | fPermanentlyDisableFwUpdate | Write once | 0 |
| 0Eh | fWriteBoosterEn | Volatile | 0 |
| 0Fh | fWriteBoosterBufferFlushEn | Volatile | 0 |
| 10h | fWriteBoosterBufferFlushDuringHibernate | Volatile | 0 |
| 13h | fUnpinEn | Volatile | 0 |

### Key Attributes (IDN) — Accessed via QUERY REQUEST OPCODE 03h/04h

| IDN | Name | Access | MDV | Key Notes |
|-----|------|--------|-----|-----------|
| 00h | bBootLunEn | Persistent | 00h | 00h=disabled, 01h=Boot LU A, 02h=Boot LU B |
| 02h | bCurrentPowerMode | Read only | — | 00h=Idle, 11h=Active, 22h=UFS-Sleep, 33h=UFS-PowerDown |
| 03h | bActiveICCLevel | Volatile | — | 00h–0Fh |
| 05h | bBackgroundOpStatus | Read only | — | 00h=not required, 01h=non-critical, 02h=perf impact, 03h=critical |
| 06h | bPurgeStatus | Read only | — | 00h=idle, 01h=in progress, 02h=stopped, 03h=completed, 04h/05h=fail |
| 0Ah | bRefClkFreq | Persistent | 03h | 03h=52MHz (default) |
| 0Bh | bConfigDescrLock | Write once | — | 0h=unlocked, 1h=locked permanently |
| 0Ch | bMaxNumOfRTT | Persistent | 02h | Must not exceed bDeviceRTTCap |
| 0Dh | wExceptionEventControl | Volatile | — | Bits 0–11: enable specific exception events |
| 0Eh | wExceptionEventStatus | Read only | — | bit0=TOO_HIGH_TEMP, bit1=TOO_LOW_TEMP, bit2=URGENT_BKOPS, bit3=PERF_THROTTLING, bit4=WB_FLUSH_NEEDED, bit5=DYN_CAP_NEEDED, bit6=CORRECTION_NEEDED, bit7=DEVICE_HEALTH_EVENT, bit8=DEVICE_LEVEL_EXCEPTION |
| 15h | bPSAState | Persistent | — | 00h=Off, 01h=Pre-soldering, 02h=Loading Complete, 03h=Soldered |
| 2Ch | bRefreshStatus | Read only | — | Same structure as bPurgeStatus; +05h=XTemp refresh |
| 2Dh | bRefreshFreq | Persistent | — | 01h=1 month, FFh=255 months |
| 2Eh | bRefreshUnit | Persistent | — | 00h=minimum capability, 01h=100% of device |
| 2Fh | bRefreshMethod | Persistent | 00h | 00h=not defined, 01h=Manual-Force, 02h=Manual-Selective |
| 35h | bDefragOperation | Volatile | — | 00h=disabled, 01h=analysis only, 02h=analysis+defrag (HID) |
| 36h | dHIDAvailableSize | Read only | — | Total fragmented size in 4KB units; FFFFFFFFh=no valid info |
| 37h | dHIDSize | Persistent | FFFFFFFFh | Size to defrag per operation (4KB units) |
| 38h | bHIDProgressRatio | Read only | — | 00h=0% to 64h=100% |
| 39h | bHIDState | Read only | — | 00h=Idle, 01h=Analysis, 02h=Required, 03h=In Progress, 04h=Completed, 05h=Not Required |
| 3Dh | bWriteBoosterBufferResizeEn | Write-only volatile | — | 01h=decrease, 02h=increase |
| 3Fh | bWriteBoosterBufferPartialFlushMode | Persistent | — | 00h=none, 01h=FIFO, 02h=Pinned |

### Logical Units

| Type | W-LUN | LUN Field | Notes |
|------|-------|-----------|-------|
| Normal LU (0–31) | — | 00h–1Fh | All UCS commands when bLUEnable=01h |
| REPORT LUNS | 01h | 81h | INQUIRY, REQUEST SENSE, TEST UNIT READY, REPORT LUNS |
| UFS Device | 50h | D0h | INQUIRY, REQUEST SENSE, TEST UNIT READY, START STOP UNIT, FORMAT UNIT |
| Boot | 30h | B0h | INQUIRY, REQUEST SENSE, READ (6)/(10)/(16), READ BUFFER |
| RPMB | 44h | C4h | INQUIRY, REQUEST SENSE, SECURITY PROTOCOL IN/OUT |

---

## Part 3 — Key Claims (59 claims, by category)

### Architecture & Protocol (Claims 1–10)

1. **[Ch 04, Ch 28]** UFS device shall support HS-GEAR1 through HS-GEAR5 (all mandatory). PWM-GEAR1 is the only mandatory PWM gear.
2. **[Ch 10]** UPIU minimum size is 32 bytes; maximum size is 65600 bytes. T_SDU max = 65600 bytes.
3. **[Ch 10]** EHS (Extended Header Segments) are only supported in COMMAND UPIU and RESPONSE UPIU; Total EHS Length shall be 0 in all other UPIU types.
4. **[Ch 10]** Max combined EHS = 96 bytes; Total EHS Length field values = 0, 1, 2, or 3 (units of 32 bytes).
5. **[Ch 22, Ch 10]** Device processes only one NOP OUT or QUERY REQUEST at any point in time.
6. **[Ch 21]** REJECT UPIU is sent only when invalid Transaction Type received. NOT sent for: wrong LUN in COMMAND UPIU, wrong LUN in TM REQUEST, or wrong Query Function in QUERY REQUEST.
7. **[Ch 20]** QUERY RESPONSE Flag Value is at byte 23 (00h=cleared, 01h=set).
8. **[Ch 19]** Write Attribute VALUE field is 64-bit big-endian right-justified.
9. **[Ch 24]** DATA OUT UPIU Data Buffer Offset and Data Transfer Count must be integer multiples of Logical Block Size.
10. **[Ch 16]** RTT Data Buffer Offset shall be an integer multiple of 4. Data Transfer Count max = bMaxDataOutSize.

### Descriptors & Flags (Claims 11–16)

11. **[Ch 68]** wSpecVersion=0410h identifies a UFS 4.1 device.
12. **[Ch 68]** bConfigDescrLock (attribute 0Bh) when set to 1 permanently locks ALL configuration descriptors — irreversible.
13. **[Ch 68]** Configuration Descriptor supports 4 indexes (00h–03h), each covering 8 LUs; bConfDescContinue=01h means more to follow.
14. **[Ch 69]** fDeviceInit (IDN=01h) is Set-only by host; device sets it to 1 during initialization, then clears to 0 when ready. Host must poll until 0.
15. **[Ch 69]** fPurgeEnable (IDN=06h) can only be set when command queues of ALL logical units are empty.
16. **[Ch 69]** fPermanentWPEn (IDN=02h) is Write-Once and cannot be cleared once set.

### Attributes (Claims 17–21)

17. **[Ch 70]** bRefClkFreq MDV=03h (52.0 MHz is the default reference clock frequency in UFS 4.1).
18. **[Ch 70]** bMaxNumOfRTT MDV=02h; shall not be set higher than bDeviceRTTCap; can only be set when all LU command queues are empty.
19. **[Ch 70]** bOutOfOrderDataEn is Write-Once — cannot be changed after first write.
20. **[Ch 70]** bConfigDescrLock write once; locks Configuration Descriptor when set to 01h.
21. **[Ch 70]** qTimestamp is write-only; value in nanoseconds since Jan 1, 1970 UTC.

### LUs & Commands (Claims 22–37)

22. **[Ch 28, Ch 10]** If bLUEnable=01h, each LU shall support all commands in Table 11.1 as mandatory.
23. **[Ch 34]** READ CAPACITY (10) and READ CAPACITY (16): Minimum Logical Block Size for UFS = 4096 bytes.
24. **[Ch 35]** TPRZ bit in READ CAPACITY (16): TPRZ=1 (03h) means unmapped LBA returns zeros; TPRZ=0 (02h) means unmapped LBA may return any data.
25. **[Ch 28]** UFS only supports fixed-length CDB format (no Variable Length CDB as in SCSI).
26. **[Ch 28]** CONTROL byte in all UFS CDBs shall be set to zero and shall be ignored. ACA is not supported.
27. **[Ch 29]** INQUIRY STANDARD DATA: PERIPHERAL DEVICE TYPE=00h for normal LU, 1Eh for well-known LU. VERSION=06h. RESPONSE DATA FORMAT=0010b. At least 36 bytes returned.
28. **[Ch 29]** PRODUCT REVISION LEVEL (bytes 32–35) shall identify firmware version; shall be uniquely encoded for any firmware modification.
29. **[Ch 32]** GROUP NUMBER in READ CDB: 00001b–01111b are Context IDs 1–15. Reserved values cause CHECK CONDITION with ILLEGAL REQUEST.
30. **[Ch 39]** GROUP NUMBER in WRITE CDB: 11000b=Pinned data (Pinned WriteBooster Partial Flush); 10000b=System Data.
31. **[Ch 47]** UNMAP command not supported on full-provisioned LUs (bProvisioningType=00h).
32. **[Ch 47]** If UNMAP BLOCK DESCRIPTOR DATA LENGTH is not a multiple of 16, the last incomplete descriptor is ignored.
33. **[Ch 42]** FORMAT UNIT to Device W-LUN formats all enabled LUs except RPMB W-LUN.
34. **[Ch 42]** After successful FORMAT UNIT: all LBAs shall be mapped (if full-provisioned) or unmapped (if thin-provisioned). Read on unmapped LBA after format returns zeros.
35. **[Ch 49]** FFU WRITE BUFFER MODE=0Eh only; firmware is activated on next power-on or hard reset, NOT on START STOP UNIT or FORMAT UNIT.
36. **[Ch 49]** WRITE BUFFER BUFFER OFFSET for FFU should be 4KB-aligned.
37. **[Ch 49]** BARRIER command (F0h) only affects Simple task attribute, normal priority commands. Head of Queue and high-priority commands are not affected.

### Power & Initialization (Claims 38–41)

38. **[Ch 07]** Three power supplies mandatory: VCC (2.4–2.7V), VCCQ (1.14–1.26V), VCCQ2 (1.70–1.95V). VCC=3.3V dropped in UFS 4.0; VCC=1.8V removed in UFS 3.0.
39. **[Ch 07]** RST_n assertion causes full hardware reset; device returns to default state.
40. **[Ch 64]** Boot sequence: partial init → boot transfer → init completion. fDeviceInit cleared by device signals completion.
41. **[Ch 64]** Boot W-LUN (30h/B0h) provides read-only access to active Boot LU.

### RPMB (Claims 42–47)

42. **[Ch 56]** Each RPMB region has its own dedicated authentication key, write counter, and result register.
43. **[Ch 56]** Write Counter starts at 00000000h and increments per authenticated write. Maximum = FFFFFFFFh; no wrap-around.
44. **[Ch 57]** Authentication key not programmed state (0007h) is the only valid result until authentication key is programmed; after programming, 0007h will never occur again.
45. **[Ch 56]** MAC uses HMAC-SHA-256; key = 256-bit authentication key stored in device.
46. **[Ch 59]** SECURITY PROTOCOL IN/OUT for RPMB: SECURITY PROTOCOL=ECh; ALLOCATION/TRANSFER LENGTH must be multiple of 512 (Normal RPMB) or 4096 (Advanced RPMB).
47. **[Ch 53]** RPMB Purge is mandatory since UFS 4.0. While RPMB Purge is in progress, authenticated read/write returns result code 000Ch.

### Data Protection (Claims 48–51)

48. **[Ch 55]** bSecureRemovalType values: 00h=erase only (default), 01h=overwrite+erase, 02h=overwrite+complement+random+erase, 03h=vendor defined.
49. **[Ch 55]** fPermanentWPEn enables permanent write protection on bLUWriteProtect=02h LUs. After manufacturing, fPermanentWPEn=0.
50. **[Ch 55]** WPF (Secure Write Protect Flag) shall be 0 after manufacturing.
51. **[Ch 55]** Secure Write Protect areas (up to 4 per LU) apply only to LUs configured as not write protected (bLUWriteProtect=00h). Total secure write protect areas shall not exceed bNumSecureWPArea.

### Unit Attention (Claims 52–53)

52. **[Ch 24]** UAC established on ALL LUs by: Power-on, HW Reset, EndPointReset, Host UniPro Warm Reset. LU Reset establishes UAC on addressed LU only.
53. **[Ch 24]** INQUIRY returns GOOD with UAC pending (does NOT clear UAC). REQUEST SENSE returns GOOD and CLEARS UAC. REPORT LUNS does NOT clear UAC.

### HID (Claims 54–57)

54. **[Ch 66]** HID (Host Initiated Defragmentation) is supported if dExtendedUFSFeaturesSupport bit[13]=1.
55. **[Ch 66]** bDefragOperation can only be set after UFS initialization phase (fDeviceInit cleared). Setting before init completion fails with FFh General Failure.
56. **[Ch 66]** If medium-changing command received during HID analysis/defrag, HID operation may be terminated; bDefragOperation, bHIDProgressRatio, bHIDState are reset to 0.
57. **[Ch 66]** After host reads bHIDState=04h (Completed) or 05h (Not Required), device resets bHIDState, bHIDProgressRatio, bDefragOperation to 0 and dHIDAvailableSize to FFFFFFFFh.

### PSA (Claims 58–59)

58. **[Ch 67]** PSA state Soldered (03h) is irreversible — cannot be changed back.
59. **[Ch 67]** First write after soldering triggers device to automatically set bPSAState to Soldered (03h).

---

## Where This Fits

Related pages: [[device-descriptor]], [[unit-descriptor]], [[configuration-descriptor]], [[geometry-descriptor]], [[device-health-descriptor]], [[rpmb]], [[write-booster]], [[psa-state]], [[hid]], [[lun]], [[flags]], [[attributes]], [[upiu]], [[scsi-commands]], [[psa]], [[power-management]], [[background-operations]], [[ffu]], [[exception-events]], [[dynamic-capacity]], [[purge]], [[refresh]], [[barrier]], [[conflicts]]
