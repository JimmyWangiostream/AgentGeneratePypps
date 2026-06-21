---
type: concept
title: "Exception Events"
tags: [exception-events, attributes, temperature, writebooster, health]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
---

# Exception Events

Exception Events are an asynchronous notification mechanism allowing the device to alert the host to conditions requiring attention. The device signals an event by setting `EVENT_ALERT` in the RESPONSE UPIU Device Information field; the host then reads `wExceptionEventStatus` to determine which event(s) are active.

## Signal Path

1. **Device detects condition** → sets corresponding bit in `wExceptionEventStatus` (IDN 0Eh)
2. **Device sets `EVENT_ALERT`** → `bit[0]` of Device Information field in the next RESPONSE UPIU
3. **Host reads `EVENT_ALERT = 1`** → issues QUERY REQUEST to read `wExceptionEventStatus`
4. **Device clears the bit** in `wExceptionEventStatus` when the status is read by the host
5. **Host takes action** based on which bits are set

## Control Attribute

`wExceptionEventControl` (Attribute IDN 0Dh):
- **Volatile** (resets on power cycle)
- 2-byte register; bits 0–11 map to corresponding event enable/disable controls
- Set a bit to **enable** the corresponding event notification
- Clear a bit to **disable** the corresponding event notification

## Status Attribute

`wExceptionEventStatus` (Attribute IDN 0Eh):
- **Read-only**
- 2-byte register; bits 0–10 (and bit 11 for XTEMP/HIR) defined
- A set bit indicates an active/pending exception condition
- Bits are cleared when the host reads the attribute

## Exception Event Bits

| Bit | Name | Description |
|-----|------|-------------|
| 0 | `TOO_HIGH_TEMP` | Device temperature exceeded upper threshold |
| 1 | `TOO_LOW_TEMP` | Device temperature fell below lower threshold |
| 2 | `URGENT_BKOPS` | Background operations critically needed (`bBackgroundOpStatus = 03h`) |
| 3 | `PERFORMANCE_THROTTLING` | Device is throttling performance due to thermal or other constraints |
| 4 | `WRITEBOOSTER_FLUSH_NEEDED` | WriteBooster buffer needs to be flushed (also used for WB buffer resize result) |
| 5 | `DYNAMIC_CAPACITY_NEEDED` | Device requests physical resource removal (see `dDynCapNeeded`) |
| 6 | `CORRECTION_NEEDED` | Corrective action required (e.g., data integrity concern) |
| 7 | `DEVICE_HEALTH_EVENT` | Device health indicator has changed (e.g., `bPreEOLInfo` or `bDeviceLifeTimeEstA/B` updated) |
| 8 | `DEVICE_LEVEL_EXCEPTION` | Device-level exception not covered by other bits |
| 11 | `XTEMP_REFRESH` | (Script-layer) HIR/XTEMP temperature-triggered refresh booking; `bRefreshStatus` transitions to 05h |

> Note: bit 11 is referenced in script test `HIR_0001` and `HIR_0002` as `wExceptionEventStatus BIT11`. This corresponds to a device-specific extension for XTEMP/HIR notification beyond the standard bits 0–8.

## Bit Details

### bit 0 — `TOO_HIGH_TEMP`

Device temperature has exceeded the high threshold. Host should reduce I/O load or allow device to cool. Relevant to XTEMP refresh triggering.

### bit 1 — `TOO_LOW_TEMP`

Device temperature is below the low threshold. Cold temperature can cause read errors. Related to XTEMP cold-triggered refresh booking.

### bit 2 — `URGENT_BKOPS`

`bBackgroundOpStatus` (Attribute IDN 05h) has reached level 03h (critical). The device urgently needs to run background operations. Host should pause I/O to allow BG operations to proceed.

### bit 3 — `PERFORMANCE_THROTTLING`

Device is actively limiting performance. May indicate thermal protection activation or other resource constraints.

### bit 4 — `WRITEBOOSTER_FLUSH_NEEDED`

Two scenarios:
1. WriteBooster buffer is filling up and needs flushing — host should set `fWriteBoosterBufferFlushEn = 1`
2. WriteBooster buffer resize operation (triggered by `bWriteBoosterBufferResizeEn`) has completed

### bit 5 — `DYNAMIC_CAPACITY_NEEDED`

Device has updated `dDynCapNeeded` (Attribute IDN 09h). Host should read `dDynCapNeeded` per LU and set `fPhyResourceRemoval` (Flag IDN 08h) to trigger physical resource release.

### bit 6 — `CORRECTION_NEEDED`

Device has detected a condition requiring corrective data management action. Device-specific behavior.

### bit 7 — `DEVICE_HEALTH_EVENT`

A health-related descriptor field has changed. Host should re-read the Device Health Descriptor (IDN 09h) to check:
- `bPreEOLInfo` — approaching end of life (02h=warning at ≥80% reserved blocks, 03h=critical at ≥90%)
- `bDeviceLifeTimeEstA` / `bDeviceLifeTimeEstB` — life span estimates (01h–0Ah = 0–100% in 10% steps, 0Bh=exceeded)

### bit 8 — `DEVICE_LEVEL_EXCEPTION`

A device-level exception that does not fall into the other defined categories. Implementation-specific.

## Typical Host Handling

```
Read RESPONSE UPIU
  └─ Device Information bit[0] = EVENT_ALERT?
       └─ Yes: READ ATTRIBUTE wExceptionEventStatus
                └─ bit 2 set? → pause I/O, allow BKOPS
                └─ bit 4 set? → set fWriteBoosterBufferFlushEn
                └─ bit 5 set? → read dDynCapNeeded, set fPhyResourceRemoval
                └─ bit 7 set? → re-read Device Health Descriptor
                └─ bit 0/1 set? → check temp, reduce load or allow cooling
```

## `bBackgroundOpStatus` Reference (Attribute IDN 05h)

| Value | Status | Action |
|-------|--------|--------|
| 00h | Not required | Normal operation |
| 01h | Non-critical | BG ops desired but not urgent |
| 02h | Performance impact | BG ops causing performance degradation |
| 03h | Critical | Triggers `URGENT_BKOPS` exception event |

## Key Claims (Spec)

- `wExceptionEventStatus` is read-only; device clears bits when status is read.
- `wExceptionEventControl` is volatile — resets to 0 on power cycle; host must re-enable events after each power-on.
- `EVENT_ALERT` in RESPONSE UPIU Device Information field (`bit[0]`) is the signal to host that at least one exception event is pending.

## Related Entities

- [[attributes]] — `wExceptionEventControl` (IDN 0Dh), `wExceptionEventStatus` (IDN 0Eh)
- [[write-booster]] — bit 4 `WRITEBOOSTER_FLUSH_NEEDED`
- [[refresh]] — bit 11 `XTEMP_REFRESH` (HIR booking)
- [[health-report]] — bit 7 `DEVICE_HEALTH_EVENT`
- [[background-operations]] — bit 2 `URGENT_BKOPS`
