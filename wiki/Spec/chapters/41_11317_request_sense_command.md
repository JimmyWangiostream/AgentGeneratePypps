# 11.3.17 REQUEST SENSE Command

The REQUEST SENSE Command requests that the Device Server transfer parameter data containing sense data information to the Application Client.

• Sense Data describes error or exception condition and/or current operational status of device
  ○ i.e., get the device "status"

• UFS devices will return a fixed format data record of 18 bytes of sense data as described in Table 10.19.

• Three tiered error code for detailed status
  ○ Sense Key: main indicator
  ○ ASC: Additional Sense Code
  ○ ASCQ: Additional Sense Code Qualifier

• If a REQUEST SENSE command is received with a pending UNIT ATTENTION condition (i.e., before the device server reports CHECK_CONDITION status), the device server shall perform the REQUEST SENSE command and clear the UNIT ATTENTION condition.

The Command CDB shall be sent in a single COMMAND UPIU

## Table 11.32 — REQUEST SENSE Command

| Byte | Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|-----|---|---|---|---|---|---|---|---|
| 0 |  |  |  | OPERATION CODE (03h) |  |  |  |  |  |
| 1 |  |  |  | Reserved |  |  |  |  | DESC = 0b |
| 2 |  | (MSB) |  |  |  |  |  |  |  |
| 3 |  |  |  | Reserved |  |  |  |  | (LSB) |
| 4 |  |  |  | ALLOCATION LENGTH |  |  |  |  |  |
| 5 |  |  |  | CONTROL = 00h |  |  |  |  |  |

UFS devices are not required to support descriptor format sense data.

### 11.3.17.1 Request Sense Data Response

• Data returned from a REQUEST SENSE command will be transferred to the Application Client in a single DATA IN UPIU.

• The Device Server will transfer up to 18 bytes of Response Data in the Data Segment area of a DATA IN UPIU.
  ○ Return 18 bytes if Allocation Length in CDB ≥ 18.
  ○ Return Allocation Length bytes if Allocation Length in CDB < 18.
  ○ An Allocation Length of zero specifies that no data shall be transferred. This condition shall not be considered as an error, and DATA IN UPIU shall not be generated.

• Data will be returned in the indicated Sense Data Format described in 11.3.17.2.

---

JEDEC Standard No. 220G  
Page 221

# JEDEC Standard No. 220G
Page 222

## 11.3.17.2 Sense Data

See Table 10.19.

## 11.3.17.3 Sense Key

See Table 10.20.

## 11.3.17.4 Request Sense Status Response

• STATUS response will be sent in a single RESPONSE UPIU.

• If the requested data is successfully transferred, the REQUEST SENSE command will terminate with a STATUS response of GOOD.

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned.

• Failure is very rare. When the REQUEST SENSE command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as

    ○ ILLEGAL REQUEST (range or CDB errors).

• Will not fail due to a pending UNIT ATTENTION condition.

• If the REQUEST SENSE command was received with a pending unit attention condition, the returned sense data will indicate the cause of the unit attention condition, and the unit attention condition within the device server will be cleared.

• If a REQUEST SENSE command is terminated with CHECK CONDITION status, then the device server shall not clear the pending unit attention condition.