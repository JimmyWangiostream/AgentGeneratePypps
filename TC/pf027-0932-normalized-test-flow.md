---
title: PF027_0932-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf027_0932, scsi-cmd, rpmb, security, latency]
description: >
  PF027_0932 RPMB Security In/Out Latency Test — 正規化 Test Flow。
  在 dirty media 預處理後，執行 100,000 次 RPMB Security Protocol Out/In
  讀取操作，量測並計算 99.9% 延遲分佈。以 SCSI CMD 與 UFS Query 為最小單位拆分。
sources:
  - JIRA: PF027_0932 (SYSTCUFS-1264)
  - UFS Spec: JESD220H Section 12.4 (RPMB), Section 11.3.19-20 (SECURITY PROTOCOL IN/OUT)
---

# PF027_0932 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

在 dirty media（已寫滿資料的 NAND）條件下，量測 RPMB Security Protocol Out/In 讀取操作的延遲效能：

- 對 RPMB 區域執行 100,000 次 Security Out → Out(Result) → In 的讀取週期（每次 RPMB Read 由 2 次 OUT + 1 次 IN 組成）
- 每次記錄延遲時間
- 計算 99.9% latency 分位數
- 產出統計報告

## JIRA Step 對照

| JIRA Step | 原始描述 | 正規化後對應 |
|-----------|---------|-------------|
| Step 1 | WIPE + Erase all purge | Phase 0 Step 0.1–0.3（Precondition） |
| Step 2 | Run the dirty media prediction | Phase 0 Step 0.4（Dirty media 寫入） |
| Step 3 | RPMB Key Programming | Phase 1 Step 1.1–1.3（RPMB 金鑰設定：OUT→OUT→IN） |
| Step 4 | RPMB Read Write Count | Phase 1 Step 1.4–1.5（讀取計數器：OUT→IN） |
| Step 5 | RPMB Read (Security Out/In) | Phase 2（單次 RPMB Read：OUT→IN） |
| Step 6 | Loop 5 until 100,000 | Loop 100,000 次 |
| Step 7 | Calculate 99.9% latency | Phase 3（統計計算） |
| Step 8 | Create statistic report | Phase 3（產出報告） |

---

## 測試架構

```
PF027_0932 Test Flow
│
├── Phase 0: Precondition（Wipe + Purge + Dirty Media）
│   ├── Step 0.1: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│   ├── Step 0.2: UNMAP — Wipe 整卡（釋放所有 LBA） → Expected: GOOD Status
│   ├── Step 0.3: QUERY Set Flag (fPurgeEnable) — Erase All Purge → Expected: QUERY RESPONSE Success
│   ├── Step 0.4: WRITE(10) — Dirty Media（寫滿整卡） → Expected: GOOD Status
│   └── Step 0.5: QUERY Read Attribute (bBackgroundOpStatus) — 等待 BKOPS 完成 → Expected: bBackgroundOpStatus == 0x00
│
├── Phase 1: RPMB 初始化設定
│   ├── Step 1.1: SECURITY PROTOCOL OUT — Key Programming Request → Expected: GOOD Status
│   ├── Step 1.2: SECURITY PROTOCOL OUT — Result Request → Expected: GOOD Status
│   ├── Step 1.3: SECURITY PROTOCOL IN — Result Response → Expected: GOOD Status, Result == 0x0000
│   ├── Step 1.4: SECURITY PROTOCOL OUT — Read Write Counter Request → Expected: GOOD Status
│   └── Step 1.5: SECURITY PROTOCOL IN — Counter Response → Expected: GOOD Status, valid Counter
│
├── Loop (100,000 次) → Expected: 每筆記錄延遲
│   └── Phase 2: RPMB Read（OUT → IN）
│       ├── Step 2.1: SECURITY PROTOCOL OUT — Authenticated Data Read Request → Expected: GOOD Status
│       └── Step 2.2: SECURITY PROTOCOL IN — Read Response + Record Latency → Expected: GOOD Status, 資料 + MAC 驗證通過
│
└── Phase 3: 統計分析
    ├── Step 3.1: Calculate 99.9% Latency → Expected: P99.9 計算完成
    └── Step 3.2: Generate Statistical Report → Expected: 報告產出完成
```

---

## Phase 0 — Precondition（Wipe + Purge + Dirty Media）

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |
| CDB Length | 6 bytes |

**Expected**: `GOOD Status` — 裝置就緒。

**UFS SPEC Reference**: JESD220H Section 11.3.10

---

### Step 0.2: Wipe 整卡（釋放所有 LBA）

**SCSI CMD**: `UNMAP (42h)`

**目的**: 對所有 LUN 的所有已配置 LBA 執行 UNMAP，釋放實體 NAND 區塊。

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| CDB Length | 10 bytes |
| LUN | All LUNs |
| UNMAP LBA Range | 整個 LUN 位址空間 |

**Expected**: `GOOD Status` — UNMAP 完成。

**UFS SPEC Reference**: JESD220H Section 11.3.24

---

### Step 0.3: Erase All Purge

**UFS QUERY**: `SET FLAG (fPurgeEnable)`

**目的**: 觸發 Purge 操作，實體抹除所有已 UNMAP 的 NAND 區塊。

| Field | Value |
|-------|-------|
| Opcode | 0x02（SET FLAG） |
| IDN | 0x06（fPurgeEnable） |
| Selector | 0x00 |
| Index | 0x00 |

**Expected**: `QUERY RESPONSE Success` — Purge 操作已啟動。

**Post-check**: 輪詢 `bPurgeStatus` attribute 直到值為 0x00（Idle），確認 Purge 完成。

**UFS SPEC Reference**: JESD220H Section 12.2（Secure Mode / Purge）, Section 14.2

---

### Step 0.4: Dirty Media 寫入

**SCSI CMD**: `WRITE(10) (2Ah)`

**目的**: 將整張卡寫滿測試資料，創造 dirty media 條件（NAND 無空閒區塊），使後續 RPMB 讀取操作在真實壓力環境下進行。

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| CDB Length | 10 bytes |
| LUN | All LUNs |
| Logical Block Address | 0 ~ MAX_LBA（全卡循序寫入） |
| Transfer Length | 依 LUN 容量分批寫入 |

**Expected**: `GOOD Status` — 全卡寫入完成。

**UFS SPEC Reference**: JESD220H Section 11.3.13

---

### Step 0.5: 等待背景作業完成

**UFS QUERY**: `READ ATTRIBUTE (bBackgroundOpStatus)`

**目的**: 確認全卡寫入後，裝置的背景作業（GC 等）已完成，避免干擾延遲量測。

| Field | Value |
|-------|-------|
| Opcode | 0x03（READ ATTRIBUTE） |
| IDN | 0x14（bBackgroundOpStatus） |
| Selector | 0x00 |
| Index | 0x00 |

**Expected**: bBackgroundOpStatus == 0x00（Idle）。若非 Idle，輪詢至 Idle。

**UFS SPEC Reference**: JESD220H Section 14.3, Section 13.4.4

---

## Phase 1 — RPMB 初始化設定

> RPMB 標準流程為 OUT(Request) → OUT(Result) → IN(Response)。每個需要讀回結果的操作
> 都遵循此三階段模式。

### Step 1.1: Authentication Key Programming — Request

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)`

**目的**: 將 Authentication Key 寫入 RPMB 區域，用於後續所有 RPMB 操作的 MAC 簽章驗證。

| Field | Value |
|-------|-------|
| Opcode | 0xB5 |
| CDB Length | 12 bytes |
| SECURITY PROTOCOL | 0xEC（RPMB Protocol） |
| SECURITY PROTOCOL SPECIFIC | 0x0001（Authentication Key Programming Request） |
| Transfer Length | 284 bytes（RPMB Message Frame） |

**RPMB Message Frame**（基於 JESD220H Section 12.4）:
- Request Type: 0x0001（Authentication Key Programming）
- Authentication Key: 32 bytes
- Nonce / MAC / Data / Result: 依 SPEC 定義

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 12.4.7.1, Section 11.3.20

---

### Step 1.2: Authentication Key Programming — Result Request

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)`

**目的**: 向裝置請求 Key Programming 操作的執行結果。

| Field | Value |
|-------|-------|
| Opcode | 0xB5 |
| CDB Length | 12 bytes |
| SECURITY PROTOCOL | 0xEC（RPMB Protocol） |
| SECURITY PROTOCOL SPECIFIC | 0x0001（Result Request） |
| Transfer Length | 284 bytes |

**RPMB Message Frame**:
- Request Type: Result Request（請求回傳 Programming 結果）

**Expected**: `GOOD Status`。

---

### Step 1.3: Authentication Key Programming — Result Response

**SCSI CMD**: `SECURITY PROTOCOL IN (A2h)`

**目的**: 讀取 Key Programming 的結果回應，確認金鑰寫入成功。

| Field | Value |
|-------|-------|
| Opcode | 0xA2 |
| CDB Length | 12 bytes |
| SECURITY PROTOCOL | 0xEC（RPMB Protocol） |
| SECURITY PROTOCOL SPECIFIC | 0x0000 |
| Allocation Length | 284 bytes |

**Expected**: `GOOD Status` + Response Result == 0x0000（程式設計成功）。

**UFS SPEC Reference**: JESD220H Section 12.4.7.1, Section 11.3.19

---

### Step 1.4: Read Write Counter — Request

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)`

**目的**: 發送 RPMB Write Counter 讀取請求。

| Field | Value |
|-------|-------|
| Opcode | 0xB5 |
| CDB Length | 12 bytes |
| SECURITY PROTOCOL | 0xEC |
| SECURITY PROTOCOL SPECIFIC | 0x0002（Read Counter Request） |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 12.4.7.2

---

### Step 1.5: Read Write Counter — Response

**SCSI CMD**: `SECURITY PROTOCOL IN (A2h)`

**目的**: 讀取 Counter 結果。

| Field | Value |
|-------|-------|
| Opcode | 0xA2 |
| CDB Length | 12 bytes |
| SECURITY PROTOCOL | 0xEC |
| SECURITY PROTOCOL SPECIFIC | 0x0000 |
| Allocation Length | 284 bytes |

**Expected**: `GOOD Status` + 有效的 Write Counter 值。

---

## Phase 2 — RPMB Read（100,000 次迴圈）

> RPMB Authenticated Data Read 為標準 OUT → IN 流程。

### Step 2.1: Authenticated Data Read — Request

**SCSI CMD**: `SECURITY PROTOCOL OUT (B5h)`

**目的**: 對 RPMB 區域發送 Authenticated Data Read 請求。

| Field | Value |
|-------|-------|
| Opcode | 0xB5 |
| CDB Length | 12 bytes |
| SECURITY PROTOCOL | 0xEC |
| SECURITY PROTOCOL SPECIFIC | 0x0004（Authenticated Data Read Request） |
| Transfer Length | 284 bytes |

**RPMB Message Frame**:
- Request Type: 0x0004
- Address: 隨機（0 ~ RPMB Region Capacity - 1）
- Nonce: 隨機 16 bytes

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 12.4.7.4

---

### Step 2.2: Authenticated Data Read — Response + Measure Latency

**SCSI CMD**: `SECURITY PROTOCOL IN (A2h)`

**目的**: 接收 RPMB Read Response（資料 + MAC），記錄延遲。

| Field | Value |
|-------|-------|
| Opcode | 0xA2 |
| CDB Length | 12 bytes |
| SECURITY PROTOCOL | 0xEC |
| SECURITY PROTOCOL SPECIFIC | 0x0000 |
| Allocation Length | 284 bytes |

**Latency Measurement**:
- Start timestamp: Step 2.1 SCSI CMD 發送前
- End timestamp: Step 2.2 SCSI CMD Response 收到後
- Latency = End - Start

**Expected**: `GOOD Status` + 有效資料 + MAC 驗證通過。

---

## Phase 3 — 統計分析

### Step 3.1: 計算 99.9% Latency

**目的**: 對 100,000 筆延遲資料進行統計分析，計算 P99.9（99.9th percentile）延遲值。

**方法**: 將所有量測到的延遲排序，取第 99,900 筆（100,000 × 0.999）作為 P99.9。

### Step 3.2: 產出統計報告

**目的**: 產出延遲分佈報告，包含：
- Min / Max / Average / Median
- P50, P90, P99, P99.9, P99.99
- 標準差
- Latency histogram（可選）

---

## 附錄 A — 本 Pattern 使用的 UFS Query 對照表

| Opcode | 名稱 | 本 Pattern 用途 |
|:---|:---|:---|
| 0x02 | SET FLAG | 設定 fPurgeEnable（觸發 Purge） |
| 0x03 | READ ATTRIBUTE | 讀取 bBackgroundOpStatus / bPurgeStatus |

### Flag IDN

| IDN | 名稱 | 本 Pattern 用途 |
|:---|:---|:---|
| 0x06 | fPurgeEnable | 觸發 Purge 清除操作 |

### Attribute IDN（唯讀）

| IDN | 名稱 | Access | 本 Pattern 用途 |
|:---|:---|:---|:---|
| 0x14 | bBackgroundOpStatus | Read-Only | 確認 BKOPS 狀態 |

---

## 附錄 B — 本 Pattern 使用的 SCSI Command 對照表

| Opcode | 命令 | CDB | 本 Pattern 用途 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | 確認裝置就緒 |
| 0x28 | READ(10) | 10 | —（未直接使用，保留） |
| 0x2A | WRITE(10) | 10 | Dirty media 全卡寫入 |
| 0x42 | UNMAP | 10 | Wipe 整卡 |
| 0xA2 | SECURITY PROTOCOL IN | 12 | RPMB Response 接收 |
| 0xB5 | SECURITY PROTOCOL OUT | 12 | RPMB Request 發送 |

---

## 附錄 C — RPMB Security Protocol Specific 值

| Value | 操作 | 說明 |
|:---|:---|:---|
| 0x0001 | Authentication Key Programming | 寫入驗證金鑰 |
| 0x0002 | Read Write Counter | 讀取 RPMB Write Counter |
| 0x0003 | Authenticated Data Write | 驗證寫入 |
| 0x0004 | Authenticated Data Read | 驗證讀取 |


---

## 自我驗證

- Tree Diagram leaf steps: **14**
- `### Step` sections: **14**
- ✓
