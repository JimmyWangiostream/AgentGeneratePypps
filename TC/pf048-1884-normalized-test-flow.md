---
title: PF048_1884_JESD219_Enterprise_WB-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf048_1884, scsi-cmd, jesd219, endurance, wb, waf]
description: >
  PF048_1884 JESD219 Enterprise Workload WB Test — JEDEC Enterprise endurance
  workload with WriteBooster, 計算 WAF (Write Amplification Factor)。
sources:
  - JIRA: PF048_1884 (SYSTCUFS-2471)
  - JESD219 (Enterprise SSD Workload), JESD220H Section 13.4.18 (WB)
---

# PF048_1884 正規化 Test Flow（SCSI CMD 単位）

## 測試目標

在 WriteBooster 啟用下執行 JEDEC Enterprise endurance workload，計算 WAF：
WAF = Total NAND Writes / Total Host Writes。Erase count gap 需 ≤ threshold。

## 測試架構（Tree Diagram — 含 Expected）

```
PF048_1884 Test Flow
│
├── Phase 0: WB 配置
│   ├── Step 0.1: QUERY Write Descriptor (Config Descriptor) — Config WB → Expected: QUERY RESPONSE Success
│   ├── Step 0.2: QUERY Set Flag (fWriteBoosterEn, 0x0E) — Enable WB → Expected: QUERY RESPONSE Success
│   └── Step 0.3: WRITE(10) — Precondition (excluded from WAF host write) → Expected: GOOD Status
│
└── Loop (JEDEC Enterprise endurance)
    ├── Step L.1: WRITE(10) — JEDEC workload, random 4K~64K → Expected: GOOD Status
    ├── Step L.2: VU CMD — Read erase count per block → Expected: 取得 erase count
    ├── Step L.3: Check erase count gap ≤ threshold → Expected: Gap ≤ threshold
    └── Step L.4: Calculate WAF = NAND writes / Host writes → Expected: 記錄 WAF
```

---

## Phase 0 — WB 配置

### Step 0.1: Config WriteBooster

**UFS QUERY**: `WRITE DESCRIPTOR (Configuration Descriptor, IDN 0x01)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x08 (WRITE DESCRIPTOR) |
| Descriptor IDN | 0x01 (Configuration Descriptor) |
| bWriteBoosterBufferType | 0x01 (Shared) |
| dLUNumWriteBoosterBufferAllocUnits | per Device Descriptor |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.2: Enable WriteBooster

**UFS QUERY**: `SET FLAG (fWriteBoosterEn, IDN 0x0E)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | 0x0E (fWriteBoosterEn) |
| Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.3: Precondition Write

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: 對所有 LUN 進行 Precondition Write（不計入 WAF Host Write）。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Transfer Length | Full card capacity |

**Expected**: `GOOD Status`。

---

## Loop — JEDEC Enterprise Endurance

### Step L.1: JEDEC Workload Write

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: 依 JEDEC Enterprise workload pattern 進行隨機寫入。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| LBA | Random (per JEDEC workload) |
| Transfer Length | Random 4KB ~ 64KB |
| Pattern | JEDEC Enterprise workload distribution |

**Expected**: `GOOD Status`。記錄 Host Write count。

**UFS SPEC Reference**: JESD219 (Enterprise SSD Workload)

---

### Step L.2: Read Erase Count

**目的**: 使用 Vendor Unique 命令讀取每個 Block 的 Erase Count。

**Expected**: 取得所有 Block 的 erase count。

---

### Step L.3: Check Erase Count Gap

**目的**: 計算所有 Block 之間的 erase count 差距，若超過 threshold 則 Fail。

| Check | Threshold |
|:---|:---|
| Max Erase Count Gap | ≤ pre-defined threshold |

**Expected**: `Gap ≤ threshold`。若超過 → Pattern FAIL。

---

### Step L.4: Calculate WAF

**目的**: 計算 Write Amplification Factor。

| Formula | WAF = Total NAND Writes / Total Host Writes |
|:---|:---|

**Expected**: 記錄 WAF 值。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | 使用位置 |
|:---|:---|:---|
| 0x2A | WRITE(10) | Step 0.3, L.1 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 使用位置 |
|:---|:---|:---|:---|
| 0x01 | Configuration Descriptor | 0x08 (WRITE DESCRIPTOR) | Step 0.1 |
| 0x0E | fWriteBoosterEn | 0x02 (SET FLAG) | Step 0.2 |

---

## 自我驗證

- Tree Diagram leaf steps: **7** (0.1~0.3=3, L.1~L.4=4)
- `### Step` sections: **7** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
