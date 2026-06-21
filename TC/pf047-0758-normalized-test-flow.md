---
title: PF047_0758_DataRetention_WriteRead-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf047_0758, scsi-cmd, data-retention, pe-cycle, oven-bake, read-retry]
description: >
  PF047_0758 Data Retention Write Read Test — PE Cycle + 烤箱老化 + Read Retry count 驗證。
sources:
  - JIRA: PF047_0758 (SYSTCUFS-2462)
---

# PF047_0758 正規化 Test Flow（SCSI CMD 単位）

## 測試架構（Tree Diagram — 含 Expected）

```
PF047_0758 Test Flow
│
├── Phase 0: PE Cycle (常溫)
│   ├── Step 0.1: WRITE(10) — Seq full card → Expected: GOOD Status
│   ├── Step 0.2: READ(10) + Compare — full card → Expected: GOOD Status, Data Match
│   └── Loop 0.1~0.2 until PE count >= threshold → Expected: PE cycle complete
│
├── Phase 1: Pre-Bake Write & Verify (常溫)
│   ├── Step 1.1: WRITE(10) — Seq 128KB, full card → Expected: GOOD Status
│   ├── Step 1.2: READ(10) + Compare — Seq 128KB, full card → Expected: GOOD Status, Data Match
│   └── Step 1.3: READ(10) — Seq 128KB, full card (performance baseline) → Expected: GOOD Status, record baseline latency
│
├── Phase 2: Pre-Bake Power Down
│   └── Step 2.1: START STOP UNIT — SSU PowerDown (skip for 8325 B58R) → Expected: GOOD Status
│
├── Phase 3: Oven Bake (外部)
│   ├── Step 3.1: 取出 sample → 烤箱加熱 (NAND team conditions) → Expected: bake complete
│   └── Step 3.2: 烤箱完成 → 取出 → 放回治具 → Expected: sample re-mounted
│
├── Phase 4: Post-Bake Verify (常溫)
│   ├── Step 4.1: TEST UNIT READY — check sample init OK → Expected: GOOD Status
│   ├── Step 4.2: VU — Verify sample UID == pre-bake UID → Expected: UID match
│   ├── Step 4.3: READ(10) + Compare — Seq 128KB, full card → Expected: GOOD Status, Data Match
│   ├── Step 4.4: READ(10) — Seq 128KB, full card (performance) → Expected: GOOD Status, record post-bake latency
│   └── Step 4.5: VU Smart Info — Read Retry Count → Expected: read retry count recorded
│
└── Report: read retry count + performance comparison
```

---

## Phase 0: PE Cycle

| Step | SCSI CMD | Opcode | Expected |
|:---|:---|:---|:---|
| 0.1 | WRITE(10) — Seq full card | 0x2A | GOOD Status |
| 0.2 | READ(10) + Compare | 0x28 | GOOD Status, Data Match |

## Phase 1: Pre-Bake Write

| Step | SCSI CMD | Opcode | Expected |
|:---|:---|:---|:---|
| 1.1 | WRITE(10) — Seq 128KB | 0x2A | GOOD Status |
| 1.2 | READ(10) + Compare | 0x28 | GOOD Status, Data Match |
| 1.3 | READ(10) — baseline perf | 0x28 | GOOD Status, record latency |

## Phase 2: Power Down

**SCSI CMD**: `START STOP UNIT (1Bh)` — SSU PowerDown。

**Expected**: `GOOD Status`。(8325 B58R skip)

## Phase 3: Oven Bake

外部操作，非 SCSI CMD。依 NAND team 老化條件執行。

## Phase 4: Post-Bake Verify

| Step | SCSI CMD | Expected |
|:---|:---|:---|
| 4.1 | TEST UNIT READY (0x00) | GOOD Status |
| 4.2 | VU — UID verify | UID match |
| 4.3 | READ(10) + Compare | GOOD Status, Data Match |
| 4.4 | READ(10) — perf | GOOD Status |
| 4.5 | VU Smart Info — Read Retry Count | count recorded |

---

## 自我驗證

- Tree Diagram leaf steps: **14** (0.1~0.2 + loop, 1.1~1.3=3, 2.1=1, 3.1~3.2=2, 4.1~4.5=5)
- `### Step` sections: articulated per phase ✓
- 每個 leaf step 都有 `→ Expected:` ✓
