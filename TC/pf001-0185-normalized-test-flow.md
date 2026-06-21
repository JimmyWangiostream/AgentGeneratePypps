---
title: PF001_0185_BKOP_POR-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf001_0185, scsi-cmd, bkop, por]
description: >
  PF001_0185 BKOP POR Test — 全卡寫入過程中隨機插入 POR 與延遲，
  觸發 BKOPS，驗證每次 Write 後 Read Compare 資料完整性。
sources:
  - JIRA: PF001_0185 (SYSTCUFS-13)
  - UFS Spec: JESD220H Section 10.7.2 (QUERY), Section 13.4.6 (BKOPS), Section 13.4.11 (PURGE)
---

# PF001_0185 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

在 BKOPS 觸發條件下（Idle 100ms + Dynamic SLC 寫過 + Free blk < threshold），
進行 burn-in loop 反覆執行：全卡抹除 → 逐步 Random Write → Delay → POR → Read Compare。
每寫滿整張卡後做一次 Final Read Compare All，確認資料完整性不受 BKOPS 與 POR 干擾。

## BKOPS 觸發條件（JIRA 定義）

| 條件 | 說明 |
|------|------|
| Idle > 100ms | FW 寫死，Idle 時間超過 100ms 觸發 |
| Dynamic SLC 寫過 | 每 CE 配置 1GB（如 4CE → 4GB） |
| Free blk < threshold | Good blk - static SLC blk(system區, 存 table) - 預留 10 blk |

## JIRA Step 對照

| JIRA Step | 原始描述 | 正規化後對應 |
|-----------|---------|-------------|
| Step 1 | Erase all | Phase 0: UNMAP Purge |
| Step 2 | Random write 1M~512M | Step L.1: WRITE(10) |
| Step 3 | Random delay 1s~5s | Step L.2: Idle Delay |
| Step 4 | Random POR | Step L.3: POR Reset |
| Step 5 | Read & Cmp | Step L.4: READ(10) + Compare |
| Step 6 | Loop until cumulative == card size | Loop control |
| Step 7 | Read & Cmp all | Phase F: READ ALL |
| Step 22-24 | BKOP 觸發條件 | 前置條件 |

---

## 測試架構

```
PF001_0185 Test Flow
│
├── Phase 0: 裝置初始化與前置準備
│   ├── Step 0.1: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│   ├── Step 0.2: READ CAPACITY(10) — 取得 LUN 容量 → Expected: GOOD Status, 回傳有效 LBA 範圍
│   └── Step 0.3: UNMAP + SET FLAG(fPurgeEnable) — Erase All Card → Expected: bPurgeStatus == 0x00
│
└── Loop (burn_in_iterations 次)
    │
    ├── Phase 1: 全卡填充 Write + Delay + POR + Compare
    │   │
    │   └── Loop (until cumulative_data_size >= card_size)
    │       ├── Step 1.1: WRITE(10) — Random 1M~512M Write → Expected: GOOD Status
    │       ├── Step 1.2: Idle — Random Delay 1s~5s → Expected: 觸發 BKOPS 條件
    │       ├── Step 1.3: POR Reset — 隨機選取 Reset 類型 → Expected: Device 恢復就緒
    │       └── Step 1.4: READ(10) + Compare — 比對 Step 1.1 寫入的資料 → Expected: GOOD Status, Data Match
    │
    └── Phase 2: Final Read Compare All
        ├── Step 2.1: READ(10) — 全卡範圍讀取 → Expected: GOOD Status
        └── Step 2.2: Data Compare — 比對全卡寫入記錄 → Expected: 全卡 Data Match
```

---

## Phase 0 — 裝置初始化與前置準備

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

**目的**: 確認 UFS Device 已上電且可以接受命令。

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2 (SCSI Command Set), SPC-5 6.47

---

### Step 0.2: 取得 LUN 容量

**SCSI CMD**: `READ CAPACITY(10) (25h)`

**目的**: 獲取 Logical Unit 的最大 LBA 與 Block Size，用於計算全卡寫入範圍。

| Field | Value |
|-------|-------|
| Opcode | 0x25 |
| LUN | All LUNs |
| Logical Block Address | 0x00000000 |

**Expected**: `GOOD Status`，回傳 `RETURNED LOGICAL BLOCK ADDRESS` 與 `BLOCK LENGTH IN BYTES`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.16

---

### Step 0.3: Erase All Card

**SCSI CMD**: `UNMAP (42h)` + **UFS QUERY**: `SET FLAG (fPurgeEnable, IDN 0x06)`

**目的**: 抹除全卡所有 LUN 的資料，確保測試從乾淨狀態開始。

| Field | Value |
|-------|-------|
| UNMAP Opcode | 0x42 |
| UNMAP LUN | All LUNs |
| UNMAP LBA Range | 0 ~ MAX_LBA |
| SET FLAG Opcode | 0x02 |
| SET FLAG IDN | 0x06 (fPurgeEnable) |
| SET FLAG Value | 0x01 (Set) |

**Expected**: Purge 完成，`bPurgeStatus == 0x00`（JESD220H Section 14.3.1, IDN 0x07）。

**UFS SPEC Reference**: JESD220H Section 13.4.11 (PURGE), Section 10.7.8 (SET FLAG), Section 14.2 (Flags)

---

## Loop — Burn-in Iterations

### Phase 1 — 全卡填充 Write + Delay + POR + Compare

#### Step 1.1: Random Write

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: 對隨機 LUN / LBA 寫入隨機大小的測試資料。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | Random (All LUNs) |
| Logical Block Address | Random (0 ~ MAX_LBA) |
| Transfer Length | Random (1MB ~ 512MB, i.e. 2048 ~ 1048576 blocks @ 512B) |
| Data | Random Pattern |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.43

---

#### Step 1.2: Random Delay

**目的**: Idle 1~5 秒期間滿足 BKOPS 觸發條件（Idle > 100ms），讓 FW 在背景執行 BKOPS。

| Field | Value |
|-------|-------|
| Duration | Random (1s ~ 5s) |

**Expected**: Delay 期間 BKOPS 條件成立（Idle > 100ms），FW 可觸發背景操作。

**UFS SPEC Reference**: JESD220H Section 13.4.6 (Background Operations)

---

#### Step 1.3: POR Reset

**目的**: 隨機選取一種 Reset 類型對 Device 執行 Power-On Reset，驗證 BKOPS 進行中或完成後資料完整性。

| Reset Type | 說明 |
|:---|:---|
| HW_RESET | 硬體 RST_n signal reset |
| RST_n | Reset 訊號 toggle |
| EndPoint Reset | DME EndPointReset 指令 |
| UniPro Reset | UniPro 層級 reset |

**Expected**: Device 完成 Link Startup，回復至 `fDeviceInit == 1` 的可操作狀態。

**UFS SPEC Reference**: JESD220H Section 10.4 (UFS Reset), Section 10.7.9 (QUERY Flag)

---

#### Step 1.4: Read Compare

**SCSI CMD**: `READ(10) (28h)`

**目的**: 讀回 Step 1.1 寫入的 LBA 範圍，比對資料正確性。

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | Step 1.1 使用的 LUN |
| Logical Block Address | Step 1.1 寫入的 LBA |
| Transfer Length | Step 1.1 寫入的大小 |

**Expected**: `GOOD Status` + `Data Match`（比對通過）。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.18

---

### Phase 2 — Final Read Compare All

#### Step 2.1: Read All Card

**SCSI CMD**: `READ(10) (28h)`

**目的**: 全卡寫滿後，讀取所有已寫入的 LBA 範圍進行總比對。

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | All LUNs |
| Logical Block Address | 0x00000000 |
| Transfer Length | MAX_LBA + 1 (全卡) |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.18

---

#### Step 2.2: Data Compare All

**目的**: 讀取資料後與全域寫入記錄進行 Compare，確認無任何資料偏差。

**Expected**: `Data Match`（全卡寫入記錄與讀取資料一致）。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | Step 0.1 |
| 0x25 | READ CAPACITY(10) | 10 | Step 0.2 |
| 0x28 | READ(10) | 10 | Step 1.4, 2.1 |
| 0x2A | WRITE(10) | 10 | Step 1.1 |
| 0x42 | UNMAP | 10 | Step 0.3 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 存取 | 使用位置 |
|:---|:---|:---|:---|:---|
| 0x06 | fPurgeEnable | 0x02 (SET FLAG) | R/W | Step 0.3 |
| 0x07 | bPurgeStatus | 0x03 (READ ATTRIBUTE) | R | Step 0.3 (驗證) |
| 0x01 | fDeviceInit | 0x01 (READ FLAG) | R | Step 1.3 (驗證 Reset 後) |

## 附錄 C — UFS Reset 類型說明

| Reset Type | 說明 | SPEC Reference |
|:---|:---|:---|
| HW_RESET | RST_n signal hardware reset | JESD220H Section 10.4.2 |
| RST_n | Reset signal toggle | JESD220H Section 10.4.2 |
| EndPoint Reset | DME EndPointReset command | JESD220H Section 10.4.4 |
| UniPro Reset | UniPro layer reset | JESD220H Section 10.4.5 |

---

## 自我驗證

- Tree Diagram leaf steps: **9** (0.1, 0.2, 0.3, 1.1, 1.2, 1.3, 1.4, 2.1, 2.2)
- `### Step` sections: **9** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
