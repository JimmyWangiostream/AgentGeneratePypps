---
title: PF027_0563-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf027_0563, scsi-cmd, power-state, read-latency]
description: >
  PF027_0563 Read Latency After Power State Transition Test — 正規化 Test Flow。
  在 8 種不同的電源狀態轉換（Sleep / PowerDown × Active / VCC Off / Hibernate / Hibernate+PowerCycle）
  之後量測 READ(10) 延遲，每種場景執行 1000 次迴圈。
sources:
  - JIRA: PF027_0563 (SYSTCUFS-734)
  - UFS Spec: JESD220H Section 7.4 (Power Modes), Section 11.3.5 (READ)
---

# PF027_0563 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

量測 UFS 裝置在不同電源狀態轉換後的讀取延遲（Read Latency）：

| 場景 | 起始狀態 | 轉換路徑 | 終止狀態 |
|:---|:---|:---|:---|
| A | Sleep | SSU Sleep → SSU Active | Active |
| B | Sleep | SSU Sleep → VCC Off → VCC On → SSU Active | Active |
| C | Sleep | SSU Sleep → Hibernate Enter → Hibernate Exit → SSU Active | Active |
| D | Sleep | SSU Sleep → Hibernate Enter → VCC Off → VCC On → Hibernate Exit → SSU Active | Active |
| E | PowerDown | SSU PowerDown → SSU Active | Active |
| F | PowerDown | SSU PowerDown → VCC Off → VCC On → SSU Active | Active |
| G | PowerDown | SSU PowerDown → Hibernate Enter → Hibernate Exit → SSU Active | Active |
| H | PowerDown | SSU PowerDown → Hibernate Enter → VCC Off → VCC On → Hibernate Exit → SSU Active | Active |

每種場景先寫入 2500 筆 4KB 隨機資料，執行電源轉換，再量測 READ(10) 延遲。全部 8 場景為一輪，共執行 1000 輪。

## JIRA Step 對照

| JIRA Step | 原始描述 | 正規化後對應 |
|-----------|---------|-------------|
| Step 1 | Precondition (Wipe, EraseAll_purge, Write Full Card) | Phase 0（Precondition） |
| Step 2–25 | 8 組 Write → Power Transition → Read + Latency | Phase 1（8 場景迴圈） |
| Step 26 | loop 1000 loops | Loop 1000× |
| Step 27 | calculate each item latency QoS | Phase 2（統計分析） |

---

## 測試架構

```
PF027_0563 Test Flow
│
├── Phase 0: Precondition
│   ├── Step 0.1: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│   ├── Step 0.2: UNMAP — Wipe 整卡 → Expected: GOOD Status
│   ├── Step 0.3: QUERY Set Flag (fPurgeEnable) — Erase All Purge → Expected: QUERY RESPONSE Success
│   └── Step 0.4: WRITE(10) — Write Full Card → Expected: GOOD Status
│
└── Loop (1000 輪) → Expected: 每輪執行 8 scenarios
    │
    ├── Scenario A: Sleep → Active
    │   ├── Step A.1: WRITE(10) — 隨機寫入 2500 × 4KB → Expected: GOOD Status
    │   ├── Step A.2: START STOP UNIT — SSU Sleep → Expected: GOOD Status, entered Sleep
    │   ├── Step A.3: START STOP UNIT — SSU Active → Expected: GOOD Status, returned Active
    │   └── Step A.4: READ(10) + Measure Latency → Expected: GOOD Status, record latency
    │
    ├── Scenario B: Sleep → PowerCycle → Active
    │   ├── Step B.1: WRITE(10) → Expected: GOOD Status
    │   ├── Step B.2: START STOP UNIT — SSU Sleep → VCC Off → VCC On → Expected: GOOD Status
    │   ├── Step B.3: START STOP UNIT — SSU Active → Expected: GOOD Status, returned Active
    │   └── Step B.4: READ(10) + Measure Latency → Expected: GOOD Status, record latency
    │
    ├── Scenario C: Sleep → Hibernate → Active
    │   ├── Step C.1: WRITE(10) → Expected: GOOD Status
    │   ├── Step C.2: START STOP UNIT — SSU Sleep → Hibernate Enter → Hibernate Exit → Expected: GOOD Status
    │   ├── Step C.3: START STOP UNIT — SSU Active → Expected: GOOD Status, returned Active
    │   └── Step C.4: READ(10) + Measure Latency → Expected: GOOD Status, record latency
    │
    ├── Scenario D: Sleep → Hibernate → PowerCycle → Active
    │   ├── Step D.1: WRITE(10) → Expected: GOOD Status
    │   ├── Step D.2: SSU Sleep → Hibernate Enter → VCC Off → VCC On → Hibernate Exit → Expected: GOOD Status
    │   ├── Step D.3: START STOP UNIT — SSU Active → Expected: GOOD Status, returned Active
    │   └── Step D.4: READ(10) + Measure Latency → Expected: GOOD Status, record latency
    │
    ├── Scenario E: PowerDown → Active
    │   ├── Step E.1: WRITE(10) → Expected: GOOD Status
    │   ├── Step E.2: START STOP UNIT — SSU PowerDown → SSU Active → Expected: GOOD Status
    │   └── Step E.3: READ(10) + Measure Latency → Expected: GOOD Status, record latency
    │
    ├── Scenario F: PowerDown → PowerCycle → Active
    │   ├── Step F.1: WRITE(10) → Expected: GOOD Status
    │   ├── Step F.2: SSU PowerDown → VCC Off → VCC On → SSU Active → Expected: GOOD Status
    │   └── Step F.3: READ(10) + Measure Latency → Expected: GOOD Status, record latency
    │
    ├── Scenario G: PowerDown → Hibernate → Active
    │   ├── Step G.1: WRITE(10) → Expected: GOOD Status
    │   ├── Step G.2: SSU PowerDown → Hibernate Enter → Hibernate Exit → SSU Active → Expected: GOOD Status
    │   └── Step G.3: READ(10) + Measure Latency → Expected: GOOD Status, record latency
    │
    ├── Scenario H: PowerDown → Hibernate → PowerCycle → Active
    │   ├── Step H.1: WRITE(10) → Expected: GOOD Status
    │   ├── Step H.2: SSU PowerDown → Hibernate Enter → VCC Off → VCC On → Hibernate Exit → SSU Active → Expected: GOOD Status
    │   └── Step H.3: READ(10) + Measure Latency → Expected: GOOD Status, record latency
    │
    └── Phase 2: 統計分析
        └── Step 2.1: Calculate Latency QoS per Scenario → Expected: QoS report generated
```

---

## Phase 0 — Precondition

### Step 0.1: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 11.3.10

---

### Step 0.2: Wipe 整卡

**SCSI CMD**: `UNMAP (42h)`

| Field | Value |
|-------|-------|
| Opcode | 0x42 |
| LUN | All LUNs |
| UNMAP LBA Range | 全卡 LBA 空間 |

**Expected**: `GOOD Status`。

**UFS SPEC Reference**: JESD220H Section 11.3.24

---

### Step 0.3: Erase All Purge

**UFS QUERY**: `SET FLAG (fPurgeEnable)` + 輪詢 `bPurgeStatus`

| Field | Value |
|-------|-------|
| Opcode | 0x02（SET FLAG） |
| IDN | 0x06（fPurgeEnable） |

**Expected**: Purge 完成後 bPurgeStatus == 0x00。

**UFS SPEC Reference**: JESD220H Section 12.2, Section 14.2

---

### Step 0.4: Write Full Card

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | All LUNs |
| Logical Block Address | 0 ~ MAX_LBA（循序寫滿） |

**Expected**: `GOOD Status`。

---

## 場景 A–H — 電源狀態轉換 + Read Latency

> 以下 8 個場景結構相同：Write → Power Transition → READ(10) + Latency。
> 差異僅在 Power Transition 的路徑。此處詳列 Scenario A，其餘僅列差異。

### Scenario A: Sleep → Active

#### Step A.1: 隨機寫入

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 |
| Logical Block Address | 隨機（2500 筆，每筆對齊 4KB） |
| Transfer Length | 1 block（4KB） |
| Total Blocks | 2500 |

**Expected**: `GOOD Status`。

---

#### Step A.2: 進入 Sleep 電源狀態

**SCSI CMD**: `START STOP UNIT (1Bh)`

**目的**: 將裝置從 Active 狀態切換至 Sleep 狀態。

| Field | Value |
|-------|-------|
| Opcode | 0x1B |
| CDB Length | 6 bytes |
| POWER CONDITION | 0x02（Sleep） |
| START | 0x00（Stop — enter power condition） |

**Expected**: `GOOD Status` — 裝置進入 Sleep。

**UFS SPEC Reference**: JESD220H Section 7.4.1.4（Sleep Power Mode）, Section 7.4.2, Section 11.3.9

---

#### Step A.3: 回到 Active 狀態

**SCSI CMD**: `START STOP UNIT (1Bh)`

| Field | Value |
|-------|-------|
| Opcode | 0x1B |
| POWER CONDITION | 0x01（Active） |
| START | 0x01（Start — exit power condition） |

**Expected**: `GOOD Status` — 裝置回到 Active。

---

#### Step A.4: Read + Measure Latency

**SCSI CMD**: `READ(10) (28h)`

| Field | Value |
|-------|-------|
| Opcode | 0x28 |
| LUN | 0 |
| Logical Block Address | 與 Step A.1 寫入的其中一筆相同（隨機選取） |
| Transfer Length | 1 block（4KB） |

**Latency Measurement**: Timestamp_{start} → 發送 READ → Timestamp_{end}

**Expected**: `GOOD Status` + 記錄延遲值。

---

### Scenario B: Sleep → VCC Off → VCC On → Active

與 Scenario A 相同，差異在 Power Transition：

| 子步驟 | 操作 |
|-------|------|
| B.2.1 | START STOP UNIT — SSU Sleep（同 A.2） |
| B.2.2 | VCC Power Off（完全斷電） |
| B.2.3 | VCC Power On + 等待供電穩定 |
| B.3 | START STOP UNIT — SSU Active（同 A.3） |

---

### Scenario C: Sleep → Hibernate → Active

| 子步驟 | 操作 |
|-------|------|
| C.2.1 | START STOP UNIT — SSU Sleep |
| C.2.2 | Hibernate Enter（透過 UFS Power Mode 控制進入 Hibernate） |
| C.2.3 | Hibernate Exit（喚醒裝置回到 Sleep） |
| C.3 | START STOP UNIT — SSU Active |

**Note**: Hibernate Enter/Exit 通常透過 UFS HCI 或 DME 控制，非 SCSI CMD。

---

### Scenario D: Sleep → Hibernate → VCC Off/On → Active

| 子步驟 | 操作 |
|-------|------|
| D.2.1 | SSU Sleep |
| D.2.2 | Hibernate Enter |
| D.2.3 | VCC Off → VCC On |
| D.2.4 | Hibernate Exit |
| D.3 | SSU Active |

---

### Scenario E: PowerDown → Active

| 步驟 | 操作 |
|------|------|
| E.1 | WRITE(10)（同 A.1） |
| E.2 | START STOP UNIT — SSU PowerDown（POWER CONDITION = 0x03）→ SSU Active |
| E.3 | READ(10) + Latency（同 A.4） |

**UFS SPEC Reference**: JESD220H Section 7.4.1.7（Pre-PowerDown）, Section 7.4.1.8（PowerDown）

---

### Scenario F: PowerDown → VCC Off/On → Active

| 子步驟 | 操作 |
|-------|------|
| F.2.1 | START STOP UNIT — SSU PowerDown |
| F.2.2 | VCC Off → VCC On |
| F.2.3 | START STOP UNIT — SSU Active |

---

### Scenario G: PowerDown → Hibernate → Active

| 子步驟 | 操作 |
|-------|------|
| G.2.1 | SSU PowerDown |
| G.2.2 | Hibernate Enter → Hibernate Exit |
| G.2.3 | SSU Active |

---

### Scenario H: PowerDown → Hibernate → VCC Off/On → Active

| 子步驟 | 操作 |
|-------|------|
| H.2.1 | SSU PowerDown |
| H.2.2 | Hibernate Enter |
| H.2.3 | VCC Off → VCC On |
| H.2.4 | Hibernate Exit |
| H.2.5 | SSU Active |

---

## Phase 2 — 統計分析

### Step 2.1: Calculate Latency QoS per Scenario

**目的**: 對每個 Scenario 的 1000 筆延遲資料分別計算：

- Min / Max / Average / Median
- P50, P90, P99, P99.9
- 標準差

**產出**: 8 組 Scenario 的延遲 QoS 報告。

---

## 附錄 A — 本 Pattern 使用的 UFS Query 對照表

| Opcode | 名稱 | 本 Pattern 用途 |
|:---|:---|:---|
| 0x02 | SET FLAG | 設定 fPurgeEnable |

### Flag IDN

| IDN | 名稱 | 本 Pattern 用途 |
|:---|:---|:---|
| 0x06 | fPurgeEnable | Precondition: Erase All Purge |

---

## 附錄 B — 本 Pattern 使用的 SCSI Command 對照表

| Opcode | 命令 | CDB | 本 Pattern 用途 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | 確認裝置就緒 |
| 0x1B | START STOP UNIT | 6 | 控制電源狀態轉換（Sleep / PowerDown / Active） |
| 0x28 | READ(10) | 10 | 讀取資料 + 量測延遲 |
| 0x2A | WRITE(10) | 10 | 每場景前寫入 2500 × 4KB |
| 0x42 | UNMAP | 10 | Wipe 整卡 |

---

## 附錄 C — START STOP UNIT 電源狀態參照

| POWER CONDITION | 值 | 說明 | JESD220H |
|:---|:---|:---|:---|
| Active | 0x01 | 正常運作狀態 | Section 7.4.1.3 |
| Sleep | 0x02 | 低功耗睡眠 | Section 7.4.1.4 |
| PowerDown | 0x03 | 最低功耗（預關機） | Section 7.4.1.8 |

| START bit | 值 | 說明 |
|:---|:---|:---|
| Stop | 0x00 | 進入指定電源狀態 |
| Start | 0x01 | 退出電源狀態回到 Active |


---

## 自我驗證

- Tree Diagram leaf steps: **33**
- `### Step` sections: **5**
- ⚠ 不一致，leaf=33, sections=5
