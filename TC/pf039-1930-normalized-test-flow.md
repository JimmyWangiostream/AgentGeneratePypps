---
title: PF039_1930_XLC_Write_Read_PowerState-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf039_1930, scsi-cmd, xlc, power-state, por, burn-in]
description: >
  PF039_1930 XLC Write Read Power State Test — 48HR XLC burn-in: Case A (Normal
  W/R + Power State) and Case B (RDH Read + Power State)。
sources:
  - JIRA: PF039_1930 (SYSTCUFS-2234)
---

# PF039_1930 正規化 Test Flow（SCSI CMD 単位）

## 測試架構（Tree Diagram — 含 Expected）

```
PF039_1930 Test Flow
│
├── Phase 0: 初始化
│   ├── Step 0.1: VU — TT Enable (KIC project) → Expected: TT enabled
│   ├── Step 0.2: UNMAP + SET FLAG(fPurgeEnable) — Erase Purge → Expected: bPurgeStatus == 0x00
│   └── Step 0.3: WRITE(10) — Write All Card → Expected: GOOD Status
│
└── Loop (48HR)
    ├── Case A: Normal W/R + Power State
    │   ├── Step A.1: WRITE(10) — LUN0, LBA=rand(3 XLC VB, whole LUN), CS=4K~512K, cnt=20~32 → Expected: GOOD Status
    │   ├── Step A.2: Random Power State — SSU PowerDown/Active, Sleep/Active ±VCC, H8 Enter/Exit → Expected: Device 恢復就緒
    │   └── Step A.3: READ(10) + Compare — same LBA/size/cnt as A.1 → Expected: GOOD Status, Data Match
    │
    └── Case B: RDH Read + Power State
        ├── Step B.1: READ(10) — LUN0, LBA=rand(0, 3 XLC VB), CS=4KB, cnt=1,000,000 → Expected: GOOD Status
        ├── Step B.2: Random Power State (同上) → Expected: Device 恢復就緒
        └── Step B.3: READ(10) — same as B.1 → Expected: GOOD Status
```

---

## Phase 0

### Step 0.1: VU TT Enable

**目的**: KIC project TT enable via VU command。

**Expected**: `TT enabled`。

### Step 0.2: Erase + Purge

**SCSI CMD**: `UNMAP (42h)` + **UFS QUERY**: `SET FLAG (fPurgeEnable, 0x06)`

**Expected**: `bPurgeStatus == 0x00`。

### Step 0.3: Write All Card

**SCSI CMD**: `WRITE(10) (2Ah)`

**Expected**: `GOOD Status`。

---

## Case A: Normal W/R

### Step A.1: Random Write

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 |
| LBA | Random (3 XLC VB ~ whole LUN) |
| Chunksize | Random 4KB ~ 512KB |
| Count | Random 20 ~ 32 |

**Expected**: `GOOD Status`。

### Step A.2: Random Power State

| Types | SSU PowerDown→Active, Sleep→Active, ±VCC off/on, H8 Enter→Exit |
|:---|:---|

**Expected**: `Device 恢復就緒`。

### Step A.3: Read Compare

**SCSI CMD**: `READ(10) (28h)`

**Expected**: `GOOD Status, Data Match`。

---

## Case B: RDH Read

### Step B.1: RDH Read × 1M

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | 0 |
| LBA | Random (0 ~ 3 XLC VB) |
| Chunksize | 4KB |
| Count | 1,000,000 |

**Expected**: `GOOD Status`。

### Step B.2: Random Power State — 同 A.2

**Expected**: `Device 恢復就緒`。

### Step B.3: RDH Read × 1M — 同 B.1

**Expected**: `GOOD Status`。

---

## 自我驗證

- Tree Diagram leaf steps: **9** (0.1~0.3=3, A.1~A.3=3, B.1~B.3=3)
- `### Step` sections: **9** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
