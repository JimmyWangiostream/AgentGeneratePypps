---
title: PF024_2106-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf024_2106, scsi-cmd, health-report, gc]
description: >
  PF024_2106 Health Report BG GC Count Test — 驗證 Health Report 中的 BG_GC_count
  在 6 種 GC 場景（BG SLC/TLC GC, WL SLC/TLC GC, RD SLC/TLC GC）下正確遞增。
sources:
  - JIRA: PF024_2106 (SYSTCUFS-2457)
  - UFS Spec: JESD220H Section 13.4.4 (Background Operations)
---

# PF024_2106 正規化 Test Flow（SCSI CMD 單位）

## 測試目標

觸發 6 種 GC 類型，驗證 Health Report 中的 BG_GC_count [504:507] 正確遞增。

## 測試架構

```
├── Scene 1: BG SLC GC
│   ├── UNMAP + Purge All
│   ├── SET FLAG (fWriteBoosterEn) + (fWriteBoosterBufferFlushEn)
│   ├── SET FLAG (fBackgroundOpsEn)
│   ├── VU Read Buffer — Get TLC GC threshold
│   ├── VU Read Buffer — Get used/free TLC VB count
│   ├── WRITE(10) — Seq LUN0 50% TLC VBs + poll used TLC VB count decrease
│   ├── QUERY Read Attribute (bBackgroundOpStatus) — poll until 0x00
│   └── VU Read Buffer — Verify BG_SLC_GC & BG_GC_count increased
│
├── Scene 2: BG TLC GC
│   ├── UNMAP + Purge All
│   ├── CLEAR FLAG (fWriteBoosterEn) + (fWriteBoosterBufferFlushEn)
│   ├── SET FLAG (fBackgroundOpsEn)
│   ├── VU Write — TLC GC threshold = 10
│   ├── WRITE(10) — Seq LUN0 50% TLC VBs + poll decrease
│   ├── Poll BKOPS until 0x00
│   └── Verify BG_TLC_GC & BG_GC_count increased → Restore threshold
│
├── Scene 3: WL TLC GC
│   ├── CLEAR FLAG (fWriteBoosterEn) + FlushEn
│   ├── WRITE(10) — LUN0 until used TLC VB > 5
│   ├── VU — Modify erase counts to trigger WL GC
│   ├── READ(10) — Random × 5
│   ├── Poll BKOPS until 0x02 (Performance Impact) → then 0x00
│   └── Verify WL_TLC_GC & BG_GC_count → Restore erase counts
│
├── Scene 4: WL SLC GC
│   ├── WRITE(10) — LUN1 until used SLC VB > 5
│   ├── VU — Modify SLC erase counts to trigger WL GC
│   ├── READ(10) — Random LUN1 × 5
│   ├── Poll BKOPS until 0x02 → then 0x00
│   └── Verify WL_SLC_GC & BG_GC_count → Restore
│
├── Scene 5: RD SLC GC
│   ├── WRITE(10) — Seq 3 SLC VB on LUN1
│   ├── VU — LBA→PCA conversion
│   ├── VUC 0xEB — Force trigger refresh on same VB
│   ├── Poll LBA→PCA until VB changes
│   └── Verify RD_SLC_GC & BG_GC_count
│
└── Scene 6: RD TLC GC
    ├── CLEAR FLAG (fWriteBoosterEn) + FlushEn
    ├── WRITE(10) — Seq 3 TLC VB on LUN0
    ├── VU — LBA→PCA → VUC 0xEB → Poll VB change
    └── Verify RD_TLC_GC & BG_GC_count
```

## 附錄

| Opcode | 命令 / Query | 用途 |
|:---|:---|:---|
| 0x28 | READ(10) | Random Read |
| 0x2A | WRITE(10) | Seq Write |
| 0x42 | UNMAP | Purge precondition |
| 0x3C | READ BUFFER | VU: GC info / Smart Info / Health Report |
| 0x02 | SET FLAG | WB En / Flush En / BKOPS En |
| 0x05 | CLEAR FLAG | WB En / Flush En |
| 0x03 | READ ATTRIBUTE | bBackgroundOpStatus (0x14) |


---

## 自我驗證

- Tree Diagram leaf steps: **0**
- `### Step` sections: **0**
- ✓
