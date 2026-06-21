---
type: concept
title: "Shipping Mode"
tags: [shipping-mode, power, thermal, hwsetting, lifecycle, psa]
sources: [script, modeldefault]
created: 2026-06-21
updated: 2026-06-21
aliases: [shipping mode, ShippingMode, shipping_mode]
---

# Shipping Mode

Shipping Mode is a low-power state that UFS devices can enter before they are shipped to end customers or system integrators. In this mode, the device draws minimal power, protecting the battery or power supply during transit and storage. The device must be explicitly woken up before normal use.

## Purpose

- Minimize power draw during shipping and storage
- Prevent unintended writes or operations while in transit
- Default thermal protection applies (`HOT_COLD`) to cover a wide range of storage temperatures

## Entry Flow

```
1. Ensure device is in Active or Idle power mode
2. Set thermal protection mode to default (HOT_COLD)
3. Issue the shipping mode entry command via HwSetting or VU
4. Power cycle (powerdown=True) to commit the shipping mode state
```

Shipping mode is typically part of the manufacturing lifecycle flow, performed before the device leaves the factory or after PSA loading is complete.

## Exit Flow

```
1. Apply power to the device (power cycle from full-off state)
2. Wait for device initialization: poll fDeviceInit until cleared (= 0)
   Timeout: 5000 ms (ModelDefault: shipping mode exit timeout)
3. Issue vendor unlock or initialization sequence
4. Device returns to normal operating mode (UFS-Sleep or Active per bInitPowerMode)
```

**Shipping mode exit timeout (ModelDefault): 5000 ms**

Failure to exit within this window indicates a device initialization problem.

## Thermal Protection Default in Shipping Mode

When entering shipping mode, thermal protection defaults to `HOT_COLD`, meaning the device will enter a stuck state if it exceeds the hot threshold **or** falls below the cold threshold:

```python
THERMAL_HOT_THRESHOLD  = 85   # °C — from ModelDefault
THERMAL_COLD_THRESHOLD = 0    # °C — from ModelDefault
```

Thermal protection mode used during shipping: `ThermalProtectionType.HOT_COLD`

If a different thermal mode was previously configured, switching to shipping mode resets the mode to `HOT_COLD`. Tests `PSW_F_P3_ThermalProtection_0004–0006` cover this behavior.

See [[thermal-protection-mode]] for full VU command details and temperature encoding formula.

## Relationship to PSA

Shipping mode is distinct from [[psa]] (Production State Awareness). PSA controls write protection during manufacturing (Off → Pre-Soldering → Loading Complete → Soldered). Shipping mode may be entered after PSA is complete (Soldered state) as a separate operational step.

## Power Cycle Requirements

- **Entry**: requires `powerdown=True` power cycle to commit the mode
- **Exit**: requires a full power cycle from the off state (not just HW_RESET)

A HW_RESET alone may not fully exit shipping mode if the device was in a deep shipping state.

## Interaction with Inhibition Timeout

After exiting shipping mode, the inhibition timeout applies normally:

```
Default inhibition_time = 180 seconds  (ModelDefault)
```

Background tasks (GC, Refresh, etc.) will be blocked for the inhibition window immediately after the device initializes post-shipping-mode-exit.

See [[inhibition-timeout]] for details.

## ModelDefault Values Summary

| Parameter | Value | Source |
|-----------|-------|--------|
| `shipping_mode_exit_timeout` | 5000 ms | modeldefault |
| `thermal_protection` (default in shipping) | `HOT_COLD` | modeldefault |
| `THERMAL_HOT_THRESHOLD` | 85°C | modeldefault |
| `inhibition_time` (after exit) | 180 s | modeldefault |

## Related

[[thermal-protection-mode]] | [[inhibition-timeout]] | [[power-modes]] | [[psa]] | [[power-management]] | [[modeldefault]]
