# JEDEC Standard No. 220G
## Page 294

### 12.4.4.2 MAC Calculation

The key used for the MAC calculation is always the 256 bit Authentication Key stored in the device. Input to the MAC calculation is the concatenation of the fields in the RPMB Message Data Frames from byte 228 to byte 511 (stuff bytes and the MAC are excluded).

If RPMB Message is composed by several RPMB Message Data Frames then the input message to MAC is the concatenation of bytes [228:511] of each data frame in the order in which the data frames are sent. The MAC is valid only in the last data frame.

### 12.4.4.3 RPMB Message Data Frame Delivery

The RPMB messages are delivered using SCSI security protocol commands:

• SECURITY PROTOCOL IN is used to send request messages to the device

• SECURITY PROTOCOL OUT is used to request to the device the sending of response messages.

### 12.4.5 Implementation in Advanced RPMB Mode

### 12.4.5.1 Advanced RPMB Message

An Advanced RPMB Message is composed of an Advanced RPMB Meta Information and a MAC/KEY in the EHS field in COMMAND UPIU and RESPONSE UPIU. Advanced RPMB Data is delivered through the Data Segment in DATA IN UPIU and DATA OUT UPIU. Advanced RPMB Data size shall be a multiple of 4 Kbytes.

Advanced RPMB Message size is 60 bytes and organized in EHS field as shown in Figure 12.2. Since the bLength indicates the total size of the EHS Header and EHS Data in 32 Byte units, the value of the bLength for Advanced RPMB is 02h. The Advanced RPMB Meta Information has fields to contain Request/Response Message Type, Nonce, Write Counter, Address or LUN, Block Count, and Result. See Table 12.13 for details. Depending on the value of the Request/Response Message Type, the validity of the MAC/KEY is determined.

[Figure 12.2 shows a diagram of the Advanced RPMB Message Structure in EHS Field. The structure contains:
- Bytes 0-3: EHS Header with bLength (02h for Adv. RPMB), bEHSType (01h for Adv. RPMB), and wEHSSubType
- Bytes 4-31: Advanced RPMB Meta Information (28 bytes) - EHS Data
- Bytes 32-63: MAC/Key (32 bytes) - EHS Data]

**Figure 12.2 — Advanced RPMB Message Structure in EHS Field**

# JEDEC Standard No. 220G
Page 295

## 12.4.5.1 Advanced RPMB Message (cont'd)

Table 12.13 shows the detailed fields of Advanced RPMB Meta Information

### Table 12.13 — Advanced RPMB Meta Information

| Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-----|---|---|---|---|---|---|---|---|
| Byte |   |   |   |   |   |   |   |   |
| 0 | (MSB) |   |   |   |   |   |   |   |
|   |   | Request Message Type / Response Message Type |   |   |   |   |   |   |
| 1 |   |   |   |   |   |   |   | (LSB) |
| 2 | (MSB) |   |   |   |   |   |   |   |
|   |   | Nonce |   |   |   |   |   |   |
| 17 |   |   |   |   |   |   |   | (LSB) |
| 18 | (MSB) |   |   |   |   |   |   |   |
|   |   | Write Counter |   |   |   |   |   |   |
| 21 |   |   |   |   |   |   |   | (LSB) |
| 22 | (MSB) |   |   |   |   |   |   |   |
|   |   | Address / LUN (1) |   |   |   |   |   |   |
| 23 |   |   |   |   |   |   |   | (LSB) |
| 24 | (MSB) |   |   |   |   |   |   |   |
|   |   | Block Count |   |   |   |   |   |   |
| 25 |   |   |   |   |   |   |   | (LSB) |
| 26 | (MSB) |   |   |   |   |   |   |   |
|   |   | Result |   |   |   |   |   |   |
| 27 |   |   |   |   |   |   |   | (LSB) |

NOTE 1 LUN is used in case of Authenticated Secure Write Protect Configuration Block Read and Authenticated Secure Write Protect Configuration Block Write RPMB request. Address is used in case of Authenticated Data Read and Authenticated Data Write request.

## 12.4.6 SECURITY PROTOCOL IN/OUT Commands

SECURITY PROTOCOL IN command and SECURITY PROTOCOL OUT command defined in [SPC] are used to encapsulate and deliver data packets of any security protocol between host and device without interpreting, dis-assembling or re-assembly the data packets for delivery.

The SECURITY PROTOCOL IN command and SECURITY PROTOCOL OUT command contain a SECURITY PROTOCOL field. A unique security protocol ID is assigned by T10 for JEDEC UFS application.

• SECURITY PROTOCOL = ECh (JEDEC Universal Flash Storage)