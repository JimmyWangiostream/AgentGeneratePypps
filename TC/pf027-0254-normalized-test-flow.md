---
title: PF027_0254_Mixed_RW_QD16_Latency-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf027_0254, scsi-cmd, read-write, latency, qd, performance]
description: >
  PF027_0254 Mixed Random R/W QD16 Latency Test — 在 QD=16（8×Read + 8×Write）
  混合負載下，量測 4KB Random Read 延遲及 Write IOPS。
sources:
  - JIRA: PF027_0254 (SYSTCUFS-291)
  - UFS Spec: JESD220H Section 10.7.2
---

# PF027_0254 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

在 Dirty Media 66% + QD=16 混合負載（8×Read@4KB + 8×Write@4KB）下量測 Read Latency 與 Write IOPS。
每 100K 命令移動到下一個 1GB range 避免過度碎片化。

## 測試架構（Tree Diagram — 含 Expected）

```
PF027_0254 Test Flow
│
├── Phase 0: Precondition — Dirty Media 66%
│   ├── Step 0.1: UNMAP — Wipe 整卡 → Expected: GOOD Status
│   ├── Step 0.2: WRITE(10) — Seq 512KB Full Card Write → Expected: GOOD Status
│   └── Step 0.3: WRITE(10) — Random 4KB × 100K per 1GB Span → Expected: GOOD Status
│
└── Phase 1: Mixed R/W QD16 Latency
    ├── Step 1.1: Parallel QD16 — 8×READ(10)@4KB + 8×WRITE(10)@4KB → Expected: GOOD Status (all)
    └── Step 1.2: Measure Read Latency + Write IOPS → Expected: 記錄 Read Latency avg + Write IOPS
```

---

## Phase 0 — Precondition (Dirty Media 66%)

### Step 0.1: Wipe 整卡

**SCSI CMD**: `UNMAP (42h)`

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | All LUNs |
| UNMAP LBA Range | 0 ~ MAX_LBA |

**Expected**: `GOOD Status`。

---

### Step 0.2: Sequential Full Card Write

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Logical Block Address | 0x00000000 |
| Transfer Length | 512KB (1024 blocks) per chunk |

**Expected**: `GOOD Status`。

---

### Step 0.3: Random Write per 1GB Span

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Logical Block Address | Random within each 1GB Span |
| Transfer Length | 4KB (8 blocks) |
| Count per Span | 100,000 |

**Expected**: `GOOD Status`。

---

## Phase 1 — Mixed R/W QD16 Latency

### Step 1.1: Parallel QD16 Mixed R/W

**SCSI CMD**: `READ(10) (28h)` + `WRITE(10) (2Ah)`

| Field | Read | Write |
|:---|:---|:---|
| Opcode | 0x28 | 0x2A |
| LUN | All LUNs, random | All LUNs, random (non-overlapping) |
| LBA | Random within current 1GB Span | Random within current 1GB Span |
| Transfer Length | 4KB | 4KB |
| Queue Slots | 8 | 8 |
| Total QD | 16 | 16 |

**Range 移動**: 每 100,000 個 Read 或 Write（先到者），移動至下一個 1GB range。

**Expected**: `GOOD Status`（所有命令）。

---

### Step 1.2: Record Metrics

**Metrics to collect**:

| Metric | Description |
|:---|:---|
| Read Latency (average) | CMD submission → completion status |
| Write IOPS (average) | Writes completed per second |

**Expected**: 成功收集足夠數據點以產出報告。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x28 | READ(10) | 10 | Step 1.1 |
| 0x2A | WRITE(10) | 10 | Step 0.2, 0.3, 1.1 |
| 0x42 | UNMAP | 10 | Step 0.1 |

---

## 自我驗證

- Tree Diagram leaf steps: **5** (0.1, 0.2, 0.3, 1.1, 1.2)
- `### Step` sections: **5** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
