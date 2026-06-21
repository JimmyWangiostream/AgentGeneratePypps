from dataclasses import dataclass

import Script.api.shared as shared
import Script.api.cmd_seq as ExecuteCMD
from Script.api.exception import PATTERN_ASSERT_SHALL_NOT_CHANGE_SPEED_TO_SLOW_MODE_IN_HSLSS, TESTER_ASSERT_SET_LINKSTARTUP_MODE_FAILED
from Script.api.ufs_api.defines.enum_define import AttributeIDN, LinkStartUpMode, RefClk, SpdChgGear, SpdChgHsRate, SpdChgLane, SpdChgPowerMode
from Script.api.unipro_api.dme_functions import dme_reg_get_speed_mode_ls

_log = shared.logger
_sdk = shared.sdk
_param = shared.param

@dataclass
class CurrentSpeed:
    link_startup_mode: LinkStartUpMode = LinkStartUpMode.LS_RESET_MODE
    txmode: SpdChgPowerMode = SpdChgPowerMode.SLOW
    rxmode: SpdChgPowerMode = SpdChgPowerMode.SLOW
    txgear: SpdChgGear = SpdChgGear.GEAR_1
    rxgear: SpdChgGear = SpdChgGear.GEAR_1
    txlane: SpdChgLane = SpdChgLane.LANE_1
    rxlane: SpdChgLane = SpdChgLane.LANE_1
    hsrate: SpdChgHsRate = SpdChgHsRate.RATE_A
    refclk: RefClk = RefClk.MHZ_19_2

    def update(self, link_startup_mode: LinkStartUpMode, txmode:SpdChgPowerMode, rxmode: SpdChgPowerMode,
                txgear: SpdChgGear, rxgear: SpdChgGear, txlane: SpdChgLane, rxlane: SpdChgLane, hsrate: SpdChgHsRate, refclk: RefClk) -> None:
        self.link_startup_mode = link_startup_mode
        self.txmode = txmode
        self.rxmode = rxmode
        self.txgear = txgear
        self.rxgear = rxgear
        self.txlane = txlane
        self.rxlane = rxlane
        self.hsrate = hsrate
        self.refclk = refclk


def push_switch_ref_clk(ref_clk: RefClk, update_cache: bool=True) -> None:
    ExecuteCMD.WriteAttribute().assign(idn=AttributeIDN.REF_CLK_FREQ).set_attr(ref_clk).enqueue()
    ExecuteCMD.CmdSeqSwitchReferenceClock().set_option(ref_clk.mhz).enqueue()
    if update_cache:
        _param.current_speed.refclk = ref_clk

def switch_ref_clk(ref_clk: RefClk, update_cache: bool=True) -> None:
    push_switch_ref_clk(ref_clk, update_cache)
    ExecuteCMD.send()

def push_speed_change(txmode: SpdChgPowerMode | None=None, rxmode: SpdChgPowerMode | None=None, txgear: SpdChgGear | None=None, rxgear: SpdChgGear | None=None,
               txlane: SpdChgLane | None=None, rxlane: SpdChgLane | None=None, hsrate: SpdChgHsRate | None=None, 
               fc0protectiontimeout: int = 8191, tc0replaytimeout: int = 65535, afc0reqtimeout: int = 32767, 
               fc1protectiontimeout: int = 8191, tc1replaytimeout: int = 65535, afc1reqtimeout: int = 32767, update_cache: bool=True) -> None:
    slow_mode_grp = (SpdChgPowerMode.SLOW, SpdChgPowerMode.SLOW_AUTO)
    fast_mode_grp = (SpdChgPowerMode.FAST, SpdChgPowerMode.FAST_AUTO)
    
    #------------- Use Previous Setting If It's None -------------#
    txmode = _param.current_speed.txmode if txmode is None else txmode
    rxmode = _param.current_speed.rxmode if rxmode is None else rxmode
    txgear = _param.current_speed.txgear if txgear is None else txgear
    rxgear = _param.current_speed.rxgear if rxgear is None else rxgear
    txlane = _param.current_speed.txlane if txlane is None else txlane
    rxlane = _param.current_speed.rxlane if rxlane is None else rxlane
    hsrate = _param.current_speed.hsrate if hsrate is None else hsrate

    # When ResetMode is set to HS_MODE, Fast_Mode and FastAuto_Mode are valid settings to PA_PWRMode. 
    # Whereas setting PA_PWRMode to Slow_Mode or SlowAuto_Mode shall be rejected with INVALID_MIB_ATTRIBUTE_VALUE.
    if _param.current_speed.link_startup_mode == LinkStartUpMode.HS_RESET_MODE and (txmode in slow_mode_grp or rxmode in slow_mode_grp):
        _log.error(f'[HS-LSS MODE] Change Speed to {txmode=}, {rxmode=} is a invalid operation.')
        raise PATTERN_ASSERT_SHALL_NOT_CHANGE_SPEED_TO_SLOW_MODE_IN_HSLSS
    # When ResetMode is HS_MODE, and Application should change PA_HSSeries only on the first Link configuration after a successful link startup
    if _param.current_speed.link_startup_mode == LinkStartUpMode.HS_RESET_MODE and hsrate != _param.current_speed.hsrate:
        _log.warning(f'[HS-LSS MODE] Change HSRate from {SpdChgHsRate(_param.current_speed.hsrate).name} to {hsrate.name}. This can only switch one time in HS-LSS MODE.')

    if _param.current_speed.link_startup_mode == LinkStartUpMode.LS_RESET_MODE and hsrate != _param.current_speed.hsrate:
        _log.info(f'[LS-LSS MODE] Change HSRate from {SpdChgHsRate(_param.current_speed.hsrate).name} to {hsrate.name}. Speed Change to LS Gear1 First.')
        ExecuteCMD.CmdSeqSpeedChange().set_option(SpdChgPowerMode.SLOW, SpdChgPowerMode.SLOW, SpdChgGear.GEAR_1, SpdChgGear.GEAR_1,
               _param.current_speed.txlane, _param.current_speed.rxlane, _param.current_speed.hsrate, fc0protectiontimeout,
               tc0replaytimeout, afc0reqtimeout, fc1protectiontimeout, 
               tc1replaytimeout, afc1reqtimeout).enqueue()
        ExecuteCMD.CmdSeqSpeedChange().set_option(SpdChgPowerMode.SLOW, SpdChgPowerMode.SLOW, SpdChgGear.GEAR_1, SpdChgGear.GEAR_1,
               _param.current_speed.txlane, _param.current_speed.rxlane, hsrate, fc0protectiontimeout,
               tc0replaytimeout, afc0reqtimeout, fc1protectiontimeout, 
               tc1replaytimeout, afc1reqtimeout).enqueue()

    ExecuteCMD.CmdSeqSpeedChange().set_option(txmode, rxmode, txgear, rxgear,
               txlane, rxlane, hsrate, fc0protectiontimeout,
               tc0replaytimeout, afc0reqtimeout, fc1protectiontimeout, 
               tc1replaytimeout, afc1reqtimeout).enqueue()
    if update_cache:
        _param.current_speed.update(_param.current_speed.link_startup_mode, txmode, rxmode, txgear, rxgear, txlane, rxlane, hsrate, _param.current_speed.refclk)

def speed_change(txmode: SpdChgPowerMode | None=None, rxmode: SpdChgPowerMode | None=None, txgear: SpdChgGear | None=None, rxgear: SpdChgGear | None=None,
               txlane: SpdChgLane | None=None, rxlane: SpdChgLane | None=None, hsrate: SpdChgHsRate | None=None, 
               fc0protectiontimeout: int = 8191, tc0replaytimeout: int = 65535, afc0reqtimeout: int = 32767, 
               fc1protectiontimeout: int = 8191, tc1replaytimeout: int = 65535, afc1reqtimeout: int = 32767, update_cache: bool=True) -> None:
    push_speed_change(txmode, rxmode, txgear, rxgear,
               txlane, rxlane, hsrate, fc0protectiontimeout,
               tc0replaytimeout, afc0reqtimeout, fc1protectiontimeout, 
               tc1replaytimeout, afc1reqtimeout, update_cache)
    ExecuteCMD.send()
 

def set_link_startup_mode_and_check(reset_mode: LinkStartUpMode) -> None:
    _sdk.set_link_startup_mode(reset_mode)
    mode = dme_reg_get_speed_mode_ls()
    if mode != reset_mode:
        _log.error(f'Link Startup Mode not changed. Expected: {reset_mode.name}({reset_mode.value}), but dme reg get: {mode}')
        raise TESTER_ASSERT_SET_LINKSTARTUP_MODE_FAILED
    _param.current_speed.link_startup_mode = reset_mode