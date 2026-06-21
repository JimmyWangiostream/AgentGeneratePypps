import inspect

from Script.api import shared, ExecuteCMD
from Script.api.self_test.base import ApiTestBase
from Script.api.ufs_api.vendor_cmd.functions import _compute_pass_key  # type: ignore


_sdk = shared.sdk
logger = shared.logger


class TestAccessVendorMode(ApiTestBase):

    def setUp(self) -> None:
        ExecuteCMD.clear()

    def tearDown(self) -> None:
        pass

    def test_algorithm(self) -> None:
        logger.info(f"Test {inspect.currentframe().f_code.co_name}")  # type: ignore

        k = {  # Acquired from KIC PS8329 BiCS8
            'PHISON': {
                'rand_num': [0xecde9b92, 0x2646b373, 0x2dc3e187, 0x46ec76d8],
                'rand_num_rev': [0x929bdeec, 0x73b34626, 0x87e1c32d, 0xd876ec46],
                'pwd': [0xc2d3b7bf, 0x3cddb30c, 0x91da68ee, 0x397f9f9d],
                'final_pwd': [0xfe0e04b3, 0xa8a5f773],
                'final_pwd_rev': [0xb3040efe, 0x73f7a5a8],
            },
            'KIC': {
                'rand_num': [0x886308fe, 0xcf70611e, 0x78bb5d77, 0x9b50a8a1],
                'rand_num_rev': [0xfe086388, 0x1e6170cf, 0x775dbb78, 0xa1a8509b],
                'pwd': [0xaa5b21c5, 0x401cc2f7, 0x5e5810bb, 0x50e18628],
                'final_pwd': [0xea47e332, 0x0eb99693],
                'final_pwd_rev': [0x32e347ea, 0x9396b90e],
            },
        }

        final_pwd0, final_pwd1 = _compute_pass_key(k['PHISON']['rand_num_rev'][0], k['PHISON']['rand_num_rev'][1], k['PHISON']['rand_num_rev'][2], k['PHISON']['rand_num_rev'][3], 'PHISON')
        self.assertEqual(final_pwd0, k['PHISON']['final_pwd_rev'][0])
        self.assertEqual(final_pwd1, k['PHISON']['final_pwd_rev'][1])

        final_pwd0, final_pwd1 = _compute_pass_key(k['KIC']['rand_num_rev'][0], k['KIC']['rand_num_rev'][1], k['KIC']['rand_num_rev'][2], k['KIC']['rand_num_rev'][3], 'KIC')
        self.assertEqual(final_pwd0, k['KIC']['final_pwd_rev'][0])
        self.assertEqual(final_pwd1, k['KIC']['final_pwd_rev'][1])
