# 10.7.10 REJECT UPIU

All UPIU packets include the basic header segment and some transaction specific fields. In addition to them, UPIU packets may have: Data Segment, Extra Header Segment, Header E2ECRC, Data E2ECRC.

The purpose of the REJECT UPIU is to simplify the software development and the system debug.

## Table 10.58 — Reject UPIU

| **Reject UPIU** |  |  |  |
|---|---|---|---|
| 0 | 1 | 2 | 3 |
| xx11 1111b | Flags | LUN | Task Tag |
| 4 | 5 | 6 | 7 |
| IID | Reserved | EXT_IID | Reserved | Response (01h) | Reserved |
| 8 | 9 | 10 | 11 |
| Total EHS Length (00h) | Device Information (00h) | (MSB) | (LSB) |
| | | Data Segment Length (0000h) |  |
| 12 | 13 | 14 | 15 |
| Basic Header Status | Reserved | E2E Status | Reserved |
| 16 | 17 | 18 | 19 |
| | | Reserved |  |
| 20 | 21 | 22 | 23 |
| | | Reserved |  |
| 24 | 25 | 26 | 27 |
| | | Reserved |  |
| 28 | 29 | 30 | 31 |
| | | Reserved |  |
| Header E2ECRC (omit if HD=0) |  |  |  |

The device shall send a REJECT UPIU if it receives a UPIU with an invalid Transaction Type.

The Transaction Type is defined in 10.6.2a, Basic Header Format, and it is composed by the following fields: HD bit, DD bit and the Transaction Code.

Since this version of the standard does not support end-to-end CRC for header and data segments, a Transaction Type value is valid if:
• HD bit and DD bit are set to zero.
• the Transaction Code identifies one of the defined UPIU transactions from the Initiator device to Target device, see Table 10.1, UPIU Transaction Codes, (reserved values excluded).

The device shall not respond with a REJECT UPIU in the following cases:
• Incorrect LUN field or Command Set Type field in a COMMAND UPIU: the device shall send a RESPONSE UPIU. In particular, in case of an incorrect Command Set Type field value, the Data Segment Area of the RESPONSE UPIU shall be empty (Data Segment Length shall be equal to zero).
• Incorrect LUN field or Task Management Function field in TASK MANAGEMENT REQUEST UPIU: the device shall send a TASK MANAGEMENT RESPONSE UPIU.
• Incorrect Query Function field in QUERY REQUEST UPIU: the device shall send a QUERY RESPONSE UPIU

---

JEDEC Standard No. 220G  
Page 144

# 10.7.10.1 Basic Header

The first 12 bytes of the Reject UPIU contain the Basic Header as described in 10.6.2, Basic Header Format. Specific details are as follows:

## a) Transaction Type

A type code value of xx11 1111b indicates a Reject UPIU.

## b) Flags

The Flags field value shall be equal to zero.

## c) LUN

The LUN shall be equal to the LUN value of the rejected UPIU.

## d) Task Tag

The Task Tag shall be equal to the Task Tag value of the rejected UPIU.

## e) IID

This field is the LSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2 for details.

The IID shall be equal to the IID value of the rejected UPIU.

## f) EXT_IID

This field is the MSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2 for details.

The EXT_IID shall be equal to the EXT_IID value of the rejected UPIU.

## g) Response

The Response field shall be set to 01h (Target Failure) indicating that the Target device was not able to execute the requested operation.

## h) Data Segment Length

The Data Segment Length field shall contain zero as there is no Data Segment in this UPIU.

---

JEDEC Standard No. 220G  
Page 145

# JEDEC Standard No. 220G
Page 146

## 10.7.10.1 Basic Header (cont'd)

### i) Basic Header Status

The Basic Header Status field provides information about error detected in the UPIU received by the Initiator device.

Table 10.59 defines the possible values for the Basic Header Status field.

**Table 10.59 — Basic Header Status Description**

| Value | Name |
|-------|------|
| 00h | Reserved |
| 01h | Invalid Transaction Type |
| 02h to FFh | Reserved |

### j) E2E Status

The E2E Status field provides the result of the end-to-end CRC of the rejected UPIU for both Header and Data. E2E Status is reserved if end-to-end CRC is not supported.

**Table 10.60 — E2E Status Definition**

| Bit | Description |
|-----|-------------|
| Bit 0 | 0: Header E2ECRC validated or not supported<br>1: Header E2ECRC error |
| Bit 1 | 0: Data E2ECRC validated or not supported<br>1: Data E2ECRC error |
| Others | Reserved |