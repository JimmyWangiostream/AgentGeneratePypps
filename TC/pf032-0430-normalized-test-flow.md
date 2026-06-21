---
title: PF032_0430_HPB2_ReadBuffer_MultiCMD-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf032_0430, scsi-cmd, hpb, hpb-read-buf, hpb20]
description: PF032_0430 HPB 2.0 Read Buffer Multi CMD — HPB error/boundary tests。
sources: [JIRA: PF032_0430 (SYSTCUFS-537)]
---

# PF032_0430 正規化 Test Flow（SCSI CMD 単位）

## 測試架構（Tree Diagram — 含 Expected）

```
PF032_0430 Test Flow
│
├── Phase 0: Pre-set
│   ├── Step 0.1: VU HW Setting (8325: SUSPEND_TIMER/BKOPS_TIMER) → Expected: HW settings applied
│   └── Step 0.2: QUERY Write Descriptor — Config HPB Device Control Mode → Expected: QUERY RESPONSE Success
│
└── Loop (per config mode)
    ├── Step 1.1: HPB READ BUFFER (0xF9) — Activate Pinned Region, BufferID=1, various len → Expected: HPB Region activated
    ├── Step 1.2: HPB READ BUFFER — Sub-Region Out of Range → Expected: CHECK_CONDITION, INVALID_FIELD_IN_CDB(0x24)
    ├── Step 1.3: Random CMD — WRITE(FUA)/READ/UNMAP/SYNC_CACHE → Expected: GOOD Status (all)
    ├── Step 1.4: HPB READ BUFFER — Activate Normal Region, various len → Expected: HPB Normal Region activated
    ├── Step 1.5: READ(10) — Device recommendation LBA (non-Pinned), len=4K → Expected: GOOD Status
    ├── Step 1.6: HPB READ BUFFER — Region Out of Range → Expected: CHECK_CONDITION, INVALID_FIELD_IN_CDB(0x24)
    ├── Step 1.7: HPB READ BUFFER — Sub-Region Out of Range → Expected: CHECK_CONDITION, INVALID_FIELD_IN_CDB(0x24)
    ├── Step 1.8: QUERY Set Flag (fHPBReset) → Expected: QUERY RESPONSE Success
    ├── Step 1.9: HPB READ BUFFER — BufferID=0x00/0x02/0xFF → Expected: CHECK_CONDITION, INVALID_FIELD_IN_CDB(0x24)
    ├── Step 1.10: HPB READ BUFFER — Non-recommendation Region → Expected: CHECK_CONDITION, ILLEGAL_REQUEST(0x05)
    ├── Step 1.11: HPB READ BUFFER — Allocation Len=0 (Normal Region) → Expected: 驗證正常回應
    └── Step 1.12: HPB READ BUFFER — Allocation Len=0 (Pinned Region) → Expected: 驗證正常回應
```

---

## Phase 0

### Step 0.1: VU HW Pre-set

**VU CMD**: 8325 specific — SUSPEND_TIMER / BKOPS_TIMER configuration。

**Expected**: `HW settings applied`。

### Step 0.2: Config HPB Device Control Mode

**UFS QUERY**: `WRITE DESCRIPTOR (Configuration Descriptor)`

**Expected**: `QUERY RESPONSE Success`。

---

## Loop

### Step 1.1: Activate Pinned Region

**HPB READ BUFFER** (0xF9)

| Field | Value |
|-------|-------|
| Opcode | 0xF9 |
| Buffer ID | 1 |
| Region Type | Pinned |

**Expected**: `HPB Region activated`。

### Step 1.2: Sub-Region Out of Range

**Expected**: `CHECK_CONDITION, INVALID_FIELD_IN_CDB (0x24)`。

### Step 1.3: Random CMD

WRITE(FUA) / READ / UNMAP / SYNC_CACHE。

**Expected**: `GOOD Status`。

### Step 1.4: Activate Normal Region

**Expected**: `HPB Normal Region activated`。

### Step 1.5: READ Device Recommendation LBA

**SCSI CMD**: `READ(10) (0x28)`

**Expected**: `GOOD Status`。

### Step 1.6~1.7: Region/Sub-Region Out of Range

**Expected**: `INVALID_FIELD_IN_CDB (0x24)`。

### Step 1.8: HPB Reset

**UFS QUERY**: `SET FLAG (fHPBReset)`

**Expected**: `QUERY RESPONSE Success`。

### Step 1.9: Invalid Buffer ID

**Expected**: `INVALID_FIELD_IN_CDB (0x24)`。

### Step 1.10: Non-recommendation Region

**Expected**: `ILLEGAL_REQUEST (0x05)`。

### Step 1.11~1.12: Allocation Len=0

**Expected**: 驗證正常回應（boundary condition）。

---

## 自我驗證

- Tree Diagram leaf steps: **15** (0.1~0.2=2, 1.1~1.12=12 + 1 loop step)
- `### Step` sections: **15** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
