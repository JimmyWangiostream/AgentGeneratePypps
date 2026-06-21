---
title: PF038_1619_ExtendedCopy_Burnin-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf038_1619, scsi-cmd, extended-copy, burn-in, ufs50]
description: >
  PF038_1619 Random Copy And Read Burn-in — UFS 5.0 EXTENDED COPY 驗證，每輪
  256×WRITE → 256-Entry Copy List → 2560-Entry Read List → EXTENDED COPY。
sources:
  - JIRA: PF038_1619 (SYSTCUFS-1903)
  - UFS Spec: JESD220H Section 11.3.x (EXTENDED COPY)
---

# PF038_1619 正規化 Test Flow（SCSI CMD 単位）

## 測試目標

Burn-in 驗證 UFS 5.0 EXTENDED COPY：每輪 256 個 WRITE → 256-entry Copy → 2560-entry Read（Read:Copy = 10:1）。

## IC 相容性

| 條件 | UFS >= 4.0, dExtendedUFSFeatureSupport bit18 (Copy) == 1 |
|:---|:---|
| IC | 8361 WDS LV |

## 測試架構（Tree Diagram — 含 Expected）

```
PF038_1619 Test Flow
│
├── Phase 0: 初始化
│   ├── Step 0.1: HW Check — IC/NAND + Copy support → Expected: 支援, 否則 NOT SUPPORTED
│   ├── Step 0.2: UNMAP — Erase All → Expected: GOOD Status
│   ├── Step 0.3: QUERY Set Flag (fPurgeEnable) — Purge → Expected: QUERY RESPONSE Success
│   ├── Step 0.4: QUERY Read Attribute (bPurgeStatus) — Wait Purge → Expected: bPurgeStatus == 0x00
│   └── Step 0.5: WRITE(10) — Write All Card → Expected: GOOD Status
│
└── Loop (burn-in)
    ├── Step L.1: WRITE(10) × 256 — 4KB, LBA=rand(0, capa/4) → Expected: GOOD Status
    ├── Step L.2: Build Copy List — 256 entries: Source(L.1 LBA)→Target(rand(3*capa/4, capa)) → Expected: Copy list ready
    ├── Step L.3: Build Read List — 2560 entries, LBA=rand(2*capa/4, 3*capa/4) → Expected: Read list ready
    └── Step L.4: EXTENDED COPY → Expected: GOOD Status
```

---

## Phase 0 — 初始化

### Step 0.1: HW Check

| Check | Expected |
|-------|---------|
| IC | 8361 WDS LV |
| UFS Version | >= 4.0 |
| dExtendedUFSFeatureSupport bit18 | 1 (Copy supported) |

---

### Step 0.2: Erase All

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
| Value | 0x01 |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.4: Wait Purge

**UFS QUERY**: `READ ATTRIBUTE (bPurgeStatus, IDN 0x07)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x07 (bPurgeStatus) |

**Expected**: `bPurgeStatus == 0x00`。

---

### Step 0.5: Write All Card

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| LBA | 0 ~ MAX_LBA |

**Expected**: `GOOD Status`。

---

## Loop — Burn-in

### Step L.1: Random Write × 256

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| LBA | Random (0 ~ capacity/4) |
| Transfer Length | 4KB |
| Count | 256, non-overlapping |

**Expected**: `GOOD Status`（所有 256 個 Write）。

---

### Step L.2: Build Copy List (256 entries)

**目的**: 建立 256-entry Copy List：Source = Step L.1 的 LBA，Target = Random(3*capa/4, capa)。

**Expected**: `Copy list ready`。

---

### Step L.3: Build Read List (2560 entries)

**目的**: 建立 2560-entry Read List（Read:Copy = 10:1），LBA = Random(2*capa/4, 3*capa/4)。

**Expected**: `Read list ready`。

---

### Step L.4: EXTENDED COPY

**SCSI CMD**: `EXTENDED COPY (83h)` or equivalent

| Field | Value |
|-------|-------|
| Opcode | 0x83 (EXTENDED COPY) |
| Copy List | 256 entries from Step L.2 |
| Read List | 2560 entries from Step L.3 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 11.3.x (EXTENDED COPY)

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | 使用位置 |
|:---|:---|:---|
| 0x2A | WRITE(10) | Step 0.5, L.1 |
| 0x42 | UNMAP | Step 0.2 |
| 0x83 | EXTENDED COPY | Step L.4 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 使用位置 |
|:---|:---|:---|:---|
| 0x06 | fPurgeEnable | 0x02 (SET FLAG) | Step 0.3 |
| 0x07 | bPurgeStatus | 0x03 (READ ATTRIBUTE) | Step 0.4 |

---

## 自我驗證

- Tree Diagram leaf steps: **9** (0.1~0.5=5, L.1~L.4=4)
- `### Step` sections: **9** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
