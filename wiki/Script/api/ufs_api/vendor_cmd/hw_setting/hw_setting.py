from abc import ABC, abstractmethod
from typing import Any, Optional
from Script.api import shared
from Script.api.exception import PATTERN_ASSERT_UNEXPECTED_CONDITION
from Script.api.ufs_api.vendor_cmd.functions import get_flash_setting
from Script.api.ufs_api.vendor_cmd.hw_setting.field_defines import HwSettingField

_log = shared.logger

class HwSetting(ABC):
    _singleton: Optional['HwSetting'] = None
    def __init__(self) -> None:
        self.ce_num = 0
        self._data_size = 0
        self._data = bytearray()
        self._backup_data = bytearray()
        self._field_offset_map: dict[HwSettingField, int] = {}

    @classmethod
    def get_instance(cls) -> 'HwSetting':
        """
        Get corresponding HW_Setting instance (HW_Setting Class can only be instantiated once).  
        Based on which IC_Version is and initialize by updating from device & backup data.  
        update_from_device() would be called for the first time.
        """
        if cls._singleton is not None:
            return cls._singleton

        flash_setting = get_flash_setting()
        ce_num = flash_setting.Max_Fdevice
        ic_version = flash_setting.IC_Version
        
        if ic_version == 8317:
            from Script.api.ufs_api.vendor_cmd.hw_setting.hw_setting_8317 import HwSetting8317
            cls._singleton = HwSetting8317(ce_num)
        # elif ic_version == 8318:
        #     cls._singleton = HwSetting8318(ce_num)
        # elif ic_version == 8325:
        #     cls._singleton = HwSetting8325(ce_num)
        # elif ic_version == 8327:
        #     cls._singleton = HwSetting8327(ce_num)
        elif ic_version == 8329:
            from Script.api.ufs_api.vendor_cmd.hw_setting.hw_setting_8329 import HwSetting8329
            cls._singleton = HwSetting8329(ce_num)
        # elif ic_version == 8361:
        #     cls._singleton = HwSetting8361(ce_num)
        elif ic_version == 8363:
            from Script.api.ufs_api.vendor_cmd.hw_setting.hw_setting_8363 import HwSetting8363
            cls._singleton = HwSetting8363(ce_num)
        else:
            _log.error(f"There's no HW_Setting class for this project(ic_version={ic_version}).")
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        
        cls._singleton.update_from_device()

        return cls._singleton

    def get_local_val(self, field: HwSettingField) -> int:
        offset = self.get_offset(field)
        val = self._data[offset]
        _log.info(f'Get local HwSetting.{field.name}, buffer[0x{offset:X}({offset})] = {val}.')
        return val

    def set_local_val(self, field: HwSettingField, val: int) -> None:
        offset = self.get_offset(field)
        self._data[offset] = val
        _log.info(f'Set local HwSetting.{field.name}, buffer[0x{offset:X}({offset})] to {val}.')

    @abstractmethod
    def update_from_device(self) -> None:
        """This will overwrite Local HW_Setting data"""
        pass

    @abstractmethod
    def set_to_device(self, field: HwSettingField | None=None, val: int | None=None) -> None:
        """
        If you only need to set one field, you can use this function directly by specifying the field and value.  
        You must provide both field and val, or leave both unset.  
          
        Will also compare if device value is identical to what user set. This will overwrite Local HW_Setting data.
        """
        pass

    def backup(self) -> None:
        self._backup_data = bytearray(self._data)

    def recover(self) -> None:
        self._data = self._backup_data
        self.set_to_device()

    @abstractmethod
    def get_offset(self, field: HwSettingField) -> int:
        """Get corresponding offset to specific HW_Setting field"""
        pass

    def _is_only_one_none(self, a: Any, b: Any) -> bool:
        return (a is None) != (b is None)
