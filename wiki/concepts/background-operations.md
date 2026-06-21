---
type: concept
title: "Background Operations (BKOPS)"
tags: [bkops, gc, wear-leveling, background]
sources: [spec, modeldefault, pronoun]
created: 2026-06-21
updated: 2026-06-21
---

# Background Operations (BKOPS)

UFS maintenance tasks that run in the background while the device is idle or between commands. Includes Garbage Collection (GC), Wear Leveling (WL), and other firmware housekeeping.

## Key Terms (from [[pronoun]])

| Term | Meaning |
|------|---------|
| **BKOPS** | Background Operations umbrella term |
| **GC** | Garbage Collection — reclaims invalid (erased) flash blocks |
| **WL** | Wear Leveling — distributes writes to extend flash lifespan |

## Attributes

| Attribute | Purpose |
|-----------|---------|
| `BKOPS_STATUS` | Reports current background operation urgency level |
| `BKOPS_ENABLE` | Flag to enable/disable BKOPS |

## Defaults (ModelDefault)

```python
BKOPS_ENABLED      = True
BKOPS_FLUSH_ENABLE = True
```

## Inhibition Interaction

[[inhibition-timeout]] governs how long the device waits idle before the inhibition manager locks out certain operations. BKOPS may be inhibited during this window. Pattern `PSW_F_P3_InhibitionTime_0002_BG_Task_Inhibition_Test.py` specifically tests BKOPS inhibition.

## DCMD Reference

- `DCMD19 (0x13)` — `BKOPS_SPOR_DEBUG`: Detects active BKOPS and executes SPOR test

## Related

[[inhibition-timeout]] | [[pronoun]] | [[spec]] | [[modeldefault]]
