from enum import Enum, IntEnum
from Script.api.ufs_api.defines.bit_define import BIT7, BIT8, BIT9, BIT10

class VUC088Paremeter(IntEnum):
    StopRefreshRefreshCanStillBeEnqueue = 0x0
    StartRefresh = 0x1
    DisableEnqueueInRefreshBQ = 0x4
    EnableEnqueueInRefreshBQ = 0x5
    
class VUC087VB_type(IntEnum):
    TableVB = 0x0
    HostVB = 0x1

class VU40C5CorrectedBits(IntEnum):
    DM_ERROR_UECC = 0x17F
    DM_ERROR_CECC= 0x17E
    DM_ERROR_RECC = 0x17D
    DM_ERROR_EMPT = 0x1FE
    DM_ERROR_NONE = 0xFFF
    
class VUC087Paremeter(IntEnum):
    HighPriority = 1
    MediumPriority = 2
    LowPriority = 3
    
class BookingUser(IntEnum):
    COMMON_BOOKING = 0
    MEDIA_SCAN_BOOKING_0 = 1   # refresh for bin > bin_high
    MEDIA_SCAN_BOOKING_1 = 2   # refresh for media scan result
    RD_SCAN_BOOKING_0 = 3      # Error Bit Count > Threshold on closed VB
    RD_SCAN_BOOKING_1 = 4      # RCTH counter overflow (RCTHptr[logVB] >= U32_MAX) on closed VB
    EXCEED_RC_TH_BOOKING_0 = 5 # drop for Cygnus, Read Count > Threshold on open VB
    EH_BOOKSIGNALUECC_BOOKING_0 = 6  # Host read detects CECC or UECC errors
    EH_BOOKSIGNALUECC_BOOKING_1 = 7  # drop for Cygnus, Host read detects CECC, only if Read Count < 10% of RC Threshold
    EH_FATALUECC_BOOKING = 8   # drop for Cygnus
    PURGE_REFRESH = 9
    SWL_REFRESH_LOW_GAP = 10
    APL_RELOCATE_BOOKING = 11  # drop for Cygnus
    POSTBOOT_BOOKING = 12      # drop for Cygnus
    VU_REFRESH = 13
    PSA_BOOKING = 14
    HOST_INITIATED_REFRESH = 15
    HIGH_BIN_VB_REFRESH = 16
    RD_SCAN_BOOKING_3 = 17     # Read disturb scan EPC check fail
    BFEA_SCAN_BOOKING = 18     # Refresh booked by BFEA/BFEAQ scan
    SWL_REFRESH_HIGH_GAP = 19
    XTEMP_BOOKING = 20
    MAX_BOOKING_USER_COUNT = 32  # use 5-bit for booking user; remaining bits store refresh reason
    BOOKING_DISCARD_FLAG = BIT7 
    BOOKING_IN_LP = BIT8  #Bit should enable if current VB added to Low priority queue
    BOOKING_IN_MP=BIT9  #Bit should enable if current VB added to Medium priority queue
    BOOKING_IN_HP=BIT10  #Bit should enable if current VB added to High priority queue