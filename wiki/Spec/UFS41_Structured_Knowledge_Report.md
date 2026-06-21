# UFS 4.1 Specification — Structured Knowledge Report
**Source**: JEDEC Standard No. 220G (UFS 4.1)
**Generated from**: All 73 chapter files in `wiki/Spec/chapters/`

---

## Part 1: Entities

### 1.1 Descriptors

Accessed via QUERY REQUEST UPIU (OPCODE=01h READ DESCRIPTOR / 02h WRITE DESCRIPTOR). DESCRIPTOR IDN + INDEX + SELECTOR address each descriptor.

| IDN | Name | Key Fields / Notes |
|-----|------|--------------------|
| 00h | Device Descriptor | bLength=59h, wSpecVersion=0410h for UFS4.1; identifies manufacturer, product, LU count, capabilities |
| 01h | Configuration Descriptor | INDEX 00h–03h (each covers 8 LUs); bConfDescContinue (00h=last, 01h=more); bConfigDescrLock locks all config permanently |
| 02h | Unit Descriptor | Per-LU parameters: bLUEnable, bBootLunID, bLUWriteProtect, bMemoryType, dNumAllocUnits, bDataReliability, bLogicalBlockSize, bProvisioningType |
| 04h | Interconnect Descriptor | UniPro/M-PHY capability and version info |
| 05h | String Descriptor | Manufacturer Name (12h len, 8 UNICODE), Product Name (22h len, 16 UNICODE), OEM ID, Serial Number, Product Revision Level (0Ah, 4 UNICODE) |
| 07h | Geometry Descriptor | Physical geometry: dSegmentSize, bMaxNumberLU (up to 32), bAllocationUnitSize, dOptimalLogicalBlockSize, bDataOrdering |
| 08h | Power Parameters Descriptor | bActiveICCLevel ranges, power profiles |
| 09h | Device Health Descriptor | bLength=2Dh; bPreEOLInfo (00h=not defined, 01h=normal, 02h=warning ≥80% reserved blocks, 03h=critical ≥90%); bDeviceLifeTimeEstA and bDeviceLifeTimeEstB (00h=no info, 01h–0Ah = 0-100% in 10% steps, 0Bh=exceeded); dRefreshTotalCount; dRefreshProgress |
| F0h–FFh | Vendor Specific Descriptor | Vendor defined |

**Device Descriptor Key Fields** (Table 14.4):

| Offset | Field | Notes |
|--------|-------|-------|
| 00h | bLength | 59h |
| 01h | bDescriptorIDN | 00h |
| 02h | bDevice | Device class |
| 03h | bDeviceClass | |
| 04h | bDeviceSubClass | |
| 05h | bProtocol | |
| 06h | bNumberLU | number of enabled LUs |
| 07h | bNumberWLU | number of well-known LUs |
| 08h | bBootEnable | 00h=disabled, 01h=bootable, 02h=permanent-bootable |
| 09h | bDescrAccessEn | |
| 0Ah | bInitPowerMode | power mode after init |
| 0Bh | bHighPriorityLUN | 7Fh=equal priority, or specific LUN |
| 0Ch | bSecureRemovalType | 00h=erase, 01h=overwrite+erase, 02h=overwrite+complement+random+erase, 03h=vendor |
| 0Dh | bSecurityLU | 01h=RPMB supported |
| 0Eh | bBackgroundOpsTermLat | background ops termination latency (10ms units) |
| 0Fh | bInitActiveICCLevel | default ICC level |
| 10h–11h | wSpecVersion | 0410h for UFS 4.1 |
| 12h–13h | wManufactureDate | |
| 14h | iManufacturerName | index into String Descriptors |
| 15h | iProductName | |
| 16h | iSerialNumber | |
| 17h | iOemID | |
| 18h–19h | wManufacturerID | JEDEC JEP106 ID |
| 1Ah | bUD0BaseOffset | |
| 1Bh | bUDConfigPLength | |
| 1Ch | bDeviceRTTCap | max simultaneous RTTs device supports |
| 1Dh–1Eh | wPeriodicRTCUpdate | |
| 1Fh | bUFSFeaturesSupport | bit[0]=FFU, bit[1]=PSA, bit[2]=Device Life Span, bit[3]=Refresh |
| 20h | bFFUTimeout | max FFU WRITE BUFFER time |
| 21h | bQueueDepth | shared queue depth (0=per-LU queue model) |
| 22h–23h | wDeviceVersion | |
| 24h | bNumSecureWPArea | max secure write protect areas |
| 25h–28h | dPSAMaxDataSize | max PSA data size (4KB units) |
| 29h | bPSAStateTimeout | |
| 2Ah | iProductRevisionLevel | |
| 4Fh–52h | dExtendedUFSFeaturesSupport | 32-bit; bit[0]=WriteBooster, bit[2]=FFU ext, bit[3]=Refresh, bit[4]=Dynamic Capacity, bit[5]=WriteBooster type, bit[6]=Advanced RPMB, bit[13]=HID, bit[14]=FastRecovery |
| 53h | bWriteBoosterBufferPreserveUserSpaceEn | |
| 54h | bWriteBoosterBufferType | 00h=LU dedicated, 01h=shared buffer |
| 55h–58h | dNumSharedWriteBoosterBufferAllocUnits | for shared buffer type |
| 59h + | bDeviceCapabilityExt, etc. | |

**RPMB Unit Descriptor Key Fields**:
- bRPMBRegionEnable: bits[0–3]=region 0–3 enabled; bit[4]=Advanced RPMB mode
- bRPMBRegion0Size–bRPMBRegion3Size: size in 128KB units (0 = disabled)
- bRPMBLifeTimeEst: 00h=no info, 01h–0Ah=0–100% used, 0Bh=exceeded

---

### 1.2 Flags

Accessed via QUERY REQUEST with OPCODE 05h (READ FLAG), 06h (SET FLAG), 07h (CLEAR FLAG), 08h (TOGGLE FLAG).

| IDN | Name | Access | Default | Description |
|-----|------|--------|---------|-------------|
| 01h | fDeviceInit | Set only | 0 | Device sets during init; host polls until cleared |
| 02h | fPermanentWPEn | Write once | 0 | Enables permanent write protection on bLUWriteProtect=02h LUs |
| 03h | fPowerOnWPEn | Power-on-reset | 0 | Enables power-on write protection on bLUWriteProtect=01h LUs |
| 04h | fBackgroundOpsEn | Volatile | 1 | Enables background operations |
| 05h | fDeviceLifeSpanModeEn | Volatile | 0 | Enables device life span mode |
| 06h | fPurgeEnable | Write-only volatile | 0 | Starts purge operation; auto-cleared when done |
| 07h | fRefreshEnable | Write-only volatile | 0 | Starts refresh operation |
| 08h | fPhyResourceRemoval | Persistent | 0 | Triggers physical resource removal (Dynamic Capacity) |
| 09h | fBusyRTC | Read Only | 0 | RTC update in progress |
| 0Bh | fPermanentlyDisableFwUpdate | Write once | 0 | Permanently disables firmware update |
| 0Eh | fWriteBoosterEn | Volatile | 0 | Enables WriteBooster |
| 0Fh | fWriteBoosterBufferFlushEn | Volatile | 0 | Enables WriteBooster buffer flush |
| 10h | fWriteBoosterBufferFlushDuringHibernate | Volatile | 0 | Flush WB buffer during Hibernate |
| 13h | fUnpinEn | Volatile | 0 | Enables unpinning of Pinned data in WriteBooster |
| 80h–FFh | Vendor specific flags | Vendor defined | — | Vendor specific |

---

### 1.3 Attributes

Accessed via QUERY REQUEST OPCODE 03h (READ ATTRIBUTE) / 04h (WRITE ATTRIBUTE). Value field is 64-bit big-endian right-justified.

| IDN | Name | Access | Size | MDV | Description / Enum |
|-----|------|--------|------|-----|-------------------|
| 00h | bBootLunEn | Persistent | 1B | 00h | 00h=disabled, 01h=Boot LU A active, 02h=Boot LU B active |
| 01h | Reserved/HPB | — | — | — | Reserved for HPB extension |
| 02h | bCurrentPowerMode | Read only | 1B | — | 00h=Idle, 10h=Pre-Active, 11h=Active, 20h=Pre-Sleep, 22h=UFS-Sleep, 30h=Pre-PowerDown, 33h=UFS-PowerDown |
| 03h | bActiveICCLevel | Volatile | 1B | — | 00h–0Fh; default=bInitActiveCCLevel |
| 04h | bOutOfOrderDataEn | Write once | 1B | — | 00h=OOO disabled, 01h=both IN/OUT, 02h=DATA IN only, 03h=DATA OUT only |
| 05h | bBackgroundOpStatus | Read only | 1B | — | 00h=not required, 01h=non-critical, 02h=performance impact, 03h=critical |
| 06h | bPurgeStatus | Read only | 1B | — | 00h=idle, 01h=in progress, 02h=stopped, 03h=completed, 04h=failed queue not empty, 05h=general failure |
| 07h | bMaxDataInSize | Persistent | 1B | — | 512-byte units; default=bMaxInBufferSize |
| 08h | bMaxDataOutSize | Persistent | 1B | — | 512-byte units; default=bMaxOutBufferSize |
| 09h | dDynCapNeeded | Read only | 4B | — | Array/LU index; amount of physical memory to release per LU |
| 0Ah | bRefClkFreq | Persistent | 1B | 03h | 0h=19.2MHz, 1h=26MHz, 2h=38.4MHz, 3h=52MHz |
| 0Bh | bConfigDescrLock | Write once | 1B | — | 0h=unlocked, 1h=locked; locks all Configuration Descriptors permanently |
| 0Ch | bMaxNumOfRTT | Persistent | 1B | 02h | Max outstanding RTTs; shall not exceed bDeviceRTTCap |
| 0Dh | wExceptionEventControl | Volatile | 2B | — | Bits 0–11: enable/disable specific exception events |
| 0Eh | wExceptionEventStatus | Read only | 2B | — | Bits 0–10 defined (TOO_HIGH_TEMP=bit0, TOO_LOW_TEMP=bit1, URGENT_BKOPS=bit2, PERFORMANCE_THROTTLING=bit3, WRITEBOOSTER_FLUSH_NEEDED=bit4, DYNAMIC_CAPACITY_NEEDED=bit5, CORRECTION_NEEDED=bit6, DEVICE_HEALTH_EVENT=bit7, DEVICE_LEVEL_EXCEPTION=bit8) |
| 0Fh | dSecondsPassed | Write-only volatile | 4B | — | Seconds since power-on (for RTC) |
| 10h | wContextConf | Volatile | 2B | — | Array/LU/ContextID; INDEX=LUN, SELECTOR=Context ID 01h–0Fh |
| 11h | dCorrPrgBlkNum | Obsolete | — | — | Deprecated |
| 14h | bDeviceFFUStatus | Read Only | 1B | — | 00h=no info, 01h=successful, 02h=corruption, 03h=internal error, 04h=version mismatch, FFh=general error |
| 15h | bPSAState | Persistent | 1B | — | 00h=Off, 01h=Pre-soldering, 02h=Loading Complete, 03h=Soldered |
| 16h | dPSADataSize | Persistent | 4B | — | PSA data size in 4KB units |
| 2Ah | bEXTIIDEn | Write once | 1B | 00h | 00h=EXT_IID ignored, 01h=EXT_IID valid (8-bit IID) |
| 2Ch | bRefreshStatus | Read only | 1B | — | Same structure as bPurgeStatus |
| 2Dh | bRefreshFreq | Persistent | 1B | — | 01h=1 month, FFh=255 months (refresh frequency) |
| 2Eh | bRefreshUnit | Persistent | 1B | — | 00h=minimum capability, 01h=100% of device |
| 2Fh | bRefreshMethod | Persistent | 1B | 00h | 00h=not defined, 01h=Manual-Force, 02h=Manual-Selective |
| 30h | qTimestamp | Write only | 8B | — | Nanoseconds since Jan 1, 1970 UTC |
| 35h | bDefragOperation | Volatile | 1B | — | 00h=disabled, 01h=analysis only, 02h=analysis+defrag |
| 36h | dHIDAvailableSize | Read only | 4B | — | Total fragmented size in 4KB units; FFFFFFFFh=no valid info |
| 37h | dHIDSize | Persistent | 4B | FFFFFFFFh | Size to defrag per operation (4KB units) |
| 38h | bHIDProgressRatio | Read only | 1B | — | 00h=0% to 64h=100% |
| 39h | bHIDState | Read only | 1B | — | 00h=idle, 01h=analysis in progress, 02h=defrag required, 03h=defrag in progress, 04h=defrag completed, 05h=not required |
| 3Dh | bWriteBoosterBufferResizeEn | Write-only volatile | 1B | — | 00h=idle, 01h=decrease, 02h=increase |
| 3Fh | bWriteBoosterBufferPartialFlushMode | Persistent | 1B | — | 00h=no partial flush, 01h=FIFO, 02h=Pinned |
| 47h | wHostHintCacheSize | Persistent | 2B | — | Host hint cache size for out-of-order data transfer |
| 80h–FFh | Vendor specific | Vendor defined | — | — | Vendor specific attributes |

---

### 1.4 UPIU Types

**General UPIU Format**: Basic header (12 bytes) + Transaction-Specific Fields (bytes 12–31) + optional EHS + Data Segment. Minimum 32 bytes, maximum 65600 bytes.

**Basic Header** (bytes 0–11):
- Byte 0: Transaction Type [bit7=HD, bit6=DD, bits5:0=Transaction Code]
- Byte 1: Flags
- Byte 2: LUN
- Byte 3: Task Tag
- Byte 4: IID [bits7:4]
- Byte 5: Command Set Type | EXT_IID (device→host) | Query Function / TM Function
- Byte 6: Response (device→host)
- Byte 7: EXT_IID (host→device) / Status (device→host)
- Bytes 8–9: Total EHS Length | Device Information
- Bytes 10–11: Data Segment Length

| UPIU | Transaction Code | Direction | Key Fields |
|------|-----------------|-----------|------------|
| NOP OUT | 00 0000b (00h) | H→D | No data; connection ping |
| COMMAND | 00 0001b (01h) | H→D | Flags.R=data-in, Flags.W=data-out, Flags.ATTR=task attribute, Flags.CP=priority; bytes 12–15=Expected Data Transfer Length; bytes 16–31=CDB[0:15] |
| DATA OUT | 00 0010b (02h) | H→D | Flags.T=retransmit; Data Buffer Offset + Data Transfer Count; must be integer multiples of Logical Block Size |
| TM REQUEST | 00 0100b (04h) | H→D | TM Function; Input Parameters: LUN, Task Tag, Initiator ID |
| QUERY REQUEST | 01 0110b (16h) | H→D | Query Function=01h(READ)/81h(WRITE); OPCODE; IDN; INDEX; SELECTOR |
| NOP IN | 10 0000b (20h) | D→H | Response=00h; echoes Task Tag |
| RESPONSE | 10 0001b (21h) | D→H | Flags.O=overflow, Flags.U=underflow, Flags.D=DATA OUT mismatch; SCSI Status; Device Information[bit0=EVENT_ALERT, bits5:2=FAST_RECOVERY_NEEDED]; Sense Data (18 bytes fixed format) |
| DATA IN | 10 0010b (22h) | D→H | Flags.T=retransmit; HintControl, HintIID, HintEXT_IID, HintLUN, Hint Data Buffer Offset, Hint Data Count |
| TM RESPONSE | 10 0100b (24h) | D→H | Service Response codes |
| RTT | 11 0001b (31h) | D→H | Flags.T=retransmit; Data Buffer Offset (must be multiple of 4); Data Transfer Count max=bMaxDataOutSize |
| QUERY RESPONSE | 11 0110b (36h) | D→H | Query Response codes; Flag Value at byte 23 |
| REJECT UPIU | 11 1111b (3Fh) | D→H | Response=01h; Basic Header Status=01h for invalid Transaction Type |

**SCSI Status Values** (in RESPONSE UPIU):
- 00h=GOOD, 02h=CHECK CONDITION, 08h=BUSY, 18h=RESERVATION CONFLICT, 28h=TASK SET FULL

**Query Function Codes**:
- 01h=STANDARD READ REQUEST, 81h=STANDARD WRITE REQUEST

**QUERY OPCODE Values**:
- 00h=NOP, 01h=READ DESCRIPTOR, 02h=WRITE DESCRIPTOR, 03h=READ ATTRIBUTE, 04h=WRITE ATTRIBUTE, 05h=READ FLAG, 06h=SET FLAG, 07h=CLEAR FLAG, 08h=TOGGLE FLAG, F0h–FFh=Vendor Specific

**QUERY RESPONSE Codes**:
- 00h=Success, F6h=not readable, F7h=not writeable, F8h=already written, F9h=invalid LENGTH, FAh=invalid value, FBh=invalid SELECTOR, FCh=invalid INDEX, FDh=invalid IDN, FEh=invalid OPCODE, FFh=general failure

**Task Management Functions** (TM REQUEST):
- 01h=Abort Task, 02h=Abort Task Set, 04h=Clear Task Set, 08h=Logical Unit Reset, 80h=Query Task, 81h=Query Task Set

**TM Service Response Codes**:
- 00h=Complete, 04h=Not Supported, 05h=Failed, 08h=Succeeded, 09h=Incorrect LU Number

**EHS (Extended Header Segments)**:
- Max combined 96 bytes; Total EHS Length field = 0, 1, 2, or 3 (units of 32 bytes)
- Only supported in COMMAND UPIU and RESPONSE UPIU
- bEHSType=01h for Advanced RPMB; bLength=02h (60 bytes total including header)

**Sense Data** (18 bytes fixed format, Response Code=70h):
- Byte 2 bits[3:0]: Sense Key
- Byte 7: Additional Sense Length=0Ah
- Byte 12: ASC (Additional Sense Code)
- Byte 13: ASCQ

**Sense Key Values**:
- 00h=NO SENSE, 01h=RECOVERED ERROR, 02h=NOT READY, 03h=MEDIUM ERROR, 04h=HARDWARE ERROR, 05h=ILLEGAL REQUEST, 06h=UNIT ATTENTION, 07h=DATA PROTECT, 08h=BLANK CHECK, 09h=VENDOR SPECIFIC, 0Bh=ABORTED COMMAND, 0Eh=MISCOMPARE

---

### 1.5 Logical Units

| Type | W-LUN | LUN Field in UPIU | Commands Supported |
|------|-------|-------------------|--------------------|
| Normal LU (0–31) | — | 00h–1Fh | All UCS commands when bLUEnable=01h |
| REPORT LUNS | 01h | 81h | INQUIRY, REQUEST SENSE, TEST UNIT READY, REPORT LUNS |
| UFS Device | 50h | D0h | INQUIRY, REQUEST SENSE, TEST UNIT READY, START STOP UNIT, FORMAT UNIT |
| Boot | 30h | B0h | INQUIRY, REQUEST SENSE, TEST UNIT READY, READ (6), READ (10), READ (16), READ BUFFER |
| RPMB | 44h | C4h | INQUIRY, REQUEST SENSE, TEST UNIT READY, SECURITY PROTOCOL IN, SECURITY PROTOCOL OUT |

**LUN Field Encoding** (8-bit in UPIU):
- Bit 7 (WLUN_ID): 0=normal LU, 1=Well-Known LU
- Bits 6:0 (UNIT_NUMBER_ID): LUN value or W-LUN value
- SAM LUN address: C1h prefix for well-known (e.g., Boot=C1 30 00..., RPMB=C1 44 00...)

**LU Configuration Parameters** (Unit Descriptor):
- bLUEnable: 00h=disabled, 01h=enabled
- bBootLunID: 00h=not a boot LU, 01h=Boot LU A, 02h=Boot LU B
- bLUWriteProtect: 00h=not protected, 01h=power-on WP, 02h=permanent WP
- bMemoryType: memory type (Normal=00h, SLC=03h, etc.)
- bDataReliability: 00h=not reliable, 01h=reliable write
- bLogicalBlockSize: 0Ch=4096 bytes (minimum for UFS)
- bProvisioningType: 00h=full provisioned, 02h=thin (TPRZ=0), 03h=thin (TPRZ=1)
- dNumAllocUnits: CEILING((LUCapacity × CapAdjFactor)/(bAllocationUnitSize × dSegmentSize × 512))

---

### 1.6 SCSI Commands (UFS Command Set)

All CDBs are fixed-length (max 16 bytes). CONTROL byte=00h always.

| Command | Opcode | Support | Notes |
|---------|--------|---------|-------|
| FORMAT UNIT | 04h | M | Formats medium; sent to Device W-LUN formats all LUs except RPMB |
| INQUIRY | 12h | M | EVPD=0: Standard (36 bytes); EVPD=1: VPD pages |
| MODE SELECT (10) | 55h | M | Sets mode pages |
| MODE SENSE (10) | 5Ah | M | Returns mode pages |
| PRE-FETCH (10) | 34h | M | Prefetch data into cache |
| PRE-FETCH (16) | 90h | O | |
| READ (6) | 08h | M | |
| READ (10) | 28h | M | Fields: LBA (4B), Transfer Length (2B), GROUP NUMBER (5b) |
| READ (16) | 88h | O | Fields: LBA (8B), Transfer Length (4B) |
| READ BUFFER | 3Ch | M | MODE field: 02h=Data, 1Ch=Error History |
| READ CAPACITY (10) | 25h | M | Returns 8 bytes: Last LBA (4B) + Block Length (4B) |
| READ CAPACITY (16) | 9Eh | M | Returns 32 bytes; includes TPE, TPRZ bits |
| REPORT LUNS | A0h | M | |
| REQUEST SENSE | 03h | M | Returns 18-byte fixed format sense data |
| SECURITY PROTOCOL IN | A2h | M | RPMB via ECh protocol; supported by RPMB W-LUN |
| SECURITY PROTOCOL OUT | B5h | M | RPMB via ECh protocol; supported by RPMB W-LUN |
| SEND DIAGNOSTIC | 1Dh | M | |
| START STOP UNIT | 1Bh | M | POWER CONDITIONS field controls power mode |
| SYNCHRONIZE CACHE (10) | 35h | M | Flush cache to medium |
| SYNCHRONIZE CACHE (16) | 91h | O | |
| TEST UNIT READY | 00h | M | No data; checks readiness |
| UNMAP | 42h | M | De-allocates LBAs; requires thin provisioning |
| VERIFY (10) | 2Fh | M | |
| WRITE (6) | 0Ah | M | |
| WRITE (10) | 2Ah | M | GROUP NUMBER: 11000b=Pinned WriteBooster data, 10000b=System Data |
| WRITE (16) | 8Ah | O | |
| WRITE BUFFER | 3Bh | M | MODE 0Eh=FFU (download microcode with offsets, save, defer active) |
| BARRIER | F0h | M | Flush ordering guarantee between command groups |

**READ (10) CDB** (opcode 28h):
- Byte 1: RDPROTECT=000b | DPO | FUA | FUA_NV=0b
- Bytes 2–5: LOGICAL BLOCK ADDRESS
- Byte 6: GROUP NUMBER (00000b=default; 00001b–01111b=ContextID)
- Bytes 7–8: TRANSFER LENGTH

**WRITE (10) CDB** (opcode 2Ah):
- Same structure as READ (10) with WRPROTECT=000b
- GROUP NUMBER: 10000b=System Data, 11000b=Pinned WriteBooster

**UNMAP Parameter List**: UNMAP DATA LENGTH (2B) + UNMAP BLOCK DESCRIPTOR DATA LENGTH (2B) + Reserved (4B) + UNMAP Block Descriptors (16 bytes each: LBA 8B + Count 4B + Reserved 4B)

**BARRIER** (opcode F0h): 16-byte CDB; no data transfer; only affects Simple task attribute, normal priority commands; scoped per LU

**INQUIRY Response Data** (standard, 36 bytes):
- Byte 0[4:0]: PERIPHERAL DEVICE TYPE (00h=direct access, 1Eh=well-known LU)
- Byte 2: VERSION=06h (SPC conformance)
- Byte 3[3:0]: RESPONSE DATA FORMAT=0010b
- Bytes 8–15: VENDOR IDENTIFICATION (ASCII, 8 chars)
- Bytes 16–31: PRODUCT IDENTIFICATION (ASCII, 16 chars)
- Bytes 32–35: PRODUCT REVISION LEVEL (ASCII, 4 chars = firmware version)

---

### 1.7 Mode Pages

| Page Code | Subpage | Name |
|-----------|---------|------|
| 01h | 00h | Read-Write Error Recovery (AWRE=1b default; READ/WRITE RETRY COUNT; RECOVERY TIME LIMIT) |
| 08h | 00h | Caching (WCE=1b default write-back; RCD=0b default; changeable: WCE, RCD) |
| 0Ah | 00h | Control (QUEUE ALGORITHM MODIFIER=0001b; SWP=changeable; BUSY TIMEOUT PERIOD; TST=000b not changeable) |
| 3Fh | 00h | ALL PAGES |
| 3Fh | FFh | ALL SUBPAGES |

---

### 1.8 Power Modes

| bCurrentPowerMode Value | State | Description |
|------------------------|-------|-------------|
| 00h | Idle | Powered on, not active; VCC may be off |
| 10h | Pre-Active | Transitioning to Active |
| 11h | Active | Full operation; all 3 power supplies on |
| 20h | Pre-Sleep | Transitioning to UFS-Sleep |
| 22h | UFS-Sleep | Reduced power; VCC may be off; UniPro link in Hibernate |
| 30h | Pre-PowerDown | Transitioning to UFS-PowerDown |
| 33h | UFS-PowerDown | Minimal power; device retains data |
| 44h | UFS-DeepSleep | Deepest power saving (optional) |

**START STOP UNIT POWER CONDITION Field Values**:
- 0h=Start valid (LOEJ=0, START=1 → Active; START=0 → Idle)
- 1h=Active
- 2h=Idle
- 3h=Standby
- 5h=Sleep (UFS-Sleep or UFS-DeepSleep)
- 7h=LU Control
- Bh=Force Idle
- Ch=Force Standby

---

### 1.9 RPMB

**RPMB Resources** (per region):
- Authentication Key: 32 bytes; write-once; not readable or erasable
- Write Counter: 4 bytes; max FFFFFFFFh (no overflow reset); per-region
- Result Register: 2 bytes; per-region
- RPMB Data Area: 128KB–16MB; multiples of 128KB; readable/writable only via authenticated access

**RPMB Modes**:
- Normal RPMB: 512-byte data blocks; message frame = 512 bytes
- Advanced RPMB: 4KB data blocks; uses EHS; bRPMBRegionEnable bit[4]=1

**SECURITY PROTOCOL SPECIFIC** (RPMB Protocol ID):
- 00h 01h = RPMB Region 0
- 01h 01h = RPMB Region 1
- 02h 01h = RPMB Region 2
- 03h 01h = RPMB Region 3

**Request Message Types** (Table 12.8):
- 0001h=Auth Key programming, 0002h=Write Counter read, 0003h=Auth data write, 0004h=Auth data read, 0005h=Result read (Normal only), 0006h=Secure WP Config Block write, 0007h=Secure WP Config Block read, 0008h=RPMB Purge Enable, 0009h=RPMB Purge Status Read, 0010h=Auth Vendor Specific Command, 0011h=Auth Vendor Specific Status Read

**Response Message Types** (Table 12.9):
- 0100h–1100h corresponding responses

**RPMB Operation Result Codes** (Table 12.11):
- 0000h=OK, 0001h=General failure, 0002h=Auth failure (MAC mismatch), 0003h=Counter failure, 0004h=Address failure, 0005h=Write failure, 0006h=Read failure, 0007h=Key not programmed, 0008h=Secure WP Config access failure, 0009h=Invalid Secure WP Config parameter, 000Ah=Secure WP not applicable, 000Bh=Unrecognized request type, 000Ch=Rejected (RPMB Purge in progress)

**MAC**: HMAC-SHA-256 (256-bit = 32 bytes); calculated over bytes 228–511 of each data frame

**RPMB Purge Status**:
- 00h=not initiated, 01h=in progress, 02h=completed, 03h=general failure

**Secure Write Protect Entry** (16 bytes): WPT (2-bit: NV=00b, P=01b, NV-AWP=10b) + WPF (1-bit) + Reserved + LOGICAL BLOCK ADDRESS (8B) + NUMBER OF LOGICAL BLOCKS (4B)

**Normal RPMB Message Data Frame** (512 bytes): Stuff Bytes (196B) + Key/MAC (32B) + Data (256B) + Nonce (16B) + Write Counter (4B) + Address (2B) + Block Count (2B) + Result (2B) + Msg Type (2B)

---

### 1.10 Physical Layer (M-PHY)

| Parameter | Value |
|-----------|-------|
| Drive Level | Large Amplitude (LA) only |
| State Machine | Type I |
| Low-speed signaling | PWM only (not NRZ) |
| HS GEAR support | HS-GEAR1 through HS-GEAR5 (all mandatory) |
| PWM GEAR support | PWM-GEAR1 only (mandatory) |
| TX_HSGEAR_Capability | 5 (HS_G1_TO_G5) |
| RX_HSGEAR_Capability | 5 |
| TX_PWMGEAR_Capability | 1 (PWM_G1_ONLY) |
| RX_PWMGEAR_Capability | 1 |
| Termination (HS-BURST) | On by default |
| Termination (PWM-BURST) | Off by default (can be enabled) |
| TX_HS_PREPARE_LENGTH | 15 (at reset) |
| TX_HS_SYNC_LENGTH | 15 COARSE type (at reset) |
| TX_LS_PREPARE_LENGTH | 10 (at reset) |
| Adapt sequence | Supported (M-PHY 4.1+); device shall implement and be able to initiate |

**HS Gear Rates** (from Chapter 06):
- GEAR1: 1248–1459 Mbps
- GEAR2: 2496–2918 Mbps
- GEAR3: 4992–5830 Mbps (mandatory since UFS 3.0)
- GEAR4: ~9984 Mbps
- GEAR5: 19968–23347 Mbps (mandatory since UFS 4.0)

---

### 1.11 Reference Clock

| Frequency | bRefClkFreq | Max RMS Jitter | Use |
|-----------|-------------|----------------|-----|
| 19.2 MHz | 0h | 5.9 ps | Not for HS-GEAR5 |
| 26.0 MHz | 1h | 4.6 ps | Not for HS-GEAR5 |
| 38.4 MHz | 2h | 3.5 ps | |
| 52.0 MHz | 3h | 2.8 ps | Default (MDV=03h) |

Deterministic Jitter max = 15 ps for all frequencies.

---

### 1.12 Power Supplies

| Supply | Range | Notes |
|--------|-------|-------|
| VCC | 2.4–2.7 V (typ 2.5V) | Main supply; 3.3V support dropped in UFS 4.0; 1.8V removed in UFS 3.0 |
| VCCQ | 1.14–1.26 V (typ 1.2V) | Core/IO supply |
| VCCQ2 | 1.70–1.95 V (typ 1.8V) | Secondary IO supply |

---

### 1.13 UniPro Layer

| Parameter | Value |
|-----------|-------|
| CPort | 0 (single CPort) |
| E2E flow control | Not used (T_CPortFlags=6) |
| N_DeviceID host | 0 |
| N_DeviceID device | 1 |
| T_PeerDeviceID host | 1 |
| T_PeerDeviceID device | 0 |
| T_SDU min | 32 bytes |
| T_SDU max | 65600 bytes |

---

## Part 2: Concepts

### 2.1 UFS Architecture

UFS uses a three-layer architecture:
1. **UFS Application Layer (UAP)**: UFS Command Set (UCS), Device Manager, Task Manager; contains UCS (SCSI commands), QUERY functions, Task Management
2. **UFS Transport Protocol Layer (UTP)**: Handles UPIU transactions; SCSI command encapsulation; data transfer sequencing (RTT mechanism)
3. **UFS Interconnect Layer (UIC)**: MIPI UniPro + MIPI M-PHY; physical packet transport

**Service Access Points (SAPs)**: UDM_SAP (Device Manager), UIO_SAP (UniPro IO), UTP_CMD_SAP (Commands), UTP_TM_SAP (Task Management)

**Physical Signals**: REF_CLK, DIN_t/c (differential pair in), DOUT_t/c (differential pair out), RST_n (active-low hardware reset)

**I_T_L_Q Nexus**: Initiator–Target–Logical Unit–Command identifier; uniquely identifies a command in flight. Components: IID/EXT_IID (Initiator ID), Target (implicit), LUN, Task Tag

---

### 2.2 Initialization Sequence

Three phases:
1. **Partial Initialization**: Host sends single NOP OUT; device responds with NOP IN; link layer established
2. **Boot Transfer**: Boot W-LUN accessible; READ commands allowed to read boot code
3. **Initialization Completion**: Host polls fDeviceInit flag (01h); device sets flag to 1 at startup and clears to 0 when initialization complete; host must wait for flag=0 before sending normal commands

Valid UPIU types per phase are defined in Table 13.2. READ BUFFER (for error log) available at Boot Ready state.

---

### 2.3 WriteBooster

SLC buffer for write acceleration. Controlled by:
- fWriteBoosterEn (0Eh): enable/disable
- fWriteBoosterBufferFlushEn (0Fh): enable flush
- fWriteBoosterBufferFlushDuringHibernate (10h): flush during Hibernate
- bWriteBoosterBufferType (Device Descriptor 54h): 00h=LU dedicated, 01h=shared

**User Space Modes**:
1. User Space Reduction Mode: WriteBooster buffer consumes logical LU space
2. Preserve User Space Mode: WriteBooster buffer from reserved physical area

**Partial Flush Modes** (bWriteBoosterBufferPartialFlushMode 3Fh):
- 00h=no partial flush
- 01h=FIFO mode: flush oldest data first
- 02h=Pinned mode: retain data marked with GROUP NUMBER=11000b; flush non-pinned first

**Buffer Resize**: bWriteBoosterBufferResizeEn (3Dh): 01h=decrease, 02h=increase; triggers resize and reports via exception event

---

### 2.4 BARRIER Command (F0h)

Guarantees flush ordering between command groups. Rules:
- Only affects Simple task attribute, normal priority commands
- Does NOT affect Head of Queue or high-priority commands
- Scoped per LU (LUN field in CDB)
- Device may flush lazily; use SYNCHRONIZE CACHE for immediate guarantee
- No data transfer phase

---

### 2.5 Dynamic Device Capacity

Allows physical memory reduction without changing logical capacity.
- dDynCapNeeded (09h): how much physical to remove per LU
- fPhyResourceRemoval (08h): set by host to trigger removal
- qPhyMemResourceCount: total physical blocks available
- qLogicalBlockCount: total logical blocks (does not decrease)
- Exception event: DYNAMIC_CAPACITY_NEEDED
- Controlled by bDynamicCapacityResourcePolicy in Geometry Descriptor

---

### 2.6 Exception Events Mechanism

- wExceptionEventStatus (0Eh): read-only; bits indicate active events
- wExceptionEventControl (0Dh): enables/disables events
- EVENT_ALERT bit[0] in RESPONSE UPIU Device Information field signals host
- Host reads wExceptionEventStatus to identify event; device clears bit when status read

**Exception Event Bits** (wExceptionEventStatus):
- bit0: TOO_HIGH_TEMP
- bit1: TOO_LOW_TEMP
- bit2: URGENT_BKOPS
- bit3: PERFORMANCE_THROTTLING
- bit4: WRITEBOOSTER_FLUSH_NEEDED
- bit5: DYNAMIC_CAPACITY_NEEDED
- bit6: CORRECTION_NEEDED
- bit7: DEVICE_HEALTH_EVENT
- bit8: DEVICE_LEVEL_EXCEPTION

---

### 2.7 Context Management

- wContextConf (10h): Volatile; Array indexed by LUN and ContextID
- ContextID range: 01h–0Fh (via SELECTOR field in Query Request)
- GROUP NUMBER field in READ/WRITE CDB: 00001b–01111b = ContextID value
- **Reliability Modes**: MODE0 (no extra reliability), MODE1, MODE2 (higher reliability)
- **Large Unit mode**: writes spanning multiple allocation units treated as atomic

---

### 2.8 Production State Awareness (PSA)

Allows secure data loading before device is soldered:
1. Check bUFSFeaturesSupport[1]=1 (PSA supported)
2. Set dPSADataSize (max data size in 4KB units)
3. Set bPSAState=01h (Pre-soldering)
4. Write PSA data
5. Set bPSAState=02h (Loading Complete)
6. Solder device onto board
7. First write after soldering triggers device to set bPSAState=03h (Soldered) — irreversible

State machine: Off(00h) → Pre-soldering(01h) → Loading Complete(02h) → Soldered(03h); Soldered is permanent.

---

### 2.9 Host Initiated Defragmentation (HID)

HID (new in UFS 4.1) allows host to control L2P defragmentation. Supported if dExtendedUFSFeaturesSupport bit[13]=1.

**Flow**:
1. Host sets bDefragOperation=01h (analysis) or 02h (analysis+defrag)
2. Device processes after command queue empties
3. After analysis, device updates bHIDState and dHIDAvailableSize
4. Host sets dHIDSize to limit defrag scope
5. Sets bDefragOperation=02h to start defrag
6. Monitors bHIDProgressRatio (0–100%)
7. After reading bHIDState=04h (Completed), device resets all HID state

**State Machine** (bHIDState): 00h(Idle) → 01h(Analysis) → 02h(Defrag Required) or 05h(Not Required) → 03h(Defrag In Progress) → 04h(Completed) → back to 00h(Idle)

HID is terminated if any medium-changing command is received during operation.

---

### 2.10 Field Firmware Update (FFU)

- Supported if bUFSFeaturesSupport bit[0]=1
- Uses WRITE BUFFER command MODE=0Eh (download microcode with offsets, save, defer active)
- BUFFER OFFSET should be 4KB-aligned; BUFFER ID=00h; sent to same LU with Simple or Ordered task attribute
- Firmware activated on next hardware reset or power cycle
- Host verifies success via bDeviceFFUStatus attribute after reinit

---

### 2.11 Out-of-Order Data Transfer

Enabled when bDataOrdering=01h/02h/03h AND bOutOfOrderDataEn≠00h.
- Device controls DATA IN / RTT UPIU ordering
- Host uses Hint fields (HintControl, HintIID, Hint Data Buffer Offset, Hint Data Count in 4KB units) to pre-position DMA
- wHostHintCacheSize limits hint cache at host
- In-order enforced when disabled (bOutOfOrderDataEn=00h); HintControl=0

---

### 2.12 Fast Recovery Mode (New in UFS 4.1)

When device detects non-recoverable hardware error:
1. Device sends RESPONSE UPIU with FAST_RECOVERY_NEEDED field in Device Information (bits 5:2)
2. Value 0h–Fh = 0–14 second delay hint before host should issue HW Reset
3. Host decides based on hint and its own recovery policy whether to perform HW Reset

---

### 2.13 Purge Operation

Removes data from physical blocks not mapped to logical blocks (protects against die-level attacks).
- Enable: set fPurgeEnable=1 (requires empty command queues)
- Monitor: bPurgeStatus
- During purge: only descriptor/attribute/flag reads allowed (except fPurgeEnable write)
- Interrupt: set fPurgeEnable=0

**RPMB Purge**: Variant targeting RPMB regions; mandatory since UFS 4.0. Result code 000Ch=rejected (purge in progress).

---

### 2.14 Refresh Operation

Relocates data to mitigate retention degradation. Controlled by:
- fRefreshEnable (07h): trigger
- bRefreshStatus (2Ch): same states as bPurgeStatus
- bRefreshMethod (2Fh): 01h=Manual-Force, 02h=Manual-Selective
- bRefreshFreq (2Dh): 01h–FFh months
- bRefreshUnit (2Eh): 00h=minimum, 01h=100% device
- dRefreshProgress and dRefreshTotalCount in Device Health Descriptor

---

### 2.15 Device Data Protection

Three write protection modes:
1. **Permanent WP** (bLUWriteProtect=02h + fPermanentWPEn=1): irreversible
2. **Power-on WP** (bLUWriteProtect=01h + fPowerOnWPEn=1): cleared on power cycle/HW reset
3. **Secure WP** (via RPMB Secure Write Protect Config Block): 4 entries per LU, max bNumSecureWPArea total; WPT=NV/P/NV-AWP; WPF=enable/disable
4. **Software WP** (Control Mode Page SWP bit)

---

### 2.16 Queue Architecture

**Shared Queue** (bQueueDepth>0 in Device Descriptor):
- Single shared queue across all LUs
- Depth = bQueueDepth

**Per-LU Queue** (bQueueDepth=0, bLUQueueDepth>0):
- Each LU has independent queue
- Depth = bLUQueueDepth

If queue full: device returns TASK SET FULL (28h).
bMaxNumOfRTT (attribute 0Ch): limits outstanding RTTs; must be ≤bDeviceRTTCap.

---

### 2.17 Data Out Transfer Rules

Three rules (enforced via RTT/DATA OUT):
1. **Rule 1**: Host sends exactly one DATA OUT per RTT; mismatch triggers ABORTED COMMAND (Flags.D=1)
2. **Rule 2**: Device shall not have more outstanding RTTs than bMaxNumOfRTT
3. **Rule 3**: DATA OUT UPIUs sent in same order RTTs received (across all LUs)

---

### 2.18 UFS Cache

Device-level volatile cache. Key behaviors:
- DPO bit in CDB: when=1, lowest retention priority for cache replacement
- FUA bit in CDB: when=1, force medium access (bypass cache for writes and reads)
- NV_SUP=0b (no non-volatile cache)
- VERIFY command: both FUA and sync cache implied
- Cache not used for Boot W-LUN or RPMB W-LUN
- Data may be lost on power cycle (write-back caching)

---

### 2.19 Thin Provisioning / UNMAP / Discard/Erase

bProvisioningType values:
- 00h: Full provisioning (UNMAP not supported)
- 02h: Thin provisioning TPRZ=0 (Discard: unmapped LBA may return any data)
- 03h: Thin provisioning TPRZ=1 (Erase: unmapped LBA returns zeros)

UNMAP command: provides list of LBA extents to de-allocate; each block descriptor = 16 bytes (LBA 8B + Count 4B + Reserved 4B).

---

## Part 3: Key Claims

### Architecture & Protocol

1. **[Ch 04, Ch 28]** UFS device shall support HS-GEAR1 through HS-GEAR5 (all mandatory). PWM-GEAR1 is the only mandatory PWM gear. (§4.1)

2. **[Ch 10]** UPIU minimum size is 32 bytes (basic header + transaction-specific fields). Maximum size is 65600 bytes. T_SDU max = 65600 bytes.

3. **[Ch 10]** EHS (Extended Header Segments) are only supported in COMMAND UPIU and RESPONSE UPIU; Total EHS Length shall be 0 in all other UPIU types.

4. **[Ch 10]** Max combined EHS = 96 bytes; Total EHS Length field values = 0, 1, 2, or 3 (units of 32 bytes).

5. **[Ch 22, Ch 10]** Device processes only one NOP OUT or QUERY REQUEST at any point in time.

6. **[Ch 21]** REJECT UPIU is sent only when invalid Transaction Type received (HD or DD bit set or unknown Transaction Code). NOT sent for: wrong LUN in COMMAND UPIU, wrong LUN in TM REQUEST, or wrong Query Function in QUERY REQUEST.

7. **[Ch 20]** QUERY RESPONSE Flag Value is at byte 23 (00h=cleared, 01h=set).

8. **[Ch 19]** Write Attribute VALUE field is 64-bit big-endian right-justified.

9. **[Ch 24]** DATA OUT UPIU Data Buffer Offset and Data Transfer Count must be integer multiples of Logical Block Size.

10. **[Ch 16]** RTT Data Buffer Offset shall be an integer multiple of 4. Data Transfer Count max = bMaxDataOutSize.

### Descriptors & Flags

11. **[Ch 68]** wSpecVersion=0410h identifies UFS 4.1 device.

12. **[Ch 68]** bConfigDescrLock (attribute 0Bh) when set to 1 permanently locks ALL configuration descriptors — irreversible.

13. **[Ch 68]** Configuration Descriptor supports 4 indexes (00h–03h), each covering 8 LUs; bConfDescContinue=01h means more to follow.

14. **[Ch 69]** fDeviceInit (IDN=01h) is Set-only by host; device sets it to 1 during initialization, then clears it to 0 when ready. Host must poll until 0.

15. **[Ch 69]** fPurgeEnable (IDN=06h) can only be set when command queues of ALL logical units are empty.

16. **[Ch 69]** fPermanentWPEn (IDN=02h) is Write-Once and cannot be cleared once set.

### Attributes

17. **[Ch 70]** bRefClkFreq MDV=03h (52.0 MHz is the default reference clock frequency in UFS 4.1).

18. **[Ch 70]** bMaxNumOfRTT MDV=02h; shall not be set higher than bDeviceRTTCap; can only be set when all LU command queues are empty.

19. **[Ch 70]** bOutOfOrderDataEn is Write-Once — cannot be changed after first write.

20. **[Ch 70]** bConfigDescrLock write once; locks Configuration Descriptor when set to 01h.

21. **[Ch 70]** qTimestamp is write-only; value in nanoseconds since Jan 1, 1970 UTC.

### LUs & Commands

22. **[Ch 28, Ch 10]** If bLUEnable=01h, each LU shall support all commands in Table 11.1 as mandatory.

23. **[Ch 34]** READ CAPACITY (10) and READ CAPACITY (16): Minimum Logical Block Size for UFS = 4096 bytes.

24. **[Ch 35]** TPRZ bit in READ CAPACITY (16) response: set by bProvisioningType. TPRZ=1 (03h) means unmapped LBA returns zeros; TPRZ=0 (02h) means unmapped LBA may return any data.

25. **[Ch 28]** UFS only supports fixed-length CDB format (no Variable Length CDB as in SCSI).

26. **[Ch 28]** CONTROL byte in all UFS CDBs shall be set to zero and shall be ignored. ACA is not supported.

27. **[Ch 29]** INQUIRY STANDARD DATA: PERIPHERAL DEVICE TYPE=00h for normal LU, 1Eh for well-known LU. VERSION=06h. RESPONSE DATA FORMAT=0010b. At least 36 bytes returned.

28. **[Ch 29]** PRODUCT REVISION LEVEL (bytes 32–35) shall identify firmware version; shall be uniquely encoded for any firmware modification.

29. **[Ch 32]** GROUP NUMBER in READ CDB: 00001b–01111b are Context IDs 1–15. Reserved values cause CHECK CONDITION with ILLEGAL REQUEST.

30. **[Ch 39]** GROUP NUMBER in WRITE CDB: 11000b=Pinned data (Pinned WriteBooster Partial Flush); 10000b=System Data.

31. **[Ch 47]** UNMAP command not supported on full-provisioned LUs (bProvisioningType=00h).

32. **[Ch 47]** If UNMAP BLOCK DESCRIPTOR DATA LENGTH is not a multiple of 16, the last incomplete descriptor is ignored.

33. **[Ch 42]** FORMAT UNIT to Device W-LUN formats all enabled LUs except RPMB W-LUN.

34. **[Ch 42]** After successful FORMAT UNIT: all LBAs shall be mapped (if full-provisioned) or unmapped (if thin-provisioned). Read on unmapped LBA after format returns zeros.

35. **[Ch 49]** FFU WRITE BUFFER MODE=0Eh only; firmware is activated on next power-on or hard reset, NOT on START STOP UNIT or FORMAT UNIT.

36. **[Ch 49]** WRITE BUFFER BUFFER OFFSET for FFU should be 4KB-aligned.

37. **[Ch 49]** BARRIER command (F0h) only affects Simple task attribute, normal priority commands. Head of Queue and high-priority commands are not affected.

### Power & Initialization

38. **[Ch 07]** Three power supplies mandatory: VCC (2.4–2.7V), VCCQ (1.14–1.26V), VCCQ2 (1.70–1.95V). VCC=3.3V dropped in UFS 4.0; VCC=1.8V removed in UFS 3.0.

39. **[Ch 07]** RST_n assertion causes full hardware reset; device returns to default state.

40. **[Ch 64]** Boot sequence: partial init → boot transfer → init completion. fDeviceInit cleared by device signals completion.

41. **[Ch 64]** Boot W-LUN (30h/B0h) provides read-only access to active Boot LU.

### RPMB

42. **[Ch 56]** Each RPMB region has its own dedicated authentication key, write counter, and result register.

43. **[Ch 56]** Write Counter starts at 00000000h and increments per authenticated write. Maximum = FFFFFFFFh; no wrap-around.

44. **[Ch 57]** Authentication key not programmed state (0007h) is the only valid result until authentication key is programmed; after programming, 0007h will never occur again.

45. **[Ch 56]** MAC uses HMAC-SHA-256; key = 256-bit authentication key stored in device.

46. **[Ch 59]** SECURITY PROTOCOL IN/OUT for RPMB: SECURITY PROTOCOL=ECh; ALLOCATION/TRANSFER LENGTH must be multiple of 512 (Normal RPMB) or 4096 (Advanced RPMB).

47. **[Ch 53]** RPMB Purge is mandatory since UFS 4.0. While RPMB Purge is in progress, authenticated read/write returns result code 000Ch.

### Data Protection

48. **[Ch 55]** bSecureRemovalType values: 00h=erase only (default), 01h=overwrite+erase, 02h=overwrite+complement+random+erase, 03h=vendor defined.

49. **[Ch 55]** fPermanentWPEn enables permanent write protection on bLUWriteProtect=02h LUs. After manufacturing, fPermanentWPEn=0.

50. **[Ch 55]** WPF (Secure Write Protect Flag) shall be 0 after manufacturing.

51. **[Ch 55]** Secure Write Protect areas (up to 4 per LU) apply only to LUs configured as not write protected (bLUWriteProtect=00h). Total secure write protect areas shall not exceed bNumSecureWPArea.

### Unit Attention

52. **[Ch 24]** Unit Attention Condition (UAC): Power-on, HW Reset, EndPointReset, Host UniPro Warm Reset establish UAC on ALL LUs including well-known. LU Reset establishes UAC on addressed LU only.

53. **[Ch 24]** INQUIRY returns GOOD status with UAC pending (does NOT clear UAC). REQUEST SENSE returns GOOD and CLEARS UAC. REPORT LUNS returns GOOD but does NOT clear UAC.

### HID

54. **[Ch 66]** HID (Host Initiated Defragmentation) is supported if dExtendedUFSFeaturesSupport bit[13]=1.

55. **[Ch 66]** bDefragOperation can only be set after UFS initialization phase (fDeviceInit cleared). Setting before init completion fails with FFh General Failure.

56. **[Ch 66]** If medium-changing command received during HID analysis/defrag, HID operation may be terminated; bDefragOperation, bHIDProgressRatio, bHIDState are reset to 0.

57. **[Ch 66]** After host reads bHIDState=04h (Completed) or 05h (Not Required), device resets bHIDState, bHIDProgressRatio, bDefragOperation to 0 and dHIDAvailableSize to FFFFFFFFh.

### PSA

58. **[Ch 67]** PSA state Soldered (03h) is irreversible — cannot be changed back.

59. **[Ch 67]** First write after soldering triggers device to automatically set bPSAState to Soldered (03h).

---

## Part 4: Chapter Map

| Filename | Content Summary |
|----------|----------------|
| 01_title_page.md | JEDEC Standard No. 220G title page and copyright information |
| 02_table_of_contents.md | Complete table of contents for all 73 chapters and annexes |
| 03_3_terms_definitions_keywords.md | Definitions for terms: application client, device server, initiator device, target device, transaction, and UFS-specific keywords |
| 04_4_introduction.md | UFS 4.1 general features: all HS gears GEAR1–GEAR5 mandatory, PWM-GEAR1 only mandatory PWM gear, 3 power supplies, BER ≤10⁻¹² |
| 05_5_ufs_architecture.md | Three-layer UFS architecture (UAP/UTP/UIC), SAPs (UDM, UIO, UTP_CMD, UTP_TM), physical signals, I_T_L_Q Nexus definition |
| 06_6_ufs_electrical.md | Power supply specs (VCC/VCCQ/VCCQ2), reference clock frequencies (19.2/26/38.4/52 MHz, default=52), HS gear data rates, RST_n timing |
| 07_7_reset_power-up_and_power-down.md | Power mode state machine (Active/Idle/Sleep/PowerDown/DeepSleep), bCurrentPowerMode values, bActiveICCLevel, START STOP UNIT POWER CONDITION values, reset behaviors |
| 08_8_ufs_uic_layer_mipi_m-phy.md | M-PHY configuration: Large Amplitude only, Type I state machine, PWM signaling in LS mode, all HS gears mandatory, Adapt sequence, PHY capability attributes |
| 09_9_ufs_uic_layer_mipi_unipro.md | UniPro configuration: single CPort 0, no E2E flow control, N_DeviceID assignments, T_PeerDeviceID assignments, DME attributes |
| 10_1023_unipro.md | UPIU Transaction Codes table, General UPIU Format (Table 10.3), UTP overview, UPIU size limits (min 32B / max 65600B) |
| 11_1062_basic_header_format.md | Basic UPIU Header (12 bytes) field layout: Transaction Type, Flags, LUN, Task Tag, IID, EXT_IID, Response, Status, EHS, Data Segment Length; EHS format |
| 12_1071_command_upiu.md | COMMAND UPIU format: Transaction Code=01h, Flags (R/W/ATTR/CP), Expected Data Transfer Length, 16-byte CDB |
| 13_1072_response_upiu.md | RESPONSE UPIU: Transaction Code=21h, SCSI Status values, Device Information (EVENT_ALERT/FAST_RECOVERY_NEEDED), 18-byte sense data, Sense Keys |
| 14_1073_data_out_upiu.md | DATA OUT UPIU: Transaction Code=02h, Flags.T=retransmit, Data Buffer Offset/Count rules (must be multiples of LBS) |
| 15_1074_data_in_upiu.md | DATA IN UPIU: Transaction Code=22h, HintControl/HintIID/HintLUN/Hint Data fields for out-of-order transfer |
| 16_1075_ready_to_transfer_upiu.md | RTT UPIU: Transaction Code=31h, Flags.T=retransmit, Data Buffer Offset (multiple of 4), Data Transfer Count max=bMaxDataOutSize |
| 17_1076_task_management_request_upiu.md | TM REQUEST: Transaction Code=04h, Task Management Functions (Abort Task/Set, Clear Task Set, LU Reset, Query Task/Set), Input Parameters |
| 18_1077_task_management_response_upiu.md | TM RESPONSE: Transaction Code=24h, Service Response codes (00h=Complete, 04h=Not Supported, 05h=Failed, 08h=Succeeded, 09h=Incorrect LU) |
| 19_1078_query_request_upiu.md | QUERY REQUEST: Transaction Code=16h, Query Functions (01h/81h), OPCODE values (00h-08h), descriptor/attribute/flag read/write operations |
| 20_1079_query_response_upiu.md | QUERY RESPONSE: Transaction Code=36h, Query Response codes (00h=Success through FFh=general failure), Flag Value at byte 23 |
| 21_10710_reject_upiu.md | REJECT UPIU: Transaction Code=3Fh, Response=01h, sent for invalid Transaction Type only; NOT for wrong LUN or Query Function |
| 22_10711_nop_out_upiu.md | NOP OUT: Transaction Code=00h, connection ping, no data segment |
| 23_10712_nop_in_upiu.md | NOP IN: Transaction Code=20h, Response=00h, echoes NOP OUT Task Tag, no data segment |
| 24_10713_data_out_transfer_rules.md | Three data-out transfer rules: Rule1=one DATA OUT per RTT, Rule2=max outstanding RTTs=bMaxNumOfRTT, Rule3=DATA OUT order matches RTT order; Mismatch→ABORTED COMMAND |
| 25_1097_data_transfer_scsi_transport_protocol_services.md | Send Data-In / Data-In Delivered / Receive Data-Out / Data-Out Received transport protocol service primitives and parameters |
| 26_1098_task_management_function_procedure_calls.md | Task Management Function procedure calls: how ABORT TASK, LU RESET, etc. are invoked and responded to |
| 27_1099_query_function_transport_protocol_services.md | Query Function transport protocol services for descriptor/attribute/flag access |
| 28_11_ufs_application_uap_layer_scsi_commands.md | UFS SCSI command set overview (Table 11.1), all mandatory/optional commands, UNC not defined, CDB general format, CONTROL=00h always |
| 29_1132_inquiry_command.md | INQUIRY command (12h): Standard (36 bytes) and VPD page response; PERIPHERAL DEVICE TYPE, VERSION, VENDOR/PRODUCT/REVISION fields |
| 30_1133_mode_select_10_command.md | MODE SELECT (10) command (55h): sets mode pages; no block descriptor in UFS |
| 31_1134_mode_sense_10_command.md | MODE SENSE (10) command (5Ah): reads mode pages; Mode Parameter Header format |
| 32_1136_read_10_command.md | READ (10) command (28h): DPO/FUA flags, LBA (4B), Transfer Length (2B), GROUP NUMBER/ContextID |
| 33_1137_read_16_command.md | READ (16) command (88h): optional; LBA (8B), Transfer Length (4B); same parameter semantics as READ (10) |
| 34_1138_read_capacity_10_command.md | READ CAPACITY (10) command (25h): returns 8 bytes (Last LBA 4B + Block Length 4B); min block size=4096 bytes; returns FFFFFFFFh if LBA count overflows 32-bit |
| 35_1139_read_capacity_16_command.md | READ CAPACITY (16) command (9Eh): returns 32 bytes including TPE, TPRZ bits, Logical Blocks per Physical Block Exponent |
| 36_11312_report_luns_command.md | REPORT LUNS command (A0h): returns list of enabled LUs and well-known LUs |
| 37_11313_verify_10_command.md | VERIFY (10) command (2Fh): verification implies FUA + cache sync |
| 38_11314_write_6_command.md | WRITE (6) command (0Ah): mandatory; small CDB variant |
| 39_11315_write_10_command.md | WRITE (10) command (2Ah): DPO/FUA flags, LBA, Transfer Length, GROUP NUMBER; 11000b=Pinned WB, 10000b=System Data |
| 40_11316_write_16_command.md | WRITE (16) command (8Ah): optional; extended LBA addressing |
| 41_11317_request_sense_command.md | REQUEST SENSE command (03h): returns 18-byte fixed sense data; clears UAC if pending; DESC=0 (descriptor format not required) |
| 42_11318_format_unit_command.md | FORMAT UNIT command (04h): formats medium; to Device W-LUN formats all LUs except RPMB; post-format read returns zeros |
| 43_11319_pre-fetch_10_command.md | PRE-FETCH (10) command (34h): hints device to prefetch data into cache |
| 44_11322_security_protocol_out_command.md | SECURITY PROTOCOL OUT command (B5h): sends data to RPMB via ECh protocol; data delivered via RTT/DATA OUT |
| 45_11323_send_diagnostic_command.md | SEND DIAGNOSTIC command (1Dh): self-test and diagnostic functions |
| 46_11324_synchronize_cache_10_command.md | SYNCHRONIZE CACHE (10) command (35h): flushes cached writes to medium |
| 47_11326_unmap_command.md | UNMAP command (42h): de-allocates LBAs on thin-provisioned LUs; ANCHOR=0; parameter list with block descriptors (16B each) |
| 48_11327_read_buffer_command.md | READ BUFFER command (3Ch): MODE 02h=Data, 1Ch=Error History; Error History Directory format; retrieve procedure |
| 49_11328_write_buffer_command.md | WRITE BUFFER command (3Bh): MODE 02h=Data, 0Eh=FFU download; BARRIER command (F0h) in same chapter; FFU activation on next power-on/HW-reset only |
| 50_1141_mode_page_overview.md | Mode page overview: page/subpage code structure, Mode Parameter List format, Mode Parameter Header (10) format, Page_0 and Subpage formats |
| 51_1142_ufs_supported_pages.md | UFS supported mode pages: Control (0Ah), Read-Write Error Recovery (01h), Caching (08h); VPD pages: Supported VPD Pages, Mode Page Policy |
| 52_1154_mode_page_policy_vpd_page.md | Mode Page Policy VPD page format and device-level vs LU-level scope for mode pages |
| 53_12224_purge_operation.md | Purge operation: secure data removal from physical blocks; fPurgeEnable flag flow; bPurgeStatus state machine; RPMB Purge variant |
| 54_12233_purge_operation.md | Purge and Discard/Erase implementation via UNMAP command; bProvisioningType=02h (discard) or 03h (erase/secure); bSecureRemovalType values; Wipe Device via FORMAT UNIT to Device W-LUN |
| 55_12236_bsecureremovaltype_parameter.md | bSecureRemovalType: 00h=erase, 01h=overwrite+erase, 02h=3-pass overwrite+erase, 03h=vendor; defines physical removal method during Purge |
| 56_12431_rpmb_resources.md | RPMB resources: Authentication Key (32B write-once), Write Counter (4B), Result Register (2B), RPMB Data Area (128KB–16MB), Secure Write Protect Config Block (256B normal / 4KB advanced), RPMB Purge Response format |
| 57_12437_rpmb_operation_result.md | RPMB Operation Result codes table (0000h–000Ch); bit[7] of Result=Write Counter expired; Request (0001h–0011h) and Response (0100h–1100h) message types |
| 58_12451_advanced_rpmb_message.md | Advanced RPMB message structure in EHS field (60 bytes): bLength=02h, bEHSType=01h, Advanced RPMB Meta Information (28B) + MAC/Key (32B); data via DATA IN/OUT segments; SECURITY PROTOCOL=ECh |
| 59_12461_cdb_format_of_security_protocol_inout_commands.md | SECURITY PROTOCOL IN (A2h) / OUT (B5h) CDB format; ECh=JEDEC UFS; RPMB Protocol IDs (00h–03h = Regions 0–3); transfer length requirements (512B or 4KB multiples) |
| 60_12471_request_type_message_delivery.md | RPMB request message delivery flow (host→device via SECURITY PROTOCOL OUT / IN sequence) |
| 61_12472_response_type_message_delivery.md | RPMB response message delivery flow (device→host) |
| 62_12473_rpmb_operations_in_normal_rpmb_mode.md | RPMB operations in Normal mode: Auth Key Programming, Write Counter Read, Authenticated Data Write/Read, Secure Write Protect Config flows |
| 63_12474_rpmb_operations_in_advanced_rpmb_mode.md | RPMB operations in Advanced mode using EHS; same operation types with 4KB blocks and EHS-based message delivery |
| 64_13_ufs_functional_descriptions.md | UFS functional descriptions: Boot sequence (three phases), bBootEnable values, fDeviceInit polling, Boot W-LUN read-only access |
| 65_132_logical_unit_management.md | LU management: Normal LU (up to 32), W-LUN types, RPMB regions (0–3, region 0 always enabled), LU config parameters, thin provisioning, dNumAllocUnits formula |
| 66_134_host_device_interaction.md | Host-device interaction: background ops, dynamic capacity, context management, exception events, WriteBooster (types/modes/flush/resize), BARRIER, HID, Refresh, temperature events, Fast Recovery Mode |
| 67_136_production_state_awareness_psa.md | PSA flow: Off→Pre-soldering→Loading Complete→Soldered; bPSAState values; bUFSFeaturesSupport bit[1] indicates support; Soldered state is irreversible |
| 68_14_ufs_descriptors_flags_and_attributes.md | All descriptor types (IDN 00h–09h, F0h–FFh), Device Descriptor fields, Configuration Descriptor (4 indexes), Geometry, Unit, RPMB, Power, Interconnect, all String Descriptors, Device Health Descriptor |
| 69_142_flags.md | Complete flags table (IDN 01h–13h, 80h–FFh): names, access types, default values |
| 70_143_attributes.md | Complete attributes table (IDN 00h–47h+, 80h–FFh): IDN, names, access types, sizes, types, MDV values, full enumeration |
| 71_annex_b_informative_reference_clock_measurement_procedure.md | Reference clock jitter measurement: Random RMS Jitter (max 2.8–5.9 ps depending on frequency), Deterministic Jitter (max 15 ps); DSO test procedure |
| 72_annex_d_informative_board_design_guideline.md | Board design guidelines for UFS 4.0: max impedance Z(f) for VCC/VCCQ/VCCQ2, capacitor recommendations, PMIC (Buck vs LDO) noise budgets |
| 73_annex_e_informative_differences_between_revisions.md | Differences between revisions (JESD220A through 220G): new features per revision, mandatory-ization of gears, removed features, added attributes/flags/descriptors |

---

*End of UFS 4.1 Structured Knowledge Report*
*Total chapters read: 73*
*Coverage: All UPIU types, all descriptors (IDN 00h–09h), all flags (IDN 01h–13h), all attributes (IDN 00h–3Fh+), all mandatory SCSI commands, RPMB protocol, and all functional features*
