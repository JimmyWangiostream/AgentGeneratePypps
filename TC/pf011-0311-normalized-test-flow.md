---
title: PF011_0311_WriteBooster_Query_SPOR-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf011_0311, scsi-cmd, write-booster, spor, query]
description: >
  PF011_0311 WriteBooster Query SPOR Test — 驗證 WB Enable 後 SPOR，
  Query Flag/Attribute 回復正確性。
sources:
  - JIRA: PF011_0311 (SYSTCUFS-16)
  - UFS Spec: JESD220H Section 13.4.18 (WriteBooster), Section 13.4.12 (SPOR)
---

# PF011_0311 正規化 Test Flow

## 測試目標

WB Enable 後 SPOR，驗證 volatile flag clear 但 descriptor config 保留。

## 測試架構

```
PF011_0311 Test Flow
│
├── Phase 0: WB 配置
│   ├── Step 0.1: TEST UNIT READY → Expected: GOOD Status
│   ├── Step 0.2: QUERY Read Attribute (dExtendedUFSFeaturesSupport) — WB支援 → Expected: QUERY RESPONSE Success
│   ├── Step 0.3: QUERY Read Attribute (dLUNumWriteBoosterBufferAllocUnits, 0x17) — R/O → Expected: QUERY RESPONSE Success
│   ├── Step 0.4: QUERY Read Descriptor (Configuration Descriptor) → Expected: QUERY RESPONSE Success
│   └── Step 0.5: QUERY Write Descriptor (Configuration Descriptor) — Shared+MAX → Expected: QUERY RESPONSE Success
│
├── Phase 1: WB Enable + W/R
│   ├── Step 1.1: QUERY Set Flag (fWriteBoosterEn, 0x0E) → Expected: QUERY RESPONSE Success
│   ├── Step 1.2: QUERY Read Flag (fWriteBoosterEn) → Expected: Flag == 1
│   ├── Step 1.3: WRITE(10) Random → Expected: GOOD Status
│   └── Step 1.4: READ(10) + Compare → Expected: GOOD Status, Data Match
│
└── Phase 2: SPOR + Query Verify
    ├── Step 2.1: SPOR → Expected: Reset device success
    ├── Step 2.2: QUERY Read Flag (fWriteBoosterEn) → Expected: Flag == 0 (volatile cleared)
    └── Step 2.3: QUERY Read Descriptor (Configuration Descriptor) → Expected: Config preserved
```

---

## Phase 0 — WB 配置

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)` | Opcode: 0x00

**Expected**: `GOOD Status`。

---

### Step 0.2: WB 支援檢查

**UFS QUERY**: `READ ATTRIBUTE (dExtendedUFSFeaturesSupport)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 |
| IDN | dExtendedUFSFeaturesSupport |

**Expected**: `QUERY RESPONSE Success`，WB supported。

---

### Step 0.3: 讀取 WB Buffer Max

**UFS QUERY**: `READ ATTRIBUTE (dLUNumWriteBoosterBufferAllocUnits, IDN 0x17)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 |
| IDN | 0x17 (R/O) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.4: 讀取 Config Descriptor

**UFS QUERY**: `READ DESCRIPTOR (Configuration Descriptor)` | Opcode: 0x07, IDN: 0x01

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.5: 寫入 Config Descriptor (Shared+MAX)

**UFS QUERY**: `WRITE DESCRIPTOR (Configuration Descriptor)` | Opcode: 0x08, IDN: 0x01

| Field | Value |
|-------|-------|
| bWriteBoosterBufferType | 0x01 (Shared) |
| dLUNumWriteBoosterBufferAllocUnits | MAX |

**Expected**: `QUERY RESPONSE Success`。

---

## Phase 1 — WB Enable + W/R

### Step 1.1: Enable WB

**UFS QUERY**: `SET FLAG (fWriteBoosterEn, IDN 0x0E)` | Opcode: 0x02

**Expected**: `QUERY RESPONSE Success`。

---

### Step 1.2: 確認 WB Enabled

**UFS QUERY**: `READ FLAG (fWriteBoosterEn)` | Opcode: 0x01, IDN: 0x0E

**Expected**: `Flag == 1`。

---

### Step 1.3: Random Write

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All |
| LBA | Random |
| Length | Random |

**Expected**: `GOOD Status`。

---

### Step 1.4: Read Compare

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN/LBA/Length | 同 Step 1.3 |

**Expected**: `GOOD Status`, `Data Match`。

---

## Phase 2 — SPOR + Query Verify

### Step 2.1: SPOR

**Expected**: `fDeviceInit == 1`。**UFS SPEC**: JESD220H 13.4.12

---

### Step 2.2: Verify WB Flag (volatile)

**UFS QUERY**: `READ FLAG (fWriteBoosterEn)` | Opcode: 0x01, IDN: 0x0E

**Expected**: `Flag == 0`（volatile, SPOR clears）。

---

### Step 2.3: Verify Config Descriptor (non-volatile)

**UFS QUERY**: `READ DESCRIPTOR (Configuration Descriptor)` | Opcode: 0x07, IDN: 0x01

**Expected**: `QUERY RESPONSE Success`，Config preserved。

---

## 附錄

### SCSI Opcodes
| Opcode | Command | 使用 |
|:---|:---|:---|
| 0x00 | TEST UNIT READY | 0.1 |
| 0x28 | READ(10) | 1.4 |
| 0x2A | WRITE(10) | 1.3 |

### UFS Query
| IDN | Name | Opcode | 使用 |
|:---|:---|:---|:---|
| 0x0E | fWriteBoosterEn | 0x01/0x02 SET/READ FLAG | 1.1,1.2,2.2 |
| 0x17 | dLUNumWriteBoosterBufferAllocUnits | 0x03 READ ATTR | 0.3 |
| 0x01 | Configuration Descriptor | 0x07/0x08 R/W DESC | 0.4,0.5,2.3 |

---

## 自我驗證
- Tree leaf: 12 | `### Step`: 12 ✓ | All `→ Expected:` ✓
