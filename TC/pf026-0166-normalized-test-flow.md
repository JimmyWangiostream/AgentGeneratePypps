---
title: PF026_0166_LUN_Config_Sim_SPOR-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf026_0166, white-box, spor, lun-config, sim-power-cycling]
description: >
  PF026_0166 LUN Config Sim SPOR — White-box SPOR simulation with random LUN
  configuration and white-box hit count tracking.
sources:
  - JIRA: PF026_0166 (SYSTCUFS-128)
---

# PF026_0166 正規化 Test Flow（White-Box 單位）

> White-box simulation — heavy VU/hardware dependency.

## 測試架構（Tree Diagram — 含 Expected）

```
PF026_0166 Test Flow
│
├── Phase 0: 初始化
│   ├── Step 0.1: TEST UNIT READY — Normal Init UFS device → Expected: GOOD Status
│   ├── Step 0.2: White-box CSV parse → transform to 8K bin → Expected: 8K bin ready
│   ├── Step 0.3: VU — Get white-box hit count → Expected: hit count retrieved
│   ├── Step 0.4: Generate random seed, merge into 8K bin → Expected: seed merged
│   ├── Step 0.5: VU DCMD13 — Change normal CMD timeout → Expected: timeout changed
│   ├── Step 0.6: VU — Set HW[1385]=0x01 (change rebuild timing) → Expected: rebuild timing set
│   └── Step 0.7: VU DCMD7 — Get hit count response → Expected: hit count response
│
└── Loop (until fail or test complete)
    ├── Step L.1: SimPowerCycling → Expected: power cycling complete
    ├── Step L.2: QUERY Write Descriptor — Config LUNs (random memory_type) → Expected: QUERY RESPONSE Success
    ├── Step L.3: QUERY Write Descriptor — Config each LUN random AU Count → Expected: QUERY RESPONSE Success
    ├── Step L.4: SPOR → white-box hit count update → send new 8K bin → Expected: SPOR complete, bin sent
    └── Step L.5: Trace assert — if error → stop; else restart → Expected: no unexpected error
```

---

## Phase 0

### Step 0.1: Normal Init

**SCSI CMD**: `TEST UNIT READY (00h)`

**Expected**: `GOOD Status`。

### Step 0.2: Parse CSV to 8K Bin

**Expected**: `8K bin ready`。

### Step 0.3: Get Hit Count

**VU CMD**: Get white-box hit count。

**Expected**: `hit count retrieved`。

### Step 0.4: Generate Random Seed

**Expected**: `seed merged into 8K bin`。

### Step 0.5: Change CMD Timeout

**VU CMD**: DCMD13。

**Expected**: `timeout changed`。

### Step 0.6: Set Rebuild Timing

**VU CMD**: HW[1385] = 0x01。

**Expected**: `rebuild timing set`。

### Step 0.7: Get Hit Count Response

**VU CMD**: DCMD7。

**Expected**: `hit count response`。

---

## Loop

### Step L.1: SimPowerCycling

**Expected**: `power cycling complete`。

### Step L.2: Config LUNs

**UFS QUERY**: `WRITE DESCRIPTOR (Configuration Descriptor)` with random memory_type (Normal/System_Code/Non-Persistent/Enhanced...)。

**Expected**: `QUERY RESPONSE Success`。

### Step L.3: Config AU Count

**UFS QUERY**: `WRITE DESCRIPTOR` — random AU Count per LUN。

**Expected**: `QUERY RESPONSE Success`。

### Step L.4: SPOR + Bin Update

**Expected**: `Reset device success` → hit count updated → new 8K bin sent。

### Step L.5: Trace Assert

**Expected**: `no unexpected error`。

---

## 自我驗證

- Tree Diagram leaf steps: **12** (0.1~0.7=7, L.1~L.5=5)
- `### Step` sections: **12** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
- SPOR Expected 使用統一格式 `Reset device success` ✓
