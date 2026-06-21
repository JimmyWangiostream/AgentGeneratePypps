from typing import Tuple
from Script.api import shared
from Script.api.exception import ENVIRONMENT_RE_TEST_SPEED_CHANGE_1_LANE_FAIL
from Script.api.ufs_api.defines.bit_define import BIT7
from Script.api.ufs_api.defines.enum_define import LinkStartUpMode
from Script.api.util.functions import dumpfile
from Script.lib import sdk_lib


_log = shared.logger
_sdk = shared.sdk

def dme_get_host_tx_rx_cap_hsgear() -> Tuple[int, int]:
    attr_type = sdk_lib.DMETarget.LOCAL.value | sdk_lib.AttrSetType.NORMAL.value
    mib_attr_id = sdk_lib.MPHY_Attributes.MPHY_TX_HSGEAR_Cap
    tx_cap = _sdk.dme_get(attr_get_type=attr_type, sel=sdk_lib.LaneNumberSelect.TX_LANE0_SELECTOR.value, mib_attr=mib_attr_id.value)
    _log.info(f'DME Get {mib_attr_id.name} = {tx_cap}.')

    mib_attr_id = sdk_lib.MPHY_Attributes.MPHY_RX_HSGEAR_Cap
    rx_cap = _sdk.dme_get(attr_get_type=attr_type, sel=sdk_lib.LaneNumberSelect.RX_LANE0_SELECTOR.value, mib_attr=mib_attr_id.value)
    _log.info(f'DME Get {mib_attr_id.name} = {rx_cap}.')
    return tx_cap, rx_cap

def dme_get_device_tx_rx_cap_hsgear() -> Tuple[int, int]:
    attr_type = sdk_lib.DMETarget.PEER.value | sdk_lib.AttrSetType.NORMAL.value
    mib_attr_id = sdk_lib.MPHY_Attributes.MPHY_TX_HSGEAR_Cap
    tx_cap = _sdk.dme_get(attr_get_type=attr_type, sel=sdk_lib.LaneNumberSelect.TX_LANE0_SELECTOR.value, mib_attr=mib_attr_id.value)
    _log.info(f'DME Get {mib_attr_id.name} = {tx_cap}.')

    mib_attr_id = sdk_lib.MPHY_Attributes.MPHY_RX_HSGEAR_Cap
    rx_cap = _sdk.dme_get(attr_get_type=attr_type, sel=sdk_lib.LaneNumberSelect.RX_LANE0_SELECTOR.value, mib_attr=mib_attr_id.value)
    _log.info(f'DME Get {mib_attr_id.name} = {rx_cap}.')
    return tx_cap, rx_cap

def dme_get_max_hsgear_cap() -> Tuple[int, int]:
    host_tx, host_rx = dme_get_host_tx_rx_cap_hsgear()
    device_tx, device_rx = dme_get_device_tx_rx_cap_hsgear()
    return min(host_tx, device_tx), min(host_rx, device_rx)

def dme_get_connect_tx_rx_lane_number() -> Tuple[int, int]:
    attr_type = sdk_lib.DMETarget.LOCAL.value | sdk_lib.AttrSetType.NORMAL.value
    mib_attr_id = sdk_lib.PHYAdapterAttributes.ConnectedTxDataLanes
    tx_lanes = _sdk.dme_get(attr_get_type=attr_type, sel=0, mib_attr=mib_attr_id.value)
    _log.info(f'DME Get {mib_attr_id.name} = {tx_lanes}.')

    mib_attr_id = sdk_lib.PHYAdapterAttributes.ConnectedRxDataLanes
    rx_lanes = _sdk.dme_get(attr_get_type=attr_type, sel=0, mib_attr=mib_attr_id.value)
    _log.info(f'DME Get {mib_attr_id.name} = {rx_lanes}.')

    if tx_lanes == 1 or rx_lanes == 1:
        _log.error(f'Device only 1-Lane Fail, Tx = {tx_lanes}, Rx = {rx_lanes}')
        raise ENVIRONMENT_RE_TEST_SPEED_CHANGE_1_LANE_FAIL
    return tx_lanes, rx_lanes

def dme_reg_get_speed_mode_ls() -> LinkStartUpMode:
    linkstartup_mode_offset = 0x8B
    val = _sdk.dme_reg_get(linkstartup_mode_offset)
    return LinkStartUpMode((val & BIT7) >> 7)

def dme_set_interrupt_device() -> None:
    attr_type = sdk_lib.DMETarget.PEER.value | sdk_lib.AttrSetType.NORMAL.value
    mib_attr_id = sdk_lib.DME_Attribute.INTERRUPT_DEVICE.value
    sel_idx = 0
    dme_val = 1
    _log.warning(f"DME set INTERRUPT_DEVICE = {dme_val}")
    _sdk.dme_set(attr_type, dme_val, sel_idx, mib_attr_id)
    r_dme_val = _sdk.dme_get(attr_type, sel_idx, mib_attr_id)
    _log.warning(f"DME get INTERRUPT_DEVICE = {r_dme_val}")

def dme_get_host_register_table() -> None:
    _log.info("DME get host register table")
    for host_reg in sdk_lib.HostReg:
        if host_reg.name == 'HOST_MPHY_REG':  # SDK has issue
            continue
        bin_name = f'DME_{host_reg.name}.bin'
        _log.info(f"  Get table {host_reg.name}, dump to {bin_name}")
        buffer = _sdk.get_host_reg(host_reg.value)
        dumpfile(bin_name, buffer)

def get_fw_assert_number(printout: bool=True) -> int:
    _log.info("DME get FW assert number")
    attr_type = sdk_lib.DMETarget.PEER.value | sdk_lib.AttrSetType.NORMAL.value
    sel_idx = 0
    val = _sdk.dme_get(attr_type, sel_idx, 0x8200)
    assert_num = val
    val = _sdk.dme_get(attr_type, sel_idx, 0x8201)
    assert_num += val << 8
    val = _sdk.dme_get(attr_type, sel_idx, 0x8202)
    assert_num += val << 16
    val = _sdk.dme_get(attr_type, sel_idx, 0x8203)
    assert_num += val << 24
    if printout:
        msg = f"  FW assert number: 0x{assert_num:08X}"
        if assert_num != 0:
            _log.error(msg)
        else:
            _log.warning(msg)
    return int(assert_num)
