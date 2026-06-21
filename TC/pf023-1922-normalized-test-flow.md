---
title: PF023_1922-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf023_1922, scsi-cmd, query, flag, access-property]
description: >
  PF023_1922 Flag Access Property Default Boundary Test — 驗證所有 UFS Flag 的
  Access Property（Read/Read-Only/Persistent/Volatile/Set-Only/Write-Only）及
  Index/Selector 邊界行為。
sources:
  - JIRA: PF023_1922 (SYSTCUFS-2223)
  - UFS Spec: JESD220H Section 14.2 (Flags)
---

# PF023_1922 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

遍歷所有 UFS Flag，驗證各 Access Property 的行為：Read、Read-Only、Persistent(Reset 前後)、Volatile(Reset 前後)、Set-Only、以及 Index/Selector 邊界錯誤處理。

## 測試架構

```
├── Test 1: Read Property Flag
│   └── READ FLAG (all flags with Read property) → expect Pass
│
├── Test 2: Read-Only Property Flag
│   └── READ FLAG (all Read-Only flags) → expect Pass
│
├── Test 3: Persistent Property Flag — Write Twice
│   ├── READ FLAG = X
│   ├── SET/CLEAR/TOGGLE → value != X
│   └── READ FLAG → verify changed
│
├── Test 4: Persistent Property Flag — Persistent After Reset
│   ├── Random Reset
│   └── READ FLAG → expect value == Y (same as before reset)
│
├── Test 5: Persistent Property Flag — Write After Reset
│   ├── SET/CLEAR/TOGGLE → value != Y
│   └── READ FLAG → verify changed
│
├── Test 6: Volatile Property Flag — Write Twice
│   ├── READ FLAG = X
│   ├── SET/CLEAR/TOGGLE → value != X
│   └── READ FLAG → verify changed
│
├── Test 7: Volatile Property Flag — Volatile After Reset
│   ├── Random Reset
│   └── READ FLAG → expect value != previous (不同)
│
├── Test 8: Volatile Property Flag — Write After Reset
│   └── SET/CLEAR/TOGGLE → verify can change
│
├── Test 9: Set-Only Property Flag — Set Twice
│   └── SET FLAG × 2 → expect Pass (若 fail 則用 CLEAR FLAG)
│
├── Test 10: Set-Only Property Flag — Clear After Reset
│   ├── Random Reset
│   └── READ FLAG → expect value = 0
│
├── Test 11: Set-Only Property Flag — Re-Set After Reset
│   └── SET FLAG → expect Pass
│
└── Test 12: Index/Selector Boundary Error
    ├── READ FLAG with index > max boundary → expect fail (or Pass with value unchanged)
    ├── READ FLAG with selector > max boundary → expect fail (or Pass with value unchanged)
    └── SET FLAG with out-of-range index/selector → expect fail or Pass+unchanged
```

## Flag Access Property 類型

| Property | 行為 |
|:---|:---|
| Read (R) | 可讀取 |
| Read-Only (RO) | 僅可讀取，不可寫入 |
| Write-Only (WO) | 僅可寫入（SET/CLEAR/TOGGLE），不可讀取 |
| Set-Only (SO) | 僅可 SET，不可 CLEAR/TOGGLE |
| Persistent (P) | Reset 後值保留 |
| Volatile (V) | Reset 後值重置為預設值 |
| Write-Once (WO) | 僅可寫入一次 |

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
