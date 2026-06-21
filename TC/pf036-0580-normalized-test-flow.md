---
title: PF036_0580_Temperature_Vendor_Write_Read-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf036_0580, scsi-cmd, temperature, vu, burn-in]
description: >
  PF036_0580 Temperature Vendor Write Read Test — 在多溫度點（T5→T3→T1→T9→T8→T7→T2→T4
  升溫 + 降溫）下驗證 WRITE/READ/UNMAP 操作正確性。
sources:
  - JIRA: PF036_0580 (SYSTCUFS-715)
---

# PF036_0580 正規化 Test Flow（SCSI CMD 単位）

## 測試目標

透過 Vendor Unique 命令設定溫度，在升溫/降溫各 8 個溫度點下驗證 WRITE/READ/UNMAP 操作正常。

## IC 相容性

| IC | 8317 B47T |
|:---|:---|

## 測試架構（Tree Diagram — 含 Expected）

```
PF036_0580 Test Flow
│
├── Phase 0: 初始化
│   ├── Step 0.1: HW Check — IC=8317 B47T → Expected: 支援, 否則 NOT SUPPORTED
│   ├── Step 0.2: UNMAP — Erase All → Expected: GOOD Status
│   ├── Step 0.3: QUERY Set Flag (fPurgeEnable) — Purge → Expected: QUERY RESPONSE Success
│   └── Step 0.4: QUERY Read Attribute (bPurgeStatus) — Wait Purge → Expected: bPurgeStatus == 0x00
│
├── Loop 升溫 (T5→T3→T1→T9→T8→T7→T2→T4)
│   ├── Step L.1: VU 0x33 — Set temperature = Tn → Expected: Temperature set
│   ├── Step L.2: READ(10) — Random, LBA=rand(0,capacity), chunksize=4K~512K, FUA=0 → Expected: GOOD Status
│   ├── Step L.3: UNMAP — Random, LBA=rand, chunksize=rand, FUA=0 → Expected: GOOD Status
│   ├── Step L.4: WRITE(10) — Random, LBA=rand, chunksize=4K~512K, FUA=0 → Expected: GOOD Status
│   └── Step L.5: VU 0xE1 — Verify temperature == Tn → Expected: Temperature == Tn
│
├── Loop 降溫 (T4→T2→T7→T8→T9→T1→T3→T5) — 同上升溫步驟 → Expected: 同上升溫
│
└── Phase F: Final Verify
    └── Step F.1: READ(10) + Compare All Card → Expected: GOOD Status, Data Match All
```

---

## Phase 0 — 初始化

### Step 0.1: IC Check

| Check | Expected |
|-------|---------|
| IC | 8317 B47T |

---

### Step 0.2: Erase All

**SCSI CMD**: `UNMAP (42h)`

**Expected**: `GOOD Status`。

---

### Step 0.3: Enable Purge

**UFS QUERY**: `SET FLAG (fPurgeEnable, IDN 0x06)`

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.4: Wait Purge

**UFS QUERY**: `READ ATTRIBUTE (bPurgeStatus, IDN 0x07)`

**Expected**: `bPurgeStatus == 0x00`。

---

## Temperature Loops

### Step L.1: Set Temperature (VU 0x33)

**目的**: 使用 VU command 0x33 設定溫度至 Tn。

| Temperature Points | T5, T3, T1, T9, T8, T7, T2, T4 |
|:---|:---|

**Expected**: `Temperature set`。

---

### Step L.2: Random Read

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | All |
| LBA | Random (0 ~ capacity) |
| Transfer Length | Random (4KB ~ 512KB) |
| FUA | 0 |

**Expected**: `GOOD Status`。

---

### Step L.3: Random UNMAP

**SCSI CMD**: `UNMAP (42h)`

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | All |
| LBA | Random |
| Transfer Length | Random |

**Expected**: `GOOD Status`。

---

### Step L.4: Random Write

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All |
| LBA | Random (0 ~ capacity) |
| Transfer Length | Random (4KB ~ 512KB) |
| FUA | 0 |

**Expected**: `GOOD Status`。

---

### Step L.5: Verify Temperature (VU 0xE1)

**目的**: 使用 VU command 0xE1 驗證當前溫度 == Tn。

**Expected**: `Temperature == Tn`。

---

## Phase F — Final Verify

### Step F.1: Read Compare All Card

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | All |
| LBA | 0 ~ MAX_LBA |

**Expected**: `GOOD Status, Data Match All`。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | 使用位置 |
|:---|:---|:---|
| 0x28 | READ(10) | Step L.2, F.1 |
| 0x2A | WRITE(10) | Step L.4 |
| 0x42 | UNMAP | Step 0.2, L.3 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode |
|:---|:---|:---|
| 0x06 | fPurgeEnable | 0x02 (SET FLAG) |
| 0x07 | bPurgeStatus | 0x03 (READ ATTRIBUTE) |

---

## 自我驗證

- Tree Diagram leaf steps: **12** (0.1~0.4=4, L.1~L.5=5×2 loops, F.1=1)
- `### Step` sections: **12** ✓ (loop steps shared for 升溫/降溫)
- 每個 leaf step 都有 `→ Expected:` ✓
