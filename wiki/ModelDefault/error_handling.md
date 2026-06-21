# Default Error Handling & Recovery Behavior

Used when TC specifies error scenarios but omits handling/recovery details.

## Exception Defaults

### Default Exception Types

When raising exceptions without specific type:

```python
# Most common test failure exceptions (from Script patterns)
SIGHTING_FAIL_DATA_COMPARE_FAIL  # Data mismatch in read-back
SIGHTING_FAIL_TIMEOUT            # Operation exceeded timeout
SIGHTING_FAIL_UNEXPECTED_STATUS  # Command returned unexpected status
SIGHTING_FAIL_HARDWARE_ERROR     # Hardware error detected
```

### Default Error Logging

```python
# Default error reporting pattern
logger.error_fp(message)        # Failure point: used when test fails
logger.error_lb(message)        # Log block: used for data mismatches
logger.flow(step_number, message)  # Flow tracking
logger.info(message)            # General information
```

---

## Data Verification Defaults

### Default Comparison Behavior

When comparing data without specifics:

```python
# Default comparison method
compare_method = api.CompareMethod.HW_COMPARE  # Use hardware

# Hardware comparison advantages:
# - Faster (parallel comparison)
# - More reliable
# - Integrates with device error detection

# Software comparison used only when:
# - HW compare unavailable
# - Comparing against pattern data
# - Debugging specific fields
```

### Default Tolerance

When checking numerical values:

```python
# Default tolerance for comparisons
exact_match_required = True       # No tolerance by default

# Exceptions (use only when explicitly stated):
tolerance_percent = 0.1           # 0.1% tolerance for analog values
tolerance_absolute = 1            # ±1 for counts/indices
```

---

## Command Timeout Defaults

When operation hangs without clear timeout:

```python
# Standard timeout values
TIMEOUT_STANDARD_CMD = 30000   # 30 seconds (read/write/query)
TIMEOUT_LONG_CMD = 60000       # 60 seconds (format/rebuild)
TIMEOUT_VENDOR_CMD = 10000     # 10 seconds (vendor specific)
TIMEOUT_INITIALIZATION = 45000 # 45 seconds (device init)

# Timeout response
on_timeout = raise SIGHTING_FAIL_TIMEOUT  # Fail test on timeout
retry_on_timeout = False  # Don't auto-retry by default
log_timeout_details = True  # Always log timeout info
```

---

## Sense Data Handling

### Default Sense Data Interpretation

When device returns error status:

```python
# Query sense data structure
sense_key = response.sense_data[2]  # Main error category
asc = response.sense_data[12]       # Additional Sense Code
ascq = response.sense_data[13]      # ASCQ (more specific)

# Common sense keys when not specified:
RECOVERED_ERROR = 0x1  # Warning, operation succeeded
NOT_READY = 0x2        # Device not ready
MEDIUM_ERROR = 0x3     # Data error (bad block)
HARDWARE_ERROR = 0x4   # Device hardware fault
ILLEGAL_REQUEST = 0x5  # Invalid command
UNIT_ATTENTION = 0x6   # State change (reset, etc.)
DATA_PROTECT = 0x7     # Write protected
BLANK_CHECK = 0x8      # Unexpected blank area
```

**Spec Reference:** Section 13 (RESPONSE UPIU - Sense Data Format)

---

## Retry Strategy

### Default Retry Behavior

When operation fails without explicit retry instruction:

```python
# Default retry policy
max_retries = 0          # Don't retry by default (fail-fast)
retry_on_timeout = False
retry_on_busy = True     # Retry if device reports BUSY

# Retry timing
retry_delay_ms = 100     # Wait 100ms between retries
exponential_backoff = False  # Use fixed delays

# Only retry when:
# - Explicitly specified in TC
# - Transient error detected
# - Device in BUSY state
```

### Retry Exhaustion

```python
# When max retries exceeded
on_exhaustion = raise SIGHTING_FAIL_<ERROR_TYPE>
log_retry_attempts = True
collect_diagnostic_info = True
```

---

## Hardware Reset Recovery

When hardware reset occurs unexpectedly:

```python
# Default recovery after unexpected reset
auto_reinit = True  # Automatically reinitialize
verify_state_after_reset = True
rebuild_corrupted_structures = True

# Re-initialization sequence
1. Detect reset occurred
2. Query device status
3. Clear any pending commands
4. Restore critical settings
5. Resume test flow
```

---

## Power Loss Recovery

When simulating/testing power loss:

```python
# Default power loss behavior
notify_firmware_before_powerdown = True  # Send notification
allow_pending_writes = False  # Flush before cutting power

# Recovery expectation
verify_data_integrity = True     # Check for corruption
check_journal_consistency = True  # Validate FTL structures
rebuild_indexes = True           # Rebuild if needed

# Acceptable data loss
unwritten_data_loss_ok = True    # Data in cache may be lost
persistent_data_must_be_intact = True  # Committed data safe
```

---

## Thermal/Environmental Faults

When device reports thermal issues:

```python
# Default thermal fault handling
immediate_shutdown = True         # Don't allow overheating
wait_for_cooldown = True         # Pause test
cooldown_target_temp = 70        # Celsius
max_cooldown_time = 300000       # 5 minutes max wait

# If device won't cool:
on_thermal_failure = SIGHTING_FAIL_HARDWARE_ERROR
log_thermal_data = True
```

---

## State Machine Violations

When device enters invalid state:

```python
# Default invalid state handling
fail_on_invalid_state = True     # Strict checking
log_state_transition = True      # Record path to invalid state
attempt_recovery = False         # Don't try to recover
report_state_machine_error = True

# State transition verification
validate_state_transitions = True  # Check against spec
allowed_invalid_paths = []         # None by default
```

**Spec Reference:** Section 7 (Reset, Power-Up and Power-Down State Machines)

