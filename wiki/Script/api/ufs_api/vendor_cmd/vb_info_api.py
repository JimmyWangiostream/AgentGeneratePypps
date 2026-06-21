from typing import Generic, TypeVar, Protocol
import Script.api.shared as shared
import Script.api.cmd_seq as ExecuteCMD
from Script.api.struct_helper import AUTO_OFFSET, BITPacketParserComposerABC, BaseField, BaseFieldBit
from Script.api.ufs_api.vendor_cmd import functions as vuc

_log = shared.logger

_T = TypeVar("_T", bound=BITPacketParserComposerABC, covariant=True)

class _VbListFormat(Protocol[_T]):
    def __call__(self, payload: bytearray, start_offset: int, end_offset: int) -> _T: ...

class GetVBInfo(Generic[_T]):
    def __init__(self, vb_list_format: _VbListFormat[_T], format_size: int) -> None:
        self.vb_list_format = vb_list_format
        self.format_size = format_size

    def get_info(self, access_vendor: bool = True) -> list[_T]:
        size = self.format_size
        vb_info: list[_T] = []
        _, data = vuc.get_vb_info(access_vendor=access_vendor)
        for i in range(0, len(data), size):
            vb_info.append(self.vb_list_format(data[i:i+size], AUTO_OFFSET, AUTO_OFFSET))
        return vb_info

    def get_valid_count(self, access_vendor: bool = True) -> list[int]:
        size = 4
        valid_cnt = []
        _, data = vuc.get_vb_valid_cnt_info(access_vendor=access_vendor)
        for vb in range(len(data) // size):
            byte = vb * size
            valid_cnt.append(int.from_bytes(data[byte:byte+size], 'little'))
        return valid_cnt
    
    def get_remap_table(self, access_vendor: bool = True) -> list[int]:
        size = 2
        remap_table = []
        _, data = vuc.get_remap_table(access_vendor=access_vendor)
        for vb in range(len(data) // size):
            byte = vb * size
            remap_table.append(int.from_bytes(data[byte:byte+size], 'little'))
        return remap_table
    
    def get_group_size(self, access_vendor: bool = True) -> list[int]:
        size = 4
        group_size = []
        _, data = vuc.get_vb_group_size(access_vendor=access_vendor)
        for vb in range(len(data) // size):
            byte = vb * size
            group_size.append(int.from_bytes(data[byte:byte+size], 'little'))
        return group_size
    
    def show(self, print_valid_cnt_zero_vb: bool = True, access_vendor: bool = True) -> None:
        for line in self._get_vb_info_str_list(print_valid_cnt_zero_vb, access_vendor):
            _log.info(line)

    def dumpfile(self, file_name: str | None = None, print_valid_cnt_zero_vb: bool = True, access_vendor: bool = True) -> None:
        from Script.api.util.functions import dumpfile
        if file_name is None:
            from datetime import datetime
            now = datetime.now()
            file_name = f'{now.strftime("%Y%m%d_%H%M%S")}_DumpVBInfo.txt'
        lines = self._get_vb_info_str_list(print_valid_cnt_zero_vb, access_vendor)
        dumpfile(file_name, "\n".join(lines))

    def _get_vb_info_str_list(self, print_valid_cnt_zero_vb: bool, access_vendor: bool) -> list[str]:
        lines = ['------------ Print VB Info ------------']
        
        valid_cnt = self.get_valid_count(access_vendor=access_vendor)
        vb_info = self.get_info(access_vendor=False)
        remap_table = self.get_remap_table(access_vendor=False)
        
        for i in range(min(len(vb_info), len(valid_cnt), len(remap_table))):
            if valid_cnt[i] != 0 or print_valid_cnt_zero_vb:
                members = {name: val.value for name, val in vars(vb_info[i]).items() if isinstance(val, (BaseField, BaseFieldBit))}
                lines.append(f'VB{i} Valid Count = {valid_cnt[i]}, Remap = {remap_table[i]}, {members}')
                
        lines.append('----------------- End -----------------')
        return lines