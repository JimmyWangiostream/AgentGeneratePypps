from dataclasses import dataclass
from typing import List, cast
import Script.api.shared as shared
import Script.api.cmd_seq as ExecuteCMD
from Script.api.cmd_seq.response import QueryResponse
from Script.api.ufs_api.debug_cmd.dcmd5 import Dcmd5, Dcmd5SpeedChange, ReadBootData, ReadData
from Script.api.ufs_api.defines import WellKnownLUN, DescriptorIDN, SpdChgPowerMode, SpdChgGear, SpdChgLane, SpdChgHsRate, MaxNumberLUN

from Script.api.ufs_api.debug_cmd.dcmd_enum import Dcmd5ResetType
from Script.api.ufs_api.defines.enum_define import AttributeIDN, Dcmd5SsuActive, LinkStartUpMode, RefClk, SpeedChangeTiming
from Script.api.unipro_api.dme_functions import dme_get_connect_tx_rx_lane_number, dme_get_max_hsgear_cap
from Script.api.unipro_api.power_change import push_speed_change, set_link_startup_mode_and_check
from Script.lib import sdk_lib as lib

_log = shared.logger
_sdk = shared.sdk
_param = shared.param

def first_init_to_max_hs_gear(link_startup_mode: LinkStartUpMode, ref_clk: RefClk) -> None:
    """
    1. Switch Tester RefClk to `ref_clk`
    2. Link
    3. Get Max HSGear Capability
    4. Get Connected TX RX Lane Number
    #### HS-LSS Flow
    1. Set to HS-LSS
    2. Set DCMD5 with `ref_clk` and speed change to max possible hsgear
    #### LS-LSS Flow
    1. Set DCMD5 with LS-Gear1
    2. Write Attibute REF_CLK_FREQ, value=`ref_clk`
    3. Speed Change to max possible hsgear
    """
    _sdk.on_switch_ref_clk(ref_clk.mhz)
    _sdk.host_link_startup()
    txgear, rxgear = dme_get_max_hsgear_cap()
    txlane, rxlane = dme_get_connect_tx_rx_lane_number()
    if ref_clk <= RefClk.MHZ_26_0:
        max_support_hsgear = SpdChgGear.GEAR_4
    else:
        max_support_hsgear = SpdChgGear.GEAR_5
    max_support_hsgear = SpdChgGear(min(max_support_hsgear, txgear, rxgear))
    _log.info(f'[First Init] LinkStartUp Mode = {link_startup_mode.name}, RefClk = {ref_clk.name}, MaxHsGear = {max_support_hsgear}, Lane = {txlane}')

    if link_startup_mode == LinkStartUpMode.HS_RESET_MODE:
        set_link_startup_mode_and_check(link_startup_mode)
        init_tester_to_unit_ready(resetmode=Dcmd5ResetType.HW_RESET,
                                  powerdown=False,
                                  speed_change=Dcmd5SpeedChange(SpeedChangeTiming.AFTER_INIT, 
                                                                SpdChgPowerMode.FAST, 
                                                                max_support_hsgear, 
                                                                SpdChgLane(txlane), 
                                                                SpdChgHsRate.RATE_B, 
                                                                ref_clk))
    else:
        init_tester_to_unit_ready(resetmode=Dcmd5ResetType.HW_RESET,
                                  powerdown=False,
                                  speed_change=Dcmd5SpeedChange(SpeedChangeTiming.AFTER_INIT, 
                                                                SpdChgPowerMode.SLOW, 
                                                                SpdChgGear.GEAR_1, 
                                                                SpdChgLane(txlane), 
                                                                SpdChgHsRate.RATE_B, 
                                                                ref_clk))
        ExecuteCMD.WriteAttribute().assign(idn=AttributeIDN.REF_CLK_FREQ).set_attr(ref_clk).enqueue()
        push_speed_change(SpdChgPowerMode.FAST, SpdChgPowerMode.FAST, max_support_hsgear, max_support_hsgear,
                          SpdChgLane(txlane), SpdChgLane(rxlane), SpdChgHsRate.RATE_B, update_cache=True)
        ExecuteCMD.send()
       

def init_tester_to_unit_ready(resetmode: Dcmd5ResetType, powerdown: bool = False, stop_after_device_init: bool = False,
                              read_boot: ReadBootData | None=None, read_data: ReadData | None=None,
                              speed_change: Dcmd5SpeedChange | None=None, ssu_active: Dcmd5SsuActive=Dcmd5SsuActive.EXIT_SLEEP) -> None:
    """
    Default behavior:  
    1. No power down
    2. Speed change after init
    3. Speed change to current speed setting
    4. No read boot data during init
    5. SSU Active after init
    6. No read data after init
    """  
    if speed_change is None:
        speed_change = Dcmd5SpeedChange(SpeedChangeTiming.AFTER_INIT, _param.current_speed.txmode, 
                                        _param.current_speed.txgear, _param.current_speed.txlane, 
                                        _param.current_speed.hsrate, _param.current_speed.refclk)
    #----------------------- Issue DCMD5 ----------------------#
    dcmd5 = Dcmd5(resetmode, powerdown, read_boot, read_data, speed_change, ssu_active)
    try:
        dcmd5.set_debug_cmd5()
    except lib.DLL_ERROR as e:
        _log.error('DCMD5 Failed.')
        dcmd5_info = dcmd5.get_debug_cmd5()
        dcmd5_info.raise_by_status()
        raise # still raise in case dcmd5 info status is 0(PASS)
    else:
        dcmd5_info = dcmd5.get_debug_cmd5()

    if read_boot is not None:
        read_boot.crc_after_read = dcmd5_info.boot_data_crc
    if read_data is not None:
        read_data.crc_after_read = dcmd5_info.read_data_crc
    #--------------- Update Current Speed Cache --------------#
    _param.current_speed.update(_param.current_speed.link_startup_mode, speed_change.mode, 
                                speed_change.mode, speed_change.gear, speed_change.gear, 
                                speed_change.lane, speed_change.lane, speed_change.hsrate, speed_change.refclk)
    #---------------------- After Init -----------------------#
    if not stop_after_device_init:
        get_desc_and_update_cache()
        push_test_all_unit_ready()
        ExecuteCMD.send()

def push_test_all_unit_ready() -> None:
    wk_lun = [WellKnownLUN.UFS_DEVICE, WellKnownLUN.REPORT_LUNS, WellKnownLUN.RPMB]
    _log.info("test unit ready! (normal lun)")
    for lun in range(_param.gMaxNumberLU):
        if _param.gUnit[lun].b3_lu_enable:
            test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
            test_unit_ready.set_option(lun)
            ExecuteCMD.enqueue(test_unit_ready)
    for lun in wk_lun:
        _log.info(f"test unit ready! {type(lun).__name__}.{lun.name}")
        test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
        test_unit_ready.set_option(lun)
        ExecuteCMD.enqueue(test_unit_ready)

def update_descriptor(idn: int, index: int, response: QueryResponse) -> None:
    if idn == DescriptorIDN.DEVICE:
        _param.gDevice.from_bytes(response.data)
    elif idn == DescriptorIDN.GEOMETRY:
        _param.gGeometry.from_bytes(response.data)
        max_num_lun_str = MaxNumberLUN(_param.gGeometry.b12_max_number_lu).name
        _param.gMaxNumberLU = int(max_num_lun_str.split('_')[-1])  # 8 or 32
    elif idn == DescriptorIDN.UNIT:
        _param.gUnit[index].from_bytes(response.data)
        _param.gLUCapacity[index] = _param.gUnit[index].q11_logical_block_count
        
        if _param.gUnit[index].q11_logical_block_count != 0:
            _log.info(f'unit_descriptor[{index}].b0_length={_param.gUnit[index].q11_logical_block_count}')

def get_desc_and_update_cache() -> None:
    _log.info("read device descriptor!")
    device_descriptor = ExecuteCMD.ReadDescriptor()
    device_descriptor.assign(DescriptorIDN.DEVICE)
    device_descriptor.set_option(wait_queue_empty=True)
    dev_desc_idx = ExecuteCMD.enqueue(device_descriptor)

    _log.info("read geometry descriptor!")
    geometry_descriptor = ExecuteCMD.ReadDescriptor()
    geometry_descriptor.assign(DescriptorIDN.GEOMETRY)
    geometry_descriptor.set_option(wait_queue_empty=True)
    geo_desc_idx = ExecuteCMD.enqueue(geometry_descriptor)

    ExecuteCMD.send(clear_on_success=False)
    update_descriptor(DescriptorIDN.DEVICE, 0, cast(QueryResponse, ExecuteCMD.read_response(dev_desc_idx)))
    update_descriptor(DescriptorIDN.GEOMETRY, 0, cast(QueryResponse, ExecuteCMD.read_response(geo_desc_idx)))
    ExecuteCMD.clear()

    _log.info("read unit descriptor!")
    unit_desc_idxes:List[int] = []
    for lun in range(0, _param.gMaxNumberLU):
        unit_descriptor = ExecuteCMD.ReadDescriptor()
        unit_descriptor.assign(DescriptorIDN.UNIT, lun)
        unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

    ExecuteCMD.send(clear_on_success=False)
    for index in unit_desc_idxes:
        update_descriptor(DescriptorIDN.UNIT, index, cast(QueryResponse, ExecuteCMD.read_response(index)))
    ExecuteCMD.clear()