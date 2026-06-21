import unittest
import sys
import os

try:
    from Script import api
except ImportError:
    root_dir = os.path.normpath(os.path.dirname(__file__) + "/../../../../")

    if "Script" not in os.listdir(root_dir):
        raise FileNotFoundError(f"this is not the root directory: {root_dir}")
    if root_dir not in sys.path:
        sys.path.append(root_dir)
    from Script import api

from Script.lib import sdk_lib as lib
from Script.api import shared
from datetime import datetime
import logging


_log = shared.logger
_g_has_init: bool = False

# only for self_test use
def setup_logger(filename: str) -> logging.Logger:
    logger = logging.getLogger(filename)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Prevent duplicate logs if root logger is used
    formatter = logging.Formatter(fmt='%(asctime)s %(name)s %(levelname)s - %(message)s')
    # Stream handler
    s_handler = logging.StreamHandler(stream=sys.stdout)
    s_handler.setFormatter(formatter)
    logger.addHandler(s_handler)
    # File handler
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f'{filename}_{date_str}.log')
    f_handler = logging.FileHandler(log_filename, encoding='utf-8')
    f_handler.setFormatter(formatter)
    logger.addHandler(f_handler)

    return logger

def init() -> None:
    global _g_has_init
    if _g_has_init:
        return

    api.set_logger(setup_logger('self_test')) # only for self_test use

    # Init tester & SDK
    drivers = api.scan_tester()
    if drivers is None or len(drivers) == 0:
        raise Exception("No tester driver found")
    sdk = lib.SDKLib(drivers[0].target_drive)
    api.set_sdk(sdk)
    api.set_param()
    api.init_device_to_default()

    _g_has_init = True


if __name__ == "__main__":
    init()


class ApiTestBase(unittest.TestCase):
    def __init__(self, *args, **kwargs) -> None: # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self._has_init = False
        self.sdk: lib.SDKLib

    @classmethod
    def setUpClass(cls) -> None:
        init()
        api.set_qd_limit(32)