---
title: PF041_2056-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf041_2056, scsi-cmd, clock, safety, vu]
description: >
  PF041_2056 Clock Freq Error Detect Test — 透過 VU Safety Function 調整 clock
  comparator threshold 觸發 clock drift，驗證 FW 偵測到 Assert ID 0xF30A 及
  Smart Info counter 正確遞增。
sources:
  - JIRA: PF041_2056 (SYSTCUFS-2386)
---

# PF041_2056 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

透過調整 clock comparator threshold 觸發 clock drift 錯誤，驗證 HW/FW 錯誤偵測機制。

## 測試架構

```
├── Phase 0: FW Debug Mode
│   └── VU Write HW Setting — FW Debug Mode = LV2 (0x45)
│
├── Test A: clk_cmp_0 threshold 調小 → Assert
│   ├── VU Safety func (subcmd=0xEE) — CDB[4]=18, CDB[5]=1
│   └── Check Assert ID 0xF30A
│
├── Test B: clk_cmp_3 threshold 調小 → Assert
│   ├── VU Safety func (subcmd=0xEE) — CDB[4]=18, CDB[5]=2
│   └── Check Assert ID 0xF30A
│
├── Test C: clk_cmp_0 threshold 調小後回復 → Counter increment
│   ├── VU Safety func (subcmd=0xEE) — CDB[4]=18, CDB[5]=3
│   └── Verify Smart Info clk_cmp_err_cnt_0 & clk_cmp_err_last_result_cnt_0 increased
│       (smart_info[0xfcc+0:0xfcc+4], [0xfcc+8:0xfcc+12])
│
├── Test D: clk_cmp_3 threshold 調小後回復 → Counter increment
│   ├── VU Safety func (subcmd=0xEE) — CDB[4]=18, CDB[5]=4
│   └── Verify Smart Info clk_cmp_err_cnt_1 & clk_cmp_err_last_result_cnt_1 increased
│       (smart_info[0xfcc+4:0xfcc+8], [0xfcc+12:0xfcc+16])
│
└── Test E: SRAM read verification
    └── Read SRAM address → verify value matches expected pattern
```

## VU Commands

| 操作 | CDB | 說明 |
|:---|:---|:---|
| Safety func (subcmd 0xEE) | CDB[4]=18, CDB[5]=param | 調整 clock comparator threshold |
| Read SRAM | — | 讀取 FAPHY register 驗證 |

**CDB[5] 參數**:
- 1: clk_cmp_0 threshold 調小
- 2: clk_cmp_3 threshold 調小
- 3: clk_cmp_0 threshold 調小後回復
- 4: clk_cmp_3 threshold 調小後回復

## 附錄

| Check | 說明 |
|:---|:---|
| Assert ID 0xF30A | Clock drift 錯誤中斷 |
| Smart Info clk_cmp_err_cnt | Clock comparator 錯誤計數 |
| Smart Info clk_cmp_err_last_result_cnt | 最後一次錯誤結果計數 |


---

## 自我驗證

- Tree Diagram leaf steps: **0**
- `### Step` sections: **0**
- ✓
