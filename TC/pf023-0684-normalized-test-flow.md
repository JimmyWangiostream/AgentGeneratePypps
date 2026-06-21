---
title: PF023_0684-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf023_0684, scsi-cmd, purge, secure-removal, provisioning]
description: >
  PF023_0684 Secure Removal Type Purge Logical Test — 正規化 Test Flow。
  驗證 bSecureRemovalType 與 bProvisioningType 的 7 種組合下，Purge 操作的
  邏輯抹除行為：確認 Purge 前後 GC count 不變、SLC erase count 不變、
  且 Purge 後實體 NAND 資料未被物理抹除（Logical Erase 而非 Physical Erase）。
sources:
  - JIRA: PF023_0684 (SYSTCUFS-845)
  - UFS Spec: JESD220H Section 12.2 (Secure Mode / Purge), Section 14.1 (Descriptors)
---

# PF023_0684 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

驗證 Secure Removal Type Purge 在 Logical Erase 模式下的行為：

- 7 種 (bProvisioningType, bSecureRemovalType) 組合之下，Purge 操作為 Logical Erase
  （僅標記為無效，不物理抹除 NAND 資料）
- Purge 前後：GC count 不變、SLC erase count 不變
- Purge 後透過 Direct Read 可讀回原始資料，確認物理層未被抹除

## JIRA Step 對照

| JIRA Step | 描述 | 正規化對應 |
|-----------|------|-----------|
| Step 1 | IC/NAND 檢查 | Phase 0 Step 0.1 |
| Step 2 | Config bSecureRemovalType + 設定 7 種組合迴圈 | Phase 0 Step 0.2 + Loop Config |
| Step 3 | poll BKOPS | Phase 1 Step 1.1 |
| Step 4 | get before purge GC cnt | Phase 1 Step 1.2 |
| Step 5 | set purge enable | Phase 1 Step 1.3 |
| Step 6 | verify GC cnt unchanged | Phase 1 Step 1.4 |
| Step 7 | get before SLC erase info | Phase 1 Step 1.5 |
| Step 8 | set purge enable | Phase 1 Step 1.6 |
| Step 9 | verify SLC erase cnt unchanged | Phase 1 Step 1.7 |
| Step 10 | sequential write 1GB | Phase 1 Step 1.8 |
| Step 11 | record first LBA PBA | Phase 1 Step 1.9 |
| Step 12 | record write CRC | Phase 1 Step 1.9 |
| Step 13 | erase 5 blocks | Phase 1 Step 1.10 |
| Step 14 | set purge enable | Phase 1 Step 1.11 |
| Step 15 | direct read verify NOT erased | Phase 1 Step 1.12 |
| Step 16 | Loop 2~8 for all 7 configs | Loop Config |

---

## 測試架構

```
PF023_0684 Test Flow
│
├── Phase 0: 初始化與裝置檢查
│   ├── Step 0.1: 裝置相容性檢查（IC / NAND / UFS Version） → Expected: 支援組合, 否則 NOT SUPPORTED
│   └── Step 0.2: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
│
└── Loop (7 Config Combinations) → Expected: 每種組合執行 Phase 1
    │
    │   Config: bProvisioningType × bSecureRemovalType
    │   1. (Thin=02h, RemovalType=00h)
    │   ├── Step 0.1: 裝置相容性檢查（IC / NAND / UFS Version） → Expected: 支援組合, 否則 NOT SUPPORTED
    │   └── Step 0.2: TEST UNIT READY — 確認裝置就緒 → Expected: GOOD Status
    │
    └── Loop (7 Config Combinations) → Expected: 每種組合執行 Phase 1
        │
        │   7 Configs: (bProvisioningType, bSecureRemovalType) permutations
        │
        ├── Step C.1: QUERY Write Descriptor (Device Descriptor) — 設定 bProvisioningType & bSecureRemovalType → Expected: QUERY RESPONSE Success
        │
        └── Phase 1: Purge Logical Erase 驗證
            ├── Step 1.1: QUERY Read Attribute (bBackgroundOpStatus) — 等待 BKOPS Idle → Expected: bBackgroundOpStatus == 0x00
            ├── Step 1.2: VU Read Buffer — 記錄 Purge 前 GC count → Expected: GC count recorded
            ├── Step 1.3: QUERY Set Flag (fPurgeEnable) — 觸發 Purge → Expected: QUERY RESPONSE Success
            ├── Step 1.4: VU Read Buffer — 驗證 GC count 不變 → Expected: GC count unchanged
            ├── Step 1.5: Direct Read — 記錄 Purge 前 SLC erase 狀態 → Expected: SLC erase state recorded
            ├── Step 1.6: QUERY Set Flag (fPurgeEnable) — 再次觸發 Purge → Expected: QUERY RESPONSE Success
            ├── Step 1.7: Direct Read — 驗證 SLC erase count 不變 → Expected: SLC erase count unchanged
            ├── Step 1.8: WRITE(10) — 循序寫入 1GB → Expected: GOOD Status
            ├── Step 1.9: 記錄 LBA0 的 PBA & Write CRC → Expected: PBA + CRC recorded
            ├── Step 1.10: UNMAP / WRITE(10) — Erase 5 個目標 LBA → Expected: GOOD Status
            ├── Step 1.11: QUERY Set Flag (fPurgeEnable) — 觸發 Purge → Expected: QUERY RESPONSE Success
            └── Step 1.12: Direct Read — 驗證資料未被物理抹除 → Expected: 原始資料 intact (Logical Erase)
```

---

## Phase 0 — 初始化與裝置檢查

### Step 0.1: 裝置相容性檢查

**目的**: 確認 IC / NAND / UFS 版本組合為支援的配置。

| 檢查項目 | 條件 |
|---------|------|
| IC | 8317 BiCS5 (KIC) 或 gTLC 或 8329 BiCS8 |
| UFS Version | 3.1 或 2.2 |

**若不支援**: Pattern 判定為 `NOT SUPPORTED`，終止測試。

---

### Step 0.2: 確認裝置就緒

**SCSI CMD**: `TEST UNIT READY (00h)`

| Field | Value |
|-------|-------|
| Opcode | 0x00 |

**Expected**: `GOOD Status`。

---

## Loop — 7 種 Config 組合

### Step C.1: 設定 Secure Removal 與 Provisioning 參數

**UFS QUERY**: `WRITE DESCRIPTOR (Device Descriptor)`

**目的**: 透過 Device Descriptor 設定 bSecureRemovalType 與 bProvisioningType。
此兩欄位為 Device Descriptor 中的可配置參數。

| Field | Value |
|-------|-------|
| Opcode | 0x08（WRITE DESCRIPTOR） |
| IDN | 0x00（Device Descriptor） |
| Selector | 0x00 |
| Index | 0x00 |

**Device Descriptor 中需設定的欄位**（基於 JESD220H Section 14.1.4.1）:

| Field | 本輪值 | 說明 |
|-------|-------|------|
| bProvisioningType | 0x02 或 0x03 | 0x02=Thin Provisioning (Discard), 0x03=Full Provisioning |
| bSecureRemovalType | 0x00~0x03 | Secure Removal 類型 |

**7 種組合**:

| Loop# | bProvisioningType | bSecureRemovalType | 說明 |
|:---|:---|:---|:---|
| 1 | 0x02 (Thin) | 0x00 | Thin + RemovalType 0 |
| 2 | 0x02 (Thin) | 0x01 | Thin + RemovalType 1 |
| 3 | 0x02 (Thin) | 0x02 | Thin + RemovalType 2 |
| 4 | 0x02 (Thin) | 0x03 | Thin + RemovalType 3 |
| 5 | 0x03 (Full) | 0x01 | Full + RemovalType 1 |
| 6 | 0x03 (Full) | 0x02 | Full + RemovalType 2 |
| 7 | 0x03 (Full) | 0x03 | Full + RemovalType 3 |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 14.1.4.1（Device Descriptor）

---

## Phase 1 — Purge Logical Erase 驗證

### Step 1.1: 等待背景作業完成

**UFS QUERY**: `READ ATTRIBUTE (bBackgroundOpStatus)`

| Field | Value |
|-------|-------|
| Opcode | 0x03（READ ATTRIBUTE） |
| IDN | 0x14（bBackgroundOpStatus） |

**Expected**: bBackgroundOpStatus == 0x00（Idle）。若非 Idle，輪詢至 Idle。

**UFS SPEC Reference**: JESD220H Section 13.4.4, Section 14.3

---

### Step 1.2: 記錄 Purge 前 GC Count

**SCSI CMD**: `READ BUFFER (3Ch)` — Vendor Unique Mode

**目的**: 透過 VU Read Buffer 讀取 Purge 前的 GC (Garbage Collection) 計數值。

| Field | Value |
|-------|-------|
| Opcode | 0x3C |
| Mode | Vendor Unique（不是 SPEC 定義的標準 mode） |

**VU 參照**（非 SPEC，僅供實作參考）:
- VU Command: 0x40AE
- Return Data byte[0-3]: GC Threshold
- Return Data byte[24-27]: TLC Used VB Count

**Expected**: 記錄 GC count 為 `before_gc_cnt`。

---

### Step 1.3: 觸發 Purge（第一次）

**UFS QUERY**: `SET FLAG (fPurgeEnable)`

| Field | Value |
|-------|-------|
| Opcode | 0x02（SET FLAG） |
| IDN | 0x06（fPurgeEnable） |

**Expected**: `QUERY RESPONSE Success`。

**UFS SPEC Reference**: JESD220H Section 12.2

---

### Step 1.4: 驗證 GC Count 不變

**SCSI CMD**: `READ BUFFER (3Ch)` — VU Mode（同 Step 1.2）

**目的**: 讀取 Purge 後的 GC count，確認 Purge 未觸發 GC（Logical Erase 不應引發 GC）。

**Expected**: `after_gc_cnt == before_gc_cnt`。

---

### Step 1.5: 記錄 Purge 前 SLC Erase 狀態

**VU Direct Read**: 讀取所有 Free SLC Block 的 Erase Page Status。

**目的**: 記錄 Purge 前每個 Free SLC Block 的 Erase Page Status（offset 4KB+128byte, bit[3]）。

**Expected**: 所有 Free SLC Block 的 erase page status == 1。

---

### Step 1.6: 再次觸發 Purge

**UFS QUERY**: `SET FLAG (fPurgeEnable)`（同 Step 1.3）

| Field | Value |
|-------|-------|
| Opcode | 0x02（SET FLAG） |
| IDN | 0x06（fPurgeEnable） |

---

### Step 1.7: 驗證 SLC Erase Count 不變

**VU Direct Read**（同 Step 1.5）

**目的**: 確認 Purge 後 SLC Erase Count 沒有增加（Logical Erase 不應觸發實體抹除）。

**Expected**: `before_slc_erase_cnt == after_slc_erase_cnt`。

---

### Step 1.8: 寫入測試資料（1GB）

**SCSI CMD**: `WRITE(10) (2Ah)`

| Field | Value |
|-------|-------|
| Opcode | 0x2A |
| LUN | 0 |
| Logical Block Address | random(0, Total Capacity - 1GB) |
| Transfer Length | 512KB chunks |
| Total Size | 1GB |

**Expected**: `GOOD Status`。

---

### Step 1.9: 記錄 LBA0 的 PBA 與 CRC

**目的**: 
- 記錄寫入的第一個 LBA 對應的 PBA（Physical Block Address），用於後續 Direct Read
- 計算並記錄 Write CRC，用於後續比對

**Note**: PBA 取得為 VU 操作，非 SPEC 定義。

---

### Step 1.10: Erase 目標 LBA

**SCSI CMD**: `UNMAP (42h)` 或 `WRITE(10) (2Ah)` with erase

**目的**: 對 5 個目標 LBA 執行抹除（Erase）操作。

| 目標 LBA | 大小 |
|---------|------|
| Step 1.8 寫入的第一個 LBA（LBA0） | 0.5 VB size |
| LBA0 所屬 VB 的前 3 個 VB 的第一個 LBA | 0.5 VB size |
| 最後一個 LBA | 0.5 VB size |
| 隨機 LBA | 0.5 VB size |

**Expected**: `GOOD Status`。

---

### Step 1.11: 觸發 Purge（第三次）

**UFS QUERY**: `SET FLAG (fPurgeEnable)`（同 Step 1.3）

---

### Step 1.12: Direct Read 驗證 Logical Erase

**VU Direct Read**: 直接讀取 Step 1.9 記錄的 PBA 位址。

**目的**: 透過 Direct Read（繞過 FTL mapping）讀取物理 NAND 位址，確認 Purge 為 Logical Erase（僅標記無效，物理資料仍在）。

**Expected**:
- Direct Read 可讀回資料（非全 0xFF）
- Read CRC == Step 1.9 記錄的 Write CRC
- 確認資料未被物理抹除

---

## 附錄 A — 本 Pattern 使用的 UFS Query 對照表

### Query Opcode

| Opcode | 名稱 | 本 Pattern 用途 |
|:---|:---|:---|
| 0x02 | SET FLAG | 設定 fPurgeEnable（觸發 Purge） |
| 0x03 | READ ATTRIBUTE | 讀取 bBackgroundOpStatus |
| 0x08 | WRITE DESCRIPTOR | 寫入 Device Descriptor（設定 bProvisioningType / bSecureRemovalType） |

### Flag IDN

| IDN | 名稱 | 本 Pattern 用途 |
|:---|:---|:---|
| 0x06 | fPurgeEnable | 觸發 Purge 清除操作 |

### Attribute IDN

| IDN | 名稱 | Access | 本 Pattern 用途 |
|:---|:---|:---|:---|
| 0x14 | bBackgroundOpStatus | Read-Only | 等待 BKOPS 完成 |

### Descriptor IDN

| IDN | 名稱 | 本 Pattern 用途 |
|:---|:---|:---|
| 0x00 | Device Descriptor | 設定 bSecureRemovalType / bProvisioningType |

---

## 附錄 B — 本 Pattern 使用的 SCSI Command 對照表

| Opcode | 命令 | CDB | 本 Pattern 用途 |
|:---|:---|:---|:---|
| 0x00 | TEST UNIT READY | 6 | 確認裝置就緒 |
| 0x2A | WRITE(10) | 10 | 寫入 1GB 測試資料 |
| 0x3C | READ BUFFER | 10 | VU: 讀取 GC count / 裝置資訊 |
| 0x42 | UNMAP | 10 | Erase 目標 LBA |

---

## 附錄 C — Device Descriptor 配置欄位

| 欄位 | 值 | 說明 |
|:---|:---|:---|
| bProvisioningType | 0x02 | Thin Provisioning (Discard) |
| bProvisioningType | 0x03 | Full Provisioning |
| bSecureRemovalType | 0x00 | Secure Removal Type 0 |
| bSecureRemovalType | 0x01 | Secure Removal Type 1 |
| bSecureRemovalType | 0x02 | Secure Removal Type 2 |
| bSecureRemovalType | 0x03 | Logical Erase Only（不物理抹除） |


---

## 自我驗證

- Tree Diagram leaf steps: **15**
- `### Step` sections: **15**
- ✓
