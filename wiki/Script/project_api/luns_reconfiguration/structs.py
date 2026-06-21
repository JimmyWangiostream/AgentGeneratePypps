import struct
from typing import List, Dict, Final
from enum import Enum, IntEnum
from Script.project_api.structs import micron_vendor_cmd


class CONFIG_DESCRIPTOR_LOCK(IntEnum):
    UNLOCK      = 0
    LOCK        = 1
