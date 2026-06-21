---
type: concept
title: "Refresh Operation"
tags: [refresh, data-retention, background-operations, attributes, flags, hir]
sources: [spec, script]
created: 2026-06-21
updated: 2026-06-21
---

# Refresh Operation

The Refresh operation relocates data to mitigate NAND retention degradation. It is supported when `dExtendedUFSFeaturesSupport bit[3] = 1` (Device Descriptor offset 4Fh–52h) and `bUFSFeaturesSupport bit[3] = 1` (offset 1Fh).

Refresh re-programs data stored in NAND cells to fresh locations, counteracting charge loss that causes read errors over time or across temperature extremes.

## Trigger Methods

### Manual Trigger

Host sets `fRefreshEnable` (Flag IDN 07h) to 1. This is a write-only volatile flag — it is automatically cleared when the operation completes.

Precondition: command queues of all logical units must be empty before the flag can be set.

### Automatic (HIR — Host-Initiated Refresh)

Temperature-triggered refresh (XTEMP): when NAND temperature goes out of range (too hot or too cold), the device books VBs for refresh automatically. The host is notified via `wExceptionEventStatus bit[11]` (device-level exception event).

### Booking Queue (Script)

Script-layer VU commands for refresh booking:

| VU | Function |
|----|----------|
| `C087` | `issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type, VB_list, booking_user)` — enqueue VBs at HP/MP/LP priority |
| `C088` | `issue_C088_to_start_or_stop_refresh(bParameter0)` — start (mode 1), stop (mode 2), disable enqueue (mode 4), enable enqueue (mode 5) |
| `40C5` | `issue_40C5_to_get_booking_queue()` — read current booking queue state |

## Attributes

| IDN | Name | Access | Description |
|-----|------|--------|-------------|
| 2Ch | `bRefreshStatus` | Read only | Same state encoding as `bPurgeStatus`: 00h=idle, 01h=in progress, 02h=stopped, 03h=completed, 04h=failed (queue not empty), 05h=general failure |
| 2Dh | `bRefreshFreq` | Persistent | Refresh frequency in months: 01h=1 month, FFh=255 months |
| 2Eh | `bRefreshUnit` | Persistent | 00h=minimum capability (device decides scope), 01h=100% of device |
| 2Fh | `bRefreshMethod` | Persistent | 00h=not defined (error if fRefreshEnable set), 01h=Manual-Force, 02h=Manual-Selective |

### `bRefreshMethod` Modes

| Value | Mode | Behavior |
|-------|------|----------|
| 00h | Not defined | Setting `fRefreshEnable` returns GENERAL FAILURE (FFh response) |
| 01h | Manual-Force | Refresh all booked VBs; forced execution |
| 02h | Manual-Selective | Selective refresh; progress increments by `(1 / total_vb_cnt) × 100000` per slice |

### `bRefreshStatus` States

| Value | State | Meaning |
|-------|-------|---------|
| 00h | Idle | No refresh in progress |
| 01h | In progress | Refresh executing |
| 02h | Stopped | Refresh interrupted by host |
| 03h | Completed | Refresh finished successfully |
| 04h | Failed — queue not empty | Could not complete with pending commands |
| 05h | General failure | Other error (also used by HIR: XTEMP booking triggers 05h then 00h) |

## Flag

| IDN | Name | Access | Default | Description |
|-----|------|--------|---------|-------------|
| 07h | `fRefreshEnable` | Write-only volatile | 0 | Triggers manual refresh; auto-cleared on completion; requires `bRefreshMethod ≠ 00h` |

## Device Health Descriptor

Two counters in the Device Health Descriptor (IDN 09h) track refresh history:

| Field | Description |
|-------|-------------|
| `dRefreshTotalCount` | Total number of refresh operations completed |
| `dRefreshProgress` | Progress of current or last refresh (0–100) |

## HIR (Host-Initiated Refresh / XTEMP Refresh)

HIR refers to the temperature-triggered refresh booking that occurs when NAND exceeds temperature thresholds. The script-layer term for this is XTEMP refresh.

### HIR Flow (Script/hir)

1. NAND temperature set to out-of-range value (exceeds `XTEMP_REFRESH_T2`)
2. Device automatically books VBs for refresh (`XTEMP_BOOKING | BOOKING_IN_MP`)
3. `wExceptionEventStatus bit[11]` asserted (device-level exception)
4. `bRefreshStatus` transitions to 05h (XTEMP booking state), then to 00h (idle) after completion
5. Host polls `bRefreshStatus` until 00h

```python
api.set_flag(FlagIDN.REFRESH_EN)
# poll:
api.read_attribute(AttributeIDN.REFRESH_STATUS)  # wait for 05h then 00h
```

### Temperature Offset (Script)

```
TEMP_GAP = 37°C   # device reports internal temp + 37°C offset
```

Set fake NAND temperature via:
```python
project_api.issue_D08A_set_vu_temperature(SetNandTemperature)
```

### VB Refresh Priority Order (HIR_0004)

Refresh executes VBs in the following priority order:

1. `CURRENT_VB` — currently open VB
2. `OPENVB_TLC_SLC` — other open VBs
3. `TABLE_AND_SYSTEM` — system table blocks
4. `CLOSED_TLC_VB` — closed TLC blocks
5. `CLOSED_SLC_STATIC` — closed SLC static blocks
6. `CLOSED_SLC_DYNAMIC` — closed SLC dynamic blocks

### Booking Queue Priority (Script/refresh)

The booking queue supports three priority levels:

| Priority | Abbreviation | Trigger Examples |
|----------|-------------|-----------------|
| High (HP) | HP | UECC-triggered refresh, read disturb scan |
| Medium (MP) | MP | WL high gap (static wear leveling, high EC delta) |
| Low (LP) | LP | WL low gap |

Deduplication rule: HP takes precedence over MP/LP for the same VB — a VB already in queue at MP/LP is upgraded to HP.

## Refresh Trigger Types (Script/refresh_0004)

| Trigger | Booking User | Priority |
|---------|-------------|----------|
| ReadDisturb | `RD_SCAN_BOOKING_1` | High |
| ReadUECC | `EH_BOOKSIGNALUECC_BOOKING_0` | High |
| sWL LowGap | `SWL_REFRESH_LOW_GAP` | Low |
| sWL HighGap | `SWL_REFRESH_HIGH_GAP` | Medium |
| HIR/XTEMP | `trigger_hir_refresh()` | High |
| PSA | `trigger_psa_refresh()` | (PSA state) |

## Event Logs

| Log ID | Name | Description |
|--------|------|-------------|
| 0x3006 | `BookRefEventLog` | Generated when VB is booked for refresh |
| 0x3051 | `RefStartEventLog` | Generated when refresh starts on a VB |

## Inhibition

Refresh can be blocked during specific operational states (see [[inhibition-time]]). During PSA PRE_SOLDERING and LOADING_COMPLETE states, refresh is blocked.

## Configuration Persistence

- `bRefreshFreq`, `bRefreshUnit`, `bRefreshMethod` are **persistent** attributes (survive power cycle)
- These attributes persist across ATS (Abort Task Set), H8, SSU, POR, and SPOR
- LU reconfiguration resets `dRefreshProgress` to 0

## Related Entities

- [[flags]] — `fRefreshEnable` (IDN 07h) triggers manual refresh
- [[exception-events]] — bit 11 of `wExceptionEventStatus` for XTEMP/HIR alert
- [[health-report]] — `dRefreshTotalCount`, `dRefreshProgress` in Device Health Descriptor
- [[psa]] — refresh is blocked during PSA PRE_SOLDERING and LOADING_COMPLETE states
- [[background-operations]] — refresh competes with other BG operations
