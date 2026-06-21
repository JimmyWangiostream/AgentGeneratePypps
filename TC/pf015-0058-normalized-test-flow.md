---
title: PF015_0058_RandomSpeedChange-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf015_0058, scsi-cmd, unipro, speed-change, gear]
description: >
  PF015_0058 Random Speed Change Test — 隨機切換 UniPro HS/LS Gear/Lane 後
  進行 R/W 驗證資料完整性。
sources:
  - JIRA: PF015_0058 (SYSTCUFS-208)
  - UFS Spec: JESD220H Section 9.0 (UniPro), Section 10.4 (Link)
---

# PF015_0058 正規化 Test Flow

## 測試目標

隨機切換 UniPro Speed Mode (HS/LS, Gear 1~7, 1/2 lane, Rate A/B)，
在每次切換後進行 R/W 比對，驗證資料不受 Speed Change 影響。

## 測試架構

```
PF015_0058 Test Flow
│
├── Phase 0: 初始化
│   ├── Step 0.1: TEST UNIT READY → Expected: GOOD Status
│   └── Step 0.2: READ CAPACITY(10) → Expected: GOOD Status
│
└── Loop (burn_in_loop)
    ├── Step L.1: [VU] DME_SET / DME_POWERMODE — Random Speed Change (HS/LS, Gear1~7, 1/2 lane, Rate A/B) → Expected: Speed Change Success
    ├── Step L.2: WRITE(10) — Random Write → Expected: GOOD Status
    ├── Step L.3: READ(10) + Compare → Expected: GOOD Status, Data Match
    └── Step L.4: WRITE(10) + READ(10) — Additional Verify → Expected: GOOD Status, Data Match
```

---

## Phase 0 — 初始化

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)` | Opcode: 0x00

**Expected**: `GOOD Status`。

---

### Step 0.2: 取得 LUN 容量

**SCSI CMD**: `READ CAPACITY(10) (25h)` | Opcode: 0x25

**Expected**: `GOOD Status`。

---

## Loop — Speed Change + R/W

### Step L.1: Random Speed Change

**VU Operation**: DME_SET / DME_POWERMODE 動態變更 UniPro 參數。

| Parameter | Random Value |
|:---|:---|
| Mode | HS (High-Speed) / LS (Low-Speed) |
| Gear | 1, 2, 3, 4, 5, 6, 7 |
| Lane | 1-Lane / 2-Lane |
| Rate | Rate_A / Rate_B |

**Expected**: Speed Change 成功，Link 穩定。

**UFS SPEC Reference**: JESD220H Section 9.0, Section 10.4

---

### Step L.2: Random Write

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | Random |
| LBA | Random |
| Length | Random |

**Expected**: `GOOD Status`。

---

### Step L.3: Read Compare

**SCSI CMD**: `READ(10) (28h)` | Opcode: 0x28

**Expected**: `GOOD Status`, `Data Match`。

---

### Step L.4: Additional Verify

**SCSI CMD**: `WRITE(10) (2Ah)` + `READ(10) (28h)` — 不同 LBA

**Expected**: `GOOD Status`, `Data Match`。

---

## 附錄

### SCSI Opcodes
| Opcode | Command | 使用 |
|:---|:---|:---|
| 0x00 | TEST UNIT READY | 0.1 |
| 0x25 | READ CAPACITY(10) | 0.2 |
| 0x28 | READ(10) | L.3, L.4 |
| 0x2A | WRITE(10) | L.2, L.4 |

### UniPro Speed Parameters
| Parameter | Values |
|:---|:---|
| Mode | HS (Gear 1~7), LS (Gear 1~4) |
| Lane | 1-Lane, 2-Lane |
| Rate | Rate_A, Rate_B |

---

## 自我驗證
- Tree leaf: 0.1,0.2(2)+L.1~L.4(4)=6 | `### Step`: 6 ✓ | All `→ Expected:` ✓
