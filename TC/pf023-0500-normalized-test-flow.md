---
title: PF023_0500_Refresh_Status_Behavior-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf023_0500, scsi-cmd, refresh, status-behavior]
description: >
  PF023_0500 Refresh Status Behavior Test — 驗證 Refresh Status 讀取後重置為 Idle(0)、
  狀態轉換正確性（Idle→InProgress→Success/Stopped→Idle），以及 Queue 非空時 Stop 行為。
sources:
  - JIRA: PF023_0500 (SYSTCUFS-640)
  - UFS Spec: JESD220H Section 13.4.15 (Refresh)
---

# PF023_0500 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

驗證 Refresh 操作的 Status 行為：
1. 每次讀取 bRefreshStatus 後再次讀取應回到 Idle (0)
2. Refresh 狀態轉換：Idle(0) → InProgress(1) → Success(3) or Stopped(2,4) → Idle(0)
3. Queue 非空時 Enable Refresh → bRefreshStatus = 4 (Stopped)
4. Burn-in loop 驗證行為一致性

## Refresh Status 定義

| 值 | 狀態 | 說明 |
|:---|:---|:---|
| 0x00 | Idle | Refresh 未執行，或上次讀取後自動重置 |
| 0x01 | In Progress | Refresh 正在執行中 |
| 0x02 | Stopped | Clear Flag 後停止 |
| 0x03 | Success | Refresh 完成 |
| 0x04 | Stopped (Queue not empty) | Queue 非空時 Enable Refresh 被拒絕 |

## 測試架構（Tree Diagram — 含 Expected）

```
PF023_0500 Test Flow
│
├── Phase 0: Refresh 支援檢查
│   ├── Step 0.1: QUERY Read Attribute (bUFSFeaturesSupport) — Check Refresh bit → Expected: QUERY RESPONSE Success, Refresh bit == 1
│   └── Step 0.2: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│
└── Loop (burn_in 次)
    │
    ├── Phase 1: Status Readback Reset to Idle
    │   ├── Step 1.1: QUERY Set Flag (fRefreshEnable, 0x07) → Expected: QUERY RESPONSE Success
    │   ├── Step 1.2: QUERY Read Attribute (bRefreshStatus, 0x2C) — expect 0 or 1 → Expected: bRefreshStatus == 0x00 or 0x01
    │   ├── Step 1.3: QUERY Read Attribute (bRefreshStatus, 0x2C) — expect 0 → Expected: bRefreshStatus == 0x00
    │   ├── Step 1.4: QUERY Clear Flag (fRefreshEnable, 0x07) → Expected: QUERY RESPONSE Success
    │   ├── Step 1.5: QUERY Read Attribute (bRefreshStatus, 0x2C) — expect 2 → Expected: bRefreshStatus == 0x02
    │   └── Step 1.6: QUERY Read Attribute (bRefreshStatus, 0x2C) — expect 0 → Expected: bRefreshStatus == 0x00
    │
    ├── Phase 2: Refresh Completion + Poll
    │   ├── Step 2.1: QUERY Set Flag (fRefreshEnable, 0x07) → Expected: QUERY RESPONSE Success
    │   ├── Step 2.2: Idle — sleep 20000ms → Expected: 等待 Refresh 執行
    │   ├── Step 2.3: QUERY Read Attribute (bRefreshStatus, 0x2C) — poll until 3 → Expected: bRefreshStatus == 0x03 (Success)
    │   ├── Step 2.4: QUERY Read Attribute (bRefreshStatus, 0x2C) — expect 0 → Expected: bRefreshStatus == 0x00
    │   └── Step 2.5: QUERY Clear Flag (fRefreshEnable, 0x07) → Expected: QUERY RESPONSE Success
    │
    └── Phase 3: Queue 非空時 Enable Refresh
        ├── Step 3.1: WRITE(10) — 全卡寫入 (queue, not sent) → Expected: (queued)
        ├── Step 3.2: QUERY Set Flag (fRefreshEnable, 0x07) → Expected: QUERY RESPONSE Success
        ├── Step 3.3: 發送 Write cmd + Refresh Enable 並行 → Expected: Write: GOOD Status
        ├── Step 3.4: QUERY Read Attribute (bRefreshStatus, 0x2C) — expect 4 → Expected: bRefreshStatus == 0x04
        └── Step 3.5: QUERY Read Attribute (bRefreshStatus, 0x2C) — expect 0 → Expected: bRefreshStatus == 0x00
```

---

## Phase 0 — Refresh 支援檢查

### Step 0.1: 檢查 Refresh 支援

**UFS QUERY**: `READ ATTRIBUTE (bUFSFeaturesSupport, IDN 0x1F)`

**目的**: 確認 Device 支援 Refresh 操作，若不支援則終止測試。

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x1F (bUFSFeaturesSupport) |

**Expected**: `QUERY RESPONSE Success`，Refresh bit == 1。

**UFS SPEC Reference**: JESD220H Section 14.3.1 (bUFSFeaturesSupport), Section 13.4.15 (Refresh)

---

### Step 0.2: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

**目的**: 確認 UFS Device 已上電且可接受命令。

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

## Loop — Burn-in

### Phase 1 — Status Readback Reset to Idle

#### Step 1.1: Enable Refresh

**UFS QUERY**: `SET FLAG (fRefreshEnable, IDN 0x07)`

**目的**: 啟用 Refresh 操作。

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | 0x07 (fRefreshEnable) |
| Flag Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.2 (Flags), Section 13.4.15

---

#### Step 1.2: 讀取 Refresh Status（expect Idle or InProgress）

**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus, IDN 0x2C)`

**目的**: 讀取 Refresh Status，應為 Idle(0) 或 InProgress(1)。

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x2C (bRefreshStatus) |

**Expected**: `bRefreshStatus == 0x00 or 0x01`。

**UFS SPEC Reference**: JESD220H Section 14.3.1 (bRefreshStatus)

---

#### Step 1.3: 再次讀取 Refresh Status（expect Idle）

**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus, IDN 0x2C)`

**目的**: 再次讀取 Refresh Status，確認回到 Idle(0)。

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x2C (bRefreshStatus) |

**Expected**: `bRefreshStatus == 0x00`（回到 Idle）。

**UFS SPEC Reference**: JESD220H Section 14.3.1

---

#### Step 1.4: Clear Refresh Enable

**UFS QUERY**: `CLEAR FLAG (fRefreshEnable, IDN 0x07)`

**目的**: 停用 Refresh。

| Field | Value |
|-------|-------|
| Query Opcode | 0x05 (CLEAR FLAG) |
| Flag IDN | 0x07 (fRefreshEnable) |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.2 (Flags)

---

#### Step 1.5: 讀取 Refresh Status（expect Stopped=2）

**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus, IDN 0x2C)`

**目的**: Clear Flag 後讀取 Status，應為 Stopped(2)。

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x2C (bRefreshStatus) |

**Expected**: `bRefreshStatus == 0x02`（Stopped）。

**UFS SPEC Reference**: JESD220H Section 14.3.1

---

#### Step 1.6: 再次讀取 Refresh Status（expect Idle）

**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus, IDN 0x2C)`

**目的**: 再次讀取，確認回到 Idle(0)。

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x2C (bRefreshStatus) |

**Expected**: `bRefreshStatus == 0x00`。

**UFS SPEC Reference**: JESD220H Section 14.3.1

---

### Phase 2 — Refresh Completion + Poll

#### Step 2.1: Enable Refresh

**UFS QUERY**: `SET FLAG (fRefreshEnable, IDN 0x07)`

**目的**: 啟用 Refresh，等待其完成。

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | 0x07 (fRefreshEnable) |
| Flag Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.2 (Flags), Section 13.4.15

---

#### Step 2.2: Sleep 20 秒

**目的**: 等待 Refresh 操作執行。

| Field | Value |
|-------|-------|
| Duration | 20000 ms |

**Expected**: 等待 Refresh 執行（JIRA 規範等待 20 秒）。

---

#### Step 2.3: Poll Refresh Status until Success

**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus, IDN 0x2C)`（Polling）

**目的**: 反覆讀取 bRefreshStatus，直到值為 3 (Success)。最多 polling 100 次。

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x2C (bRefreshStatus) |
| Polling Max | 100 次 |

**Expected**: `bRefreshStatus == 0x03`（Success）。若 polling 超過 100 次仍未成功，判定 FAIL。

**UFS SPEC Reference**: JESD220H Section 14.3.1

---

#### Step 2.4: 再次讀取 Refresh Status（expect Idle）

**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus, IDN 0x2C)`

**目的**: Refresh 完成後再次讀取 Status，確認回到 Idle(0)。

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x2C (bRefreshStatus) |

**Expected**: `bRefreshStatus == 0x00`。

**UFS SPEC Reference**: JESD220H Section 14.3.1

---

#### Step 2.5: Clear Refresh Enable

**UFS QUERY**: `CLEAR FLAG (fRefreshEnable, IDN 0x07)`

**目的**: 停用 Refresh。

| Field | Value |
|-------|-------|
| Query Opcode | 0x05 (CLEAR FLAG) |
| Flag IDN | 0x07 (fRefreshEnable) |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.2

---

### Phase 3 — Queue 非空時 Enable Refresh

#### Step 3.1: Queue Full-Card Write（not sent）

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: 準備一個全卡 Write 命令放入 Queue 中（尚未發送），模擬 Queue 非空情境。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 |
| Logical Block Address | 0x00000000 |
| Transfer Length | MAX_LBA + 1 |
| Data Size | 1 (minimum data per LBA) |

**Expected**: Command queued（尚未發送）。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.43

---

#### Step 3.2: Enable Refresh（Queue 非空時）

**UFS QUERY**: `SET FLAG (fRefreshEnable, IDN 0x07)`

**目的**: Queue 非空的情況下發送 SET FLAG (fRefreshEnable)。

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | 0x07 (fRefreshEnable) |
| Flag Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.2

---

#### Step 3.3: 並行發送 Write + Refresh Enable

**目的**: 將 Step 3.1 的 Write 命令與 Step 3.2 的 Refresh Enable 一同發送。

**Expected**: Write 返回 `GOOD Status`。

---

#### Step 3.4: 讀取 Refresh Status（expect Stopped=4）

**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus, IDN 0x2C)`

**目的**: Queue 非空時 Refresh 應被 Stop，Status 應為 4。

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x2C (bRefreshStatus) |

**Expected**: `bRefreshStatus == 0x04`（Stopped — Queue 非空）。

**UFS SPEC Reference**: JESD220H Section 14.3.1

---

#### Step 3.5: 再次讀取 Refresh Status（expect Idle）

**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus, IDN 0x2C)`

**目的**: 再次讀取，確認回到 Idle(0)。

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x2C (bRefreshStatus) |

**Expected**: `bRefreshStatus == 0x00`。

**UFS SPEC Reference**: JESD220H Section 14.3.1

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | Step 0.2 |
| 0x2A | WRITE(10) | 10 | Step 3.1 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 使用位置 |
|:---|:---|:---|:---|
| 0x07 | fRefreshEnable | 0x02 (SET FLAG), 0x05 (CLEAR FLAG) | Step 1.1, 1.4, 2.1, 2.5, 3.2 |
| 0x1F | bUFSFeaturesSupport | 0x03 (READ ATTRIBUTE) | Step 0.1 |
| 0x2C | bRefreshStatus | 0x03 (READ ATTRIBUTE) | Step 1.2, 1.3, 1.5, 1.6, 2.3, 2.4, 3.4, 3.5 |

## Refresh Status 完整對照表

| 值 | 名稱 | 說明 |
|:---|:---|:---|
| 0x00 | Idle | 無 Refresh 活動，或讀取後重置 |
| 0x01 | In Progress | Refresh 執行中 |
| 0x02 | Stopped | Clear Flag 後停止 |
| 0x03 | Success | Refresh 成功完成 |
| 0x04 | Stopped (Queue not empty) | Queue 非空時拒絕執行 |

---

## 自我驗證

- Tree Diagram leaf steps: **18** (0.1, 0.2, 1.1~1.6 = 6, 2.1~2.5 = 5, 3.1~3.5 = 5)
- `### Step` sections: **18** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
- 無 `(待確認)` 佔位符 ✓
