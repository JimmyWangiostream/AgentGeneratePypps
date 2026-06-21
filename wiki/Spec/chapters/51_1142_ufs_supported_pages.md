# 11.4.2 UFS Supported Pages

Table 11.66 shows the mode pages supported by UFS device. This standard does not define any additional subpages.

## Table 11.66 — UFS Supported Pages

| PAGE NAME | PAGE CODE | SUBPAGE CODE | DESCRIPTION |
|-----------|-----------|--------------|-------------|
| CONTROL | 0Ah | 00h | Return CONTROL mode page |
| READ-WRITE ERROR RECOVERY | 01h | 00h | Return READ-WRITE ERROR RECOVERY mode page |
| CACHING | 08h | 00h | Return CACHING mode page |
| ALL PAGES | 3Fh | 00h | Return all mode pages (not including subpages) |
| ALL SUBPAGES | 3Fh | FFh | Return all mode pages and subpages |

If the device has more than one logical unit, host should read Mode Page Policy VPD in order to know whether the logical unit maintains its own copy of the mode page and subpage or all logical units share the mode page and subpage.

# 11.4.2.1 Control Mode Page

The Control mode page provides controls over SCSI features that are applicable to all device types (e.g., task set management and error logging).

Table 11.67 defines the Control mode page default value (PC = 10b).

## Table 11.67 — Control Mode Page Default Value

| Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-----|---|---|---|---|---|---|---|---|
| **Byte** | | | | | | | | |
| 0 | PS | SPF (0) | | | PAGE CODE (0Ah) | | | |
| 1 | | | PAGE LENGTH (0Ah) | | | | | |
| 2 | | TST = 00b | TMF_ONLY = 0b | DPICZ = 0b | D_SENSE = 0b | GLTSD = 0b | RLEC = 0b |
| 3 | QUEUE ALGORITHM MODIFIER = 0001b | | NUAR = 0b | | QERR = 00b | | Obsolete = 0b |
| 4 | VS = 0b | RAC = 0b | UA_INTLCK_CTRL = 00b | SWP = 0b | | Obsolete = 000b | |
| 5 | ATO = 0b | TAS = 0b | ATMPE = 0b | RWWP = 0b | Reserved = 0b | AUTOLOAD MODE = 000b | |
| 6 | | | | | Obsolete = 0000h | | | |
| 7 | | | | | | | | |
| 8 | (MSB) | | | | | | | |
| 9 | | | BUSY TIMEOUT PERIOD | | | | | (LSB) |
| 10 | (MSB) | | | | | | | |
| 11 | | | EXTENDED SELF-TEST COMPLETION TIME | | | | | (LSB) |

**NOTE 1** Default values for PS bit, BUSY TIMEOUT PERIOD field and EXTENDED SELF-TEST COMPLETION TIME field are device specific.

The following Control mode page field shall be changeable: SWP. The following Control mode page fields are not changeable: TST and BUSY TIMEOUT PERIOD. Other fields may or may not be changeable, refer to the vendor datasheet for details.

---

JEDEC Standard No. 220G  
Page 259

# 11.4.2.1.1 Control Mode Page Parameters

## Table 11.68 — Control Mode Page Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 1 | 7:5 | **TST**: Indicates Task Set Type.<br>000b indicates the logical unit maintains one task set for all I_T nexuses.<br>Others: reserved. |
| 4 | 3:3 | **SWP**: A software write protect (SWP) bit set to one specifies that the logical unit shall inhibit writing to the medium after writing all cached or buffered write data, if any. When SWP is one, all commands requiring writes to the medium shall be terminated with CHECK CONDITION status, with the sense key set to DATA PROTECT |
| 8:9 | 7:0 | **BUSY TIMEOUT PERIOD**: The BUSY TIMEOUT PERIOD field specifies the maximum time, in 100 milliseconds increments, that the application client allows for the device server to return BUSY status for commands from the application client. A 0000h value in this field is undefined. An FFFFh value in this field is defined as an unlimited period. |

**NOTE 1** In addition to the software write protection, logical units may be configured as permanently write protected or power on write protected. A logical unit is writeable if all types of write protection are disabled. Logical units may be write protected setting SWP to one or using one of the methods described in 12.3, Device Data Protection.

---

*JEDEC Standard No. 220G*  
*Page 260*

# 11.4.2.2 Read-Write Error Recovery Mode Page

The Read-Write Error Recovery mode page specifies the error recovery parameters the device server shall use during any command that performs a read or write operation to the medium (e.g., READ command, WRITE command, or VERIFY command).

Table 11.69 defines the Read-Write Error Recovery mode page default value (PC = 10b).

## Table 11.69 — Read-Write Error Recovery Mode Page Default Value

| Bit<br>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|---|---|---|---|---|---|---|---|---|
| 0 | PS | SPF<br>(0b) | | | PAGE CODE (01h) | | | |
| 1 | | | | | PAGE LENGTH (0Ah) | | | |
| 2 | AWRE<br>= 1b | ARRE<br>= 0b | TB<br>= 0b | RC<br>= 0b | EER<br>= 0b | PER<br>= 0b | DTE<br>= 0b | DCR<br>= 0b |
| 3 | | | | | READ RETRY COUNT | | | |
| 4 | | | | | Obsolete = 00h | | | |
| 5 | | | | | Obsolete = 00h | | | |
| 6 | | | | | Obsolete = 00h | | | |
| 7 | TPERE<br>= 0b | | | Reserved = 00000b | | | Restricted for MMC-6<br>= 00b | |
| 8 | | | | | WRITE RETRY COUNT | | | |
| 9 | | | | | Reserved = 00h | | | |
| 10 | (MSB) | | | | | | | |
| | | | | RECOVERY TIME LIMIT | | | | |
| 11 | | | | | | | | (LSB) |

NOTE 1 Default values for PS field, READ RETRY COUNT field, WRITE RETRY COUNT field and RECOVERY TIME LIMIT are device specific.

This standard does not define which Read-Write Error Recovery mode page fields are changeable, refer to vendor datasheet for details.

---

*JEDEC Standard No. 220G*  
*Page 261*

# JEDEC Standard No. 220G
## Page 262

### 11.4.2.2.1 Read-Write Error Recovery Parameters

#### Table 11.70 — Read-Write Error Recovery Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 3 | 7:0 | **READ RETRY COUNT**: The READ RETRY COUNT field specifies the number of times that the device server shall attempt its recovery algorithm during read operations. |
| 8 | 7:0 | **WRITE RETRY COUNT**: The WRITE RETRY COUNT field specifies the number of times that the device server shall attempt its recovery algorithm during write operations. |
| 10:11 | 7:0 | **RECOVERY TIME LIMIT**: The RECOVERY TIME LIMIT field specifies in milliseconds the maximum time duration that the device server shall use for data error recovery procedures. When both a retry count and a recovery time limit are specified, the field that specifies the recovery action of least duration shall have priority. |

# 11.4.2.3 Caching Mode Page

The Caching mode page defines the parameters that affect the use of the cache. A UFS device shall implement support for following parameters.

Table 11.71 defines the Caching mode page default value (PC = 10b).

## Table 11.71 — Caching Mode Page Default Value

| Byte | Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
|------|-------|-------|-------|-------|-------|-------|-------|-------|
| 0 | PS | SPF (0b) | | | PAGE CODE (08h) | | | |
| 1 | | | PAGE LENGTH (12h) | | | | | |
| 2 | IC = 0b | ABPF = 0b | CAP = 0b | DISC = 0b | SIZE = 0b | WCE =1b | MF = 0b | RCD =0b |
| 3 | DEMAND READ RETENTION PRIORITY = 0000b | | | WRITE RETENTION PRIORITY = 0000b | | | |
| 4 | (MSB) | | DISABLE PRE-FETCH TRANSFER LENGTH = 0000h | | | | (LSB) |
| 5 | | | | | | | | |
| 6 | (MSB) | | MINIMUM PRE-FETCH = 0000h | | | | (LSB) |
| 7 | | | | | | | | |
| 8 | (MSB) | | MAXIMUM PRE-FETCH = 0000h | | | | (LSB) |
| 9 | | | | | | | | |
| 10 | (MSB) | | MAXIMUM PRE-FETCH CEILING = 0000h | | | | (LSB) |
| 11 | | | | | | | | |
| 12 | FSW = 0b | LBCSS = 0b | DRA = 0b | Vendor Specific = 00b | | Reserved = 00b | | NV_DIS = 0b |
| 13 | | | NUMBER OF CACHE SEGMENTS = 00h | | | | | |
| 14 | (MSB) | | CACHE SEGMENT SIZE = 0000h | | | | (LSB) |
| 15 | | | | | | | | |
| 16 | | | Reserved = 00h | | | | | |
| 17 | | | | | | | | |
| 18 | | | Obsolete = 0000000h | | | | | |
| 19 | | | | | | | | |

The following Caching mode page fields shall be changeable: WCE and RCD. Other fields may or may not be changeable, refer to the vendor datasheet for details.

---

*JEDEC Standard No. 220G*  
*Page 263*

# 11.4.2.3.1 Caching Mode Page Parameters

## Table 11.72 — Caching Mode Page Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 2 | 2:2 | **WCE: WRITE BACK CACHE ENABLE.** A writeback cache enable bit set to zero specifies that the device server shall complete a WRITE command with GOOD status only after writing all of the data to the medium without error. A WCE bit set to one specifies that the device server may complete a WRITE command with GOOD status after receiving the data without error and prior to having written the data to the medium. |
| 2 | 0:0 | **RCD: READ CACHE DISABLE.** A read cache disable bit set to zero specifies that the device server may return data requested by a READ command by accessing either the cache or medium. A RCD bit set to one specifies that the device server shall transfer all of the data requested by a READ command from the medium (i.e., data shall not be transferred from the cache). |

**NOTE 1** Fields that are not supported by UFS should be set to zero, and are documented assigning a value of zero to them (e.g., PS=0b). The device may ignore values in fields that are not supported by UFS.

---

*JEDEC Standard No. 220G*  
*Page 264*

# 11.5 Vital Product Data Parameters

## 11.5.1 Overview

The vital product data (VPD) pages are returned by an INQUIRY command with the EVPD bit set to one and contain vendor specific product information about a logical unit and SCSI target device.

A UFS device shall support the following VPD pages:

• Supported VPD Pages
• Mode Page Policy;

Support for other VPD pages is optional.

## 11.5.2 VPD Page Format

Table 11.73 shows the VPD page structure.

**Table 11.73 — VPD Page Format**

| Bit<br/>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|--------------|---|---|---|---|---|---|---|---|
| 0 | PERIPHERAL QUALIFIER | | | | PERIPHERAL DEVICE TYPE | | | |
| 1 | | | | PAGE CODE | | | | |
| 2 | (MSB) | | | | | | | |
| 3 | | | PAGE LENGTH (n-3) | | | | | (LSB) |
| 4 | (MSB) | | | | | | | |
| n | | | VPD parameters | | | | | (LSB) |

The PERIPHERAL QUALIFIER field and the PERIPHERAL DEVICE TYPE field are the same as defined for standard INQUIRY data (see 11.3.2.2).

The PAGE CODE field identifies the VPD page and contains the same value as in the PAGE CODE field in the INQUIRY CDB (see 11.3.2).

The PAGE LENGTH field indicates the length in bytes of the VPD parameters that follow this field. See [SPC] for further details.

---

*JEDEC Standard No. 220G*
*Page 265*

# JEDEC Standard No. 220G
## Page 266

### 11.5.3 Supported VPD Pages VPD Page

The Supported VPD Pages VPD page contains a list of the VPD page codes supported by the logical unit (see Table 11.74).

#### Table 11.74—Supported VPD Pages VPD Page

| Bit<br>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-------------|---|---|---|---|---|---|---|---|
| 0 | PERIPHERAL QUALIFIER | | | | PERIPHERAL DEVICE TYPE | | | |
| 1 | | | | PAGE CODE (00h) | | | | |
| 2 | (MSB) | | | | | | | |
| | | | PAGE LENGTH (n-3) | | | | | |
| 3 | | | | | | | | (LSB) |
| 4 | | | | | | | | |
| ⋮ | | | Supported VPD page list | | | | | |
| n | | | | | | | | |

The supported VPD page list shall contain a list of all VPD page codes implemented by the logical unit in ascending order beginning with page code 00h.