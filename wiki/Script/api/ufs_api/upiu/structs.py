from abc import ABC, abstractmethod
import struct
from typing import Generic, TypeVar
import bitstruct
from Script.api.struct_helper import *
from Script.api.ufs_api.defines.enum_define import QueryFunctionOpcode, ScsiCmd, UPIUTransactionType

T = TypeVar("T", bound=PacketComposerABC)

class CdbFormatUnit(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.FORMAT_UNIT
        self.b1_fmtpinfo = 0
        self.b1_longlist = 0
        self.b1_fmtdata = 0
        self.b1_cmplst = 0
        self.b1_defect_list_format = 0
        self.b2_vendor_specific = 0
        self.w3_obsolete = 0
        self.b5_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBHB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u2u1u1u1u3', self.b1_fmtpinfo, self.b1_longlist, 
                           self.b1_fmtdata, self.b1_cmplst, self.b1_defect_list_format)[0],
            self.b2_vendor_specific,
            self.w3_obsolete,
            self.b5_control
        )
        return buf

class CdbInquiry(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.INQUIRY
        self.b1_rsvd = 0
        self.b1_obsolete = 0
        self.b1_evpd = 0
        self.b2_page_code = 0
        self.w3_allocation_length = 0
        self.b5_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBHB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u6u1u1', self.b1_rsvd, self.b1_obsolete, 
                           self.b1_evpd)[0],
            self.b2_page_code,
            self.w3_allocation_length,
            self.b5_control
        )
        return buf
    
class CdbModeSelect10(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.MODE_SELECT_10
        self.b1_rsvd = 0
        self.b1_pf = 1
        self.b1_rsvd2 = 0
        self.b1_sp = 0
        self.b2_rsvd = 0
        self.l3_rsvd = 0
        self.w7_parameter_list_length = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBLHB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u1u3u1', self.b1_rsvd, self.b1_pf,
                            self.b1_rsvd2, self.b1_sp)[0],
            self.b2_rsvd,
            self.l3_rsvd,
            self.w7_parameter_list_length,
            self.b9_control
        )
        return buf

class CdbModeSense10(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.MODE_SENSE_10
        self.b1_rsvd = 0
        self.b1_llbaa = 0
        self.b1_dbd = 1
        self.b1_rsvd2 = 0
        self.b2_pc = 0
        self.b2_page_code = 0
        self.b3_subpage_code = 0
        self.b4_rsvd = 0
        self.w5_rsvd = 0
        self.w7_allocation_length = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBBHHB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u1u1u3', self.b1_rsvd, self.b1_llbaa, 
                           self.b1_dbd, self.b1_rsvd2)[0],
            bitstruct.pack('u2u6', self.b2_pc, self.b2_page_code)[0],
            self.b3_subpage_code,
            self.b4_rsvd,
            self.w5_rsvd,
            self.w7_allocation_length,
            self.b9_control
        )
        return buf

class CdbPreFetch10(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.PREFETCH_10
        self.b1_rsvd = 0
        self.b1_immed = 0
        self.b1_obsolete = 0
        self.l2_lba = 0
        self.b6_rsvd = 0
        self.b6_group_number = 0
        self.w7_prefetch_length = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBLBHB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u6u1u1', self.b1_rsvd, self.b1_immed, 
                           self.b1_obsolete)[0],
            self.l2_lba,
            bitstruct.pack('u3u5', self.b6_rsvd, self.b6_group_number)[0],
            self.w7_prefetch_length,
            self.b9_control
        )
        return buf

class CdbPreFetch16(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.PREFETCH_16
        self.b1_rsvd = 0
        self.b1_immed = 0
        self.b1_obsolete = 0
        self.l2_lba_h = 0
        self.l6_lba_l = 0
        self.l10_prefetch_length = 0
        self.b14_rsvd = 0
        self.b14_group_number = 0
        self.b15_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBLLLBB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u6u1u1', self.b1_rsvd, self.b1_immed, 
                           self.b1_obsolete)[0],
            self.l2_lba_h,
            self.l6_lba_l,
            self.l10_prefetch_length,
            bitstruct.pack('u3u5', self.b14_rsvd, self.b14_group_number)[0],
            self.b15_control
        )
        return buf

class CdbRead6(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.READ_6
        self.b1_rsvd = 0
        self.b1_lba_h = 0
        self.w2_lba_l = 0
        self.b4_transfer_length = 0
        self.b5_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBHBB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u5', self.b1_rsvd, self.b1_lba_h)[0],
            self.w2_lba_l,
            self.b4_transfer_length,
            self.b5_control
        )
        return buf

class CdbRead10(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.READ_10
        self.b1_rdprotect = 0
        self.b1_dpo = 0
        self.b1_fua = 0
        self.b1_rsvd = 0
        self.b1_fua_nv = 0
        self.b1_obsolete = 0
        self.l2_lba = 0
        self.b6_rsvd = 0
        self.b6_group_number = 0
        self.w7_transfer_length = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            ">BBLBHB", buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u1u1u1u1u1', self.b1_rdprotect, self.b1_dpo, 
                           self.b1_fua, self.b1_rsvd, self.b1_fua_nv, self.b1_obsolete)[0],
            self.l2_lba,
            bitstruct.pack('u3u5', self.b6_rsvd, self.b6_group_number)[0],
            self.w7_transfer_length,
            self.b9_control
        )
        return buf
    
class CdbRead16(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.READ_16
        self.b1_rdprotect = 0
        self.b1_dpo = 0
        self.b1_fua = 0
        self.b1_rsvd = 0
        self.b1_fua_nv = 0
        self.b1_rsvd2 = 0
        self.l2_lba_h = 0
        self.l6_lba_l = 0
        self.l10_transfer_length = 0
        self.b14_rsvd = 0
        self.b14_rsvd2 = 0
        self.b14_group_number = 0
        self.b15_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBLLLBB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u1u1u1u1u1', self.b1_rdprotect, self.b1_dpo, 
                           self.b1_fua, self.b1_rsvd, self.b1_fua_nv, self.b1_rsvd2)[0],
            self.l2_lba_h, 
            self.l6_lba_l, 
            self.l10_transfer_length, 
            bitstruct.pack('u1u2u5', self.b14_rsvd, self.b14_rsvd2, self.b14_group_number)[0],
            self.b15_control
        )
        return buf

class CdbReadBuffer(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.READ_BUFFER
        self.b1_rsvd = 0
        self.b1_mode = 0
        self.b2_buffer_id = 0
        self.b3_buffer_offset_h = 0
        self.w4_buffer_offset_l = 0
        self.b6_allocation_length_h = 0
        self.w7_allocation_length_l = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBHBHB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u5', self.b1_rsvd, self.b1_mode)[0],
            self.b2_buffer_id,
            self.b3_buffer_offset_h,
            self.w4_buffer_offset_l,
            self.b6_allocation_length_h,
            self.w7_allocation_length_l,
            self.b9_control
        )
        return buf

class CdbReadCapacity10(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.READ_CAPACITY_10
        self.b1_rsvd = 0
        self.b1_obsolete = 0
        self.l2_lba = 0
        self.b6_rsvd = 0
        self.b7_rsvd = 0 
        self.b8_rsvd = 0
        self.b8_pmi = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBLBBBB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u7u1', self.b1_rsvd, self.b1_obsolete)[0],
            self.l2_lba,
            self.b6_rsvd,
            self.b7_rsvd,
            bitstruct.pack('u7u1', self.b8_rsvd, self.b8_pmi)[0],
            self.b9_control
        )
        return buf

class CdbReadCapacity16(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.READ_CAPACITY_16
        self.b1_rsvd = 0
        self.b1_service_action = 0x10
        self.l2_lba_h = 0
        self.l6_lba_l = 0
        self.l10_allocation_length = 0
        self.b14_rsvd = 0
        self.b14_pmi = 0
        self.b15_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBLLLBB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u5', self.b1_rsvd, self.b1_service_action)[0],
            self.l2_lba_h,
            self.l6_lba_l,
            self.l10_allocation_length,
            bitstruct.pack('u7u1', self.b14_rsvd, self.b14_pmi)[0],
            self.b15_control            
        )
        return buf

class CdbReportLUNs(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.REPORT_LUNS
        self.b1_rsvd = 0
        self.b2_select_report = 0
        self.b3_rsvd = 0
        self.w4_rsvd = 0
        self.l6_allocation_length = 0
        self.b10_rsvd = 0
        self.b11_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBHLBB', buf, 0, 
            self.b0_opcode,
            self.b1_rsvd,
            self.b2_select_report,
            self.b3_rsvd,
            self.w4_rsvd,
            self.l6_allocation_length,
            self.b10_rsvd,
            self.b11_control
        )
        return buf

class CdbRequestSense(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.REQUEST_SENSE
        self.b1_rsvd = 0
        self.b1_desc = 0
        self.w2_rsvd = 0
        self.b4_allocation_length = 0
        self.b5_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBHBB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u7u1', self.b1_rsvd, self.b1_desc)[0],
            self.w2_rsvd,
            self.b4_allocation_length,
            self.b5_control
        )
        return buf

class CdbSecurityProtocolIn(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.SECURITY_PROTOCOL_IN
        self.b1_security_protocol = 0
        self.w2_security_protocol_specific = 0
        self.b4_inc_512 = 0
        self.b4_rsvd = 0
        self.b5_rsvd = 0
        self.l6_allocation_length = 0
        self.b10_rsvd = 0
        self.b11_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBHBBLBB', buf, 0,
            self.b0_opcode,
            self.b1_security_protocol,
            self.w2_security_protocol_specific,
            bitstruct.pack('u1u7', self.b4_inc_512, self.b4_rsvd)[0],
            self.b5_rsvd,
            self.l6_allocation_length,
            self.b10_rsvd,
            self.b11_control
        )
        return buf

class CdbSecurityProtocolOut(PacketComposerABC):
    def __init__(self) -> None: 
        self.b0_opcode = ScsiCmd.SECURITY_PROTOCOL_OUT
        self.b1_security_protocol = 0
        self.w2_security_protocol_specific = 0
        self.b4_inc_512 = 0
        self.b4_rsvd = 0
        self.b5_rsvd = 0
        self.l6_transfer_length = 0
        self.b10_rsvd = 0
        self.b11_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBHBBLBB', buf, 0,
            self.b0_opcode,
            self.b1_security_protocol,
            self.w2_security_protocol_specific,
            bitstruct.pack('u1u7', self.b4_inc_512, self.b4_rsvd)[0],
            self.b5_rsvd,
            self.l6_transfer_length,
            self.b10_rsvd,
            self.b11_control
        )
        return buf

class CdbSendDiagnostic(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.SEND_DIAGNOSTIC
        self.b1_self_test_code = 0 
        self.b1_pf = 0
        self.b1_0 = 0
        self.b1_selftest = 0
        self.b1_devoffl = 0
        self.b1_unitoffl = 0
        self.b2_rsvd = 0
        self.w3_parameter_list_length = 0
        self.b5_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBHB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u1u1u1u1u1', self.b1_self_test_code, self.b1_pf, 
                           self.b1_0, self.b1_selftest, self.b1_devoffl, self.b1_unitoffl)[0],
            self.b2_rsvd,
            self.w3_parameter_list_length,
            self.b5_control
        )
        return buf

class CdbStartStopUnit(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.START_STOP_UNIT
        self.b1_rsvd = 0
        self.b1_immed = 0
        self.b2_rsvd = 0
        self.b3_rsvd = 0
        self.b3_power_condition_modifier = 0
        self.b4_power_conditions = 0
        self.b4_rsvd = 0
        self.b4_no_flush = 0
        self.b4_loej = 0
        self.b4_start = 0
        self.b5_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBBB', buf, 0, 
            self.b0_opcode,
            bitstruct.pack('u7u1', self.b1_rsvd, self.b1_immed)[0],
            self.b2_rsvd,
            bitstruct.pack('u4u4', self.b3_rsvd, self.b3_power_condition_modifier)[0],
            bitstruct.pack('u4u1u1u1u1', self.b4_power_conditions, self.b4_rsvd, self.b4_no_flush, self.b4_loej, self.b4_start)[0],
            self.b5_control
        )
        return buf

class CdbSyncCache10(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.SYNCHRONIZE_CACHE_10
        self.b1_rsvd = 0
        self.b1_sync_nv = 0
        self.b1_immed = 0
        self.b1_obsolete = 0
        self.l2_lba = 0
        self.b6_rsvd = 0
        self.b6_group_number = 0
        self.w7_number_of_logical_blocks = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBLBHB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u5u1u1u1', self.b1_rsvd, self.b1_sync_nv, 
                           self.b1_immed, self.b1_obsolete)[0],
            self.l2_lba,
            bitstruct.pack('u3u5', self.b6_rsvd, self.b6_group_number)[0],
            self.w7_number_of_logical_blocks,
            self.b9_control
        )
        return buf

class CdbSyncCache16(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.SYNCHRONIZE_CACHE_16
        self.b1_rsvd = 0
        self.b1_sync_nv = 0
        self.b1_immed = 0
        self.b1_obsolete = 0
        self.l2_lba_h = 0
        self.l6_lba_l = 0        
        self.l10_number_of_logical_blocks = 0
        self.b14_rsvd = 0
        self.b14_group_number = 0
        self.b15_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBLLLBB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u5u1u1u1', self.b1_rsvd, self.b1_sync_nv, 
                           self.b1_immed, self.b1_obsolete)[0],
            self.l2_lba_h,
            self.l6_lba_l,
            self.l10_number_of_logical_blocks,
            bitstruct.pack('u3u5', self.b14_rsvd, self.b14_group_number)[0],
            self.b15_control
        )
        return buf            

class CdbTestUnitReady(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.TEST_UNIT_READY
        self.l1_rsvd = 0
        self.b5_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BLB', buf, 0,
            self.b0_opcode,
            self.l1_rsvd,
            self.b5_control
        )
        return buf

class CdbUnmap(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.UNMAP
        self.b1_rsvd = 0
        self.b1_anchor = 0
        self.l2_rsvd = 0
        self.b6_rsvd = 0
        self.b6_group_number = 0
        self.w7_param_list_length = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBLBHB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u7u1', self.b1_rsvd, self.b1_anchor)[0],
            self.l2_rsvd,
            bitstruct.pack('u3u5', self.b6_rsvd, self.b6_group_number)[0],
            self.w7_param_list_length,
            self.b9_control
        )
        return buf

class CdbVerify10(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.VERIFY_10
        self.b1_vrprotect = 0
        self.b1_dpo = 0
        self.b1_rsvd = 0
        self.b1_bytchk = 0
        self.b1_obsolete = 0
        self.l2_lba = 0
        self.b6_rsvd = 0
        self.b6_group_number = 0
        self.w7_verification_length = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBLBHB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u1u2u1u1', self.b1_vrprotect, self.b1_dpo, 
                            self.b1_rsvd, self.b1_bytchk, self.b1_obsolete)[0],
            self.l2_lba,
            bitstruct.pack('u3u5', self.b6_rsvd, self.b6_group_number)[0],
            self.w7_verification_length,
            self.b9_control
        )
        return buf

class CdbWrite6(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.WRITE_6
        self.b1_rsvd = 0
        self.b1_lba_h = 0
        self.w2_lba_l = 0
        self.b4_transfer_length = 0
        self.b5_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBHBB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u5', self.b1_rsvd, self.b1_lba_h)[0],
            self.w2_lba_l,
            self.b4_transfer_length,
            self.b5_control
        )
        return buf
    
class CdbWrite10(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.WRITE_10
        self.b1_wrprotect = 0
        self.b1_dpo = 0
        self.b1_fua = 0
        self.b1_rsvd = 0
        self.b1_fua_nv = 0
        self.b1_obsolete = 0
        self.l2_lba = 0
        self.b6_rsvd = 0
        self.b6_group_number = 0
        self.w7_transfer_length = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBLBHB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u1u1u1u1u1', self.b1_wrprotect, self.b1_dpo, 
                           self.b1_fua, self.b1_rsvd, self.b1_fua_nv, self.b1_obsolete)[0],
            self.l2_lba,
            bitstruct.pack('u3u5', self.b6_rsvd, self.b6_group_number)[0],
            self.w7_transfer_length,
            self.b9_control
        )
        return buf

class CdbWrite16(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.WRITE_16
        self.b1_wrprotect = 0
        self.b1_dpo = 0
        self.b1_fua = 0
        self.b1_rsvd = 0
        self.b1_fua_nv = 0
        self.b1_rsvd2 = 0
        self.l2_lba_h = 0
        self.l6_lba_l = 0
        self.l10_transfer_length = 0
        self.b14_ignore = 0
        self.b14_rsvd = 0
        self.b14_group_number = 0
        self.b15_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBLLLBB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u1u1u1u1u1', self.b1_wrprotect, self.b1_dpo, 
                           self.b1_fua, self.b1_rsvd, self.b1_fua_nv, self.b1_rsvd2)[0],
            self.l2_lba_h, 
            self.l6_lba_l, 
            self.l10_transfer_length, 
            bitstruct.pack('u1u2u5', self.b14_ignore, self.b14_rsvd, self.b14_group_number)[0],
            self.b15_control
        )
        return buf

class CdbWriteBuffer(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.WRITE_BUFFER
        self.b1_rsvd = 0
        self.b1_mode = 0
        self.b2_buffer_id = 0
        self.b3_buffer_offset_h = 0
        self.w4_buffer_offset_l = 0
        self.b6_allocation_length_h = 0
        self.w7_allocation_length_l = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBHBHB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u5', self.b1_rsvd, self.b1_mode)[0],
            self.b2_buffer_id,
            self.b3_buffer_offset_h,
            self.w4_buffer_offset_l,
            self.b6_allocation_length_h,
            self.w7_allocation_length_l,
            self.b9_control
        )
        return buf

class CdbHpbRead(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.HPB_READ
        self.b1_rsvd = 0
        self.b1_dpo = 0
        self.b1_fua = 0
        self.b1_rsvd2 = 0
        self.l2_lba = 0
        self.l6_hpb_entry_h = 0
        self.l10_hpb_entry_l = 0
        self.b14_transfer_length = 0
        self.b15_hpb_read_id = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBLLLBB', buf, 0,
            self.b0_opcode,
            bitstruct.pack('u3u1u1u3', self.b1_rsvd, self.b1_dpo, self.b1_fua, self.b1_rsvd2)[0],
            self.l2_lba,
            self.l6_hpb_entry_h,
            self.l10_hpb_entry_l,
            self.b14_transfer_length,
            self.b15_hpb_read_id
        )
        return buf

class CdbHpbReadBuffer(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.HPB_READ_BUFFER
        self.b1_bufferid = 0
        self.w2_hpb_region = 0
        self.w4_hpb_subregion = 0
        self.b6_allocation_length_h = 0
        self.w7_allocation_length_l = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBHHBHB', buf, 0,
            self.b0_opcode,
            self.b1_bufferid,
            self.w2_hpb_region,
            self.w4_hpb_subregion,
            self.b6_allocation_length_h,
            self.w7_allocation_length_l,
            self.b9_control
        )
        return buf

class CdbHpbWriteBuffer01(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.HPB_WRITE_BUFFER
        self.b1_buffer_id = 0x01
        self.w2_hpb_region = 0
        self.b4_rsvd = 0
        self.l5_rsvd = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBHBLB', buf, 0,
            self.b0_opcode,
            self.b1_buffer_id,
            self.w2_hpb_region,
            self.b4_rsvd,
            self.l5_rsvd,
            self.b9_control
        )
        return buf

class CdbHpbWriteBuffer02(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.HPB_WRITE_BUFFER
        self.b1_buffer_id = 0x02
        self.l2_lba = 0
        self.b6_hpb_read_id = 0
        self.w7_param_list_length = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBLBHB', buf, 0,
            self.b0_opcode,
            self.b1_buffer_id,
            self.l2_lba,
            self.b6_hpb_read_id,
            self.w7_param_list_length,
            self.b9_control
        )
        return buf
    
class CdbHpbWriteBuffer03(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_opcode = ScsiCmd.HPB_WRITE_BUFFER
        self.b1_buffer_id = 0x03
        self.b2_rsvd = 0
        self.l3_rsvd = 0
        self.w7_rsvd = 0
        self.b9_control = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBLHB', buf, 0,
            self.b0_opcode,
            self.b1_buffer_id,
            self.b2_rsvd,
            self.l3_rsvd,
            self.w7_rsvd,
            self.b9_control
        )
        return buf

class CdbVendorCmd(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_cmd_code = 0x06
        self.b1_cmd_index = 0
        self.b2_rsvd = 0
        self.b3_rsvd = 0
        self.b4_cmd0 = 0
        self.b5_cmd1 = 0
        self.b6_cmd2 = 0
        self.b7_cmd3 = 0
        self.l8_pw_h = 0
        self.l12_pw_l = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBBBBBLL', buf, 0,
            self.b0_cmd_code,
            self.b1_cmd_index,
            self.b2_rsvd,
            self.b3_rsvd,
            self.b4_cmd0,
            self.b5_cmd1,
            self.b6_cmd2,
            self.b7_cmd3,
            self.l8_pw_h,
            self.l12_pw_l
        )
        return buf

class SfReadDescriptor(PacketComposerABC, PacketParserABC):
    def __init__(self) -> None:
        self.b12_opcode = QueryFunctionOpcode.READ_DESCRIPTOR
        self.b13_idn = 0
        self.b14_index = 0
        self.b15_selector = 0
        self.b16_rsvd = 0
        self.b17_rsvd = 0
        self.w18_length = 0
        self.l20_rsvd = 0
        self.l24_rsvd = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBBBHLL', buf, 0,
            self.b12_opcode,
            self.b13_idn,
            self.b14_index,
            self.b15_selector,
            self.b16_rsvd,
            self.b17_rsvd,
            self.w18_length,
            self.l20_rsvd,
            self.l24_rsvd
        )
        return buf
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBBBHLL'
        unpacked_data = struct.unpack(format_string, payload[0:16])
        self.b13_idn = unpacked_data[1]
        self.b14_index = unpacked_data[2]
        self.b15_selector = unpacked_data[3]
        self.w18_length = unpacked_data[6]

class SfWriteDescriptor(PacketComposerABC, PacketParserABC):
    def __init__(self) -> None:
        self.b12_opcode = QueryFunctionOpcode.WRITE_DESCRIPTOR
        self.b13_idn = 0
        self.b14_index = 0
        self.b15_selector = 0
        self.b16_rsvd = 0
        self.b17_rsvd = 0
        self.w18_length = 0
        self.l20_rsvd = 0
        self.l24_rsvd = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBBBHLL', buf, 0,
            self.b12_opcode,
            self.b13_idn,
            self.b14_index,
            self.b15_selector,
            self.b16_rsvd,
            self.b17_rsvd,
            self.w18_length,
            self.l20_rsvd,
            self.l24_rsvd
        )
        return buf
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBBBHLL'
        unpacked_data = struct.unpack(format_string, payload[0:16])
        self.b13_idn = unpacked_data[1]
        self.b14_index = unpacked_data[2]
        self.b15_selector = unpacked_data[3]
        self.w18_length = unpacked_data[6]

class SfReadAttribute(PacketComposerABC, PacketParserABC):
    def __init__(self) -> None:
        self.b12_opcode = QueryFunctionOpcode.READ_ATTRIBUTE
        self.b13_idn = 0
        self.b14_index = 0
        self.b15_selector = 0
        self.q16_value = 0
        self.l24_rsvd = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBQL', buf, 0,
            self.b12_opcode,
            self.b13_idn,
            self.b14_index,
            self.b15_selector,
            self.q16_value,
            self.l24_rsvd
        )
        return buf
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBQL'
        unpacked_data = struct.unpack(format_string, payload[0:16])
        self.b13_idn = unpacked_data[1]
        self.b14_index = unpacked_data[2]
        self.b15_selector = unpacked_data[3]
        self.q16_value = unpacked_data[4]

class SfWriteAttribute(PacketComposerABC, PacketParserABC):
    def __init__(self) -> None:
        self.b12_opcode = QueryFunctionOpcode.WRITE_ATTRIBUTE
        self.b13_idn = 0
        self.b14_index = 0
        self.b15_selector = 0
        self.q16_value = 0
        self.l24_rsvd = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBQL', buf, 0,
            self.b12_opcode,
            self.b13_idn,
            self.b14_index,
            self.b15_selector,
            self.q16_value,
            self.l24_rsvd
        )
        return buf
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBQL'
        unpacked_data = struct.unpack(format_string, payload[0:16])
        self.b13_idn = unpacked_data[1]
        self.b14_index = unpacked_data[2]
        self.b15_selector = unpacked_data[3]
        self.q16_value = unpacked_data[4]

class SfReadFlag(PacketComposerABC, PacketParserABC):
    def __init__(self) -> None:
        self.b12_opcode = QueryFunctionOpcode.READ_FLAG
        self.b13_idn = 0
        self.b14_index = 0
        self.b15_selector = 0
        self.l16_rsvd = 0
        self.b20_rsvd = 0
        self.b21_rsvd = 0
        self.b22_rsvd = 0
        self.b23_flag_value = 0
        self.l24_rsvd = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBLBBBBL', buf, 0,
            self.b12_opcode,
            self.b13_idn,
            self.b14_index,
            self.b15_selector,
            self.l16_rsvd,
            self.b20_rsvd,
            self.b21_rsvd,
            self.b22_rsvd,
            self.b23_flag_value,
            self.l24_rsvd
        )
        return buf
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBLBBBBL'
        unpacked_data = struct.unpack(format_string, payload[0:16])
        self.b13_idn = unpacked_data[1]
        self.b14_index = unpacked_data[2]
        self.b15_selector = unpacked_data[3]
        self.b23_flag_value = unpacked_data[8]

class SfSetFlag(PacketComposerABC, PacketParserABC):
    def __init__(self) -> None:
        self.b12_opcode = QueryFunctionOpcode.SET_FLAG
        self.b13_idn = 0
        self.b14_index = 0
        self.b15_selector = 0
        self.l16_rsvd = 0
        self.b20_rsvd = 0
        self.b21_rsvd = 0
        self.b22_rsvd = 0
        self.b23_flag_value = 0
        self.l24_rsvd = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBLBBBBL', buf, 0,
            self.b12_opcode,
            self.b13_idn,
            self.b14_index,
            self.b15_selector,
            self.l16_rsvd,
            self.b20_rsvd,
            self.b21_rsvd,
            self.b22_rsvd,
            self.b23_flag_value,
            self.l24_rsvd
        )
        return buf
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBLBBBBL'
        unpacked_data = struct.unpack(format_string, payload[0:16])
        self.b13_idn = unpacked_data[1]
        self.b14_index = unpacked_data[2]
        self.b15_selector = unpacked_data[3]
        self.b23_flag_value = unpacked_data[8]

class SfClearFlag(PacketComposerABC, PacketParserABC):
    def __init__(self) -> None:
        self.b12_opcode = QueryFunctionOpcode.CLEAR_FLAG
        self.b13_idn = 0
        self.b14_index = 0
        self.b15_selector = 0
        self.l16_rsvd = 0
        self.b20_rsvd = 0
        self.b21_rsvd = 0
        self.b22_rsvd = 0
        self.b23_flag_value = 0
        self.l24_rsvd = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBLBBBBL', buf, 0,
            self.b12_opcode,
            self.b13_idn,
            self.b14_index,
            self.b15_selector,
            self.l16_rsvd,
            self.b20_rsvd,
            self.b21_rsvd,
            self.b22_rsvd,
            self.b23_flag_value,
            self.l24_rsvd
        )
        return buf
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBLBBBBL'
        unpacked_data = struct.unpack(format_string, payload[0:16])
        self.b13_idn = unpacked_data[1]
        self.b14_index = unpacked_data[2]
        self.b15_selector = unpacked_data[3]
        self.b23_flag_value = unpacked_data[8]

class SfToggleFlag(PacketComposerABC, PacketParserABC):
    def __init__(self) -> None:
        self.b12_opcode = QueryFunctionOpcode.TOGGLE_FLAG
        self.b13_idn = 0
        self.b14_index = 0
        self.b15_selector = 0
        self.l16_rsvd = 0
        self.b20_rsvd = 0
        self.b21_rsvd = 0
        self.b22_rsvd = 0
        self.b23_flag_value = 0
        self.l24_rsvd = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBLBBBBL', buf, 0,
            self.b12_opcode,
            self.b13_idn,
            self.b14_index,
            self.b15_selector,
            self.l16_rsvd,
            self.b20_rsvd,
            self.b21_rsvd,
            self.b22_rsvd,
            self.b23_flag_value,
            self.l24_rsvd
        )
        return buf
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBLBBBBL'
        unpacked_data = struct.unpack(format_string, payload[0:16])
        self.b13_idn = unpacked_data[1]
        self.b14_index = unpacked_data[2]
        self.b15_selector = unpacked_data[3]
        self.b23_flag_value = unpacked_data[8]

class SfNop(PacketComposerABC, PacketParserABC):
    def __init__(self) -> None:
        self.b12_opcode = QueryFunctionOpcode.NOP
        self.b13_rsvd = 0
        self.b14_rsvd = 0
        self.b15_rsvd = 0
        self.l16_rsvd = 0
        self.l20_rsvd = 0
        self.l24_rsvd = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(16)
        struct.pack_into(
            '>BBBBLLL', buf, 0,
            self.b12_opcode,
            self.b13_rsvd,
            self.b14_rsvd,
            self.b15_rsvd,
            self.l16_rsvd,
            self.l20_rsvd,
            self.l24_rsvd
        )
        return buf
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBLLL'
        unpacked_data = struct.unpack(format_string, payload[0:16])

class NopOutUpiu(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_transaction_type = UPIUTransactionType.NOP_OUT
        self.b1_flags = 0
        self.b2_rsvd = 0
        self.b3_tasktag = -1
        self.l4_rsvd = 0
        self.b8_total_ehs_length = 0
        self.b9_rsvd = 0
        self.w10_data_segment_length = 0
        self.l12_rsvd = 0
        self.l16_rsvd = 0
        self.l20_rsvd = 0
        self.l24_rsvd = 0
        self.l28_rsvd = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(32)
        struct.pack_into(
            '>BBBBLBBHLLLLL', buf, 0,
            self.b0_transaction_type,
            self.b1_flags,
            self.b2_rsvd,
            self.b3_tasktag,
            self.l4_rsvd,
            self.b8_total_ehs_length,
            self.b9_rsvd,
            self.w10_data_segment_length,
            self.l12_rsvd,
            self.l16_rsvd,
            self.l20_rsvd,
            self.l24_rsvd,
            self.l28_rsvd
        )
        return buf

class CommandUpiu(PacketComposerABC, Generic[T]):
    def __init__(self, cdb: T) -> None:
        self.b0_transaction_type = UPIUTransactionType.CMD
        self.b1_flags = 0
        self.b2_lun = 0
        self.b3_tasktag = -1
        self.b4_iid = 0
        self.b4_command_set_type = 0
        self.b5_rsvd = 0
        self.b6_rsvd = 0
        self.b7_ext_iid = 0
        self.b7_rsvd = 0
        self.b8_total_ehs_length = 0
        self.b9_rsvd = 0
        self.w10_data_segment_length = 0
        self.l12_expected_data_length = 0
        self.u16_cdb: T = cdb
    def to_bytes(self) -> bytearray:
        buf = bytearray(32)
        struct.pack_into(
            '>BBBBBBBBBBHL', buf, 0,
            self.b0_transaction_type,
            self.b1_flags,
            self.b2_lun,
            self.b3_tasktag,
            bitstruct.pack('u4u4', self.b4_iid, self.b4_command_set_type)[0],
            self.b5_rsvd,
            self.b6_rsvd,
            bitstruct.pack('u4u4', self.b7_ext_iid, self.b7_rsvd)[0],
            self.b8_total_ehs_length,
            self.b9_rsvd,
            self.w10_data_segment_length,
            self.l12_expected_data_length
        )
        buf[16:32] = self.u16_cdb.to_bytes()
        return buf

class TaskMngmtRequestUpiu(PacketComposerABC):
    def __init__(self) -> None:
        self.b0_transaction_type = UPIUTransactionType.TM_REQ
        self.b1_flags = 0
        self.b2_lun = 0
        self.b3_tasktag = -1
        self.b4_iid = 0
        self.b4_rsvd = 0
        self.b5_task_manag_function = 0
        self.b6_rsvd = 0        
        self.b7_rsvd = 0
        self.b8_total_ehs_length = 0
        self.b9_rsvd = 0
        self.w10_data_segment_length = 0
        self.l12_input_parameter1 = 0
        self.l16_input_parameter2 = 0
        self.l20_input_parameter3 = 0
        self.l24_rsvd = 0
        self.l28_rsvd = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(32)
        struct.pack_into(
            '>BBBBBBBBBBHLLLLL', buf, 0,
            self.b0_transaction_type,
            self.b1_flags,
            self.b2_lun,
            self.b3_tasktag,
            self.b4_iid,
            self.b5_task_manag_function,
            self.b6_rsvd,
            self.b7_rsvd,
            self.b8_total_ehs_length,
            self.b9_rsvd,
            self.w10_data_segment_length,
            self.l12_input_parameter1,
            self.l16_input_parameter2,
            self.l20_input_parameter3,
            self.l24_rsvd,
            self.l28_rsvd
        )
        return buf

class QueryRequestUpiu(PacketComposerABC, Generic[T]):
    def __init__(self, specific_fields: T) -> None:
        self.b0_transaction_type = UPIUTransactionType.QRY_REQ
        self.b1_flags = 0
        self.b2_rsvd = 0
        self.b3_tasktag = -1
        self.b4_rsvd = 0
        self.b5_query_function = 0
        self.b6_rsvd = 0
        self.b7_rsvd = 0
        self.b8_total_ehs_length = 0
        self.b9_rsvd = 0
        self.w10_data_segment_length = 0
        self.u12_specific_fields: T = specific_fields
        self.l28_rsvd = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(32)
        struct.pack_into(
            '>BBBBBBBBBBH', buf, 0,
            self.b0_transaction_type,
            self.b1_flags,
            self.b2_rsvd,
            self.b3_tasktag,
            self.b4_rsvd,
            self.b5_query_function,
            self.b6_rsvd,
            self.b7_rsvd,
            self.b8_total_ehs_length,
            self.b9_rsvd,
            self.w10_data_segment_length
        )
        buf[12:28] = self.u12_specific_fields.to_bytes()
        struct.pack_into('>L', buf, 28, self.l28_rsvd)
        return buf

class UnmapBlockDescriptor(PacketComposerABC):
    def __init__(self) -> None:
        self.l0_lba_h = 0
        self.l4_lba_l = 0
        self.l8_number_of_logical_blocks = 0
        self.l12_rsvd = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(12)
        struct.pack_into(
            '>LLLL', buf, 0,
            self.l0_lba_h,
            self.l4_lba_l,
            self.l8_number_of_logical_blocks,
            self.l12_rsvd
        )
        return buf

class UnmapParameterList(PacketComposerABC):
    def __init__(self) -> None:
        self.w0_unmap_data_length = 0
        self.w2_unmap_block_descriptor_data_length = 0
        self.l4_rsvd = 0
        self.unmap_block_descriptor: list[UnmapBlockDescriptor] = []
    def to_bytes(self) -> bytearray:         
        total_length = 8 + len(self.unmap_block_descriptor) * 16  # 每個 BlockDescriptor 占 16 字元
        buf = bytearray(total_length)

        struct.pack_into(
            '>HHL', buf, 0,
            self.w0_unmap_data_length,
            self.w2_unmap_block_descriptor_data_length,
            self.l4_rsvd
        )

        offset = 8  # 從第 8 字元開始
        for block in self.unmap_block_descriptor:
            struct.pack_into(
                '>LLLL',
                buf, offset,
                block.l0_lba_h,
                block.l4_lba_l,
                block.l8_number_of_logical_blocks,
                block.l12_rsvd
            )
            offset += 16  # 每個 BlockDescriptor 占 16 字元

        return buf

class Ehs(PacketComposerABC, PacketParserABC):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_ehs_type = 0
        self.w2_ehs_subtype = 0
        self.ehs_data = bytearray()
    def to_bytes(self) -> bytearray:
        if self.b0_length == 0:
            return bytearray()
        total_length = self.b0_length * 32
        buf = bytearray(total_length)
        struct.pack_into(
            '>BBH', buf, 0,
            self.b0_length,
            self.b1_ehs_type,
            self.w2_ehs_subtype
        )
        buf[4: 4+len(self.ehs_data)] = self.ehs_data
        return buf
    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBH', payload[0:4])
        self.b0_length = unpacked_data[0]
        self.b1_ehs_type = unpacked_data[1]
        self.w2_ehs_subtype = unpacked_data[2]
        self.ehs_data = payload[4:len(payload)]
    
class ResponseUpiu(PacketParserABC):
    def __init__(self) -> None:
        self.b0_transaction_type = UPIUTransactionType.RSP
        self.b1_flags = 0
        self.b2_lun = 0
        self.b3_tasktag = 0
        self.b4_iid = 0
        self.b4_command_set_type = 0
        self.b5_ext_iid = 0
        self.b5_rsvd = 0
        self.b6_response = 0
        self.b7_status = 0
        self.b8_total_ehs_length = 0
        self.b9_device_information = 0
        self.w10_data_segment_length = 0
        self.l12_residual_transfer_count = 0
    
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBBBBBBBHL'
        unpacked_data = struct.unpack(format_string, payload[0:16])

        self.b1_flags = unpacked_data[1]
        self.b2_lun = unpacked_data[2]
        self.b3_tasktag = unpacked_data[3]
        self.b4_iid = unpacked_data[4]
        self.b4_command_set_type = unpacked_data[4]
        self.b5_ext_iid = unpacked_data[5]
        self.b5_rsvd = unpacked_data[5]
        self.b6_response = unpacked_data[6]
        self.b7_status = unpacked_data[7]
        self.b8_total_ehs_length = unpacked_data[8]
        self.b9_device_information = unpacked_data[9]
        self.w10_data_segment_length = unpacked_data[10]
        self.l12_residual_transfer_count = unpacked_data[11]

class SenseData(PacketParserABC):
    def __init__(self) -> None:
        self.w_sense_data_length = 0
        self.b0_valid = 0
        self.b0_response_code = 0
        self.b1_obsolete = 0
        self.b2_filemark = 0
        self.b2_eom = 0
        self.b2_ili = 0
        self.b2_rsvd = 0
        self.b2_sense_key = 0
        self.l3_information = 0
        self.b7_additional_sense_length = 0
        self.l8_command_specific_information = 0
        self.b12_asc = 0
        self.b13_ascq = 0
        self.b14_fruc = 0
        self.w15_sksv = 0
        self.w15_sense_key_specific = 0
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>HBBBLBLBBBBH'
        unpacked_data = struct.unpack(format_string, payload[0:20])
        self.w_sense_data_length = unpacked_data[0]
        self.b0_valid, self.b0_response_code = bitstruct.unpack('>u1u7', int.to_bytes(payload[2]))
        self.b1_obsolete = unpacked_data[2]
        self.b2_filemark, self.b2_eom, self.b2_ili, self.b2_rsvd, self.b2_sense_key = \
            bitstruct.unpack('>u1u1u1u1u4', int.to_bytes(payload[4]))
        self.l3_information = unpacked_data[4]
        self.b7_additional_sense_length = unpacked_data[5]
        self.l8_command_specific_information = unpacked_data[6]
        self.b12_asc = unpacked_data[7]
        self.b13_ascq = unpacked_data[8]
        self.b14_fruc = unpacked_data[9]
        self.w15_sksv, self.w15_sense_key_specific = bitstruct.unpack('>u1u23', payload[17:20])

class TaskMngmtResponseUpiu(PacketParserABC):
    def __init__(self) -> None:
        self.b0_transaction_type = UPIUTransactionType.TM_RSP
        self.b1_flags = 0
        self.b2_lun = 0
        self.b3_tasktag = 0
        self.b4_iid = 0
        self.b4_rsvd = 0
        self.b5_ext_iid = 0
        self.b5_rsvd = 0
        self.b6_response = 0       
        self.b7_rsvd = 0
        self.b8_total_ehs_length = 0
        self.b9_rsvd = 0
        self.w10_data_segment_length = 0
        self.l12_output_parameter1 = 0
        self.l16_output_parameter2 = 0
        self.l20_rsvd = 0
        self.l24_rsvd = 0
        self.l28_rsvd = 0
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBBBBBBBHLL'
        unpacked_data = struct.unpack(format_string, payload[0:20])
        self.b1_flags = unpacked_data[1]
        self.b2_lun = unpacked_data[2]
        self.b3_tasktag = unpacked_data[3]
        self.b4_iid = unpacked_data[4]
        self.b5_ext_iid = unpacked_data[5]
        self.b5_rsvd = unpacked_data[5]
        self.b6_response = unpacked_data[6]
        self.b8_total_ehs_length = unpacked_data[8]
        self.w10_data_segment_length = unpacked_data[10]
        self.l12_output_parameter1 = unpacked_data[11]
        self.l16_output_parameter2 = unpacked_data[12]

class QueryResponseUpiu(PacketParserABC):
    def __init__(self) -> None:
        self.b0_transaction_type = UPIUTransactionType.QRY_RSP
        self.b1_flags = 0
        self.b2_rsvd = 0
        self.b3_tasktag = 0
        self.b4_rsvd = 0
        self.b5_query_function = 0
        self.b6_query_response = 0
        self.b7_rsvd = 0
        self.b8_total_ehs_length = 0
        self.b9_device_information = 0
        self.w10_data_segment_length = 0
        self.u12_specific_fields = bytearray(16)
        self.l28_rsvd = 0
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBBBBBBBH'
        unpacked_data = struct.unpack(format_string, payload[0:12])
        self.b1_flags = unpacked_data[1]
        self.b3_tasktag = unpacked_data[3]
        self.b5_query_function = unpacked_data[5]
        self.b6_query_response = unpacked_data[6]
        self.b8_total_ehs_length = unpacked_data[8]
        self.b9_device_information = unpacked_data[9]
        self.w10_data_segment_length = unpacked_data[10]
        self.u12_specific_fields = payload[12:28]

class NopInUpiu(PacketParserABC):
    def __init__(self) -> None:
        self.b0_transaction_type = UPIUTransactionType.NOP_IN
        self.b1_flags = 0
        self.b2_rsvd = 0
        self.b3_tasktag = 0
        self.b4_rsvd = 0
        self.b5_rsvd = 0
        self.b6_response = 0
        self.b7_rsvd = 0
        self.b8_total_ehs_length = 0
        self.b9_device_information = 0
        self.w10_data_segment_length = 0
        self.l12_rsvd = 0
        self.l16_rsvd = 0
        self.l20_rsvd = 0
        self.l24_rsvd = 0
        self.l28_rsvd = 0
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>BBBBBBBBBBHLLLLL'
        unpacked_data = struct.unpack(format_string, payload[0:32])
        self.b1_flags = unpacked_data[1]
        self.b3_tasktag = unpacked_data[3]
        self.b6_response = unpacked_data[6]
        self.b8_total_ehs_length = unpacked_data[8]
        self.b9_device_information = unpacked_data[9]
        self.w10_data_segment_length = unpacked_data[10]

class EhsAdvRpmb(PacketComposerABC, PacketParserABC):
    def __init__(self) -> None:
        self.b0_length = 0
        self.b1_ehs_type = 0
        self.w2_ehs_subtype = 0
        self.meta_info = AdvRpmbMetaInfo()
        self.mac_key = bytearray(32)
    def to_bytes(self) -> bytearray:
        if self.b0_length == 0:
            return bytearray()
        total_length = self.b0_length * 32
        buf = bytearray(total_length)
        struct.pack_into(
            '>BBH', buf, 0,
            self.b0_length,
            self.b1_ehs_type,
            self.w2_ehs_subtype
        )
        buf[4:32] = self.meta_info.to_bytes()
        buf[32:64] = self.mac_key
        return buf
    def from_bytes(self, payload: bytearray) -> None:
        unpacked_data = struct.unpack('>BBH', payload[0:4])
        self.b0_length = unpacked_data[0]
        self.b1_ehs_type = unpacked_data[1]
        self.w2_ehs_subtype = unpacked_data[2]
        self.meta_info.from_bytes(payload[4:32])
        self.mac_key = payload[32:64]

class AdvRpmbMetaInfo(PacketComposerABC, PacketParserABC):
    def __init__(self) -> None:
        self.w0_message_type = 0
        self.dq2_nonce = bytearray(16)
        self.l18_write_counter = 0
        self.w22_address_lun = 0
        self.w24_block_count = 0
        self.w26_result = 0
    def to_bytes(self) -> bytearray:
        buf = bytearray(28)
        struct.pack_into(
            '>H16sLHHH', buf, 0,
            self.w0_message_type,
            bytes(self.dq2_nonce),
            self.l18_write_counter,
            self.w22_address_lun,
            self.w24_block_count,
            self.w26_result
        )
        return buf
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>H16sLHHH'
        unpacked_data = struct.unpack(format_string, payload[0:28])

        self.w0_message_type = unpacked_data[0]
        self.dq2_nonce = bytearray(unpacked_data[1])
        self.l18_write_counter = unpacked_data[2]
        self.w22_address_lun = unpacked_data[3]
        self.w24_block_count = unpacked_data[4]
        self.w26_result = unpacked_data[5]