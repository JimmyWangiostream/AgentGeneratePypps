from enum import Enum, IntEnum

class ThermalProtectionType(IntEnum):
    TP_ENABLE  = 0  # Not allowed in FW with efuse in shipping mode
    TP_DISABLE = 1  # Not allowed in FW with efuse in shipping mode

class HardThermalProtectionType(IntEnum):
    TP_HARD_HOT_ONLY  = 0
    TP_HARD_COLD_ONLY = 1  # Not allowed in FW with efuse in shipping mode
    TP_HARD_HOT_COLD  = 2

