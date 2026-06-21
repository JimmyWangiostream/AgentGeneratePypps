# Default Power Management Parameters

Used when TC specifies power operations but omits timing/mode details.

## power_cycle()

**Default Behavior (from Script analysis):**
```python
# Random selection between powerdown and HW_RESET
if random.randint(0, 1):
    # 50% chance: Hard reset without power cycle
    init_tester_to_unit_ready(resetmode=Dcmd5ResetType.HW_RESET, powerdown=False)
else:
    # 50% chance: Power cycle (more stress)
    init_tester_to_unit_ready(resetmode=Dcmd5ResetType.HW_RESET, powerdown=True)

# Always restore vendor mode after power cycle
access_vendor_mode()
```

**When randomization not appropriate (TC-specific):**
```python
# For deterministic tests, default to:
resetmode = Dcmd5ResetType.HW_RESET
powerdown = False  # Less disruptive than full power loss
```

---

## Reset Type Defaults

When reset type not specified:

| Scenario | Default Reset | Rationale |
|----------|-------|-----------|
| **General testing** | HW_RESET | Safest, most complete |
| **Warm reset testing** | SOFT_RESET | If testing reset recovery |
| **Power loss testing** | HW_RESET + powerdown=True | Full power cycle |
| **Link recovery** | HW_RESET | Reestablishes all links |

**Spec Reference:** Section 7 (Reset types and procedures)

---

## Timing Defaults

### Idle/Inhibition Time

```python
# When inhibition_time not specified in TC
default_inhibition_time = 180  # seconds (3 minutes)

# Test values (derived from Inhibition_time patterns)
test_inhibition_values = [30, 60, 90, 150, 180, 210, 240, 255]  # seconds

# Zero timeout test (special case)
zero_sec_inhibition_time = 0  # Immediate inhibition on idle
```

### Sleep Duration

```python
# When adding delay between operations
short_delay = 0.01      # 10 milliseconds (minimal)
standard_delay = 0.1    # 100 milliseconds (between checks)
long_delay = 1.0        # 1 second (between major operations)
inhibition_delay = 180  # Must match inhibition_time setting
```

---

## Voltage/Thermal Defaults

When power supply or thermal parameters not specified:

```python
# From UFS Spec electrical requirements
VCC_NOMINAL = 3.3      # volts (primary power)
VCCQ_NOMINAL = 1.8     # volts (I/O power)
VCCQ2_NOMINAL = 1.8    # volts (second I/O rail)

# Thermal protection defaults
THERMAL_HOT_THRESHOLD = 85    # Celsius (trigger throttling)
THERMAL_COLD_THRESHOLD = 0    # Celsius (lower bound)
THERMAL_SAFE_OPERATING = 25   # Celsius (room temperature)
```

**Spec Reference:** 
- Section 6 (Electrical: Clock, Reset, Signals and Supplies)
- Section 8 (MIPI M-PHY: electrical characteristics)

---

## Shipping Mode Defaults

If entering shipping mode but parameters not specified:

```python
# Shipping mode entry
enable_shipping_mode = True
thermal_protection_mode = api.ThermalProtectionMode.HOT_COLD  # Default is both hot/cold

# Recovery from shipping mode
powerdown = True  # Full power cycle required to exit
timeout_for_exit = 5000  # milliseconds
```

**Spec Reference:** Section 7.7 (Shipping Mode)

