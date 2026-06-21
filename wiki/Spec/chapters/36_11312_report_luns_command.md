# 11.3.12 REPORT LUNS Command

The REPORT LUNS command requests that the peripheral device logical unit inventory be sent to the Application Client.

• The logical unit inventory is a list that shall include the logical unit numbers of all logical units accessible to a UFS Application Client

• If a REPORT LUNS command is received with a pending unit attention condition (i.e., before the device server reports CHECK CONDITION status), the device server shall perform the REPORT LUNS command

The Command CDB shall be sent in a single COMMAND UPIU

## Table 11.19 — REPORT LUNS Command

| Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|---|---|---|---|---|---|---|---|
| 0 | | | OPERATION CODE (A0h) | | | | | |
| 1 | | | Reserved | | | | | |
| 2 | | | SELECT REPORT | | | | | |
| 3 | (MSB) | | | | | | | |
| 5 | | | Reserved | | | | | (LSB) |
| 6 | (MSB) | | | | | | | |
| 9 | | | ALLOCATION LENGTH | | | | | (LSB) |
| 10 | | | Reserved | | | | | |
| 11 | | | CONTROL = 00h | | | | | |

# 11.3.12.1 Report LUNS Command Parameters

## Table 11.20 — Report LUNS Command Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 2 | 7:0 | **SELECT REPORT**: Specifies the type of logical unit addresses that shall be reported. The report types available are listed in the Table 11.21. UFS will support all report types. |
| 6:9 | 7:0 | **ALLOCATION LENGTH**: Specifies the maximum number of bytes of buffer space that the Application Client has allocated for data reception. |

## 11.3.12.2 Report LUNS Command Select Report Field Values

### Table 11.21 — SELECT REPORT Field

| CODE | DESCRIPTION |
|------|-------------|
| 00h | The list shall contain all accessible logical units using the single level LUN structure using the peripheral device addressing method, if any. If there are no logical units, the LUN LIST LENGTH field shall be zero. |
| 01h | The list shall contain all accessible well known logical units, if any using the well known logical unit extended addressing format. If there are no well known logical units, the LUN LIST LENGTH field shall be zero. |
| 02h | The list shall contain all accessible logical units using their respective addressing format. |
| 03h-FFh | Reserved |

**NOTE** The well known logical units are not included in the list when the SELECT REPORT field is set to zero.

## 11.3.12.3 Report LUNS Data Response

• Data returned from a REPORT LUNS command will be transferred to the Application Client in a one or more DATA IN UPIU's

• Most likely one DATA IN UPIU

• The Device Server will transfer less than or equal to Allocation Length data bytes to the Application Client.

• Less if Device Server has less total data than requested

• Data will be returned in the indicated Parameter Data Format described in the following.

• Each reportable logical unit will produce 8 bytes of data.

---
*JEDEC Standard No. 220G*  
*Page 207*

# 11.3.12.4 Report LUNS Parameter Data Format

## Table 11.22 — Report LUNS Parameter Data Format

| Byte | Description |
|------|-------------|
| 0:3 | **LUN LIST LENGTH:** Length = N – 7. This field shall contain the length in bytes of the LUN list that is available to be transferred. The LUN list length is the number of logical unit numbers in the logical unit inventory multiplied by eight. |
| 4:7 | **RESERVED:** 00000000h |
| 8:15 | **FIRST LUN RECORD:** 8 byte record that contains the first LUN |
| … | … next LUN record … |
| N-7:N | **LAST LUN RECORD:** 8 byte record that contains the last LUN |

• Total List Length = LUN LIST LENGTH + 8 (i.e., 8*number of LUN's + 8)

• Each LUN record is 8 bytes in length

• UFS uses two formats:
  ○ The single level LUN structure using peripheral device addressing method
  ○ The well known logical unit extended addressing format

## 11.3.12.5 Report LUNS LUN Addressing Formats

### Table 11.23 — Single Level LUN Structure Using Peripheral Device Addressing Method

#### Peripheral Device Addressing Method

| Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|---|---|---|---|---|---|---|---|
| 0 | | 00b | | | 000000b | | | |
| 1 | | | LUN | | | | | |
| 2 | | | | | | | | |
| 3 | | | NULL (0000h) | | | | | |
| 4 | | | | | | | | |
| 5 | | | NULL (0000h) | | | | | |
| 6 | | | | | | | | |
| 7 | | | NULL (0000h) | | | | | |

• Format used for standard Logical Unit addressing

• LUN = Logical Unit Number
  ○ For UFS: 00h ≤ LUN ≤ 7Fh
  
  **NOTE** The expected value is the SCSI LUN and not the LUN field in UPIU.

# JEDEC Standard No. 220G
Page 209

## 11.3.12.5 Report LUNS LUN Addressing Formats (cont'd)

### Table 11.24 — Well Known Logical Unit Extended Addressing Format

**Well Known Logical Unit Extended Addressing Format**

| Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|---|---|---|---|---|---|---|---|
| 0 | 11b | | 00b | | | 0001b | |
| 1 | | | | W-LUN | | | | |
| 2 | | | | | | | | |
| 3 | | | NULL (0000h) | | | | |
| 4 | | | | | | | | |
| 5 | | | NULL (0000h) | | | | |
| 6 | | | | | | | | |
| 7 | | | NULL (0000h) | | | | |

• Format used for well known logical unit addressing

• W-LUN = Well Known Logical Unit Number
  ○ For UFS: 00h ≤ W-LUN ≤ 7Fh
  
  NOTE The expected value is the SCSI LUN and not the LUN field in UPIU.

## 11.3.12.6 Report LUNS Status Response

• Status response will be sent in a single RESPONSE UPIU

• If all requested data is successfully read and transferred, the REPORT LUNS command will terminate with a STATUS response of GOOD

• The REPORT LUNS command will succeed when a pending UNIT ATTENTION condition exists

• Failure can occur for very few reasons, mainly for illegal values in the CDB. When the REPORT LUNS command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as
  ○ ILLEGAL REQUEST (CDB errors)

# 11.3.12.7 UFS LUN Format

**Table 11.25 — Format of LUN field in UPIU**

| 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|---|---|---|---|---|---|---|---|
| WLUN_ID | | | | UNIT_NUMBER_ID | | | |

The UFS 8-bit LUN field in UPIU supports two types of LUN addressing:

• If WLUN_ID bit = '0' then the UNIT_NUMBER_ID field addresses a standard logical unit (LUN)

• If WLUN_ID bit = '1' then the UNIT_NUMBER_ID field addresses a well known logical unit (W-LUN)

Up to 128 LUN's and up to 128 W-LUN's

• 0 ≤ UNIT_NUMBER_ID ≤ 127

The following table defines the logical unit number for UFS well known logical units (WLUN_ID bit set to '1')

**Table 11.26 — Well Known Logical Unit Numbers**

| Well known logical unit | WLUN_ID | UNIT_NUMBER_ID | LUN Field in UPIU |
|------------------------|---------|----------------|-------------------|
| REPORT LUNS | 1b | 01h | 81h |
| UFS Device | 1b | 50h | D0h |
| RPMB | 1b | 44h | C4h |
| BOOT | 1b | 30h | B0h |

---
JEDEC Standard No. 220G  
Page 210