import struct
from Script.api.struct_helper import *
from Script.project_api.structs import micron_vendor_cmd

class VU_40F0_struct(PacketParserComposerABC):
    def __init__(self, payload: bytearray = bytearray(72), start_offset:int = AUTO_OFFSET, end_offset:int = AUTO_OFFSET) -> None:
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.num_of_cmd_still_in_HW_queue = self.add_field(0,3,'little')  #only in hw queue
        self.num_of_read_cmd_been_abort = self.add_field(4,7,'little')
        self.num_of_write_cmd_been_abort = self.add_field(8,11,'little')
        self.num_of_other_cmd_been_abort = self.add_field(12,15,'little')
        self.abort_read_during_cmd_analysis_stage = self.add_field(16,19,'little')
        self.abort_read_during_dtm_read_queue_status_report_stage = self.add_field(20,23,'little')
        self.l24_rev = self.add_field(24,27,'little')
        self.abort_write_during_cmd_analysis_stage = self.add_field(28,31,'little')
        self.abort_write_during_dtm_write_queue_status_report_stage = self.add_field(32,35,'little')
        self.l36_rev = self.add_field(36,39,'little')
        self.abort_write_after_dataout_fill_write_cache = self.add_field(40,43,'little')
        self.abort_cmd_but_it_may_send_response_at_last = self.add_field(44,47,'little')
        self.total_number_of_abort_cmd = self.add_field(48,51,'little')
        self.verify_abort_cmd_wait = self.add_field(52,55,'little')
        self.verify_abort_rw_done_wait = self.add_field(56,59,'little')
        self.verify_abort_flush_done_wait = self.add_field(60,63,'little')
        self.verify_abort_data_check_done_wait = self.add_field(64,67,'little')
        self.verify_abort_repsonse_down_wait = self.add_field(68,71,'little')

