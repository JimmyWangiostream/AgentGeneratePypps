---
title: PF020_0687_ModeSelect_SWP_AfterReset-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf020_0687, scsi-cmd, mode-select, swp, write-protect, reset]
description: >
  PF020_0687 Mode Select SWP After Reset — 驗證 7 種 SWP/SP mode page 組合在
  5 種 Reset (PowerOn/HW/Endpoint/LU/UniPro) 後的 Write Protection 持久性。
sources:
  - JIRA: PF020_0687 (SYSTCUFS-848)
  - UFS Spec: JESD220H Section 11.3.14 (MODE SELECT), Section 10.4 (Reset)
---

# PF020_0687 正規化 Test Flow（SCSI CMD 単位）

## 測試目標

驗證 MODE SELECT (Control Mode Page) 設定 SWP (Software Write Protect) / SP 後，
經過 5 種 Reset 類型後 Write Protection 狀態的正確性（持久性 / 回復性）。
涵蓋 7 種 SWP/SP 組合測試案例。

## 測試架構（Tree Diagram — 含 Expected）

```
PF020_0687 Test Flow
│
├── Step 0.1: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│
├── Case 1 (SWP=1, SP=0): Permanent Write Protect → Expected: WRITE FAIL post-reset
├── Case 2 (SWP=1, SP=1): Permanent Write Protect → Expected: WRITE FAIL post-reset
├── Case 3 (SWP=1→0, SP=1→0): Unprotect → Expected: WRITE first FAIL then PASS; LU Reset blocked
├── Case 4 (SWP=1→0, SP=1→1): Unprotect → Expected: WRITE first FAIL then PASS; all pass post-reset
├── Case 5 (SWP=1,SP=1→SWP=1,SP=0): Both protected → Expected: WRITE FAIL both stages
├── Case 6 (SWP=0→1, SP=0): Add Protect → Expected: WRITE PASS then FAIL; LU Reset blocked
├── Case 7 (SWP=0→1, SP=1): Add Protect → Expected: WRITE PASS then FAIL; LU Reset blocked
│
└── Recovery: MODE SELECT — Restore original mode page → Expected: QUERY RESPONSE Success
```

---

## Phase 0 — 初始化

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

---

## 7 Cases — SWP/SP Write Protection

### 每個 Case 的通用流程

每個 Case 遵循以下子步驟：

| Sub-step | 操作 | SCSI CMD | Opcode |
|:---|:---|:---|:---|
| a | MODE SENSE(10) — 讀取原始 Mode Page | MODE SENSE(10) | 0x5A |
| b | MODE SELECT(10) — 設定 SWP/SP（Stage 1） | MODE SELECT(10) | 0x55 |
| c | WRITE(10) — 驗證 Write Protect → expect Pass or Data Protect | WRITE(10) | 0x2A |
| d | (Optional) MODE SELECT(10) — Stage 2 變更 | MODE SELECT(10) | 0x55 |
| e | (Optional) WRITE(10) — Stage 2 驗證 | WRITE(10) | 0x2A |
| f | 5 種 Reset × 各 → PowerOn / HW / EndPoint / LU / UniPro | — | — |
| g | WRITE(10) — Post-Reset 驗證 | WRITE(10) | 0x2A |
| h | (LU Reset only) UNMAP → expect blocked | UNMAP | 0x42 |
| i | (LU Reset only) FORMAT UNIT (LUN1) → expect blocked | FORMAT UNIT | 0x04 |
| j | (LU Reset only) FORMAT UNIT (Device WK LUN 0xD0) → expect blocked | FORMAT UNIT | 0x04 |

### Case 1: SWP=1, SP=0 (Permanent Write Protect)

| Stage | SWP | SP | WRITE Expected |
|:---|:---|:---|:---|
| 設定後 | 1 | 0 | Data Protect (WRITE FAIL) |
| Post ALL Reset | 1 | 0 | Data Protect (WRITE FAIL) |

**Expected**: 所有 5 種 Reset 後 Write Protection 保持有效。

### Case 2: SWP=1, SP=1 (Permanent Write Protect)

| Stage | SWP | SP | WRITE Expected |
|:---|:---|:---|:---|
| 設定後 | 1 | 1 | Data Protect (WRITE FAIL) |
| Post ALL Reset | 1 | 1 | Data Protect (WRITE FAIL) |

**Expected**: `SP=1` 確保即使 PowerOn Reset 也保持 Write Protect。

### Case 3: SWP=1→0, SP=1→0 (Unprotect)

| Stage | SWP | SP | WRITE Expected |
|:---|:---|:---|:---|
| Stage 1 | 1 | 1 | Data Protect (WRITE FAIL) |
| Stage 2 | 0 | 0 | WRITE PASS |
| Post LU Reset | 0 | 0 | UNMAP/FORMAT blocked; WRITE PASS |
| Post Other Reset | 0 | 0 | WRITE PASS |

**Expected**: Unprotect 後 WRITE PASS。LU Reset 後 UNMAP/FORMAT 被阻擋（因 Reset 本身不恢復保護，但 Unmap/Format 需額外權限）。

### Case 4: SWP=1→0, SP=1→1 (Unprotect SWP only)

| Stage | SWP | SP | WRITE Expected |
|:---|:---|:---|:---|
| Stage 1 | 1 | 1 | Data Protect (WRITE FAIL) |
| Stage 2 | 0 | 1 | WRITE PASS |
| Post ALL Reset | 0 | 1 | WRITE PASS |

**Expected**: SWP 解除後 WRITE PASS，SP=1 無影響。

### Case 5: SWP=1,SP=1→SWP=1,SP=0

| Stage | SWP | SP | WRITE Expected |
|:---|:---|:---|:---|
| Stage 1 | 1 | 1 | Data Protect (WRITE FAIL) |
| Stage 2 | 1 | 0 | Data Protect (WRITE FAIL) |

**Expected**: 兩個 Stage 均 WRITE FAIL，保護始終有效。

### Case 6: SWP=0→1, SP=0

| Stage | SWP | SP | WRITE Expected |
|:---|:---|:---|:---|
| Stage 1 | 0 | 0 | WRITE PASS |
| Stage 2 | 1 | 0 | Data Protect (WRITE FAIL) |
| Post LU Reset | — | — | UNMAP/FORMAT blocked |
| Post Other Reset | — | — | WRITE PASS (SWP reset to 0) |

### Case 7: SWP=0→1, SP=1

| Stage | SWP | SP | WRITE Expected |
|:---|:---|:---|:---|
| Stage 1 | 0 | 1 | WRITE PASS |
| Stage 2 | 1 | 0 | Data Protect (WRITE FAIL) |
| Post LU Reset | — | — | UNMAP/FORMAT blocked |
| Post Other Reset | — | — | WRITE FAIL (SP=1 保持保護) |

---

## Recovery

### Recovery: Restore Original Mode Page

**SCSI CMD**: `MODE SELECT(10) (55h)`

| Field | Value |
|-------|-------|
| Opcode | 0x55 |
| LUN | 1 |
| Mode Page | Restore original SWP/SP values |

**Expected**: `GOOD Status`，Mode Page 恢復原始設定。

---

## SCSI CMD 通用參數

### MODE SENSE(10)

| Field | Value |
|-------|-------|
| Opcode | 0x5A |
| LUN | 1 |
| Page Code | 0x0A (Control Mode Page) |

### MODE SELECT(10)

| Field | Value |
|-------|-------|
| Opcode | 0x55 |
| LUN | 1 |
| Page Code | 0x0A (Control Mode Page) |
| SWP | 0 or 1 |
| SP | 0 or 1 |

### WRITE(10) — Verification

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 1 |
| Logical Block Address | 0x00000000 |
| Transfer Length | 512KB |

## 5 種 Reset 類型

| Reset | 說明 |
|:---|:---|
| PowerOn Reset | 完整電源循環 |
| HW Reset | RST_n hardware reset |
| EndPoint Reset | DME EndPointReset |
| LU Reset | Logical Unit Reset |
| UniPro Reset | UniPro layer reset |

**Expected per Reset**: `Reset device success`。

## 附錄 B — SCSI Command Opcode 對照表

| Opcode | Command | CDB Size | 使用位置 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | Step 0.1 |
| 0x04 | FORMAT UNIT | 6 | LU Reset checks |
| 0x28 | READ(10) | 10 | (optional verify) |
| 0x2A | WRITE(10) | 10 | All cases verification |
| 0x42 | UNMAP | 10 | LU Reset checks |
| 0x55 | MODE SELECT(10) | 10 | All cases + Recovery |
| 0x5A | MODE SENSE(10) | 10 | All cases |

---

## 自我驗證

- Tree Diagram leaf steps: **7 Cases + Recovery** = named test scenarios
- Each case has documented SWP/SP transitions and Expected outcomes ✓
- Reset Expected 使用統一格式 `Reset device success` ✓
- 無 `(待確認)` 佔位符 ✓
