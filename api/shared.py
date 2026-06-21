import logging
from Script.lib.sdk_lib import SDKLib
from Script.lib import sdk_lib as lib

class _LazySDK(lib.SDKLib):
    def __init__(self) -> None:
        pass

    def set_sdk(self, sdk: SDKLib) -> None:
        super().__init__(sdk.drive)

# =================================================================================================================
# =================================================================================================================

class _LazyLogger(logging.Logger):
    def __init__(self, name: str | None = None, level: int | None = None):
        if name is None:
            name = __name__
        if level is None:
            level = logging.NOTSET
        super().__init__(name, level)

    def set_logger(self, logger: logging.Logger) -> None:
        super().__init__(logger.name, logger.level)

        self.handlers.clear()

        for h in logger.handlers:
            self.addHandler(h)

# =================================================================================================================
# =================================================================================================================

class _LazyParamCache:
    """
    The global parameters defined here (e.g. extcsd, partition_size) are only for demostration.
    We should try our best to reduce the usage of global paramters.
    """
    def set_param(self) -> None:
        from Script.api.ufs_api.descriptors.geometry_desc.structs import GeometryDescriptor410
        from Script.api.ufs_api.descriptors.unit_desc.structs import UnitDescriptor410
        from Script.api.ufs_api.descriptors.device_desc.structs import DeviceDescriptor410
        from Script.api.unipro_api.power_change import CurrentSpeed

        self.gHostInfo = lib.HostInfo()
        self.gDevice = DeviceDescriptor410()
        self.gGeometry = GeometryDescriptor410()
        self.gUnit = [UnitDescriptor410() for _ in range(32)]
        self.gMaxNumberLU = 0
        self.gLUCapacity = [0] * 32
        self.current_speed = CurrentSpeed()

sdk = _LazySDK()
logger = _LazyLogger()
param = _LazyParamCache()


def set_sdk(s: SDKLib) -> None:
    global sdk
    sdk.set_sdk(s)

def set_logger(log: logging.Logger) -> None:
    global logger
    logger.set_logger(log)

    def _lib_log_callback(entry: lib.LogEntry) -> None:

        # note: if don't want to print sdk log, mark the logic
        # if entry.source == lib.LogEntry.Source.SDK:
        #     return

        level_to_func = {
            lib.LogEntry.Level.DEBUG: logger.debug,
            lib.LogEntry.Level.INFO: logger.info,
            lib.LogEntry.Level.WARN: logger.warning,
            lib.LogEntry.Level.ERROR: logger.error,
        }
        f = level_to_func.get(entry.level, logger.info)
        f(entry.message)

    lib.set_log_callback(_lib_log_callback)

def set_param() -> None:
    param.set_param()