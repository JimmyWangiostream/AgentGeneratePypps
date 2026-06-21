from enum import IntEnum, Enum

class Dcmd(IntEnum):
    DCMD0_DOUT_DIN_CNT_STOP = 0x00
    DCMD1_PAUSE_TASK_MNGT = 0x01
    DCMD2_OVER_UNDER_FLOW = 0x02
    DCMD3_BUS_IDLE_DET = 0x03
    DCMD4_UNIPRO_ERROR_INJECT = 0x04
    DCMD5_MEASURE_INIT_FLOW = 0x05
    DCMD6_SSU_HIBERNATE_FLOW = 0x06
    DCMD7_INTERRUPT_DEBUG = 0x07
    DCMD8_INIT_SPOR_DEBUG = 0x08
    DCMD9_PURGE_SPOR_DEBUG = 0x09
    DCMD10_RESP_EXE_DEBUG = 0x0A
    DCMD11_SUSPEND_TEST_DEBUG = 0x0B
    DCMD12_LINK_SPEED_STRESS_DEBUG = 0x0C
    DCMD13_TIMEOUT_SETTING = 0x0D
    DCMD14_POWER_CHANGE_STRESS = 0x0E
    DCMD15_RESERVED = 0x0F
    DCMD16_GPIO_DEBUG = 0x10
    DCMD17_DME_ERROR_DEBUG = 0x11
    DCMD18_RESERVED = 0x12
    DCMD19_BKOPS_SPOR_DEBUG = 0x13
    DCMD20_KEEP_SEND_CMD_DEBUG = 0x14
    DCMD21_INACTIVE_HPB_TABLE_DEBUG = 0x15
    DCMD23_ADVANCED_OPTION_DEBUG = 0x17

class Dcmd5Error(IntEnum):
    PASS = 0
    SSU_POWERDOWN_FAIL = 1
    LINK_STARTUP_FAIL = 2
    SET_REFERENCE_CLOCK_FAIL = 3
    SPEED_CHANGE_FAIL_AFTER_LINK = 4
    NOP_OUT_FAIL = 5
    READ_BOOT_DATA_FAIL = 6
    SET_INITIAL_FLAG_FAIL = 7
    READ_INITIAL_FLAG_FAIL = 8
    READ_INITIAL_FLAG_TIMEOUT = 9
    SPEED_CHANGE_FAIL_AFTER_INIT = 10
    NOP_OUT_FAIL_AFTER_POWER_CHANGE = 11
    SSU_ACTIVE_FAIL = 12
    READ_DATA_FAIL = 13
    SPOR_BEFORE_HW_RESET = 14
    SPOR_BEFORE_END_POINT_RESET = 15
    READ_ATTR_FAIL_BEFORE_SPEED_CHANGE_AFTER_INIT = 16

class Dcmd5SSUPowerDown(IntEnum):
    DIS = 0
    EN = 1

class Dcmd5ResetType(IntEnum):
    SKIP_RESET = 0xF
    HW_RESET = 0
    RESET_N = 1
    ENDPOINT_RESET = 2
    UNIPRO_RESET = 3

class Dcmd5ReadBootData(IntEnum):
    DIS = 0
    EN = 1

class Dcmd5SpdChgAfterLink(IntEnum):
    DIS = 0
    EN = 1

class Dcmd5SpdChgAfterInit(IntEnum):
    DIS = 0
    EN = 1

class Dcmd5SSUActiveAfterInit(IntEnum):
    STAY_IN_ACTIVE = 0
    STAY_IN_SLEEP = 1
    EXIT_SLEEP = 2

class Dcmd5ReadData(IntEnum):
    DIS = 0
    EN = 1

class Dcmd5RefClkSetting(IntEnum):
    DIS = 0
    EN = 1

class Dcmd5RefClk(IntEnum):
    MHZ_19_2 = 0
    MHZ_26_0 = 1
    MHZ_38_4 = 2
    MHZ_52_0 = 3

class Dcmd7Status(IntEnum):
    PASS = 0
    FAIL = 1

class Dcmd7InterruptStatus(IntEnum):
    FAIL = 0
    SUCCESS = 1

class Dcmd7Activate(IntEnum):
    DIS = 0
    EN = 1

class Dcmd7DetectType(IntEnum):
    BUSY_TIME_DETECT = 0
    TOTAL_BUSY_TIME_DETECT = 1
    GPIO0_RISING_DETECT = 2
    GPIO0_FALLING_DETECT = 3
    GPIO0_RISING_N_FALLING = 4
    TIMER_DETECT = 5
    DME_INT_DETECT = 6
    SIM_POWER_3_0 = 7
    RESPONSE_DETECT = 8

class Dcmd7ResetType(IntEnum):
    HW_RESET = 0
    RESET_N = 1
    ENDPOINT_RESET = 2
    UNIPRO_RESET = 3

class Dcmd7PowerOn(IntEnum):
    DIS = 0
    EN = 1

class Dcmd7Enhance(IntEnum):
    DIS = 0
    EN = 1

class Dcmd71stStepSPORChannel(IntEnum):
    VCC = 1
    VCCQ_VCCQ2 = 2

class Dcmd72ndStepDelayTimeSwitch(IntEnum):
    DIS = 0
    EN = 1

class HostDoneQueueType(IntEnum):
    TAG_DONE_QUEUE = 1
    LUN_DONE_QUEUE = 2
    ALL_DONE_QUEUE = 3
    ALL_DONE_QUEUE_ERR_HANDLE = 4    

class Dcmd9SetPurgeFlag(IntEnum):
    DIS = 0
    EN = 1

class Dcmd9ResetType(IntEnum):
    HW_RESET = 0
    RESET_N = 1
    ENDPOINT_RESET = 2
    UNIPRO_RESET = 3

class Dcmd9Status(IntEnum):
    SPOR_PASS = 0
    SKIP_SPOR_DUE_TO_READ_ATTRIBUTE_ERROR = 1
    SKIP_SPOR_DUE_TO_PURGE_STATUS_GREATER_EQUAL_2 = 2
    SKIP_SPOR_DUE_TO_IDLE = 3
    END_POINT_RESET_OR_UNIPRO_RESET_FAIL = 4
    TIMEOUT = 5
    SET_PURGE_FLAG_FAIL = 6

class Dcmd9InterruptStatus(IntEnum):
    FAIL = 0
    SUCCESS = 1
