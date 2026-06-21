# UFS Pattern Wiki Index

Entry point for navigating the integrated knowledge base. Updated: 2026-06-21.

---

## Sources (6)

| Page | Description |
|------|-------------|
| [[sources/spec]] | JEDEC UFS 4.1 Specification (220G) — 73-chapter coverage: all UPIU types, descriptors, flags, attributes, SCSI commands, RPMB protocol, and 59 Key Claims |
| [[sources/script]] | Script Pattern Code Library — all 31 pattern folders with one-sentence summaries, cross-pattern API tables, power_cycle() implementation, and exception type reference |
| [[sources/customerreq]] | Customer Rules — WriteBooster Attribute/Flag writes restricted to Normal non-Boot LUN 0–7; violations return `invalid INDEX` |
| [[sources/userprompt]] | User Prompt Conventions — when LUN is unspecified, use the MaxCapacity Enabled LUN |
| [[sources/modeldefault]] | Model Default Parameters — auto-generated defaults for power management, initialization, HW settings, and data operations |
| [[sources/pronoun]] | Proper Nouns / Domain Glossary — UFS, GC, FTL, WL, LUN, BKOPS, H8, NAND types, WB, EOL, Thermal Throttling, DCMD 0–23 definitions |

---

## Entities

### Descriptors

| Page | Description |
|------|-------------|
| [[device-descriptor]] — Device Descriptor (IDN=00h); wSpecVersion=0410h for UFS4.1; bUFSFeaturesSupport; dExtendedUFSFeaturesSupport |
| [[unit-descriptor]] — Unit Descriptor (IDN=02h); per-LU parameters: bLUEnable, bBootLunID, bLUWriteProtect, bMemoryType, dNumAllocUnits |
| [[configuration-descriptor]] — Configuration Descriptor (IDN=01h); 4 indexes (00h–03h) each covering 8 LUs; bConfigDescrLock |
| [[geometry-descriptor]] — Geometry Descriptor (IDN=07h); dSegmentSize, bMaxNumberLU, bAllocationUnitSize, bDataOrdering |
| [[device-health-descriptor]] — Device Health Descriptor (IDN=09h); bPreEOLInfo, bDeviceLifeTimeEstA/B, dRefreshTotalCount/Progress |

### Flags & Attributes

| Page | Description |
|------|-------------|
| [[flags]] — All UFS flags (IDN 01h–13h, 80h–FFh): fDeviceInit, fPermanentWPEn, fPurgeEnable, fRefreshEnable, fWriteBoosterEn, fWriteBoosterBufferFlushEn, fPhyResourceRemoval |
| [[attributes]] — All UFS attributes (IDN 00h–47h+): bBootLunEn, bCurrentPowerMode, bActiveICCLevel, bBackgroundOpStatus, bRefClkFreq, bConfigDescrLock, wExceptionEventControl/Status, bPSAState, bRefreshMethod, bDefragOperation, bHIDState, bWriteBoosterBufferPartialFlushMode |

### Commands

| Page | Description |
|------|-------------|
| [[scsi-commands]] — All mandatory/optional UCS commands: READ(6/10/16), WRITE(6/10/16), FORMAT UNIT, INQUIRY, UNMAP, SYNCHRONIZE CACHE, BARRIER(F0h), SECURITY PROTOCOL IN/OUT, WRITE BUFFER (FFU), READ BUFFER |
| [[upiu]] — All UPIU types: COMMAND, RESPONSE, DATA IN/OUT, RTT, QUERY REQUEST/RESPONSE, TM REQUEST/RESPONSE, NOP IN/OUT, REJECT; general format, EHS, Sense Data |

### Features

| Page | Description |
|------|-------------|
| [[write-booster]] — SLC buffer for write acceleration; bWriteBoosterBufferType (LU dedicated vs shared); Partial Flush Modes (FIFO/Pinned); Buffer Resize; **CustomerReq: restricted to Normal non-Boot LUN 0–7** |
| [[psa-state]] — Production State Awareness: Off→Pre-soldering→Loading Complete→Soldered; bPSAState attribute; Soldered state irreversible |
| [[hid]] — Host Initiated Defragmentation (new in UFS 4.1); dExtendedUFSFeaturesSupport bit[13]; bDefragOperation; bHIDState state machine; bHIDProgressRatio |
| [[ffu]] — Field Firmware Update: WRITE BUFFER MODE=0Eh; 4KB-aligned BUFFER OFFSET; activated on next power-on/HW reset only; bDeviceFFUStatus |
| [[rpmb]] — Replay Protected Memory Block: 4 regions (0–3); HMAC-SHA-256 MAC; Auth Key programming; Write Counter (no wrap); Advanced RPMB via EHS; RPMB Purge mandatory since UFS 4.0 |

### Storage

| Page | Description |
|------|-------------|
| [[lun]] — Logical Unit Number: Normal LU (0–31), Well-Known LUs (Device/Boot/RPMB/REPORT LUNS); bLUEnable; bBootLunID; **UserPrompt: default = MaxCapacity Enabled LUN** |

---

## Concepts

### Features

| Page | Description |
|------|-------------|
| [[psa]] — PSA lifecycle flow: Off→Pre-soldering→Loading Complete→Soldered; dPSADataSize; bUFSFeaturesSupport bit[1]; irreversible Soldered state; Script PSA folder: 6 tests |
| [[background-operations]] — BKOPS: fBackgroundOpsEn, bBackgroundOpStatus (0=idle, 1=recommended, 2=urgent, 3=critical); exception event URGENT_BKOPS |
| [[exception-events]] — wExceptionEventStatus / wExceptionEventControl; EVENT_ALERT bit in RESPONSE UPIU; 9 event bits including TOO_HIGH/LOW_TEMP, URGENT_BKOPS, WB_FLUSH_NEEDED, DYNAMIC_CAPACITY_NEEDED |
| [[dynamic-capacity]] — dDynCapNeeded, fPhyResourceRemoval, qPhyMemResourceCount; exception event DYNAMIC_CAPACITY_NEEDED |
| [[purge]] — fPurgeEnable, bPurgeStatus; requires all LU queues empty; RPMB Purge variant mandatory since UFS 4.0 |
| [[refresh]] — fRefreshEnable, bRefreshStatus, bRefreshMethod (Force/Selective), bRefreshFreq, bRefreshUnit; HIR; Script refresh folder: booking queue, HP/MP/LP priority |
| [[barrier]] — BARRIER command (F0h); only affects Simple task attribute, normal priority commands; scoped per LU |
| [[out-of-order-transfer]] — bOutOfOrderDataEn, bDataOrdering; HintControl/HintIID/Hint Data fields in DATA IN UPIU; wHostHintCacheSize |

### Power & Thermal

| Page | Description |
|------|-------------|
| [[power-management]] — Power mode state machine: Active/Idle/UFS-Sleep/UFS-PowerDown/UFS-DeepSleep; bCurrentPowerMode; START STOP UNIT POWER CONDITION; VCC/VCCQ/VCCQ2 supplies |
| [[inhibition-timeout]] — BG task inhibition window; gInhibitMgr.lock FW variable; leave_inhibition_mode() = 1001 consecutive reads; HwSettingField.INHIBITION_TIME; Script Inhibition_time folder: 11 tests |
| [[thermal-protection-mode]] — HOT_ONLY / COLD_ONLY / HOT_COLD stuck states; VU D0F1 set thresholds, D0F3 disable TP, D08A inject fake temperature; Script Thermal_Protection folder: 7 tests |

### Patterns

| Page | Description |
|------|-------------|
| [[gc]] — Garbage Collection: FG GC (threshold = mlc_threshold), BG GC (threshold = mlc_threshold - 3); VB pool allocation; erase_fail and program_fail pattern testing |
| [[ftl]] — Flash Translation Layer: L2P via VU 4051/4052; PTE/PMD table; EC/RC tracking; wear leveling; RAIN parity protection; BBT maintenance |
| [[wear-leveling]] — Static WL (EC gap / version gap triggers), Dynamic WL (lowest EC selection); C072 parameter control; WL refresh vs WL GC; Script wear_leveling folder: 4 tests |
| [[rain]] — Redundant Array of Independent NAND: parity across CE/plane; open VB temp protection vs closed VB permanent protection; VU D08B enable/disable; 4 RAIN types (Table/S_CHK, Simple, Permanent, Full Block) |
| [[media-scan]] — FG/BG scan, VHC/NDEP UECC modes, PSA interaction, bin LOW/HIGH thresholds; booking queue deduplication; VU C085 parameters; Script media_scan folder: 7 tests |
| [[read-disturb]] — RC tracking per VB; RC_TH based on EC bracket; RD scan trigger; RC_TH update post-scan; health report counters; Script read_disturb folder: 5 tests |
| [[sgm]] — Scan Guard Mechanism: dynamic/static RC threshold retirement; event logs 0x6008/0x6009/0x0026/0x6002; VU D017 fail injection; 13 scenarios |

---

## Conflicts

| Page | Description |
|------|-------------|
| [[conflicts]] — 2 detected conflicts: #1 WriteBooster LUN restriction (CustomerReq wins over Spec), #2 Default LUN selection (UserPrompt wins over ModelDefault) |
