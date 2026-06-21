---
title: PF027_0270_UNMAP_Latency-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf027_0270, scsi-cmd, unmap, latency, performance]
description: >
  PF027_0270 UNMAP Latency Test — 在 Dirty Media 66% 條件下量測 UNMAP 命令在不同
  Range Size (4KB/2MB)、QD (1/8)、TPRZ (0/1) 組合下的延遲。
sources:
  - JIRA: PF027_0270 (SYSTCUFS-295)
  - UFS Spec: JESD220H Section 11.3.24 (UNMAP)
---

# PF027_0270 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

在 Dirty Media (66% filled) 條件下，量測 UNMAP 命令延遲。
測試矩陣：Range Size (4KB, 2MB) × QD (1, 8) × TPRZ (0, 1)。
每個 UNMAP 命令僅包含一個 Range，使用整個 UDA LBA 空間。

## 測試架構（Tree Diagram — 含 Expected）

```
PF027_0270 Test Flow
│
├── Phase 0: Precondition — Dirty Media 66%
│   ├── Step 0.1: UNMAP — Wipe 整卡 → Expected: GOOD Status
│   ├── Step 0.2: WRITE(10) — Seq 512KB Full Card Write → Expected: GOOD Status
│   └── Step 0.3: WRITE(10) — Random 4KB × 100K per 1GB Span → Expected: GOOD Status
│
└── Loop (Range Size × QD × TPRZ 組合)
    └── Loop (sufficient data points)
        └── Step L.1: UNMAP + Measure Latency → Expected: GOOD Status
```

---

## Phase 0 — Precondition (Dirty Media 66%)

### Step 0.1: Wipe 整卡

**SCSI CMD**: `UNMAP (42h)`

**目的**: 整卡 UNMAP 清空所有 LBA。

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

**目的**: 在每個 1GB Span 內隨機寫入 4KB × 100K 次，達到 66% Dirty Media。

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

## Loop — UNMAP Latency Measurement

### 測試矩陣

| Parameter | Values |
|:---|:---|
| Range Size | 4KB (8 blocks), 2MB (4096 blocks) |
| Queue Depth (QD) | 1, 8 |
| TPRZ (Truncate Partial Range Zero) | 0 (disabled), 1 (enabled) |
| Range Count per CMD | 1 (單一 range) |
| LBA Range | 整個 UDA LBA 空間 |

### Step L.1: UNMAP + Latency Measurement

**SCSI CMD**: `UNMAP (42h)`

**目的**: 對整個 UDA LBA 空間中的隨機位置發送單一 Range UNMAP，並量測延遲。

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | All LUNs |
| UNMAP LBA | Random (within UDA LBA range) |
| UNMAP Block Count | 4KB (8 blocks) or 2MB (4096 blocks) per matrix |
| TPRZ | 0 or 1 per matrix |
| Queue Depth | 1 or 8 per matrix |

**Expected**: `GOOD Status`。記錄延遲值（Timestamp_completion − Timestamp_CMD_sent）。

**UFS SPEC Reference**: JESD220H Section 11.3.24 (UNMAP), SBC-4 5.28

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x2A | WRITE(10) | 10 | Step 0.2, 0.3 |
| 0x42 | UNMAP | 10 | Step 0.1, L.1 |

---

## 自我驗證

- Tree Diagram leaf steps: **4** (0.1, 0.2, 0.3, L.1)
- `### Step` sections: **4** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
- 無 `(待確認)` 佔位符 ✓
