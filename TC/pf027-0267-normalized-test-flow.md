---
title: PF027_0267_PowerState_Latency-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf027_0267, scsi-cmd, power-state, sleep, powerdown, latency, performance]
description: >
  PF027_0267 Power State Latency Test — 量測 START STOP UNIT 進入/退出 Sleep 與
  PowerDown 狀態的延遲，共 8 種路徑組合（±VCC off, ±Hibernate）。
sources:
  - JIRA: PF027_0267 (SYSTCUFS-235)
  - UFS Spec: JESD220H Section 7.4 (Power Modes), Section 11.3.9 (START STOP UNIT)
---

# PF027_0267 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

量測 START STOP UNIT 進入 Sleep / PowerDown 與回到 Active 的延遲。
測試矩陣：Sleep×4 路徑 + PowerDown×4 路徑（±VCC off, ±Hibernate）。

## 8 種轉換路徑

| Scenario | 起始狀態 | VCC Off | Hibernate |
|:---|:---|:---|:---|
| A | Sleep | No | No |
| B | Sleep | Yes | No |
| C | Sleep | No | Yes |
| D | Sleep | Yes | Yes |
| E | PowerDown | No | No |
| F | PowerDown | Yes | No |
| G | PowerDown | No | Yes |
| H | PowerDown | Yes | Yes |

## 測試架構（Tree Diagram — 含 Expected）

```
PF027_0267 Test Flow
│
├── Phase 0: Precondition
│   ├── Step 0.1: Performance Precondition — Seq Write full card → Expected: GOOD Status
│   └── Step 0.2: QUERY Read Attribute (bBackgroundOpStatus, 0x14) — BKOPS Idle → Expected: bBackgroundOpStatus == 0x00
│
└── Loop (8 Scenarios: A~H)
    │
    ├── Step S.1: START STOP UNIT — Enter Sleep/PowerDown + Record Latency → Expected: GOOD Status
    └── Step S.2: START STOP UNIT — Return to Active + Record Latency → Expected: GOOD Status
```

---

## Phase 0 — Precondition

### Step 0.1: Performance Precondition

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: 對卡片進行 Sequential Write 使 Media 進入穩定效能狀態。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Logical Block Address | 0x00000000 |
| Transfer Length | 512KB per chunk, full card |

**Expected**: `GOOD Status`。

---

### Step 0.2: 確認 BKOPS Idle

**UFS QUERY**: `READ ATTRIBUTE (bBackgroundOpStatus, IDN 0x14)`

**目的**: 每個 Scenario 執行前確認 BKOPS 處於 Idle，避免背景操作干擾延遲量測。

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x14 (bBackgroundOpStatus) |

**Expected**: `bBackgroundOpStatus == 0x00`（BKOPS Idle）。

---

## Loop — 8 Power State Scenarios

### Step S.1: Enter Power State + Latency

**SCSI CMD**: `START STOP UNIT (1Bh)`

**目的**: 進入 Sleep 或 PowerDown 狀態，記錄延遲。

| Field | Sleep | PowerDown |
|:---|:---|:---|
| Opcode | 0x1B | 0x1B |
| START bit | 0 (Stop) | 0 (Stop) |
| POWER CONDITION | 0x02 (Sleep) | 0x03 (PowerDown) |
| VCC Off | Per Scenario | Per Scenario |
| Hibernate | Per Scenario | Per Scenario |

**Expected**: `GOOD Status`。記錄 Latency = CMD sent → completion received。

**UFS SPEC Reference**: JESD220H Section 11.3.9 (START STOP UNIT)

---

### Step S.2: Return to Active + Latency

**SCSI CMD**: `START STOP UNIT (1Bh)`

**目的**: 從 Sleep/PowerDown 回到 Active 狀態，記錄延遲。

| Field | Value |
|-------|-------|
| Opcode | 0x1B |
| START bit | 1 (Start) |
| POWER CONDITION | 0x01 (Active) |

**Expected**: `GOOD Status`。記錄 Latency = CMD sent → completion received。

**UFS SPEC Reference**: JESD220H Section 11.3.9

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x1B | START STOP UNIT | 6 | Step S.1, S.2 |
| 0x2A | WRITE(10) | 10 | Step 0.1 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 使用位置 |
|:---|:---|:---|:---|
| 0x14 | bBackgroundOpStatus | 0x03 (READ ATTRIBUTE) | Step 0.2 |

---

## 自我驗證

- Tree Diagram leaf steps: **5** (0.1, 0.2, S.1, S.2 — S.1/S.2 iterate per scenario)
- `### Step` sections: **5** ✓ (S.1 covers all enter ops; S.2 covers all exit ops)
- 每個 leaf step 都有 `→ Expected:` ✓
