---
title: PF021_1649_SSU_Sleep_PowerDown_CMD-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf021_1649, scsi-cmd, power-state, well-known-lun, sleep, powerdown]
description: >
  PF021_1649 Issue SCSI Under SSU Sleep/PowerDown Test — 驗證在 Sleep/PowerDown 狀態下
  對 LUN0~31 及所有 Well-Known LUN 發出 30 種 SCSI 命令的回應正確性。
sources:
  - JIRA: PF021_1649 (SYSTCUFS-1921)
  - UFS Spec: JESD220H Section 7.4 (Power Modes), Table 10.59 (Well Known LU)
---

# PF021_1649 正規化 Test Flow（SCSI CMD 単位）

## 測試目標

驗證在 Sleep 與 PowerDown 狀態下，對 LUN0~31 及所有 Well-Known LUN 發出 30 種 SCSI 命令，
確認回應符合 SPEC 定義。

## 測試架構（Tree Diagram — 含 Expected）

```
PF021_1649 Test Flow
│
├── Phase 0: 初始化
│   ├── Step 0.1: Config LUNs — Boot LU A/B, Enhanced Memory → Expected: QUERY RESPONSE Success
│   ├── Step 0.2: WRITE ATTRIBUTE (bBootLunEn) → Expected: QUERY RESPONSE Success
│   ├── Step 0.3: SECURITY PROTOCOL OUT→OUT→IN — RPMB Key Programming → Expected: GOOD Status
│   └── Step 0.4: SECURITY PROTOCOL OUT→IN — RPMB Read Counter → Expected: GOOD Status, valid counter
│
└── Loop (Sleep / PowerDown)
    ├── Step P.1: START STOP UNIT — Enter Sleep/PowerDown → Expected: GOOD Status
    ├── Step T.1~T.30: Issue SCSI CMD × 30 per LUN → Expected: Per table below
    └── Step P.2: START STOP UNIT — SSU Active (recovery) → Expected: GOOD Status
```

---

## Phase 0 — 初始化

### Step 0.1: Config LUNs

**UFS QUERY**: `WRITE DESCRIPTOR (Configuration Descriptor)`

**目的**: 設定 Boot LU A/B 及 Enhanced Memory。

| Field | Value |
|-------|-------|
| Query Opcode | 0x08 (WRITE DESCRIPTOR) |
| Descriptor IDN | 0x01 (Configuration Descriptor) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.2: Enable Boot LUN

**UFS QUERY**: `WRITE ATTRIBUTE (bBootLunEn, IDN 0x00)`

| Field | Value |
|-------|-------|
| Query Opcode | 0x04 (WRITE ATTRIBUTE) |
| Attribute IDN | 0x00 (bBootLunEn) |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.3: RPMB Key Programming

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL IN (A2h)`

| Field | Value |
|-------|-------|
| SECURITY PROTOCOL | 0xEC (RPMB) |
| Operation | Authentication Key Programming |

**Expected**: `GOOD Status`，RPMB Key programmed。

---

### Step 0.4: RPMB Read Counter

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL IN (A2h)`

| Field | Value |
|-------|-------|
| SECURITY PROTOCOL | 0xEC (RPMB) |
| Operation | Read Write Counter |

**Expected**: `GOOD Status`，valid counter。

---

## Loop — Sleep / PowerDown

### Step P.1: Enter Power State

**SCSI CMD**: `START STOP UNIT (1Bh)`

| Field | Sleep | PowerDown |
|:---|:---|:---|
| Opcode | 0x1B | 0x1B |
| START | 0 | 0 |
| POWER CONDITION | 0x02 | 0x03 |

**Expected**: `GOOD Status`。

---

### Steps T.1~T.30: 30 SCSI Commands Per LUN

對 **LUN0~31** 及 **所有 Well-Known LUN**（REPORT LUNS / BOOT / RPMB / Device）逐一測試 30 種 SCSI CMD。

| # | SCSI CMD | Opcode | LUN0~31 Expected | WK LUN Expected |
|:--|:---|:---|:---|:---|
| 1 | INQUIRY | 0x12 | CHECK_CONDITION, NOT_READY(02h), INITIALIZING_CMD_REQUIRED(0402h) | per Table 10.59 |
| 2 | MODE SELECT(10) | 0x55 | 同上 | 同上 |
| 3 | MODE SENSE(10) | 0x5A | 同上 | 同上 |
| 4 | READ(6) | 0x08 | 同上 | 同上 |
| 5 | READ(10) | 0x28 | 同上 | 同上 |
| 6 | READ(16) | 0x88 | 同上（若支援） | 同上 |
| 7 | READ CAPACITY(10) | 0x25 | 同上 | 同上 |
| 8 | READ CAPACITY(16) | 0x9E | 同上 | 同上 |
| 9 | START STOP UNIT | 0x1B | ILLEGAL_REQUEST(05h), INVALID_FIELD_IN_CDB(24h) | Device WK: GOOD |
| 10 | TEST UNIT READY | 0x00 | NOT_READY(02h) | per Table 10.59 |
| 11 | REPORT LUNS | 0xA0 | CHECK_CONDITION | per Table 10.59 |
| 12 | VERIFY(10) | 0x2F | NOT_READY(02h) | 同上 |
| 13 | WRITE(6) | 0x0A | 同上 | 同上 |
| 14 | WRITE(10) | 0x2A | 同上 | 同上 |
| 15 | WRITE(16) | 0x8A | 同上（若支援） | 同上 |
| 16 | REQUEST SENSE | 0x03 | GOOD | GOOD |
| 17 | FORMAT UNIT | 0x04 | NOT_READY(02h) | per Table 10.59 |
| 18 | PRE-FETCH(10) | 0x34 | 同上 | 同上 |
| 19 | PRE-FETCH(16) | 0x90 | 同上（若支援） | 同上 |
| 20 | SECURITY PROTOCOL IN | 0xA2 | 同上 | 同上 |
| 21 | SECURITY PROTOCOL OUT | 0xB5 | 同上 | 同上 |
| 22 | SEND DIAGNOSTIC | 0x1D | 同上 | 同上 |
| 23 | SYNC CACHE(10) | 0x35 | 同上 | 同上 |
| 24 | SYNC CACHE(16) | 0x91 | 同上（若支援） | 同上 |
| 25 | UNMAP | 0x42 | 同上 | 同上 |
| 26 | READ BUFFER | 0x3C | 同上 | 同上 |
| 27 | WRITE BUFFER | 0x3B | 同上 | 同上 |
| 28 | (FBarrier) | — | 同上 | 同上 |
| 29 | START STOP UNIT (start=0) | 0x1B | NOT_READY(02h) | per Table 10.59 |
| 30 | START STOP UNIT (start=1) | 0x1B | NOT_READY(02h) | 同上 |

> **SSU 特殊處理**: LUN0~31 → CHECK_CONDITION + ILLEGAL_REQUEST; REPORT LUNS/BOOT/RPMB WK → CHECK_CONDITION; Device WK → GOOD。

---

### Step P.2: Recovery to Active

**SCSI CMD**: `START STOP UNIT (1Bh)`

| Field | Value |
|-------|-------|
| Opcode | 0x1B |
| START | 1 |
| POWER CONDITION | 0x01 (Active) |

**Expected**: `GOOD Status`。

---

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size |
|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 |
| 0x03 | REQUEST SENSE | 6 |
| 0x04 | FORMAT UNIT | 6 |
| 0x08 | READ(6) | 6 |
| 0x0A | WRITE(6) | 6 |
| 0x12 | INQUIRY | 6 |
| 0x1B | START STOP UNIT | 6 |
| 0x1D | SEND DIAGNOSTIC | 6 |
| 0x25 | READ CAPACITY(10) | 10 |
| 0x28 | READ(10) | 10 |
| 0x2A | WRITE(10) | 10 |
| 0x2F | VERIFY(10) | 10 |
| 0x34 | PRE-FETCH(10) | 10 |
| 0x35 | SYNC CACHE(10) | 10 |
| 0x3B | WRITE BUFFER | 10 |
| 0x3C | READ BUFFER | 10 |
| 0x42 | UNMAP | 10 |
| 0x55 | MODE SELECT(10) | 10 |
| 0x5A | MODE SENSE(10) | 10 |
| 0x88 | READ(16) | 16 |
| 0x8A | WRITE(16) | 16 |
| 0x90 | PRE-FETCH(16) | 16 |
| 0x91 | SYNC CACHE(16) | 16 |
| 0x9E | READ CAPACITY(16) | 16 |
| 0xA0 | REPORT LUNS | 12 |
| 0xA2 | SECURITY PROTOCOL IN | 12 |
| 0xB5 | SECURITY PROTOCOL OUT | 12 |

---

## 自我驗證

- Tree Diagram leaf steps: **6 main steps** (0.1~0.4=4, P.1, P.2) + 30 CMD sub-steps per LUN
- `### Step` sections: **7** (Phase 0:4, Loop: P.1, T.1~T.30 table, P.2) ✓
- 每個 leaf step 都有 `→ Expected:` ✓
