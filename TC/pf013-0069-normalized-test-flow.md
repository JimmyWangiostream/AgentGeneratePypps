---
title: PF013_0069_Time_ReliableWrite_SPOR-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf013_0069, scsi-cmd, reliable-write, spor, data-reliability]
description: >
  PF013_0069 Increasing Time Reliable Write SPOR — 配置 Data Reliability 模式，
  進行長時間 Reliable Write 後 SPOR，驗證資料完整性。
sources:
  - JIRA: PF013_0069 (SYSTCUFS-213)
  - UFS Spec: JESD220H Section 10.7.2, Section 13.4.12 (SPOR)
---

# PF013_0069 正規化 Test Flow

## 測試目標

Data Reliability LUN 配置後，長時間 Reliable Write + SPOR，驗證資料可靠性。

## 測試架構

```
PF013_0069 Test Flow
│
├── Phase 0: Data Reliability 配置
│   ├── Step 0.1: TEST UNIT READY → Expected: GOOD Status
│   ├── Step 0.2: QUERY Read Descriptor (Unit Descriptor) — 確認 LUN 類型 → Expected: QUERY RESPONSE Success
│   └── Step 0.3: QUERY Write Descriptor — Config all LUN to data_reliability type → Expected: QUERY RESPONSE Success
│
├── Phase 1: Full Card Reliable Write
│   ├── Step 1.1: WRITE(10) — All LUN, All LBA, Reliable Write attribute → Expected: GOOD Status (all)
│   └── Step 1.2: READ(10) + Compare — 全卡比對 → Expected: GOOD Status, Data Match
│
├── Phase 2: Increasing Time Write
│   ├── Step 2.1: WRITE(10) — Random LBA, Increasing transfer length → Expected: GOOD Status
│   └── Step 2.2: READ(10) + Compare → Expected: GOOD Status, Data Match
│
├── Phase 3: SPOR
│   ├── Step 3.1: SPOR → Expected: Reset device success
│   └── Step 3.2: QUERY Read Flag (fDeviceInit) → Expected: Flag == 1
│
└── Phase 4: Post-SPOR Verify
    ├── Step 4.1: READ(10) — Read all written data → Expected: GOOD Status
    ├── Step 4.2: Data Compare — 全卡比對 → Expected: Data Match All
    └── Step 4.3: WRITE(10) + READ(10) — 確認仍可正常讀寫 → Expected: GOOD Status, Data Match
```

---

## Phase 0 — Data Reliability 配置

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)` | Opcode: 0x00

**Expected**: `GOOD Status`。

---

### Step 0.2: 讀取 Unit Descriptor

**UFS QUERY**: `READ DESCRIPTOR (Unit Descriptor)` | Opcode: 0x07, IDN: 0x02

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.3: Config Data Reliability

**UFS QUERY**: `WRITE DESCRIPTOR` — Config all LUN as data_reliability type

**Expected**: `QUERY RESPONSE Success`。

---

## Phase 1 — Full Card Reliable Write

### Step 1.1: Reliable Write All Card

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| LBA | 0 ~ MAX_LBA |
| Transfer Length | Full card |
| Reliable Write | Enabled (per configuration) |

**Expected**: `GOOD Status` (all writes)。

---

### Step 1.2: Read Compare All

**SCSI CMD**: `READ(10) (28h)` | Opcode: 0x28

**Expected**: `GOOD Status`, `Data Match All`。

---

## Phase 2 — Increasing Time Write

### Step 2.1: Random Writes with Increasing Time

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | Random |
| LBA | Random |
| Transfer Length | Increasing (step-up each iteration) |

**Expected**: `GOOD Status`。

---

### Step 2.2: Read Compare

**SCSI CMD**: `READ(10) (28h)`

**Expected**: `GOOD Status`, `Data Match`。

---

## Phase 3 — SPOR

### Step 3.1: SPOR

**Expected**: Device recovers。**UFS SPEC**: JESD220H 13.4.12

---

### Step 3.2: Verify Init

**UFS QUERY**: `READ FLAG (fDeviceInit, 0x01)` | Opcode: 0x01

**Expected**: `Flag == 1`。

---

## Phase 4 — Post-SPOR Verify

### Step 4.1: Read All Data

**SCSI CMD**: `READ(10) (28h)`

**Expected**: `GOOD Status`。

---

### Step 4.2: Data Compare All

**Expected**: `Data Match All Card`。

---

### Step 4.3: Functional Check

**SCSI CMD**: `WRITE(10) (2Ah)` + `READ(10) (28h)`

**Expected**: `GOOD Status`, `Data Match`（確認 device 恢復正常讀寫）。

---

## 附錄

### SCSI
| Opcode | Command | 使用 |
|:---|:---|:---|
| 0x00 | TEST UNIT READY | 0.1 |
| 0x28 | READ(10) | 1.2,2.2,4.1,4.3 |
| 0x2A | WRITE(10) | 1.1,2.1,4.3 |

### UFS Query
| IDN | Name | Opcode | 使用 |
|:---|:---|:---|:---|
| 0x02 | Unit Descriptor | 0x07 READ DESC | 0.2 |
| 0x01 | fDeviceInit | 0x01 READ FLAG | 3.2 |

---

## 自我驗證
- Tree leaf: 0.1~0.3(3)+1.1,1.2(2)+2.1,2.2(2)+3.1,3.2(2)+4.1~4.3(3)=12
- `### Step`: 12 ✓ | All `→ Expected:` ✓
