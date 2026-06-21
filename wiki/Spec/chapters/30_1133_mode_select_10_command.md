# JEDEC Standard No. 220G
Page 188

## 11.3.2.5 Inquiry Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU

• If the requested data is successfully transferred, the INQUIRY command will terminate with a STATUS response of GOOD

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned

• When the INQUIRY command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as
  ○ ILLEGAL REQUEST (range or CDB errors)
  ○ HARDWARE ERROR (hardware failure)

• Will not fail due to a pending UNIT ATTENTION condition

## 11.3.3 MODE SELECT (10) Command

MODE SELECT command provides a means for the application client to specify medium, logical unit, or peripheral device parameters to the device server.

• Parameters are managed by means of parameter pages called mode pages
  ○ UFS devices shall support the following mode pages
    ▪ CONTROL, CACHING, READ-WRITE ERROR RECOVERY
  ○ UFS devices may support vendor specific mode pages
  ○ See 11.4 for further details.

• Writes parameters to one or more mode pages in a list
  ○ The Application Client can specify a single, multiple or all supported pages in a single command
• Complementary command to the MODE SENSE command

The Command CDB shall be sent in a single COMMAND UPIU

**Table 11.5 — MODE SELECT (10) Command**

| Byte | Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|-----|---|---|---|---|---|---|---|---|
| 0 |  |  |  | OPERATION CODE (55h) |  |  |  |  |  |
| 1 |  | Reserved | PF = 1b |  | Reserved |  |  | SP |
| 2 |  |  |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |  |  |
| 4 |  |  | Reserved |  |  |  |  |  |
| 5 |  |  |  |  |  |  |  |  |  |
| 6 |  |  |  |  |  |  |  |  |  |
| 7 |  |  | PARAMETER LIST LENGTH |  |  |  |  |  |
| 8 |  |  |  |  |  |  |  |  |  |
| 9 |  |  | CONTROL = 00h |  |  |  |  |  |

# JEDEC Standard No. 220G
Page 189

## 11.3.3.1 Mode Select Command Parameters

### Table 11.6 — Mode Select Command Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 1 | 4:4 | **PF: PAGE FORMAT.** A page format bit set to zero specifies that all parameters after the block descriptors are vendor specific. A PF bit set to one specifies that the MODE SELECT parameters following the header and block descriptor(s) are structured as pages of related parameters as defined in the SCSI standard. |
| 1 | 0:0 | **SP: SAVE PAGES.** A save pages (SP) bit set to zero specifies that the device server shall perform the specified MODE SELECT operation, and shall not save any mode pages. If the logical unit implements no distinction between current and saved mode pages, and the SP bit is set to zero, the command shall be terminated with CHECK CONDITION status, with the sense key set to ILLEGAL REQUEST. An SP bit set to one specifies that the device server shall perform the specified MODE SELECT operation and shall save to a nonvolatile vendor specific location all the saveable mode pages including any sent in the Data-Out Buffer. Mode pages that are saved are specified by the parameter saveable (PS) bit that is returned in the first byte of each mode page when read via the MODE SENSE command. If the PS bit is set to one in the MODE SENSE data, then the mode page shall be saveable when issuing a MODE SELECT command with the SP bit set to one. If the logical unit does not implement saved pages and the SP bit is set to one, the command shall terminate with a CHECK CONDITION status and a sense key set to ILLEGAL REQUEST. |
| 7:8 | 7:0 | **PARAMETER LIST LENGTH:** Specifies length in bytes of the mode parameter list that the Application Client will transfer to the Device Server. A PARAMETER LIST LENGTH of zero specifies that no data shall be transferred, this shall not be considered an error and in this case the device shall not send RTT UPIU. |

## 11.3.3.2 Mode Select Command Data Transfer

The Device Server requests to transfer the mode parameter list from the Application Client data-out buffer by issuing one or more READY TO TRANSFER UPIU's (RTT).

The mode parameter list is delivered in one or more segments sending DATA OUT UPIU packets, as indicated in the RTT requests.

Zero or an incomplete number of segments may be requested, if an error occurs before the entire data transfer is complete.

Mode parameters are changed as specified in the received mode parameter list if the command completes successfully.

See 11.4.1.2 for details about the mode parameter list.