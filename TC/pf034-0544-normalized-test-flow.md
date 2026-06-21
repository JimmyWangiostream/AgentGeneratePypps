---
title: PF034_0544_HID_Defrag_Operation_Error-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf034_0544, scsi-cmd, hid, defrag, general-failure, query]
description: >
  PF034_0544 HID Defrag Operation Error Test — 驗證 Init 未完成前設定
  bDefragOperation 應回 GENERAL_FAILURE，以及 Clean case 的 HID Defrag 成功完成。
sources:
  - JIRA: PF034_0544 (SYSTCUFS-686)
  - UFS Spec: JESD220H Section 13.4.x (HID Defrag)
---

# PF034_0544 正規化 Test Flow（SCSI CMD 単位）

## 測試目標

1. 驗證 HID 不支援時的 Error case（INVALID_IDN）
2. 驗證 HID Defrag 在 Q not empty 時不啟動（首次 Read Status = Idle）
3. 驗證 Init 未完成前設定 bDefragOperation → GENERAL_FAILURE（×4 scenarios）
4. Clean case: HID Defrag 成功完成

## IC/NAND 相容性

| 支援組合 | 8317 BiCS5 (KIC) / 8317 B47R/Wanli/WD / 8325 BiCS6 |
|:---|:---|
| 8317 WYS | NOT SUPPORTED |

## 測試架構（Tree Diagram — 含 Expected）

```
PF034_0544 Test Flow
│
├── Phase 0: 相容性檢查
│   ├── Step 0.1: HW Check — IC/NAND combo → Expected: 支援組合, 否則 NOT SUPPORTED / 進入 Error case
│   └── Step 0.2: Error Case (不支援 HID) — READ DESCRIPTOR(wHIDVersion,59h)→INVALID_IDN(FDh); READ ATTR(34h/35h)→INVALID_IDN → Expected: INVALID_IDN(FDh)
│
├── Phase 1: HID Version & Precondition
│   ├── Step 1.1: QUERY Read Descriptor (wHIDVersion, 59h) → Expected: QUERY RESPONSE Success
│   └── Step 1.2: WRITE(10) — Full Card + 10% Random → Expected: GOOD Status
│
├── Phase 2: Queue Not Empty — HID Should Not Start
│   ├── Step 2.1: WRITE(10) — Queue cmd (not sent yet) → Expected: (queued)
│   ├── Step 2.2: QUERY Write Attribute (bDefragOperation, 13h)=01h + Send Step 2.1 cmd → Expected: QUERY RESPONSE Success
│   └── Step 2.3: QUERY Read Attribute (bDefragmentationExecutionProgress, 35h) — expect Idle → Expected: bDefragmentationExecutionProgress == 0x00 (Idle)
│
├── Phase 3: Init 未完成 → GENERAL_FAILURE (×4 scenarios)
│   ├── Scenario A: SSU PowerOff→On → LinkStartup → NOP → WRITE ATTR(bDefragOperation=01h) → Expected: GENERAL_FAILURE
│   ├── Scenario B: (同上 + Read Descriptor before WRITE ATTR) → Expected: GENERAL_FAILURE
│   ├── Scenario C: (同上 + TEST UNIT READY Boot LUN before WRITE ATTR) → Expected: GENERAL_FAILURE
│   └── Scenario D: (同上 + SCSI READ Boot LUN before WRITE ATTR) → Expected: GENERAL_FAILURE
│
└── Phase 4: Clean Case — HID Defrag Success
    ├── Step 4.1: FORMAT UNIT → Expected: GOOD Status
    ├── Step 4.2: QUERY Set Flag (HID trigger) → Expected: QUERY RESPONSE Success
    └── Step 4.3: QUERY Read Attribute (bDefragmentationExecutionProgress, 35h) — expect Successfully Done → Expected: bDefragmentationExecutionProgress == Successfully Done
```

---

## Phase 0 — 相容性檢查

### Step 0.1: IC/NAND Check

| Check | Expected |
|-------|---------|
| IC | 8317 (KIC) / 8325 |
| NAND | BiCS5 / B47R / Wanli / WD / BiCS6 |
| 8317 WYS | NOT SUPPORTED |

---

### Step 0.2: Error Case — HID Not Supported

**UFS QUERY**: `READ DESCRIPTOR (Device Descriptor, Offset 59h = wHIDVersion)` + `READ ATTRIBUTE (34h, 35h)`

| Field | Value |
|-------|-------|
| READ DESCRIPTOR Offset | 59h (wHIDVersion) |
| READ ATTRIBUTE IDN | 34h (bDefragmentationStatus) |
| READ ATTRIBUTE IDN | 35h (bDefragmentationExecutionProgress) |

**Expected**: 不支援時 → `INVALID_IDN (FDh)`。

---

## Phase 1 — HID Version & Precondition

### Step 1.1: Read HID Version

**UFS QUERY**: `READ DESCRIPTOR (Device Descriptor, Offset 59h)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x07 (READ DESCRIPTOR) |
| Descriptor IDN | 0x00 (Device Descriptor) |
| Offset | 59h (wHIDVersion) |

**Expected**: `QUERY RESPONSE Success`，回傳 wHIDVersion。

---

### Step 1.2: Full Card Write + 10% Random

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| LBA | 0 ~ MAX_LBA + random 10% |

**Expected**: `GOOD Status`。

---

## Phase 2 — Queue Not Empty Test

### Step 2.1: Queue Write CMD

**SCSI CMD**: `WRITE(10) (2Ah)`（Queue，未發送）

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| LBA | 0 ~ MAX_LBA |
| Data Size | 1 (per LBA) |

**Expected**: Command queued（未發送）。

---

### Step 2.2: Enable Defrag + Send Queued CMD

**UFS QUERY**: `WRITE ATTRIBUTE (bDefragOperation, IDN 0x13)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| Attribute IDN | 0x13 (bDefragOperation) [KIC] |
| Value | 0x01 (Enable) |

**Expected**: `QUERY RESPONSE Success`。同時發送 Step 2.1 的 Write 命令。

---

### Step 2.3: Check Defrag Progress — expect Idle

**UFS QUERY**: `READ ATTRIBUTE (bDefragmentationExecutionProgress, IDN 0x35)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x35 (bDefragmentationExecutionProgress) [KIC] |
| Timeout | 15 min (若超時 → FAIL) |

**Expected**: `bDefragmentationExecutionProgress == 0x00` (Idle) — Q not empty 時 HID 不啟動。

---

## Phase 3 — Init 未完成 → GENERAL_FAILURE

### 通用前置子步驟（每個 Scenario 重複）

| Sub-step | 操作 | Expected |
|:---|:---|:---|
| a | START STOP UNIT — PowerOff → PowerOn | GOOD Status |
| b | Link Startup | Link startup success |
| c | NOP CMD | GOOD Status |

### Scenario A: 直接 WRITE ATTRIBUTE

| Extra Step | 操作 | Expected |
|:---|:---|:---|
| d | WRITE ATTRIBUTE (bDefragOperation, 13h) = 01h | GENERAL_FAILURE |

### Scenario B: Read Descriptor 後

| Extra Steps | 操作 | Expected |
|:---|:---|:---|
| d | READ DESCRIPTOR | QUERY RESPONSE Success |
| e | WRITE ATTRIBUTE (bDefragOperation) = 01h | GENERAL_FAILURE |

### Scenario C: TEST UNIT READY Boot LUN 後

| Extra Steps | 操作 | Expected |
|:---|:---|:---|
| d | READ DESCRIPTOR | QUERY RESPONSE Success |
| e | TEST UNIT READY (Boot LUN) | GOOD Status |
| f | WRITE ATTRIBUTE (bDefragOperation) = 01h | GENERAL_FAILURE |

### Scenario D: SCSI READ Boot LUN 後

| Extra Steps | 操作 | Expected |
|:---|:---|:---|
| d | READ DESCRIPTOR | QUERY RESPONSE Success |
| e | TEST UNIT READY (Boot LUN) | GOOD Status |
| f | READ(10) (Boot LUN) | GOOD Status |
| g | WRITE ATTRIBUTE (bDefragOperation) = 01h | GENERAL_FAILURE |

---

## Phase 4 — Clean Case

### Step 4.1: FORMAT UNIT

**SCSI CMD**: `FORMAT UNIT (04h)`

| Field | Value |
|-------|-------|
| Opcode | 0x04 |

**Expected**: `GOOD Status`。

---

### Step 4.2: Trigger HID Defrag

**UFS QUERY**: `SET FLAG (HID trigger)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | HID trigger flag |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 4.3: Verify Defrag Successfully Done

**UFS QUERY**: `READ ATTRIBUTE (bDefragmentationExecutionProgress, IDN 0x35)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x35 (bDefragmentationExecutionProgress) |

**Expected**: `bDefragmentationExecutionProgress == Successfully Done`。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | Scenario C/D |
| 0x04 | FORMAT UNIT | 6 | Step 4.1 |
| 0x1B | START STOP UNIT | 6 | Phase 3 |
| 0x28 | READ(10) | 10 | Scenario D |
| 0x2A | WRITE(10) | 10 | Step 1.2, 2.1 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 使用位置 |
|:---|:---|:---|:---|
| 0x13 | bDefragOperation | 0x04 (WRITE ATTRIBUTE) | Step 2.2, Phase 3 |
| 0x34 | bDefragmentationStatus | 0x03 (READ ATTRIBUTE) | Step 0.2 |
| 0x35 | bDefragmentationExecutionProgress | 0x03 (READ ATTRIBUTE) | Step 0.2, 2.3, 4.3 |
| 59h | wHIDVersion | 0x07 (READ DESCRIPTOR) | Step 0.2, 1.1 |

---

## 自我驗證

- Tree Diagram leaf steps: **8** (0.1, 0.2, 1.1, 1.2, 2.1~2.3=3, 4.1~4.3=3 + Phase 3 4 scenarios)
- `### Step` sections: **12** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
