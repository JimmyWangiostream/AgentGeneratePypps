# JEDEC Standard No. 220G
Page 7

## 4 Introduction

Universal Flash Storage (UFS) is a simple, high performance, mass storage device with a serial interface. It is primarily for use in mobile systems, between host processing and mass storage memory devices. The following is a summary of the UFS device features.

### 4.1 General Features

• **Target performance**
  ○ High speed GEARs (1)
    ▪ Support for GEAR1 is mandatory
    ▪ Support for GEAR2 is mandatory
    ▪ Support for GEAR3 is mandatory
    ▪ Support for GEAR4 is mandatory
    ▪ Support for GEAR5 is mandatory

• **Target host applications**
  ○ Mobile phone, UMPC, DSC, PMP, MP3 and any other applications that require mass storage, bootable mass storage, and external card

• **Target device types**
  ○ External card
  ○ Embedded device
    ▪ Mass storage and bootable mass storage
  ○ Future expansion of device class types
    ▪ I/O devices, camera, wireless, … , etc.

• **Topology**
  ○ One device per UFS port.

• **UFS Layering**
  ○ UFS Command Set Layer (UCS)
    ▪ Simplified SCSI command set based on SBC and SPC. UFS will not modify these SBC and SPC Compliant commands. Option for defining UFS Native command and future extension exist.
  ○ UFS Transport Protocol Layer (UTP)
    ▪ JEDEC to define the supported protocol layer, i.e., UTP for SCSI. This does not exclude the support of other protocol in UFS Transport Protocol Layer.
  ○ UFS Interconnect Layer (UIC)
    ▪ MIPI UniPro® [MIPI-UniPro] is adopted for data link layer
    ▪ MIPI M-PHY® [MIPI-M-PHY ] is adopted for physical layer

NOTE 1 See 6.4.1 for details.

# JEDEC Standard No. 220G
Page 8

## 4.2 Interface Features

• Three power supplies
  ○ VCCQ power supply: 1.2 V (nominal)
  ○ VCCQ2 power supply: 1.8 V (nominal)
  ○ VCC power supply: 2.5 V (nominal)

• Signaling as defined by [MIPI-M-PHY]
  ○ 400 or 620 mVp (not terminated)
  ○ 200 or 310 mVp (terminated)

• 8b10b line coding, as defined by MIPI M-PHY

• High reliability – BER under 10⁻¹²

• Two signaling schemes
  ○ Low-speed mode with PWM signaling scheme
  ○ High-Speed burst mode

• Multiple gears defined for High-Speed mode

• Only Gear 1 supported in Low Speed mode

• Adapt (M-PHY® versions 4.1 and above)
  ○ M-RX equalizer training to adapt to the channel characteristic

## 4.3 Functional Features

UFS functional features are NAND management features. These include

• Similar functional features as eMMC
• Boot Operation Mode
• Multiple logical units with configurable characteristics
• Replay Protected Memory Block (RPMB)
• Reliable write operation
• Background operations
• Secure operations, Purge and Erase to enhance data security
• Write Protection options, including Permanent and Power-On Write Protection
• Signed access to a Replay Protected Memory Block
• HW Reset Signal
• Task management operations
• Power management operations