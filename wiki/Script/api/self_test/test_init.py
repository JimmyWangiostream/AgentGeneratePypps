from .base import ApiTestBase
from Script.api import shared
from Script.lib import sdk_lib as lib

_sdk = shared.sdk

#fail
# class TestGetHubInfo(ApiTestBase):
#     def test_get_hub_info(self):
#         hub_info = _sdk.get_hub_info()
#         print(f"tester_id: {hub_info.tester_id}")
#         print(f"port_num: {hub_info.port_num}")
#         print(f"vid: {hub_info.vid}")
#         print(f"pid: {hub_info.pid}")
#         print(f"usb_version: {hub_info.usb_version}")
#         print(f"hubID: {hub_info.hubID}")

#         # if string empty, fail
#         self.assertNotEqual(hub_info.tester_id, "")
#         self.assertNotEqual(hub_info.port_num, "")
#         self.assertNotEqual(hub_info.vid, "")
#         self.assertNotEqual(hub_info.pid, "")
#         self.assertNotEqual(hub_info.usb_version, "")
#         self.assertNotEqual(hub_info.hubID, "")

# pass
# class TestDllInitial(ApiTestBase):
#     def test_dll_init(self):
#         _sdk.dll_initial()

#pass
# class TestHostInit(ApiTestBase):
#     def test_power_short_detect(self):
#         _sdk.host_initial(lib.HostInit.TESTER_SHORT_DETECT.value) # Reset Tester + Power Short Detect (Default)

#     def test_power_off(self):
#         _sdk.host_initial(lib.HostInit.TESTER_POWER_OFF.value) # Reset Tester + Power OFF

#     def test_keep_vol_set(self):
#         _sdk.host_initial(lib.HostInit.TESTER_KEEP_VOL_SET.value) # Reset Tester (Keep voltage setting)

#pass
# class TestLinkStartUp(ApiTestBase):
#     def test_link_startup(self):
#         _sdk.host_link_startup()

#pass
# class TestSetLinkStartUpMode(ApiTestBase):
#     def test_set_hs_mode(self):
#         _sdk.set_link_startup_mode(1)
    
#     def test_set_ls_mode(self):
#         _sdk.set_link_startup_mode(0)

# pass
# class TestGetDllVer(ApiTestBase):
#     def test_get_dll_ver(self):
#         dll_ver = _sdk.get_dll_version()
#         print(f"v: {dll_ver.v}")
#         print(f"main_ver: {dll_ver.main_ver}")
#         print(f"minor_ver: {dll_ver.minor_ver}")
#         print(f"year: {dll_ver.year}")
#         print(f"month: {dll_ver.month}")
#         print(f"date: {dll_ver.date}")

