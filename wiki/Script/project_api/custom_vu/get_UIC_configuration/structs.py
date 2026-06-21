import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class UICconfigdata(PacketParserComposerABC):
    def __init__(self, payload:bytearray, start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.PA_HIBERN8TIME = self.add_field(0, 0)
        self.PA_TXHSG1SYNCLENGTH = self.add_field(1, 1)
        self.PA_TXHSG2SYNCLENGTH = self.add_field(2, 2)
        self.PA_TXHSG3SYNCLENGTH = self.add_field(3, 3)
        self.PA_TXHSG4SYNCLENGTH = self.add_field(4, 4)
        self.N_DEVICEID = self.add_field(5, 5)
        self.T_CONNECTIONSTATE = self.add_field(6, 6)
        self.RX_Min_ActivateTime_Capability = self.add_field(7, 7)
        self.RX_ADV_GRAN_SUPPORTED = self.add_field(8, 8)
        self.RX_ADV_GRAN_STEP = self.add_field(9, 9)
        self.RX_Advanced_Min_ActivateTime_Capability = self.add_field(10, 10)
        self.RX_Hibern8Time_Capability = self.add_field(11, 11)
        self.RX_Advanced_Hibern8Time_Capability = self.add_field(12, 12)
        self.TX_Advanced_Hibern8Time_Capability = self.add_field(13, 13)
        self.RX_LS_PREPARE_LENGTH_Capability = self.add_field(14, 14)
        self.RX_HS_G1_PREPARE_LENGTH_Capability = self.add_field(15, 15)
        self.RX_HS_G2_PREPARE_LENGTH_Capability = self.add_field(16, 16)
        self.RX_HS_G3_PREPARE_LENGTH_Capability = self.add_field(17, 17)
        self.RX_HS_G1_SYNC_LENGTH_Capability = self.add_field(18, 18)
        self.RX_HS_G2_SYNC_LENGTH_Capability = self.add_field(19, 19)
        self.RX_HS_G3_SYNC_LENGTH_Capability = self.add_field(20, 20)
