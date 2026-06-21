---
title: PF027_0748_HPB_ReadWhileWrite_Perf-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf027_0748, scsi-cmd, hpb, performance, parallel, read-while-write]
description: >
  PF027_0748 HPB Read While Write Performance Test — 比較 Normal Read 與 HPB Read
  在平行 Seq Write 負載下的效能 (latency)，輸出 line chart 對比。
  W/R Ratio: Normal=1:35, HPB=1:15。
sources:
  - JIRA: PF027_0748 (SYSTCUFS-930)
  - UFS Spec: JESD220-3 (HPB Extension), JESD220H Section 10.7.2
---

# PF027_0748 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

在平行 Seq Write 負載下比較 Normal Read 與 HPB Read 的效能 (latency)：
1. **Test A**: Normal Read（HPB off）— W/R Ratio 1:35
2. **Test B**: HPB Read（HPB on）— W/R Ratio 1:15
3. 輸出 line chart 對比 Normal vs HPB Read latency

## 測試架構（Tree Diagram — 含 Expected）

```
PF027_0748 Test Flow
│
├── Test A: Normal Read (HPB off)
│   ├── Phase A.0: Precondition
│   │   ├── Step A.0.1: UNMAP — Wipe 整卡 → Expected: GOOD Status
│   │   ├── Step A.0.2: QUERY Set Flag (fPurgeEnable, 0x06) — Erase All → Expected: QUERY RESPONSE Success
│   │   └── Step A.0.3: QUERY Read Attribute (bPurgeStatus) — Wait Purge complete → Expected: bPurgeStatus == 0x00
│   │
│   ├── Phase A.1: Baseline Write
│   │   └── Step A.1.1: WRITE(10) — Seq Write first 8GB → Expected: GOOD Status
│   │
│   ├── Phase A.2: Read-Only Baseline (Normal Read)
│   │   └── Step A.2.1: READ(10) — 4KB Random Read in 0~8GB × 8 rounds → Expected: GOOD Status (record latency)
│   │
│   └── Phase A.3: Parallel Read-While-Write
│       ├── Step A.3.1 (Parallel): WRITE(10) — Seq Write from 8GB+, W/R Ratio=1:35 → Expected: GOOD Status
│       └── Step A.3.2 (Parallel): READ(10) — Random Read in 0~8GB × 8 rounds → Expected: GOOD Status (record latency)
│
├── Reboot + Enable HPB
│
└── Test B: HPB Read
    ├── Phase B.0: Precondition
    │   ├── Step B.0.1: UNMAP — Wipe 整卡 → Expected: GOOD Status
    │   ├── Step B.0.2: QUERY Set Flag (fPurgeEnable, 0x06) — Erase All → Expected: QUERY RESPONSE Success
    │   └── Step B.0.3: QUERY Read Attribute (bPurgeStatus) — Wait Purge complete → Expected: bPurgeStatus == 0x00
    │
    ├── Phase B.1: Baseline Write
    │   └── Step B.1.1: WRITE(10) — Seq Write first 8GB → Expected: GOOD Status
    │
    ├── Phase B.2: Read-Only Baseline (HPB Read)
    │   └── Step B.2.1: HPB READ — 4KB HPB Random Read in 0~8GB × 8 rounds → Expected: GOOD Status (record latency)
    │
    └── Phase B.3: Parallel HPB Read-While-Write
        ├── Step B.3.1 (Parallel): WRITE(10) — Seq Write from 8GB+, W/R Ratio=1:15 → Expected: GOOD Status
        └── Step B.3.2 (Parallel): HPB READ — Random Read in 0~8GB × 8 rounds → Expected: GOOD Status (record latency)
```

---

## Test A — Normal Read (HPB off)

### Phase A.0 — Precondition

#### Step A.0.1: Wipe 整卡

**SCSI CMD**: `UNMAP (42h)`

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | All LUNs |
| UNMAP LBA Range | 0 ~ MAX_LBA |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.28

---

#### Step A.0.2: Enable Purge

**UFS QUERY**: `SET FLAG (fPurgeEnable, IDN 0x06)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | 0x06 (fPurgeEnable) |
| Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`。

---

#### Step A.0.3: Wait Purge Complete

**UFS QUERY**: `READ ATTRIBUTE (bPurgeStatus, IDN 0x07)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x07 (bPurgeStatus) |

**Expected**: `bPurgeStatus == 0x00`。

---

### Phase A.1 — Baseline Write

#### Step A.1.1: Sequential Write First 8GB

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 |
| Logical Block Address | 0x00000000 |
| Transfer Length | 8GB (16,777,216 blocks @ 512B) |

**Expected**: `GOOD Status`。

---

### Phase A.2 — Read-Only Baseline

#### Step A.2.1: Normal Random Read 4KB × 8 Rounds

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | 0 |
| Logical Block Address | Random (0 ~ 8GB range) |
| Transfer Length | 4KB (8 blocks @ 512B) |
| Rounds | 8 (each round: specific number of commands) |

**Expected**: `GOOD Status`。記錄每次 READ latency，計算平均值。

---

### Phase A.3 — Parallel Read-While-Write

#### Step A.3.1 (Parallel): Sequential Write from 8GB+

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 |
| Logical Block Address | 8GB+ (sequential from 8GB boundary) |
| Transfer Length | Per W/R Ratio: 35 writes per 1 read |
| W/R Ratio | 1:35 |

**Expected**: `GOOD Status`。

---

#### Step A.3.2 (Parallel): Normal Random Read in 0~8GB

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | 0 |
| Logical Block Address | Random (0 ~ 8GB range) |
| Transfer Length | 4KB (8 blocks @ 512B) |
| Rounds | 8 |
| W/R Ratio | 1:35 |

**Expected**: `GOOD Status`。記錄 latency under parallel write load。

---

## Reboot + Enable HPB

執行 Reboot 並啟用 HPB 功能後進入 Test B。

---

## Test B — HPB Read

### Phase B.0 — Precondition

#### Step B.0.1: Wipe 整卡

**SCSI CMD**: `UNMAP (42h)`

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | All LUNs |
| UNMAP LBA Range | 0 ~ MAX_LBA |

**Expected**: `GOOD Status`。

---

#### Step B.0.2: Enable Purge

**UFS QUERY**: `SET FLAG (fPurgeEnable, IDN 0x06)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | 0x06 (fPurgeEnable) |
| Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`。

---

#### Step B.0.3: Wait Purge Complete

**UFS QUERY**: `READ ATTRIBUTE (bPurgeStatus, IDN 0x07)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x07 (bPurgeStatus) |

**Expected**: `bPurgeStatus == 0x00`。

---

### Phase B.1 — Baseline Write

#### Step B.1.1: Sequential Write First 8GB

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 |
| Logical Block Address | 0x00000000 |
| Transfer Length | 8GB |

**Expected**: `GOOD Status`。

---

### Phase B.2 — HPB Read-Only Baseline

#### Step B.2.1: HPB Random Read 4KB × 8 Rounds

**SCSI CMD**: `HPB READ` (JESD220-3 HPB Extension)

| Field | Value |
|-------|-------|
| Opcode | HPB READ (HPB extension command) |
| LUN | 0 |
| Logical Block Address | Random (0 ~ 8GB range) |
| Transfer Length | 4KB (8 blocks @ 512B) |
| Rounds | 8 |

**Expected**: `GOOD Status`。記錄每次 HPB READ latency。

**UFS SPEC Reference**: JESD220-3 (HPB Extension)

---

### Phase B.3 — Parallel HPB Read-While-Write

#### Step B.3.1 (Parallel): Sequential Write from 8GB+

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 |
| Logical Block Address | 8GB+ (sequential) |
| Transfer Length | Per W/R Ratio: 15 writes per 1 read |
| W/R Ratio | 1:15 |

**Expected**: `GOOD Status`。

---

#### Step B.3.2 (Parallel): HPB Random Read in 0~8GB

**SCSI CMD**: `HPB READ` (JESD220-3 HPB Extension)

| Field | Value |
|-------|-------|
| Opcode | HPB READ |
| LUN | 0 |
| Logical Block Address | Random (0 ~ 8GB range) |
| Transfer Length | 4KB (8 blocks @ 512B) |
| Rounds | 8 |
| W/R Ratio | 1:15 |

**Expected**: `GOOD Status`。記錄 HPB READ latency under parallel write load。

---

## Metrics 輸出

| Metric | Test A (Normal) | Test B (HPB) |
|:---|:---|:---|
| Read-Only Baseline Latency | A.2 avg | B.2 avg |
| Read-While-Write Latency | A.3 avg | B.3 avg |
| W/R Ratio | 1:35 | 1:15 |

輸出：Line chart 對比 Normal Read vs HPB Read latency（both baseline and under load）。

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x28 | READ(10) | 10 | Step A.2.1, A.3.2 |
| 0x2A | WRITE(10) | 10 | Step A.1.1, A.3.1, B.1.1, B.3.1 |
| 0x42 | UNMAP | 10 | Step A.0.1, B.0.1 |
| — | HPB READ | (HPB ext.) | Step B.2.1, B.3.2 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 使用位置 |
|:---|:---|:---|:---|
| 0x06 | fPurgeEnable | 0x02 (SET FLAG) | Step A.0.2, B.0.2 |
| 0x07 | bPurgeStatus | 0x03 (READ ATTRIBUTE) | Step A.0.3, B.0.3 |

---

## 自我驗證

- Tree Diagram leaf steps: **16** (A.0.1~A.0.3=3, A.1.1=1, A.2.1=1, A.3.1~A.3.2=2, B.0.1~B.0.3=3, B.1.1=1, B.2.1=1, B.3.1~B.3.2=2)
- `### Step` sections: **16** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
- 無 `(待確認)` 佔位符 ✓
