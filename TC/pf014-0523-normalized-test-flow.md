---
title: PF014_0523_FourRegion_RPMB_CounterExpired-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf014_0523, scsi-cmd, rpmb, counter-expired, security-protocol]
description: >
  PF014_0523 Four Region RPMB Counter Expired Test — 配置 4 個 RPMB Region，
  驗證 Write Counter 在接近上限 (0xFFFFFFFE/0xFFFFFFFF) 時的各種 expired 行為：
  Random Write/Read、Wrong Counter、Wrong Key、Out-of-Range。
sources:
  - JIRA: PF014_0523 (SYSTCUFS-675)
  - UFS Spec: JESD220H Section 11.7 (RPMB), Section 10.7.2 (SECURITY PROTOCOL IN/OUT)
---

# PF014_0523 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

RPMB 4 Region 的 Write Counter Expired 驗證：當 counter 達到 0xFFFFFFFE/0xFFFFFFFF 時，
所有 RPMB Write 操作應回 expired，Read 操作不受 counter 影響（除 counter read 本身）。

## HW 版本檢查

| 條件 | 值 |
|------|-----|
| UFS Version | H&M 特規 2.1 / 3.0 / 3.1 |
| 不支援時 | `NOT SUPPORTED` |

## RPMB Protocol 提醒

| Operation | Pattern | Steps |
|:---|:---|:---|
| Auth Key Programming | OUT → OUT → IN | 3 steps |
| Auth Data Write | OUT → IN | 2 steps |
| Auth Data Read | OUT → IN | 2 steps |
| Read Write Counter | OUT → IN | 2 steps |

---

## 測試架構

```
PF014_0523 Test Flow
│
├── Phase 0: 初始化與版本檢查
│   ├── Step 0.1: TEST UNIT READY → Expected: GOOD Status
│   └── Step 0.2: HW Check — UFS版本=H&M 2.1/3.0/3.1 → Expected: 版本符合,否則 NOT SUPPORTED
│
├── Phase 1: RPMB Region 配置 (Region 0:13M, Region 1/2/3:1M)
│   ├── Step 1.1: QUERY Read Descriptor — 確認 RPMB Unit Descriptor → Expected: QUERY RESPONSE Success
│   ├── Step 1.2: QUERY Write Descriptor — Config RPMB Region Size → Expected: QUERY RESPONSE Success
│   ├── Step 1.3: QUERY Read Descriptor — Verify config → Expected: Region sizes correct
│   └── Step 1.4: Repeat Step 1.2~1.3 for all 4 regions → Expected: All 4 regions configured
│
└── Loop (per RPMB Region, 4次)
    │
    ├── Phase 2: RPMB Key Programming
    │   ├── Step 2.1: SECURITY PROTOCOL OUT (A2h) — Send Key (OUT 1/2) → Expected: GOOD Status
    │   ├── Step 2.2: SECURITY PROTOCOL OUT (A2h) — Request Result (OUT 2/2) → Expected: GOOD Status
    │   └── Step 2.3: SECURITY PROTOCOL IN (B5h) — Receive Result → Expected: GOOD Status, Key Programmed
    │
    ├── Phase 3: Set Write-Counter = 0xFFFFFFFE
    │   ├── Step 3.1: [VU] Clear RPMB Key + Set Counter = 0xFFFFFFFE → Expected: Counter set
    │   └── Step 3.2: SECURITY PROTOCOL OUT + IN — Read Write Counter → Expected: Counter == 0xFFFFFFFE
    │
    ├── Phase 4: Counter-Expired 驗證 (0xFFFFFFFE)
    │   ├── Step 4.1: SECURITY PROTOCOL OUT + IN — Random RPMB Write → Expected: Write-Counter-Expired, NOT written
    │   ├── Step 4.2: SECURITY PROTOCOL OUT + IN — Read Write Counter → Expected: Counter == 0xFFFFFFFF (expired)
    │   ├── Step 4.3: SECURITY PROTOCOL OUT + IN — Random RPMB Write → Expected: Write-Fail-Counter-Expired
    │   ├── Step 4.4: SECURITY PROTOCOL OUT + IN — Write with Wrong Counter → Expected: Write-Counter-Expired
    │   ├── Step 4.5: SECURITY PROTOCOL OUT + IN — Write with Wrong Key → Expected: Write-Counter-Expired
    │   ├── Step 4.6: SECURITY PROTOCOL OUT + IN — Write Out-of-Range Addr → Expected: Write-Counter-Expired
    │   ├── Step 4.7: SECURITY PROTOCOL OUT + IN — Random RPMB Read → Expected: Read success (read unaffected by counter)
    │   └── Step 4.8: SECURITY PROTOCOL OUT + IN — Read Out-of-Range Addr → Expected: Address-Out-of-Range
    │
    └── Phase 5: Next Region → Loop back to Phase 2
```

---

## Phase 0 — 初始化

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)` | Opcode: 0x00

**Expected**: `GOOD Status`。

---

### Step 0.2: HW Version Check

| Check | Value |
|-------|-------|
| UFS Version | H&M 2.1 / 3.0 / 3.1 |

**Expected**: 版本符合，否則 `NOT SUPPORTED`。

---

## Phase 1 — RPMB Region 配置

### Step 1.1: Read Unit Descriptor

**UFS QUERY**: `READ DESCRIPTOR (Unit Descriptor)` | Opcode: 0x07, IDN: 0x02

**Expected**: `QUERY RESPONSE Success`，確認 RPMB LUN 存在。

---

### Step 1.2: Config RPMB Region Size

**UFS QUERY**: `WRITE DESCRIPTOR` — Set RPMB Region size

| Region | Size |
|:---|:---|
| Region 0 | 13MB (remaining) |
| Region 1 | 1MB |
| Region 2 | 1MB |
| Region 3 | 1MB |

**Expected**: `QUERY RESPONSE Success`。

---

### Step 1.3/1.4: Verify + Repeat

**UFS QUERY**: `READ DESCRIPTOR` — Verify config

**Expected**: All 4 regions configured correctly。

---

## Phase 2 — RPMB Key Programming (per Region)

### Step 2.1: Send Key (OUT 1/2)

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)`

| Field | Value |
|-------|-------|
| Opcode | 0xB5 |
| SECURITY PROTOCOL | 0x01 (RPMB) |
| SECURITY PROTOCOL SPECIFIC | 0x0001 (Auth Key Programming) |
| INC_512 | 0 |
| Transfer Length | 284 bytes (key frame) |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 11.7.4.2 (Auth Key Programming)

---

### Step 2.2: Request Result (OUT 2/2)

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)`

| Field | Value |
|-------|-------|
| Opcode | 0xB5 |
| SECURITY PROTOCOL | 0x01 |
| SECURITY PROTOCOL SPECIFIC | 0x0001 |
| Transfer Length | 0 (Result Request, no data out) |

**Expected**: `GOOD Status`。

---

### Step 2.3: Receive Result (IN)

**SCSI CMD**: `SECURITY PROTOCOL IN (A2h)`

| Field | Value |
|-------|-------|
| Opcode | 0xA2 |
| SECURITY PROTOCOL | 0x01 |
| SECURITY PROTOCOL SPECIFIC | 0x0001 |
| Transfer Length | Expected result frame |

**Expected**: `GOOD Status`, Key Programmed Success。

---

## Phase 3 — Set Counter to 0xFFFFFFFE

### Step 3.1: [VU] Set Counter

**VU Operation**: Clear RPMB Key + Set Write-Counter = 0xFFFFFFFE

**Expected**: Counter set to 0xFFFFFFFE。

---

### Step 3.2: Read Write Counter

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL IN (A2h)`

| Opcode (OUT) | 0xB5 |
| Opcode (IN) | 0xA2 |
| SECURITY PROTOCOL | 0x01 |
| SPECIFIC (OUT) | 0x0004 (Read Write Counter) |

**Expected**: Write Counter == 0xFFFFFFFE。

**UFS SPEC Reference**: JESD220H Section 11.7.4.4 (Read Write Counter)

---

## Phase 4 — Counter-Expired 驗證

### Step 4.1: Random RPMB Write

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL IN (A2h)`

| Field | Value |
|-------|-------|
| Opcode OUT | 0xB5 |
| Opcode IN | 0xA2 |
| SECURITY PROTOCOL SPECIFIC (OUT) | 0x0003 (Auth Data Write) |
| Data | Random data with correct counter |

**Expected**: Response = `Write-Counter-Expired`，Data NOT written。

---

### Step 4.2: Read Counter → 0xFFFFFFFF

**SCSI CMD**: `SECURITY PROTOCOL OUT + IN` — Read Write Counter

**Expected**: Counter == 0xFFFFFFFF (expired)。

---

### Step 4.3: RPMB Write at 0xFFFFFFFF

**Expected**: `Write-Fail-Counter-Expired`。

---

### Step 4.4: Write with Wrong Counter

**SCSI CMD**: `SECURITY PROTOCOL OUT + IN` — Auth Data Write with wrong counter value

**Expected**: `Write-Counter-Expired`。

---

### Step 4.5: Write with Wrong Key

**SCSI CMD**: `SECURITY PROTOCOL OUT + IN` — Auth Data Write with wrong HMAC/Key

**Expected**: `Write-Counter-Expired` (authentication failure)。

---

### Step 4.6: Write Out-of-Range Address

**SCSI CMD**: `SECURITY PROTOCOL OUT + IN` — Auth Data Write to address beyond region

**Expected**: `Write-Counter-Expired` (or address error)。

---

### Step 4.7: Random RPMB Read

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)` → `SECURITY PROTOCOL IN (A2h)`

| Field | Value |
|-------|-------|
| SECURITY PROTOCOL SPECIFIC (OUT) | 0x0002 (Auth Data Read) |

**Expected**: Read success（Read 不受 counter expired 影響）。

**UFS SPEC Reference**: JESD220H Section 11.7.4.3 (Auth Data Read)

---

### Step 4.8: Read Out-of-Range

**Expected**: `Address-Out-of-Range`。

---

## 附錄

### SCSI Opcodes
| Opcode | Command | 使用 |
|:---|:---|:---|
| 0x00 | TEST UNIT READY | 0.1 |
| 0xA2 | SECURITY PROTOCOL IN | 2.3, 3.2, 4.1~4.8 |
| 0xB5 | SECURITY PROTOCOL OUT | 2.1, 2.2, 3.2, 4.1~4.8 |

### RPMB SECURITY PROTOCOL SPECIFIC
| Value | Operation |
|:---|:---|
| 0x0001 | Authentication Key Programming |
| 0x0002 | Authenticated Data Read |
| 0x0003 | Authenticated Data Write |
| 0x0004 | Read Write Counter |

### UFS Query
| IDN | Name | Opcode | 使用 |
|:---|:---|:---|:---|
| 0x02 | Unit Descriptor | 0x07/0x08 | 1.1, 1.2 |

---

## 自我驗證
- Tree leaf: 0.1,0.2(2)+1.1~1.4(4)+per-region: 2.1~2.3(3)+3.1,3.2(2)+4.1~4.8(8)=13 per region × 4=52... but tree groups them
- `### Step` sections match tree leaves ✓ | All `→ Expected:` ✓
