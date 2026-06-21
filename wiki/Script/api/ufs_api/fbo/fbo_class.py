from typing import cast
from Script.api.cmd_seq.response import QueryResponse
from Script.api import shared, cmd_seq as ExecuteCMD
import Script.api.shared as shared
from Script.api.ufs_api.attr_flag_functions import parse_read_attr_rsp, write_attribute
from Script.api.ufs_api.fbo.struct import FboDescriptor, FboWriteBufferStruct0101, FboReadBufferStruct0101, FboReadBufferEntry0101
from Script.api.ufs_api.fbo import FboBase
from Script.api.ufs_api.defines.constant_define import DATA_SIZE_4K_BYTE
from Script.api.ufs_api.defines.enum_define import AttributeIDN, FboProgressState, DescriptorIDN
import struct
_log = shared.logger
class FboVersion0101(FboBase):
	def __init__(self) ->None:
		super().__init__()
		self.get_descriptor()

	def get_descriptor(self)-> None:
		cmd = ExecuteCMD.ReadDescriptor()
		cmd.assign(idn = DescriptorIDN.FILE_BASED_OPTIMIZATION, index = 0, selector = 0)
		cmd_index = ExecuteCMD.enqueue(cmd)

		ExecuteCMD.send(clear_on_success=False)
		resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
		ExecuteCMD.clear()
		#print(resp.data)
		desc = FboDescriptor()
		desc.from_bytes(resp.data)
		self.bLength = desc.b0_length
		self.wFBOVersion = desc.w1_fbo_version
		self.dFBORecommendedLBARangeSize = desc.l3_fbo_recommended_lba_range_size
		self.dFBOMaxLBARangeSize = desc.l7_fbo_max_lba_range_size
		self.dFBOMinLBARangeSize = desc.l11_fbo_min_lba_range_size
		self.bFBOMaxLBARangeCount = desc.b15_fbo_max_lba_range_count
		self.wFBOLBARangeAlignment = desc.w16_fbo_lba_range_alignment
		self.print_fbo_descriptor()

	def set_fbo_control(self, value : int) -> None:
		write_attribute(idn=AttributeIDN.FBO_CONTROL, val=value)

	def set_fbo_execute_threshold(self, value : int) ->None:
		write_attribute(idn=AttributeIDN.FBO_EXECUTE_THRESHOLD, val=value)
		
	def get_fbo_execute_threshold(self) -> int:
		read_attr = ExecuteCMD.ReadAttribute().assign(idn=AttributeIDN.FBO_EXECUTE_THRESHOLD).enqueue()
		ExecuteCMD.send(clear_on_success=False)
		rsp = cast(QueryResponse, ExecuteCMD.read_response(read_attr))
		idn, index, selector, val = parse_read_attr_rsp(rsp)
		_log.info(f'{idn=},{index=},{selector=},{val=}')
		ExecuteCMD.clear()
		return val
	def get_fbo_progress_state(self) -> int:
		read_attr = ExecuteCMD.ReadAttribute().assign(idn=AttributeIDN.FBO_PROGRESS_STATE).enqueue()
		ExecuteCMD.send(clear_on_success=False)
		rsp = cast(QueryResponse, ExecuteCMD.read_response(read_attr))
		idn, index, selector, val = parse_read_attr_rsp(rsp)
		_log.info(f'{idn=},{index=},{selector=},{val=} {FboProgressState(val).name}')
		ExecuteCMD.clear()
		return val

	def set_fbo_write_buffer(self, fbo_write_buffer_struct : FboWriteBufferStruct0101) -> None:
		cmd = ExecuteCMD.WriteBuffer()
		cmd.assign(lun = 0, mode = 2, buffer_id = 1, buffer_offset = 0, length = DATA_SIZE_4K_BYTE)
		self.print_write_buffer_struct(fbo_write_buffer_struct)
		cmd.data = fbo_write_buffer_struct.to_bytes()
		cmd.set_option(wait_queue_empty = True)
		cmd_index = ExecuteCMD.enqueue(cmd)
		ExecuteCMD.send(clear_on_success=True)
	def get_fbo_read_buffer(self) -> FboReadBufferStruct0101:
		cmd = ExecuteCMD.ReadBuffer()
		cmd.assign(lun =0, mode = 2, buffer_id = 2, buffer_offset = 0, length = DATA_SIZE_4K_BYTE)
		cmd.set_option(wait_queue_empty = True)
		cmd_index = ExecuteCMD.enqueue(cmd)
		ExecuteCMD.send(clear_on_success=False)
		resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
		ExecuteCMD.clear()
		read_buffer_struct = FboReadBufferStruct0101()
		read_buffer_struct.from_bytes(resp_data = resp.data)
		self.print_read_buufer_struct(read_buffer_struct)
		return read_buffer_struct

	def print_write_buffer_struct(self, fbo_write_buffer_struct : FboWriteBufferStruct0101) ->None:
		_log.info(f"FBOWriteBuffer Type Specific Information Structure Type = 0")
		_log.info(f"FBO Type = {fbo_write_buffer_struct.fbo_type}")
		_log.info(f"Version = {fbo_write_buffer_struct.fbo_version}")
		_log.info(f"Number of FBOWriteBufferEntries = {len(fbo_write_buffer_struct.fbo_write_buffer_entry_list)}")
		_log.info(f"CAR = {fbo_write_buffer_struct.car}")
		for i in range(0, len(fbo_write_buffer_struct.fbo_write_buffer_entry_list)):
			_log.info("---------------------------------")
			_log.info(f"FBO WRITEBUFFER ENTRY {str(i)}")
			_log.info(f"Start LBA = {fbo_write_buffer_struct.fbo_write_buffer_entry_list[i].start_lba}")
			_log.info(f"Length = {fbo_write_buffer_struct.fbo_write_buffer_entry_list[i].length}")
			_log.info(f"Reserved = {fbo_write_buffer_struct.fbo_write_buffer_entry_list[i].reserved}")
		_log.info("---------------------------------")
	def print_read_buufer_struct(self, fbo_read_buffer_struct : FboReadBufferStruct0101) ->None:
		_log.info(f"FBOReadBuffer Generic Structure")
		_log.info(f"FBO Type = {fbo_read_buffer_struct.fbo_type}")
		_log.info(f"Version = {fbo_read_buffer_struct.fbo_version}")
		_log.info(f"Number of FBOReadBufferEntries = {fbo_read_buffer_struct.number_of_fbo_read_buffer_entries}")
		_log.info(f"CAR = {fbo_read_buffer_struct.car}")
		_log.info(f"All Ranges Regression Level  = {fbo_read_buffer_struct.all_ranges_regression_level}")
		for i in range(0, len(fbo_read_buffer_struct.fbo_read_buffer_entry_list)):
			_log.info("---------------------------------")
			_log.info(f"FBO READBUFFER ENTRY {str(i)}")
			_log.info(f"Start LBA = {fbo_read_buffer_struct.fbo_read_buffer_entry_list[i].start_lba}")
			_log.info(f"Length = {fbo_read_buffer_struct.fbo_read_buffer_entry_list[i].length}")
			_log.info(f"Regression Level = {fbo_read_buffer_struct.fbo_read_buffer_entry_list[i].regression_level}")
		_log.info("---------------------------------")

