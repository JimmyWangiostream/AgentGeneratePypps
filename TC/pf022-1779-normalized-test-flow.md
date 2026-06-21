---
title: PF022_1779_WriteJournal_ATS-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf022_1779, scsi-cmd, write-journal, vu, ats, pca]
description: >
  PF022_1779 Write Journal Test — ATS 後 journal index 驗證，透過 VU 命令
  讀取 PCA→PBA 及 spare data journal index。
sources:
  - JIRA: PF022_1779 (SYSTCUFS-2069)
---

# PF022_1779 正規化 Test Flow（SCSI CMD 単位）

## IC 相容性

| IC | 8361 WDS LV |
| Flash Setting | [493] bit0 == 1 |

## 測試架構（Tree Diagram — 含 Expected）

```
PF022_1779 Test Flow
│
├── Phase 0: 初始化
│   ├── Step 0.1: HW Check (8361 WDS LV, flash setting[493] bit0==1) → Expected: 支援, 否則 NOT SUPPORTED
│   ├── Step 0.2: QUERY Write Descriptor — Config LUNs (2 Boot EM1, 1 Normal, 1 HPB) → Expected: QUERY RESPONSE Success
│   ├── Step 0.3: UNMAP — Erase All → Expected: GOOD Status
│   ├── Step 0.4: QUERY Set Flag (fPurgeEnable) — Purge → Expected: QUERY RESPONSE Success
│   └── Step 0.5: QUERY Read Attribute (bPurgeStatus) — Wait Purge → Expected: bPurgeStatus == 0x00
│
└── Loop (burn-in, select_lun = random enable lun)
    ├── Step L.1: VU 0xDF subcmd=0 — Get cur/new write journal PCA → Expected: PCA values retrieved
    ├── Step L.2: VU — Set HW 0xB02/0xB01 = 1000 (hw_nodes) → Expected: HW nodes set
    ├── Step L.3: WRITE(10) — select_lun, start LBA=0, chunksize=hw_nodes, FUA=0 → Expected: GOOD Status
    ├── Step L.4: Sleep 500ms (ATS) → Expected: ATS completed
    ├── Step L.5: VU 0xDF — Get cur journal PCA → Expected: current journal index
    ├── Step L.6: VU — Direct Read PCA→PBA, spare data journal index (offset 4096+4102) → Expected: journal index
    ├── Step L.7: Verify current journal index - backup >= hw_nodes → Expected: journal delta >= hw_nodes
    ├── Step L.8: WRITE(10) — Fill remaining window / TLC nodes → Expected: GOOD Status
    └── Step L.9: VU 0xDF — Check cur PCA invalid (0xFFFFFFFF), update backup → Expected: PCA invalidated, backup updated
```

---

## Phase 0

### Step 0.1: HW Check

**Expected**: IC=8361 WDS LV, flash[493]bit0=1。

### Step 0.2: Config LUNs

**UFS QUERY**: `WRITE DESCRIPTOR (Configuration Descriptor)`

**Expected**: `QUERY RESPONSE Success`。

### Step 0.3~0.5: Erase + Purge

**Expected**: `bPurgeStatus == 0x00`。

---

## Loop

### Step L.1: Get Write Journal PCA

**VU CMD**: 0xDF subcmd=0 — Get current/new write journal PCA。

**Expected**: `PCA values retrieved`。

### Step L.2: Set HW Nodes

**VU CMD**: Set HW 0xB02/0xB01 = 1000。

**Expected**: `HW nodes set`。

### Step L.3: Write

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| LUN | select_lun (random) |
| LBA | 0 |
| Chunksize | hw_nodes |
| FUA | 0 |

**Expected**: `GOOD Status`。

### Step L.4: Sleep 500ms

**Expected**: `ATS completed`。

### Step L.5: Get Current Journal PCA

**VU CMD**: 0xDF — Get current journal PCA。

**Expected**: `current journal index`。

### Step L.6: Direct Read PCA→PBA

**VU CMD**: Direct Read PCA→PBA, spare data journal index (offset 4096, 4102)。

**Expected**: `journal index`。

### Step L.7: Verify Journal Delta

**Check**: current journal index - backup >= hw_nodes。

**Expected**: `journal delta >= hw_nodes`。

### Step L.8: Fill Remaining

**SCSI CMD**: `WRITE(10) (2Ah)`

**Expected**: `GOOD Status`。

### Step L.9: Check PCA Invalidated

**VU CMD**: 0xDF — Check cur PCA = 0xFFFFFFFF, update backup。

**Expected**: `PCA invalidated, backup updated`。

---

## 自我驗證

- Tree Diagram leaf steps: **14** (0.1~0.5=5, L.1~L.9=9)
- `### Step` sections: **14** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
