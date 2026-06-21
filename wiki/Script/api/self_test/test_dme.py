from .base import ApiTestBase
from Script.api import shared
from Script.lib import sdk_lib as lib
_sdk = shared.sdk

#pass
# class TestDmeGetSet(ApiTestBase):
    # def test_get_hot_device_powermode(self):
    #     att_type = lib.DMETarget.DME_LOCAL.value | lib.AttrSetType.NORMAL.value
    #     mib_att_id = lib.PHYAdapterAttributes.PA_PWRMode.value
    #     sel_idx = 0
    #     (result, attr_val) = _sdk.dme_get(att_type, sel_idx, mib_att_id)
    #     self.assertEqual(result, lib.DMEConfigResult.DME_CONFIG_SUCCESS.value)
            
    # def test_dme_set(self):
    #     att_type = lib.DMETarget.PEER.value | lib.AttrSetType.NORMAL.value
    #     mib_att_id = lib.DME_Attribute.INTERRUPT_DEVICE.value
    #     sel_idx = 0
    #     (result, ori_attr_val) = _sdk.dme_get(att_type, sel_idx, mib_att_id)
    #     self.assertEqual(result, lib.DMEConfigResult.SUCCESS.value)

    #     dme_val = 0
    #     result = _sdk.dme_set(att_type, dme_val, sel_idx, mib_att_id)
    #     self.assertEqual(result, lib.DMEConfigResult.SUCCESS.value)

    #     # for compare, make sure set success
    #     (result, attr_val) = _sdk.dme_get(att_type, sel_idx, mib_att_id)
    #     self.assertEqual(result, lib.DMEConfigResult.DME_CONFIG_SUCCESS.value)
    #     self.assertEqual(attr_val, dme_val)

    #     # recover
    #     dme_val = ori_attr_val
    #     result = _sdk.dme_set(att_type, dme_val, sel_idx, mib_att_id)
    #     self.assertEqual(result, lib.DMEConfigResult.DME_CONFIG_SUCCESS.value)

# class TestDmeReq(ApiTestBase):
#     def test_dme_req(self):
#         _sdk.dme_req(lib.DMEReqMODE.DME_REQ_MPHY_RESE.value)

#pass
# class TestDmeRegGetSet(ApiTestBase):
#     def test_dme_reg_get_set_auto_mode(self):
#         dme_quto_mode_offset = 0xB8
#         ori_dme_quto_mode_val = _sdk.dme_reg_get(dme_quto_mode_offset)
        
#         set_val = 0x00
#         _sdk.dme_reg_set(dme_quto_mode_offset, set_val)
#         dme_quto_mode_val_cmp = _sdk.dme_reg_get(dme_quto_mode_offset)
#         self.assertEqual(set_val, dme_quto_mode_val_cmp)

#         _sdk.dme_reg_set(dme_quto_mode_offset, ori_dme_quto_mode_val)

#pass
# class TestReadDmeReg(ApiTestBase):
#     def test_ReadDmeReg(self):
#         mphyinfo_data = _sdk.read_dme_reg(lib.DMEReg.MPHY_INFO.value) 