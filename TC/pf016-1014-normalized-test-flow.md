---
title: PF016_1014_IdlePower_WriteRead-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf016_1014, scsi-cmd, idle, power, burn-in]
description: >
  PF016_1014 Idle Power Write Read — 24h burn-in: W/R with Idle intervals,
  final Read Compare All。
sources:
  - JIRA: PF016_1014 (SYSTCUFS-1297)
  - UFS Spec: JESD220H Section 10.7.2
---

# PF016_1014 正規化 Test Flow

## 測試目標

24h burn-in: Random Write ×10 → Idle 500ms~2s → Random Read ×10 → Idle → Repeat。
最終全卡 Read Compare 確認資料無誤。

## 測試架構

```
PF016_1014 Test Flow
│
├── Phase 0: 初始化
│   ├── Step 0.1: TEST UNIT READY → Expected: GOOD Status
│   └── Step 0.2: READ CAPACITY(10) → Expected: GOOD Status, 回傳 LBA 範圍
│
└── Loop (until 24h)
    ├── Step L.1: WRITE(10) ×10 — Random chunk 4K~512K → Expected: GOOD Status (all 10)
    ├── Step L.2: Idle 500ms~2s → Expected: Idle timeout
    ├── Step L.3: READ(10) ×10 — Random chunk 4K~512K → Expected: GOOD Status (all 10)
    ├── Step L.4: Idle 500ms~2s → Expected: Idle timeout
    └── Step L.5: READ(10) + Compare All Card → Expected: GOOD Status, Data Match
```

---

## Phase 0

### Step 0.1: TEST UNIT READY

**SCSI CMD**: `TEST UNIT READY (00h)` | Opcode: 0x00

**Expected**: `GOOD Status`。

---

### Step 0.2: READ CAPACITY(10)

**SCSI CMD**: `READ CAPACITY(10) (25h)` | Opcode: 0x25

**Expected**: `GOOD Status`。

---

## Loop — 24h Burn-in

### Step L.1: Random Write ×10

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | Random |
| LBA | Random (0 ~ capacity - chunksize) |
| Chunk Size | Random (4KB ~ 512KB) |
| Cmd Count | 10 |

**Expected**: `GOOD Status` (all 10)。

---

### Step L.2: Idle 500ms~2s

**Expected**: Idle timeout。

---

### Step L.3: Random Read ×10

**SCSI CMD**: `READ(10) (28h)` | Opcode: 0x28

| Field | Value |
|-------|-------|
| LUN/LBA/Chunk/Cnt | 同 Step L.1 pattern |

**Expected**: `GOOD Status` (all 10)。

---

### Step L.4: Idle 500ms~2s

**Expected**: Idle timeout。

---

### Step L.5: Read Compare All Card

**SCSI CMD**: `READ(10) (28h)` — All Card

**Expected**: `GOOD Status`, `Data Match All`。

---

## 附錄

| Opcode | Command | 使用 |
|:---|:---|:---|
| 0x00 | TEST UNIT READY | 0.1 |
| 0x25 | READ CAPACITY(10) | 0.2 |
| 0x28 | READ(10) | L.3, L.5 |
| 0x2A | WRITE(10) | L.1 |

---

## 自我驗證
- Tree leaf: 0.1,0.2(2)+L.1~L.5(5)=7 | `### Step`: 7 ✓ | All `→ Expected:` ✓
