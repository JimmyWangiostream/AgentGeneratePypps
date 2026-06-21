from .base import ApiTestBase
from Script.api import shared

_sdk = shared.sdk

#pass
# class TestDebugFWEventActivate(ApiTestBase):
#     def test_disable_debug_fw_event_activate(self):
#         _sdk.debug_fw_event_activate(0)
#     def test_enable_debug_fw_event_activate(self):
#         _sdk.debug_fw_event_activate(1)

#pass
# class TestDebugFWEventResult(ApiTestBase):
#     def test_debug_fw_event_result(self):
#         _sdk.debug_fw_event_activate(1)
#         debug_fw_event_info = _sdk.debug_fw_event_result()
#         print("debug fw event info:", list(debug_fw_event_info))
#         print(len(debug_fw_event_info))

#pass
# class TestDebugFWEventReset(ApiTestBase):
#     def test_debug_fw_event_reset(self):
#         _sdk.debug_fw_event_reset()
