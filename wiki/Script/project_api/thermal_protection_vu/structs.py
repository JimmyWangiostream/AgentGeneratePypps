import struct
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class ReadThermalStuckThreshold(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(28), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        dumpfile("read_thermal_stuck_threshold.bin", payload)
        self.threshold_for_high_thermal_stuck_area = self.add_field(16, 19, 'little')
        self.threshold_for_low_thermal_stuck_area = self.add_field(24, 27, 'little')

class WriteThermalStuckThreshold(PacketParserComposerABC):
    def __init__(self, payload:bytearray = bytearray(8), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.threshold_count = self.add_field(0, 3, 'little')
        self.low_thermal_protection_threshold = self.add_field(4, 5, 'little')
        self.high_thermal_protection_threshold = self.add_field(6, 7, 'little')

class micron_vu_D0F1(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.threshold_count = self.add_field(12, 15, 'little')
        self.low_thermal_protection_threshold = self.add_field(16, 17, 'little')
        self.high_thermal_protection_threshold = self.add_field(18, 19, 'little')

class micron_vu_D0F3(micron_vendor_cmd):
    def __init__(self, payload: bytearray | None = None) -> None:
        payload = payload if payload is not None else bytearray(44)
        super().__init__(payload)
        self.thermal_protection_type = self.add_field(13, 13, 'little')
        self.hard_thermal_protection_type = self.add_field(14, 14, 'little')

