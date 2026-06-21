class error_data():
    def __init__(self):
        self.result_buf = None
        self.info_buf = None

class CommonLibErrorBase(Exception):
    def __init__(self, message: str = None, error_data: error_data = None):
        super().__init__(message)
        self.error_data = error_data
       
class DLL_ERROR(CommonLibErrorBase): pass
class SDK_UNDEFINED_ERROR(CommonLibErrorBase): pass
class DLL_UNSUPPORT_ON_PS2806(DLL_ERROR): pass
class DLL_UNSUPPORT_ON_PS2807(DLL_ERROR): pass

# Dll_Initial
class DLL_VID_ERROR(DLL_ERROR): pass
class DLL_SDK_FW_ERROR(DLL_ERROR): pass
class DLL_HANDSHAKE_ERROR(DLL_ERROR): pass
class DLL_VERSION_ERROR(DLL_ERROR): pass
class DLL_AUTH_ERROR(DLL_ERROR): pass
class DLL_GENERAL_ERROR(DLL_ERROR): pass
class DLL_POWER_CYCLE(DLL_ERROR): pass