from .base import ApiTestBase
from Script.api import shared
from Script.lib import sdk_lib as lib

_sdk = shared.sdk

#pass
# class TestGetSDRAMData(ApiTestBase):
#     def test_get_sdram_data(self):
#         sdram_data =_sdk.get_sdram_data(512)
#         file_path = 'sdram_data.bin'
#         with open(file_path, 'wb') as file:
#             file.write(sdram_data[0:262144])
#         print("SDRAM data:", list(sdram_data))
