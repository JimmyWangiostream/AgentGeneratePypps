---
type: concept
title: "PSA — Production State Awareness"
tags: [psa, manufacturing, state-machine, attributes]
sources: [spec, script]
created: 2026-06-21
updated: 2026-06-21
---

# PSA — Production State Awareness

## Introduction (Spec 13.6.1)

UFS devices can utilize knowledge about their production status and adjust internal operations accordingly. Content loaded into the storage device prior to device soldering might be corrupted at a higher probability than in regular mode. The UFS device uses "special" internal operations for loading content prior to device soldering which reduces production failures, and switches to "regular" operations post-soldering.

The sensitivity to device soldering is a property of the individual logical unit. Some logical units may be sensitive to device soldering while others may not. Before loading data, the host reads `bPSASensitive` to identify which LUs are sensitive.

Pre-loaded data is data written to the device **after** device configuration is completed (`bConfigDescrLock` is set and device has been reset), and **before** device soldering to the host platform.

The combined maximum amount of data which can be pre-loaded to all sensitive LUs is device-specific and defined by `dPSAMaxDataSize` (Device Descriptor offset 25h–28h, in 4 KB units).

PSA support is indicated by `bUFSFeaturesSupport[bit1] = 1b` in the Device Descriptor.

## State Machine

```
OFF (00h)
  │  host sets bPSAState = Pre-soldering
  ▼
PRE_SOLDERING (01h)
  │  host writes dPSADataSize amount of data to sensitive LUs
  │  host sets bPSAState = Loading Complete
  ▼
LOADING_COMPLETE (02h)
  │  ← device is soldered onto board here (power cycle) →
  │  first WRITE command after power-up triggers automatic transition
  ▼
SOLDERED (03h)  [IRREVERSIBLE]
```

Additional transitions:
- From any pre-SOLDERED state: host may set `bPSAState = Off (00h)`, UNMAP all sensitive LBA ranges, then restart the flow from PRE_SOLDERING.
- The SOLDERED state (03h) cannot be reversed — once set, it is permanent.

## PSA Flow (Spec 13.6.2)

1. **Check support**: `bUFSFeaturesSupport[1] = 1b`
2. **Read capacity**: read `dPSAMaxDataSize` from Device Descriptor (4 KB units)
3. **Set data size**: write `dPSADataSize` attribute (IDN 16h) — must be ≤ `dPSAMaxDataSize`; setting above this value returns GENERAL FAILURE
4. **Prerequisite**: `bConfigDescrLock` must already be set (=1) and the device must have been reset before PSA flow begins
5. **UNMAP**: issue UNMAP for the entire LBA range of each LU with `bPSASensitive = 01h` to ensure all LBAs are unmapped
6. **Enter Pre-soldering**: write `bPSAState = 01h` (Pre-soldering)
7. **Load PSA data**: write data via WRITE commands to LUs with `bPSASensitive = 01h`
   - Host should not write to the same LBA more than once during PSA flow (undefined behavior)
   - Count only writes to `bPSASensitive = 01h` LUs toward the `dPSADataSize` limit
8. **Complete loading**: write `bPSAState = 02h` (Loading Complete)
9. **Optional verify**: host may read back pre-loaded data; if verification fails, set `bPSAState = Off` and restart
10. **Power down**: device is powered down and soldered onto the board
11. **Power up**: device powers up with `bPSAState = Loading Complete`
12. **Automatic SOLDERED transition**: device automatically sets `bPSAState = 03h` (Soldered) during processing of the **first WRITE command** after this power-up

> At 'Loading Complete' state (prior to soldering), the device may stop using special internal operations and resume regular operations. Therefore the host should not write data to the device after setting Loading Complete, as data may be corrupted during soldering. A WRITE command in this situation may result in an error.

## Key Attributes and Descriptors

| Entity | IDN / Offset | Type | Description |
|--------|-------------|------|-------------|
| `bUFSFeaturesSupport` | Device Descriptor 1Fh | Read | bit[1]=1 → PSA supported |
| `dPSAMaxDataSize` | Device Descriptor 25h–28h | Read | Maximum PSA data in 4 KB units |
| `bPSAStateTimeout` | Device Descriptor 29h | Read | Timeout exponent: `2^value × 100 ms` |
| `bPSASensitive` | Unit Descriptor (per-LU) | Read | 01h = this LU is sensitive to soldering |
| `bPSAState` | Attribute IDN 15h | R/W Persistent | Current PSA state: 00h=Off, 01h=Pre-soldering, 02h=Loading Complete, 03h=Soldered |
| `dPSADataSize` | Attribute IDN 16h | R/W Persistent | Data host plans to pre-load (4 KB units); must be ≤ `dPSAMaxDataSize` |
| `bConfigDescrLock` | Attribute IDN 0Bh | Write-once | Must be set (=1) before PSA flow begins |

### `dPSAMaxDataSize` vs `dPSADataSize`

- `dPSAMaxDataSize` — device capability upper bound (read from Device Descriptor, 4-byte field)
- `dPSADataSize` — host declaration of how much data it intends to write (attribute IDN 16h, must not exceed `dPSAMaxDataSize`)

Writing `dPSADataSize > dPSAMaxDataSize` causes GENERAL FAILURE. Writing more actual data than `dPSADataSize` during PRE_SOLDERING may result in data corruption during soldering (device behavior undefined).

## PSA State Timeout

State transitions may involve internal device operations requiring up to `bPSAStateTimeout` to complete:

```python
psa_timeout_ms = pow(2, bPSAStateTimeout) * 100  # milliseconds
```

## Key Claims (Spec §13.6)

- **[Ch 67]** PSA state Soldered (03h) is irreversible — cannot be changed back.
- **[Ch 67]** The device automatically sets `bPSAState = Soldered` during processing of the first WRITE command after a power-up when `bPSAState = Loading Complete`.
- `bConfigDescrLock` must be set (=1) and device must have been reset before PSA data loading begins.
- PSA flow may only be initiated if all LBAs in `bPSASensitive = 01h` LUs are unmapped.

## Script Patterns

### PSA VU Commands (Script/PSA)

| VU | Function |
|----|----------|
| `405C` | `issue_405C_get_PSA_post_reflow_progress()` — reads post-reflow migration progress |
| `404F` | `issue_404F_get_PSA_migration_state()` — reads current PSA migration state |
| `4050` | `issue_4050_check_PSA_buffer_size()` — reads remaining PSA buffer size |
| VendorCmdWrite | `VU_clear_PSA_state()` — clears PSA state in post-process cleanup |

### PSA State Attributes (API)

```python
api.write_attribute(idn=AttributeIDN.PSA_DATA_SIZE, val=param.gDevice.l37_psa_max_data_size)
api.write_attribute(idn=AttributeIDN.PSA_STATE, val=api.PSAState.PRE_SOLDERING)
# ... write PSA data ...
api.write_attribute(idn=AttributeIDN.PSA_STATE, val=api.PSAState.LOADING_COMPLETE)
# post-process cleanup:
api.write_attribute(idn=AttributeIDN.PSA_STATE, val=api.PSAState.OFF)
```

### PSA Flow in Tests (Script/outgoing_slx)

```python
api.write_attribute(PSA_DATA_SIZE)        # step 1
api.write_attribute(PSA_STATE=PRE_SOLDERING)  # step 2
api.sequential_write()                     # step 3
api.write_attribute(PSA_STATE=LOADING_COMPLETE)  # step 4
```

### Interaction with HIR

HIR (High Intensity Refresh) is **rejected** during the PSA flow (PRE_SOLDERING / LOADING_COMPLETE states). Media scan is also blocked during these states. After SOLDERED state, PSA VBs are excluded from scan results.

See [[hir]] for HIR trigger behavior. See [[refresh]] for Refresh interaction.

## Related Entities

- [[write-booster]] — WB buffer availability changes during PSA state transitions
- [[lun]] — `bPSASensitive` flag per-LU; only Normal LUNs can be PSA-sensitive
- [[health-report]] — PSA internal state visible at health report payload offset 469
- [[exception-events]] — HIR/HID are rejected during PSA active states
