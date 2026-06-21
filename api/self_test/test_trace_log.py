from .base import ApiTestBase
from Script.api import shared
from Script.lib import sdk_lib as lib
_sdk = shared.sdk

#pass
# class TestSDKTrackActivate(ApiTestBase):
#     def test_sdk_track_activate(self):
#         arg = lib.SdkTrackActivateArgs()
#         arg.activate_cmd = True
#         arg.activate_resp = True
#         arg.activate_unipro = True
#         arg.activate_host = True
#         arg.activate_usb = True
#         arg.activate_latency = True
#         arg.activate_group_rw = True
#         arg.activate_cmd_seq = False
#         arg.activate_perfc = False
#         _sdk.sdk_track_activate(arg)

#pass
# class TestSDKTrackReset(ApiTestBase):
#     def test_sdk_track_reset(self):
#         _sdk.sdk_track_reset()

#pass
# class TestSDKTrackList(ApiTestBase):
#     def test_sdk_track_list_usb_cdb(self):
#         time_stamp_start = 0
#         time_stamp_end = 4294967295
        
#         #sdk_track_active
#         arg = lib.SdkTrackActivateArgs()
#         arg.activate_cmd = True
#         arg.activate_resp = True
#         arg.activate_unipro = True
#         arg.activate_host = True
#         arg.activate_usb = True
#         arg.activate_latency = True
#         arg.activate_group_rw = True
#         arg.activate_cmd_seq = False
#         arg.activate_perfc = False
#         _sdk.sdk_track_activate(arg)

#         #sdk_track_reset
#         _sdk.sdk_track_reset()
        
#         #sdk_track_list
#         count, info_buf = _sdk.sdk_track_list(lib.SDKTrackListItem.USB_CDB_LIST.value, time_stamp_start, time_stamp_end)
#         print("USB CDB Count:", count)
#         print("USB CDB Infobuf:", list(info_buf))
#         print(len(info_buf))

#     def test_sdk_track_list_send_cmd(self):
#         time_stamp_start = 0
#         time_stamp_end = 4294967295
        
#         #sdk_track_active
#         arg = lib.SdkTrackActivateArgs()
#         arg.activate_cmd = True
#         arg.activate_resp = True
#         arg.activate_unipro = True
#         arg.activate_host = True
#         arg.activate_usb = True
#         arg.activate_latency = True
#         arg.activate_group_rw = True
#         arg.activate_cmd_seq = False
#         arg.activate_perfc = False
#         _sdk.sdk_track_activate(arg)

#         #sdk_track_reset
#         _sdk.sdk_track_reset()

#         #sdk_track_list
#         count, info_buf = _sdk.sdk_track_list(lib.SDKTrackListItem.SEND_CMD_LIST.value, time_stamp_start, time_stamp_end)
#         print("Send CMD Count:", count)
#         print("Send CMD Infobuf:", list(info_buf))
#         print(len(info_buf))

#     def test_sdk_track_list_rsp(self):
#         time_stamp_start = 0
#         time_stamp_end = 4294967295
        
#         #sdk_track_active
#         arg = lib.SdkTrackActivateArgs()
#         arg.activate_cmd = True
#         arg.activate_resp = True
#         arg.activate_unipro = True
#         arg.activate_host = True
#         arg.activate_usb = True
#         arg.activate_latency = True
#         arg.activate_group_rw = True
#         arg.activate_cmd_seq = False
#         arg.activate_perfc = False
#         _sdk.sdk_track_activate(arg)

#         #sdk_track_reset
#         _sdk.sdk_track_reset()
        
#         #sdk_track_list
#         count, info_buf = _sdk.sdk_track_list(lib.SDKTrackListItem.RESPONSE_LIST.value, time_stamp_start, time_stamp_end)
#         print("RSP Count:", count)
#         print("RSP Infobuf:", list(info_buf))
#         print(len(info_buf))
    


#pass
# class TestSDKTrackResult(ApiTestBase):
#     def test_sdk_track_result(self):
#         #sdk_track_active
#         arg = lib.SdkTrackActivateArgs()
#         arg.activate_cmd = True
#         arg.activate_resp = True
#         arg.activate_unipro = True
#         arg.activate_host = True
#         arg.activate_usb = True
#         arg.activate_latency = True
#         arg.activate_group_rw = True
#         arg.activate_cmd_seq = False
#         arg.activate_perfc = False
#         _sdk.sdk_track_activate(arg)

#         #sdk_track_reset
#         _sdk.sdk_track_reset()

#         #sdk_track_result
#         track_result = _sdk.sdk_track_result()
#         print("track result:", list(track_result))
#         print("byActivateCMD:",track_result[0])
#         print("byActivateRESP:",track_result[1])
#         print("byActivateUNIPRO:",track_result[2])
#         print("byActivateHOST:",track_result[3])
#         print("byActivateUSB:",track_result[4])
#         print("byActivateLATENCY:",track_result[5])
#         print("byActivateGROUP_RW:",track_result[6])
#         print("byActivateCMD_SEQ:",track_result[7])
#         print("byActivatePERFC:",track_result[8])
#         print(len(track_result))