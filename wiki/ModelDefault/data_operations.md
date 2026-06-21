# Default Data Operation Parameters

Used when TC flow specifies read/write operations but omits parameter details.

## sequential_write()

**Default Parameters:**
```python
# When chunk_size not specified
chunk_size = api.BLOCK4K_SIZE_128M_BYTE  # 128 MB chunks (optimal for performance)

# When fua (Force Unit Access) not specified
fua = 0  # Disabled by default (allows write caching)

# When need_compare not specified  
need_compare = False  # Skip hardware verify unless data integrity is critical

# When compare_method not specified
compare_method = api.CompareMethod.HW_COMPARE  # Use hardware comparison when available

# When write_record not specified
write_record = api.get_empty_write_record()  # Create new record for tracking
```

**Rationale:**
- Large chunk sizes (128MB) reduce test execution time for non-critical patterns
- FUA disabled allows firmware write optimization (WriteBooster)
- Hardware compare is faster and more reliable than software verification
- Write record tracks all operations for debugging and analysis

**Related Spec:** Section 11.3.15 (WRITE command)

---

## sequential_read()

**Default Parameters:**
```python
# When chunk_size not specified
chunk_size = api.BLOCK4K_SIZE_128M_BYTE  # 128 MB chunks

# When compare_method not specified
compare_method = api.CompareMethod.HW_COMPARE  # Hardware verify
```

---

## lba_to_pba() — LBA to Physical Block Address Conversion

**Default Parameters:**
```python
# LUN defaults when operating on specific LU types:
TestNormalLun = 0      # General data storage
TestEM1Lun = 1         # Enhanced Memory 1 (slower, reliable)
TestWBLun = 2          # WriteBooster LUN
TestGC_Lun = 3         # Garbage Collection
TestTemperatureLun = 4 # Temperature monitoring
```

---

## Data Size Defaults

When data size/block count not specified:

```python
# Common test data sizes (in bytes)
MINIMAL_TEST_SIZE = api.BLOCK4K_SIZE_128M_BYTE        # ~128 MB (small test)
STANDARD_TEST_SIZE = 10 * api.BLOCK4K_SIZE_128M_BYTE  # ~1.3 GB (typical)
STRESS_TEST_SIZE = 100 * api.BLOCK4K_SIZE_128M_BYTE   # ~13 GB (extensive)

# VB (Virtual Block) sizing
SLC_VB_SIZE = fw_geometry.l84_vb_size_u0 * 512 // 4096  # SLC block size
TLC_VB_SIZE = fw_geometry.l88_vb_size_u1 * 512 // 4096  # TLC block size
EXCEED_SIZE = 50  # Extra blocks beyond main VB (safety margin)
```

---

## Transfer Parameters

**Default transfer behavior when TC omits specifics:**

```python
# Data alignment
start_lba = 0           # Start from beginning unless specified
total_size = <from above>  # Use appropriate test size tier

# Ordering
allow_out_of_order = False  # Maintain FIFO order by default
max_pending_transfers = 1   # Single outstanding transfer (safe default)

# Timing
timeout_ms = 30000          # 30 second timeout for standard operations
busy_wait_threshold = 100   # Check busy status every 100ms
```

**Spec Reference:** Section 10.7.13 (Data Out Transfer Rules), 25 (SCSI Transport)

