# Default Initialization Parameters

Used when TC specifies device initialization but omits parameter details.

## init_tester_to_unit_ready()

**Default Parameters:**
```python
# When resetmode not specified
resetmode = Dcmd5ResetType.HW_RESET  # Hardware reset (full reset cycle)

# When powerdown not specified
powerdown = False  # Keep power on (faster initialization)
```

**Alternatives based on context:**
- If testing power-loss recovery → `powerdown = True`
- If testing reset recovery → `resetmode = HW_RESET`
- If testing warm reset → `resetmode = SOFT_RESET` (if available)

**Rationale:**
- HW_RESET is most reliable and recommended by UFS spec
- Keeping power on reduces test time unless power behavior is being tested

**Spec Reference:** Section 7 (Reset, Power-Up and Power-Down)

---

## access_vendor_mode()

**Default Parameters:**
```python
# Vendor mode access defaults
timeout = 5000  # 5 second timeout for vendor commands
retries = 3     # Retry up to 3 times on temporary failure
```

---

## LU Configuration

When TC specifies logical unit setup but omits details:

```python
# Standard LU configuration (from Script patterns)
config_lun(
    normal_list = [0, 2, 3, 4],    # Standard LUs: Data, WB, GC, Temp
    em1_list = [1],                 # Enhanced Memory 1 LU
    slc_lu = None,                  # No dedicated SLC LU unless specified
    tlc_lu = None,                  # No dedicated TLC LU unless specified
    rpmb_lu = None                  # No direct RPMB LU access unless needed
)
```

**Rationale:**
- 4 normal LUs cover most test scenarios
- EM1 provides reliable storage for critical data
- Additional LUs only configured when explicitly needed

**Related Script:** `Script/pattern/custom_vu/` initialization examples

---

## Hardware Setting Defaults

When getting/setting hardware settings without specifics:

```python
# Default settings retrieval
hw_setting = api.HwSetting.get_instance()
hw_setting.update_from_device()  # Always sync with device before reading

# Common defaults when modifying
inhibition_time = 180  # Seconds (typical idle timeout)
psa_state = api.PSAState.PRE_SOLDERING  # Default PSA mode
write_booster = ENABLED  # EnableWriteBooster by default
background_ops = ENABLED  # Background operations on by default
```

**Spec Reference:** Section 13 (UFS Functional Descriptions)

