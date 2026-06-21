
import Script.api.shared as shared
from abc import ABC, abstractmethod
from Script.api.ufs_api.fbo.struct import FboReadBufferStruct0101, FboWriteBufferStruct0101
_log = shared.logger

class FboBase(ABC):
	def __init__(self) ->None:
		self.bLength = 0
		self.wFBOVersion = 0
		self.dFBORecommendedLBARangeSize = 0
		self.dFBOMaxLBARangeSize = 0
		self.dFBOMinLBARangeSize = 0
		self.bFBOMaxLBARangeCount = 0
		self.wFBOLBARangeAlignment = 0
	@abstractmethod
	def get_descriptor(self)-> None:
		raise NotImplementedError("virtual Method! Must be overwrited.")
	@abstractmethod
	def set_fbo_control(self, value : int) -> None:
		raise NotImplementedError("virtual Method! Must be overwrited.")
	@abstractmethod
	def set_fbo_execute_threshold(self, value : int) -> None:
		raise NotImplementedError("virtual Method! Must be overwrited.")
	@abstractmethod
	def get_fbo_execute_threshold(self) -> int:
		raise NotImplementedError("virtual Method! Must be overwrited.")
	@abstractmethod
	def get_fbo_progress_state(self) -> int:
		raise NotImplementedError("virtual Method! Must be overwrited.")
	@abstractmethod
	def set_fbo_write_buffer(self, fbo_write_buffer_struct : FboWriteBufferStruct0101) -> None:
		raise NotImplementedError("virtual Method! Must be overwrited.")
	@abstractmethod
	def get_fbo_read_buffer(self) -> FboReadBufferStruct0101:
		raise NotImplementedError("virtual Method! Must be overwrited.")
	def print_fbo_descriptor(self) -> None:
		_log.info(f" FBO Descriptor-------------------------------------------------")
		_log.info(f" bLength = {hex(self.bLength)}")
		_log.info(f" wFBOVersion = {hex(self.wFBOVersion)}")
		_log.info(f" dFBORecommendedLBARangeSize = {hex(self.dFBORecommendedLBARangeSize)}")
		_log.info(f" dFBOMaxLBARangeSize = {hex(self.dFBOMaxLBARangeSize)}")
		_log.info(f" dFBOMinLBARangeSize = {hex(self.dFBOMinLBARangeSize)}")
		_log.info(f" bFBOMaxLBARangeCount = {hex(self.bFBOMaxLBARangeCount)}")
		_log.info(f" wFBOLBARangeAlignment = {hex(self.wFBOLBARangeAlignment)}")
		_log.info(f" ---------------------------------------------------------------")
