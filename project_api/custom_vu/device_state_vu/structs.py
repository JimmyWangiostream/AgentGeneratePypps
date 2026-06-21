import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class micron_vu_D0FC(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.bValue = self.add_field(12, 12, 'little')

class micron_vu_D0E2(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.bDeviceState = self.add_field(12, 12, 'little')

class micron_vu_40FC(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)

class micron_vu_40E2(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)