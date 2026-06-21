---
title: PF021_1037-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf021_1037, scsi-cmd, query, descriptor, length-mismatch]
description: >
  PF021_1037 Query Request Descriptor Length Mismatch Test — 驗證 WRITE DESCRIPTOR
  與 READ DESCRIPTOR 在各種 Length Mismatch 情境下的正確回應行為。
sources:
  - JIRA: PF021_1037 (SYSTCUFS-1361)
  - UFS Spec: JESD220H Section 10.7.8-9 (QUERY), Section 14.1 (Descriptors)
---

# PF021_1037 正規化 Test Flow（SCSI CMD 単位）

## 測試目標

驗證 UFS Query Descriptor 操作在 Length 參數不匹配時的正確行為：
- **WRITE DESCRIPTOR**：寫入 Data Length < descriptor bLength → Response F9h，Response LENGTH == bLength
- **READ DESCRIPTOR**：Request LENGTH > bLength → 回傳完整 descriptor（Response LENGTH == bLength）
- **READ DESCRIPTOR**：Request LENGTH <= bLength → 回傳 Request LENGTH 大小的資料

## 測試架構（含 Expected）

```
PF021_1037 Test Flow
│
├── Phase 0: 裝置相容性檢查
│   └── Step 0.1: HW Check (8317 BiCS5/gTLC/8329 BiCS8, UFS 3.1/2.2) → Expected: 支援則繼續，否則 NOT SUPPORTED
│
├── Phase 1: WRITE DESCRIPTOR — Data Length < bLength
│   ├── Step 1.1: QUERY Write Descriptor (Config, DataLen < bLength) → Expected: RESPONSE Code 0xF9, RESPONSE LENGTH == bLength
│   └── Step 1.2: QUERY Write Descriptor (OEM_ID String, DataLen < bLength) → Expected: RESPONSE Code 0xF9, RESPONSE LENGTH == bLength
│
├── Phase 2: READ DESCRIPTOR — Request LENGTH > bLength
│   ├── Step 2.1: QUERY Read Descriptor (Device, LENGTH > bLength) → Expected: Response DataSegment Length == Device bLength
│   ├── Step 2.2: QUERY Read Descriptor (Config, LENGTH > bLength) → Expected: Response DataSegment Length == Config bLength
│   ├── Step 2.3: QUERY Read Descriptor (Unit, LENGTH > bLength) → Expected: Response DataSegment Length == Unit bLength
│   ├── Step 2.4: QUERY Read Descriptor (Interconnect, LENGTH > bLength) → Expected: Response DataSegment Length == Interconnect bLength
│   ├── Step 2.5: QUERY Read Descriptor (OEM_ID String, LENGTH > bLength) → Expected: Response DataSegment Length == String bLength
│   ├── Step 2.6: QUERY Read Descriptor (Geometry, LENGTH > bLength) → Expected: Response DataSegment Length == Geometry bLength
│   ├── Step 2.7: QUERY Read Descriptor (Power, LENGTH > bLength) → Expected: Response DataSegment Length == Power bLength
│   └── Step 2.8: QUERY Read Descriptor (Device Health, LENGTH > bLength) → Expected: Response DataSegment Length == Device Health bLength
│
└── Phase 3: READ DESCRIPTOR — Request LENGTH <= bLength
    ├── Step 3.1: QUERY Read Descriptor (Device, LENGTH <= bLength) → Expected: Response DataSegment Length == Request LENGTH
    ├── Step 3.2: QUERY Read Descriptor (Config, LENGTH <= bLength) → Expected: Response DataSegment Length == Request LENGTH
    ├── Step 3.3: QUERY Read Descriptor (Unit, LENGTH <= bLength) → Expected: Response DataSegment Length == Request LENGTH
    ├── Step 3.4: QUERY Read Descriptor (Interconnect, LENGTH <= bLength) → Expected: Response DataSegment Length == Request LENGTH
    ├── Step 3.5: QUERY Read Descriptor (OEM_ID String, LENGTH <= bLength) → Expected: Response DataSegment Length == Request LENGTH
    ├── Step 3.6: QUERY Read Descriptor (Geometry, LENGTH <= bLength) → Expected: Response DataSegment Length == Request LENGTH
    ├── Step 3.7: QUERY Read Descriptor (Power, LENGTH <= bLength) → Expected: Response DataSegment Length == Request LENGTH
    └── Step 3.8: QUERY Read Descriptor (Device Health, LENGTH <= bLength) → Expected: Response DataSegment Length == Request LENGTH
```

> **Self-Verify**: leaf count = 19, `### Step` sections = 19, all leaves have `→ Expected:` ✅

---

## Phase 0 — 裝置相容性檢查

### Step 0.1: 裝置相容性檢查

**目的**: 確認 IC / NAND / UFS 版本組合為支援的配置。

| 檢查項目 | 條件 |
|---------|------|
| IC + NAND | 8317 BiCS5 (KIC) 或 gTLC 或 8329 BiCS8 |
| UFS Version | 3.1 或 2.2 |

**Expected**: 支援則繼續，否則 Pattern 判定為 `NOT SUPPORTED`。

---

## Phase 1 — WRITE DESCRIPTOR：Data Length < bLength

### Step 1.1: WRITE DESCRIPTOR — Configuration Descriptor, Data Length < bLength

**UFS QUERY**: `WRITE DESCRIPTOR`

**目的**: 以短於 descriptor bLength 的 Data Length 寫入，驗證裝置拒絕並回報實際 bLength。

| Field | Value |
|-------|-------|
| Opcode | 0x08（WRITE DESCRIPTOR） |
| IDN | 0x01（Configuration Descriptor） |
| Selector | 0x00 |
| Index | Config Descriptor Index |
| Data Length | < bLength |

**Expected**: RESPONSE Code 0xF9, RESPONSE LENGTH == descriptor bLength。

**UFS SPEC Reference**: JESD220H Section 14.1.3, 14.1.4.2

---

### Step 1.2: WRITE DESCRIPTOR — OEM_ID String Descriptor, Data Length < bLength

**UFS QUERY**: `WRITE DESCRIPTOR`

| Field | Value |
|-------|-------|
| Opcode | 0x08（WRITE DESCRIPTOR） |
| IDN | OEM_ID String Descriptor |
| Selector | 0x00 |
| Index | OEM_ID Index |
| Data Length | < bLength |

**Expected**: RESPONSE Code 0xF9, RESPONSE LENGTH == descriptor bLength。

---

## Phase 2 — READ DESCRIPTOR：Request LENGTH > bLength

> 當 LENGTH > bLength 時，裝置回傳完整 descriptor，Response DataSegment Length == bLength。

### Step 2.1: READ DESCRIPTOR — Device Descriptor

**UFS QUERY**: `READ DESCRIPTOR`

| Field | Value |
|-------|-------|
| Opcode | 0x07（READ DESCRIPTOR） |
| IDN | 0x00（Device Descriptor） |
| Selector | 0x00 |
| Index | 0x00 |
| Request LENGTH | > Device Descriptor bLength |

**Expected**: Response DataSegment Length == Device Descriptor bLength。

---

### Step 2.2: READ DESCRIPTOR — Configuration Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | 0x01（Configuration Descriptor） |
| Index | Config Descriptor Index |
| Request LENGTH | > Config bLength |

**Expected**: Response DataSegment Length == Config bLength。

---

### Step 2.3: READ DESCRIPTOR — Unit Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | 0x02（Unit Descriptor） |
| Index | LUN Index |
| Request LENGTH | > Unit bLength |

**Expected**: Response DataSegment Length == Unit bLength。

---

### Step 2.4: READ DESCRIPTOR — Interconnect Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | 0x04（Interconnect Descriptor） |
| Index | 0x00 |
| Request LENGTH | > Interconnect bLength |

**Expected**: Response DataSegment Length == Interconnect bLength。

---

### Step 2.5: READ DESCRIPTOR — OEM_ID String Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | OEM_ID String Descriptor |
| Index | OEM_ID Index |
| Request LENGTH | > String bLength |

**Expected**: Response DataSegment Length == String bLength。

---

### Step 2.6: READ DESCRIPTOR — Geometry Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | 0x07（Geometry Descriptor） |
| Index | 0x00 |
| Request LENGTH | > Geometry bLength |

**Expected**: Response DataSegment Length == Geometry bLength。

---

### Step 2.7: READ DESCRIPTOR — Power Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | 0x08（Power Parameters Descriptor） |
| Index | 0x00 |
| Request LENGTH | > Power bLength |

**Expected**: Response DataSegment Length == Power bLength。

---

### Step 2.8: READ DESCRIPTOR — Device Health Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | 0x09（Device Health Descriptor） |
| Index | 0x00 |
| Request LENGTH | > Device Health bLength |

**Expected**: Response DataSegment Length == Device Health bLength。

---

## Phase 3 — READ DESCRIPTOR：Request LENGTH <= bLength

> 當 LENGTH <= bLength 時，裝置僅回傳 Request LENGTH 大小的資料。

### Step 3.1: READ DESCRIPTOR — Device Descriptor

**UFS QUERY**: `READ DESCRIPTOR`

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | 0x00（Device Descriptor） |
| Index | 0x00 |
| Request LENGTH | <= Device bLength |

**Expected**: Response DataSegment Length == Request LENGTH。

---

### Step 3.2: READ DESCRIPTOR — Configuration Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | 0x01 |
| Index | Config Index |
| Request LENGTH | <= Config bLength |

**Expected**: Response DataSegment Length == Request LENGTH。

---

### Step 3.3: READ DESCRIPTOR — Unit Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | 0x02 |
| Index | LUN Index |
| Request LENGTH | <= Unit bLength |

**Expected**: Response DataSegment Length == Request LENGTH。

---

### Step 3.4: READ DESCRIPTOR — Interconnect Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | 0x04 |
| Index | 0x00 |
| Request LENGTH | <= Interconnect bLength |

**Expected**: Response DataSegment Length == Request LENGTH。

---

### Step 3.5: READ DESCRIPTOR — OEM_ID String Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | OEM_ID String |
| Index | OEM_ID Index |
| Request LENGTH | <= String bLength |

**Expected**: Response DataSegment Length == Request LENGTH。

---

### Step 3.6: READ DESCRIPTOR — Geometry Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | 0x07 |
| Index | 0x00 |
| Request LENGTH | <= Geometry bLength |

**Expected**: Response DataSegment Length == Request LENGTH。

---

### Step 3.7: READ DESCRIPTOR — Power Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | 0x08 |
| Index | 0x00 |
| Request LENGTH | <= Power bLength |

**Expected**: Response DataSegment Length == Request LENGTH。

---

### Step 3.8: READ DESCRIPTOR — Device Health Descriptor

| Field | Value |
|-------|-------|
| Opcode | 0x07 |
| IDN | 0x09 |
| Index | 0x00 |
| Request LENGTH | <= Device Health bLength |

**Expected**: Response DataSegment Length == Request LENGTH。

---

## Self-Verify

| 檢查 | 結果 |
|:---|:---|
| Tree leaf count | 19 |
| `### Step` sections | 19 |
| 每個 leaf 有 `→ Expected:` | ✅ |
| 每個 Expected 精確（非模糊詞） | ✅ |


---

## 自我驗證

- Tree Diagram leaf steps: **19**
- `### Step` sections: **19**
- ✓
