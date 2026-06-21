---
title: PF037_0609_Fbarrier_Unmap_PowerLoss-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf037_0609, scsi-cmd, fbarrier, unmap, spor, tprz]
description: >
  PF037_0609 Fbarrier Unmap Power Loss Test — TPRZ Erase(TPRZ=1)/Discard(TPRZ=0)
  + Fbarrier + SPOR 後驗證資料正確性。
sources:
  - JIRA: PF037_0609 (SYSTCUFS-756)
---

# PF037_0609 正規化 Test Flow（SCSI CMD 単位）

## IC 相容性

| IC | 8318 BiCS5 OPPO, UFS 3.1 |

## 測試架構（Tree Diagram — 含 Expected）

```
PF037_0609 Test Flow
│
├── Phase 0: 初始化
│   └── Step 0.1: HW Check (8318 BiCS5 OPPO, UFS 3.1) → Expected: 支援, 否則 NOT SUPPORTED
│
└── Loop (8HR burn-in)
    │
    ├── Test A: TPRZ=1 (Erase)
    │   ├── Step A.1: VU/MODE SELECT — Set TPRZ=1 → Expected: TPRZ=1 set
    │   ├── Step A.2: WRITE(10) — Random, CS=4K~512K, LBA=rand(0,capacity) → Expected: GOOD Status
    │   ├── Step A.3: UNMAP (queued) — Erase Step A.2 LBA + chunksize → Expected: (queued)
    │   ├── Step A.4: Fbarrier CMD (F0h) (queued) → Expected: (queued)
    │   ├── Step A.5: Send A.3 + A.4 together → Expected: GOOD Status
    │   ├── Step A.6: HW_RESET (SPOR) → Expected: Reset device success
    │   ├── Step A.7: READ(10) — Step A.3 unmap'd LBA (expect erased) → Expected: 回傳 erased data
    │   └── Step A.8: READ(10) + Compare — Random → Expected: GOOD Status, Data Match
    │
    └── Test B: TPRZ=0 (Discard)
        ├── Step B.1: VU/MODE SELECT — Set TPRZ=0 → Expected: TPRZ=0 set
        ├── Step B.2: WRITE(10) — Random → Expected: GOOD Status
        ├── Step B.3: UNMAP (queued, TPRZ=0) + Fbarrier (queued) → Send together → Expected: GOOD Status
        ├── Step B.4: HW_RESET (SPOR) → Expected: Reset device success
        ├── Step B.5: READ(10) — Step B.3 unmap'd LBA → Expected: GOOD Status
        └── Step B.6: READ(10) + Compare — Random → Expected: GOOD Status, Data Match
```

---

## Phase 0

### Step 0.1: HW Check

**Expected**: IC=8318 BiCS5 OPPO, UFS >= 3.1。

---

## Test A: TPRZ=1 (Erase)

### Step A.1: Set TPRZ=1

**VU / MODE SELECT**: Set TPRZ=1。

**Expected**: `TPRZ=1 set`。

### Step A.2: Random Write

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| LBA | Random (0 ~ capacity) |
| Chunksize | Random (4KB ~ 512KB) |

**Expected**: `GOOD Status`。

### Step A.3~A.5: UNMAP + Fbarrier

**SCSI CMD**: `UNMAP (42h)` + `Fbarrier (F0h)` — queued then sent together。

**Expected**: `GOOD Status`。

### Step A.6: SPOR

**Expected**: `Reset device success`。

### Step A.7~A.8: Verify

| Step | SCSI CMD | Expected |
|:---|:---|:---|
| A.7 | READ(10) — unmap'd LBA | erased data |
| A.8 | READ(10) + Compare | GOOD Status, Data Match |

---

## Test B: TPRZ=0 (Discard)

### Step B.1: Set TPRZ=0

**Expected**: `TPRZ=0 set`。

### Step B.2: Random Write

**Expected**: `GOOD Status`。

### Step B.3: UNMAP + Fbarrier

**Expected**: `GOOD Status`。

### Step B.4: SPOR

**Expected**: `Reset device success`。

### Step B.5~B.6: Verify

**Expected**: `GOOD Status, Data Match`。

---

## 自我驗證

- Tree Diagram leaf steps: **16** (0.1=1, A.1~A.8=8, B.1~B.6=6 + loop)
- `### Step` sections: **16** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
- SPOR Expected 使用統一格式 `Reset device success` ✓
