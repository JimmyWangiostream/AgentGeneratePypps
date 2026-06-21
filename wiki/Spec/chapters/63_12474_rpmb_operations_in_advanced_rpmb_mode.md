# 12.4.7.4 RPMB Operations in Advanced RPMB Mode

In Advanced RPMB, EHS shall be used. Therefore, "Total EHS Length" shall be "2h", "bLength" and "bEHSType" in "EHS Entry" shall be respectively "02h" and "01h". Otherwise, the command shall be terminated with CHECK CONDITION status. See 12.4.5.1 for the details of error handling.

## 12.4.7.4.1 Authentication Key Programming

• The Authentication Key programming is initiated by a SECURITY PROTOCOL OUT command.
  ○ An initiator sends the SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame includes the Request Message Type = 0001h and the Authentication Key.
  
  ○ If "Transfer Length" is not "0h", then the command shall be terminated with CHECK CONDITION status. See 12.4.5.1 for the details of error handling.
  
  ○ The device returns GOOD status in status response when Authentication Key programming is completed.
  
  ○ If programming of Authentication Key failed then returned result is "Write failure" (0005h). If some other error occurred during Authentication Key programming then returned result is "General failure" (0001h).

Access to RPMB data area is not possible before the Authentication Key is programmed in the corresponding RPMB region. The state of the device can be checked by trying to write/read data to/from the RPMB data area if the Authentication Key is not programmed then the Result field in the response message will be set to "Authentication Key not yet programmed" (0007h).

[THIS IS FIGURE: Figure 12.15 shows an Authentication Key Programming Flow diagram in Advanced RPMB Mode. The diagram displays communication between Host and Device, showing:

- COMMAND UPIU structure with fields for xx00.0001b, Flags, LUN, Task Tag
- IID, Command Set Type, Reserved, Reserved, EXT_IID Reserved
- Total EHS Length, Reserved, Data Segment Length sections
- Expected Data Transfer Length
- A detailed bit field structure showing OPERATION CODE, SECURITY PROTOCOL, SECURITY PROTOCOL SPECIFIC (Region Info), Reserved fields, and TRANSFER LENGTH = 0
- An EHS field section showing various parameters including Request Message Type (0001h), Nonce (0.00h), Write Counter (0...0h), Address/LUN (0000h), Block Count (0000h), Result (0000h), and MAC/Key with Header E2E CRC]

---

JEDEC Standard No. 220G  
Page 325

# JEDEC Standard No. 220G
Page 326

## 12.4.7.4.1 Authentication Key Programming (cont'd)

[DIAGRAM: Flow diagram showing communication between Host and Device with CMD UPIU Security Protocol Out (with EHS field) going from Host to Device, and Response UPIU (with EHS field) returning from Device to Host]

### RESPONSE UPIU

| 0 | 1 | 2 | 3 |
|---|---|---|---|
| xx10 0001b | Flags | LUN | Task Tag |
| 4 | 5 | 6 | 7 |
| HD | Command Set Type | EXT_IID Reserved: | Response |
| 8 | 9 | 10 | 11 |
| | | (MSB) | (LSB) |
| Total EHS length | Device Information | Data Segment Length |
| 12 | 13 | 14 | 15 |
| (MSB) | | | (LSB) |
| | Residual Transfer Count |
| 16 | 17 | 18 | 19 |
| | | Reserved |
| 20 | 21 | 22 | 23 |
| | | Reserved |
| 24 | 25 | 26 | 27 |
| | | Reserved |
| 28 | 29 | 30 | 31 |
| | | Reserved |

### EHS field(2)

| Field | Value | Description |
|-------|-------|-------------|
| 0~3 | | EHS Header |
| 4~5 | (Req./Resp. Message Type) | 010h |
| 6~21 | (Nonce) | 0..00h |
| 22~25 | (Write Counter) | 0..00h |
| 26~27 | (Address / LUN) | 0000h |
| 28~29 | (Block Count) | 0000h |
| 30~31 | (Result) | Result Code |
| 32~63 | (MAC / Key) | 0..00h |

### Header E2E CRC (omit if HD=0)

| K | (MSB) | K+1 | (LSB) | K+2 | K+3 |
|---|-------|-----|-------|-----|-----|
| | Sense Data Length | | Sense Data[0] | Sense Data[1] |

| K+16 | K+17 | K+18 | K+19 |
|------|------|------|------|
| Sense Data[14] | Sense Data[15] | Sense Data[16] | Sense Data[17] |

### Data E2E CRC (omit if DD=0)

**Note 1:** K=32 if HD=0 and EHS field is not included  
K=96 if HD=0 and EHS field is included

**Note 2:** EHS end shall not be sent when SFUDD command terminated with  
CHECK CONDITION status. In this case, the Total EHS length is 0h.

**Figure 12.15 - Authentication Key Programming Flow (in Advanced RPMB Mode) (cont'd)**

# JEDEC Standard No. 220G
Page 327

## 12.4.7.4.2 Read Counter Value

• The Read Counter Value sequence is initiated by a SECURITY PROTOCOL OUT IN command.
  ○ An initiator sends the SECURITY PROTOCOL OUT IN command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame includes the Request Message Type = 0002h and the Nonce.
  
  ○ If "Allocation Length" is not "0h", then the command shall be terminated with CHECK CONDITION status. See 12.4.5.1 for the details of error handling.
  
  ○ The device returns a RPMB data frame with Response Message Type = 0200h, a copy of the Nonce received in the request, the Write Counter value, the MAC and the Result.

If reading of the counter value fails then returned result is "Read failure" (0006h/0086h).

If some other error occurs then Result is "General failure" (0001h/0081h).

If counter has expired also bit 7 is set to 1 in returned results.

[THIS IS FIGURE: A detailed communication flow diagram showing the Read Counter Value process in Advanced RPMB Model. The diagram shows:

1. A command structure with fields for:
   - COMMAND UPIU (bytes 0-3 with Flags, LUN, Task Tag)
   - Additional fields (bytes 4-15) including Command Set Type, Reserved fields, Data Segment Length, and Expected Data Transfer Length

2. Communication flow between Host and Device showing:
   - CMD UPIU Security Protocol In (with EHS field)
   - Response UPIU (with EHS field)

3. Detailed bit layout (Bit 7-0) showing:
   - OPERATION CODE (A2h)
   - SECURITY PROTOCOL
   - SECURITY PROTOCOL SPECIFIC (Region Info)
   - Reserved fields
   - ALLOCATION LENGTH = 0
   - Reserved and CONTROL fields

4. EHS field structure (bytes 28-63) containing:
   - Header information
   - Request/Response Message Type (0002h)
   - Nonce from the host
   - Write Counter, Address/LUN, Block Count
   - Result and MAC/Key fields
   - Header EZECRC information]

**Figure 12.16— Read Counter Value Flow (in Advanced RPMB Model)**

# JEDEC Standard No. 220G
Page 328

## 12.47.42 Read Counter Value (cont'd)

[THIS IS FIGURE: A flow diagram showing communication between Host and Device. The Host sends "CMD UPIU Security Protocol In (with EHS field)" to the Device, and the Device responds with "Response UPIU (with EHS field)". Below this is a detailed packet structure table showing the RESPONSE_UPIU format.]

| RESPONSE_UPIU |  |  |  |
|---------------|--|--|--|
| 0 | 1 | 2 | 3 |
| x=10.0001b | | Flags | LUN | Task Tag |
| 4 | 5 | 6 | 7 |
| IID | Command Code Type | EXT_IID | Reserved | Response | Status |
| 8 | 9 | 10 | 11 |
| Total EHS length (MSB) | Device Information | (MSB) | Data Segment Length (LSB) |
| 12 | 13 | 14 | 15 |
| | | Residual Transfer Count | (LSB) |
| 16 | 17 | 18 | 19 |
| | | Reserved | |
| 20 | 21 | 22 | 23 |
| | | Reserved | |
| 24 | 25 | 26 | 27 |
| | | Reserved | |
| 28 | 29 | 30 | 31 |
| | | Reserved | |

**EHS field⁽²⁾**

| 0~3 | | EHS Header |
|-----|--|-----------|
| 4~5 | (Req./Resp. Message Type) | 0200h |
| 6~21 | (Nonce) | Copy of the Nonce |
| 22~25 | (Write Counter) | Counter Value |
| 26~27 | (Address / LUN) | 0000h |
| 28~29 | (Block Count) | 0000h |
| 30~31 | (Result) | Result Code |
| 32~63 | (MAC / Key) | MAC from the Device |

**Header E2ECBC (omit if HD=0)**
| K | (MSB) | K+1 | (LSB) | K+2 | K+3 |
|---|-------|-----|-------|-----|-----|
| | Sense Data Length | | Sense Data[0] | | Sense Data[1] |
| K+16 | K+17 | K+18 | K+19 |
| Sense Data[14] | Sense Data[15] | Sense Data[16] | Sense Data[17] |

**Data E2ECBC (omit if DD=0)**

**Notes:**
1. K=32 if HD=0 and EHS field is not included
   K=96 if HD=0 and EHS field is included
2. EHS field shall not be sent when SPSRQ command formulated with
   CHECK CONDITION status. In this case, the Total EHS length is 0h.

**Figure 12.16 — Read Counter Value Flow (in Advanced RPMB Mode) (cont'd)**

# JEDEC Standard No. 220G
Page 329

## 12.4.7.4.3 Authenticated Data Write

• The Authenticated Data Write sequence is initiated by a SECURITY PROTOCOL OUT command.
  ○ An initiator sends the SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB message is composed of Request Message Type = 0003h, Advanced RPMB Block Count, Address, Write Counter, Nonce, Data and MAC.

  ○ When the device receives the RPMB message, it first checks whether the write counter has expired. If the write counter is expired then the device sets the Result to "Write failure, write counter expired" (0005h). No data is written to the RPMB data area.

  ○ Next the address is checked. If the Address value is equal to or greater than the size of target RPMB region which is defined as bRPMBRegion0Size – bRPMBRegion3Size parameter value in the RPMB Unit Descriptor, then the Result is set to "Address failure" (0004h). No data is written to the RPMB data area.

  ○ If the Address value plus the Advanced RPMB Block Count value is greater than the size of target RPMB region which is defined as bRPMBRegion0Size – bRPMBRegion3Size parameter value, then the Result is set to "Address failure" (0004h). No data is written to the RPMB data area.

  ○ If the Advanced RPMB Block Count indicates a value greater than bRPMB_ReadWriteSize, then the authenticated data write operation fails and the Result is set to "General failure" (0001h).

  ○ If the write counter was not expired then the device calculates the MAC of request type, Advanced RPMB Block Count, write counter, address and data, and compares this with the MAC in the request. If the two MAC's are different, then the device sets the Result to "Authentication failure" (0002h). No data is written to the RPMB data area.

  ○ If the MAC in the request and calculated MAC are equal then the device compares the write counter in the request with the write counter stored in the device. If the two counters are different then the device sets the Result to "Counter failure" (0003h). No data is written to the RPMB data area.

  ○ If the MAC and write counter comparisons are successful then the write request is considered to be authenticated. The data is written to the address indicated in the request.

  ○ The write counter is incremented by one if the write operation is successfully executed.

  ○ If write fails then returned result is "Write failure" (0005h).

  ○ If some other error occurs during the write procedure then returned result is "General failure" (0001h).

  ○ In an authenticated data write request with Advanced RPMB Block Count greater than one
    ▪ the MAC is included in RESPONSE UPIU.
    ▪ When the authenticated data write operation is completed, the device may return GOOD status in response to the SECURITY PROTOCOL OUT command regardless of whether the Authenticated Data Write was successful or not.

• Device returns the RPMB data frame containing the Response Message Type = 0300h, the counter value (incremented if the write operation is successfully executed), a copy of the Nonce received in the request, the address received in the Authenticated data write request, the MAC and result of the authenticated data write operation.

# 12.4.7.4.3 Authenticated Data Write (cont'd)

[This is a detailed flow diagram showing the Authenticated Data Write process in Advanced RPMB Mode. The diagram shows communication between Host and Device with multiple UPIU (UFS Protocol Information Unit) exchanges.]

**Top Section - Command Phase:**

The diagram shows:
- Host sends CMD UPIU Security Protocol Out (with EHS field) to Device
- Device responds with Ready To Transfer UPIU
- Host sends DATA Out UPIU
- Device responds with Response UPIU (with EHS field)

**COMMAND UPIU Structure:**
```
Bit    7    6    5    4    3    2    1    0
Byte
0      xx00 000b           Flags        LUN        Task Tag
4      IID  Command        Reserved     Reserved   EXT_IID Reserved
       Set Type
8      Total EHS length (2N)  Reserved  (MSB)     (LSB)
       Data Segment Length (0000h)
12     (MSB)               (LSB)
       Expected Data Transfer Length
```

**OPERATION CODE Details:**
- Byte 0-1: OPERATION CODE (85h), SECURITY PROTOCOL
- Byte 2: SECURITY PROTOCOL SPECIFIC (Region Info)
- Byte 3-4: Reserved, Reserved  
- Byte 5: Reserved
- Byte 6: (MSB) ALLOCATION LENGTH
- Byte 9: (RPMB Data Size) (LSB)
- Byte 10: Reserved
- Byte 11: CONTROL = 00h

**EHS Header Structure:**
```
28    29    30    31
CDB[12]=00h  CDB[13]=00h  CDB[14]=00h  CDB[15]=00h
EHS Header
```

**EHS Field Details:**
- 0-3: (Req./Resp. Message Type) 0003h
- 4-5: (Nonce) Nonce from the host
- 6-21: (Write Counter) Current counter Value
- 22-25: (Address / LUN) Address
- 26-37: (Block Count) Advanced RPMB Block Count
- 38-293: (Result) 0000h
- 294-549: (MAC / Key) Mac from the host
- Header E2ECRC (omit if HD=0)

**Bottom Section - Data Phase:**

**DATA OUT UPIU Structure:**
```
0     1     2     3
xx00 001b   Flags   LUN   Task Tag
4     5     6     7
IID  Reserved  Reserved  Reserved  EXT_IID Reserved
8     9     10    11
Total EHS length (2N)  Reserved  (MSB)  (LSB)
      Data Segment Length
12    13    14    15
(MSB) (LSB)        (LSB)
      Data Buffer Offset
16    17    18    19
      Data Transfer Count
20    21    22    23
      Reserved
24    25    26    27
      Reserved  
28    29    30    31
      Reserved
```

**Header E2ECRC (omit if HD=0):**
```
K     K+1   K+2   K+3
Adv. RPMB Data[0]  Adv. RPMB Data[1]  Adv. RPMB Data[2]  Adv. RPMB Data[3]
K+Length-4  K+Length-3  K+Length-2  K+Length-1
```

**Note:** 
- Adv. RPMB DataLength=4J, Adv. RPMB DataLength=3J, Adv. RPMB DataLength=2J, Adv. RPMB DataLength=1J
- Data E2ECRC (omit if DD=0)
- Note: 1 ≤ J ≤ 2^8 if HD=0

**Figure 12.17 — Authenticated Data Write Flow (in Advanced RPMB Mode)**

# JEDEC Standard No. 220G
Page 331

## 12.4.7.4.3 Authenticated Data Write (cont'd)

[**Figure 12.17 — Authenticated Data Write Flow (in Advanced RPMB Mode) (cont'd)**

This is a sequence diagram showing communication between Host and Device with the following components:

**Left side - Message Flow:**
- CMD UPIU Security Protocol Out (with EHS field)
- LOOP: Ready To Transfer UPIU
- DATA Out UPIU  
- Response UPIU (with EHS field)

**Right side - RESPONSE UPIU packet structure:**
A detailed packet format table showing byte positions 0-31 with fields including:
- Flags, LUN, Task Tag
- IID, Command Set Type, EXT_IID, Reserved, Response, Status
- Total EHS Length, Device Information, Data Segment Length
- Residual Transfer Count
- Reserved sections

**Bottom section - EHS field details:**
Shows the Enhanced Header Segment structure with:
- EHS Header (0x0h)
- Request/Response Message Type, Device, Copy of Nonce
- Write Counter, New Counter Value, Address
- Block Count (0x00h), Result, Result Code
- MAC/Key, MAC from the device

**Additional technical details:**
- Header E2ECRC information
- Sense Data Length and Sense Data fields
- Various K+ values and data segments
- Multiple footnotes explaining field conditions and requirements]

**Notes:**
- Note 1: K=32 if HD=0 and EHS field is not included
- K=96 if HD=0 and EHS field is included  
- Note 2: EHS field shall not be sent when SPI SNO command terminated with CHECK CONDITION status. In this case, the Total EHS length is 0h.
- Note 3: The Write Counter is incremented only if the Enable operation was successfully completed.

# JEDEC Standard No. 220G
## Page 332

### 12.4.7.4.4 Authenticated Data Read

The Authenticated Data Read sequence is initiated by a SECURITY PROTOCOL IN command.

• An initiator sends the SECURITY PROTOCOL IN command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame includes the Request Message Type = 0004h, the nonce, the data address, and the Advanced RPMB Block Count.

  ○ When the device receives this request it first checks the address. If the Address value is equal to or greater than the size of target RPMB region which is defined as bRPMBRegion0Size – bRPMBRegion3Size parameter value in the RPMB Unit Descriptor, then Result is set to "Address failure" (0004h/0084h). The data read is not valid.

  ○ If the Address value plus the Advanced RPMB Block Count value is greater than the size of target RPMB region which is defined as bRPMBRegion0Size – bRPMBRegion3Size parameter value, then the Result is set to "Address failure" (0004h/0084h). No data is read from the RPMB data area.

  ○ If the Block Count indicates a value greater than bRPMB_ReadWriteSize, then the Authenticated Data Read operation fails and the Result is set to "General failure" (0001h).

  ○ After successful data fetch the MAC is calculated from response type, nonce, address, data and result. If the MAC calculation fails then returned result is "Authentication failure" (0002h/0082h).

  ○ In an authenticated data read response with Advanced RPMB Block Count greater than one,
    ▪ the MAC is included only in the RESPONSE UPIU
    ▪ When the authenticated data read operation is completed, the device may return GOOD status in response to the SECURITY PROTOCOL IN command regardless of whether the Authenticated Data Read was successful or not.

• If data fetch from addressed location inside device fails then returned result is "Read failure" (0006h/0086h). If some other error occurs during the read procedure then returned result is "General failure" (0001h/0081h).

# JEDEC Standard No. 220G
Page 333

## 12.4.7.4.4 Authenticated Data Read (cont'd)

[THIS IS FIGURE: Flow diagram showing communication between Host and Device with the following components:

**First Communication Flow:**
- Host sends "CMD UPIU Security Protocol In (with EHS field)" to Device
- Device sends "Data in UPIU" back to Host (in LOOP)
- Device sends "Response UPIU (with EHS field)" back to Host

**Command Structure Table:**
| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | | | | OPERATION CODE (A2h) | | | | |
| 1 | | | | SECURITY PROTOCOL | | | | |
| 2 | | | | SECURITY PROTOCOL SPECIFIC | | | | |
| 3 | | | | (Region Info) | | | | |
| 4 | | | | Reserved | | | | |
| 5 | | | | Reserved | | | | |
| 6 | (MSB) | | | TRANSFER LENGTH | | | | (LSB) |
| 9 | | | | | | | | |
| 10 | | | | Reserved | | | | |
| 11 | | | | CONTROL = 00h | | | | |

**EHS Header Details:**
- 28: 29, 30: 31
- CDB[12]: 00h, CDB[13]: 00h, CDB[14]: 00h, CDB[15]: 00h
- EHS Header sections showing Request/Response Message Type, Nonce details, Write Counter, Address/LUN, Block Count, Result, and MAC/Key information

**Second Communication Flow:**
Similar structure with additional Data Buffer Offset and Data Transfer Count fields, plus extended header information for RPMB operations including K+Length values and EZICRC details.]

**Figure 12.18 — Authenticated Data Read Flow (in Advanced RPMB Mode)**

# JEDEC Standard No. 220G
Page 334

## 12.4.7.4.4 Authenticated Data Read (cont'd)

[**Figure 12.18 — Authenticated Data Read Flow (in Advanced RPMB Mode) (cont'd)**

This figure shows a communication flow diagram between Host and Device with the following elements:

**Left side - Host to Device flow:**
- CMD UPIU Security Protocol In (with EHS field)
- LOOP: Data in UPIU
- Response UPIU (with EHS field)

**Right side - UPIU structure diagram:**
A detailed packet structure showing bytes 0-31 with the following fields:
- Bytes 0-3: Transaction type, Flags, LUN, Task Tag
- Bytes 4-7: IID, Command, EXT_IID, Reserved, Response, Status
- Bytes 8-11: TotalEHS length, Device Information, Data Segment Length
- Bytes 12-15: Reserved, Residual Transfer Count
- Bytes 16-31: Various Reserved fields

**EHS field section:**
Contains detailed field mappings including:
- Bytes 0-3: EHS Header
- Bytes 4-5: Request/Response Message Type (0x00h)
- Bytes 6-21: Nonce, Write Counter, Address information
- Bytes 22-25: Write Counter (0...0h)
- Bytes 26-27: Address/LUN
- Bytes 28-29: Block Count (Advanced RPMB Block Count)
- Bytes 30-31: Result (Result Code)
- Bytes 32-63: MAC from the device

**Header section:**
Shows K, K+1, K+2, K+3 structure with:
- Sense Data Length, Sense Data sections
- K+16 through K+19: Various Sense Data fields
- Data EZERC information

**Notes:**
1. Note 1: K=48 for UPIU. Sense data length is included
2. Note 2: EHS field must not be sent when SPINOR command terminated with CHECK CONDITION status. In this case, the Total EHS length is 0H.]

# 12.4.7.4.5 Authenticated Secure Write Protect Configuration Block Write

• Authenticated Secure Write Protect Configuration Block write operation is supported by RPMB region 0 only. If Authenticated Secure Write Protect Configuration Block write operation is issued to the RPMB region other than RPMB region 0, then returned result is "General failure" (0001h/0081h).

○ The Authenticated Secure Write Protect Configuration Block write sequence is initiated by a SECURITY PROTOCOL OUT command.

○ An initiator sends the SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region 0 in the SECURITY PROTOCOL SPECIFIC field.

○ If the INC_512 bit and TRANSFER LENGTH field are not set to zero and 4096 respectively, then the command shall be terminated with CHECK CONDITION status with the sense key set to ILLEGAL REQUEST and the additional sense code set to INVALID FIELD IN CDB.

○ The SECURITY PROTOCOL OUT command delivers a single RPMB message data frame which contains the Secure Write Protect Configuration Block in the Data field. The Secure Write Protect Configuration Block is specific of the logical unit indicated by the LUN field

○ The other fields of RPMB data frame are set as specified in the following: Request Message Type = 0006h, Result = 0000h, Advanced RPMB Block Count = 0001h, Address = LUN, Write Counter = current counter value, Nonce from the host, and MAC.

○ When the device receives the RPMB message data frame, it first checks whether the write counter has expired. If the write counter is expired then the device sets the result to "Write failure, write counter expired" (0085h). The Secure Write Protect Configuration Block is not updated.

○ If the write counter was not expired, then the device calculates the MAC of request type, Advanced RPMB Block Count, write counter, address and data, and compares this with the MAC in the request. If the two MAC's are different, then the device sets the result to "Authentication failure" (0002h). The Secure Write Protect Configuration Block is not updated.

○ If the MAC in the request and the calculated MAC are equal, then the device compares the write counter in the request with the write counter stored in the device. If the two counters are different then the device sets the result to "Counter failure" (0003h). The Secure Write Protect Configuration Block is not updated.

○ If the MAC and write counter comparisons are successful then the write request is considered to be authenticated.

○ If the LUN field indicates a logical unit with bLUWriteProtect set to a value different from zero, then the device sets the result to "Secure Write Protection not applicable" (000Ah). The Secure Write Protect Configuration Block is not updated.

○ The device sets the result to "Invalid Secure Write Protect Block Configuration parameter" (0009h) and it does not update the Secure Write Protect Configuration Block if one or more of the following conditions occurs.

    ▪ The LUN field is invalid: greater than the value specified by bMaxNumberLU or if the logical unit is not enabled (bLUEnable=00h) ), or if the LUN value differs from the LUN value in the Advanced RPMB Meta Information in EHS.

    ▪ The DATA LENGTH is set to a value different from the following ones: 0, 16, 32, 48, 64.

    ▪ The LOGICAL BLOCK ADDRESS in a Secure Write Protect entry exceeds the logical unit capacity.

---

JEDEC Standard No. 220G  
Page 335

# JEDEC Standard No. 220G
Page 336

## 12.4.7.4.5 Authenticated Secure Write Protect Configuration Block Write (cont'd)

- The LOGICAL BLOCK ADDRESS plus the NUMBER OF LOGICAL BLOCKS in a Secure Write Protect entry exceeds the logical unit capacity.

- Two or more Secure Write Protect entries specify overlapping areas.

- With this request, the number of Secure Write Protect areas set in the entire device is increased to a value greater than what indicated by bNumSecureWPArea.

  ○ If some other error occurs during the write procedure then returned result is "Secure Write Protect Configuration Block access failure" (0008h). The Secure Write Protect Configuration Block is not updated.

  ○ If no error occurred, then the Secure Write Protect Configuration Block is updated overwriting the former configuration and the write counter is incremented by one.

• The device may return GOOD status in response to the SECURITY PROTOCOL OUT command regardless of whether the Authenticated Secure Write Protect Configuration Block Write was successful or not.

• Device returns the RPMB data frame containing the Response Message Type = 0600h, the incremented counter value, a copy of the Nonce received in the request, the MAC and result of the Authenticated Secure Write Protect Configuration Block write operation.

[THIS IS FIGURE: A flow diagram showing communication between Host and Device with the following elements:

1. Host to Device: CMD UPIU Security Protocol Out (with EHS field)
2. Device to Host: Ready To Transfer UPIU  
3. Host to Device: DATA Out UPIU
4. Device to Host: Response UPIU (with EHS field)

The diagram includes detailed bit-field layouts showing:
- COMMAND UPIU structure with fields for Flags, LUN, Task Tag, IID, Command Set Type, Reserved fields, MSB/LSB data, etc.
- Bit-by-bit breakdown of operation codes and security protocol fields
- EHS field structure showing various components like CDB fields, message types, nonce, write counter, address/LUN, block count, result, and MAC

The figure is labeled "Figure 12.19 — Authenticated Secure Write Protect Configuration Block Write Flow (in Advanced RPMB Mode)"]

# JEDEC Standard No. 220G
## Page 337

### 12.4.7.4.5 Authenticated Secure Write Protect Configuration Block Write (cont'd)

[**Figure 12.19 - Authenticated Secure Write Protect Configuration Block Write Flow (in Advanced RPMB Mode) (cont'd)**

This is a sequence diagram showing communication between Host and Device. The diagram shows:

**Left side: Host**
**Right side: Device**

**Communication flows from top to bottom:**
1. CMD UPIU Security Protocol Out (with EHS field) →
2. ← Ready To Transfer UPIU
3. DATA Out UPIU →
4. ← Response UPIU (with EHS field)

**Right side shows a detailed DATA OUT UPIU structure with numbered byte positions:**

| Bytes | Field | Description |
|-------|-------|-------------|
| 0-3 | x000 001bh, Flags, LUN, Task Tag |
| 4-7 | IID, Reserved, Reserved, Reserved, EXT_IID Reserved |
| 8-11 | TotalLEB Length (8'h3), Reserved, Data Segment Length (MSB), (LSB) |
| 12-15 | (MSB), Data Buffer Offset, (LSB) |
| 16-19 | Data Transfer Count |
| 20-23 | Reserved |
| 24-27 | Reserved |
| 28-31 | Reserved |

**Header E2ECRC (omit if DD=0):**
- K, K+1, K+2, K+3
- LUN, DATA LENGTH, Reserved, Reserved
- K+16 through K+31

**Secure Write Protect Entry 0**
- K+64 through K+79

**Secure Write Protect Entry 3**
- K+480 and beyond

**Reserved ("0" padding)**
**Data E2ECRC (omit if DD=0)**

*Note 1: K=32 if FD=0*]

# 12.4.7.4.5 Authenticated Secure Write Protect Configuration Block Write (cont'd)

[This is a flow diagram showing communication between Host and Device with the following elements:

**Left side - Host:**
- Sends CMD UPIU Security Protocol Out (with EHS field) to Device
- Receives Ready To Transfer UPIU from Device
- Sends DATA Out UPIU to Device
- Receives Response UPIU (with EHS field) from Device

**Right side - Device with RESPONSE UPIU table:**

| Byte | 0 | 1 | 2 | 3 |
|------|---|---|---|---|
| 0x00 | 0001b | Flags | LUN | Task Tag |
| 4 | | | 6 | 7 |
| 8 | IID | Command Set Type | EXT_IID | Reserved | Response | Status |
| | | | 9 | 10 | (MSB) 11 | (LSB) |
| 12 | Total EHS Length | Device Information | Data Segment Length | |
| | (MSB) 13 | | 14 | 15 (LSB) |
| 16 | | Residual Transfer Count | | |
| | 17 | | 18 | 19 |
| 20 | | Reserved | | |
| | 21 | | 22 | 23 |
| 24 | | Reserved | | |
| | 25 | | 26 | 27 |
| 28 | | Reserved | | |
| | 29 | | 30 | 31 |
| | | Reserved | | |

**EHS field:**
- 0~3: EHS Header
- 4~5: (Req./Resp. Message Type) 0600h
- 6~21: (Device) Copy of Nonce
- 22~25: (Write Counter) New Counter Value
- 26~27: (Address / LUN) LUN
- 28~29: (Block Count) 0000h
- 30~31: (Result) Result Code
- 32~63: (MAC / Key) MAC from the device

**Header E2ECRC (omit if HD=0):**
- K (MSB) | K+1 (LSB) | K+2 | K+3
- Sense Data Length | Sense Data[0] | Sense Data[1]

- K+16 | K+17 | K+18 | K+19
- Sense Data[14] | Sense Data[15] | Sense Data[16] | Sense Data[17]
- Data E2ECRC (omit if DD=0)

**Notes:**
- Note 1: K=32 if HD=0 and EHS field is not included
- Note 1a: K=96 if HD=0 and EHS field is included
- Note 2: EHS field is included only if the UPDO command is terminated with CHECK CONDITION status. In this case, the Total EHS length is 0h.
- Note 3: The Write Counter is incremented only if the Enable operation was successfully completed.]

**Figure 12.19 — Authenticated Secure Write Protect Configuration Block Write Flow (in Advanced RPMB Mode) (cont'd)**

---

*JEDEC Standard No. 220G*  
*Page 338*

# 12.4.7.4.6 Authenticated Secure Write Protect Configuration Block Read

• Authenticated Secure Write Protect Configuration Block read operation is supported by RPMB region 0 only. If Authenticated Secure Write Protect Configuration Block read operation is issued to the RPMB region other than RPMB region 0, then returned result is "General failure" (0001h/0081h).

• The Authenticated Secure Write Protect Configuration Block Read sequence is initiated by a SECURITY PROTOCOL IN command.

    ○ An initiator sends the SECURITY PROTOCOL IN command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region 0 in the SECURITY PROTOCOL SPECIFIC field.

    ○ If the INC_512 bit and TRANSFER LENGTH field are not set to zero and 4096 respectively, then the command shall be terminated with CHECK_CONDITION status with the sense key set to ILLEGAL REQUEST and the additional sense code set to INVALID FIELD IN CDB.

    ○ The SECURITY PROTOCOL IN command delivers a single RPMB message data frame which contains the LUN field. The Secure Write Protect Configuration Block that will be returned is specific of the logical unit indicated by the LUN field.

    ○ The RPMB data frame delivered from the host to the device includes the Request Message Type = 0007h, Advanced RPMB Block Count = 0001h, Address = LUN, the Data and Nonce.

    ○ If the LUN field is not valid, then the device sets the result to "Invalid Secure Write Protect Block Configuration parameter" (0009h/0089h). The LUN field is invalid if it is greater than the value specified by bMaxNumberLU or if the logical unit is not enabled (bLUEnable = 00h).

    ○ If the LUN field indicates a logical unit with bLUWriteProtect set to a value different from zero, then the device sets the result to "Secure Write Protection not applicable" (000Ah/008Ah).

    ○ After successful fetch of the Secure Write Protect Configuration Block, the MAC is calculated from response type, nonce, address, data and result. If the MAC calculation fails then returned result is "Authentication failure" (0002h/0082h).

• The device returns a RPMB data frame with Response Message Type = 0700h, the Advanced RPMB Block Count, a copy of the nonce received in the request, the contents of the Secure Write Protect Configuration Block in the Data field, the MAC and the result

• If data fetch from addressed location inside device fails or some other error occurs during the read procedure then returned result is "Secure Write Protect Configuration Block access failure" (0008h/0088h).

---
*JEDEC Standard No. 220G*  
*Page 339*

# JEDEC Standard No. 220G
## Page 340

### 12.4.7.4.6 Authenticated Secure Write Protect Configuration Block Read Flow (cont'd)

[DIAGRAM: Flow diagram showing communication between Host and Device with the following elements:

**First flow:**
- Host sends "CMD UPIU Security Protocol In (with EHS field)" to Device
- Device sends "Data in UPIU" back to Host  
- Device sends "Response UPIU (with EHS field)" back to Host

**Command UPIU structure showing bit fields:**
- Bits 0-3: Flags (xx00 0001b), LUN, Task Tag
- Bits 4-7: Command Set Type, Reserved fields, EXT_IID Reserved
- Bits 8-11: Total EHS length (02h), Reserved, (MSB) Data Segment Length, (LSB)
- Bits 12-15: (MSB), Expected Data Transfer Length, (LSB)

**Expected Data Transfer Length bit breakdown:**
| Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-----|---|---|---|---|---|---|---|---|
| Byte 0 | | | OPERATION CODE (A2h) | | | | | |
| 1 | | | SECURITY PROTOCOL | | | | | |
| 2 | | | SECURITY PROTOCOL SPECIFIC | | | | | |
| 3 | | | (Region Info) | | | | | |
| 4 | | | Reserved | | | | | |
| 5 | | | Reserved | | | | | |
| 6 | | | | | | | | |
| 9 | | | TRANSFER LENGTH | | | | | |
| 10 | | | Reserved | | | | | |
| 11 | | | CONTROL = 00h | | | | | |

**EHS field breakdown:**
- CDB[12]=00h, CDB[13]=00h, CDB[14]=00h, CDB[15]=00h
- EHS Header with various fields including Rev/Resp Message Type, Nonce from host, Write Counter, Address/LUN, Block Count, Rcvd, and MAC/Key
- Header E2ECRC (omit if HD=0)

**Second flow:**
- Host sends "CMD UPIU Security Protocol In (with EHS field)" to Device
- Device sends "Data in UPIU" back to Host
- Device sends "Response UPIU (with EHS field)" back to Host

**Second Command UPIU structure:**
Similar structure with additional fields for Data Buffer Offset, Data transfer Count, and various reserved sections extending to K+79 with Secure Write Protect Entries.]

**Figure 12.20 — Authenticated Secure Write Protect Configuration Block Read Flow (in Advanced RPMB Mode)**

# JEDEC Standard No. 220G
## Page 341

### 12.4.7.4.6 Authenticated Secure Write Protect Configuration Block Read Flow (cont'd)

[THIS IS FIGURE: A detailed protocol flow diagram showing communication between Host and Device for Authenticated Secure Write Protect Configuration Block Read Flow. The diagram includes:

1. **Message Flow Section**: Shows CMD UPIU Security Protocol In (with EHS field) flowing from Host to Device, followed by Data in UPIU and Response UPIU (with EHS field) flowing back from Device to Host.

2. **Response UPIU Structure Table**: A detailed byte-by-byte breakdown showing:
   - Bytes 0-31 with various fields including:
     - Transaction Type (0x00 0001b)
     - Flags, LUN, Task Tag
     - Command Set Type, EXT_IID, Reserved, Response, Status
     - Total EHS length, Device Information, Data Segment Length
     - Residual Transfer Count
     - Reserved sections

3. **EHS Field Details**: Shows the Extended Header Segment structure with:
   - EHS Header (bytes 0*-3)
   - Request/Response Message Type (0*100h)
   - Nonce/Copy information
   - Write Counter, Address/LUN details
   - Block Count and Result sections
   - MAC information and verification codes

4. **Additional Data Fields**: Shows sense data structure (K+16 through K+19) with sense data bytes 14-17.

The diagram includes detailed notes about EHS field inclusion conditions and CHECK CONDITION status handling.]

**Figure 12.20 — Authenticated Secure Write Protect Configuration Block Read Flow (in Advanced RPMB Mode) (cont'd)**

# 12.4.7.4.7 RPMB Purge Enable

The RPMB Purge operation is initiated by a SECURITY PROTOCOL OUT command.

• An initiator sends the SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame includes the Request Message Type = 0008h (RPMB Purge Enable Request), Write Counter, Nonce, and MAC.

  ○ When the device receives the Request message (RPMB Purge Enable Request), it first checks whether the write counter has expired. If the write counter is expired then the device sets the Result to "Write failure, write counter expired" (0085h) and the RPMB Purge is not initiated.

  ○ If the Write Counter was not expired, then the device calculates the MAC of request and compares this with the MAC in the request. If the two MAC's are different, then the device sets the Result to "Authentication failure" (0002h) and RPMB Purge operation is not initiated.

  ○ If the Write Counter and MAC comparisons are successful, then the RPMB Purge Enable Request is considered to be authenticated and the RPMB Purge operation on the target RPMB Region is initiated.

  ○ When the device is ready to start purge the RPMB, the device can return a GOOD status in response to the SECURITY PROTOCOL OUT command, regardless of whether the RPMB purge operation was successful or not. The success or failure of RPMB purge can be known by the operation of RPMB Purge Status Read.

  ○ On the successful completion of the RPMB Purge Enable Request Message, the device shall update the write counter in the RPMB Purge Enable Response.

• If a GOOD status is not return, a general failure error should be reported.

# 12.4.7.4.7 RPMB Purge Enable (cont'd)

[DIAGRAM: Communication flow between Host and Device showing RPMB Purge Enable command structure]

**Host** ↔ **Device**

**CMD UPIU Security Protocol Out (with EHS field)** →

**← Response UPIU (with EHS field)**

## COMMAND UPIU

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | x000 0001b | | | Flags | | LUN | | Task Tag |
| 4 | | 5 | | 6 | | 7 | |
| | ID | Command Set Type | Reserved | Reserved | EXT_IID_Reserved |
| 8 | | 9 | | 10 | (MSB) | 11 | (LSB) |
| | Total EHS Length (02h) | Reserved | Data Segment Length (0000h) |
| 12 | (MSB) | 13 | | 14 | | 15 | (LSB) |
| | | | Expected Data Transfer Length | |

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | | | | OPERATION CODE (85h) | |
| 1 | | | | SECURITY PROTOCOL | |
| 2 | | | | SECURITY PROTOCOL SPECIFIC | |
| 3 | | | | (Region Info) | |
| 4 | INC_512 | | | Reserved | |
| 5 | | | | Reserved | |
| 6 | (MSB) | | | TRANSFER LENGTH | | (LSB) |
| 9 | | | | | |
| 10 | | | | Reserved | |
| 11 | | | | CONTROL = 00h | |

| Bits | 28 | 29 | 30 | 31 |
|------|----|----|----|----|
| | CDB[12]:00h | CDB[13]:00h | CDB[14]:00h | CDB[15]:00h |

## EHS field

| Bits | Description | Value |
|------|-------------|--------|
| 0~3 | EHS Header | - |
| 4~5 | (Req./Rep. Message Type) | 0008h |
| 6~21 | (Device) | Nonce from Host |
| 22~25 | (Write Counter) | Current counter Value |
| 26~27 | (Address / LUN) | 0000h |
| 28~29 | (Block Count) | 0000h |
| 30~31 | (Result) | 0000h |
| 32~63 | (MAC / Key) | Mac from the host |
| | | Header E2E CRC (omit if HD=0) |

**Figure 12.21 — RPMB Purge Enable Flow (in Advanced RPMB Mode)**

---
JEDEC Standard No. 220G  
Page 343

# JEDEC Standard No. 220G
## Page 344

### 12.4.7.4.7 RPMB Purge Enable Flow (cont'd)

[THIS IS DIAGRAM: Shows communication flow between Host and Device with CMD UPIU Security Protocol Out (with EHS field) going from Host to Device, and Response UPIU (with EHS field) going from Device to Host]

#### RESPONSE UPIU
| 0 | 1 | 2 | 3 |
|---|---|---|---|
| xx10 0001b | | Flags | |
| 4 | 5 | 6 | 7 |
| IID | Command Set Type | EXT_IID Reserved | Response |
| 8 | 9 | 10 | 11 |
| Total EHS length^[1] | Device Information | (MSB) Data Segment Length | (LSB) |
| 12 | 13 | 14 | 15 |
| (MSB) | | Residual Transfer Count | (LSB) |
| 16 | 17 | 18 | 19 |
| | | Reserved | |
| 20 | 21 | 22 | 23 |
| | | Reserved | |
| 24 | 25 | 26 | 27 |
| | | Reserved | |
| 28 | 29 | 30 | 31 |
| | | Reserved | |

#### EHS field^[2]

| Field | Description | Value |
|-------|-------------|-------|
| 0~3 | | EHS Header |
| 4~5 | (Req./Resp. Message Type) | 0800h |
| 6~21 | (Nonce) | Copy of Nonce |
| 22~25 | (Write Counter) | New Counter Value^[3] |
| 26~27 | (Address / LUN) | 0000h |
| 28~29 | (Block Count) | 0000h |
| 30~31 | (Result) | Result Code |
| 32~63 | (MAC / Key) | MAC from the device |

| Field | Description | Value |
|-------|-------------|-------|
| | | Header E2ECRC (omit if HD=0) |
| K | (MSB) K+1 | (LSB) K+2 | K+3 |
| | Sense Data Length | Sense Data[0] | Sense Data[1] |
| K+16 | K+17 | K+18 | K+19 |
| Sense Data[14] | Sense Data[15] | Sense Data[16] | Sense Data[17] |

Data E2ECRC (omit if DD=0)

**Note 1** K=32 if HD=0 and EHS field is omitted, K=48 if HD=1 and EHS field is included
**Note 2** EHS field shall not be sent when SPI/SPO command is terminated with CHECK CONDITION status, in this case the Total EHS length is 0h
**Note 3** The Write Counter is incremented only if the Enable operation was successfully completed

**Figure 12.16 — RPMB Purge Enable Flow (in Advanced RPMB Mode) (cont'd)**

# 12.4.7.4.8 RPMB Purge Status Read

RPMB Purge polling starts by issuing a SECURITY PROTOCOL IN command.

• An initiator sends a SECURITY PROTOCOL IN command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame contains the Request Message Type = 0009h (RPMB Purge Status Read Request) and Nonce.

• The device returns purge status by issuing a DATA IN UPIU with an RPMB Purge Response Packet for Advanced RPMB.

  ○ Supported purge status value are as follows:
    ▪ 00 – RPMB Purge not initiated (reset value)
    ▪ 01 – RPMB Purge in progress
    ▪ 02 – RPMB Purge successfully completed
    ▪ 03 – RPMB Purge general failure

• The device returns a RPMB data frame with Response Message Type = 0900h (RPMB Purge Status Read Response), a copy of the Nonce received in the request, the MAC and the Result.

• If a GOOD status is not returned, a general failure error should be reported.

[Figure 12.22 — RPMB Purge Status Read Flow (in Advanced RPMB Mode): This diagram shows the communication flow between Host and Device for RPMB Purge Status Read operation. It includes:

1. A sequence diagram showing CMD UPIU Security Protocol In (with EHS field) from Host to Device, followed by Data In UPIU and Response UPIU (with EHS field) back to Host.

2. A detailed COMMAND UPIU packet structure showing fields from bytes 0-15 including flags, LUN, task tag, IID, command set type, reserved fields, and data segment length.

3. A breakdown of the EHS field showing the operation code (A2h), security protocol, security protocol specific, region info, reserved fields, transfer length, control field, and various CDB bytes with their specific values and purposes including nonce, write counter, address/LUN, block count, result, and MAC/key information.]

---
*JEDEC Standard No. 220G  
Page 345*

# JEDEC Standard No. 220G
Page 346

## 12.4.7.4.8 RPMB Purge Status Read (cont'd)

[DIAGRAM: Flow diagram showing communication between Host and Device with the following elements:

- Host and Device boxes connected by arrows
- CMD UPIU Security Protocol In (with EHS field) arrow from Host to Device
- Data in UPIU arrow from Device to Host  
- Response UPIU (with EHS field) arrow from Device to Host

Adjacent to the diagram is a detailed data structure table showing:

DATA IN UPIU with numbered fields 0-31 containing:
- Fields for IID, Reserved, EXT_IID, Flags, LUN, Task Tag, Response
- Total EHS length, Reserved fields, Data Segment Length
- Data Buffer Offset, Data Transfer Count
- Various Reserved fields
- Header (32CRC+omit if HD=0)

Below this are additional fields K, K+1, K+2, K+3 showing:
- Adv. RPMB Data[0] through Adv. RPMB Data[3]
- K+Length-4 through K+Length-1 entries
- Adv. RPMB Data[Length-4] through Adv. RPMB Data[Length-1]
- Data (32CRC omit if DD=0)
- Note 1 (~3) if HD=0]

**Figure 12.22 — RPMB Purge Status Read Flow (in Advanced RPMB Mode) (cont'd)**

# JEDEC Standard No. 220G
Page 347

## 12.4.7.4.8 RPMB Purge Status Read (cont'd)

[THIS IS FIGURE: A communication flow diagram showing interaction between Host and Device through CMD UPIU, Data in UPIU, and Response UPIU with Security Protocol In and EHS field. The diagram includes a detailed packet structure table showing byte positions 0-31 with various fields like flags, LUN, Task Tag, Command Set Type, Response, Status, etc.]

### RESPONSE UPIU Structure:

| Byte | Field | Description |
|------|-------|-------------|
| 0 | 0x10 0003h | - |
| 1 | Flags | - |
| 2 | - | LUN |
| 3 | - | Task Tag |
| 4 | Command Set Type | EXT_IID Reserved |
| 5 | - | - |
| 6 | - | Response |
| 7 | - | Status |
| 8 | Residual HD Length | - |
| 9 | Device Information | (MSB) |
| 10 | - | Data Segment Length |
| 11 | - | (LSB) |
| 12 | (MSB) | - |
| 13 | - | Residual Transfer Count |
| 14 | - | - |
| 15 | - | (LSB) |
| 16-31 | Reserved fields | - |

### EHS field:
- **0-3**: EHS Header
- **4-5**: (Req./Resp. Message Type) - 0000h
- **6-21**: (Nonce) - Copy of Nonce 0...00h
- **22-25**: (Write Counter) - 0000h
- **26-27**: (Address / LUN) - 0000h
- **28-29**: (Block Count) - 0001h
- **30-31**: (Result) - Result Code
- **32-63**: (MAC / Key) - MAC from the device

### Header E2ECRC (omit if HD=0):
- **K**: (MSB) K+1 (LSB) K+2 K+3
- **Sense Data Length**: Sense Data[0] Sense Data[1]

**K+16**: Sense Data[14] **K+17**: Sense Data[15] **K+18**: Sense Data[16] **K+19**: Sense Data[17]

### Notes:
- **Note 1**: K≥32 if HD≠0 and EHS field is not included; K≥96 if HD≠0 and EHS field is included
- **Note 2**: EHS field shall not be sent when SPINOR command terminated with an EHS GOOD error status if the match Total EHS length is 0h.

**Figure 12.22 — RPMB Purge Status Read Flow (in Advanced RPMB Mode) (cont'd)**

# JEDEC Standard No. 220G
Page 348

## 12.4.7.4.9 Authenticated Vendor Specific Command Request

The Authenticated Vendor Specific Command operation is initiated by a SECURITY PROTOCOL OUT command. An initiator sends the SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB message includes the Request Message Type = 0010h (Authenticated Vendor Specific Command Request), Advanced RPMB Block Count, Write Counter, Nonce, and MAC.

• When the device receives the Request message (Authenticated Vendor Specific Command Request), it first checks whether the write counter has expired. If the write counter is expired then the device sets the Result to "Write failure, write counter expired" (0008h) and the RPMB Purge is not initiated.

• If the Write Counter was not expired, then the device calculates the MAC of request and compares this with the MAC in the request. If the two MAC's are different, then the device sets the Result to "Authentication failure" (0002h) and vendor specific command operation is not initiated.

• If the Write Counter and MAC comparisons are successful, then the Vendor Specific Command Request is considered to be authenticated and the vendor specific command operation is initiated.

• When the device is ready to start the vendor specific command, the device can return a GOOD status in response to the SECURITY PROTOCOL OUT command, regardless of whether the vendor specific command operation was successful or not. The success or failure of vendor specific command can be known by the operation of vendor specific command Status Read.

• On the successful completion of the Vendor Specific Command Request Message, the device shall increment the write counter.

If a GOOD status is not return, a general failure error should be reported.

[Diagram showing communication flow between Host and Device with the following components:
- CMD UPIU Security Protocol Out (with EHS field)
- LOOP Ready To Transfer UPIU
- DATA OUT UPIU  
- Response UPIU (with EHS field)

The diagram includes a detailed breakdown of the COMMAND UPIU structure showing:
- Flags, LUN, Task Tag fields
- Command Set Type, Reserved, EXT_ID fields
- Total EHS Length, Reserved, Data Segment Length fields
- Expected Data Transfer Length
- A bit field breakdown (Bits 7-0) showing:
  - OPERATION CODE (85h)
  - SECURITY PROTOCOL
  - SECURITY PROTOCOL SPECIFIC
  - Region Info
  - Reserved fields
  - ALLOCATION LENGTH
  - CONTROL = 00h

EHS field breakdown showing various components like:
- CDB header information
- Req./Resp. Message Type (0010h)
- Nonce from the host
- Current counter Value
- Advanced RPMB Block Count
- Result
- Mac from the host
- Header E2E CRC]

**Figure 12.23 — Authenticated Vendor Specific Command Request Flow (in Advanced RPMB Model)**

# 12.4.7.4.9 Authenticated Vendor Specific Command Request (cont'd)

[THIS IS FIGURE: A sequence diagram showing the flow of an Authenticated Vendor Specific Command Request in Advanced RPMB Mode. The diagram shows communication between Host and Device with the following sequence:

1. CMD UPIU Security Protocol Out (with EHS field) - Host to Device
2. Ready To Transfer UPIU - Device to Host (in a LOOP)
3. DATA Out UPIU - Host to Device
4. Response UPIU (with EHS field) - Device to Host

On the right side is a detailed DATA OUT UPIU structure table showing:
- Bytes 0-31 with various fields including:
  - xx00 0010h at bytes 0-1
  - Flags, LUN, Task Tag fields
  - Reserved fields
  - EXT_IID field
  - Total EHS length, Data Segment Length
  - Data Buffer Offset
  - Data transfer Count
  - Reserved sections

Below the main table is a breakdown of the Header EZtCRC structure showing:
- Vendor Specific Command+Data fields (X, X+1, X+2, X+3)
- Length fields (X+Length-4 through X+Length-1)
- Data EZtCRC section
- Final field showing "N-N-1 K+N-(4n-6)"]

**Figure 12.23 — Authenticated Vendor Specific Command Request Flow (in Advanced RPMB Mode) (cont'd)**

---

*JEDEC Standard No. 220G*  
*Page 349*

# JEDEC Standard No. 220G
Page 350

## 12.4.7.4.9 Authenticated Vendor Specific Command Request (cont'd)

[This is a sequence diagram showing communication between Host and Device for an Authenticated Vendor Specific Command Request Flow in Advanced RPMB Mode. The diagram shows the following sequence:

1. CMD UPIU Security Protocol Out (with EHS field) - from Host to Device
2. Ready To Transfer UPIU - from Device to Host (in a LOOP)
3. DATA Out UPIU - from Host to Device
4. Response UPIU (with EHS field) - from Device to Host

On the right side is a detailed packet structure diagram showing:

RESPONSE UPIU format with byte positions 0-31, including:
- Flags, LUN, Task Tag fields
- Command Set Type, EXT_ID, Reserved, Response, Status fields
- Device Information and Data Segment Length fields
- Residual Transfer Count
- Reserved sections
- EHS Header section

Below this is an EHS field structure showing bytes 0-63 with various fields including:
- Message Type, Copy of Nonce, New Counter Value
- Address/LUN, Block Count
- Result, Result Code
- MAC/Key, MAC from device
- Header E2ECRC
- Sense Data sections

The diagram includes detailed notes about field meanings and conditions.]

**Figure 12.23 — Authenticated Vendor Specific Command Request Flow (in Advanced RPMB Mode) (cont'd)**

# JEDEC Standard No. 220G Page 351

## 12.4.7.4.10 Authenticated Vendor Specific Command Status Read Request

Authenticated Vendor Specific Command Status Read sequence starts by issuing a SECURITY PROTOCOL IN command.

An initiator sends a SECURITY PROTOCOL IN command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB message contains the Request Message Type = 0011h (Authenticated Vendor Specific Command Status Read Request), Nonce and the Advanced RPMB Block Count.

The device returns vendor specific command status by issuing one or more DATA IN UPIUs for Advanced RPMB.

The device returns a RPMB data frame with Response Message Type = 1100h (Authenticated Vendor Specific Command Status Response), a copy of the Nonce received in the request, the MAC and the Result.

○ Supported vendor command status value are as follows, reported in the Authenticated Vendor Specific Command Status Response UPIU's Result field
  ▪ 00 – Vendor Specific Command not initiated (reset value)
  ▪ 01 – Vendor Specific Command in progress
  ▪ 02 – Vendor Specific Command completed
  ▪ 03 – Vendor Specific Command general failure

If a GOOD status is not returned, a general failure error should be reported.

[THIS IS DIAGRAM: A flow diagram showing communication between Host and Device with the following elements:

**COMMAND UPIU table:**
| Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|---|---|---|---|---|---|---|---|
| 0 | OPERATION CODE (A2h) |
| 1 | SECURITY PROTOCOL |
| 2 | SECURITY PROTOCOL SPECIFIC |
| 3 | (Region Info) |
| 4-5 | Reserved |
| 6 | (MSI) TRANSFER LENGTH |
| 9-10 | Reserved |
| 11 | CONTROL = 00h |

The diagram shows:
1. Host sends "CMD UPIU Security Protocol In (with EHS field)" to Device
2. Device responds with "Data in UPIU" (shown in a loop)
3. Device sends back "Response UPIU (with EHS field)"

**EHS field details:**
- Bytes 28-31: CDB[12]=00h, CDB[13]=00h, CDB[14]=00h, CDB[15]=00h
- Bytes 0-3: EHS Header
- Bytes 4-5: (Req./Resp. Message Type) 0011h
- Bytes 6-21: (Device) Nonce from the host
- Bytes 22-25: (Write Counter) 0...00h
- Bytes 26-27: (Address / LUN) 0000h
- Bytes 28-29: (Block Count) Advanced RPMB Block Count
- Bytes 30-31: (Result) 0000h
- Bytes 32-63: (MAC / Key) 0...00h Header C2CRC (omit if HID=0)]

**Figure 12.24 — Authenticated Vendor Specific Command Status Read Request Flow (in Advanced RPMB Mode)**

# JEDEC Standard No. 220G
## Page 352

### 12.4.7.4.10 Authenticated Vendor Specific Command Status Read Request (cont'd)

[THIS IS FIGURE: A flow diagram showing the Authenticated Vendor Specific Command Status Read Request process. The diagram shows communication between Host and Device with the following components:

1. Host sends "CMD UPIU Security Protocol In (with Flags field)" to Device
2. A LOOP section showing "Data in UPIU" exchanged between Host and Device
3. Device responds with "Response UPIU (with EHS field)"

On the right side is a detailed data structure table showing:
- DATA IN UPIU with numbered fields from 0-31
- Fields include: Flags, LUN, Task Tag, IID, Reserved, EXT_IID, Reserved, Response, Reserved
- Various MSB/LSB fields and data segments
- At the bottom shows vendor-specific command data fields (K1 through K4) with different lengths and data types
- Includes "Data E2E CRC (omit if DD=0)" and "NOTE 1: K1>K2+K3+K4" annotations]

**Figure 12.24 — Authenticated Vendor Specific Command Status Read Request Flow (in Advanced RPMB Mode) (cont'd)**

# 12.4.7.4.10 Authenticated Vendor Specific Command Status Read Request (cont'd)

[THIS IS DIAGRAM: A flow diagram showing communication between Host and Device using CMD UPIU, Data in UPIU, and Response UPIU with EHS field. The diagram includes a detailed packet structure showing:

- RESPONSE UPIU with bytes 0-31 mapped out
- Fields including: Flags, LUN, Task Tag, Command Set Type, EXT_ID, Reserved, Response, Status
- Transfer length, Device Information, Data Segment Length
- Residual Transfer Count
- Reserved sections
- EHS Header section (bytes 0-3 through 32-63) containing:
  - EHS (Req./Resp. Message Type)
  - Nonce (Copy of the Nonce)
  - Write Counter
  - Address (/LUN)
  - Block Count (Advanced RPMB Block Count)
  - Result (Status)
  - MAC/Xcvr (MAC from the device)
- Header E2E-CRC section with:
  - MSB K+1, LSB K+2, K+3 for Sense Data Length and Sense Data[0-1]
  - K+16 through K+19 for Sense Data[14-17]
  - Data E2E-CRC information]

**Figure 12.24 — Authenticated Vendor Specific Command Status Read Request Flow (in Advanced RPMB Model) (cont'd)**

## 12.5 Malware Protection

The UFS device will also have the option to protect boot, bus configuration settings and other important device configuration settings so that once they are set they cannot be modified. The implementation of the protection of these parameters is defined within the spec where the parameter is defined.

---
*JEDEC Standard No. 220G*  
*Page 353*