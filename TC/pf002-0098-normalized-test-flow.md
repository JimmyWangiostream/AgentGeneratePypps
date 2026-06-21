---
title: PF002_0098_Boot_Stress-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf002_0098, scsi-cmd, boot-lun, reset, stress]
description: >
  PF002_0098 Boot Stress Test — 配置 Boot LU 後寫入資料，在隨機 Reset
  後做 100 次 Reboot + Read Compare 的壓力測試，驗證 Boot LU 資料完整性。
sources:
  - JIRA: PF002_0098 (SYSTCUFS-107)
  - UFS Spec: JESD220H Section 13.4.4 (Boot), Section 14.1 (Device Descriptor), Section 14.3 (Attributes)
---

# PF002_0098 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

驗證 Boot LU 在反覆 Reset + Reboot 壓力下的資料完整性：
1. 配置並啟用 Boot LU
2. 寫入測試資料至 Boot LU
3. 執行 100 次 loop：隨機 Reset → Reboot → Read Compare Boot Data

## JIRA Step 對照

| JIRA Step | 原始描述 | 正規化後對應 |
|-----------|---------|-------------|
| Step 1 | Config device with boot LUN is needed | Phase 0: Boot LU 配置 |
| Step 2 | Enable Boot LUN | Step 0.3: Enable Boot LUN |
| Step 3 | Write data to Boot LUN | Phase 1: Write Boot Data |
| Step 4 | Random reset | Step 2.2: Random Reset |
| Step 5 | Reboot + read compare boot data | Step 2.4: Read Compare |
| Step 6 | Loop 100 times | Loop wrapper |

---

## 測試架構

```
PF002_0098 Test Flow
│
├── Phase 0: Boot LU 配置與啟用
│   ├── Step 0.1: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│   ├── Step 0.2: QUERY Read Descriptor (Device Descriptor) — 確認 bBootEnable 支援 → Expected: QUERY RESPONSE Success
│   ├── Step 0.3: QUERY Read Attribute (bBootLunEn) — 讀取目前 Boot LU 狀態 → Expected: QUERY RESPONSE Success
│   ├── Step 0.4: QUERY Write Attribute (bBootLunEn) — 啟用 Boot LU → Expected: QUERY RESPONSE Success
│   ├── Step 0.5: QUERY Read Attribute (bBootLunEn) — 確認已啟用 → Expected: bBootLunEn != 0x00
│   └── Step 0.6: QUERY Read Descriptor (Unit Descriptor) — 取得 Boot LU 之 LUN Number → Expected: QUERY RESPONSE Success, 回傳 bBootLunID
│
├── Phase 1: 寫入 Boot LU 測試資料
│   ├── Step 1.1: WRITE(10) — 寫入測試 Pattern 至 Boot LU → Expected: GOOD Status
│   └── Step 1.2: READ(10) — 讀取比對確認寫入成功 → Expected: GOOD Status, Data Match
│
└── Loop (100 次)
    │
    ├── Step L.1: Random Reset — 隨機選取 Reset 類型 → Expected: Reset device success
    ├── Step L.2: TEST UNIT READY — 確認 Device 就緒 → Expected: GOOD Status
    ├── Step L.3: POWER CONDITION Active — 確保 LUN 可操作 → Expected: LUN 進入 Active 狀態
    └── Step L.4: READ(10) — 讀取 Boot LU 資料並比對 → Expected: GOOD Status, Data Match
```

---

## Phase 0 — Boot LU 配置與啟用

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

**目的**: 確認 UFS Device 已上電且可接受命令。

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

### Step 0.2: 讀取 Device Descriptor（確認 Boot 支援）

**UFS QUERY**: `READ DESCRIPTOR (Device Descriptor)`

**目的**: 讀取 Device Descriptor 確認 `bBootEnable` 欄位支援 Boot 功能。

| Field | Value |
|-------|-------|
| Query Opcode | 0x07 (READ DESCRIPTOR) |
| IDN | 0x00 (Device Descriptor) |
| Index | 0x00 |
| Selector | 0x00 |
| Length | 0x40 (sufficient for full descriptor) |

**Expected**: `QUERY RESPONSE Success`，回傳完整 Device Descriptor，確認 `bBootEnable` 欄位存在。

**UFS SPEC Reference**: JESD220H Section 14.1.4.2 (Device Descriptor)

---

### Step 0.3: 讀取 bBootLunEn 目前狀態

**UFS QUERY**: `READ ATTRIBUTE (bBootLunEn)`

**目的**: 讀取目前 Boot LU Enable 狀態。

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| IDN | 0x00 (bBootLunEn) |
| Index | 0x00 |
| Selector | 0x00 |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.3.1 (bBootLunEn, IDN 0x00)

---

### Step 0.4: 啟用 Boot LU

**UFS QUERY**: `WRITE ATTRIBUTE (bBootLunEn)`

**目的**: 設定 bBootLunEn 啟用對應的 Boot LUN。

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| IDN | 0x00 (bBootLunEn) |
| Index | 0x00 |
| Selector | 0x00 |
| Value | 依所需 Boot LU 設定 bit mask |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.3.1 (bBootLunEn), Section 13.4.4 (Boot)

---

### Step 0.5: 確認 Boot LU 已啟用

**UFS QUERY**: `READ ATTRIBUTE (bBootLunEn)`

**目的**: 回讀確認 bBootLunEn 已確實啟用。

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| IDN | 0x00 (bBootLunEn) |
| Index | 0x00 |
| Selector | 0x00 |

**Expected**: `QUERY RESPONSE Success`，`bBootLunEn != 0x00`（至少一個 Boot LU 已啟用）。

**UFS SPEC Reference**: JESD220H Section 14.3.1

---

### Step 0.6: 取得 Boot LU 之 LUN Number

**UFS QUERY**: `READ DESCRIPTOR (Unit Descriptor)`

**目的**: 讀取 Unit Descriptor 以獲取 Boot LU 對應的 `bLUN` 編號。

| Field | Value |
|-------|-------|
| Query Opcode | 0x07 (READ DESCRIPTOR) |
| IDN | 0x02 (Unit Descriptor) |
| Index | Boot LU index (依 bBootLunEn bit) |
| Selector | 0x00 |
| Length | 0x20 |

**Expected**: `QUERY RESPONSE Success`，回傳 `bBootLunID` 欄位值（對應 LUN number）。

**UFS SPEC Reference**: JESD220H Section 14.1.4.3 (Unit Descriptor)

---

## Phase 1 — 寫入 Boot LU 測試資料

### Step 1.1: 寫入測試資料至 Boot LU

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: 將已知測試 Pattern 寫入 Boot LU。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | Boot LU (from Step 0.6) |
| Logical Block Address | 0x00000000 |
| Transfer Length | Boot LU 可用空間 |
| Data | Known Test Pattern |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.43

---

### Step 1.2: 讀取比對確認寫入

**SCSI CMD**: `READ(10) (28h)`

**目的**: 讀回 Step 1.1 寫入的資料，確認寫入成功。

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | Boot LU |
| Logical Block Address | 0x00000000 |
| Transfer Length | Step 1.1 寫入大小 |

**Expected**: `GOOD Status` + `Data Match`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.18

---

## Loop — Reset + Reboot Stress (100 次)

### Step L.1: Random Reset

**目的**: 隨機選取一種 Reset 類型，模擬 Boot 過程中斷電/Reset 情境。

| Reset Type | 說明 |
|:---|:---|
| HW_RESET | RST_n signal hardware reset |
| RST_n | Reset signal toggle |
| EndPoint Reset | DME EndPointReset command |
| UniPro Reset | UniPro layer reset |

**Expected**: Device 完成 Link Startup，`fDeviceInit == 1`。

**UFS SPEC Reference**: JESD220H Section 10.4 (UFS Reset)

---

### Step L.2: 確認 Device 就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

**目的**: Reset 後確認 Device 可操作。

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

### Step L.3: 確認 LUN 進入 Active State

**SCSI CMD**: `START STOP UNIT (1Bh)`

**目的**: 確保 Boot LU 已進入 Active Power Condition 可進行 I/O。

| Field | Value |
|-------|-------|
| Opcode | 0x1B |
| START bit | 1 (Start) |
| Power Condition | 0x0 (Active) |

**Expected**: `GOOD Status`，Boot LU 可進行 READ/WRITE。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.25

---

### Step L.4: Read Compare Boot Data

**SCSI CMD**: `READ(10) (28h)`

**目的**: 讀取 Boot LU 資料並與 Step 1.1 寫入的 Test Pattern 進行比對。

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | Boot LU |
| Logical Block Address | 0x00000000 |
| Transfer Length | Step 1.1 寫入大小 |

**Expected**: `GOOD Status` + `Data Match`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.18

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | Step 0.1, L.2 |
| 0x1B | START STOP UNIT | 6 | Step L.3 |
| 0x28 | READ(10) | 10 | Step 1.2, L.4 |
| 0x2A | WRITE(10) | 10 | Step 1.1 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 存取 | 使用位置 |
|:---|:---|:---|:---|:---|
| 0x00 | bBootLunEn | 0x03/0x04 (READ/WRITE ATTRIBUTE) | R/W | Step 0.3, 0.4, 0.5 |
| 0x00 | Device Descriptor | 0x07 (READ DESCRIPTOR) | R | Step 0.2 |
| 0x02 | Unit Descriptor | 0x07 (READ DESCRIPTOR) | R | Step 0.6 |
| 0x01 | fDeviceInit | 0x01 (READ FLAG) | R | Step L.1 (驗證) |

## 附錄 C — UFS Reset 類型說明

| Reset Type | 說明 | SPEC Reference |
|:---|:---|:---|
| HW_RESET | RST_n signal hardware reset | JESD220H Section 10.4.2 |
| RST_n | Reset signal toggle | JESD220H Section 10.4.2 |
| EndPoint Reset | DME EndPointReset command | JESD220H Section 10.4.4 |
| UniPro Reset | UniPro layer reset | JESD220H Section 10.4.5 |

---

## 自我驗證

- Tree Diagram leaf steps: **14** (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 1.1, 1.2, L.1, L.2, L.3, L.4)
- Wait - recounting: Phase 0 has 6, Phase 1 has 2, Loop has 4 = 12 leaf steps
- Let me recount: 0.1-0.6 (6) + 1.1-1.2 (2) + L.1-L.4 (4) = 12
- `### Step` sections: **12** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
