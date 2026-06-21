---
title: PF012_2088_HIQM_Interrupt-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf012_2088, scsi-cmd, hiqm, interrupt, write-booster, psa]
description: >
  PF012_2088 HIQM Interrupt Test — 在 PSA (Power-Saving-Active) flow 中
  進行 HIQM (Host I/O Queue Manager) interrupt 測試，驗證 WB config +
  W/R 操作與 FFU 版本確認。
sources:
  - JIRA: PF012_2088 (SYSTCUFS-2427)
  - UFS Spec: JESD220H Section 10.6 (Command Queue), Section 13.4.18 (WriteBooster)
---

# PF012_2088 正規化 Test Flow

## 測試目標

PSA flow 中驗證 HIQM interrupt 機制：WB 配置 + 大量 I/O + FFU 版本確認。

## 測試架構

```
PF012_2088 Test Flow
│
├── Phase 0: FFU Version Check
│   ├── Step 0.1: INQUIRY — 讀取 Current Version → Expected: GOOD Status, 回傳 SVN
│   └── Step 0.2: 確認 FFU Version vs Current → Expected: 版本相符
│
├── Phase 1: WB Configuration (PSA flow)
│   ├── Step 1.1: QUERY Write Descriptor (Configuration Descriptor) — LUN0 WB=6GB, Normal LUN=8GB → Expected: QUERY RESPONSE Success
│   ├── Step 1.2: UNMAP + SET FLAG(fPurgeEnable) — Erase All → Expected: bPurgeStatus == 0x00
│   └── Step 1.3: QUERY Set Flag (fWriteBoosterEn, 0x0E) → Expected: QUERY RESPONSE Success
│
├── Phase 2: PSA W/R Operations
│   ├── Step 2.1: WRITE(10) — PSA Write pattern → Expected: GOOD Status
│   ├── Step 2.2: READ(10) + Compare → Expected: GOOD Status, Data Match
│   ├── Step 2.3: Random Delay (PSA idle) → Expected: PSA state transition
│   └── Step 2.4: READ(10) + Re-compare → Expected: GOOD Status, Data Match
│
└── Phase 3: HIQM Interrupt Verification
    ├── Step 3.1: High Queue Depth W/R → Expected: GOOD Status (all)
    ├── Step 3.2: Verify Interrupt Count → Expected: Interrupt count > 0
    └── Step 3.3: Final Read Compare All → Expected: GOOD Status, Data Match
```

---

## Phase 0 — FFU Version Check

### Step 0.1: Read Current Version

**SCSI CMD**: `INQUIRY (12h)`

| Field | Value |
|-------|-------|
| Opcode | 0x12 |
| EVPD | 0 |
| Page Code | 0x00 |

**Expected**: `GOOD Status`，回傳 SVN Version。

---

### Step 0.2: Verify Version

**目的**: 確認 FFU 版本與 Current Version 一致。

**Expected**: Version Match。

---

## Phase 1 — WB Configuration

### Step 1.1: Config WB via Configuration Descriptor

**UFS QUERY**: `WRITE DESCRIPTOR (Configuration Descriptor)` | Opcode: 0x08, IDN: 0x01

| Field | Value |
|-------|-------|
| bWriteBoosterBufferType | Shared |
| LUN0 WB AllocUnits | 6GB |
| Normal LUN AllocUnits | 8GB (for PSA flow) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 1.2: Erase All

**SCSI CMD**: `UNMAP (42h)` + **UFS QUERY**: `SET FLAG (fPurgeEnable, 0x06)` | Opcode: 0x02

**Expected**: `bPurgeStatus == 0x00`。

---

### Step 1.3: Enable WB

**UFS QUERY**: `SET FLAG (fWriteBoosterEn, 0x0E)` | Opcode: 0x02

**Expected**: `QUERY RESPONSE Success`。

---

## Phase 2 — PSA W/R

### Step 2.1: PSA Write

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All |
| LBA | Pattern-defined |
| Length | Pattern-defined |

**Expected**: `GOOD Status`。

---

### Step 2.2: Read Compare

**SCSI CMD**: `READ(10) (28h)` | Opcode: 0x28

**Expected**: `GOOD Status`, `Data Match`。

---

### Step 2.3: PSA Idle Delay

**目的**: Random delay 模擬 PSA idle state。

**Expected**: PSA 狀態轉換正常。

---

### Step 2.4: Re-compare

**SCSI CMD**: `READ(10) (28h)`

**Expected**: `GOOD Status`, `Data Match`。

---

## Phase 3 — HIQM Interrupt

### Step 3.1: High QD W/R

**SCSI CMD**: `WRITE(10) (2Ah)` / `READ(10) (28h)` — High Queue Depth

**Expected**: `GOOD Status` (all)。

---

### Step 3.2: Verify Interrupt

**目的**: 確認 HIQM interrupt count > 0（VU operation）。

**Expected**: Interrupt count > 0。

---

### Step 3.3: Final Read Compare

**SCSI CMD**: `READ(10) (28h)` — All card

**Expected**: `GOOD Status`, `Data Match All`。

---

## 附錄

### SCSI
| Opcode | Command | 使用 |
|:---|:---|:---|
| 0x00 | TEST UNIT READY | (implied) |
| 0x12 | INQUIRY | 0.1 |
| 0x28 | READ(10) | 2.2,2.4,3.1,3.3 |
| 0x2A | WRITE(10) | 2.1,3.1 |
| 0x42 | UNMAP | 1.2 |

### UFS Query
| IDN | Name | Opcode | 使用 |
|:---|:---|:---|:---|
| 0x0E | fWriteBoosterEn | 0x02 SET FLAG | 1.3 |
| 0x06 | fPurgeEnable | 0x02 SET FLAG | 1.2 |
| 0x01 | Configuration Descriptor | 0x08 WRITE DESC | 1.1 |

---

## 自我驗證
- Tree leaf: 0.1,0.2(2)+1.1~1.3(3)+2.1~2.4(4)+3.1~3.3(3)=12
- `### Step`: 12 ✓ | All `→ Expected:` ✓
