# 11.4 Mode Pages

This sub-clause describes the mode pages used with MODE SELECT command and MODE SENSE command. Subpages are identical to mode pages except that they include a SUBPAGE CODE field that further differentiates the mode page contents.

## 11.4.1 Mode Page Overview

### 11.4.1.1 Mode Page/Subpage Codes

• Mode pages and subpages are selected by Page Code field and the Subpage Code Field
• UFS devices are not required to support subpages (subpage = 0)

**Table 11.58 — Mode Page Code Usage**

| Page Code | Subpage Code | Description | Page Format |
|-----------|--------------|-------------|-------------|
| 00h | Vendor specific | Vendor specific page | Vendor specific format |
| | 00h | Device specific STANDARD page (subpage 0) | Page 0 format |
| 01h to 1Fh (SCSI SPECIFIC) | 01h to DFh | Device specific SUBPAGE | Subpage format |
| | E0h to FEh | Vendor specific SUBPAGE | Subpage Format |
| | FFh | Return all SUBPAGES for the specified device specific mode page | Page 0 format for subpage 00h, subpage format for subpages 01h to FEh |
| | 00h | Vendor specific STANDARD page (subpage 0) | Page 0 format |
| 20h to 3Eh (VENDOR SPECIFIC) | 01h to FEh | Vendor specific SUBPAGE | Subpage format |
| | FFh | Return all SUBPAGES for the specified vendor specific mode page | Page 0 format for subpage 00h, subpage format for subpages 01h to FEh |
| | 00h | Return all STANDARD pages (subpage 0) | Page 0 format |
| 3Fh (Return ALL pages) | 01h to FEh | Reserved | NA |
| | FFh | Return all subpages for all mode pages | Page 0 format for subpage 00h, sub_page format for subpages 01h to FEh |

---
JEDEC Standard No. 220G  
Page 253

# JEDEC Standard No. 220G
## Page 254

### 11.4.1.2 Mode Parameter List Format

General format for reading or writing mode pages.

UFS will not implement Block Descriptor field

**Table 11.59 — UFS Mode Parameter List**

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
|          |   |   |   | Mode Parameter Header |   |   |   |   |
|          |   |   | Block Descriptor(s) |   |   |   |   |   |
|          | Mode Page(s) or Subpages or Vendor specific pages |   |   |   |   |   |   |

### 11.4.1.3 Mode Parameter Header

The mode parameter header that is used by the MODE SELECT (10) command and the MODE SENSE (10) command is defined in the following table.

**Table 11.60 — UFS Mode Parameter Header (10)**

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | (MSB) |   |   |   |   |   |   |   |
| 1 |   | MODE DATA LENGTH |   |   |   |   | (LSB) |
| 2 |   |   | MEDIUM TYPE = 00h |   |   |   |   |
| 3 |   |   | DEVICE SPECIFIC PARAMETER |   |   |   |   |
|   | WP | Reserved = 00b | DPOFUA | Reserved = 0000b |   |   |   |
| 4 |   |   | Reserved = 00h |   |   |   | LONGLBA = 0b |
| 5 |   |   | Reserved = 00h |   |   |   |   |
| 6 | (MSB) |   |   |   |   |   |   |   |
| 7 |   | BLOCK DESCRIPTOR LENGTH = 0000h |   |   | (LSB) |

When using the MODE SENSE command, the MODE DATA LENGTH field indicates the length in bytes of the following data that is available to be transferred. The mode data length does not include the number of bytes in the MODE DATA LENGTH field. When using the MODE SELECT command, this field is reserved.

# 11.4.1.4 Mode Parameter Header Detail

**Table 11.61 — Mode Parameter Header Detail**

| Byte | Bit | Description |
|------|-----|-------------|
| 0-1 | 7:0 | **MODE DATA LENGTH:** Indicates the length in bytes of data following this field that is available to transfer. This value does not include the size of this field (2 bytes). For MODE SENSE 10-byte CDB, this value will be calculated as 6 + page data bytes. |
| 2 | 7:0 | **MEDIUM TYPE:** Indicates the medium type of the device. For UFS this value shall be set to 00h, indicating Data Medium. |
| 3 | 7:0 | **DEVICE SPECIFIC PARAMETER:** Direct access device specific value.<br>When used with the MODE SELECT command, the write protect (WP) bit is reserved. When used with the MODE SENSE command, a WP bit set to one indicates that the medium is write-protected, a WP bit set to zero indicates that the medium is not write-protected⁽¹⁾.<br>When used with the MODE SELECT command, the DPOFUA bit is reserved.<br>When used with the MODE SENSE command, a DPOFUA bit set to zero indicates that the device server does not support the DPO and FUA bits.<br>When used with the MODE SENSE command, a DPOFUA bit set to one indicates that the device server supports the DPO and FUA bits |
| 6:7 | 7:0 | **BLOCK DESCRIPTOR LENGTH:** Length of block descriptor in parameter list. For UFS this value shall be 00h indicating that there is no block descriptor(s) used in the parameter list. |

**NOTE 1** The WP bit shall be set to one when the entire logical unit is write-protected by any method.

---
*JEDEC Standard No. 220G*  
*Page 255*

# 11.4.1.5 Page_0 Mode Page Format

## Table 11.62 — Page_0 Mode Page Format

| Byte | Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
|------|-------|-------|-------|-------|-------|-------|-------|-------|
| 0    | PS    | SPF (0b) |       |       | PAGE CODE |     |       |       |
| 1    |       |       |       | PAGE LENGTH (n − 1) |       |       |       |       |
| 2    |       |       |       |       |       |       |       |       |
| n    |       |       | Mode Parameters |       |       |       |       |       |

## Table 11.63 — Page 0 Format Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 0    | 7:7 | **PS:** Indicates the page parameters can be saved. When using the MODE SENSE command, the PS bit set to one indicates that the mode page may be saved by the logical unit in a nonvolatile, vendor specific location. A PS bit set to zero indicates that the device server is not able to save the supported parameters. When using the MODE SELECT command, the PS bit is reserved. |
| 0    | 6:6 | **SPF:** Indicates SUBPAGE format. When set to zero indicates that the PAGE 0 format is being used. When set to one, indicates the SUBPAGE mode page format is being used. |
| 0    | 5:0 | **PAGE CODE:** Indicates the format and parameters for particular mode page. |
| 1    | 7:0 | **PAGE LENGTH:** Indicates the size in bytes of the following mode page parameters. |
| 2:N  | 7:0 | **MODE PARAMETERS:** The contents of the indicated mode page. |

---
*JEDEC Standard No. 220G*  
*Page 256*

# 11.4.1.6 Sub_page Mode Page Format

**JEDEC Standard No. 220G**  
**Page 257**

## Table 11.64 — Sub_page Mode Page Format

| Byte | Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|-----|---|---|---|---|---|---|---|---|
| 0 | | PS | SPF (1b) | | | PAGE CODE | | | |
| 1 | | | | SUBPAGE CODE | | | | | |
| 2 | | (MSB) | | | | | | | |
| 3 | | | | PAGE LENGTH (n − 3) | | | | | (LSB) |
| 4 | | | | | | | | | |
| ⋮ | | | | Mode Parameters | | | | | |
| n | | | | | | | | | |

## Table 11.65 — Subpage Format Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 0 | 7:7 | **PS:** Indicates the page parameters can be saved. When using the MODE SENSE command, the PS bit set to one indicates that the mode page may be saved by the logical unit in a nonvolatile, vendor specific location. A PS bit set to zero indicates that the device server is not able to save the supported parameters. When using the MODE SELECT command, the PS bit is reserved. |
| 0 | 6:6 | **SPF:** Indicates SUBPAGE format. When set to zero indicates that the PAGE 0 format is being used. When set to one, indicates the SUBPAGE mode page format is being used. |
| 0 | 5:0 | **PAGE CODE:** Specifies the mode page. |
| 1 | 7:0 | **SUBPAGE CODE:** Specifies the subpage of a particular mode page. |
| 2:3 | 7:0 | **PAGE LENGTH:** Indicates the size in bytes of the following mode page parameters. |
| 4:N | 7:0 | **MODE PARAMETERS:** The contents of the indicated mode page. |