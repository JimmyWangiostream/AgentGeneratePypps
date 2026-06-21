# 11.5.4 Mode Page Policy VPD Page

The Mode Page Policy VPD page (see Table 11.75) indicates which mode page policy is in effect for each mode page supported by the logical unit.

## Table 11.75 — Mode Page Policy VPD Page

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | PERIPHERAL QUALIFIER | | | PERIPHERAL DEVICE TYPE | | | | |
| 1 | | | PAGE CODE (87h) | | | | | |
| 2 | (MSB) | | | | | | | |
| 3 | | | PAGE LENGTH (n-3) | | | | | (LSB) |
| | | Mode page policy descriptor list | | | | | | |
| 4 | | | | | | | | |
| ... | | Mode page policy descriptor [first] | | | | | | |
| 7 | | | | | | | | |
| | | ... | | | | | | |
| n-3 | | | | | | | | |
| ... | | Mode page policy descriptor [last] | | | | | | |
| n | | | | | | | | |

Each mode page policy descriptor (see Table 11.76) contains information describing the mode page policy for one or more mode pages or subpages.

## Table 11.76 — Mode Page Policy Descriptor

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | Reserved | | | POLICY PAGE CODE | | | | |
| 1 | | | POLICY SUBPAGE CODE | | | | | |
| 2 | MLUS | | Reserved | | | MODE PAGE POLICY = 00b | | |
| 3 | | | Reserved | | | | | |

The POLICY PAGE CODE field and POLICY SUBPAGE CODE field indicate the mode page and subpage to which the descriptor applies. See [SPC] for further details.

---

JEDEC Standard No. 220G
Page 267

# JEDEC Standard No. 220G
Page 268

## 11.5.4 Mode Page Policy VPD page (cont'd)

If more than one logical unit are configured in the device, a multiple logical units share (MLUS) bit set to one indicates the mode page and subpage identified by the POLICY PAGE CODE field and POLICY SUBPAGE CODE field is shared by more than one logical unit.

A MLUS bit set to zero indicates the logical unit maintains its own copy of the mode page and subpage identified by the POLICY PAGE CODE field and POLICY SUBPAGE CODE field.

Table 11.77 describes the mode page policies.

### Table 11.77 — MODE PAGE POLICY Field

| Code | Description |
|------|-------------|
| 00b  | Shared |
| 01b  | Per target port |
| 10b  | Obsolete |
| 11b  | Per I_T nexus |

NOTE    This standard defines only one target port and one initiator port.

MODE PAGE POLICY field shall be set to zero (Shared).

See [SPC] for further details about Mode Page Policy VPD page.

# 12 UFS Security

This sub-clause summarizes UFS device security features and the implementation details. These features include: Secure mode operation, data and registry protection, RPMB and reset.

## 12.1 UFS Security Feature Support Requirements

The security features defined in this standard are mandatory for all devices.

The following security features are defined: replay protected memory block (RPMB), secure mode and different types of logical unit write protection.

## 12.2 Secure Mode

### 12.2.1 Description

UFS devices will be used to store user's personal and/or corporate data information. The UFS device provides a way to remove the data permanently from the device when requested, ensuring that it cannot be retrieved using reverse engineering on the memory device.

The UFS device shall support a secure and insecure mode of operation. In the secure mode all operations that result in the removal or retiring of information on the device will purge this information in a secure manner, as outlined in 12.2.2.1, Secure Removal.

The secure mode is applied at the logical unit level, so different logical unit may have different secure modes.

---

*JEDEC Standard No. 220G*  
*Page 269*