from abc import ABC, abstractmethod
from typing import Literal, Optional, Union
from Script.pattern.pattern_logger import PyppsLogger

AUTO_OFFSET = -1

class MemoryViewWithCopy:
    __slots__ = ("_mv",)
    def __init__(self, mv: memoryview) -> None:
        self._mv = mv
    def __getitem__(self, key): # type: ignore
        return self._mv[key]
    def __len__(self) -> int:
        return len(self._mv)
    def __iter__(self): # type: ignore
        return iter(self._mv)
    def __repr__(self) -> str:
        return f"<MemoryViewWithCopy {self._mv!r}>"
    def copy(self) -> bytearray:
        return bytearray(self._mv)
    def __getattr__(self, name): # type: ignore
        return getattr(self._mv, name)
    def __setitem__(self, key, value) -> None:  # type: ignore
        self._mv[key] = value
    def __eq__(self, other):  # type: ignore
        if isinstance(other, MemoryViewWithCopy):
            return bytes(self._mv) == bytes(other._mv)
        return NotImplemented
    def __ne__(self, other):  # type: ignore
        result = self.__eq__(other)
        return NotImplemented if result is NotImplemented else not result

class PacketComposerABC(ABC):
    @abstractmethod
    def to_bytes(self) -> bytearray:
        pass

class PacketParserABC(ABC):
    @abstractmethod
    def from_bytes(self, payload: bytearray) -> None:
        pass
    

class BaseFieldBit(ABC):
    def __init__(self, payload: bytearray, start_bit: int, end_bit: int, start_offset: int, endian: Literal['little', 'big'] = "little") -> None:
        self.start_bit = start_bit
        self.end_bit = end_bit
        self.endian = endian
        self.__payload = payload
        self.__start_offset = start_offset
        self._update_value()

    def _get_parameter(self) -> tuple[int, int, int, memoryview]:
        bit_length = self.end_bit - self.start_bit + 1
        byte_start = self.start_bit // 8
        byte_end   = self.end_bit // 8
        byte_length = byte_end - byte_start + 1
        view = memoryview(self.__payload)[
            byte_start + self.__start_offset :
            byte_start + self.__start_offset + byte_length
        ]
        return bit_length, byte_start, byte_length, view

    def _update_value(self) -> None:
        bit_length, byte_start, byte_length, byte_data = self._get_parameter()
        if self.endian == 'big':
            value = int.from_bytes(byte_data, 'big')
        else:
            value = int.from_bytes(byte_data, 'little')

        mask = (1 << bit_length) - 1
        if self.endian == 'big':
            if byte_length == 1:
                shift_amount = self.end_bit % 8
            else:
                shift_amount = (8 * byte_length - 1) - self.end_bit
            shift_amount = max(0, shift_amount)
            shifted_value = value >> shift_amount
        else:
            shift_amount = self.start_bit % 8
            shifted_value = value >> shift_amount
        self._current_value = shifted_value & mask

    @property
    def value(self) -> int:
        self._update_value()
        return self._current_value

    @value.setter
    def value(self, val: int) -> None:
        bit_length, byte_start, byte_length, byte_data = self._get_parameter()
        mask = (1 << bit_length) - 1

        if val > mask:
            raise ValueError(f"Value {val} exceeds bit width {bit_length}")

        if self.endian == 'big':
            value = int.from_bytes(byte_data, 'big')
        else:
            value = int.from_bytes(byte_data, 'little')

        if self.endian == 'big':
            bit_mask = mask << (8 * byte_length - 1 - self.end_bit)
        else:
            bit_mask = mask << (self.start_bit % 8)
        value = value & ~bit_mask

        if self.endian == 'big':
            shifted_val = val << (8 * byte_length - 1 - self.end_bit)
        else:
            shifted_val = val << (self.start_bit % 8)
        value = value | shifted_val

        if self.endian == 'big':
            new_bytes = value.to_bytes(byte_length, 'big')
        else:
            new_bytes = value.to_bytes(byte_length, 'little')

        self.__payload[byte_start + self.__start_offset : byte_start + self.__start_offset + byte_length] = new_bytes

class BaseField(ABC):
    def __init__(self,payload: bytearray, start_offset: int, end_offset: int, endian: Literal['little', 'big'] = "little") -> None:
        if end_offset < start_offset:
            raise ValueError(f"start_offset = {start_offset} must greater than end_offset = {end_offset}")
        self.start_offset = start_offset 
        self.end_offset = end_offset 
        self.endian = endian
        self.__payload = payload
    
    @property
    def payload(self) -> MemoryViewWithCopy:
        mv = memoryview(self.__payload)[self.start_offset : self.end_offset + 1]
        return MemoryViewWithCopy(mv)

    @payload.setter
    def payload(self, new_data: Union[bytes, bytearray]) -> None:
        expected = self.end_offset - self.start_offset + 1
        if len(new_data) != expected:
            raise ValueError(f"Payload length must be {expected}")
        self.__payload[self.start_offset : self.end_offset + 1] = new_data
    
    @property
    def value(self) -> int:
        if self.endian == 'big':
            return int.from_bytes(self.__payload[self.start_offset : self.end_offset + 1], 'big')
        else:
            return int.from_bytes(self.__payload[self.start_offset : self.end_offset + 1], 'little')
    
    @value.setter
    def value(self, val: int) -> None:
        byte_length = self.end_offset - self.start_offset + 1
        if self.endian == 'big':
            bytes_val = val.to_bytes(byte_length, 'big')
        else:
            bytes_val = val.to_bytes(byte_length, 'little')
        self.__payload[self.start_offset : self.start_offset + byte_length] = bytes_val
        
class PacketParserComposerABC(BaseField):
    def __init__(self, payload: bytearray, start_offset: int, end_offset: int) -> None:
        start_offset = start_offset if start_offset != AUTO_OFFSET else 0
        end_offset = end_offset if end_offset != AUTO_OFFSET else len(payload)-1
        super().__init__(payload = payload, start_offset = start_offset, end_offset = end_offset)
        self.__payload = payload
        self.__start_offset = start_offset
        if end_offset > len(self.__payload) - 1:
            raise ValueError(f"end_offset = {end_offset}, should not exceed payload length = {len(self.__payload)}")
        pass

    def add_field(self, start_offset: int, end_offset: int, endian: Literal['little', 'big'] = "little") -> BaseField:
        actual_start_offset = self.__start_offset + start_offset
        actual_end_offset = self.__start_offset + end_offset
        if actual_end_offset > len(self.__payload) - 1:
            raise ValueError(f"end_offset = {actual_end_offset}, should not exceed payload length = {len(self.__payload)}")
        field = BaseField(self.__payload, actual_start_offset, actual_end_offset, endian)
        return field
    
class BITPacketParserComposerABC(ABC):
    def __init__(self, payload: bytearray, start_offset:int, end_offset:int) -> None:
        start_offset = start_offset if start_offset != AUTO_OFFSET else 0
        end_offset = end_offset if end_offset != AUTO_OFFSET else len(payload)-1
        if end_offset > len(payload) - 1:
            raise ValueError(f"end_offset = {end_offset}, should not exceed payload length = {len(payload)}")
        self.__full_payload = payload
        self.__local_start = start_offset
        self.__local_end = end_offset

    @property
    def payload(self) -> MemoryViewWithCopy:
        """Return the local byte slice as a writable memoryview."""
        mv = memoryview(self.__full_payload)[self.__local_start : self.__local_end + 1]
        return MemoryViewWithCopy(mv)

    def add_field_bit(self, start_bit: int, end_bit: int, endian: Literal['little', 'big'] = "little") -> BaseFieldBit:
        field = BaseFieldBit(self.__full_payload, start_bit, end_bit, self.__local_start, endian)
        return field
