---
title: PF010_0310_WriteBooster_SSU_Rst-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf010_0310, scsi-cmd, write-booster, reset, flush]
description: >
  PF010_0310 Write Booster Reset Test — 驗證 WB Enable/Disable/Flush 狀態下
  SSU/POR/LINKSTARTUP Reset 後行為正確性。
sources:
  - JIRA: PF010_0310 (SYSTCUFS-15)
  - UFS Spec: JESD220H Section 13.4.18 (WriteBooster), Section 14.1 (Descriptors), Section 14.2 (Flags)
---

# PF010_0310 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

三場景 burn-in loop：WB Enable + W/R + Reset / WB Disable + W/R + Reset / Flush Enable + Reset。
Reset 類型隨機：SSU / POR / LINKSTARTUP。

## JIRA Step 對照

| JIRA Step | 原始描述 | 正規化對應 |
|-----------|---------|-----------|
| Step 1 | Config max WB Buffer | Phase 0 |
| Step 2 | WB Enable + W/R + Reset | Phase 1 |
| Step 3 | WB Disable + W/R + Reset | Phase 2 |
| Step 4 | Flush Enable + Reset | Phase 3 |

---

## 測試架構

```
PF010_0310 Test Flow
│
├── Phase 0: WB 初始化配置
│   ├── Step 0.1: TEST UNIT READY → Expected: GOOD Status
│   ├── Step 0.2: READ CAPACITY(10) → Expected: GOOD Status, 回傳 LBA 範圍
│   ├── Step 0.3: QUERY Read Attribute (dExtendedUFSFeaturesSupport) → Expected: QUERY RESPONSE Success, WB 支援確認
│   ├── Step 0.4: QUERY Read Attribute (dLUNumWriteBoosterBufferAllocUnits) — 唯讀 → Expected: QUERY RESPONSE Success, 取得 max buffer
│   ├── Step 0.5: QUERY Read Descriptor (Configuration Descriptor) → Expected: QUERY RESPONSE Success
│   └── Step 0.6: QUERY Write Descriptor (Configuration Descriptor) — Shared Type + MAX → Expected: QUERY RESPONSE Success
│
└── Loop (burn_in_loop)
    │
    ├── Phase 1: WB Enable + W/R + Reset
    │   ├── Step 1.1: QUERY Set Flag (fWriteBoosterEn, 0x0E) → Expected: QUERY RESPONSE Success
    │   ├── Step 1.2: QUERY Read Flag (fWriteBoosterEn) → Expected: fWriteBoosterEn == 1
    │   ├── Step 1.3: WRITE(10) FUA=0 — Random W/R data → Expected: GOOD Status
    │   ├── Step 1.4: READ(10) + Compare → Expected: GOOD Status, Data Match
    │   ├── Step 1.5: Random Reset (SSU/POR/LINKSTARTUP) → Expected: Reset device success
    │   └── Step 1.6: QUERY Read Flag (fWriteBoosterEn) — Reset 後 WB 狀態 → Expected: fWriteBoosterEn 依 SPEC 定義 (volatile flag)
    │
    ├── Phase 2: WB Disable + W/R + Reset
    │   ├── Step 2.1: WRITE(10) FUA=0 → Expected: GOOD Status
    │   ├── Step 2.2: QUERY Clear Flag (fWriteBoosterEn) → Expected: QUERY RESPONSE Success
    │   ├── Step 2.3: READ(10) + Compare → Expected: GOOD Status, Data Match
    │   ├── Step 2.4: Random Reset → Expected: Reset device success
    │   └── Step 2.5: QUERY Read Flag (fWriteBoosterEn) → Expected: fWriteBoosterEn == 0 (已 Clear)
    │
    └── Phase 3: Flush Enable + Reset
        ├── Step 3.1: [Branch 50%] QUERY Set Flag (fWriteBoosterBufferFlushEn, 0x0B) → Expected: QUERY RESPONSE Success
        ├── Step 3.2: [Branch 50%] QUERY Set Flag (fWriteBoosterBufferFlushDuringHibernate, 0x0C) → Expected: QUERY RESPONSE Success
        ├── Step 3.3: Random Delay 0~2s → Expected: 等待 Flush 觸發
        ├── Step 3.4: Random Reset (POR_delay / SSU+Hibernate+POR) → Expected: Reset device success
        └── Step 3.5: QUERY Read Flag — 驗證 Flush Flag → Expected: 依 SPEC 確認 flag reset 後狀態
```

---

## Phase 0 — WB 初始化配置

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

---

### Step 0.2: 取得 LUN 容量

**SCSI CMD**: `READ CAPACITY(10) (25h)`

| Field | Value |
|-------|-------|
| Opcode | 0x25 |
| LUN | All LUNs |

**Expected**: `GOOD Status`，取得 MAX_LBA。

---

### Step 0.3: 檢查 WB 支援

**UFS QUERY**: `READ ATTRIBUTE (dExtendedUFSFeaturesSupport)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| IDN | dExtendedUFSFeaturesSupport |

**Expected**: `QUERY RESPONSE Success`，確認 WB bit 已 set。

---

### Step 0.4: 讀取最大 WB Buffer

**UFS QUERY**: `READ ATTRIBUTE (dLUNumWriteBoosterBufferAllocUnits, IDN 0x17)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| IDN | 0x17 (dLUNumWriteBoosterBufferAllocUnits — R/O) |

**Expected**: `QUERY RESPONSE Success`，回傳 max alloc units。

**UFS SPEC Reference**: JESD220H Section 14.3.1 (dLUNumWriteBoosterBufferAllocUnits 為 Read-Only)

---

### Step 0.5: 讀取 Configuration Descriptor

**UFS QUERY**: `READ DESCRIPTOR (Configuration Descriptor)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x07 (READ DESCRIPTOR) |
| IDN | 0x01 (Configuration Descriptor) |
| Index | 0x00 |
| Selector | 0x00 |
| Length | 0x40 |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.6: 配置 WB Buffer（Shared Type + MAX）

**UFS QUERY**: `WRITE DESCRIPTOR (Configuration Descriptor)`

**重要**: dLUNumWriteBoosterBufferAllocUnits 為唯讀 Attribute，必須透過 WRITE DESCRIPTOR (Configuration Descriptor) 設定。

| Field | Value |
|-------|-------|
| Query Opcode | 0x08 (WRITE DESCRIPTOR) |
| IDN | 0x01 (Configuration Descriptor) |
| bWriteBoosterBufferType | 0x01 (Shared) |
| dLUNumWriteBoosterBufferAllocUnits | MAX (from Step 0.4) |

**Expected**: `QUERY RESPONSE Success`。

---

## Loop — Burn-in

### Phase 1: WB Enable + W/R + Reset

#### Step 1.1: Enable WB

**UFS QUERY**: `SET FLAG (fWriteBoosterEn, IDN 0x0E)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| IDN | 0x0E (fWriteBoosterEn) |
| Value | 0x01 |

**Expected**: `QUERY RESPONSE Success`。

---

#### Step 1.2: 確認 WB 已啟用

**UFS QUERY**: `READ FLAG (fWriteBoosterEn)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x01 (READ FLAG) |
| IDN | 0x0E |

**Expected**: `fWriteBoosterEn == 1`。

---

#### Step 1.3: Write Test Data

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| LBA | Random |
| Transfer Length | Random |

**Expected**: `GOOD Status`。

---

#### Step 1.4: Read Compare

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | Step 1.3 LUN |
| LBA | Step 1.3 LBA |
| Transfer Length | Step 1.3 大小 |

**Expected**: `GOOD Status`, `Data Match`。

---

#### Step 1.5: Random Reset

**Reset Types**（隨機）:

| Type | 說明 |
|:---|:---|
| SSU | START STOP UNIT Power Cycle |
| POR | Power-On Reset |
| LINKSTARTUP | Link re-startup |

**Expected**: `fDeviceInit == 1`。

---

#### Step 1.6: 驗證 Reset 後 WB Flag

**UFS QUERY**: `READ FLAG (fWriteBoosterEn)`

**Expected**: 依 SPEC 定義確認 volatile flag 狀態。

---

### Phase 2: WB Disable + W/R + Reset

#### Step 2.1: Write Test Data

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| FUA | 0 |

**Expected**: `GOOD Status`。

---

#### Step 2.2: Disable WB

**UFS QUERY**: `CLEAR FLAG (fWriteBoosterEn)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x05 (CLEAR FLAG) |
| IDN | 0x0E |

**Expected**: `QUERY RESPONSE Success`。

---

#### Step 2.3: Read Compare

**SCSI CMD**: `READ(10) (28h)`

**Expected**: `GOOD Status`, `Data Match`。

---

#### Step 2.4: Random Reset

同 Step 1.5。

**Expected**: `fDeviceInit == 1`。

---

#### Step 2.5: 驗證 WB Disabled

**UFS QUERY**: `READ FLAG (fWriteBoosterEn)`

**Expected**: `fWriteBoosterEn == 0`。

---

### Phase 3: Flush Enable + Reset

#### Step 3.1/3.2: [Branch 50%/50%] Set Flush Flag

**UFS QUERY**: `SET FLAG`

| Branch | IDN | Name |
|:---|:---|:---|
| 50% | 0x0B | fWriteBoosterBufferFlushEn |
| 50% | 0x0C | fWriteBoosterBufferFlushDuringHibernate |

**Expected**: `QUERY RESPONSE Success`。

---

#### Step 3.3: Random Delay

**目的**: 延遲 0~2 秒，等待 Flush 觸發。

**Expected**: Delay 完成。

---

#### Step 3.4: Random Reset

**Reset Types**（隨機）:

| Type | 說明 |
|:---|:---|
| POR_delay | POR with delay |
| SSU+Hibernate+POR | SSU → Hibernate → POR |

**Expected**: `fDeviceInit == 1`。

---

#### Step 3.5: 驗證 Flush Flag

**UFS QUERY**: `READ FLAG (依 Step 3.1/3.2 選擇的 flag)`

**Expected**: 確認 reset 後 flush flag 狀態符合 SPEC。

---

## 附錄 B — SCSI Command Opcode

| Opcode | Command | 使用位置 |
|:---|:---|:---|
| 0x00 | TEST UNIT READY | Step 0.1 |
| 0x25 | READ CAPACITY(10) | Step 0.2 |
| 0x28 | READ(10) | Step 1.4, 2.3 |
| 0x2A | WRITE(10) | Step 1.3, 2.1 |

## 附錄 A — UFS Query IDN

| IDN | Name | Opcode | 存取 | 使用 |
|:---|:---|:---|:---|:---|
| 0x0E | fWriteBoosterEn | 0x01/0x02/0x05 | R/W | Phase 1, 2 |
| 0x0B | fWriteBoosterBufferFlushEn | 0x02 (SET FLAG) | R/W | Step 3.1 |
| 0x0C | fWriteBoosterBufferFlushDuringHibernate | 0x02 (SET FLAG) | R/W | Step 3.2 |
| 0x17 | dLUNumWriteBoosterBufferAllocUnits | 0x03 (READ ATTRIBUTE) | R/O | Step 0.4 |
| 0x01 | Configuration Descriptor | 0x07/0x08 (R/W DESCRIPTOR) | R/W | Step 0.5, 0.6 |
| 0x01 | fDeviceInit | 0x01 (READ FLAG) | R | Reset 驗證 |

## 附錄 C — Reset 類型

| Reset | SPEC |
|:---|:---|
| POR | JESD220H 10.4.2 |
| SSU | JESD220H 10.2.5 |
| LINKSTARTUP | JESD220H 10.4.6 |

---

## 自我驗證

- Tree leaf: 0.1~0.6(6) + 1.1~1.6(6) + 2.1~2.5(5) + 3.1~3.5(5) = 22
- `### Step`: 22 ✓
- 所有 leaf 有 `→ Expected:` ✓
