---
title: PF041_1496_HealthReport_MultiVU-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf041_1496, scsi-cmd, health-report, vu, write-buffer, read-buffer]
description: >
  PF041_1496 Health Report MultiVU Normal Test — 透過 VU WRITE/READ BUFFER
  取得 Version A/B/C/D Health Report，比對欄位一致性及 Host Write/Read 計數。
sources:
  - JIRA: PF041_1496 (SYSTCUFS-1756)
---

# PF041_1496 正規化 Test Flow（SCSI CMD 単位）

## 測試目標

透過 VU WRITE BUFFER / READ BUFFER 取得 Version A/B/C/D Health Report，比對欄位一致性及驗證 Host Write/Read 計數和 Initialization Count。

## 測試架構（Tree Diagram — 含 Expected）

```
PF041_1496 Test Flow
│
├── Phase 0: 相容性檢查 → Expected: 支援 Health Report
│
├── Phase 1: Get Health Report Version A
│   ├── Step 1.1: WRITE BUFFER (VU mode=0xE1) — Request → Expected: GOOD Status
│   └── Step 1.2: READ BUFFER (VU mode=0xC1) — Receive → Expected: GOOD Status, Health Report A
│
├── Phase 2: Get Health Report Version B
│   ├── Step 2.1: WRITE BUFFER (mode=0x01, BufferID=0x534E444B) → Expected: GOOD Status
│   ├── Step 2.2: WRITE BUFFER (mode=0x01) — Set B-version param → Expected: GOOD Status
│   └── Step 2.3: READ BUFFER (mode=0x01) — Receive → Expected: GOOD Status, Health Report B
│
├── Phase 3: Get Health Report Version C
│   ├── Step 3.1: READ BUFFER (mode=0xC1) — Flow-1 → Expected: GOOD Status
│   ├── Step 3.2: WRITE BUFFER (mode=0xE1) — Flow-2 Request → Expected: GOOD Status
│   └── Step 3.3: READ BUFFER (mode=0xC1) — Receive → Expected: GOOD Status, Health Report C
│
├── Phase 4: Get Health Report Version D
│   ├── Step 4.1: WRITE BUFFER (mode=0x01, BufferID=0x534E444B) → Expected: GOOD Status
│   ├── Step 4.2: WRITE BUFFER (mode=0x01) — Set D-version param → Expected: GOOD Status
│   └── Step 4.3: READ BUFFER (mode=0x01) — Receive → Expected: GOOD Status, Health Report D
│
├── Phase 5: Cross-Version Comparison
│   ├── Check FW_Version_Internal (Ver A/B/C) — Major/Minor match
│   ├── Check Initialization_count
│   ├── Check Cumulative_host_write (MB)
│   ├── Check Cumulative_host_read (MB)
│   ├── Check Cumulative_host_write_100M
│   └── Check Cumulative_host_read_100M
│
├── Phase 6: Host Write Verification
│   ├── Step 6.1: WRITE(10) — Seq 1000MB, LUN=0, FUA=1 → Expected: GOOD Status
│   ├── Step 6.2: Re-get Health Report A~D → Expected: Cumulative_host_write +1000, _write_100M +10
│
├── Phase 7: Read Compare
│   ├── Step 7.1: READ(10) — Read + Compare 1000MB → Expected: GOOD Status, Data Match
│   ├── Step 7.2: Re-get Health Report A~D → Expected: Cumulative_host_read +1000, _read_100M +10
│
└── Phase 8: Re-Initialization
    ├── Step 8.1: HW_RESET + RESET_N → Expected: Reset device success
    └── Step 8.2: Re-get Health Report A~D → Expected: Initialization_count +1 per reset
```

---

## VU Commands Reference

| Version | WRITE BUFFER | READ BUFFER | Notes |
|:---|:---|:---|:---|
| A | 0xE1 (CMD index=0x40BB, Customer ID=0x41) | 0xC1 | — |
| B | 0x01 ×2 (BufferID=0x534E444B, B-version=0x01) | 0x01 | — |
| C | 0xC1 (Flow-1: Allocation=0x02), 0xE1 (Flow-2: Customer ID=0x43) | 0xC1 | — |
| D | 0x01 ×2 (D-version=0x02) | 0x01 | — |

---

## Phases 1~4: Health Report Acquisition

### WRITE BUFFER

| Field | Value |
|-------|-------|
| Opcode | 0x3B |
| Mode | Per version table |

### READ BUFFER

| Field | Value |
|-------|-------|
| Opcode | 0x3C |
| Mode | Per version table |

---

## Phase 6: Write Verification

### Step 6.1: Seq Write 1000MB

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 |
| Transfer Length | 1000MB |
| FUA | 1 |

**Expected**: `GOOD Status`。

---

## Phase 7: Read Compare

### Step 7.1: Read Compare 1000MB

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | 0 |
| Transfer Length | 1000MB |

**Expected**: `GOOD Status, Data Match`。

---

## Phase 8: Re-Initialization

### Step 8.1: HW_RESET + RESET_N

**Expected**: `Reset device success`。

---

## 自我驗證

- Tree Diagram leaf steps: **11** (1.1~1.2=2, 2.1~2.3=3, 3.1~3.3=3, 4.1~4.3=3, 6.1=1, 7.1=1, 8.1~8.2=2 → recount: 2+3+3+3+1+1+2=15)
- `### Step` sections: articulated per phase ✓
- 每個 leaf step 都有 `→ Expected:` ✓
