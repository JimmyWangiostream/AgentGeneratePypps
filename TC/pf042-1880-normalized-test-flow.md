---
title: PF042_1880_SSLC_HW_Page_WB_PE_Threshold-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf042_1880, scsi-cmd, sslc, wb, vu, pe-threshold]
description: PF042_1880 SSLC HW Page — WB PE Threshold 對 SSLC/Dynamic Pool 影響。
sources: [JIRA: PF042_1880 (SYSTCUFS-2183)]
---

# PF042_1880 正規化 Test Flow

## IC: 8329 QLC, WB support

## 測試架構（Tree Diagram — 含 Expected）

```
PF042_1880 Test Flow
│
├── Phase 0: 初始化
│   ├── Step 0.1: HW Check (8329 QLC, WB) → Expected: 支援, NOT SUPPORTED otherwise
│   └── Step 0.2: QUERY Write Descriptor — Config WB 4GB → Expected: QUERY RESPONSE Success
│
├── Test A: WB_PE_THRESHOLD=30%, bit[7]=1, D3 avg PE > 30%
│   ├── Step A.1: VU HW (0xA93) = 0xBE (bit7=1, thresh=30%) → Expected: HW setting applied
│   ├── Step A.2: VU — D3 erase count = 1500*0.3+1 (PE>30%) → Expected: erase count set
│   ├── Step A.3: HW Reset → Expected: Reset device success
│   ├── Step A.4: QUERY Set/Clear Flag (fWriteBoosterEn) — test both → Expected: QUERY RESPONSE Success
│   ├── Step A.5: UNMAP + SET FLAG (fPurgeEnable) → Expected: bPurgeStatus == 0x00
│   ├── Step A.6: WRITE(10) — Ran, total=2 VB, CS=16M → Expected: GOOD Status
│   ├── Step A.7: WRITE(10) — 1 VB, CS=512KB → Expected: GOOD Status
│   └── Step A.8: VU LBA→PBA → verify VB=SSLC (group 7/15, partition 3) → Expected: VB == SSLC
│
├── Test B: D3 avg PE <= 30%
│   ├── Step B.1: VU — D3 erase = 1500*0.2 → Expected: erase count set
│   ├── Step B.2: HW Reset → Expected: Reset device success
│   ├── Step B.3: QUERY Set/Clear Flag (fWriteBoosterEn) → Expected: QUERY RESPONSE Success
│   ├── Step B.4: Erase Purge All → Expected: bPurgeStatus == 0x00
│   ├── Step B.5: WRITE(10) — 1 VB, CS=512KB → Expected: GOOD Status
│   └── Step B.6: VU — VB verify: WB on→Dynamic Pool; WB off→SSLC → Expected: WB on: Dynamic Pool; WB off: SSLC
│
├── Test C: WB_PE_THRESHOLD=60%, bit[7]=0
│   ├── Step C.1: VU HW (0xA93) = 0x3C (bit7=0, thresh=60%) → Expected: HW setting applied
│   ├── Step C.2: Case 1: PE>60%; Case 2: PE<=60% → Expected: erase counts set
│   ├── Step C.3: HW Reset → Expected: Reset device success
│   └── (Repeat A.4~A.8) → Expected: per Test A expectations
│
└── Recovery
    └── Step R.1: VU — Restore erase counts + HW settings → Expected: restored
```

---

## 附錄

| Opcode | Command |
|:---|:---|
| 0x2A | WRITE(10) |
| 0x42 | UNMAP |

## 自我驗證

- Tree leaf: **20** ✓ 每個有 `→ Expected:` ✓
- Reset Expected 使用 `Reset device success` ✓
