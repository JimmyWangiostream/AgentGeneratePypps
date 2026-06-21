---
title: PF043_1520_Competitor_RW_Unmap_Burnin-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf043_1520, scsi-cmd, burn-in, random, read-write, unmap]
description: >
  PF043_1520 Competitor R/W/Unmap Burnin — 簡單 Random Write/Read/Unmap burn-in
  測試，每輪 32 個隨機命令後 Read Compare，最後全卡 Read Compare。
sources:
  - JIRA: PF043_1520 (SYSTCUFS-1743)
  - UFS Spec: JESD220H Section 10.7.2
---

# PF043_1520 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

Burn-in 反覆執行：Random (WRITE / READ / UNMAP) × 32 命令 → Read Compare → 全卡 Final Read Compare。

## 測試架構（Tree Diagram — 含 Expected）

```
PF043_1520 Test Flow
│
├── Phase 0: 初始化
│   ├── Step 0.1: UNMAP — Erase All → Expected: GOOD Status
│   ├── Step 0.2: QUERY Set Flag (fPurgeEnable, 0x06) — Purge → Expected: QUERY RESPONSE Success
│   ├── Step 0.3: QUERY Read Attribute (bPurgeStatus) — Wait Purge → Expected: bPurgeStatus == 0x00
│   └── Step 0.4: WRITE(10) — Write All Card → Expected: GOOD Status
│
├── Loop (burn-in)
│   ├── Step L.1: Random CMD × 32 — WRITE/READ/UNMAP, LUN=0, LBA=0~capacity, len=4K~1M, FUA=rand → Expected: GOOD Status
│   └── Step L.2: READ(10) + Compare — Step L.1 write LBA → Expected: GOOD Status, Data Match
│
└── Phase F: Final Read Compare
    └── Step F.1: READ(10) + Compare All Card → Expected: GOOD Status, Data Match All
```

---

## Phase 0 — 初始化

### Step 0.1: Erase All

**SCSI CMD**: `UNMAP (42h)`

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | All LUNs |
| UNMAP LBA Range | 0 ~ MAX_LBA |

**Expected**: `GOOD Status`。

---

### Step 0.2: Enable Purge

**UFS QUERY**: `SET FLAG (fPurgeEnable, IDN 0x06)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | 0x06 (fPurgeEnable) |
| Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.3: Wait Purge Complete

**UFS QUERY**: `READ ATTRIBUTE (bPurgeStatus, IDN 0x07)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x07 (bPurgeStatus) |

**Expected**: `bPurgeStatus == 0x00`。

---

### Step 0.4: Write All Card

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 (LUN0) |
| Logical Block Address | 0x00000000 ~ MAX_LBA |
| Transfer Length | Full card capacity |

**Expected**: `GOOD Status`。

---

## Loop — Burn-in

### Step L.1: Random CMD × 32

**SCSI CMD**: `WRITE(10) (2Ah)` / `READ(10) (28h)` / `UNMAP (42h)`

**目的**: 每輪執行 32 個隨機選取的命令。

| Field | Value |
|-------|-------|
| Command Type | Random: WRITE / READ / UNMAP |
| Command Count | 32 |
| LUN | 0 (LUN0) |
| LBA | Random (0 ~ capacity) |
| Transfer Length | Random (4KB ~ 1MB) |
| FUA (WRITE only) | Random (0 or 1) |

**Expected**: `GOOD Status`（所有 32 個命令）。

---

### Step L.2: Read Compare Written LBAs

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | 0 (LUN0) |
| Logical Block Address | Step L.1 WRITE 寫入的 LBA |
| Transfer Length | Step L.1 WRITE 寫入的大小 |

**Expected**: `GOOD Status, Data Match`。

---

## Phase F — Final Read Compare All

### Step F.1: Read Compare All Card

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | 0 (LUN0) |
| Logical Block Address | 0x00000000 |
| Transfer Length | MAX_LBA + 1 |

**Expected**: `GOOD Status, Data Match All`。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x28 | READ(10) | 10 | Step L.1, L.2, F.1 |
| 0x2A | WRITE(10) | 10 | Step 0.4, L.1 |
| 0x42 | UNMAP | 10 | Step 0.1, L.1 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 使用位置 |
|:---|:---|:---|:---|
| 0x06 | fPurgeEnable | 0x02 (SET FLAG) | Step 0.2 |
| 0x07 | bPurgeStatus | 0x03 (READ ATTRIBUTE) | Step 0.3 |

---

## 自我驗證

- Tree Diagram leaf steps: **7** (0.1~0.4=4, L.1~L.2=2, F.1=1)
- `### Step` sections: **7** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
