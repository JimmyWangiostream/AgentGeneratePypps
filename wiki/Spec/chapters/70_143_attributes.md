# 14.3 Attributes

An Attribute is a parameter that represents a specific range of numeric values that can be written or read. For example, the maximum Data In data packet size would be an attribute. Attribute size can be from 1-bit to 64-bit. Attributes of the same type can be organized in array, each element of them identified by an index. For example, in case of parameter that is logical unit specific, the LUN would be used as index.

Read access property (read or write only) and write access property (read only, write once, persistent, etc.) are defined for each attribute. Table 14.27 on the following consecutive pages describes the supported access properties for attributes

## Table 14.27 — Attributes Access Properties

| Access Property |  | Description |
|-----------------|--|-------------|
| Read | Read | The attribute can be read. |
|  | Write only | The attribute cannot be read. |
|  | Read only | The attribute cannot be written. |
|  | Write once | The attribute can be written only one time, the value is kept after power cycle or any type of reset. |
|  | Persistent | The attribute can be written multiple times, the value is kept after power cycle or any type of reset event. |
| Write | Volatile | The attribute can be written multiple times. The attribute is set to the default value after power cycle or any type of reset event. |
|  | Power on reset | The attribute is set to the default value after power cycle or hardware reset event. |
|  |  | The attribute can written only one time after a power cycle or hardware reset, and it cannot be re-written until the next power cycle or hardware reset. |

---
JEDEC Standard No. 220G  
Page 472

# JEDEC Standard No. 220G
Page 473

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes
#### ATTRIBUTES

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTES |
|-----|------|----------------|------|---------------------|------|-------------|--------|
| 00h | bBootLunEn | Read / Persistent | 1 byte | D | 00h | Boot LUN Enable<br>00h: Boot disabled<br>01h: Enabled boot from Boot LU A<br>02h: Enabled boot from Boot LU B<br>All others: Reserved<br><br>When bBootLunEn = 00h the boot feature is disabled, the device behaves as if bBootEnable would be equal to 0.<br><br>When bBootEnable = 02h permanent-bootable is enabled. In this mode, a Query Request to change bBootLunEn value from 01h or 02h to 00h shall fail and and the Query Response field shall be set to "General failure (FFh)". | |
| 01h | Reserved | - | - | - | - | Reserved for Host Performance Booster (HPB) Extension Standard | |
| 02h | bCurrentPowerM ode | Read only | 1 byte | D | see Note 5 | Current Power Mode<br>00h: Idle power mode<br>10h: Pre-Active power mode<br>11h: Active power mode<br>20h: Pre-Sleep power mode<br>22h: UFS-Sleep power mode<br>30h: Pre-PowerDown power mode<br>33h: UFS-PowerDown power mode<br>Others: Reserved | 5 |
| 03h | bActiveICCLevel | Read / Volatile | 1 byte | D | see Note 6 | Active ICC Level<br>bActiveICCLevel defines the maximum current consumption allowed during Active Mode.<br>00h: Lowest Active ICC level<br>⋮<br>0Fh: Highest Active ICC level<br>Others: Reserved<br>Valid range from 00h to 0Fh. | 6 |

# JEDEC Standard No. 220G
Page 474

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTES |
|-----|------|----------------|------|---------------------|------|-------------|--------|
| 04h | bOutOfOrderDataEn | Read / Write once | 1 byte | D | 00h | Out of Order Data transfer Enable<br>00h: Out-of-order data transfer is disabled for both DATA IN and DATA OUT UPIUs<br>01h: Out-of-order data transfer is enabled for both DATA IN and DATA OUT UPIUs<br>02h: Out-of-order data transfer is enabled for DATA IN UPIUs only, and is disabled for DATA OUT UPIUs<br>03h: Out-of-order data transfer is enabled for DATA OUT UPIUs only, and is disabled for DATA IN UPIUs<br>Others: Reserved<br>This bit shall have effect only when bDataOrdering declares device support for the specific UPIU's enablement | |
| 05h | bBackgroundOpStatus | Read only | 1 byte | D | 00h | Background Operations Status<br>Device health status for background operation<br>00h: Not required<br>01h: Required, not critical<br>02h: Required, performance impact<br>03h: Critical.<br>Others: Reserved | |

**ATTRIBUTES**

# 14.3 Attributes (cont'd)

## Table 14.28 — Attributes

### ATTRIBUTES

| IDN | Name | Access Property | Size | Type¹ | MDV⁴ | Description | NOTES |
|-----|------|----------------|------|--------|------|-------------|-------|
|     |      |                |      | # Ind.² |      |             |       |
|     |      |                |      | # Sel.³ |      |             |       |
| 06h | bPurgeStatus | Read only | 1 byte | D | 00h | Purge Operation Status<br/>00h: Idle (purge operation disabled)<br/>01h: Purge operation in progress<br/>02h: Purge operation stopped prematurely<br/>03h: Purge operation completed successfully<br/>04h: Purge operation failed due to logical unit queue not empty<br/>05h: Purge operation general failure.<br/>Others: Reserved<br/>When the bPurgeStatus is equal to the values 02h, 03h, 04h or 05h, the bPurgeStatus is automatically cleared to 00h (Idle) the first time that it is read. |       |
| 07h | bMaxDataInSize | Read / Persistent | 1 byte | D | see Note 7 | Maximum Data In Size<br/>Maximum data size in a DATA IN UPIU.<br/>Value expressed in number of 512-byte units.<br/>bMaxDataInSize shall not exceed the bMaxInBufferSize parameter.<br/>bMaxDataInSize = bMaxInBufferSize when the UFS device is shipped.<br/>This parameter can be written by the host only when all LU task queues are empty. | 7, 8 |

---

*JEDEC Standard No. 220G*  
*Page 475*

# 14.3 Attributes (cont'd)

## Table 14.28 — Attributes

### ATTRIBUTES

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTEs |
|-----|------|-----------------|------|---------------------|------|-------------|-------|
| 08h | bMaxDataOutSize | Read / Persistent | 1 byte | D | See Description | Maximum Data-Out Size<br>The maximum number of bytes that can be requested with a READY TO TRANSFER UPIU shall not be greater than the value indicated by this attribute.<br><br>Value expressed in number of 512-byte units.<br><br>bMaxDataOutSize shall not exceed the bMaxOutBufferSize parameter.<br><br>bMaxDataOutSize = bMaxOutBufferSize when the UFS device is shipped.<br><br>This parameter can be written by the host only when all LU task queues are empty. | 8 |
| 09h | dDynCapNeeded | Read only | 4 bytes | A<br>Number of LU specified by bMaxNumberLU | 0000 0000h | Dynamic Capacity Needed<br>The amount of physical memory needed to be removed from the physical memory resources pool of the particular logical unit, in units of bOptimalWriteBlockSize. | 9 |
| | | | | 0 | | | |
| 0Ah | bRefClkFreq | Read / Persistent | 1 byte | D | 03h | Reference Clock Frequency value<br>0h:19.2 MHz<br>1h: 26 MHz<br>2h: 38.4 MHz<br>3h: 52 MHz (default)<br>Others: Reserved<br><br>This attribute value is used only when LSS is low. It is ignored when LSS is high | 10 |
| 0Bh | bConfigDescrLock | Read / Write once | 1 byte | D | 00h | Configuration Descriptor Lock<br>0h: Configuration Descriptor not locked<br>1h: Configuration Descriptor locked<br>Others: Reserved | |

---

*JEDEC Standard No. 220G*  
*Page 476*

# JEDEC Standard No. 220G
Page 477

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes

**ATTRIBUTES**

| IDN | Name | Access Property | Size | Type¹ | MDV⁴ | Description | NOTES |
|-----|------|----------------|------|-------|------|-------------|--------|
|     |      |                |      | # Ind.² |      |             |        |
|     |      |                |      | # Sel.³ |      |             |        |
| 0Ch | bMaxNumOfRTT | Read / Persistent | 1 byte | D | 02h | Maximum current number of outstanding RTTs in device that is allowed. bMaxNumOfRTT shall not exceed the bDeviceRTTCap parameter. This parameter can be written by the host only when all LU task queues are empty. |        |
| 0Dh | wExceptionEventControl | Read / Volatile | 2 bytes | D | 0000h | Exception Event Control<br>This attribute enables the setting of the EVENT_ALERT bit of Device Information field, which is contained in the RESPONSE UPIU.<br>EVENT_ALERT is set to one if at least one exception event occurred (wExceptionEventStatus[i]) and the corresponding bit in this attribute is one (wExceptionEventControl[i]).<br>bit[0]: DYNCAP_EVENT_EN<br>bit[1]: SYSPOOL_EVENT_EN<br>bit[2]: URGENT_BKOPS_EN<br>bit[3]: TOO_HIGH_TEMP_EN<br>bit[4]: TOO_LOW_TEMP_EN<br>bit[5]: WRITEBOOSTER_EVENT_EN<br>bit[6]: PERFORMANCE_THROTTLING_EN<br>bit[7]: DEVICE_LEVEL_EXCEPTION_EN<br>bit[8]: WRITEBOOSTER_RESIZE_HINT_EN<br>bit[9]: HEALTH_CRITICAL_EN<br>bit[10]: PINNED_WRITE_BOOSTER_EVENT_EN<br>bit[11~15]: Reserved |        |

# JEDEC Standard No. 220G
## Page 478

### 14.3 Attributes (cont'd)

#### Table 14.28 — Attributes

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTEs |
|-----|------|----------------|------|----------------------|------|-------------|--------|
| 0Eh | wExceptionEventStatus | Read only | 2 bytes | D | 0000h | Each bit represents an exception event. A bit will be set only if the relevant event has occurred (regardless of the wExceptionEventControl status).<br>bit[0]: DYNCAP_NEEDED<br>bit[1]: SYSPOOL_EXHAUSTED<br>bit[2]: URGENT_BKOPS<br>bit[3]: TOO_HIGH_TEMP<br>bit[4]: TOO_LOW_TEMP<br>bit[5]: WRITEBOOSTER_FLUSH_NEEDED<br>bit[6]: PERFORMANCE_THROTTLING<br>bit[7]: DEVICE_LEVEL_EXCEPTION_OCCURRED<br>bit[8]: WRITEBOOSTER_RESIZE_HINT<br>bit[9]: HEALTH_CRITICAL<br>bit[10]: PINNED_WRITE_BOOSTER_FULL<br>bit[11-15]: Reserved | |
| 0Fh | dSecondsPasssed | Write only / Volatile | 4 bytes | D | 0000 0000h | Bits[31:0]: Seconds passed from TIME_BASELINE (see wPeriodicRTCUpdate in Device Descriptor) | |

# 14.3 Attributes (cont'd)

## Table 14.28 — Attributes

### ATTRIBUTES

| IDN | Name | Access Property | Size | Type¹ | MDV⁴ | Description | NOTES |
|-----|------|-----------------|------|-------|------|-------------|--------|
|     |      |                 |      | # Ind.² |      |             |        |
|     |      |                 |      | # Sel.³ |      |             |        |
| 10h | wContextConf | Read / Volatile | 2 bytes | Δ Number of LU specifically by MaxUnumber LU (LUN) 15 (ID) | 0000h | INDEX specifies the LU number. SELECTOR specifies the Context ID within the LU. Valid values are 01h – Fh. **Bit[15:8]: Reserved** **Bit[7:6]: Reliability mode** 00b: MODE0 (normal) 01b: MODE1 (non-Large Unit, reliable mode or Large Unit unit-by-unit mode) 10b: MODE2 (Large Unit, one-unit-tail mode) 11b: Reserved **Bit[5:3]: Large Unit multiplier** If Large Unit context is set, this field defines the Large Unit size, else it is ignored **Bit[2]: Large Unit context** 0b: Context is not following Large Unit rules 1b: Context follows Large Unit rules **Bit [1:0]: Activation and direction mode** 00b: Context is closed and it is no longer active 01b: Context is configured and activated as a write-only context. 10b: Context is configured and activated as a read-only context 11b: Context is configured and activated as a read/write context |        |
| 11h | Obsolete | - | - | - | - | - |        |
| 12h | Reserved | - | - | - | - | Reserved for Unified Memory Extension standard |        |

---

*JEDEC Standard No. 220G  
Page 479*

# JEDEC Standard No. 220G
Page 480

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTEs |
|-----|------|-----------------|------|---------------------|------|-------------|-------|
| 13h | Reserved | - | - | - | - | Reserved for Unified Memory Extension standard | |
| 14h | bDeviceFFUStatus | Read Only | 1 byte | D | 00h | Device FFU Status<br>00h: No information<br>01h: Successful microcode update<br>02h: Microcode corruption error<br>03h: Internal error<br>04h: Microcode version mismatch<br>05h-FEh: Reserved<br>0FFh: General Error | 11 |
| 15h | bPSAState | Read / Persistent | 1 byte | D | Device specific | 00h: 'Off'. PSA feature is off.<br>01h: 'Pre-soldering'. PSA feature is on, device is in the pre-soldering state.<br>02h: 'Loading Complete' PSA feature is on. The host will set to this value after the host finished writing data during pre-soldering state.<br>03h: 'Soldered'. PSA feature is no longer available. Set by the Device to indicate it is in post-soldering state. This attribute unchangeable after it is in 'Soldered' state. | |
| 16h | dPSADataSize | Read / Persistent | 4 bytes | D | 00<br>…<br>00h | The amount of data that the host plans to load to all logical units with bPSASensitive set to 1.<br>Value expressed in units of 4 Kbyte. | |

# 14.3 Attributes (cont'd)

## Table 14.28 — Attributes
### ATTRIBUTES

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTES |
|-----|------|----------------|------|---------------------|------|-------------|-------|
| 17h | bRefClkGatingWaitTime | Read only | 1 byte | D | Device specific | Minimum time for which the reference clock is required by device during transition to LS-MODE or HIBERN8 state. The larger time requirement among the transition to LS-MODE and HIBERN8 states should be set for this attribute.<br>00h: Undefined<br>01h: 1 micro second<br>...<br>FFh: 255 micro seconds | 12, 13 |
| 18h | bDeviceCaseRoughTemperature | Read only | 1 byte | D | 00h | Device's rough package case surface temperature. This value shall be valid when (TOO_HIGH_TEMPERATURE is supported and TOO_HIGH_TEMP_EN is enabled) or ( TOO_LOW_TEMPERATURE is supported and TOO_LOW_TEMP_EN is enabled ).<br>0 : Unknown Temperature<br>1~250 : ( this value – 80 ) degrees in Celsius. ( i.e., -79 ºC ~ 170 ºC )<br>Others: Reserved | |
| 19h | bDeviceTooHighTempBoundary | Read only | 1 byte | D | Device specific | High temperature boundary from which TOO_HIGH_TEMP in wExceptionEventStatus is turned on.<br>0 : Unknown<br>100~250: ( this value – 80 ) degrees in celsius. ( i.e., 20 ºC ~ 170 ºC )<br>Others: Reserved | |
| 1Ah | bDeviceTooLowTempBoundary | Read only | 1 byte | D | Device specific | Low temperature boundary from which TOO_LOW_TEMP in wExceptionEventStatus is turned on.<br>0 : Unknown<br>1~80 : ( this value – 80 ) degrees in celcius. ( i.e., -79 ºC ~ 0 ºC )<br>Others: Reserved | |

---
JEDEC Standard No. 220G
Page 481

# JEDEC Standard No. 220G
Page 482

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTEs |
|-----|------|----------------|------|---------------------|------|-------------|-------|
| 1Bh | bThrottlingStatus | Read only | 1 byte | D | 00h | Each set bit represents an existing situation resulting in performance throttling. Bit 0: Temperature Others: Reserved | |
| 1Ch | bWriteBoosterBufferFlushStatus | Read only | 1 byte | A/LU/0 or D | 0 | Flush operation status of WriteBooster Buffer. 00h: idle. Device is not flushing the WriteBooster Buffer; either the WriteBooster Buffer is empty or a flush has not been initiated 01h: Flush operation in progress. The WriteBooster Buffer is not yet empty and a flush has been initiated. 02h: Flush operation stopped prematurely. The WriteBooster Buffer is not empty and the host stopped the in-progress flush. 03h: Flush operation completed successfully. 04h: Flush operation general failure Others : Reserved When the bWriteBoosterBufferFlushStatus is equal to the one of values 02h, 03h or 04h, value of the bWriteBoosterBufferFlushStatus is automatically cleared as 00h right after the bWriteBoosterBufferFlushStatus is read. A write to the WriteBooster Buffer when the status is 03h will cause automatic transition to either 00h or 01h. | 15 |

# 14.3 Attributes (cont'd)

## Table 14.28 — Attributes
### ATTRIBUTES

| IDN | Name | Access Property | Size | Type¹ | MDV⁴ | Description | NOTES |
|-----|------|-----------------|------|-------|------|-------------|--------|
| | | | | # Ind.² | | | |
| | | | | # Sel.³ | | | |
| 1Dh | bAvailableWriteBoosterBufferSize | Read only | 1 byte | A/LU/0 or D | 0 | Available WriteBooster Buffer Size<br><br>This available buffer size is decreased by WriteBooster operation and increased by flush operation.<br><br>Value expressed in unit of 10% granularity<br><br>00h: 0% buffer remains.<br>01h: 10% buffer remains.<br>02h~09h: 20%~90% buffer remains<br>0Ah: 100% buffer remains<br>Others : Reserved<br><br>The % reported by the attributes is remaining portion of the current WriteBooster Buffer size indicated by the dCurrentWriteBoosterBufferSize attribute.<br><br>If bWriteBoosterBufferPartialFlushMode is set to 02h (i.e. Pinned Mode), this attribute indicates the WriteBooster available buffer size excluding the currently allocated size for the Pinned Write Booster Buffer. | 15 |

# JEDEC Standard No. 220G
Page 484

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTEs |
|-----|------|----------------|------|----------------------|------|-------------|-------|
| 1E | bWriteBoosterBufferLifeTimeEst | Read only | 1 byte | A/LU⁰ or D | Device specific | This field provides an indication of the WriteBooster Buffer lifetime based on the amount of performed program/erase cycles. In cases of preserve user space configuration for WriteBooster Buffer, this lifetime will be reduced by writing on normal user level space, since WriteBooster Buffer is shared with the user level space.<br><br>The detailed calculation method is vendor specific.<br><br>00h: Information not available (WriteBooster Buffer is disabled)<br>01h: 0% - 10% WriteBooster Buffer life time used<br>02h: 10% - 20% WriteBooster Buffer life time used<br>03h: 20% - 30% WriteBooster Buffer life time used<br>04h: 30% - 40% WriteBooster Buffer life time used<br>05h: 40% - 50% WriteBooster Buffer life time used<br>06h: 50% - 60% WriteBooster Buffer life time used<br>07h: 60% - 70% WriteBooster Buffer life time used<br>08h: 70% - 80% WriteBooster Buffer life time used<br>09h: 80% - 90% WriteBooster Buffer life time used<br>0Ah: 90% - 100% WriteBooster Buffer life time used<br>0Bh: Exceeded its maximum estimated WriteBooster Buffer life time (write commands are processed as if WriteBooster feature was disabled)<br><br>Others: Reserved | 15 |

**ATTRIBUTES**

# JEDEC Standard No. 220G
Page 485

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes
**ATTRIBUTES**

| IDN | Name | Access Property | Size | Type¹ | MDV⁴ | Description | NOTES |
|-----|------|----------------|------|-------|------|-------------|--------|
| | | | | # Ind.² | | | |
| | | | | # Sel.³ | | | |
| 1Fh | dCurrentWriteBoosterBufferSize | Read only | 4 byte | A/LU/0 or D | 0 | The current WriteBooster Buffer size. In the case of preserve user space mode, depending on available user space remained, the storage block for the WriteBooster Buffer may be used for the user space. Therefore, the WriteBooster Buffer size can be less than initially configured WriteBooster Buffer size. Host can check the current WriteBooster Buffer size by checking this attribute. Value expressed in unit of Allocation Units. If this value is 0, then the current WriteBooster Buffer size is 0. In the case of user space reduction mode, this value shall be same to the value of dLUNumWriteBoosterBufferAllocUnits or dNumSharedWriteBoosterBufferAllocUnits depending on buffer configuration mode. If bWriteBoosterBufferPartialFlushMode is set to 02h (i.e. Pinned Mode), this attribute indicates the WriteBooster current buffer size excluding the currently allocated size for the Pinned Write Booster Buffer. | 15 |
| 20h-29h | Reserved | - | - | - | - | - | |
| 2Ah | bEXTIIDEn | Read/Write once | 1 byte | D | 00h | EXT_IID Enable<br>00h:EXT_IID is ignored<br>01h: EXT_IID is valid<br>Others: Reserved | |

# JEDEC Standard No. 220G
Page 486

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTEs |
|-----|------|----------------|------|---------------------|------|-------------|-------|
| 2Bh | wHostHintCacheSize | Read / Persistent | 2 byte | D | 0000h | This attribute is set by the host to indicate the host controller Hint Cache size.<br><br>wHostHintCacheSize indicates the maximum sum of outstanding Hint Data Count fields that device is allowed to send to the host controller.<br><br>A hint is considered outstanding when it was provided to the host controller and the corresponding DATA IN UPiU / RTT UPiU was not transferred to the host controller.<br><br>If the device sends hint that exceeds wHostHintCacheSize, it may lead to performance degradation since host may not be able to process command in optimal manner.<br><br>Maximum total number of outstanding Hint Count fields = 32 x 2^wHostHintCacheSize.<br><br>For example, if wHostHintCacheSize = 2, Maximum total number of outstanding Hint Data Count fields is 128 units, each unit correspond to 4KB of data. | |

# 14.3 Attributes (cont'd)

## Table 14.28 — Attributes

### ATTRIBUTES

| IDN | Name | Access Property | Size | Type¹ | MDV⁴ | Description | NOTES |
|-----|------|-----------------|------|-------|------|-------------|-------|
|     |      |                 |      | # Ind.² |      |             |       |
|     |      |                 |      | # Sel.³ |      |             |       |
| 2Ch | bRefreshStatus | Read only | 1 byte | D | 00h | Refresh Operation Status<br/>00h: Idle (refresh operation disabled)<br/>01h: Refresh operation in progress<br/>02h: Refresh operation stopped prematurely<br/>03h: Refresh operation completed successfully<br/>04h: Refresh operation failed due to logical unit queue not empty<br/>05h: Refresh operation general failure.<br/>Others: Reserved<br/>When the bRefreshStatus is equal to the values 02h, 03h, 04h or 05h, the bRefreshStatus is automatically cleared to 00h (Idle) the first time that it is read. |       |
| 2Dh | bRefreshFreq | Read / Persistent | 1 byte | D | Device Specific | Refresh Frequency<br/>Host should make sure that dRefreshTotalCount will be incremented on this frequency.<br/>00h: Not defined<br/>01h: 1 month<br/>02h: 2 month<br/>...<br/>FFh: 255 month |       |
| 2Eh | bRefreshUnit | Read / Persistent | 1 byte | D | Device Specific | Refresh Operation Unit<br/>This attribute may be set to adjust the minimum physical block numbers to be refreshed upon a single request (i.e., fRefreshEnable set to 1)<br/>00h: Minimum refresh capability of Device<br/>01h: 100.000% (i.e., entire device)<br/>Others: Reserved |       |

---

*JEDEC Standard No. 220G*  
*Page 487*

# JEDEC Standard No. 220G
Page 488

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTEs |
|-----|------|-----------------|------|---------------------|------|-------------|--------|
| 2Fh | bRefreshMethod | Read / Persistent | 1 byte | D | 00h | Refresh Method<br>This parameter specifies the refresh operation method.<br>00h : Not defined<br>01h: Manual-Force<br>    The device is obliged to refresh the amount of physical blocks as requested by the host, regardless whether these blocks need refresh or not. The refresh command refreshes the amount of physical blocks given in bRefreshUnit. Refresh starts at the next physical block from where it stopped (or the first block if refresh was never triggered before).<br>02h: Manual-Selective<br>    The refresh command refreshes the amount of physical blocks given in bRefreshUnit. Refresh starts at the next physical block from where it stopped (or the first block if refresh was never triggered before). The device only refreshes the blocks that it considers to be in need of refresh. Regardless of the actually refreshed blocks, dRefreshProgress is increased by bRefreshUnit once the refresh command is completed.<br>Others: Reserved | 14 |
| 30h | qTimestamp | Write only | 8 byte | D | 00h | Timestamp in nanoseconds since January 1, 1970 Coordinated Universal Time (UTC) |  |
| 31h-33h | Reserved | - | - | - | - | Reserved for File Based Optimization (FBO) Extension Specification |  |

**Footnotes:**
- ¹ Type
- ² # Ind.
- ³ # Sel.
- ⁴ MDV

# 14.3 Attributes (cont'd)

## Table 14.28 — Attributes

### ATTRIBUTES

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTES |
|-----|------|----------------|------|----------------------|------|-------------|-------|
| 34h | qDeviceLevelExceptionID | Read only | 8 bytes | D | Vendor specific | This attribute is to indicate the device level exception ID.<br><br>For a detailed definition of this attribute, refer to the device manufacturer datasheet. | |
| 35h | bDefragOperation | Read / Volatile | 1 byte | D | 00h | HID Operations<br>00h: HID analysis and HID defrag operation are disabled.<br>01h: HID analysis is enabled.<br>02h: HID analysis and HID defrag operation are enabled.<br>Others: Reserved<br><br>When this attribute is set to 01h, the device starts to analyze the device's fragmentation status.<br><br>When this attribute is set to 02h, the device starts the HID analysis operation and then executes the defragmentation operation. Note that if the device has already been analyzed, the device may start executing the HID defrag operation without further HID analysis operation.<br><br>This attribute is automatically set to 0 by the device when the operation is completed or a stop condition occurs. | |

---

**JEDEC Standard No. 220G**  
**Page 489**

# JEDEC Standard No. 220G
Page 490

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTEs |
|-----|------|----------------|------|-------------------|------|-------------|-------|
| 36h | dHIDAvailableSize | Read only | 4 byte | D | Vendor specific | HID Available Size<br><br>The total fragmented size in the device is reported through this attribute.<br>- FFFFFFFFh: Indicating no valid information available about the fragmented size. Analysis required.<br>- Other values: Total fragmented size in units of 4Kbyte<br><br>When the HID analysis is completed, the device updates this attribute to indicate the total fragmented size in the device.<br><br>The HID defrag operation is completed if the defragmentation is performed as much as the requested defragmentation size. (The requested defragmentation size is calculated as the minimum value of the size indicated by dHIDSize and the size indicated by dHIDAvailableSize.) | |
| 37h | dHIDSize | Read / Persistent | 4 byte | D | FFFFFFh | HID Size<br><br>The host sets the size to be defragmented by an HID defrag operation.<br><br>The default value is 0xFFFFFFFFh indicating that the device defrag as much as possible.<br><br>The value expressed in units of 4 Kbyte. | |

# 14.3 Attributes (cont'd)

## Table 14.28 — Attributes
### ATTRIBUTES

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTES |
|-----|------|----------------|------|-------------------|------|-------------|-------|
| 38h | bHIDProgressRatio | Read only | 1 byte | D | 00h | HID Progress Ratio<br><br>Defrag progress is reported by this attribute. I.e this attribute indicates the ratio of the completed defrag size over the requested defrag size. (The requested defrag size is calculated as the minimum value of the size indicated by dHIDSize and the size indicated by dHIDAvailableSize.)<br><br>Value expressed in units of 1%.<br>00h: 0%<br>01h: 1%<br>⋮<br>64h: 100%<br>Others: reserved<br><br>If bHIDState is set to 0h, this attribute is initialized to 00h.<br><br>If bDefragOperation is set to 01h or 02h, this attribute is initialized to 00h.<br><br>When this attribute is 64h, the attribute is cleared to 00h automatically right after reading this attribute by the host. | |

# JEDEC Standard No. 220G
Page 492

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTES |
|-----|------|----------------|------|----------------------|------|-------------|-------|
| 39h | bHIDState | Read only | 1 byte | D | 00h | HID State<br><br>The HID state is reported by this attribute.<br><br>00h: Idle (Analysis Required because there is no valid information about fragmentation of the device)<br>01h: Analysis in Progress<br>02h: Defrag Required<br>03h: Defrag In Progress<br>04h: Defrag Completed<br>05h: Defrag is not required<br>Others: Reserved<br><br>If the host set bDefragOperation to 0 (i.e. disable HID operation), the bHIDState is set to idle state from any HID state.<br><br>The bHIDState may be cleared to 00h after receiving any write-type command changing the medium status of the device. In this case, the host can read from time to time the value of bHIDState to verify the operation was terminated or the device managed to resume the HID operation. | |
| 3Ah-3Bh | Reserved | - | - | - | - | - | |

# 14.3 Attributes (cont'd)

## Table 14.28 — Attributes
### ATTRIBUTES

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTES |
|-----|------|----------------|------|---------------------|------|-------------|-------|
| 3Ch | bWriteBoosterBufferResizeHint | Read only | 1 Byte | A/LU/0 or D | 0 | WriteBooster Buffer Resize Hint information<br><br>This field indicates hint information about which type of resize for WriteBooster Buffer is recommended.<br>00h: Recommend keep the buffer size<br>01h: Recommend to decrease the buffer size<br>02h: Recommend to increase the buffer size<br>Others: Reserved<br><br>This field shall be cleared automatically when the device receives the WriteBooster Resize command. | 15 |
| 3Dh | bWriteBoosterBufferResizeEn | Write only / Volatile | 1 Byte | A/LU/0 or D | 0 | Enable WriteBooster Buffer Resize operation<br><br>The host can decrease or increase the WriteBooster Buffer size by setting this attribute.<br>00h: Idle (There is no resize operation)<br>01h: Decrease WriteBooster Buffer Size<br>02h: Increase WriteBooster Buffer Size<br>Others: Reserved<br>The amount of increase or decrease in WriteBooster Buffer is determined by the device.<br>If the WriteBooster Buffer size cannot be increased or decreased, the device will not change the WriteBooster Buffer size. | 15 |

---
JEDEC Standard No. 220G  
Page 493

# 14.3 Attributes (cont'd)

## Table 14.28 — Attributes

### ATTRIBUTES

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTEs |
|-----|------|----------------|------|---------------------|------|-------------|-------|
| 3Eh | bWriteBoosterBufferResizeStatus | Read Only | 1 Byte | A/L/U/0 or D | 0 | Resize operation status of the Write Booster Buffer<br><br>00h: Idle (resize operation is not issued)<br>01h: Resize operation in progress<br>02h: Resize operation completed successfully<br>03h: Resize operation general failure<br>Others: Reserved<br><br>When a Resize operation is completed, the updated size of WriteBooster Buffer is set to dCurrentWriteBoosterBufferSize attribute.<br><br>When the bWriteBoosterBufferResizeStatus is equal to the values 02h or 03h, the status value is cleared to 00h automatically right after bWriteBoosterBufferResizeStatus is read.<br><br>If the host requests the resize operation, the status values of 00h, 02h, or 03h shall be set to 01h. | 15 |

---

*JEDEC Standard No. 220G*  
*Page 494*

# JEDEC Standard No. 220G
## Page 495

### 14.3 Attributes (cont'd)

#### Table 14.28 — Attributes
##### ATTRIBUTES

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTES |
|-----|------|-----------------|------|---------------------|------|-------------|-------|
| 3Fh | bWriteBoosterBufferPartialFlushMode | Read / Persistent | 1 Byte | D | 0 | WriteBooster Buffer Partial Flush Mode<br>00h: No partial flush<br>01h: FIFO(first-in-first-out) mode<br>02h: Pinned mode<br>This field indicates the partial flush mode when WriteBooster Buffer Flush is performed.<br>When this value is set to 01h, the latest written data as much as the FIFO WriteBooster Buffer is not flushed from the WriteBooster flush operation.<br>When this value is set to 02h, the data in the Pinned WriteBooster Buffer is not flushed from the WriteBooster flush operation.<br>When this value is set to 00h, all data in WriteBooster Buffer can be flushed. | |
| 40h | dMaxFIFOSizeForWriteBoosterPartialFlushMode | Read / Persistent | 4 Bytes | A/LU/0 or D | 0 | Maximum FIFO Size for WriteBooster FIFO partial flush mode.<br>Note that in the case of "preserve user space mode", depending on available user space remaining at run-time, storage blocks allocated for the WriteBooster Buffer can be returned to user space. In such a case, the currently allocated WriteBooster FIFO Buffer size is indicated by dCurrentFIFOSizeForWriteBoosterPartialFlushMode which can be less than indicated by this attribute.<br>The value of the attribute is expressed in the unit of Allocation Units | 15 |

# JEDEC Standard No. 220G
Page 496

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTEs |
|-----|------|----------------|------|---------------------|------|-------------|--------|
| 41h | dCurrentFIFOSizeForWriteBoosterPartialFlushMode | Read Only | 4 Bytes | A/LU/0 or D | 0 | Current FIFO Size for WriteBooster FIFO partial flush mode. Device shall manage this attribute to be less than dCurrentWriteBoosterBufferSize. The value of the attribute is expressed in the unit of Allocation Units | 15 |
| 42h | dPinnedWriteBoosterBufferCurrentAllocUnits | Read Only | 4 Bytes | D | 0 | The currently allocated size of Pinned WriteBooster Buffer which is excluded from the flush operation When the WriteBooster Buffer size decreases, the Pinned WriteBooster Buffer size may be decreased and can be less than the size by the dPinnedWriteBoosterBufferNumAllocUnits attribute. If this value is 00h (i.e. there is no Pinned buffer area), even the write command with Group Number set to 18h can be written to the Non-Pinned WriteBooster Buffer area, or to the normal storage if the Non-Pinned WriteBooster Buffer area is full or not configured. The value is expressed in the unit of Allocation Units. | |

**ATTRIBUTES**

# JEDEC Standard No. 220G
Page 497

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes
**ATTRIBUTES**

| IDN | Name | Access Property | Size | Type¹ | MDV⁴ | Description | NOTES |
|-----|------|----------------|------|-------|------|-------------|-------|
|     |      |                |      | # Ind.² |      |             |       |
|     |      |                |      | # Sel.³ |      |             |       |
| 43h | bPinnedWriteBoosterBufferAvailablePercentage | Read Only | 1 Byte | D | 0 | Available Pinned WriteBooster Buffer size in Percentage<br/>This attribute indicates the remaining portion over the current Pinned WriteBooster Buffer size indicated by the dPinnedWriteBoosterBufferCurrentAllocUnits attribute.<br/>The value expressed in 10% granularity<br/>00h: 0% buffer remains.<br/>01h~09h: 10%~90% buffer remains.<br/>0Ah: 100% buffer remains.<br/>Others: Reserved<br/>This value is decreased by the WRITE command whose Group Number is set to 18h and increased by WriteBooster flush operation. |       |
| 44h | dPinnedWriteBoosterCurrentWrittenSize | Read Only | 4 Bytes | D | 0 | Cumulative size is written in the Pinned Write Booster Buffer.<br/>When this value reaches its maximum value (0xffffffff), it does not increase.<br/>The value is expressed in the unit of 10MB. |       |
| 45h | dPinnedWriteBoosterBufferNumAllocUnits | Read / Persistent | 4 Bytes | A/LU/0 or D | 0 | Size for Pinned WriteBooster Buffer area in Pinned partial flush mode.<br/>This value shall be in the unit of Allocation Units. | 15 |
| 46h | dNonPinnedWriteBoosterBufferMinNumAllocUnits | Read / Persistent | 4 Bytes | A/LU/0 or D | 0 | Minimum size for Non-Pinned WriteBooster Buffer area in Pinned partial flush mode.<br/>This value shall be in the unit of Allocation Units. | 15 |
| 47h-7Fh | Reserved | - | - | - | - | - |       |

# JEDEC Standard No. 220G
Page 498

## 14.3 Attributes (cont'd)

### Table 14.28 — Attributes

| IDN | Name | Access Property | Size | Type¹ # Ind.² # Sel.³ | MDV⁴ | Description | NOTEs |
|-----|------|-----------------|------|----------------------|------|-------------|--------|
| 80h-FFh | VendorSpecific | Device Specific | Device Specific | Device Specific | Device Specific | These attributes are reserved for vendor specific usage. Content and function of these attributes may vary based on Manufacturer Name String Descriptor and Product Revision Level String Descriptor. For detailed definition of these attributes please refer to the device manufacturer datasheet. | |

**NOTE 1** The type "D" identifies a device level attribute, while the type "A" identifies an array of attributes. If Type = "D", the attribute is addressed setting INDEX = 00h and SELECTOR = 00h.

**NOTE 2** For array of attributes, "# Ind." specifies the amount of valid values for the INDEX field in QUERY REQUEST/RESPONSE UPIU. If # Ind = 0, the attribute is addressed setting INDEX = 00h.

**NOTE 3** For array of attributes, "# Sel." specifies the amount of valid values for the SELECTOR field in QUERY REQUEST/RESPONSE UPIU. If # Sel = 0, the attribute is addressed setting SELECTOR = 00h.

**NOTE 4** The column "MDV" (Manufacturer Default Value) specifies attribute values after device manufacturing.

**NOTE 5** bInitPowerMode value after device initialization can be 10h (Pre-Sleep mode) or 22h (UFS-Sleep mode) if bInitPowerMode = 00h, or 11h (Active Mode) if bInitPowerMode = 01h.

**NOTE 6** After power on or reset, bActiveCCLevel is equal to bInitActiveCCLevel parameter value included in the Device Descriptor. bInitActiveCCLevel is equal to 00h after device manufacturing, configured by writing the Configuration Descriptor.

**NOTE 7** bMaxDataInSize = bMaxInBufferSize when the UFS device is shipped.

**NOTE 8** If the host attempts to write this Attribute when there is at least one logical unit with command queue not empty, the operation shall fail, and Response field in the QUERY RESPONSE UPIU shall be set to FFh ("General failure").

**NOTE 9** dDynCapNeeded is composed by eight elements, one for each logical unit. The desired element shall be selected assigning the LUN to INDEX field of QUERY REQUEST UPIU.

**NOTE 10** bRefClkFreq field had "Write once" Access Property up to UFS 2.0.

**NOTE 11** bDeviceFFUStatus value is kept after power cycle, hardware reset or any other type of reset.This attribute may change value when a microcode activation occurs.

**NOTE 12** UFS Host may start a timer when DME_POWERMODE.ind is received for HS-MODE to LS-MODE transition or DME_HIBERNATE_ENTER.ind is received for HS-MODE to HIBERN8 transition. In addition to bRefClkGatingWaitTime, Device PA_MinRxTrailingClocks and Host PA_MinRxTrailingClocks should be considered to determine when the reference clock may be stopped.

**NOTE 13** If this attribute is set to value '00h', it means the minimum wait time for reference clock removal is not specified by the device.

**NOTE 14** If the host attempts to write bRefreshMethod when dRefreshProgress is not zero, the operation shall fail, and Response field in the QUERY RESPONSE UPIU shall be set to FFh ("General failure").

**NOTE 15** If the bWriteBoosterBufferType is configured as 01h (shared type), the WriteBooster Buffer is configured as a single shared buffer for the whole device. In this case, the value of LU does not matter.

# 15 UFS Mechanical Standard

UFS discrete and multichip ballouts are defined in [JESD21].

---

JEDEC Standard No. 220G
Page 499

# JEDEC Standard No. 220G
Page 500

---

## Annex A (Informative) Dynamic Capacity Host Implementation Example

### A.1 Overview

This standard defines the Dynamic Capacity feature to enable a UFS device to regain at least partial functionality at the end-of-life where the defect level of the storage medium has accumulated to the point where the device can no longer maintain normal functionality.

Dynamic Capacity operation allows the device, at the direction of the host system, to remove physical memory resources from the resource pool dedicated for data storage and re-task the resources for device internal utility, thus restoring device functionality.

The net result of the Dynamic Capacity operation is a reduction of the usable storage space in the physical medium while the logical address space remains the same as before – i.e., the physical storage is less than the logical address space. It is the responsibility of the host system to keep track of the reduction in physical storage to maintain normal operation in its file system.

This application note outlines a method for the host file system to account for the reduction in physical storage with minimal impact.

### A.2 Method Outline

1. The host system receives notification from the device in the Device Information parameter in Response UPIU that the device requires physical memory to be freed up from the storage space to continue operation.

2. The host reads the bDynCapNeeded[LUN] attributes and the bOptimalWriteBlockSize parameter in the Device Descriptor to determine how much physical memory resources needs to be freed up in each logical unit.

3. The host identifies the logical block address range(s) in the file system where the data can be discarded/erased to free up the physical memory resources. The host then uses the UNMAP command to unmap (deallocate) the LBA range(s), and initiates the Dynamic Capacity operation by setting the fPhyResourceRemoval flag and resetting the UFS device.

4. The host can mark the particular LBA range(s) as unusable in its file system by the means of dummy file(s) to ensure these LBA's will not be used in future write operations. The unusable LBA's marked by dummy file(s) match the reduction of physical storage, therefore from the host system perspective, the file system is intact.

5. The host can further backup the unusable LBA information by storing the information in the system area in case the file system of the main data storage logical unit is corrupted.