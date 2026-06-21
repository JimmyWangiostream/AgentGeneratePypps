---
title: PF027_0929_SendDiagnostic_Latency-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf027_0929, scsi-cmd, send-diagnostic, latency, performance]
description: >
  PF027_0929 Send Diagnostic Latency Test — 在 Dirty Media 條件下量測
  SEND DIAGNOSTIC 命令延遲，收集 10,000 筆資料點。
sources:
  - JIRA: PF027_0929 (SYSTCUFS-1250)
  - UFS Spec: JESD220H Section 11.3.21 (SEND DIAGNOSTIC)
---

# PF027_0929 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

在 Dirty Media 條件下，反覆發送 SEND DIAGNOSTIC 命令並量測延遲，
收集至少 10,000 筆有效資料點。

## 測試架構（Tree Diagram — 含 Expected）

```
PF027_0929 Test Flow
│
├── Phase 0: Precondition — Dirty Media
│   ├── Step 0.1: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│   ├── Step 0.2: UNMAP — Wipe 整卡 → Expected: GOOD Status
│   ├── Step 0.3: QUERY Set Flag (fPurgeEnable) — Erase All Purge → Expected: QUERY RESPONSE Success
│   ├── Step 0.4: QUERY Read Attribute (bPurgeStatus) — Wait Purge → Expected: bPurgeStatus == 0x00
│   └── Step 0.5: WRITE(10) — Dirty Media 全卡寫滿 → Expected: GOOD Status
│
└── Loop (10,000 次)
    └── Phase 1: SEND DIAGNOSTIC Latency
        ├── Step 1.1: SEND DIAGNOSTIC (1Dh) + Measure Latency → Expected: GOOD Status
        └── Step 1.2: Record Latency Data Point → Expected: 記錄延遲值
```

---

## Phase 0 — Precondition (Dirty Media)

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

---

### Step 0.2: Wipe 整卡

**SCSI CMD**: `UNMAP (42h)`

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | All LUNs |
| UNMAP LBA Range | 0 ~ MAX_LBA |

**Expected**: `GOOD Status`。

---

### Step 0.3: Enable Purge

**UFS QUERY**: `SET FLAG (fPurgeEnable, IDN 0x06)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | 0x06 (fPurgeEnable) |
| Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.4: Wait Purge Complete

**UFS QUERY**: `READ ATTRIBUTE (bPurgeStatus, IDN 0x07)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x07 (bPurgeStatus) |

**Expected**: `bPurgeStatus == 0x00`。

---

### Step 0.5: Dirty Media — 全卡寫滿

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Logical Block Address | 0x00000000 ~ MAX_LBA |
| Transfer Length | Full card capacity |

**Expected**: `GOOD Status`。

---

## Loop — 10,000 Data Points

### Phase 1 — SEND DIAGNOSTIC Latency

#### Step 1.1: SEND DIAGNOSTIC + Latency

**SCSI CMD**: `SEND DIAGNOSTIC (1Dh)`

| Field | Value |
|-------|-------|
| Opcode | 0x1D |
| SelfTest | 0 (standard diagnostic) |
| PF (Page Format) | 0 |
| Parameter List Length | 0 |

**Expected**: `GOOD Status`。記錄 Latency = Timestamp_completion − Timestamp_CMD_sent。

**UFS SPEC Reference**: JESD220H Section 11.3.21 (SEND DIAGNOSTIC)

---

#### Step 1.2: Record Latency Data

**目的**: 記錄此筆延遲值，累積至 10,000 筆。

| Metric | Description |
|:---|:---|
| Data Points Target | 10,000 |
| Latency = | Completion Timestamp − CMD Sent Timestamp |

**Expected**: 累積足夠資料點。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | Step 0.1 |
| 0x1D | SEND DIAGNOSTIC | 6 | Step 1.1 |
| 0x2A | WRITE(10) | 10 | Step 0.5 |
| 0x42 | UNMAP | 10 | Step 0.2 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 使用位置 |
|:---|:---|:---|:---|
| 0x06 | fPurgeEnable | 0x02 (SET FLAG) | Step 0.3 |
| 0x07 | bPurgeStatus | 0x03 (READ ATTRIBUTE) | Step 0.4 |

---

## 自我驗證

- Tree Diagram leaf steps: **7** (0.1~0.5=5, 1.1~1.2=2)
- `### Step` sections: **7** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
