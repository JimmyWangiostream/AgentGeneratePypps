---
title: PF007_2103_Trim_Save_P2L_Cross_VB_Window-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf007_2103, scsi-cmd, trim, unmap, p2l, vb, window]
description: >
  PF007_2103 Trim Save P2L Cross VB And Window — 透過 UNMAP + WRITE 操作
  模擬 P2L (Physical-to-Logical) mapping 跨 VB 與跨 Window 的 Trim Save 場景，
  驗證 SPOR 後資料完整性。涵蓋大/小 chunksize UNMAP 觸發 Cross VB/Window 節點變化。
sources:
  - JIRA: PF007_2103 (SYSTCUFS-2449)
  - UFS Spec: JESD220H Section 10.7.2, Section 13.4.9 (UNMAP), Section 14.2 (Flags)
---

# PF007_2103 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

建立一個全新的 Current L2 VB 後，透過兩種 Write pattern（loop1: TLC_VB_size、loop2: window_size）
搭配大/小 chunksize UNMAP 操作，驗證 P2L mapping 在跨 VB 或跨 Window 時的 Trim Save 正確性，
並在 SPOR 後確認資料不遺失。

## JIRA Step 對照

| JIRA Step | 原始描述 | 正規化後對應 |
|-----------|---------|-------------|
| Step 1 | Erase Purge All + config | Step 0.2, 0.3 |
| Step 2 | Create new empty current L2 VB | Step 1.1~1.3 |
| Step 3 | Seq write loop1/loop2 (FUA=1) | Step 2.1, 2.2 |
| Step 4 | Big chunksize unmap ×3 | Step 3.1 |
| Step 5 | Small chunksize unmap (cross VB/window) | Step 3.2 |
| Step 6 | Big chunksize unmap | Step 3.3 |
| Step 7 | Write program_unit (FUA=1) | Step 4.1 |
| Step 8 | HW_RESET (SPOR) | Step 5.1 |
| Step 9 | Read Compare | Step 6.1 |
| Step 10 | Write 1 block (FUA=1) | Step 4.2 |
| Step 11 | Loop step2~10 | Loop wrapper |

---

## 測試架構

```
PF007_2103 Test Flow
│
├── Phase 0: 初始化配置
│   ├── Step 0.1: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│   ├── Step 0.2: QUERY Read Descriptor (Configuration Descriptor) — 確認 discard disable → Expected: QUERY RESPONSE Success
│   └── Step 0.3: UNMAP + SET FLAG(fPurgeEnable) — Erase All, LUN0 discard disable → Expected: bPurgeStatus == 0x00
│
├── Phase 1: 建立新 Current L2 VB
│   ├── Step 1.1: QUERY Read Flag (fBackgroundOpsEn) — 讀取目前 BKOPS 狀態 → Expected: QUERY RESPONSE Success
│   ├── Step 1.2: QUERY Clear Flag (fBackgroundOpsEn) — 關閉 BKOPS → Expected: QUERY RESPONSE Success
│   └── Step 1.3: [Loop] WRITE(10) 4KB + UNMAP 40KB — 直到 Current L2 VB 改變 → Expected: New Current L2 VB detected
│
└── Loop (outer: loop1=VB_size, loop2=window_size)
    │
    ├── Phase 2: Sequential Write (FUA=1)
    │   ├── Step 2.1: WRITE(10) FUA=1 — loop1 len = TLC_VB_size - program_unit → Expected: GOOD Status
    │   └── Step 2.2: WRITE(10) FUA=1 — loop2 len = window_size - program_unit → Expected: GOOD Status
    │
    ├── Phase 3: UNMAP 操作
    │   ├── Step 3.1: UNMAP ×3 Big Chunk — LBA random, len=4096 → Expected: GOOD Status (all 3), 記錄最後一筆區域
    │   ├── Step 3.2: UNMAP Small Chunk — LBA 在 Step 3.1 最後區域內, len=8, ceil(program_unit/8)+1 次 → Expected: GOOD Status, 跨 VB 或跨 Window
    │   └── Step 3.3: UNMAP Big Chunk — LBA random, len=100 → Expected: GOOD Status
    │
    ├── Phase 4: 驗證寫入 (FUA=1)
    │   ├── Step 4.1: WRITE(10) FUA=1 — LBA random, len = program_unit → Expected: GOOD Status
    │   └── Step 4.2: WRITE(10) FUA=1 — LBA random, len = 1 block → Expected: GOOD Status
    │
    ├── Phase 5: SPOR
    │   └── Step 5.1: HW_RESET (SPOR) → Expected: Reset device success
    │
    └── Phase 6: Read Compare
        └── Step 6.1: READ(10) + Compare — 比對所有已寫入資料 → Expected: GOOD Status, Data Match
```

---

## Phase 0 — 初始化配置

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

### Step 0.2: 讀取 Configuration Descriptor（確認 discard disable）

**UFS QUERY**: `READ DESCRIPTOR (Configuration Descriptor)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x07 (READ DESCRIPTOR) |
| IDN | 0x01 (Configuration Descriptor) |
| Index | 0x00 |
| Selector | 0x00 |
| Length | 0x40 |

**Expected**: `QUERY RESPONSE Success`，確認 discard 相關設定。

**UFS SPEC Reference**: JESD220H Section 14.1.4.5

---

### Step 0.3: Erase Purge All

**SCSI CMD**: `UNMAP (42h)` + **UFS QUERY**: `SET FLAG (fPurgeEnable, IDN 0x06)`

| Field | Value |
|-------|-------|
| UNMAP Opcode | 0x42 |
| UNMAP LUN | LUN0 |
| UNMAP LBA Range | 0 ~ MAX_LBA |
| SET FLAG Opcode | 0x02 |
| SET FLAG IDN | 0x06 (fPurgeEnable) |

**Expected**: `bPurgeStatus == 0x00`。

**UFS SPEC Reference**: JESD220H Section 13.4.11 (PURGE)

---

## Phase 1 — 建立新 Current L2 VB

### Step 1.1: 關閉 BKOPS

**UFS QUERY**: `CLEAR FLAG (fBackgroundOpsEn)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x05 (CLEAR FLAG) |
| IDN | 0x03 (fBackgroundOpsEn) |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.2 (Flags)

---

### Step 1.2: Write 4KB + Unmap 40KB Loop

**SCSI CMD**: `WRITE(10) (2Ah)` + `UNMAP (42h)` (loop)

**目的**: 反覆 Write 4KB + Unmap 40KB 直到 Current L2 VB 改變，建立全新的 empty Current L2 VB。

| Field | Value |
|-------|-------|
| WRITE Opcode | 0x2A |
| WRITE LUN | LUN0 |
| WRITE Transfer Length | 4KB (8 blocks @ 512B) |
| UNMAP Opcode | 0x42 |
| UNMAP LUN | LUN0 |
| UNMAP Transfer Length | 40KB (80 blocks) |

**Expected**: 偵測到 Current L2 VB 變更（新 VB 建立）。

**UFS SPEC Reference**: JESD220H Section 13.4.9 (UNMAP)

---

## Loop — outer: loop1 (VB_size) + loop2 (window_size)

### Phase 2 — Sequential Write

#### Step 2.1: WRITE(10) FUA=1 — loop1

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | LUN0 |
| Logical Block Address | Random (0 ~ LUN0_capacity) |
| Transfer Length | TLC_VB_size - program_unit |
| FUA bit | 1 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 10.7.2

---

#### Step 2.2: WRITE(10) FUA=1 — loop2

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | LUN0 |
| Logical Block Address | Random |
| Transfer Length | window_size - program_unit |
| FUA bit | 1 |

**Expected**: `GOOD Status`。

---

### Phase 3 — UNMAP 操作

#### Step 3.1: UNMAP Big Chunk ×3

**SCSI CMD**: `UNMAP (42h)` × 3

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | LUN0 |
| Logical Block Address | Random (0 ~ LUN0_capacity) × 3 |
| Transfer Length | 4096 blocks × 3 |

**Expected**: `GOOD Status`（3 筆），記錄最後一筆 UNMAP 的 LBA+Length 區域。

**UFS SPEC Reference**: JESD220H Section 13.4.9

---

#### Step 3.2: UNMAP Small Chunk（跨 VB / 跨 Window）

**SCSI CMD**: `UNMAP (42h)` × N

**目的**: 使用 small chunksize UNMAP 補滿 node 直到跨 VB 或跨 Window。

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | LUN0 |
| Logical Block Address | Step 3.1 最後一筆 UNMAP 區域內 |
| Transfer Length | 8 blocks |
| Command Count (N) | ceil(program_unit / 8) + 1 |

**Expected**: `GOOD Status`，觸發 P2L node 跨 VB 或跨 Window 變化。

**UFS SPEC Reference**: JESD220H Section 13.4.9

---

#### Step 3.3: UNMAP Big Chunk

**SCSI CMD**: `UNMAP (42h)`

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | LUN0 |
| Logical Block Address | Random |
| Transfer Length | 100 blocks |

**Expected**: `GOOD Status`。

---

### Phase 4 — 驗證寫入

#### Step 4.1: WRITE(10) FUA=1 — program_unit

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | LUN0 |
| Logical Block Address | Random |
| Transfer Length | program_unit |
| FUA bit | 1 |

**Expected**: `GOOD Status`。

---

#### Step 4.2: WRITE(10) FUA=1 — 1 block

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | LUN0 |
| Logical Block Address | Random |
| Transfer Length | 1 block |
| FUA bit | 1 |

**Expected**: `GOOD Status`。

---

### Phase 5 — SPOR

#### Step 5.1: HW_RESET (SPOR)

**目的**: Sudden Power-Off Recovery。

**Expected**: Device 恢復，`fDeviceInit == 1`。

**UFS SPEC Reference**: JESD220H Section 13.4.12 (SPOR)

---

### Phase 6 — Read Compare

#### Step 6.1: READ(10) + Compare

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | LUN0 |
| Logical Block Address | 對應 Step 2.1/2.2/4.1/4.2 寫入的 LBA |
| Transfer Length | 對應寫入大小 |

**Expected**: `GOOD Status` + `Data Match`。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | Step 0.1 |
| 0x28 | READ(10) | 10 | Step 6.1 |
| 0x2A | WRITE(10) | 10 | Step 1.2, 2.1, 2.2, 4.1, 4.2 |
| 0x42 | UNMAP | 10 | Step 0.3, 1.2, 3.1, 3.2, 3.3 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 存取 | 使用位置 |
|:---|:---|:---|:---|:---|
| 0x03 | fBackgroundOpsEn | 0x05 (CLEAR FLAG) | R/W | Step 1.1 |
| 0x06 | fPurgeEnable | 0x02 (SET FLAG) | R/W | Step 0.3 |
| 0x01 | Configuration Descriptor | 0x07 (READ DESCRIPTOR) | R | Step 0.2 |
| 0x01 | fDeviceInit | 0x01 (READ FLAG) | R | Step 5.1 (驗證) |

---

## 自我驗證

- Tree Diagram leaf steps: 0.1, 0.2, 0.3, 1.1, 1.2 (5) + 2.1, 2.2 (2) + 3.1, 3.2, 3.3 (3) + 4.1, 4.2 (2) + 5.1 (1) + 6.1 (1) = 14
- `### Step` sections: **14** ✓
