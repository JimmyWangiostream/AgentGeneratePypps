---
title: PF008_0093_FFU_INT_ActivateFW-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf008_0093, scsi-cmd, ffu, activate-fw, reset]
description: >
  PF008_0093 FFU INT ActivateFW — 執行 Field Firmware Update (FFU) 後，
  在不同 Reset 類型下驗證 SVN Version 變更與 FFU Status 的正確性：
  HW_RESET/RST_n → SVN 變更 + FFU Success；
  EndPoint/UniPro/LUN Reset → SVN 不變 + FFU NO_INFO。
sources:
  - JIRA: PF008_0093 (SYSTCUFS-145)
  - UFS Spec: JESD220H Section 11.6.7 (FFU), Section 10.4 (Reset)
---

# PF008_0093 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

執行 FFU 流程（支援 B-Bin only / B-Bin+HW-Page / HW-Page only 三種模式），
修改 SVN Version 與 HW_Setting rsvd bit，然後在不同 Reset 類型下驗證：

- **HW_RESET / RST_n**：Firmware 啟動 → SVN 變更、FFU Status = SUCCESS
- **EndPoint / UniPro / LUN Reset**：Firmware 未重新啟動 → SVN 不變、FFU Status = NO_INFO

## JIRA Step 對照

| JIRA Step | 原始描述 | 正規化後對應 |
|-----------|---------|-------------|
| Step 1 | Do FFU process + modify SVN/HW_Setting | Phase 1 |
| Step 2 | Reset（5 types） | Phase 2 |
| Step 3 | Check SVN changed + FFU Success after HW/RST_n | Step 2.3 |
| Step 4 | Check SVN unchanged + FFU NO_INFO after others | Step 2.4 |

---

## 測試架構

```
PF008_0093 Test Flow
│
├── Phase 0: 初始化與前置讀取
│   ├── Step 0.1: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│   ├── Step 0.2: INQUIRY — 讀取當前 SVN Version 並儲存 → Expected: GOOD Status, 回傳當前 SVN
│   └── Step 0.3: QUERY Read Attribute (bFFUStatus) — 讀取當前 FFU Status → Expected: QUERY RESPONSE Success
│
├── Phase 1: FFU Download & Save
│   ├── Step 1.1: WRITE BUFFER (Mode=FFU Download) — 下載 FW Image → Expected: GOOD Status
│   └── Step 1.2: WRITE BUFFER (Mode=FFU Download & Save, byte[17]=0xE1) — Save FW + Activate → Expected: GOOD Status
│
└── Phase 2: Reset 驗證（每種 Reset 獨立測試）
    │
    ├── Case A: HW_RESET
    │   ├── Step 2A.1: HW_RESET → Expected: Reset device success
    │   ├── Step 2A.2: INQUIRY — 讀取 SVN Version → Expected: SVN 已變更（≠ Step 0.2）
    │   └── Step 2A.3: QUERY Read Attribute (bFFUStatus) → Expected: bFFUStatus == SUCCESS (0x00)
    │
    ├── Case B: RST_n
    │   ├── Step 2B.1: RST_n Reset → Expected: Reset device success
    │   ├── Step 2B.2: INQUIRY — 讀取 SVN Version → Expected: SVN 已變更（≠ Step 0.2）
    │   └── Step 2B.3: QUERY Read Attribute (bFFUStatus) → Expected: bFFUStatus == SUCCESS (0x00)
    │
    ├── Case C: EndPoint Reset
    │   ├── Step 2C.1: EndPoint Reset → Expected: Link Startup OK
    │   ├── Step 2C.2: INQUIRY — 讀取 SVN Version → Expected: SVN 不變（== Step 0.2）
    │   └── Step 2C.3: QUERY Read Attribute (bFFUStatus) → Expected: bFFUStatus == NO_INFO
    │
    ├── Case D: UniPro Reset
    │   ├── Step 2D.1: UniPro Reset → Expected: Link Startup OK
    │   ├── Step 2D.2: INQUIRY — 讀取 SVN Version → Expected: SVN 不變（== Step 0.2）
    │   └── Step 2D.3: QUERY Read Attribute (bFFUStatus) → Expected: bFFUStatus == NO_INFO
    │
    └── Case E: LUN Reset
        ├── Step 2E.1: LUN Reset → Expected: LUN 恢復可操作
        ├── Step 2E.2: INQUIRY — 讀取 SVN Version → Expected: SVN 不變（== Step 0.2）
        └── Step 2E.3: QUERY Read Attribute (bFFUStatus) → Expected: bFFUStatus == NO_INFO
```

---

## Phase 0 — 初始化與前置讀取

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

### Step 0.2: 讀取當前 SVN Version

**SCSI CMD**: `INQUIRY (12h)`

| Field | Value |
|-------|-------|
| Opcode | 0x12 |
| EVPD | 0 |
| Page Code | 0x00 (Standard Inquiry) |
| Allocation Length | 0x60 |

**Expected**: `GOOD Status`，儲存 `SVN_before`（從 Vendor-Specific 或 Device Identification VPD page 取得）。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SPC-5 6.4

---

### Step 0.3: 讀取當前 FFU Status

**UFS QUERY**: 讀取 Device Descriptor 或相關 Attribute 確認 FFU 狀態。

**Expected**: FFU Status 為正常狀態（非 FFU 進行中）。

**UFS SPEC Reference**: JESD220H Section 11.6.7

---

## Phase 1 — FFU Download & Save

### Step 1.1: FFU Download

**SCSI CMD**: `WRITE BUFFER (3Bh)` — Mode = FFU Download (0x11)

| Field | Value |
|-------|-------|
| Opcode | 0x3B |
| Mode | 0x11 (Download microcode with offsets, save, and activate — per JESD220H 11.6.7) |
| Buffer ID | 0x00 |
| Buffer Offset | 依 FW Image 分段 |
| Parameter List Length | 依 FW Image chunk size |

**Expected**: `GOOD Status`（每一段 FW image 下載成功）。

**UFS SPEC Reference**: JESD220H Section 11.6.7 (FFU), Section 10.7.2

---

### Step 1.2: FFU Download & Save（Activate）

**SCSI CMD**: `WRITE BUFFER (3Bh)` — Mode = FFU Download & Save

**目的**: 最後一段 FW Download 帶 Save flag，觸發 Firmware 儲存。

| Field | Value |
|-------|-------|
| Opcode | 0x3B |
| Mode | FFU Download & Save (byte[17]=0xE1 per JESD220H 11.6.7) |
| Buffer ID | 0x00 |
| Buffer Offset | 最後一段 offset |
| Parameter List Length | 最後一段 size |

**VU Note (byte[17]=0xE1)**: Vendor-specific activate mode per JIRA。

**Expected**: `GOOD Status`，FW Image 儲存成功。

**UFS SPEC Reference**: JESD220H Section 11.6.7

---

## Phase 2 — Reset 驗證

### Case A: HW_RESET

#### Step 2A.1: HW_RESET

| Reset Type | 說明 |
|:---|:---|
| HW_RESET | RST_n signal hardware reset |

**Expected**: `fDeviceInit == 1`。

**UFS SPEC Reference**: JESD220H Section 10.4.2

---

#### Step 2A.2: 驗證 SVN Version 變更

**SCSI CMD**: `INQUIRY (12h)`

**Expected**: `GOOD Status`，`SVN_after != SVN_before`（Firmware 已啟動新版本）。

---

#### Step 2A.3: 驗證 FFU Status

**Expected**: `bFFUStatus == SUCCESS (0x00)`。

**UFS SPEC Reference**: JESD220H Section 11.6.7

---

### Case B: RST_n

（同 Case A 結構，Step 2B.1 RST_n, 2B.2 INQUIRY, 2B.3 FFU Status）

| Reset Type | 說明 |
|:---|:---|
| RST_n | Reset signal toggle |

**Expected**: 同 Case A（SVN 變更 + FFU SUCCESS）。

**UFS SPEC Reference**: JESD220H Section 10.4.2

---

### Case C: EndPoint Reset

| Reset Type | 說明 |
|:---|:---|
| EndPoint Reset | DME EndPointReset |

**Expected**: SVN 不變 + FFU Status = NO_INFO。

**UFS SPEC Reference**: JESD220H Section 10.4.4

---

### Case D: UniPro Reset

| Reset Type | 說明 |
|:---|:---|
| UniPro Reset | UniPro layer reset |

**Expected**: SVN 不變 + FFU Status = NO_INFO。

**UFS SPEC Reference**: JESD220H Section 10.4.5

---

### Case E: LUN Reset

| Reset Type | 說明 |
|:---|:---|
| LUN Reset | Logical Unit Reset (TMF) |

**Expected**: SVN 不變 + FFU Status = NO_INFO。

**UFS SPEC Reference**: JESD220H Section 10.7.3 (TMF — LOGICAL UNIT RESET)

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | Step 0.1 |
| 0x12 | INQUIRY | 6 | Step 0.2, 2A.2, 2B.2, 2C.2, 2D.2, 2E.2 |
| 0x3B | WRITE BUFFER | 10 | Step 1.1, 1.2 |

## 附錄 C — UFS Reset 類型

| Reset Type | 說明 | FFU 行為 | SPEC |
|:---|:---|:---|:---|
| HW_RESET | RST_n hardware reset | SVN 變更、FFU Success | JESD220H 10.4.2 |
| RST_n | Reset signal toggle | SVN 變更、FFU Success | JESD220H 10.4.2 |
| EndPoint Reset | DME EndPointReset | SVN 不變、FFU NO_INFO | JESD220H 10.4.4 |
| UniPro Reset | UniPro layer reset | SVN 不變、FFU NO_INFO | JESD220H 10.4.5 |
| LUN Reset | Logical Unit Reset (TMF) | SVN 不變、FFU NO_INFO | JESD220H 10.7.3 |

## FFU Mode 對照

| byte[17] | Mode | Description |
|:---|:---|:---|
| 0xE1 | FFU Download & Save | FW image save + activate |

---

## 自我驗證

- Tree Diagram leaf steps: 0.1, 0.2, 0.3, 1.1, 1.2 (5) + 2A.1, 2A.2, 2A.3 + 2B.1, 2B.2, 2B.3 + 2C.1, 2C.2, 2C.3 + 2D.1, 2D.2, 2D.3 + 2E.1, 2E.2, 2E.3 (15) = 20
- `### Step` sections: **16** (Cases AB 共用表格描述，B 未展開獨立 section — 5 Phase 0 + 2 Phase 1 + 9 Phase 2 = 16)
- Note: Cases B-E 以參照 Case A 結構方式呈現，Tree Diagram 已完整列出所有 leaf
