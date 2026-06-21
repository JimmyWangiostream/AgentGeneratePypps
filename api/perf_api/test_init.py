from Script.api import shared
from Script.lib import sdk_lib as lib
from Script.lib.sdk_lib.user import constant

_sdk = shared.sdk

class SeqInitFlowStrut:
    def __init__(self):
        self._byte0 = 0xFF
        self._byte1 = 0x05
        self.delay_time_us = 0
        self.option = 0
        self.linkstatup_time = 0
        self.nop_out_time = 0
        self.init_flag_time = 0

    def to_bytes(self) -> bytearray:
        entry = bytearray(72)
        entry[0] = self._byte0
        entry[1] = self._byte1
        for i in range(2, 32):
            entry[i] = 0
        entry[32:36] = self.delay_time_us.to_bytes(4, 'little')
        entry[36:38] = self.option.to_bytes(2, 'little')
        for i in range(38, 40):
            entry[i] = 0
        entry[40:44] = self.linkstatup_time.to_bytes(4, 'little')
        entry[44:48] = self.nop_out_time.to_bytes(4, 'little')
        entry[48:52] = self.init_flag_time.to_bytes(4, 'little')
        for i in range(52, 72):
            entry[i] = 0

        return entry

# pass
class SeqTestUnitReadyStruct:
    def __init__(self):
        self.b0 = 0xFF
        self.b1 = 0x08
        self.lun = 0
        self.timeout_us = 0
        self.delaytime_us = 0
        self.option = 0
    
    def to_bytes(self) -> bytearray:
        entry = bytearray(72)
        entry[0] = self.b0
        entry[1] = self.b1
        entry[2] = self.lun
        entry[3:7] = self.timeout_us.to_bytes(4, 'little')
        for i in range(7, 31):
            entry[i] = 0
        entry[32:36] = self.delaytime_us.to_bytes(4, 'little')
        entry[36:38] = self.option.to_bytes(2, 'little')
        for i in range(38, 71):
            entry[i] = 0

        return entry
def test_cmdseq_monitor():
    init_flow = SeqInitFlowStrut()
    init_flow.option = 1
    init_flow.delay_time_us = 0
    init_flow_buf = init_flow.to_bytes()

    cmd_seq = lib.SendCmdSeq()
    cmd_seq.pby_cmd_buf = init_flow_buf
    if len(cmd_seq.pby_cmd_buf) % constant.DATA_SIZE_8K_BYTE > 0:
        zero_pad_size = constant.DATA_SIZE_8K_BYTE - (len(cmd_seq.pby_cmd_buf) % constant.DATA_SIZE_8K_BYTE)
        cmd_seq.pby_cmd_buf += bytearray([0xFF] * zero_pad_size)
    
    cmd_seq.qd = 1
    cmd_seq.option = 3
    cmd_seq.cmd_blk_cnt = 1
    cmd_seq.data_blk_cnt = 1

    _sdk.send_cmd_seq(cmd_seq)
    result, info_buf = _sdk.cmd_seq_monitor(cmd_seq.cmd_blk_cnt, cmd_seq.data_blk_cnt)

    test_unit_ready = SeqTestUnitReadyStruct()
    test_unit_ready.lun = 0
    test_unit_ready.timeout_us = 100000
    test_unit_ready.delaytime_us = 0
    test_unit_ready.option = 0
    test_unit_ready_buf = test_unit_ready.to_bytes()

    cmd_seq.pby_cmd_buf = test_unit_ready_buf
    if len(cmd_seq.pby_cmd_buf) % constant.DATA_SIZE_8K_BYTE > 0:
        zero_pad_size = constant.DATA_SIZE_8K_BYTE - (len(cmd_seq.pby_cmd_buf) % constant.DATA_SIZE_8K_BYTE)
        cmd_seq.pby_cmd_buf += bytearray([0xFF] * zero_pad_size)
    
    cmd_seq.qd = 1
    cmd_seq.option = 3
    cmd_seq.cmd_blk_cnt = 1
    cmd_seq.data_blk_cnt = 1

    _sdk.send_cmd_seq(cmd_seq)
    result, info_buf = _sdk.cmd_seq_monitor(cmd_seq.cmd_blk_cnt, cmd_seq.data_blk_cnt)