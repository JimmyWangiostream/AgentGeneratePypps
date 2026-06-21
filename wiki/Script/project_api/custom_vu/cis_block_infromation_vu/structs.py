import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class VU_40B9_struct(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(48), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.physical_blk_number_of_cis_vb = self.add_field(0,1,'little')
        self.die_number_of_the_STC_copy = self.add_field(2,3,'little')
        self.physical_blk_number_of_the_STC_copy = self.add_field(4,5,'little')
        self.plane_number_of_the_STC_copy = self.add_field(6,7,'little')
        self.bitmap_of_the_copies_pending_on_refresh = self.add_field(8,9,'little')
        self.if_cis0_is_bad_blk = self.add_field(10,10,'little')
        self.if_cis1_is_bad_blk = self.add_field(11,11,'little')
        self.if_cis2_is_bad_blk = self.add_field(12,12,'little')
        self.if_cis3_is_bad_blk = self.add_field(13,13,'little')
        self.cis0_ec_count = self.add_field(14,17,'little')
        self.cis1_ec_count = self.add_field(18,21,'little')
        self.cis2_ec_count = self.add_field(22,25,'little')
        self.cis3_ec_count = self.add_field(26,29,'little')
        self.cis_copy_used_to_load_FE_bank = self.add_field(30,30,'little')
        self.cis_copy_used_to_load_DM_bank = self.add_field(31,31,'little')
        self.fw_image_page_start_index = self.add_field(32,35,'little')
        self.fw_image_page_end_index = self.add_field(36,39,'little')
        self.bank_page_start_index = self.add_field(40,43,'little')
        self.bank_page_end_index = self.add_field(44,47,'little')



