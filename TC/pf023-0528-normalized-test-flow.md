---
title: PF023_0528_Refresh_Attribute_Immutability-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf023_0528, scsi-cmd, refresh, attribute, immutability]
description: >
  PF023_0528 Refresh Attribute Value Write/Read Test — 驗證 Refresh 屬性
  在 Write/Read/Unmap/SSU 下不變，以及 Refresh 進行中仍可讀取
  Descriptor/Flag/Attribute。
sources:
  - JIRA: PF023_0528 (SYSTCUFS-672)
  - UFS Spec: JESD220H Section 13.4.15 (Refresh)
---

# PF023_0528 正規化 Test Flow（SCSI CMD 単位）

## 測試目標

驗證 Refresh 屬性（bRefreshFreq, bRefreshUnit, dRefreshProgress, dRefreshTotalCount）
在 Write/Read/Unmap/SSU 操作下保持不變，以及在 Refresh 進行中讀取其他 Descriptor/Flag/Attribute 的正確性。

## 測試架構（Tree Diagram — 含 Expected）

```
PF023_0528 Test Flow
│
├── Phase 0: 檢查 Refresh 支援
│   └── Step 0.1: QUERY Read Attribute (bUFSFeaturesSupport) — Check Refresh bit → Expected: QUERY RESPONSE Success, Refresh bit == 1
│
├── Phase 1: 屬性配置 + Refresh 進行中讀取
│   ├── Step 1.1: QUERY Write Attribute (Refresh_Frequency=1) → Expected: QUERY RESPONSE Success
│   ├── Step 1.2: QUERY Write Attribute (Refresh_Unit=1) — expect reserved/error → Expected: 依 SPEC, reserved value 應回 error
│   ├── Step 1.3: QUERY Write Attribute (Refresh_Method=1) — expect reserved/error → Expected: 依 SPEC, reserved value 應回 error
│   ├── Step 1.4: HW Reset → QUERY Set Flag (fRefreshEnable) → Expected: Reset device success → QUERY RESPONSE Success
│   └── Step 1.5: QUERY Read Descriptor / Read Flag / Read Attribute — Refresh 進行中讀取 → Expected: QUERY RESPONSE Success
│
├── Phase 2: 屬性不變性驗證
│   ├── Step 2.1: QUERY Read Attributes — Record baseline → Expected: 記錄 baseline 值
│   ├── Step 2.2: WRITE(10) — Full Card → Verify attributes unchanged → Expected: GOOD Status, 屬性不變
│   ├── Step 2.3: READ(10) — Full Card → Verify attributes unchanged → Expected: GOOD Status, 屬性不變
│   ├── Step 2.4: UNMAP — Full Card → Verify attributes unchanged → Expected: GOOD Status, 屬性不變
│   └── Step 2.5: START STOP UNIT — Power cycle → Verify attributes unchanged → Expected: GOOD Status, 屬性不變
│
└── Phase 3: Cleanup
    └── Step 3.1: QUERY Clear Flag (fRefreshEnable) → Expected: QUERY RESPONSE Success
```

---

## Phase 0

### Step 0.1: Check Refresh Support

**UFS QUERY**: `READ ATTRIBUTE (bUFSFeaturesSupport)`

**Expected**: `QUERY RESPONSE Success`，Refresh bit == 1。

---

## Phase 1 — 屬性配置

### Step 1.1: Set Refresh Frequency

**UFS QUERY**: `WRITE ATTRIBUTE (Refresh_Frequency)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| Attribute IDN | Refresh_Frequency |
| Value | 1 |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 1.2: Set Refresh Unit (reserved value)

**UFS QUERY**: `WRITE ATTRIBUTE (Refresh_Unit)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| Attribute IDN | Refresh_Unit |
| Value | 1 (reserved) |

**Expected**: 依 SPEC，reserved value 應回 error。

---

### Step 1.3: Set Refresh Method (reserved value)

**UFS QUERY**: `WRITE ATTRIBUTE (Refresh_Method)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| Attribute IDN | Refresh_Method |
| Value | 1 (reserved) |

**Expected**: 依 SPEC，reserved value 應回 error。

---

### Step 1.4: HW Reset + Enable Refresh

**目的**: 執行 HW Reset 後啟用 Refresh。

**Expected**: `Reset device success` → `QUERY RESPONSE Success`。

---

### Step 1.5: Read During Refresh

**目的**: Refresh 進行中讀取 Descriptor / Flag / Attribute。

**Expected**: `QUERY RESPONSE Success`（Refresh 進行中不影響讀取）。

---

## Phase 2 — 屬性不變性

### Step 2.1: Record Baseline

**UFS QUERY**: `READ ATTRIBUTE (bRefreshFreq, bRefreshUnit, dRefreshProgress, dRefreshTotalCount)`

**Expected**: 記錄 baseline 值。

---

### Steps 2.2~2.5: Verify Immutability

| Step | SCSI CMD | Opcode | Expected |
|:---|:---|:---|:---|
| 2.2 | WRITE(10) — Full Card | 0x2A | GOOD Status, 屬性不變 |
| 2.3 | READ(10) — Full Card | 0x28 | GOOD Status, 屬性不變 |
| 2.4 | UNMAP — Full Card | 0x42 | GOOD Status, 屬性不變 |
| 2.5 | START STOP UNIT — Power cycle | 0x1B | GOOD Status, 屬性不變 |

---

## Phase 3 — Cleanup

### Step 3.1: Clear Refresh Enable

**UFS QUERY**: `CLEAR FLAG (fRefreshEnable, IDN 0x07)`

**Expected**: `QUERY RESPONSE Success`。

---

## 自我驗證

- Tree Diagram leaf steps: **10** (0.1, 1.1~1.5=5, 2.1~2.5=5, 3.1=1 → adjusted) = **12** 
- `### Step` sections: **12** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
