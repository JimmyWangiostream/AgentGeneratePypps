from ._sdk_base import _SDKLibProtocol
from .. import _hal

class HpbActivateArg():
    def __init__(self):
            self.activate = 0
            self.mode = 0
            self.hpb_read_buf_mode = 0
            self.reserved1 = 0
            self.hpb_prefetch = 0
            self.skip_inactive_chk = 0
            self.hpb_turbo_mode = 0
    
class HpbAutoSettingArg:
    def __init__(self):
            self.auto_l2p = 0
            self.auto_upd_table = 0
            self.manual_update_table = 0

class HpbGetEntryArg:
    def __init__(self):
            self.lun = 0
            self.lba = 0

class HpbDumpTableArg:
    def __init__(self):
            self.type = 0
            self.lun = 0
            self.region = 0
            self.sub_region = 0

class HpbResultInfo():
    def __init__(self, info_buf):
            self.status = info_buf[0]
            self.major_error_code = info_buf[1]
            self.sub_error_code = info_buf[2]
            self.reserved = info_buf[3]
            self.issue_region0 = int.from_bytes(info_buf[4:6], byteorder='little')
            self.issue_sub_region0 = int.from_bytes(info_buf[6:8], byteorder='little')
            self.issue_region1 = int.from_bytes(info_buf[8:10], byteorder='little')
            self.issue_sub_region1 = int.from_bytes(info_buf[10:12], byteorder='little')
            self.hpb_activate = info_buf[12]
            self.hpb_mode = info_buf[13]
            self.auto_l2p = info_buf[14]
            self.auto_update_table = info_buf[15]
            self.manual_update_table = info_buf[16]
            self.table_total_size = int.from_bytes(info_buf[17:21], byteorder='little')
            self.table_region_size = int.from_bytes(info_buf[21:25], byteorder='little')
            self.table_sub_region_size = int.from_bytes(info_buf[25:29], byteorder='little')
            self.hpb_read_buff_cnt = int.from_bytes(info_buf[29:33], byteorder='little')
            self.hpb_read_buff_latency = int.from_bytes(info_buf[33:37], byteorder='little')
            self.hpb_read_buff_mode = info_buf[37]
            self.resvered1 = info_buf[38]
            self.hpb_prefetch = info_buf[39]
            self.skip_inactive_chk = info_buf[40]
            self.hpb_read_hit_count = int.from_bytes(info_buf[41:45], byteorder='little')
            self.skip_repeat_re_cmd = info_buf[45]
            self.hpb_write_buff_cnt = int.from_bytes(info_buf[46:50], byteorder='little')
        
    def status(self):
            return self.status

class HpbResultTableInfo():
    class Entry:
        def __init__(self, lun, region, address, reserved):
                self.lun = lun
                self.region = region
                self.address = address
                self.reserved = reserved

        def __init__(self, buffer):
            self.entries = []
            self.from_buffer(buffer)

        def from_buffer(self, buffer):
            entry_size = 16  # 1 byte for LUN, 2 bytes for Region, 4 bytes for Address, 9 bytes for Reserved
            num_entries = len(buffer) // entry_size

            for i in range(num_entries):
                offset = i * entry_size
                lun = int.from_bytes(buffer[offset:offset+1], byteorder='little')
                region = int.from_bytes(buffer[offset+1:offset+3], byteorder='little')
                address = int.from_bytes(buffer[offset+3:offset+7], byteorder='little')
                reserved = buffer[offset+7:offset+16]
                self.entries.append(self.Entry(lun, region, address, reserved))


class _SDKLibHpbMixin(_SDKLibProtocol): 
    def hpb_activate(self, arg: HpbActivateArg):
        arg_buf = bytearray(512)
        arg_buf[0] = arg.activate
        arg_buf[1] = arg.mode
        arg_buf[2] = arg.hpb_read_buf_mode
        arg_buf[3] = arg.reserved1
        arg_buf[4] = arg.hpb_prefetch
        arg_buf[5] = arg.skip_inactive_chk
        arg_buf[6] = arg.hpb_turbo_mode

        _hal.hpb_activate(self._dll, arg_buf)

    def hpb_auto_setting(self, arg: HpbAutoSettingArg):
        arg_buf = bytearray(512)
        arg_buf[0] = arg.auto_l2p
        arg_buf[1] = arg.auto_upd_table
        arg_buf[2] = arg.manual_update_table

        _hal.hpb_activate(self._dll, arg_buf)

    def hpb_reset(self):
        _hal.hpb_reset(self._dll)

    def hpb_get_entry(self, arg: HpbGetEntryArg) -> bytearray:
        arg_buf = bytearray(512)
        arg_buf[0] = arg.lun
        arg_buf[1] = arg.lba

        return _hal.hpb_get_entry(self._dll, arg_buf)
    
    def hpb_dump_table(self, arg: HpbDumpTableArg) -> bytearray:
        arg_buf = bytearray(512)
        arg_buf[0] = arg.type
        arg_buf[1:5] = arg.lun.to_bytes(4, byteorder='little')
        arg_buf[5:9] = arg.region.to_bytes(4, byteorder='little')
        arg_buf[9:13] = arg.sub_region.to_bytes(4, byteorder='little')

        return _hal.hpb_dump_table(self._dll, arg_buf)
    
    def hpb_result(self) -> tuple[HpbResultInfo, HpbResultTableInfo]:
        (info_buf, table_info_buf) = _hal.hpb_result(self._dll)
        info = HpbResultInfo(info_buf)
        table_info = HpbResultTableInfo(table_info_buf)
        return (info, table_info)
    
    def hpb_dump_bitmap(self, arg: bytearray, bitmap_buf: bytearray): # no doc ref
        _hal.hpb_dump_table(self._dll, arg, bitmap_buf)