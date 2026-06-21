from ._sdk_base import _SDKLibProtocol
from .. import _hal

class RWTaskEntry:
    class GwrOption:
        def __init__(self):
            self.Data_Pattern_Mode = 0  # [0:1]
            self.Attribute = 0          # [2:3]
            self.CP = 0                 # [4]
            self.FUA = 0                # [5]
            self.DPO = 0                # [6]
            self.AddTag = 0             # [7]
            self.CheckSum_En = 0        # [8:9]
            self.Mode = 0               # [10:12]
            self.ShareQueue = 0         # [13]
            self.LBAMark_CheckSum = 0   # [14] Gen LBA Mark 4 Bytes only
            self.SameTask_En = 0        # [15] Insert Same Task
        
        def to_bytes(self):
            option = (
                (self.Data_Pattern_Mode & 0x03) |
                ((self.Attribute & 0x03) << 2) |
                ((self.CP & 0x01) << 4) |
                ((self.FUA & 0x01) << 5) |
                ((self.DPO & 0x01) << 6) |
                ((self.AddTag & 0x01) << 7) |
                ((self.CheckSum_En & 0x03) << 8) |
                ((self.Mode & 0x07) << 10) |
                ((self.ShareQueue & 0x01) << 13) |
                ((self.LBAMark_CheckSum & 0x01) << 14) |
                ((self.SameTask_En & 0x01) << 15)
            )
            return option.to_bytes(2, 'little')
    
    def __init__(self):
        self.task_tag = 0
        self.lun = 0
        self.block_size = 0
        self.option = self.GwrOption()  # SDK_GWR_Option in c code
        self.lba_msb = 0
        self.lba_lsb = 0  # LBA_L, big endian
        self.length = 0   # dwDataLen, big endian
        self.pattern_tag = 0  # dwLoopTag, big endian
        self.group = 0
        self.lu_depth = 0
        self.seed_msb = 0  # dwCustom_Data_H, big endian
        self.seed_lsb = 0  # dwCustom_Data_L, big endian
        self.option_2 = 0  # by512B_4K_Opt

class RWInfo:
    class GRWErr:
        def __init__(self):
            self.bg_error = 0
            self.bg_sub_error = 0
            self.bg_sk = 0
            self.bg_asc = 0

    def __init__(self):
        self.action = 0
        self.scsicmd = 0
        self.lun = 0
        self.lba_h = 0
        self.lba_l = 0
        self.fua = 0
        self.dpo = 0
        self.groupno = 0
        self.datalen = 0
        self.datapattern = 0
        self.databuf = 0
        self.modetype = 0
        self.patternmode = 0
        self.addtag = 0
        self.lba_markcrc_en = 0
        self.sametasktag_en = 0
        self.looptag = 0
        self.timeout = 0
        self.maxbusytime = 0
        self.totalbusytime = 0
        self.expectdatalen = 0
        self.assignlb = 0
        self.taskatt = 0
        self.cp = 0
        self.tasktag = 0
        self.wklun = 0
        self.cmdorder = 0
        self.lbamark_checksum = 0
        self.datacrc = 0
        self.u64checksum = 0
        self.rdprotect = 0
        self.bg_errcode = self.GRWErr()
        self.isinthit = 0
        self.startlba_ptn = 0
        self.rwtype = 0
        self.cmpcurdata = 0

class MonitorInfoBuf:
    def __init__(self, buf: bytearray):
        self.bg_step = buf[0]
        self.current_cnt_lsb = buf[1]
        self.current_cnt_msb = buf[2]
        self.bg_error = buf[3]
        self.bg_sub_error = buf[4]
        self.bg_sense_key = buf[5]
        self.current_tx_task_tag = int.from_bytes(buf[6:8], byteorder='little')
        self.current_rx_task_tag = int.from_bytes(buf[8:10], byteorder='little')
        self.bg_sense_code = buf[10]
        self.reserved_1 = buf[11:16]
        self.ptng_tx_lba = int.from_bytes(buf[16:20], byteorder='little')
        self.ptng_rx_lba = int.from_bytes(buf[20:24], byteorder='little')
        self.manual_rx_lba = int.from_bytes(buf[24:28], byteorder='little')
        self.fw_bus_idle_time = int.from_bytes(buf[28:32], byteorder='little')
        self.spor_flag = buf[32]
        self.layer_error = buf[33]
        self.dme_error = int.from_bytes(buf[34:38], byteorder='little')
        self.unipro_state = buf[38]
        self.line_reset = buf[39]
        self.cmd_list_index = buf[40]
        self.rsp_list_index = buf[41]
        self.cmd_list = buf[42:170]
        self.rsp_list = buf[170:378]
        self.reserved_2 = buf[378:495]
        self.current_response_task_tag = int.from_bytes(buf[495:497], byteorder='little')
        self.reserved_3 = buf[497:511]

class _SDKLibGroupRWMixin(_SDKLibProtocol):
    def monitor(self, opt: int, blk_cnt: int):
        buf = _hal.monitor(self._dll, opt, blk_cnt)
        return MonitorInfoBuf(buf)

    def monitor_w_rw_info(self, rw_info_vector: list[RWInfo], opt: int, blk_cnt: int):
        # rw_info_vector to C type CRW_Info list
        crw_info_array = (_hal.CRW_Info * len(rw_info_vector))()
        for i, rw_info in enumerate(rw_info_vector):
            crw_info_array[i] = _hal.CRW_Info(
                byAction=rw_info.action,
                bySCSICmd=rw_info.scsicmd,
                byLun=rw_info.lun,
                LBA_H=rw_info.lba_h,
                LBA_L=rw_info.lba_l,
                byFUA=rw_info.fua,
                byDPO=rw_info.dpo,
                byGroupNo=rw_info.groupno,
                dwDataLen=rw_info.datalen,
                dwDataPattern=rw_info.datapattern,
                dwDataBuf=rw_info.databuf,
                byModeType=rw_info.modetype,
                byPatternMode=rw_info.patternmode,
                byAddTag=rw_info.addtag,
                byLBA_MarkCRC_En=rw_info.lba_markcrc_en,
                bySameTaskTag_En=rw_info.sametasktag_en,
                dwLoopTag=rw_info.looptag,
                dwTimeOut=rw_info.timeout,
                dwMaxBusyTime=rw_info.maxbusytime,
                dwTotalBusyTime=rw_info.totalbusytime,
                dwExpectDataLen=rw_info.expectdatalen,
                dwAssignLB=rw_info.assignlb,
                byTaskAtt=rw_info.taskatt,
                byCP=rw_info.cp,
                byTaskTag=rw_info.tasktag,
                byWKLun=rw_info.wklun,
                byCmdOrder=rw_info.cmdorder,
                byLBAMark_CheckSum=rw_info.lbamark_checksum,
                dwDataCRC=rw_info.datacrc,
                u64CheckSum=rw_info.u64checksum,
                byRDPROTECT=rw_info.rdprotect,
                stBG_ErrCode=_hal.CGRW_Err(
                    byBG_Error=rw_info.bg_errcode.bg_error,
                    byBG_SubError=rw_info.bg_errcode.bg_sub_error,
                    byBG_SK=rw_info.bg_errcode.bg_sk,
                    byBG_ASC=rw_info.bg_errcode.bg_asc
                ),
                dwIsINTHit=rw_info.isinthit,
                dwStartLBA_Ptn=rw_info.startlba_ptn,
                dwRWType=rw_info.rwtype,
                bCmpCurData=rw_info.cmpcurdata
            )
        buf = _hal.monitor_w_rw_info(self._dll, rw_info_vector, opt, blk_cnt)
        return MonitorInfoBuf(buf)
    
    def group_read_write(self, rw_entry_list: list[RWTaskEntry]):
        
        # convert rw_entry_list to bytearray
        gp_rw_buf = bytearray(32 * len(rw_entry_list))
        for i, entry in enumerate(rw_entry_list):
            offset = i * 32
            gp_rw_buf[offset + 0] = entry.task_tag
            gp_rw_buf[offset + 1] = entry.lun
            gp_rw_buf[offset + 2] = entry.block_size
            gp_rw_buf[offset + 3:offset + 5] = entry.option.to_bytes()
            gp_rw_buf[offset + 5:offset + 9] = entry.lba_msb.to_bytes(4, 'little')
            gp_rw_buf[offset + 9:offset + 13] = entry.lba_lsb.to_bytes(4, 'big')
            gp_rw_buf[offset + 13:offset + 17] = entry.length.to_bytes(4, 'big')
            gp_rw_buf[offset + 17:offset + 21] = entry.pattern_tag.to_bytes(4, 'big')
            gp_rw_buf[offset + 21] = entry.group
            gp_rw_buf[offset + 22] = entry.lu_depth
            gp_rw_buf[offset + 23:offset + 27] = entry.seed_msb.to_bytes(4, 'big')
            gp_rw_buf[offset + 27:offset + 31] = entry.seed_lsb.to_bytes(4, 'big')
            gp_rw_buf[offset + 31] = entry.option_2

        _hal.group_read_write(self._dll, gp_rw_buf)