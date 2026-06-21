# JEDEC Standard No. 220G
Page 232

## 11.3.23 SEND DIAGNOSTIC Command

The SEND DIAGNOSTIC command requests the Device Server to perform diagnostic operations on the SCSI target device, on the logical unit or on both. Logical units shall implement, at a minimum, the default self-test feature (i.e., the SELFTEST bit equal to one and a parameter list length of zero).

The Command CDB shall be sent in a single COMMAND UPIU.

### Table 11.40 — SEND DIAGNOSTIC Command

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 |   |   |   | OPERATION CODE (1Dh) |   |   |   |   |
| 1 | SELF-TEST CODE |   | PF | Reserved = 0b | SELFTEST | DEVOFFL | UNITOFFL |
| 2 |   |   |   | Reserved |   |   |   |   |
| 3 | (MSB) |   |   |   |   |   |   |   |
|   |   |   | PARAMETER LIST LENGTH |   |   |   |   |
| 4 |   |   |   |   |   |   |   | (LSB) |
| 5 |   |   |   | CONTROL = 00h |   |   |   |   |

### 11.3.23.1 Send Diagnostic Parameters

#### Table 11.41 — Send Diagnostic Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 1 | 7:5 | **SELF-TEST CODE**: Specifies the self-test code as defined in SPC4. |
| 1 | 4 | **PF**: Specifies the format of any parameter list sent by the Application Client |
| 1 | 2 | **SELFTEST**: Specifies the device server shall perform a self test. |
| 1 | 1 | **DEVOFFL**: If set to '0', the device server will perform a self-test without exhibiting any effects on the logical unit. If set to '1', the device server may perform a self-test that affects the logical unit. |
| 1 | 0 | **UNITOFFL**: If set to '0', the device server will perform a self-test without exhibiting any effects on the user accessible medium of the logical unit. If set to '1', the device server may perform operations that affect the user accessible medium. |
| 1 | 5 | **PARAMETER LIST LENGTH**: Specifies the length in bytes that shall be transferred from the Application Client to the device server. A parameter list length of zero specifies that no data shall be transferred. |

### 11.3.23.2 Send Diagnostic Command Data Transfer

The SEND DIAGNOSTIC command will transfer out the number of bytes specified by the Parameter List Length. If that value is zero then no data out transfer will occur. The Device Server will request the transfer of the specified bytes from the Application Client by issuing a series READY TO TRANSFER UPIU (RTT). RTT will be followed by DATA OUT UPIU containing the number of bytes to transfer.

# JEDEC Standard No. 220G
Page 233

## 11.3.23.3 Send Diagnostic Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU.

• If the requested diagnostics are performed successfully then the command will terminate with a STATUS response of GOOD.

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned.

• Other failures can occur for numerous reasons. When the SEND DIAGNOSTIC command fails, a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as

    ○ ILLEGAL REQUEST (range or CDB errors)
    
    ○ MEDIUM ERROR (medium failure, ECC, etc.)
    
    ○ HARDWARE ERROR (hardware failure)
    
    ○ UNIT ATTENTION (reset, power-on, etc.)
    
    ○ etc.