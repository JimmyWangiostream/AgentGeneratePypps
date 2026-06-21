---
type: source
title: "ProNoun — UFS System Terminology"
tags: [pronoun, terminology, glossary]
ingested: 2026-06-21
updated: 2026-06-21
entities: [lun, write-booster]
concepts: [psa, power-management, background-operations]
---

# ProNoun — UFS System Terminology

Canonical glossary of UFS system terminology used across all Pattern Code, TC flows, and logs. Reference this when a log or TC contains an unfamiliar abbreviation.

## Core Storage Terms

| Term | Full Name | Meaning |
|------|-----------|---------|
| **UFS** | Universal Flash Storage | The embedded flash storage system and protocol |
| **GC** | Garbage Collection | Internal UFS background process for reclaiming invalid data |
| **FTL** | Flash Translation Layer | Maps logical addresses to physical flash addresses |
| **WL** | Wear Leveling | Distributes writes evenly to extend flash lifespan |
| **LUN** | Logical Unit Number | A logical storage partition within UFS |
| **BKOPS** | Background Operations | UFS background maintenance tasks (GC, WL, etc.) |
| **NAND** | — | Physical flash memory storing actual data |
| **SLC** | Single-Level Cell | Fast, durable NAND type |
| **MLC** | Multi-Level Cell | Higher density NAND |
| **TLC** | Triple-Level Cell | Even higher density, shorter write endurance |
| **WB** | Write Booster | TLC/QLC region used in SLC mode for performance |
| **EOL** | End Of Life | Device near or at storage lifespan limit |

## Protocol / Link Terms

| Term | Full Name | Meaning |
|------|-----------|---------|
| **H8 / Hibern8** | Hibernate | UFS Link hibernate power-saving state |
| **UIC** | UFS Interconnect Command | Commands for controlling UFS link |
| **PA** | Physical Adapter | UFS physical layer settings/state |
| **DL** | Data Link Layer | Protocol layer ensuring reliable data transfer |
| **QD** | Queue Depth | Number of simultaneous I/O requests on the device |
| **Link Startup** | — | UFS host-device connection establishment flow |
| **Power Mode Change** | — | UFS switching between performance/power-saving modes |

## Reliability / Debug Terms

| Term | Meaning |
|------|---------|
| **Thermal Throttling** | Auto performance reduction due to overtemperature |
| **Read Disturb** | Data reliability issue from frequent reads |
| **Flush** | Force UFS to write cached data to NAND |

## RPMB Security Terms

| Term | Full Name | Meaning |
|------|-----------|---------|
| **SPO** | Security Protocol Out | RPMB-related SCSI command |
| **SPI** | Security Protocol In | RPMB-related SCSI command |

## SDK / BG Status Codes

| Term | Meaning |
|------|---------|
| **BG_Step** | SDK-defined CMD send state |
| **BG_Error** | SDK-defined post-send error |
| **BG_Sub_Error** | SDK-defined error detail |
| **BG_SK** | Sense Key received after CMD |
| **BG_ASC** | ASC received after CMD |

## DCMD Codes

| DCMD | Code | Name | Purpose |
|------|------|------|---------|
| DCMD0 | 0x00 | DOUT_DIN_CNT_STOP | DOUT and DIN stop test |
| DCMD1 | 0x01 | PAUSE_TASK_MNGT | RTT pause test |
| DCMD2 | 0x02 | OVER_UNDER_FLOW | Overflow / underflow test |
| DCMD3 | 0x03 | BUS_IDLE_DET | Bus idle detection |
| DCMD4 | 0x04 | UNIPRO_ERROR_INJECT | UniPro error injection |
| DCMD5 | 0x05 | MEASURE_INIT_FLOW | Device initial flow |
| DCMD6 | 0x06 | SSU_HIBERNATE_FLOW | SSU and Hibernate test |
| DCMD7 | 0x07 | INTERRUPT_DEBUG | SPOR test |
| DCMD8 | 0x08 | INIT_SPOR_DEBUG | Initial flow + SPOR (timer type) |
| DCMD9 | 0x09 | PURGE_SPOR_DEBUG | SPOR test for device purge |
| DCMD10 | 0x0A | RESP_EXE_DEBUG | Receive response + execute process 1 & 2 |
| DCMD11 | 0x0B | SUSPEND_TEST_DEBUG | Suspend stress test |
| DCMD12 | 0x0C | LINK_SPEED_STRESS_DEBUG | Link and speed change stress loop |
| DCMD13 | 0x0D | TIMEOUT_SETTING | Set/Get SDK timeout |
| DCMD14 | 0x0E | POWER_CHANGE_STRESS | Power change stress (speed change + hibernate) |
| DCMD15 | 0x0F | Reserved | — |
| DCMD16 | 0x10 | GPIO_DEBUG | Set GPIO value |
| DCMD17 | 0x11 | DME_ERROR_DEBUG | DME Error Count debug |
| DCMD19 | 0x13 | BKOPS_SPOR_DEBUG | Detect BKOPS and execute SPOR |
| DCMD20 | 0x14 | KEEP_SEND_CMD_DEBUG | Prevent idle performance drop (auto-send Read Flag) |
| DCMD21 | 0x15 | Inactive_HPB_Table_debug | Inactive Tester HPB Region |
| DCMD23 | 0x17 | ADVANCED_OPTION_DEBUG | Toggle switch for special requirements |

## Where This Fits

Touches: [[lun]], [[write-booster]], [[psa]], [[power-management]], [[background-operations]]
