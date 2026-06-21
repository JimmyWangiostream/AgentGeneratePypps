---
type: entity
title: "PSA State"
tags: [psa, attribute, state-machine, bPSAState, pre-soldering]
sources: [spec, script, modeldefault]
created: 2026-06-21
updated: 2026-06-21
aliases: [bPSAState, PSAState, psa_state]
---

# PSA State

The `bPSAState` attribute (IDN 15h) tracks the current phase of the Production State Awareness (PSA) flow. Transitions are one-directional and irreversible once the device is soldered. PSA enables secure pre-loading of data before the device is physically soldered to the host board.

**Spec reference**: JEDEC Standard No. 220G §13.6 (Chapter 67)

## Attribute

| Field | Value |
|-------|-------|
| Attribute IDN | 15h (`api.AttributeIDN.PSA_STATE`) |
| Access | Persistent (read/write with state-transition restrictions) |
| Size | 1 byte |
| Default (factory) | 00h (Off) or 01h (Pre-soldering), device-specific |
| QUERY OPCODE | READ ATTRIBUTE (03h) / WRITE ATTRIBUTE (04h) |

## State Definitions

| State | Value | Description |
|-------|-------|-------------|
| Off | 00h | PSA not active; normal operation or PSA reset |
| Pre-soldering | 01h | PSA data loading phase; device uses special internal write operations for pre-loaded data |
| Loading Complete | 02h | All PSA data loaded; host signals completion; device may stop special operations |
| Soldered | 03h | Device has been soldered; PSA trimming in progress or complete; **irreversible** |

## State Machine

```
          +-------+
          |  Off  |  (00h)
          +---+---+
              |  Host sets bPSAState = Pre-soldering
              |  (requires: all bPSASensitive LU LBAs are unmapped)
              v
     +----------------+
     | Pre-soldering  |  (01h)
     +-------+--------+
             |  Host writes dPSADataSize amount of data to sensitive LUs
             |  Host sets bPSAState = Loading Complete
             v
    +-------------------+
    | Loading Complete  |  (02h)
    +---------+---------+
              |  Device power-up + first WRITE command received
              v
        +-----------+
        | Soldered  |  (03h)  <-- PERMANENT, no further writes accepted
        +-----------+

Restart path (any state before Soldered):
  Pre-soldering OR Loading Complete --> set bPSAState = Off
                                    --> UNMAP all sensitive LU LBAs
                                    --> set bPSAState = Pre-soldering
```

## Transition Rules (Spec §13.6.2)

1. **Off → Pre-soldering**: Valid only when all LBAs in every LU with `bPSASensitive=01h` are unmapped. If LBAs are not unmapped, device returns GENERAL_FAILURE (FFh).

2. **Pre-soldering → Loading Complete**: Host sets after writing `dPSADataSize` total amount of data to sensitive LUs. Device may then stop special internal operations.

3. **Loading Complete → Soldered**: Triggered automatically by the device during processing of the **first WRITE command** after a power-up occurred while `bPSAState = Loading Complete`. Host does NOT write this transition.

4. **Any pre-soldered state → Off (restart)**: Host may restart PSA by:
   - Writing `bPSAState = Off`
   - Sending UNMAP for all pre-loaded data in sensitive LUs
   - Writing `bPSAState = Pre-soldering` again

5. **Soldered state**: Any WRITE ATTRIBUTE to `bPSAState` (any value, including 00h/01h/02h/03h/FFh) returns `GENERAL_FAILURE (FFh)`. This is permanent.

6. **Loading Complete → do NOT write**: After setting Loading Complete, the host must not write data to the device. Device may return an error for WRITEs in this state because special operations have stopped.

## Key Attributes Involved

| Attribute | IDN | Access | Description |
|-----------|-----|--------|-------------|
| bPSAState | 15h | Persistent R/W | Current PSA phase |
| dPSADataSize | 16h | Persistent R/W | Host-declared total data to pre-load in 4KB units; must be ≤ dPSAMaxDataSize |
| dPSAMaxDataSize | Device Descriptor offset 25h–28h | Read only | Hardware limit for PSA data in 4KB units |
| bPSAStateTimeout | Device Descriptor offset 29h | Read only | Timeout = 2^bPSAStateTimeout × 100 ms |
| bUFSFeaturesSupport | Device Descriptor offset 1Fh | Read only | bit[1]=1 means PSA is supported |

### dPSADataSize vs dPSAMaxDataSize

- `dPSADataSize` (IDN 16h, attribute) is set by the **host** to declare how much data it plans to pre-load (4KB units).
- `dPSAMaxDataSize` (Device Descriptor, read-only) is the **hardware limit** set by the device manufacturer.
- If host tries to write `dPSADataSize > dPSAMaxDataSize`, device returns **GENERAL_FAILURE (FFh)**.
- Writing more data than `dPSADataSize` during pre-soldering may result in **undefined behavior / data corruption** during soldering.
- Data written to non-sensitive LUs does NOT count toward `dPSAMaxDataSize`.

## bPSASensitive — LU Sensitivity Field

`bPSASensitive` is a field in the **Unit Descriptor** (not an attribute) that identifies which LUs are sensitive to the soldering process.

| Value | Meaning |
|-------|---------|
| 00h | LU not sensitive to soldering (e.g., Enhanced memory type / EM1) |
| 01h | LU sensitive to soldering (e.g., Normal memory type / MLC) |

**Rules:**
- PSA flow only applies to LUs with `bPSASensitive=01h`.
- Before setting `bPSAState = Pre-soldering`, all LBAs in all `bPSASensitive=01h` LUs must be unmapped.
- Host should read `bPSASensitive` to identify sensitive LUs before starting the PSA flow.
- Only WRITE commands to `bPSASensitive=01h` LUs count toward `dPSADataSize`.

```python
# Read bPSASensitive for all enabled LUs
for lun in range(param.gMaxNumberLU):
    unit_desc = param.gUnit[lun]
    if unit_desc.b3_lu_enable != api.LUNEnable.DISABLE:
        print(f"LUN{lun}: memory_type=0x{unit_desc.b8_memory_type:02X}, "
              f"PSASensitive=0x{unit_desc.b7_psa_sensitive:02X}")
```

## Complete PSA Flow (Spec §13.6.2)

```
1. Check bUFSFeaturesSupport[1] == 1b (PSA supported)
2. Read dPSAMaxDataSize from Device Descriptor
3. Set dPSADataSize = planned data amount (must be <= dPSAMaxDataSize)
4. UNMAP all LBAs in sensitive LUs (bPSASensitive=01h)
5. Write bPSAState = 01h (Pre-soldering)
   -- Device starts using special internal operations for writes to sensitive LUs
6. Pre-load data via WRITE commands to sensitive LUs
   -- Total data must not exceed dPSADataSize
   -- Do NOT write to the same LBA more than once (undefined behavior)
7. Write bPSAState = 02h (Loading Complete)
   -- Device may stop special operations after this
8. [Optional] Verify pre-loaded data with READ commands
9. If verification fails:
   a. Write bPSAState = Off
   b. UNMAP all sensitive LU LBAs
   c. Return to step 5
10. Power down device
11. Solder device onto host platform
12. Power up device
13. Issue first WRITE command
    -- Device automatically sets bPSAState = 03h (Soldered)
    -- PSA trimming begins internally
```

## FW Internal State (Vendor Debug)

```python
# Debug via vendor cmd — FW internal PSA state
debug_info = vendor_cmd.get_debug_info()
fw_psa_state = debug_info.payload[469]
# 0x02 = Post_reflow state (after power cycle when bPSAState was Loading Complete)
```

VU 0x404F: Check PSA migration state and host read trim:
```python
migration_state = project_api.issue_404F_get_PSA_migration_state()
print(f"PSA Ongoing: {migration_state.IsPsaOngoing.value}")
print(f"Host Read Trim: {migration_state.HostReadWithPSATrim.value}")
```

VU 0x4050: Check remaining PSA buffer size:
```python
PSA_buffer = project_api.issue_4050_check_PSA_buffer_size()
print(f"Remain PSA Buffer: {PSA_buffer.RemainPSABufferSize.value}")
```

VU 0x405C: Check PSA post-reflow progress:
```python
reflow_progress = project_api.issue_405C_get_PSA_post_reflow_progress()
print(f"SLC PSA blocks %: {reflow_progress.PercentageForSLCPSAblocks.value}")
```

## VU Clear PSA State (Script Pattern)

Used in production/test to forcibly reset PSA state when device is in Soldered state, enabling PSA re-testing. This is a Vendor-specific operation — not part of the UFS spec.

```python
def VU_clear_PSA_state(self) -> None:
    api.access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdWrite()
    vuc.assign(length=api.DATA_SIZE_4K_BYTE,
               cmd_index=api.VendorCmd.WRITE_PARAMETER,
               cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = api.VendorCmdRuleCdb2.CMD_IN_DOUT
    data = bytearray(b'\x00' * 0x1000)
    data[0]  = 0x04
    data[4]  = 0x01
    data[8]  = 0x44
    data[12] = 0x41
    data[14] = 0x01
    data[16] = 0x15   # bPSAState IDN = 0x15
    data[21] = 0x02
    data[24] = 0x01
    data[28] = 0x46
    data[32] = 0x53
    vuc.data = data
    vuc.enqueue()
    ExecuteCMD.send()
```

This pattern appears in:
- `PSW_F_P3_PSA_0001_PSAflow_Test.py` (standard PSA flow test)
- `PSW_F_P3_PSA_0004_PSAVU_Test.py` (VU-focused PSA test)

## Test Validation — When Soldered

```python
# Verify ALL writes to bPSAState in Soldered state return GENERAL_FAILURE
test_states = [api.PSAState.OFF, api.PSAState.PRE_SOLDERING,
               api.PSAState.LOADING_COMPLETE, api.PSAState.SOLDERED, 0xFF]
for state in test_states:
    write_attr = ExecuteCMD.WriteAttribute()
    write_attr.assign(idn=api.AttributeIDN.PSA_STATE, index=0, selector=0)
    write_attr.set_attr(state)
    write_attr.enqueue()
    response = sendcmd_keeperror(cmd_index=write_attr)
    assert response.upiu.b6_query_response == api.QueryResponseCode.GENERAL_FAILURE, \
        f"Expected GENERAL_FAILURE for state=0x{state:02X}"
```

## Timeout Handling

```python
# bPSAStateTimeout: timeout = 2^value * 100 ms
psa_timeout_ms = pow(2, param.gDevice.b41_psa_state_timeout) * 100
logger.info(f"PSA state transition timeout: {psa_timeout_ms} ms")
```

State transitions (e.g., Off→Pre-soldering) may take up to `psa_timeout_ms` milliseconds before the device returns a response. Host must not time out before this window.

## PSA Health Report Fields

Enhanced Health Report (VU 0x40FE) includes PSA-related fields:

| Field | Description |
|-------|-------------|
| `psastate` | Current PSA state value |
| `psa_off_counter` | Number of times PSA was reset to Off state |
| `psa_data_size` | Current dPSADataSize value |
| `psa_refresh_percentage_progress` | Post-reflow refresh progress (0–100%) |

## Script References

| Script | Coverage |
|--------|---------|
| `PSA/PSW_F_P3_PSA_0001_PSAflow_Test.py` | Full 38-step PSA flow including error paths |
| `PSA/PSW_F_P3_PSA_0002_PSAinterrupt_Test.py` | PSA flow interrupt and resume |
| `PSA/PSW_F_P3_PSA_0003_PSAevnetlog_Test.py` | PSA event log validation |
| `PSA/PSW_F_P3_PSA_0004_PSAVU_Test.py` | VU commands for PSA state inspection |
| `PSA/PSW_F_P3_PSA_0005_PSAwritebootEM1_Test.py` | PSA boot + EM1 write test |
| `PSA/PSW_F_P3_PSA_0006_PSAHIRwithoutInhibit_Test.py` | HIR without inhibit in PSA |
| `apl_system_rebuild/PSW_F_P3_APL_0018_Rebuild_PSA_UECC_Test.py` | PSA with UECC rebuild |
| `apl_system_rebuild/PSW_F_P3_APL_0019_Rebuild_PSA_Test.py` | PSA rebuild flow |

## Related

[[attributes]] | [[flags]] | [[lun]] | [[upiu]] | [[write-booster]] | [[spec]] | [[modeldefault]]
