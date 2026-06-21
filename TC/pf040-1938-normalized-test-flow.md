---
title: PF040_1938_CrossTemp_ATS_Seq_Perf-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf040_1938, scsi-cmd, cross-temp, ats, performance, seq-read, seq-write]
description: >
  PF040_1938 CrossTemp ATS SeqW SeqR Perf Test — 跨溫度 Sequential Write/Read
  效能測試，包含溫度切換前後的 Read 比對。
sources:
  - JIRA: PF040_1938 (SYSTCUFS-2239)
---

# PF040_1938 正規化 Test Flow（SCSI CMD 単位）

## 測試架構（Tree Diagram — 含 Expected）

```
PF040_1938 Test Flow
│
├── Phase 0: 初始化
│   └── Step 0.1: VU — TT Enable (KIC project) → Expected: TT enabled
│
└── Loop (X times, ARG56)
    ├── Step 1.1: UNMAP — Wipe → Expected: GOOD Status
    ├── Step 1.2: Idle X min (ARG54, default 15min) → Expected: 等待溫度穩定
    ├── Step 1.3: WRITE(10) — Seq 512KB, QD32, 0~1GB range, shift to next GB → Expected: GOOD Status
    ├── Step 1.4: Idle X min → Expected: 等待 BKOPS
    ├── Step 1.5: READ(10) — Seq, 0~1GB, shift to next GB (full card) → Expected: GOOD Status
    ├── Step 1.6: QUERY Read Attribute (bBackgroundOpStatus) — poll until 0x00 → Expected: bBackgroundOpStatus == 0x00
    ├── Step 1.7: START STOP UNIT — SSU PowerDown + All Power Off → Expected: GOOD Status
    ├── Step 1.8: Change Temperature + Idle 15min → Expected: 溫度已切換
    ├── Step 1.9: READ(10) — Seq cross-temp read (full card) → Expected: GOOD Status
    └── Step 1.10: READ(10) — Seq second cross-temp read → Expected: GOOD Status
```

---

## Phase 0

### Step 0.1: VU TT Enable

**目的**: KIC project TT enable。

**Expected**: `TT enabled`。

---

## Loop

### Step 1.1: Wipe

**SCSI CMD**: `UNMAP (42h)`

**Expected**: `GOOD Status`。

### Step 1.2: Idle

**Expected**: 等待溫度穩定。

### Step 1.3: Seq Write

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| Transfer Length | 512KB |
| QD | 32 |
| LBA Range | 0~1GB per iteration, shift to next GB |

**Expected**: `GOOD Status`。

### Step 1.4: Idle

**Expected**: 等待 BKOPS 穩定。

### Step 1.5: Seq Read

**SCSI CMD**: `READ(10) (28h)`

**Expected**: `GOOD Status`。

### Step 1.6: BKOPS Idle

**UFS QUERY**: `READ ATTRIBUTE (bBackgroundOpStatus, 0x14)`

**Expected**: `bBackgroundOpStatus == 0x00`。

### Step 1.7: Power Down

**SCSI CMD**: `START STOP UNIT (1Bh)`

**Expected**: `GOOD Status`。

### Step 1.8: Change Temperature

**Expected**: 溫度已切換，idle 15min。

### Step 1.9~1.10: Cross-Temp Seq Read

**SCSI CMD**: `READ(10) (28h)`

**Expected**: `GOOD Status`。

---

## 自我驗證

- Tree Diagram leaf steps: **11** (0.1=1, 1.1~1.10=10)
- `### Step` sections: **11** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
