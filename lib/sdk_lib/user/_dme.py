from ._sdk_base import _SDKLibProtocol
from .. import _hal
from . import log_callback as logger
from ._error_code import dme_error_code_table
from enum import Enum, auto

class DMETarget(Enum):
    LOCAL = 0x00
    PEER = 0x80

class AttrSetType(Enum):
    NORMAL = 0
    STATIC = 1

class LaneNumberSelect(Enum):
    SELECTOR_IDX_NONE = 0
    TX_LANE0_SELECTOR = 0
    TX_LANE1_SELECTOR = 1
    TX_LANE2_SELECTOR = 2
    TX_LANE3_SELECTOR = 3
    RX_LANE0_SELECTOR = 4
    RX_LANE1_SELECTOR = 5
    RX_LANE2_SELECTOR = 6
    RX_LANE3_SELECTOR = 7

class MPHY_Attributes(Enum):
    MPHY_TX_HSMODE_Cap = 0x01
    MPHY_TX_HSGEAR_Cap = 0x02
    MPHY_TX_PWMG0_Cap = 0x03
    MPHY_TX_PWMGEAR_Cap = 0x04
    MPHY_TX_Amplitude_Cap = 0x05
    MPHY_TX_ExternalSYNC_Cap = 0x06
    MPHY_TX_HS_Unter_LINE_Drive_Cap = 0x07
    MPHY_TX_LS_Ter_LINE_Drive_Cap = 0x08
    MPHY_TX_Min_SLEEP_NoConfig_Time_Cap = 0x09
    MPHY_TX_Min_STALL_NoConfig_Time_Cap = 0x0A
    MPHY_TX_Min_SAVE_Config_Time_Cap = 0x0B
    MPHY_TX_REF_CLOCK_SHARED_Cap = 0x0C
    MPHY_TX_PHY_MajorMinor_Release_Cap = 0x0D
    MPHY_TX_PHY_Editorial_Release_Cap = 0x0E
    MPHY_TX_Hibern8Time_Cap = 0x0F
    MPHY_TX_Advanced_Granularity_Cap = 0x10
    MPHY_TX_Advanced_Hibern8Time_Cap = 0x11
    MPHY_TX_HS_Equalizer_Setting_Cap = 0x12
    MPHY_TX_MODE = 0x21
    MPHY_TX_HSRATE_Series = 0x22
    MPHY_TX_HSGEAR = 0x23
    MPHY_TX_PWMGEAR = 0x24
    MPHY_TX_Amplitude = 0x25
    MPHY_TX_HS_SlewRate = 0x26
    MPHY_TX_SYNC_Source = 0x27
    MPHY_TX_HS_SYNC_Len = 0x28
    MPHY_TX_HS_PREPARE_Len = 0x29
    MPHY_TX_LS_PREPARE_Len = 0x2A
    MPHY_TX_HIBERN8_Control = 0x2B
    MPHY_TX_LCC_Enable = 0x2C
    MPHY_TX_PWM_BURST_Closure_Ext = 0x2D
    MPHY_TX_BYPASS_8B10B_Enable = 0x2E
    MPHY_TX_DRIVER_POLARITY = 0x2F
    MPHY_TX_HS_Unterminated_LINE_Drive_Enable = 0x30
    MPHY_TX_LS_Terminated_LINE_Drive_Enable = 0x31
    MPHY_TX_LCC_Sequencer = 0x32
    MPHY_TX_Min_ActivateTime = 0x33
    MPHY_TX_PWM_G6_G7_SYNC_Len = 0x34

    MPHY_TX_HS_ADAPT_LENGTH = 0x3A

    MPHY_TX_FSM_STATE = 0x41

    # OMC attributes
    MPHY_MC_Output_Amplitude = 0x61
    MPHY_MC_HS_Unterminated_Enable = 0x62
    MPHY_MC_LS_Terminated_Enable = 0x63
    MPHY_MC_HS_Unterminated_LINE_Drive_Enable = 0x64
    MPHY_MC_LS_Terminated_LINE_Drive_Enable = 0x65

    # M-RX Capability attributes
    MPHY_RX_HSMODE_Cap = 0x81
    MPHY_RX_HSGEAR_Cap = 0x82
    MPHY_RX_PWMG0_Cap = 0x83
    MPHY_RX_PWMGEAR_Cap = 0x84
    MPHY_RX_HS_Unterminated_Cap = 0x85
    MPHY_RX_LS_Terminated_Cap = 0x86
    MPHY_RX_Min_SLEEP_NoCfg_Time_Cap = 0x87 # RX_Min_SLEEP_NoConfig_Time_Capability
    MPHY_RX_Min_STALL_NoCfg_Time_Cap = 0x88
    MPHY_RX_Min_SAVE_Cfg_Time_Cap = 0x89
    MPHY_RX_REF_CLOCK_SHARED_Cap = 0x8A
    MPHY_RX_HS_G1_SYNC_LENGTH_Cap = 0x8B
    MPHY_RX_HS_G1_PREPARE_LENGTH_Cap = 0x8C
    MPHY_RX_LS_PREPARE_LENGTH_Cap = 0x8D
    MPHY_RX_PWM_Burst_Closure_Len_Cap = 0x8E
    MPHY_RX_Min_ActivateTime_Cap = 0x8F
    MPHY_RX_PHY_MajorMinor_Release_Cap = 0x90
    MPHY_RX_PHY_Editorial_Release_Cap = 0x91
    MPHY_RX_Hibern8Time_Cap = 0x92
    MPHY_RX_PWM_G6_G7_SYNC_Len_Cap = 0x93
    MPHY_RX_HS_G2_SYNC_Len_Cap = 0x94
    MPHY_RX_HS_G3_SYNC_Len_Cap = 0x95
    MPHY_RX_HS_G2_PREPARE_Len_Cap = 0x96
    MPHY_RX_HS_G3_PREPARE_Len_Cap = 0x97
    MPHY_RX_Advanced_Granularity_Cap = 0x98
    MPHY_RX_Advanced_Hibern8Time_Cap = 0x99
    MPHY_RX_Advanced_Min_ActivateTime_Cap = 0x9A
    MPHY_RX_MODE = 0xA1
    MPHY_RX_HSRATE_Series = 0xA2
    MPHY_RX_HSGEAR = 0xA3
    MPHY_RX_PWMGEAR = 0xA4
    MPHY_RX_LS_Terminated_Enable = 0xA5
    MPHY_RX_HS_Unterminated_Enable = 0xA6
    MPHY_RX_Enter_HIBERN8 = 0xA7
    MPHY_RX_BYPASS_8B10B_Enable = 0xA8
    MPHY_RX_Termination_Force_Enable = 0xA9

    MPHY_RX_ADAPT_Control = 0xAA

    MPHY_RX_FSM_STATE = 0xC1

class PHYAdapterAttributes(Enum):
    PHY_Type = 0x1500            # static, MPHY = 1
    AvailTxDataLanes = 0x1520    # static
    AvailRxDataLanes = 0x1540    # static
    MinRxTrailingClocks = 0x1543 # static, 0~255
    TxHsG1SyncLength = 0x1552    # r/w, bit[7:6]:0~1, bit[5:0]=0~15
    TxHsG1PrepareLength = 0x1553 # r/w, 0~15
    TxHsG2SyncLength = 0x1554    # r/w, bit[7:6]:0~1, bit[5:0]=0~15
    TxHsG2PrepareLength = 0x1555 # r/w, 0~15
    TxHsG3SyncLength = 0x1556    # r/w, bit[7:6]:0~1, bit[5:0]=0~15
    TxHsG3PrepareLength = 0x1557 # r/w, 0~15
    TxMk2Extension = 0x155A      # r/w,  0= unsupported, 1=supported
    PeerScrambling = 0x155B      # r/w, 0= unsupported, 1=supported
    TxSkip = 0x155C              # r/w, 0= not require, 1=require
    TXSKIPPERIOD = 0x155D
    LOCAL_TX_LCC_ENABLE = 0x155E
    PEER_TX_LCC_ENABLE = 0x155F
    ActiveTxDataLanes = 0x1560 # r/w
    ConnectedTxDataLanes = 0x1561
    TxTrailingClocks = 0x1564 #r/w,  0~255
    TxPWRStatus = 0x1567      # read, 0= off_state, 1= fast_state, 2=slow_state, 3=hibernate_state, 4=sleep_state
    TxGear = 0x1568           # r/w, PWM_G1~7=1~7, HS_G1~3 = 1~3
    TxTermination = 0x1569
    HSSeries = 0x156A
    PWRMode = 0x1571          # bit[3:0] = TX, bit[7:4] = Rx, 1= fast_state, 2=slow_state, 4= fastAuto_mode, 5=SlowAuto_mode, 7=Unchanged

    ActiveRxDataLanes = 0x1580 # r/w
    ConnectedRxDataLanes = 0x1581
    RxPWRStatus = 0x1582   # r, 0= off_state, 1= fast_state, 2=slow_state, 3=hibernate_state, 4=sleep_state
    RxGear = 0x1583        # r/w, PWM_G1~7=1~7, HS_G1~3 = 1~3
    RxTermination = 0x1584 # r/w, 0=off, 1=on
    Scrambling = 0x1585    # r/w, 0=off, 1=on
    MaxRxPWMGear = 0x1586  # r/w, max. RX low speed Gears, G1~7 = 1~7
    MaxRxHSGear = 0x1587   # r/w, 0= no_HS, 1~3 = HS_G1~3
    PACPREQTIMEOUT = 0x1590
    PACPREQEOBTIMEOUT = 0x1591
    RemoteVerInfo = 0x15A0 # r, peer device version information
    LOGICALLANEMAP = 0x15A1
    SleepNoConfigTime = 0x15A2
    StallNoConfigTime = 0x15A3
    SaveConfigTime = 0x15A4
    RxHSUnterminationCap = 0x15A5
    RxLSTerminationCap = 0x15A6
    Hibern8Time = 0x15A7 # r/w, 0~10000
    TActivate = 0x15A8   # r/w, 1~10000
    LocalVerInfo = 0x15A9
    GRANULARITY = 0x15AA
    MK2ExtensionGuradBand = 0x15AB
    PWRModeUserData0 = 0x15B0
    PWRModeUserData1 = 0x15B1
    PWRModeUserData2 = 0x15B2
    PWRModeUserData3 = 0x15B3
    PWRModeUserData4 = 0x15B4
    PWRModeUserData5 = 0x15B5
    PWRModeUserData6 = 0x15B6
    PWRModeUserData7 = 0x15B7
    PWRModeUserData8 = 0x15B8
    PWRModeUserData9 = 0x15B9
    PWRModeUserDataA = 0x15BA
    PWRModeUserDataB = 0x15BB
    PACPFrameCount = 0x15C0
    PACPErrorCount = 0x15C1
    PHYTestControl = 0x15C2
    TxHsG4SyncLength = 0x15D0    # r/w, bit[7:6]:0~1, bit[5:0]=0~15
    TxHsG4PrepareLength = 0x15D1 # r/w, 0~15
    PeerRxHsAdaptRefresh = 0x15D2
    PeerRxHsAdaptInitial = 0x15D3
    TxHsAdaptType = 0x15D4
    AdaptAfterLRSTInPA_INIT = 0x15D5

    #PHISON define, out of spec.
    ERR_LAYER_NUM_CODE = 0x5006

class DME_Attribute(Enum):
        DDBL1_Revision = 0x5000
        DDBL1_Level = 0x5001
        DDBL1_DeviceClass = 0x5002
        DDBL1_ManufacturerID = 0x5003
        DDBL1_ProductID = 0x5004
        DDBL1_Length = 0x5005

        TX_DATA_OFL = 0x5100
        TX_NAC_RECEIVED = 0x5101
        X_QoS_COUNT = 0x5102
        TX_DL_LM_ERROR = 0x5103

        RX_DATA_OFL = 0x5110
        RX_CRC_ERROR = 0x5111
        RX_QoS_COUNT = 0x5112
        RX_DL_LM_ERROR = 0x5113
        TXRX_DATA_OFL = 0x5120
        TXRX_PA_INIT_REQUEST = 0x5121
        TXRX_QoS_COUNT = 0x5122
        TXRX_DL_LM_ERROR = 0x5123
        QoS_ENABLE = 0x5130
        QoS_STATUS = 0x5131

        NES_ERROR_CNT = 0x8200 #PPS NES Used
        DUMMY_ATTR_SIM_POWER_PLACE = 0x8201 #PPS Sim Power Used
        DUMMY_ATTR_SIM_POWER_COND = 0x8202
        INTERRUPT_DEVICE = 0x8204 #Device DME interrupt

class DMEConfigResult(Enum):
    SUCCESS = 0
    INVALID_MIB_ATT = 1
    INVALID_MIB_ATT_VALUE = 2
    READ_ONLY_MIB_ATT = 3
    WRITE_ONLY_MIB_ATT = 4
    BAD_INDEX = 5
    LOCKED_MIB_ATT = 6
    BAD_TEST_FAEATURE_INDEX = 7
    PEER_COMMUNICATION_FAIL = 8
    BUSY = 9
    FAILURE = 10
    TIME_OUT_TESTER_FW = 0x80

class DMEReqMODE(Enum):
    EndPointReset = 1
    UP_Reset = auto()
    UPStack_Reset = auto()
    UPStack_Enable = auto()
    Test_Mode = auto()
    PEET_SET_CNF_OFF = auto()
    MPHY_RESE = auto()

class DMEReg(Enum):
    PCS = 0 # ps2807
    PMA0 = auto() # ps2807
    PMA1 = auto() # ps2807
    MPHY_INFO = auto() # ps2808

class _SDKLibDmeMixin(_SDKLibProtocol):
    def dme_set(self, attr_set_type: int, mib_val: int, sel: int, mib_attr: int):
        apb_result = 0
        apb_result  = _hal.dme_set(self._dll, attr_set_type, mib_val, sel, mib_attr)
        if apb_result != 0:
            _hal.handle_error_code(apb_result, dme_error_code_table , "dme_set")

    def dme_get(self, attr_get_type: int, sel: int, mib_attr: int) -> int:
        apl_result, apl_val  = _hal.dme_get(self._dll, attr_get_type, sel, mib_attr)
        if apl_result != 0:
            _hal.handle_error_code(apl_result, dme_error_code_table , "dme_get")
        return apl_val
    
    def dme_req (self, option: int, lane_cnt: int = 0):
        _hal.dme_req(self._dll, option, lane_cnt)

    def dme_reg_set(self, reg_addr: int, reg_val: int) -> int:
        return _hal.dme_reg_set(self._dll, reg_addr, reg_val)

    def dme_reg_get(self, reg_addr: int) -> int:
        result = _hal.dme_reg_get(self._dll, reg_addr)
        return result
    
    def read_dme_reg(self, reg_addr: int) -> bytearray:
        return _hal.read_dme_reg(self._dll, reg_addr)