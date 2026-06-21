from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import Any
import configparser
from Script.api.util.common_path import CommonPath
from Script.api import shared
from Script.lib import sdk_lib as lib
from Script.api.struct_helper import MemoryViewWithCopy

_log = shared.logger
_sdk = shared.sdk

def dumpfile(filename: str, data: Any, print_info: bool=True) -> None:
    target_path = CommonPath.development_report
    file_path = os.path.join(target_path, filename)
    if print_info:
        _log.info(f'[Dump File] => {file_path}')
    if isinstance(data, (memoryview, MemoryViewWithCopy)):
        data = bytearray(data)
    if isinstance(data, (bytes, bytearray)):
        with open(file_path, 'wb') as f:
            f.write(data)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(data))


def find_enum_member_from_val(target_enum: Any, val: Any) -> str:
    ret: str
    try:
        ret = target_enum(val).name
    except ValueError:
        ret = 'undefined'
    return ret

def track_activate_and_reset() -> None:
    active_param = lib.SdkTrackActivateArgs()
    config = configparser.ConfigParser()
    config.read(f"{Path(CommonPath.ini) / 'SDK_Track.ini'}")
    active_param.activate_cmd = config.getboolean('SDKActivateParam', 'ActivateCMD')
    active_param.activate_resp = config.getboolean('SDKActivateParam', 'ActivateRESP')
    active_param.activate_unipro = config.getboolean('SDKActivateParam', 'ActivateUnipro')
    active_param.activate_host = config.getboolean('SDKActivateParam', 'ActivateHost')
    active_param.activate_usb = config.getboolean('SDKActivateParam', 'ActivateUSB')
    active_param.activate_latency = config.getboolean('SDKActivateParam', 'ActivateLatency')
    active_param.activate_group_rw = config.getboolean('SDKActivateParam', 'ActivateGroupRW')
    active_param.activate_cmd_seq = config.getboolean('SDKActivateParam', 'ActivateCMD_SEQ')
    active_param.activate_perfc = config.getboolean('SDKActivateParam', 'ActivatePerfc')
    
    _sdk.sdk_track_activate(active_param)
    _sdk.sdk_track_reset()

def sw_timeout(
    start_time: datetime,
    hr: int = 0,
    min: int = 0,
    sec: int = 0
) -> bool:
    timeout = timedelta(hours=hr, minutes=min, seconds=sec)
    return datetime.now() - start_time >= timeout

