---
title: PF027_0305_BootReady_Latency-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf027_0305, scsi-cmd, boot, latency, performance]
description: >
  PF027_0305 Boot Ready Latency Test — 量測 Boot WLUN ready 後讀取 4KB 的延遲
  （包含 clear UAC 時間），收集 10,000 筆。
sources:
  - JIRA: PF027_0305 (SYSTCUFS-239)
  - UFS Spec: JESD220H Section 13.1 (UFS Boot)
---

# PF027_0305 正規化 Test Flow（SCSI CMD 単位）

## 測試目標

量測 Boot WLUN ready 後首次 4KB Read 的延遲，包含 Clear Unit Attention Condition (UAC) 時間。
收集 10,000 筆有效資料點。

## 測試架構（Tree Diagram — 含 Expected）

```
PF027_0305 Test Flow
│
├── Phase 0: Precondition + Boot LUN Enable
│   ├── Step 0.1: FORMAT UNIT — 格式化 → Expected: GOOD Status
│   ├── Step 0.2: WRITE(10) — Seq 512KB Full Card Write → Expected: GOOD Status
│   ├── Step 0.3: WRITE(10) — Random 4KB × 100K per 1GB Span → Expected: GOOD Status
│   └── Step 0.4: QUERY Read Attribute (bBootLunEn) — 確認 Boot LUN 已啟用 → Expected: bBootLunEn != 0x00
│
└── Loop (10,000 次)
    └── Phase 1: Boot Ready + Read Latency
        ├── Step 1.1: Link Startup — 建立連結 → Expected: Link startup success
        ├── Step 1.2: READ(10) — Boot WLUN 4KB Read + Latency → Expected: GOOD Status
        └── Step 1.3: Record Latency Data → Expected: 記錄延遲值
```

---

## Phase 0 — Precondition

### Step 0.1: FORMAT UNIT

**SCSI CMD**: `FORMAT UNIT (04h)`

| Field | Value |
|-------|-------|
| Opcode | 0x04 |
| LUN | All LUNs |

**Expected**: `GOOD Status`。

---

### Step 0.2: Sequential Full Card Write

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Transfer Length | 512KB per chunk, full card |

**Expected**: `GOOD Status`。

---

### Step 0.3: Random Write per 1GB Span

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| LBA | Random within each 1GB Span |
| Transfer Length | 4KB |
| Count per Span | 100,000 |

**Expected**: `GOOD Status`。

---

### Step 0.4: 確認 Boot LUN 已啟用

**UFS QUERY**: `READ ATTRIBUTE (bBootLunEn, IDN 0x00)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x00 (bBootLunEn) |

**Expected**: `bBootLunEn != 0x00`（Boot LUN 已啟用）。

---

## Loop — 10,000 Iterations

### Phase 1 — Boot Ready Latency

#### Step 1.1: Link Startup

**目的**: 建立 UFS Link，模擬 Boot 情境下的 Link Startup。

**Expected**: `Link startup success`。

---

#### Step 1.2: Boot WLUN 4KB Read + Latency

**SCSI CMD**: `READ(10) (28h)`

**目的**: 讀取 Boot WLUN 的 4KB 資料並記錄延遲。延遲包含 Clear UAC 時間。

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | Boot WLUN |
| Transfer Length | 1 block (512B) → 4KB after clear UAC |

**Expected**: `GOOD Status`。記錄 Latency = Timestamp_completion − Timestamp_CMD_sent。

---

#### Step 1.3: Record Latency

**目的**: 記錄延遲值，累積至 10,000 筆。

**Expected**: 成功記錄資料點。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x04 | FORMAT UNIT | 6 | Step 0.1 |
| 0x28 | READ(10) | 10 | Step 1.2 |
| 0x2A | WRITE(10) | 10 | Step 0.2, 0.3 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | bBootLunEn | 0x03 (READ ATTRIBUTE) | Step 0.4 |

---

## 自我驗證

- Tree Diagram leaf steps: **7** (0.1~0.4=4, 1.1~1.3=3)
- `### Step` sections: **7** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
