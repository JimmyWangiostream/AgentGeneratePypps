---
title: PF004_0001_CmdQueueDepth-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf004_0001, scsi-cmd, command-queue, task-set-full, busy]
description: >
  PF004_0001 Command Queue Depth Test — 驗證 UFS Device 的 Command Queue Depth
  行為：同 LUN 內超出深度應回 TASK SET FULL，跨 LUN 超出深度應回 BUSY。
sources:
  - JIRA: PF004_0001 (SYSTCUFS-214)
  - UFS Spec: JESD220H Section 14.1.4.2 (Device Descriptor), Section 10.6 (Command Queue), Section 10.7.2 (Status)
---

# PF004_0001 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

驗證 UFS Device Command Queue Depth 的正確行為：
1. 讀取 Queue Depth 參數
2. 在 Queue Depth 範圍內發送 Write/Read → 應全部 GOOD
3. 同 LUN 內超出 Queue Depth → 應回 TASK SET FULL（非 BUSY）
4. 跨 LUN 超出 Queue Depth → 應回 BUSY

## JIRA Step 對照

| JIRA Step | 原始描述 | 正規化後對應 |
|-----------|---------|-------------|
| Step 1 | Get LUN command queue depth | Step 0.2 |
| Step 2 | Send W/R within depth | Phase 1 |
| Step 3 | Send write over depth (same LUN) | Phase 2 |
| Step 4 | Check TASK SET FULL (not BUSY) | Step 2.3 |
| Step 5 | Send command over depth (different LUN) | Phase 3 |
| Step 6 | Check BUSY | Step 3.3 |

---

## 測試架構

```
PF004_0001 Test Flow
│
├── Phase 0: 初始化與 Queue Depth 查詢
│   ├── Step 0.1: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│   └── Step 0.2: QUERY Read Descriptor (Device Descriptor) — 讀取 bCommandQueueDepth → Expected: QUERY RESPONSE Success, 回傳 Queue Depth 值
│
├── Phase 1: 正常 Queue Depth 範圍內 W/R
│   ├── Step 1.1: WRITE(10) × QD — 同 LUN 發送 QD 個 Write → Expected: GOOD Status (all)
│   ├── Step 1.2: SYNCHRONIZE CACHE(10) — 確認所有 Write 完成 → Expected: GOOD Status
│   └── Step 1.3: READ(10) × QD — 同 LUN 發送 QD 個 Read → Expected: GOOD Status (all)
│
├── Phase 2: 同 LUN 超出 Queue Depth → TASK SET FULL
│   ├── Step 2.1: WRITE(10) × QD — 填滿同 LUN Queue → Expected: GOOD Status (前 QD 個)
│   ├── Step 2.2: WRITE(10) × 1 — 同 LUN 再發一個 Write → Expected: TASK SET FULL (28h)
│   └── Step 2.3: 驗證 Status ≠ BUSY → Expected: Status 為 TASK SET FULL, NOT BUSY(08h)
│
└── Phase 3: 跨 LUN 超出 Queue Depth → BUSY
    ├── Step 3.1: WRITE(10) × QD — 填滿 LUN0 Queue → Expected: GOOD Status (前 QD 個)
    ├── Step 3.2: WRITE(10) × 1 — 對 LUN1 發送 → Expected: BUSY (08h)
    └── Step 3.3: 驗證 Status == BUSY → Expected: Status 為 BUSY(08h)
```

---

## Phase 0 — 初始化與 Queue Depth 查詢

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

### Step 0.2: 讀取 Command Queue Depth

**UFS QUERY**: `READ DESCRIPTOR (Device Descriptor)`

**目的**: 從 Device Descriptor 的 `bCommandQueueDepth` 欄位取得支援的 Queue Depth。

| Field | Value |
|-------|-------|
| Query Opcode | 0x07 (READ DESCRIPTOR) |
| IDN | 0x00 (Device Descriptor) |
| Index | 0x00 |
| Selector | 0x00 |
| Length | 0x40 |

**Expected**: `QUERY RESPONSE Success`，回傳 `bCommandQueueDepth` 值。設 `QD = bCommandQueueDepth`。

**UFS SPEC Reference**: JESD220H Section 14.1.4.2 (Device Descriptor, bCommandQueueDepth)

---

## Phase 1 — 正常 Queue Depth 範圍內 W/R

### Step 1.1: 同 LUN 發送 QD 個 WRITE(10)

**SCSI CMD**: `WRITE(10) (2Ah)` × QD

**目的**: 在同一個 LUN 上發送 Queue Depth 數量的 Write 命令，驗證全部正常接收。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | LUN0（固定） |
| Logical Block Address | 遞增 LBA（每個 cmd 不同） |
| Transfer Length | 100 blocks (51200 bytes) |
| Command Count | QD (from Step 0.2) |

**Expected**: `GOOD Status`（全部 QD 個命令）。

**UFS SPEC Reference**: JESD220H Section 10.6 (Command Queue), SBC-4 5.43

---

### Step 1.2: Flush Cache

**SCSI CMD**: `SYNCHRONIZE CACHE(10) (35h)`

**目的**: 確保 Step 1.1 的所有 Write 完成。

| Field | Value |
|-------|-------|
| Opcode | 0x35 |
| LUN | LUN0 |
| Logical Block Address | 0x00000000 |
| Number of Blocks | 0x0000 (All) |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.24

---

### Step 1.3: 同 LUN 發送 QD 個 READ(10)

**SCSI CMD**: `READ(10) (28h)` × QD

**目的**: 驗證同 LUN 可在 Queue Depth 範圍內正常排隊 Read。

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | LUN0 |
| Logical Block Address | Step 1.1 寫入之 LBA（對應） |
| Transfer Length | 100 blocks |
| Command Count | QD |

**Expected**: `GOOD Status`（全部 QD 個命令）+ `Data Match`。

**UFS SPEC Reference**: JESD220H Section 10.6, SBC-4 5.18

---

## Phase 2 — 同 LUN 超出 Queue Depth → TASK SET FULL

### Step 2.1: 同 LUN 填滿 Queue

**SCSI CMD**: `WRITE(10) (2Ah)` × QD

**目的**: 發送 QD 個 Write 命令填滿同 LUN 的 Command Queue。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | LUN0 |
| Logical Block Address | 遞增 LBA |
| Transfer Length | 100 blocks |
| Command Count | QD |

**Expected**: `GOOD Status`（前 QD 個）。

**UFS SPEC Reference**: JESD220H Section 10.6

---

### Step 2.2: 同 LUN 超發一個 Write

**SCSI CMD**: `WRITE(10) (2Ah)` × 1

**目的**: 在 Queue 已滿的同 LUN 上再發一個 Write，預期被拒絕。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | LUN0（同 LUN） |
| Logical Block Address | 遞增 LBA（下一個） |
| Transfer Length | 100 blocks |

**Expected**: `TASK SET FULL (28h)`。

**UFS SPEC Reference**: JESD220H Section 10.7.2 (Status), SAM-5 5.3.2 (TASK SET FULL)

---

### Step 2.3: 驗證 Status 為 TASK SET FULL（非 BUSY）

**目的**: 確認收到的 Status 是 TASK SET FULL (28h) 而非 BUSY (08h)。

**Expected**: `Status == TASK SET FULL (28h)`, `Status != BUSY (08h)`。

**UFS SPEC Reference**: JESD220H Section 10.7.2; SAM-5 5.3.2

---

## Phase 3 — 跨 LUN 超出 Queue Depth → BUSY

### Step 3.1: 填滿 LUN0 Queue

**SCSI CMD**: `WRITE(10) (2Ah)` × QD

**目的**: 先以 QD 個 Write 填滿 LUN0 的 Queue。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | LUN0 |
| Logical Block Address | 遞增 LBA |
| Transfer Length | 100 blocks |
| Command Count | QD |

**Expected**: `GOOD Status`（前 QD 個）。

**UFS SPEC Reference**: JESD220H Section 10.6

---

### Step 3.2: 對不同 LUN 發送 Write

**SCSI CMD**: `WRITE(10) (2Ah)` × 1

**目的**: LUN0 Queue 已滿，對 LUN1 發送 Write，預期回 BUSY。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | LUN1（不同於 LUN0） |
| Logical Block Address | 0x00000000 |
| Transfer Length | 100 blocks |

**Expected**: `BUSY (08h)`。

**UFS SPEC Reference**: JESD220H Section 10.7.2; SAM-5 5.3.2

---

### Step 3.3: 驗證 Status == BUSY

**目的**: 確認跨 LUN 超出 Queue Depth 回 BUSY。

**Expected**: `Status == BUSY (08h)`。

**UFS SPEC Reference**: JESD220H Section 10.7.2; SAM-5 5.3.2

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | Step 0.1 |
| 0x28 | READ(10) | 10 | Step 1.3 |
| 0x2A | WRITE(10) | 10 | Step 1.1, 2.1, 2.2, 3.1, 3.2 |
| 0x35 | SYNCHRONIZE CACHE(10) | 10 | Step 1.2 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 存取 | 使用位置 |
|:---|:---|:---|:---|:---|
| 0x00 | Device Descriptor | 0x07 (READ DESCRIPTOR) | R | Step 0.2 |

## SCSI Status 對照

| Status Code | Name | 說明 |
|:---|:---|:---|
| 0x00 | GOOD | 正常完成 |
| 0x08 | BUSY | LU 忙碌 |
| 0x28 | TASK SET FULL | Command Queue 已滿（同 LUN） |

---

## 自我驗證

- Tree Diagram leaf steps: **9** (0.1, 0.2, 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3 = 11)
- Wait recount: 0.1+0.2=2, 1.1+1.2+1.3=3, 2.1+2.2+2.3=3, 3.1+3.2+3.3=3. Total=11
- `### Step` sections: Step 0.1-0.2 (2), Step 1.1-1.3 (3), Step 2.1-2.3 (3), Step 3.1-3.3 (3) = 11 ✓
