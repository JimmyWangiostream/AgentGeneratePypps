from __future__ import annotations
from copy import deepcopy
from typing import Any, Self, TYPE_CHECKING
from Script.api.exception import PATTERN_ASSERT_RPMB_MAC_OR_KEY_SHALL_BE_32B, PATTERN_ASSERT_VALUE_EXCEEDS_FIELD_MAX_VALUE, PATTERN_ASSERT_VALUE_SHALL_NOT_BE_NAGTIVE
from Script.api.ufs_api.defines.enum_define import *
from Script.api.ufs_api.defines.bit_define import *
from Script.api.ufs_api.upiu.protocols import IsUpiu
from Script.api.ufs_api.upiu.structs import AdvRpmbMetaInfo, CdbFormatUnit, CdbHpbRead, CdbHpbReadBuffer, CdbHpbWriteBuffer01, CdbHpbWriteBuffer02, CdbHpbWriteBuffer03, CdbInquiry, CdbModeSelect10, CdbModeSense10, CdbPreFetch10, CdbPreFetch16, CdbRead10, CdbRead16, CdbRead6, CdbReadBuffer, CdbReadCapacity10, CdbReadCapacity16, CdbReportLUNs, CdbRequestSense, CdbSecurityProtocolIn, CdbSecurityProtocolOut, CdbSendDiagnostic, CdbStartStopUnit, CdbSyncCache10, CdbSyncCache16, CdbTestUnitReady, CdbUnmap, CdbVendorCmd, CdbVerify10, CdbWrite10, CdbWrite16, CdbWrite6, CdbWriteBuffer, CommandUpiu, EhsAdvRpmb, NopOutUpiu, QueryRequestUpiu, SfClearFlag, SfReadAttribute, SfReadDescriptor, SfReadFlag, SfSetFlag, SfToggleFlag, SfWriteAttribute, SfWriteDescriptor, TaskMngmtRequestUpiu, UnmapBlockDescriptor, UnmapParameterList
from Script.api import shared

if TYPE_CHECKING:
    from Script.api.ufs_api.descriptors.configuration_desc.structs import ConfigDescriptor

_log = shared.logger

class BaseNopOut(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu = NopOutUpiu()

class BaseFormatUnit(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbFormatUnit] = CommandUpiu(CdbFormatUnit())
        self.upiu.b1_flags = UPIUCmdFlag.NO_DATA
    def assign(self, lun: int, longlist: int = 0, cmplist: int = 1) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(longlist, 1)
        chk_over_under_flow(cmplist, 1)
        self.upiu.b2_lun = lun
        self.upiu.u16_cdb.b1_longlist = longlist
        self.upiu.u16_cdb.b1_cmplst = cmplist
        return self

class BaseInquiry(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbInquiry] = CommandUpiu(CdbInquiry())
        self.upiu.b1_flags = UPIUCmdFlag.READ
    def assign(self, lun: int, evpd: int = 1, page_code: int = 0xB0, length: int = 64) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(evpd, 1)
        chk_over_under_flow(page_code, 8)
        chk_over_under_flow(length, 16)
        self.upiu.b2_lun = lun
        self.upiu.l12_expected_data_length = length
        self.upiu.u16_cdb.b1_evpd = evpd
        self.upiu.u16_cdb.b2_page_code = page_code
        self.upiu.u16_cdb.w3_allocation_length = length
        return self

class BaseModeSelect10(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbModeSelect10] = CommandUpiu(CdbModeSelect10())
        self.upiu.b1_flags = UPIUCmdFlag.WRITE
    def assign(self, lun: int, sp: int = 1, length: int = 0) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(sp, 1)
        chk_over_under_flow(length, 32)
        self.upiu.b2_lun = lun
        self.upiu.l12_expected_data_length = length
        self.upiu.u16_cdb.b1_sp = sp
        self.upiu.u16_cdb.w7_parameter_list_length = length
        return self

class BaseModeSense10(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbModeSense10] = CommandUpiu(CdbModeSense10())
        self.upiu.b1_flags = UPIUCmdFlag.READ
    def assign(self, lun: int, pc: int = 0, page_code: int = 8, subpage_code: int = 0, length: int = 28) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(pc, 2)
        chk_over_under_flow(page_code, 6)
        chk_over_under_flow(subpage_code, 8)
        chk_over_under_flow(length, 16)
        self.upiu.b2_lun = lun
        self.upiu.l12_expected_data_length = length
        self.upiu.u16_cdb.b2_pc = pc
        self.upiu.u16_cdb.b2_page_code = page_code
        self.upiu.u16_cdb.b3_subpage_code = subpage_code
        self.upiu.u16_cdb.w7_allocation_length = length
        return self

class BasePreFetch10(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbPreFetch10] = CommandUpiu(CdbPreFetch10())
    def assign(self, lun: int, immed: int, lba: int, length: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(immed, 1)
        chk_over_under_flow(lba, 32)
        chk_over_under_flow(length, 16)
        self.upiu.b2_lun = lun
        self.upiu.u16_cdb.b1_immed = immed
        self.upiu.l12_expected_data_length = length
        self.upiu.u16_cdb.l2_lba = lba
        self.upiu.u16_cdb.w7_prefetch_length = length
        return self

class BasePreFetch16(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbPreFetch16] = CommandUpiu(CdbPreFetch16())
    def assign(self, lun: int, immed: int, lba: int, length: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(immed, 1)
        chk_over_under_flow(lba, 64)
        chk_over_under_flow(length, 32)
        self.upiu.b2_lun = lun
        self.upiu.u16_cdb.b1_immed = immed
        self.upiu.l12_expected_data_length = length
        self.upiu.u16_cdb.l2_lba_h = 0xFFFFFFFF & (lba >> 32)
        self.upiu.u16_cdb.l6_lba_l = 0xFFFFFFFF & lba
        self.upiu.u16_cdb.l10_prefetch_length = length
        return self

class BaseRead6(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbRead6] = CommandUpiu(CdbRead6())
        self.upiu.b1_flags = UPIUCmdFlag.READ
    def assign(self, lun: int, lba: int, length: int) -> Self:
        rw6_assign(self.upiu, lun, lba, length)
        return self

class BaseRead10(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbRead10] = CommandUpiu(CdbRead10())
        self.upiu.b1_flags = UPIUCmdFlag.READ
    def assign(self, lun: int, lba: int, length: int, fua: int = 0) -> Self:
        rw_assign(self.upiu, lun, lba, length, fua)
        return self
        
class BaseRead16(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbRead16] = CommandUpiu(CdbRead16())
        self.upiu.b1_flags = UPIUCmdFlag.READ
    def assign(self, lun: int, lba: int, length: int, fua: int = 0) -> Self:
        rw16_assign(self.upiu, lun, lba, length, fua)
        return self

class BaseReadBuffer(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbReadBuffer] = CommandUpiu(CdbReadBuffer())
        self.upiu.b1_flags = UPIUCmdFlag.READ
    def assign(self, lun: int, mode: int, buffer_id: int, buffer_offset: int, length: int, vendor: bool = False) -> Self:
        rwbuf_assign(self.upiu, lun, mode, buffer_id, buffer_offset, length, vendor)
        return self
        
class BaseReadCapacity10(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbReadCapacity10] = CommandUpiu(CdbReadCapacity10())
        self.upiu.b1_flags = UPIUCmdFlag.READ
        self.upiu.l12_expected_data_length = 8
    def assign(self, lun: int) -> Self:
        chk_over_under_flow(lun, 8)
        self.upiu.b2_lun = lun
        return self

class BaseReadCapacity16(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbReadCapacity16] = CommandUpiu(CdbReadCapacity16())
        self.upiu.b1_flags = UPIUCmdFlag.READ
    def assign(self, lun: int, alloc_length: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(alloc_length, 32)
        self.upiu.b2_lun = lun
        self.upiu.l12_expected_data_length = alloc_length
        self.upiu.u16_cdb.l10_allocation_length = alloc_length
        return self


class BaseReportLUNs(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbReportLUNs] = CommandUpiu(CdbReportLUNs())
        self.upiu.b1_flags = UPIUCmdFlag.READ
    def assign(self, lun: int, sel_report: int, length: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(sel_report, 8)
        chk_over_under_flow(length, 32)
        self.upiu.b2_lun = lun
        self.upiu.l12_expected_data_length = length
        self.upiu.u16_cdb.b2_select_report = sel_report
        self.upiu.u16_cdb.l6_allocation_length = length        
        return self

class BaseRequestSense(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbRequestSense] = CommandUpiu(CdbRequestSense())
        self.upiu.b1_flags = UPIUCmdFlag.READ
    def assign(self, lun: int, length: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(length, 8)

        self.upiu.b2_lun = lun
        self.upiu.l12_expected_data_length = length
        self.upiu.u16_cdb.b4_allocation_length = length
        return self
        
class BaseSecurityProtocolIn(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbSecurityProtocolIn] = CommandUpiu(CdbSecurityProtocolIn())
        self.upiu.b1_flags = UPIUCmdFlag.READ
    def assign(self, lun: int, security_protocol: int, security_protocol_spec: int, allocation_length: int) -> Self:
        self.upiu.b2_lun = lun
        self.upiu.l12_expected_data_length = allocation_length
        self.upiu.u16_cdb.b1_security_protocol = security_protocol
        self.upiu.u16_cdb.w2_security_protocol_specific = security_protocol_spec
        self.upiu.u16_cdb.l6_allocation_length = allocation_length
        return self
    def set_adv_rpmb_ehs(self, meta_info: AdvRpmbMetaInfo, mac_or_key: bytearray=bytearray(32)) -> Self:
        self.ehs: EhsAdvRpmb
        _set_adv_rpmb_ehs(self, meta_info, mac_or_key)
        return self

class BaseSecurityProtocolOut(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbSecurityProtocolOut] = CommandUpiu(CdbSecurityProtocolOut())
        self.upiu.b1_flags = UPIUCmdFlag.WRITE
    def assign(self, lun: int, security_protocol: int, security_protocol_spec: int, transfer_length: int) -> Self:
        self.upiu.b2_lun = lun
        self.upiu.l12_expected_data_length = transfer_length
        self.upiu.u16_cdb.b1_security_protocol = security_protocol
        self.upiu.u16_cdb.w2_security_protocol_specific = security_protocol_spec
        self.upiu.u16_cdb.l6_transfer_length = transfer_length
        return self
    def set_adv_rpmb_ehs(self, meta_info: AdvRpmbMetaInfo, mac_or_key: bytearray=bytearray(32)) -> Self:
        self.ehs: EhsAdvRpmb
        _set_adv_rpmb_ehs(self, meta_info, mac_or_key)
        return self
        
class BaseSendDiagnostic(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbSendDiagnostic] = CommandUpiu(CdbSendDiagnostic())
        self.upiu.b1_flags = UPIUCmdFlag.NO_DATA
    def assign(self, lun: int, selftest_code: int, pf: int, selftest: int, dev: int, unit: int, length: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(selftest_code, 3)
        chk_over_under_flow(pf, 1)
        chk_over_under_flow(selftest, 1)
        chk_over_under_flow(dev, 1)
        chk_over_under_flow(unit, 1)
        chk_over_under_flow(length, 16)
        self.upiu.b2_lun = lun
        self.upiu.l12_expected_data_length = length
        self.upiu.u16_cdb.b1_self_test_code = selftest_code
        self.upiu.u16_cdb.b1_pf = pf
        self.upiu.u16_cdb.b1_selftest = selftest
        self.upiu.u16_cdb.b1_devoffl = dev
        self.upiu.u16_cdb.b1_unitoffl = unit
        self.upiu.u16_cdb.w3_parameter_list_length = length
        return self

class BaseStartStopUnit(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbStartStopUnit] = CommandUpiu(CdbStartStopUnit())
        self.upiu.b1_flags = UPIUCmdFlag.NO_DATA
    def assign(self, lun: int, immed: int, power_condition: int, no_flush: int, start: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(immed, 1)
        chk_over_under_flow(power_condition, 4)
        chk_over_under_flow(no_flush, 1)
        chk_over_under_flow(start, 1)
        self.upiu.b2_lun = lun
        self.upiu.u16_cdb.b1_immed = immed
        self.upiu.u16_cdb.b4_power_conditions = power_condition
        self.upiu.u16_cdb.b4_no_flush = no_flush
        self.upiu.u16_cdb.b4_start = start
        return self

class BaseSyncCache10(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbSyncCache10] = CommandUpiu(CdbSyncCache10())
        self.upiu.b1_flags = UPIUCmdFlag.NO_DATA
    def assign(self, lun: int, immed: int, lba: int, length: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(immed, 1)
        chk_over_under_flow(lba, 32)
        chk_over_under_flow(length, 16)
        self.upiu.b2_lun = lun
        self.upiu.u16_cdb.b1_immed = immed
        self.upiu.u16_cdb.l2_lba = lba
        self.upiu.u16_cdb.w7_number_of_logical_blocks = length
        return self

class BaseSyncCache16(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbSyncCache16] = CommandUpiu(CdbSyncCache16())
        self.upiu.b1_flags = UPIUCmdFlag.NO_DATA
    def assign(self, lun: int, immed: int, lba: int, length: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(immed, 1)
        chk_over_under_flow(lba, 64)
        chk_over_under_flow(length, 32)
        self.upiu.b2_lun = lun
        self.upiu.u16_cdb.b1_immed = immed
        self.upiu.u16_cdb.l2_lba_h = 0xFFFFFFFF & (lba >> 32)
        self.upiu.u16_cdb.l6_lba_l = 0xFFFFFFFF & lba
        self.upiu.u16_cdb.l10_number_of_logical_blocks = length
        return self

class BaseTestUnitReady(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbTestUnitReady] = CommandUpiu(CdbTestUnitReady())
        self.upiu.b1_flags = UPIUCmdFlag.NO_DATA
    def assign(self, lun: int) -> Self:
        chk_over_under_flow(lun, 8)
        self.upiu.b2_lun = lun
        return self

class BaseUnmap(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbUnmap] = CommandUpiu(CdbUnmap())
        self.upiu.b1_flags = UPIUCmdFlag.WRITE
        self._block_descriptors: list[UnmapBlockDescriptor] = []
    def assign(self, lun: int, lba: int, length: int) -> Self:
        self._block_descriptors.clear()
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(lba, 64)
        chk_over_under_flow(length, 32)

        blockdescriptor = UnmapBlockDescriptor()
        blockdescriptor.l0_lba_h = 0xFFFFFFFF & (lba >> 32)
        blockdescriptor.l4_lba_l = 0xFFFFFFFF & lba
        blockdescriptor.l8_number_of_logical_blocks = length

        paramlist = UnmapParameterList()        
        paramlist.w0_unmap_data_length = 22
        paramlist.w2_unmap_block_descriptor_data_length = 16
        paramlist.unmap_block_descriptor.append(blockdescriptor)
        self._block_descriptors.append(blockdescriptor)

        self.upiu.b2_lun = lun
        self.upiu.u16_cdb.w7_param_list_length = 24
        self.upiu.l12_expected_data_length = self.upiu.u16_cdb.w7_param_list_length
        
        self.data = paramlist.to_bytes()
        return self
    def assign_multi_cmd(self, lun: int, block_descriptor: list[UnmapBlockDescriptor]) -> Self:
        self._block_descriptors.clear()
        self._block_descriptors = deepcopy(block_descriptor)

        chk_over_under_flow(lun, 8)
        for desc in block_descriptor:
            chk_over_under_flow(desc.l0_lba_h, 32)
            chk_over_under_flow(desc.l4_lba_l, 32)
            chk_over_under_flow(desc.l8_number_of_logical_blocks, 32)

        paramlist = UnmapParameterList()
        paramlist.w0_unmap_data_length = len(block_descriptor) * 16 + 6
        paramlist.w2_unmap_block_descriptor_data_length = len(block_descriptor) * 16
        paramlist.unmap_block_descriptor = deepcopy(block_descriptor)
        chk_over_under_flow(paramlist.w0_unmap_data_length, 16)
        chk_over_under_flow(paramlist.w2_unmap_block_descriptor_data_length, 16)

        self.upiu.b2_lun = lun
        self.upiu.u16_cdb.w7_param_list_length = len(block_descriptor) * 16 + 8
        self.upiu.l12_expected_data_length = self.upiu.u16_cdb.w7_param_list_length

        self.data = paramlist.to_bytes()
        return self

class BaseVerify10(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbVerify10] = CommandUpiu(CdbVerify10())
        self.upiu.b1_flags = UPIUCmdFlag.NO_DATA
    def assign(self, lun: int, lba: int, length: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(lba, 32)
        chk_over_under_flow(length, 16)
        self.upiu.b2_lun = lun
        self.upiu.u16_cdb.l2_lba = lba
        self.upiu.u16_cdb.w7_verification_length = length
        return self

class BaseWrite6(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbWrite6] = CommandUpiu(CdbWrite6())
        self.upiu.b1_flags = UPIUCmdFlag.WRITE
    def assign(self, lun: int, lba: int, length: int) -> Self:
        rw6_assign(self.upiu, lun, lba, length)
        return self

class BaseWrite10(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbWrite10] = CommandUpiu(CdbWrite10())
        self.upiu.b1_flags = UPIUCmdFlag.WRITE
    def assign(self, lun: int, lba: int, length: int, fua: int) -> Self:
        rw_assign(self.upiu, lun, lba, length, fua)
        return self

class BaseWrite16(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbWrite16] = CommandUpiu(CdbWrite16())
        self.upiu.b1_flags = UPIUCmdFlag.WRITE
    def assign(self, lun: int, lba: int, length: int, fua: int) -> Self:
        rw16_assign(self.upiu, lun, lba, length, fua)
        return self

class BaseWriteBuffer(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbWriteBuffer] = CommandUpiu(CdbWriteBuffer())
        self.upiu.b1_flags = UPIUCmdFlag.WRITE
    def assign(self, lun: int, mode: int, buffer_id: int, buffer_offset: int, length: int, vendor: bool = False) -> Self:
        rwbuf_assign(self.upiu, lun, mode, buffer_id, buffer_offset, length, vendor)
        return self

class BaseTaskManagement(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: TaskMngmtRequestUpiu = TaskMngmtRequestUpiu()
    def assign(self, lun: int, iid: int, task_management_function: int, target_lun: int, target_tasktag: int, target_iid: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(task_management_function, 8)
        chk_over_under_flow(target_lun, 8)
        chk_over_under_flow(target_tasktag, 8)
        chk_over_under_flow(target_iid, 4)
        self.upiu.b2_lun = lun
        self.upiu.b4_iid = iid
        self.upiu.b5_task_manag_function = task_management_function
        self.upiu.l12_input_parameter1 = target_lun
        self.upiu.l16_input_parameter2 = target_tasktag
        self.upiu.l20_input_parameter3 = target_iid
        return self
    
class BaseHpbRead(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbHpbRead] = CommandUpiu(CdbHpbRead())
        self.upiu.b1_flags = UPIUCmdFlag.READ
    def assign(self, lun: int, lba: int, length: int, fua: int, hpb_entry: int, hpb_read_id: int) -> Self:
        rw_assign(self.upiu, lun, lba, length, fua)
        chk_over_under_flow(hpb_read_id, 8)
        self.upiu.u16_cdb.l6_hpb_entry_h = 0xFFFFFFFF & (hpb_entry >> 32)
        self.upiu.u16_cdb.l10_hpb_entry_l = 0xFFFFFFFF & hpb_entry
        self.upiu.u16_cdb.b14_transfer_length = length
        self.upiu.u16_cdb.b15_hpb_read_id = hpb_read_id
        return self

class BaseHpbReadBuffer(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbHpbReadBuffer] = CommandUpiu(CdbHpbReadBuffer())
        self.upiu.b1_flags = UPIUCmdFlag.READ
        self.upiu.u16_cdb.b1_bufferid = 0x1
    def assign(self, lun: int, hpb_region: int, hpb_subregion: int, allocation_length: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(hpb_region, 16)
        chk_over_under_flow(hpb_subregion, 16)
        chk_over_under_flow(allocation_length, 24)

        self.upiu.b2_lun = lun
        self.upiu.l12_expected_data_length = allocation_length        
        self.upiu.u16_cdb.w2_hpb_region = hpb_region
        self.upiu.u16_cdb.w4_hpb_subregion = hpb_subregion
        self.upiu.u16_cdb.b6_allocation_length_h = 0xFF & (allocation_length >> 16)
        self.upiu.u16_cdb.w7_allocation_length_l = 0xFFFF & allocation_length
        return self

class BaseHpbWriteBuffer01(IsUpiu): # host control mode only
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbHpbWriteBuffer01] = CommandUpiu(CdbHpbWriteBuffer01())
        self.upiu.b1_flags = UPIUCmdFlag.NO_DATA
    def assign(self, lun: int, hpb_region: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(hpb_region, 16)

        self.upiu.b2_lun = lun        
        self.upiu.u16_cdb.w2_hpb_region = hpb_region
        return self

class BaseHpbWriteBuffer02(IsUpiu): # any control mode
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbHpbWriteBuffer02] = CommandUpiu(CdbHpbWriteBuffer02())
        self.upiu.b1_flags = UPIUCmdFlag.WRITE
    def assign(self, lun: int, lba: int, hpb_read_id: int, param_list_length: int) -> Self:
        chk_over_under_flow(lun, 8)
        chk_over_under_flow(lba, 32)
        chk_over_under_flow(hpb_read_id, 8)
        chk_over_under_flow(param_list_length, 16)

        self.upiu.b2_lun = lun
        self.upiu.l12_expected_data_length = param_list_length
        self.upiu.u16_cdb.l2_lba = lba
        self.upiu.u16_cdb.b6_hpb_read_id = hpb_read_id
        self.upiu.u16_cdb.w7_param_list_length = param_list_length
        return self

class BaseHpbWriteBuffer03(IsUpiu): # device control mode only
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbHpbWriteBuffer03] = CommandUpiu(CdbHpbWriteBuffer03())
        self.upiu.b1_flags = UPIUCmdFlag.NO_DATA
    def assign(self, lun: int) -> Self:
        chk_over_under_flow(lun, 8)
        self.upiu.b2_lun = lun        
        return self

class BaseVendorCmdWrite(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbVendorCmd] = CommandUpiu(CdbVendorCmd())
        self.upiu.b1_flags = UPIUCmdFlag.WRITE
        self.upiu.b2_lun = 0xFF
        self.upiu.b3_tasktag = 0xFE
        self.upiu.b4_command_set_type = 0x0F
    def assign(self, length: int, cmd_index: int, cmd_set_type: int = 0x0F) -> Self:
        self.upiu.b4_command_set_type = cmd_set_type
        self.upiu.l12_expected_data_length = length
        self.upiu.u16_cdb.b1_cmd_index = cmd_index
        return self

class BaseVendorCmdRead(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbVendorCmd] = CommandUpiu(CdbVendorCmd())
        self.upiu.b1_flags = UPIUCmdFlag.READ
        self.upiu.b2_lun = 0xFF
        self.upiu.b3_tasktag = 0xFE
        self.upiu.b4_command_set_type = 0x0F
    def assign(self, length: int, cmd_index: int, cmd_set_type: int = 0x0F) -> Self:
        self.upiu.b4_command_set_type = cmd_set_type
        self.upiu.l12_expected_data_length = length
        self.upiu.u16_cdb.b1_cmd_index = cmd_index
        return self

class BaseVendorCmdNoWR(IsUpiu): 
    def __init__(self) -> None:
        super().__init__()
        self.upiu: CommandUpiu[CdbVendorCmd] = CommandUpiu(CdbVendorCmd())
        self.upiu.b1_flags = UPIUCmdFlag.NO_DATA
        self.upiu.b2_lun = 0xFF
        self.upiu.b3_tasktag = 0xFE
        self.upiu.b4_command_set_type = 0x0F
    def assign(self, cmd_index: int, cmd_set_type: int = 0x0F) -> Self:
        self.upiu.b4_command_set_type = cmd_set_type
        self.upiu.u16_cdb.b1_cmd_index = cmd_index
        return self

class BaseReadDescriptor(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: QueryRequestUpiu[SfReadDescriptor] = QueryRequestUpiu(SfReadDescriptor())
        self.upiu.b5_query_function = QueryFunction.STANDARD_READ_REQ
        self.upiu.u12_specific_fields.w18_length = 0xFF     #先設256，因為會填到cmd seq的l46_data length，不夠時再往上加
    def assign(self, idn: int, index: int = 0, selector: int = 0) -> Self:
        assign_idn(self.upiu, idn, index, selector)
        return self

class BaseWriteDescriptor(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: QueryRequestUpiu[SfWriteDescriptor] = QueryRequestUpiu(SfWriteDescriptor())
        self.upiu.b5_query_function = QueryFunction.STANDARD_WRITE_REQ
    def assign(self, idn: int, index: int, selector: int, length: int) -> Self:
        chk_over_under_flow(length, 16)
        assign_idn(self.upiu, idn, index, selector)

        self.upiu.w10_data_segment_length = length
        self.upiu.u12_specific_fields.w18_length = length
        return self
    
    def set_desc(self, configdescriptor: ConfigDescriptor) -> Self:
        self.data = configdescriptor.to_bytes()
        return self

class BaseReadAttribute(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: QueryRequestUpiu[SfReadAttribute] = QueryRequestUpiu(SfReadAttribute())
        self.upiu.b5_query_function = QueryFunction.STANDARD_READ_REQ
    def assign(self, idn: int, index: int = 0, selector: int = 0) -> Self:
        assign_idn(self.upiu, idn, index, selector)
        return self

class BaseWriteAttribute(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: QueryRequestUpiu[SfWriteAttribute] = QueryRequestUpiu(SfWriteAttribute())
        self.upiu.b5_query_function = QueryFunction.STANDARD_WRITE_REQ
    def assign(self, idn: int, index: int = 0, selector: int = 0) -> Self:
        assign_idn(self.upiu, idn, index, selector)
        return self
        
    def set_attr(self, value: int) -> Self:
        chk_over_under_flow(value, 64)
        self.upiu.u12_specific_fields.q16_value = value
        return self

class BaseReadFlag(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: QueryRequestUpiu[SfReadFlag] = QueryRequestUpiu(SfReadFlag())
        self.upiu.b5_query_function = QueryFunction.STANDARD_READ_REQ
    def assign(self, idn: int, index: int = 0, selector: int = 0) -> Self:
        assign_idn(self.upiu, idn, index, selector)
        return self

class BaseSetFlag(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: QueryRequestUpiu[SfSetFlag] = QueryRequestUpiu(SfSetFlag())
        self.upiu.b5_query_function = QueryFunction.STANDARD_WRITE_REQ
    def assign(self, idn: int, index: int = 0, selector: int = 0) -> Self:
        assign_idn(self.upiu, idn, index, selector)
        return self

    def set_flag(self, value: int) -> Self:
        chk_over_under_flow(value, 1)
        self.upiu.u12_specific_fields.b23_flag_value = value
        return self

class BaseClearFlag(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: QueryRequestUpiu[SfClearFlag] = QueryRequestUpiu(SfClearFlag())
        self.upiu.b5_query_function = QueryFunction.STANDARD_WRITE_REQ
    def assign(self, idn: int, index: int = 0, selector: int = 0) -> Self:
        assign_idn(self.upiu, idn, index, selector)
        return self

class BaseToggleFlag(IsUpiu):
    def __init__(self) -> None:
        super().__init__()
        self.upiu: QueryRequestUpiu[SfToggleFlag] = QueryRequestUpiu(SfToggleFlag())
        self.upiu.b5_query_function = QueryFunction.STANDARD_WRITE_REQ
    def assign(self, idn: int, index: int = 0, selector: int = 0) -> Self:
        assign_idn(self.upiu, idn, index, selector)
        return self

#============= plain helper function ===============#

def rw6_assign(upiu: CommandUpiu[Any], lun: int, lba: int, length: int) -> None:
    cdb: CdbWrite6 | CdbRead6
    cdb = upiu.u16_cdb
    chk_over_under_flow(lun, 8)
    chk_over_under_flow(lba, 32)
    chk_over_under_flow(length, 16)
    # COMMAND UPIU basic header
    upiu.b2_lun = lun

    if length == 0:
       upiu.l12_expected_data_length = 256 * 4096
       cdb.b4_transfer_length = 256 * length
    else:
        upiu.l12_expected_data_length = length * 4096
        cdb.b4_transfer_length = length

    cdb.b1_lba_h = 0x1F & (lba >> 16)
    cdb.w2_lba_l = 0xFFFF & lba
    

def rw_assign(upiu: CommandUpiu[Any], lun: int, lba: int, length: int, fua: int) -> None:
    cdb: CdbWrite10 | CdbRead10
    cdb = upiu.u16_cdb
    chk_over_under_flow(lun, 8)
    chk_over_under_flow(lba, 32)
    chk_over_under_flow(length, 16)
    chk_over_under_flow(fua, 1)
    # COMMAND UPIU basic header
    upiu.b2_lun = lun
    upiu.l12_expected_data_length = length * 4096
    cdb.b1_fua = fua
    cdb.l2_lba = lba
    cdb.w7_transfer_length = length

def rw16_assign(upiu: CommandUpiu[Any], lun: int, lba: int, length: int, fua: int, group_num: int = 0) -> None:
    cdb: CdbWrite16 | CdbRead16
    cdb = upiu.u16_cdb
    chk_over_under_flow(lun, 8)
    chk_over_under_flow(lba, 64)
    chk_over_under_flow(length, 32)
    chk_over_under_flow(fua, 1)

    # COMMAND UPIU basic header
    upiu.b2_lun = lun
    upiu.l12_expected_data_length = length * 4096
    cdb.b1_fua = fua 
    cdb.l2_lba_h = 0xFFFFFFFF & (lba >> 32)
    cdb.l6_lba_l = 0xFFFFFFFF & lba
    cdb.l10_transfer_length = length
    cdb.b14_group_number = group_num

def rwbuf_assign(upiu: CommandUpiu[Any], lun: int, mode: int, buffer_id: int, buffer_offset: int, length: int, vendor: bool) -> None:
    cdb: CdbWriteBuffer | CdbReadBuffer
    cdb = upiu.u16_cdb
    chk_over_under_flow(lun, 8)
    if(vendor == True):
        chk_over_under_flow(mode, 8)  # the first three bits are for vendor
    else:
        chk_over_under_flow(mode, 5)
    chk_over_under_flow(buffer_id, 8)
    chk_over_under_flow(buffer_offset, 24)
    chk_over_under_flow(length, 24)
    
    upiu.b2_lun = lun
    upiu.l12_expected_data_length = length

    if vendor == True:
        cdb.b1_rsvd = 0x7 & (mode >> 5) 
        cdb.b1_mode = 0x1F & mode
    else:
        cdb.b1_mode = mode

    cdb.b2_buffer_id = buffer_id
    cdb.b3_buffer_offset_h = 0xFF & (buffer_offset >> 16)
    cdb.w4_buffer_offset_l = 0xFFFF & buffer_offset
    cdb.b6_allocation_length_h = 0xFF & (length >> 16)
    cdb.w7_allocation_length_l = 0xFFFF & length

def assign_idn(upiu: QueryRequestUpiu[Any], idn: int, index: int, selector: int) -> None:
    sf: SfReadDescriptor | SfWriteDescriptor | \
        SfReadAttribute | SfWriteAttribute | \
        SfSetFlag | SfReadFlag | SfClearFlag | SfToggleFlag
    sf = upiu.u12_specific_fields
    chk_over_under_flow(idn, 8)
    chk_over_under_flow(index, 8)
    chk_over_under_flow(selector, 8)

    sf.b13_idn = idn
    sf.b14_index = index
    sf.b15_selector = selector

def chk_over_under_flow(num: int, bit: int) -> None:
    if num >= BIT(bit):
        _log.error(f'UPIU value {num} overflow {bit} bit')
        raise PATTERN_ASSERT_VALUE_EXCEEDS_FIELD_MAX_VALUE
    elif num < 0:
        _log.error(f'UPIU value {num} < 0')
        raise PATTERN_ASSERT_VALUE_SHALL_NOT_BE_NAGTIVE
    else:
        pass

def _set_adv_rpmb_ehs(upiu: BaseSecurityProtocolOut | BaseSecurityProtocolIn, meta_info: AdvRpmbMetaInfo, mac_or_key: bytearray) -> None:
    if len(mac_or_key) != 32:
        raise PATTERN_ASSERT_RPMB_MAC_OR_KEY_SHALL_BE_32B
    upiu.upiu.b8_total_ehs_length = 2
    upiu.ehs = EhsAdvRpmb()
    upiu.ehs.b0_length = 2
    upiu.ehs.b1_ehs_type = 1
    upiu.ehs.w2_ehs_subtype = 0
    upiu.ehs.meta_info = deepcopy(meta_info)
    upiu.ehs.mac_key = deepcopy(mac_or_key)