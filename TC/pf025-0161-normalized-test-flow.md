---
title: PF025_0161_UP_Attribute_OutOfRange-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf025_0161, unipro, dme, pa-attribute, mib]
description: >
  PF025_0161 UniPro PA Attribute OutOfRange Test — 透過 DME_SET 設定
  Local/Peer PA_Attributes 的 out-of-range 值，驗證回傳 INVALID_MIB_ATT_VALUE。
sources:
  - JIRA: PF025_0161 (SYSTCUFS-124)
  - UFS Spec: JESD220H Section 6.7 (UniPro DME), MIPI UniPro Spec
---

# PF025_0161 正規化 Test Flow（UniPro DME 層級）

## 測試目標

透過 DME_SET 對所有 Local 及 Peer PA_Attributes 寫入超出範圍的值，
驗證 Device 正確回傳 `INVALID_MIB_ATT_VALUE` 結果碼。

> 注意：此 Pattern 操作於 UniPro DME 層級（UIO_SAP / DME_SAP），非 SCSI CMD。

## 測試架構（Tree Diagram — 含 Expected）

```
PF025_0161 Test Flow
│
├── Test A: Local PA_Attributes
│   ├── Step A.1: DME_SET — All Local PA_Attributes with out-of-range value → Expected: 發送成功（DME layer）
│   └── Step A.2: Check Result Code — expect INVALID_MIB_ATT_VALUE → Expected: Result Code == INVALID_MIB_ATT_VALUE
│
└── Test B: Peer PA_Attributes
    ├── Step B.1: DME_SET — All Peer PA_Attributes with out-of-range value → Expected: 發送成功（DME layer）
    └── Step B.2: Check Result Code — expect INVALID_MIB_ATT_VALUE → Expected: Result Code == INVALID_MIB_ATT_VALUE
```

---

## Test A — Local PA_Attributes

### Step A.1: DME_SET All Local PA_Attributes (Out-of-Range)

**DME Operation**: `DME_SET` (via UIO_SAP / DME_SAP)

**目的**: 對所有 Local PA_Attributes 寫入超出 SPEC 定義範圍的值。

| Field | Value |
|-------|-------|
| Layer | DME (Device Management Entity) |
| SAP | UIO_SAP → DME_SAP |
| Target | All Local PA_Attributes |
| Value | Out-of-range (超出 SPEC 定義範圍) |

**Expected**: DME_SET 發送成功（DME layer 接收）。

**UFS SPEC Reference**: JESD220H Section 6.7 (UniPro), MIPI UniPro Spec v2.0

---

### Step A.2: Check Result Code — INVALID_MIB_ATT_VALUE

**目的**: 檢查 DME_SET 的回應結果碼，應為 `INVALID_MIB_ATT_VALUE`。

| Field | Value |
|-------|-------|
| Check | Result Code |
| Expected Value | `INVALID_MIB_ATT_VALUE` |

**Expected**: `Result Code == INVALID_MIB_ATT_VALUE`。

**UFS SPEC Reference**: MIPI UniPro Spec — DME Result Codes

---

## Test B — Peer PA_Attributes

### Step B.1: DME_SET All Peer PA_Attributes (Out-of-Range)

**DME Operation**: `DME_SET` (via UIO_SAP / DME_SAP)

**目的**: 對所有 Peer PA_Attributes 寫入超出 SPEC 定義範圍的值。

| Field | Value |
|-------|-------|
| Layer | DME |
| SAP | UIO_SAP → DME_SAP |
| Target | All Peer PA_Attributes |
| Value | Out-of-range (超出 SPEC 定義範圍) |

**Expected**: DME_SET 發送成功（DME layer 接收）。

**UFS SPEC Reference**: JESD220H Section 6.7 (UniPro), MIPI UniPro Spec v2.0

---

### Step B.2: Check Result Code — INVALID_MIB_ATT_VALUE

**目的**: 檢查 DME_SET 的回應結果碼，應為 `INVALID_MIB_ATT_VALUE`。

| Field | Value |
|-------|-------|
| Check | Result Code |
| Expected Value | `INVALID_MIB_ATT_VALUE` |

**Expected**: `Result Code == INVALID_MIB_ATT_VALUE`。

**UFS SPEC Reference**: MIPI UniPro Spec — DME Result Codes

---

## 自我驗證

- Tree Diagram leaf steps: **4** (A.1, A.2, B.1, B.2)
- `### Step` sections: **4** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
- 無 `(待確認)` 佔位符 ✓
