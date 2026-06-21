---
type: entity
title: "Device Health Descriptor (IDN 09h)"
tags: [descriptor, health, eol, lifetime, query, ufs]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
aliases: [Device Health Descriptor, IDN 09h, Health Descriptor, bDescriptorIDN 09h]
---

# Device Health Descriptor (IDN 09h)

The Device Health Descriptor provides device wear and lifetime information. It is used to monitor the health of the UFS device's NAND flash, including End-of-Life (EOL) prediction, life-time estimate, and refresh progress tracking.

- **IDN**: 09h
- **bLength**: 2Dh (45 bytes)
- **INDEX**: 00h, SELECTOR: 00h
- **Access**: Read only (OPCODE=01h)

## Field Table

| Offset | Field | Value / Notes |
|--------|-------|---------------|
| 00h | bLength | 2Dh |
| 01h | bDescriptorIDN | 09h |
| 02h | bPreEOLInfo | Pre-EOL information (see enum below) |
| 03h | bDeviceLifeTimeEstA | Life-time estimate for memory type A (see enum below) |
| 04h | bDeviceLifeTimeEstB | Life-time estimate for memory type B (see enum below) |
| 05h–24h | VendorPropInfo | 32 bytes vendor-specific health info |
| 25h–28h | dRefreshTotalCount | Total number of refresh operations completed |
| 29h–2Ch | dRefreshProgress | Progress indicator of current/last refresh operation |

## Field Enumerations

### bPreEOLInfo (02h) — Pre-End-Of-Life Information

| Value | Meaning |
|-------|---------|
| 00h | Not defined (no info available) |
| 01h | Normal — reserved blocks within specification |
| 02h | Warning — consumed >= 80% of reserved blocks |
| 03h | Critical — consumed >= 90% of reserved blocks |

> At 02h (Warning), plan for device replacement soon.
> At 03h (Critical), device is at risk of failure; immediate action required.

### bDeviceLifeTimeEstA / bDeviceLifeTimeEstB (03h, 04h) — Lifetime Estimate

These fields estimate the percentage of device lifetime consumed for two different memory types (A and B, as defined by the manufacturer).

| Value | Meaning |
|-------|---------|
| 00h | No information available |
| 01h | 0%–10% consumed |
| 02h | 10%–20% consumed |
| 03h | 20%–30% consumed |
| 04h | 30%–40% consumed |
| 05h | 40%–50% consumed |
| 06h | 50%–60% consumed |
| 07h | 60%–70% consumed |
| 08h | 70%–80% consumed |
| 09h | 80%–90% consumed |
| 0Ah | 90%–100% consumed |
| 0Bh | Exceeded (device lifetime has been exceeded) |

## Refresh-Related Fields

### dRefreshTotalCount (25h–28h)
32-bit counter of total successful refresh operations since device manufacture. Monotonically increasing.

### dRefreshProgress (29h–2Ch)
Progress of the current (or most recently completed) refresh operation. Interpretation is device-specific; used with [[attributes]] `bRefreshStatus` for monitoring.

## Exception Events

The Device Health Descriptor status feeds into exception events:
- `wExceptionEventStatus` bit[7] = `DEVICE_HEALTH_EVENT` — set when device health condition requires host attention
- Enable via `wExceptionEventControl` bit[7]

## Usage Example

```python
# Read Device Health Descriptor
resp = query_read_descriptor(idn=0x09, index=0x00, selector=0x00)

pre_eol       = resp[0x02]
life_est_a    = resp[0x03]
life_est_b    = resp[0x04]
refresh_total = int.from_bytes(resp[0x25:0x29], 'big')
refresh_prog  = int.from_bytes(resp[0x29:0x2D], 'big')

# Interpret Pre-EOL
eol_map = {0x00: "No info", 0x01: "Normal", 0x02: "Warning (>=80%)", 0x03: "Critical (>=90%)"}
print(f"Pre-EOL: {eol_map.get(pre_eol, 'Unknown')}")

# Interpret lifetime estimate
def decode_lifetime(val):
    if val == 0x00: return "No info"
    if val == 0x0B: return "Exceeded"
    pct = val * 10
    return f"{pct-10}%–{pct}% consumed"

print(f"Lifetime A: {decode_lifetime(life_est_a)}")
print(f"Lifetime B: {decode_lifetime(life_est_b)}")
print(f"Refresh operations completed: {refresh_total}")
```

## Related

[[device-descriptor]] | [[unit-descriptor]] | [[attributes]] | [[write-booster]]

## Sources

- JEDEC UFS 4.1 (JESD220G) — Device Health Descriptor section (IDN=09h, bLength=2Dh)
- Section 1.1 Descriptors, UFS41_Structured_Knowledge_Report
