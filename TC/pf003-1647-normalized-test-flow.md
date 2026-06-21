---
title: PF003_1647_NonFUA_SyncCache_L1_PPP-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf003_1647, scsi-cmd, non-fua, sync-cache, write-booster, l1-ppp, flush]
description: >
  PF003_1647 Non-FUA Sync Cache L1 PPP Test — 混合 WriteBooster MIX mode (SLC L2)
  與 Non-FUA TLC Write (L1/L2 split) 的多種 Flush 條件下驗證資料完整性。
  涵蓋 Sync Cache、Sleep/Awake、Power Down、Reset、Auto Standby 五種 Flush 路徑。
sources:
  - JIRA: PF003_1647 (SYSTCUFS-1926)
  - UFS Spec: JESD220H Section 13.4.18 (WriteBooster), Section 10.2.5 (Power Conditions), Section 13.4.11 (PURGE)
---

# PF003_1647 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

在 WriteBooster MIX mode（SLC L2 Buffer）配置下，先以 FUA=1 填滿 WB Buffer，
再以 Non-FUA（FUA=0）進行 TLC L1/L2 split write（以 TLC L2 threshold 區分 chunk size），
透過五種 Flush 條件確保資料從快取落 NAND 後正確性不受影響。
測試在 burn-in loop 內反覆執行。

## IC/NAND 相容性檢查

| 條件 | 值 |
|------|-----|
| IC | 8329 |
| NAND | BICS8 |
| 不支援時 | Pattern 判定為 `NOT SUPPORTED`，終止測試 |
| 備註 | PS8363 KIC 不支援 MIX mode，跳過 WB fill flow |

## JIRA Step 對照

| JIRA Step | 原始描述 | 正規化後對應 |
|-----------|---------|-------------|
| Step 1 | IC/NAND check | Step 0.1 |
| Step 2 | Config WB Max Buffer | Step 0.3 |
| Step 3 | Erase all + purge | Step 0.4 |
| Step 4 | Enable WB | Step 1.1 |
| Step 5 | Seq write WB buffer FUA=1 | Phase 1 (Steps 1.2) |
| Step 6 | Disable WB | Step 1.3 |
| Step 7 | Random write big chunk FUA=0 | Step L.1 |
| Step 8 | Random write small chunk FUA=0 | Step L.2 |
| Step 9 | Random flush | Step L.3 |
| Step 10 | Read compare | Step L.4 |
| Step 11 | Random power/reset case | Step L.5 |
| Step 12 | Read compare | Step L.6 |
| Step 13 | Random write (20-33 cmds) | Step L.7 |
| Step 14 | Random flush | Step L.8 |
| Step 15 | Read compare | Step L.9 |
| Step 16 | Loop to step 7 | Loop control |
| Step 17 | Read compare all card | Phase F |

---

## 測試架構

```
PF003_1647 Test Flow
│
├── Phase 0: 初始化與 WriteBooster 配置
│   ├── Step 0.1: HW Check — 確認 IC/NAND 相容性 → Expected: IC=8329, NAND=BICS8, 否則 NOT SUPPORTED
│   ├── Step 0.2: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│   ├── Step 0.3: QUERY Write Descriptor (Configuration Descriptor) — Config WB Buffer MAX → Expected: QUERY RESPONSE Success
│   ├── Step 0.4: UNMAP + SET FLAG(fPurgeEnable) — Erase All Card → Expected: bPurgeStatus == 0x00
│   └── Step 0.5: READ CAPACITY(10) — 取得 LUN 容量 → Expected: GOOD Status, 回傳有效 LBA 範圍
│
├── Phase 1: WB Enable + Fill Buffer (MIX mode SLC L2)
│   ├── Step 1.1: QUERY Set Flag (fWriteBoosterEn) — 啟用 WB → Expected: QUERY RESPONSE Success
│   ├── Step 1.2: WRITE(10) — Seq Write WB Buffer LUN0, FUA=1, chunk=1G → Expected: GOOD Status
│   └── Step 1.3: QUERY Clear Flag (fWriteBoosterEn) — 停用 WB → Expected: QUERY RESPONSE Success
│
└── Loop (until burnin_time)
    │
    ├── Phase 2: TLC L2 Big Chunk + L1 Small Chunk Write (Non-FUA)
    │   ├── Step 2.1: WRITE(10) — Random Big Chunk to L2, FUA=0 → Expected: GOOD Status
    │   └── Step 2.2: WRITE(10) — Random Small Chunk to L1, FUA=0 → Expected: GOOD Status
    │
    ├── Phase 3: Random Flush + Read Compare
    │   ├── Step 3.1: Random Flush — 隨機選取 Flush 類型 → Expected: Flush 完成, 資料落 NAND
    │   ├── Step 3.2: READ(10) + Compare — 比對 Step 2.1/2.2 資料 → Expected: GOOD Status, Data Match
    │   ├── Step 3.3: Random Power/Reset Case — 隨機選取 Power Transition → Expected: Reset device success
    │   └── Step 3.4: READ(10) + Compare — 比對 Step 2.1/2.2 資料 → Expected: GOOD Status, Data Match
    │
    ├── Phase 4: Random Multi-CMD Write + Flush + Compare
    │   ├── Step 4.1: WRITE(10) × N — Random N=20~33, chunk random, FUA=0 → Expected: GOOD Status (all)
    │   ├── Step 4.2: Random Flush — 隨機選取 Flush 類型 → Expected: Flush 完成
    │   └── Step 4.3: READ(10) + Compare — 比對 Step 4.1 資料 → Expected: GOOD Status, Data Match
    │
    └── Phase F: Final Read Compare All
        └── Step F.1: READ(10) — 全卡 Read Compare → Expected: GOOD Status, Data Match All
```

---

## Phase 0 — 初始化與 WriteBooster 配置

### Step 0.1: 裝置相容性檢查

**目的**: 確認 IC / NAND 組合為支援的配置。

| Check | Expected Value |
|-------|---------------|
| IC | 8329 |
| NAND | BICS8 |

**若不支援**: Pattern 判定為 `NOT SUPPORTED`，終止測試。

**備註**: PS8363 KIC 不支援 MIX mode，跳過 WB fill flow。

---

### Step 0.2: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

### Step 0.3: 配置 WriteBooster Buffer（Configuration Descriptor）

**UFS QUERY**: `WRITE DESCRIPTOR (Configuration Descriptor)`

**目的**: 透過 Configuration Descriptor 設定 WriteBooster 為 Shared Type + MAX buffer size。
`dLUNumWriteBoosterBufferAllocUnits` (IDN 0x17) 為唯讀 Attribute，不可用 WRITE ATTRIBUTE 寫入。

| Field | Value |
|-------|-------|
| Query Opcode | 0x08 (WRITE DESCRIPTOR) |
| IDN | 0x01 (Configuration Descriptor) |
| Index | 0x00 |
| Selector | 0x00 |
| bWriteBoosterBufferType | 0x01 (Shared Buffer Type) |
| dLUNumWriteBoosterBufferAllocUnits | MAX (取自 Device Descriptor) |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.1.4.5 (Configuration Descriptor), Section 14.3.1 (dLUNumWriteBoosterBufferAllocUnits 為 R/O)

---

### Step 0.4: Erase All Card

**SCSI CMD**: `UNMAP (42h)` + **UFS QUERY**: `SET FLAG (fPurgeEnable, IDN 0x06)`

| Field | Value |
|-------|-------|
| UNMAP Opcode | 0x42 |
| UNMAP LUN | All LUNs |
| UNMAP LBA Range | 0 ~ MAX_LBA |
| SET FLAG Opcode | 0x02 |
| SET FLAG IDN | 0x06 (fPurgeEnable) |
| SET FLAG Value | 0x01 (Set) |

**Expected**: Purge 完成，`bPurgeStatus == 0x00`。

**UFS SPEC Reference**: JESD220H Section 13.4.11 (PURGE)

---

### Step 0.5: 取得 LUN 容量

**SCSI CMD**: `READ CAPACITY(10) (25h)`

| Field | Value |
|-------|-------|
| Opcode | 0x25 |
| LUN | All LUNs |

**Expected**: `GOOD Status`，取得 `TOTAL_LBA` 與 Block Size。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

## Phase 1 — WB Enable + Fill Buffer

### Step 1.1: 啟用 WriteBooster

**UFS QUERY**: `SET FLAG (fWriteBoosterEn)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| IDN | 0x0E (fWriteBoosterEn) |
| Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.2 (Flags), Section 13.4.18 (WriteBooster)

---

### Step 1.2: Sequential Write Fill WB Buffer（FUA=1）

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: 以 FUA=1 對 LUN0 從 LBA=0 開始循序寫入，填滿 WB Buffer（MIX mode = SLC L2）。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 (LUN0) |
| Logical Block Address | 0x00000000 |
| Transfer Length | per chunk = 1GB (2097152 blocks @ 512B) |
| FUA bit | 1 (Force Unit Access) |
| Total Length | dLUNumWriteBoosterBufferAllocUnits (WB Buffer Total) |

**Expected**: `GOOD Status`（全部 chunks 寫入成功）。

**UFS SPEC Reference**: JESD220H Section 13.4.18 (WriteBooster), SBC-4 5.43 (FUA)

---

### Step 1.3: 停用 WriteBooster

**UFS QUERY**: `CLEAR FLAG (fWriteBoosterEn)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x05 (CLEAR FLAG) |
| IDN | 0x0E (fWriteBoosterEn) |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.2 (Flags)

---

## Loop — Burn-in

### Phase 2 — TLC L2 Big Chunk + L1 Small Chunk Write

#### Step 2.1: Random Big Chunk Write to L2（Non-FUA, FUA=0）

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: Chunk size ≥ TLC L2 threshold，確保資料寫入 TLC L2（big chunk mode）。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Logical Block Address | Random (total_WB_size ~ TOTAL_LBA) |
| Transfer Length | Random (TLC_L2_THRESHOLD ~ TLC_L2_THRESHOLD + 5) (units) |
| FUA bit | 0 (Non-FUA) |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.43

---

#### Step 2.2: Random Small Chunk Write to L1（Non-FUA, FUA=0）

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: Chunk size < TLC L2 threshold，確保資料寫入 TLC L1（small chunk mode）。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Logical Block Address | Random (total_WB_size ~ TOTAL_LBA) |
| Transfer Length | Random (1 ~ TLC_L2_THRESHOLD - 1) (units) |
| FUA bit | 0 (Non-FUA) |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.43

---

### Phase 3 — Random Flush + Read Compare

#### Step 3.1: Random Flush

**目的**: 隨機選取一種 Flush 機制，確保 Non-FUA 寫入的資料從 cache 落 NAND。

**Flush 類型**（隨機選一）:

| # | Flush Method | Mechanism |
|:---|:---|:---|
| 1 | Sync Cache | `SYNCHRONIZE CACHE(10) (35h)` |
| 2 | Sleep / Awake | `START STOP UNIT` → Sleep → Start |
| 3 | Power Down / Active | `START STOP UNIT` → Power Down → Active |
| 4 | Reset + Power Down/Active | HW_RESET / RST_n / EndPoint / UniPro Reset → Power cycle |
| 5 | Auto Standby | Idle 10s + Hibernate entry + current < 2mA |

**Expected**: 依所選機制完成 Flush。

**UFS SPEC Reference**: JESD220H Section 10.2.5 (Power Conditions), Section 10.4 (Reset)

---

#### Step 3.2: Read Compare（Step 2.1 + 2.2 資料）

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | Step 2.1/2.2 使用之 LUN |
| Logical Block Address | Step 2.1/2.2 寫入之 LBA |
| Transfer Length | Step 2.1/2.2 寫入之大小 |

**Expected**: `GOOD Status` + `Data Match`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.18

---

#### Step 3.3: Random Power / Reset Case

**目的**: 隨機選取一種 Power Transition 或 Reset，模擬異常中斷情境。

**Case 類型**（隨機選一）:

| # | Case | 說明 |
|:---|:---|:---|
| 1 | SPOR | Sudden Power-Off Recovery |
| 2 | Sleep / Awake | Power Condition transition |
| 3 | Reset + Power Down/Active | HW_RESET / RST_n / EndPoint / UniPro → Power cycle |
| 4 | Hibernate Enter / Exit | Hibernate state transition |
| 5 | Auto Standby | Idle 10s + HIB + current < 2mA |
| 6 | Power Down / Active | Simple power cycle |

**Expected**: Device 恢復就緒，`fDeviceInit == 1`。

**UFS SPEC Reference**: JESD220H Section 10.2.5 (Power Conditions), Section 10.4 (Reset), Section 13.4.12 (SPOR)

---

#### Step 3.4: Read Compare（Step 2.1 + 2.2 資料，Post Power Case）

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | Step 2.1/2.2 使用之 LUN |
| Logical Block Address | Step 2.1/2.2 寫入之 LBA |
| Transfer Length | Step 2.1/2.2 寫入之大小 |

**Expected**: `GOOD Status` + `Data Match`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

### Phase 4 — Random Multi-CMD Write + Flush + Compare

#### Step 4.1: Random Multi-CMD Write（Non-FUA, FUA=0）

**SCSI CMD**: `WRITE(10) (2Ah)` × N (N = Random 20~33)

**目的**: 隨機數量（20~33）的 Non-FUA Write，模擬混合 L1/L2 大量寫入。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Logical Block Address | Random (total_WB_size ~ TOTAL_LBA) |
| Transfer Length | Random (1 ~ TLC_L2_THRESHOLD + 5) (units) |
| FUA bit | 0 (Non-FUA) |
| Command Count (N) | Random (20 ~ 33) |

**Expected**: `GOOD Status`（所有 N 個命令）。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.43

---

#### Step 4.2: Random Flush

**目的**: 隨機選取一種 Flush 機制（同 Step 3.1）。

**Flush 類型**: 隨機選一（Sync Cache / Sleep/Awake / Power Down / Reset / Auto Standby）

**Expected**: Flush 完成。

**UFS SPEC Reference**: JESD220H Section 10.2.5, Section 10.4

---

#### Step 4.3: Read Compare（Step 4.1 資料）

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | Step 4.1 使用之 LUN |
| Logical Block Address | Step 4.1 寫入之 LBA |
| Transfer Length | Step 4.1 寫入之大小 |

**Expected**: `GOOD Status` + `Data Match`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

## Phase F — Final Read Compare All

### Step F.1: 全卡 Read Compare

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | All LUNs |
| Logical Block Address | 0x00000000 |
| Transfer Length | TOTAL_LBA + 1 |

**Expected**: `GOOD Status` + `Data Match All Card`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | Step 0.2, Post-Reset |
| 0x25 | READ CAPACITY(10) | 10 | Step 0.5 |
| 0x28 | READ(10) | 10 | Step 3.2, 3.4, 4.3, F.1 |
| 0x2A | WRITE(10) | 10 | Step 1.2, 2.1, 2.2, 4.1 |
| 0x35 | SYNCHRONIZE CACHE(10) | 10 | Step 3.1 (Flush #1) |
| 0x1B | START STOP UNIT | 6 | Step 3.1 (Flush #2,3), Step 3.3 |
| 0x42 | UNMAP | 10 | Step 0.4 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 存取 | 使用位置 |
|:---|:---|:---|:---|:---|
| 0x0E | fWriteBoosterEn | 0x02/0x05 (SET/CLEAR FLAG) | R/W | Step 1.1, 1.3 |
| 0x06 | fPurgeEnable | 0x02 (SET FLAG) | R/W | Step 0.4 |
| 0x07 | bPurgeStatus | 0x03 (READ ATTRIBUTE) | R | Step 0.4 (驗證) |
| 0x01 | Configuration Descriptor | 0x08 (WRITE DESCRIPTOR) | W | Step 0.3 |
| 0x01 | fDeviceInit | 0x01 (READ FLAG) | R | Step 3.3 (驗證) |
| 0x14 | bBackgroundOpStatus | 0x03 (READ ATTRIBUTE) | R | (如需確認 BKOPS) |

## 附錄 C — UFS Reset 類型說明

| Reset Type | 說明 | SPEC Reference |
|:---|:---|:---|
| HW_RESET | RST_n signal hardware reset | JESD220H Section 10.4.2 |
| RST_n | Reset signal toggle | JESD220H Section 10.4.2 |
| EndPoint Reset | DME EndPointReset command | JESD220H Section 10.4.4 |
| UniPro Reset | UniPro layer reset | JESD220H Section 10.4.5 |
| SPOR | Sudden Power-Off Recovery | JESD220H Section 13.4.12 |

---

## 自我驗證

- Tree Diagram leaf steps: **16** (0.1~0.5=5, 1.1~1.3=3, 2.1~2.2=2, 3.1~3.4=4, 4.1~4.3=3, F.1=1 → 但 0.1 是 HW check 不算 SCSI/Query step... wait, let me recount properly)
- 0.1(HW), 0.2(TUR), 0.3(WRITE DESC), 0.4(UNMAP+SET FLAG), 0.5(RD CAP) = 5
- 1.1(SET FLAG), 1.2(WRITE), 1.3(CLEAR FLAG) = 3
- 2.1(WRITE), 2.2(WRITE) = 2
- 3.1(Flush), 3.2(READ), 3.3(Power), 3.4(READ) = 4
- 4.1(WRITE), 4.2(Flush), 4.3(READ) = 3
- F.1(READ) = 1
- Total: 5+3+2+4+3+1 = 18
- `### Step` sections: Step 0.1−0.5 (5), Step 1.1−1.3 (3), Step 2.1−2.2 (2), Step 3.1−3.4 (4), Step 4.1−4.3 (3), Step F.1 (1) = 18 ✓
