from typing import Any, Optional, Tuple, cast
from pathlib import Path
import json

from prettytable import PrettyTable
from Script.api import shared
from Script.api.ufs_api._mp import TesterInfo
from Script.api.util.dut.project_enum import M1, M2, M3, M4, VendorID, Project
from Script.api.util.functions import find_enum_member_from_val
from Script.api.exception import PATTERN_ASSERT_UNEXPECTED_CONDITION

_log = shared.logger

class Dut:
    _singleton: Optional['Dut'] = None
    def __init__(self) -> None:
        if Dut._singleton is not None:
            raise Exception('Use get_instance() instead of creating a new instance.')
        self.project_sn: str = 'not_initialized'
        self.enum: Project = Project.NOT_INITIALIZED
        self.original_svn: int = -1
        self.name: str = 'not_initialized'
        self.uid: str = 'not_initialized'
        self.m1: int = M1.NOT_INITIALIZED
        self.m2: int = M2.NOT_INITIALIZED
        self.m3: int = M3.NOT_INITIALIZED
        self.m4: int = M4.NOT_INITIALIZED
        self.vendor_id: int = VendorID.NOT_INITIALIZED
        self.ufs_version: int = -1
        self.ce_num: int = -1
        self.tester_info: TesterInfo

    @classmethod
    def get_instance(cls) -> 'Dut':
        """
        Get corresponding Dut instance (Dut Class can only be instantiated once).  
        """
        if cls._singleton is None:
            cls._singleton = Dut()
            cls._singleton._set_properties()
        return cls._singleton
    
    def set_to_specific_project(self, M1: int, M2: int, M3: int, M4: int, vendor_id: int, ufs_version: int) -> None:
        """
        Set DUT property manually for debugging usage.  
        """
        _log.warning(f'Manually Set DUT to {M1=}, {M2=}, {M3=}, {M4=}, {vendor_id=}, {ufs_version=}')
        self.m1 = M1
        self.m2 = M2
        self.m3 = M3
        self.m4 = M4
        self.vendor_id = vendor_id
        self.ufs_version = ufs_version
        self.uid, self.name, self.enum, self.project_sn = self._get_best_match_project()
        self.print_info()

    def _set_properties(self) -> None:
        from Script.api.ufs_api.descriptors.device_desc.functions import get_device_descriptor
        from Script.api.ufs_api.descriptors.device_desc.structs import DeviceDescriptor, DeviceDescriptor310
        from Script.api.ufs_api.vendor_cmd.functions import get_flash_setting
        flash_setting = get_flash_setting()
        device_desc = cast(DeviceDescriptor310, get_device_descriptor())
        self.original_svn = flash_setting.FW_SVN
        self.m1 = flash_setting.M1
        self.m2 = flash_setting.M2
        self.m3 = flash_setting.FW_UFS_version_M3_128
        self.m4 = flash_setting.FW_UFS_application_M4_129
        self.vendor_id = flash_setting.FW_Vendor
        self.ufs_version = device_desc.w16_spec_version
        self.ce_num = flash_setting.Max_Fdevice
        self.uid, self.name, self.enum, self.project_sn = self._get_best_match_project()

    def _get_best_match_project(self) -> Tuple[str, str, Project, str]:
        """
        M1/M2/M3/M4/VendorID/UFS_Version of this device will compare to ProjectField.json,  
        and return a best match result.  
        e.g.  
        [Device] M1=1, M2=2, M3=3, M4=4  
          
        [Matched Json] M1=1, M2=2 (2 matched)  
        [Not Matched Json] M1=0, M2=2, M3=3, M4=4 (M1 is different)  
        [Best Matched Json] M1=1, M3=3, M4=4 (3 matched)  
        """
        with open(Path(__file__).parent / 'ProjectField.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        property_map: dict[str, int] = {}
        property_map['M1'] = self.m1
        property_map['M2'] = self.m2
        property_map['M3'] = self.m3
        property_map['M4'] = self.m4
        property_map['VendorID'] = self.vendor_id
        property_map['UFS_Version'] = self.ufs_version

        project_match_counts = []
        for p in data['Projects']:
            match_count = 0;
            for property_key, property_val in p['CompareProperty'].items():
                _log.debug(f'UID {p["UID"]} Property {property_key}: json={property_val}, device={property_map[property_key]}')
                if property_map[property_key] == property_val:
                    match_count += 1
                else:
                    match_count = -1
                    break
            project_match_counts.append((p, match_count))

        max_count = max(project_match_counts, key=lambda x: x[1])[1]
        max_projects = [obj for obj, val in project_match_counts if val == max_count]

        if len(max_projects) > 1:
            _log.error('Device property matches multiple Projects:')
            for p in max_projects:
                _log.error(f'Matched Project UID: {p}')
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        
        try:
            project_sn = max_projects[0]['PyppsProjectSN']
        except KeyError:
            project_sn = 'undefined'

        try:
            project = Project(max_projects[0]['UID'])
        except ValueError:
            project = Project.NOT_INITIALIZED

        return max_projects[0]['UID'], max_projects[0]['Name'], project, project_sn

    def print_info(self) -> None:
        table = PrettyTable()
        table.title = 'DUT INFO'
        table.align = 'l'
        table.field_names = ['Property', 'Value', 'Description']

        table.add_row(['Project SN', self.project_sn, ''])
        table.add_row(['Enum', self.enum, ''])
        table.add_row(['SVN', self.original_svn, ''])
        table.add_row(['CE Number', self.ce_num, ''])
        table.add_row(['Name', self.name, ''])
        table.add_row(['UID', self.uid, ''])
        table.add_row(['M1', self.m1, find_enum_member_from_val(M1, self.m1)])
        table.add_row(['M2', self.m2, find_enum_member_from_val(M2, self.m2)])
        table.add_row(['M3', self.m3, find_enum_member_from_val(M3, self.m3)])
        table.add_row(['M4', self.m4, find_enum_member_from_val(M4, self.m4)])
        table.add_row(['VendorID', self.vendor_id, find_enum_member_from_val(VendorID, self.vendor_id)])
        table.add_row(['UFS Version', f'{self.ufs_version}(0x{self.ufs_version:x})', ''])
        table.add_row([f'{self.tester_info.tester_generation}', f'P{self.tester_info.port_num}_D{self.tester_info.target_drive}', ''])

        table_str = table.get_string()
        for line in table_str.splitlines():
            _log.info(line)
