---
title: PF023_0536-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf023_0536, scsi-cmd, refresh, attribute]
description: >
  PF023_0536 Refresh Method Value Test — 正規化 Test Flow。
  驗證 UFS Refresh 操作的各項參數正確性：非法 RefreshMethod(0x00) 應拒絕、
  Manual-Force(0x01) / Manual-Selective(0x02) 方法可正確執行、
  RefreshUnit Minimum(0x00) / Whole Device(0x01) 可正確切換。
sources:
  - JIRA: PF023_0536 (SYSTCUFS-680)
  - UFS Spec: JESD220H Section 13.4.15 (Refresh Operation), Section 14.3 (Attributes)
---

# PF023_0536 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

驗證 UFS Refresh 功能的屬性配置與操作正確性：

- 非法 RefreshMethod (0x00) 寫入應被拒絕
- Manual-Force (0x01) 模式：啟用 Refresh → 確認成功 (0x03) → 確認 TotalCount 遞增 → Idle
- Manual-Selective (0x02) 模式：同上流程
- Minimum Unit (0x00) 與 Whole Device Unit (0x01) 兩種 RefreshUnit 各自驗證

## JIRA Step 對照

| JIRA Step | 原始描述 | 正規化後對應 |
|-----------|---------|-------------|
| Step 1 | 確認 bUFSFeaturesSupport 支援 Refresh | Phase 0 Step 0.2 |
| Step 2 | Set RefreshMethod=0x00, expect fail | Phase 0 Step 0.3 |
| Step 3 | Set RefreshUnit=0x00 (Minimum) | Phase 0 Step 0.4 |
| Step 4 | Set RefreshMethod=0x01 (Manual-Force) | Phase 0 Step 0.5 |
| Step 5 | Read dRefreshTotalCount | Phase 1 Step 1.2 |
| Step 6 | Enable Refresh, check status=3h | Phase 1 Step 1.3–1.4 |
| Step 7 | Read dRefreshTotalCount, expect +1 | Phase 1 Step 1.5 |
| Step 8 | Read status, expect 0 | Phase 1 Step 1.6 |
| Step 9 | Clear Refresh Enable | Phase 1 Step 1.7 |
| Step 10 | Loop with RefreshMethod=0x02 | Loop: Phase 1 × RefreshMethod=0x02 |
| Step 11 | Loop with RefreshUnit=0x01 | Loop: Phase 0 Step 0.4–Phase 1 × RefreshUnit=0x01 |

---

## 測試架構

```
PF023_0536 Test Flow
│
├── Phase 0: Refresh 功能檢查與初始配置
│   ├── Step 0.1: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│   ├── Step 0.2: QUERY Read Attribute (bUFSFeaturesSupport) — 檢查 Refresh 支援 → Expected: Refresh bit == 1, 否則 NOT SUPPORTED
│   ├── Step 0.3: QUERY Write Attribute (bRefreshMethod=0x00) — 驗證非法值被拒絕 → Expected: QUERY RESPONSE Failure (非法值)
│   ├── Step 0.4: QUERY Write Attribute (bRefreshUnit=0x00) — Minimum Unit → Expected: QUERY RESPONSE Success
│   └── Step 0.5: QUERY Write Attribute (bRefreshMethod=0x01) — Manual-Force → Expected: QUERY RESPONSE Success
│
├── Loop (RefreshMethod: 0x01 → 0x02) → Expected: 每種 RefreshMethod 均執行 Phase 1
│   │
│   ├── Phase 1: Refresh 操作驗證
│   │   ├── Step 1.1: QUERY Set Flag (fRefreshEnable) — 啟用 Refresh → Expected: QUERY RESPONSE Success
│   │   ├── Step 1.2: QUERY Read Attribute (dRefreshTotalCount) — 記錄初始值 → Expected: 回傳 baseline_count
│   │   ├── Step 1.3: QUERY Read Attribute (bRefreshStatus) — 確認完成 (0x03) → Expected: bRefreshStatus == 0x03
│   │   ├── Step 1.4: QUERY Read Attribute (dRefreshTotalCount) — 確認遞增 +1 → Expected: baseline_count + 1
│   │   ├── Step 1.5: QUERY Read Attribute (bRefreshStatus) — 確認回到 Idle (0x00) → Expected: bRefreshStatus == 0x00
│   │   └── Step 1.6: QUERY Clear Flag (fRefreshEnable) — 停用 Refresh → Expected: QUERY RESPONSE Success
│   │
│   └── (更新 RefreshMethod = 0x02 後重複 Phase 1)
│
└── Outer Loop (RefreshUnit: 0x00 → 0x01) → Expected: 每種 RefreshUnit 均重複 Phase 0.4 ~ Phase 1
    └── (更新 RefreshUnit = 0x01 後重複 Phase 0.4 ~ Loop)
```

---

## Phase 0 — Refresh 功能檢查與初始配置

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

---

### Step 0.2: 檢查 Refresh 功能支援

**UFS QUERY**: `READ ATTRIBUTE (bUFSFeaturesSupport)`

**目的**: 確認裝置韌體支援 Refresh 操作。

| Field | Value |
|-------|-------|
| Opcode | 0x03（READ ATTRIBUTE） |
| IDN | bUFSFeaturesSupport（參照 JESD220H Section 14.3） |
| Selector | 0x00 |
| Index | 0x00 |

**Expected**: Refresh bit == 1（支援 Refresh）。

**若不支援**: Pattern 判定為 `NOT SUPPORTED`。

---

### Step 0.3: 驗證非法 RefreshMethod 被拒絕

**UFS QUERY**: `WRITE ATTRIBUTE (bRefreshMethod = 0x00)`

**目的**: 寫入非法 Refresh Method 值 (0x00)，確認裝置正確拒絕。

| Field | Value |
|-------|-------|
| Opcode | 0x04（WRITE ATTRIBUTE） |
| IDN | bRefreshMethod（參照 JESD220H Section 14.3） |
| Value | 0x00（非法值，非 Manual-Force 也非 Manual-Selective） |

**Expected**: `QUERY RESPONSE` with failure code（如 General Failure 或 Invalid Value）。

**UFS SPEC Reference**: JESD220H Section 13.4.15（Refresh Operation）, Section 14.3

---

### Step 0.4: 設定 Refresh Unit = Minimum

**UFS QUERY**: `WRITE ATTRIBUTE (bRefreshUnit = 0x00)`

**目的**: 設定 Refresh Unit 為 Minimum Device Capability（僅刷新最小必要單位）。

| Field | Value |
|-------|-------|
| Opcode | 0x04（WRITE ATTRIBUTE） |
| IDN | bRefreshUnit（參照 JESD220H Section 14.3） |
| Value | 0x00（Minimum Device Capability） |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.5: 設定 Refresh Method = Manual-Force

**UFS QUERY**: `WRITE ATTRIBUTE (bRefreshMethod = 0x01)`

**目的**: 設定 Refresh Method 為 Manual-Force（手動強制刷新）。

| Field | Value |
|-------|-------|
| Opcode | 0x04（WRITE ATTRIBUTE） |
| IDN | bRefreshMethod |
| Value | 0x01（Manual-Force） |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 13.4.15

---

## Phase 1 — Refresh 操作驗證

### Step 1.1: 讀取目前 Refresh Total Count（baseline）

**UFS QUERY**: `READ ATTRIBUTE (dRefreshTotalCount)`

| Field | Value |
|-------|-------|
| Opcode | 0x03（READ ATTRIBUTE） |
| IDN | dRefreshTotalCount（參照 JESD220H Section 14.3） |

**目的**: 記錄 Refresh 觸發前的 Total Count 值，作為後續遞增驗證的基準。

**Access**: Read-Only。

**Expected**: 回傳目前計數值，暫存為 `baseline_count`。

---

### Step 1.2: 啟用 Refresh

**UFS QUERY**: `SET FLAG (fRefreshEnable)`

**目的**: 觸發 Refresh 操作。

| Field | Value |
|-------|-------|
| Opcode | 0x02（SET FLAG） |
| IDN | fRefreshEnable（參照 JESD220H Section 14.2） |

**Expected**: `QUERY RESPONSE Success` — Refresh 操作已啟動。

---

### Step 1.3: 確認 Refresh 完成

**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus)`

**目的**: 輪詢 Refresh 狀態直到完成。

| Field | Value |
|-------|-------|
| Opcode | 0x03（READ ATTRIBUTE） |
| IDN | bRefreshStatus（參照 JESD220H Section 14.3） |

**Expected**: bRefreshStatus == 0x03（Refresh Completed Successfully）。

**若尚未完成**: 輪詢至完成（或 timeout 後報告失敗）。

---

### Step 1.4: 驗證 Refresh Total Count 遞增

**UFS QUERY**: `READ ATTRIBUTE (dRefreshTotalCount)`

| Field | Value |
|-------|-------|
| Opcode | 0x03（READ ATTRIBUTE） |
| IDN | dRefreshTotalCount |

**Expected**: `baseline_count + 1`（Refresh Count 正確遞增）。

---

### Step 1.5: 確認 Refresh Status 回到 Idle

**UFS QUERY**: `READ ATTRIBUTE (bRefreshStatus)`

| Field | Value |
|-------|-------|
| Opcode | 0x03（READ ATTRIBUTE） |
| IDN | bRefreshStatus |

**Expected**: bRefreshStatus == 0x00（Idle）— Refresh 完成後狀態回歸。

---

### Step 1.6: 停用 Refresh Enable

**UFS QUERY**: `CLEAR FLAG (fRefreshEnable)`

| Field | Value |
|-------|-------|
| Opcode | 0x05（CLEAR FLAG） |
| IDN | fRefreshEnable |

**Expected**: `QUERY RESPONSE Success`。

---

## Loop 控制邏輯

```
Outer Loop: for each RefreshUnit in [0x00 (Minimum), 0x01 (Whole Device)]:
    Step 0.4: WRITE ATTRIBUTE (bRefreshUnit = RefreshUnit)
    
    Inner Loop: for each RefreshMethod in [0x01 (Manual-Force), 0x02 (Manual-Selective)]:
        Step 0.5: WRITE ATTRIBUTE (bRefreshMethod = RefreshMethod)
        Execute Phase 1 (Step 1.1 ~ 1.6)
```

---

## 附錄 A — 本 Pattern 使用的 UFS Query 對照表

### Query Opcode

| Opcode | 名稱 | 本 Pattern 用途 |
|:---|:---|:---|
| 0x02 | SET FLAG | 設定 fRefreshEnable（觸發 Refresh） |
| 0x03 | READ ATTRIBUTE | 讀取 Refresh 相關屬性 |
| 0x04 | WRITE ATTRIBUTE | 寫入 RefreshMethod / RefreshUnit |
| 0x05 | CLEAR FLAG | 清除 fRefreshEnable |

### Attribute（Refresh 相關，參照 JESD220H Section 14.3）

| 名稱 | Access | 本 Pattern 用途 |
|:---|:---|:---|
| bRefreshMethod | Read-Write | 設定 Refresh 方法（01h/02h），驗證 00h 被拒 |
| bRefreshUnit | Read-Write | 設定 Refresh 單位（00h/01h） |
| bRefreshStatus | Read-Only | 確認 Refresh 完成狀態（03h=成功, 00h=Idle） |
| dRefreshTotalCount | Read-Only | 驗證 Refresh 次數遞增 |

### Flag

| 名稱 | Volatile | 本 Pattern 用途 |
|:---|:---|:---|
| fRefreshEnable | Yes | 觸發/停用 Refresh 操作 |

---

## 附錄 B — 本 Pattern 使用的 SCSI Command 對照表

| Opcode | 命令 | CDB | 本 Pattern 用途 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | 確認裝置就緒 |

---

## 附錄 C — Refresh 屬性值定義

| 屬性 | 值 | 說明 |
|:---|:---|:---|
| bRefreshMethod | 0x00 | 非法值（應被拒絕） |
| bRefreshMethod | 0x01 | Manual-Force（手動強制刷新） |
| bRefreshMethod | 0x02 | Manual-Selective（手動選擇性刷新） |
| bRefreshUnit | 0x00 | Minimum Device Capability |
| bRefreshUnit | 0x01 | Whole Device |
| bRefreshStatus | 0x00 | Idle |
| bRefreshStatus | 0x03 | Refresh Completed Successfully |


---

## 自我驗證

- Tree Diagram leaf steps: **11**
- `### Step` sections: **11**
- ✓
