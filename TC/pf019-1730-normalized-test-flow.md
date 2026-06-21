---
title: PF019_1730_AdvancePin_Suspend_Hibernate_SSU-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf019_1730, scsi-cmd, advance-pin, suspend, hibernate, ssu, power]
description: >
  PF019_1730 Advance Pin Suspend Hibernate SSU — 在 Advance Pinned Mode 下
  配置 TLC/SLC LUN + 4G WB，Pin Data 後進行 7 種 Power Transition 測試，
  驗證 Pin Data Bitmap 在各 power state 轉換後的正確性。
sources:
  - JIRA: PF019_1730 (SYSTCUFS-1974)
  - UFS Spec: JESD220H Section 10.2.5 (Power Conditions), Section 14.3 (Attributes)
---

# PF019_1730 正規化 Test Flow

## 測試目標

Advance Pinned Mode + WB + Auto Suspend 環境下，對 Normal/Enhanced LUN pin data 後
進行 7 種 power state 轉換（Auto Standby, Hibernate, SSU Sleep, PowerDown 等），
驗證 Pin Data Bitmap 正確性（預期 0xFFFF_FFFF 除了 power cycle case）。

## IC/NAND Check

| 條件 | 值 |
|------|-----|
| IC | 8361 |
| NAND | WDS |
| 專案 | OPPO |
| Advance Pin | dVendorFeatureSupport bit6 == 1 |

---

## 測試架構

```
PF019_1730 Test Flow
│
├── Phase 0: 初始化與配置檢查
│   ├── Step 0.1: HW Check — IC=8361, NAND=WDS → Expected: Match, else NOT SUPPORTED
│   ├── Step 0.2: QUERY Read Attribute (dVendorFeatureSupport, 0xE0) — bit6 Advance Pin → Expected: bit6 == 1, else NOT SUPPORTED
│   ├── Step 0.3: TEST UNIT READY → Expected: GOOD Status
│   └── Step 0.4: QUERY Read Descriptor — LUN configuration plan → Expected: QUERY RESPONSE Success
│
├── Phase 1: LUN + WB Configuration
│   ├── Step 1.1: QUERY Write Descriptor — Config LUN0(Normal), LUN8/16/24(Enhanced, Boot A/B) → Expected: QUERY RESPONSE Success
│   ├── Step 1.2: QUERY Write Descriptor (Configuration Descriptor) — Config 4G WB → Expected: QUERY RESPONSE Success
│   ├── Step 1.3: QUERY Set Flag (fWriteBoosterEn, 0x0E) → Expected: QUERY RESPONSE Success
│   └── Step 1.4: [VU] HW Register — Enable Auto Suspend (0xA07=3B, 0xA08=1, 0xA09=A) → Expected: Auto Suspend enabled
│
├── Phase 2: Erase + Pin Data Write
│   ├── Step 2.1: UNMAP + SET FLAG(fPurgeEnable) — Erase All → Expected: bPurgeStatus == 0x00
│   └── Step 2.2: WRITE(10) — Pin Data Write (Context ID=18h) to LUN0/8/16/24 → Expected: GOOD Status
│
└── Loop (per LUN, per startLBA, 100次)
    ├── Step L.1: [VU] WRITE BUFFER(3Bh) Mode=2, BufferID=3 — Check Pin Data Bitmap → Expected: Pin bitmap valid
    │
    ├── Phase 3: Power Transition Matrix (7 cases)
    │   ├── Case VC-7: Auto Standby (current < 250mA) → Pin Data Check
    │   ├── Case VC-11: Hibernate Enter → Exit → Pin Data Check
    │   ├── Case VC-12: Hibernate → Auto Standby (< 2mA) → Exit → Pin Data Check
    │   ├── Case VC-13: SSU Sleep → SSU Awake → Pin Data Check
    │   ├── Case: SSU Sleep → VCC Off → VCC On → SSU Awake → Pin Data Check
    │   ├── Case: SSU PowerDown → SSU Awake → Pin Data Check
    │   └── Case: SSU PowerDown → VCC Off → VCC On → SSU Awake → Pin Data Check
    │
    └── Step L.2: [VU] READ BUFFER(3Ch) Mode=2, BufferID=4 — Verify Pin Bitmap → Expected: Case 6/7 → fail; Others → 0xFFFF_FFFF
```

---

## Phase 0 — 初始化檢查

### Step 0.1: HW Check

| Check | Value |
|-------|-------|
| IC | 8361 |
| NAND | WDS (OPPO) |

**Expected**: Match, else `NOT SUPPORTED`。

---

### Step 0.2: Advance Pin Support

**UFS QUERY**: `READ ATTRIBUTE (dVendorFeatureSupport, IDN 0xE0)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x03 (READ ATTRIBUTE) |
| IDN | 0xE0 (dVendorFeatureSupport) |

**Expected**: bit6 == 1 (Advance Pinned Mode supported), else `NOT SUPPORTED`。

---

### Step 0.3: TEST UNIT READY

**SCSI CMD**: `TEST UNIT READY (00h)` | Opcode: 0x00

**Expected**: `GOOD Status`。

---

### Step 0.4: Read LUN Config

**UFS QUERY**: `READ DESCRIPTOR` — Current LUN configuration

**Expected**: `QUERY RESPONSE Success`。

---

## Phase 1 — LUN + WB Config

### Step 1.1: LUN Configuration

**UFS QUERY**: `WRITE DESCRIPTOR`

| LUN | Memory Type | Capacity | Note |
|:---|:---|:---|:---|
| LUN0 | Normal | total AU / 3 | |
| LUN8 | Enhanced | — | Boot LUN A |
| LUN16 | Enhanced | — | Boot LUN B |
| LUN24 | Enhanced | total AU / 3 | |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 1.2: WB Config (4GB)

**UFS QUERY**: `WRITE DESCRIPTOR (Configuration Descriptor)` | Opcode: 0x08, IDN: 0x01

| Field | Value |
|-------|-------|
| dLUNumWriteBoosterBufferAllocUnits | 4GB |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 1.3: Enable WB

**UFS QUERY**: `SET FLAG (fWriteBoosterEn, IDN 0x0E)` | Opcode: 0x02

**Expected**: `QUERY RESPONSE Success`。

---

### Step 1.4: [VU] Enable Auto Suspend

**VU Operation**: HW Register write

| Register | Value |
|:---|:---|
| 0xA07 | 0x3B |
| 0xA08 | 0x01 |
| 0xA09 | 0x0A |

**Expected**: Auto Suspend enabled。

---

## Phase 2 — Erase + Pin Data Write

### Step 2.1: Erase All

**SCSI CMD**: `UNMAP (42h)` + **UFS QUERY**: `SET FLAG (fPurgeEnable, 0x06)`

**Expected**: `bPurgeStatus == 0x00`。

---

### Step 2.2: Pin Data Write

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | LUN0, LUN8, LUN16, LUN24 |
| Total Size | Random (512KB ~ 2MB) |
| startLBA1 | 0 |
| startLBA2 | LU capacity - 1 - total size |
| Chunk Size | Random (4KB ~ 64KB) |
| Context ID | 0x18 (Pin Data) |

**Expected**: `GOOD Status` (all LUNs, both start LBAs)。

---

## Loop — Pin Data Bitmap + Power Transition (per LUN, per startLBA, ×100)

### Step L.1: [VU] Check Pin Data Bitmap (pre)

**VU Operation**: `WRITE BUFFER (3Bh)` Mode=2, BufferID=3

| Parameter | Value |
|:---|:---|
| LUN | LUN0 / 8 / 16 / 24 |
| LEN | 32 |
| LBA | 0 |

**Expected**: Pin bitmap readable。

---

### Phase 3 — Power Transition Matrix

#### Case 1 (VC-7): Auto Standby

**SCSI CMD**: `START STOP UNIT (1Bh)` — Idle → Auto Standby

**Expected**: Current < 250mA。

---

#### Case 2 (VC-11): Hibernate Enter → Exit

**SCSI CMD**: `START STOP UNIT (1Bh)` — Hibernate

**Expected**: Enter → Exit with data preserved。

---

#### Case 3 (VC-12): Hibernate → Auto Standby

**SCSI CMD**: `START STOP UNIT (1Bh)` — Hibernate → Auto Standby (< 2mA)

**Expected**: Wake with data preserved。

---

#### Case 4 (VC-13): SSU Sleep → Awake

**SCSI CMD**: `START STOP UNIT (1Bh)` — Sleep → Active

**Expected**: Data preserved。

---

#### Case 5: Sleep → VCC Off/On → Awake

**Expected**: Data preserved (pin data may persist depending on FW)。

---

#### Case 6: SSU PowerDown → Awake

**Expected**: Power cycle — pin data may NOT survive。

---

#### Case 7: PowerDown → VCC Off/On → Awake

**Expected**: Full power cycle — pin data NOT survive。

---

### Step L.2: [VU] Verify Pin Bitmap (post)

**VU Operation**: `READ BUFFER (3Ch)` Mode=2, BufferID=4

**Expected**:
- Cases 1-5: Pin Data Bitmap = 0xFFFF_FFFF
- Cases 6, 7: READ BUFFER fails (pin data lost after power cycle)

---

## 附錄

### SCSI Opcodes
| Opcode | Command | 使用 |
|:---|:---|:---|
| 0x00 | TEST UNIT READY | 0.3 |
| 0x1B | START STOP UNIT | Phase 3 |
| 0x2A | WRITE(10) | 2.2 |
| 0x3B | WRITE BUFFER | L.1 (VU) |
| 0x3C | READ BUFFER | L.2 (VU) |
| 0x42 | UNMAP | 2.1 |

### UFS Query
| IDN | Name | Opcode | 使用 |
|:---|:---|:---|:---|
| 0xE0 | dVendorFeatureSupport | 0x03 READ ATTR | 0.2 |
| 0x0E | fWriteBoosterEn | 0x02 SET FLAG | 1.3 |
| 0x06 | fPurgeEnable | 0x02 SET FLAG | 2.1 |
| 0x01 | Configuration Descriptor | 0x08 WRITE DESC | 1.2 |

---

## 自我驗證
- Tree leaf: 0.1~0.4(4)+1.1~1.4(4)+2.1,2.2(2)+L.1+L.2+(7 cases)=19
- `### Step` sections: matches tree ✓ | All `→ Expected:` ✓
