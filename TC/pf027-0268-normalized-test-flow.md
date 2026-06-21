---
title: PF027_0268_SyncCache_Latency-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf027_0268, scsi-cmd, sync-cache, latency, performance]
description: >
  PF027_0268 SYNC CACHE Latency Test — 量測 SYNCHRONIZE CACHE(10) 命令在不同
  Write/Sync 比例 (1:1/5:1/10:1/20:1)、QD (1/8/16/32)、IMMED (0/1) 組合下的延遲。
sources:
  - JIRA: PF027_0268 (SYSTCUFS-293)
  - UFS Spec: JESD220H Section 11.3.22-23 (SYNCHRONIZE CACHE)
---

# PF027_0268 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

在 Dirty Media (66% filled) 條件下，量測 SYNCHRONIZE CACHE(10) 延遲。
測試矩陣：Write/Sync Ratio (1:1, 5:1, 10:1, 20:1) × QD (1, 8, 16, 32) × IMMED (0, 1)。
每 100K writes 移動到下一個 1GB range 以避免過度碎片化。

## 測試架構（Tree Diagram — 含 Expected）

```
PF027_0268 Test Flow
│
├── Phase 0: Precondition — Dirty Media 66%
│   ├── Step 0.1: UNMAP — Wipe 整卡 → Expected: GOOD Status
│   ├── Step 0.2: WRITE(10) — Seq 512KB Full Card Write → Expected: GOOD Status
│   └── Step 0.3: WRITE(10) — Random 4KB × 100K per 1GB Span → Expected: GOOD Status
│
└── Loop (Ratio × QD × IMMED 組合)
    └── Loop (data points per combination)
        │
        ├── Step L.1: WRITE(10) — Random 4KB × N writes (依 Ratio) → Expected: GOOD Status
        └── Step L.2: SYNCHRONIZE CACHE(10) — Measure Latency → Expected: GOOD Status
```

---

## Phase 0 — Precondition (Dirty Media 66%)

### Step 0.1: Wipe 整卡

**SCSI CMD**: `UNMAP (42h)`

**目的**: 整卡 UNMAP 清空所有 LBA，從乾淨狀態開始 Precondition。

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | All LUNs |
| UNMAP LBA Range | 0 ~ MAX_LBA |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.28

---

### Step 0.2: Sequential Full Card Write

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: 以 512KB Chunk 循序寫滿整張卡。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Logical Block Address | 0x00000000 (sequential) |
| Transfer Length | 512KB (1024 blocks @ 512B) |
| Total Length | MAX_LBA + 1 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.43

---

### Step 0.3: Random Write per 1GB Span

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: 在每個 1GB Span 內隨機寫入 4KB × 100K 次，達到 66% Dirty Media 狀態。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Logical Block Address | Random within each 1GB Span |
| Transfer Length | 4KB (8 blocks @ 512B) |
| Write Count per Span | 100,000 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.43

---

## Loop — Latency Measurement

### 測試矩陣

| Parameter | Values |
|:---|:---|
| Write/Sync Ratio | 1:1, 5:1, 10:1, 20:1 |
| Queue Depth (QD) | 1, 8, 16, 32 |
| IMMED | 0, 1 |
| Starting LBA Range | 1GB Spans, move to next span every 100K writes |

### Step L.1: Random Write (per Ratio)

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: 依 Write/Sync Ratio 發送 N 個 4KB Random Write（N = Ratio 中的 Write 數量）。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | Current 1GB Span LUN |
| Logical Block Address | Random within current 1GB Span |
| Transfer Length | 4KB (8 blocks @ 512B) |
| Write Count (N) | 1 (Ratio 1:1) / 5 (5:1) / 10 (10:1) / 20 (20:1) |
| Queue Depth | 1 / 8 / 16 / 32 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.43

---

### Step L.2: SYNCHRONIZE CACHE + Latency Measurement

**SCSI CMD**: `SYNCHRONIZE CACHE(10) (35h)`

**目的**: 發送 SYNCHRONIZE CACHE(10) 並量測延遲（Timestamp_CMD_sent → Timestamp_completion）。

| Field | Value |
|-------|-------|
| Opcode | 0x35 |
| LUN | Current 1GB Span LUN |
| Logical Block Address | 0x00000000 |
| Number of Blocks | 0x0000 (all blocks) |
| IMMED | 0 or 1 (per matrix) |

**Expected**: `GOOD Status`。記錄延遲值（Timestamp_completion − Timestamp_CMD_sent）。

**UFS SPEC Reference**: JESD220H Section 11.3.22-23 (SYNCHRONIZE CACHE), SBC-4 5.26

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x2A | WRITE(10) | 10 | Step 0.2, 0.3, L.1 |
| 0x35 | SYNCHRONIZE CACHE(10) | 10 | Step L.2 |
| 0x42 | UNMAP | 10 | Step 0.1 |

---

## 自我驗證

- Tree Diagram leaf steps: **5** (0.1, 0.2, 0.3, L.1, L.2)
- `### Step` sections: **5** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
- 無 `(待確認)` 佔位符 ✓
