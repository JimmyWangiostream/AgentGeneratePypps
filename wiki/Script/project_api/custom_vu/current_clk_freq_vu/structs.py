import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class VU_40EE_struct(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(12), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.clk_tree_grp2_cpu = self.add_field(0, 1, 'little') 
        self.clk_tree_grp3_buf = self.add_field(2, 3, 'little') 
        self.clk_tree_grp3_cop0 = self.add_field(4, 5, 'little')  
        self.domain_12_ldpc_dec_clk = self.add_field(6, 7, 'little') 
        self.domain_13_ldpc_enc_clk = self.add_field(8, 9, 'little') 
        self.domain_15_onfi_phy_mdll = self.add_field(10,11,'little')




