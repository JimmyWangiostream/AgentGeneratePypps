---
type: entity
title: "Inhibition Timeout"
tags: [power-management, hwsetting, timing, background-operations, gc]
sources: [spec, script, modeldefault]
created: 2026-06-21
updated: 2026-06-21
aliases: [inhibition_time, INHIBITION_TIME, inhibition time]
---

# Inhibition Timeout

The duration (in seconds) a UFS device waits in idle before entering inhibition mode. During the inhibition window, background (BG) tasks — including Garbage Collection, Media Scan, Read Disturb scans, HIR, HID, and Refresh — are blocked from executing. Once the window expires, blocked tasks resume normally.

Configured via `HwSettingField.INHIBITION_TIME` and persists across power cycles.

## Attribute

- **Field:** `api.HwSettingField.INHIBITION_TIME`
- **Type:** Integer (seconds)
- **FW register:** `gInhibitMgr.lock` — returns `1` when inhibition is active, `0` when inactive
- **Read method:** `get_hwsetting_inhibition_time()` — reads configured value from HwSetting

## Valid Values

| Value | Meaning |
|-------|---------|
| `0` | Immediate inhibition on idle (zero-timeout special case; `gInhibitMgr.lock` already `0` after power cycle) |
| `30–255` | Wait N seconds before inhibition window closes |
| `180` | **Default value (ModelDefault)** |

Test sweep values used across Script patterns: `[180, 150, 90, 60, 30, 210, 240, 255]`

## Default Value

**180 seconds** — from [[modeldefault]] (`HwSettingField.INHIBITION_TIME = 180`).

## How to Set

```python
self.hw_setting.set_local_val(api.HwSettingField.INHIBITION_TIME, sec)
self.hw_setting.set_to_device()
self.power_cycle()   # setting takes effect after power cycle
```

## How to Verify Active Inhibition

Check `gInhibitMgr.lock` while inhibition is active; it should be `1`:

```python
# Verify BG task is blocked during inhibition window
value = cast(int, read_fw_value('gInhibitMgr.lock'))
assert value == 1   # inhibition is active, BG task blocked
```

After the inhibition window expires, `gInhibitMgr.lock` transitions to `0`:

```python
time.sleep(self.inhibition_time_sec)
value = cast(int, read_fw_value('gInhibitMgr.lock'))
assert value == 0   # inhibition window closed, BG tasks can run
```

Zero-timeout case: after power cycle, `gInhibitMgr.lock` should already be `0` immediately.

## Exiting the Inhibition Window

The inhibition window can be exited programmatically by issuing **1001 consecutive reads**:

```python
leave_inhibition_mode()   # issues 1001 consecutive reads → exits inhibition window
```

This is used in test teardown to ensure BG tasks are unblocked for post-verification.

## Spec Context

While not directly named "inhibition" in the JEDEC UFS 4.1 spec (JEDEC Standard No. 220G), the background operations framework it relies on includes:

- `fBackgroundOpsEn` (Flag IDN 04h): enables/disables BG operations globally
- `wExceptionEventStatus` bit[2]: `URGENT_BKOPS` — signals urgent BG operations needed
- BG operations include GC, Refresh, Read Scan, Media Scan, etc.

The inhibition mechanism is a vendor-specific (Micron) extension layered on top of the standard BG operations model.

## BG Tasks Covered by Inhibition

| Test | BG Task Blocked |
|------|----------------|
| 0001 | Timer behavior — disable/enable timing |
| 0002 | Garbage Collection (GC) |
| 0003 | Garbage Collection (GC) detailed |
| 0004 | Media Scan (MS), BFEA, Read Disturb (RD) |
| 0005 | Bad Block Management (BBM) scan |
| 0006 | Read Back — Open TLC blocks |
| 0007 | HIR (High Intensity Refresh) Read Back |
| 0008 | Purge Read Back |
| 0009 | HID (Host-Initiated Defrag) Read Back |
| 0010 | PSA Refresh |
| 0011 | Other Refresh tasks |

## Script Pattern — Key Helper Functions (mutual_fun.py)

| Function | Description |
|----------|-------------|
| `leave_inhibition_mode()` | Issues 1001 consecutive reads to exit inhibition window |
| `trigger_read_disturb()` | Triggers a Read Disturb scan |
| `trigger_wear_leveling()` | Triggers Wear Leveling refresh |
| `trigger_read_scan_UECC()` | Injects UECC to initiate a read scan |
| `trigger_refresh()` | Triggers HIR (High Intensity Refresh) |
| `polling_bkops_idle()` | Polls `BG_OP_STATUS` until 0 (idle) |
| `polling_bfea_idle()` | Polls BFEA idle state (2000 s timeout) |
| `get_hwsetting_inhibition_time()` | Reads configured inhibition time from HwSetting |
| `power_cycle()` | Random HW_RESET (powerdown=False or True) + `access_vendor_mode()` |

## Standard Test Pattern (0003–0011)

```
1. Write data to prepare target blocks
2. Trigger the relevant BG task
3. Verify gInhibitMgr.lock == 1  →  task is blocked
4. Call leave_inhibition_mode()   →  1001 consecutive reads
5. Verify BG task resumes and completes normally
```

## Script References

- `Script/pattern/Inhibition_time/mutual_fun.py` — shared helpers
- `Script/pattern/Inhibition_time/PSW_F_P3_InhibitionTime_0001_Disable_Enable_Test.py`
- 11 test scripts total: `PSW_F_P3_InhibitionTime_0001` through `PSW_F_P3_InhibitionTime_0011`

## Related

[[power-modes]] | [[thermal-protection-mode]] | [[background-operations]] | [[power-management]] | [[psa-state]] | [[modeldefault]]
