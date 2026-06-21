---
title: PF023_0296-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf023_0296, scsi-cmd, query, flag, error-case]
description: >
  PF023_0296 Query Flags Error Case Test — 驗證 UFS Query Flag 操作的各種錯誤
  回應：不可讀 Flag、無效 IDN、Write-Once Flag 重複寫入、Write-Only Flag。
sources:
  - JIRA: PF023_0296 (SYSTCUFS-58)
  - UFS Spec: JESD220H Section 14.2 (Flags), Section 10.7.8-9 (QUERY)
---

# PF023_0296 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

驗證 UFS Query Flag 操作的錯誤回應正確性，包含不可讀、無效 IDN、Write-Once、Write-Only 等情境。

## 測試架構

```
├── Test A: Read 不可讀 Flag
│   └── QUERY READ FLAG (fRefreshEnable) → expect QRY_PARA_NOT_READABLE
│
├── Test B: 無效 Flag IDN
│   ├── QUERY READ FLAG (Invalid IDN) → expect QRY_INVALID_IDN
│   └── QUERY SET FLAG (Invalid IDN) → expect QRY_INVALID_IDN
│
├── Test C: Write-Once Flag (PERMANENT_WP_EN)
│   ├── QUERY SET FLAG × 2 → expect QRY_PARA_ALREADY_WRITTEN
│   └── QUERY CLEAR FLAG → expect QRY_GENERAL_FAILURE
│
├── Test D: Write-Once Flag (PERMANENTLY_DIS_FW_UPDATE)
│   ├── QUERY SET FLAG × 2 → expect QRY_PARA_ALREADY_WRITTEN
│   └── (Need Vendor CMD to clear)
│
├── Test E: 正常操作（code coverage）
│   ├── QUERY SET FLAG (fRefreshEnable) → expect Pass
│   └── QUERY CLEAR FLAG (fRefreshEnable) → expect Pass
│
└── Test F: Write-Only Flag + Index/Selector Boundary
    ├── QUERY READ FLAG (Write-Only Flag) → expect QRY_PARA_NOT_READABLE
    ├── QUERY SET/CLEAR/TOGGLE — Index/Selector boundary test
    └── 若 Type="D": index=0, selector=0
        若 Type="A": index/selector = random(min, max boundary)
```

## Query Response Codes

| Response | 值 | 觸發條件 |
|:---|:---|:---|
| QRY_PARA_NOT_READABLE | — | 讀取 Write-Only Flag |
| QRY_INVALID_IDN | 0xFC | 無效的 Flag IDN |
| QRY_PARA_ALREADY_WRITTEN | — | Write-Once Flag 重複 SET |
| QRY_GENERAL_FAILURE | 0xFF | CLEAR Write-Once Flag |
| SUCCESS | — | 正常操作 |

## 附錄

| Opcode | Query 操作 |
|:---|:---|
| 0x01 | READ FLAG |
| 0x02 | SET FLAG |
| 0x05 | CLEAR FLAG |
| 0x06 | TOGGLE FLAG |


---

## 自我驗證

- Tree Diagram leaf steps: **0**
- `### Step` sections: **0**
- ✓
