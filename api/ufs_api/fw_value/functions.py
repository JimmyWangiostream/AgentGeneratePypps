from Script.api.ufs_api.fw_value.compiler.variable_declaration import AddSeq # type: ignore[attr-defined]
import Script.api.ufs_api.fw_value.compiler.trans_address as trans_add
from Script.api import shared
from Script.api.ufs_api.vendor_cmd import read_memory
from typing import Literal, Optional

from Script.api.ufs_api.vendor_cmd.functions import access_vendor_mode

_log = shared.logger


def get_fw_address(name: str) -> Optional[AddSeq]:
    print('parsing address %s' % (name,))
    add_seq = trans_add.address_set.get_add_seq(name) # type: ignore
    if not add_seq:
        return None
    for item in add_seq.seq:
        if item.is_pointer:
            item.base_add = get_address_content(address=add_seq.address, length=4)
        add_seq.address = item.base_add + item.shift
    return add_seq

def read_fw_value(name: str, is_buf: bool=False) -> Optional[bytearray | int]:
    access_vendor_mode()
    add_seq = get_fw_address(name)
    if not add_seq:
        return None
    _log.info(f"address={hex(add_seq.address)}")
    if add_seq.is_constant:
        return add_seq.constant_value # type: ignore
    if is_buf:
        return get_address_content(address=add_seq.address, is_buf=True)
    else:
        value = get_address_content(add_seq.address, add_seq.value_size, False)
        if add_seq.bit_mask:
            value = value >> (add_seq.value_size * 8 - add_seq.bit_mask[1] - add_seq.bit_mask[0])
            value = value & (~(0xFFFFFFFF << add_seq.bit_mask[0]))
        return value

def get_address_content(address: int, length: int=4, is_buf: bool=False) -> bytearray | int:
    print("address",address)
    offset = address % 4
    if offset:
        _log.info(f"address={hex(address)} should align 4Byte, {offset=}")
        address = int(address / 4) * 4

    rsp, Buf = read_memory(address)
    if is_buf:
        return Buf[offset:]
    else:
        value = 0
        for i in range(length):
            value |= (Buf[i + offset] << (i * 8))
        return value