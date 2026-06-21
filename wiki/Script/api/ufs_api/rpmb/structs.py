from abc import ABC, abstractmethod
import struct
import bitstruct

from Script.api.struct_helper import *

class RPMBMsgDataFrame(PacketComposerABC, PacketParserABC):
    def __init__(self) -> None:
        self.stuff = bytearray(196)  
        self.key_mac = bytearray(32) 
        self.data = bytearray(256) 
        self.nonce = bytearray(16) 
        self.write_counter = 0
        self.address = 0
        self.block_count = 0
        self.result = 0
        self.req_rsp_type = 0

    def to_bytes(self) -> bytearray:
        buf = bytearray(512)
        buf[0:196] = self.stuff
        buf[196:228] = self.key_mac
        buf[228:484] = self.data
        buf[484:500] = self.nonce
        buf[500:504] = self.write_counter.to_bytes(4, 'big')
        buf[504:506] = self.address.to_bytes(2, 'big')
        buf[506:508] = self.block_count.to_bytes(2, 'big')
        buf[508:510] = self.result.to_bytes(2, 'big')
        buf[510:512] = self.req_rsp_type.to_bytes(2, 'big')
        return buf
    
    def from_bytes(self, payload: bytearray) -> None:
        format_string = '>196s32s256s16sLHHHH'
        unpacked_data = struct.unpack(format_string, payload[0:512])
        
        self.stuff = unpacked_data[0]
        self.key_mac = unpacked_data[1]
        self.data = unpacked_data[2]
        self.nonce = unpacked_data[3]
        self.write_counter = unpacked_data[4]
        self.address = unpacked_data[5]
        self.block_count = unpacked_data[6]
        self.result = unpacked_data[7]
        self.req_rsp_type = unpacked_data[8]
    


