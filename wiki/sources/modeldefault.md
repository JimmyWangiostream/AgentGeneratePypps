---
type: source
title: "ModelDefault — Auto-Generated Default Parameters"
tags: [modeldefault, defaults, reference]
ingested: 2026-06-21
updated: 2026-06-21
entities: [inhibition-timeout, thermal-protection-mode, write-booster, lun]
concepts: [power-management, background-operations]
---

# ModelDefault — Auto-Generated Default Parameters

Eight files documenting the default parameter values used when a TC flow does not specify them. Derived from analysis of Script patterns and UFS Spec.

## Files

| File | Contents |
|------|----------|
| `power_management.md` | power_cycle, reset types, inhibition time, voltage/thermal thresholds |
| `initialization.md` | init_tester_to_unit_ready, access_vendor_mode, LU config |
| `hardware_settings.md` | HwSettingField defaults, device descriptor access |
| `data_operations.md` | Read/write chunk sizes, FUA, compare methods |
| Others | Attribute operations, BKOPS, debugging helpers |

## Key Default Values

### Power Management
```python
default_inhibition_time = 180      # seconds (overridden by UserPrompt if TC specifies LUN)
THERMAL_HOT_THRESHOLD  = 85        # Celsius
THERMAL_COLD_THRESHOLD = 0         # Celsius
VCC_NOMINAL            = 3.3       # volts
VCCQ_NOMINAL           = 1.8       # volts
```

### Initialization
```python
resetmode = Dcmd5ResetType.HW_RESET
powerdown = False
timeout   = 5000   # ms for vendor mode
retries   = 3
```

### Hardware Settings
```python
HwSettingField.INHIBITION_TIME = 180      # seconds
PSA_STATE                      = api.PSAState.PRE_SOLDERING
WRITEBOOSTER_ENABLED           = True
BKOPS_ENABLED                  = True
CACHE_MODE                     = WRITE_BACK
TEMPERATURE_THRESHOLD_HIGH     = 85       # Celsius
```

### LUN Defaults *(DELETED by UserPrompt — see [[conflicts]])*
```python
# CONFLICT: ModelDefault says LUN 0; UserPrompt says MaxCapacity Enabled LUN
# UserPrompt wins. Do NOT use this default.
TestNormalLun = 0   # DELETED — use UserPrompt rule instead
```

### Data Operations
```python
chunk_size      = api.BLOCK4K_SIZE_128M_BYTE   # 128 MB
fua             = 0                             # disabled
compare_method  = api.CompareMethod.HW_COMPARE
timeout_ms      = 30000                         # 30 seconds
```

## Where This Fits

Touches: [[inhibition-timeout]], [[thermal-protection-mode]], [[write-booster]], [[lun]], [[power-management]], [[background-operations]]
