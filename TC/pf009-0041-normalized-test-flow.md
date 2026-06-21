---
title: PF009_0041_IllegalCmd_Diff_PowerMode-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf009_0041, scsi-cmd, power-mode, sleep, powerdown, illegal-cmd, check-condition]
description: >
  PF009_0041 Illegal Command in Different Power Mode — 在 Sleep / PowerDown
  模式下發送非法的 SCSI Command 與 Task Management Function，驗證應回
  CHECK CONDITION (SENSE KEY=NOT_READY)、TMF Fail (Task_Fun_Failed)。
  SSU START/STOP LUN 也應回 CHECK CONDITION。
  PowerDown 中發送 Sleep parameter → CHECK CONDITION (ILLEGAL_REQUEST)。
sources:
  - JIRA: PF009_0041 (SYSTCUFS-206)
  - UFS Spec: JESD220H Section 10.2.5 (Power Conditions), Section 10.7.2 (Status), Section 10.7.3 (TMF)
---

# PF009_0041 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

驗證在 Sleep Mode 與 PowerDown Mode 下：
1. 所有 SCSI Command 應回 `CHECK CONDITION`, `SENSE KEY = NOT_READY (02h)`
2. 所有 Task Management Function 應回 `FUNCTION FAILED`
3. `SSU START LUN` / `SSU STOP LUN` 應回 `CHECK CONDITION`, `SENSE KEY = NOT_READY`, `ASC = LOGICAL UNIT NOT READY`
4. 在 PowerDown 中發送 `SSU with Sleep parameter` 應回 `CHECK CONDITION`, `SENSE KEY = ILLEGAL_REQUEST (05h)`

## JIRA Step 對照

| JIRA Step | 原始描述 | 正規化後對應 |
|-----------|---------|-------------|
| Step 1 | Switch to Sleep Mode | Phase 1 |
| Step 2 | Send all illegal SCSI cmds | Step 1.2 |
| Step 3 | Send all TMF | Step 1.3 |
| Step 4 | SSU START LUN | Step 1.4 |
| Step 5 | SSU STOP LUN | Step 1.5 |
| Step 6 | Hibernate→SSU START | Step 1.6 |
| Step 7 | Hibernate→SSU STOP | Step 1.7 |
| Step 8 | Switch to PowerDown | Phase 2 |
| Step 9-14 | (同 Sleep 的測試) | Phase 2 Steps |
| Step 15 | SSU Sleep in PowerDown | Step 2.8 |

---

## 測試架構

```
PF009_0041 Test Flow
│
├── Phase 0: 初始化
│   ├── Step 0.1: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│   └── Step 0.2: READ CAPACITY(10) — 取得 LUN 資訊 → Expected: GOOD Status
│
├── Phase 1: Sleep Mode — 非法命令測試
│   ├── Step 1.1: START STOP UNIT → Sleep — 進入 Sleep → Expected: GOOD Status
│   ├── Step 1.2: SCSI Commands — 發送非法 SCSI CMD → Expected: CHECK CONDITION, SENSE_KEY=NOT_READY(02h)
│   ├── Step 1.3: Task Management Functions — 發送所有 TMF → Expected: FUNCTION FAILED
│   ├── Step 1.4: SSU START LUN — 在 Sleep 中啟動 LUN → Expected: CHECK CONDITION, SENSE_KEY=NOT_READY, ASC=LOGICAL UNIT NOT READY
│   ├── Step 1.5: SSU STOP LUN — 在 Sleep 中停止 LUN → Expected: CHECK CONDITION, SENSE_KEY=NOT_READY, ASC=LOGICAL UNIT NOT READY
│   ├── Step 1.6: Hibernate Enter→Exit→SSU START LUN → Expected: CHECK CONDITION, SENSE_KEY=NOT_READY, ASC=LOGICAL UNIT NOT READY
│   └── Step 1.7: Hibernate Enter→Exit→SSU STOP LUN → Expected: CHECK CONDITION, SENSE_KEY=NOT_READY, ASC=LOGICAL UNIT NOT READY
│
└── Phase 2: PowerDown Mode — 非法命令測試
    ├── Step 2.1: START STOP UNIT → PowerDown — 進入 PowerDown → Expected: GOOD Status
    ├── Step 2.2: SCSI Commands — 發送非法 SCSI CMD → Expected: CHECK CONDITION, SENSE_KEY=NOT_READY(02h)
    ├── Step 2.3: Task Management Functions — 發送所有 TMF → Expected: FUNCTION FAILED
    ├── Step 2.4: SSU START LUN → Expected: CHECK CONDITION, SENSE_KEY=NOT_READY, ASC=LOGICAL UNIT NOT READY
    ├── Step 2.5: SSU STOP LUN → Expected: CHECK CONDITION, SENSE_KEY=NOT_READY, ASC=LOGICAL UNIT NOT READY
    ├── Step 2.6: Hibernate Enter→Exit→SSU START LUN → Expected: CHECK CONDITION, SENSE_KEY=NOT_READY, ASC=LOGICAL UNIT NOT READY
    ├── Step 2.7: Hibernate Enter→Exit→SSU STOP LUN → Expected: CHECK CONDITION, SENSE_KEY=NOT_READY, ASC=LOGICAL UNIT NOT READY
    └── Step 2.8: SSU Sleep in PowerDown — PowerDown 中發送 Sleep → Expected: CHECK CONDITION, SENSE_KEY=ILLEGAL_REQUEST(05h)
```

---

## Phase 0 — 初始化

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

### Step 0.2: 取得 LUN 資訊

**SCSI CMD**: `READ CAPACITY(10) (25h)`

| Field | Value |
|-------|-------|
| Opcode | 0x25 |
| LUN | All LUNs |

**Expected**: `GOOD Status`。

---

## Phase 1 — Sleep Mode 非法命令測試

### Step 1.1: 進入 Sleep Mode

**SCSI CMD**: `START STOP UNIT (1Bh)`

| Field | Value |
|-------|-------|
| Opcode | 0x1B |
| START bit | 1 |
| Power Condition | 0x2 (Sleep) |

**Expected**: `GOOD Status`，Device 進入 Sleep。

**UFS SPEC Reference**: JESD220H Section 10.2.5 (Sleep Mode)

---

### Step 1.2: 發送非法 SCSI Commands

**目的**: 在 Sleep Mode 下發送所有 SCSI commands（WRITE, READ, UNMAP, SYNCHRONIZE CACHE 等）。

**Test Commands**:

| Command | Opcode |
|:---|:---|
| WRITE(10) | 0x2A |
| READ(10) | 0x28 |
| UNMAP | 0x42 |
| SYNCHRONIZE CACHE(10) | 0x35 |
| VERIFY(10) | 0x2F |
| WRITE BUFFER | 0x3B |
| TEST UNIT READY | 0x00 |

**Expected**: `CHECK CONDITION`, `SENSE KEY = NOT_READY (02h)`。

**UFS SPEC Reference**: JESD220H Section 10.2.5, Section 10.7.2; SAM-5 5.3

---

### Step 1.3: 發送 Task Management Functions

**目的**: 在 Sleep Mode 下發送所有 TMF。

**Test TMFs**:

| TMF | Function |
|:---|:---|
| ABORT TASK | 0x01 |
| LOGICAL UNIT RESET | 0x08 |
| QUERY TASK | 0x80 |

**Expected**: `Response == FUNCTION FAILED`。

**UFS SPEC Reference**: JESD220H Section 10.7.3 (TMF), Section 10.2.5

---

### Step 1.4: SSU START LUN in Sleep

**SCSI CMD**: `START STOP UNIT (1Bh)` — Start LUN

| Field | Value |
|-------|-------|
| Opcode | 0x1B |
| START bit | 1 (Start) |
| Power Condition | 0x0 (Active) |

**Expected**: `CHECK CONDITION`, `SENSE KEY = NOT_READY (02h)`, `ASC = LOGICAL UNIT NOT READY (04h/00h)`。

**UFS SPEC Reference**: JESD220H Section 10.2.5

---

### Step 1.5: SSU STOP LUN in Sleep

**SCSI CMD**: `START STOP UNIT (1Bh)` — Stop

| Field | Value |
|-------|-------|
| Opcode | 0x1B |
| START bit | 0 (Stop) |

**Expected**: `CHECK CONDITION`, `SENSE KEY = NOT_READY`, `ASC = LOGICAL UNIT NOT READY`。

---

### Step 1.6: Hibernate→Exit→SSU START LUN

**目的**: Sleep Mode → Hibernate Enter → Hibernate Exit → SSU START LUN。

**Expected**: `CHECK CONDITION`, `SENSE KEY = NOT_READY`, `ASC = LOGICAL UNIT NOT READY`。

**UFS SPEC Reference**: JESD220H Section 10.2.5 (Hibernate)

---

### Step 1.7: Hibernate→Exit→SSU STOP LUN

**目的**: Sleep Mode → Hibernate Enter → Hibernate Exit → SSU STOP LUN。

**Expected**: `CHECK CONDITION`, `SENSE KEY = NOT_READY`, `ASC = LOGICAL UNIT NOT READY`。

---

## Phase 2 — PowerDown Mode 非法命令測試

### Step 2.1: 進入 PowerDown Mode

**SCSI CMD**: `START STOP UNIT (1Bh)`

| Field | Value |
|-------|-------|
| Opcode | 0x1B |
| START bit | 1 |
| Power Condition | 0x3 (Power Down) |

**Expected**: `GOOD Status`，Device 進入 PowerDown。

**UFS SPEC Reference**: JESD220H Section 10.2.5 (Power Down Mode)

---

### Step 2.2: 發送非法 SCSI Commands（PowerDown）

（同 Step 1.2 的命令清單，在 PowerDown mode 下執行）

**Expected**: `CHECK CONDITION`, `SENSE KEY = NOT_READY (02h)`。

---

### Step 2.3: Task Management Functions（PowerDown）

（同 Step 1.3 的 TMF 清單，在 PowerDown mode 下執行）

**Expected**: `Response == FUNCTION FAILED`。

---

### Step 2.4: SSU START LUN（PowerDown）

**Expected**: `CHECK CONDITION`, `SENSE KEY = NOT_READY`, `ASC = LOGICAL UNIT NOT READY`。

---

### Step 2.5: SSU STOP LUN（PowerDown）

**Expected**: `CHECK CONDITION`, `SENSE KEY = NOT_READY`, `ASC = LOGICAL UNIT NOT READY`。

---

### Step 2.6: Hibernate→Exit→SSU START LUN（PowerDown）

**Expected**: `CHECK CONDITION`, `SENSE KEY = NOT_READY`, `ASC = LOGICAL UNIT NOT READY`。

---

### Step 2.7: Hibernate→Exit→SSU STOP LUN（PowerDown）

**Expected**: `CHECK CONDITION`, `SENSE KEY = NOT_READY`, `ASC = LOGICAL UNIT NOT READY`。

---

### Step 2.8: SSU Sleep in PowerDown

**SCSI CMD**: `START STOP UNIT (1Bh)` — Sleep parameter

**目的**: 在 PowerDown mode 中發送 SSU with Sleep Power Condition，驗證回 ILLEGAL_REQUEST。

| Field | Value |
|-------|-------|
| Opcode | 0x1B |
| START bit | 1 |
| Power Condition | 0x2 (Sleep) |

**Expected**: `CHECK CONDITION`, `SENSE KEY = ILLEGAL_REQUEST (05h)`。

**UFS SPEC Reference**: JESD220H Section 10.2.5 (Power Condition transitions)

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | Step 0.1 |
| 0x1B | START STOP UNIT | 6 | Step 1.1, 1.4, 1.5, 2.1, 2.4, 2.5, 2.8 |
| 0x25 | READ CAPACITY(10) | 10 | Step 0.2 |

## Power Condition 對照

| Code | Mode | Description |
|:---|:---|:---|
| 0x0 | Active | Normal operation |
| 0x1 | Idle | Low power (not used in this pattern) |
| 0x2 | Sleep | SCSI commands rejected → NOT_READY |
| 0x3 | Power Down | SCSI commands rejected → NOT_READY |

## SENSE KEY 對照

| Code | Name | 使用位置 |
|:---|:---|:---|
| 0x02 | NOT READY | Step 1.2, 1.4~1.7, 2.2, 2.4~2.7 |
| 0x05 | ILLEGAL REQUEST | Step 2.8 |

---

## 自我驗證

- Tree Diagram leaf steps: 0.1, 0.2 (2) + 1.1~1.7 (7) + 2.1~2.8 (8) = 17
- `### Step` sections: 0.1, 0.2 (2) + 1.1~1.7 (7) + 2.1~2.8 (8) = 17 ✓
