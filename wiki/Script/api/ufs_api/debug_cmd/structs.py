from abc import ABC, abstractmethod
import struct
import bitstruct

from Script.api.struct_helper import *

class PowerFlags(PacketComposerABC):
    def __init__(self) -> None:
        self.rx_termination = 0
        self.tx_termination = 0
        self.line_reset = 0
        self.hs_series = 0
        self.user_data_valid = 0
        self.scramble = 0
        self.rsvd = 0

    def to_bytes(self) -> bytearray:
        buf = bytearray(1)
        buf[0] = bitstruct.pack('u1u1u1u1u1u3', self.rx_termination, self.tx_termination, self.line_reset, self.hs_series, self.user_data_valid, 
                       self.scramble, self.rsvd)[0]
        return buf
    
    


