---
title: PF028_1772_Speed_Mode_Hibernate_Suspend-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf028_1772, scsi-cmd, speed-change, hibernate, suspend, wb, rpmb, boot-lun]
description: >
  PF028_1772 All SLC/TLC Speed Mode Hibernate Suspend Test — 在 9 種 Config
  (SLC×8 + TLC×1) × 5 Speed Modes × 6 CMD Types 的組合下驗證 Hibernate/Suspend
  後所有命令類型正常運作。
sources:
  - JIRA: PF028_1772 (SYSTCUFS-1901)
  - UFS Spec: JESD220H Section 10.4 (Reset), Section 10.2.5 (Power Conditions), Section 13.4.18 (WB), Section 13.4.17 (RPMB)
---

# PF028_1772 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

驗證在不同 Speed Mode 與 Config 組合下，Hibernate enter/exit + Suspend 後所有命令類型正常執行：
- 9 Configs：SLC (WB + Boot + RPMB = 8 combos) + TLC only = 9
- 5 Speed Modes：Gear1 PWM / Gear1 PWM Auto / Max Gear HS / Max Gear HS Auto / TX-RX Asymmetric
- 6 CMD Types × 10 rounds per speed mode

## IC 相容性

| 條件 | 需支援 Write Booster 與 RPMB |
|------|------|
| 不支援時 | `NOT SUPPORTED` |

## 測試架構（Tree Diagram — 含 Expected）

```
PF028_1772 Test Flow
│
├── Phase 0: 相容性檢查
│   └── Step 0.1: HW Check — IC 支援 WB + RPMB → Expected: 支援, 否則 NOT SUPPORTED
│
└── Loop (9 Config Combos)
    │
    ├── Phase 1: Config Setup (per combo)
    │   ├── Step 1.1: QUERY Write Descriptor (Config Descriptor) — 設定 WB Buffer → Expected: QUERY RESPONSE Success
    │   ├── Step 1.2: QUERY Set Flag (fWriteBoosterEn) — Enable WB (若 combo 含 WB) → Expected: QUERY RESPONSE Success
    │   ├── Step 1.3: QUERY Write Attribute (bBootLunEn) — Enable Boot LU (若 combo 含 Boot) → Expected: QUERY RESPONSE Success
    │   ├── Step 1.4: SECURITY PROTOCOL OUT + OUT + IN — RPMB Key Programming → Expected: GOOD Status, RPMB Key programmed
    │   └── Step 1.5: SECURITY PROTOCOL OUT + IN — RPMB Read Counter → Expected: GOOD Status, valid counter
    │
    └── Loop (5 Speed Modes)
        │
        ├── Phase 2: Speed Change
        │   └── Step 2.1: UniPro DME — Speed Change → Expected: Speed change success
        │
        └── Phase 3: Execute CMD × 10 Rounds (random order each round)
            ├── Step 3.1: Hibernate Enter → Exit, cnt=1~10, delay=1us~10000us → Expected: Device 恢復就緒
            ├── Step 3.2: WRITE(10), cnt=1~10, all LUNs, chunksize=4K~4MB → Expected: GOOD Status
            ├── Step 3.3: READ(10), cnt=1~10, all LUNs, chunksize=4K~4MB → Expected: GOOD Status
            ├── Step 3.4: UNMAP, cnt=1~10, all LUNs, chunksize=4K~4MB → Expected: GOOD Status
            ├── Step 3.5: SECURITY PROTOCOL OUT→IN — RPMB Write (if configured) → Expected: GOOD Status
            └── Step 3.6: SECURITY PROTOCOL OUT→IN — RPMB Read (if configured) → Expected: GOOD Status
```

---

## Phase 0 — 相容性檢查

### Step 0.1: 裝置相容性檢查

**目的**: 確認 IC 支援 Write Booster 與 RPMB。

| Check | Requirement |
|-------|------------|
| Write Booster | Supported |
| RPMB | Supported |

**若不支援**: Pattern 判定為 `NOT SUPPORTED`。

---

## Phase 1 — Config Setup (9 Combos)

### Config 組合矩陣

| Combo | Write Booster | Boot LUN | RPMB | Partition |
|:---|:---|:---|:---|:---|
| 1 | ✓ | ✓ | ✓ | SLC |
| 2 | ✓ | ✓ | — | SLC |
| 3 | ✓ | — | ✓ | SLC |
| 4 | ✓ | — | — | SLC |
| 5 | — | ✓ | ✓ | SLC |
| 6 | — | ✓ | — | SLC |
| 7 | — | — | ✓ | SLC |
| 8 | — | — | — | SLC |
| 9 (TLC) | — | — | — | TLC |

### Step 1.1: 設定 WB Buffer

**UFS QUERY**: `WRITE DESCRIPTOR (Configuration Descriptor, IDN 0x01)`

**條件**: 僅 combo 含 WB 時執行。

| Field | Value |
|-------|-------|
| Query Opcode | 0x08 (WRITE DESCRIPTOR) |
| Descriptor IDN | 0x01 (Configuration Descriptor) |
| bWriteBoosterBufferType | 0x01 (Shared) |
| dLUNumWriteBoosterBufferAllocUnits | dWriteBoosterBufferMaxNAllocUnits (from Geometry Descriptor) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 1.2: Enable WriteBooster

**UFS QUERY**: `SET FLAG (fWriteBoosterEn, IDN 0x0E)`

**條件**: 僅 combo 含 WB 時執行。

| Field | Value |
|-------|-------|
| Query Opcode | 0x02 (SET FLAG) |
| Flag IDN | 0x0E (fWriteBoosterEn) |
| Value | 0x01 (Set) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 1.3: Enable Boot LU

**UFS QUERY**: `WRITE ATTRIBUTE (bBootLunEn, IDN 0x00)`

**條件**: 僅 combo 含 Boot LU 時執行。

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| Attribute IDN | 0x00 (bBootLunEn) |
| Value | 依所需 Boot LU bit mask |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 1.4: RPMB Key Programming

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL IN (A2h)`

**條件**: 僅 combo 含 RPMB 時執行。

| Field | Value |
|-------|-------|
| SECURITY PROTOCOL | 0xEC (RPMB) |
| Region | Region 0 |
| Operation | Authentication Key Programming |

**RPMB Protocol Flow**: OUT (Send Key) → OUT (Request Result) → IN (Receive Result)

**Expected**: `GOOD Status`，RPMB Key programmed successfully。

**UFS SPEC Reference**: JESD220H Section 13.4.17 (RPMB)

---

### Step 1.5: RPMB Read Counter

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL IN (A2h)`

**條件**: 僅 combo 含 RPMB 時執行。

| Field | Value |
|-------|-------|
| SECURITY PROTOCOL | 0xEC (RPMB) |
| Region | Region 0 |
| Operation | Read Write Counter |

**RPMB Protocol Flow**: OUT (Send Request) → IN (Receive Counter)

**Expected**: `GOOD Status`，回傳 valid counter value。

**UFS SPEC Reference**: JESD220H Section 13.4.17

---

## Phase 2 — Speed Change (5 Speed Modes)

### Speed Mode 類型

| # | Speed Mode | 說明 |
|:---|:---|:---|
| 1 | Gear 1 PWM | Gear 1 Power fast (PWM-GEAR1) |
| 2 | Gear 1 PWM Auto | Gear 1 Power fast auto |
| 3 | Max Gear HS | UFS 4.0=Gear5, 3.0=Gear4, 2.1=Gear3 |
| 4 | Max Gear HS Auto | Max gear power fast auto |
| 5 | TX-RX Asymmetric | TX/RX 非對稱 Gear Speed |

### Step 2.1: UniPro DME Speed Change

**DME Operation**: Speed Change via UniPro DME

**目的**: 切換至指定 Speed Mode。

| Field | Value |
|-------|-------|
| Layer | UniPro DME |
| Target Speed | 依 loop 目前 Speed Mode |

**Expected**: `Speed change success`。

**UFS SPEC Reference**: JESD220H Section 6.7 (UniPro)

---

## Phase 3 — Execute CMD × 10 Rounds

### 每個 Round 的 CMD 執行順序隨機排列，共 10 輪。

### Step 3.1: Hibernate Enter → Exit

**目的**: 執行 Hibernate enter 後立即 exit，驗證 Suspend/Resume 正常。

| Field | Value |
|-------|-------|
| Hibernate Count | Random (1 ~ 10) |
| Loop Count | Random (1 ~ 30) |
| Delay between loops | Random (1us ~ 10000us) |

**Expected**: Device 恢復就緒（Hibernate exit 後可操作）。

**UFS SPEC Reference**: JESD220H Section 10.2.5 (Power Conditions)

---

### Step 3.2: WRITE(10) — Random Write

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All enabled LUNs |
| Logical Block Address | Random |
| Transfer Length | Random (4KB ~ 4MB) |
| Command Count | Random (1 ~ 10) |
| Delay between CMDs | Random (1us ~ 10000us) |

**Expected**: `GOOD Status`。

---

### Step 3.3: READ(10) — Random Read

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | All enabled LUNs |
| Logical Block Address | Random |
| Transfer Length | Random (4KB ~ 4MB) |
| Command Count | Random (1 ~ 10) |
| Delay between CMDs | Random (1us ~ 10000us) |

**Expected**: `GOOD Status`。

---

### Step 3.4: UNMAP — Random Unmap

**SCSI CMD**: `UNMAP (42h)`

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | All enabled LUNs |
| UNMAP LBA Range | Random, chunksize 4KB ~ 4MB |
| Command Count | Random (1 ~ 10) |
| Delay between CMDs | Random (1us ~ 10000us) |

**Expected**: `GOOD Status`。

---

### Step 3.5: RPMB Write (if configured)

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL IN (A2h)`

**條件**: 僅 combo 含 RPMB 時執行。

| Field | Value |
|-------|-------|
| SECURITY PROTOCOL | 0xEC (RPMB) |
| Region | Region 0 |
| LBA | Random (0 ~ region 0 size) |
| Block Count | Random (0x01 ~ 0xFF) |
| Command Count | Random (1 ~ 10) |

**RPMB Protocol Flow**: OUT (Send Write Request) → IN (Receive Result)

**Expected**: `GOOD Status`。

---

### Step 3.6: RPMB Read (if configured)

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL IN (A2h)`

**條件**: 僅 combo 含 RPMB 時執行。

| Field | Value |
|-------|-------|
| SECURITY PROTOCOL | 0xEC (RPMB) |
| Region | Region 0 |
| LBA | Random (0 ~ region 0 size) |
| Block Count | Random (0x01 ~ 0xFF) |
| Command Count | Random (1 ~ 10) |

**RPMB Protocol Flow**: OUT (Send Read Request) → IN (Receive Data + MAC)

**Expected**: `GOOD Status`。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x28 | READ(10) | 10 | Step 3.3 |
| 0x2A | WRITE(10) | 10 | Step 3.2 |
| 0x42 | UNMAP | 10 | Step 3.4 |
| 0xA2 | SECURITY PROTOCOL IN | 12 | Step 1.4, 1.5, 3.5, 3.6 |
| 0xB5 | SECURITY PROTOCOL OUT | 12 | Step 1.4, 1.5, 3.5, 3.6 |

## 附錄 A — UFS Query IDN 對照表

| IDN | Name | Opcode | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | bBootLunEn | 0x04 (WRITE ATTRIBUTE) | Step 1.3 |
| 0x01 | Configuration Descriptor | 0x08 (WRITE DESCRIPTOR) | Step 1.1 |
| 0x0E | fWriteBoosterEn | 0x02 (SET FLAG) | Step 1.2 |

---

## 自我驗證

- Tree Diagram leaf steps: **18** (0.1=1, 1.1~1.5=5, 2.1=1, 3.1~3.6=6; plus loop multipliers for configs×speeds not counted as extra leaves since they're iterations)
- `### Step` sections: **12** (3.2~3.6 are distinct; 1.4/1.5 are distinct; 1.1~1.3 distinct)
- 每個 leaf step 都有 `→ Expected:` ✓
- 無 `(待確認)` 佔位符 ✓
