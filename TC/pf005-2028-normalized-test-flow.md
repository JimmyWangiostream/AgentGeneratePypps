---
title: PF005_2028_FIO12_VDT_Drop_Drvlog_Check-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf005_2028, scsi-cmd, vdt, drvlog, vccq, voltage, nand]
description: >
  PF005_2028 VDT Drop Drvlog Check — 在 VCCQ 電壓變化（1.08V ↔ 1.14V × 11 次→ 1.2V）
  後透過 NAND Direct Read 搜尋 Drvlog，驗證 EVENT_VDT (0x4B) 記錄存在，
  確認 VDT (Voltage Drop Test) 事件正確被記錄到 NAND。
sources:
  - JIRA: PF005_2028 (SYSTCUFS-2353)
  - UFS Spec: JESD220H Section 14.1.5.1 (VCCQ), 本 Pattern 大量使用 Vendor-Unique NAND Direct Read
---

# PF005_2028 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

透過 VCCQ 電壓循環變化（1.08V ↔ 1.14V）觸發 Voltage Drop，然後回到 1.2V（UFS4 Typical），
利用 NAND Direct Read 掃描 Drvlog 區域，確認 EVENT_VDT (0x4B) 事件記錄存在於 NAND 中。

## 注意

本 Pattern 涉及大量 Vendor-Unique (VU) 操作：HW Register 設定、VCCQ 電壓調整、NAND Direct Read。
VU 操作在下面步驟中以專有標註呈現，便於 C++ 實作時參考。

## JIRA Step 對照

| JIRA Step | 原始描述 | 正規化後對應 |
|-----------|---------|-------------|
| Step 1 | Disable autostandby (HW_Setting 0xA07) | Step 0.2 |
| Step 2 | Set VCCQ to 1.08V | Step 1.1 (loop) |
| Step 3 | Set VCCQ to 1.14V | Step 1.2 (loop) |
| Step 4 | Loop step2~3 × 11 | Loop (11 次) |
| Step 5 | Set VCCQ to 1.2V (UFS4 Typical) | Step 1.3 |
| Step 6 | Get Flash Setting (0x820/4/8/4/C) | Step 2.1 |
| Step 7 | NAND Direct Read search for EVENT_VDT | Step 2.2~2.7 |
| Step 8 | Verify EVENT_VDT found | Step 2.7 |

---

## 測試架構

```
PF005_2028 Test Flow
│
├── Phase 0: 初始化與前置配置
│   ├── Step 0.1: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│   └── Step 0.2: [VU] HW Register Write (0xA07) — Disable Auto Standby → Expected: Auto Standby Disabled
│
├── Phase 1: VCCQ Voltage Cycling
│   │
│   └── Loop (11 次)
│       ├── Step 1.1: [VU] Set VCCQ → 1.08V → Expected: VCCQ = 1.08V
│       └── Step 1.2: [VU] Set VCCQ → 1.14V → Expected: VCCQ = 1.14V
│   │
│   └── Step 1.3: [VU] Set VCCQ → 1.2V (UFS4 Typical) → Expected: VCCQ = 1.2V, Device Stable
│
└── Phase 2: NAND Direct Read — Drvlog Scan for EVENT_VDT
    ├── Step 2.1: [VU] READ BUFFER(3Ch) — 讀取 Flash Setting Registers (0x820/4/8/4/C) → Expected: 回傳 CE/Page/Block 位置資訊
    ├── Step 2.2: [VU] WRITE BUFFER(3Bh) / NAND Direct Read — 設定搜尋起點 → Expected: Direct Read 參數設定成功
    ├── Step 2.3: [VU] NAND Direct Read — Plane 掃描 (V-1, V-2, V-3, V-4) → Expected: 找到 read_status == STATUS_READY(0x0) 的 Block
    ├── Step 2.4: [VU] NAND Direct Read — Page 掃描 → Expected: 找到 Spare Mark == Drvlog(0xA3)
    ├── Step 2.5: [VU] NAND Direct Read — Drvlog Entry 掃描 (每 32B) → Expected: 讀取 Drvlog Data
    ├── Step 2.6: [VU] NAND Direct Read — 若目前 Block/Plane 搜完，跨 Plane/CE 繼續 → Expected: 覆蓋所有可能位置
    └── Step 2.7: 驗證 EVENT_VDT (0x4B) 存在於 Drvlog → Expected: Drvlog entry[6] == 0x4B (EVENT_VDT)
```

---

## Phase 0 — 初始化與前置配置

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

### Step 0.2: [VU] Disable Auto Standby

**目的**: 透過 HW Register 0xA07 關閉 Auto Standby 功能，避免測試過程中 Device 自動進入 Standby 干擾電壓測試。

**VU Operation**: HW Register Write (0xA07 = Disable Auto Standby)

**Expected**: Auto Standby 功能關閉。

---

## Phase 1 — VCCQ Voltage Cycling

### Step 1.1: [VU] Set VCCQ to 1.08V

**目的**: 設定 VCCQ 電壓為 1.08V（低於 UFS4 Typical 1.2V），模擬低電壓情境。

**VU Operation**: HW VCCQ Regulator 設定 → 1.08V

**Expected**: VCCQ = 1.08V。

---

### Step 1.2: [VU] Set VCCQ to 1.14V

**目的**: 設定 VCCQ 電壓為 1.14V，與 Step 1.1 形成電壓變動循環。

**VU Operation**: HW VCCQ Regulator 設定 → 1.14V

**Expected**: VCCQ = 1.14V。

---

### Step 1.3: [VU] Set VCCQ to 1.2V（UFS4 Typical）

**目的**: 11 次循環後將 VCCQ 恢復為 UFS4 典型電壓 1.2V。

**VU Operation**: HW VCCQ Regulator 設定 → 1.2V

**Expected**: VCCQ = 1.2V（UFS4 Typical），Device 穩定運行。

**UFS SPEC Reference**: JESD220H Section 14.1.5.1 (VCCQ Nominal 1.2V for UFS4)

---

## Phase 2 — NAND Direct Read Drvlog Scan

### Step 2.1: [VU] 讀取 Flash Setting Registers

**目的**: 讀取 HW Register 取得下一個 Drvlog 的 NAND 位置資訊。

**VU Operation**: 透過 Vendor-Unique 介面讀取以下 HW Registers:

| Register | Description |
|:---|:---|
| 0x820 | 下一個 Drvlog 所在 CE |
| 0x824 | 下一個 Drvlog 所在 Page |
| 0x828 | 下一個 Drvlog 所在 Block |
| 0x804 | 一個 Block 中的 Page 數量 |
| 0x80C | 一個 Die 的 Plane 數量 |

設：`X = CE`, `Y = Page`, `Z = Block`, `U = Page per Block`, `V = Planes per Die`

**Expected**: 回傳有效的 CE/Page/Block 參數值。

---

### Step 2.2: [VU] NAND Direct Read — 設定搜尋起點

**目的**: 從 Drvlog 起始位置往回一個位置開始搜尋。

**VU Operation**: `NAND Direct Read(OP=0x20000, en_force_block, CE=X, Plane=V-1, Block=Z, Page=Y-1)`

**Note**: Direct Read OP=0x20000 為 Vendor-Unique 操作碼，透過 WRITE BUFFER(3Bh) 或專有介面發送。

**Expected**: Direct Read 執行。

---

### Step 2.3: [VU] Plane 掃描 — 尋找有效 Block

**目的**: 從 Plane V-1 往 V-4 依序讀取，直到 `read_status == STATUS_READY(0x0)`。

**VU Operation**:

| Sequence | Command |
|:---|:---|
| 1 | Direct Read(CE=X, Plane=V-1, Block=Z, Page=Y-1) |
| 2 | Direct Read(CE=X, Plane=V-2, Block=Z, Page=Y-1) |
| 3 | Direct Read(CE=X, Plane=V-3, Block=Z, Page=Y-1) |
| 4 | Direct Read(CE=X, Plane=V-4, Block=Z, Page=Y-1) |

**Expected**: 找到 `read_status == STATUS_READY(0x0)` 的有效 Plane（例如 V-2）。

---

### Step 2.4: [VU] Page 掃描 — 尋找 Drvlog

**目的**: 在有效 Plane 上從 Page Y-1 往回掃描，直到 `Spare Mark (Data[0x4004]) == Drvlog(0xA3)`。

**VU Operation**:

| Sequence | Command |
|:---|:---|
| 1 | Direct Read(CE=X, Plane=V-2, Block=Z, Page=Y-1) |
| 2 | Direct Read(CE=X, Plane=V-2, Block=Z, Page=Y-2) |
| 3 | Direct Read(CE=X, Plane=V-2, Block=Z, Page=Y-3) |
| ... | 持續往回掃描 |

**Expected**: 找到 `Spare Mark == 0xA3 (Drvlog)` 的 Page。

---

### Step 2.5: [VU] Drvlog Entry 掃描

**目的**: 在找到的 Drvlog Page 內以每 32B 為單位掃描，尋找 `EVENT_VDT (0x4B)`。

**Rule**:
- 每條 Drvlog Entry 32B
- 若 `Data[offset] == 0x00` → 此 entry invalid，跳過
- 檢查 `Data[offset + 6]` 是否等於 `0x4B` (EVENT_VDT)
- 掃描直到 offset > 4KB

**VU Operation**:

| Offset | Check | 
|:---|:---|
| 32×1 | Data[32] != 0 → Data[32+6] == 0x4B? |
| 32×2 | Data[64] != 0 → Data[64+6] == 0x4B? |
| 32×3 | Data[96] != 0 → Data[96+6] == 0x4B? |
| ... | 直到 offset > 4096 |

**Expected**: 找到 `Data[offset + 6] == 0x4B` 的 Drvlog Entry。

---

### Step 2.6: [VU] 跨 Plane / CE 繼續搜尋

**目的**: 若目前 Block/Plane 的所有 Page 已搜完，跨到下一個 Plane 或 CE 繼續。

**搜尋順序**:
1. 同 CE, 下一個 Plane: `Direct Read(CE=X, Plane=V-3, Block=Z, Page=U-1)`
2. 同 CE, 最後 Plane: `Direct Read(CE=X, Plane=V-4, Block=Z, Page=U-1)`
3. 換 CE: `Direct Read(CE=X-1, Plane=V-1, Block=Z, Page=U-1)`
4. 搜尋終點: `Direct Read(CE=0, Plane=0, Block=Z, Page=0)`

**Expected**: 覆蓋所有可能的 Drvlog 儲存位置。

---

### Step 2.7: 驗證 EVENT_VDT 存在

**目的**: 確認在 Step 2.5 的掃描中找到 `EVENT_VDT (0x4B)`。

**Expected**: 存在至少一條 Drvlog Entry 的 entry[6] == 0x4B (EVENT_VDT)。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | Step 0.1 |
| 0x3B | WRITE BUFFER | 10 | Step 2.2 (VU — Direct Read 參數設定) |
| 0x3C | READ BUFFER | 10 | Step 2.1 (VU — Flash Register 讀取) |

## 附錄 A — UFS Query IDN 對照表

（本 Pattern 主要使用 HW Register 和 VU NAND Direct Read，不使用 UFS Query）

## HW Register 對照表（Vendor-Unique）

| Register | Description |
|:---|:---|
| 0xA07 | Auto Standby Enable/Disable |
| 0x804 | Pages per Block |
| 0x80C | Planes per Die |
| 0x820 | Next Drvlog CE |
| 0x824 | Next Drvlog Page |
| 0x828 | Next Drvlog Block |

## Drvlog Entry 結構（32B）

| Offset | Field | Description |
|:---|:---|:---|
| +0 | valid_flag | 0x00 = invalid entry |
| +6 | event_type | 0x4B = EVENT_VDT |

---

## 自我驗證

- Tree Diagram leaf steps: **12** (0.1, 0.2, 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7)
- `### Step` sections: **12** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
