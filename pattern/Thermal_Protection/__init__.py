import package_root, time
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_logger import logger
from Script.api.ufs_api.defines import *

_sdk = api.shared.sdk
_param = api.shared.param

def manual_rst_n() -> None:
    logger.info('RST_n')
    _sdk.reset_n(mode=0)
    # time.sleep(1)
    # _sdk.reset_n(mode=0)

    logger.info('Link start up')
    cmd = ExecuteCMD.CmdSeqPowerCycle()
    cmd.set_option(api.PowerCycleMode.LINK_START_UP)
    cmd.enqueue()
    ExecuteCMD.send(clear_on_success=True) 

    logger.info('Nop out')
    cmd = ExecuteCMD.CmdSeqPushNopOutPollNopIn()
    cmd.set_option(timeout=10000000)
    cmd.enqueue()
    ExecuteCMD.send(clear_on_success=True)
    
    logger.info('Ready device init flag')
    cmd = ExecuteCMD.CmdSeqReadyDeviceInitFlag()
    cmd.enqueue()
    ExecuteCMD.send(clear_on_success=True)

    for lun in range(_param.gMaxNumberLU):
        if  _param.gUnit[lun].b3_lu_enable:
            test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
            test_unit_ready.set_option(lun)
            ExecuteCMD.enqueue(test_unit_ready)
    ExecuteCMD.send(clear_on_success=True)
                
    cmd = ExecuteCMD.CmdSeqSwitchReferenceClock()
    cmd.set_option()
    cmd.enqueue()
    ExecuteCMD.send(clear_on_success=True)
    
    cmd = ExecuteCMD.CmdSeqSpeedChange()
    cmd.set_option(txmode=SpdChgPowerMode.FAST, rxmode=SpdChgPowerMode.FAST,
                   txgear=SpdChgGear.GEAR_4, rxgear=SpdChgGear.GEAR_4,
                   txlane=SpdChgLane.LANE_2, rxlane=SpdChgLane.LANE_2,
                   hsrate=SpdChgHsRate.RATE_B)
    cmd.enqueue()
    ExecuteCMD.send(clear_on_success=True)