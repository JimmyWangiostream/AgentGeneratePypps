from Script.api.struct_helper import *
from Script.project_api.functions import print_object_info_ai
from Script.pattern.pattern_logger import logger

# Event log specific info starts at this offset in the 0x4000 buffer
SPECIFIC_LOG_INFO_OFFSET = 0x0A08


# ══════════════════════════════════════════════════════════════
# Helper: print bit-field sub-structs (like print_object_info_ai for bits)
# ══════════════════════════════════════════════════════════════
def print_bit_fields(title: str, bit_obj: BITPacketParserComposerABC) -> None:
    """Print all add_field_bit fields in a BITPacketParserComposerABC object."""
    logger.info(f"  [{title}]")
    items = sorted(
        ((name, field) for name, field in bit_obj.__dict__.items()
         if hasattr(field, "start_bit") and hasattr(field, "end_bit") and hasattr(field, "value")),
        key=lambda kv: kv[1].start_bit,
    )
    for name, field in items:
        logger.info(f"    Bit[{field.start_bit}:{field.end_bit}] {name} = {field.value} (0x{field.value:X})")


# ══════════════════════════════════════════════════════════════
# 0x3006 — DM_BookRefEventLog_t
# ══════════════════════════════════════════════════════════════

class BookRefScanBits(BITPacketParserComposerABC):
    """Last uint32_t: rdScanPage[13:0], reserved[31:14]"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.rdScanPage = self.add_field_bit(0, 13, 'little')  # read scan page, don't care
        self.reserved   = self.add_field_bit(14, 31, 'little')  # reserved, don't care


class BookRefEventLog(PacketParserComposerABC):
    """Flush event log when there Book VB to refresh (LogID=0x3006, 44 bytes)"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.log_id      = self.add_field(0, 3)      # uint32_t  0x3006
        self.rdLogVB     = self.add_field(4, 5)  # logic VB to refresh
        self.rdPhyBlk    = self.add_field(6, 7)  # physical VB to refresh
        self.blockType   = self.add_field(8, 9)      # uint16_t  0=SLC,1=TLC
        self.user        = self.add_field(10, 11)  # booking user type (COMMON_BOOKING=0 ... VU_REFRESH=13)
        self.firstFreePP = self.add_field(12, 15)  # first free PP of partial block
        self.rcCount     = self.add_field(16, 19)  # read count of the VB
        self.ecCount     = self.add_field(20, 23)  # erase count of the VB
        self.refReason   = self.add_field(24, 27)  # refresh reason (don't care)
        self.SWErr       = self.add_field(28, 31)  # SW error (don't care)
        self.bfeaBin_0   = self.add_field(32, 32)  # BFEA bin for CE 0
        self.bfeaBin_1   = self.add_field(33, 33)  # BFEA bin for CE 1
        self.bfeaBin_2   = self.add_field(34, 34)  # BFEA bin for CE 2
        self.bfeaBin_3   = self.add_field(35, 35)  # BFEA bin for CE 3
        self.bfeaBin_4   = self.add_field(36, 36)  # BFEA bin for CE 4
        self.bfeaBin_5   = self.add_field(37, 37)  # BFEA bin for CE 5
        self.bfeaBin_6   = self.add_field(38, 38)  # BFEA bin for CE 6
        self.bfeaBin_7   = self.add_field(39, 39)  # BFEA bin for CE 7
        self.packed_scan = self.add_field(40, 43)  # packed rdScanPage[13:0] + reserved[31:14]
        # bit-field sub-struct — pass absolute offset
        so = self.start_offset
        self.scan_bits   = BookRefScanBits(payload, so + 40, so + 43)

    def print_all(self) -> None:
        print_object_info_ai(self)
        print_bit_fields("scan_bits (packed_scan)", self.scan_bits)


# ══════════════════════════════════════════════════════════════
# 0x6001 — BeUeccEvent_t  (with nested BeRealUeccRefInfo)
# ══════════════════════════════════════════════════════════════

class BeUeccFlagsBits(BITPacketParserComposerABC):
    """Byte 9: withVTdata[0]:1, ueccType[4:1]:4, slcMode[7:5]:3"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.withVTdata = self.add_field_bit(0, 0, 'little')  # 1=vt data attached with this uecc event
        self.ueccType   = self.add_field_bit(1, 4, 'little')  # 0=soft, 1=fake, 2=real uecc
        self.slcMode    = self.add_field_bit(5, 7, 'little')  # 0=TLC mode, 1=SLC mode


class BeUeccPageInfoBits(BITPacketParserComposerABC):
    """Bytes 24-27: vtBufIndex[7:0], page[31:8]"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.vtBufIndex = self.add_field_bit(0, 7, 'little')  # vt buffer index (not used)
        self.page       = self.add_field_bit(8, 31, 'little')  # fail page


class BeRealUeccRefInfo(PacketParserComposerABC):
    """Nested sub-struct inside BeUeccEvent (57 bytes)"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.ueccBitmap         = self.add_field(0, 3)  # uecc bitmap for refined info
        self.initUeccBitmap     = self.add_field(4, 7)  # uecc bitmap before rain recovery
        self.partialReadParaTbl_00 = self.add_field(8, 11)  # partial read param [0][0] (0xFF=unused)
        self.partialReadParaTbl_01 = self.add_field(12, 15)  # partial read param [0][1] (0xFF=unused)
        self.partialReadParaTbl_10 = self.add_field(16, 19)  # partial read param [1][0] (0xFF=unused)
        self.partialReadParaTbl_11 = self.add_field(20, 23)  # partial read param [1][1] (0xFF=unused)
        self.lastProgBlk_00 = self.add_field(24, 25)  # last programmed block [0][0] (0xFF=unused)
        self.lastProgBlk_01 = self.add_field(26, 27)  # last programmed block [0][1] (0xFF=unused)
        self.lastProgBlk_10 = self.add_field(28, 29)  # last programmed block [1][0] (0xFF=unused)
        self.lastProgBlk_11 = self.add_field(30, 31)  # last programmed block [1][1] (0xFF=unused)
        self.lastProgPage_00 = self.add_field(32, 33)  # last programmed page [0][0] (0xFF=unused)
        self.lastProgPage_01 = self.add_field(34, 35)  # last programmed page [0][1] (0xFF=unused)
        self.lastProgPage_10 = self.add_field(36, 37)  # last programmed page [1][0] (0xFF=unused)
        self.lastProgPage_11 = self.add_field(38, 39)  # last programmed page [1][1] (0xFF=unused)
        self.isPartialBlk   = self.add_field(40, 40)  # 0=close blk, 1=partial blk
        self.partialBlkType = self.add_field(41, 41)  # 0=host blk, 1=defrag blk
        self.errType        = self.add_field(42, 42)  # 1=host read UECC, 2=fatal UECC, 3=ignore cecc, 4=gc read, 5=bbm read
        self.hostLun        = self.add_field(43, 43)  # host read LUN
        self.hostLba        = self.add_field(44, 47)  # host read LBA
        self.lba            = self.add_field(48, 51)  # logical block address
        self.seedBits       = self.add_field(52, 53)  # EC seed used in BE entry
        self.bin            = self.add_field(54, 54)  # BFEA bin
        self.isPSA          = self.add_field(55, 55)  # 0=False, 1=True (PSA)
        self.isXtemp        = self.add_field(56, 56)  # 0=False, 1=True (XTemp)


class BeUeccEvent(PacketParserComposerABC):
    """Event log for BE read UECC (LogID=0x6001, 115 bytes)"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.log_id       = self.add_field(0, 3)       # 0x6001
        self.magicNum     = self.add_field(4, 7)       # "UECC"
        self.die          = self.add_field(8, 8)  # fail die (CE)
        self.flags_packed = self.add_field(9, 9)  # packed withVTdata:1 ueccType:4 slcMode:3
        self.multiPlane   = self.add_field(10, 10)  # 0=single plane, 1=multi-plane
        self.startPlane   = self.add_field(11, 11)  # start plane of the UECC
        self.block_0      = self.add_field(12, 13)  # fail block plane 0
        self.block_1      = self.add_field(14, 15)  # fail block plane 1
        self.block_2      = self.add_field(16, 17)  # fail block plane 2
        self.block_3      = self.add_field(18, 19)  # fail block plane 3
        self.block_4      = self.add_field(20, 21)  # fail block plane 4
        self.block_5      = self.add_field(22, 23)  # fail block plane 5
        self.page_info_packed = self.add_field(24, 27)  # packed vtBufIndex:8 + page:24
        self.bufUnitSize       = self.add_field(28, 28)  # buffer unit size in 1K (0=unused)
        self.unitOffset        = self.add_field(29, 29)  # start unit offset (0=unused)
        self.len               = self.add_field(30, 30)  # data length (0=unused)
        self.temperatureInSpare = self.add_field(31, 31)  # write temperature from spare
        self.ueccBitmap         = self.add_field(32, 35)  # read uecc bitmap
        self.dataMode           = self.add_field(36, 37)  # 00=normal 01=meta-only 02=data-only (0=unused)
        self.bufAddrMode        = self.add_field(38, 39)  # 00=BM index 01=physical 02=scattered (0=unused)
        self.bufAddr            = self.add_field(40, 43)  # buffer address (0=unused)
        self.refBookingList     = self.add_field(44, 45)  # current refresh booking queue list

        so = self.start_offset
        # bit-field sub-structs
        self.flags_bits     = BeUeccFlagsBits(payload, so + 9, so + 9)
        self.page_info_bits = BeUeccPageInfoBits(payload, so + 24, so + 27)
        # nested sub-struct at offset 46 (57 bytes)
        self.realUeccInfo   = BeRealUeccRefInfo(payload, so + 46, so + 46 + 56)

        self.tailFlag      = self.add_field(103, 106)   # "TAIL"
        self.phyVB         = self.add_field(107, 108)  # UECC physical VB
        self.logVB         = self.add_field(109, 110)  # UECC logical VB
        self.ecValue       = self.add_field(111, 114)  # erase count value

    @property
    def magic_str(self) -> str:
        v = self.magicNum.value
        return "".join(chr((v >> (8 * i)) & 0xFF) for i in range(4))

    @property
    def tail_str(self) -> str:
        v = self.tailFlag.value
        return "".join(chr((v >> (8 * i)) & 0xFF) for i in range(4))

    def print_all(self) -> None:
        print_object_info_ai(self)
        print_bit_fields("flags_bits (byte 9)", self.flags_bits)
        print_bit_fields("page_info_bits (bytes 24-27)", self.page_info_bits)
        logger.info("  ── BeRealUeccRefInfo ──")
        print_object_info_ai(self.realUeccInfo)


# ══════════════════════════════════════════════════════════════
# 0x3011 — DM_RainRecoveryEventLog_t  (45 bytes, no bit fields)
# ══════════════════════════════════════════════════════════════

class RainRecoveryEventLog(PacketParserComposerABC):
    """Event log for Rain recovery (LogID=0x3011, 48 bytes)"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.log_id          = self.add_field(0, 3)  # 0x3011, fix value
        self.errblock_0      = self.add_field(4, 5)  # error block plane 0
        self.errblock_1      = self.add_field(6, 7)  # error block plane 1
        self.errblock_2      = self.add_field(8, 9)  # error block plane 2
        self.errblock_3      = self.add_field(10, 11)  # error block plane 3
        self.errblock_4      = self.add_field(12, 13)  # error block plane 4
        self.errblock_5      = self.add_field(14, 15)  # error block plane 5
        self.ueccBitmap      = self.add_field(16, 19)  # UECC bitmap in a die
        self.errType         = self.add_field(20, 21)  # 0=read UECC, 1=program fail
        self.logVB           = self.add_field(22, 23)  # logical VB (Reserved)
        self.pvb             = self.add_field(24, 25)  # L2PVBT of logVB (Reserved)
        self.die             = self.add_field(26, 27)  # die of the error
        self.pageInfo        = self.add_field(28, 29)  # page info (upper=logical_page, lower 2=lmu)
        self.recovResult     = self.add_field(30, 31)  # RAIN recovery result code
        self.openVbFlag      = self.add_field(32, 33)  # 0=close VB, 1=open VB
        self.vbType          = self.add_field(34, 35)  # 0=TLC, 1=SLC
        self.pageLine        = self.add_field(36, 37)  # physical page line of error
        self.parityPosition  = self.add_field(38, 39)  # 0=closed VB, 1=parity buffer, 2=SWAP VB
        self.abnormalUECCPhy = self.add_field(40, 43)  # abnormal UECC physical address
        self.RecGroup        = self.add_field(44, 45)  # recovery group
        self.reserved        = self.add_field(46, 47)  # reserved, don't care


# ══════════════════════════════════════════════════════════════
# 0x7002 — eventGBB_t  (32 bytes, no bit fields)
# ══════════════════════════════════════════════════════════════

class EventGBB(PacketParserComposerABC):
    """Records all grown bad block (GBB) defect events (LogID=0x7002, 32 bytes)"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.magicNum          = self.add_field(0, 3)       # 0x0026
        self.Channel           = self.add_field(4, 4)  # NAND channel
        self.CE                = self.add_field(5, 5)  # chip enable
        self.LUN               = self.add_field(6, 6)  # logical unit number
        self.pageType          = self.add_field(7, 7)  # 0=LP, 1=UP, 2=XP
        self.BlockPhysical     = self.add_field(8, 9)  # physical block address
        self.Page              = self.add_field(10, 11)  # page address
        self.reserved0         = self.add_field(12, 12)  # reserved
        self.blockType         = self.add_field(13, 13)  # 1=SLC Full 3=TLC Full 5=SLC Partial 7=TLC Partial 9=SLC Open 11=TLC Open
        self.SuperBlock        = self.add_field(14, 15)  # super block index
        self.defectType        = self.add_field(16, 16)  # 0x02=EraseFail 0x03=ProgramFail 0x04=UECC 0x05=MultiWL 0x06=SB_UECC 0x07=SelGate
        self.BFBinIndex        = self.add_field(17, 17)  # BFEA bin index
        self.ErsPgmPulseCount  = self.add_field(18, 18)  # erase/program pulse count
        self.FinalReadLevel1   = self.add_field(19, 19)  # final read level 1
        self.FinalReadLevel2   = self.add_field(20, 20)  # final read level 2
        self.FinalReadLevel3   = self.add_field(21, 21)  # final read level 3
        self.SR                = self.add_field(22, 22)  # status register value
        self.ESR               = self.add_field(23, 23)  # extended status register value
        self.reserved1         = self.add_field(24, 24)  # reserved
        self.blockPEC          = self.add_field(25, 26)  # block program erase count
        self.tempC             = self.add_field(27, 27)  # temperature in Celsius
        self.PoS               = self.add_field(28, 31)  # power on seconds


# ══════════════════════════════════════════════════════════════
# 0x7004 — RDL (Read Disturb Relocation) event  (36 bytes)
# ══════════════════════════════════════════════════════════════

class EventRDL(PacketParserComposerABC):
    """Records data/block refreshed due to read disturb relocation (LogID=0x7004, 36 bytes)"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.log_id           = self.add_field(0, 3)       # 0x7004
        self.magicNum         = self.add_field(4, 5)       # uint16_t 0x7004
        self.channel          = self.add_field(6, 6)  # NAND channel (fix=1)
        self.ce               = self.add_field(7, 7)  # scan failed CE (0xFF=no scan fail)
        self.lun              = self.add_field(8, 8)  # LUN (0xFF=no scan fail)
        self.page_type        = self.add_field(9, 9)  # 0=LP 1=UP 2=XP (0xFF=no scan fail)
        self.blockphysical    = self.add_field(10, 11)  # VB index * NUM_PLANE + plane_index
        self.page             = self.add_field(12, 13)  # scan failed page (0xFFFF=no scan fail)
        self.CW               = self.add_field(14, 14)  # scan failed frame index
        self.block_type       = self.add_field(15, 15)  # 1=SLC Full, 3=TLC Full, 5=SLC Partial, 7=TLC Partial, 9=SLC Open, 11=TLC Open
        self.superblock       = self.add_field(16, 17)  # VB index
        self.refreshtype      = self.add_field(18, 18)  # 0=no scan fail, 1=RBER>TH/UECC, 2=NDEP fail
        self.BFBinIndex       = self.add_field(19, 19)  # BFEA bin index
        self.reserved_0       = self.add_field(20, 20)  # reserved[0]
        self.reserved_1       = self.add_field(21, 21)  # reserved[1]
        self.reserved_2       = self.add_field(22, 22)  # reserved[2]
        self.reserved_3       = self.add_field(23, 23)  # reserved[3]
        self.reserved_4       = self.add_field(24, 24)  # reserved[4]
        self.reserved_5       = self.add_field(25, 25)  # reserved[5]
        self.reserved_6       = self.add_field(26, 26)  # reserved[6]
        self.reserved_7       = self.add_field(27, 27)  # reserved[7]
        self.reserved_8       = self.add_field(28, 28)  # reserved[8]
        self.blockPEC         = self.add_field(29, 30)  # PE count of VB
        self.tempC            = self.add_field(31, 31)  # temperature in Celsius
        self.PoS              = self.add_field(32, 35)  # power on seconds

# ══════════════════════════════════════════════════════════════
# 0x0007 — FFU health report event
# ══════════════════════════════════════════════════════════════
class FFUEventILog(PacketParserComposerABC):
    """Event log for FW health report (LogID=0x0007, total 19 bytes)"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.log_id   = self.add_field(0, 3)  # 0x0007, fix value
        self.eventCnt = self.add_field(4, 7)  # security event count
        self.oldVer   = self.add_field(8, 11)  # old firmware version
        self.newVer   = self.add_field(12, 15)  # new firmware version
        self.STCopySN = self.add_field(16, 16)  # SN value of the STC copy
        self.serialNo = self.add_field(17, 17)  # CIS serial number
        self.logType  = self.add_field(18, 18)  # 0=sig1 fail, 1=sig2 fail; 0x00=mcode corrupt, 0xFF=ok
    def print_all(self) -> None:
        print_object_info_ai(self)


# ══════════════════════════════════════════════════════════════
# 0x3005 — DmCisBankEvent_t  (25 bytes, no bit fields)
# ══════════════════════════════════════════════════════════════

class CisBankEvent(PacketParserComposerABC):
    """Event log for read UECC in bank (LogID=0x3005, 29 bytes)"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.log_id          = self.add_field(0, 3)       # 0x3005
        self.isSync          = self.add_field(4, 4)  # is sync read (sync read always)
        self.bankToLoad      = self.add_field(5, 5)  # bank to load index
        self.FWCopyID        = self.add_field(6, 6)  # firmware copy ID
        self.bankMachineId   = self.add_field(7, 7)  # bank machine ID (die)
        self.bankReadErrCode = self.add_field(8, 11)  # bank read error code (0=no UECC)
        self.bankHmacErr     = self.add_field(12, 12)  # bank HMAC error flag
        self.wEC_0           = self.add_field(13, 16)  # word error count [0]
        self.wEC_1           = self.add_field(17, 20)  # word error count [1]
        self.wEC_2           = self.add_field(21, 24)  # word error count [2]
        self.wEC_3           = self.add_field(25, 28)  # word error count [3]


# ══════════════════════════════════════════════════════════════
# 0x6002 — BeBBEvent_t  (76 bytes)
# ══════════════════════════════════════════════════════════════

class BeBBFlagsBits(BITPacketParserComposerABC):
    """Byte 9: opType[3:0], slcMode[7:4]"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.opType  = self.add_field_bit(0, 3, 'little')  # 0=ERASE, 1=Write, 2=Read, 3=Sync
        self.slcMode = self.add_field_bit(4, 7, 'little')  # 0=TLC, 1=SLC


class BeBBPageErrBits(BITPacketParserComposerABC):
    """Bytes 28-31: page[23:0], errType[31:24]"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.page    = self.add_field_bit(0, 23, 'little')  # fail page
        self.errType = self.add_field_bit(24, 31, 'little')  # Error handler type (ErrorHandler_em)


class BeBBEsr1Bits(BITPacketParserComposerABC):
    """Bytes 51-54: esrPresent[7:0], esrPlaneLow[31:8]"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.esrPresent   = self.add_field_bit(0, 7, 'little')  # ESR present bits
        self.esrPlaneLow  = self.add_field_bit(8, 31, 'little')  # ESR plane low (don't care)


class BeBBEsr2Bits(BITPacketParserComposerABC):
    """Bytes 55-58: esrPlaneHigh[23:0], reserved[31:24]"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.esrPlaneHigh = self.add_field_bit(0, 23, 'little')  # ESR plane high (don't care)
        self.reserved     = self.add_field_bit(24, 31, 'little')  # reserved


class BeBBEvent(PacketParserComposerABC):
    """Event log for bad block happened (LogID=0x6002, 76 bytes)"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.log_id          = self.add_field(0, 3)       # 0x6002
        self.magicNum        = self.add_field(4, 7)       # "BBLK"
        self.die             = self.add_field(8, 8)  # fail die (CE)
        self.flags_packed    = self.add_field(9, 9)  # packed opType:4 + slcMode:4
        self.multiPlane      = self.add_field(10, 10)  # 0=single plane, 1=multi-plane
        self.startPlane      = self.add_field(11, 11)  # start plane
        self.allPlaneFail    = self.add_field(12, 12)  # all plane fail (don't care)
        self.failedPlane     = self.add_field(13, 13)  # failed plane index
        self.failedSubType   = self.add_field(14, 14)  # failed sub-type (not used, for SGM)
        self.bufAddrMode     = self.add_field(15, 15)  # buffer addr mode (don't care)
        self.block_0         = self.add_field(16, 17)  # fail block plane 0
        self.block_1         = self.add_field(18, 19)  # fail block plane 1
        self.block_2         = self.add_field(20, 21)  # fail block plane 2
        self.block_3         = self.add_field(22, 23)  # fail block plane 3
        self.block_4         = self.add_field(24, 25)  # fail block plane 4
        self.block_5         = self.add_field(26, 27)  # fail block plane 5
        self.page_err_packed = self.add_field(28, 31)  # packed page:24 + errType:8
        self.refBookingList  = self.add_field(32, 33)  # current refresh booking queue list
        self.errTypeOrigin   = self.add_field(34, 34)  # original error type (don't care)
        self.touchUpPlnBit_0 = self.add_field(35, 35)  # SGS related (not used)
        self.touchUpPlnBit_1 = self.add_field(36, 36)  # SGS related (not used)
        self.touchUpPlnBit_2 = self.add_field(37, 37)  # SGS related (not used)
        self.touchUpPlnBit_3 = self.add_field(38, 38)  # SGS related (not used)
        self.dataMode        = self.add_field(39, 39)  # data mode (don't care)
        self.scanSG          = self.add_field(40, 40)  # SG scan flag (not used, for SGM)
        self.seedBits        = self.add_field(41, 42)  # EC seed used in BE entry
        self.tailFlag        = self.add_field(43, 46)  # "TAIL" magic
        self.blockEC         = self.add_field(47, 50)  # block erase count
        self.esr1_packed     = self.add_field(51, 54)  # packed esrPresent:8 + esrPlaneLow:24
        self.esr2_packed     = self.add_field(55, 58)  # packed esrPlaneHigh:24 + reserved:8
        self.failBitmap      = self.add_field(59, 62)  # fail bitmap
        self.driveRc_0       = self.add_field(63, 66)  # drive RC [0] (don't care)
        self.driveRc_1       = self.add_field(67, 70)  # drive RC [1] (don't care)
        self.phyVB           = self.add_field(71, 72)  # physical VB (logical VB * 6 + plane)
        self.logVB           = self.add_field(73, 74)  # logical VB
        self.dppmBitmap      = self.add_field(75, 75)  # DPPM bitmap (not used, for SGM)

        so = self.start_offset
        # bit-field sub-structs
        self.flags_bits     = BeBBFlagsBits(payload, so + 9, so + 9)
        self.page_err_bits  = BeBBPageErrBits(payload, so + 28, so + 31)
        self.esr1_bits      = BeBBEsr1Bits(payload, so + 51, so + 54)
        self.esr2_bits      = BeBBEsr2Bits(payload, so + 55, so + 58)

    @property
    def magic_str(self) -> str:
        v = self.magicNum.value
        return "".join(chr((v >> (8 * i)) & 0xFF) for i in range(4))

    @property
    def tail_str(self) -> str:
        v = self.tailFlag.value
        return "".join(chr((v >> (8 * i)) & 0xFF) for i in range(4))

    def print_all(self) -> None:
        print_object_info_ai(self)
        print_bit_fields("flags_bits (byte 9)", self.flags_bits)
        print_bit_fields("page_err_bits (bytes 28-31)", self.page_err_bits)
        print_bit_fields("esr1_bits (bytes 51-54)", self.esr1_bits)
        print_bit_fields("esr2_bits (bytes 55-58)", self.esr2_bits)


# ══════════════════════════════════════════════════════════════
# 0xC001 — SerEventStoreInfo_t  (20 bytes, has bit fields)
# ══════════════════════════════════════════════════════════════

class SerStoreByte7Bits(BITPacketParserComposerABC):
    """Byte 7: serBankID[3:0], serTypeError[5:4], serFabEType[7:6]"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.serBankID    = self.add_field_bit(0, 3, 'little')  # bank ID
        self.serTypeError = self.add_field_bit(4, 5, 'little')  # 0=INVALID, 1=TRANS, 2=SOFT, 3=PERM
        self.serFabEType  = self.add_field_bit(6, 7, 'little')  # ECC type: CECC/UECC/PARITY


class SerStoreOffsetBits(BITPacketParserComposerABC):
    """Bytes 8-11: serOffsetAddress[21:0], serEventID[28:22], serEccType[29], reserved[31:30]"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.serOffsetAddress = self.add_field_bit(0, 21, 'little')  # offset address of module where ECC happened
        self.serEventID       = self.add_field_bit(22, 28, 'little')  # ECC event ID
        self.serEccType       = self.add_field_bit(29, 29, 'little')  # ECC type: 0=CECC, 1=UECC
        self.reserved         = self.add_field_bit(30, 31, 'little')  # reserved


class SerStoreCpuBits(BITPacketParserComposerABC):
    """Bytes 12-15: ser_CpuCore[1:0], reserved[31:2]"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.ser_CpuCore = self.add_field_bit(0, 1, 'little')  # CPU Core: PMU/HS/EM0/EM1
        self.reserved    = self.add_field_bit(2, 31, 'little')  # reserved


class SerEventStoreInfo(PacketParserComposerABC):
    """Event log flush/record for SER event (LogID=0xC001, 20 bytes)"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.magicNum     = self.add_field(0, 3)        # "SERE"
        self.serEccCnt    = self.add_field(4, 5)  # ECC count
        self.serIntNum    = self.add_field(6, 6)  # ISR number
        self.byte7_packed = self.add_field(7, 7)  # packed serBankID:4 serTypeError:2 serFabEType:2
        self.offset_packed = self.add_field(8, 11)  # packed offset:22 eventID:7 eccType:1 reserved:2
        self.cpu_packed   = self.add_field(12, 15)  # packed ser_CpuCore:2 reserved:30
        self.tailFlag     = self.add_field(16, 19)  # "TAIL" magic

        so = self.start_offset
        self.byte7_bits   = SerStoreByte7Bits(payload, so + 7, so + 7)
        self.offset_bits  = SerStoreOffsetBits(payload, so + 8, so + 11)
        self.cpu_bits     = SerStoreCpuBits(payload, so + 12, so + 15)

    @property
    def magic_str(self) -> str:
        v = self.magicNum.value
        return "".join(chr((v >> (8 * i)) & 0xFF) for i in range(4))

    @property
    def tail_str(self) -> str:
        v = self.tailFlag.value
        return "".join(chr((v >> (8 * i)) & 0xFF) for i in range(4))

    def print_all(self) -> None:
        print_object_info_ai(self)
        print_bit_fields("byte7_bits (byte 7)", self.byte7_bits)
        print_bit_fields("offset_bits (bytes 8-11)", self.offset_bits)
        print_bit_fields("cpu_bits (bytes 12-15)", self.cpu_bits)


# ══════════════════════════════════════════════════════════════
# 0x300C — DM_InitUECCEventLog_t  (20 bytes, no bit fields)
# ══════════════════════════════════════════════════════════════

class InitUECCEventLog(PacketParserComposerABC):
    """Event for assert happened during power on (LogID=0x300C, 20 bytes)"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.log_id        = self.add_field(0, 3)       # 0x300C
        self.ppa           = self.add_field(4, 7)  # UECC physical address
        self.logVB         = self.add_field(8, 9)  # UECC logical VB
        self.phyVB         = self.add_field(10, 11)  # UECC physical VB
        self.block         = self.add_field(12, 13)  # UECC physical block
        self.planeIdx      = self.add_field(14, 15)  # UECC plane index
        self.pageline      = self.add_field(16, 17)  # UECC physical page
        self.vpInPageLine  = self.add_field(18, 19)  # first UECC 4K offset in page line


# ══════════════════════════════════════════════════════════════
# 0x300E — DM_RefCompleteEventLog_t  (20 bytes, no bit fields)
# ══════════════════════════════════════════════════════════════

class RefCompleteEventLog(PacketParserComposerABC):
    """Flush log when block refresh is completed (LogID=0x300E, 20 bytes)"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.log_id         = self.add_field(0, 3)       # 0x300E
        self.isAbort        = self.add_field(4, 4)  # 0=False, 1=True (refresh aborted)
        self.reserved       = self.add_field(5, 5)  # reserved for debug
        self.srcLogicVB     = self.add_field(6, 7)  # refresh src logic VB
        self.srcPhysicalVB  = self.add_field(8, 9)  # refresh src physical VB
        self.destLogicVB    = self.add_field(10, 11)  # refresh dest logic VB
        self.destPhysicalVB = self.add_field(12, 13)  # refresh dest physical VB
        self.refBookingList = self.add_field(14, 15)  # booking queue type
        self.sliceNumFG     = self.add_field(16, 17)  # slice number FG completed
        self.sliceNumBG     = self.add_field(18, 19)  # slice number BG completed


# ══════════════════════════════════════════════════════════════
# 0x3051 — DM_RefStartEventLog_t  (14 bytes, no bit fields)
# ══════════════════════════════════════════════════════════════

class RefStartEventLog(PacketParserComposerABC):
    """Flush log when Block Refresh starts (LogID=0x3051, 16 bytes)"""
    def __init__(self, payload: bytearray, start_offset: int = AUTO_OFFSET,
                 end_offset: int = AUTO_OFFSET) -> None:
        super().__init__(payload, start_offset, end_offset)
        self.log_id          = self.add_field(0, 3)       # 0x3051
        self.timestamp       = self.add_field(4, 7)  # time stamp (ms)
        self.srcLogicVB      = self.add_field(8, 9)  # refresh src logic VB
        self.srcPhysicalVB   = self.add_field(10, 11)  # refresh src physical VB
        self.temperature     = self.add_field(12, 12)  # NAND temperature
        self.isOppositeRisky = self.add_field(13, 13)  # is opposite risky flag
        self.reserved        = self.add_field(14, 15)  # reserved, don't care