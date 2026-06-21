---
type: concept
title: "Power Management"
tags: [power, reset, hibernate, timing]
sources: [spec, script, modeldefault]
created: 2026-06-21
updated: 2026-06-21
---

# Power Management

Covers power cycling, reset types, hibernate states, and timing defaults used across UFS Pattern Code.

## Reset Types

| Reset | Enum | powerdown | Use Case |
|-------|------|-----------|----------|
| HW_RESET (no power loss) | `Dcmd5ResetType.HW_RESET` | `False` | General reset, faster |
| HW_RESET (with power loss) | `Dcmd5ResetType.HW_RESET` | `True` | Full power cycle, more stress |
| SOFT_RESET | `Dcmd5ResetType.SOFT_RESET` | `False` | Warm reset, reset recovery testing |

## Default power_cycle() Pattern

Script patterns randomize between power-on and power-off reset to maximize stress coverage:

```python
def power_cycle(self) -> None:
    if random.randint(0, 1):
        init_tester_to_unit_ready(resetmode=Dcmd5ResetType.HW_RESET, powerdown=False)
    else:
        init_tester_to_unit_ready(resetmode=Dcmd5ResetType.HW_RESET, powerdown=True)
    access_vendor_mode()   # always restore after reset
```

For deterministic tests (e.g., PSA flow step 27, 35), use explicit `powerdown=True`.

## Hibernate (H8 / Hibern8)

UFS link low-power state. See [[pronoun]] for terminology. Triggered by SSU command or power mode change. DCMD6 (`SSU_HIBERNATE_FLOW`) tests hibernate behavior.

## Timing Defaults

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `inhibition_delay` | 180 s | Must match `INHIBITION_TIME` setting |
| `short_delay` | 0.01 s | Minimal delay between checks |
| `standard_delay` | 0.1 s | Between status polls |
| `long_delay` | 1.0 s | Between major operations |
| `vendor_mode_timeout` | 5000 ms | Vendor command timeout |
| `vendor_mode_retries` | 3 | Retry count |

## Voltage Defaults

```python
VCC_NOMINAL  = 3.3   # volts (primary power)
VCCQ_NOMINAL = 1.8   # volts (I/O power)
VCCQ2_NOMINAL= 1.8   # volts (second I/O rail)
```

## Shipping Mode

Entry: `enable_shipping_mode = True`, `thermal_protection_mode = HOT_COLD`
Exit: requires full power cycle (`powerdown=True`), `timeout_for_exit = 5000 ms`

## Related Entities

[[inhibition-timeout]] — idle timeout before inhibition
[[thermal-protection-mode]] — thermal-triggered power behavior

## Sources

[[spec]] Section 6–7 | [[script]] pattern power_cycle() | [[modeldefault]] power_management.md
