---
title: PF027_0271_LogicalErase_Latency-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf027_0271, scsi-cmd, unmap, format-unit, logical-erase, latency, performance]
description: >
  PF027_0271 Logical Data Erase/Wipe Latency Test — 量測 UNMAP、FORMAT UNIT 等
  邏輯抹除操作的延遲。測試前在每個 2MB region 寫入 1×4KB。
sources:
  - JIRA: PF027_0271 (SYSTCUFS-296)
  - UFS Spec: JESD220H Section 11.3.24 (UNMAP), Section 11.3.16 (FORMAT UNIT)
---

# PF027_0271 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

量測各種邏輯抹除操作（UNMAP / FORMAT UNIT）的延遲。
測試前在每個 2MB region 寫入一筆 4KB 資料，確保有資料可抹除。

## 測試架構（Tree Diagram — 含 Expected）

```
PF027_0271 Test Flow
│
├── Phase 0: Precondition — Fill each 2MB region
│   ├── Step 0.1: 計算 Region 數量 = UDA / 2MB → Expected: 取得 region 數
│   └── Step 0.2: WRITE(10) — 每個 2MB region 寫入 1 × 4KB → Expected: GOOD Status
│
└── Loop (per Logical Erase Operation Type)
    └── Phase 1: Logical Erase Latency
        ├── Step 1.1: Wait — 等待最後一個 Write 完成 → Expected: 所有 Write 完成
        └── Step 1.2: Logical Erase CMD + Measure Latency → Expected: GOOD Status
```

---

## Phase 0 — Precondition

### Step 0.1: 計算 Region 數量

**目的**: 根據 UDA 容量計算 2MB region 總數。

| Field | Value |
|-------|-------|
| UDA Size | READ CAPACITY(10) 取得 |
| Region Size | 2MB (4096 blocks @ 512B) |
| Region Count | UDA / 2MB |

**Expected**: 取得正確的 region 數量。

---

### Step 0.2: 每個 2MB Region 寫入 4KB

**SCSI CMD**: `WRITE(10) (2Ah)` × N regions

**目的**: 對每個 2MB region 內的隨機 LBA 寫入一筆 4KB，確保有資料可抹除（非計時）。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Logical Block Address | Random within each 2MB region |
| Transfer Length | 4KB (8 blocks) |
| Count | Region 數量 (N) |

**Expected**: `GOOD Status`（所有 N 個 Write）。

---

## Loop — Per Logical Erase Operation Type

### Phase 1 — Logical Erase Latency

#### Step 1.1: Wait for Last Write

**目的**: 等待 Step 0.2 的最後一個 Write 完成，確保 Queue 清空。

**Expected**: 所有 pending Write 完成。

---

#### Step 1.2: Logical Erase CMD + Latency Measurement

**目的**: 發送邏輯抹除命令並量測延遲。無額外 delay。

**Logical Erase 類型**（逐一測試）:

| 操作 | SCSI CMD | Opcode | 說明 |
|:---|:---|:---|:---|
| UNMAP | UNMAP | 0x42 | Unmap 整個 UDA LBA 範圍 |
| FORMAT UNIT | FORMAT UNIT | 0x04 | Low-level format |

**UNMAP 參數**:

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | All LUNs |
| UNMAP LBA Range | 0 ~ MAX_LBA |

**FORMAT UNIT 參數**:

| Field | Value |
|-------|-------|
| Opcode | 0x04 |
| LUN | All LUNs |

**Expected**: `GOOD Status`。記錄延遲（Timestamp_completion − Timestamp_CMD_sent）。

**Latency Measurement**: Start = CMD sent, End = completion received, no additional delay。

**UFS SPEC Reference**: JESD220H Section 11.3.24 (UNMAP), Section 11.3.16 (FORMAT UNIT)

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x04 | FORMAT UNIT | 6 | Step 1.2 (FORMAT UNIT) |
| 0x2A | WRITE(10) | 10 | Step 0.2 |
| 0x42 | UNMAP | 10 | Step 1.2 (UNMAP) |

---

## 自我驗證

- Tree Diagram leaf steps: **5** (0.1, 0.2, 1.1, 1.2 × per erase type)
- `### Step` sections: **4** (step 1.2 covers both erase types within one section)
- ✓ (1.2 describes both UNMAP and FORMAT UNIT as variants of the same logical erase step)
- 每個 leaf step 都有 `→ Expected:` ✓
