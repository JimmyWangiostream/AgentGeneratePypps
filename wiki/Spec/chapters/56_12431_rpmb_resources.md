# 12.4.3 Requirements

## 12.4.3.1 RPMB Resources

• **Authentication Key**
  ○ Type: Write once, not erasable or readable
  ○ Size: 32 bytes
  ○ Description: Authentication key register which is used to authenticate accesses when MAC is calculated. Each RPMB region has a dedicated authentication key.

• **Write Counter**
  ○ Type: Read only
  ○ Size: 4 bytes
  ○ Description: Counter value for the total amount of successful authenticated data write requests made by the host. The initial value of this register after production is 0000 0000h. The value will be incremented by one automatically by the UFS device along with each successful programming access. The value cannot be reset. After the counter has reached the maximum value of FFFF FFFFh, it will not be incremented anymore (overflow prevention). Each RPMB region has dedicated write counter.

• **Result Register**
  ○ Type: Read only
  ○ Size: 2 bytes
  ○ Description: This register provides the result of an authenticated operation. Result register values are described in 12.4.3.6. Each RPMB region has dedicated result register.

• **RPMB Data Area**
  ○ Type: Readable and writable
  ○ Size: Multiples of 128 Kbytes defined in RPMB Unit Descriptor
    ▪ 128 Kbytes minimum, 16 Mbytes maximum.
    ▪ Each RPMB region size is defined as bRPMBRegion0Size – bRPMBRegion3Size in the RPMB Unit Descriptor.
  ○ Description: Data which can only be read and written via successfully authenticated read/write access. This data may be overwritten by the host but can never be erased.

• **Secure Write Protect Configuration Block for Normal RPMB**
  ○ Type: Readable and writable
  ○ Size : 256 Bytes
  ○ Description: Secure Write Protect Configuration Block is supported by RPMB region 0 only. This block is used for configuring secure write protect areas in logical units. There is one Secure Write Protect Configuration Block for each logical unit. Each Secure Write Protect Configuration Block has up to four Secure Write Protect Entries. Each entry represents one secure write protect area. If an entry is not used, then the related fields shall contain a value of zero. The Secure Write Protect Configuration Block is structured as shown in Table 12.1.

---

*JEDEC Standard No. 220G*  
*Page 279*

# JEDEC Standard No. 220G
Page 280

## 12.4.3.1 RPMB Resources (cont'd)

• **Secure Write Protect Configuration Block for Advanced RPMB**
  ○ Type: Readable and writable
  
  ○ Size: 4Kbytes
  
  ○ Description: Secure Write Protect Configuration Block is supported by RPMB region 0 only. This block is used for configuring secure write protect areas in logical units. There is one Secure Write Protect Configuration Block for each logical unit. Each Secure Write Protect Configuration Block has up to four Secure Write Protect Entries. Each entry represents one secure write protect area. If an entry is not used, then the related fields shall contain a value of zero. The Secure Write Protect Configuration Block is structured as shown in Table 12.1.

# JEDEC Standard No. 220G
## Page 281

### 12.4.3.1 RPMB Resources (cont'd)

#### Table 12.1 — Secure Write Protect Configuration Block for Normal RPMB

| Byte | Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
|------|-------|-------|-------|-------|-------|-------|-------|-------|
| 0 (228) | | | | LUN | | | | |
| 1 (229) | | | DATA LENGTH | | | | |
| 2 (230) | | | | | | | | |
| ... | | | Reserved | | | | |
| 15 (243) | | | | | | | | |
| 16 (244) | | | | | | | | |
| ... | | | Secure Write Protect Entry 0 | | | | |
| 31 (259) | | | | | | | | |
| 32 (260) | | | | | | | | |
| ... | | | Secure Write Protect Entry 1 | | | | |
| 47 (275) | | | | | | | | |
| 48 (276) | | | | | | | | |
| ... | | | Secure Write Protect Entry 2 | | | | |
| 63 (291) | | | | | | | | |
| 64 (292) | | | | | | | | |
| ... | | | Secure Write Protect Entry 3 | | | | |
| 79 (307) | | | | | | | | |
| 80 (308) | | | | | | | | |
| ... | | | Reserved | | | | |
| 255 (483) | | | | | | | | |

**NOTE 1** Values in parenthesis indicates the byte number in the RPMB Message Data Frame.

# JEDEC Standard No. 220G
Page 282

## 12.4.3.1 RPMB Resources (cont'd)

### Table 12.2 — Secure Write Protect Configuration Block for Advanced RPMB

| Byte⁽¹⁾ | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|---------|---|---|---|---|---|---|---|---|
| 0 | | | | LUN | | | | |
| 1 | | | DATA LENGTH | | | | |
| 2 | | | | | | | | |
| ... | | | Reserved | | | | |
| 15 | | | | | | | | |
| 16 | | | | | | | | |
| ... | | | Secure Write Protect Entry 0 | | | | |
| 31 | | | | | | | | |
| 32 | | | | | | | | |
| ... | | | Secure Write Protect Entry 1 | | | | |
| 47 | | | | | | | | |
| 48 | | | | | | | | |
| ... | | | Secure Write Protect Entry 2 | | | | |
| 63 | | | | | | | | |
| 64 | | | | | | | | |
| ... | | | Secure Write Protect Entry 3 | | | | |
| 79 | | | | | | | | |
| 80 | | | | | | | | |
| ... | | | Reserved | | | | |
| 4095 | | | | | | | | |

# JEDEC Standard No. 220G
## Page 283

### 12.4.3.1 RPMB Resources (cont'd)

#### a) LUN

The LUN field indicates the logical unit to which secure write protection shall apply. Valid values are from 0 to the number of LU specified by bMaxNumberLU.

#### b) DATA LENGTH

The DATA LENGTH field specifies the length in bytes of the Secure Write Protect Entries (0 for no entry, 16 for one entry, 32 for two entries, 48 for three entries and 64 for four entries). In a write request, the device shall ignore the bytes from DATA LENGTH + 16 to 255 in Normal RPMB mode, from DATA LENGTH + 16 to 4095 in Adv. RPMB mode and set these bytes of the Secure Write Protect Configuration Block to zero.

#### c) Secure Write Protect Entry 0 to Entry 3

The Secure Write Protect Configuration Block may contain only the Entry 0, the Entries 0 and 1, the Entries 0, 1 and 2, or all four Entries. If the Secure Write Protect Configuration Block does not contain any entry (DATA LENGTH = 00h), all entries in the specified logical unit will be removed.

Table 12.3 defines the structure of Secure Write Protect Entry.

**Table 12.3 — Secure Write Protect Entry**

| Bit<br>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-------------|---|---|---|---|---|---|---|---|
| 0 |   |   | Reserved |   |   |   | WPT | WPF |
| 1 |   |   |   |   | Reserved |   |   |   |
| 2 |   |   |   |   | Reserved |   |   |   |
| 3 |   |   |   |   | Reserved |   |   |   |
| 4 | (MSB) |   |   |   |   |   |   |   |
| … |   |   | LOGICAL BLOCK ADDRESS |   |   |   |   |   |
| 11 |   |   |   |   |   |   |   | (LSB) |
| 12 | (MSB) |   |   |   |   |   |   |   |
| … |   |   | NUMBER OF LOGICAL BLOCKS |   |   |   |   |   |
| 15 |   |   |   |   |   |   |   | (LSB) |

# JEDEC Standard No. 220G
Page 284

## 12.4.3.1 RPMB Resources (cont'd)

### d) WPT (Write Protect Type)

The write protect type field (WPT) specifies how WPF bit may be modified.

**Table 12.4 — Write Protect Type Field**

| Code | Definition |
|------|------------|
| 00b | NV-type<br>WPF bit is persistent through power cycle and hardware reset. WPF value may only be changed writing to Secure Write Protect Configuration Block. |
| 01b | P-type<br>WPF bit is automatically cleared to 0b after power cycle or hardware reset. |
| 10b | NV-AWP-type<br>WPF bit is automatically set to 1b after power cycle or hardware reset. |
| 11b | Reserved |

### e) WPF (Write Protect Flag)

0b : Secure Write Protection is disabled.
1b : Secure Write Protection is enabled.

A WPF set to one specifies that the logical unit shall inhibit alteration of the medium for LBA within the range indicated by LOGICAL BLOCK ADDRESS field and NUMBER OF LOGICAL BLOCKS field. Commands requiring writes to the medium shall be terminated with CHECK CONDITION status, with the sense key set to DATA PROTECT, and the additional sense code set to WRITE PROTECTED.

Logical units that contain cache shall write all cached logical blocks to the medium (e.g., as they would do in response to a SYNCHRONIZE CACHE command with the LOGICAL BLOCK ADDRESS field and the NUMBER OF LOGICAL BLOCKS field set to the values indicated in the Secure Write Protect Entry) prior to enabling the write protection.

A WPF bit set to zero specifies that the logical unit may allow writing to the medium, depending on other write inhibit mechanisms implemented by the logical unit.

WPF shall be set to zero after device manufacturing.

### f) LOGICAL BLOCK ADDRESS

This field specifies the LBA of the first logical block of the Secure Write Protect area.

# JEDEC Standard No. 220G
Page 285

## 12.4.3.1 RPMB Resources (cont'd)

### g) NUMBER OF LOGICAL BLOCKS

This field specifies the number of contiguous logical blocks that belong to the Secure Write Protect area.

If the NUMBER OF LOGICAL BLOCKS field is set to zero, then the secure write protection shall apply to the entire logical unit. In that case, only Entry-0 needs to be configured to enable secure write protection for the entire logical unit.

• **RPMB Purge Response Packet Format**
  
  ○ The RPMB Purge Response Packet is contained in the Data field of the RPMB Purge Status Response message. Refer to the Data field in Figure 12.12, RPMB Purge Read Flow.

**Table 12.5 — RPMB Purge Response Packet Format (Legacy RPMB Model)**

| Bit  | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|---|---|---|---|---|---|---|---|
| Byte |   |   |   |   |   |   |   |   |
| 0 (228) | | | | | STATUS | | | |
| 1 (229) | | | | bRPMBLifeTimeEst | | | | |
| 2 (230) | | | | | | | | |
| 3 (231) | | | | | | | | |
| 4 (232) | | | | RESERVED | | | | |
| …… | | | | | | | | |
| 255 (483) | | | | | | | | |

**Table 12.6 — RPMB Purge Response Packet Format (Advanced RPMB Model)**

| Bit  | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|---|---|---|---|---|---|---|---|
| Byte |   |   |   |   |   |   |   |   |
| 0 | | | | | STATUS | | | |
| 1 | | | | bRPMBLifeTimeEst | | | | |
| 2 | | | | | | | | |
| 3 | | | | | | | | |
| 4 | | | | RESERVED | | | | |
| …… | | | | | | | | |
| 4095 | | | | | | | | |

# JEDEC Standard No. 220G
## Page 286

### 12.4.3.1 RPMB Resources (cont'd)

RPMB Purge Status Read Response includes:

**a) STATUS**

- 00h : RPMB Purge not initiated (reset value)
- 01h : RPMB Purge in progress
- 02h : RPMB Purge successfully completed. The device will send this status on the next **RPMB Purge Status Read Request**, and this status will change to 00, RPMB Purge not initiated.
- 03h : RPMB Purge General Failure. The device will send this status on the next **RPMB Purge Status Read Request**, and this status will change to 00, RPMB Purge not initiated.

**b) bRPMBLifeTimeEst**

This field provides an indication of the RPMB LU life time based on the amount of performed program/erase cycles of the RPMB LU. Note that whenever the RPMB purge operation is executed, multiple program/erase cycles may be performed depending on the fragmentation of the valid RPMB data scattered in the RPMB LU. The calculation method is vendor specific.

- 00h : Information not available
- 01h : 0% - 10% device life time used
- 02h : 10% - 20% device life time used
- 03h : 20% - 30% device life time used
- 04h : 30% - 40% device life time used
- 05h : 40% - 50% device life time used
- 06h : 50% - 60% device life time used
- 07h : 60% - 70% device life time used
- 08h : 70% - 80% device life time used
- 09h : 80% - 90% device life time used
- 0Ah : 90% - 100% device life time used
- 0Bh : Exceeded its maximum estimated device life time
- Others: Reserved

# JEDEC Standard No. 220G
Page 287

## 12.4.3.2 Algorithm and Key for MAC Calculation

The message authentication code (MAC) is calculated using HMAC SHA-256 as defined in [HMAC-SHA]. The HMAC SHA-256 calculation takes as input a key and a message. The resulting MAC is 256 bits (32 bytes), which are embedded in the data frame as part of the request or response.

The key used for the MAC calculation is always the 256-bit Authentication Key stored in the target RPMB region. The message used as input to the MAC calculation is the concatenation of the fields in the RPMB packet.

## 12.4.3.3 MAC Calculation for Advanced RPMB

The key used for the MAC calculation is the 256-bit Authentication Key stored in the device.

If RPMB Message includes data in a DATA IN UPIU or a DATA OUT UPIU, the concatenation of the data transferred in each DATA IN/OUT UPIU in the order in which it is sent is input into the MAC calculation. Then the concatenation of the fields in the Advanced RPMB Meta Information from byte 0 to byte 27 is input into the MAC calculation. After this, four 00h bytes are input into the MAC calculation.

# JEDEC Standard No. 220G
Page 288

## 12.4.3.4 RPMB Message Components

Each RPMB message includes specific components. These components are displayed in Table 12.7.

### Table 12.7 — RPMB Message Components

| Component Name | Length | Request | Response | Description |
|---|---|---|---|---|
| Request Message Type | 2 bytes | Yes | No | This component indicates the request message type. See 12.4.3.5. |
| Response Message Type | 2 bytes | No | Yes | This component indicates the response message type. See 12.4.3.6. |
| Authentication Key | 32 bytes | Yes | No | This component is used only when programming the Authentication Key. |
| MAC | 32 bytes | Yes | Yes | Message Authentication Code |
| Result | 2 bytes | No | Yes | This component provides the operation result. See 12.4.3.7. |
| Write Counter | 4 bytes | Yes | Yes | Total amount of successful authenticated data write operations. |
| Address | 2 bytes | Yes | Yes | Logical block address of data to be programmed to or read from the RPMB region. |
| Nonce | 16 bytes | Yes | Yes | Random number generated by the host for the requests and copied to response by the RPMB engine. |
| Data | 256 bytes | Yes | Yes | Data to be written or read by signed access. |
| Advanced RPMB Data | 4096 bytes | Yes | Yes | Data to be written or read by signed access in Advanced RPMB operation. |
| Block Count | 2 bytes | Yes | Yes | Number of 256-byte logical blocks requested to be read or programmed. |
| Advanced RPMB Block Count | 2 bytes | Yes | Yes | Number of 4Kbytes (Advanced RPMB data) requested to be read or programmed. |

# JEDEC Standard No. 220G
Page 289

## 12.4.3.5 Request Message Types

The host sends messages to the device to initiate RPMB operations.

Table 12.8 lists RPMB's Request Message Types and their codes.

### Table 12.8— Request Message Types

| Code | Request Message Types |
|------|----------------------|
| 0001h | Authentication Key programming request |
| 0002h | Write Counter read request |
| 0003h | Authenticated data write request |
| 0004h | Authenticated data read request |
| 0005h | Result read request (Normal RPMB Mode only) |
| 0006h | Secure Write Protect Configuration Block write request |
| 0007h | Secure Write Protect Configuration Block read request |
| 0008h | RPMB Purge Enable Request |
| 0009h | RPMB Purge Status Read Request |
| 0010h | Authenticated Vendor Specific Command Request |
| 0011h | Authenticated Vendor Specific Command Status Read Request |
| Others | Reserved |

# JEDEC Standard No. 220G
Page 290

## 12.4.3.6 Response Message Types

The device responds with messages to the host during RPMB operations.

Table 12.9 lists RPMB's Response Message Types and their codes.

### Table 12.9 — Response Message Types

| Code | Response Message Types |
|------|------------------------|
| 0100h | Authentication Key programming response |
| 0200h | Write Counter read response |
| 0300h | Authenticated data write response |
| 0400h | Authenticated data read response |
| 0500h | Reserved |
| 0600h | Secure Write Protect Configuration Block write response |
| 0700h | Secure Write Protect Configuration Block read response |
| 0800h | RPMB Purge Enable Response |
| 0900h | RPMB Purge Status Read Response |
| 1000h | Authenticated Vendor Specific Command Response (Advanced RPMB Mode only) |
| 1100h | Authenticated Vendor Specific Command Status Response |
| Others | Reserved |