---
title: PF045_1352_HPB2_HCM_Recommend-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf045_1352, scsi-cmd, hpb, hcm, recommend, hpb20]
description: >
  PF045_1352 HPB 2.0 Host Control Mode Recommend Test — 驗證 HCM 下
  READ/WRITE/UNMAP 觸發 HPB Recommend 及 HPB_RESET 行為。
sources:
  - JIRA: PF045_1352 (SYSTCUFS-1597)
  - JESD220-3 (HPB Extension)
---

# PF045_1352 正規化 Test Flow（SCSI CMD 単位）

## IC 相容性

| 條件 | 8325 B58R, UFS >= 3.1, HPB >= 2.0 |
|:---|:---|

## 測試架構（Tree Diagram — 含 Expected）

```
PF045_1352 Test Flow
│
├── Phase 0: 初始化
│   ├── Step 0.1: HW Check (8325 B58R, UFS 3.1, HPB >= 2.0) → Expected: 支援, 否則 NOT SUPPORTED
│   ├── Step 0.2: QUERY Write Descriptor — Config LUN0 = HPB LUN, Host Control Mode → Expected: QUERY RESPONSE Success
│   └── Step 0.3: QUERY Set Flag (fHPBEn) → Expected: QUERY RESPONSE Success
│
└── Loop (burn-in)
    ├── Test T.1: Write region → READ(10) → expect NO recommend → Expected: NO HPB Recommend
    ├── Step T.2: HPB READ BUFFER (0xF9) — Activate Region 0~max, BufferID=1 → Expected: HPB Region activated
    ├── Case 1: READ(10) — outside active region, len<=8 → expect recommend → Expected: HPB Recommend received
    ├── Case 2: WRITE(10) — inside active region, len=rand → expect recommend → Expected: HPB Recommend received
    ├── Case 3: UNMAP — inside active region, len=rand → expect recommend → Expected: HPB Recommend received
    ├── Step T.3: QUERY Write Descriptor — Config change / Enable reliable write → Expected: QUERY RESPONSE Success
    └── Step T.4: READ(10) — activation subregion, len<=1 → expect HPB_RESET(0x02) → Expected: HPB type == HPB_RESET(0x02)
```

---

## Phase 0

### Step 0.1: HW Check

| Check | Expected |
|-------|---------|
| IC | 8325 B58R |
| UFS | >= 3.1 |
| HPB | >= 2.0 |

### Step 0.2: Config HPB LUN + HCM

**UFS QUERY**: `WRITE DESCRIPTOR (Configuration Descriptor)`

**Expected**: `QUERY RESPONSE Success`。

### Step 0.3: Enable HPB

**UFS QUERY**: `SET FLAG (fHPBEn)`

**Expected**: `QUERY RESPONSE Success`。

---

## Loop

### Test T.1: Write + No Recommend

| Step | SCSI CMD | Expected |
|:---|:---|:---|
| Write region | WRITE(10) (0x2A) | GOOD Status |
| Read | READ(10) (0x28) | NO HPB Recommend |

### Step T.2: HPB READ BUFFER Activate

| Field | Value |
|-------|-------|
| Opcode | 0xF9 (HPB READ BUFFER) |
| Region | 0 ~ max |
| Buffer ID | 1 |

**Expected**: `HPB Region activated`。

### Case 1~3: Recommend Triggers

| Case | CMD | Condition | Expected |
|:---|:---|:---|:---|
| 1 | READ(10) | outside active region, len<=8 | HPB Recommend |
| 2 | WRITE(10) | inside active region, random len | HPB Recommend |
| 3 | UNMAP | inside active region, random len | HPB Recommend |

### Step T.3: Config Change

**UFS QUERY**: `WRITE DESCRIPTOR` — Config change / Enable reliable write。

**Expected**: `QUERY RESPONSE Success`。

### Step T.4: Verify HPB_RESET

**SCSI CMD**: `READ(10) (28h)` — activation subregion, len<=1

**Expected**: `HPB type == HPB_RESET (0x02)`。

---

## 自我驗證

- Tree Diagram leaf steps: **11** (0.1~0.3=3, T.1=1, T.2=1, Case1~3=3, T.3=1, T.4=1)
- `### Step` sections: **11** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
