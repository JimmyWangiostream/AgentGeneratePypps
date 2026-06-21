---
type: entity
title: "LUN — Logical Unit Number"
tags: [lun, storage, configuration, encoding, well-known-lun]
sources: [spec, customerreq, userprompt, modeldefault]
created: 2026-06-21
updated: 2026-06-21
aliases: [LUN, logical unit, LogicalUnit, W-LUN, Well-Known LUN]
---

# LUN — Logical Unit Number

A logical storage partition within a UFS device. Multiple LUNs can coexist on one device, each with its own capacity, memory type, provisioning behavior, and access permissions.

## LUN Types

| Type | W-LUN | LUN Field in UPIU | Commands Supported |
|------|-------|-------------------|--------------------|
| Normal LU (0–31) | — | 00h–1Fh | All UCS commands when bLUEnable=01h |
| REPORT LUNS | 01h | 81h | INQUIRY, REQUEST SENSE, TEST UNIT READY, REPORT LUNS |
| UFS Device | 50h | D0h | INQUIRY, REQUEST SENSE, TEST UNIT READY, START STOP UNIT, FORMAT UNIT |
| Boot | 30h | B0h | INQUIRY, REQUEST SENSE, TEST UNIT READY, READ (6), READ (10), READ (16), READ BUFFER |
| RPMB | 44h | C4h | INQUIRY, REQUEST SENSE, TEST UNIT READY, SECURITY PROTOCOL IN, SECURITY PROTOCOL OUT |

## LUN Field Encoding (Spec)

The LUN field in a UPIU is 8-bit and encoded as follows:

| Bit(s) | Name | Meaning |
|--------|------|---------|
| Bit 7 | WLUN_ID | 0=Normal LU, 1=Well-Known LU |
| Bits 6:0 | UNIT_NUMBER_ID | LUN index (Normal) or W-LUN value (Well-Known) |

**Examples:**
- Normal LU 0: `00h` (bit7=0, UNIT_NUMBER_ID=0)
- Normal LU 5: `05h`
- Boot W-LUN: `B0h` (bit7=1, UNIT_NUMBER_ID=30h)
- RPMB W-LUN: `C4h` (bit7=1, UNIT_NUMBER_ID=44h)
- UFS Device W-LUN: `D0h` (bit7=1, UNIT_NUMBER_ID=50h)

**SAM LUN address format** (for Well-Known LUs): `C1h` prefix followed by W-LUN value.
- Boot: `C1 30 00 00 00 00 00 00`
- RPMB: `C1 44 00 00 00 00 00 00`

## LUN Configuration Parameters (Unit Descriptor)

Configured via [[configuration-descriptor]], readable via [[unit-descriptor]] (IDN=02h):

| Field | Offset in Unit Descriptor | Value / Notes |
|-------|--------------------------|---------------|
| bLUEnable | 03h | 00h=disabled, 01h=enabled |
| bBootLunID | 04h | 00h=not a boot LU, 01h=Boot LU A, 02h=Boot LU B |
| bLUWriteProtect | 05h | 00h=none, 01h=power-on WP, 02h=permanent WP |
| bMemoryType | 08h | 00h=Normal, 03h=SLC, etc. |
| bDataReliability | 09h | 00h=not reliable, 01h=reliable write |
| bLogicalBlockSize | 0Ah | 0Ch=4096 bytes (minimum for UFS) |
| bProvisioningType | 17h | 00h=full provisioned, 02h=thin (TPRZ=0), 03h=thin (TPRZ=1) |
| dNumAllocUnits | 0Bh–0Eh (in config) | See capacity formula below |

### Capacity Allocation Formula

```
dNumAllocUnits = CEILING(
    (LUCapacity × CapAdjFactor) /
    (bAllocationUnitSize × dSegmentSize × 512)
)
```

Where `bAllocationUnitSize` and `dSegmentSize` are from [[geometry-descriptor]].

## Standard Test LUN Allocation (ModelDefault)

```python
TestNormalLun      = 0   # General data
TestEM1Lun         = 1   # Enhanced Memory 1
TestWBLun          = 2   # WriteBooster
TestGCLun          = 3   # Garbage Collection
TestTemperatureLun = 4   # Temperature monitoring
```

## Default LUN When TC Does Not Specify *(UserPrompt overrides ModelDefault)*

**UserPrompt rule (KEPT):** Use the **Enabled LUN with the largest capacity** (MaxCapacity Enabled LUN).

**ModelDefault rule (DELETED):** Default to `TestNormalLun = 0`.

*UserPrompt wins per Rule 2 (UserPrompt > ModelDefault). See conflict rules below.*

**Implementation:**

```python
# Do NOT hardcode lun=0
# Select MaxCapacity Enabled LUN:
max_lun = max(
    (lun for lun in range(param.gMaxNumberLU)
     if param.gUnit[lun].b3_lu_enable != api.LUNEnable.DISABLE),
    key=lambda lun: param.gUnit[lun].q11_logical_block_count
)
```

## WriteBooster LUN Constraint *(CustomerReq)*

For WB Attribute/Flag operations targeting a specific LUN:

| Constraint | Required Value | Source |
|------------|---------------|--------|
| LU type | Normal LUN only | CustomerReq |
| Boot LUN | Must NOT be a Boot LUN (bBootLunID=00h) | CustomerReq |
| Index range | 0–7 only | CustomerReq |

Violation of these constraints causes the device to return QUERY RESPONSE `FCh` (invalid INDEX).

*CustomerReq wins per Rule 1 (CustomerReq > Spec) if Spec allows broader usage.*

See [[write-booster]] for full WriteBooster configuration details.

## PSA Sensitivity

LUNs can be PSA-sensitive (`bPSASensitive == 01h`) or not:
- Normal memory LUNs → PSA sensitive (filled with data, then unmapped during PSA flow)
- Enhanced Memory (EM1) LUNs → not PSA sensitive

In PSA flow, sensitive LUNs are filled with data then unmapped before transitioning state. See [[psa-state]].

## Conflict Rules Summary

| Rule | Priority | Description |
|------|----------|-------------|
| Rule 1 | CustomerReq > Spec | If CustomerReq and Spec conflict, use CustomerReq value; annotate Spec value as DELETED |
| Rule 2 | UserPrompt > ModelDefault | If UserPrompt and ModelDefault conflict, use UserPrompt value; annotate ModelDefault as DELETED |

Applied conflicts in this file:
- Default LUN selection: UserPrompt (MaxCapacity Enabled LUN) **overrides** ModelDefault (LUN 0) — per Rule 2
- WriteBooster LUN scope: CustomerReq (Normal, non-Boot, index 0–7) **overrides** any broader Spec allowance — per Rule 1

## Usage Example

```python
# Enumerate all enabled LUNs and find the one with maximum capacity
enabled_luns = []
for lun_idx in range(param.gMaxNumberLU):
    unit_desc = query_read_descriptor(idn=0x02, index=lun_idx, selector=0x00)
    if unit_desc[0x03] == 0x01:  # bLUEnable = enabled
        block_count = int.from_bytes(unit_desc[0x0B:0x13], 'big')
        block_size  = 2 ** unit_desc[0x0A]
        enabled_luns.append((lun_idx, block_count * block_size))

# Select MaxCapacity Enabled LUN (UserPrompt rule)
default_lun = max(enabled_luns, key=lambda x: x[1])[0]

# Verify WriteBooster LUN constraints (CustomerReq rule)
def is_valid_wb_lun(lun_idx):
    if lun_idx > 7:
        return False  # CustomerReq: index must be 0-7
    unit_desc = query_read_descriptor(idn=0x02, index=lun_idx, selector=0x00)
    if unit_desc[0x04] != 0x00:
        return False  # CustomerReq: must not be Boot LUN
    return True
```

## Related

[[unit-descriptor]] | [[configuration-descriptor]] | [[device-descriptor]] | [[geometry-descriptor]] | [[psa-state]] | [[write-booster]]

## Sources

- JEDEC UFS 4.1 (JESD220G) — Section on LUN Field Encoding and Logical Units
- Section 1.5 Logical Units, UFS41_Structured_Knowledge_Report
- CustomerReq: WriteBooster LUN constraints (Normal, non-Boot, index 0–7)
- UserPrompt: Default LUN = MaxCapacity Enabled LUN (overrides ModelDefault LUN 0)
