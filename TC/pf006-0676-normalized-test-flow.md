---
title: PF006_0676_Wearleveling_Trigger_Cnt-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf006_0676, scsi-cmd, wear-leveling, bkop, vender-cmd]
description: >
  PF006_0676 Wear Leveling Trigger Count — 透過 VU Command 設定 Erase Count
  觸發 Wear Leveling，監測 BKOPS status 直到完成，驗證 WL Trigger Count
  等於 Free VB Count。
sources:
  - JIRA: PF006_0676 (SYSTCUFS-837)
  - UFS Spec: JESD220H Section 13.4.6 (BKOPS), Section 14.3 (Attributes)
---

# PF006_0676 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

透過 Vendor-Unique Command 設定特定 VB 的 Erase Count（Used VB=40, Free Q VB=401），
觸發 Data GC Wear Leveling，然後 Polling BKOPS Status 直到完成，
驗證 Wear Leveling Trigger Count 等於 Free VB Count。

## IC/NAND 相容性檢查

| 條件 | 值 |
|------|-----|
| IC | 8317 |
| NAND | BICS5 gTLC |
| 不支援時 | Pattern 判定為 `NOT SUPPORTED`，終止測試 |
| 備註 | 限定 KIC 專案（8317 BICS5 / 8329 BICS8） |

## JIRA Step 對照

| JIRA Step | 原始描述 | 正規化後對應 |
|-----------|---------|-------------|
| Step 1 | IC/NAND check | Step 0.2 |
| Step 2 | Get WL trigger count | Step 0.3 |
| Step 3 | Seq Write 512KB × 10×VB | Step 1.1 |
| Step 4 | Select 10 VB from free q group | Step 1.3 (VU) |
| Step 5 | Select 10 VB from used pool | Step 1.2 (VU) |
| Step 6 | Set erase count (VU cmd 0x2B) | Step 2.1 |
| Step 7 | Poll BKOPS status | Step 2.2~2.3 |
| Step 8 | Check WL trigger count == free VB | Step 2.4 |

---

## 測試架構

```
PF006_0676 Test Flow
│
├── Phase 0: 初始化與前置檢查
│   ├── Step 0.1: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│   ├── Step 0.2: HW Check — 確認 IC/NAND 相容性 → Expected: IC=8317, NAND=BICS5, 否則 NOT SUPPORTED
│   └── Step 0.3: [VU] Get Event Info (index=0xC1, offset=138) — 讀取 WL 執行次數並儲存 → Expected: 回傳當前 WL Trigger Count
│
├── Phase 1: 準備 VB 並寫入資料
│   ├── Step 1.1: WRITE(10) Seq — LBA random, chunk=512KB, total=VB_size×10 → Expected: GOOD Status
│   ├── Step 1.2: [VU] Select VB — 從 used pool (VB group=16) 選 10 個 VB → Expected: 成功選取 10 used VB
│   └── Step 1.3: [VU] Select VB — 從 free q group (VB group=23) 選 10 個 VB → Expected: 成功選取 10 free VB
│
└── Phase 2: 觸發 Wear Leveling 並驗證
    ├── Step 2.1: [VU] Set Erase Count (index=0x2B) — Used VB EC=40, Free VB EC=401 → Expected: Set 成功
    ├── Step 2.2: QUERY Read Attribute (bBackgroundOpStatus) — Polling BKOPS → Expected: 回傳當前 BKOPS Status
    ├── Step 2.3: 驗證 BKOPS 完成 — Status 從 02h 回到 00h → Expected: bBackgroundOpStatus == 0x00
    └── Step 2.4: [VU] Get Event Info + Verify — WL Trigger Count == Free VB Count → Expected: Trigger Count Match
```

---

## Phase 0 — 初始化與前置檢查

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

### Step 0.2: 裝置相容性檢查

| Check | Expected Value |
|-------|---------------|
| IC | 8317 |
| NAND | BICS5 gTLC |

**若不支援**: Pattern 判定為 `NOT SUPPORTED`，終止測試。

---

### Step 0.3: [VU] 讀取當前 WL Trigger Count

**VU Operation**: `Get Event Info (index=0xC1, offset=138)`

**目的**: 讀取當前 Wear Leveling 執行次數並儲存為 `WL_cnt_before`。

**Expected**: 回傳當前 WL 執行次數值。

---

## Phase 1 — 準備 VB 並寫入資料

### Step 1.1: Sequential Write

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Logical Block Address | Random (0 ~ total_capacity) |
| Transfer Length | per chunk = 512KB (1024 blocks @ 512B) |
| Total Size | VB_size × 10 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

### Step 1.2: [VU] Select Used VB

**VU Operation**: `Select VB from used pool (VB group=16)`

**目的**: 從 used pool 中選取 10 個 VB，用於後續 Erase Count 設定。

**Expected**: 成功選取 10 個 used VB。

---

### Step 1.3: [VU] Select Free VB

**VU Operation**: `Select VB from free q group (VB group=23)`

**目的**: 從 free q 中選取 10 個 VB。

**Expected**: 成功選取 10 個 free VB。

---

## Phase 2 — 觸發 Wear Leveling 並驗證

### Step 2.1: [VU] Set Erase Count

**VU Operation**: `Set Erase Count (index=0x2B)`

| Target | Erase Count | 說明 |
|:---|:---|:---|
| Used VB (Step 1.2) | 40 | 設定較低的 EC 使其為 WL target |
| Free Q VB (Step 1.3) | 401 | 設定較高的 EC 觸發 WL 搬移條件 |

**Expected**: Erase Count 設定成功。

---

### Step 2.2: Polling BKOPS Status

**UFS QUERY**: `READ ATTRIBUTE (bBackgroundOpStatus)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| IDN | 0x14 (bBackgroundOpStatus) |
| Index | 0x00 |
| Selector | 0x00 |

**Expected**: 回傳當前 BKOPS Status。

**UFS SPEC Reference**: JESD220H Section 14.3.1 (bBackgroundOpStatus, IDN 0x14)

---

### Step 2.3: 驗證 BKOPS 完成

**目的**: Polling bBackgroundOpStatus 直到穩定為 0x00。

**Rule**:
- 等待 status == 0x02（In Progress）
- 持續 Polling 直到 status == 0x00
- 需連續 5 次 status == 0x00 才確認，避免 FW 暫態 (2→0→2→0)
- Timeout: 15 分鐘，超時判定 FAIL

**Expected**: `bBackgroundOpStatus == 0x00`（BKOPS 完成）。

**UFS SPEC Reference**: JESD220H Section 13.4.6 (BKOPS), Section 14.3.1

---

### Step 2.4: 驗證 WL Trigger Count

**VU Operation**: `Get Event Info (index=0xC1, offset=138)` + 比對

**目的**: 讀取 WL 執行次數，確認 `WL_cnt_after - WL_cnt_before == Free VB Count (10)`。

**Expected**: `WL Trigger Count == Free VB Count`。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | Step 0.1 |
| 0x2A | WRITE(10) | 10 | Step 1.1 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 存取 | 使用位置 |
|:---|:---|:---|:---|:---|
| 0x14 | bBackgroundOpStatus | 0x03 (READ ATTRIBUTE) | R | Step 2.2 |

## Vendor-Unique Operations

| Index | Description | 使用位置 |
|:---|:---|:---|
| 0xC1 | Get Event Info (offset 138 = WL count) | Step 0.3, 2.4 |
| 0x2B | Set Erase Count | Step 2.1 |

## VB Group 定義

| Group | Meaning |
|:---|:---|
| 16 | Used pool VB |
| 23 | Free Q VB |

---

## 自我驗證

- Tree Diagram leaf steps: **8** (0.1, 0.2, 0.3, 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4 = 10)
- `### Step` sections: **10** ✓
