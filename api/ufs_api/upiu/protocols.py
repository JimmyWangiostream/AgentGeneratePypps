from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from Script.api.ufs_api.defines.enum_define import UPIUTransactionType

class HasTransactionType(Protocol):
    b0_transaction_type: UPIUTransactionType

    def to_bytes(self) -> bytearray: ...

class HasCommonHeader(Protocol):
    b0_transaction_type: int
    b1_flags: int
    b3_tasktag: int
    b8_total_ehs_length: int
    w10_data_segment_length: int

    def to_bytes(self) -> bytearray: ...

class IsEhs(Protocol):
    b0_length: int
    b1_ehs_type: int
    w2_ehs_subtype: int

    def to_bytes(self) -> bytearray: ...
    def from_bytes(self, payload: bytearray) -> None: ...

class IsUpiu(ABC):
    def __init__(self) -> None:
        from Script.api.ufs_api.upiu.structs import Ehs
        self.upiu: HasTransactionType
        self.ehs: IsEhs = Ehs()
        self.data: bytearray = bytearray()

