---
title: PF017_0938_FlushNAND_WriteAbort-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf017_0938, scsi-cmd, abort, rpmb, boot-lun, spor, flush]
description: >
  PF017_0938 Flush NAND Write Abort — 對 Normal LUN / Boot LUN / RPMB LUN
  在 last RTT 後發送 Abort，SPOR 後驗證 FUA=1 資料完整性。
sources:
  - JIRA: PF017_0938 (SYSTCUFS-1201)
  - UFS Spec: JESD220H Section 10.7.3 (ABORT TASK), Section 11.7 (RPMB), Section 13.4.4 (Boot)
---

# PF017_0938 正規化 Test Flow

## 測試目標

在 Flush NAND Write 期間，對三種 LUN 類型（Normal / Boot / RPMB）
在 last RTT 後發送 Abort，SPOR 後驗證 FUA=1 的資料已成功寫入 NAND。

## IC/NAND Check

| 條件 | 值 |
|------|-----|
| IC | Micron 8325 |
| NAND | N58R |
| UFS Version | UFS 3.1 |

---

## 測試架構

```
PF017_0938 Test Flow
│
├── Phase 0: 初始化與配置
│   ├── Step 0.1: HW Check — IC=8325, NAND=N58R, UFS3.1 → Expected: Match, else NOT SUPPORTED
│   ├── Step 0.2: TEST UNIT READY → Expected: GOOD Status
│   ├── Step 0.3: RPMB Config — 4 regions (R0=remaining, R1/R2/R3=128KB) → Expected: QUERY RESPONSE Success
│   ├── Step 0.4: RPMB Key Programming (OUT→OUT→IN) — All 4 regions → Expected: Key Programmed
│   ├── Step 0.5: QUERY Write Attribute (bBootLunEn) — Enable Boot LUN A (LUN1) → Expected: QUERY RESPONSE Success
│   └── Step 0.6: UNMAP + SET FLAG(fPurgeEnable) — Erase All → Expected: bPurgeStatus == 0x00
│
├── Phase 1: Normal LUN Abort Test
│   ├── Step 1.1: WRITE(10) FUA=1 — LUN0, 64KB, LBA random, last RTT trigger → Expected: Write started
│   ├── Step 1.2: ABORT TASK — Send abort after last RTT → Expected: Abort accepted
│   ├── Step 1.3: SPOR → Expected: Reset device success
│   └── Step 1.4: READ(10) + Compare — Verify FUA data → Expected: GOOD Status, Data Match (FUA committed)
│
├── Phase 2: Boot LUN Abort Test
│   ├── Step 2.1: WRITE(10) FUA=1 — LUN1(Boot), 64KB, last RTT → Expected: Write started
│   ├── Step 2.2: ABORT TASK → Expected: Abort accepted
│   ├── Step 2.3: SPOR → Expected: Reset device success
│   └── Step 2.4: READ(10) + Compare → Expected: GOOD Status, Data Match
│
└── Phase 3: RPMB LUN Abort Test
    ├── Step 3.1: SECURITY PROTOCOL OUT (B5h) — RPMB Write, Region0, last RTT → Expected: Write started
    ├── Step 3.2: ABORT TASK → Expected: Abort accepted
    ├── Step 3.3: SPOR → Expected: Reset device success
    └── Step 3.4: SECURITY PROTOCOL OUT+IN — RPMB Read + Compare → Expected: GOOD Status, Data Match
```

---

## Phase 0 — 初始化

### Step 0.1: HW Check

| Check | Value |
|-------|-------|
| IC | Micron 8325 |
| NAND | N58R |
| UFS | 3.1 |

**Expected**: Match, else `NOT SUPPORTED`。

---

### Step 0.2: TEST UNIT READY

**SCSI CMD**: `TEST UNIT READY (00h)` | Opcode: 0x00

**Expected**: `GOOD Status`。

---

### Step 0.3: RPMB Region Config

**UFS QUERY**: `WRITE DESCRIPTOR`

| Region | Size |
|:---|:---|
| Region 0 | Remaining capacity |
| Region 1 | 128 KB |
| Region 2 | 128 KB |
| Region 3 | 128 KB |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 0.4: RPMB Key Programming

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL IN (A2h)`

**Expected**: Key Programmed for all 4 regions。

**UFS SPEC**: JESD220H Section 11.7.4.2

---

### Step 0.5: Enable Boot LUN

**UFS QUERY**: `WRITE ATTRIBUTE (bBootLunEn, IDN 0x00)` | Opcode: 0x04

**Expected**: Boot LUN A (LUN1) enabled。

---

### Step 0.6: Erase All

**SCSI CMD**: `UNMAP (42h)` + **UFS QUERY**: `SET FLAG (fPurgeEnable, 0x06)`

**Expected**: `bPurgeStatus == 0x00`。

---

## Phase 1 — Normal LUN Abort

### Step 1.1: Write with FUA=1 (Normal LUN)

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 (Normal) |
| LBA | Random |
| Chunk | 64KB |
| FUA | 1 |
| RTT Trigger | DCMD1 set RTT cnt = last RTT |

**Expected**: Write started, RTT triggered。

---

### Step 1.2: ABORT TASK

**TMF**: `ABORT TASK` — Send after last RTT

**Expected**: Abort accepted by device。

**UFS SPEC**: JESD220H Section 10.7.3

---

### Step 1.3: SPOR

**Expected**: `fDeviceInit == 1`。**UFS SPEC**: JESD220H 13.4.12

---

### Step 1.4: Read Compare FUA Data

**SCSI CMD**: `READ(10) (28h)` | Opcode: 0x28

| Field | Value |
|-------|-------|
| LUN/LBA/Length | 同 Step 1.1 |

**Expected**: `GOOD Status`, `Data Match`（FUA=1 資料已落 NAND）。

---

## Phase 2 — Boot LUN Abort

（結構同 Phase 1，LUN 改為 LUN1/Boot LUN A）

### Step 2.1: WRITE(10) FUA=1 — LUN1

### Step 2.2: ABORT TASK

### Step 2.3: SPOR

### Step 2.4: READ(10) + Compare

---

## Phase 3 — RPMB LUN Abort

### Step 3.1: RPMB Write

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)`

| Field | Value |
|-------|-------|
| Opcode | 0xB5 |
| SECURITY PROTOCOL | 0x01 (RPMB) |
| SPECIFIC | 0x0003 (Auth Data Write) |
| LUN | 0xC4 (WK_RPMB) |
| Region | Region 0 |
| BlockCount | b23_RPMB_ReadWriteSize |
| Start Addr | Random |
| RTT Trigger | last RTT |

**Expected**: Write started。

---

### Step 3.2: ABORT TASK

**Expected**: Abort accepted。

---

### Step 3.3: SPOR

**Expected**: `fDeviceInit == 1`。

---

### Step 3.4: RPMB Read Compare

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL IN (A2h)`

| SPECIFIC (OUT) | 0x0002 (Auth Data Read) |

**Expected**: Data Match。

---

## 附錄

### SCSI Opcodes
| Opcode | Command | 使用 |
|:---|:---|:---|
| 0x00 | TEST UNIT READY | 0.2 |
| 0x28 | READ(10) | 1.4, 2.4 |
| 0x2A | WRITE(10) | 1.1, 2.1 |
| 0x42 | UNMAP | 0.6 |
| 0xA2 | SEC PROTOCOL IN | 0.4, 3.4 |
| 0xB5 | SEC PROTOCOL OUT | 0.4, 3.1, 3.4 |

### UFS Query
| IDN | Name | Opcode | 使用 |
|:---|:---|:---|:---|
| 0x00 | bBootLunEn | 0x04 WRITE ATTR | 0.5 |
| 0x06 | fPurgeEnable | 0x02 SET FLAG | 0.6 |

---

## 自我驗證
- Tree leaf: 0.1~0.6(6)+1.1~1.4(4)+2.1~2.4(4)+3.1~3.4(4)=18
- `### Step`: Phase 2 共用結構描述；核心 section 18 ✓ | All `→ Expected:` ✓
