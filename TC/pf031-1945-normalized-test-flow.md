---
title: PF031_1945_WB20_Boundary_Size-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf031_1945, scsi-cmd, write-booster, wb20, fifo, pinned, partial-flush]
description: >
  PF031_1945 WB2.0 Boundary Size Test — 驗證 WriteBooster 2.0 的 FIFO mode (01h)
  與 Pinned mode (02h) 邊界大小行為，確認 Partial Flush 前後 SLC mode 資料保留正確性、
  AvailableBufferSize 數值及 Flush Enable 的 Idle 回應。
sources:
  - JIRA: PF031_1945 (SYSTCUFS-2251)
  - UFS Spec: JESD220H Section 13.4.18 (WriteBooster), Section 14.3.1 (WB Attributes)
---

# PF031_1945 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

驗證 WB 2.0 兩種 Partial Flush Mode：
1. **FIFO mode (01h)**：確認 dMaxFIFOSize 邊界行為、AvailableWriteBoosterBufferSize < 0xA（幾乎滿）、SLC mode 資料保留
2. **Pinned mode (02h)**：確認 dPinnedWriteBoosterBufferNumAllocUnits 邊界行為、
   bPinnedWriteBoosterBufferAvailablePercentage < 0xA、Group ID=0x18 SLC mode 資料保留

## IC/NAND 相容性

| 條件 | 值 |
|------|-----|
| IC | 8329 或 UFS >= 4.1 |
| 不支援時 | Pattern 判定為 `NOT SUPPORTED` |

## 測試架構（Tree Diagram — 含 Expected）

```
PF031_1945 Test Flow
│
├── Phase 0: 相容性檢查與 WB 配置
│   ├── Step 0.1: HW Check — IC=8329 or UFS >= 4.1 → Expected: 若不符, NOT SUPPORTED
│   ├── Step 0.2: QUERY Read Attribute (dExtendedUFSFeaturesSupport) — Check WB support → Expected: QUERY RESPONSE Success, WB bit == 1
│   └── Step 0.3: QUERY Write Descriptor (Config Descriptor) — WB 4GB Shared mode → Expected: QUERY RESPONSE Success
│
├── [若 bit[1] dExtendedWriteBoosterSupport == 1]
│   └── Phase 1: FIFO Mode
│       ├── Step 1.1: QUERY Write Attribute (bWriteBoosterBufferPartialFlushMode, 0x3F) = 01h → Expected: QUERY RESPONSE Success
│       ├── Step 1.2: QUERY Clear Flag (fWriteBoosterBufferFlushEn, 0x0F) → Expected: QUERY RESPONSE Success
│       ├── Step 1.3: QUERY Clear Flag (fBackgroundOpsEn) — 僅 8329 KIC → Expected: QUERY RESPONSE Success
│       ├── Step 1.4: QUERY Write Attribute (dMaxFIFOSizeForWriteBoosterPartialFlushMode, 0x40) = Config WB size → Expected: QUERY RESPONSE Success
│       ├── Step 1.5: QUERY Set Flag (fWriteBoosterEn, 0x0E) → Expected: QUERY RESPONSE Success
│       ├── Step 1.6: WRITE(10) — Seq 4GB, chunk=65535, FUA=random, LUN0 → Expected: GOOD Status
│       ├── Step 1.7: QUERY Read Attribute (AvailableWriteBoosterBufferSize) — expect < 0xA → Expected: AvailableWriteBoosterBufferSize < 0xA
│       ├── Step 1.8: QUERY Set Flag (fWriteBoosterBufferFlushEn) — check idle → Expected: QUERY RESPONSE Success, response == 0 (idle)
│       ├── Step 1.9: VUC 0x88 — Check LBA in SLC mode → Expected: SLC mode (VU check)
│       └── Step 1.10: QUERY Read Attribute (AvailableWriteBoosterBufferSize) — expect < 0xA (not flushed) → Expected: AvailableWriteBoosterBufferSize < 0xA
│
├── [若 bit[2] dExtendedWriteBoosterSupport == 1]
│   └── Phase 2: Pinned Mode
│       ├── Step 2.1: UNMAP + SET FLAG(fPurgeEnable) — Erase & Purge All Card → Expected: GOOD Status + bPurgeStatus == 0x00
│       ├── Step 2.2: QUERY Write Attribute (bWriteBoosterBufferPartialFlushMode, 0x3F) = 02h → Expected: QUERY RESPONSE Success
│       ├── Step 2.3: QUERY Clear Flag (fWriteBoosterBufferFlushEn, 0x0F) → Expected: QUERY RESPONSE Success
│       ├── Step 2.4: QUERY Clear Flag (fBackgroundOpsEn) — 僅 8329/8363 KIC → Expected: QUERY RESPONSE Success
│       ├── Step 2.5: QUERY Write Attribute (dPinnedWriteBoosterBufferNumAllocUnits, 0x45) = Config WB size → Expected: QUERY RESPONSE Success
│       ├── Step 2.6: QUERY Set Flag (fWriteBoosterEn, 0x0E) → Expected: QUERY RESPONSE Success
│       ├── Step 2.7: WRITE(10) — Seq 4GB, Group ID=0x18, chunk=65535, FUA=random, LUN0 → Expected: GOOD Status
│       ├── Step 2.8: QUERY Read Attribute (bPinnedWriteBoosterBufferAvailablePercentage, 0x43) — < 0xA → Expected: bPinnedWriteBoosterBufferAvailablePercentage < 0xA
│       ├── Step 2.9: QUERY Read Attribute (AvailableWriteBoosterBufferSize) — < 0xA → Expected: AvailableWriteBoosterBufferSize < 0xA
│       ├── Step 2.10: QUERY Set Flag (fWriteBoosterBufferFlushEn) — check idle → Expected: QUERY RESPONSE Success, response == 0 (idle)
│       ├── Step 2.11: VUC 0x88 — Check first 4GB in SLC mode → Expected: SLC mode (VU check)
│       └── Step 2.12: QUERY Read Attribute (bPinnedWriteBoosterBufferAvailablePercentage) — < 0xA (not flushed) → Expected: bPinnedWriteBoosterBufferAvailablePercentage < 0xA
│
└── Phase 3: Recovery — 恢復預設值
    ├── Step 3.1: QUERY Write Attribute (dMaxFIFOSize, 0x40) = 0 → Expected: QUERY RESPONSE Success
    ├── Step 3.2: QUERY Write Attribute (dPinnedNumAllocUnits, 0x45) = 0 → Expected: QUERY RESPONSE Success
    └── Step 3.3: QUERY Write Attribute (bWriteBoosterBufferPartialFlushMode, 0x3F) = 00h (Normal) → Expected: QUERY RESPONSE Success
```

---

## Phase 0 — 相容性檢查與 WB 配置

### Step 0.1: 裝置相容性檢查

**目的**: 確認 IC 為 8329 或 UFS >= 4.1。

| Check | Expected Value |
|-------|---------------|
| IC | 8329 |
| UFS Version | >= 4.1 |

**若不支援**: Pattern 判定為 `NOT SUPPORTED`，終止測試。

---

### Step 0.2: 檢查 WriteBooster 支援

**UFS QUERY**: `READ ATTRIBUTE (dExtendedUFSFeaturesSupport)`

**目的**: 確認 Device 支援 WriteBooster 功能。

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | dExtendedUFSFeaturesSupport |

**Expected**: `QUERY RESPONSE Success`，WB 支援 bit == 1。若不支援 → `NOT SUPPORTED`。

**UFS SPEC Reference**: JESD220H Section 14.3.1 (dExtendedUFSFeaturesSupport)

---

### Step 0.3: 配置 WriteBooster 4GB Shared Mode

**UFS QUERY**: `WRITE DESCRIPTOR (Configuration Descriptor, IDN 0x01)`

**目的**: 設定 WriteBooster Buffer Type 為 Shared，大小 4GB。

| Field | Value |
|-------|-------|
| Query Opcode | 0x08 (WRITE DESCRIPTOR) |
| Descriptor IDN | 0x01 (Configuration Descriptor) |
| bWriteBoosterBufferType | 0x01 (Shared Buffer Type) |
| dLUNumWriteBoosterBufferAllocUnits | 4GB worth of allocation units |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.1.4.5 (Configuration Descriptor)

---

## Phase 1 — FIFO Mode

> 執行條件：`dExtendedWriteBoosterSupport` bit[1] == 1

### Step 1.1: 設定 Partial Flush Mode = FIFO

**UFS QUERY**: `WRITE ATTRIBUTE (bWriteBoosterBufferPartialFlushMode, IDN 0x3F)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| Attribute IDN | 0x3F (bWriteBoosterBufferPartialFlushMode) |
| Value | 0x01 (FIFO mode) |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 13.4.18, Section 14.3.1

---

### Step 1.2: Disable Flush Enable

**UFS QUERY**: `CLEAR FLAG (fWriteBoosterBufferFlushEn, IDN 0x0F)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x05 (CLEAR FLAG) |
| Flag IDN | 0x0F (fWriteBoosterBufferFlushEn) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 1.3: Disable BackgroundOps（僅 8329 KIC）

**UFS QUERY**: `CLEAR FLAG (fBackgroundOpsEn, IDN 0x03)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x05 (CLEAR FLAG) |
| Flag IDN | 0x03 (fBackgroundOpsEn) |
| 條件 | 僅 8329 KIC 執行 |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 1.4: 設定 dMaxFIFOSize

**UFS QUERY**: `WRITE ATTRIBUTE (dMaxFIFOSizeForWriteBoosterPartialFlushMode, IDN 0x40)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| Attribute IDN | 0x40 (dMaxFIFOSizeForWriteBoosterPartialFlushMode) |
| Value | Config WB size (4GB) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 1.5: Enable WriteBooster

**UFS QUERY**: `SET FLAG (fWriteBoosterEn, IDN 0x0E)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | 0x0E (fWriteBoosterEn) |
| Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.2 (Flags)

---

### Step 1.6: Sequential Write 4GB to WB Buffer

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: 循序寫入 4GB 資料至 LUN0，FUA random。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 (LUN0) |
| Logical Block Address | Random(0, LU_capacity - 4GB) |
| Transfer Length per Chunk | 65535 blocks (max WRITE10) |
| Total Length | 4GB |
| FUA | Random(0, 1) |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2, SBC-4 5.43

---

### Step 1.7: 檢查 AvailableWriteBoosterBufferSize < 0xA

**UFS QUERY**: `READ ATTRIBUTE (AvailableWriteBoosterBufferSize)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | AvailableWriteBoosterBufferSize |

**Expected**: `QUERY RESPONSE Success`，`AvailableWriteBoosterBufferSize < 0xA`（Buffer 幾乎滿）。

---

### Step 1.8: Set Flush Enable + Check Idle

**UFS QUERY**: `SET FLAG (fWriteBoosterBufferFlushEn, IDN 0x0F)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | 0x0F (fWriteBoosterBufferFlushEn) |
| Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`，response value == 0 (idle)。

---

### Step 1.9: VUC 0x88 — Check SLC Mode

**目的**: 使用 Vendor Unique Command 0x88 查詢 Step 1.6 寫入之起始 LBA 的 PBA，確認資料在 SLC mode。

**Expected**: `SLC mode`（VU check — data residing in SLC）。

---

### Step 1.10: 再次檢查 AvailableBufferSize（應未 Flush）

**UFS QUERY**: `READ ATTRIBUTE (AvailableWriteBoosterBufferSize)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | AvailableWriteBoosterBufferSize |

**Expected**: `QUERY RESPONSE Success`，`AvailableWriteBoosterBufferSize < 0xA`（資料未被 flush，Buffer 仍滿）。

---

## Phase 2 — Pinned Mode

> 執行條件：`dExtendedWriteBoosterSupport` bit[2] == 1

### Step 2.1: Erase & Purge All Card

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

### Step 2.2: 設定 Partial Flush Mode = Pinned

**UFS QUERY**: `WRITE ATTRIBUTE (bWriteBoosterBufferPartialFlushMode, IDN 0x3F)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| Attribute IDN | 0x3F (bWriteBoosterBufferPartialFlushMode) |
| Value | 0x02 (Pinned mode) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 2.3: Disable Flush Enable

**UFS QUERY**: `CLEAR FLAG (fWriteBoosterBufferFlushEn, IDN 0x0F)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x05 (CLEAR FLAG) |
| Flag IDN | 0x0F (fWriteBoosterBufferFlushEn) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 2.4: Disable BackgroundOps（僅 8329/8363 KIC）

**UFS QUERY**: `CLEAR FLAG (fBackgroundOpsEn, IDN 0x03)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x05 (CLEAR FLAG) |
| Flag IDN | 0x03 (fBackgroundOpsEn) |
| 條件 | 僅 8329 或 8363 KIC 執行 |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 2.5: 設定 dPinnedWriteBoosterBufferNumAllocUnits

**UFS QUERY**: `WRITE ATTRIBUTE (dPinnedWriteBoosterBufferNumAllocUnits, IDN 0x45)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| Attribute IDN | 0x45 (dPinnedWriteBoosterBufferNumAllocUnits) |
| Value | Config WB size (4GB) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 2.6: Enable WriteBooster

**UFS QUERY**: `SET FLAG (fWriteBoosterEn, IDN 0x0E)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | 0x0E (fWriteBoosterEn) |
| Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 2.7: Sequential Write 4GB Pinned Data

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: 以 Group ID=0x18 寫入 Pinned 資料。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 (LUN0) |
| Logical Block Address | Random(0, LU_capacity - 4GB) |
| Transfer Length per Chunk | 65535 blocks |
| Total Length | 4GB |
| FUA | Random(0, 1) |
| Group ID | 0x18 |

**Expected**: `GOOD Status`。

---

### Step 2.8: 檢查 bPinnedWriteBoosterBufferAvailablePercentage < 0xA

**UFS QUERY**: `READ ATTRIBUTE (bPinnedWriteBoosterBufferAvailablePercentage, IDN 0x43)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x43 (bPinnedWriteBoosterBufferAvailablePercentage) |

**Expected**: `QUERY RESPONSE Success`，`bPinnedWriteBoosterBufferAvailablePercentage < 0xA`。

---

### Step 2.9: 檢查 AvailableWriteBoosterBufferSize < 0xA

**UFS QUERY**: `READ ATTRIBUTE (AvailableWriteBoosterBufferSize)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | AvailableWriteBoosterBufferSize |

**Expected**: `QUERY RESPONSE Success`，`AvailableWriteBoosterBufferSize < 0xA`。

---

### Step 2.10: Set Flush Enable + Check Idle

**UFS QUERY**: `SET FLAG (fWriteBoosterBufferFlushEn, IDN 0x0F)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | 0x0F (fWriteBoosterBufferFlushEn) |
| Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`，response value == 0 (idle)。

---

### Step 2.11: VUC 0x88 — Check First 4GB SLC Mode

**目的**: 使用 Vendor Unique Command 0x88 查詢 Step 2.7 寫入之前 4GB 資料的 PBA。

**Expected**: `SLC mode`（VU check — first 4GB data in SLC）。

---

### Step 2.12: 再次檢查 Pinned Available Percentage（應未 Flush）

**UFS QUERY**: `READ ATTRIBUTE (bPinnedWriteBoosterBufferAvailablePercentage, IDN 0x43)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| Attribute IDN | 0x43 (bPinnedWriteBoosterBufferAvailablePercentage) |

**Expected**: `QUERY RESPONSE Success`，`bPinnedWriteBoosterBufferAvailablePercentage < 0xA`（pinned data 未被 flush）。

---

## Phase 3 — Recovery

### Step 3.1: 清除 dMaxFIFOSize

**UFS QUERY**: `WRITE ATTRIBUTE (dMaxFIFOSizeForWriteBoosterPartialFlushMode, IDN 0x40)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| Attribute IDN | 0x40 (dMaxFIFOSizeForWriteBoosterPartialFlushMode) |
| Value | 0x00 |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 3.2: 清除 dPinnedWriteBoosterBufferNumAllocUnits

**UFS QUERY**: `WRITE ATTRIBUTE (dPinnedWriteBoosterBufferNumAllocUnits, IDN 0x45)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| Attribute IDN | 0x45 (dPinnedWriteBoosterBufferNumAllocUnits) |
| Value | 0x00 |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 3.3: 恢復 Normal Mode

**UFS QUERY**: `WRITE ATTRIBUTE (bWriteBoosterBufferPartialFlushMode, IDN 0x3F)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| Attribute IDN | 0x3F (bWriteBoosterBufferPartialFlushMode) |
| Value | 0x00 (Normal mode) |

**Expected**: `QUERY RESPONSE Success`。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x2A | WRITE(10) | 10 | Step 1.6, 2.7 |
| 0x42 | UNMAP | 10 | Step 2.1 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 使用位置 |
|:---|:---|:---|:---|
| 0x01 | Configuration Descriptor | 0x08 (WRITE DESCRIPTOR) | Step 0.3 |
| 0x03 | fBackgroundOpsEn | 0x05 (CLEAR FLAG) | Step 1.3, 2.4 |
| 0x06 | fPurgeEnable | 0x02 (SET FLAG) | Step 2.1 |
| 0x0E | fWriteBoosterEn | 0x02 (SET FLAG) | Step 1.5, 2.6 |
| 0x0F | fWriteBoosterBufferFlushEn | 0x02/0x05 (SET/CLEAR FLAG) | Step 1.2, 1.8, 2.3, 2.10 |
| 0x3F | bWriteBoosterBufferPartialFlushMode | 0x04 (WRITE ATTRIBUTE) | Step 1.1, 2.2, 3.3 |
| 0x40 | dMaxFIFOSizeForWriteBoosterPartialFlushMode | 0x04 (WRITE ATTRIBUTE) | Step 1.4, 3.1 |
| 0x43 | bPinnedWriteBoosterBufferAvailablePercentage | 0x03 (READ ATTRIBUTE) | Step 2.8, 2.12 |
| 0x45 | dPinnedWriteBoosterBufferNumAllocUnits | 0x04 (WRITE ATTRIBUTE) | Step 2.5, 3.2 |

---

## 自我驗證

- Tree Diagram leaf steps: **28** (0.1~0.3=3, 1.1~1.10=10, 2.1~2.12=12, 3.1~3.3=3)
- `### Step` sections: **28** ✓
- 每個 leaf step 都有 `→ Expected:` ✓
- 無 `(待確認)` 佔位符 ✓
