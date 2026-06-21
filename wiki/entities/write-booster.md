---
type: entity
title: "Write Booster"
tags: [write-booster, performance, attribute, flag]
sources: [spec, customerreq, modeldefault]
created: 2026-06-21
updated: 2026-06-21
aliases: [WB, WriteBooster, WRITEBOOSTER]
---

# Write Booster

A UFS performance feature that uses a portion of TLC/QLC NAND in SLC mode as a write buffer. Improves sustained write performance by absorbing bursts before data is migrated to TLC/QLC.

## Key Attributes and Flags

| Name | IDN | Type | Purpose |
|------|-----|------|---------|
| `WRITEBOOSTER_EN` | `api.FlagIDN.WRITEBOOSTER_EN` | Flag | Enable/disable WB |
| `AVAILABLE_WRITEBOOSTER_BUFFER_SIZE` | `api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE` | Attribute (read) | Current available WB buffer |
| `b16_write_booster_buffer_preserve_user_space_en` | Config Descriptor | Config | Preserve user space when WB enabled |
| `l18_num_shared_write_booster_buffer_alloc_units` | Config Descriptor | Config | WB buffer size in allocation units |

## Default Value

`WRITEBOOSTER_ENABLED = True` — from [[modeldefault]].

## LUN Constraint *(CustomerReq overrides Spec)*

**CustomerReq rule (KEPT):** WB-related Attribute/Flag operations must target:
- A **Normal LUN** (not Enhanced Memory, not WB-dedicated)
- **Not** a Boot LUN
- LUN index in range **0~7**

If violated, device responds with **`invalid INDEX`**.

*Spec originally does not impose this restriction — CustomerReq wins per Rule 1. See [[conflicts]].*

## PSA Interaction

During PSA flow, WB buffer capacity remains constant even while writing PSA-sensitive LUNs. After PSA `PRE_SOLDERING` is set, `AVAILABLE_WRITEBOOSTER_BUFFER_SIZE` should equal `0xA`.

```python
api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
ava_WB_size = api.read_attribute(idn=api.AttributeIDN.AVAILABLE_WRITEBOOSTER_BUFFER_SIZE)
assert ava_WB_size == 0xA
```

## Config Descriptor Setup

```python
config_descs[0].header.b17_write_booster_buffer_type = 1
config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = 1
config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0x400
```

## Related

[[lun]] | [[psa-state]] | [[psa]] | [[spec]] | [[customerreq]] | [[modeldefault]]
