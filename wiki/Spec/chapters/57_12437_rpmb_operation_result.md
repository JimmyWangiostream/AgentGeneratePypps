# JEDEC Standard No. 220G
## Page 291

### 12.4.3.7 RPMB Operation Result

• Result component of an RPMB message is composed of two bytes. The most significant byte is reserved and shall be set to zero.

• Bit 7 of Result field shall indicate if the write counter has expired (i.e., reached its maximum value) or not
  ○ Value of one will represent an expired write counter
  ○ Value of zero will represent a valid write counter

• The other bits shall indicate the operation status
  ○ Operation Okay (00h)
    ▪ General Failure (01h)
  ○ Authentication Failure (02h)
    ▪ MAC comparison not matching, MAC calculation failure
  ○ Counter Failure (03h)
    ▪ Counters not matching in comparison, counter incrementing failure
  ○ Address Failure (04h)
    ▪ Address out of range, wrong address alignment
  ○ Write Failure (05h)
    ▪ Data, Counter or Result write failure
  ○ Read Failure (06h)
    ▪ Data, Counter or Result read failure
  ○ Authentication key not yet programmed (07h)
    ▪ This value is the only valid result until the Authentication Key has been programmed in the target RPMB region, after which it can never occur again
  ○ Secure Write Protect Configuration Block access failure (08h).
    ▪ Secure Write Protect Configuration read or write failure.
  ○ Invalid Secure Write Protect Block Configuration parameter (09h).
    ▪ Invalid LUN (or logical unit not enabled), DATA LENGTH, LOGICAL BLOCK ADDRESS, NUMBER OF LOGICAL BLOCKS, or overlapped areas.
  ○ Secure Write Protection not applicable (0Ah).
    ▪ Logical unit configured with other write protection modes (permanent or power-on)
  ○ Unrecognized/Unsupported Request Type (0Bh)
    ▪ Request type unrecognized or unsupported
  ○ Rejected, RPMB purge operation in progress (0Ch)
    ▪ While an RPMB Purge is in progress, authenticated Read or Write is rejected.

#### Table 12.10 — Result Data Structure

| Bit[15:8] | Bit[7] | Bit[6:0] |
|-----------|--------|----------|
| Reserved | Write Counter Status | Operation Status |

# JEDEC Standard No. 220G
## Page 292

### 12.4.3.7 RPMB Operation Result (cont'd)

#### Table 12.11 — Result Code Definition

| Code | Description |
|------|-------------|
| 0000h (0080h) | Operation OK |
| 0001h (0081h) | General failure |
| 0002h (0082h) | Authentication failure<br>• MAC comparison not matching, MAC calculation failure |
| 0003h (0083h) | Counter failure<br>• Counters not matching in comparison, counter incrementing failure |
| 0004h (0084h) | Address failure<br>• Address out of range, wrong address alignment |
| 0005h (0085h) | Write failure<br>• Data / Counter / Result write failure |
| 0006h (0086h) | Read failure<br>• Data / Counter / Result read failure |
| 0007h | Authentication Key not yet programmed.<br>• This value is the only valid Result value until the Authentication Key has been programmed. Once the key is programmed, this value will no longer be used. |
| 0008h (0088h) | Secure Write Protect Configuration Block access failure<br>• Secure Write Protect Configuration read or write failure |
| 0009h (0089h) | Invalid Secure Write Protect Block Configuration parameter<br>• Invalid LUN or logical unit not enabled, DATA LENGTH, LOGICAL BLOCK ADDRESS, NUMBER OF LOGICAL BLOCKS, or overlapped areas |
| 000Ah (008Ah) | Secure Write Protection not applicable<br>• Logical unit configured with other write protection modes (permanent or power-on) |
| 000Bh (008Bh) | Unrecognized/Unsupported Request Type<br>• Request type unrecognized or unsupported |
| 000Ch (008Ch) | Rejected, RPMB purge operation in progress<br>• While an RPMB Purge is in progress, authenticated Read or Write is rejected. |

**NOTE** The values in parenthesis are valid when Write Counter has expired.

# 12.4.4 Implementation in Normal RPMB Mode

## 12.4.4.1 RPMB Message

An RPMB Message may be composed of one or more RPMB Message Data Frames.

RPMB Message Data Frame size is 512 bytes and it is organized as shown in Table 12.12.

**Table 12.12 — RPMB Message Data Frame**

| Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-----|---|---|---|---|---|---|---|---|
| **Byte** | | | | | | | | |
| 0 | (MSB) | | | | | | | |
| | | Stuff Bytes | | | | | | |
| 195 | | | | | | | | (LSB) |
| 196 | (MSB) | | | | | | | |
| | | Key / MAC | | | | | | |
| 227 | | | | | | | | (LSB) |
| 228 | | Data [255] | | | | | | |
| 483 | | Data [0] | | | | | | |
| 484 | (MSB) | | | | | | | |
| | | Nonce | | | | | | |
| 499 | | | | | | | | (LSB) |
| 500 | (MSB) | | | | | | | |
| | | Write Counter | | | | | | |
| 503 | | | | | | | | (LSB) |
| 504 | (MSB) | | | | | | | |
| | | Address | | | | | | |
| 505 | | | | | | | | (LSB) |
| 506 | (MSB) | | | | | | | |
| | | Block Count | | | | | | |
| 507 | | | | | | | | (LSB) |
| 508 | (MSB) | | | | | | | |
| | | Result | | | | | | |
| 509 | | | | | | | | (LSB) |
| 510 | (MSB) | | | | | | | |
| | | Request Message Type / Response Message Type | | | | | | | |
| 511 | | | | | | | | (LSB) |

---
JEDEC Standard No. 220G  
Page 293