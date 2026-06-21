---
title: PF044_1493_D3_SLC_FFU_LowHighSpeed-Normalized-TestFlow
type: normalized-test-flow
tags: [test-flow, ufs, pf044_1493, scsi-cmd, ffu, d3-slc, wb, speed-change]
description: PF044_1493 D3 SLC FFU Low High Speed — D3 SLC GC + FFU × 4 Speed modes。
sources: [JIRA: PF044_1493 (SYSTCUFS-1762)]
---

# PF044_1493 正規化 Test Flow

## IC: 8317 BiCS5 KIC, UFS 3.1, WB support

## 測試架構（Tree Diagram — 含 Expected）

```
PF044_1493 Test Flow
│
├── Phase 0: 初始化
│   ├── Step 0.1: HW Check (8317 BiCS5 KIC, UFS 3.1, WB) → Expected: 支援, NOT SUPPORTED otherwise
│   ├── Step 0.2: QUERY Write Descriptor — Config WB → Expected: QUERY RESPONSE Success
│   ├── Step 0.3: VU HW Setting — Enable same-version FFU → Expected: FFU feature enabled
│   ├── Step 0.4: Search FFU FW bin (version T) → Expected: FW bin found
│   ├── Step 0.5: UNMAP + SET FLAG (fPurgeEnable) — Precondition → Expected: bPurgeStatus == 0x00
│   └── Step 0.6: VU — Check FW debug event (D3 SLC) valid → Expected: D3 SLC event valid
│
└── Loop (per Speed Mode: Gear1 PWM / PWM Auto / Gear4 HS / HS Auto)
    ├── Step L.1: UniPro DME — Speed change → Expected: Speed change success
    ├── Step L.2: QUERY Clear Flag (fBackgroundOpsEn, 0x04) → Expected: QUERY RESPONSE Success
    ├── Step L.3: WRITE(10) — Seq WB max, LUN0, LBA=0, CS=512KB → Expected: GOOD Status
    ├── Step L.4: WRITE(10) — Seq 1GB, LUN0, LBA=WB max+1, FUA=1, CS=512KB → Expected: GOOD Status
    ├── Step L.5: VU — Verify D3 SLC GC triggered → Expected: D3 SLC GC confirmed
    ├── Step L.6: WRITE(10) — Small FUA, LBA=rand, CS=4K, FUA=1 → Expected: GOOD Status
    ├── Step L.7: WRITE BUFFER (FFU) — download (4K/16K/256K/all) → Expected: FFU download success
    ├── Step L.8: WRITE(10) — Big FUA, LBA=rand, CS=512K, FUA=1 → Expected: GOOD Status
    ├── Step L.9: Power Cycle Reset → Expected: Reset device success
    ├── Step L.10: QUERY Read Attribute (FFUStatus) — expect 0x01 → Expected: FFUStatus == 0x01 (Successful)
    └── Step L.11: QUERY Read Descriptor — verify SVN = target → Expected: SVN version == target
```

---

## 附錄

| Opcode | Command | 使用位置 |
|:---|:---|:---|
| 0x2A | WRITE(10) | L.3, L.4, L.6, L.8 |
| 0x3B | WRITE BUFFER (FFU) | L.7 |
| 0x42 | UNMAP | 0.5 |

## 自我驗證

- Tree leaf: **17** (0.1~0.6=6, L.1~L.11=11) ✓ 每個有 `→ Expected:` ✓
