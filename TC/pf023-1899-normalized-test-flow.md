---
title: PF023_1899-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf023_1899, scsi-cmd, snapshot, backup, recovery]
description: >
  PF023_1899 Snapshot20 Backup/Drop/Recover All SCSI Test — 驗證 Snapshot 2.0
  的 Backup、Drop、Recovery 完整流程，包含 15 種隨機案例的 burn-in 測試。
sources:
  - JIRA: PF023_1899 (SYSTCUFS-2205)
  - UFS Spec: JESD220H Section 13.4 (Snapshot-related, if applicable)
---

# PF023_1899 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

驗證 Snapshot 2.0 的完整功能：Backup 建立、Drop 刪除、Recovery 復原，並在 72HR burn-in 中混合 15 種隨機操作案例。

## 測試架構

```
├── Phase 0: 裝置相容性 + LUN 配置
│   ├── Step 0.1: IC/NAND/Vendor check → Expected: 支援組合, 否則 NOT SUPPORTED
│   ├── Step 0.2: QUERY Read Attribute (dExtendedUFSFeaturesSupport) — Snapshot bit[31] → Expected: Snapshot bit[31] == 1
│   ├── Step 0.3: RPMB Key Programming (OUT→OUT→IN) → Expected: GOOD Status, Key programmed
│   ├── Step 0.4: Config LUN0/1 (Normal), LUN3 (HPB), LUN4~7 (Boot EM1) → Expected: QUERY RESPONSE Success
│   └── Step 0.5: QUERY Write Descriptor (Config Descriptor) — WB 4GB → Expected: QUERY RESPONSE Success
│
├── Phase 1: Snapshot 初始化
│   ├── Step 1.1: QUERY Read Attribute (bSnapshotVersionMax, 0x22) — expect 6 → Expected: bSnapshotVersionMax == 6
│   ├── Step 1.2: QUERY Read Attribute (bSnapshotProgress, 0x23) — expect 0 → Expected: bSnapshotProgress == 0
│   ├── Step 1.3: QUERY Write Attribute (bSnapshotDropFreeSpaceSize, 0x24) = 20GB → Expected: QUERY RESPONSE Success
│   └── Step 1.4: QUERY Write Attribute (wExceptionEventControl) — bit[11]=1 → Expected: QUERY RESPONSE Success, bit[11]=1
│
├── Phase 2: 寫入 Baseline 資料
│   ├── WRITE(10) — LUN0/1: 512KB chunk, total=(TotalAU-500MB)/2
│   ├── WRITE(10) — LUN4~7: 512KB chunk, total=500MB each
│   └── SECURITY PROTOCOL OUT — RPMB Write: full region
│
└── Loop (72HR burn-in) → Expected: 每輪執行 15 cases
    ├── Case 1 (10%): WRITE(10) LUN0+1, 500MB, FUA=random → Save record → Expected: GOOD Status
    ├── Case 2 (10%): READ(10) LUN0+1, 500MB → Compare → Expected: GOOD Status, Data Match
    ├── Case 3 (10%): SECURITY PROTOCOL OUT/IN — RPMB Write+Read all regions → Expected: GOOD Status
    ├── Case 4 (4%): Idle 3s → Expected: idle complete
    ├── Case 5 (4%): HPB Read Buffer + HPB Read → Expected: GOOD Status
    ├── Case 6 (4%): SSU Sleep → SSU Active → Expected: GOOD Status
    ├── Case 7 (4%): UNMAP — LUN0+1, 500MB → Expected: GOOD Status
    ├── Case 8 (4%): SYNC CACHE + Read bSnapshotVersionMax → Expected: GOOD Status, value unchanged
    ├── Case 9 (4%): Enable WriteBooster (SET FLAG + Read Flag) → Expected: All QUERY RESPONSE Success
    │   ├── WRITE ATTRIBUTE (bWriteBoosterBufferPartialFlushMode, 0x3F)=02h (Pinned)
    │   ├── WRITE ATTRIBUTE (dPinnedWriteBoosterBufferNumAllocUnits, 0x45)=2GB
    │   └── SET FLAG (fWriteBoosterEn, 0x0E) + (fWriteBoosterBufferFlushEn, 0x0F)
    ├── Case 10 (4%): WRITE(10) — Random 10% of total capacity → Expected: GOOD Status
    ├── Case 11 (4%): FBO — WRITE BUFFER (BufferID=0x01) + Pin/Unpin → Expected: GOOD Status
    ├── Case 12 (4%): FBO LUN config: random LUN, FBO_length, FBO_startLBA → Expected: QUERY RESPONSE Success
    ├── Case 13 (10%): Exception Event Check → Expected: 若 bit[11]=1, 執行 Drop
    │   ├── QUERY Read Attribute (wExceptionEventStatus) — check bit[11]
    │   ├── If bit[11]==1: UNMAP 1GB → idle 1s → check GC
    │   ├── READ BUFFER — Get Backup Data Entry Info
    │   └── WRITE BUFFER — Drop operation (random version)
    ├── Case 14 (10%): Recovery Flow → Expected: Recovery 或 Drop 成功
    │   ├── READ BUFFER — Get Backup Data Entry Info
    │   ├── If valid count > 0: WRITE BUFFER — Recovery
    │   ├── Sub-case 1 (15%): TASK MANAGEMENT — Abort write buffer
    │   ├── Sub-case 2 (15%): Software Reset
    │   └── Sub-case 3 (70%): Do nothing
    │   └── Verify recovery status: if invalid → Drop operation
    └── Case 15 (10%): Snapshot version check + conditional Drop → Expected: 若 count>=50%, Drop random version
        ├── READ BUFFER — Get Backup Data Entry Info
        └── If valid count >= 0.5*bSnapshotVersionMax → Drop random version
```

## Phase 13 — Exception Event + Drop

**SCSI CMD**: `READ BUFFER (3Ch)` / `WRITE BUFFER (3Bh)`

| 操作 | Mode | 說明 |
|:---|:---|:---|
| Read Entry Info | 0x3E | GetAll Backup Data, Allocation=0x0038 |
| Drop | 0x9D | BufferID = Random(0~valid-1), 44-byte payload |
| Recovery | 0x5D | BufferID = backup version, 44-byte payload |

## Phase 14 — Recovery + Abort/Reset

| Sub-case | 操作 |
|:---|:---|
| 15% | TASK MANAGEMENT — Abort WRITE BUFFER |
| 15% | Software Reset |
| 70% | 無操作（正常完成） |

## 附錄

| Opcode | 命令 | 用途 |
|:---|:---|:---|
| 0x1B | START STOP UNIT | Sleep/Active |
| 0x28 | READ(10) | Read + Compare |
| 0x2A | WRITE(10) | Write data |
| 0x35 | SYNC CACHE | Cache flush |
| 0x3B | WRITE BUFFER | VU: Drop/Recovery |
| 0x3C | READ BUFFER | VU: Entry Info |
| 0x42 | UNMAP | Erase |
| 0xA2 | SECURITY PROTOCOL IN | RPMB Read |
| 0xB5 | SECURITY PROTOCOL OUT | RPMB Write |


---

## 自我驗證

- Tree Diagram leaf steps: **9**
- `### Step` sections: **0**
- ⚠ 不一致，leaf=9, sections=0
