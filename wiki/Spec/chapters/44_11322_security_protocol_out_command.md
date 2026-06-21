# 11.3.22 SECURITY PROTOCOL OUT Command

The SECURITY PROTOCOL OUT command is used to send data to the logical unit. The data sent specifies one or more operations to be performed by the logical unit. The format and function of the operations depends on the contents of the SECURITY PROTOCOL field. See [SPC] for details.

## Table 11.39 — SECURITY PROTOCOL OUT Command

| Bit<br>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-------------|---|---|---|---|---|---|---|---|
| 0 | | | | OPERATION CODE (B5h) | | | | |
| 1 | | | | SECURITY PROTOCOL | | | | |
| 2 | | | | | | | | |
| 3 | | | SECURITY PROTOCOL SPECIFIC | | | | |
| 4 | INC_512 | | | Reserved | | | | |
| 5 | | | | Reserved | | | | |
| 6 | (MSB) | | | | | | | |
| 9 | | | TRANSFER LENGTH | | | | | (LSB) |
| 10 | | | | Reserved | | | | |
| 11 | | | | CONTROL = 00h | | | | |

### 11.3.22.1 SECURITY PROTOCOL OUT Command Parameter

• The SECURITY PROTOCOL field specifies which security protocol is being used. UFS devices shall support the following value:
  ○ ECh: JEDEC UFS application

Support of other SECURITY PROTOCOL values is device specific.

• A INC_512 bit set to one specifies that the TRANSFER LENGTH is expressed in increments of 512 bytes.

### 11.3.22.2 SECURITY PROTOCOL OUT Command Data Transfer

The Device Server requests to transfer data from the Application Client data-out buffer by issuing a series of READY TO TRANSFER UPIU's (RTT).

The data is delivered in one or more segments sending DATA OUT UPIU packets, as indicated in the RTT requests.

Zero or an incomplete number of segments may be requested, if an error occurs before the entire data transfer is complete.

---
*JEDEC Standard No. 220G*  
*Page 230*

# JEDEC Standard No. 220G
Page 231

## 11.3.22.3 SECURITY PROTOCOL OUT Command Status Response

• Status response shall be sent in a single RESPONSE UPIU

• If the command is successfully executed, it shall terminate with a STATUS response of GOOD

• Failure can occur for numerous reasons. When the command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as

    ○ ILLEGAL REQUEST (range or CDB errors)
    
    ○ HARDWARE ERROR (hardware failure)
    
    ○ UNIT ATTENTION (reset, power-on, etc.)
    
    ○ etc.