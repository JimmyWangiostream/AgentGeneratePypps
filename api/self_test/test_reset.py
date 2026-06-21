from .base import ApiTestBase
from Script.api import shared
from Script.lib import sdk_lib as lib

_sdk = shared.sdk

#pass
# class TestResetN(ApiTestBase):
#     def test_rstn_n_control_mode_0(self):
#         _sdk.reset_n(0)
#     def test_rstn_n_control_mode_1(self):
#         _sdk.reset_n(1)
#     def test_rstn_n_control_mode_2(self):
#         _sdk.reset_n(2)
#     def test_rstn_n_control_mode_3(self):
#         _sdk.reset_n(3)

#fail
# class TestResetNKey(ApiTestBase):
#     def test_rstn_key(self):
#         #Setting RSTN Key Mode, 0 = 8317, 1 = 8318
#         _sdk.reset_n_key(4, 0)

#         #turning and send ResetN Key 100 times 
#         _sdk.reset_n_key(0, 100)

#         #enable send RSTN Key function
#         _sdk.reset_n_key(1, 1)

#         #when script fail , send RSTN Key Send
#         _sdk.reset_n_key(2)

#         #if  RSTN Key Send pass then send RSTN  authentication , when RSTN authentication pass , you can send ResetN_VendorCMD
#         _sdk.reset_n_key(3)

#fail
# class TestResetNKeyVendorCMD(ApiTestBase):
#     def test_rstn_key(self):
#         #Setting RSTN Key Mode, 0 = 8317, 1 = 8318
#         _sdk.reset_n_key(4, 0)

#         #turning and send ResetN Key 100 times 
#         _sdk.reset_n_key(0, 100)

#         #enable send RSTN Key function
#         _sdk.reset_n_key(1, 1)

#         #when script fail , send RSTN Key Send
#         _sdk.reset_n_key(2)

#         #if  RSTN Key Send pass then send RSTN  authentication , when RSTN authentication pass , you can send ResetN_VendorCMD
#         _sdk.reset_n_key(3)

#         ArgPage = bytearray(512)
#         data = bytearray(512)
#         _sdk.reset_n_vendor_cmd(0, 1, ArgPage, data)

#pass
# class TestClearDoneQueue(ApiTestBase):
#     def test_clear_done_queue(self):
#         #Tag done queue
#         _sdk.clear_done_queue(lib.HostDQType.TAG_DONE_QUEUE.value, 0)

#         #LUN done queue
#         _sdk.clear_done_queue(lib.HostDQType.LUN_DONE_QUEUE.value, 0)

#         #All done queue
#         _sdk.clear_done_queue(lib.HostDQType.ALL_DONE_QUEUE.value, 0)

#         #All done queue & error check
#         _sdk.clear_done_queue(lib.HostDQType.ALL_DONE_QUEUE_ERR_HANDLE.value, 0)
