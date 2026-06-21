---
title: PF035_0726-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf035_0726, scsi-cmd, fbo, writebooster, l2p]
description: PF035_0726 FBO WB En/Dis L2P Check — FBO 優化後 L2P 變化驗證。
sources: [JIRA: PF035_0726 (SYSTCUFS-904)]
# PF035_0726 正規化 Test Flow（SCSI CMD 単位）
## 測試架構
```
├── Step 0.1: QUERY Read Attribute (bUFSFeaturesSupport) — check FBO → Expected: FBO bit == 1
├── Step 0.2: QUERY Read Descriptor — wFBOVersion (01h) → Expected: QUERY RESPONSE Success, version 01h
├── Step 0.3: QUERY Read Attribute — dFBORecommendedLBARangeSize (03h) → Expected: QUERY RESPONSE Success
├── Step 0.4: QUERY Read Attribute — dFBOMaxLBARangeSize (07h) → Expected: QUERY RESPONSE Success
├── Step 0.5: QUERY Read Attribute — dFBOMinLBARangeSize (0Bh) → Expected: QUERY RESPONSE Success
├── Step 0.6: QUERY Read Attribute — bFBOMaxLBARangeCount (0Fh) → Expected: QUERY RESPONSE Success
│
├── VC7 (WB Disable):
│   ├── Step 7.1: QUERY Clear Flag (fWriteBoosterEn, 0x0E) → Expected: QUERY RESPONSE Success
│   ├── Step 7.2: WRITE(10) — LUN0, LBA=rand, chunksize=512K, total=TLC_VB/2 → Expected: GOOD Status
│   ├── Step 7.3: VU 0x88 L2P Read — first LBA → Address X → Expected: Address X retrieved
│   ├── Step 7.4: FBO WRITE BUFFER (Mode=02h, BufferID=01h) — Analysis LBA range → Expected: GOOD Status
│   ├── Step 7.5: QUERY Write Attribute (fFBOControl, 0x31) = 1 → Expected: QUERY RESPONSE Success
│   ├── Step 7.6: QUERY Read Attribute (bFBOProgressState, 0x33) — poll until 02h → Expected: bFBOProgressState == 02h
│   ├── Step 7.7: FBO READ BUFFER (Mode=02h, BufferID=02h, len=4096) — verify entry → Expected: entry valid
│   ├── Step 7.8: QUERY Write Attribute (bFBOExecuteThreshold, 0x32) = 0 → Expected: QUERY RESPONSE Success
│   ├── Step 7.9: QUERY Write Attribute (fFBOControl, 0x31) = 2 → Expected: QUERY RESPONSE Success
│   ├── Step 7.10: QUERY Read Attribute (bFBOProgressState) — poll until 02h → Expected: bFBOProgressState == 02h
│   ├── Step 7.11: VU 0x88 L2P Read — first LBA → Address Y → Expected: Address Y retrieved
│   └── Step 7.12: Verify X != Y (L2P changed by FBO optimization) → Expected: X != Y (L2P changed)
│
├── VC8 (WB Enable): repeat Step 7.1~7.12 with Step 7.1→SET FLAG(fWriteBoosterEn), Step 7.2 total=WB/2 → Expected: 同 VC7, WB enabled
│
├── VC9 (WB Disable→WB Enable mid-flow):
│   ├── Step 9.1: QUERY Clear Flag (fWriteBoosterEn) → Expected: QUERY RESPONSE Success
│   ├── Step 9.2: WRITE(10) — total=TLC_VB/2 → Expected: GOOD Status
│   ├── Step 9.3: VU 0x88 L2P → Address X → Expected: Address X retrieved
│   ├── Step 9.4: QUERY Set Flag (fWriteBoosterEn) → Expected: QUERY RESPONSE Success
│   ├── Step 9.5: WRITE(10) — total=WB/2 → Expected: GOOD Status
│   ├── Step 9.6~9.11: FBO Analysis→Control=1→Poll→ReadBuf→Threshold=0→Control=2→Poll → Expected: 同 Step 7.4~7.10
│   ├── Step 9.12: VU 0x88 L2P → Address Y → Expected: Address Y retrieved
│   └── Step 9.13: Verify X != Y → Expected: X != Y
│
└── Step F.1: READ(10) — Random × 10, LBA=rand(0,total), compare pass → Expected: GOOD Status, Data Match


---

## 自我驗證

- Tree Diagram leaf steps: **0**
- `### Step` sections: **0**
- ✓
