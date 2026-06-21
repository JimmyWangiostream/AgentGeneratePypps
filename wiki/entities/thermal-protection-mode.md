---
type: entity
title: "Thermal Protection Mode"
tags: [thermal, hwsetting, protection, stuck, VU, temperature, shipping-mode]
sources: [spec, script, modeldefault]
created: 2026-06-21
updated: 2026-06-21
aliases: [ThermalProtectionMode, thermal_protection_mode, TP, thermal stuck]
---

# Thermal Protection Mode

Configures how the UFS device responds to temperature extremes. When thermal thresholds are exceeded, the device enters a "stuck" state — it stops responding to write commands until reset. The three protection modes correspond to which direction of temperature violation triggers a stuck state.

## Modes

| Mode | Value | Behavior |
|------|-------|----------|
| `HOT_COLD` | Default | Triggers stuck on both overheating AND extreme cold |
| `HOT_ONLY` | — | Triggers stuck on overheating only |
| `COLD_ONLY` | — | Triggers stuck on extreme cold only |
| `DISABLE` | — | No thermal protection (use only in controlled environments) |

## Default Value

`thermal_protection = HOT_COLD` — from [[modeldefault]].

## Thresholds (ModelDefault)

```python
THERMAL_HOT_THRESHOLD  = 85   # °C — trigger throttling / stuck
THERMAL_COLD_THRESHOLD = 0    # °C — lower bound
THERMAL_SAFE_OPERATING = 25   # °C — room temperature baseline
```

## Temperature Encoding

UFS firmware reports temperature in an offset-encoded format:

```
UFS_temp = real_temp + 80
```

Examples:
- Real 0°C → UFS_temp = 80
- Real 85°C → UFS_temp = 165
- Real -40°C → UFS_temp = 40

This encoding is used in VU D0F1 threshold fields and in the NAND temperature injection struct (`SetNandTemperature`). The formula applies equally to `WriteThermalStuckThreshold.low_threshold` and `high_threshold` fields.

Additional NAND temperature offset (VU 4021 / D08A): FW adds an additional **+37** to injected NAND die temperatures. Valid injection range: approximately -37 to 125 (exclusive at boundaries).

## VU Commands

| VU | Function | Python API |
|----|----------|-----------|
| D0F1 | Write thermal stuck threshold | `project_api.issue_D0F1_write_thermal_stuck_threshold(WriteThermalStuckThreshold)` |
| 40FA | Read thermal stuck threshold | `project_api.issue_40FA_read_thermal_stuck_threshold()` |
| D0F3 | Disable/release thermal stuck state | `project_api.issue_D0F3_disable_thermal_stuck(ThermalProtectionType, HardThermalProtectionType)` |
| D08A | Inject fake NAND temperature | `project_api.issue_D08A_set_vu_temperature(SetNandTemperature)` |
| D088 | Enable/disable auto-standby | `project_api.issue_D088_enable_disable_auto_standby()` |
| 40FD | Read uC temperature | `project_api.issue_40FD_to_get_uC_temperature()` |
| 40FE | Read enhanced health report (includes temp) | `project_api.issue_40FE_to_read_enhanced_health_report()` |
| 4021 | Get NAND temperature | `project_api.issue_4021_get_nand_temperature()` |

## Key Data Structures

```python
# WriteThermalStuckThreshold — used with VU D0F1
tp_threshold = WriteThermalStuckThreshold()
tp_threshold.high_thermal_protection_threshold.value = 165   # 85°C real
tp_threshold.low_thermal_protection_threshold.value  = 80    # 0°C real
project_api.issue_D0F1_write_thermal_stuck_threshold(tp_threshold)

# SetNandTemperature — used with VU D08A
nand_temp = SetNandTemperature()
nand_temp.bEnableSetVuTemp = 1
nand_temp.NAND_TEMPERATURE_DIE_0 = 165   # inject 85°C real
project_api.issue_D08A_set_vu_temperature(nand_temp)

# ThermalProtectionType enum
ThermalProtectionType.HOT_ONLY
ThermalProtectionType.COLD_ONLY
ThermalProtectionType.HOT_COLD
```

## Stuck State Behavior

When a thermal threshold is crossed:

1. Device stops responding to write commands (write command times out)
2. Firmware records an assert code — readable via `api.get_fw_assert_number()`
   - Expected assert code: `0x464` (confirmed in Script patterns)
3. Device must be reset (`HW_RESET` or `RST_n`) to recover
4. After reset, any unwritten data buffered at the time of the stuck event is **not** guaranteed to be present (volatile cache lost)

## Stuck State Recovery Steps

```
1. Detect timeout / stuck condition (G_TIMEOUT_ALL exception)
2. Read fw_assert_number → verify == 0x464
3. Call manual_rst_n()  or  HW_RESET with powerdown=True
4. Re-init device (access_vendor_mode())
5. Optionally re-issue VU D0F3 to confirm thermal protection is cleared
6. Resume normal operation
```

## Shipping Mode Interaction

Tests 0004–0006 cover switching between shipping mode configurations:
- When entering shipping mode, default thermal protection is `HOT_COLD`
- Recovery from shipping mode requires a full power cycle (`powerdown=True`)
- Switching modes verifies that the device applies the new protection type correctly without residual stuck states

See [[shipping-mode]] for full entry/exit flow.

## Temperature Measurement Health Report

`issue_40FE_to_read_enhanced_health_report()` returns temperature history fields:

| Field | Description |
|-------|-------------|
| `highest_temp` | Highest recorded temperature (lifetime) |
| `lowest_temp` | Lowest recorded temperature (lifetime) |
| `power_on_highest_temp` | Highest temp since last power-on |
| `power_on_lowest_temp` | Lowest temp since last power-on |
| `temperature_profile_t_37` | Time in zone ≤ -37°C |
| `temperature_profile_37_t_25` | Time in zone -37°C to -25°C |
| `temperature_profile_25_t_0` | Time in zone -25°C to 0°C |
| `temperature_profile_0_t_95` | Time in zone 0°C to 95°C (normal operating) |
| `temperature_profile_95_t_115` | Time in zone 95°C to 115°C |
| `temperature_profile_t_115` | Time in zone > 115°C |
| `temperature_delta_*` | Delta bins: <1°C, 1–5°C, 5–10°C, 10–15°C, ≥15°C |

Temperature profile buckets are cleared by VU D011; non-zero data is restored after power cycle (HW_RESET).

## UFS Spec — Exception Events for Temperature

From `wExceptionEventStatus` (attribute 0Eh):
- **bit[0]**: `TOO_HIGH_TEMP` — temperature exceeded upper limit
- **bit[1]**: `TOO_LOW_TEMP` — temperature below lower limit

These standard exception events exist alongside the vendor-specific thermal stuck mechanism.

## Test Coverage (7 tests)

| Test | Purpose |
|------|---------|
| 0001 — HOT_ONLY Stuck | Set hot threshold; inject temp above; verify stuck; release via D0F3 |
| 0002 — COLD_ONLY Stuck | Same as 0001 but with cold temperature (below threshold) |
| 0003 — HOT_COLD Stuck | Test both hot and cold thresholds together |
| 0004–0006 — Shipping Mode Switches | Verify TP behavior when switching between shipping mode configs |
| 0010 — Temperature Measurement | ATS timer, delta_asic_nand delta, FW symbol reads, auto-standby interaction |

**Common Exceptions:** `SIGHTING_FAIL_DATA_COMPARE_FAIL`, `G_TIMEOUT_ALL`

## FW Symbol for Temperature

```python
read_fw_value('gUfsApiStruct.ftl->temp.*')   # temperature-related FW state
```

## Script References

- `Script/pattern/Thermal_Protection/PSW_F_P3_ThermalProtection_0001_HOT_ONLY_Stuck_Test.py`
- `Script/pattern/Thermal_Protection/PSW_F_P3_ThermalProtection_0002_COLD_ONLY_Stuck_Test.py`
- `Script/pattern/Thermal_Protection/PSW_F_P3_ThermalProtection_0003_HOT_COLD_Stuck_Test.py`
- `Script/pattern/Thermal_Protection/PSW_F_P3_ThermalProtection_0004_Switch_To_HOT_COLD_In_Shipping_Mode_Test.py`
- `Script/pattern/Thermal_Protection/PSW_F_P3_ThermalProtection_0010_Temperature_Measurement_Check.py`

## Related

[[shipping-mode]] | [[power-modes]] | [[inhibition-timeout]] | [[power-management]] | [[modeldefault]]
